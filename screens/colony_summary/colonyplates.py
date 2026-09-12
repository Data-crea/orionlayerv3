"""What a colony window IS, and where its rectangle comes from.

**THE STATIC FRAME IS THE ONLY PATH — 12 September 2026, Phase B,
Data's decision after seeing all three.** The screen wears one fixed
image, `assets/frame.png`, scaled to the reference area and blitted.
There is no master, no built plate, no nine-slice, no bevel, no rails
and no flag: `frame_build`, `frame_mask`, `frame_cut`, `frame_master`,
`colony_frame_check`, `gimp_fixtures` and `colonyframe` are gone, and
so are `frame_preview` and `colony_plateless`. This module kept the
half of itself that survived — where a box's rectangle comes from —
and lost the drawn fill/rim/lit line, which existed to answer "what
does a box look like with no artwork at all" and is a question nobody
is asking any more.

**THE CHAIN IS TWO LINKS NOW.** Decision 3 ran
`layout_reference.json` -> mask -> plate -> `boxes.json`, with the
artwork in the middle purely to turn a rectangle into a hole so the
hole could be measured back into a rectangle. The artwork is fixed and
was drawn first; the rectangles were measured off it. So the chain is
`layout_reference.json` -> `boxes.json`,
`tools/boxes_from_reference.py` writes it, and `reseat` below rebuilds
it in memory at every load.

**`boxes.json` IS A CACHE AND NEVER THE AUTHORITY.** Edit the
reference, forget the tool, and the screen used to draw yesterday's
fills behind today's frame with nothing saying so — which happened the
same day it became possible. `reseat` runs from
`screen._reload_boxes`, so it runs on entry AND on every resize, which
is the fault `colonyheader.install_columns` records for the column
table.

**WHAT STILL HOLDS THE RECTANGLES TO THE ARTWORK.** A smoke check
matches every window to a transparent hole of `assets/frame.png` by
overlap and asserts it sits inside that hole at all three shipped
resolutions. That is the whole of decision 3's guarantee with the
generated middle removed: the rectangles are measured off the picture,
and something re-measures them.
"""
import json
import os

import pygame

#: Reference-pixel bleed, so content covers what overlaps a box's own
#: edge — here the frame's own rim, which is drawn over the content.
#: **ONE NUMBER, AND `tools/boxes_from_reference.py` IMPORTS IT FROM
#: HERE** rather than keeping its own: the tool writes `boxes.json` and
#: `box_rects` rebuilds the same rects at startup, so a second copy
#: would let a file on disk and a screen in memory disagree by two
#: pixels with nothing to report it.
BLEED = 2

#: Keys of `layout_reference.json` that are not a window.
#:
#: **THE ONE HOME SINCE PHASE B.** `tools/frame_mask.NOT_A_WINDOW` held
#: the same list and a smoke check held the two together; that file is
#: deleted and this is what is left. A screen that derives its own
#: boxes has to be able to say what a box is with no tool on the path,
#: which is why the rule ended up on this side rather than the other.
#:
#: `list_columns` divides a window that is already here, and
#: `_resolutions` is a list of sizes. A key that is neither a rectangle
#: nor named here is an ERROR and not a silent omission — a screen that
#: quietly skipped a malformed rect would draw thirteen boxes and look
#: almost right.
NOT_A_WINDOW = ("list_columns", "_resolutions")

#: `layout_reference.json` names a RECTANGLE, `boxes.json` names a BOX,
#: and two of them differ. `tools/frame_holes.BOX_NAME` holds the same
#: mapping for the naming side and a smoke check holds the two to each
#: other. Anything absent maps to itself.
BOX_NAME = {"return_button": "return", "list": "list_area"}

REFERENCE = "layout_reference.json"


