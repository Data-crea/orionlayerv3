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
  colony_summary  MATCHED TO `layout_reference.json` BY OVERLAP, and
                  the four rows (header, list, the lower band's four
                  panels, the sort row's eight) are checked as a
                  SHAPE rather than used as an order. Left-to-right
                  order is the fallback for a plate with no reference
                  beside it, and it says so when it falls back.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ITS OWN DIRECTORY, EXPLICITLY — the same fault `frame_cut` records:
# `import frame_mask` resolves from a shell run because the script's
# directory is on the path, and not from a loader that addresses this
# file by path, which is how the smoke test reaches it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.config import REF_W, REF_H  # noqa: E402

import frame_mask  # noqa: E402  (same directory)

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
#: One box per sort key, named `sort_<key>` — DEVIATION, 12 September
#: 2026, reversing Stage A3's single `sort_bar`. Data's artwork cuts a
#: slot per key, so the division is geometry again; see
#: `layout_reference._sort_slots_note` and `colonysort`.
#:
#: DERIVED FROM `SORT_KEYS` AND NOT TYPED OUT, so the spelling rule
#: lives once. `colonysort.box_name` builds the same string from the
#: other end and a smoke check holds the two to each other.
SORT_BOX_KEYS = [f"sort_{k}" for k in SORT_KEYS]

#: `layout_reference.json` names a RECTANGLE, `boxes.json` names a
#: BOX, and two of them differ. The mapping is this module's own —
#: it is what `--write` writes and what the overlap match has to go
#: through — so it is stated once here rather than inferred at each
#: use. Anything absent maps to itself.
BOX_NAME = {"return_button": "return", "list": "list_area"}
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


def name_holes_galaxy_map(holes, size=None, reference=None):
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

#: The colony plate's four rows, by hole count. DERIVED from the key
#: lists above so it cannot disagree with them: a header, the list,
#: the lower band, and the sort row's seven slots plus RETURN.
ROW_SHAPE = [1, 1, len(BAND_KEYS), len(SORT_BOX_KEYS) + 1]


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
    "colony_summary": {"header", "list_area", "return"}
                      | set(BAND_KEYS) | set(SORT_BOX_KEYS),
}


def cutout_names(screen):
    """The names `screen`'s rule can produce, or an empty set.

    A screen with no rule has no cutout-derived boxes at all — every
    box on it is hand-placed — which is a real answer and not a
    missing one.
    """
    return RULE_NAMES.get(screen, set())


#: How the last colony naming was done, for whoever wants to print it.
#: A REPORT CHANNEL AND NOT STATE: nothing reads it to decide
#: anything, and the naming does not consult it. It exists because
#: "which rule named these holes" is the first question to ask of a
#: plate that came out wrong, and the answer was previously nowhere.
LAST_MATCH = None


def _overlap(a, b):
    x = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    y = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return x * y if x > 0 and y > 0 else 0


