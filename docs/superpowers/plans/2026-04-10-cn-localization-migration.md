# TTS 40K CN Localization Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the CN mod from "patch a monolithic 22MB JSON" to a source-driven workflow where Lua scripts live in separate `.ttslua` files, a Python build script handles CN-specific transforms (translations, deck fixes, XML UI injection), and a single `build_cn.py` produces the final `3398190636_CN.json`.

**Architecture:** The EN repo (`ThePants999/tts-comp-ftc-base-lua-scripts`) provides the base JSON + compiler structure. However, the CN mod is based on **Hutber's fork v1.7.4 (EN v14.2.1)**, which adds massive features not in the ThePants999 repo (stats tracking, doubles mode, mission packs, control boards, etc.). Our strategy is:
1. Extract current CN JSON's state as the new baseline (not the EN repo's outdated sources)
2. Reuse the repo's directory structure (TTSLUA/, TTSJSON/, Compiler/)
3. Replace the EN `.ttslua` files with extracted CN versions
4. Build a `cn_patch.py` that handles non-Lua transforms (translations, decks, XML UI, new objects)
5. Create a `build_cn.py` orchestrator that chains: base JSON -> Lua injection -> CN patches -> output

**Tech Stack:** Python 3, PowerShell (existing compiler), JSON, Lua (TTS scripting)

**Key files reference:**
- Current CN JSON: `../3398190636_CN.json` (the working mod, 203 objects, 49K lines)
- EN base JSON: `TTSJSON/ftc_base.json` (v2.65, 222 objects — NOT the same version as CN base)
- EN Lua sources: `TTSLUA/*.ttslua` (25 files, 363-2064 lines each)
- EN compiler: `Compiler/compile.ps1`

---

## File Structure

```
tts-comp-ftc-base-lua-scripts_CN/
├── TTSJSON/
│   ├── ftc_base.json              (REPLACE: extract from CN JSON, Lua fields emptied)
│   └── ftc_base_original_en.json  (KEEP: rename current EN base for reference)
├── TTSLUA/
│   ├── global.ttslua              (REPLACE: extract CN Global LuaScript)
│   ├── startMenu.ttslua           (REPLACE: extract CN GUID 738804 LuaScript)
│   ├── 10eScoreSheet.ttslua       (REPLACE: extract CN GUID 06d627 LuaScript)
│   ├── diceTable.ttslua           (REPLACE: extract CN GUID c57d70/a84ed2 — note: CN uses different GUIDs 839fcc/acae21)
│   ├── ... (all other existing .ttslua files: replace with CN versions)
│   ├── controlBoard.ttslua        (NEW: CN-only, GUID 32ed4c/83ab2a)
│   ├── statsHelper.ttslua         (NEW: CN-only, GUID 7c7c20/b7ac7a)
│   ├── selectionHighlighter.ttslua (NEW: CN-only, GUID 27de4f/84c3a4)
│   └── tokenCounter.ttslua        (NEW: CN-only, GUID 42c164/42c161)
├── CN/
│   ├── build_cn.py                (NEW: orchestrator — runs compile then patches)
│   ├── extract_from_json.py       (NEW: extracts base JSON + Lua files from CN JSON)
│   ├── cn_translations.json       (NEW: object nickname/description translations)
│   ├── cn_xmlui.xml               (NEW: CN XmlUI as standalone file)
│   ├── cn_deck_fixes.py           (NEW: DeckIDs sync, deck restructuring)
│   └── cn_new_objects.json        (NEW: CN-only objects not in base JSON)
├── Compiler/
│   └── compile.ps1                (KEEP: original EN compiler, used as reference)
├── docs/
│   └── superpowers/plans/
│       └── 2026-04-10-cn-localization-migration.md (this file)
└── graphics/
    └── ca2025_cn/                 (NEW: CN card images if needed)
```

---

## Task 0: Backup and Branch Setup

**Files:**
- Repository root

- [ ] **Step 1: Create working branch**

```bash
cd "C:\Users\user\Documents\My Games\Tabletop Simulator\Mods\Workshop\tts-comp-ftc-base-lua-scripts_CN"
git checkout -b cn-migration
```

- [ ] **Step 2: Backup current EN base files**

```bash
cp TTSJSON/ftc_base.json TTSJSON/ftc_base_original_en.json
git add TTSJSON/ftc_base_original_en.json
git commit -m "chore: backup original EN base JSON for reference"
```

