"""The box fill rows of Game Settings — HD EXTENSION, decision 94 (work order 227).

Two of Data's decisions of 9 October 2026 in the dialog where the frame
colour and the glass already live (`gmorion`):

- **The glass switch**, on the Panel glass row: a small button at the
  value column, "On" / "Off". Off fills every box opaque with the fill
  colour; on is the glass of work order 174 with its strength bar — and
  the bar takes a click only while the switch is on (drawn dimmed, its
  value kept, while it is off).
- **The fill colour**, two rows of THE FRAME COLOUR'S KIND OF CONTROL — a
  hue bar with RESET, and a tone row with two bars (saturation, then
  brightness), `gmorion.bar_value` / `bar_x` for click and thumb — so the
  project has one colour control. Its colour model is `core.hud.fill`'s:
  hue and saturation free, the brightness bar the fill's luminance from
  black to `fill.y_max()` (the range limit that keeps every word
  readable). The brightness bar shows the real fills; the hue and
  saturation bars show their colour at a visible level, as the frame
  colour's hue bar shows an edge, not a fill.

Nothing here is sent; values live in `user_settings.json` (`hud_glass_on`,
`hud_fill`), apply at once and are written with the rest (`gmorion.save`).
"""
import colorsys

import pygame

from core.hud import blocks as hud
from core.hud import fill
from core.hud import glass

#: The luminance the hue and saturation bars show their colours at — a
#: display level, not a fill (the fills are near black and would hide the
#: hue); the brightness bar shows the fills themselves.
SHOW_Y = 0.18

#: The switch's share of the row, from the value column.
SWITCH_W = 0.12


def _settings(screen):
    return getattr(screen.app, "user_settings", None)


