# CLAUDE.md — TTS 40K CN 模組開發指引

## 專案概述

這是 Warhammer 40K 第十版 Tabletop Simulator (TTS) 競技地圖模組的繁體中文版。
Fork 自 ThePants999 的原始 repo，基於 Hutber 的 v1.7.4 (EN v14.2.1) 分支。

- Steam Workshop ID: `3398190636`
- GitHub: `aiinpocket/tts-comp-ftc-base-lua-scripts_CN`

## 建構流程

```bash
# 建構（注入 Lua + XmlUI + 修復 DeckIDs + 版本化卡圖 URL + 同步 GCP）
python CN/build_cn.py . <version>

# 部署到 TTS Workshop 目錄
python CN/deploy.py .
```

build_cn.py 每次建構會自動執行：
1. 將 `TTSLUA/*.ttslua` 注入 `TTSJSON/ftc_base.json`（按 FTC-GUID 配對）
2. 注入 `CN/cn_xmlui.xml` 到 XmlUI 欄位
3. 同步所有 Deck 的 DeckIDs 與 ContainedObjects（防止 index out of range 錯誤）
4. 將所有 `steam-40k/cards/` URL 改寫為 `steam-40k/cards/<version>/`
5. 在 GCP 上複製卡圖到版本化資料夾 `gs://steam-40k/cards/<version>/`
6. 更新版本號和日期

## 關鍵架構

### 檔案結構
- `TTSLUA/*.ttslua` — 每個 TTS 物件一個 Lua 腳本檔。第一行 `-- FTC-GUID: xxx yyy` 標記對應的物件 GUID。`global.ttslua` 無 GUID 標記。
- `TTSJSON/ftc_base.json` — 基底 JSON，所有已映射物件的 LuaScript 欄位為空（由 build 注入）。27 個地形佈局卡的 LuaScript 保留在 JSON 中（未提取為 .ttslua）。
- `CN/cn_xmlui.xml` — 全域 XML UI 定義（座位選擇、階段面板、賽前引導等）
- `CN/cn_translations.json` — 物件名稱翻譯對照表（參考用，不影響建構）

### 重要物件 GUID
- `738804` — 開始選單 (startMenu.ttslua)，最大的腳本，包含遊戲模式、部署區、任務選擇、階段管理
- `06d627` — 第十版計分板 (10eScoreSheet.ttslua)，管理次要任務卡抽取/回收
- `839fcc`/`acae21` — 骰子桌 (diceTable.ttslua)，紅/藍方
- `32ed4c`/`83ab2a` — 控制面板 (controlBoard.ttslua)，紅/藍方，CN 新增

### XML UI 注意事項
- XML UI 定義在 Global 層級 (`data["XmlUI"]`)
- `onClick` 處理函式必須定義在 **Global 腳本** (`global.ttslua`) 中，不能只在物件腳本中
- 若新增需要 Global 處理的 UI 按鈕，記得在 `global.ttslua` 加入對應函式

### DeckIDs 同步
- TTS 的 Deck 物件有 `DeckIDs` 陣列和 `ContainedObjects` 陣列，兩者必須一致
- build_cn.py 每次建構自動從 ContainedObjects 的 CardID 重建 DeckIDs
- 因此只需維護 ContainedObjects，不需手動管理 DeckIDs

## 卡牌圖片管理

### GCP Storage
- Bucket: `gs://steam-40k/`
- 卡圖根目錄: `gs://steam-40k/cards/` （master 版本，79 張中文卡圖）
- 版本化目錄: `gs://steam-40k/cards/v1.3/` 等（每次 build 自動建立）
- 公開 URL 格式: `https://storage.googleapis.com/steam-40k/cards/<version>/<filename>.png`

### TTS 圖片快取
- TTS 根據 URL 做本地快取，同一 URL 不重新下載
- 因此每次 build 用新版號 → URL 改變 → TTS 重新下載
- 舊版本圖片保留在 GCP 上（不自動刪除）

### 更新卡片圖片
```bash
# 上傳新圖到根目錄（覆蓋舊圖）
gcloud storage cp 新卡片.png gs://steam-40k/cards/

# build 時自動複製到版本資料夾 + 改寫 JSON 中的 URL
python CN/build_cn.py . v1.4
python CN/deploy.py .
```

### 圖片分類
- 已中文化 (steam-40k bucket): 主要任務、次要任務（戰術+固定）、部署卡、挑戰者卡、巨獸系列、參考牆
- 未中文化 (Steam UGC): 地形佈局卡 (GW/WTC/UKTC/Alpine Cup)、卡背、其他視覺元素（無規則文字，不需翻譯）

## 常見問題

### 新增 UI 面板
1. 在 `CN/cn_xmlui.xml` 加入 Panel XML
2. 在 `TTSLUA/global.ttslua` 加入 onClick/show/hide 函式（因為 XML UI 在 Global 層級）
3. 在需要觸發的物件腳本中呼叫 `Global.call("functionName", params)`

### 新增/修改卡牌
1. 在 `TTSJSON/ftc_base.json` 中修改對應 Deck 的 ContainedObjects
2. 不需手動更新 DeckIDs（build 時自動同步）
3. 上傳新卡圖到 `gs://steam-40k/cards/`
4. build 會自動版本化 URL

### 從 TTS 反向提取
如果在 TTS 中直接修改了 mod 並存檔，可以反向提取回源碼：
```bash
cp "Workshop目錄/3398190636_CN.json" cn_source.json
python CN/extract_from_json.py cn_source.json .
```
