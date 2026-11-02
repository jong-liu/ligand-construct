#!/bin/bash
# 最小可重現測試：驗證 pubchem_fetch.py 四階段仍與 SOP 基準一致。
# 基準來自 docs/pubchem-ligand-SOP.md（Nirmatrelvir, CID 155903259）：
#   Tanimoto 90% -> 743 筆、95% -> 281 筆
# 命中數隨 PubChem 資料增長會漂移，故允許 ±5% 誤差；差太多就是演算法或端點變了。
set -u
cd "$(dirname "$0")"
PY=${PYTHON:-python}
FAIL=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

check_count() {  # $1=門檻 $2=期望值
  local got
  got=$("$PY" -I pubchem_fetch.py --cid 155903259 --threshold "$1" --dry-run 2>&1 \
        | grep -oE '命中 [0-9]+' | grep -oE '[0-9]+')
  if [ -z "$got" ]; then
    echo "❌ 門檻 ${1}%：拿不到命中數（端點或輸出格式變了）"; FAIL=1; return
  fi
  local lo=$(( $2 * 95 / 100 )) hi=$(( $2 * 105 / 100 ))
  if [ "$got" -ge "$lo" ] && [ "$got" -le "$hi" ]; then
    echo "✅ 門檻 ${1}%：命中 $got 筆（基準 $2，容許 $lo-$hi）"
  else
    echo "❌ 門檻 ${1}%：命中 $got 筆，偏離基準 $2（容許 $lo-$hi）"; FAIL=1
  fi
}

echo "── 測試 1-2：相似度門檻對應命中數 ──"
check_count 95 281
check_count 90 743

echo ""
echo "── 測試 3-4：小批次 2D 下載與歸檔 ──"
"$PY" -I pubchem_fetch.py --cid 155903259 --threshold 95 --max-records 5 \
      --label testlib --outdir "$TMP" > "$TMP/run.log" 2>&1
if [ $? -ne 0 ]; then
  echo "❌ 下載流程失敗："; cat "$TMP/run.log"; FAIL=1
else
  D="$TMP/testlib_like95"
  N=$(grep -c '\$\$\$\$' "$D/testlib_like95.sdf" 2>/dev/null || echo 0)
  [ "$N" -eq 5 ] && echo "✅ SDF 含 5 個分子" || { echo "❌ SDF 分子數為 $N，應為 5"; FAIL=1; }
  [ -s "$D/testlib_like95_properties.csv" ] && echo "✅ 屬性 CSV 已產生" \
    || { echo "❌ 缺屬性 CSV"; FAIL=1; }
  if "$PY" -I -c "import json,sys;d=json.load(open(sys.argv[1]));assert d['search']['threshold_percent']==95;assert len(d['cids'])==5" \
       "$D/testlib_like95_manifest.json" 2>/dev/null; then
    echo "✅ manifest 內容正確（門檻 + CID 清單）"
  else
    echo "❌ manifest 缺失或內容不符"; FAIL=1
  fi
  grep -q 'testlib_like95.sdf' "$D/testlib_like95_manifest.json" \
    && echo "✅ 檔名符合 <label>_like<門檻>.sdf 命名規範" \
    || { echo "❌ 命名規範不符"; FAIL=1; }
fi

echo ""
[ "$FAIL" -eq 0 ] && echo "🎉 全部通過" || echo "💥 有測試失敗"
exit $FAIL
