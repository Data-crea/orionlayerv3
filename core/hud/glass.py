"""The panel GLASS — work order 174 B2, and its slider (B3, HD EXTENSION).

**WHAT IT IS.** Every filled HUD panel shows the background behind it,
dimmed, under a vertical gradient, instead of a flat near-black fill:
Data's Select Race mockup (`references/doc/briefs/174-mockup-select-race.png`,
measured by `dev:tools/hud_glass.py` into `measured.glass`). One place makes
it, for every panel and popup — `blocks.panel` asks `fill()` here — so no
screen draws its own.

**THE PARTS.**
- WHAT SHOWS THROUGH IS WHAT IS DRAWN UNDER THE BOX (work order 253,
  Data's way (b) of 252 P1): the map's stars and ships through the GAME
  menu, the battle field through the battle's panels, an earlier panel
  through a later one. Until then the glass showed only the screen's
  background picture (`backgrounds.current`, work order 174: "a popup
  stays opaque over its screen") — near black on every screen, so the
  glass read as none. A box is a translucent layer (`profile`: per row
  the gradient's colour and its opacity) laid over the surface; the
  layer depends only on the box's size and the transparency used, so
  it is built once and blitted each frame.
- The gradient's two colours are style values, so they follow the frame
  colour through the tint rule (navy under blue, dark violet under
  violet, anthracite under grey and silver, near-black under black);
  the background itself is never tinted (172's component rule).
- Its opacity is the mockup's, top to bottom, moved by the slider:
  `alpha = 1 - (1 - measured) * T`, `T = (1 - v) / (1 - v0)` — `v0` the
  measured position (0.5), `v = 0` doubles the transparency, `v = 1` is
  solid. The DENSE variant lets through `dense_transparency` of that, so
  it moves with the slider and stays denser.
- **THE FLOOR** (170/171: every HUD word >= 4.5:1). Per panel, the
  brightest background row under it decides: if at the slider's position
  the dimmest HUD word would fall under the floor over the glass there,
  THAT panel is made denser until it does not — never the words dimmer.
  Every such clamp is recorded (`clamps`), so it can be said where and
  at which value.

Built once per box size, tint and transparency used (the blocks'
cache); per frame only the floor is decided, on a third-size copy of
what lies under the box (`ground`, `t_for`), and the layer blitted.
"""
import numpy as np

from core.hud import style as hudstyle

#: The slider's value, 0..1; None = the default (`chosen.glass.slider_default`,
#: which a mod's partial style.json may set).
_value = None

#: (rect, dense, T wanted, T used) of every panel the floor made denser,
#: since the last `clear_clamps`.
clamps = []

#: HUD words the floor protects — 006b's list: every text colour but the
#: red negative, and the table's two.
WORDS = ("text.title.color", "text.label.color", "text.value.color",
         "text.sub.color", "text.button.color", "text.action.color",
         "mockup_colony.text_header", "mockup_colony.text_row")


def default():
    return float(hudstyle.get().get("glass.slider_default"))


def value():
    return default() if _value is None else _value


def set_value(v):
    """The slider (None = the default). Applies at once. True if anything
    changed. Nothing cached is dropped (work order 253): every glass box
    is cached under the transparency it uses (`t_for`), so the next frame
    simply asks for other keys — dropping every shape and piece made each
    step of the slider cost a tenth of a second."""
    global _value
    v = None if v is None else min(1.0, max(0.0, float(v)))
    if v is not None and abs(v - default()) < 0.005:
        v = None
    if v == _value:
        return False
    _value = v
    return True


def transparency(dense=False, v=None):
    """The share of the MEASURED transparency let through (1 = the
    mockup's)."""
    st = hudstyle.get()
    v = value() if v is None else v
    v0 = default()
    t = max(0.0, (1.0 - v) / max(1e-6, 1.0 - v0))
    if dense:
        t *= float(st.get("glass.dense_transparency"))
    return t