- [ ] **Step 3: Copy CN JSON into repo for extraction**

```bash
cp "../3398190636_CN.json" ./cn_source.json
```

(This is a temporary working file, will be gitignored after extraction.)

- [ ] **Step 4: Update .gitignore**

Add to `.gitignore`:
```
*_compiled.json
cn_source.json
__pycache__/
*.pyc
```

```bash
git add .gitignore
git commit -m "chore: update gitignore for CN build artifacts"
```

---

## Task 1: Build the Extraction Script (`CN/extract_from_json.py`)

**Files:**
- Create: `CN/extract_from_json.py`

This script reads the CN JSON and produces:
1. A base JSON with all `LuaScript` fields emptied (-> `TTSJSON/ftc_base.json`)
2. Individual `.ttslua` files for each scripted object (-> `TTSLUA/`)
3. The XmlUI as a standalone file (-> `CN/cn_xmlui.xml`)
4. A translations mapping file (-> `CN/cn_translations.json`)
5. A list of CN-only objects (-> `CN/cn_new_objects.json`)

- [ ] **Step 1: Create the CN directory**

```bash
mkdir -p CN
```

- [ ] **Step 2: Write extract_from_json.py**

```python
#!/usr/bin/env python3
"""Extract base JSON, Lua scripts, XmlUI, and translations from a compiled CN TTS JSON."""

import json
import os
import re
import sys

# --- Configuration ---
# Map of GUID -> .ttslua filename (based on original EN repo naming)
# Objects with the same script share one file; first GUID listed is canonical.
GUID_TO_FILE = {
    # Original EN objects (keep same filenames)
    "06d627": "10eScoreSheet.ttslua",
    "51ee2f": "3SearchAndDestroy.ttslua",
    "5549a7": "40kItems.ttslua",
    "8b7aa6": "armyPlacer.ttslua",
    "d618cb": "blankObjectiveCard.ttslua",
    "f4ee71": "chessClock.ttslua",
    "1fcbf0": "clock.ttslua",
    "573333": "customTile.ttslua",  # multi-GUID: 573333,764a2e,6d45cf,33e32b,f32864,a91751
    "70b9f6": "extractTerrain.ttslua",
    "bd69bd": "flexTableControl.ttslua",
    "ee92cf": "gameRounds.ttslua",
    "5c328f": "injectionDetector.ttslua",
    "4ee1f2": "matObjSurface.ttslua",
    "c5e288": "matUrl.ttslua",
    "471de1": "missionManager.ttslua",   # multi-GUID: 471de1,cff35b
    "cff35b": "missionManager.ttslua",
    "a76485": "spawnGameTools.ttslua",
    "229946": "squadActivation.ttslua",   # multi-GUID: 229946,bcf2a4,37e995
    "bcf2a4": "squadActivation.ttslua",
    "37e995": "squadActivation.ttslua",
    "738804": "startMenu.ttslua",
    "2671c8": "timer.ttslua",
    "7e4111": "turns.ttslua",             # multi-GUID: 7e4111,055302
    "055302": "turns.ttslua",
    "ad63ba": "woundsRemaining.ttslua",   # multi-GUID: ad63ba,2e4f26,5fd19f
    "2e4f26": "woundsRemaining.ttslua",
    "5fd19f": "woundsRemaining.ttslua",
    # CN dice tables use different GUIDs than EN
    "839fcc": "diceTable.ttslua",         # CN blue dice table
    "acae21": "diceTable.ttslua",         # CN red dice table
    "c57d70": "diceTable.ttslua",         # EN red dice table (if present)
    "a84ed2": "diceTable.ttslua",         # EN blue dice table (if present)
    # CN dice rollers
    "17ca2b": "kustom40kDiceRollerMk3.ttslua",
    "927ca1": "kustom40kDiceRollerMk3.ttslua",
    "4e0e0b": "kustom40kDiceRollerMk3.ttslua",
    "beae28": "kustom40kDiceRollerMk3.ttslua",
    # CN-only objects
    "32ed4c": "controlBoard.ttslua",      # Red control board
    "83ab2a": "controlBoard.ttslua",      # Blue control board
    "7c7c20": "statsHelper.ttslua",       # Red stats helper
    "b7ac7a": "statsHelper.ttslua",       # Blue stats helper
    "27de4f": "selectionHighlighter.ttslua",
    "84c3a4": "selectionHighlighter.ttslua",
    "42c164": "tokenCounter.ttslua",
    "42c161": "tokenCounter.ttslua",
}

# Multi-GUID files: which GUIDs share the same script
MULTI_GUID = {
    "customTile.ttslua": ["573333", "764a2e", "6d45cf", "33e32b", "f32864", "a91751"],
    "missionManager.ttslua": ["471de1", "cff35b"],
    "squadActivation.ttslua": ["229946", "bcf2a4", "37e995"],
    "turns.ttslua": ["7e4111", "055302"],
    "woundsRemaining.ttslua": ["ad63ba", "2e4f26", "5fd19f"],
    "diceTable.ttslua": ["839fcc", "acae21"],
    "kustom40kDiceRollerMk3.ttslua": ["17ca2b", "927ca1"],
    "controlBoard.ttslua": ["32ed4c", "83ab2a"],
    "statsHelper.ttslua": ["7c7c20", "b7ac7a"],
    "selectionHighlighter.ttslua": ["27de4f", "84c3a4"],
    "tokenCounter.ttslua": ["42c164", "42c161"],
}


def extract(cn_json_path, repo_root):
    with open(cn_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ttslua_dir = os.path.join(repo_root, "TTSLUA")
    ttsjson_dir = os.path.join(repo_root, "TTSJSON")
    cn_dir = os.path.join(repo_root, "CN")
    os.makedirs(ttslua_dir, exist_ok=True)
    os.makedirs(ttsjson_dir, exist_ok=True)
    os.makedirs(cn_dir, exist_ok=True)

    # --- 1. Extract Global LuaScript ---
    global_lua = data.get("LuaScript", "")
    with open(os.path.join(ttslua_dir, "global.ttslua"), "w", encoding="utf-8") as f:
        f.write(global_lua)
    print(f"  Extracted global.ttslua ({len(global_lua)} chars)")
    data["LuaScript"] = ""

    # --- 2. Extract XmlUI ---
    xmlui = data.get("XmlUI", "")
    with open(os.path.join(cn_dir, "cn_xmlui.xml"), "w", encoding="utf-8") as f:
        f.write(xmlui)
    print(f"  Extracted cn_xmlui.xml ({len(xmlui)} chars)")

    # --- 3. Extract per-object Lua scripts and translations ---
    translations = {}
    written_files = set()
    unmatched_scripts = []

    for i, obj in enumerate(data.get("ObjectStates", [])):
        guid = obj.get("GUID", "")
        lua = obj.get("LuaScript", "")
        nickname = obj.get("Nickname", "")
        name = obj.get("Name", "")

        # Record translation if nickname has Chinese characters
        if nickname and re.search(r'[\u4e00-\u9fff]', nickname):
            translations[guid] = {
                "Name": name,
                "Nickname": nickname,
                "Description": obj.get("Description", "")[:200]
            }

        # Extract Lua script
        if lua and len(lua) > 10:
            filename = GUID_TO_FILE.get(guid)
            if filename:
                if filename not in written_files:
                    # Build FTC-GUID header
                    guids_for_file = MULTI_GUID.get(filename, [guid])
                    guid_line = "-- FTC-GUID: " + " ".join(guids_for_file)
                    filepath = os.path.join(ttslua_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        # Only prepend GUID line if not global
                        f.write(guid_line + "\n")
                        f.write(lua)
                    written_files.add(filename)
                    print(f"  Extracted {filename} (GUID {guid}, {len(lua)} chars)")
            else:
                unmatched_scripts.append({
                    "index": i,
                    "GUID": guid,
                    "Name": name,
                    "Nickname": nickname,
                    "LuaScript_length": len(lua)
                })

            # Clear LuaScript in base JSON
            obj["LuaScript"] = ""

        # Also process contained objects (nested)
        _extract_nested_translations(obj, translations)

    # --- 4. Save translations ---
    with open(os.path.join(cn_dir, "cn_translations.json"), "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    print(f"  Extracted cn_translations.json ({len(translations)} entries)")

    # --- 5. Save base JSON (Lua emptied) ---
    with open(os.path.join(ttsjson_dir, "ftc_base.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved ftc_base.json (Lua fields emptied)")

    # --- 6. Report unmatched ---
    if unmatched_scripts:
        print(f"\n  WARNING: {len(unmatched_scripts)} objects with scripts not in GUID_TO_FILE:")
        for u in unmatched_scripts:
            print(f"    GUID={u['GUID']} Name={u['Name']} Nickname={u['Nickname']} Lua={u['LuaScript_length']} chars")
        with open(os.path.join(cn_dir, "unmatched_scripts.json"), "w", encoding="utf-8") as f:
            json.dump(unmatched_scripts, f, ensure_ascii=False, indent=2)


def _extract_nested_translations(obj, translations):
    """Recurse into ContainedObjects to capture card translations."""
    for co in obj.get("ContainedObjects", []):
        guid = co.get("GUID", "")
        nickname = co.get("Nickname", "")
        if nickname and re.search(r'[\u4e00-\u9fff]', nickname):
            translations[guid] = {
                "Name": co.get("Name", ""),
                "Nickname": nickname,
                "Description": co.get("Description", "")[:200]
            }
        _extract_nested_translations(co, translations)


if __name__ == "__main__":
    cn_json = sys.argv[1] if len(sys.argv) > 1 else "cn_source.json"
    repo_root = sys.argv[2] if len(sys.argv) > 2 else "."
    print(f"Extracting from {cn_json} into {repo_root}...")
    extract(cn_json, repo_root)
    print("\nDone! Review unmatched_scripts.json for objects needing GUID_TO_FILE mapping.")
```

