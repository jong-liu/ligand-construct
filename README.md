# ligand-construct

**從 PubChem 建立可重現、可追溯的小分子配體庫。**

虛擬篩選與分子對接的第一步是備好配體庫。手動在 PubChem 網頁上點選、下載、改檔名
可行但無法重現——三個月後沒人記得 `PubChem_search_records.sdf` 當初用的是哪個門檻。
本專案把那套 SOP 固化成一條命令與一個網頁，每份配體庫都附帶完整來源紀錄。

🌐 **線上工具**：https://jong-liu.github.io/ligand-construct/

## 四階段 SOP

| 階段 | 動作 | 產出 |
|---|---|---|
| 1. 目標化合物定位 | 名稱／CID → PubChem CID，核對分子式、MW、SMILES、InChIKey | 鎖定 query molecule |
| 2. 相似度篩選 | PubChem Fingerprint + Tanimoto 2D 門檻（預設 90%，高嚴格度 95%） | 命中 CID 清單 |
| 3. 結構檔導出 | SDF，2D（指紋比對）或 3D（分子對接，1 conformer） | 配體庫本體 + 屬性 CSV |
| 4. 命名歸檔 | `<母核>_like<門檻>.sdf` + manifest | 可追溯的配體庫 |

示範標的 Paxlovid（主成分 Nirmatrelvir, CID 155903259）：
Tanimoto 90% → 743 筆、95% → 281 筆。完整說明見 [docs/pubchem-ligand-SOP.md](docs/pubchem-ligand-SOP.md)。

## 快速開始

不需安裝任何套件（Python ≥ 3.8，只用標準庫）：

```bash
# 先探命中數，不下載
python tools/pubchem-fetch/pubchem_fetch.py --name paxlovid --threshold 95 --dry-run

# 建庫：2D 座標
python tools/pubchem-fetch/pubchem_fetch.py --name paxlovid --threshold 95

# 建庫：3D 座標（供 docking）
python tools/pubchem-fetch/pubchem_fetch.py --name paxlovid --threshold 95 --coord 3d
```

產出落在 `data/paxlovid_like95/`：SDF + 屬性 CSV + manifest JSON。
完整參數與限制見 [tools/pubchem-fetch/README.md](tools/pubchem-fetch/README.md)。

```bash
# 最小可重現測試（驗證仍對得上 SOP 基準）
bash tools/pubchem-fetch/test_minimal.sh
```

## 兩種介面怎麼選

| | 網頁（GitHub Pages） | CLI（pubchem-fetch） |
|---|---|---|
| 適合 | 探索門檻、少量下載、教學演示 | 批次建庫、納入 pipeline |
| 產出 | SDF | SDF + 屬性 CSV + **manifest** |
| 規模 | 數百筆以內 | 無實質上限（內建節流與重試） |

## 專案結構

```
ligand-construct/
├── index.html                      # GitHub Pages：互動式四階段建構器
├── docs/pubchem-ligand-SOP.md      # SOP 全文 + 手動操作↔PUG-REST 對照
├── tools/pubchem-fetch/            # CLI 工具 + 最小測試
└── data/                           # 配體庫輸出（SDF/CSV 不進 repo，manifest 進）
```

## 在 pipeline 中的位置

本專案是 protein-ligand binding affinity pipeline 的**第 0 階段（配體庫準備）**，
輸出的 SDF 直接餵給下游 docking：

```
[ligand-construct] → docking (AutoDock Vina / DiffDock) → rescoring (GNINA)
                   → MD (GROMACS) → free energy (MM-GBSA / FEP)
```

## 注意事項

- PubChem PUG-REST 流量限制：**每秒 5 次請求、每分鐘 400 次**。CLI 已內建 0.25 秒節流
  與退避重試；請勿同時開多個 instance 打同一個 API。
- 相似度由 PubChem 伺服器端的 PubChem Fingerprint 算出，**不可**與 RDKit/Morgan 指紋的
  Tanimoto 值直接互相比較。
- 命中數會隨 PubChem 資料庫成長而緩慢變動（例：SOP 當時 90% 為 743 筆，2026-11 實測 744 筆）。
  所以每份配體庫都要留 manifest 記下當時的 CID 清單。

## 資料來源與授權

化學資料來自 [NCBI PubChem](https://pubchem.ncbi.nlm.nih.gov/)（公眾領域）。
本 repo 程式碼採 MIT 授權。
