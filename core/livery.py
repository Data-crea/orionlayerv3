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

THE CHOICE, three values, kept with the player's settings
(`core.usersettings`, never with a save game):

  pattern   which masks: Light plates, Stripes, Outer hull, Mixed — or Full,
            no mask: 219's lighter colour over all the grey (decision 82 as
            amended by 219's decision 6)
  second    any colour, or None, on the second zone — the player's own fleet
            only (decision 8): with eight owners every strong second colour
            is some other owner's colour
  strength  how strongly the painted plates take the colour (decision 9),
            from `STRENGTH_RANGE[0]` (faint) to 1 (full)

The owner's colour is always laid as it is: the core variants of decision 4
(Light, Muted; Dark was left out at the time) were retired on 13 Nov 2026
(Data): measured, each only moved the saturation the strength slider
moves, and each made neighbouring owners harder to tell apart on the
galaxy map. A stored `livery_core` is dropped on load
(`core.usersettings.RETIRED`).

Pattern and strength apply to every fleet, so a battle looks of one
piece (decision 8). A ship without masks for the chosen pattern is drawn as
Full.

MASK FILES sit beside the ship's picture, one pair per pattern
(`mask_name`): `cmbtshp/all_<picture>_<frame>_<pattern>_mask.png` (the
first zone) and `…_mask2.png` (the second), greyscale, white = takes the
colour, soft edges, the picture's size exactly. Read through the same
loader as the picture (`CombatArt.painted_file`), so a mask is sized,
held (decision 83) and cached as its picture is.
"""
import logging

log = logging.getLogger("livery")

#: The patterns in the order the window steps through them; `full` has no
#: mask (decision 3).
PATTERNS = ("full", "light", "stripes", "outer", "mixed")
MASK_PATTERNS = PATTERNS[1:]
#: The strength slider's span (decision 9): faint .. full. Not 0: a fleet
#: with no colour at all is nobody's; and not below 0.5 since 13 Nov 2026
#: (Data): measured on a battleship, the nearest two owners of the eight
#: were 7 apart (of 255) at 0.3 and 24 at 1.0 — under half the colour the
#: owners cannot be told apart. A stored value below it is read as 0.5.
STRENGTH_RANGE = (0.5, 1.0)

#: The window's defaults ("Reset") and what a battle uses with nothing
#: stored: the first pattern with masks — decision 1, the masks are read
#: and their plates take the colour at full strength — in the colour as it
#: is, no second colour.
DEFAULT_PATTERN = "light"
DEFAULT_SECOND = None
DEFAULT_STRENGTH = 1.0

#: The user settings' keys (`core.usersettings.DEFAULTS` holds the same
#: defaults; the check holds the two equal).
KEYS = {"pattern": "livery_pattern", "second": "livery_second",
        "strength": "livery_strength"}

def mask_name(picture, frame, pattern, zone=1):
    """The mask file of a painted picture's frame for a pattern: zone 1
    `…_mask.png`, zone 2 `…_mask2.png`."""
    return (f"all_{int(picture)}_{int(frame)}_{pattern}_mask"
            f"{'' if zone == 1 else '2'}.png")


class Livery:
    """One livery: the three choices and whose fleet carries the second
    colour (`own`, the player's colour index; None in the window's row of
    other owners and in a tool). Compared and hashed by value, so a battle
    knows when the choice changed (`CombatArt.set_livery`)."""

    __slots__ = ("pattern", "second", "strength", "own")

    def __init__(self, pattern=DEFAULT_PATTERN, second=DEFAULT_SECOND,
                  strength=DEFAULT_STRENGTH, own=None):
        self.pattern = pattern
        self.second = None if second is None else tuple(int(c)
                                                        for c in second)
        self.strength = float(strength)
        self.own = None if own is None else int(own)

    def key(self):
        return (self.pattern, self.second,
                round(self.strength, 3), self.own)

    def __eq__(self, other):
        return isinstance(other, Livery) and self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

    def __repr__(self):
        return "Livery(%s, %s, %.2f, own=%s)" % self.key()

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
    strength = get(KEYS["strength"])
    if strength is None:
        strength = DEFAULT_STRENGTH
    else:
        try:
            strength = float(strength)
            if strength < STRENGTH_RANGE[0]:
                strength = STRENGTH_RANGE[0]
            elif strength > STRENGTH_RANGE[1] + 1e-9:
                raise ValueError(strength)
        except (TypeError, ValueError):
            strength = _fallback(KEYS["strength"], strength,
                                 DEFAULT_STRENGTH)
    return Livery(pattern, _second(get(KEYS["second"])), strength, own)


def store(settings, liv):
    """Write `liv` into the settings (in memory; `usersettings.save`
    writes the file)."""
    settings.set(KEYS["pattern"], liv.pattern)
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
