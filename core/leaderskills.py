"""Leaders: the skill table and the rules that turn a record into a row.

**TRANSCRIPTION, and a copy — so it has a checker.** `SKILLS` is
`MOX::_skill_data[54]` (mox.cpp:667-722), a literal in the engine that
is on no wire, and `SKILL_NAME_ESTRINGS` / `LEVEL_NAME_ESTRINGS` are the
ESTRINGS ids `Load_E_Strings_` hangs on it (estrings.cpp:215-294).
`tools/leader_skill_check.py` reads both files and the level steps in
officer.cpp and fails on any difference; the smoke test runs it. A hand
copy without that is the nebula sizes again.

The functions below are `OFFICER::` functions with the same arithmetic,
named after them. Nothing here imports pygame, so the verification tool
and the smoke test can use it without a window.

A leader record is anything with the `core/structs/leader.py` field
names — a `StructView`, or a plain object in a tool.
"""
from core.structs import leader as leader_struct

#: `s_skill_data.skill_type` (mox.h:5-14): who can have the skill.
GENERAL, SHIP_SPECIAL, COLONY_SPECIAL = 0, 1, 2

#: `MOX::_skill_data[54]`, mox.cpp:667-722:
#: (skill_id, skill_mask, skill_type, strength, level_up, cost, format).
#: Skills come in pairs — even id the plain one, odd id the starred one
#: — and the ICON is chosen by `id / 2` (officer.cpp:3776, :3812).
SKILLS = (
    (0, 0x1, 0, 20, 1, 2, "%d%%"),
    (1, 0x2, 0, 30, 1, 4, "%d%%"),
    (2, 0x4, 0, 20, 1, 0, "+%d"),
    (3, 0x8, 0, 30, 1, 0, "+%d"),
    (4, 0x10, 0, 100, 1, 1, "+%d%"),
    (5, 0x20, 0, 150, 1, 2, "+%d%"),
    (6, 0x1, 1, 20, 1, 3, "%d%%"),
    (7, 0x2, 1, 30, 1, 6, "%d%%"),
    (8, 0x1, 2, 100, 1, 2, "-%d%%"),
    (9, 0x2, 2, 150, 1, 4, "-%d%%"),
    (10, 0x40, 0, 600, 1, 2, "-%dBC"),
    (11, 0x80, 0, 900, 1, 4, "-%dBC"),
    (12, 0x4, 2, 100, 1, 3, "+%d%%"),
    (13, 0x8, 2, 150, 1, 6, "+%d%%"),
    (14, 0x4, 1, 50, 1, 3, "+%d"),
    (15, 0x8, 1, 75, 1, 6, "+%d"),
    (16, 0x10, 2, 100, 1, 3, "+%d%%"),
    (17, 0x20, 2, 150, 1, 6, "+%d%%"),
    (18, 0x10, 1, 50, 1, 2, "+%d"),
    (19, 0x20, 1, 75, 1, 4, "+%d"),
    (20, 0x40, 1, 50, 1, 4, "+%d"),
    (21, 0x80, 1, 75, 1, 8, "+%d"),
    (22, 0x40, 2, 10, 1, 1, "+%d"),
    (23, 0x80, 2, 15, 1, 2, "+%d"),
    (24, 0x100, 2, 100, 1, 3, "+%d%%"),
    (25, 0x200, 2, 150, 1, 6, "+%d%%"),
    (26, 0x400, 2, 100, 1, 2, "+%d%%"),
    (27, 0x800, 2, 150, 1, 4, "+%d%%"),
    (28, 0x100, 0, 100, 1, 1, "+10BC"),
    (29, 0x200, 0, 100, 1, 2, "+15BC"),
    (30, 0x100, 1, 10, 4, 1, "+%d"),
    (31, 0x200, 1, 10, 3, 2, "+%d"),
    (32, 0x400, 0, 20, 1, 2, "+%d"),
    (33, 0x800, 0, 30, 1, 4, "+%d"),
    (34, 0x400, 1, 50, 1, 3, "+%d"),
    (35, 0x800, 1, 75, 1, 6, "+%d"),
    (36, 0x1000, 0, 50, 1, 2, "+%d"),
    (37, 0x2000, 0, 75, 1, 4, "+%d"),
    (38, 0x1000, 2, 100, 1, 3, "+%d%%"),
    (39, 0x2000, 2, 150, 1, 6, "+%d%%"),
    (40, 0x1000, 1, 20, 1, 1, "+%d"),
    (41, 0x2000, 1, 30, 1, 2, "+%d"),
    (42, 0x4000, 2, 50, 1, 4, "+%d%%"),
    (43, 0x8000, 2, 75, 1, 8, "+%d%%"),
    (44, 0x4000, 0, 20, 1, 3, "+%d%%"),
    (45, 0x8000, 0, 30, 1, 6, "+%d%%"),
    (46, 0x10000, 2, 20, 1, 2, "+%d"),
    (47, 0x20000, 2, 30, 1, 4, "+%d"),
    (48, 0x10000, 0, 20, 1, 2, "+%d%%"),
    (49, 0x20000, 0, 30, 1, 4, "+%d%%"),
    (50, 0x40000, 0, 100, 1, 2, "+%d%%"),
    (51, 0x80000, 0, 150, 1, 4, "+%d%%"),
    (52, 0x4000, 1, 50, 1, 3, "+%d"),
    (53, 0x8000, 1, 75, 1, 6, "+%d"),
)
SKILL_COUNT = len(SKILLS)       # the loops' `< 54` / `< 0x36`

