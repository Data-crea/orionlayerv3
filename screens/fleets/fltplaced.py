"""The six Fleets boxes that have no hole, and the rule that places each.

Thirty-two of this screen's boxes are CUTOUTS: `tools/frame_holes.py`
reads them off the frame's alpha and the smoke test holds every one to
its hole. Six are not. They have nothing in the artwork to be derived
from, they were placed by hand once, and when the frame changed shape
in work order 153 every one of them was left sitting over the old
layout — which is the fault work order 151 paid for and the reason
this module exists.

**EACH ONE IS A RULE AGAINST A HOLE, NOT A REMEMBERED RECTANGLE.**
Every rule below reproduces the value the file carried before 153 from
the holes as they were before 153, to the pixel except where noted.
That is the only licence a rule of this kind can have: it has to
explain the numbers that were already there.

Run against the boxes as they stood at `fb197ac`, five of the six come
out identical and `status_text` comes out one pixel further right
(343 against 342) — the file's value is what `int()` gave and this
module rounds, everywhere, rather than carrying two rounding rules.
One pixel on a hand-placed text field is not worth a second rule; it
is written down here so that nobody later reads the difference as a
fault.

`tools/fleets_place_boxes.py` SEEDS them, so a future reshape moves
them with the frame and nobody has to remember that they exist.

**THE SEED IS A STARTING POINT AND NOT A CAGE** — Data,
20 September 2026, and it is what `fltgeom`'s own docstring and
decision 14 already promised. Until then a smoke check demanded that
every one of these six EQUAL what this module computes, which quietly
turned six F5-editable boxes into locked ones: the first nudge in the
editor — one pixel of `ship_panel_text` at 2560x1440 — turned the
suite red, and the box was never supposed to be locked. What the
check holds now is `contained`, and nothing else. Run the seeder
after the frame changes shape; drag afterwards and the drag stands.

**WHAT THE SEEDER STILL OWES.** Re-running it OVERWRITES whatever F5
left, because it writes the computed rect. That is the same bargain
`tools/fleet_boxes.py` carried, and the tool says so before it
writes.

**WHAT IS NOT HERE.** `scroll_column` is placed from
`fltgeom.SCROLL_SRC_COLUMN`, measured onto the painted bar, and has
its own checker already; `help_popup` belongs to the help overlay and
to no part of this screen's layout.
"""

from . import fltgeom

#: Reference px the ship panel's words are inset from the hole on
#: every side. It is what the file has carried since the box was
#: split out, and it clears the chamfer with room to spare:
#: `CONTENT_INSET_SRC["ship_panel"]` is 39 source px, which is 19.5
#: reference px at the 2:1 the frame is drawn down by.
PANEL_TEXT_INSET = 25

#: The six, in the order they are written.
NAMES = ("ship_panel_text", "icon_area", "button_band", "status_text",
         "inset_hint", "status_hint")

#: The seven controls `button_band` is the union of — the union the
#: original's own help table bounds (evanhelp.cpp:159-165) and which
#: `fltgeom.REGIONS` names as ours, not the original's.
_CONTROLS = ("btn_all", "btn_relocate", "btn_scrap", "btn_leaders",
             "btn_support", "btn_combat", "btn_return")


def _fraction(inner, outer, box):
    """`inner` placed inside `box` the way it sits inside `outer`.

    Both native rectangles, `box` a reference one. The offsets and the
    lengths are taken as FRACTIONS of the native parent, so the child
    follows a hole of any shape — which is the whole point after a
    reshape that changed one parent's aspect and not another's.
    """
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    bx, by, bw, bh = box
    return [bx + int(round((ix - ox) / ow * bw)),
            by + int(round((iy - oy) / oh * bh)),
            int(round(iw / ow * bw)),
            int(round(ih / oh * bh))]


def placed(boxes):
    """`{name: rect}` for the six, from the derived boxes.

    `boxes` is `{name: reference rect}` and must hold all thirty-two
    cutouts; nothing here reads a file.
    """
    out = {}

    # 1. The words in the ship panel: the hole, inset on every side.
    px, py, pw, ph = boxes["ship_panel"]
    k = PANEL_TEXT_INSET
    out["ship_panel_text"] = [px + k, py + k, pw - 2 * k, ph - 2 * k]

    # 2. The grid AND the bar beside it: from the first cell's left
    #    edge to the scroll column's right one, over the column's own
    #    height. The column is the taller of the two and the original
    #    says so — help 361 runs y 59..349 against the grid's 53..349
    #    (evanhelp.cpp:154) — so the height is the column's.
    cx = boxes["cell_00"][0]
    sx, sy, sw, sh = boxes["scroll_column"]
    out["icon_area"] = [cx, sy, sx + sw - cx, sh]

    # 3. The seven controls, bounded. A union and not a measurement:
    #    `fltgeom.REGIONS["button_band"]` is ours for exactly this
    #    reason — the original draws no outline there.
    rects = [boxes[n] for n in _CONTROLS]
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    out["button_band"] = [x0, y0, x1 - x0, y1 - y0]

    # 4-6. The three that sit inside another box by the original's own
    #      proportions. `status_text` is help 363 inside the strip that
    #      holds it; the two hints are `fltgeom.hint_rect`, which is
    #      where HINT_INSET and the inset's bottom strip are decided.
    out["status_text"] = _fraction(
        fltgeom.CONTROLS["status_text"][1], fltgeom.REGIONS["status_band"],
        boxes["status_band"])
    for name, region in (("inset_hint", "inset_map"),
                         ("status_hint", "status_band")):
        out[name] = _fraction(fltgeom.hint_rect(region),
                              fltgeom.REGIONS[region], boxes[region])
    return out


#: Which placed box must stay inside which derived one. THE 151
#: LESSON, and since 20 September 2026 the ONLY thing held about
#: these six: a box that leaves its hole is drawn and then covered,
#: because the frame image renders last, and nothing says so on
#: screen. Where it sits inside the hole is the editor's business;
#: whether it is inside at all is not.
#:
#: `icon_area` and `button_band` are unions and contain their cutouts
#: rather than sitting in one, so they are checked the other way
#: round by `contained`.
INSIDE = {"ship_panel_text": "ship_panel", "status_text": "status_band",
          "inset_hint": "inset_map", "status_hint": "status_band"}

#: The unions, and what each must hold.
HOLDS = {"icon_area": ("cell_00", "cell_19"),
         "button_band": _CONTROLS}


def contained(boxes, out=None):
    """Every containment that must hold, as a list of failures.

    `out` is what the six ACTUALLY are — `boxes.json`'s own rects,
    wherever F5 left them. It defaults to the seed, which is what the
    seeder checks before it writes; the smoke test passes the file's
    values, because the file is what the screen draws.
    """
    out = placed(boxes) if out is None else out
    bad = []

    def inside(small, big):
        sx, sy, sw, sh = small
        bx, by, bw, bh = big
        return (sx >= bx and sy >= by
                and sx + sw <= bx + bw and sy + sh <= by + bh)

    for name, parent in INSIDE.items():
        if not inside(out[name], boxes[parent]):
            bad.append(f"{name} {out[name]} leaves {parent} {boxes[parent]}")
    for name, children in HOLDS.items():
        for child in children:
            if not inside(boxes[child], out[name]):
                bad.append(f"{name} {out[name]} does not hold {child} "
                           f"{boxes[child]}")
    return bad
