"""The box fill: one colour for every box, and the glass switch.

HD EXTENSION, decision 94 (work order 227, Data's decisions 1 and 2 of
9 October 2026).

MOO2 draws its boxes in its own palette and has no such setting; both
controls are ours, marked here, in the GAME menu's Settings dialog
(`screens/game_menu/gmfill.py`), in the state and in a smoke check.

**ONE COLOUR, A FAMILY.** The player sets the PANEL fill (`colour()`).
Every other fill a block draws follows it by the relation decision 93
measured off Data's Planets picture (`measured.mockup_planets`): the
cell, the B stripe, the header band and a button darker than the panel,
"selected" lighter. A member is the panel colour scaled in linear light
to the picture's luminance ratio (`member`), so it keeps the chosen hue
and saturation and changing the colour moves the whole family. Nothing
here is per screen: `core.hud.style` resolves `fill.<name>` tokens to
these, and the blocks read the tokens.

**THE FILL IS WHAT THE PLAYER SETS — the frame colour never touches it**
(Data, answering 226 P2). Frame hue, saturation and brightness turn the
lines only (`core.hud.tint`); a member is returned as it is, untinted.
The lines keep their contrast against the fill instead: `tint` reads
`ground_pair()`, the brightest fill an edge stands on, and lifts an edge
that would fall under 3:1 against it, or under the contrast it has at
the starting colour where that is less (the dim edge, by Data's design).

**GLASS ON OR OFF.** Off (the default — Data's decision of work order
228, answering 227 P1; also for a settings file without the key):
every box is filled opaque with its member, and the background never
shows through (`core.hud.glass.fill`). On: the glass of work order 174,
its gradient this colour's family, with its strength slider.

**THE RANGE IS LIMITED, THE WORDS NEVER CHANGE** (the order: "the
control's range is limited, or the text colour follows"). Hue and
saturation are free; the fill's luminance runs from black to `y_max()`,
the highest at which every HUD word keeps `glass.floor_contrast` on the
brightest member a word can stand on, and "selected" still stands 12 L*
off a cell (decision 71 as amended). "Selected" itself rises with the
colour, never under the picture's (decision 93) and never above the
word floor — it gives way, never the words.
"""
import colorsys

import numpy as np

from core.hud import style as hudstyle
from core.hud import tint

#: The picture's members (decision 93) and what each is measured against:
#: a target is drawn opaque at the panel's luminance times its ratio.
#: (key in measured.mockup_planets, basis key)
TARGETS = {
    "panel": ("panel", "panel"),
    "cell": ("cell", "panel"),
    "header": ("header", "panel"),
    "button": ("button", "panel"),
    # Data's decision 2 of work order 228 (226 P1): ONE "selected", the
    # picture's brighter — the toggle that is on, the active sort button
    # (74, 74, 66) — for a chosen row as well (decision 92).
    "selected": ("on", "panel"),
    "dense": ("dense_glass", "ref_panel"),
    "glass_top": ("glass_top", "ref_panel"),
    "glass_bottom": ("glass_bottom", "ref_panel"),
}

#: A band laid over dense glass, its target and the share it is laid at
#: (`chosen.glass.<share>`): the shade colour is SOLVED so that over the
#: dense member the band reads its target, as `dev:tools/hud_planets.py`
#: solves the picture's — one formula for both switch positions.
SHADES = {
    "shade_cell": ("cell", "row_shade"),
    "shade_row_b": ("row_b", "row_shade"),
    "shade_header": ("header", "header_shade"),
    "shade_selected": ("selected", "selected_shade"),
}

#: The members an edge or a word can stand on (not "selected", which
#: wears its own lit edge and holds its own word floor).
GROUND = ("panel", "dense", "cell", "row_b", "header", "button",
          "glass_top", "glass_bottom")

#: "Selected" stands at least this far off a cell (decision 71 as amended
#: by work order 223: "'on' at least 12 L* off a field").
ON_OFF_FIELD = 12.0

_glass_on = None
_colour = None
_cache = {}
#: What depends on the style alone (the word floor, the range): kept
#: across colour changes, dropped with the style (`reset`).
_fixed = {}


def _st():
    return hudstyle.get()


def default_colour():
    """The starting colour: `chosen.fill.default` — decision 93's panel,
    or a mod's partial style.json."""
    return tuple(int(v) for v in _st().get("fill.default")[:3])