- [ ] **Step 3: Run extraction**

```bash
cd "C:\Users\user\Documents\My Games\Tabletop Simulator\Mods\Workshop\tts-comp-ftc-base-lua-scripts_CN"
python3 CN/extract_from_json.py cn_source.json .
```

Expected output: list of extracted files, possible warnings about unmatched scripts.

- [ ] **Step 4: Review unmatched scripts**

Check `CN/unmatched_scripts.json`. For each unmatched object:
- If it has significant Lua (>100 chars), add its GUID to `GUID_TO_FILE` in the script and re-run
- If it's a map layout card with embedded terrain-spawning Lua, these stay in the base JSON (they're data, not logic)

- [ ] **Step 5: Verify extraction quality**

```bash
# Check that all key .ttslua files were created
ls -la TTSLUA/*.ttslua | wc -l
# Should be ~29+ files (25 original + 4 new CN-only)

# Check base JSON has empty LuaScript fields
python3 -c "
import json
with open('TTSJSON/ftc_base.json','r',encoding='utf-8') as f:
    d=json.load(f)
scripts = [o for o in d['ObjectStates'] if o.get('LuaScript','').strip()]
print(f'Objects with non-empty LuaScript: {len(scripts)}')
print(f'Global LuaScript empty: {d[\"LuaScript\"]==\"\"}')
"
```

