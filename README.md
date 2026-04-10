# 40K 10e 競技模組 — 繁體中文版 (CN Fork)

基於 Hutber 40k Competitive 10e Map Base v1.7.4 (EN v14.2.1) 的繁體中文翻譯版。
原始 repo: [ThePants999/tts-comp-ftc-base-lua-scripts](https://github.com/ThePants999/tts-comp-ftc-base-lua-scripts)

## CN 建構方式

```bash
# 建構 CN JSON
python CN/build_cn.py . v1.2

# 部署到 TTS Workshop 目錄
python CN/deploy.py .
```

### 目錄結構

- `TTSLUA/` — Lua 源碼（每個物件一個 `.ttslua` 檔案，以 `-- FTC-GUID:` 標記對應物件）
- `TTSLUA/global.ttslua` — Global 腳本（無 GUID 標記）
- `TTSJSON/ftc_base.json` — 基底 JSON（Lua 欄位為空，由建構腳本注入）
- `CN/` — CN 專屬工具和資源
  - `build_cn.py` — 建構腳本（注入 Lua + XmlUI + 修復 DeckIDs）
  - `deploy.py` — 部署到 TTS
  - `extract_from_json.py` — 從編譯後的 JSON 反向提取源碼
  - `cn_xmlui.xml` — 中文 UI 面板定義
  - `cn_translations.json` — 物件名稱翻譯對照表
- `Compiler/compile.ps1` — 原始 EN 版 PowerShell 編譯器（保留供參考）

### 修改工作流程

1. 編輯 `TTSLUA/*.ttslua` 修改 Lua 邏輯
2. 編輯 `CN/cn_xmlui.xml` 修改 UI 面板
3. 編輯 `TTSJSON/ftc_base.json` 修改物件結構（牌組、位置等）
4. 執行 `python CN/build_cn.py . <version>` 建構
5. 執行 `python CN/deploy.py .` 部署測試

### CN 版本紀錄

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