def default_glass():
    return bool(_st().get("fill.glass_default", False))


def glass_on():
    return default_glass() if _glass_on is None else _glass_on


def colour():
    """The panel fill in force: the player's, else the default."""
    return default_colour() if _colour is None else _colour


def is_default():
    return _colour is None


def _changed():
    _cache.clear()
    hudstyle._mixes.clear()
    tint.set_ground(*ground_pair())
    for fn in hudstyle._listeners:
        fn()


def set_glass(on):
    """The switch (None = the default). Applies at once. True if changed."""
    global _glass_on
    on = None if on is None else bool(on)
    if on is not None and on == default_glass():
        on = None
    if on == _glass_on:
        return False
    _glass_on = on
    _changed()
    return True


def set_colour(rgb):
    """The fill colour (None = the default), clamped into the range.
    Applies at once. True if anything changed."""
    global _colour
    c = None if rgb is None else clamp(rgb)
    if c is not None and c == default_colour():
        c = None
    if c == _colour:
        return False
    _colour = c
    _changed()
    return True


def apply_settings(user_settings):
    """The saved switch and colour (`hud_glass_on`, `hud_fill`), at start."""
    on = user_settings.get("hud_glass_on")
    rgb = user_settings.get("hud_fill")
    ok_rgb = (isinstance(rgb, (list, tuple)) and len(rgb) == 3
              and all(isinstance(v, (int, float)) for v in rgb))
    a = set_glass(None if on is None else bool(on))
    b = set_colour(tuple(rgb) if ok_rgb else None)
    return a or b


def reset():
    """Back to the defaults (the smoke test, after swapping roots)."""
    global _glass_on, _colour
    _glass_on, _colour = None, None
    _cache.clear()
    _fixed.clear()
    if hudstyle._STYLE is not None:
        tint.set_ground(*ground_pair())
    else:
        tint.set_ground(None, None)


# ── the colour model: hue, saturation, luminance ─────────────────────

def lum(rgb):
    return float(tint.luminance(rgb[:3]))


def at_luminance(rgb, y):
    """`rgb` scaled in linear light to relative luminance `y`, its hue and
    saturation kept; what a saturated colour cannot reach goes the rest of
    the way towards white. Black at y > 0 is the grey of y."""
    y = max(0.0, min(1.0, float(y)))
    lin = tint._lin(np.asarray(rgb[:3], np.float64) / 255.0)
    have = float((lin * tint._W).sum())
    if have <= 1e-12:
        lin = np.full(3, y)
    else:
        lin = np.clip(lin * y / have, 0.0, 1.0)
        short = y - float((lin * tint._W).sum())
        if short > 1e-12:
            room = float(((1.0 - lin) * tint._W).sum())
            lin = lin + (1.0 - lin) * min(1.0, short / max(room, 1e-12))
    out = tint._srgb(lin)
    return tuple(int(v) for v in np.clip(np.round(out * 255.0), 0, 255))


def from_controls(h, s, y):
    """The colour of the three bars: hue 0..1, saturation 0..1, luminance
    0..y_max. The one mapping for the click and the swatch (decision 5)."""
    base = tuple(int(round(v * 255)) for v in colorsys.hsv_to_rgb(
        h % 1.0, max(0.0, min(1.0, s)), 1.0))
    return at_luminance(base, min(y, y_max()))


def to_controls(rgb):
    """(hue, saturation, luminance) of a stored colour, for the thumbs."""
    h, s, _v = colorsys.rgb_to_hsv(*(v / 255.0 for v in rgb[:3]))
    return h, s, lum(rgb)


def clamp(rgb):
    """A colour inside the range: its luminance at most `y_max()`."""
    rgb = tuple(int(max(0, min(255, round(v)))) for v in rgb[:3])
    return at_luminance(rgb, y_max()) if lum(rgb) > y_max() + 1e-9 else rgb


# ── the family ───────────────────────────────────────────────────────

def ratio(name):
    """A member's luminance over the panel's, in Data's picture."""
    mp = _st().get("mockup_planets")
    if name == "row_b":
        # Decision 57's stripe as `hud_planets` lifts it: the cell's sRGB
        # values times the colony mockup's B/A ratio to the 1/2.2.
        lift = float(mp["stripe_lift"]) ** (1 / 2.2)
        b = [min(255.0, v * lift) for v in mp["cell"][:3]]
        return lum(b) / max(lum(mp["panel"]), 1e-12)
    key, basis = TARGETS[name]
    return lum(mp[key]) / max(lum(mp[basis]), 1e-12)