#: `MOX::_skill_data[i].name = ESTRINGS::E_Strings_(n)`,
#: estrings.cpp:215-268, in skill order. Two break the run: skill 4
#: (Diplomat, 0x26F) and skill 40 (Security, 0x2A0) reuse strings that
#: exist for other screens.
SKILL_NAME_ESTRINGS = (
    (0x2D4, 0x2D5, 0x2D6, 0x2D7, 0x26F)
    + tuple(range(0x2D8, 0x2FA + 1))
    + (0x2A0,)
    + tuple(range(0x2FB, 0x307 + 1)))

#: `_officer_level_names` (ship officers) and `_star_officer_level_names`
#: (colony leaders), estrings.cpp:280-294, level 0..5.
LEVEL_NAME_ESTRINGS = {
    leader_struct.TYPE_SHIP: tuple(range(0x308, 0x30D + 1)),
    leader_struct.TYPE_COLONY: tuple(range(0x30E, 0x313 + 1)),
}

#: `Get_Officer_Base_Level_` (officer.cpp:44-61): the xp at which levels
#: 1..5 start. Level 5 needs the owner's WARLORD trait as well.
LEVEL_STEPS = (60, 150, 300, 500, 1000)
MAX_LEVEL = 5

#: `TRAIT_WARLORD` (officer.cpp:93 "trait[30]"), an index into
#: `s_player.traits` — `core/structs/player.TRAITS_OFFSET`.
TRAIT_WARLORD = 30

#: The two leaders the rules single out by index. 65 is Loknar, whose
#: maintenance is always 0 (officer.cpp:424); 66 never gets the WARLORD
#: level (:88-89).
LOKNAR = 65
NO_WARLORD_LEADER = 66

#: Megawealth and Megawealth* (skills 28, 29): a leader who PAYS. Double
#: price, no maintenance (officer.cpp:392-395, :417-426, :2000-2003), and
#: their help box states 10 / 15 instead of a bonus (:1774-1778).
MEGAWEALTH = (28, 29)
MEGAWEALTH_HELP_VALUE = {28: 10, 29: 15}

#: Famous and Famous* (skills 10, 11): the best of the owner's famous
#: leaders knocks its bonus off every hiring price (officer.cpp:584-612).
FAMOUS = 10
SUPER_FAMOUS = 11

#: `Set_Officer_To_Player_` refuses a fifth of one type (officer.cpp:2073)
#: and the screen lists at most four (:2722): one number, two readers.
MAX_PER_TYPE = 4

#: The leaders the original lists as female, for the ", the" wording
#: (`Officer_Is_Female_`, officer.cpp:3053-3064).
FEMALE = frozenset((10, 22, 34, 37, 39, 60))

#: A status-4 leader leaves after 30 turns; the row says how many are
#: left (`0x1e - eta`, officer.cpp:3700-3704; :1735).
HIRE_WINDOW = 30


def skill(index):
    """`(id, mask, type, strength, level_up, cost, format)`."""
    return SKILLS[index]


def has_general(rec, index):
    """`Officer_Has_General_Skill_` (officer.cpp:225-227)."""
    return (SKILLS[index][1] & int(rec.general_skills)) != 0


def has_special(rec, index):
    """`Officer_Has_Special_Skill_` (officer.cpp:229-234)."""
    return (SKILLS[index][1] & int(rec.special_skills)) != 0


def base_level(xp, warlord):
    """`Get_Officer_Base_Level_` (officer.cpp:44-61)."""
    for level, step in enumerate(LEVEL_STEPS):
        if xp < step:
            return level
    return MAX_LEVEL if warlord else MAX_LEVEL - 1


