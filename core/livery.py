"""The fleet's livery on painted ships — work order 220, Data's decisions 1-6,
8 and 9.

HD EXTENSION `livery`: MOO2 draws eight drawings of a ship, one per colour,
and has nothing like it. A painted ship (decision 82: one colour-free
picture serves every owner) may bring livery MASKS beside its picture: a
first zone that takes the owner's colour, a second zone that takes the
player's own second colour. The player composes the look in the livery
window (GAME -> Settings, `screens/game_menu/gmlivery.py`); the battle lays
it on (`screens/combat/cbpaint.py`). This module is the one place that
holds the choice, its defaults, its names and the colour rules; nothing
here draws.

THE CHOICE, four values, kept with the player's settings
(`core.usersettings`, never with a save game):

  pattern   which masks: Light plates, Stripes, Outer hull, Mixed — or Full,
            no mask: 219's lighter colour over all the grey (decision 82 as
            amended by 219's decision 6)
  core      the tone of the owner's colour on the first zone: Strong (the
            colour as it is), Dark, Light, Muted — derived by one rule each,
            the same for every owner and every player-colour preset
            (`core_rgb`); not free (decision 4)
  second    any colour, or None, on the second zone — the player's own fleet
            only (decision 8): with eight owners every strong second colour
            is some other owner's colour
  strength  how strongly the painted plates take the colour (decision 9),
            from `STRENGTH_RANGE[0]` (faint) to 1 (full)

Pattern, core and strength apply to every fleet, so a battle looks of one
piece (decision 8). A ship without masks for the chosen pattern is drawn as
Full.

MASK FILES sit beside the ship's picture, one pair per pattern
(`mask_name`): `cmbtshp/all_<picture>_<frame>_<pattern>_mask.png` (the
first zone) and `…_mask2.png` (the second), greyscale, white = takes the
colour, soft edges, the picture's size exactly. Read through the same
loader as the picture (`CombatArt.painted_file`), so a mask is sized,
held (decision 83) and cached as its picture is.
"""
import colorsys
import logging

log = logging.getLogger("livery")

#: The patterns in the order the window steps through them; `full` has no
#: mask (decision 3).
PATTERNS = ("full", "light", "stripes", "outer", "mixed")
MASK_PATTERNS = PATTERNS[1:]
#: The core variants the chat side proposed (decision 4), each with its rule
#: below; the sheet of part E shows all four (`dev:tools/livery_sheets.py`).
CANDIDATES = ("strong", "dark", "light", "muted")
#: The ones the window offers. Two to four is Data's range; a candidate
#: that does not read as its owner for some owner is left out (decision 4).
#: Dark is: the silver owner's plates under it are the metal's grey (Delta
#: E 76 at battle size 3.3 with the original's colours, 6.6 with Okabe-Ito;
#: every other owner and variant 12 or more, `dev:tools/livery_sheets.py`).
#: Its rule stays, for the sheet that shows why.
CORES = ("strong", "light", "muted")
LEFT_OUT = {"dark": "silver"}
#: The strength slider's span (decision 9): faint .. full. Not 0: a fleet
#: with no colour at all is nobody's.
STRENGTH_RANGE = (0.2, 1.0)

#: The window's defaults ("Reset") and what a battle uses with nothing
#: stored: the first pattern with masks — decision 1, the masks are read
#: and their plates take the colour at full strength — in the colour as it
#: is, no second colour.
DEFAULT_PATTERN = "light"
DEFAULT_CORE = "strong"
DEFAULT_SECOND = None
DEFAULT_STRENGTH = 1.0

#: The user settings' keys (`core.usersettings.DEFAULTS` holds the same
#: defaults; the check holds the two equal).
KEYS = {"pattern": "livery_pattern", "core": "livery_core",
        "second": "livery_second", "strength": "livery_strength"}

# ── the core variants' rules, one place (part C) ─────────────────────
#: Dark: the colour's HSV value times this, its hue and saturation kept.
DARK_VALUE = 0.62
#: Light: the colour's HLS lightness this share of the way to white, its
#: hue and saturation kept.
LIGHT_TO_WHITE = 0.40
#: Muted: the colour's HLS saturation times this, its hue and lightness kept.
MUTED_SATURATION = 0.45


def core_rgb(rgb, core):
    """The owner's colour `rgb` (0-255) in the core variant `core`."""
    r, g, b = (max(0, min(255, int(c))) / 255 for c in rgb[:3])
    if core == "dark":
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        r, g, b = colorsys.hsv_to_rgb(h, s, v * DARK_VALUE)
    elif core == "light":
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb(h, l + (1 - l) * LIGHT_TO_WHITE, s)
    elif core == "muted":
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb(h, l, s * MUTED_SATURATION)
    return tuple(int(round(c * 255)) for c in (r, g, b))


def mask_name(picture, frame, pattern, zone=1):
    """The mask file of a painted picture's frame for a pattern: zone 1
    `…_mask.png`, zone 2 `…_mask2.png`."""
    return (f"all_{int(picture)}_{int(frame)}_{pattern}_mask"
            f"{'' if zone == 1 else '2'}.png")


