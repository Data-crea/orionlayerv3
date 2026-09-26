#!/usr/bin/env python3
"""Extract the Races screen's own artwork from the player's MOO2 — work order 175 C.

    python tools/races_art_extract.py                 # the usual dirs
    python tools/races_art_extract.py /path/to/DATA   # a folder with RACES.LBX
    python tools/races_art_extract.py --list          # say what it would take

The Leaders extractor's shape (decision 38): raw LBX entry blobs and the
palette, a manifest with a format version, decoding at load time in
`screens/races/racesart.py` through `core/lbx.py`. Never committed, never
shipped (decisions 40 and 42): the output directory is gitignored.

WHAT IT TAKES (racescrn.cpp unless named):

  RACES.LBX
    32 + race     the race portraits, 76 x 88, drawn at `_race_picture`
                  (`Draw_Race_Photos_`, :258-281, loaded :328) — 13 races
    31            the ELIMINATED overlay over a portrait (:266-268, :288)
    46 + race     the spy icon of each race (:286, :319, :335)
  the palette     RACES.LBX entry 0 — the screen's background, which
                  carries the palette the screen runs in (:742, :775) —
                  laid over FONTS.LBX 9, the main palette its range leaves
                  as it is (`lbx.read_palette`)

NOT taken, and why: the background itself (entry 0's pixels — the order's
"no outer frame", decision 71's HUD style draws the panels), the bars,
sliders and buttons (2, 3, 6-9, 60 — HUD blocks), the mission buttons
10-30 (the spy missions are not built, parked), the cursors (1, 4, 5,
61-63) and the network box (59).
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
DEFAULT_OUT = os.path.join(ROOT, "screens", "races", "assets", "gamedata")

RACES = 13
PORTRAIT_FIRST, SPY_FIRST, ELIMINATED = 32, 46, 31
BACKGROUND = 0
FONTS_PALETTE, PALETTE_BYTES = 9, 256 * 4


def wanted():
    out = {"eliminated": ELIMINATED}
    out.update({f"portrait_{r}": PORTRAIT_FIRST + r for r in range(RACES)})
    out.update({f"spy_{r}": SPY_FIRST + r for r in range(RACES)})
    return out


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in ("RACES.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/races_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    races = lbx.read_entries(paths["RACES.LBX"])
    fonts = lbx.read_entries(paths["FONTS.LBX"])
    take = wanted()
    if len(races) <= max(take.values()):
        sys.exit(f"{paths['RACES.LBX']} holds {len(races)} entries.")
    base = lbx.screen_palette(fonts[FONTS_PALETTE][:PALETTE_BYTES])
    head = lbx.parse_header(races[BACKGROUND], "RACES.LBX 0")
    if not head.has_palette:
        sys.exit("RACES.LBX entry 0 carries no palette — not the file the "
                 "source reads")
    palette = dict(base)
    palette.update(lbx.read_palette(races[BACKGROUND], head.frame_count))
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The Races screen's portraits, overlay and spy icons and "
                  "its palette, out of the player's own Master of Orion 2. "
                  "Never committed, never shipped (decisions 38, 40, 42). "
                  "Rebuild with tools/races_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "races": {k: {"entry": v, "bytes": len(races[v])}
                  for k, v in take.items()},
    }
    if dry_run:
        return manifest
    os.makedirs(out, exist_ok=True)
    for name, entry in take.items():
        with open(os.path.join(out, f"{name}.bin"), "wb") as fh:
            fh.write(races[entry])
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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    manifest = extract(args.folder, args.out, dry_run=args.list)
    for name, info in manifest["source"].items():
        print(f"{name:10} {info['path']}  sha256 {info['sha256'][:16]}…")
    print(f"RACES.LBX entries: {len(manifest['races'])}")
    print("(--list: nothing written)" if args.list
          else f"written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
