"""The panel GLASS — work order 174 B2, and its slider (B3, HD EXTENSION).

**WHAT IT IS.** Every filled HUD panel shows the background behind it,
dimmed, under a vertical gradient, instead of a flat near-black fill:
Data's Select Race mockup (`doc/briefs/174-mockup-select-race.png`,
measured by `tools/hud_glass.py` into `measured.glass`). One place makes
it, for every panel and popup — `blocks.panel` asks `fill()` here — so no
screen draws its own.

**THE PARTS.**
- The background is the picture `core.backgrounds` drew for this window
  (`backgrounds.current`), cropped to the panel. The glass never shows
  what a screen drew over the background (a map, a star, another
  panel): a popup stays opaque over its screen, as every dialog was.
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

Built once per panel, window size, tint, background and slider value
(the blocks' cache); nothing is blurred or blended per frame.
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
    """The slider (None = the default). Applies at once: every cached
    panel is rebuilt for it. True if anything changed."""
    global _value
    v = None if v is None else min(1.0, max(0.0, float(v)))
    if v is not None and abs(v - default()) < 0.005:
        v = None
    if v == _value:
        return False
    _value = v
    for fn in hudstyle._listeners:
        fn()
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


def word_floor_lum():
    """The brightest a glass pixel may be: the dimmest HUD word at the
    current tint, at the floor contrast."""
    st = hudstyle.get()
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


def peak_pixels(img):
    """Per row, the colour at the row's 99th percentile of luminance,
    both taken on the 3x3 average — the ONE statistic the floor is
    decided and checked by."""
    soft = _box3(np.asarray(img, np.float32))
    ls = lum(soft)
    k = int(np.ceil(0.99 * (ls.shape[1] - 1)))
    idx = np.argsort(ls, axis=1)[:, k]
    return soft[np.arange(ls.shape[0]), idx].astype(np.float32)


def peak_lum(img):
    """The brightest a row of `img` reads, by `peak_pixels`: max over rows."""
    return float(lum(peak_pixels(img)).max())


def fill(bg, w, h, dense=False, rect=None):
    """The glass for a w x h panel as float RGB (h, w, 3). `bg` is the
    background under it (same shape, float), or None: then the glass is
    the gradient over black."""
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


def clear_clamps():
    del clamps[:]


# ── the edgeless glass: every fill that is not a panel ───────────────

_DRAWN = {}
_DRAWN_MAX = 600


def draw(surface, rect, dense=False, shade=None, shade_alpha=0.0):
    """Glass over `rect` without a panel's edge — the ONE fill for what a
    screen used to fill flat and near-black itself: table rows and their
    headers, a grid's cells, a text field, a colony popup's body (work
    order 174 B2). `shade`, at `shade_alpha`, lays a colour over the
    glass: a table's A/B stripe or its selected row stays told apart,
    and the background still shows through."""
    import pygame
    from core import backgrounds
    rect = pygame.Rect(rect)
    if rect.w < 1 or rect.h < 1:
        return
    bg = backgrounds.current(*surface.get_size())
    key = (tuple(rect), dense, bg[0] if bg is not None else None,
           round(value(), 4), tuple(shade[:3]) if shade else None,
           round(shade_alpha, 3), _tint_key())
    surf = _DRAWN.get(key)
    if surf is None:
        under = None
        if bg is not None:
            under = np.zeros((rect.h, rect.w, 3), np.float32)
            clip = rect.clip(bg[1].get_rect())
            if clip.w and clip.h:
                a = pygame.surfarray.pixels3d(bg[1])
                under[clip.y - rect.y:clip.bottom - rect.y,
                      clip.x - rect.x:clip.right - rect.x] = \
                    a[clip.x:clip.right, clip.y:clip.bottom].transpose(1, 0, 2)
                del a
        px = fill(under, rect.w, rect.h, dense, rect=rect)
        if shade:
            px = px * (1 - shade_alpha) + np.array(
                shade[:3], np.float32) * shade_alpha
        surf = pygame.Surface(rect.size)
        view = pygame.surfarray.pixels3d(surf)
        view[...] = np.clip(px, 0, 255).astype(np.uint8).transpose(1, 0, 2)
        del view
        if len(_DRAWN) >= _DRAWN_MAX:
            _DRAWN.pop(next(iter(_DRAWN)))
        _DRAWN[key] = surf
    surface.blit(surf, rect.topleft)


def shade(kind):
    """The share a table's `kind` colour ("row", "selected", "header")
    is laid over the glass with — `chosen.glass.<kind>_shade`."""
    return float(hudstyle.get().get(f"glass.{kind}_shade"))


def _tint_key():
    from core.hud import tint
    return (tint._hue, tint._sat, tint._bright)


def forget():
    """Drop the drawn glass (a resize, the colour or the slider)."""
    _DRAWN.clear()


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
