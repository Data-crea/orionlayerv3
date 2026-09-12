"""The colony screen with no frame artwork: every box drawn by code.

**DATA'S DECISION, 12 September 2026 — PHASE A, A PROTOTYPE.** There
is no plate, no master and no ring. Every rectangle in
`layout_reference.json` is drawn where it is typed, and Data moves a
box by editing that file and nothing else. It supersedes decision 49
(derived plates) for THIS screen, and nothing is deleted yet: the
flag is off by default, `tools/frame_build.py` and the three plates
still exist and still pass their checks, and Phase B is what removes
them once Data has looked.

**WHY IT CAN WORK AT ALL.** Decision 3's chain already ran
`layout_reference.json` -> mask -> plate -> `boxes.json`, with the
artwork in the middle of it purely to turn a rectangle into a hole.
Take the artwork out and the chain is `layout_reference.json` ->
`boxes.json`, which is shorter and has one fewer place to disagree.
What is LOST with it is the metal — the ring, the struts, the rails,
the bevels, the corner tiles — and that is the whole of what this
module has to answer for.

**WHAT A BOX GETS INSTEAD: FILL, RIM, LIT LINE.** All three through
`StyleRenderer.draw_plate`, which is the one home for how a plate
looks (decision 51) and which the header plates and the fifty cell
plates already go through. So the screen has one plate routine and
not two, and a change to the appearance lands on all of them.

  fill      the panel fill the box already had — `PANEL_BG`, or the
            box's own `<name>_fill` from `layout.json`. Unchanged
            from today except that it is now ROUNDED with the rest of
            the plate; a square fill under a rounded rim leaves the
            corner poking out, which is visible at any radius.
  rim       `panel.border`, `RIM_REF` reference px. **DEVIATION.**
            The original has metal around every field and we no
            longer have any; this band is what stands in for it. It
            is not a transcription of anything — the original's rim
            is artwork in COLSUM.LBX, which decision 42 says HD
            cannot ship — and it is in the project's own panel
            language (decision 34) rather than in the metal's grey,
            for the same reason the header's outline is.
  lit line  `panel.border_highlight`, 1 px, OUTERMOST. **The
            RELATIONSHIP is transcribed, not the RGB** — the same
            move `_row_name_note` makes for the list's names. On the
            original's own framebuffer a plate reads interior 44,
            metal 60, outline 96: the outline is the BRIGHTEST of the
            three and it is on the outside. Ours is fill 11, rim 78,
            line 134 in luma, which keeps rim/interior and line/rim
            in the same direction and close to the same ratio (1.6
            there, 1.7 here). Taking the original's absolute greys
            instead would put a neutral metal edge on a screen whose
            every other panel line is `panel.thin_border`, which is a
            different question from the one being transcribed
            (decision 34).

**THE CORNER RADIUS IS A MEASUREMENT AND IT IS IN NATIVE PX.** The
original turns its rim corner on about **2 native px** — measured at
the sort panel's top-left on the live framebuffer, the top edge
reaches full brightness at x=114 and the left edge at y=453, with the
corner pixel at luminance 88 against the rim's 120-144; bottom-left
reads the same (c5977cf, 10 September 2026). Two native px is
**3 reference px** at 1920, and 3 is what `layout.json` carries under
`frame.plate_corner_radius`. 0 is allowed and means a square corner.

That measurement is the whole reason this screen can have a rounded
corner at all. With the plate it could not: the rim was the master's
own lit edge nine-sliced, the four corner tiles were flat, and
c5977cf's verdict was "needs artwork" — a radius in the data would
have been inert because what reads as the rim is RGB the alpha never
touches. Drawn boxes have no such problem, and closing that item is
Phase B's.

**NOTHING IS DRAWN BETWEEN THE BOXES.** No rails, no struts, no
junctions, no tiled texture. The background stays exactly what it is
today (`ScreenBase._render_background`), and what was metal is now
background. That is the single biggest thing to judge on the picture.
"""
import pygame

#: The rim band, reference px. Two, because the original's own rim
#: reads 2 native px wide before it turns its corner (c5977cf) and
#: this is the same band at 1920 — one reference px would be a line
#: rather than a rim, and the lit line already is one.
RIM_REF = 2

#: The corner radius when `layout.json` says nothing, reference px.
#: The original's ~2 native px at x3. See the module docstring.
CORNER_RADIUS_REF = 3

