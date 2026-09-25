"""The HUD's frame colour, set by the player — HD EXTENSION (work order 170).

MOO2 has one look and no such setting; this is ours, and marked as such
here, in the GAME menu's Settings dialog where the slider is
(`screens/game_menu/gmorion.py`), in the status document and in a smoke
check.

**ONE RULE FOR CODE AND ARTWORK ALIKE, so the two never disagree.** A
colour whose hue lies in the HUD's accent band is turned by the same
angle and then brought back to its own RELATIVE LUMINANCE; every other
colour is left as it is.

**Why luminance and not HLS lightness** — measured, not assumed: turning
at constant HLS lightness made the fills of hues 25-175 degrees (orange
to cyan) so much brighter that a table word fell to 3.3:1 against the
selected row, and the order's alternative was to clamp the slider to the
other half of the wheel. Keeping each colour's luminance keeps every
word's contrast exactly what it is in the measured blue, at every hue,
so the slider runs the whole circle (a smoke check sweeps it). `rotate` applies it to one RGB triple (every code-drawn block,
through `core.hud.style.HudStyle.colour`) and `rotate_pixels` to an
image (the title plate, and the frame glyphs if they follow — see
`FOLLOWS`). The title plate's orange lamps are outside the band and stay
orange, exactly as a code-drawn orange would.

**WHAT IS NEVER TURNED** — the list the order gives, and where each is
guaranteed:
- every TEXT colour (`text.*`, the table words): `HudStyle.colour` skips
  them, so no word changes colour and readability cannot move;
- the background placeholder: skipped the same way;
- star colours, player and race colours, star names, red negatives,
  MOO2's sprites and portraits: none of them is a HUD style value, so
  none of them passes through here at all;
- the info panel's picture icons (coins, food, station, freighter,
  microscope): `art` asks `FOLLOWS` and they are not in it.

**THE BAND** is 170-250 degrees: it holds every accent value
`style.json` measured (187-218 degrees, the TURN edge to the fills) with
room, and nothing else the HUD draws — the lamps are ~30, the red
negative 2, the microscope's green ~120. The REFERENCE hue is the
measured panel edge's, 196: a setting of 196 changes nothing, and so
does the default, `None`.
"""
import colorsys

import numpy as np

#: The accent band, degrees (see the module docstring).
BAND = (170.0, 250.0)

#: The measured accent's hue — `measured.panel.edge`, (13, 172, 232).
#: A smoke check re-derives it from style.json.
REFERENCE = 196

#: The cut pieces the frame colour turns. The title plate is frame; the
#: nav glyphs and the TURN triangle are frame-coloured glyphs and follow
#: by default (parked, 170 P4); the info panel's pictures never do.
FOLLOWS = {"title_plate", "icon_colonies", "icon_planets", "icon_fleets",
           "icon_leaders", "icon_races", "icon_info", "icon_turn"}

_hue = None


def hue():
    """The setting: None (the measured blue) or a hue in degrees."""
    return _hue


def delta():
    return 0.0 if _hue is None else (float(_hue) - REFERENCE)


def set_hue(value):
    """Set the frame hue (None = the measured blue). True if it changed."""
    global _hue
    value = None if value is None else float(value) % 360.0
    if value is not None and abs(value - REFERENCE) < 0.5:
        value = None
    if value == _hue:
        return False
    _hue = value
    return True


def in_band(h_degrees):
    return BAND[0] <= h_degrees <= BAND[1]


def rotate(rgb, d=None):
    """One RGB triple through the rule; a tuple of ints."""
    d = delta() if d is None else d
    r, g, b = (v / 255.0 for v in rgb[:3])
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if d == 0 or s < 0.08 or not in_band(h * 360.0):
        return tuple(int(v) for v in rgb[:3])
    h = ((h * 360.0 + d) % 360.0) / 360.0
    out = _keep_luminance(np.array([[[r, g, b]]]),
                          np.array([[colorsys.hls_to_rgb(h, l, s)]]))
    return tuple(int(v) for v in out[0, 0])


def _lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _srgb(x):
    return np.where(x <= 0.0031308, x * 12.92,
                    1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


_W = np.array([0.2126, 0.7152, 0.0722])


def _keep_luminance(before, after):
    """`after` (floats 0..1, (..., 3)) scaled in linear light to the
    relative luminance of `before`; uint8. A channel that would pass 1
    is clipped, which lowers that colour's luminance a little — never
    raises it, so contrast against light words can only grow."""
    lb = (_lin(before) * _W).sum(axis=-1, keepdims=True)
    la_lin = _lin(after)
    la = (la_lin * _W).sum(axis=-1, keepdims=True)
    k = np.where(la > 1e-9, lb / np.where(la > 1e-9, la, 1.0), 1.0)
    out = _srgb(np.clip(la_lin * k, 0.0, 1.0))
    return np.clip(np.round(out * 255.0), 0, 255).astype(np.uint8)


def rotate_pixels(rgb, d=None):
    """The same rule over an (H, W, 3) uint8 array; a new array.

    Vectorised HLS, identical to `rotate` per pixel up to rounding
    (a smoke check holds the two to within one level)."""
    d = delta() if d is None else d
    if d == 0:
        return rgb.copy()
    x = rgb.astype(np.float64) / 255.0
    mx, mn = x.max(axis=2), x.min(axis=2)
    l = (mx + mn) / 2.0
    c = mx - mn
    s = np.where(c == 0, 0.0,
                 c / np.where(l <= 0.5, mx + mn, 2.0 - mx - mn + 1e-12))
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    safe = np.where(c == 0, 1.0, c)
    h = np.where(mx == r, ((g - b) / safe) % 6.0,
                 np.where(mx == g, (b - r) / safe + 2.0, (r - g) / safe + 4.0))
    h = np.where(c == 0, 0.0, h * 60.0)
    turn = (s >= 0.08) & (h >= BAND[0]) & (h <= BAND[1])
    h2 = (h + d) % 360.0
    # HLS -> RGB for the turned pixels.
    cc = (1.0 - np.abs(2.0 * l - 1.0)) * s
    hp = h2 / 60.0
    xx = cc * (1.0 - np.abs(hp % 2.0 - 1.0))
    z = np.zeros_like(cc)
    idx = np.floor(hp).astype(int) % 6
    rr = np.choose(idx, [cc, xx, z, z, xx, cc])
    gg = np.choose(idx, [xx, cc, cc, xx, z, z])
    bb = np.choose(idx, [z, z, xx, cc, cc, xx])
    m = l - cc / 2.0
    out = _keep_luminance(x, np.stack([rr + m, gg + m, bb + m], axis=2))
    return np.where(turn[..., None], out, rgb).astype(np.uint8)
