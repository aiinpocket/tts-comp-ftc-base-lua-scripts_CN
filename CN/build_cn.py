#!/usr/bin/env python3
"""
Build script for the CN TTS mod.

Compiles TTSLUA scripts, XmlUI, and metadata into a single TTS save JSON.
Also versions card image URLs and syncs them on GCP so TTS clients
always fetch the latest images.

Usage:
    python3 CN/build_cn.py <project_root> <version>

Example:
    python3 CN/build_cn.py . v1.3
"""

import json
import glob
import os
import re
import subprocess
import sys
from datetime import datetime

# GCP bucket config
GCS_BUCKET = "steam-40k"
GCS_CARDS_BASE = f"gs://{GCS_BUCKET}/cards/"
GCS_PUBLIC_BASE = f"https://storage.googleapis.com/{GCS_BUCKET}/cards/"

# On Windows, gcloud must be invoked via its .cmd wrapper for subprocess
GCLOUD = "gcloud.cmd" if sys.platform == "win32" else "gcloud"


def parse_ttslua_file(filepath):
    """Parse a .ttslua file, returning (guids, lua_body).

    For global.ttslua: guids=None, lua_body=full file content.
    For others: reads all leading '-- FTC-GUID:' lines, extracts GUIDs,
    and returns the remaining content as lua_body.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    basename = os.path.basename(filepath)
    if basename == "global.ttslua":
        return None, content

    lines = content.split("\n")
    guids = set()
    body_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("-- FTC-GUID:"):
            rest = stripped[len("-- FTC-GUID:"):].strip()
            for g in rest.replace(",", " ").split():
                g = g.strip()
                if g:
                    guids.add(g)
            body_start = i + 1
        else:
            break

    lua_body = "\n".join(lines[body_start:])
    return guids, lua_body


def find_all_objects(data):
    """Recursively find all objects in the save, yielding (obj, path) tuples.

    Searches ObjectStates, ContainedObjects, and States.
    """
    for i, obj in enumerate(data.get("ObjectStates", [])):
        yield from _walk_object(obj, f"ObjectStates[{i}]")


def _walk_object(obj, path):
    """Walk an object tree yielding (obj, path)."""
    yield obj, path

    # Check ContainedObjects
    for i, child in enumerate(obj.get("ContainedObjects", [])):
        yield from _walk_object(child, f"{path}.ContainedObjects[{i}]")

    # Check States (multi-state objects)
    if "States" in obj:
        for key, state_obj in obj["States"].items():
            yield from _walk_object(state_obj, f"{path}.States[{key}]")


def fix_deck_ids(data):
    """For every Deck/DeckCustom, sync DeckIDs from ContainedObjects' CardIDs."""
    count = 0
    for obj, path in find_all_objects(data):
        if obj.get("Name") in ("Deck", "DeckCustom"):
            contained = obj.get("ContainedObjects", [])
            if contained:
                new_ids = [c["CardID"] for c in contained if "CardID" in c]
                old_ids = obj.get("DeckIDs", [])
                if new_ids != old_ids:
                    obj["DeckIDs"] = new_ids
                    count += 1
    return count