#: Keys of `layout_reference.json` that are not a window.
#:
#: **A SECOND COPY WITH A CHECKER, AND IT IS THE ONE THAT SURVIVES.**
#: `tools/frame_mask.NOT_A_WINDOW` holds the same list, and a smoke
#: check asserts the two answer identically for the file in the tree
#: (decision 36: a copy is legitimate when a checker holds it). The
#: duplication is deliberate and temporary in ONE direction — Phase B
#: deletes `frame_mask`, and this module is where the rule then lives,
#: because a screen that draws its own boxes must be able to say what
#: a box is without a tool on the path.
NOT_A_WINDOW = ("ring", "gaps", "list_columns", "figure_scale",
                "_resolutions")

REFERENCE = "layout_reference.json"


def active(screen):
    """Is this screen drawing its own boxes?

    The flag is runtime state and lives in `settings.json`, beside
    `frame_preview` and for the same reason `colonyframe` gives: a
    render toggle is not layout, so it does not go in `boxes.json`
    where `Box.to_dict` would drop it at the first editor save
    (decision 37).
    """
    return bool(screen.app.settings.get("colony_plateless"))


def windows(screen):
    """{name: [x, y, w, h]} — every window `layout_reference` types.

    Reference px, the file's own spelling of the names
    (`return_button`, `list`), and in the file's own order so the
    drawing order is the reading order of the file Data edits.

    A key that is neither a rectangle nor excluded is an ERROR and
    not a silent omission, the same rule `frame_mask.load_reference`
    applies — a screen that quietly skipped a malformed rect would
    draw thirteen boxes and look almost right.
    """
    data = screen.app.res.load_json(
        f"screens/{screen.SCREEN_NAME}/{REFERENCE}", {}) or {}
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
    return out


def radius(screen):
    """The corner radius in DEVICE px, from `layout.json`.

    Rounded rather than truncated: at 1920 the reference value IS the
    device value, and truncating 3 * 1.333 at 1440p would give 3
    where the rim is 2 device px thick, which draws a corner tighter
    than the band that has to follow it.
    """
    ref = screen._data.get("frame", {}).get(
        "plate_corner_radius", CORNER_RADIUS_REF)
    return max(0, round(ref * screen.layout.scale))


def fill_colour(screen, name):
    """The fill a window takes, or None if it draws its own.

    `layout.json`'s `panels` block is the authority and is unchanged
    by any of this: a window listed there gets `PANEL_BG` unless it
    names its own `<name>_fill` beside it, which the galaxy inset
    does. `return` is not in that block — it fills itself in
    `colonysort.render_return`, because it is the one control here
    that takes the CLICK path and draws its own button.
    """
    from .screen import PANEL_BG
    panels = screen._data.get("panels", {})
    box = _box_name(name)
    if box not in panels:
        return None
    return tuple(panels.get(box + "_fill") or PANEL_BG)[:3]


#: `layout_reference.json` names a RECTANGLE, `boxes.json` names a
#: BOX, and two of them differ. `tools/frame_holes.BOX_NAME` holds the
#: same mapping for the tool side; a smoke check holds the two to each
#: other, and Phase B leaves this one.
BOX_NAME = {"return_button": "return", "list": "list_area"}


def _box_name(name):
    return BOX_NAME.get(name, name)


#: Reference-pixel bleed, so content covers what overlaps a box's own
#: edge — the frame's rim on the static path, the drawn rim on the
#: plateless one. **ONE NUMBER, AND `tools/boxes_from_reference.py`
#: IMPORTS IT FROM HERE** rather than keeping its own: the tool writes
#: `boxes.json` and this module rebuilds the same rects at startup, so
#: a second copy would let a file on disk and a screen in memory
#: disagree by two pixels and nothing would say so.
BLEED = 2


def box_rects(screen):
    """{box name: [x, y, w, h]} — the cutouts, reference px, bled.

    **DERIVED AT STARTUP, NOT READ** — 12 September 2026. `boxes.json`
    is written from `layout_reference.json` by
    `tools/boxes_from_reference.py`, and until now the screen read the
    written file: edit the reference, forget the tool, and the screen
    draws yesterday's fills behind today's frame with nothing saying
    so. That happened the same day it became possible. The rects are
    rebuilt here from the reference every time the boxes are loaded,
    so the file on disk is a cache of this and never the authority.

    THE SIX COLUMN BOXES ARE NOT TOUCHED. They are strips of
    `list_area` placed by hand in the editor (decision 14) and have no
    rectangle in the reference to be derived from — `list_columns`
    declares their SPLIT and `tools/boxes_from_reference.py --columns`
    seats them from it, which is a deliberate act and not a startup.
    """
    return {BOX_NAME.get(n, n): [x - BLEED, y - BLEED,
                                 w + 2 * BLEED, h + 2 * BLEED]
            for n, (x, y, w, h) in windows(screen).items()}


