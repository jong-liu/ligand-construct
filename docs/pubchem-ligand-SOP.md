# PubChem 配體庫建立與化合物結構篩選操作指南

> 📌 本檔為本專案的**規劃來源文件**（手動操作 SOP）。
> 自動化實作見 `tools/pubchem-fetch/`，互動版見 `index.html`。
> 文中以抗病毒藥物 Paxlovid（主成分 Nirmatrelvir）作為示範標的。

在計算生物學與藥物設計領域中，透過公共資料庫建立高效且具代表性的配體庫（Ligand Library）是進行虛擬篩選（Virtual Screening）與分子對接（Molecular Docking）的關鍵第一步。國家生物技術資訊中心（NCBI）旗下的 PubChem 資料庫提供了龐大的化學物質結構與生物活性數據。本指南詳細解讀運用 PubChem 進行參考化合物檢索、結構相似度門檻設定、SDF 結構檔案下載以及檔案命名管理的標準流程。

## 1. 標的化合物檢索與基本分子資訊識別

建構配體庫的首要步驟是在 PubChem 資料庫中定位目標參考化合物（Query Molecule）。透過 PubChem 官方入口網站進行文字搜尋，能快速獲取化合物的精確識別碼與分子結構特徵。

1. **進入 PubChem 資料庫**：開啟瀏覽器造訪 NCBI PubChem 官方網站（`https://pubchem.ncbi.nlm.nih.gov/`）。
2. **執行化學名檢索**：在首頁中央的搜尋欄中輸入目標化合物名稱 `paxlovid` 並點擊搜尋按鈕。
3. **核對最佳化合物匹配（Best Compound Match）**：系統會自動匹配並顯示主成分 Nirmatrelvir 之詳細化學資料。

在最佳匹配結果中，PubChem 提供了一系列關鍵的化學識別碼與物理化學參數：

| 識別項目 / 參數名稱 | 資料庫記載內容 |
| :--- | :--- |
| **化合物名稱（Compound Name）** | Nirmatrelvir（別名包括 2628280-40-8, PF-07321332, Paxlovid） |
| **PubChem CID** | 155903259 |
| **分子式（Molecular Formula）** | C23H32F3N5O4 |
| **分子量（Molecular Weight）** | 499.5 g/mol |
| **IUPAC 名稱** | (1R,2S,5S)-N-[(1S)-1-cyano-2-[(3S)-2-oxopyrrolidin-3-yl]ethyl]-3-[(2S)-3,3-dimethyl-2-[(2,2,2-trifluoroacetyl)amino]butanoyl]-6,6-dimethyl-3-azabicyclo[3.1.0]hexane-2-carboxamide |
| **SMILES 標記式** | `CC1([C@@H]2[C@@H]1[C@H](N(C2)C(=O)[C@H](C(C)(C)C)NC(=O)C(F)(F)F)C(=O)N[C@@H](C[C@@H]3CCNC3=O)C#N)C` |
| **InChIKey** | LIENCHBZNNMNKG-OJFNHCPVSA-N |
| **資料建立日期（Create Date）** | 2021-05-01 |

確認化學結構與 CID 無誤後，可直接於該化合物頁面中點擊 **Similar Structures Search**（相似結構搜尋）功能，進一步擴充潛在配體候選庫。

## 2. 指紋相似度演算法與 Tanimoto 門檻校正

在藥物化學中，基於「相似結構具有相似生物活性」的原理，利用分子指紋（Fingerprint）進行 2D 相似度搜尋是擴充配體庫的主要手段。PubChem 採用基於 Fingerprint Tanimoto 演算法的二維結構相似性檢索。

當進入 CID 155903259 的結構搜尋介面時，資料庫預設與手動調整的門檻會直接影響篩選出之化合物數量：

1. **預設門檻搜尋**：PubChem 預設的 Tanimoto 門檻（Tanimoto Threshold）為 90%。在此條件下，系統檢索出 743 筆相似化合物結構。
2. **調整相似度設定**：若需要提高配體庫中化學結構的一致性與關聯強度，可點擊頁面上的 **Settings**（設定）按鈕，開啟 Tanimoto Threshold 調節滑桿。
3. **提升門檻至 95%**：將 Tanimoto 門檻由預設的 90% 手動提高至 95%。
4. **結果收斂**：套用 95% 門檻後，篩選結果由原本的 743 筆精確收斂至 281 筆高相似度化合物。

| 相似度類別 | Tanimoto 設定門檻 (%) | 檢索結果化合物數量 | 篩選特徵與用途 |
| :--- | :--- | :--- | :--- |
| **預設相似度（Similarity）** | 90% | 743 | 涵蓋範圍較廣，適用於初步大規模化學空間探索 |
| **高嚴格度相似度（Similarity）** | 95% | 281 | 結構高度相似，適用於建立高特異性小分子配體庫 |

透過提高門檻至 95%，能夠剔除結構差異較大的化合物，確保後續虛擬篩選集中於與 Nirmatrelvir 骨架高度重疊的活性分子。

## 3. 化學結構檔案（SDF）導出與構型參數配置

