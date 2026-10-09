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

  COLBLDG.LBX
    0                    the build popup's art, 640 x 480 with its palette:
                         its picture box (203..285, 9..103) is the GRID ROOM
                         a product stands in (`Draw_Build_Queue_Popup_`,
                         colbldg.cpp:1026-1030; work order 226 D)
  BLDG<n>.LBX
    30 + (k % 10) * 36   building k + 1's drawing on the colony's ground
                         at cell (5, 5), n = k // 10 (`Cache_Load_Bldg_`,
                         colbcach.cpp:4-19; `Bldg_Coords_To_Effective_Frame_`
                         colony_main.cpp:229) — the build popup cuts it out
                         (`Draw_Building_With_Bottom_Centered_`, :421-442)
  COLONY.LBX
    9 + p                a satellite's drawing, p by `Satellite_Anim_Pic_`
                         (colony.cpp:205-228)
  COLONY2.LBX
    7                    Trade Goods' BC stack (`Prod_Anims_(3, 1, 0)`,
                         colony.cpp:345-353; colbldg.cpp, TRADE_GOODS)
  RACEICON.LBX
    0xA9                 the android a farmer, worker or scientist product
                         shows (`People_Anim_(0, 4, race)`, colony_main.cpp:
                         444-462)
    race * 13 + 11       the race's spy (`Spy_Anim_`, colony.cpp:237-245)
    race * 13 + v + 6    the units at the screen's foot, v 0..4 (militia,
                         marines, powered armour, armour, battleoids;
                         `Military_Anims_`, colony.cpp:1297-1306; 226 G)
  COLPUPS.LBX
    5                    the colony screen's band with its build box's grid
                         room (`Draw_Colony_Info_Background_`, colony.cpp:
                         621-635; work order 226 G)

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

FORMAT_VERSION = 3
DEFAULT_OUT = os.path.join(ROOT, "screens", "colony", "assets", "gamedata")

CLIMATES, BG_TYPES, SIZES = 10, 3, 5
SKY = 0x31
SYS_FIRST, GAS_GIANT, ASTEROIDS, MARKER = 11, 0x3E, 0x3F, 0x41
SCREEN_PALETTE, PALETTE_BYTES = 2, 256 * 4
#: BUILDING_COUNT (orion2_consts.h:62); cell (5, 5)'s frame, y odd:
#: 5 * 6 - 5 + 5 (colony_main.cpp:229-236); COLONY.LBX's satellites
#: 9..16 (colony.cpp:205-228: pictures 0..7); RACEICON's 13 races (13 entries each, then 0xA9, 0xAA).
BUILDINGS, BLDG_CELL, SATELLITES, RACES = 49, 30, 8, 13


def wanted():
    """{file stem: (lbx, entry)}."""
    out = {"sky": ("COLONY2.LBX", SKY),
           "gas_giant": ("COLSYSDI.LBX", GAS_GIANT),
           "asteroids": ("COLSYSDI.LBX", ASTEROIDS),
           "marker": ("COLSYSDI.LBX", MARKER)}
    # The build popup (work order 226 D): its art, the buildings at cell
    # (5, 5), the satellites, Trade Goods, the android and the spies.
    out["build_art"] = ("COLBLDG.LBX", 0)
    for b in range(1, BUILDINGS):
        k = b - 1
        out[f"bldg_{b}"] = (f"BLDG{k // 10}.LBX", BLDG_CELL + (k % 10) * 36)
    for p in range(SATELLITES):
        out[f"satellite_{p}"] = ("COLONY.LBX", 9 + p)
    out["trade_goods"] = ("COLONY2.LBX", 7)
    out["android"] = ("RACEICON.LBX", 0xA9)
    for r in range(RACES):
        out[f"spy_{r}"] = ("RACEICON.LBX", r * 13 + 11)
        # the colony screen's units (work order 226 G): militia, marines,
        # powered armour, armour, battleoids (`Military_Anims_`, colony.cpp:
        # 1297-1306: race * 13 + variant + 6)
        for v in range(5):
            out[f"military_{r}_{v}"] = ("RACEICON.LBX", r * 13 + v + 6)
    # the colony screen's band, its build box's room in it (work order 226
    # G; `Draw_Colony_Info_Background_`, colony.cpp:621-635)
    out["band"] = ("COLPUPS.LBX", 5)
    for c in range(CLIMATES):
        for t in range(BG_TYPES):
            out[f"ground_{c}_{t}"] = ("PLANETS.LBX", c * BG_TYPES + t)
        for s in range(SIZES):
            out[f"planet_{c}_{s}"] = ("COLSYSDI.LBX", c * SIZES + s + SYS_FIRST)
    return out


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    names = sorted({n for n, _e in wanted().values()} | {"FONTS.LBX"})
    for name in names:
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
