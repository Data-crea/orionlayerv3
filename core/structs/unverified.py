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
  s_leader_data -> core/structs/leader.py   (24 Sep 2026, work order
                   167; header route plus tools/leader_check.py)

The old s_planet_data guess that used to sit here had `star_index`
at offset 0 and an invented `position` at 2. Both were wrong: the
real first member is `colony_index`. Kept as a note because it is
exactly the kind of plausible-looking guess this file exists to
quarantine.

Still needed, still unverified:
  s_player.hyper_advanced_tech @640 — see HYPER_ADVANCED_TECH below
  (s_player.tech_applications @379 was promoted 22 September 2026 —
                  work order 165 part A; see the note further down)
"""
from core.structs import Spec

#: s_leader_data — **PROMOTED 24 September 2026, work order 167**, to
#: `core/structs/leader.py`, where both sources are written out: the
#: header route (now in `tools/struct_header_check.py`'s COVERED list)
#: and `tools/leader_check.py`'s numbers out of fourteen saves — the
#: stored skill_value against `Officer_Skill_Value_` recomputed, and the
#: ship and star officer links in both directions.
#:
#: What work order 154 recorded here is worth one line more, because
#: its two blockers were about the FLEETS PANEL's officer path (Beam
#: OCV/DCV) and not about the struct, which is why they did not have to
#: be lifted for this promotion. One reading differs and is stated
#: rather than smoothed over: 154 counted one officered ship each in
#: SAVE1, 3, 4 and 5; `tools/leader_check.py` finds SIX ships with an
#: officer on SAVE4 and SAVE5, across all owners — one of them the
#: player's (Slith on ship 13), which is the count 154's sentence fits.
#: The Beam line itself is still dropped; lifting it is its own work.


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


#: s_player.tech_applications @379 — **PROMOTED 22 September 2026**,
#: work order 165 part A, when its second source came in. It lives in
#: `core/structs/player.py` now, in the SPEC, with both sources written
#: out beside it.
#:
#: What the second source turned out to be is worth leaving here,
#: because this file had recorded the opposite: it was NOT a reading of
#: the game's own screen. Three agreements in one read-only snapshot did
#: it instead — every one of the 212 bytes a TECH_RESEARCH_STATUS, all
#: 52 researched applications backed by a researched field in the
#: VERIFIED `tech_fields`, and the application `current_research_
#: application` names as in progress reading "available" rather than
#: "researched". The claim the screen alone can settle — that status 1
#: means the row APPEARS — is still what
#: `researchlist.validate_against_fields` tests on every entry.
