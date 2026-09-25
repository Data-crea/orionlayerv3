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

#: SATURATION and BRIGHTNESS — work order 171. The hue alone reaches
#: only saturated colours; Data wants grey, silver and black too. Two
#: factors on the same rule: S multiplies the accent's saturation (0 =
#: a neutral grey of the same luminance, 1 = the measured saturation;
#: nothing above, the measured blue is already fully saturated in most
#: values), B multiplies its relative luminance. The ranges are ours
#: (decision 53): B from 0.1 (black) to 1.6 (silver), chosen so that the
#: named settings below are reachable and every word stays readable —
#: a smoke check sweeps the whole range.
SAT_RANGE = (0.0, 1.0)
BRIGHT_RANGE = (0.1, 1.6)

#: The neutral settings the order names, as (hue, saturation,
#: brightness). A smoke check proves each is reachable from the
#: controls and holds the edge floors there.
NAMED = {"silver": (None, 0.0, 1.4), "grey": (None, 0.0, 0.8),
         "dark_grey": (None, 0.0, 0.4), "black": (None, 0.0, 0.1)}

#: THE EDGE FLOORS — the minimum edge brightness the order asks for,
#: named. A colour is sorted by its MEASURED relative luminance: under
#: EDGE_CLASS it is a fill, from EDGE_CLASS an edge, from LIT_CLASS a lit
#: edge (the TURN edge, the panel's bright rim, the underline). While B
#: darkens (B < 1), an edge never falls below EDGE_FLOOR and a lit edge
#: never below LIT_FLOOR; a fill may go to black.
#:
#: EDGE_FLOOR 0.15 — MEASURED, not derived: the smallest floor at which
#: every edge stays at 3:1 against every fill, or at least as visible as
#: in the measured blue, over the whole brightness range at every
#: saturation (0.11 failed at 29 settings, 0.13 at 4; the smoke check
#: sweeps it). 3:1 is WCAG 2.1's non-text contrast (SC 1.4.11).
#: LIT_FLOOR 0.36: a hover, active or TURN edge stays at least 2:1 above
#: a normal edge at its floor, (0.36 + 0.05) / (0.15 + 0.05) = 2.05 —
#: which is what keeps the states visible on a black frame.
EDGE_CLASS, LIT_CLASS = 0.05, 0.30
EDGE_FLOOR, LIT_FLOOR = 0.15, 0.36

_hue = None
_sat = None
_bright = None


def hue():
    """The hue setting: None (the measured blue) or degrees."""
    return _hue


def sat():
    return 1.0 if _sat is None else _sat


def bright():
    return 1.0 if _bright is None else _bright


def is_default():
    return _hue is None and _sat is None and _bright is None


def delta():
    return 0.0 if _hue is None else (float(_hue) - REFERENCE)


def set_tone(hue_value=None, sat_value=None, bright_value=None):
    """Set all three (None = measured). True if anything changed."""
    global _hue, _sat, _bright
    h = None if hue_value is None else float(hue_value) % 360.0
    if h is not None and abs(h - REFERENCE) < 0.5:
        h = None
    s = None if sat_value is None else min(max(float(sat_value),
                                               SAT_RANGE[0]), SAT_RANGE[1])
    if s is not None and abs(s - 1.0) < 0.005:
        s = None
    b = None if bright_value is None else min(max(float(bright_value),
                                                  BRIGHT_RANGE[0]),
                                              BRIGHT_RANGE[1])
    if b is not None and abs(b - 1.0) < 0.005:
        b = None
    if (h, s, b) == (_hue, _sat, _bright):
        return False
    _hue, _sat, _bright = h, s, b
    return True


def set_hue(value):
    """The hue alone, the other two kept (170's API)."""
    return set_tone(value, _sat, _bright)


def in_band(h_degrees):
    return BAND[0] <= h_degrees <= BAND[1]


def _lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _srgb(x):
    return np.where(x <= 0.0031308, x * 12.92,
                    1.055 * np.power(np.clip(x, 0, None), 1 / 2.4) - 0.055)


_W = np.array([0.2126, 0.7152, 0.0722])


def luminance(rgb):
    """Relative luminance (WCAG) of RGB values 0..255, any shape (...,3)."""
    return (_lin(np.asarray(rgb, np.float64)[..., :3] / 255.0) * _W).sum(-1)