def _lin(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lum(rgb):
    """WCAG relative luminance of (..., 3) values 0..255."""
    x = _lin(rgb)
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


#: The WCAG luminance weights.
_LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
#: (style object, tint, floor) of the last `word_floor_lum`.
_FLOOR = [None, None, None]


def word_floor_lum():
    """The brightest a glass pixel may be: the dimmest HUD word at the
    current tint, at the floor contrast. Kept per style and tint (asked
    for every box of every frame since work order 253)."""
    from core.hud import tint
    st = hudstyle.get()
    key = (tint._hue, tint._sat, tint._bright)
    if _FLOOR[0] is st and _FLOOR[1] == key:
        return _FLOOR[2]
    _FLOOR[:] = [st, key, _word_floor(st)]
    return _FLOOR[2]


def _word_floor(st):
    tmin = min(float(lum(np.array(st.colour(w), float))) for w in WORDS)
    return (tmin + 0.05) / float(st.get("glass.floor_contrast")) - 0.05


def profile(h, t):
    """Per row: (alpha (h,), colour (h, 3)) for transparency share t."""
    st = hudstyle.get()
    y = np.linspace(0.0, 1.0, max(1, h))[:, None]
    a_meas = (float(st.get("glass.alpha_top")) * (1 - y[:, 0])
              + float(st.get("glass.alpha_bottom")) * y[:, 0])
    top = np.array(st.colour("glass.top"), np.float32)
    bot = np.array(st.colour("glass.bottom"), np.float32)
    col = top * (1 - y) + bot * y
    alpha = np.clip(1.0 - (1.0 - a_meas) * t, 0.0, 1.0)
    return alpha.astype(np.float32), col.astype(np.float32)


def _ok(bright, t, h, limit):
    alpha, col = profile(h, t)
    comp = bright * (1 - alpha[:, None]) + col * alpha[:, None]
    return bool((lum(comp) <= limit).all())


def _box3(a):
    """A 3x3 box average of an (h, w, ...) array, edges repeated."""
    p = np.pad(a, [(1, 1), (1, 1)] + [(0, 0)] * (a.ndim - 2), mode="edge")
    h, w = a.shape[:2]
    return sum(p[dy:dy + h, dx:dx + w] for dy in range(3)
               for dx in range(3)) / 9.0


def peak_pixels(img, soft=False):
    """Per row, the colour at the row's 99th percentile of luminance,
    both taken on the 3x3 average — the ONE statistic the floor is
    decided and checked by. `soft`: `img` is averaged already (`ground`'s
    third-size copy, each pixel the mean of a 3x3 block)."""
    soft = (np.asarray(img, np.float32) if soft
            else _box3(np.asarray(img, np.float32)))
    # ranked by the luminance's own order: linearising is monotone per
    # channel, and the ranking weights are the luminance's
    ls = _lin(soft) @ _LUMA
    k = int(np.ceil(0.99 * (ls.shape[1] - 1)))
    idx = np.argpartition(ls, k, axis=1)[:, k]
    return soft[np.arange(ls.shape[0]), idx].astype(np.float32)


def peak_lum(img):
    """The brightest a row of `img` reads, by `peak_pixels`: max over rows."""
    return float(lum(peak_pixels(img)).max())


def fill(bg, w, h, dense=False, rect=None):
    """The glass for a w x h panel as float RGB (h, w, 3). `bg` is the
    background under it (same shape, float), or None: then the glass is
    the gradient over black.

    WITH THE GLASS SWITCHED OFF (work order 227, decision 94) it is the
    fill colour, opaque and flat — the panel member, or the dense one —
    and `bg` is not read: the box does not depend on the background."""
    from core.hud import fill as boxfill
    if not boxfill.glass_on():
        c = boxfill.member("dense" if dense else "panel")
        return np.broadcast_to(np.array(c, np.float32), (h, w, 3)).copy()
    t = transparency(dense)
    if bg is None:
        bg = np.zeros((h, w, 3), np.float32)
    # The floor, per panel: the brightest background of each row must
    # stay dark enough under the glass for the dimmest HUD word. "The
    # brightest" is `peak_pixels`: a 3x3 average, then the 99th
    # percentile of the row — a point star smaller than a glyph's stroke
    # does not decide; a cloud does.
    limit = word_floor_lum()
    bright = peak_pixels(bg)
    used = t
    if not _ok(bright, t, h, limit):
        lo, hi = 0.0, t
        for _ in range(14):
            mid = (lo + hi) / 2
            if _ok(bright, mid, h, limit):
                lo = mid
            else:
                hi = mid
        used = lo
        clamps.append((tuple(rect) if rect is not None else None, dense,
                       round(t, 3), round(used, 3)))
        del clamps[:-500]
    alpha, col = profile(h, used)
    a = alpha[:, None, None]
    return bg * (1 - a) + col[:, None, :] * a


#: The floor is decided on a copy of the ground this many REFERENCE px
#: smaller (a 3x3 block's mean per pixel at 1920x1080, 6x6 at 3840x2160:
#: `peak_pixels`' own average, `soft`, the same statistic at every size).
GROUND_STEP = 3
#: The transparency used is rounded DOWN to a multiple of 1/QUANT, so the
#: layer is rebuilt only when the floor moves by a step, never denser
#: than the floor allows less.
QUANT = 128


def ground(surface, rect):
    """What is drawn under `rect` on `surface`, at a third of its size,
    float (h, w, 3) — the floor's input; None where nothing is."""
    import pygame
    rect = pygame.Rect(rect)
    clip = rect.clip(surface.get_rect())
    if clip.w < 1 or clip.h < 1:
        return None
    sub = surface.subsurface(clip)
    step = max(GROUND_STEP, round(GROUND_STEP * surface.get_height() / 1080))
    size = (max(1, clip.w // step), max(1, clip.h // step))
    try:
        small = pygame.transform.smoothscale(sub, size)
    except ValueError:          # an 8-bit surface: no smoothscale
        small = pygame.transform.scale(sub.convert(24), size)
    view = pygame.surfarray.pixels3d(small)
    out = np.asarray(view, np.float32).transpose(1, 0, 2)
    del view
    return out


def t_for(surface, rect, dense=False):
    """The transparency share a box over `rect` may use over what is
    drawn there: the slider's, made smaller where the floor needs it (the
    module docstring), rounded down to a step. Recorded in `clamps`."""
    t = transparency(dense)
    under = ground(surface, rect)
    if under is None or t <= 0.0:
        return round(np.floor(t * QUANT) / QUANT, 6)
    limit = word_floor_lum()
    h = under.shape[0]
    # THE QUICK WAY OUT: a grey as bright as the ground's brightest
    # channel is at least as bright as any of its pixels; if that passes
    # on every row, every row's peak does (most grounds are dark)
    top = np.full(3, float(under.max()), np.float32)
    if _ok(np.broadcast_to(top, (h, 3)), t, h, limit):
        return round(np.floor(t * QUANT) / QUANT, 6)
    bright = peak_pixels(under, soft=True)
    used = t
    if not _ok(bright, t, h, limit):
        lo, hi = 0.0, t
        for _ in range(10):
            mid = (lo + hi) / 2
            if _ok(bright, mid, h, limit):
                lo = mid
            else:
                hi = mid
        used = lo
        clamps.append((tuple(rect), dense, round(t, 3), round(used, 3)))
        del clamps[:-500]
    return round(np.floor(used * QUANT) / QUANT, 6)


def clear_clamps():
    del clamps[:]


# ── the edgeless glass: every fill that is not a panel ───────────────

_DRAWN = {}
_DRAWN_MAX = 600


#: The ground under each glass panel drawn so far, by surface: (rect,
#: copy). A glass fill INSIDE a panel (a table row, a field) blends with
#: what lay under the panel, not with the panel's own glass — two glass
#: layers over each other were nearly opaque (work order 253). Each panel
#: replaces its entry when it is drawn, so the fills of a frame see the
#: ground of the same frame.
_GROUNDS = {}


def keep_ground(surface, rect):
    """Called by `blocks.panel` before it draws a glass panel."""
    import pygame
    rect = pygame.Rect(rect).clip(surface.get_rect())
    if rect.w < 1 or rect.h < 1:
        return
    lst = _GROUNDS.setdefault(id(surface), [])
    lst[:] = [g for g in lst if g[0] != rect and not rect.contains(g[0])]
    lst.append((rect, surface.subsurface(rect).copy()))
    del lst[:-64]


def _panel_ground(surface, rect):
    """The kept ground of the innermost panel containing `rect`, cut to
    it, or None."""
    for r, pic in reversed(_GROUNDS.get(id(surface), ())):
        if r.contains(rect) and pic.get_size() == r.size:
            return pic.subsurface(rect.move(-r.x, -r.y))
    return None


def draw(surface, rect, dense=False, shade=None, shade_alpha=0.0):
    """Glass over `rect` without a panel's edge — the ONE fill for what a
    screen used to fill flat and near-black itself: table rows and their
    headers, a grid's cells, a text field, a colony popup's body (work
    order 174 B2). `shade`, at `shade_alpha`, lays a colour over the
    glass: a table's A/B stripe or its selected row stays told apart,
    and what is drawn under it still shows through (work order 253: a
    translucent layer over the surface, the same arithmetic as before)."""
    import pygame
    rect = pygame.Rect(rect)
    if rect.w < 1 or rect.h < 1:
        return
    from core.hud import fill as boxfill
    on = boxfill.glass_on()
    ground = _panel_ground(surface, rect) if on else None
    t = (t_for(ground, ground.get_rect(), dense) if ground is not None
         else t_for(surface, rect, dense)) if on else None
    key = (rect.size, dense, t, tuple(shade[:3]) if shade else None,
           round(shade_alpha, 3), _tint_key())
    surf = _DRAWN.get(key)
    if surf is None:
        if on:
            alpha, col = profile(rect.h, t)
            sa = shade_alpha if shade else 0.0
            sc = np.array(shade[:3] if shade else (0, 0, 0), np.float32)
            a = 1.0 - (1.0 - alpha) * (1.0 - sa)
            c = (col * (alpha * (1.0 - sa))[:, None] + sc * sa) / \
                np.maximum(a, 1e-6)[:, None]
            surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            view = pygame.surfarray.pixels3d(surf)
            view[...] = np.clip(np.round(c), 0, 255).astype(
                np.uint8)[None, :, :]
            del view
            pa = pygame.surfarray.pixels_alpha(surf)
            pa[...] = np.clip(np.round(a * 255.0), 0, 255).astype(
                np.uint8)[None, :]
            del pa
        else:
            px = fill(None, rect.w, rect.h, dense, rect=rect)
            if shade:
                px = px * (1 - shade_alpha) + np.array(
                    shade[:3], np.float32) * shade_alpha
            surf = pygame.Surface(rect.size)
            view = pygame.surfarray.pixels3d(surf)
            view[...] = np.clip(px, 0, 255).astype(np.uint8).transpose(
                1, 0, 2)
            del view
        if len(_DRAWN) >= _DRAWN_MAX:
            _DRAWN.pop(next(iter(_DRAWN)))
        _DRAWN[key] = surf
    under = _panel_ground(surface, rect) if on else None
    if under is not None:
        # inside a glass panel: over what lay under the panel
        base = under.copy()
        base.blit(surf, (0, 0))
        surface.blit(base, rect.topleft)
        return
    surface.blit(surf, rect.topleft)


def shade(kind):
    """The share a table's `kind` colour ("row", "selected", "header")
    is laid over the glass with — `chosen.glass.<kind>_shade`."""
    return float(hudstyle.get().get(f"glass.{kind}_shade"))


def _tint_key():
    from core.hud import fill as boxfill
    from core.hud import tint
    return (tint._hue, tint._sat, tint._bright, boxfill.glass_on(),
            boxfill.colour())


def forget():
    """Drop the drawn glass (a resize, the colour or the slider)."""
    _DRAWN.clear()
    _GROUNDS.clear()


hudstyle.on_change(forget)


def corner_lines(surface, rect, scale):
    """The mockup's inner corner lines — optional (`chosen.glass.
    corner_lines`, off; parked with renders): at each corner a thin line
    inset from the edge, following its chamfer, in the dim edge colour
    at half strength."""
    import pygame
    st = hudstyle.get()
    rect = pygame.Rect(rect)
    e, arm = 9 * scale, 60 * scale
    ch = min(float(st.get("panel.chamfer")) * scale, min(rect.w, rect.h) / 4)
    if rect.w < 4 * arm or rect.h < 3 * arm:
        return
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    col = tuple(st.colour("panel.edge_dim")) + (128,)
    w, h = rect.w - 1, rect.h - 1
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        x0 = e if sx > 0 else w - e
        y0 = e if sy > 0 else h - e
        pts = [(x0 + sx * arm, y0), (x0 + sx * ch, y0), (x0, y0 + sy * ch),
               (x0, y0 + sy * arm)]
        pygame.draw.aalines(layer, col, False, pts)
    surface.blit(layer, rect.topleft)
