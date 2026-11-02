# ligand-construct — 專案藍圖

> PubChem 配體庫建構工具。把「手動點網頁」的 SOP 自動化成可重現、可追溯的 CLI + 網頁工具。
> 定位：protein-ligand binding affinity pipeline 的**第 0 階段（配體庫準備）**，產出餵給 docking。

## 對話開始時請先讀
進度與最近更動都在 Obsidian：`2ndbrain/ligand-construct/工作筆記.md`

## 工作模式
- **加新工具/模組**：對 Claude 說「我想做一個 XXX」→ Claude 建 `tools/<名稱>/` 子資料夾並引導
- **結束工作**：對 Claude 說「**收工**」→ 自動 commit + push + 更新 Obsidian 工作筆記
- **接續工作**：對 Claude 說「**開工**」→ 讀工作筆記、報告 git 狀態、建議下一步

## 一桌三櫃
- 🪑 GDrive 工作桌：`G:\我的雲端硬碟\claude\projects\ligand-construct\`（自動跨電腦同步）
- 🐙 GitHub repo：`jong-liu/ligand-construct`（公開）
- 🌐 GitHub Pages：https://jong-liu.github.io/ligand-construct/
- 📘 Obsidian 駕駛艙：`2ndbrain/ligand-construct/工作筆記.md`
- 🔥 Firebase：不使用（本專案不存使用者資料）

## 工具/模組清單
| 模組 | 路徑 | 用途 | 狀態 |
|---|---|---|---|
| pubchem-fetch | `tools/pubchem-fetch/` | 名稱/CID → Tanimoto 相似度搜尋 → SDF + 屬性表 + manifest | ✅ 可用 |
| SOP 網頁 | `index.html` | Pages 上的互動式 SOP 與參數預覽（直打 PUG-REST） | ✅ 可用 |

## 配體庫建構 SOP（四階段，依據 `docs/pubchem-ligand-SOP.md`）
1. **目標化合物定位**：名稱 → CID，核對分子式/MW/SMILES/InChIKey
2. **相似度篩選**：Fingerprint Tanimoto 2D；PubChem 預設門檻 90%，高嚴格度用 95%
3. **結構檔導出**：SDF（2D 用於指紋比對；3D 用於 docking，每化合物 1 conformer）
4. **命名歸檔**：`<母核>_like<門檻>.sdf`（例 `paxlovid_like95.sdf`）+ 同名 manifest 保證可追溯

> 參考基準（Nirmatrelvir, CID 155903259）：Tanimoto 90% → 743 筆；95% → 281 筆。
> 這組數字是**回歸測試基準**，`tools/pubchem-fetch/test_minimal.sh` 會驗證 95% → 281。

## 檔案/資料格式慣例
- 配體庫輸出：SDF（批次）；屬性表：CSV；來源紀錄：`*_manifest.json`
- 輸出一律放 `data/<label>_like<門檻>/`，SDF/CSV 本體不進 repo（見 `.gitignore`），**manifest 要進 repo**
- 下游接 docking（AutoDock Vina / DiffDock），座標需求見 SOP 第 3 階段

## 工作注意事項
- PubChem PUG-REST 有流量限制：**每秒最多 5 次請求**，批次下載務必節流（程式已內建 0.25s 間隔）
- 不要把 SDF/CSV 實體檔 commit 進 repo；靠 manifest 重現即可
- 改動 SOP 階段或門檻預設值時，同步更新本檔第「配體庫建構 SOP」節與 `index.html`
- commit 訊息寫清楚「做了什麼 + 為什麼」
- 機密（API key、token、個資）絕不進 repo

## 開放問題 / Next Steps
- [ ] 加 Lipinski / 自訂屬性過濾（MW、XLogP、HBD/HBA、RotatableBond）成為篩選後處理步驟
- [ ] 3D conformer 缺失化合物的補救（RDKit 本地產構型）
- [ ] 與 docking 階段串接：SDF → 分子分割 → pdbqt 轉換
- [ ] 評估改用 ChEMBL 補充生物活性數據（PubChem 無活性值的化合物）
