#!/usr/bin/env python3
"""Extract the invasion's pictures from the player's MOO2 — work order 232 C.

    python tools/invasion_art_extract.py                 # the usual dirs
    python tools/invasion_art_extract.py /path/to/DATA   # a folder with the LBX files
    python tools/invasion_art_extract.py --list          # say what it would take

The colony extractor's shape (decision 38): raw LBX entry blobs and the
palettes, a manifest with a format version, decoding at load time in
`screens/ground_combat/gcart.py` through `core/lbx.py`. Never committed,
never shipped (decisions 40 and 42): the output directory is gitignored.

WHAT IT TAKES (colgcbt.cpp, mainpups.cpp, colony_main.cpp, colony.cpp):

  COLGCBT.LBX
    0..9                 the infantry, attacker's side then defender's: per
                         kind five pictures (die, stand, fire, walk, hit) —
                         `Load_Combat_Anims_` (colgcbt.cpp:89-163) and
                         `Action_Anim_` (:313-330)
    10..14, 15..19       the tanks, without and with Battleoids
    20, 21               the heart (unused by the screen) and the summary
                         boxes' frame (`Draw_Summary_Box_ATK_`, :279-296)
  COLONY.LBX
    7                    the ground combat's explosion (`_explosion_anim`)
  MAINPUPS.LBX
    0x3D, 0x49           a bomb's and a biological bomb's explosion over the
                         planet (`Apply_Next_Bomb_Hit_`, mainpups.cpp:
                         1509-1590; `_anims[25]`, `_anims[26]`)
  COLONY2.LBX
    0x2E, 0x2F, 0x30     the popup's icons: the bombardment, the buildings,
                         the best shield (`Draw_Colony_Combat_Popup_`,
                         mainpups.cpp:2682-2811; `Load_Colony_Combat_Popup_`)
  CMBTPLNT.LBX
    climate * 6 + size   the planet in the popup's middle; climate * 6 + 5
                         its palette (`Load_Combat_Colony_Picture_To_
                         Screen_Seg_`, mainpups.cpp:2431-2448)
  RACEICON.LBX
    race * 13 + job * 2 + 1  a colonist as the popup shows one
                         (`People_Anim_(job, 2, race)`, colony_main.cpp:
                         444-448)
  COLONY2.LBX
    0x32                 the picture whose palette the popup's icons,
                         colonists and troops are drawn in: `Remap_Draw_`
                         after `Calculate_Picture_Remap_Colors_(C_Anims_(13))`
                         (mainpups.cpp:2702-2703; colony_main.cpp:518-519)
  RACEICON.LBX
    race * 13 + v + 6    the troops as the popup shows them
                         (`Player_Troop_Anim_` -> `Military_Anims_`,
                         colony.cpp:1297-1306, :2317-2336)
  FONTS.LBX
    0                    its first 16 x 4 bytes: the glass colours
                         (`Load_Font_File_`, fonts.cpp:887-903), glass 0
                         made 50 % black by `Update_Glass_Remap_Colors_`
                         (remap.cpp:153-157) on both screens
    1                    palette 0, the popup's (`fonts::Load_Palette_(0)`,
                         mainpups.cpp:1294; fonts.cpp:72-73 loads entry id
                         + 1)

The ground combat's scene, its palette and the troops' figures in the popup
are the colony screen's (`tools/colony_art_extract.py`).

NOT taken: the popup's box and its button pictures (MAINPUPS.LBX 0x35-0x52;
decision 71's HUD draws them) and the colony's buildings on the scene
(OMISSION `ground_buildings`).
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
DEFAULT_OUT = os.path.join(ROOT, "screens", "ground_combat", "assets",
                           "gamedata")

CLIMATES, PLANET_SIZES, RACES, JOBS = 10, 5, 13, 3
POPUP_PALETTE, PALETTE_BYTES = 1, 256 * 4
#: `video::_glass_colors[16]` (video.cpp:24), (intensity, r, g, b) each.
GLASS_COUNT = 16
UNIT_PICTURES = 22


def wanted():
    """{file stem: (lbx, entry)}."""
    out = {f"gcbt_{n}": ("COLGCBT.LBX", n) for n in range(UNIT_PICTURES)}
    out["explosion"] = ("COLONY.LBX", 7)
    out["bomb"] = ("MAINPUPS.LBX", 0x3D)
    out["bio"] = ("MAINPUPS.LBX", 0x49)
    out["icon_bombard"] = ("COLONY2.LBX", 0x2E)
    out["icon_buildings"] = ("COLONY2.LBX", 0x2F)
    out["icon_shield"] = ("COLONY2.LBX", 0x30)
    for c in range(CLIMATES):
        for s in range(PLANET_SIZES):
            out[f"planet_{c}_{s}"] = ("CMBTPLNT.LBX", c * 6 + s)
        out[f"planet_palette_{c}"] = ("CMBTPLNT.LBX", c * 6 + 5)
    out["remap_picture"] = ("COLONY2.LBX", 0x32)
    for r in range(RACES):
        for j in range(JOBS):
            out[f"people_{r}_{j}"] = ("RACEICON.LBX", r * 13 + j * 2 + 1)
        for v in range(5):
            out[f"military_{r}_{v}"] = ("RACEICON.LBX", r * 13 + v + 6)
    return out


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    names = sorted({n for n, _e in wanted().values()} | {"FONTS.LBX"})
    for name in names:
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/invasion_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    files = {k: lbx.read_entries(v) for k, v in paths.items()}
    take = wanted()
    for stem, (name, entry) in take.items():
        if entry >= len(files[name]):
            sys.exit(f"{paths[name]} holds {len(files[name])} entries; "
                     f"{stem} needs {entry}")
    palette = lbx.screen_palette(
        files["FONTS.LBX"][POPUP_PALETTE][:PALETTE_BYTES])
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The invasion's pictures — the ground combat's troops, "
                  "its frame and explosions, the colony combat popup's "
                  "icons, planets and colonists, and the popup's palette — "
                  "out of the player's own Master of Orion 2. Never "
                  "committed, never shipped (decisions 38, 40, 42). Rebuild "
                  "with tools/invasion_art_extract.py."),
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
    glass = files["FONTS.LBX"][0][:GLASS_COUNT * 4]
    with open(os.path.join(out, "glass.json"), "w", encoding="utf-8") as fh:
        json.dump([list(glass[i * 4:i * 4 + 4]) for i in range(GLASS_COUNT)],
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