def reseat(screen):
    """Rewrite every cutout box's `ref_rect` from the reference.

    Called from `_reload_boxes`, so it runs on load AND on every
    resize — `ScreenBase.on_resize` replaces `screen.boxes` with
    freshly parsed objects, and a derivation that ran only at
    `enter()` would be undone by the first F9 (the fault
    `colonyheader.install_columns` records for the column table).
    """
    want = box_rects(screen)
    for box in screen.boxes:
        rect = want.get(box.name)
        if rect and tuple(box.ref_rect) != tuple(rect):
            box.ref_rect = tuple(rect)
            box.update_layout(screen.layout)
    return want


def fill(screen, surface, rect, colour):
    """Lay a window's fill, rounded when this screen draws its boxes.

    **ONE CALL FOR BOTH MODES** (decision 5's shape for a drawing):
    `screen._render_panels` and `colonysort.render_return` both come
    here, so a fill can never be square in one place and rounded in
    another. With the plate on it is `surface.fill` exactly as it has
    always been — the rounding is the only difference the flag makes
    to a fill, and it has to be there or the fill's square corner
    shows outside the rim's rounded one.
    """
    rect = pygame.Rect(rect)
    if not active(screen):
        surface.fill(tuple(colour)[:3], rect)
        return
    screen.style.draw_plate(surface, rect, screen.layout.scale,
                            color=tuple(colour)[:3],
                            radius=radius(screen), fill=colour)


def render_fills(screen, surface):
    """Every cutout that shows content gets its panel fill.

    **THE LOOP LIVES HERE AND NOT ON THE SCREEN** — moved 12 September
    2026, when `screen.py` crossed the 300-line guideline by two. It
    belongs here on its own merits either way: what a fill IS, which
    box gets one, and whether it is square or rounded are one
    question, and `fill` below already answered the last third of it
    from this module while the first two thirds sat in `screen.py`.

    A panel may name its own fill as `<name>_fill` BESIDE IT in the
    `panels` block — the galaxy inset does, and
    `_galaxy_inset_fill_note` carries the measurement it rests on. A
    per-box value rather than a renderer change, because
    `colonyinset` draws no background at all, by transcription
    (movebox.cpp:36-38).

    **AND IT IS READ FROM `panels`, NOT FROM THE TOP LEVEL.** For a
    day it was `screen._data.get(name + "_fill")` while the value sat
    in `panels` — so the lookup found nothing, every panel silently
    took `PANEL_BG`, and the status document said the inset was black
    on the strength of the measurement that chose the value rather
    than of the frame it was drawn in. A missing key here cannot
    raise, because most panels have none; the smoke check is what
    makes a stray one visible.
    """
    from .screen import PANEL_BG
    panels = screen._data.get("panels", {})
    for name in panels:
        box = (None if name.startswith("_") or name.endswith("_fill")
               else screen.box_rect(name))
        if box:
            fill(screen, surface, pygame.Rect(*screen.layout.rect(box)),
                 tuple(panels.get(name + "_fill") or PANEL_BG)[:3])


def render(screen, surface):
    """Draw every window's rim and lit line, over the content.

    Called where the frame image is blitted, and for the same reason
    it is blitted there: the rim belongs on TOP of what the box
    holds, the way the plate's metal overlapped every cutout. The
    fill went down earlier, with the panels.

    Nothing is drawn between the boxes — see the module docstring.
    """
    if not active(screen):
        return
    colors = screen.style.colors
    rim = colors.get("panel", {}).get("border", [60, 80, 120])
    line = colors.get("panel", {}).get(
        "border_highlight", [100, 140, 200])
    r = radius(screen)
    band = max(1, round(RIM_REF * screen.layout.scale))
    for name in windows(screen):
        box = screen.box_rect(_box_name(name))
        if not box:
            continue
        screen.style.draw_plate(
            surface, pygame.Rect(*screen.layout.rect(box)),
            screen.layout.scale, color=line, radius=r,
            rim=rim, rim_width=band)
