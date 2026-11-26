"""Which special systems the original draws dim in the special picker, and why.

TRANSCRIPTION of `Print_Special_System_Data` (desbox.cpp:2800-2835) and
`Special_System_Exclusion` (design_specials.cpp:4-33): a row is bright when
it is "No Special" (row 0) or when it fits — the design's used space plus the
row's space, less the space of the special the chosen slot already holds,
stays within the hull — and no special already in the design excludes it,
unless that one is the very special being replaced. Otherwise the row is
drawn in the original's dull colour (`Font_Colors2(2, 'U', 'W')`).

WHERE THE INPUTS COME FROM: `rows` are DSBX's (item, space, cost: the
engine's `System_Added_Cost_And_Space`), `design` is DSGN's (space used, hull
space, the eight specials), `slot` DSBX's replacement slot. The space of the
replaced special is the engine's `special_device_space[slot]`, which is not on
the wire: it is taken from that special's own row in the list (the same
function gives it), UNVERIFIED `fit_replaced_space`: equal unless the design
was built at another tech level than the list is read at.

`EXCLUDES` is `TECHDATA::specials[i].exclude` (techdata.cpp:455-495), nonzero
entries only; a check holds it to the file where the source is on disk.

OMISSION `config_exclude_table`: the engine lets a config key `exclude`
of the tech tables override this table (`src/config/`, generated
`config.cpp`), and no wire block reports the effective one; the DEFAULT
table stands here. With a modded config the picker would dim a special
the engine accepts, or the reverse. UNVERIFIED with a modded config.
Wished from the engine: the exclusion mask per row in DSBX.
"""

EXCLUDES = {
    1: (1,),
    2: (2,),
    3: (3,),
    4: (4,),
    5: (5,),
    6: (23, 6, 31),
    7: (7, 13, 20, 30),
    8: (8,),
    9: (21, 9, 38),
    10: (10,),
    11: (11,),
    12: (12,),
    13: (13, 7),
    14: (14,),
    15: (15,),
    16: (16,),
    17: (18, 17),
    18: (17, 18),
    19: (19,),
    20: (20, 7),
    21: (9, 21, 38),
    22: (33, 22),
    23: (6, 23, 31),
    24: (24,),
    25: (25,),
    26: (26,),
    27: (27,),
    28: (28,),
    29: (29,),
    30: (30, 7),
    31: (31, 6, 23),
    32: (32,),
    33: (22, 33),
    34: (34,),
    35: (35,),
    36: (36,),
    37: (37,),
    38: (9, 38, 21),
    39: (3,),
}


def conflicts(special_id, current, slot):
    """Special_System_Exclusion: True when a special already in the design
    (`current`, the eight slots) is on `special_id`'s exclude list and is not
    the special in the replaced `slot`."""
    held = current[slot] if 0 <= slot < len(current) else 0
    for ex in EXCLUDES.get(special_id, ()):
        for cur in current:
            if cur == ex and held != cur:
                return True
    return False


def fits(row, rows, design, slot):
    """Whether the special picker draws `row` bright (see the module)."""
    item = row["item"]
    if item <= 0:
        return True
    current = list(design.get("specials") or [])
    held = current[slot] if 0 <= slot < len(current) else 0
    replaced = 0
    if held > 0:
        replaced = next((r["space"] for r in rows if r["item"] == held), 0)
    if design["space_used"] + row["space"] - replaced > design["hull_space"]:
        return False
    return not conflicts(item, current, slot)