def parse_reference(data):
    """(data, {name: rect}) from an already-loaded reference dict.

    Split from `windows` so a tool can hand in a file it read itself,
    with no screen, no app and no resource stack — which is what
    `tools/frame_holes.py` and `tools/boxes_from_reference.py` both
    need and what `frame_mask.load_reference` used to give them.
    """
    out = {}
    for key, value in data.items():
        if key.startswith("_") or key in NOT_A_WINDOW:
            continue
        if not (isinstance(value, list) and len(value) == 4
                and all(isinstance(v, int) for v in value)):
            raise ValueError(
                f"{REFERENCE}: {key} is not a rectangle and is not "
                f"excluded — add it to colonyplates.NOT_A_WINDOW or "
                f"make it [x, y, w, h]")
        out[key] = value
    return data, out


def load_reference(path):
    """(data, windows) read straight off disk, no resource stack."""
    with open(path, encoding="utf-8") as fh:
        return parse_reference(json.load(fh))


def reference_path(root, screen="colony_summary"):
    return os.path.join(root, "screens", screen, REFERENCE)


def windows(screen):
    """{name: [x, y, w, h]} — every window the reference types.

    Reference px, the file's own spelling of the names
    (`return_button`, `list`), and in the file's own order, so the
    reading order of the file Data edits is the order everything
    downstream walks. Through the resource stack, so a mod can
    override it.
    """
    data = screen.app.res.load_json(
        f"screens/{screen.SCREEN_NAME}/{REFERENCE}", {}) or {}
    return parse_reference(data)[1]


def bled(rect):
    """One rectangle grown by `BLEED` on every side.

    **ONE EXPRESSION, ONE HOME** — 12 September 2026, the redundancy
    audit. `x - b, y - b, w + 2*b, h + 2*b` stood in three places:
    here, in `tools/boxes_from_reference.py` and open-coded in a smoke
    check. Three copies of an arithmetic that has to agree to the
    pixel, when what it is FOR is that the file on disk and the screen
    in memory hold the same rect.
    """
    x, y, w, h = rect
    return [x - BLEED, y - BLEED, w + 2 * BLEED, h + 2 * BLEED]


#: The six column boxes, in `list_columns`' own order. Named here
#: because `column_rects` has to produce a BOX name from a SPLIT key,
#: and `colonyheader.COLUMN_BOXES` holds the same six for the screen
#: side — a smoke check holds the two to each other, which is what
#: makes the copy legitimate (decision 36).
COLUMN_PREFIX = "col_"


def column_rects(list_box, cols):
    """{col_<key>: rect} — the six columns laid across `list_box`.

    **THE SPLIT HAS ONE HOME AND IT IS `list_columns`** — 12 September
    2026. The six rects stood in `boxes.json` as well, seated from
    here by a tool nobody had to run; they are derived at startup now,
    like the fourteen cutouts, so a list that moves takes its columns
    with it and the editor cannot save a column that disagrees with
    the reference.

    THE SCROLL COLUMN IS AN ABSOLUTE WIDTH AND THE OTHER FIVE ARE
    FRACTIONS. Native x 619..627 is 9 px, which is 27 reference px
    (colsum.cpp:263-264 for the arrows' field x, :278 and :759 for the
    track it holds). Scaling it with the rest put it at 22 the first
    time the list got narrower — a transcription quietly becoming a
    share — so it comes off the top and the remaining five split what
    is left in their own ratios. Each column ends where the next
    begins, and the last before the scroll ends where the scroll
    starts, so the six tile the box exactly by construction rather
    than by a rounding residue landing in the last one.
    """
    ax, ay, aw, ah = list_box
    keys = list(cols)
    last = keys[-1]
    fixed = cols[last]
    total = sum(v for k, v in cols.items() if k != last)
    span = aw - fixed
    out, off = {}, 0
    for key in keys:
        if key == last:
            out[COLUMN_PREFIX + key] = [ax + aw - fixed, ay, fixed, ah]
        else:
            x = ax + round(off * span / total)
            nxt = (ax + aw - fixed if off + cols[key] >= total
                   else ax + round((off + cols[key]) * span / total))
            out[COLUMN_PREFIX + key] = [x, ay, nxt - x, ah]
        off += cols[key]
    return out


