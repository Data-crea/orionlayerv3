"""How finely the battle holds a painted picture — work order 219,
Data's decisions 1-3.

HD EXTENSION `painted_detail`: MOO2 has no such setting (its battle draws
its 640 x 480 drawings and nothing finer). A painted battle picture in the
player's mod folder may carry k times the pixels of the drawing it replaces
(decision 81); this setting lets the game HOLD it at a smaller whole
multiple: Normal at 4 x at most, High at 8 x at most. The mod folder keeps
one picture per name, the largest the modder has, and the game shrinks it
once at load (`screens/combat/cbart.py`); a picture is never enlarged — a
4 x file stays 4 x under High, a 2 x file 2 x under Normal.

Auto picks by the battle's opening view (`cbview.Camera.framing`: 32 cells
across the field, window px per drawing px): the smallest step at which a
painted picture is not enlarged there — Normal while the opening view is at
most 4 x, i.e. a field up to 2560 px wide (2560 x 1440 and below), High
above it (3440 x 1440, 3840 x 2160). Read when a battle's first view is
built, so a change in Game Settings shows from the next battle on.
"""

#: The battle's opening view in drawing px across the field: 32 cells of
#: 20 px (`screens/combat/cbview.py` VIEW_CELLS x CELL), so its scale is the
#: field's width / 640 — for the row's "Auto (k x)" outside a battle.
OPENING_PX = 32 * 20

STEPS = ("auto", "normal", "high")
DEFAULT = "auto"
#: The largest factor each step holds a painted picture at.
FACTORS = {"normal": 4, "high": 8}


def cap(choice, framing):
    """The largest factor a painted picture is held at, for a choice and the
    battle's opening view `framing` (window px per drawing px)."""
    choice = choice if choice in STEPS else DEFAULT
    if choice != "auto":
        return FACTORS[choice]
    steps = sorted(FACTORS.values())
    return next((k for k in steps if k >= framing - 1e-9), steps[-1])
