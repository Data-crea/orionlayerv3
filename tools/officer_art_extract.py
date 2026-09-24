#!/usr/bin/env python3
"""Extract the Leaders screen's own artwork from the player's MOO2.

    python tools/officer_art_extract.py                 # the usual dirs
    python tools/officer_art_extract.py /path/to/DATA   # a folder with the LBX
    python tools/officer_art_extract.py --list          # say what it would take

**DECISION 38's RULE, THE FLEETS EXTRACTOR's SHAPE.** Raw LBX entry blobs
and the raw palette, a manifest with a format version, decoding at load
time in `screens/leaders/ldrart.py` through `core/lbx.py`. The folder
search and the file hash are `tools/fleet_art_extract.py`'s own,
imported rather than copied.

**NEVER COMMITTED, NEVER SHIPPED** (decisions 40 and 42): the output
directory is gitignored and the smoke test refuses game data anywhere
in the tree.

WHAT IT TAKES, every entry traced to the line that loads or draws it
(officer.cpp unless named):

  OFFICER.LBX
    1, 2          the ship-view and colony-view BOX art, drawn at
                  (300, 12) (:1197-1203, loaded :2269-2270)
    3, 4          the COLONY LEADERS / SHIP OFFICERS tabs, two frames,
                  frame 1 = the active view (:2271-2272, drawn :834-839)
    5, 6          the scroll bar's up / down arrows (:2273, :2277)
    7, 8          PREV / NEXT (:2278-2279)
    9, 10, 11, 12 HIRE, POOL, DISMISS, RETURN, two frames, frame 1 while
                  that mode is on (:2280-2283, drawn :778-794)
    13            CANCEL, hire mode only (:2284)
    14, 15        the selected / scanned big-icon boxes (:2288-2289)
    16            the scroll bar's track (:2290)
    17            the hire-mode panel under the buttons (:2291, :797)
    18, 19, 20    the DULL hire / pool / dismiss buttons (:2292-2294)
    0x15 + n      portrait n, n = `pict_num` (Load_Officer_Picture_ with
                  pic_type 0, :2639-2663), for n = 0..66
    0x58 + k      the 27 skill icons, k = skill id / 2 (:2220-2230)
    0x73..0x81    the small ship icons of the galaxy box: eight players
                  and seven monsters (:2765-2793)
    0x82..0x8C    the galaxy box's eleven star sprites (:2206-2214)
    0x8D, 0x8E    the normal / bright windows (:2298-2299)
    0x8F + n      the DARKENED portrait n — travelling or for hire
                  (Load_Darkened_Officer_Picture_, :3532-3540, drawn
                  :634-638)
  MAINPUPS.LBX
    0x39, 0x3A, 0x3B  the hire popup as the Leaders screen opens it:
                  background, REJECT, HIRE
                  (Load_New_Officer_Popup_For_Officer_Screen_,
                  mainpups.cpp:1644-1655)
  FONTS.LBX
    9             the palette: `fonts::Load_Palette_(8, 0, 0xFF)`
                  (:674) reads entry `palette_id + 1` (fonts.cpp:73)

The two other portrait sets at 0xD2 and 0x115 (pic types 1 and 2) are
not taken: nothing on this screen asks for them.
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

#: Anchored to the project, never to the working directory.
DEFAULT_OUT = os.path.join(ROOT, "screens", "leaders", "assets", "gamedata")

#: OFFICER.LBX entries by the name the loader asks for.
OFFICER_ENTRIES = {
    "fleet_box": 1, "colony_box": 2,
    "tab_colony": 3, "tab_ship": 4,
    "scroll_up": 5, "scroll_down": 6,
    "prev": 7, "next": 8,
    "hire": 9, "pool": 10, "dismiss": 11, "return": 12, "cancel": 13,
    "selected_box": 14, "scanned_box": 15, "scroll_track": 16,
    "hire_panel": 17,
    "hire_dull": 18, "pool_dull": 19, "dismiss_dull": 20,
    "window_normal": 0x8D, "window_bright": 0x8E,
}
PORTRAIT_FIRST, DARK_FIRST, PORTRAIT_COUNT = 0x15, 0x8F, 67
SKILL_ICON_FIRST, SKILL_ICON_COUNT = 0x58, 27
SMALL_SHIP_FIRST, SMALL_SHIP_COUNT = 0x73, 15
STAR_FIRST, STAR_COUNT = 0x82, 11
MAINPUPS_ENTRIES = {"popup": 0x39, "popup_reject": 0x3A, "popup_hire": 0x3B}
PALETTE_ENTRY = 9
PALETTE_BYTES = 256 * 4


def wanted():
    """{name: OFFICER.LBX entry} for everything taken from that file."""
    out = dict(OFFICER_ENTRIES)
    out.update({f"portrait_{n}": PORTRAIT_FIRST + n
                for n in range(PORTRAIT_COUNT)})
    out.update({f"dark_{n}": DARK_FIRST + n for n in range(PORTRAIT_COUNT)})
    out.update({f"skill_{k}": SKILL_ICON_FIRST + k
                for k in range(SKILL_ICON_COUNT)})
    out.update({f"small_ship_{k}": SMALL_SHIP_FIRST + k
                for k in range(SMALL_SHIP_COUNT)})
    out.update({f"star_{k}": STAR_FIRST + k for k in range(STAR_COUNT)})
    return out


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    """Write the blobs and the manifest. Returns the manifest."""
    paths = {}
    for name in ("OFFICER.LBX", "MAINPUPS.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/officer_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    officer = lbx.read_entries(paths["OFFICER.LBX"])
    mainpups = lbx.read_entries(paths["MAINPUPS.LBX"])
    fonts = lbx.read_entries(paths["FONTS.LBX"])
    take = wanted()
    top = max(take.values())
    if len(officer) <= top:
        sys.exit(f"{paths['OFFICER.LBX']} holds {len(officer)} entries; "
                 f"entry {top} is needed.")
    if len(mainpups) <= max(MAINPUPS_ENTRIES.values()):
        sys.exit(f"{paths['MAINPUPS.LBX']} holds {len(mainpups)} entries.")
    palette = fonts[PALETTE_ENTRY] if len(fonts) > PALETTE_ENTRY else b""
    if len(palette) < PALETTE_BYTES:
        sys.exit(f"FONTS.LBX entry {PALETTE_ENTRY} is {len(palette)} bytes; "
                 f"at least {PALETTE_BYTES} expected.")
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The Leaders screen's own artwork and palette, raw, out "
                  "of the player's own Master of Orion 2. Never committed, "
                  "never shipped (decisions 38, 40, 42). Rebuild with "
                  "tools/officer_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "officer": {k: {"entry": v, "bytes": len(officer[v])}
                    for k, v in take.items()},
        "mainpups": {k: {"entry": v, "bytes": len(mainpups[v])}
                     for k, v in MAINPUPS_ENTRIES.items()},
        "palette": {"entry": PALETTE_ENTRY, "bytes": PALETTE_BYTES},
    }
    if dry_run:
        return manifest
    os.makedirs(os.path.join(out, "officer"), exist_ok=True)
    for name, entry in take.items():
        _write(os.path.join(out, "officer", f"{name}.bin"), officer[entry])
    for name, entry in MAINPUPS_ENTRIES.items():
        _write(os.path.join(out, "officer", f"{name}.bin"), mainpups[entry])
    _write(os.path.join(out, "palette.bin"), palette[:PALETTE_BYTES])
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def _write(path, blob):
    with open(path, "wb") as fh:
        fh.write(blob)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", nargs="?",
                    help="folder holding OFFICER.LBX, MAINPUPS.LBX, FONTS.LBX")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true",
                    help="say what would be taken, write nothing")
    args = ap.parse_args()
    manifest = extract(args.folder, args.out, dry_run=args.list)
    for name, info in manifest["source"].items():
        print(f"{name:13} {info['path']}")
        print(f"{'':13} sha256 {info['sha256'][:16]}…")
    print(f"OFFICER.LBX entries: {len(manifest['officer'])}  "
          f"MAINPUPS.LBX entries: {len(manifest['mainpups'])}  "
          f"palette: FONTS.LBX entry {manifest['palette']['entry']}")
    print("\n(--list: nothing written)" if args.list
          else f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
