"""s_leader_data — VERIFIED spec, work order 167 (24 September 2026).

59 bytes, `MAX_LEADERS` = 67 of them, always on the wire
(ext_api.cpp:156-159) and in `GameState.leaders_raw`. Promoted out of
`core/structs/unverified.py`, where work order 154 had left it with six
of fifteen fields corroborated and two blockers that were about the
Fleets panel's officer path, not about the struct.

**SOURCE 1 — THE HEADER.** `src/game/orion2.h:1088-1104`, compiled with
its own `#pragma pack(1)`: every offset below is asserted by
`tools/struct_header_check.py` (this spec is in its COVERED list), and
`sizes.h` asserts `sizeof == 0x3b`. The member names here ARE the C++
names, which is what lets that tool generate the asserts. The save
serializer (`SAVEGAME::Write_Leader_`, savegame.cpp:479-495) writes the
same fifteen members in the same order at the same widths, so a `.GAM`
holds the 67 records at this stride too.

**SOURCE 2 — NUMBERS THAT CAN ONLY LAND IF THE OFFSET IS RIGHT.** Read
by `tools/leader_check.py` out of real data: thirteen `.GAM` files on
this disk (SAVE1-11 and the three secured fixtures), 871 records, each
array located by HERODATA.LBX's own 67 names at this stride:

  name @0, title @15   all 67 names at 59-byte steps in all 13 files
  type @35, pict_num @49   equal to HERODATA.LBX's own record on every
                       record of every file (the static fields)
  general_skills @38, special_skills @42, tech_application @46,
  skill_value @50      **skill_value equals `Officer_Skill_Value_`
                       (officer.cpp:105-155) recomputed from the other
                       three, 67 of 67, in nine files.** A wrong offset
                       for any of the four does not land on another
                       function's sum. The four files of ONE game
                       lineage (SAVE1 -> 3 -> 4 -> 5) agree on 35 of 67,
                       all four on the same 32 records by the same
                       deltas, with skills identical to HERODATA's — the
                       STORED value there came from a different
                       computation when that game was created, and the
                       engine never recomputes it (Init_Leaders_ is the
                       only writer, initgame.cpp:486). The screen prices
                       a leader from the stored value (officer.cpp:387),
                       so HD reads it and never recomputes.
  xp @36               unowned leaders only on 0/60/150/300/1000 — the
                       level steps of `Get_Officer_Base_Level_`
                       (officer.cpp:44-61); owned ones +1 each between
                       SAVE4 and SAVE5, which are one turn apart
  location @53, status @57, player_index @58, type @35
                       ship officers: every status-1 leader's location
                       is a ship whose `officer_index` @116 names that
                       leader back, and no other ship names one — six on
                       SAVE4 and SAVE5. Colony leaders: every status-1
                       leader's location is a star whose
                       `officer_index[player_index]` @187 names it back
                       in exactly that player's slot — two on SAVE4, one
                       on the natives fixture. Both directions.
  eta @55              status-4 leaders ("For Hire (%d)", 30 - eta)
                       in 1..29 everywhere, and +1 each from SAVE4 to
                       SAVE5 — `Decrement_Officer_ETA_` increments a
                       status-4 leader's eta every turn (officer.cpp:1732-1737)

`level` @52 is 0 in every record of every file AND in HERODATA.LBX, and
no line of the engine writes it (grep: only the save serializer and
loader touch `leader->level`); the hire popup's two button help texts
are its only readers (mainpups.cpp:893, :908). So its value is a
source fact, not a guess, but a zero confirms no offset — the header is
its only positional source, and it is declared here for that one
reader. `display_level_popup` @56 is 0 or 1 in every file.

**AND WHAT IS NOT IN THIS STRUCT, so nobody looks for it here:** the
level a leader is SHOWN at is computed from `xp` (and the owner's
WARLORD trait), the price from `skill_value`, the skill bonuses from
the static `_skill_data` table (mox.cpp:667-722) — all in
`core/leaderskills.py`.

Run `python tools/leader_check.py` to repeat the second source.
"""
from core.structs import Spec

SIZE = 59                   # sizes.h: ORION2RE_STATIC_SIZE_ASSERT 0x3b
COUNT = 67                  # MAX_LEADERS

#: `LEADER_TYPE_*` (orion2_consts.h): the ship officer and the colony
#: leader, and `_officer_scrn_type`'s two values.
TYPE_SHIP, TYPE_COLONY = 0, 1

#: `status` values the screen branches on (officer.cpp).
STATUS_DEAD = -2            # never counted as owned (:2060)
STATUS_NONE = -1            # nobody's (Deassign_Officer_, :307)
STATUS_POOL = 0             # "Officer Pool"
STATUS_ASSIGNED = 1         # at `location`, maybe still travelling (eta)
STATUS_LIMBO = 2            # "(Unassigned)", pool on leaving the screen
STATUS_FOR_HIRE = 4         # offered to the player, eta counts to 30
STATUS_MAROONED = 5         # a hero waiting at a star (:3418)

SPEC = Spec("s_leader_data", SIZE, [
    ("name",                 0, "str15"),
    ("title",               15, "str20"),
    ("type",                35, "u8"),
    ("xp",                  36, "i16"),
    ("general_skills",      38, "u32"),
    ("special_skills",      42, "u32"),
    ("tech_application",    46, "u8[3]"),
    ("pict_num",            49, "u8"),
    ("skill_value",         50, "i16"),
    ("level",               52, "u8"),
    ("location",            53, "i16"),
    ("eta",                 55, "i8"),
    ("display_level_popup", 56, "i8"),
    ("status",              57, "i8"),
    ("player_index",        58, "i8"),
], verified=True)


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    """Every record, with `.index` — the leader's id, which is what
    `_officer_id_list`, `ship.officer_index` and `star.officer_index`
    hold."""
    return SPEC.parse_all(raw_list)