Expected: 0 objects with non-empty LuaScript (except map layout cards if we chose to keep them), Global LuaScript empty = True.

- [ ] **Step 6: Commit extraction results**

```bash
git add TTSLUA/ TTSJSON/ftc_base.json CN/extract_from_json.py CN/cn_xmlui.xml CN/cn_translations.json
git commit -m "feat: extract CN mod into source file structure

- Replace EN .ttslua files with CN versions (Hutber v1.7.4 base + CN additions)
- Replace ftc_base.json with CN base (203 objects, Lua fields emptied)
- Extract XmlUI to CN/cn_xmlui.xml
- Extract translations to CN/cn_translations.json
- Add CN-only object scripts: controlBoard, statsHelper, selectionHighlighter, tokenCounter"
```

---

## Task 2: Build the CN Compile Script (`CN/build_cn.py`)

**Files:**
- Create: `CN/build_cn.py`

This replaces the PowerShell compiler with a Python version that also handles CN-specific transforms.

- [ ] **Step 1: Write build_cn.py**

```python
#!/usr/bin/env python3
"""
Build the CN TTS JSON from source files.

Pipeline:
1. Load base JSON (TTSJSON/ftc_base.json)
2. Inject Lua scripts from TTSLUA/*.ttslua (matching by FTC-GUID)
3. Inject XmlUI from CN/cn_xmlui.xml
4. Fix deck structures (sync DeckIDs with ContainedObjects)
5. Write output JSON
"""

import json
import os
import re
import sys
import glob
import copy
from datetime import datetime


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_ttslua_files(ttslua_dir):
    """Parse all .ttslua files, return {guid: lua_content} mapping."""
    guid_to_lua = {}
    global_lua = None

    for filepath in glob.glob(os.path.join(ttslua_dir, "*.ttslua")):
        filename = os.path.basename(filepath)
        content = load_text(filepath)

        if filename == "global.ttslua":
            global_lua = content
            continue

        # Parse FTC-GUID from first line
        first_line = content.split("\n", 1)[0]
        guids = re.findall(r'[0-9a-f]{6}', first_line)
        if not guids:
            print(f"  WARNING: No GUIDs found in {filename}, skipping")
            continue

        # Remove the FTC-GUID header line from the script content
        lua_body = content.split("\n", 1)[1] if "\n" in content else ""

        for guid in guids:
            guid_to_lua[guid] = lua_body
            print(f"  Mapped {guid} -> {filename}")

    return global_lua, guid_to_lua


def inject_lua(data, global_lua, guid_to_lua):
    """Inject Lua scripts into the JSON structure."""
    if global_lua:
        data["LuaScript"] = global_lua
        print(f"  Injected Global LuaScript ({len(global_lua)} chars)")

    injected = 0
    for obj in data.get("ObjectStates", []):
        guid = obj.get("GUID", "")
        if guid in guid_to_lua:
            obj["LuaScript"] = guid_to_lua[guid]
            injected += 1

    print(f"  Injected Lua into {injected} objects")


def inject_xmlui(data, xmlui_path):
    """Replace XmlUI with CN version."""
    if os.path.exists(xmlui_path):
        data["XmlUI"] = load_text(xmlui_path)
        print(f"  Injected XmlUI ({len(data['XmlUI'])} chars)")


def fix_deck_ids(data):
    """Ensure every Deck's DeckIDs matches its ContainedObjects CardIDs."""
    fixed = 0
    for obj in data.get("ObjectStates", []):
        if obj.get("Name") == "Deck" or obj.get("Name") == "DeckCustom":
            contained = obj.get("ContainedObjects", [])
            card_ids = [co.get("CardID") for co in contained if co.get("CardID") is not None]
            old_ids = obj.get("DeckIDs", [])
            if set(old_ids) != set(card_ids) or len(old_ids) != len(card_ids):
                obj["DeckIDs"] = card_ids
                nickname = obj.get("Nickname", obj.get("GUID", "?"))
                print(f"  Fixed DeckIDs for '{nickname}': {len(old_ids)} -> {len(card_ids)}")
                fixed += 1
    if fixed == 0:
        print("  All deck DeckIDs already consistent")


def update_metadata(data, version):
    """Update version metadata."""
    data["VersionNumber"] = f"EN v14.2.1 / CN {version}"
    data["Date"] = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(f"  Updated version to CN {version}")


def build(repo_root, version="v1.2", output_path=None):
    print("=" * 60)
    print(f"Building CN TTS JSON — {version}")
    print("=" * 60)

    ttsjson_dir = os.path.join(repo_root, "TTSJSON")
    ttslua_dir = os.path.join(repo_root, "TTSLUA")
    cn_dir = os.path.join(repo_root, "CN")

    # 1. Load base JSON
    print("\n[1/5] Loading base JSON...")
    data = load_json(os.path.join(ttsjson_dir, "ftc_base.json"))
    print(f"  Loaded: {len(data.get('ObjectStates', []))} objects")

    # 2. Inject Lua scripts
    print("\n[2/5] Injecting Lua scripts...")
    global_lua, guid_to_lua = parse_ttslua_files(ttslua_dir)
    inject_lua(data, global_lua, guid_to_lua)

    # 3. Inject XmlUI
    print("\n[3/5] Injecting XmlUI...")
    inject_xmlui(data, os.path.join(cn_dir, "cn_xmlui.xml"))

    # 4. Fix deck structures
    print("\n[4/5] Fixing deck structures...")
    fix_deck_ids(data)

    # 5. Update metadata and save
    print("\n[5/5] Saving output...")
    update_metadata(data, version)

    if output_path is None:
        output_path = os.path.join(repo_root, f"ftc_base_{version}_compiled.json")
    save_json(data, output_path)
    print(f"\n  Output: {output_path}")
    print(f"  Size: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
    print("\nBuild complete!")


if __name__ == "__main__":
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    version = sys.argv[2] if len(sys.argv) > 2 else "v1.2"
    output = sys.argv[3] if len(sys.argv) > 3 else None
    build(repo_root, version, output)
```

