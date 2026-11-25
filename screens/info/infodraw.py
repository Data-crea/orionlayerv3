"""Drawing the Info screen, in the HUD style — every piece at the HD image
of its native rectangle (`infogeom`, through the Leaders screen's
`nativedraw` helpers), every text through `core/modtexts` and `infobox`.

  OMISSION     `outer_frame` — INFO.LBX 0 (the frame with the tabs, the
               drop areas and the chart painted in) and the interlaced
               fill are not drawn: glass HUD panels stand where they are
  (`app_pictures`, an OMISSION until work order 196 F: the Tech Review's
  APP_PICS.LBX pictures are extracted by `tools/info_art_extract.py` and
  drawn, `infoart`; the box stays empty only while they are absent)
  DEVIATION    `button_words` — the tabs, the tech categories, the metric
               toggles, BACK and RETURN are words the original bakes into
               INFO.LBX; HD writes OrionLayer's words (moddable, `own`)
  DEVIATION    `chart_colours` — the chart's bars in the original's colours
               (order from info.cpp:311, RGB measured off a screenshot), flat
               where the original shades them in 3D; the texts in HUD tones, not
               INFO.LBX 22-25 recoloured by `_maintenance_bar_colors`
  HD EXTENSION `legend_bars` — the legend rows are the bars themselves, as
               in the original, the word in the tone that reads best on each
  HD EXTENSION `legend_columns` — the legend's numbers right-aligned in
               one column, the words left-aligned beside it
  HD EXTENSION `wrap_and_scroll` — `infobox`
"""
import pygame

from core import fontscale, modtexts, textfit
from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core import lang
from core import nativedraw as nd

from . import infobox, infogeom as geom, infopages as pages

T = modtexts.text
#: The Info screen's text colours, `_info_normal_color` / `_high_color`
#: body indices (info.cpp:111-113) as HUD tones — INFO.LBX's palette is
#: not extracted (DEVIATION `chart_colours` covers the text too).
NORMAL, HIGH, RED = (150, 190, 215), (235, 240, 245), (225, 70, 60)
#: The chart's seven bars and legend rows. TRANSCRIPTION of the ORDER
#: (`maintenance_bar_colors`, info.cpp:311: orange, grey, red, purple,
#: yellow, blue, green); the RGB are measured off a native screenshot of
#: the original's legend (mid-tone of each row, Data's picture of 30 October
#: 2026) because INFO.LBX's palette is not extracted (DEVIATION
#: `chart_colours`: the bars' flat colour for the original's shaded 3D bars).
BAR_COLOURS = ((228, 152, 0), (143, 143, 143), (133, 12, 12),
               (123, 0, 143), (175, 175, 0), (0, 0, 207), (12, 125, 12))


#: The text on a legend bar: the darker or the lighter of two tones,
#: whichever stands at the higher contrast on the bar's colour (WCAG; every
#: bar clears 4.5:1, the word floor of decision 94). HD EXTENSION
#: `legend_bars`: the original's rows are shaded bars with the word in the
#: game's own text colour; HD picks it by contrast so each stays readable.
BAR_TEXT = ((14, 14, 16), (250, 250, 252))


#: Native width of the legend's number column, from the row's left edge:
#: "100%" at the status size with a margin each side.
LEGEND_NUMBER_W = 52


def bar_text(bar):
    from core.hud import tint
    lum = float(tint.luminance(bar))

    def ratio(t):
        other = float(tint.luminance(t))
        return (max(lum, other) + 0.05) / (min(lum, other) + 0.05)
    return max(BAR_TEXT, key=ratio)


def R(screen, native):
    return nd.rect(screen.layout, native)


def px(screen, key):
    return nd.font_px(screen.layout, key)


def draw_frame(surface, screen, page):
    # In the shell the content panel is the screen's own box (the original's
    # content area reaches up under the title, which stands on the plate).
    panel = screen.box_screen_rect("content_panel")
    nd.draw_box(surface, screen, geom.LEFT_PANEL)
    if panel is not None and getattr(screen, "SHELL_WORN", False):
        hud.panel(surface, panel, screen.ref_layout.scale)
    else:
        nd.draw_box(surface, screen, geom.CONTENT)
    layout = screen.layout
    for k, name in enumerate(pages_names()):
        r = R(screen, geom.tab_rect(k))
        hud.small_button(surface, r, layout.scale,
                         "active" if k == page else "normal")
        infobox.line(surface, screen, T(f"info.tab.{name}", name).upper(),
                     r.inflate(
            -8, 0), px(screen, "button"), hudtext.colour("button"), "center")
    # EXIT: the slanted closing action in the content panel's corner; the
    # page's title stands on the shell's plate (work order 225).
    shell.draw_button(surface, screen.exit_rect(), screen.ref_layout,
                      T("info.exit", "RETURN"), screen.style)


