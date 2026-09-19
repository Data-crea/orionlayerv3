#!/usr/bin/env python3
"""Extract the Fleets screen's own artwork from the player's MOO2.

    python tools/fleet_art_extract.py                 # search the usual dirs
    python tools/fleet_art_extract.py /path/to/DATA   # a folder holding the LBX
    python tools/fleet_art_extract.py --list          # say what it would take

**DECISION 38's RULE, NOT A PNG DUMP.** This hands the bytes over
UNTOUCHED — the raw LBX entry blobs and the raw palette — and the
decoding happens at load time in `screens/fleets/fltart.py`, through
`core/lbx.py`, which every other extraction in this tree already uses.
So a fix to the decoder needs no re-extraction, and the manifest
carries a format version because a body mangled by an older extractor
renders ALMOST right, which is worse than not loading at all.

**NEVER COMMITTED, NEVER SHIPPED** (decisions 40 and 42). These are the
original's own pixels out of somebody's installation. The output
directory is gitignored and the smoke test refuses game data anywhere
in the tree.

WHAT IT TAKES, AND WHY EACH — every entry traced to the function that
draws it:

  SHIPS.LBX  entry `ship_type + colour * 50`
             `KEN::Do_Get_Ship_Picture_Seg` (ken.cpp:458), reached from
             `Get_Ship_Id_Picture_Seg_` (:451) and drawn into the grid
             cell at flt1.cpp:106-107. `colour` is
             `_player[previous_owner].color`, or MAX_PLAYERS (8,
             consts.h:7) for a monster — so nine sets of fifty and the
             whole file is taken: the ship a stack holds is not known
             until the wire says so.

             WHAT THE FILE ACTUALLY HOLDS, counted rather than assumed,
             because the arithmetic above says 450 and the header says
             449 (`entry_count` at offset 0, `vfs_lbx.cpp`; the 450th
             offset is the end of the file, so `read_entries` is right
             and the file is simply shorter than the index space):

               0..399   the eight PLAYER sets, exactly 50 each and
                        complete
               400..448 the monster set, 49 — slot 449 is not there
               slot 49  of EVERY set is a 2x1 placeholder, not a ship,
                        so `ship_type` is 0..48 in practice and the
                        missing 449 is that same placeholder
               400..448 holds 14 real pictures among 1x1 stubs: the
                        monster set is sparse by construction

             AND A PICTURE IS NOT ONE SIZE. 52x48 is the common one,
             but 52x52 (slots 40..43 of every set), 55x55 and 51x49 all
             occur. Nothing here or in the loader may assume a size:
             the original itself asks the sprite (`animate::Get_Width_`,
             animate.cpp:79) and centres it in the 0x39 cell
             (flt1.cpp:81-85). A degenerate 1x1 or 2x1 is a HOLE, and
             the loader treats it exactly as it treats a missing file.

  FLEET.LBX  0       the screen's own background, 640x480 — the grid
                     plates, the rails and the button faces are painted
                     into it (`_fleet_background_seg`, flt1.cpp:1130)
             9, 10   the SUPPORT and COMBAT filter radios, two frames
                     each: `Add_Radio_Button_Field_` is handed the
                     animation and the status variable
                     (flt1.cpp:1255-1256, loaded at :1139-1140), and
                     the frame IS the state — frame 1 is the lit one
             17      the box round a SELECTED cell (flt1.cpp:103)
             18      the box round the SCANNED cell (flt1.cpp:1100-1104)
             34..44  the inset's stars, one per colour index 0..10,
                     five frames each (`Load_Galaxy_Stars_`,
                     flt1.cpp:1439-1447), drawn by
                     `MOVEBOX::Draw_Galaxy_Map_Box_` under view_mode 1
                     (movebox.cpp:84-86)

  FONTS.LBX  9       the palette the screen is drawn in.
                     `fonts::Load_Palette_(8, 0, 255)` (flt1.cpp:555)
                     reads `palette_id + 1` out of FONTS.LBX
                     (fonts.cpp:73), so 8 means entry 9. 256 entries of
                     `{changed, r, g, b}`, six-bit — the byte order
                     `core/lbx.read_palette` was corrected to on
                     6 September 2026 and that a fixture pins.

AN ABSENT FILE IS A STATE, not an error: the screen says how to get it
and draws what it drew before (work order 142 D1.4).
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import lbx  # noqa: E402

#: Bumped when the LAYOUT of what is written changes. The loader
#: refuses an older one rather than rendering almost right
#: (decision 38's own reason).
FORMAT_VERSION = 1

#: Anchored to the project, never to the working directory — the fault
#: `help_extract.py` and `nebula_extract.py` each shipped once.
DEFAULT_OUT = os.path.join(ROOT, "screens", "fleets", "assets", "gamedata")

DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]

#: FLEET.LBX entries, by the name the loader asks for.
FLEET_ENTRIES = {"background": 0, "selected_box": 17, "scanned_box": 18,
                 "radio_support": 9, "radio_combat": 10}
#: The inset's eleven star sprites, colour index 0..10.
STAR_FIRST, STAR_COUNT = 34, 11
#: `Do_Get_Ship_Picture_Seg`'s stride and the number of colour sets:
#: eight players plus the monster set at MAX_PLAYERS.
SHIP_STRIDE, SHIP_SETS = 50, 9
#: FONTS.LBX entry, from `Load_Palette_(8, …)` + 1 (fonts.cpp:73).
PALETTE_ENTRY = 9
PALETTE_BYTES = 256 * 4


def find_lbx(folder, filename):
    """The LBX, in `folder` if given, else in the usual places."""
    roots = [folder] if folder else DEFAULT_SEARCH
    for d in roots:
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == filename.lower():
                return os.path.join(d, name)
    return None


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    """Write the blobs and the manifest. Returns the manifest."""
    paths = {}
    for name in ("FLEET.LBX", "SHIPS.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/fleet_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found

    fleet = lbx.read_entries(paths["FLEET.LBX"])
    ships = lbx.read_entries(paths["SHIPS.LBX"])
    fonts = lbx.read_entries(paths["FONTS.LBX"])

    wanted = dict(FLEET_ENTRIES)
    wanted.update({f"star_{i}": STAR_FIRST + i for i in range(STAR_COUNT)})
    # THE FILE WINS AND THE DIFFERENCE IS NAMED. The index space is
    # 450 and the file holds 449 — see the module docstring for what
    # was counted. Demanding 450 would reject a correct SHIPS.LBX, so
    # what is REQUIRED is the eight player sets, which the grid needs
    # and which are complete; the ninth is taken as far as it goes.
    n_full = SHIP_STRIDE * SHIP_SETS
    n_player = SHIP_STRIDE * (SHIP_SETS - 1)
    if len(ships) < n_player:
        sys.exit(f"{paths['SHIPS.LBX']} holds {len(ships)} entries; at "
                 f"least {n_player} expected for the eight player "
                 f"colour sets of {SHIP_STRIDE} (ken.cpp:458).")
    n_ships = min(len(ships), n_full)
    if len(fonts) <= PALETTE_ENTRY:
        sys.exit(f"{paths['FONTS.LBX']} has no entry {PALETTE_ENTRY}.")
    palette_blob = fonts[PALETTE_ENTRY]
    if len(palette_blob) < PALETTE_BYTES:
        sys.exit(f"FONTS.LBX entry {PALETTE_ENTRY} is {len(palette_blob)} "
                 f"bytes; at least {PALETTE_BYTES} expected.")

    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The Fleets screen's own artwork and palette, raw, out "
                  "of the player's own Master of Orion 2. Never committed, "
                  "never shipped (decisions 38, 40, 42). Rebuild with "
                  "tools/fleet_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "fleet": {k: {"entry": v, "bytes": len(fleet[v])}
                  for k, v in wanted.items()},
        "ships": {"stride": SHIP_STRIDE, "sets": SHIP_SETS,
                  "count": n_ships, "in_file": len(ships),
                  "full_set_would_be": n_full},
        "palette": {"entry": PALETTE_ENTRY, "bytes": PALETTE_BYTES},
    }
    if dry_run:
        return manifest

    os.makedirs(os.path.join(out, "fleet"), exist_ok=True)
    os.makedirs(os.path.join(out, "ships"), exist_ok=True)
    for name, entry in wanted.items():
        _write(os.path.join(out, "fleet", f"{name}.bin"), fleet[entry])
    for i in range(n_ships):
        _write(os.path.join(out, "ships", f"{i}.bin"), ships[i])
    _write(os.path.join(out, "palette.bin"), palette_blob[:PALETTE_BYTES])
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def _write(path, blob):
    with open(path, "wb") as fh:
        fh.write(blob)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", nargs="?",
                    help="folder holding FLEET.LBX, SHIPS.LBX, FONTS.LBX")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--list", action="store_true",
                    help="say what would be taken, write nothing")
    args = ap.parse_args()
    manifest = extract(args.folder, args.out, dry_run=args.list)
    for name, info in manifest["source"].items():
        print(f"{name:12} {info['path']}")
        print(f"{'':12} sha256 {info['sha256'][:16]}…")
    print(f"fleet entries: {len(manifest['fleet'])}  "
          f"ship pictures: {manifest['ships']['count']}  "
          f"palette: FONTS.LBX entry {manifest['palette']['entry']}")
    if args.list:
        print("\n(--list: nothing written)")
    else:
        print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
