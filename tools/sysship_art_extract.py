#!/usr/bin/env python3
"""Extract the star system window's fleet pictures from the player's MOO2 —
work order 326 C.

    python tools/sysship_art_extract.py                 # the usual dirs
    python tools/sysship_art_extract.py /path/to/DATA   # a folder with BUFFER0.LBX
    python tools/sysship_art_extract.py --list          # say what it would take

The Tech Review extractor's shape (decision 38): raw LBX entry blobs and the
palette, a manifest with a format version, decoding at load time in
`screens/galaxy_map/sysshipart.py` through `core/lbx.py`. Never committed,
never shipped (decisions 40 and 42): the output directory is gitignored.

WHAT IT TAKES:

  BUFFER0.LBX
    273-280   a player's fleet in the window's bar, entry 273 + the
              player's colour (`SYS::Buffer_Reload_System_Ships`,
              sys.cpp:1032-1040); eight different ships, one per colour
    281       owner 8 (sys.cpp:1043-1046)
    282-287   the monsters, owner 9-14 at (owner - 9) + 282 (:1048-1051)
              — each 8 identical frames, no palette of its own
  the palette FONTS.LBX 1, the palette the main screen loads
              (`fonts::Load_Palette(0, 0, 255)`, mainscr.cpp:1372, reads
              entry palette_id + 1, fonts.cpp:73); its first 1024 bytes are
              those of entry 9, which the other extractors read
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
DEFAULT_OUT = os.path.join(ROOT, "screens", "galaxy_map", "assets",
                           "gamedata")
#: BUFFER0.LBX entries 273 (0x111) .. 287: players' colours 0-7, owner 8,
#: monsters 9-14 (sys.cpp:1036-1051).
FIRST, LAST = 273, 287
FONTS_PALETTE, PALETTE_BYTES = 1, 256 * 4


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in ("BUFFER0.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/sysship_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    pics = lbx.read_entries(paths["BUFFER0.LBX"])
    if len(pics) <= LAST:
        sys.exit(f"BUFFER0.LBX has {len(pics)} entries, the bar's pictures "
                 f"reach entry {LAST}")
    fonts = lbx.read_entries(paths["FONTS.LBX"])
    base = lbx.screen_palette(fonts[FONTS_PALETTE][:PALETTE_BYTES])
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The star system window's fleet pictures (BUFFER0.LBX "
                  "273-287: a player's by colour, owner 8, the monsters) and "
                  "the main screen's palette, out of the player's own Master "
                  "of Orion 2. Never committed, never shipped (decisions 38, "
                  "40, 42). Rebuild with tools/sysship_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "entries": [FIRST, LAST],
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    for i in range(FIRST, LAST + 1):
        with open(os.path.join(out, f"sysship_{i}.bin"), "wb") as fh:
            fh.write(pics[i])
    with open(os.path.join(out, "sysship_palette.json"), "w",
              encoding="utf-8") as fh:
        # indent=2: the tree's JSON convention (smoke check 062).
        json.dump([list(base.get(i, (0, 0, 0)))[:3] for i in range(256)],
                  fh, indent=2)
        fh.write("\n")
    with open(os.path.join(out, "sysship_manifest.json"), "w",
              encoding="utf-8") as fh:
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
        print(f"{name:12} {info['path']}  sha256 {info['sha256'][:16]}…")
    print(f"BUFFER0.LBX entries {FIRST}-{LAST}")
    print("(--list: nothing written)" if args.list
          else f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
