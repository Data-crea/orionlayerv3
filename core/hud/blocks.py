"""The HUD's building blocks — the ONE place each is drawn (decision 71).

Every block takes the device rect it fills and the layout's `scale`
(device px per reference px), reads its colours and widths from
`assets/shared/hud/style.json` and draws itself at the device size,
cached per size and state. No screen draws its own variant: a screen
that needs a panel calls `panel`, and two screens therefore cannot wear
two panels.

The blocks, and what each is measured from (style.json says exactly):

    panel          the HUD's right info panel
    separator      the lines between that panel's rows
    slant_button   the nav row's six buttons (four states)
    action_button  the TURN button
    small_button   the action button's shape, small, for inside panels
    title_plate    a piece CUT from the HUD (`core.hud.art`) + its text
    table_header / table_row / scrollbar   Data's colony mockup
    popup          a panel lit like the action button, opaque

States: "normal", "hover", "active", "disabled". Only "normal" is in
Data's material; the other three are `chosen.button`, named there.
"""
from collections import OrderedDict

import pygame

from core.hud import art
from core.hud import raster
from core.hud import style as hudstyle
from core.hud import text as hudtext

STATES = ("normal", "hover", "active", "disabled")

#: Drawn shapes, keyed on everything that changes the pixels. Bounded,
#: because a caller with a new size every frame (a resize drag) must not
#: grow it without limit; 400 covers every block of every screen at one
#: window size several times over.
_CACHE = OrderedDict()
_CACHE_MAX = 400

#: The title plate's lit inner hexagon, in `title_plate.png` px
#: (x0, y0, x1, y1): measured on the cut piece, the inside of the rim the
#: word sits in. The piece is 4780x240; the box is its middle.
TITLE_TEXT_BOX = (1737, 27, 3024, 190)


def _cached(key, build):
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    val = build()
    _CACHE[key] = val
    if len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return val


def clear():
    """Forget every drawn shape (a resize, the frame colour changing, or
    the smoke test)."""
    _CACHE.clear()
    art.clear()


hudstyle.on_change(clear)


def _px(ref_len, scale, floor=1.0):
    return max(floor, ref_len * scale)


def _blit_shape(surface, rect, built):
    surf, pad = built
    surface.blit(surf, (rect.x - pad, rect.y - pad))


def _dim(surf):
    out = surf.copy()
    a = float(hudstyle.get().get("button.disabled_alpha"))
    out.fill((255, 255, 255, int(255 * a)), special_flags=pygame.BLEND_RGBA_MULT)
    return out


# ── panel, popup, separator ──────────────────────────────────────────

def panel(surface, rect, scale, lit=False, filled=True):
    """A HUD panel. `lit` gives it the action button's edge: a popup.

    `filled=False` draws the edge, its glow and the soft inner band but
    no fill — the panel for a box whose content is ALREADY drawn when the
    border comes, which is what the `thin_border` skin always meant."""
    rect = pygame.Rect(rect)
    if rect.w < 4 or rect.h < 4:
        return
    st = hudstyle.get()
    key = ("panel", rect.w, rect.h, round(scale, 4), lit, filled)

    def build():
        ch = min(_px(st.get("panel.chamfer"), scale), min(rect.w, rect.h) / 4)
        edge = st.colour("popup.edge") if lit else st.colour("panel.edge")
        return raster.shape(
            lambda w, h: raster.chamfered(w, h, ch), rect.w, rect.h,
            fill=st.colour("panel.fill"), edge=edge,
            edge_w=_px(st.get("panel.edge_width"), scale),
            glow=st.colour("panel.glow"),
            glow_w=_px(st.get("panel.glow_width"), scale),
            inner=st.colour("panel.fill_edge"),
            inner_w=_px(st.get("panel.inner_glow"), scale),
            fill_alpha=1.0 if filled else 0.0,
            ss=int(st.get("supersample")))
    _blit_shape(surface, rect, _cached(key, build))


