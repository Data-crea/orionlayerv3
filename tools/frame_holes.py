"""Derive box rects from the transparent cutouts of a frame image.

Usage:
    python tools/frame_holes.py screens/<screen>/assets/frame.png [--write]

Prints every transparent hole (alpha < 16) larger than MIN_AREA in
image pixels and as a 1920x1080 reference rect, assuming the image
is stretched over the whole reference area. With --write, that
screen's boxes.json is regenerated from the holes (both stored
resolutions), keeping any style block already present per box.

Hole → box name mapping is by position, not by index, and there is
one rule per screen, chosen from the path (screens/<name>/assets/):

  galaxy_map      the largest hole is the map, the topmost narrow one
                  the title, the two on the right the sidebar and the
                  TURN button, the bottom row the six nav buttons
  colony_summary  four rows of holes, grouped by vertical overlap:
                  the header band, the list, the lower band's four
                  panels (planet_info, planet_output, galaxy_inset,
                  empire_stats, left to right) and the sort row's two
                  (sort_bar, return)
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import REF_W, REF_H  # noqa: E402

MIN_AREA = 2000
ALPHA_LIMIT = 16
#: Reference-pixel bleed so content covers the anti-aliased rim.
BLEED = 2
NAV_KEYS = ["colonies", "planets", "fleets", "leaders", "races", "info"]


def find_holes(path):
    from scipy import ndimage
    a = np.array(Image.open(path).convert("RGBA"))[:, :, 3]
    lab, n = ndimage.label(a < ALPHA_LIMIT)
    holes = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        x, y, w, h = xs.start, ys.start, xs.stop - xs.start, ys.stop - ys.start
        if w * h < MIN_AREA:
            continue
        if x == 0 or y == 0 or xs.stop == a.shape[1] or ys.stop == a.shape[0]:
            continue                      # touches the border: outside
        holes.append((x, y, w, h))
    return a.shape[1], a.shape[0], holes


SORT_KEYS = ["name", "population", "food", "industry", "science",
             "producing", "bc"]
# Left to right, so the galaxy map is the RIGHTMOST of the three —
# derived from the source, not from position. The original draws its
# small galaxy map with MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0,
# 0x17c, 0x15d, 0x80, 0x5b, ...) (colsum.cpp:415), whose signature
# (movebox.cpp:4-9) reads those as x_base 380, y_base 349, width 128,
# height 91; COLSUM::Colsum_Connect_Galaxy_Map_Stars_ passes the same
# four to Get_Galaxy_Map_Star_XY_ (colsum.cpp:734-735). Scaled to the
# reference area that native rect is (1140, 785, 384, 205) — centre x
# 1332, which is the third hole, not the second. The middle hole
# covers native x ~193-347, where the original draws its production
# and morale sprite column (Draw_Colony_Wee_Prod_(..., 106, y_pos,
# 366, 20), colsum.cpp:1171-1176) — values output_panel already
# answers for, so that one is the spare. A smoke check asserts the
# rule rather than this list, so a redrawn frame cannot quietly
# reassign the names by position again.
PANEL_KEYS = ["output_panel", "spare_panel", "galaxy_inset"]


def _split_common(holes, main_name):
    """The part both frames share: main area, title, right column."""
    holes = sorted(holes, key=lambda r: r[2] * r[3], reverse=True)
    named = {main_name: holes[0]}
    rest = holes[1:]
    title = min(rest, key=lambda r: r[1])
    named["title"] = title
    rest.remove(title)
    main_right = named[main_name][0] + named[main_name][2]
    right = sorted([r for r in rest if r[0] > main_right], key=lambda r: r[1])
    rest = [r for r in rest if r not in right]
    return named, right, rest


def name_holes_galaxy_map(holes):
    named, right, rest = _split_common(holes, "map_area")
    named["sidebar"], named["nav_turn"] = right[0], right[1]
    bottom = sorted(rest, key=lambda r: r[0])
    for key, r in zip(NAV_KEYS, bottom):
        named[f"nav_{key}"] = r
    return named


#: The lower band, left to right. Unlike the old frame's three, these
#: four are named by POSITION AND CONFIRMED BY THE SOURCE: the galaxy
#: inset's native rect (380, 349, 128, 91) is centre x 444 of 640,
#: which is the THIRD of the four, and the empire readouts the fourth.
BAND_KEYS = ["planet_info", "planet_output", "galaxy_inset", "empire_stats"]


#: WHICH BOX NAMES EACH RULE CAN PRODUCE — the vocabulary, not a
#: second copy of the geometry.
#:
#: Added 9 September 2026 for the F5 editor, which has to know whether
#: a box is a frame CUTOUT before it offers a resize handle: decision 3
#: says a cutout's rect comes from the artwork through this tool, and
#: dragging one by hand slides content out from under its hole. The
#: editor must be able to ask that question without a plate on disk and
#: without running the namer, so the answer is a name list.
#:
#: **BUILT FROM THE SAME CONSTANTS THE RULES BUILD FROM**, never typed
#: out beside them — `NAV_KEYS` and `BAND_KEYS` appear once each and
#: both the namer and this set read them. A hand-written list would be
#: the second copy this project keeps paying for, and it would go stale
#: the first time a plate gained a hole.
#:
#: THE ALTERNATIVE WAS A FLAG IN `boxes.json` AND IT WAS REFUSED.
#: `Box.locked` exists in the data model and is serialized, and nothing
#: has ever read it. Filling it in would mean typing which boxes are
#: cutouts into every screen's box file — a second copy of what this
#: module already knows, and exactly decision 3's failure.
RULE_NAMES = {
    "galaxy_map": {"title", "map_area", "sidebar", "nav_turn"}
                  | {f"nav_{k}" for k in NAV_KEYS},
    "colony_summary": {"header", "list_area", "sort_bar", "return"}
                      | set(BAND_KEYS),
}


def cutout_names(screen):
    """The names `screen`'s rule can produce, or an empty set.

    A screen with no rule has no cutout-derived boxes at all — every
    box on it is hand-placed — which is a real answer and not a
    missing one.
    """
    return RULE_NAMES.get(screen, set())


def name_holes_colony_summary(holes):
    """The built plate's eight windows, by shape and position.

    **REWRITTEN 7 September 2026 FOR THE STAGE A3 PLATE, and the old
    rule could not have been adapted.** The shipped frame had 14
    holes: a title, a right-hand sidebar, a right-hand RETURN, SEVEN
    sort buttons and three bottom panels. The plate has 8: a header
    band, the list, four panels in one lower band, ONE sort bar and
    RETURN beside it. Nothing on the right of the list any more, one
    sort hole instead of seven, and a header where the title was — so
    `_split_common`, which exists to find a title and a right column,
    does not apply here at all and is not called.

    The shape is read off `layout_reference.json`'s own geometry
    rather than off pixel thresholds: rows are found by grouping on y,
    which is what makes the rule survive a plate rebuilt at a
    different ring or with different gaps.
    """
    rows = _rows(holes)
    if len(rows) != 4:
        raise SystemExit(
            f"expected 4 rows of holes (header, list, lower band, sort "
            f"row), found {len(rows)}: {rows}")
    header, listing, band, sort = rows
    if len(header) != 1 or len(listing) != 1:
        raise SystemExit("the header and the list must be one hole each")
    if len(band) != len(BAND_KEYS):
        raise SystemExit(
            f"the lower band has {len(band)} holes, expected "
            f"{len(BAND_KEYS)}: {BAND_KEYS}")
    if len(sort) != 2:
        raise SystemExit("the sort row must be the sort bar and RETURN")
    named = {"header": header[0], "list_area": listing[0]}
    for key, r in zip(BAND_KEYS, band):
        named[key] = r
    named["sort_bar"], named["return"] = sort
    return named


def _rows(holes):
    """Holes grouped into rows by vertical overlap, top to bottom.

    Overlap rather than a y threshold: the galaxy inset is 20 px
    shorter than its band and centred in it (`_lower_band_note`), so
    its top is not its neighbours' and a tolerance would be a number
    somebody has to keep in step with the layout.
    """
    rows = []
    for r in sorted(holes, key=lambda r: (r[1], r[0])):
        top, bottom = r[1], r[1] + r[3]
        for row in rows:
            if any(top < q[1] + q[3] and bottom > q[1] for q in row):
                row.append(r)
                break
        else:
            rows.append([r])
    return [sorted(row, key=lambda r: r[0]) for row in rows]


RULES = {"galaxy_map": name_holes_galaxy_map,
         "colony_summary": name_holes_colony_summary}


def screen_of(path):
    """screens/<name>/assets/frame.png -> <name>, else None."""
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    if "assets" in parts and parts.index("assets") >= 1:
        return parts[parts.index("assets") - 1]
    return None


def name_holes(holes, screen="galaxy_map"):
    return RULES[screen](holes)


def to_ref(rect, img_w, img_h, bleed=BLEED):
    sx, sy = REF_W / img_w, REF_H / img_h
    x, y, w, h = rect
    return [int(round(x * sx)) - bleed, int(round(y * sy)) - bleed,
            int(round(w * sx)) + 2 * bleed, int(round(h * sy)) + 2 * bleed]


def main():
    path = sys.argv[1]
    screen = screen_of(path)
    if screen not in RULES:
        print(f"no naming rule for screen {screen!r}; known: "
              + ", ".join(RULES))
        return
    img_w, img_h, holes = find_holes(path)
    named = name_holes(holes, screen)
    print(f"image {img_w}x{img_h}, {len(holes)} holes")
    for k, r in named.items():
        print(f"  {k:14s} img={r}  ref={to_ref(r, img_w, img_h)}")

    if "--write" not in sys.argv:
        return
    # The plate lives one level deeper than the shipped frame
    # (assets/frames/frame_WxH.png), so walk up to the screen dir by
    # name rather than by a fixed number of dirnames.
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    screen_dir = os.sep.join(parts[:parts.index("assets")])
    boxes_path = os.path.join(screen_dir, "boxes.json")
    with open(boxes_path) as f:
        data = json.load(f)
    derived = {n for n in named if n != "title"}
    for res, boxes in data.items():
        styles = {b["name"]: b for b in boxes}
        out = []
        for name, r in named.items():
            if name == "title":
                continue
            old = styles.get(name, {})
            entry = {"name": name, "rect": to_ref(r, img_w, img_h),
                     "role": old.get("role", ["display"])}
            if "style" in old:
                entry["style"] = old["style"]
            out.append(entry)
        # Boxes that are not cutouts survive verbatim. The sidebar
        # readouts (sb_*) are placed by hand in the editor and have no
        # hole to be derived from; regenerating the cutout boxes must
        # not delete them.
        kept = [b for b in boxes if b["name"] not in derived]
        if kept:
            print(f"  kept {len(kept)} non-cutout box(es) in {res}")
        data[res] = out + kept
    with open(boxes_path, "w") as f:
        json.dump(data, f, indent=2)
    print("wrote", boxes_path)


if __name__ == "__main__":
    main()
