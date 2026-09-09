"""The list's five column headings, plus the scroll slot.

**DEVIATION — THE HEADER WINDOW IS OURS.** The original has no header
window. It draws five raised plates directly on the frame's metal,
each a recessed dark field with a light rounded outline: measured on
the live framebuffer of screen 20, a plate interior sits at luminance
**44** against metal at **60**, with the outline at **96**. We cut a
window instead and draw the plates inside it, so **the window's own
panel fill stands in for the original's plate recess** — one dark
field behind five outlines rather than five dark fields on metal.

Chosen at Stage 4 over closing the hole and drawing plates on the
plate's metal, because the metal there is not bare: with the header
window removed the gap between ring and list grows to about 74 ref px
and the Stage A3 rail pass fills it with a stretched rail. That is
buildable, but it is a change to the plate machinery and a fill under
every plate, and it is not what Stage 4 is for. Marked here, in
`layout.json` under `header._deviation_window`, in
`v3_projektstatus.md`, and in a smoke check.

**DEVIATION — THE OUTLINE COLOUR.** The original's outline is a
neutral grey at luminance 114-124. Ours is `panel.thin_border`,
[55, 65, 85], luminance about 68 and blue — the project's own panel
language (decision 34), used so the header reads as part of this UI
rather than as a transplanted sprite. The value lives in
`colors.json` and the marking travels with it.

**THE PLATE HEIGHT IS A FINDING, NOT A CHOICE — see below.**

**TRANSCRIBED: THE PLATES SHARE THEIR EDGE.** They do not sit in a
row with gaps between them. The framebuffer shows two interiors of 44
separated by exactly two pixels at 85 and 93 — one divider, belonging
to both neighbours. So the plates here are laid edge to edge and the
divider is `DIVIDER_REF`, 6 reference px, which is that 2 native px
at x3. An earlier draft used a 9 px gap and it was invented.

**THE COLUMNS ARE THE LIST'S OWN**, from `layout_reference.json`, so
a heading is always exactly as wide as the column under it and the
two cannot drift.
"""
import os

import pygame

from core import zoomtables

#: The original's plate divider: 2 native px, shared by both
#: neighbours (framebuffer, x 99-100 between NAME and FARMERS).
DIVIDER_REF = 6

#: What the original's own plate measures, top outline to bottom
#: outline: native y 11..32 = 22 px, which is 66 reference px.
#:
#: **IT DOES NOT FIT AND THAT IS RECORDED RATHER THAN ABSORBED.** The
#: header window is 48 reference px of drawable height (52 with
#: `frame_holes.BLEED`), so the transcribed plate is 18 px taller than
#: the window can hold — 37 % over. The plates therefore fill the
#: window instead, and this constant is what says so. Closing the gap
#: means giving the header 66 px and taking 18 from the list (605 ->
#: 587), which is a layout decision and not a drawing one.
PLATE_HEIGHT_NATIVE = 22
PLATE_HEIGHT_REF = PLATE_HEIGHT_NATIVE * 3

#: Reference px of window left above and below the plates, so the
#: frame's own rim is not overdrawn.
INSET_REF = 2


#: The six column boxes, in ECON order with the name column first
#: and the scroll slot last. **THE BOXES ARE THE COLUMNS** — one rect
#: per column, F5-draggable (decisions 14 and 5), and the header
#: plate, the cell column and the scroll slot all read it.
COLUMN_BOXES = ("col_name", "col_farmers", "col_workers",
                "col_scientists", "col_building", "col_scroll")


def column_boxes(screen):
    """[(key, Box)] for the six column boxes, or [] if any is absent.

    **THE BOX OBJECT AND NOT ITS RECT.** A `Box` is mutable and the
    editor mutates `ref_rect` in place while dragging
    (`Editor._on_drag`), so handing the object over is what makes the
    preview live: every consumer reads the rect it has THIS frame
    rather than a copy taken when the screen loaded. That was the
    whole reason `install_columns` baked a table at init and the
    whole reason it could not be dragged.

    All six or none: a partial set would silently fall through to the
    single-track geometry, which is the pre-Stage-4 row and looks
    almost right.
    """
    by_name = {b.name: b for b in screen.boxes}
    got = [(n[4:], by_name[n]) for n in COLUMN_BOXES if n in by_name]
    return got if len(got) == len(COLUMN_BOXES) else []


