"""Derive box rects from the transparent cutouts of a frame image.

Usage:
    python tools/frame_holes.py screens/<screen>/assets/frame.png [--write]

Prints every transparent hole (alpha < 16) larger than MIN_AREA in
image pixels and as a 1920x1080 reference rect, assuming the image is
stretched over the whole reference area. With --write, that screen's
boxes.json is regenerated from the holes.

**WHAT IS LEFT OF THIS MODULE AFTER PHASE B, and what each part is
for.** The colony screen no longer derives its boxes from an image —
`tools/boxes_from_reference.py` writes them straight out of
`layout_reference.json` and `colonyplates.reseat` rebuilds them at
every load. What survives here is the other direction: given the
frame the screen wears, WHICH hole is which box.

  `find_holes`             the alpha reading, used by every check
                           that measures the artwork
  `name_holes` + the
  colony rule + `_rows`    matches every rectangle to a hole by
                           OVERLAP, refuses anything that is not a
                           clean bijection, reports the holes nothing
                           claims. This is what holds
                           `layout_reference.json` to
                           `assets/frame.png`, and the smoke test
                           runs it on the shipped file
  `RULE_NAMES` /
  `cutout_names`           the vocabulary `core/editor/boxclass.py`
                           asks for: which boxes are cutouts and
                           therefore LOCKED in the F5 editor
  `to_ref`, `--write`,
  the galaxy_map rule      the GALAXY MAP still derives its boxes
                           from its own frame.png this way, and
                           nothing about that screen changed

**Hole → box name mapping is by OVERLAP against the geometry, never
by index.** Seven hand-placed sort slots in one row is a lot of
chances to drag one past its neighbour, and an index-based namer
answers that silently: PRODUCING would sort by science and every
other thing on the screen would still be right. This project paid for
that once already — the last two bottom panels were the wrong way
round for a fortnight (`layout.json`, `panels._note`).

The galaxy map keeps its own positional rule, which is fine there:
its holes are not hand-placed and it has no reference file.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.config import REF_W, REF_H  # noqa: E402
# THE REFERENCE RULE LIVES ON THE SCREEN SIDE since Phase B, when
# `frame_mask` was deleted: what counts as a window, and what a
# rectangle is called once it is a box, are the screen's own answers
# and this module asks for them rather than keeping a second copy.
from screens.colony_summary import colonyplates as _cplates  # noqa: E402

MIN_AREA = 2000
ALPHA_LIMIT = 16
#: Reference-pixel bleed so content covers the anti-aliased rim.
#: IMPORTED, not declared — 12 September 2026, the redundancy audit.
#: It stood here AND in `colonyplates`, which is the side that has to
#: answer it with no tool on the path and the side
#: `tools/boxes_from_reference.py` already imports it from. Two
#: declarations of one number that has to agree to the pixel is the
#: fault this module already avoids for `BOX_NAME` two lines down.
BLEED = _cplates.BLEED
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
#: BOX, and two of them differ. IMPORTED, not restated: the screen
#: derives its own boxes through the same mapping at startup, so a
#: copy here could make a tool write a name the screen does not use.
BOX_NAME = _cplates.BOX_NAME
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

def row_shape(screen="colony_summary"):
    """The row shape `layout_reference.json`'s own rectangles have.

    **THE SHAPE IS A PROPERTY OF THE GEOMETRY, NOT A CONSTANT** —
    12 September 2026. It was `[1, 1, 4, 8]` written out of the key
    lists, which described the Stage-A3 layout and nothing else: on
    the static-frame path the sidebar sits beside the list and RETURN
    beside the lower band, so the rows are `[1, 2, 4, 7]` and a
    constant rejected a frame that is perfectly well formed.

    What the check is FOR survives intact, because the shape is still
    compared: the plate's rows must match the rows the rectangles
    describe. A RETURN dragged up into the lower band still changes
    the plate's shape away from the reference's and still fails. What
    stops being asserted is that the reference has one particular
    shape, which was never the rule and was only ever true.
    """
    data, windows = _cplates.load_reference(_cplates.reference_path(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        screen))
    for name in data.get("_windows_without_a_hole", ()):
        windows.pop(name, None)
    return [len(r) for r in _rows(list(windows.values()))]


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

#: The holes the last overlap match left unclaimed, in reading order.
#: A REPORT CHANNEL like `LAST_MATCH`: the static frame carries the
#: pre-Stage-4 title cartouche and this screen draws no title, so one
#: hole is spare by design and saying which is the whole point.
SPARE_HOLES = []


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
    data, windows = _cplates.load_reference(path)
    # A WINDOW MAY HAVE NO HOLE, and the file has to say so. The
    # colony header is one: the frame it wears was drawn for a screen
    # that had no column headings, so there is no band for them and
    # the header is a strip of the LIST's hole. Declared rather than
    # inferred — a window the matcher silently failed to place would
    # look exactly like a frame that had lost a hole.
    for name in data.get("_windows_without_a_hole", ()):
        windows.pop(name, None)
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
    # **A FRAME MAY HAVE A HOLE NOTHING USES.** It was `len(want) !=
    # len(holes) -> give up`, which is right for a plate GENERATED
    # from the rectangles and wrong for artwork: the static frame
    # carries the pre-Stage-4 title cartouche, and this screen has
    # drawn no title since Stage 4 (`frame._no_title_note`). So every
    # WINDOW must find a hole and the match must still be injective;
    # a hole no window claims is reported, not refused. Fewer holes
    # than windows is still a refusal — that is a frame that has lost
    # one.
    if len(want) > len(holes):
        return None
    names = sorted(want)
    best = {}
    for name in names:
        scored = sorted(holes, key=lambda h: -_overlap(h, want[name]))
        if not _overlap(scored[0], want[name]):
            return None
        best[tuple(scored[0])] = name
    if len(best) != len(want):
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
    global SPARE_HOLES
    SPARE_HOLES = [list(h) for h in
                   sorted((tuple(h) for h in holes if tuple(h) not in best),
                          key=lambda h: order[h])]
    return {name: list(hole) for hole, name in
            sorted(best.items(), key=lambda kv: order[kv[0]])}


def name_holes_colony_summary(holes, size=None, reference=None):
    """The plate's windows, matched to `layout_reference.json`.

    **THE MATCH IS THE CHECK, AND THE ROW SHAPE CONFIRMS IT** —
    rewritten 12 September 2026 for the static frame. Order-and-count
    named these holes until the sort row grew to seven hand-placed
    slots, and a fixed row shape gated the naming until the screen
    took a frame whose rows are not the plate's. Both were instances.
    What is asserted now:

      every WINDOW finds a hole it overlaps, and no two windows find
      the same one — a hole nothing claims is fine and is reported
      (`SPARE_HOLES`), because this frame carries the pre-Stage-4
      title cartouche and nothing has drawn a title since Stage 4

      the holes that WERE claimed group into the same rows the
      rectangles do — which is what still catches a window that has
      drifted into a neighbouring band, the thing the shape gate was
      written for

    A failure to match is a HARD STOP and there is no fallback. Naming
    by position is what produced the silent misnaming this rule exists
    to prevent — the last two bottom panels were the wrong way round
    for a fortnight — and a frame whose holes do not correspond to the
    rectangles is a frame and a geometry describing different screens.
    The order fallback was kept for "no reference readable at all"
    until Phase B, when the reference became the only thing there is.
    """
    global LAST_MATCH
    named = _match_by_overlap(holes, "colony_summary", size, reference)
    if named is not None:
        got = [len(r) for r in _rows(list(named.values()))]
        want = row_shape()
        if got != want:
            raise SystemExit(
                f"the claimed holes group into rows of {got} and "
                f"layout_reference.json's own rectangles into {want} "
                f"— a window has drifted into another band")
        LAST_MATCH = (
            f"overlap against layout_reference.json, rows {got}"
            + (f", {len(SPARE_HOLES)} hole(s) claimed by nothing: "
               f"{SPARE_HOLES}" if SPARE_HOLES else ", every hole claimed"))
        return named
    raise SystemExit(
        f"{len(holes)} holes and none of the overlap matches is a "
        f"clean one: every rectangle in layout_reference.json has to "
        f"land on a hole of its own. Holes: "
        f"{sorted(tuple(h) for h in holes)}")


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