def sync_card_images_to_version(version):
    """Copy all card images from gs://steam-40k/cards/ to gs://steam-40k/cards/<version>/.

    This ensures each build version has its own set of image URLs,
    forcing TTS clients to re-download when the version changes.
    """
    src = GCS_CARDS_BASE
    dst = f"gs://{GCS_BUCKET}/cards/{version}/"

    # Check if version folder already exists
    result = subprocess.run(
        [GCLOUD, "storage", "ls", dst],
        capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip():
        print(f"  GCS: {dst} already exists, skipping copy")
        return True

    # Copy all images from cards/ root to cards/<version>/
    print(f"  GCS: Copying {src}*.png -> {dst}")
    result = subprocess.run(
        [GCLOUD, "storage", "cp", f"{src}*.png", dst],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  WARNING: GCS copy failed: {result.stderr}")
        return False

    # Count copied files
    count_result = subprocess.run(
        [GCLOUD, "storage", "ls", dst],
        capture_output=True, text=True
    )
    count = len([l for l in count_result.stdout.strip().split("\n") if l])
    print(f"  GCS: Copied {count} images to {dst}")
    return True


def version_card_urls(data, version):
    """Replace all steam-40k/cards/ URLs with steam-40k/cards/<version>/ URLs.

    This applies to FaceURL and BackURL in CustomDeck entries throughout the JSON.
    Only rewrites URLs that point to our GCS bucket (steam-40k), not Steam UGC URLs.
    """
    old_base = f"storage.googleapis.com/{GCS_BUCKET}/cards/"
    new_base = f"storage.googleapis.com/{GCS_BUCKET}/cards/{version}/"
    count = 0

    for obj, path in find_all_objects(data):
        for dk_id, dk_data in obj.get("CustomDeck", {}).items():
            for key in ("FaceURL", "BackURL"):
                url = dk_data.get(key, "")
                if old_base in url and f"/cards/{version}/" not in url:
                    dk_data[key] = url.replace(old_base, new_base)
                    count += 1

    return count


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 CN/build_cn.py <project_root> <version>")
        print("Example: python3 CN/build_cn.py . v1.2")
        sys.exit(1)

    project_root = sys.argv[1]
    version = sys.argv[2]

    # Resolve paths
    base_json_path = os.path.join(project_root, "TTSJSON", "ftc_base.json")
    xmlui_path = os.path.join(project_root, "CN", "cn_xmlui.xml")
    ttslua_dir = os.path.join(project_root, "TTSLUA")
    output_path = os.path.join(project_root, "release", f"ftc_base_{version}_compiled.json")

    # 1. Load base JSON
    print(f"Loading base JSON: {base_json_path}")
    with open(base_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Build GUID -> object index for fast lookup
    guid_map = {}  # guid -> list of (obj, path)
    for obj, path in find_all_objects(data):
        guid = obj.get("GUID", "")
        if guid:
            guid_map.setdefault(guid, []).append((obj, path))

    # 3. Parse and inject Lua scripts
    ttslua_files = sorted(glob.glob(os.path.join(ttslua_dir, "*.ttslua")))
    print(f"Found {len(ttslua_files)} .ttslua files")

    injected_count = 0
    missing_guids = []

    for filepath in ttslua_files:
        basename = os.path.basename(filepath)
        guids, lua_body = parse_ttslua_file(filepath)

        if guids is None:
            # global.ttslua
            data["LuaScript"] = lua_body
            print(f"  Injected global.ttslua ({len(lua_body)} chars)")
            injected_count += 1
        else:
            for guid in guids:
                if guid in guid_map:
                    for obj, path in guid_map[guid]:
                        obj["LuaScript"] = lua_body
                        injected_count += 1
                    print(f"  Injected {basename} -> GUID {guid} ({len(guid_map[guid])} objects, {len(lua_body)} chars)")
                else:
                    missing_guids.append((basename, guid))
                    print(f"  WARNING: GUID {guid} from {basename} not found in JSON")

    print(f"Total injections: {injected_count}")
    if missing_guids:
        print(f"Missing GUIDs: {len(missing_guids)}")

    # 4. Inject XmlUI
    print(f"Loading XmlUI: {xmlui_path}")
    with open(xmlui_path, "r", encoding="utf-8") as f:
        xmlui_content = f.read()
    data["XmlUI"] = xmlui_content
    print(f"  Injected XmlUI ({len(xmlui_content)} chars)")

    # 5. Fix DeckIDs
    deck_fixes = fix_deck_ids(data)
    print(f"Fixed {deck_fixes} deck DeckIDs")

    # 6. Version card image URLs and sync to GCP
    print(f"Versioning card images to {version}...")
    url_count = version_card_urls(data, version)
    print(f"  Rewrote {url_count} image URLs to cards/{version}/")
    if url_count > 0:
        print(f"Syncing card images to GCS...")
        sync_card_images_to_version(version)

    # 7. Update metadata
    now = datetime.now()
    hour_12 = now.hour % 12 or 12
    am_pm = "AM" if now.hour < 12 else "PM"
    data["Date"] = f"{now.month}/{now.day}/{now.year} {hour_12}:{now.minute:02d}:{now.second:02d} {am_pm}"
    data["VersionNumber"] = f"EN v14.2.1 / CN {version}"
    data["SaveName"] = f"40K 10e 競技模組 CN {version} (基於 EN v1.7.4)"
    print(f"Set SaveName: {data['SaveName']}")
    print(f"Set VersionNumber: {data['VersionNumber']}")
    print(f"Set Date: {data['Date']}")

    # 8. Save output
    print(f"Saving to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done! Output: {output_path}")


if __name__ == "__main__":
    main()