def outline(surface, rect, scale):
    """The thinnest block: a line round a cell or a plate INSIDE a
    panel, corners cut small. No fill, no glow — a separator that goes
    round, and what decision 51's `draw_plate` draws since decision 71.

    Its colour is the HUD's DIM edge (`panel.edge_dim`, the panel's own
    top and bottom line), not the separator's: sixty of these tile the
    colony list, and at separator brightness the grid outshone the
    figures in it. The colony figure checks rely on it staying below
    the figures' brightness, and assert that they do."""
    rect = pygame.Rect(rect)
    if rect.w < 3 or rect.h < 3:
        return
    st = hudstyle.get()
    key = ("outline", rect.w, rect.h, round(scale, 4))

    def build():
        # WHOLE PIXELS, NOT A SUPERSAMPLED SHAPE: a line one or two px
        # wide came out of the smoothscale at 98 % coverage, so no pixel
        # was ever the outline's colour — and "the plate's colour on
        # every edge of the drop rect" is how the colony list proves its
        # plate rect IS its drop rect (decision 5). The outer polygon is
        # filled with the colour and the inner one keyed out.
        w = max(1, round(max(1.0, _px(st.get("separator.width"), scale))))
        ch = min(_px(st.get("panel.chamfer"), scale) * 0.35,
                 min(rect.w, rect.h) / 4)
        key_col = (255, 0, 255)
        s = pygame.Surface(rect.size)
        s.fill(key_col)
        s.set_colorkey(key_col)
        outer = raster.chamfered(rect.w - 1, rect.h - 1, round(ch))
        pygame.draw.polygon(s, st.colour("panel.edge_dim"),
                            [(round(x), round(y)) for x, y in outer])
        inner = raster.inset(outer, w)
        pygame.draw.polygon(s, key_col,
                            [(round(x), round(y)) for x, y in inner])
        return s, 0
    _blit_shape(surface, rect, _cached(key, build))


