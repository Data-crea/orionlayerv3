"""Player-colour presets — an HD EXTENSION (fundament 63).

MOO2 assigns its eight player colours fixed. OrionLayer lets a player
swap all four tables that carry them — galaxy_map `owner_*` (star
names, the Planets list, the colony inset), `ship_*` (ship tints),
planets `owner_hover_*` and the `banner` / `banner_hd` cloth tints —
for a preset, or none of them: one empire, one colour everywhere.

`original` is no table: it is the skin as shipped. Every other preset
is eight base colours in `colors.json` [player_presets], and `apply`
derives the four tables from them by the rule stored next to them,
which is OUR rule and marked DEVIATION there — the original's tables
follow from no relation at all (measured 14 September 2026).

Operates on the colour DICT, never through `core.palette`, so
`palette.init` can call it before anything has a palette to ask.
"""
import copy
import itertools
import logging

log = logging.getLogger("playercolors")

ORIGINAL = "original"
ORDER = ("red", "yellow", "green", "silver", "blue", "brown", "purple",
         "orange")


def _section(colors):
    return colors.get("player_presets", {}) or {}


def names(colors):
    """Every preset the skin offers, `original` first."""
    return [ORIGINAL] + [k for k, v in _section(colors).items()
                         if isinstance(v, dict) and "base" in v]


def base(colors, name):
    """The eight base colours of a preset, in ORDER."""
    if name == ORIGINAL:
        g = colors.get("galaxy_map", {})
        return [tuple(g[f"owner_{i}"]) for i in range(8)]
    table = _section(colors)[name]["base"]
    return [tuple(table[n]) for n in ORDER]


def lift(rgb, k):
    return tuple(int(round(c + (255 - c) * k)) for c in rgb[:3])


def derive(colors, base_rgb):
    """The four tables of a preset, by the stored rule."""
    rule = _section(colors)["rule"]
    return {
        "owner": [tuple(b) for b in base_rgb],
        "ship": [lift(b, rule["k_ship"]) for b in base_rgb],
        "hover": [lift(b, rule["k_hover"]) for b in base_rgb],
        "banner": {n: (tuple(b), (0, 0, 0)) for n, b in zip(ORDER, base_rgb)},
    }


def apply(colors, preset=ORIGINAL, base_override=None):
    """(colour dict to use, preset actually active).

    `original` with no override returns the skin untouched — the same
    object, so the default path is the path the tree always had.
    """
    if preset in (None, ORIGINAL) and base_override is None:
        return colors, ORIGINAL
    if preset not in names(colors):
        log.warning("player colours: no preset %r in the skin — using the "
                    "original", preset)
        preset = ORIGINAL
        if base_override is None:
            return colors, ORIGINAL
    rgb = base(colors, preset)
    if base_override is not None:
        if (len(base_override) != 8
                or any(len(c) != 3 for c in base_override)):
            log.warning("player colours: the user's base table is not "
                        "eight RGB colours — ignored")
        else:
            rgb = [tuple(int(v) for v in c) for c in base_override]
            warn_if_indistinct(colors, rgb, "the user's base table")
    tables = derive(colors, rgb)
    out = copy.deepcopy(colors)
    for i in range(8):
        out["galaxy_map"][f"owner_{i}"] = list(tables["owner"][i])
        out["galaxy_map"][f"ship_{i}"] = list(tables["ship"][i])
        out["planets"][f"owner_hover_{i}"] = list(tables["hover"][i])
    for sec in ("banner", "banner_hd"):
        for name, (mul, add) in tables["banner"].items():
            out[sec][name] = {"multiply": list(mul), "add": list(add)}
    return out, preset


# ── Deuteranopia distance ────────────────────────────────

#: Viénot, Brettel & Mollon (1999), deuteranopia, in LINEAR sRGB.
DEUTERANOPIA = ((0.29275, 0.70725, 0.0),
                (0.29275, 0.70725, 0.0),
                (-0.02234, 0.02234, 1.0))


def _linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lab(lin):
    x = 0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]
    y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    z = 0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x / 0.95047), f(y), f(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def deuteranope_lab(rgb):
    lin = [_linear(c) for c in rgb[:3]]
    sim = [max(0.0, min(1.0, sum(DEUTERANOPIA[r][c] * lin[c]
                                 for c in range(3)))) for r in range(3)]
    return _lab(sim)


def deuteranopia_min(base_rgb):
    """(smallest pairwise dE76 after the simulation, index a, index b)."""
    labs = [deuteranope_lab(c) for c in base_rgb]
    best = None
    for a, b in itertools.combinations(range(len(labs)), 2):
        d = sum((p - q) ** 2 for p, q in zip(labs[a], labs[b])) ** 0.5
        if best is None or d < best[0]:
            best = (d, a, b)
    return best


def warn_if_indistinct(colors, base_rgb, what):
    """A warning, never an abort: it is the player's own choice."""
    limit = float(_section(colors).get("deuteranopia_min_delta_e", 10.0))
    dist, a, b = deuteranopia_min(base_rgb)
    if dist < limit:
        log.warning("player colours: in %s, %s and %s are only dE %.1f "
                    "apart for a deuteranope (the presets keep %.0f)",
                    what, ORDER[a], ORDER[b], dist, limit)
        return False
    return True
