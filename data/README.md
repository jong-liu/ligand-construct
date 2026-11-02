# data/ — 配體庫輸出目錄

每次建庫在此產生一個子資料夾 `<label>_like<門檻>/`，內含三個檔：

| 檔案 | 進 repo？ | 說明 |
|---|---|---|
| `*_manifest.json` | ✅ 要 | 查詢條件、門檻、命中數、完整 CID 清單、產生時間 |
| `*.sdf` | ❌ 不要 | 配體庫本體，體積大，可由 manifest 重現 |
| `*_properties.csv` | ❌ 不要 | 屬性表，同樣可重現 |

SDF/CSV 已在 `.gitignore` 排除。要重現某份配體庫，拿它的 manifest 看 `query.cid` 與
`search.threshold_percent`，重跑一次 CLI 即可；CID 清單還能用來核對資料庫成長造成的差異。