def field(surface, screen, native):
    """A content box inside the page: the original's inset field (its
    striped green box) is the shared field since work order 223 —
    inside the two panels, not a third panel."""
    r = R(screen, native)
    hud.field(surface, r, screen.layout.scale)
    return r


def backdrop(surface, screen, box, anchor=(0.5, 0.5)):
    """HD EXTENSION `howto_background`: the player's background picture
    inside the field `box` (the Reference's boxes; nothing without the
    picture)."""
    from . import inforef
    inner = hud.panel_inner(box, screen.layout.scale).inflate(-4, -4)
    back = inforef.background(inner.size, anchor)
    if back is not None:
        surface.blit(back, inner.topleft)


def pages_names():
    from .infotexts import PAGES
    return PAGES


def draw_stardate(surface, screen, stardate):
    x, y = geom.STARDATE_AT
    r = R(screen, (x - 60, y - 9, x + 60, y + 9))
    text = pages.stardate_text(stardate, lang.engine_language_number())
    infobox.line(surface, screen, text, r, px(screen, "name"), HIGH, "center")


def draw_chart(surface, screen, player):
    """`Draw_Maint_Income_Chart_` (info.cpp:732-776) in HUD parts."""
    nd.draw_box(surface, screen, geom.CHART_BOX)
    income, maint, pct, net = pages.chart(player)
    h = geom.BAR_BOTTOM - geom.BAR_TOP
    # a bar is skipped when its value is below 1 (info.cpp:688); a negative
    # value counted as visible and shifted the others (WO 427)
    visible = [k for k in range(1, 7) if pct[k] >= 1]
    x_of = {0: geom.INCOME_BAR_X}
    x = (len(visible) * 18 - 42) // 2 + 120
    for k in range(6, 0, -1):
        if pct[k] >= 1:
            x_of[k] = x
            x -= 18
    for k, bx in x_of.items():
        top = geom.BAR_BOTTOM - h * pct[k] // 100
        r = R(screen, (bx, top, bx + geom.BAR_W - 1, geom.BAR_BOTTOM))
        if r.h > 0:
            # LOOK EXCEPTION data: an expense's bar, one colour per expense
            pygame.draw.rect(surface, BAR_COLOURS[k], r)
    net_text = pages.stat(T("info.chart.net_income", ""), net)
    x, y = geom.NET_AT
    infobox.line(surface, screen, net_text, R(screen, (x - 90, y - 7, x + 90,
                                                       y + 7)),
                 px(screen, "status"), RED if net < 0 else NORMAL, "center")
    for (x, y), key in ((geom.INCOME_HEAD_AT, "info.chart.income"),
                        (geom.MAINT_HEAD_AT, "info.chart.maintenance")):
        infobox.line(surface, screen, T(key, "") or "",
                     R(screen, (x - 40, y - 5, x + 40, y + 5)),
                     px(screen, "note"), NORMAL, "center")
    x0, y0 = geom.LABEL_AT
    w = geom.LABEL_SIZE[0]
    names = ("income", "buildings", "freighters", "ships", "spies",
             "tribute", "leaders")
    for k, name in enumerate(names):
        y = y0 + k * geom.LABEL_STEP
        label = (T(f"info.chart.label.{name}", "") or "").strip()
        number = f"{income}" if k == 0 else f"{pct[k]}%"
        # a row is no taller than its step: the original's 20 px sprites
        # overlap by their shading, flat fills would show the overlap
        r = R(screen, (x0, y, x0 + w - 1, y + geom.LABEL_STEP - 2))
        # LOOK EXCEPTION data: an expense's bar, one colour per expense
        pygame.draw.rect(surface, BAR_COLOURS[k], r)
        # HD EXTENSION `legend_columns` (Data, 30 October 2026): the numbers
        # stand right-aligned in one column and the words left-aligned in
        # the next, so the rows read as a table (the original's proportional
        # text left the digits and words ragged).
        tone = bar_text(BAR_COLOURS[k])
        size = px(screen, "status")
        infobox.line(surface, screen, number,
                     R(screen, (x0 + 4, y, x0 + LEGEND_NUMBER_W, y + geom.LABEL_STEP - 2)),
                     size, tone, "right")
        infobox.line(surface, screen, label,
                     R(screen, (x0 + LEGEND_NUMBER_W + 8, y, x0 + w - 4,
                                y + geom.LABEL_STEP - 2)),
                     size, tone, "left")


