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


def columns(res, screen_name):
    """[(key, reference width)] — the list's own column table.

    From `layout_reference.json`, so a heading is exactly as wide as
    the column beneath it by construction and the two cannot drift.
    The three JOB widths are transcribed from
    COLSUM::Get_Selected_Pop_ (colsum.cpp:1006-1024), which passes the
    column bounds as literals; see that file's `_list_columns_note`.
    """
    data = res.load_json(
        os.path.join("screens", screen_name, "layout_reference.json"),
        {}) or {}
    return list(data.get("list_columns", {}).items())


def plate_rects(header_box, columns, scale):
    """[(key, rect)] — one plate per column, window pixels.

    `header_box` is the header cutout in WINDOW pixels and `columns`
    the [(key, ref_width)] list `layout_reference.json` carries. The
    plates tile the box exactly: the last one takes what integer
    division left, so the row can never end short of the column it
    heads.
    """
    box = pygame.Rect(header_box)
    total = sum(w for _k, w in columns)
    if total <= 0:
        return []
    inset = max(1, round(INSET_REF * scale))
    half = max(1, round(DIVIDER_REF * scale / 2))
    out = []
    x = box.x
    for i, (key, ref_w) in enumerate(columns):
        w = (box.right - x if i == len(columns) - 1
             else round(box.width * ref_w / total))
        out.append((key, pygame.Rect(
            x + half, box.y + inset,
            max(1, w - 2 * half), max(1, box.height - 2 * inset))))
        x += w
    return out


def render_for(screen, surface, outline, text_color):
    """Draw `screen`'s headings. Nothing to do without a header box."""
    box = screen.box_rect("header")
    if not box:
        return
    cfg = screen._data.get("header", {})
    render(surface, screen.layout.rect(box),
           columns(screen.app.res, screen.SCREEN_NAME),
           cfg.get("labels", {}), screen.style,
           screen.layout.font_size(cfg.get("font_size", 20)),
           outline, text_color, screen.layout.scale)


def render(surface, header_box, columns, labels, style, font_size,
           outline, text_color, scale):
    """Draw the plates and their headings.

    `columns` is [(key, ref_width)], `labels` a key -> word map; a key
    with no word (the scroll slot) gets its plate and no text, which
    is what the original does with the column its scroll arrow sits
    in.
    """
    radius = max(6, int(10 * scale))
    for key, rect in plate_rects(header_box, columns, scale):
        pygame.draw.rect(surface, outline[:3], rect, 1, border_radius=radius)
        word = labels.get(key)
        if not word:
            continue
        text = style.render_text(word.upper(), font_size, text_color[:3])
        if text.get_width() > rect.width - 8:
            continue
        surface.blit(text, (rect.x + (rect.width - text.get_width()) // 2,
                            rect.y + (rect.height - text.get_height()) // 2))