def glow_pad(scale):
    """Device px a panel's (or popup's) outer glow reaches past its rect
    — `raster.shape`'s pad for the panel's measured glow. A caller that
    must keep EVERYTHING it draws inside a box insets the panel by this
    (the help popup does)."""
    g = _px(hudstyle.get().get("panel.glow_width"), scale)
    return int(-(-g * 2.2 // 1)) + 2


def popup(surface, rect, scale):
    """A dialog body: opaque, lit (`chosen.popup`)."""
    panel(surface, rect, scale, lit=True)


def separator(surface, x0, x1, y, scale, vertical=False):
    """One separator line from x0 to x1 at y (or y0..y1 at x)."""
    st = hudstyle.get()
    w = max(1, round(_px(st.get("separator.width"), scale)))
    col = st.colour("separator.color")
    if vertical:
        pygame.draw.rect(surface, col, (int(y) - w // 2, int(x0), w,
                                        int(x1 - x0)))
    else:
        pygame.draw.rect(surface, col, (int(x0), int(y) - w // 2,
                                        int(x1 - x0), w))


def panel_inner(rect, scale):
    """The part of a panel's rect clear of its edge and inner glow's
    brightest band — where content goes. Separators are inset by their
    measured insets from THIS rect's sides."""
    st = hudstyle.get()
    e = int(round(_px(st.get("panel.edge_width"), scale))) + 2
    return pygame.Rect(rect).inflate(-2 * e, -2 * e)


def separator_span(rect, scale):
    """(x0, x1) of a separator across panel `rect`, at the measured
    insets from the panel's two edge lines."""
    st = hudstyle.get()
    r = pygame.Rect(rect)
    return (r.x + st.get("separator.inset_left") * scale,
            r.right - st.get("separator.inset_right") * scale)


# ── buttons ──────────────────────────────────────────────────────────

def _button_colours(state):
    st = hudstyle.get()
    fill, edge = st.colour("button.fill"), st.colour("button.edge")
    if state == "hover":
        fill, edge = st.colour("button.hover_fill"), st.colour("button.hover_edge")
    elif state == "active":
        fill, edge = st.colour("button.active_fill"), st.colour("button.active_edge")
    return fill, edge


def slant_offset(rect, scale=None):
    """How far a slanted button's top is shifted right of its bottom."""
    return hudstyle.get().get("button.slant") * pygame.Rect(rect).h


def slant_hit(rect, x, y):
    """True when (x, y) is inside the parallelogram `slant_button` draws
    in `rect` — the drawing and the hit are one shape (decision 5)."""
    r = pygame.Rect(rect)
    if not r.collidepoint(x, y):
        return False
    # Pixel CENTRES, as the rasteriser covers them: a pixel is drawn
    # when its centre is inside the polygon, so it is hit on the same
    # rule — at the corners of pixels the two disagreed on 57 of them.
    cx, cy = x + 0.5, y + 0.5
    s = min(slant_offset(r), r.w / 2)
    d = s * (r.bottom - cy) / max(1, r.h)
    return r.x + d <= cx <= r.right - (s - d)


def _label(surface, style_renderer, rect, label, role, state, icon, scale):
    if icon is None and not label:
        return
    r = pygame.Rect(rect)
    # ONE LABEL COLOUR IN EVERY STATE: the state is the block's, never
    # the word's. Data's rule for the colony sort keys (12 September
    # 2026 — a dimmed PRODUCING was read as a wrong colour twice), made
    # the rule for every HUD button.
    col = hudtext.colour(role)
    ic = art.icon(icon, int(r.h * 0.6)) if icon else None
    left = r.x
    if ic is not None:
        ix = r.x + int(r.h * 0.35)
        surface.blit(ic, (ix, r.y + (r.h - ic.get_height()) // 2))
        left = ix + ic.get_width() + int(r.h * 0.12)
    if label:
        s = hudtext.render(style_renderer, label.upper(), role, r.h, col)
        hudtext.blit(surface, s, pygame.Rect(left, r.y, r.right - left, r.h))


def slant_button(surface, rect, scale, state="normal", label="",
                 icon=None, style_renderer=None, underline=True):
    """A nav button: parallelogram, dim edge, glowing underline, and its
    label (and icon, when the HUD has one) drawn in code."""
    rect = pygame.Rect(rect)
    if rect.w < 6 or rect.h < 6:
        return
    st = hudstyle.get()
    key = ("slant", rect.w, rect.h, round(scale, 4), state, underline)

    def build():
        fill, edge = _button_colours(state)
        surf, pad = raster.shape(
            lambda w, h: raster.slanted(w, h, st.get("button.slant")),
            rect.w, rect.h, fill=fill, edge=edge,
            edge_w=_px(st.get("button.edge_width"), scale),
            glow=edge, glow_w=_px(st.get("panel.glow_width"), scale) * 0.6,
            inner=st.colour("panel.fill_edge"),
            inner_w=_px(st.get("panel.inner_glow"), scale) * 0.5,
            ss=int(st.get("supersample")))
        if underline:
            _underline(surf, pad, rect.w, rect.h, scale,
                       bright=state in ("hover", "active"))
        return (_dim(surf) if state == "disabled" else surf), pad
    _blit_shape(surface, rect, _cached(key, build))
    if style_renderer is not None:
        inner = pygame.Rect(rect.x + int(slant_offset(rect)), rect.y,
                            rect.w - 2 * int(slant_offset(rect)), rect.h)
        _label(surface, style_renderer, inner, label, "button", state,
               icon, scale)


def _underline(surf, pad, w, h, scale, bright=False):
    """The glowing bar centred on the bottom edge (measured: 6 found,
    each `button.underline_width` wide and `underline_height` tall)."""
    st = hudstyle.get()
    uw = _px(st.get("button.underline_width"), scale)
    uh = max(2.0, _px(st.get("button.underline_height"), scale))
    if bright:
        uw *= 1.6
    core = st.colour("button.underline")
    glow = st.colour("action.edge")
    cx = pad + w / 2        # the box's centre, as the six measured are
    cy = pad + h
    g = pygame.Surface((int(uw * 2), int(uh * 5)), pygame.SRCALPHA)
    gw, gh = g.get_size()
    for i in range(4, 0, -1):
        a = int(40 * (5 - i))
        pygame.draw.ellipse(g, (*glow, a), (gw / 2 - uw * (0.5 + 0.12 * i),
                                            gh / 2 - uh * (0.5 + 0.45 * i),
                                            uw * (1 + 0.24 * i),
                                            uh * (1 + 0.9 * i)))
    surf.blit(g, (cx - gw / 2, cy - gh / 2))
    pygame.draw.rect(surf, core, (cx - uw / 2, cy - uh / 2, uw, uh),
                     border_radius=int(uh / 2))


def action_button(surface, rect, scale, state="normal", label="",
                  icon=None, style_renderer=None):
    """The large action button (TURN): chamfered, brightly lit edge."""
    rect = pygame.Rect(rect)
    if rect.w < 6 or rect.h < 6:
        return
    st = hudstyle.get()
    key = ("action", rect.w, rect.h, round(scale, 4), state)

    def build():
        edge = st.colour("action.edge")
        fill = st.colour("action.fill")
        if state == "hover":
            fill = st.colour("button.hover_fill")
        elif state == "active":
            fill = st.colour("button.active_fill")
        ch = min(_px(st.get("panel.chamfer"), scale), rect.h / 4)
        surf, pad = raster.shape(
            lambda w, h: raster.chamfered(w, h, ch), rect.w, rect.h,
            fill=fill, edge=edge, edge_w=_px(st.get("action.edge_width"), scale),
            glow=st.colour("action.inner"),
            glow_w=_px(st.get("panel.glow_width"), scale) * 1.6,
            inner=st.colour("action.inner"),
            inner_w=_px(st.get("panel.inner_glow"), scale),
            ss=int(st.get("supersample")))
        return (_dim(surf) if state == "disabled" else surf), pad
    _blit_shape(surface, rect, _cached(key, build))
    if style_renderer is not None:
        _label(surface, style_renderer, rect, label, "action", state,
               icon, scale)


def small_button(surface, rect, scale, state="normal", label="",
                 style_renderer=None, role="button"):
    """A button inside a panel: the action button's shape, small."""
    rect = pygame.Rect(rect)
    if rect.w < 4 or rect.h < 4:
        return
    st = hudstyle.get()
    key = ("small", rect.w, rect.h, round(scale, 4), state)

    def build():
        fill, edge = _button_colours(state)
        ch = min(_px(st.get("panel.chamfer"), scale)
                 * st.get("small_button.chamfer_frac"), rect.h / 3)
        surf, pad = raster.shape(
            lambda w, h: raster.chamfered(w, h, ch), rect.w, rect.h,
            fill=fill, edge=edge,
            edge_w=_px(st.get("button.edge_width"), scale),
            # NO OUTER GLOW: a small button sits inside a panel and draws
            # inside its own rect, nothing past it — which is what the
            # research EXIT button's check holds it to.
            inner=st.colour("panel.fill_edge"),
            inner_w=_px(st.get("panel.inner_glow"), scale) * 0.4,
            ss=int(st.get("supersample")))
        return (_dim(surf) if state == "disabled" else surf), pad
    _blit_shape(surface, rect, _cached(key, build))
    if style_renderer is not None and label:
        _label(surface, style_renderer, rect, label, role, state, None, scale)


def checkbox(surface, rect, scale, checked, hover=False):
    """A checkbox (work order 172): the small button's square and, when
    `checked`, a tick in the lit edge colour — so it follows the frame
    colour and, at the edge floors, stays visible on a black frame. Both
    states are drawn every frame; the state is never a shade alone."""
    rect = pygame.Rect(rect)
    small_button(surface, rect, scale,
                 "active" if checked else ("hover" if hover else "normal"))
    if not checked:
        return
    st = hudstyle.get()
    col = st.colour("action.edge")
    w = max(2, int(round(rect.h / 7)))
    pts = [(rect.x + rect.w * 0.24, rect.y + rect.h * 0.52),
           (rect.x + rect.w * 0.43, rect.y + rect.h * 0.72),
           (rect.x + rect.w * 0.78, rect.y + rect.h * 0.30)]
    pygame.draw.lines(surface, col, False, pts, w)
    for p in pts:
        pygame.draw.circle(surface, col, (int(p[0]), int(p[1])), w // 2)


# ── the title plate ──────────────────────────────────────────────────

def title_plate_rect(center_x, top_y, scale):
    """(plate rect, text rect) in device px: the cut piece at the HUD's
    own proportion — its width in the HUD times 1920/6704 reference px
    — centred on `center_x`, its top at `top_y`."""
    raw = art.raw(art.TITLE_PLATE)
    pw, ph = raw.get_size() if raw is not None else (4780, 240)
    k = hudstyle.get().get("source.to_ref") * scale
    w, h = pw * k, ph * k
    plate = pygame.Rect(int(center_x - w / 2), int(top_y), int(w), int(h))
    x0, y0, x1, y1 = TITLE_TEXT_BOX
    text = pygame.Rect(int(plate.x + x0 * k), int(plate.y + y0 * k),
                       int((x1 - x0) * k), int((y1 - y0) * k))
    return plate, text


def title_plate(surface, center_x, top_y, scale, text="",
                style_renderer=None, colour=None):
    """The title plate (a cut piece) and its title (drawn in code).

    Without the piece — a clone that has not run setup — the text is
    drawn on a small lit panel of the same text box, so the title is
    never lost. Returns the text rect, which is the plate's click area."""
    plate, box = title_plate_rect(center_x, top_y, scale)
    img = art.fit(art.TITLE_PLATE, plate.h, plate.w)
    if img is not None:
        surface.blit(img, plate.topleft)
    else:
        panel(surface, box, scale, lit=True)
    if text and style_renderer is not None:
        s = hudtext.render(style_renderer, text.upper(), "title", box.h,
                           colour or hudtext.colour("title"))
        hudtext.blit(surface, s, box)
    return box


# ── tables — `core/hud/tables.py`, re-exported here so every block is
# still reached as `blocks.<name>` (split for the line guideline, 172) ──

from core.hud.tables import (  # noqa: E402,F401
    scrollbar, table_header, table_row, table_text_colour)
