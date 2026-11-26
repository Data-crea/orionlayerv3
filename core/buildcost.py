"""`TECHDATA::buildings[id].cost` — the one number `Prod_To_Sort_Type` reads.

TRANSCRIPTION, `techdata.cpp:41-90` (`s_tech_building_data buildings
[BUILDING_COUNT]`, fields `name, building_id, tech_app, cost, unknown1,
maintenance, group, unknown2`, `techdata.h:40-49`): the table is compiled
into the engine, not read from techname.lbx, so it is a table here too
(work order 437; the earlier state said the costs were "not extracted",
which was wrong). Entry 0 is `BUILDING_NO_BUILDING`; the table has
`BUILDING_COUNT` = 49 entries (orion2_consts.h:64).

OMISSION `config_building_cost`: the engine lets a config key `cost` of
the tech tables override these values (`src/config/`, generated
`config.cpp`), and no wire block reports the effective ones. This is the
DEFAULT table. With a modded config the Colonies list's PRODUCING sort
orders buildings by a cost the engine does not use. `CSUM` carries the
game's own order (`core.colsumblock`); `colonyrows.csum_order_matches`
compares it with ours, so a divergence is visible, never silent.
UNVERIFIED live against a modded config. Wished from the engine: the
effective cost per building id in a wire block (orion2re_open_fixes).
"""

#: cost per building id, 0..48 (techdata.cpp:41-90, third number of
#: each entry after the name).
BUILDING_COST = (
    0, 60, 150, 1000, 200, 150, 200, 60,
    1000, 200, 100, 200, 250, 200, 500, 60,
    200, 500, 250, 250, 120, 60, 60, 500,
    200, 120, 120, 200, 80, 150, 150, 250,
    80, 200, 200, 60, 150, 120, 100, 80,
    400, 2500, 1000, 150, 250, 300, 200, 150,
    800,
)
assert len(BUILDING_COST) == 49


def cost(building_id):
    """`TECHDATA::buildings[id].cost`, or None for an id outside the table."""
    try:
        i = int(building_id)
    except (TypeError, ValueError):
        return None
    return BUILDING_COST[i] if 0 <= i < len(BUILDING_COST) else None