#: The words' floor is taken a little above `glass.floor_contrast`: a word
#: the frame colour turns keeps its luminance only to the rounding of its
#: channels (a few thousandths), and the fill may not depend on the frame
#: colour to make up for it.
WORD_MARGIN = 0.1


def _word_floor():
    """The brightest a fill a word stands on may be: the dimmest HUD word
    at the floor contrast (plus `WORD_MARGIN`) — the same at every frame
    colour. A word the frame colour never turns counts at its own
    luminance; an accent word (`style.WORDS_THAT_FOLLOW`) at the least it
    reaches over every hue and saturation the frame colour can take (a
    saturated hue clips a channel and loses some)."""
    hit = _fixed.get("word_floor")
    if hit is not None:
        return hit
    from core.hud import glass
    st = _st()
    hues = np.arange(0.0, 360.0, 1.0)
    tmin = 1.0
    for w in glass.WORDS:
        # resolved as a word the frame colour never turns: its own colour
        c = st._colour(w, "text.untinted")
        y = lum(c)
        if hudstyle.follows_as_word(w):
            arr = np.array([[list(c)]], np.uint8)
            for sf in (0.0, 0.5, 1.0):
                for d in hues - tint.REFERENCE:
                    y = min(y, lum(tint.transform_array(
                        arr, d, sf, 1.0, word=True)[0, 0]))
        tmin = min(tmin, y)
    floor = float(st.get("glass.floor_contrast")) + WORD_MARGIN
    _fixed["word_floor"] = (tmin + 0.05) / floor - 0.05
    return _fixed["word_floor"]


def _L(y):
    return 116 * y ** (1 / 3) - 16 if y > 216 / 24389 else y * 24389 / 27


def _y_of_L(L):
    return ((L + 16) / 116) ** 3 if L > 8 else L * 27 / 24389


def y_max():
    """The brightest panel luminance the control reaches: every word at the
    floor on every member it can stand on, and room for 'selected' 12 L*
    above a cell under the same floor."""
    if "y_max" in _fixed:
        return _fixed["y_max"]
    wf = _word_floor()
    by_words = wf / max(ratio(n) for n in GROUND)
    by_on = _y_of_L(_L(wf) - ON_OFF_FIELD) / ratio("cell")
    _fixed["y_max"] = min(by_words, by_on)
    return _fixed["y_max"]


def target(name, rgb=None):
    """What a member reads when drawn: the panel colour at the member's
    luminance. 'selected' is raised to the picture's (its toggle that is
    on, work order 228) and to 12 L* off a cell, and gives way at the word
    floor."""
    rgb = colour() if rgb is None else tuple(rgb[:3])
    y = lum(rgb) * ratio(name if name != "selected" else "selected")
    if name == "selected":
        mp = _st().get("mockup_planets")
        cell = lum(rgb) * ratio("cell")
        y = max(y, lum(mp["on"]), _y_of_L(_L(cell) + ON_OFF_FIELD))
        y = min(y, _word_floor())
    return at_luminance(rgb, y)


def shade(name, rgb=None):
    """A band's shade colour: solved per channel so that laid at its share
    over the dense member it reads its target (clipped to 0..255)."""
    want, share_key = SHADES[name]
    a = float(_st().get("glass." + share_key))
    t = np.asarray(target(want, rgb), float)
    d = np.asarray(target("dense", rgb), float)
    return tuple(int(v) for v in np.clip(np.round((t - d * (1 - a)) / a),
                                         0, 255))


def member(name):
    """`fill.<name>` as `core.hud.style` resolves it; untinted."""
    key = (name, colour())
    hit = _cache.get(key)
    if hit is None:
        hit = shade(name) if name in SHADES else target(name)
        _cache[key] = hit
    return hit


def ground(rgb=None):
    """The luminance of the brightest member an edge or word stands on."""
    return max(lum(target(n, rgb)) for n in GROUND)


def ground_pair():
    """(ground now, ground at the starting colour) for `tint`'s edge floors."""
    return ground(), ground(default_colour())