def reference_windows(screen, size):
    """`layout_reference.json`'s rectangles in IMAGE px, box-named.

    Returns {} when the file is not there — a plate can be handed to
    this module from anywhere, and a missing reference is a reason to
    fall back rather than to fail.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "screens", screen, "layout_reference.json")
    if not os.path.isfile(path) or not size:
        return {}
    _data, windows = frame_mask.load_reference(path)
    img_w, img_h = size
    sx, sy = img_w / REF_W, img_h / REF_H
    return {BOX_NAME.get(name, name):
            (x * sx, y * sy, w * sx, h * sy)
            for name, (x, y, w, h) in windows.items()}


def _match_by_overlap(holes, screen, size, want=None):
    """{name: hole} matched by area overlap, or None.

    **BY OVERLAP AND NOT BY ORDER, and the sort row is why** —
    12 September 2026. Order-and-count was adequate while the
    colony plate had two holes on its bottom row; it has eight now,
    every one of them hand-placed in GIMP, and the failure mode of
    an index is silent: two slots swapped left to right give a
    frame where PRODUCING sorts by science and everything else on
    the screen is still correct. That is the same fault this
    project already paid for once, when `frame_holes` had the last
    two bottom panels the wrong way round for a fortnight
    (`layout.json`, `panels._note`, 4 September 2026).

    A hole takes the reference rectangle it overlaps MOST, and the
    match is rejected wholesale unless it is a bijection in which
    every hole's best rectangle also ranks that hole first. A
    partial match is not used for the holes it did get right: a
    plate that half-matches is a plate whose geometry has moved, and
    naming half of it would hide that.

    `want` is {box name: rect in IMAGE px} and defaults to reading
    `layout_reference.json` off the disk. It is a parameter because
    that makes the matcher a pure function of the two things it
    compares — the caller that wants to ask "what would these holes be
    called against THAT geometry" can, without a file on disk.
    """
    want = reference_windows(screen, size) if want is None else want
    if len(want) != len(holes):
        return None
    names = sorted(want)
    best = {}
    for hole in holes:
        scored = sorted(names, key=lambda n: -_overlap(hole, want[n]))
        if not _overlap(hole, want[scored[0]]):
            return None
        best[tuple(hole)] = scored[0]
    if len(set(best.values())) != len(holes):
        return None
    # READING ORDER, BY ROW AND THEN BY X — and the row is `_rows`'
    # overlap grouping, not the raw y. The matcher has no order of its
    # own (it walks the holes as `find_holes` found them) and `--write`
    # writes `boxes.json` in whatever order it is handed, so an
    # unsorted answer reshuffles that file whenever scipy labels the
    # blobs differently — a diff nobody can read, which is the fault
    # the JSON formatting rule exists for. Sorting on the raw y is not
    # enough either: the sort slots sit at y 961 and 962 because that
    # is where the artwork cut them, so a plain y sort interleaves the
    # row. Grouping first puts them in one row and x orders it.
    order = {}
    for i, row in enumerate(_rows(holes)):
        for j, hole in enumerate(row):
            order[tuple(hole)] = (i, j)
    return {name: list(hole) for hole, name in
            sorted(best.items(), key=lambda kv: order[kv[0]])}


def name_holes_colony_summary(holes, size=None, reference=None):
    """The built plate's fourteen windows.

    **THE ROW SHAPE IS A CHECK, NOT THE NAMING** — 12 September 2026.
    It was both until the sort row grew to eight hand-placed slots.
    Now the rows say the plate is structurally the colony screen —
    a header, the list, four panels in one band, eight controls in
    the sort row — and `_match_by_overlap` says which hole is which,
    against the rectangles `layout_reference.json` types. So a slot
    Data drags past its neighbour still gets its own name, and a
    plate that has genuinely lost a window still fails here.

    **REWRITTEN 7 September 2026 FOR THE STAGE A3 PLATE**, and again
    on 12 September. The shipped frame had 14 holes: a title, a
    right-hand sidebar, a right-hand RETURN, seven sort buttons and
    three bottom panels. Stage A3's plate had 8: a header band, the
    list, four panels in one lower band, ONE sort bar and RETURN.
    This plate has 14 again and they are not the old 14 — nothing on
    the right of the list, a header where the title was, and the
    seven sort buttons back as slots on the bottom row beside
    RETURN. `_split_common`, which exists to find a title and a
    right column, applies to none of it and is not called.
    """
    global LAST_MATCH
    rows = _rows(holes)
    shape = [len(r) for r in rows]
    if shape != ROW_SHAPE:
        raise SystemExit(
            f"expected rows of {ROW_SHAPE} holes (header, list, the "
            f"lower band's {len(BAND_KEYS)}, the sort row's "
            f"{len(SORT_BOX_KEYS) + 1}), found {shape}: {rows}")
    named = _match_by_overlap(holes, "colony_summary", size, reference)
    if named is not None:
        LAST_MATCH = (
            "overlap against layout_reference.json — a hand-placed "
            "slot keeps its name whatever order it sits in")
        return named
    LAST_MATCH = (
        "row order, left to right — no usable layout_reference.json "
        "for this image size, so the sort slots are named by POSITION "
        "and two swapped slots would be named the wrong way round")
    header, listing, band, sort = rows
    named = {"header": header[0], "list_area": listing[0]}
    for key, r in zip(BAND_KEYS, band):
        named[key] = r
    for key, r in zip(SORT_BOX_KEYS, sort[:-1]):
        named[key] = r
    named["return"] = sort[-1]
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


def name_holes(holes, screen="galaxy_map", size=None, reference=None):
    """{box name: hole}. `size` is (img_w, img_h) and is what lets a
    rule match against `layout_reference.json` instead of counting;
    `reference` substitutes a geometry for that file's."""
    return RULES[screen](holes, size, reference)


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
    named = name_holes(holes, screen, (img_w, img_h))
    print(f"image {img_w}x{img_h}, {len(holes)} holes")
    if LAST_MATCH:
        print(f"  matched by {LAST_MATCH}")
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