def install_columns(screen):
    """Bind the six column boxes, and `list_area`'s reference span,
    into the screen's `list` block.

    They travel with every other row value rather than sitting on the
    screen, so `colonytrack` reads them the way it read the baked
    table — and a fixture that wants the column row installs the same
    way, which is what stops a check from silently exercising the
    single-track path instead.

    **IDEMPOTENT, AND CALLED AGAIN WHENEVER THE BOXES ARE — corrected
    9 September 2026.** This used to say "called ONCE, on load: what
    is stored is the live objects, so nothing has to be refreshed
    when one moves". The first half was true and the second did not
    follow. A box moving is not the only thing that happens to it:
    `ScreenBase.on_resize` calls `_reload_boxes`, which REPLACES
    `screen.boxes` with freshly parsed objects, and the table bound
    at `enter()` then held six boxes that were no longer the screen's
    — laid out for the window size the screen was entered at and
    never touched again. `sync_columns` runs this first for exactly
    that reason, so the table is never older than the frame it is
    read in.

    The SPAN is bound here rather than looked up where it is used,
    because a lookup that misses returns the common case and cannot
    report itself (fundament, "the background you see is not always
    the background that is set"): `columns` answers `{}` without it
    and the single-track path is a legitimate state.
    """
    from . import colonytrack
    table = column_boxes(screen)
    block = screen._data.setdefault("list", {})
    block[colonytrack.COLUMNS_KEY] = table
    area = screen.box_rect("list_area")
    block[colonytrack.COLUMNS_SPAN_KEY] = (
        (area[0], area[2]) if area and table else None)
    return table


def sync_columns(screen):
    """Rebind the column table, then hold the six boxes to the list
    window's own y and height.

    **A COLUMN DRAGGED VERTICALLY IS IGNORED, and this is what makes
    that visible rather than merely true.** Only the LEFT EDGE is
    read (`colonytrack.columns`): y and height come from `list_area`
    because a column is a strip of the list, and the width is the
    distance to the next column because the six have to tile the
    window exactly. Without this the outline would follow a drag that
    nothing else obeyed, and a save would write the stray numbers
    into `boxes.json`.

    The rebind is first because everything below reads
    `screen.boxes`, and the table has to be the same six objects or
    this function repairs one set while `colonytrack` reads another —
    which is precisely the state the 8 September screenshots were
    taken in.
    """
    install_columns(screen)
    box = screen.box_rect("list_area")
    if not box:
        return
    ax, y, aw, h = box
    boxes = sorted(column_boxes(screen), key=lambda kb: kb[1].ref_rect[0])
    for i, (_key, b) in enumerate(boxes):
        bx = b.ref_rect[0]
        right = (boxes[i + 1][1].ref_rect[0] if i + 1 < len(boxes)
                 else ax + aw)
        want = (bx, y, max(1, right - bx), h)
        if tuple(b.ref_rect) != want:
            b.ref_rect = want
            b.update_layout(screen.layout)


def plate_rects(header_box, cols, scale):
    """[(key, rect)] — one plate per column heading, window pixels.

    **THE COLUMN'S OWN RECT, NOT A SECOND TILING.** `cols` is what
    `colonytrack.columns` answers — `{key: (x, width)}` in window
    pixels, read off the six column boxes — so the heading above a
    column and the cells inside it come from ONE rect (decision 5).
    Until 8 September 2026 this tiled the header box itself from a
    ref-width table, which is the second copy that agreed by
    construction until somebody dragged one.

    `header_box` supplies only the vertical: the plates sit in the
    header cutout and the columns run down the list.
    """
    box = pygame.Rect(header_box)
    if not cols:
        return []
    inset = max(1, round(INSET_REF * scale))
    half = max(1, round(DIVIDER_REF * scale / 2))
    return [(key, pygame.Rect(
        x + half, box.y + inset,
        max(1, w - 2 * half), max(1, box.height - 2 * inset)))
        for key, (x, w) in cols.items()]


