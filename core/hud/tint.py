"""The HUD's frame colour, set by the player — HD EXTENSION (work order 170).

MOO2 has one look and no such setting; this is ours, and marked as such
here, in the GAME menu's Settings dialog where the slider is
(`screens/game_menu/gmorion.py`), in the status document and in a smoke
check.

**BY COMPONENT, NEVER BY COLOUR — work order 172.** The frame colour
turns exactly the HUD's own components and nothing else, whatever its
hue: the style values the blocks of `core/hud/` draw with (through
`core.hud.style.HudStyle.colour`), the accent words
(`style.WORDS_THAT_FOLLOW`), and the cut pieces that ARE frame
(`FOLLOWS`: the title plate, the nav glyphs, the TURN triangle). Inside
such a component EVERY pixel turns — 170 and 171 selected pixels by an
accent hue band (170-250 degrees), and on the title plate that left the
low-saturation and near-cyan pixels of its glossy centre untouched while
their neighbours went grey: the "blotchy smear" Data saw. The one named
exemption inside a component is the plate's two orange LAMPS
(`lamp_mask`), which 170 promised never turn.

Everything that is not a HUD component never reaches this module: the
pictures (New Game's settings, the planet surfaces, portraits, banners),
MOO2's sprites, star, player and race colours, the info panel's picture
icons, every value and white word. Nothing here can touch them, because
nothing passes them in.

**ONE RULE FOR CODE AND ARTWORK ALIKE, so the two never disagree.**
`transform_array` is the only function that turns anything; a style
colour and a plate pixel go through it identically.

**Why luminance and not HLS lightness** — measured, not assumed (170):
turning at constant HLS lightness made the fills of hues 25-175 degrees
so much brighter that a table word fell to 3.3:1; keeping each colour's
relative luminance keeps every word's contrast at every hue. The
REFERENCE hue is the measured panel edge's, 196: a setting of 196 changes
nothing, and so does the default, `None`.
"""
import colorsys

import numpy as np

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


#: Px the lamp mask grows by, in the piece's own (HUD) pixels: the pale
#: core of the lamps measures up to ~6 px from the nearest warm pixel.
LAMP_GROW = 6


def lamp_mask(rgb):
    """The title plate's two orange LAMPS, the one exemption inside a
    component (170: they never turn): warm (hue under 70 or over 330
    degrees), saturated (s >= 0.35) pixels of the UNTINTED piece."""
    x = np.asarray(rgb, np.uint8).astype(np.float64) / 255.0
    h, l, s = _hls(x)
    warm = ((h < 70.0) | (h > 330.0)) & (s >= 0.35)
    pale = (s < 0.35) & (l > 0.5)
    # AND THE LAMP'S PALE CORE: a lit lamp is near-white at its centre,
    # too unsaturated to be "warm", and turned it went grey inside an
    # orange ring (seen on dark grey and black, 172). The mask is grown
    # by LAMP_GROW px so the whole lamp stays as painted.
    grown = warm.copy()
    for _ in range(LAMP_GROW):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    # Grown only into the lamp's own warm or pale pixels — never into
    # the saturated blue lines beside it, which are frame and turn.
    return warm | (grown & pale)


def transform_array(rgb, d, s_factor, b_factor, word=False, floors=True,
                    keep=None):
    """THE RULE, over any (..., 3) uint8 array of a HUD COMPONENT — every
    colour and every pixel the frame colour turns goes through this one
    function, so code and cut pieces cannot disagree. Every pixel turns;
    `keep` (a boolean mask) names pixels that do not, which is only ever
    the plate's lamps.

    The hue turns by `d`, the saturation is multiplied by `s_factor`, and
    the result is scaled in linear light to a TARGET relative luminance —
    for a WORD its own measured luminance (labels follow the colour,
    never the brightness, so their contrast cannot fall), for everything
    else the measured luminance times `b_factor` (a fill only ever
    darkens; an edge darkens with the square root), held above the edge
    floors while `b_factor` darkens."""
    rgb = np.asarray(rgb, np.uint8)
    if d == 0 and s_factor == 1.0 and b_factor == 1.0:
        return rgb.copy()
    x = rgb.astype(np.float64) / 255.0
    h, l, s = _hls(x)
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
    if keep is not None:
        out = np.where(np.asarray(keep)[..., None], rgb, out)
    return out


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


def rotate_pixels(rgb, d=None, keep=None):
    """An (H, W, 3) uint8 image of a HUD component through the rule,
    current setting unless `d` is given (then the hue alone); a new
    array. `keep`: pixels that stay (the plate's lamps)."""
    # NO FLOORS ON PAINTED ARTWORK (work order 172). The floors lift a
    # colour whose measured luminance is an edge's to a fixed minimum;
    # on a painted GRADIENT — the plate's glossy centre glow — that lifted
    # the brighter half and let the darker half fall, which posterised it
    # into the smear Data saw in grey. A piece is scaled by one smooth
    # curve, so a gradient stays a gradient; its lines stay visible
    # because an edge still darkens only with the square root.
    if d is not None:
        return transform_array(rgb, d, 1.0, 1.0, keep=keep, floors=False)
    return transform_array(rgb, delta(), sat(), bright(), keep=keep,
                           floors=False)