#: HD EXTENSION `reference_pictures`: the wide pictures' height as a share of
#: their box — the BOX's, not the text's: the player's text size moves the
#: rows, never the picture (Data, 22 Nov). 0.25 of a list's 790 px at 1080 is
#: 197 px, the mockup's own proportion (its pictures are a quarter of the box).
ART_H = 0.25
#: the how-to's ship picture is larger (Data's mockup, 24 Nov)
HOWTO_ART_H = 0.32


def rows(surface, screen, key, native, items, selected=None, lit=None,
         icons=None, reserve=0.0, back=False, marks=False,
         anchor=(0.5, 0.5)):
    """A scrolling list of one-line rows — `(text, payload, header)` — each
    shrunk to its width. Returns nothing; its hit rects go to
    `screen._hits[key]` as (rect, payload). `icons`, when given, maps a
    row's payload to the picture drawn in front of its words (HD EXTENSION
    `reference_icons`, `inforef`); a row it gives None for has the words
    only, and a list with no picture at all keeps the pitch it always had.
    `reserve` is the share of the box's height kept free at its foot for a
    picture (`ART_H`): the symbols' taller pitch never eats into it."""
    box = field(surface, screen, native)
    if back:
        backdrop(surface, screen, box, anchor)
    inner = hud.panel_inner(box, screen.layout.scale).inflate(-4, -4)
    # HD EXTENSION `font_scale` (WO 356): the pitch follows the text size
    # (the factor is 1.0 by default, so the product is unchanged).
    step = int(px(screen, "skill") * fontscale.factor() * 1.35)
    if marks:
        inner = inner.inflate(-10, -12)       # clear of the box's edge
        # HD EXTENSION `howto_prose` for a topic list: looser rows, as many
        # as fit (a longer list keeps the old pitch and scrolls)
        step = max(step, min(int(step * 1.45), inner.h // max(1, len(items))))
    pics = [icons(item[1]) if icons else None for item in items]
    if any(p is not None for p in pics):
        # room for a symbol: taller rows (a third more), never so tall that
        # a scrollbar is needed, never shorter than the words' own pitch
        free = inner.h - int(inner.h * reserve) - 12
        step = max(step, min(int(step * 1.3), free // max(1, len(items))))
    total = step * len(items)
    overflow = max(0, total - inner.h)
    if overflow:
        inner.w -= max(6, step // 3) + 2
    offset = max(0, min(screen._scroll.get(key, 0), overflow))
    screen._scroll[key] = offset
    hits = []
    y = inner.y - offset
    previous = surface.get_clip()
    surface.set_clip(inner)
    for n, item in enumerate(items):
        text, payload, header = item[:3]
        # HD EXTENSION `tech_review_groups`: a group row may carry a count
        # on its right and a fold mark (`opened` True / False) on its left.
        count = item[3] if len(item) > 3 else None
        opened = item[4] if len(item) > 4 else None
        indent = item[5] if len(item) > 5 else 0      # `reference_groups`
        r = pygame.Rect(inner.x, y, inner.w, step)
        if inner.contains(r):
            colour = HIGH if header or payload in (selected, lit) else NORMAL
            if payload is not None and payload == selected and marks:
                from . import infoprose
                infoprose.paint_band(surface, r)       # the gold band
            elif payload is not None and payload == selected:
                # The chosen entry is 'on' (work order 223, proposal C).
                hud.field(surface, r, screen.layout.scale, on=True)
            if marks:
                from . import infoprose
                sq = max(4, step // 4)
                # LOOK EXCEPTION marking: a topic's gold square and the rows' faint rule, Data's mockup (24 Nov)
                pygame.draw.rect(surface, infoprose.GOLD, (
                    r.x + 10, r.centery - sq // 2, sq, sq))
                # LOOK EXCEPTION marking: a topic's gold square and the rows' faint rule, Data's mockup (24 Nov)
                pygame.draw.line(surface, (70, 52, 22), (r.x + 4, r.bottom - 1),
                                 (r.right - 4, r.bottom - 1))
            if header and opened is not None:
                text = ("v  " if opened else ">  ") + text
            line = r.inflate(-4, 0) if header and pics[n] is None \
                else r.inflate(-16, 0).move(8, 0)
            if marks:
                line = line.move(max(4, step // 4) + 10, 0)
                line.w -= max(4, step // 4) + 10
            if count:
                infobox.line(surface, screen, count, line,
                             px(screen, "skill"), colour, "right")
                line.w -= px(screen, "skill") * 4
            if indent:
                line = line.move(indent * max(12, step - 6), 0)
                line.w -= indent * max(12, step - 6)
            if pics[n] is not None:
                side = max(12, step - 6)
                k = min(side / pics[n].get_width(),
                        side / pics[n].get_height())
                pic = pygame.transform.smoothscale(
                    pics[n], (max(1, round(pics[n].get_width() * k)),
                              max(1, round(pics[n].get_height() * k))))
                surface.blit(pic, (line.x + (side - pic.get_width()) // 2,
                                   r.centery - pic.get_height() // 2))
                line = line.move(side + 8, 0)
                line.w -= side + 8
            infobox.line(surface, screen, text, line, px(screen, "skill"),
                         colour)
            if payload is not None:
                hits.append((r, payload))
        y += step
    surface.set_clip(previous)
    if overflow:
        hud.scrollbar(surface, pygame.Rect(inner.right + 2, inner.y,
                                           max(6, step // 3), inner.h),
                      screen.layout.scale, offset, inner.h, total)
    screen._hits[key] = hits
    screen._boxes[key] = _ListBox(box, overflow, step, inner,
                                  inner.y - offset + total)


class _ListBox:
    def __init__(self, rect, overflow, step, inner=None, rows_end=0):
        self.rect, self.overflow, self.step = rect, overflow, step
        #: the rows' area and the y under the last row (a picture's room)
        self.inner, self.rows_end = inner, rows_end


def head(surface, screen, native, title, count=None):
    """HD EXTENSION `reference_heads`: a list's head — its title vertically
    centred in the field and, when given, a count at the right in the dim
    tone (Data's mockup: "TECHNOLOGY DATABASE  14 ENTRIES")."""
    box = field(surface, screen, native)
    inner = box.inflate(-24, -8)
    key = px(screen, "name")
    if count:
        infobox.line(surface, screen, count, inner, px(screen, "skill"),
                     NORMAL, "right")
        inner.w -= px(screen, "skill") * 8
    infobox.line(surface, screen, title, inner, key, HIGH)


def _art_size(picture, room_w, box_h, share=None):
    """The picture at `ART_H` of the box's height (width from its
    proportion), narrowed to `room_w` when that is wider."""
    k = box_h * (share or ART_H) / picture.get_height()
    k = min(k, room_w / picture.get_width())
    return (max(1, round(picture.get_width() * k)),
            max(1, round(picture.get_height() * k)))


def art_below(surface, screen, key, picture):
    """HD EXTENSION `reference_pictures`: `picture` at the foot of the list
    `key`, centred, at a size that follows the box and never the text
    (`ART_H`); nothing when the rows reach into its room or the list
    scrolls."""
    box = screen._boxes.get(key)
    if picture is None or box is None or box.inner is None or box.overflow:
        return
    size = _art_size(picture, box.inner.w - 12, box.inner.h)
    top = box.inner.bottom - 6 - size[1]
    if top < box.rows_end + 6:
        return
    surface.blit(pygame.transform.smoothscale(picture, size),
                 (box.inner.centerx - size[0] // 2, top))


def art_in(surface, screen, native, picture, share=None):
    """HD EXTENSION `reference_pictures`: `picture` at the foot of a text
    box, at the same share of the box as under the lists (`ART_H`); a box
    under 300 px high gets none."""
    if picture is None:
        return
    box = R(screen, native)
    if box.h < 300:
        return
    room = box.inflate(-24, -16)
    size = _art_size(picture, room.w, room.h, share)
    surface.blit(pygame.transform.smoothscale(picture, size),
                 (room.centerx - size[0] // 2, room.bottom - size[1]))


def text(surface, screen, key, native, body, size_key="skill", colour=NORMAL,
         align="left", panel=True, size_mul=1.0, back=False):
    rect = R(screen, native)
    if panel:
        field(surface, screen, native)
        if back:
            backdrop(surface, screen, rect)
        # Clear of the field's outline (`blocks.panel_inner`).
        rect = hud.panel_inner(rect, screen.layout.scale).inflate(-4, -4)
    infobox.Box(key, rect, body or "", int(px(screen, size_key) * size_mul),
                colour, align).draw(surface, screen)


def prose(surface, screen, key, native, body, struct=None, given=None,
          picture=None, anchor=(0.5, 0.5), inset=0.0):
    """HD EXTENSION `howto_prose`: a how-to's body set as a reading text
    (`infoprose`) in the page's panel, in a little larger type than `text`;
    `struct` is the topic's resolved bands and note, if it has any."""
    from . import infoprose
    rect = R(screen, native)
    field(surface, screen, native)
    backdrop(surface, screen, rect, anchor)
    rect = hud.panel_inner(rect, screen.layout.scale).inflate(-4, -4)
    from . import inforef
    base = px(screen, "skill")
    if inset:           # an article stands clear of its box's edge
        rect = rect.inflate(-int(2 * base * inset), -int(base * inset))
    if picture is not None and rect.h >= 300:
        # the picture's room is the text's no more: the picture stands where
        # it always did, whatever the size or the text
        rect.h -= int(rect.h * HOWTO_ART_H) + 16
    from . import inforef
    box = infoprose.ProseBox(key, rect, body or "",
                             int(base * infoprose.SIZE_UP), NORMAL, base,
                             struct, inforef.picture, given)
    box.draw(surface, screen)
    return box.text_end


def _guide_art():
    from . import inforef
    return inforef.art("guide")


def button(surface, screen, native, words, active=False):
    r = R(screen, native)
    hud.small_button(surface, r, screen.layout.scale,
                     "active" if active else "normal")
    # Capitals (work order 225): a control's word, as every button's.
    # HD EXTENSION `font_scale` (WO 356): above 1.0 a long word keeps a
    # 10 px margin a side instead of filling the button (core.textfit).
    label = (words or "").upper()
    size = textfit.fit_width_size(screen.style, label, px(screen, "cost"),
                                  r.w - 20)
    infobox.line(surface, screen, label, r.inflate(-6, 0), size,
                 hudtext.colour("button"), "center")


def player_colour(player):
    """A player's colour in the galaxy map's owner colours (the skin's),
    by the record's `color` — the HUD's stand-in for `_hist_graph_palettes`
    (DEVIATION `chart_colours`)."""
    from core import palette
    c = int(player.color) if 0 <= int(player.color) < 8 else 0
    return tuple(palette.col("galaxy_map", f"owner_{c}", HIGH))[:3]


def draw_graph(surface, screen, graph, order, stardate):
    """The axes (x 237..588 at y 390, y 140..396 at x 237), the y maximum at
    (246, 138), the eight labels at y 400 from x 239 stepping 50, and each
    player's curve from x 238, stepping `step`, y = 390 - value, with the
    original's one-pixel shadow (info.cpp:1330-1346, :1565-1643)."""
    layout = screen.layout
    axis = hudtext.colour("button")
    P = lambda x, y: nd.point(layout, x, y)
    w = max(1, int(nd.native_scale(layout)))
    pygame.draw.line(surface, axis, P(232, 390), P(588, 390), w)
    pygame.draw.line(surface, axis, P(237, 140), P(237, 396), w)
    language = lang.engine_language_number()
    for k, label in enumerate(pages.x_labels(stardate, language)):
        x = 239 + 50 * k
        infobox.line(surface, screen, label, R(screen, (x - 24, 396, x + 24,
                                                        408)),
                     px(screen, "cost"), NORMAL, "center")
    if graph is None:
        return
    scale, step, curves = graph
    infobox.line(surface, screen, str(scale), R(screen, (240, 132, 300, 144)),
                 px(screen, "cost"), NORMAL)
    # THE SHADOW IS THE BACKGROUND'S OWN DARK TONE — work order 196 G. The
    # original's shadow is palette 0xB1 one pixel down-right
    # (info.cpp:1339-1340), measured on its frame as (8, 28, 8): exactly the
    # darker of the graph's two interlaced rows, so it only darkens the
    # lighter rows and never reads as a line. HD drew it in (40, 40, 48),
    # BRIGHTER than its black panel, and every curve got a grey twin —
    # Data's "drawn twice". So it takes the graph box's own tone, sampled
    # before any curve is drawn.
    shade = surface.get_at(P(560, 150))[:3]
    for p in reversed(order):
        pts = curves.get(p) or []
        if len(pts) < 2:
            continue
        colour = player_colour(screen._players[p])
        line = [P(0xEE + step * t, 390 - v) for t, v in enumerate(pts)]
        pygame.draw.lines(surface, shade, False,
                          [(x + w, y + w) for x, y in line], w)
        pygame.draw.lines(surface, colour, False, line, w)
