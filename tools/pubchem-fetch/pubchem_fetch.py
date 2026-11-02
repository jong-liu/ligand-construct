#!/usr/bin/env python3
"""PubChem 配體庫建構 CLI — 把 docs/pubchem-ligand-SOP.md 的四階段手動流程自動化。

四階段對應：
  1. 目標化合物定位   name/CID -> CID + 分子基本資訊
  2. 相似度篩選       fastsimilarity_2d (Fingerprint Tanimoto)
  3. 結構檔導出       SDF (2D 或 3D) + 屬性 CSV
  4. 命名歸檔         <label>_like<threshold>.sdf + manifest.json（可追溯）

只用標準庫，無需安裝任何套件。

用法：
  python pubchem_fetch.py --name paxlovid --threshold 95
  python pubchem_fetch.py --cid 155903259 --threshold 95 --coord 3d
  python pubchem_fetch.py --name aspirin --threshold 99 --dry-run
"""

import argparse
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Windows 主控台預設不是 UTF-8（cp950），中文訊息會變亂碼或丟 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# PUG-REST 流量限制：每秒最多 5 次請求 -> 每次請求間隔至少 0.25 秒
REQUEST_INTERVAL = 0.25
# 一次 POST 帶多少 CID；太多會超出伺服器單次處理上限
CHUNK_SIZE = 100

# 核對標的化合物用的屬性欄位（2025 年後 PubChem 已改名：
# CanonicalSMILES -> ConnectivitySMILES、IsomericSMILES -> SMILES）
PROPERTIES = [
    "Title",
    "MolecularFormula",
    "MolecularWeight",
    "SMILES",
    "InChIKey",
    "XLogP",
    "TPSA",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
]

_last_request = 0.0


def _throttle():
    """保證兩次請求間隔不小於 REQUEST_INTERVAL。"""
    global _last_request
    wait = REQUEST_INTERVAL - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


