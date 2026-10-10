#!/usr/bin/env python3
"""Extract the tactical battle's artwork from the player's own MOO2.

    python tools/combat_art_extract.py                 # search the usual dirs
    python tools/combat_art_extract.py /path/to/DATA   # a folder holding the LBX
    python tools/combat_art_extract.py --list          # say what it would take

Work order 197 C. **Decision 38's rule, not a PNG dump**: the raw LBX entry
blobs and the raw battle palette, decoded at load time by
`screens/combat/cbart.py` through `core/lbx.py` (its keyframe composition
included), so a fix to the decoder needs no re-extraction. **Never
committed, never shipped** (decisions 40 and 42): the output folder is
gitignored.

WHAT IT TAKES — every file whole, because which entries a battle needs is
known only when the wire says who fights (`dev:doc/combat_drawing_reading.md`
has the formulas):

  CMBTSHP.LBX   the ships, colour * 45 + picture (44 = the colour's ramp)
  MONSTER.LBX   monsters, their palettes and deaths
  CMBTPLNT.LBX  the battle planet, climate * 6 + size (+5 = its palette)
  CMBTMISL.LBX  missiles, torpedoes, bombs, type * 16 + facing
  CMBTFGTR.LBX  fighters, type * 16 + facing
  CMBTSFX.LBX   explosions, warp-out, stasis, tractor, web, blasts
  BEAMS.LBX     muzzle and hit flashes, shield flares, the beam palette
  SPHERSFX.LBX  the spherical blasts
  COMBAT.LBX    the star layers (46, 47, 48; 35 in a nebula), the cursor
  SOUND.LBX     the battle's sounds, WAV entries by the engine's sound id
                (`Play_Sound_`, sound.cpp:1290-1341), played by HD since
                open fix 79 (`screens/combat/cbsound.py`, work order 212)
  FONTS.LBX 4   the battle palette (`Load_Palette_(3)`, combinit.cpp:661)

An absent file is a state, not an error: the battle screen says how to get
it and draws what it can without it.
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import lbx  # noqa: E402
from core import paths  # noqa: E402 — work order 229 D: the game folder

FORMAT_VERSION = 1
DEFAULT_OUT = os.path.join(ROOT, "screens", "combat", "assets", "gamedata")
DEFAULT_SEARCH = [
    paths.game_dir(),
    os.path.join(paths.game_dir(), "DATA"),
    ".",
]
FILES = ("CMBTSHP.LBX", "MONSTER.LBX", "CMBTPLNT.LBX", "CMBTMISL.LBX",
         "CMBTFGTR.LBX", "CMBTSFX.LBX", "BEAMS.LBX", "SPHERSFX.LBX",
         "COMBAT.LBX", "SOUND.LBX")
PALETTE_FILE, PALETTE_ENTRY, PALETTE_BYTES = "FONTS.LBX", 4, 256 * 4


def find_lbx(folder, filename):
    roots = [folder] if folder else DEFAULT_SEARCH
    for d in roots:
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == filename.lower():
                return os.path.join(d, name)
    return None


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    """Write every entry of FILES and the palette. Returns the manifest."""
    paths = {}
    for name in FILES + (PALETTE_FILE,):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/combat_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    entries = {name: lbx.read_entries(paths[name]) for name in FILES}
    fonts = lbx.read_entries(paths[PALETTE_FILE])
    if len(fonts) <= PALETTE_ENTRY or \
            len(fonts[PALETTE_ENTRY]) < PALETTE_BYTES:
        sys.exit(f"FONTS.LBX entry {PALETTE_ENTRY} is not a 256-colour "
                 f"palette.")
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The tactical battle's artwork and palette, raw, out of "
                  "the player's own Master of Orion 2. Never committed, "
                  "never shipped (decisions 38, 40, 42). Rebuild with "
                  "tools/combat_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "files": {name: len(entries[name]) for name in FILES},
        "palette": {"file": PALETTE_FILE, "entry": PALETTE_ENTRY,
                    "bytes": PALETTE_BYTES},
    }
    if dry_run:
        return manifest
    for name in FILES:
        d = os.path.join(out, name.split(".")[0].lower())
        os.makedirs(d, exist_ok=True)
        for i, blob in enumerate(entries[name]):
            with open(os.path.join(d, f"{i}.bin"), "wb") as fh:
                fh.write(blob)
    with open(os.path.join(out, "palette.bin"), "wb") as fh:
        fh.write(fonts[PALETTE_ENTRY][:PALETTE_BYTES])
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args()
    m = extract(a.folder, a.out, dry_run=a.list)
    for name, n in m["files"].items():
        print(f"  {name:13s} {n:4d} entries")
    print(f"  palette: {PALETTE_FILE} entry {PALETTE_ENTRY}")
    if not a.list:
        print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