class Livery:
    """One livery: the four choices and whose fleet carries the second
    colour (`own`, the player's colour index; None in the window's row of
    other owners and in a tool). Compared and hashed by value, so a battle
    knows when the choice changed (`CombatArt.set_livery`)."""

    __slots__ = ("pattern", "core", "second", "strength", "own")

    def __init__(self, pattern=DEFAULT_PATTERN, core=DEFAULT_CORE,
                 second=DEFAULT_SECOND, strength=DEFAULT_STRENGTH, own=None):
        self.pattern = pattern
        self.core = core
        self.second = None if second is None else tuple(int(c)
                                                        for c in second)
        self.strength = float(strength)
        self.own = None if own is None else int(own)

    def key(self):
        return (self.pattern, self.core, self.second,
                round(self.strength, 3), self.own)

    def __eq__(self, other):
        return isinstance(other, Livery) and self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

    def __repr__(self):
        return "Livery(%s, %s, %s, %.2f, own=%s)" % self.key()

    def second_for(self, colour):
        """The second colour on `colour`'s ships: the player's own only
        (decision 8), and never under Full (no second zone)."""
        if self.second is None or self.pattern == "full" or \
                self.own is None or int(colour) != self.own:
            return None
        return self.second


DEFAULT = Livery()

#: Values already said once (a stored value this build does not know).
_SAID = set()


def _fallback(key, value, default):
    if (key, repr(value)) not in _SAID:
        _SAID.add((key, repr(value)))
        log.warning("livery: the stored %s %r is not one this build knows — "
                    "the default %r is used", key, value, default)
    return default


def _second(value):
    if value is None or value == "none":
        return None
    try:
        rgb = tuple(int(c) for c in value)
    except (TypeError, ValueError):
        return _fallback(KEYS["second"], value, DEFAULT_SECOND)
    if len(rgb) != 3 or not all(0 <= c <= 255 for c in rgb):
        return _fallback(KEYS["second"], value, DEFAULT_SECOND)
    return rgb


def from_settings(settings, own=None):
    """The stored livery (`core.usersettings`), every value checked: one
    the build does not know is its default, with one log line (part D)."""
    get = settings.get if settings is not None else (lambda k: None)
    pattern = get(KEYS["pattern"])
    if pattern is None:
        pattern = DEFAULT_PATTERN
    elif pattern not in PATTERNS:
        pattern = _fallback(KEYS["pattern"], pattern, DEFAULT_PATTERN)
    core = get(KEYS["core"])
    if core is None:
        core = DEFAULT_CORE
    elif core not in CORES:
        core = _fallback(KEYS["core"], core, DEFAULT_CORE)
    strength = get(KEYS["strength"])
    if strength is None:
        strength = DEFAULT_STRENGTH
    else:
        try:
            strength = float(strength)
            if not STRENGTH_RANGE[0] - 1e-9 <= strength <= \
                    STRENGTH_RANGE[1] + 1e-9:
                raise ValueError(strength)
        except (TypeError, ValueError):
            strength = _fallback(KEYS["strength"], strength,
                                 DEFAULT_STRENGTH)
    return Livery(pattern, core, _second(get(KEYS["second"])), strength, own)


def store(settings, liv):
    """Write `liv` into the settings (in memory; `usersettings.save`
    writes the file)."""
    settings.set(KEYS["pattern"], liv.pattern)
    settings.set(KEYS["core"], liv.core)
    settings.set(KEYS["second"], None if liv.second is None
                 else list(liv.second))
    settings.set(KEYS["strength"], round(liv.strength, 2))


# ── what the mod folder offers (decision 2) ───────────────────────────
#: Where a colour-free painted ship and its masks sit in the tree that the
#: mod folder's `files/` mirrors (`core.usermod`).
SHIPS = "screens/combat/assets/gamedata/cmbtshp/"


def offered():
    """{picture: (patterns its frame 0 has a first-zone mask for)} of the
    colour-free painted ships the mod folder holds — only while the folder
    is switched on and in use (decision 2: the window is there only when it
    can do something); {} otherwise."""
    from core import usermod
    if not usermod.started_enabled() or not usermod.active():
        return {}
    # asked every frame of the settings view: the index changes only when
    # the folder is indexed again (`usermod.init` builds a new one)
    index = usermod._state["index"]
    if _OFFERED[0] is index:
        return _OFFERED[1]
    have = set(usermod.targets(SHIPS + "all_*_0.png"))
    out = {}
    for target in sorted(have):
        stem = target[len(SHIPS):-len(".png")]
        parts = stem.split("_")
        if len(parts) != 3 or not parts[1].isdigit():
            continue
        pic = int(parts[1])
        out[pic] = tuple(p for p in MASK_PATTERNS if SHIPS + mask_name(
            pic, 0, p) in set(usermod.targets(SHIPS + f"all_{pic}_0_*")))
    _OFFERED[:] = [index, out]
    return out


#: (the index `offered` read, its answer)
_OFFERED = [None, {}]


def window_available():
    """Decision 2: the livery window's button shows only when the mod folder
    is on and holds at least one painted ship with masks."""
    return any(offered().values())
