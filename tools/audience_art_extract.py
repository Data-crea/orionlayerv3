#!/usr/bin/env python3
"""Extract the diplomacy audience's own artwork from the player's MOO2.

    python tools/audience_art_extract.py                 # search the usual dirs
    python tools/audience_art_extract.py /path/to/DATA   # a folder holding the LBX
    python tools/audience_art_extract.py --list          # say what it would take

Work order 185 part 10. **The Fleets extractor's rule** (decision 38): the
raw LBX entry blobs, untouched; decoding at load time in
`screens/audience/auart.py` through `core/lbx.py`. **NEVER COMMITTED,
NEVER SHIPPED** (decisions 40, 42): the output directory is gitignored.

WHAT IT TAKES, AND WHY EACH (DIPLOMAT.LBX, per race r, 0..12):

  r         the race's palette (a 24x24 cursor picture carrying the
            screen's palette: `Diplomacy_Mouse_Init_` draws it with
            `Draw_Palette_`, dip_scrn_main.cpp:465-480)
  2r + 13   the room (`Setup_Back_Page_`, :1645-1657) — frame 0 is the
            room; its later frames are the fade-in's
  2r + 14   the ambassador (`Setup_Ambassador_Pic_`, :1665-1678), drawn at
            (0, 0) over the room — the talking loop's frames

The text box, the list and the cursor are NOT taken: decision 71 draws
every panel with the HUD blocks.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import lbx  # noqa: E402

FORMAT_VERSION = 1
RACES = 13
DEFAULT_OUT = os.path.join(ROOT, "screens", "audience", "assets",
                           "gamedata")
DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]
#: Each group: (folder, the entry of race r).
GROUPS = (("palettes", lambda r: r), ("rooms", lambda r: 2 * r + 13),
          ("ambassadors", lambda r: 2 * r + 14))


def find_lbx(folder, filename="DIPLOMAT.LBX"):
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
    path = find_lbx(folder)
    if path is None:
        sys.exit("DIPLOMAT.LBX not found. Give the folder that holds it:\n"
                 "    python tools/audience_art_extract.py "
                 "/path/to/'Master of Orion 2'")
    entries = lbx.read_entries(path)
    if len(entries) < 2 * (RACES - 1) + 15:
        sys.exit(f"{path} holds {len(entries)} entries; the audience needs "
                 f"{2 * (RACES - 1) + 15}")
    manifest = {
        "format": FORMAT_VERSION,
        "_what": ("The diplomacy audience's rooms, ambassadors and palettes, "
                  "raw, out of the player's own Master of Orion 2. Never "
                  "committed, never shipped (decisions 38, 40, 42). Rebuild "
                  "with tools/audience_art_extract.py."),
        "source": {"DIPLOMAT.LBX": {"path": path, "sha256": _sha(path)}},
        "races": RACES,
    }
    if dry_run:
        return manifest
    for name, entry in GROUPS:
        os.makedirs(os.path.join(out, name), exist_ok=True)
        for r in range(RACES):
            with open(os.path.join(out, name, f"{r}.bin"), "wb") as fh:
                fh.write(entries[entry(r)])
    with open(os.path.join(out, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    return manifest


def main(argv):
    folder = next((a for a in argv if not a.startswith("--")), None)
    manifest = extract(folder, dry_run="--list" in argv)
    print(("would take" if "--list" in argv else "wrote") +
          f" {manifest['races']} races' rooms, ambassadors and palettes" +
          ("" if "--list" in argv else f" -> {DEFAULT_OUT}"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