確定篩選結果（281 筆化合物）後，必須將這些化學結構導出為結構數據檔案（Structure-Data File, SDF），以供第三方分子模擬軟體（如 AutoDock, Discovery Studio, PyMOL 等）進行後續處理。

1. **開啟下載視窗**：在相似結構搜尋結果頁面的右上角，點擊 **Download** 下拉選單。
2. **選擇結構紀錄格式**：在彈出視窗的 **Chemical Structure Records** 區塊中，選擇 **SDF** 格式。
3. **配置構型與維度參數**：
   - **2D 座標（2D Coordinate）**：若僅需平面結構或進行二維指紋比對，選擇 2D 座標，壓縮格式設置為 None 或 GZip。
   - **3D 座標（3D Coordinate）**：若需用於分子對接與三維構型分析，可切換至 3D 座標，並設定構型數量（Number of Conformers，預設通常設為 1）。
4. **執行檔案導出**：確認參數後點擊下載按鈕，瀏覽器將自動下載包含該 281 筆化合物結構的檔案。

| 下載類別 | 可選檔案格式 | 座標維度與設定參數 | 適用情境 |
| :--- | :--- | :--- | :--- |
| **Summary (Search Results)** | CSV, JSON, JSONL, XML | 欄位設定：All (default)；壓縮：None / GZip | 化學屬性數據分析與表格整理 |
| **Chemical Structure Records** | SDF, JSON, XML, ASNT | 2D / 3D 座標（3D 可指定 1 個 Conformer）；壓縮：None / GZip | 分子對接、虛擬篩選與三維模擬 |
| **Chemical Structure Images** | PNG | 圖片尺寸：Small / Large；壓縮：Zip Only | 圖形化展示與報告撰寫 |

在建構配體庫的標準流程中，選擇 Chemical Structure Records 中的 **SDF** 格式是最適切的配置。

## 4. 檔案命名規範與配體庫管理

下載完成後，系統預設的檔案名稱通常為 `PubChem_search_records.sdf`。由於在藥物研發過程中會產生多個不同標的或不同門檻的結構集，建立標準化的檔案命名規範至關重要。

1. **定位下載檔案**：於系統下載資料夾中找到 `PubChem_search_records.sdf`。
2. **執行重新命名**：將檔案名稱修改為 `paxlovid_like95.sdf`。
3. **命名邏輯說明**：
   - `paxlovid`：明確標示參考母核化合物為 Paxlovid（Nirmatrelvir）。
   - `like95`：清晰記錄搜尋採用的 Tanimoto 相似度門檻為 95%。
   - `.sdf`：保持標準化化學結構檔案副檔名。

遵循此命名規範，能確保配體庫檔案具備高可追溯性，防止在多批次數據處理中混淆篩選條件與化合物來源。

## 5. 配體庫建構標準作業流程彙整

| 作業階段 | PubChem UI 操作位置 | 關鍵設定參數 / 動作 | 預期產出與成果 |
| :--- | :--- | :--- | :--- |
| **1. 目標化合物定位** | 首頁搜尋欄 | 輸入 `paxlovid`，檢索 CID 155903259 | 鎖定 Nirmatrelvir 標的結構與分子數據 |
| **2. 相似度篩選與調整** | Similar Structures Search → Settings | Tanimoto Threshold 設定為 95% | 篩選結果精確收斂至 281 筆化合物 |
| **3. 結構檔案下載** | Download 選單 → Chemical Structure Records | 選擇 SDF 格式（可選 2D 或 3D 座標） | 下載 `PubChem_search_records.sdf` |
| **4. 庫檔案歸檔與命名** | 本地檔案系統 / 另存新檔 | 重新命名為 `paxlovid_like95.sdf` | 完成高可追溯性配體庫建立 |

本流程提供了一套完整、可重複且嚴謹的 PubChem 小分子配體庫建構機制，為後續的計算藥物篩選奠定堅實的資料基礎。

---

## 附錄：手動 SOP → PUG-REST 自動化對照

本專案把上述 UI 操作對應到 PubChem PUG-REST API（已於 2026-11-03 實測可用）：

| SOP 階段 | UI 操作 | 對應 PUG-REST 端點 |
| :--- | :--- | :--- |
| 1. 定位 | 首頁搜尋 `paxlovid` | `GET /compound/name/{name}/cids/JSON` |
| 1. 核對 | 化合物頁面屬性表 | `GET /compound/cid/{cid}/property/{props}/CSV` |
| 2. 相似度 | Similar Structures + Settings | `GET /compound/fastsimilarity_2d/cid/{cid}/cids/JSON?Threshold={n}` |
| 3. SDF 導出 | Download → SDF（2D/3D） | `POST /compound/cid/SDF`（body `cid=...`，3D 加 `?record_type=3d`） |
| 4. 命名歸檔 | 手動改檔名 | 程式直接輸出 `<label>_like<門檻>.sdf` + manifest |

> ⚠️ PUG-REST 流量限制：每秒最多 5 次請求、每分鐘最多 400 次。批次下載必須節流。
> ⚠️ 2025 年後 PubChem 已將屬性 `CanonicalSMILES` 更名為 `ConnectivitySMILES`、`IsomericSMILES` 更名為 `SMILES`。