def render_for(screen, surface, outline, text_color):
    """Draw `screen`'s headings. Nothing to do without a header box."""
    box = screen.box_rect("header")
    if not box:
        return
    from . import colonytrack
    cfg = screen._data.get("header", {})
    area = pygame.Rect(*screen.layout.rect(screen.box_rect("list_area")))
    render(surface, screen.layout.rect(box),
           colonytrack.columns(area, screen._data.get("list", {})),
           cfg.get("labels", {}), screen.style,
           screen.layout.font_size(cfg.get("font_size", 20)),
           outline, text_color, screen.layout.scale)


def render(surface, header_box, cols, labels, style, font_size,
           outline, text_color, scale):
    """Draw the plates and their headings.

    `cols` is `colonytrack.columns`' answer, `labels` a key -> word
    map; a key with no word (the scroll slot) gets its plate and no
    text, which is what the original does with the column its scroll
    arrow sits in.

    The plate itself is `StyleRenderer.draw_plate` (decision 51) —
    this used to paste `max(6, int(10 * scale))` and a 1 px rounded
    rect, which was `draw_thin_border`'s arithmetic in a second home.
    """
    for key, rect in plate_rects(header_box, cols, scale):
        style.draw_plate(surface, rect, scale, outline)
        word = labels.get(key)
        if not word:
            continue
        text = style.render_text(word.upper(), font_size, text_color[:3])
        if text.get_width() > rect.width - 8:
            continue
        surface.blit(text, (rect.x + (rect.width - text.get_width()) // 2,
                            rect.y + (rect.height - text.get_height()) // 2))


def editor_note(screen, box):
    """What a column box means, for the F5 info bar.

    **Everything this line reports is DERIVED and has no rect the
    editor could show**: the row band is `list_area` divided by
    `list.row_count`, the sprite step is the largest that fits
    that band, and the fill is what a column holds against what
    the original's holds. Dragging a column without them is
    dragging blind.

    For `col_name` it reports the LOWER BOUND and never clamps to
    it — the widest name the game can make is `WWWWWWW IV`,
    because `Do_Change_Star_Name_` caps the input field at the
    pixel width of seven W's (namestar.cpp:246-256) on top of the
    `char[15]` buffer. **That cap is measured in FONTS.LBX style
    3, which this project cannot read**, so the translation into
    this font is close and not exact — which is exactly why this
    is a report and not a clamp. Same gap as the "No Farming"
    size; the font extractor is owed twice now.
    """
    if not box.name.startswith("col_"):
        return None
    area, cfg, _scale, _n = screen._list_view()
    if not area.width:
        return None
    key = box.name[4:]
    from . import colonyicons, colonylist, colonytrack
    cols = colonytrack.columns(area, cfg)
    if key not in cols:
        return None
    width = cols[key][1]
    band = colonytrack.band_height(area, cfg)
    step = colonytrack.figure_step(area, cfg)
    px = screen.layout.font_size(cfg.get("name_font", 21))
    if key == "name":
        small = screen.layout.font_size(cfg.get("small_font", 15))
        return (f"{width}px band {band} | min "
                f"{screen.style.render_text(colonylist.NAME_BOUND_STAR, px, (255,)*3).get_width()}px "
                f"({colonylist.NAME_BOUND_STAR}) / "
                f"{screen.style.render_text(colonylist.NAME_BOUND_DETAIL, small, (255,)*3).get_width()}px "
                f"({colonylist.NAME_BOUND_DETAIL}) — REPORTED, "
                f"not clamped; {colonylist.NAME_BOUND_NOTE}")
    native = zoomtables.NATIVE_JOB_COLUMNS.get(key)
    if native is None:
        return f"{width}px band {band} step {step} (no native share)"
    fits = max(0, width // (colonyicons.ICON_SPACING * step))
    return (f"{width}px band {band} step {step} | fits {fits} "
            f"unsqueezed | fill {step * native / width * 100:.0f}% "
            f"of the original's")