def all_rects(data):
    """{box name: rect} for every box this screen has — cutouts and
    columns alike — from an already-loaded reference dict.

    Pure, so a tool or a check can ask for the geometry at any
    resolution with no screen, no app and no pygame.
    """
    _data, wins = parse_reference(data)
    out = {BOX_NAME.get(n, n): bled(r) for n, r in wins.items()}
    cols = data.get("list_columns")
    if cols:
        out.update(column_rects(out["list_area"], cols))
    return out


#: A key shaped `_hole_<window>` gives that window's CUTOUT, for the
#: one window whose cutout is deliberately bigger than its rectangle.
#: A PREFIX AND NOT A SUFFIX: `_<window>_hole` read
#: `_windows_without_a_hole` as a rectangle for a window called
#: "windows_without_a", and a naming rule that collides with a key
#: already in the file is a naming rule that will collide again.
HOLE_PREFIX = "_hole_"


def hole_rects(data):
    """{box name: rect} — cutouts that are larger than their box.

    `galaxy_inset` is the only one and is meant to be: it keeps the
    original's coverage aspect (movebox.cpp:20-21) inside a hole Data
    drew wider, so 34 reference px of cutout have no box over them.
    What goes there is the panel's own BLACK and not the screen's
    background, which is what this rect is for — it seats nothing, the
    editor never sees it, and `render_fills` is its only reader.

    Declared rather than measured at run time on purpose: Phase B
    ended the practice of deriving geometry from artwork while the
    game is running. A smoke check re-measures it off the alpha.
    """
    out = {}
    wins = parse_reference(data)[1]
    for key, value in data.items():
        if not key.startswith(HOLE_PREFIX):
            continue
        name = key[len(HOLE_PREFIX):]
        if name not in wins:
            raise ValueError(
                f"{REFERENCE}: {key} names a hole for {name!r}, which "
                f"is not a window in this file")
        out[BOX_NAME.get(name, name)] = list(value)
    return out


def box_rects(screen):
    """{box name: [x, y, w, h]} — every box, reference px."""
    return all_rects(reference(screen))


def reference(screen):
    """The reference file this screen loads, through the mod stack."""
    return screen.app.res.load_json(
        f"screens/{screen.SCREEN_NAME}/{REFERENCE}", {}) or {}


def reseat(screen):
    """Give every box its rect, from `layout_reference.json`.

    **THE COLUMNS COME THROUGH HERE TOO SINCE 12 September 2026.**
    They were strips of `list_area` placed by hand in the editor and
    seated from `list_columns` by a tool somebody had to remember to
    run; the split has one home now and the six follow the list the
    way the fourteen cutouts do. What that costs is the drag: a
    column moved in the F5 editor is rebuilt from the reference at the
    next load, so the way to move one is to edit `list_columns`. The
    editor says so — `core/editor/boxclass.py` classes them from the
    screen's rules, not from a flag in a file.

    `boxes.json` carries no rectangle at all for this screen now, so
    this is not a correction of what was loaded — it is where the
    geometry comes from.
    """
    data = reference(screen)
    want = all_rects(data)
    # STASHED HERE BECAUSE RENDERING MUST NOT READ JSON. `render_fills`
    # runs every frame and `res.load_json` opens the file every call —
    # so the hole fills are read where the rects are, once per load and
    # per resize, and the renderer only draws them.
    screen._hole_fills = hole_rects(data)
    seat(screen.boxes, want, screen.layout)
    return want


def seat(boxes, rects, layout):
    """Give each box in `boxes` its rect from `rects`, and lay it out.

    Split from `reseat` so a check can seat a box list it built itself
    — `load_boxes` returns boxes with no rectangle for this screen now,
    and a second loop that filled them in would be a second copy of
    the one rule that matters here.
    """
    for box in boxes:
        rect = rects.get(box.name)
        if rect is None:
            continue
        if box.ref_rect is None or tuple(box.ref_rect) != tuple(rect):
            box.ref_rect = tuple(rect)
        box.derived = True
        box.update_layout(layout)
    missing = [b.name for b in boxes if b.ref_rect is None]
    assert not missing, (
        f"{missing} have no rectangle: boxes.json names them and "
        f"neither layout_reference.json nor list_columns places them. "
        f"A box this screen cannot seat is a box nothing can draw")
    return boxes