- [ ] **Step 2: Test the build**

```bash
cd "C:\Users\user\Documents\My Games\Tabletop Simulator\Mods\Workshop\tts-comp-ftc-base-lua-scripts_CN"
python3 CN/build_cn.py . v1.2-test
```

Expected: build completes with all Lua injected, DeckIDs consistent, output file produced.

- [ ] **Step 3: Validate output matches original**

```bash
python3 -c "
import json
with open('ftc_base_v1.2-test_compiled.json','r',encoding='utf-8') as f:
    new = json.load(f)
with open('cn_source.json','r',encoding='utf-8') as f:
    old = json.load(f)

# Compare Global LuaScript length
print(f'Global Lua: old={len(old[\"LuaScript\"])} new={len(new[\"LuaScript\"])}')

# Compare scripted objects
for i, (o, n) in enumerate(zip(old['ObjectStates'], new['ObjectStates'])):
    ol = len(o.get('LuaScript',''))
    nl = len(n.get('LuaScript',''))
    if ol > 10 and nl == 0:
        print(f'  MISSING script: [{i}] {o.get(\"Nickname\",o.get(\"Name\",\"?\"))} GUID={o.get(\"GUID\",\"?\")} ({ol} chars)')
    elif abs(ol - nl) > 50 and ol > 10:
        print(f'  DIFF: [{i}] {o.get(\"Nickname\",\"?\")} old={ol} new={nl}')

# Compare deck integrity
for o in new['ObjectStates']:
    if o.get('Name') in ('Deck','DeckCustom'):
        ids = len(o.get('DeckIDs',[]))
        cos = len(o.get('ContainedObjects',[]))
        if ids != cos:
            print(f'  DECK MISMATCH: {o.get(\"Nickname\",\"?\")} DeckIDs={ids} Contained={cos}')

print('Validation complete.')
"
```

