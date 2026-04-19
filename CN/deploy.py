#!/usr/bin/env python3
"""Copy compiled CN JSON to TTS Workshop directory for testing."""

import shutil
import sys
import os
import glob

def deploy(repo_root="."):
    pattern = os.path.join(repo_root, "release", "ftc_base_*_compiled.json")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        print("No compiled JSON found. Run build_cn.py first.")
        sys.exit(1)

    source = files[0]
    docs = os.path.expanduser("~")
    tts_workshop = os.path.join(docs, "Documents", "My Games",
                                "Tabletop Simulator", "Mods", "Workshop")
    dest = os.path.join(tts_workshop, "3706079312.json")

    print(f"Deploying: {os.path.basename(source)} -> 3706079312.json")
    print(f"  -> {dest}")
    shutil.copy2(source, dest)
    print("Done! Restart TTS or reload the mod to see changes.")


if __name__ == "__main__":
    deploy(sys.argv[1] if len(sys.argv) > 1 else ".")