def editor_free(data):
    """Box names the F5 editor may move, from a loaded reference."""
    return {BOX_NAME.get(n, n): n
            for n in data.get("_editor_free", ())}


def write_back(screen):
    """Write the editor-free boxes' rects back into the reference.

    **THE ONLY WAY A DRAG SURVIVES A RESTART ON THIS SCREEN.**
    `boxes.json` carries no rectangle and `reseat` rebuilds every one
    at load, so a rect saved there is overwritten before it is drawn.
    `Editor._save` calls `screen.save_geometry()` — the same hook it
    already uses for the race portraits' crops — and this edits
    `layout_reference.json` in place.

    ONLY THE DECLARED NAMES, and the rest of the file byte for byte:
    it is re-serialised at indent 2 with the key order preserved,
    which is the convention the JSON formatting check holds every file
    in this tree to. A box that is not in `_editor_free` is not
    written even if something moved it, because the editor refuses to
    move those in the first place and a second writer for them is
    exactly decision 3's fault.

    The BLEED comes off again on the way in: `boxes.json`'s rect is
    the typed rect grown by what overlaps it, and what is typed here
    is the rect itself.
    """
    path = os.path.join(screen._screen_dir, REFERENCE)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=_ordered())
    free = editor_free(data)
    if not free:
        return []
    by_name = {b.name: b for b in screen.boxes}
    wrote = []
    for box_name, ref_name in free.items():
        box = by_name.get(box_name)
        if box is None or box.ref_rect is None:
            continue
        x, y, w, h = box.ref_rect
        rect = [x + BLEED, y + BLEED, w - 2 * BLEED, h - 2 * BLEED]
        if data.get(ref_name) != rect:
            data[ref_name] = rect
            wrote.append((ref_name, rect))
    if wrote:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
    return wrote


def _ordered():
    import collections
    return collections.OrderedDict


def render_fills(screen, surface):
    """Every cutout that shows content gets its panel fill.

    Laid BEFORE the frame, which is blitted over the top — so a fill
    reaches only as far as its hole lets it, and the frame's own rim
    covers the `BLEED` the rect was grown by.

    A panel may name its own fill as `<name>_fill` BESIDE IT in the
    `panels` block — the galaxy inset does, and
    `_galaxy_inset_fill_note` carries the measurement it rests on. A
    per-box value rather than a renderer change, because `colonyinset`
    draws no background at all, by transcription (movebox.cpp:36-38).

    **AND IT IS READ FROM `panels`, NOT FROM THE TOP LEVEL.** For a day
    it was `screen._data.get(name + "_fill")` while the value sat in
    `panels` — so the lookup found nothing, every panel silently took
    `PANEL_BG`, and the status document said the inset was black on the
    strength of the measurement that chose the value rather than of the
    frame it was drawn in. A missing key here cannot raise, because
    most panels have none; the smoke check is what makes a stray one
    visible.
    """
    from .screen import PANEL_BG
    panels = screen._data.get("panels", {})

    def _fill(name, rect):
        surface.fill(tuple(panels.get(name + "_fill") or PANEL_BG)[:3],
                     pygame.Rect(*screen.layout.rect(rect)))

    # THE HOLES THAT ARE BIGGER THAN THEIR BOX GO DOWN FIRST, so the
    # box's own fill lands on top of the part it covers. Only
    # `galaxy_inset` has one; see `hole_rects`.
    for name, rect in getattr(screen, "_hole_fills", {}).items():
        _fill(name, bled(rect))
    for name in panels:
        box = (None if name.startswith("_") or name.endswith("_fill")
               else screen.box_rect(name))
        if box:
            _fill(name, box)