def unowned_level(rec):
    """`Get_Officer_Level_` (officer.cpp:32-42) — no WARLORD, ever."""
    return min(base_level(int(rec.xp), False), MAX_LEVEL)


def owned_level(rec, index, warlord):
    """`Owned_Officer_Level_` (officer.cpp:82-103)."""
    if index == NO_WARLORD_LEADER:
        warlord = False
    return min(base_level(int(rec.xp), warlord), MAX_LEVEL)


def shown_level(rec, index, warlord_of):
    """The level a leader is named and paid at — `Leader_Name_`'s and
    `Officer_Skill_Bonus_`'s choice (officer.cpp:67-71, :3104-3108): the
    owned level for an owned leader, the plain one for nobody's.
    `warlord_of(player)` says whether that player has TRAIT_WARLORD."""
    player = int(rec.player_index)
    if player == -1:
        return unowned_level(rec)
    return owned_level(rec, index, bool(warlord_of(player)))


def skill_bonus(level, index):
    """`Officer_Skill_Bonus_` (officer.cpp:63-80): the number a skill row
    prints. Integer arithmetic on non-negative values, as the original."""
    _sid, _mask, _typ, strength, level_up, _cost, _fmt = SKILLS[index]
    steps = (level + 1 + level_up - 1) // level_up
    return (steps * strength) // 10


def c_format(fmt, value):
    """`snprintf(buf, fmt, value)` for the table's own formats.

    Every format in `SKILLS` is one `%d` with literal text round it, or
    no conversion at all ("+10BC"). `%%` is a percent sign; `+%d%` —
    skills 4 and 5 — ends in a lone `%`, and glibc's `snprintf` prints
    nothing for it: MEASURED on this machine, `snprintf(b, 40, "+%d%",
    1)` gives `[+1]` (work order 167). The engine runs on that library,
    so "+1" is what the original prints for Diplomat at level 0.
    Transcribed rather than tidied.
    """
    out, i = [], 0
    while i < len(fmt):
        ch = fmt[i]
        if ch == "%" and i + 1 < len(fmt):
            nxt = fmt[i + 1]
            if nxt == "%":
                out.append("%")
            elif nxt == "d":
                out.append(str(int(value)))
            else:
                out.append(ch + nxt)
            i += 2
            continue
        if ch == "%":
            i += 1          # a lone trailing '%' prints nothing
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def displayed_skills(rec):
    """The skill ids a row lists, in the original's order.

    `Print_Officer_Data_` walks all 54 ids twice (officer.cpp:3760-3837):
    first the SPECIAL skills of the leader's own type (ship officer ->
    type 1, colony leader -> type 2), then the GENERAL skills (type 0).
    The same order `Add_Skill_Description_Help_Fields_` builds the help
    fields in (:3906-3968), which is why a right click on the n-th line
    reaches the n-th skill.
    """
    want = (SHIP_SPECIAL if int(rec.type) == leader_struct.TYPE_SHIP
            else COLONY_SPECIAL)
    special = [s[0] for s in SKILLS if s[2] == want and has_special(rec, s[0])]
    general = [s[0] for s in SKILLS if s[2] == GENERAL and has_general(rec, s[0])]
    return special + general


def famous_bonus(leaders, player, warlord_of):
    """`Bonus_For_Famous_Heroes_` (officer.cpp:584-612).

    Transcribed with its one oddity: `current_skill_bonus` is declared
    outside the loop and never reset, so a leader with neither skill
    re-offers the previous leader's bonus. Taking the maximum makes that
    harmless, and it is kept rather than tidied so the two cannot drift.
    """
    best, current = 0, 0
    for idx, rec in enumerate(leaders):
        if int(rec.player_index) != player:
            continue
        if int(rec.status) not in (leader_struct.STATUS_POOL,
                                   leader_struct.STATUS_ASSIGNED):
            continue
        level = shown_level(rec, idx, warlord_of)
        if has_general(rec, FAMOUS):
            current = skill_bonus(level, FAMOUS)
        elif has_general(rec, SUPER_FAMOUS):
            current = skill_bonus(level, SUPER_FAMOUS)
        best = max(best, current)
    return best


def hire_cost(leaders, index, player, warlord_of):
    """`Officer_Cost_` (officer.cpp:383-404).

    NOTE the level: `Get_Officer_Level_`, the UNOWNED one, whoever owns
    the leader — the price never sees WARLORD. And the value is the
    STORED `skill_value` (see `core/structs/leader.py` for why HD never
    recomputes it).
    """
    rec = leaders[index]
    multiplier = unowned_level(rec) + 1
    base = int(rec.skill_value) * multiplier
    total = base * (20 if any(has_general(rec, s) for s in MEGAWEALTH)
                    else 10)
    final = total - famous_bonus(leaders, player, warlord_of)
    return final if final >= 1 else 0