Expected: no MISSING scripts for key objects, no DECK MISMATCH, small diffs are OK (FTC-GUID header line adds ~30 chars).

- [ ] **Step 4: Commit build script**

```bash
git add CN/build_cn.py
git commit -m "feat: add Python build script for CN mod

Replaces PowerShell compiler with Python pipeline:
- Lua injection by FTC-GUID matching
- XmlUI injection from standalone file
- Automatic DeckIDs sync with ContainedObjects
- Version metadata stamping"
```

---

## Task 3: Fix Known Bugs in Source Files

**Files:**
- Modify: `TTSLUA/global.ttslua`
- Modify: `TTSLUA/startMenu.ttslua`

Fix the two bugs we already identified, now in the source files.

- [ ] **Step 1: Add closePregamePanel to global.ttslua**

Append to end of `TTSLUA/global.ttslua`:

```lua
-- === CN Pregame Panel close handler (Global) ===
function closePregamePanel()
    UI.setAttribute("pregamePanel", "active", "false")
end
```

- [ ] **Step 2: Remove duplicate showPregameGuide from startMenu.ttslua**

In `TTSLUA/startMenu.ttslua`, find the `writeStartMenu` function and remove the `showPregameGuide()` call:

Before:
```lua
function writeStartMenu()
    if gameMode ~= "game" then return end
    self.createButton(startBtn)
    self.createButton(firstPlayerBtn)
    showPregameGuide()
end
```

After:
```lua
function writeStartMenu()
    if gameMode ~= "game" then return end
    self.createButton(startBtn)
    self.createButton(firstPlayerBtn)
end
```

- [ ] **Step 3: Rebuild and verify**

```bash
python3 CN/build_cn.py . v1.2-bugfix
```

- [ ] **Step 4: Commit bugfixes**

```bash
git add TTSLUA/global.ttslua TTSLUA/startMenu.ttslua
git commit -m "fix: pregame panel close button and duplicate showPregameGuide

- Add closePregamePanel() to Global script (was only in object script,
  but XML UI onClick targets Global)
- Remove duplicate showPregameGuide() call from writeStartMenu()
  (already called in confirmSizeGame)"
```

---

## Task 4: Create Deploy-to-TTS Helper

**Files:**
- Create: `CN/deploy.py`

Quick script to copy the compiled output to the TTS Workshop directory for testing.

- [ ] **Step 1: Write deploy.py**