def request(path, data=None, retries=3):
    """打 PUG-REST。data 不為 None 時以 POST 送出（表單編碼）。回傳 bytes。"""
    url = f"{BASE}/{path}"
    body = urllib.parse.urlencode(data).encode() if data else None
    for attempt in range(1, retries + 1):
        _throttle()
        req = urllib.request.Request(url, data=body, headers={"User-Agent": "ligand-construct/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace").strip()
            # 404 = 查無資料，重試無意義；503 = 伺服器忙碌，值得退避重試
            if exc.code == 404 or attempt == retries:
                raise RuntimeError(f"PubChem HTTP {exc.code}: {detail}") from exc
            print(f"   ⚠️  HTTP {exc.code}，{attempt * 2}s 後重試（{attempt}/{retries - 1}）", file=sys.stderr)
            time.sleep(attempt * 2)
        except urllib.error.URLError as exc:
            if attempt == retries:
                raise RuntimeError(f"連線 PubChem 失敗：{exc.reason}") from exc
            time.sleep(attempt * 2)
    raise RuntimeError("unreachable")


# ── 階段 1：目標化合物定位 ──────────────────────────────────────────────


def resolve_cid(name):
    """化合物名稱 -> CID（取 Best Compound Match，即回傳清單第一筆）。"""
    payload = json.loads(request(f"compound/name/{urllib.parse.quote(name)}/cids/JSON"))
    cids = payload["IdentifierList"]["CID"]
    return cids[0], cids


def fetch_properties(cids):
    """取屬性表。回傳 (dict 清單, 原始 CSV 文字)。"""
    props = ",".join(PROPERTIES)
    raw = request(
        f"compound/cid/property/{props}/CSV",
        data={"cid": ",".join(str(c) for c in cids)},
    ).decode("utf-8", "replace")
    rows = list(csv.DictReader(io.StringIO(raw)))
    return rows, raw


# ── 階段 2：Tanimoto 相似度篩選 ─────────────────────────────────────────


def similarity_search(cid, threshold, max_records=None):
    """Fingerprint Tanimoto 2D 相似結構搜尋，回傳 CID 清單（含 query 自身）。"""
    query = {"Threshold": threshold}
    if max_records:
        query["MaxRecords"] = max_records
    path = f"compound/fastsimilarity_2d/cid/{cid}/cids/JSON?{urllib.parse.urlencode(query)}"
    payload = json.loads(request(path))
    return payload["IdentifierList"]["CID"]


# ── 階段 3：SDF 導出 ───────────────────────────────────────────────────


def download_sdf(cids, coord, out_path, progress=True):
    """分批抓 SDF 併成單一檔案。回傳 (成功 CID 清單, 缺構型 CID 清單)。

    3D 座標並非每個化合物都有；整批失敗時退回逐一抓取，把真正缺 3D 的挑出來，
    不讓單一化合物拖垮整個配體庫。
    """
    path = "compound/cid/SDF" + ("?record_type=3d" if coord == "3d" else "")
    chunks = [cids[i : i + CHUNK_SIZE] for i in range(0, len(cids), CHUNK_SIZE)]
    ok, missing = [], []

    with out_path.open("wb") as fh:
        for idx, chunk in enumerate(chunks, 1):
            if progress:
                print(f"   下載 {idx}/{len(chunks)} 批（{len(chunk)} 筆）…", flush=True)
            try:
                fh.write(request(path, data={"cid": ",".join(str(c) for c in chunk)}))
                ok.extend(chunk)
            except RuntimeError as exc:
                print(f"   ⚠️  整批失敗（{exc}），改逐一抓取此批", file=sys.stderr)
                for cid in chunk:
                    try:
                        fh.write(request(path, data={"cid": str(cid)}))
                        ok.append(cid)
                    except RuntimeError:
                        missing.append(cid)
    return ok, missing


# ── 階段 4：命名歸檔 ───────────────────────────────────────────────────


def slugify(text):
    """化合物名稱 -> 檔名可用的 label（小寫、非英數轉連字號）。"""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-") or "library"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="PubChem 配體庫建構：相似度搜尋 + SDF 導出 + manifest（SOP 四階段自動化）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="範例：python pubchem_fetch.py --name paxlovid --threshold 95 --coord 3d",
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--name", help="化合物名稱（例 paxlovid），自動解析成 CID")
    src.add_argument("--cid", type=int, help="直接指定 PubChem CID（例 155903259）")
    ap.add_argument("--threshold", type=int, default=95,
                    help="Tanimoto 門檻 %%（PubChem UI 預設 90，高嚴格度用 95；預設 95）")
    ap.add_argument("--coord", choices=["2d", "3d"], default="2d",
                    help="SDF 座標維度：2d 供指紋比對，3d 供 docking（預設 2d）")
    ap.add_argument("--max-records", type=int, help="相似度搜尋回傳上限（不設則全取）")
    ap.add_argument("--label", help="輸出檔名的母核標籤（預設由 --name 或化合物 Title 推導）")
    ap.add_argument("--outdir", default=None,
                    help="輸出根目錄（預設為 repo 的 data/）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只做階段 1-2 並報告命中數，不下載 SDF")
    args = ap.parse_args(argv)

    if not 1 <= args.threshold <= 100:
        ap.error("--threshold 必須在 1-100 之間")

    # 階段 1：定位
    print("── 階段 1：目標化合物定位 ──")
    if args.name:
        cid, all_cids = resolve_cid(args.name)
        print(f"   查詢 `{args.name}` → CID {cid}" + (f"（同名另有 {len(all_cids) - 1} 筆，取 best match）" if len(all_cids) > 1 else ""))
    else:
        cid = args.cid
        print(f"   指定 CID {cid}")

    query_rows, _ = fetch_properties([cid])
    info = query_rows[0] if query_rows else {}
    for key in ("Title", "MolecularFormula", "MolecularWeight", "InChIKey", "SMILES"):
        if info.get(key):
            print(f"   {key:<18}{info[key]}")

    label = slugify(args.label or args.name or info.get("Title") or f"cid{cid}")

    # 階段 2：相似度篩選
    print(f"\n── 階段 2：Tanimoto {args.threshold}% 相似度篩選 ──")
    hits = similarity_search(cid, args.threshold, args.max_records)
    print(f"   命中 {len(hits)} 筆化合物")

    if args.dry_run:
        print("\n   --dry-run：不下載 SDF，流程結束。")
        return 0

    # 階段 3-4：導出與歸檔
    outroot = Path(args.outdir) if args.outdir else Path(__file__).resolve().parents[2] / "data"
    outdir = outroot / f"{label}_like{args.threshold}"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"{label}_like{args.threshold}" + ("_3d" if args.coord == "3d" else "")
    sdf_path = outdir / f"{stem}.sdf"
    csv_path = outdir / f"{stem}_properties.csv"

    print(f"\n── 階段 3：SDF 導出（{args.coord.upper()} 座標）──")
    ok, missing = download_sdf(hits, args.coord, sdf_path)
    print(f"   ✅ {sdf_path.name}：{len(ok)} 筆")
    if missing:
        print(f"   ⚠️  {len(missing)} 筆無 {args.coord.upper()} 構型，已略過（見 manifest 的 missing_cids）")

    print("   取屬性表…")
    prop_rows, prop_csv = fetch_properties(ok)
    csv_path.write_text(prop_csv, encoding="utf-8")
    print(f"   ✅ {csv_path.name}：{len(prop_rows)} 列")

    print("\n── 階段 4：命名歸檔 ──")
    manifest = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "tool": "tools/pubchem-fetch/pubchem_fetch.py",
        "query": {
            "name": args.name,
            "cid": cid,
            "title": info.get("Title"),
            "molecular_formula": info.get("MolecularFormula"),
            "inchikey": info.get("InChIKey"),
            "smiles": info.get("SMILES"),
        },
        "search": {
            "method": "PubChem fastsimilarity_2d (Fingerprint Tanimoto)",
            "threshold_percent": args.threshold,
            "max_records": args.max_records,
            "hit_count": len(hits),
        },
        "output": {
            "coordinate": args.coord,
            "sdf": sdf_path.name,
            "properties_csv": csv_path.name,
            "compound_count": len(ok),
        },
        "missing_cids": missing,
        "cids": ok,
    }
    manifest_path = outdir / f"{stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✅ {manifest_path.name}（來源可追溯紀錄）")
    print(f"\n配體庫完成：{outdir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n中斷。", file=sys.stderr)
        sys.exit(130)