def maintenance(leaders, index, player, warlord_of):
    """`Officer_Maintenance_` (officer.cpp:412-434), with
    `Get_Officer_Costs_`'s override (:2000-2003) folded in — the two
    always travel together on this screen."""
    rec = leaders[index]
    cost = hire_cost(leaders, index, player, warlord_of)
    if index == LOKNAR or any(has_general(rec, s) for s in MEGAWEALTH):
        return 0
    return max(1, (cost + 99) // 100)


def captain_id_list(leaders, player, view_type):
    """`Build_Captain_Id_List_` (officer.cpp:2705-2730): the leaders one
    view lists, in index order, at most four.

    `status >= 0 || status == 4` is the original's own test and the
    second half can never add anything; it is kept so the comparison
    with the source is a line-for-line read.
    """
    out = []
    for idx, rec in enumerate(leaders):
        status = int(rec.status)
        valid = status >= 0 or status == leader_struct.STATUS_FOR_HIRE
        if (valid and int(rec.player_index) == player
                and int(rec.type) == view_type):
            out.append(idx)
            if len(out) >= MAX_PER_TYPE:
                break
    return out


def leaders_for_hire(leaders, player, view_type):
    """`Leaders_In_Hiring_Pool_` (officer.cpp:1951-1973): does HIRE
    exist in this view."""
    return any(int(r.type) == view_type
               and int(r.status) == leader_struct.STATUS_FOR_HIRE
               and int(r.player_index) == player
               for r in leaders)


def can_be_assigned(rec):
    """`Leader_Can_Be_Assigned_` (officer.cpp:1514-1522)."""
    return int(rec.status) in (leader_struct.STATUS_POOL,
                               leader_struct.STATUS_ASSIGNED,
                               leader_struct.STATUS_LIMBO)


def level_name_estring(rec, level):
    """The ESTRINGS id of the title a leader is named with."""
    return LEVEL_NAME_ESTRINGS[int(rec.type)][level]


def the_word_hestring(index):
    """`Leader_Name_`'s ", the" (officer.cpp:3129-3141): HESTRNGS 0x182
    for the leaders the original lists as female, 0x110 for the rest.

    Transcribed for the English, German and Spanish paths. French picks
    0x186 before a vowel and Italian runs `Get_Italian_The_`
    (:3507-3530); both are languages this tree does not ship strings for.
    """
    return 0x182 if index in FEMALE else 0x110


def leader_name(rec, level_title, the_word=None):
    """`Leader_Name_` (officer.cpp:3099-3147): "<level title> <name>",
    and with `the_word` given and a title present, the title after it."""
    text = f"{level_title} {rec.name}"
    if the_word is not None and rec.title:
        text += the_word + rec.title
    return text


def research_cost_value(cost):
    """`Get_Research_Cost_Skill_Value_` (officer.cpp:236-246)."""
    if cost < 1000:
        return 1
    return 4 if cost >= 5000 else 3


def skill_value(rec, app_field, field_cost):
    """`Officer_Skill_Value_` (officer.cpp:105-155) — **FOR VERIFICATION
    ONLY.** The engine runs it once per leader at game creation
    (initgame.cpp:486) and stores the result; the screen reads the
    stored value. `tools/leader_check.py` recomputes it to prove the
    offsets of the four fields it reads (see core/structs/leader.py).

    `app_field(app)` is the application's field or None/-1;
    `field_cost(field)` its research cost.
    """
    kind = int(rec.type)
    total = 0
    for sid, _mask, styp, _st, _lu, cost, _fmt in SKILLS:
        if styp == GENERAL and has_general(rec, sid):
            value = cost
            if sid in (2, 3):
                value += 3 if kind == leader_struct.TYPE_SHIP else 1
                if sid == 3:
                    value += 3 if kind == leader_struct.TYPE_SHIP else 1
            total += value
        if kind == leader_struct.TYPE_SHIP:
            if styp == SHIP_SPECIAL and has_special(rec, sid):
                total += cost
        elif kind == leader_struct.TYPE_COLONY:
            if styp == COLONY_SPECIAL and has_special(rec, sid):
                total += cost
    for app in list(rec.tech_application)[:3]:
        if app:
            field = app_field(app)
            if field is None or field <= -1:
                total = 1       # the original's own reset (:145-147)
            else:
                total += research_cost_value(field_cost(field))
    return total
