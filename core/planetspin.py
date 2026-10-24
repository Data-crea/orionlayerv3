"""The rotating planets' values, their one clock and each planet's own turn —
work order 331 (Data: every planet picture is a sphere that turns).

HD EXTENSION `rotating_planets`: the original draws a planet as one static
sprite (`CMBTPLNT`, the battle's; the discs of the lists are ours). Nothing
here touches the game: the angle is a function of the clock and of the
planet's identity, never stored, never sent.

**ONE CLOCK.** `now()` is the process's monotonic time. Every screen asks it
and nothing else, so one planet shows the same orientation on every screen
at the same moment (decision 78: elapsed time, never a frame count).

**A PLANET'S OWN TURN** is derived from `(climate, seed)` by a CRC, so it is
the same on every run and every screen: a start angle anywhere in the turn
and a speed within `speed_spread` of the type's. All turn the same way,
prograde (the surface moves left to right as seen with north up).

**THE VALUES ARE A MOD'S.** `DEFAULT` is the one copy; the player's
`planets.json` in the mod folder is merged over it key by key
(`core.usermod.planet_overrides`), so a mod writes only what it changes.
MODDING.md lists every key.
"""
import math
import time
import zlib

from core import usermod

#: Built in, so a pack with no file still turns: the file only changes values.
DEFAULT = {
    # One full turn of a planet whose own speed factor is 1; 0 = no turn.
    "seconds_per_turn": 60.0,
    # A planet's own factor lies within 1 +- this (a fraction).
    "speed_spread": 0.15,
    # The cloud layer's turn relative to the surface (only if a map exists).
    "cloud_speed": 1.25,
    # What the shade never goes below (0..1), and how fast the limb darkens.
    "ambient": 0.10,
    "limb": 0.55,
    # The ring of glow, as a fraction of the picture's half side, and the
    # brightness of the atmosphere seen over the lit rim.
    "glow_width": 0.068,
    "rim": 0.45,
    # The simplest of the two night-side lights: lava keeps its own glow
    # where `emissive` > 0 (see planetsphere).
    "types": {},
}
#: One type's values; `light` points from the planet to the light, x right,
#: y down, z toward the viewer (the old pictures: upper left).
TYPE_DEFAULT = {
    "glow": [110, 150, 200], "glow_strength": 0.8,
    "speed": 1.0, "emissive": 0.0, "light": [-0.58, -0.52, 0.63],
}
#: The first proposal, read off the old pictures' rim (WO 331); Data judges.
GLOWS = {
    "toxic": [120, 200, 60], "radiated": [255, 150, 40],
    "barren": [150, 150, 160], "desert": [230, 130, 60],
    "tundra": [120, 190, 240], "ocean": [60, 140, 230],
    "swamp": [90, 180, 100], "arid": [220, 180, 120],
    "terran": [70, 150, 240], "gaia": [90, 220, 190],
    "volcanic": [255, 90, 30],
}
EMISSIVE = {"volcanic": 1.0, "radiated": 0.5}
for _n, _g in GLOWS.items():
    DEFAULT["types"][_n] = dict(TYPE_DEFAULT, glow=_g,
                                emissive=EMISSIVE.get(_n, 0.0))

_clock = time.monotonic
_state = {"cfg": None, "touched": None}


def now():
    return _clock()


def set_clock(fn):
    """Tests and the evidence tool drive the clock; None restores it."""
    global _clock
    _clock = fn or time.monotonic


def config(res=None):
    """The values: `DEFAULT` with the player's `planets.json` over it, read
    once per `reload`."""
    if _state["cfg"] is None:
        _state["cfg"] = _sane(usermod.planet_overrides(DEFAULT))
    return _state["cfg"]


def _sane(cfg):
    """A mod's numbers kept inside what the drawing can use: `merge` checks
    kinds, not ranges, and a glow width of 1 would divide by zero."""
    def num(v, lo, hi, d):
        return min(hi, max(lo, v)) if isinstance(v, (int, float)) else d
    cfg = dict(cfg)
    cfg["glow_width"] = num(cfg["glow_width"], 0.02, 0.4, 0.068)
    cfg["ambient"] = num(cfg["ambient"], 0.0, 1.0, 0.10)
    cfg["limb"] = num(cfg["limb"], 0.0, 1.0, 0.55)
    cfg["rim"] = num(cfg["rim"], 0.0, 2.0, 0.45)
    cfg["speed_spread"] = num(cfg["speed_spread"], 0.0, 0.9, 0.15)
    cfg["seconds_per_turn"] = max(0.0, cfg["seconds_per_turn"])
    types = {}
    for name, v in cfg["types"].items():
        v = dict(v)
        for key, fix in (("glow", (3, 0, 255)), ("light", (3, -1e6, 1e6))):
            val = v.get(key)
            if not (isinstance(val, list) and len(val) == fix[0] and all(
                    isinstance(x, (int, float)) for x in val)):
                v[key] = TYPE_DEFAULT[key]
            elif key == "glow":
                v[key] = [min(255, max(0, x)) for x in val]
        v["speed"] = num(v.get("speed"), 0.0, 10.0, 1.0)
        v["emissive"] = num(v.get("emissive"), 0.0, 1.0, 0.0)
        v["glow_strength"] = num(v.get("glow_strength"), 0.0, 2.0, 0.8)
        types[name] = v
    cfg["types"] = types
    return cfg


def reload():
    _state["cfg"] = None


def type_values(cfg, name):
    return cfg["types"].get(name) or dict(TYPE_DEFAULT)


def variation(climate, seed):
    """(start angle in turns, speed factor) of one planet, from its identity
    alone."""
    h = zlib.crc32(f"{climate}/{seed}".encode())
    return ((h & 0xFFFF) / 65536.0, ((h >> 16) & 0xFFFF) / 65535.0)


def angle(cfg, name, climate, seed, t=None):
    """The planet's turn at time `t`, in radians, growing without bound
    (prograde)."""
    start, spread = variation(climate, seed)
    period = float(cfg["seconds_per_turn"])
    speed = float(type_values(cfg, name)["speed"]) * (
        1.0 + float(cfg["speed_spread"]) * (2.0 * spread - 1.0))
    turns = start
    if period > 0 and speed > 0:
        turns += (now() if t is None else t) * speed / period
    return 2.0 * math.pi * turns


#: A still screen that shows a planet is redrawn when the nearest sphere
#: has moved about this many pixels at its centre, and never faster than
#: `FASTEST`: a small planet turns under a pixel a second and costs a
#: redraw a second, a big one a few (`core.drawgate`).
MOVE_PX = 0.7
FASTEST = 1 / 15


def touch(side=0, cfg=None):
    """A sphere of `side` px was drawn this frame: `core.drawgate` reads the
    soonest moment any sphere shown has moved a visible step."""
    cfg = cfg or config()
    period = float(cfg["seconds_per_turn"])
    speed = 1.0 + float(cfg["speed_spread"])
    if period <= 0 or side <= 0:
        return
    rate = (side / 2.0) * 2.0 * math.pi * speed / period      # px / second
    due = max(FASTEST, MOVE_PX / rate) if rate > 0 else None
    old = _state["touched"]
    _state["touched"] = due if old is None else min(old, due)


def take_touched():
    """The seconds until the next visible step of the spheres drawn since
    the last call, or None when none was drawn."""
    seen, _state["touched"] = _state["touched"], None
    return seen
