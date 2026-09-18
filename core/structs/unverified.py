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
  s_player.tech_applications @379 — see TECH_APPLICATIONS below; ONE of
                  its two sources is in, and it is the one that matters
                  less
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


#: s_player.tech_applications[TECH_APP_COUNT] — 212 bytes, the per
#: APPLICATION research status: 0 unavailable, 1 available to pick, 3
#: researched (`TECH_RESEARCH_STATUS`, orion2_consts.h:1321-1325). It is
#: what decides which CHOICE ROWS the research screen offers under each
#: category's field (`TECH::Init_Entry_Data_`, tech.cpp:602-624), so the
#: reconstruction in `core/researchlist.py` cannot be trusted further than
#: this offset can.
#:
#: SOURCE ONE, 18 September 2026 (work order 130 C): orion2re's own headers
#: compiled with their `#pragma pack(1)` put it at 379, 212 bytes wide, with
#: `sizeof(s_player) == 0xf0e` — the assert in sizes.h:21. It is a whole
#: `uint8_t[]` member and not a packed word, so the header route carries it
#: end to end (decision 23's own limit does not bite here).
#: `tools/struct_header_check.py` re-runs that compile on every suite.
#:
#: SOURCE TWO IS THE ONE THAT MATTERS and is not in: a live read whose
#: values agree with the rows the game's own screen draws. The header says
#: where the bytes are; only the screen says that these bytes mean "this
#: row is offered". Until that agrees, `core/researchlist.py` may be
#: reconstructed and validated against the FIELD_LIST, but the research
#: screen does not draw a list it cannot vouch for — it hands over to the
#: fallback view (work order 130 C and E).
#:
#: The same offset is in `core/structs/player.py` as
#: `TECH_APPLICATIONS_OFFSET`, where it is used as a live-read ANCHOR and
#: not as data. That is the only thing it may be used for from here.
TECH_APPLICATIONS_OFFSET = 379
TECH_APPLICATIONS_COUNT = 212
TECH_APPLICATION_STATUS_AVAILABLE = 1