def _hls(x):
    mx, mn = x.max(axis=-1), x.min(axis=-1)
    l = (mx + mn) / 2.0
    c = mx - mn
    s = np.where(c == 0, 0.0,
                 c / np.where(l <= 0.5, mx + mn, 2.0 - mx - mn + 1e-12))
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    safe = np.where(c == 0, 1.0, c)
    h = np.where(mx == r, ((g - b) / safe) % 6.0,
                 np.where(mx == g, (b - r) / safe + 2.0, (r - g) / safe + 4.0))
    return np.where(c == 0, 0.0, h * 60.0), l, s


def _rgb(h, l, s):
    cc = (1.0 - np.abs(2.0 * l - 1.0)) * s
    hp = (h % 360.0) / 60.0
    xx = cc * (1.0 - np.abs(hp % 2.0 - 1.0))
    z = np.zeros_like(cc)
    idx = np.floor(hp).astype(int) % 6
    rr = np.choose(idx, [cc, xx, z, z, xx, cc])
    gg = np.choose(idx, [xx, cc, cc, xx, z, z])
    bb = np.choose(idx, [z, z, xx, cc, cc, xx])
    m = l - cc / 2.0
    return np.stack([rr + m, gg + m, bb + m], axis=-1)


def transform_array(rgb, d, s_factor, b_factor, word=False, floors=True):
    """THE RULE, over any (..., 3) uint8 array — every colour and every
    pixel the frame colour turns goes through this one function, so code
    and cut pieces cannot disagree.

    In the accent band (and saturated at all): the hue turns by `d`, the
    saturation is multiplied by `s_factor`, and the result is scaled in
    linear light to a TARGET relative luminance — for a WORD its own
    measured luminance (labels follow the colour, never the brightness,
    so their contrast cannot fall), for everything else the measured
    luminance times `b_factor` (a fill only ever darkens), held above
    the edge floors while `b_factor` darkens. Outside the band nothing
    changes."""
    rgb = np.asarray(rgb, np.uint8)
    if d == 0 and s_factor == 1.0 and b_factor == 1.0:
        return rgb.copy()
    x = rgb.astype(np.float64) / 255.0
    h, l, s = _hls(x)
    turn = (s >= 0.08) & (h >= BAND[0]) & (h <= BAND[1])
    moved = _rgb(h + d, l, np.clip(s * s_factor, 0.0, 1.0))
    l0 = (_lin(x) * _W).sum(-1)
    if word:
        target = l0
    else:
        # A FILL never brightens: above 1 the factor lifts the lines
        # (silver) and leaves the fills as dark as measured — brighter
        # fills only took contrast from the edges and words on them.
        # AN EDGE DARKENS MORE SLOWLY THAN A FILL (square root of the
        # factor): darkened by the same factor, edge and fill lost
        # contrast together — measured, the grey setting put a separator
        # at 2.8:1 on the selected row, against 3.1:1 in the blue.
        target = np.where(l0 < EDGE_CLASS, l0 * min(b_factor, 1.0),
                          l0 * (b_factor if b_factor >= 1.0
                                else np.sqrt(b_factor)))
        if b_factor < 1.0 and floors:
            floor = np.where(l0 >= LIT_CLASS, LIT_FLOOR,
                             np.where(l0 >= EDGE_CLASS, EDGE_FLOOR, 0.0))
            target = np.maximum(target, floor)
    lm = _lin(moved)
    la = (lm * _W).sum(-1)
    k = np.where(la > 1e-9, target / np.where(la > 1e-9, la, 1.0), 1.0)
    out = _srgb(np.clip(lm * k[..., None], 0.0, 1.0))
    out = np.clip(np.round(out * 255.0), 0, 255).astype(np.uint8)
    return np.where(turn[..., None], out, rgb)


def transform(rgb, word=False, d=None, s_factor=None, b_factor=None,
              floors=True):
    """One RGB triple through the rule, with the current setting unless
    given; a tuple of ints. `floors=False` only for the settings row's
    PREVIEW of the brightness bar, which shows the factor itself."""
    d = delta() if d is None else d
    s_factor = sat() if s_factor is None else s_factor
    b_factor = bright() if b_factor is None else b_factor
    arr = np.array([[list(rgb[:3])]], np.uint8)
    return tuple(int(v) for v in transform_array(arr, d, s_factor,
                                                 b_factor, word,
                                                 floors)[0, 0])


def rotate(rgb, d=None):
    """The hue alone, by `d` degrees (170's API: the slider's own bar)."""
    return transform(rgb, d=delta() if d is None else d, s_factor=1.0,
                     b_factor=1.0)


def rotate_pixels(rgb, d=None):
    """An (H, W, 3) uint8 image through the rule, current setting unless
    `d` is given (then the hue alone); a new array."""
    if d is not None:
        return transform_array(rgb, d, 1.0, 1.0)
    return transform_array(rgb, delta(), sat(), bright())
