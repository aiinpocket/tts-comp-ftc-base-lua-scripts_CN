# 40K 10e 競技模組 — 繁體中文版 (CN Fork)

基於 Hutber 40k Competitive 10e Map Base v1.7.4 (EN v14.2.1) 的繁體中文翻譯版。
原始 repo: [ThePants999/tts-comp-ftc-base-lua-scripts](https://github.com/ThePants999/tts-comp-ftc-base-lua-scripts)

## CN 建構方式

```bash
# 建構 CN JSON（自動注入 Lua、修復 DeckIDs、版本化卡圖 URL、同步 GCP）
python CN/build_cn.py . v1.3

# 部署到 TTS Workshop 目錄
python CN/deploy.py .
```

### 目錄結構

- `TTSLUA/` — Lua 源碼（每個物件一個 `.ttslua` 檔案，以 `-- FTC-GUID:` 標記對應物件）
- `TTSLUA/global.ttslua` — Global 腳本（無 GUID 標記）
- `TTSJSON/ftc_base.json` — 基底 JSON（Lua 欄位為空，由建構腳本注入）
- `CN/` — CN 專屬工具和資源
  - `build_cn.py` — 建構腳本（注入 Lua + XmlUI + 修復 DeckIDs + 卡圖版本化）
  - `deploy.py` — 部署到 TTS
  - `extract_from_json.py` — 從編譯後的 JSON 反向提取源碼
  - `cn_xmlui.xml` — 中文 UI 面板定義
  - `cn_translations.json` — 物件名稱翻譯對照表
- `Compiler/compile.ps1` — 原始 EN 版 PowerShell 編譯器（保留供參考）
- `graphics/` — 卡牌原始圖檔（EN 版參考用）

### 修改工作流程

1. 編輯 `TTSLUA/*.ttslua` 修改 Lua 邏輯
2. 編輯 `CN/cn_xmlui.xml` 修改 UI 面板
3. 編輯 `TTSJSON/ftc_base.json` 修改物件結構（牌組、位置等）
4. 執行 `python CN/build_cn.py . <version>` 建構
5. 執行 `python CN/deploy.py .` 部署測試

### 卡牌圖片管理

卡牌圖片託管於 GCP Storage：`gs://steam-40k/cards/`

**TTS 快取機制**：TTS 根據 URL 做本地快取，同一 URL 不會重新下載。因此 build script 會自動：
1. 將 JSON 中所有 `steam-40k/cards/` URL 改寫為 `steam-40k/cards/<version>/`
2. 在 GCP 上複製圖片到版本化資料夾 `gs://steam-40k/cards/<version>/`
3. 玩家開遊戲時看到新 URL → TTS 重新下載 → 顯示最新圖片

**更新卡片圖片的流程**：
```bash
# 1. 上傳新圖到 GCP 根目錄（覆蓋舊圖）
gcloud storage cp 新卡片.png gs://steam-40k/cards/

# 2. 用新版號 build（自動複製圖片到版本資料夾 + 改寫 URL）
python CN/build_cn.py . v1.4

# 3. 部署
python CN/deploy.py .
```

**注意**：
- 卡圖根目錄 `gs://steam-40k/cards/` 是主版本（master），build 時從這裡複製
- 每個版本的圖片保留在 `gs://steam-40k/cards/v1.3/` 等子目錄，不會自動刪除
- 目前有 79 張中文卡圖（主要/次要/固定次要/部署/挑戰者/巨獸系列）
- 地形佈局卡 (GW/WTC/UKTC Layout) 和卡背仍使用 Steam UGC 原始 URL（純視覺圖無需翻譯）

### CN 版本紀錄

#### v1.3 — 2026-04-11
- 全面中文化所有 UI 文字與遊戲訊息（15 個檔案、200+ 字串）
- build script 自動版本化卡圖 URL 並同步 GCP
- 翻譯涵蓋：開始選單、計分板、骰子桌、棋鐘、桌面控制、軍隊放置、地形匯出等

#### v1.2 — 2026-04-11
- 遷移至源碼驅動工作流程（Lua 腳本獨立檔案 + Python 建構）
- 修復賽前準備面板關閉按鈕
- 修復次要任務卡 DeckIDs 不同步問題（建構時自動修復）

#### v1.1 — 2026-04-10
- 新增階段規則提示面板（射擊造傷表、衝鋒判定等）
- 新增賽前準備 12 步驟引導面板（CA 2025 錦標賽序列）
- 面板可拖曳，不遮擋視野

#### v1.0 — 2026-04-10
- 初次 CA 2025 任務卡中文化校正
- 修正 12 張任務卡規則
- 不留活口移至固定次要任務牌組（10 戰術 + 9 固定 = 19）
- 卡片圖片重新生成上傳

---

## 致謝

- 原始腳本: [ThePants999/tts-comp-ftc-base-lua-scripts](https://github.com/ThePants999/tts-comp-ftc-base-lua-scripts)
- 功能擴充: [Hutber](https://github.com/hutber/hutber-tts) (統計追蹤、雙人模式、任務包系統等)
- 社群貢獻: GenWilhelm, BaconCatBug, Phubar, Mothman_Zack, Zyllos, Kurcenkurce, Trashpanda, Rob Mayer, Gizmo, MoonkeyMod, Liyarin, Josie, FChippendale, Tyrone, MariusEvander, Ziggy, Shinobau
- Discord: https://discord.gg/Drpzcwwmm6

EN 版完整更新歷史請參閱 [原始 repo](https://github.com/ThePants999/tts-comp-ftc-base-lua-scripts#update-history)。
