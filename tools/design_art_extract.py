#!/usr/bin/env python3
"""Extract the Ship Designer's own artwork from the player's MOO2.

    python tools/design_art_extract.py                 # search the usual dirs
    python tools/design_art_extract.py /path/to/DATA   # a folder holding the LBX
    python tools/design_art_extract.py --list          # say what it would take

Work order 185. **The Fleets extractor's rule** (`tools/fleet_art_extract.py`,
decision 38): the raw LBX entry blobs and the raw palette, untouched;
decoding at load time in `screens/ship_design/sdart.py` through
`core/lbx.py`. **NEVER COMMITTED, NEVER SHIPPED** (decisions 40, 42): the
output directory is gitignored.

WHAT IT TAKES, AND WHY EACH:

  DESIGN.LBX  33..37  the weapon picker's five firing-arc pictures
                      (`_weapons_arc_pict_seg[5]`, loaded in
                      `Load_Design_Screen_Pictures_`, design_main.cpp:
                      522-561, drawn in the arc box);
              38..42  the five arc words and
              43..47  the five rack words ("Shot x2" …), each with its
                      lit / offered frames — their words are in no
                      string table;
              22..25  the four filter buttons (BEAM, MISSILE, BOMB,
                      SPECIAL), two frames, the status — the same reason.
                      The page's and the pickers' CHROME — background,
                      buttons, box sprites — is NOT taken: decision 71
                      draws every screen's frame with the HUD blocks.
  FONTS.LBX   5       the palette the designer is drawn in: the screen
                      calls `fonts::Load_Palette_(4, …)` on entry, and the
                      loader reads `palette_id + 1` (the Fleets
                      extractor's arithmetic, fonts.cpp).

The ship pictures are the Fleets screen's extraction (SHIPS.LBX, the same
entries); `sdart` reads them from there and decodes them in THIS palette
with the owner's ship ramp, as the designer draws them.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import lbx  # noqa: E402

FORMAT_VERSION = 2
DEFAULT_OUT = os.path.join(ROOT, "screens", "ship_design", "assets",
                           "gamedata")
DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]
#: DESIGN.LBX entries of the five arc pictures.
ARC_FIRST, ARC_COUNT = 33, 5
#: The groups taken, each (folder, first entry, count), in the load
#: order `Load_Design_Screen_Pictures_` reads them (idx counts on from 12).
GROUPS = (("arcs", ARC_FIRST, ARC_COUNT), ("arc_words", 38, 5),
          ("rack_words", 43, 5), ("filters", 22, 4))
#: FONTS.LBX entry: `Load_Palette_(4, …)` + 1.
PALETTE_ENTRY = 5
PALETTE_BYTES = 256 * 4


def find_lbx(folder, filename):
    for d in ([folder] if folder else DEFAULT_SEARCH):
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == filename.lower():
                return os.path.join(d, name)
    return None


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract(folder=None, out=DEFAULT_OUT, dry_run=False):
    paths = {}
    for name in ("DESIGN.LBX", "FONTS.LBX"):
        found = find_lbx(folder, name)
        if found is None:
            sys.exit(f"{name} not found. Give the folder that holds it:\n"
                     f"    python tools/design_art_extract.py "
                     f"/path/to/'Master of Orion 2'")
        paths[name] = found
    design = lbx.read_entries(paths["DESIGN.LBX"])
    fonts = lbx.read_entries(paths["FONTS.LBX"])
    last = max(first + count for _, first, count in GROUPS)
    if len(design) < last:
        sys.exit(f"{paths['DESIGN.LBX']} holds {len(design)} entries; the "
                 f"designer's pictures reach entry {last - 1}")
    if len(fonts) <= PALETTE_ENTRY or \
            len(fonts[PALETTE_ENTRY]) < PALETTE_BYTES:
        sys.exit(f"FONTS.LBX has no {PALETTE_BYTES}-byte entry "
                 f"{PALETTE_ENTRY}")
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The Ship Designer's pictures and palette, raw, out of "
                  "the player's own Master of Orion 2. Never committed, "
                  "never shipped (decisions 38, 40, 42). Rebuild with "
                  "tools/design_art_extract.py."),
        "source": {k: {"path": v, "sha256": _sha(v)} for k, v in paths.items()},
        "arcs": {"first": ARC_FIRST, "count": ARC_COUNT},
        "groups": {name: {"first": first, "count": count}
                   for name, first, count in GROUPS},
        "palette": {"entry": PALETTE_ENTRY, "bytes": PALETTE_BYTES},
    }
    if dry_run:
        return manifest
    for name, first, count in GROUPS:
        os.makedirs(os.path.join(out, name), exist_ok=True)
        for i in range(count):
            with open(os.path.join(out, name, f"{i}.bin"), "wb") as fh:
                fh.write(design[first + i])
    with open(os.path.join(out, "palette.bin"), "wb") as fh:
        fh.write(fonts[PALETTE_ENTRY][:PALETTE_BYTES])
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def main(argv):
    folder = next((a for a in argv if not a.startswith("--")), None)
    manifest = extract(folder, dry_run="--list" in argv)
    print(("would take" if "--list" in argv else "wrote") +
          f" {sum(g['count'] for g in manifest['groups'].values())} "
          f"designer pictures and FONTS palette "
          f"{manifest['palette']['entry']}" +
          ("" if "--list" in argv else f" -> {DEFAULT_OUT}"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
