"""Which boxes may be resized, and on which axes.

Added 9 September 2026, when the editor gained resize handles for
every box. Until then it offered eight handles on ALL of them, which
is wrong in two different ways on the same screen and silently.

**THE CLASS IS DERIVED, NEVER DECLARED.** A box is LOCKED because the
screen's `frame_holes` rule produces its name, not because somebody
typed a flag next to it. `Box.locked` existed in the data model, was
serialized by `to_dict`, and was never read by anything; it is
deleted, with `Box.role`, since 12 September 2026. Filling
it in would mean hand-copying which boxes are cutouts into every
screen's box file, which is a second copy of what `frame_holes`
already knows and is exactly the failure decision 3 was written
against: *"moving one by hand slides content out from under its
hole."*

THE THREE CLASSES

`FREE` — hand-placed content boxes with no hole and no derivation.
Eight handles, both axes. The `sb_*` sidebar readouts, `help_popup`,
and everything on the four screens that have no frame plate.

`BOUND` — the colony list's six column boxes. Only the LEFT and RIGHT
edges are live: y and height come from `list_area` and
`colonyheader.sync_columns` writes them back every frame, so a
vertical drag is not refused arbitrarily — it is a drag on a number
this screen does not keep. And a horizontal drag moves a BOUNDARY:
a column's width is the distance to the next one
(`colonytrack.columns`), so the neighbour follows.

`LOCKED` — the frame cutouts. No handles at all. The rect comes from
the artwork through `tools/frame_holes.py`, and the editor says so
rather than refusing silently.

WHY A REFUSAL HAS TO SPEAK. The person dragging cannot see any of
this: a cutout box and a hand-placed one look identical on screen, and
a handle that does nothing reads as a broken editor rather than as a
rule. Every refusal here returns a sentence naming what to change
instead.
"""
import sys
import os

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "tools"))

FREE = "free"
BOUND = "bound"
LOCKED = "locked"

#: The boxes whose x edges are theirs and whose y is the list's.
#: Named here rather than imported from the screen: `core` must not
#: depend on a screen package, and the screen holds the same six names
#: in `colonyheader.COLUMN_BOXES`. A smoke check asserts the two agree,
#: which is what makes the duplication legitimate (decision 36's rule:
#: a copy is allowed when a checker holds it).
COLUMN_PREFIX = "col_"


def _cutout_names(screen_name):
    """The names `screen_name`'s frame rule can produce."""
    try:
        import frame_holes
    except Exception:                                # pragma: no cover
        return set()
    return frame_holes.cutout_names(screen_name)


def classify(screen_name, box_name):
    """FREE, BOUND or LOCKED for one box on one screen."""
    if box_name in _cutout_names(screen_name):
        return LOCKED
    if box_name.startswith(COLUMN_PREFIX):
        return BOUND
    return FREE


#: Which handles each class offers. `l`/`r`/`t`/`b` and the four
#: corners, as `Editor._hit_resize` names them.
HANDLES = {
    FREE: {"tl", "tr", "bl", "br", "t", "b", "l", "r"},
    BOUND: {"l", "r"},
    LOCKED: set(),
}


def refusal(screen_name, box_name, handle):
    """Why this handle is not offered, or None if it is.

    The sentence is the whole point — see the module docstring.
    """
    kind = classify(screen_name, box_name)
    if handle in HANDLES[kind]:
        return None
    if kind is LOCKED:
        return (f"{box_name} is a frame cutout: its rect comes from the "
                f"artwork through tools/frame_holes.py, and moving it "
                f"here would slide content out from under its hole "
                f"(decision 3). Change the plate, then re-derive.")
    if kind is BOUND:
        return (f"{box_name} is a list column: only its left and right "
                f"edges are its own. y and height come from list_area "
                f"and sync_columns writes them back every frame. A "
                f"side handle moves the BOUNDARY and its neighbour "
                f"follows, because a column's width is the distance to "
                f"the next one.")
    return f"{box_name} has no {handle} handle"


#: Boxes that must keep an aspect ratio whatever edge is dragged, as
#: `{screen: {box: ratio}}`.
#:
#: **THE GALAXY INSET IS HERE THOUGH IT IS LOCKED, AND THAT IS
#: DELIBERATE.** Its width-to-height is TRANSCRIBED to a thousandth —
#: `128 * (506000 // 128) / (91 * (400000 // 91))` from
#: movebox.cpp:20-21, the crop the original's own inset covers — and a
#: smoke check holds `layout_reference.json` to it. Today the editor
#: refuses to resize it anyway because it is a cutout. The rule goes
#: in now so that the first person to unlock it, for whatever reason,
#: cannot break the ratio by dragging a corner and find out from a
#: failing suite three commits later.
ASPECT = {
    "colony_summary": {
        "galaxy_inset": (128 * (506000 // 128)) / (91 * (400000 // 91)),
    },
}


def hold_aspect(screen_name, box_name, rect, handle):
    """`rect` corrected to the box's required ratio, or unchanged.

    The axis the handle did NOT drive is the one that follows: pulling
    a side sets the width and the height follows it, pulling a top or
    bottom the other way round, and a corner keeps the width because
    that is the edge the pointer was on last.
    """
    ratio = ASPECT.get(screen_name, {}).get(box_name)
    if ratio is None:
        return rect
    x, y, w, h = rect
    if handle in ("t", "b"):
        w = max(1, int(round(h * ratio)))
    else:
        h = max(1, int(round(w / ratio)))
    return (x, y, w, h)
