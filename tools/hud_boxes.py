#!/usr/bin/env python3
"""The galaxy map's boxes, written from the HUD's measured layout.

    python tools/hud_boxes.py            # print what would be written
    python tools/hud_boxes.py --write    # update screens/galaxy_map/boxes.json

Decision 3 cut these boxes out of `frame.png`'s holes; decision 71
superseded that, and they come from `tools/hud_measure.galaxy_layout`
now — the places Data's HUD gives the info panel, its rows, the six nav
buttons and TURN. The smoke test holds `boxes.json` to this tool, so a
box dragged by hand is a box that has left its place in the artwork.

**A regenerator keeps what it did not create** (decision 3's rule, kept):
the boxes below are the ones this tool owns; every other box in the
file — the help popup, the system window, the fleet box — is written
back verbatim, and the count kept is printed.

What is OURS in here, and named: `MAP_GAP`, the clearance between the
star map and the HUD; `ROW_PAD`, the text inset inside a panel row. Both
are chosen, not measured (decision 53: Data's to change).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hud_cut  # noqa: E402
import hud_measure  # noqa: E402

ROOT = hud_measure.ROOT
BOXES = os.path.join(ROOT, "screens", "galaxy_map", "boxes.json")

#: Reference px between the star map and the panel / the nav row: the
#: map's floor runs to the screen's top and left edge and stops this far
#: short of the HUD, so no star is drawn under a button.
MAP_GAP = 6
#: Reference px of breathing room inside a panel row, above and below
#: its text. It lives in the galaxy map's layout.json, because the
#: screen draws each separator that far above its row's text box; one
#: number, two readers.
with open(os.path.join(ROOT, "screens", "galaxy_map", "layout.json"),
          encoding="utf-8") as _f:
    ROW_PAD = json.load(_f)["sidebar_row_pad"]

ROWS = ["stardate", "treasury", "command", "food", "freighters", "research"]
NAV = ["colonies", "planets", "fleets", "leaders", "races", "info"]
#: The text's font_scale in every row: sized against Data's mockup,
#: whose label reads 13 ref px of cap height and whose value 21.
TEXT_STYLE = {"font_scale": 1.2, "align": "left"}


def owned(layout=None, icons=None):
    """name -> box dict, for every box this tool owns."""
    g = layout or hud_measure.measure()["galaxy"]
    a = hud_cut.load() if icons is None else None
    px0, py0, px1, py1 = g["panel"]
    out = {}
    # THE BAR SITS ON THE BOTTOM EDGE — work order 170. The HUD image
    # carries 137 transparent rows under its bar, and 169 kept them as
    # layout: the bar ended 54 ref px above the bottom. The bar moves
    # down as one piece until its lowest edge line (TURN's) is the
    # HUD's own screen-edge margin (`edge_margin`, measured on the
    # panel's right side) above the bottom, and it hangs from the
    # WINDOW's bottom edge (`anchor_v: bottom`), so a window taller
    # than 16:9 keeps it there too.
    drop = (1080 - g["edge_margin"]) - g["turn"][3]
    nav_top, nav_bottom = g["nav_top"] + drop, g["nav_bottom"] + drop
    tx0, ty0, tx1, ty1 = g["turn"]
    ty0, ty1 = ty0 + drop, ty1 + drop
    # THE MAP LIES IN THE FREE SPACE — work order 170: below the title
    # plate, above the bar, left of the panel, `MAP_GAP` clear of each;
    # it stretches with the window between plate and bar.
    plate_bottom = hud_measure.ref(hud_cut.TITLE[3] - hud_cut.TITLE[1], 0)
    map_top = plate_bottom + MAP_GAP
    out["map_area"] = {"name": "map_area",
                       "rect": [0, map_top, px0 - MAP_GAP,
                                ty0 - MAP_GAP - map_top],
                       "anchor_v": "stretch",
                       "style": {"font_scale": 1.0}}
    out["sidebar"] = {"name": "sidebar",
                      "rect": [px0, py0, px1 - px0, py1 - py0],
                      "style": {"font_scale": 1.3}}
    st = json.load(open(hud_measure.STYLE, encoding="utf-8"))["measured"]
    inset_l = st["separator"]["inset_left"]
    inset_r = st["separator"]["inset_right"]
    bands = [py0] + g["separators"] + [py1]
    for i, key in enumerate(ROWS):
        top, bot = bands[i], bands[i + 1]
        x = round(px0 + inset_l)
        right = round(px1 - inset_r)
        if key == "stardate":
            ib = None
        else:
            b = (icons[key] if icons is not None
                 else hud_cut.find_box(a, *hud_cut.ICONS[key]))
            ib = [hud_measure.ref(v, 0) for v in b]
            # Inside its own band, less the row pad: the cut piece's box
            # carries a transparent margin, and the microscope's reached
            # past the panel's bottom edge with it.
            ib[1] = max(ib[1], top + ROW_PAD)
            ib[3] = min(ib[3], bot - ROW_PAD)
        text_w = (ib[0] - 4 - x) if ib else (right - x)
        out[f"sb_{key}_text"] = {
            "name": f"sb_{key}_text",
            "rect": [x, top + ROW_PAD, text_w, bot - top - 2 * ROW_PAD],
            "style": dict(TEXT_STYLE)}
        if ib:
            out[f"sb_{key}_icon"] = {
                "name": f"sb_{key}_icon",
                "rect": [ib[0], ib[1], ib[2] - ib[0], ib[3] - ib[1]]}
    h = nav_bottom - nav_top
    for key, c in zip(NAV, g["nav_centres"]):
        w = g["nav_width"]
        out[f"nav_{key}"] = {"name": f"nav_{key}",
                             "rect": [round(c - w / 2), nav_top, w, h],
                             "anchor_v": "bottom",
                             "style": {"font_size": 18}}
    out["nav_turn"] = {"name": "nav_turn",
                       "rect": [tx0, ty0, tx1 - tx0, ty1 - ty0],
                       "anchor_v": "bottom",
                       "style": {"font_size": 26}}
    return out


def merged(current, mine):
    """The file's list with `mine` replacing its namesakes, in place,
    new ones appended; and how many foreign boxes were kept."""
    out, seen, kept = [], set(), 0
    for box in current:
        if box["name"] in mine:
            out.append(mine[box["name"]])
            seen.add(box["name"])
        else:
            out.append(box)
            kept += 1
    out += [mine[n] for n in mine if n not in seen]
    return out, kept


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    mine = owned()
    with open(BOXES, encoding="utf-8") as f:
        data = json.load(f)
    for key in data:
        data[key], kept = merged(data[key], mine)
    if not args.write:
        print(json.dumps(list(mine.values()), indent=1))
        return 0
    with open(BOXES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"wrote {len(mine)} boxes to each of {len(data)} resolution "
          f"lists; kept {kept} this tool does not own")
    return 0


if __name__ == "__main__":
    sys.exit(main())