def geometry(out, rule):
    """Add the switch and the fill bars to `gmorion.bands`' dict, in the
    frame colour's columns (decision 5: one place for draw and click)."""
    hb, rr = out["hue_bar"], out["hue_reset"]
    gl = out["glass"]
    sw = max(8, int(gl.w * SWITCH_W))
    gap = max(4, int(hb.w * 0.04))
    out["glass_switch"] = pygame.Rect(hb.x, gl.y + gl.h // 8, sw,
                                      gl.h - gl.h // 4)
    out["glass_bar"] = pygame.Rect(hb.x + sw + gap, out["glass_bar"].y,
                                   hb.w - sw - gap, hb.h)
    fr = out["fill"]
    out["fill_bar"] = pygame.Rect(hb.x, fr.y + (fr.h - hb.h) // 2, hb.w,
                                  hb.h)
    out["fill_reset"] = pygame.Rect(rr.x, fr.y, rr.w, fr.h)
    to = out["fill_tone"]
    sat, bright = out["sat_bar"], out["bright_bar"]
    ty = to.y + (to.h - hb.h) // 2
    out["fill_sat_bar"] = pygame.Rect(sat.x, ty, sat.w, sat.h)
    out["fill_lum_bar"] = pygame.Rect(bright.x, ty, bright.w, bright.h)


def controls(screen):
    """(hue, saturation, luminance) the bars stand at. Kept on the screen
    while the dialog is up, so a grey or a black does not lose its hue."""
    now = fill.colour()
    kept = getattr(screen, "_fill_controls", None)
    if kept is None or kept[0] != now:
        h, s, y = fill.to_controls(now)
        kept = (now, (h, s, min(y, fill.y_max())))
        screen._fill_controls = kept
    return kept[1]


def set_colour(screen, rgb, controls_now=None):
    """Store the fill colour and apply it at once; None is the default."""
    fill.set_colour(rgb)
    settings = _settings(screen)
    if settings is not None:
        settings.set("hud_fill", None if fill.is_default()
                     else list(fill.colour()))
    screen._fill_controls = (None if controls_now is None
                             else (fill.colour(), controls_now))


def set_glass(screen, on):
    """The switch: stored as the PLAYER'S value (None for the default)."""
    fill.set_glass(on)
    settings = _settings(screen)
    if settings is not None:
        settings.set("hud_glass_on", None if fill._glass_on is None
                     else bool(fill._glass_on))


def handle_click(screen, geo, x, y):
    """True if (x, y) hit one of these controls (which then acted)."""
    from . import gmorion
    if geo["glass_switch"].collidepoint(x, y):
        set_glass(screen, not fill.glass_on())
        return True
    if geo["glass"].collidepoint(x, y) and not fill.glass_on():
        return True          # the strength bar and its RESET wait for the switch
    if geo["fill_reset"].collidepoint(x, y):
        set_colour(screen, None)
        return True
    h, s, lum = controls(screen)
    for key, row in (("fill_bar", "fill"), ("fill_sat_bar", "fill_tone"),
                     ("fill_lum_bar", "fill_tone")):
        bar = geo[key]
        if bar.inflate(0, geo[row].h - bar.h).collidepoint(x, y) and \
                bar.left <= x <= bar.right:
            if key == "fill_bar":
                h = gmorion.bar_value(bar, x, 0.0, 1.0)
            elif key == "fill_sat_bar":
                s = gmorion.bar_value(bar, x, 0.0, 1.0)
            else:
                lum = gmorion.bar_value(bar, x, 0.0, fill.y_max())
            set_colour(screen, fill.from_controls(h, s, lum), (h, s, lum))
            return True
    return geo["fill"].collidepoint(x, y) or \
        geo["fill_tone"].collidepoint(x, y)


def _show(h, s):
    rgb = tuple(int(round(v * 255)) for v in colorsys.hsv_to_rgb(h, s, 1.0))
    return fill.at_luminance(rgb, SHOW_Y)


def _bar(screen, surface, bar, colour_at, value, lo, hi, dim=False):
    from . import gmorion
    for i in range(bar.w):
        c = colour_at(gmorion.bar_value(bar, bar.x + i, lo, hi))
        if dim:
            c = tuple(int(v * 0.45) for v in c)
        pygame.draw.line(surface, c, (bar.x + i, bar.y),
                         (bar.x + i, bar.bottom - 1))
    screen.style.draw_plate(surface, bar, screen.layout.scale)
    w = max(2, int(3 * screen.layout.scale))
    tx = gmorion.bar_x(bar, value, lo, hi)
    # LOOK EXCEPTION marking: the slider's position tick
    surface.fill((128, 128, 128) if dim else (255, 255, 255),
                 (tx - w // 2, bar.y - w, w, bar.h + 2 * w))


def render_switch(screen, surface, geo, words, size):
    """The glass switch, a small button that is 'on' while the glass is."""
    from . import gmorion
    rect = geo["glass_switch"]
    on = fill.glass_on()
    hud.small_button(surface, rect, screen.layout.scale,
                     "active" if on else "normal")
    word = words.get("glass_steps", {}).get("on" if on else "off",
                                            "On" if on else "Off")
    img = screen.style.render_text(word, size, tuple(gmorion.COL_OPTION[:3]))
    while img.get_width() > rect.w * 0.9 and size > 8:
        size -= 1
        img = screen.style.render_text(word, size,
                                       tuple(gmorion.COL_OPTION[:3]))
    surface.blit(img, (rect.x + (rect.w - img.get_width()) // 2,
                       rect.y + (rect.h - img.get_height()) // 2))


def glass_dim():
    """True while the strength bar waits for the switch."""
    return not fill.glass_on()


def render(screen, surface, geo, words, size, lx):
    """The two fill rows: label, hue bar and RESET; label, saturation and
    brightness bars."""
    from . import gmorion
    h, s, lum = controls(screen)
    gmorion._text(screen, surface, words.get("fill", "Box fill"), size,
                  gmorion.COL_OPTION, lx, geo["fill"])
    _bar(screen, surface, geo["fill_bar"], lambda v: _show(v, 1.0), h,
         0.0, 1.0)
    reset = geo["fill_reset"]
    gmorion._text(screen, surface, words.get("reset", "Reset"), size,
                  gmorion.COL_OPTION if fill.is_default()
                  else gmorion.COL_STATE, reset.x, reset,
                  gmorion._reset_room(screen, reset))
    gmorion._text(screen, surface, words.get("fill_tone", "Box fill tone"),
                  size, gmorion.COL_OPTION, lx, geo["fill_tone"])
    _bar(screen, surface, geo["fill_sat_bar"], lambda v: _show(h, v), s,
         0.0, 1.0)
    _bar(screen, surface, geo["fill_lum_bar"],
         lambda v: fill.from_controls(h, s, v), lum, 0.0, fill.y_max())


def render_glass_bar(screen, surface, bar):
    """The strength bar of `gmorion`'s glass row, dimmed while the switch
    is off (it keeps its value)."""
    sample = (90, 120, 170)
    dim = glass_dim()

    def at(v):
        alpha, col = glass.profile(2, glass.transparency(v=v))
        a = float(alpha[0])
        return tuple(int(sample[k] * (1 - a) + col[0][k] * a)
                     for k in range(3))
    _bar(screen, surface, bar, at, glass.value(), 0.0, 1.0, dim=dim)
