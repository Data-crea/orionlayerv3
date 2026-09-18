"""Select Race's frame: one fixed image, and where its two features are.

Work order 132. `assets/frame.png` replaces the shared 9-slice on this
screen and nothing else — decision 69's shape, applied to a whole screen
instead of to a popup body, which is what `planets` and `galaxy_map`
already do with their own images. Decision 12 is untouched: there is no
runtime tile swapping here, there is one image. Decision 34's panel
skins are untouched too: the boxes inside keep theirs.

WHY THIS SCREEN AND NOT ANOTHER. The frame has ONE opening, so the test
is containment: every box of the screen must lie inside it. Select Race
is the only screen where that holds at every resolution it defines —
measured in `doc/briefs/132-frame-assignment.md`, which also says why
the other three assets of that set fit nowhere.

WHAT THE 9-SLICE DID THAT AN IMAGE DOES NOT. `ScreenBase._render_frame`
draws the screen title into the frame's own title bar
(`FrameRenderer.title_rect`). A fixed image has no title bar, so the
title — "Select Race", and "Select Race Picture" in picture mode —
would have disappeared silently on the day the image went in. This
artwork carries a dark title plate of its own and the screen draws the
title on it.

**THE TWO RECTANGLES ARE MEASURED OFF THE IMAGE, AND THE FILE IS A
CACHE.** `layout.json` `frame.opening` and `frame.title_plate` are what
the artwork's own pixels say, and the smoke test re-measures both from
the asset and fails on any difference — decision 69's arrangement
exactly ("the opening is measured, not typed", with a check holding the
two equal). The measurement is a component walk over two million
pixels; doing it here would run it on every screen entry, so it lives
in the check and the answer lives in the file. Replace the artwork and
the suite tells you the numbers moved, with both values printed.
"""

#: Keys in `layout.json`. Named here so the screen, the check and the
#: document all say the same word.
OPENING = "opening"
TITLE_PLATE = "title_plate"

#: How the check finds each feature, so a future session re-measuring a
#: new artwork uses the same rule rather than inventing one.
#:
#: The opening is the largest region of alpha < 16 — the same limit
#: `tools/frame_holes.py` uses, so "what counts as an opening" has one
#: meaning in the project.
ALPHA_LIMIT = 16
#: The plate is opaque and TEAL — rgba(20, 31, 37, 255) in this artwork
#: — where the metal is grey. Keyed on "more blue than red" rather than
#: on darkness: a first measurement with a luminance threshold tuned for
#: black missed all seven button plates of the sibling asset, which is
#: how this rule was found. The widest such region in the top
#: `PLATE_TOP_BAND` of the image is the plate; in this artwork the next
#: candidate is 40 px wide against its 615, so it is not a close call.
OPAQUE = 200
PLATE_BLUE_OVER_RED = 8
PLATE_MAX_RED = 110
PLATE_MAX_GREEN = 130
PLATE_TOP_BAND = 0.15


def spec(words):
    """The `frame` block of `layout.json`, or an empty mapping."""
    return (words or {}).get("frame") or {}


def rect(words, key, ref_w, ref_h, img_w=1920, img_h=1080):
    """One feature as a reference-space rect, or None.

    The stored numbers are the artwork's own pixels. The conversion is
    a plain scale with NO bleed: `tools/frame_holes.to_ref` grows a
    cutout by `BLEED` outward so panel fills cover the rim, and nothing
    is filled here — the opening is a containment bound and the plate is
    a text anchor, and growing either would make the bound weaker and
    put the title above the plate it sits on.
    """
    value = spec(words).get(key)
    if not value or len(value) != 4:
        return None
    sx, sy = ref_w / img_w, ref_h / img_h
    x, y, w, h = value
    return (int(round(x * sx)), int(round(y * sy)),
            int(round(w * sx)), int(round(h * sy)))


def contains(opening, box):
    """True when `box` lies inside `opening`; both reference px.

    True when either is None, so a screen with no frame declared is not
    reported as a screen whose boxes escape one.
    """
    if opening is None or box is None:
        return True
    ox, oy, ow, oh = opening
    x, y, w, h = box
    return (x >= ox and y >= oy
            and x + w <= ox + ow and y + h <= oy + oh)


def escapes(opening, boxes):
    """The names of the boxes that do NOT lie inside the opening."""
    out = []
    for box in boxes:
        if box.ref_rect is None or box.hidden:
            continue
        if not contains(opening, tuple(box.ref_rect)):
            out.append(box.name)
    return out
