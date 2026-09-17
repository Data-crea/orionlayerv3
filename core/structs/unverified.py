"""UNVERIFIED starting-point specs — DO NOT use in production paths.

Specs live here until their offsets are confirmed. Confirmation
means one of:
  - numeric agreement with live data via tools/struct_probe.py, or
  - orion2re's own header compiled with its `#pragma pack(1)` and
    the resulting sizeof matching the assert in sizes.h.

Once confirmed, a spec moves into its own module with
verified=True and the evidence written into the docstring.

Already promoted out of this file:
  s_nebula      -> core/structs/nebula.py   (26 Aug 2026)
  s_planet_data -> core/structs/planet.py   (26 Aug 2026)
  s_player      -> core/structs/player.py   (26 Aug 2026, partial)
  s_colony      -> core/structs/colony.py   (31 Aug 2026; byte
                   layout verified against the colony summary of an
                   85-turn savegame, the pop[] bit masks promoted
                   with it but NOT all verified — only MASK_PROF is)

The old s_planet_data guess that used to sit here had `star_index`
at offset 0 and an invented `position` at 2. Both were wrong: the
real first member is `colony_index`. Kept as a note because it is
exactly the kind of plausible-looking guess this file exists to
quarantine.

Still needed, still unverified:
  s_leader_data (59 B)  — officers screen
  s_player.hyper_advanced_tech @640 — see HYPER_ADVANCED_TECH below
"""
from core.structs import Spec

# s_leader_data: 59 bytes. Same situation.
LEADER = Spec("s_leader_data", 59, [], verified=False,
              note="confirm name string offset first, it is the "
                   "cheapest ground truth")


#: s_player.hyper_advanced_tech[MAX_PLAYERS] — eight bytes, one per
#: technology field from 75 on, each adding 10000 to that field's research
#: cost (`COLCALC::Player_Research_Cost_`, colcalc.cpp:526-539). Read at 640
#: from orion2re's own headers compiled with their packing, with
#: `sizeof(s_player)` matching sizes.h — ONE source. The live read on SAVE4
#: and SAVE5 is eight zeros, and **a zero confirms no offset** (the same
#: rule the monster damage fields were left under, fundament 64), so this
#: stays here until a game that has reached hyper-advanced research can be
#: read. Consequence, written down rather than discovered later: the
#: sidebar's turn count is an UNDERESTIMATE for fields 75..82 while the
#: surcharge cannot be read (work order 129 C/D).
HYPER_ADVANCED_TECH_OFFSET = 640
HYPER_ADVANCED_TECH_COUNT = 8