```python
#!/usr/bin/env python3
"""Copy compiled CN JSON to TTS Workshop directory for testing."""

import shutil
import sys
import os
import glob

def deploy(repo_root="."):
    # Find most recent compiled file
    pattern = os.path.join(repo_root, "ftc_base_*_compiled.json")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        print("No compiled JSON found. Run build_cn.py first.")
        sys.exit(1)

    source = files[0]
    docs = os.path.expanduser("~")
    tts_workshop = os.path.join(docs, "Documents", "My Games",
                                "Tabletop Simulator", "Mods", "Workshop")
    dest = os.path.join(tts_workshop, "3398190636_CN.json")

    print(f"Deploying: {os.path.basename(source)}")
    print(f"  -> {dest}")
    shutil.copy2(source, dest)
    print("Done! Restart TTS or reload the mod to see changes.")


if __name__ == "__main__":
    deploy(sys.argv[1] if len(sys.argv) > 1 else ".")
```

- [ ] **Step 2: Commit**

```bash
git add CN/deploy.py
git commit -m "feat: add deploy script to copy compiled JSON to TTS Workshop"
```

---

## Task 5: Verify Full Round-Trip

**Files:**
- No new files; validation only

- [ ] **Step 1: Full build**

```bash
cd "C:\Users\user\Documents\My Games\Tabletop Simulator\Mods\Workshop\tts-comp-ftc-base-lua-scripts_CN"
python3 CN/build_cn.py . v1.2
```

- [ ] **Step 2: Deploy and test in TTS**

```bash
python3 CN/deploy.py .
```

Then open TTS and verify:
1. Mod loads without errors in console
2. Pregame guide panel appears and can be closed with the X button
3. Secondary mission cards can be drawn without index errors
4. Phase guide panel shows correct Chinese text
5. All buttons and menus function correctly

- [ ] **Step 3: Push to GitHub**

```bash
git push origin cn-migration
```

---

## Task 6: Clean Up and Document

**Files:**
- Modify: `README.md`
- Remove: `cn_source.json` (temporary)

- [ ] **Step 1: Remove temporary source file**

```bash
rm cn_source.json
```

- [ ] **Step 2: Update README.md**

Add a CN section to README:

```markdown
## CN (繁體中文) 版本

基於 Hutber 40k Competitive 10e Map Base v1.7.4 (EN v14.2.1) 的繁體中文翻譯版。

### 建構方式

```bash
# 首次設置
pip install json  # (標準庫，不需安裝)

# 建構 CN JSON
python CN/build_cn.py . v1.2

# 部署到 TTS
python CN/deploy.py .
```

### 目錄結構

- `TTSLUA/` — Lua 源碼（每個物件一個 `.ttslua` 檔案）
- `TTSJSON/ftc_base.json` — 基底 JSON（Lua 欄位為空，由建構腳本注入）
- `CN/` — CN 專屬工具和資源
  - `build_cn.py` — 建構腳本
  - `deploy.py` — 部署到 TTS
  - `extract_from_json.py` — 從編譯後的 JSON 反向提取
  - `cn_xmlui.xml` — 中文 UI 面板定義
  - `cn_translations.json` — 物件名稱翻譯對照表

### 修改工作流程

1. 編輯 `TTSLUA/*.ttslua` 修改 Lua 邏輯
2. 編輯 `CN/cn_xmlui.xml` 修改 UI 面板
3. 編輯 `TTSJSON/ftc_base.json` 修改物件結構（牌組、位置等）
4. 執行 `python CN/build_cn.py . <version>` 建構
5. 執行 `python CN/deploy.py .` 部署測試
```

- [ ] **Step 3: Commit and push**

```bash
git add README.md .gitignore
git rm --cached cn_source.json 2>/dev/null || true
git commit -m "docs: add CN build instructions to README"
git push origin cn-migration
```

---

## Summary of What This Achieves

| Before | After |
|--------|-------|
| Edit Lua inside 22MB JSON | Edit separate `.ttslua` files |
| Manual DeckIDs sync (error-prone) | `fix_deck_ids()` auto-syncs every build |
| Global function placement bugs | All Global functions in one `global.ttslua` |
| No version control on changes | Full git diff on every script |
| No build reproducibility | `python CN/build_cn.py . v1.3` from clean state |
| XML UI changes in escaped JSON | Edit `cn_xmlui.xml` as normal XML |
