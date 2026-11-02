# pubchem-fetch

把 `docs/pubchem-ligand-SOP.md` 的四階段手動網頁操作，自動化成一條命令。

**只用 Python 標準庫**，不需要 `pip install` 任何東西（Python ≥ 3.8）。

## 用法

```bash
# 最常用：名稱查詢 + 95% 門檻 + 2D 座標
python pubchem_fetch.py --name paxlovid --threshold 95

# docking 用途：3D 座標（每化合物 1 個 conformer）
python pubchem_fetch.py --cid 155903259 --threshold 95 --coord 3d

# 先探命中數再決定要不要下載（不碰 SDF，秒回）
python pubchem_fetch.py --name aspirin --threshold 99 --dry-run

# 試跑 / 教學：只取前 10 筆
python pubchem_fetch.py --name paxlovid --threshold 95 --max-records 10
```

## 參數

| 參數 | 說明 |
|---|---|
| `--name` | 化合物名稱，自動解析成 CID（取 PubChem best compound match） |
| `--cid` | 直接指定 CID，跳過名稱解析。與 `--name` 互斥、必擇一 |
| `--threshold` | Tanimoto 門檻 %，預設 **95**（PubChem 網頁預設是 90） |
| `--coord` | `2d`（預設，供指紋比對）或 `3d`（供分子對接） |
| `--max-records` | 相似度搜尋回傳上限，不設則全取 |
| `--label` | 輸出檔名的母核標籤，預設由 `--name` 或化合物 Title 推導 |
| `--outdir` | 輸出根目錄，預設 repo 的 `data/` |
| `--dry-run` | 只跑階段 1-2 並報告命中數 |

## 產出

輸出落在 `data/<label>_like<門檻>/`，三個檔一組：

| 檔案 | 內容 |
|---|---|
| `<label>_like<門檻>[_3d].sdf` | 配體庫本體，多分子串接的 SDF |
| `<label>_like<門檻>[_3d]_properties.csv` | 屬性表（MW、SMILES、InChIKey、XLogP、TPSA、HBD/HBA、可旋轉鍵） |
| `<label>_like<門檻>[_3d]_manifest.json` | **來源紀錄**：查詢條件、門檻、命中數、完整 CID 清單、產生時間 |

命名直接落實 SOP 第 4 階段的規範——`paxlovid_like95.sdf` 一眼看出母核與門檻，
不必再手動把 `PubChem_search_records.sdf` 改名。

> SDF 與 CSV 體積大且能由 manifest 完整重現，已在 `.gitignore` 排除；
> **manifest 要進 repo**，它就是配體庫的可追溯憑證。

## 最小可重現測試

```bash
bash test_minimal.sh
```

驗證四件事：門檻 95% → 281 筆、90% → 743 筆（SOP 基準，容許 ±5% 資料庫成長漂移）、
小批次下載的分子數正確、manifest 與命名規範正確。

## 已知限制

- **3D 座標並非每個化合物都有**。整批失敗時程式會退回逐一抓取，把真正缺 3D 的
  CID 記進 manifest 的 `missing_cids`，不讓單一化合物拖垮整個配體庫。
  要補齊可考慮用 RDKit 本地產構型（見 `CLAUDE.md` 的 Next Steps）。
- **PUG-REST 流量限制**：每秒 5 次請求、每分鐘 400 次。程式已內建 0.25 秒節流
  與 503 退避重試；不要同時開多個 instance 打同一個 API。
- 相似度搜尋用的是 PubChem 伺服器端的 **PubChem Fingerprint + Tanimoto**，
  與 RDKit/Morgan 指紋算出的相似度不可直接互相比較。
- `--name` 取的是 best match 第一筆。像 `paxlovid` 這種複方商品名會解析到主成分
  （Nirmatrelvir），**不含** Ritonavir；要兩者都要就跑兩次或改用 `--cid`。
