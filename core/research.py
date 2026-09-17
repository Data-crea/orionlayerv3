"""The original's research arithmetic: cost, breakthrough chance, turns.

TRANSCRIBED from orion2re's own source, read 17 September 2026 (work order
129 C) against the engine `core.config.ORION2RE_VERSION` names.
The galaxy map's sidebar prints what `MAINSCR::Print_Main_Screen_Data_`
prints (mainscr_main.cpp:178-243), and that reads the three functions below.
Nothing here is HD's own rule; where a number is a copy it has a checker,
because a hand-copied table without one is the nebula sizes again
(decision 36).

    FIELD_COST            TECHDATA::_technology_fields[].cost
                          (techdata.cpp:319ff, TECH_FIELD_COUNT = 83),
                          checked against the source by
                          tools/research_cost_check.py, which the smoke
                          test runs.
    cost()                COLCALC::Player_Research_Cost_ (colcalc.cpp:526-539)
    chance()              COLCALC::Chance_For_Research_Breakthrough_Aux_
                          (colcalc.cpp:469-484)
    turns_until_complete() COLCALC::Player_N_Turns_Until_Research_Complete_
                          (colcalc.cpp:432-458)

The player values these need — `tech_fields[]` (the per-field status) and
`hyper_advanced_tech[]` (the per-field surcharge counter) — are in
`core/structs/player.py`; see there for the two sources each rests on.
"""

#: TECHDATA::_technology_fields[i].cost, techdata.cpp:319ff — the sixth
#: column of the table, one row per technology field, index 0 unused.
#: A transcription: tools/research_cost_check.py reads the same column out
#: of techdata.cpp and fails on any difference.
FIELD_COST = (
    0, 400, 650, 150, 80, 250, 4500, 250,
    1500, 250, 150, 2000, 2000, 2000, 1500, 400,
    1150, 4500, 80, 1150, 400, 250, 50, 80,
    3500, 2750, 3500, 1500, 50, 50, 2750, 150,
    6000, 4500, 900, 1150, 650, 3500, 4500, 6000,
    10000, 900, 6000, 1150, 1500, 900, 2750, 1150,
    10000, 6000, 4500, 4500, 2000, 2000, 900, 50,
    150, 50, 7500, 3500, 900, 4500, 650, 900,
    2750, 1500, 250, 3500, 15000, 15000, 7500, 7500,
    2000, 650, 15000, 25000, 25000, 25000, 25000, 25000,
    25000, 25000, 25000,
)

#: The field from which a research field carries the hyper-advanced
#: surcharge, and what each count costs (colcalc.cpp:533-537).
HYPER_ADVANCED_FIRST_FIELD = 75
HYPER_ADVANCED_STEP = 10000

#: TECH_FIELD_COUNT (orion2_consts.h:945) — the length of both the cost
#: table and the player's status array.
FIELD_COUNT = 83

#: `tech_fields[field] == 3` is "already researched"
#: (colcalc.cpp:436-438).
STATUS_RESEARCHED = 3


def cost(field, hyper_advanced=None):
    """COLCALC::Player_Research_Cost_ (colcalc.cpp:526-539).

    0 for field 0; the table's cost otherwise, plus 10000 per count in
    `hyper_advanced_tech[field - 75]` from field 75 on.
    """
    if field is None or field <= 0 or field >= FIELD_COUNT:
        return 0
    total = FIELD_COST[field]
    if field >= HYPER_ADVANCED_FIRST_FIELD and hyper_advanced:
        index = field - HYPER_ADVANCED_FIRST_FIELD
        if 0 <= index < len(hyper_advanced):
            total += int(hyper_advanced[index]) * HYPER_ADVANCED_STEP
    return total


def chance(accumulated, produced, field_cost):
    """COLCALC::Chance_For_Research_Breakthrough_Aux_ (colcalc.cpp:469-484).

    The percentage for THIS turn: zero until the accumulated points pass
    the cost, then `(accumulated - cost) * 100 / cost`, clamped to 100 and
    raised to 1 where the division gives 0. Integer arithmetic throughout,
    as the original's is.
    """
    if not (0 < field_cost < accumulated):
        return 0
    value = (accumulated - field_cost) * 100 // field_cost
    if value > 100:
        return 100
    return value or 1


def turns_until_complete(field, status, accumulated, produced, field_cost):
    """COLCALC::Player_N_Turns_Until_Research_Complete_ (colcalc.cpp:432-458).

    0 when the field is already researched; -1 when nothing is produced and
    the points have not reached the cost (research stands still); otherwise
    the loop the original runs — add a turn, add this turn's production,
    add this turn's chance, until the chances sum to 100.
    """
    if field is None or field <= 0:
        return 0
    if status == STATUS_RESEARCHED:
        return 0
    if produced == 0 and accumulated <= field_cost:
        return -1
    turns, total, points = 0, 0, int(accumulated)
    while total < 100:
        turns += 1
        points += int(produced)
        total += chance(points, produced, field_cost)
        if turns > 10000:            # the original cannot loop for ever
            break                    # here: produced > 0 above guarantees it
    return turns
