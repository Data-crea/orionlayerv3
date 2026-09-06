#!/usr/bin/env python3
"""Extract the 48 galaxy-map nebula sprites from starbg.lbx.

The original stores 12 nebula types x 4 zoom variants in starbg.lbx,
entries 6..53 (entry = type * 4 + zoom + 6, mapgen.cpp
Load_Nebula_Pictures_). Like the star sprites, the four zoom variants
are separate pre-rendered drawings, never scaled at runtime
(mainscr.cpp Draw_Nebulae_ draws at native size).

Zoom variant 3 doubles as the GAMEPLAY geometry: geo.cpp
Point_Is_In_Nebula_N_ maps world coordinates through /3 onto that
sprite's raw pixel grid and treats palette index > 5 as "inside the
nebula". This tool therefore also writes that mask so HD artwork can
be shaped to match it.

The container and the frame decoders live in `core/lbx.py` — this
tool was one of the two that used to own a private copy, and
`raceicon_extract.py` was the third reader that made two copies
indefensible. The formats and their source citations are documented
there.

Usage:
  python tools/nebula_extract.py                       # search default dirs
  python tools/nebula_extract.py /path/to/starbg.lbx
  python tools/nebula_extract.py --out screens/galaxy_map/assets/nebula_ref

Output (per type t, zoom z):
  <out>/type_<t>/zoom_<z>.png        RGBA sprite (embedded palette or
                                     grayscale-by-index fallback)
  <out>/type_<t>/mask.png            gameplay mask from zoom 3
                                     (white = index > 5, geo.cpp rule)
  <out>/summary.txt                  dimensions, flags, frame counts

Requires: Pillow (pip install pillow --break-system-packages).
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import lbx  # noqa: E402

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run: pip install pillow --break-system-packages")

NEBULA_FIRST_ENTRY = 6          # mapgen.cpp: type * 4 + frame + 6
NEBULA_TYPES = 12
NEBULA_ZOOMS = 4
GAMEPLAY_ZOOM = 3               # geo.cpp uses variant [3]
GAMEPLAY_THRESHOLD = 5          # geo.cpp: pixel_data[...] > 5

DEFAULT_SEARCH = [
    os.path.expanduser("~/Master of Orion 2"),
    os.path.expanduser("~/Master of Orion 2/DATA"),
    ".",
]


def find_lbx(explicit):
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        sys.exit(f"File not found: {explicit}")
    for d in DEFAULT_SEARCH:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.lower() == "starbg.lbx":
                return os.path.join(d, name)
    sys.exit("starbg.lbx not found. Pass the path explicitly:\n"
             "  python tools/nebula_extract.py /path/to/starbg.lbx")


#: Anchored to the project, not to the working directory. `--out`
#: defaulted to a bare "nebula_ref" and therefore landed wherever the
#: shell happened to be — for one run, the repository root, where git
#: staged 61 files nobody meant to commit while the smoke test went
#: on reporting the references as absent. The identical fault was
#: fixed in help_extract.py days earlier and not looked for here.
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screens", "galaxy_map", "assets", "nebula_ref")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lbx", nargs="?", help="path to starbg.lbx")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output directory (default: the project's own "
                         "screens/galaxy_map/assets/nebula_ref)")
    args = ap.parse_args()

    path = find_lbx(args.lbx)
    try:
        entries = lbx.read_entries(path)
    except lbx.LbxError as exc:
        sys.exit(f"{exc} Is this really starbg.lbx?")
    needed = NEBULA_FIRST_ENTRY + NEBULA_TYPES * NEBULA_ZOOMS
    if len(entries) < needed:
        sys.exit(f"{path} has only {len(entries)} entries, "
                 f"{needed} expected. Wrong file version?")

    os.makedirs(args.out, exist_ok=True)
    lines = [f"source: {path}", f"entries: {len(entries)}", ""]
    ok = 0

    for t in range(NEBULA_TYPES):
        type_dir = os.path.join(args.out, f"type_{t:02d}")
        os.makedirs(type_dir, exist_ok=True)
        for z in range(NEBULA_ZOOMS):
            entry_idx = t * NEBULA_ZOOMS + z + NEBULA_FIRST_ENTRY
            label = f"type {t} zoom {z} (entry {entry_idx})"
            blob = entries[entry_idx]
            try:
                hdr = lbx.parse_header(blob, label)
            except lbx.LbxError as exc:
                sys.exit(str(exc))
            width, height, frames = hdr.width, hdr.height, hdr.frame_count
            palette = lbx.read_palette(blob, frames) if hdr.has_palette else {}
            if hdr.mode not in (lbx.DRAW_MODE_BITMAP, lbx.DRAW_MODE_ANIMATED):
                lines.append(f"{label}: unsupported draw mode {hdr.mode} "
                             f"— skipped")
                continue
            pixels = lbx.decode_frame(blob, hdr, 0)
            if pixels is None:
                lines.append(f"{label}: frame data truncated — skipped")
                continue

            Image.frombytes("RGBA", (width, height),
                            lbx.rgba_bytes(pixels, palette)).save(
                os.path.join(type_dir, f"zoom_{z}.png"))
            lines.append(f"{label}: {width}x{height} frames={frames} "
                         f"flags=0x{hdr.flags:02X} palette={len(palette)}")
            ok += 1

            if z == GAMEPLAY_ZOOM:
                mask = Image.new("L", (width, height))
                mask.putdata([255 if p > GAMEPLAY_THRESHOLD else 0
                              for p in pixels])
                mask.save(os.path.join(type_dir, "mask.png"))
                lines.append(f"  gameplay mask written (index > "
                             f"{GAMEPLAY_THRESHOLD}, world/3 grid)")

    summary = os.path.join(args.out, "summary.txt")
    with open(summary, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{ok}/{NEBULA_TYPES * NEBULA_ZOOMS} sprites extracted to "
          f"{os.path.abspath(args.out)} — details in "
          f"{os.path.abspath(summary)}")
    print("The smoke test's nebula shape and weight assertions read "
          "this directory.")
    if ok < NEBULA_TYPES * NEBULA_ZOOMS:
        print("Some entries were skipped; see summary.txt.")


if __name__ == "__main__":
    main()
