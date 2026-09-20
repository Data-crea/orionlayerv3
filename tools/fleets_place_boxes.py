#!/usr/bin/env python3
"""Re-seat the six Fleets boxes that have no hole.

    python tools/fleets_place_boxes.py            # print what it would write
    python tools/fleets_place_boxes.py --write    # write boxes.json

Run it after `tools/frame_holes.py screens/fleets/assets/frame.png
--write`, which derives the thirty-two cutouts. Those two commands are
the whole of "the boxes follow the frame" for this screen.

**IT IS A SEEDER, AND RE-RUNNING IT THROWS AWAY F5's EDITS** — the
same bargain `tools/fleet_boxes.py` carried, and it says so below
before it writes. Run it when the frame changes SHAPE. The smoke test
does not hold these six to what this tool computes (Data,
20 September 2026: the seat is a starting point, not a cage); it
holds only that each is inside the hole it belongs to, so a drag in
the editor stands.

**THIS IS NOT `tools/fleet_boxes.py`**, which seated the original's
rectangles into one opening and must not be made to run again. Every
rule here is a rule against a HOLE, and it lives in
`screens/fleets/fltplaced.py` so that the smoke test can recompute it
without going through a tool (decision 5: nothing computes a
rectangle twice).

It overwrites six boxes and touches nothing else — the thirty-two
cutouts, `scroll_column`, `help_popup` and every style survive.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from screens.fleets import fltplaced  # noqa: E402

BOXES = os.path.join(ROOT, "screens", "fleets", "boxes.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    with open(BOXES, encoding="utf-8") as fh:
        data = json.load(fh)

    changed = 0
    for res, boxes in data.items():
        by = {b["name"]: b["rect"] for b in boxes if "rect" in b}
        want = fltplaced.placed(by)
        bad = fltplaced.contained(by, want)
        if bad:
            raise SystemExit(f"{res}: " + "; ".join(bad))
        for box in boxes:
            if box["name"] in want and box["rect"] != want[box["name"]]:
                print(f"  {res} {box['name']:16s} "
                      f"{box['rect']} -> {want[box['name']]}")
                box["rect"] = want[box["name"]]
                changed += 1
        for name in fltplaced.NAMES:
            if name not in by:
                raise SystemExit(f"{res}: no {name} box to re-seat")

    if not changed:
        print("every placed box already sits where its holes put it")
        return 0
    if not args.write:
        print(f"\n({changed} box(es) would move — pass --write)")
        return 0
    print("\nOVERWRITING the six placed boxes — any F5 edit to them "
          "is lost. The thirty-two cutouts and every style survive.")
    with open(BOXES, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print(f"wrote {BOXES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
