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
  (s_player.tech_applications @379 was promoted 22 September 2026 —
                  work order 165 part A; see the note further down)
"""
from core.structs import Spec

#: s_leader_data: 59 bytes. **STILL UNVERIFIED, AND THE REASON IS NO
#: LONGER "nobody has looked"** — 20 September 2026, the attempt is
#: written down here so the next one starts where this one stopped.
#:
#: THE LAYOUT, from orion2re's own header compiled with its
#: `#pragma pack(1)` (orion2.h:1088-1104), and `sizes.h:28` asserts
#: `sizeof == 0x3b`, which the field offsets below add up to:
#:
#:     name[15]              0      pict_num             49
#:     title[20]            15      skill_value (i16)    50
#:     type (u8)            35      level (u8)           52
#:     xp (i16)             36      location (i16)       53
#:     general_skills (u32) 38      eta (i8)             55
#:     special_skills (u32) 42      display_level_popup  56
#:     tech_application[3]  46      status (i8)          57
#:                                  player_index (i8)    58
#:
#: WHAT A LIVE READING OF ALL 67 RECORDS AGREES WITH (struct_probe
#: `leaders`, one client, 20 September 2026). Six of the fifteen
#: fields corroborate, and two of those numerically:
#:
#:   * `name` @0 and `title` @15 — 67 plausible names and titles, none
#:     straddling its neighbour;
#:   * `type` @35 against the TITLE, on all 67: 0 for "Fighter Ace",
#:     "Rebel Pilot", "Legendary Pilot", "Pirate Captain"; 1 for
#:     "Science Leader", "Noble", "Planetologist", "High Priestess".
#:     No counter-example;
#:   * `special_skills` @42 against the title, semantically: "Weapons
#:     Officer" is exactly 0x4000 (LEADER_SHIP_SKILL_WEAPONRY),
#:     "Trilarian Navigator" is HELMSMAN|WEAPONRY, "Legendary Pilot"
#:     HELMSMAN2, "Master Tactician" HELMSMAN;
#:   * **`xp` @36 NUMERICALLY**, which is the strongest of them: the
#:     only values in 67 records are 0, 60, 150, 300 and 1000, and
#:     `OFFICER::Get_Officer_Base_Level_` (officer.cpp:44-61) steps at
#:     exactly 60, 150, 300, 500 and 1000. A wrong offset does not land
#:     on another function's thresholds;
#:   * `player_index` @58 — only -1 and 0..4 on a five-player game.
#:
#: **WHY THAT IS STILL NOT VERIFIED.** `level` @52 is 0 in all 67 and
#: `location` @53 is -1 in 65 of them, so neither is corroborated by
#: anything; `general_skills`, `tech_application`, `pict_num`,
#: `skill_value`, `eta`, `display_level_popup` and `status` have no
#: ground truth at all in this reading.
#:
#: **AND THE FIELD THAT MATTERS CANNOT BE EXERCISED.** The reason to
#: want this struct is the Fleets panel's Beam OCV/DCV, which reaches
#: it through `s_ship_data.officer_index`. On the loaded save, 0 of
#: 21 ships carries an officer. Across ALL TEN saves on this disk —
#: read from the files, nothing loaded — only SAVE1, SAVE3, SAVE4 and
#: SAVE5 have one at all, and each has exactly one: **4 ships of 185**.
#: That is the shape of the damaged-special check that "held on all 60
#: ships and proved nothing" (decision 23, fundament 64).
#:
#: WHAT WOULD FINISH IT: a save where several ships carry officers,
#: AND a way to read the number the game itself prints for one of
#: them. The second is the harder half — the game prints that panel
#: only for `_scanned_big_ship`, which it sets from its OWN cursor,
#: and the Extension API has no mouse motion (open fixes 3 and 4). A
#: click would set it, at the cost of toggling that ship's selection.
LEADER = Spec("s_leader_data", 59, [], verified=False,
              note="layout from the header and sizes.h; six fields "
                   "corroborated live on 67 records, xp numerically; "
                   "the officer_index path is vacuous — 4 ships of 185 "
                   "across all ten saves carry an officer")


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
