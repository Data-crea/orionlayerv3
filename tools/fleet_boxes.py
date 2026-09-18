#!/usr/bin/env python3
"""Seed `screens/fleets/boxes.json` from the original's own rectangles.

    python3 tools/fleet_boxes.py            # print what it would write
    python3 tools/fleet_boxes.py --write    # write the file

**RUN ONCE, THEN F5 OWNS THE FILE.** This is not `tools/frame_holes.py`:
that one re-derives a cutout screen's boxes from its frame every time the
frame changes and the smoke test holds the two together, which is
decision 3. Decision 3 does NOT apply to the Fleets screen — its frame
has one opening and nothing inside it is a cutout. So this tool places
the original's sixteen rectangles once, as one group under one factor,
and after that `boxes.json` is what the person dragging boxes in F5
leaves behind. Re-running it with `--write` throws those edits away, and
it says so before it does.

The geometry it places is `screens/fleets/fltgeom.py`, which cites the
engine line for every number; the opening it places them in is
`screens/fleets/layout.json`. This file holds neither.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from screens.fleets import fltgeom  # noqa: E402

SCREEN_DIR = os.path.join(ROOT, "screens", "fleets")

#: The resolutions the file carries. The frame is plain-scaled over the
#: reference area at every window size, so the seat is the SAME in
#: reference pixels at both — they are written separately only so that
#: F5 can tune one without moving the other, which is what every other
#: screen's `boxes.json` offers.
RESOLUTIONS = ["1920x1080", "2560x1440"]

#: Decision 34: everything here groups, nothing here frames a picture.
#: `layout.json` `regions._skin_note` carries the argument.
SKIN = {"skin": "thin_border"}


def opening():
    with open(os.path.join(SCREEN_DIR, "layout.json"), encoding="utf-8") as f:
        return json.load(f)["frame"]["opening"]


def entries():
    """The sixteen boxes, regions first so the F5 list reads outside-in."""
    seated = fltgeom.seat_regions(opening())
    order = list(fltgeom.REGIONS) + list(fltgeom.CONTROLS)
    return [{"name": name, "rect": seated[name], "style": dict(SKIN)}
            for name in order]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="write boxes.json (overwrites F5 edits)")
    args = ap.parse_args()

    boxes = entries()
    path = os.path.join(SCREEN_DIR, "boxes.json")
    f, dx, dy = fltgeom.seat(opening())
    print(f"opening {opening()}  factor {f:.6f}  offset {dx:.1f}, {dy:.1f}")
    for box in boxes:
        print(f"  {box['name']:<14} {box['rect']}")

    if not args.write:
        print("\n(dry run — pass --write to write the file)")
        return 0
    if os.path.exists(path):
        print(f"\nOVERWRITING {path} — any F5 edits in it are lost.")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({key: boxes for key in RESOLUTIONS}, fh, indent=2)
        fh.write("\n")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
