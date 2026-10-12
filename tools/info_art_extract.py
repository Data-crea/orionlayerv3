#!/usr/bin/env python3
"""Extract the Info screen's Tech Review pictures from the player's MOO2 — work
order 196 F.

    python tools/info_art_extract.py                 # the usual dirs
    python tools/info_art_extract.py /path/to/DATA   # a folder with APP_PICS.LBX
    python tools/info_art_extract.py --list          # say what it would take

The Races extractor's shape (decision 38): raw LBX entry blobs and the base
palette, a manifest with a format version, decoding at load time in
`screens/info/infoart.py` through `core/lbx.py`. Never committed, never
shipped (decisions 40 and 42): the output directory is gitignored.

WHAT IT TAKES:

  APP_PICS.LBX
    every entry   the picture of technology application `id` is entry `id`
                  (`Far_Reload_Next_("APP_PICS.LBX", tech_app_id)`,
                  info.cpp:893), 180 x 139, drawn at native (0x1B1, 0x73)
                  (`Draw_Tech_Review_Subscreen_`, info.cpp:1555); each
                  carries its own palette (`Draw_Palette_`, info.cpp:896)
  the palette     FONTS.LBX 9, the main palette the pictures' own ranges
                  are laid over (`lbx.read_palette`, as the Races art)
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import lbx  # noqa: E402
from fleet_art_extract import _sha, find_lbx  # noqa: E402

FORMAT_VERSION = 1
DEFAULT_OUT = os.path.join(ROOT, "screens", "info", "assets", "gamedata")
FONTS_PALETTE, PALETTE_BYTES = 9, 256 * 4


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in ("APP_PICS.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/info_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    pics = lbx.read_entries(paths["APP_PICS.LBX"])
    fonts = lbx.read_entries(paths["FONTS.LBX"])
    base = lbx.screen_palette(fonts[FONTS_PALETTE][:PALETTE_BYTES])
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The Info screen's Tech Review pictures (APP_PICS.LBX, one "
                  "per technology application) and the main palette, out of "
                  "the player's own Master of Orion 2. Never committed, never "
                  "shipped (decisions 38, 40, 42). Rebuild with "
                  "tools/info_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "pictures": len(pics),
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    for i, blob in enumerate(pics):
        with open(os.path.join(out, f"app_{i}.bin"), "wb") as fh:
            fh.write(blob)
    with open(os.path.join(out, "palette.json"), "w", encoding="utf-8") as fh:
        # indent=2: the tree's JSON convention (smoke check 062).
        json.dump([list(base.get(i, (0, 0, 0)))[:3] for i in range(256)],
                  fh, indent=2)
        fh.write("\n")
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    manifest = extract(args.folder, args.out, dry_run=args.list)
    for name, info in manifest["source"].items():
        print(f"{name:13} {info['path']}  sha256 {info['sha256'][:16]}…")
    print(f"APP_PICS.LBX pictures: {manifest['pictures']}")
    print("(--list: nothing written)" if args.list
          else f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
