#!/usr/bin/env python3
"""Extract the colony screen's planet pictures from the player's MOO2 — work order 223.

    python tools/colony_art_extract.py                 # the usual dirs
    python tools/colony_art_extract.py /path/to/DATA   # a folder with the LBX files
    python tools/colony_art_extract.py --list          # say what it would take

The Races extractor's shape (decision 38): raw LBX entry blobs and the
palette, a manifest with a format version, decoding at load time in
`screens/colony/colart.py` through `core/lbx.py`. Never committed, never
shipped (decisions 40 and 42): the output directory is gitignored.

WHAT IT TAKES (colony_main.cpp, colsysdi.cpp, colony.cpp):

  PLANETS.LBX
    climate * 3 + type   the ground of the colony's world, 640 x 480 with
                         its palette — `C_Anims_(0)` picks it by the
                         colony's climate and the planet's
                         `climate_bg_type` (colony_main.cpp:475-479), and
                         its palette is laid over the screen's
                         (`Update_Colony_Palette_`, colony.cpp:230-233)
  COLONY2.LBX
    0x31                 the sky the ground stands under, drawn first
                         (`Draw_Colony_Screen_`, colony_main.cpp:111-115)
  COLSYSDI.LBX
    climate * 5 + size + 11   a planet of the system display
                         (`Planet_Anims_`, colsysdi.cpp:4-6)
    0x3E, 0x3F           a gas giant, an asteroid belt (:28-33)
    0x41                 the orbit marker left of every row (:44-45)
  FONTS.LBX
    2                    palette 1, the screen's (`Load_Palette_(1, ...)`,
                         colony.cpp:231; fonts.cpp:72-73 loads entry id + 1)

NOT taken: the screen's frames, buttons and sprites (decision 71's HUD
draws them), the buildings and roads on the ground (OMISSION `roads`), and
COLONY2's planet ball (0x32), which the map's planet popups draw, not this
screen.
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
DEFAULT_OUT = os.path.join(ROOT, "screens", "colony", "assets", "gamedata")

CLIMATES, BG_TYPES, SIZES = 10, 3, 5
SKY = 0x31
SYS_FIRST, GAS_GIANT, ASTEROIDS, MARKER = 11, 0x3E, 0x3F, 0x41
SCREEN_PALETTE, PALETTE_BYTES = 2, 256 * 4


def wanted():
    """{file stem: (lbx, entry)}."""
    out = {"sky": ("COLONY2.LBX", SKY),
           "gas_giant": ("COLSYSDI.LBX", GAS_GIANT),
           "asteroids": ("COLSYSDI.LBX", ASTEROIDS),
           "marker": ("COLSYSDI.LBX", MARKER)}
    for c in range(CLIMATES):
        for t in range(BG_TYPES):
            out[f"ground_{c}_{t}"] = ("PLANETS.LBX", c * BG_TYPES + t)
        for s in range(SIZES):
            out[f"planet_{c}_{s}"] = ("COLSYSDI.LBX", c * SIZES + s + SYS_FIRST)
    return out


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in ("PLANETS.LBX", "COLONY2.LBX", "COLSYSDI.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/colony_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    files = {k: lbx.read_entries(v) for k, v in paths.items()}
    take = wanted()
    for stem, (name, entry) in take.items():
        if entry >= len(files[name]):
            sys.exit(f"{paths[name]} holds {len(files[name])} entries; "
                     f"{stem} needs {entry}")
    palette = lbx.screen_palette(
        files["FONTS.LBX"][SCREEN_PALETTE][:PALETTE_BYTES])
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The colony screen's sky, the ground of each climate, "
                  "the system display's planets and the screen's palette, "
                  "out of the player's own Master of Orion 2. Never "
                  "committed, never shipped (decisions 38, 40, 42). Rebuild "
                  "with tools/colony_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "entries": {k: {"lbx": n, "entry": e, "bytes": len(files[n][e])}
                    for k, (n, e) in take.items()},
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    for stem, (name, entry) in take.items():
        with open(os.path.join(out, f"{stem}.bin"), "wb") as fh:
            fh.write(files[name][entry])
    with open(os.path.join(out, "palette.json"), "w", encoding="utf-8") as fh:
        # indent=2: the tree's JSON convention (smoke check 062).
        json.dump([list(palette.get(i, (0, 0, 0)))[:3] for i in range(256)],
                  fh, indent=2)
        fh.write("\n")
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", nargs="?", default=None)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    m = extract(a.folder, a.out, dry_run=a.list)
    print(f"{len(m['entries'])} entries from "
          + ", ".join(sorted(m["source"])))
    if not a.list:
        print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
