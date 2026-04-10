#!/usr/bin/env python3
"""Extract base JSON, Lua scripts, XmlUI, and translations from a compiled CN TTS JSON."""

import json
import os
import re
import sys

GUID_TO_FILE = {
    "06d627": "10eScoreSheet.ttslua",
    "51ee2f": "3SearchAndDestroy.ttslua",
    "5549a7": "40kItems.ttslua",
    "8b7aa6": "armyPlacer.ttslua",
    "d618cb": "blankObjectiveCard.ttslua",
    "f4ee71": "chessClock.ttslua",
    "1fcbf0": "clock.ttslua",
    "573333": "customTile.ttslua",
    "70b9f6": "extractTerrain.ttslua",
    "bd69bd": "flexTableControl.ttslua",
    "ee92cf": "gameRounds.ttslua",
    "5c328f": "injectionDetector.ttslua",
    "4ee1f2": "matObjSurface.ttslua",
    "c5e288": "matUrl.ttslua",
    "471de1": "missionManager.ttslua",
    "cff35b": "missionManager.ttslua",
    "a76485": "spawnGameTools.ttslua",
    "229946": "squadActivation.ttslua",
    "bcf2a4": "squadActivation.ttslua",
    "37e995": "squadActivation.ttslua",
    "738804": "startMenu.ttslua",
    "2671c8": "timer.ttslua",
    "7e4111": "turns.ttslua",
    "055302": "turns.ttslua",
    "ad63ba": "woundsRemaining.ttslua",
    "2e4f26": "woundsRemaining.ttslua",
    "5fd19f": "woundsRemaining.ttslua",
    "839fcc": "diceTable.ttslua",
    "acae21": "diceTable.ttslua",
    "c57d70": "diceTable.ttslua",
    "a84ed2": "diceTable.ttslua",
    "17ca2b": "kustom40kDiceRollerMk3.ttslua",
    "927ca1": "kustom40kDiceRollerMk3.ttslua",
    "4e0e0b": "kustom40kDiceRollerMk3.ttslua",
    "beae28": "kustom40kDiceRollerMk3.ttslua",
    "32ed4c": "controlBoard.ttslua",
    "83ab2a": "controlBoard.ttslua",
    "7c7c20": "statsHelper.ttslua",
    "b7ac7a": "statsHelper.ttslua",
    "27de4f": "selectionHighlighter.ttslua",
    "84c3a4": "selectionHighlighter.ttslua",
    "42c164": "tokenCounter.ttslua",
    "42c161": "tokenCounter.ttslua",
}

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

    # 1. Extract Global LuaScript (no FTC-GUID header)
    global_lua = data.get("LuaScript", "")
    with open(os.path.join(ttslua_dir, "global.ttslua"), "w", encoding="utf-8") as f:
        f.write(global_lua)
    print(f"  Extracted global.ttslua ({len(global_lua)} chars)")
    data["LuaScript"] = ""

    # 2. Extract XmlUI
    xmlui = data.get("XmlUI", "")
    with open(os.path.join(cn_dir, "cn_xmlui.xml"), "w", encoding="utf-8") as f:
        f.write(xmlui)
    print(f"  Extracted cn_xmlui.xml ({len(xmlui)} chars)")

    # 3. Extract per-object Lua scripts and translations
    translations = {}
    written_files = set()
    unmatched_scripts = []

    for i, obj in enumerate(data.get("ObjectStates", [])):
        guid = obj.get("GUID", "")
        lua = obj.get("LuaScript", "")
        nickname = obj.get("Nickname", "")
        name = obj.get("Name", "")

        if nickname and re.search(r'[\u4e00-\u9fff]', nickname):
            translations[guid] = {
                "Name": name,
                "Nickname": nickname,
                "Description": obj.get("Description", "")[:200]
            }

        if lua and len(lua) > 10:
            filename = GUID_TO_FILE.get(guid)
            if filename:
                if filename not in written_files:
                    guids_for_file = MULTI_GUID.get(filename, [guid])
                    guid_line = "-- FTC-GUID: " + " ".join(guids_for_file)
                    filepath = os.path.join(ttslua_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(guid_line + "\n")
                        f.write(lua)
                    written_files.add(filename)
                    print(f"  Extracted {filename} (GUID {guid}, {len(lua)} chars)")
                obj["LuaScript"] = ""
            else:
                unmatched_scripts.append({
                    "index": i, "GUID": guid, "Name": name,
                    "Nickname": nickname, "LuaScript_length": len(lua)
                })
                # Keep LuaScript in base JSON for unmatched (map layout cards etc.)

        _extract_nested_translations(obj, translations)

    # 4. Save translations
    with open(os.path.join(cn_dir, "cn_translations.json"), "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    print(f"  Extracted cn_translations.json ({len(translations)} entries)")

    # 5. Save base JSON
    with open(os.path.join(ttsjson_dir, "ftc_base.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved ftc_base.json")

    # 6. Report unmatched
    if unmatched_scripts:
        print(f"\n  WARNING: {len(unmatched_scripts)} objects with scripts not in GUID_TO_FILE:")
        for u in unmatched_scripts:
            print(f"    GUID={u['GUID']} Name={u['Name']} Nickname={u['Nickname']} Lua={u['LuaScript_length']} chars")
        with open(os.path.join(cn_dir, "unmatched_scripts.json"), "w", encoding="utf-8") as f:
            json.dump(unmatched_scripts, f, ensure_ascii=False, indent=2)


def _extract_nested_translations(obj, translations):
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
    print("\nDone!")
