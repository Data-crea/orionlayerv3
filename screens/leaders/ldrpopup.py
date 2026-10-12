"""The hire popup, as the Leaders screen opens it — recognised and described.

`OFFICER::Ask_For_Hire_` (officer.cpp:443-481) formats the question and
hands it to `Hire_Officer_Popup_` (:3391-3400), which runs
`MAINPUPS::Random_New_Officer_Popup_` (mainpups.cpp:784-930) with
`_on_officer_screen_flag` set. The game keeps reporting screen 29 the
whole time; the field list is the popup's own (`Eric_Push_Fields_`
re-bases it, mainpups.cpp:1728 via :240-243).

GEOMETRY, all of it the source's (mainpups.cpp:107-110, :1721-1778):
the popup art is MAINPUPS.LBX 0x39 and `Get_Picture_Draw_XY_` centres
it on (0x140, 0xF0) by ITS OWN size — the original reads the art, so
the art's header size (306 x 266) is the source here, the argument
`ldrgeom` makes for the buttons. REJECT is `Add_Button_Field_(g_x +
0x2C, g_y + 0xE2, …, MAINPUPS 0x3A, E_Strings(0x1B4) = "r")`, HIRE the
same at `g_x + 0xAF` with 0x3B and "h" (0x13C); a button field stores
its hotkey upper-cased (fields.cpp:378-381). Up to five hidden help
fields follow, one per skill line, from `(g_x + 0x61, g_y + 0x36)`
(`Wrapper_To_Add_Officer_Popup_Help_Fields_`, officer.cpp:3875-3887).

WHO IS OFFERED. Only a leader of the player's who is FOR HIRE reaches
the popup: `Do_Hire_Officer_` answers anyone else with a message
(officer.cpp:492-501). With open fix 30's block the leader comes off the
wire (`popup_leader`). Without it the popup is identified by what the
list shows — its skill help fields' exact rectangles, which depend on
how many SPECIAL and how many GENERAL skills the leader shows (the two
loops make different rectangles, `ldrgeom.skill_help_rects`) — and ONLY
when exactly one candidate fits.
Anything else is `leader = None`, and the screen shows the game's own
pixels for the popup (the `core/gamebox` limitation) rather than a
leader it guessed.
"""
from core import leaderskills as ls
from core import livefields
from core.structs import leader as leader_struct

#: MAINPUPS.LBX 0x39's size, which `Get_Picture_Draw_XY_` centres by.
POPUP_SIZE = (306, 266)
ORIGIN = (0x140 - POPUP_SIZE[0] // 2, 0xF0 - POPUP_SIZE[1] // 2)  # (167, 107)
#: MAINPUPS.LBX 0x3A and 0x3B, REJECT and HIRE.
REJECT_SIZE, HIRE_SIZE = (92, 27), (85, 27)
TYPE_BUTTON, TYPE_HIDDEN = 0, 7


def _button(dx, size):
    x, y = ORIGIN[0] + dx, ORIGIN[1] + 0xE2
    return (x, y, x + size[0] - 1, y + size[1] - 1)


REJECT_RECT = _button(0x2C, REJECT_SIZE)        # (211, 333, 302, 359)
HIRE_RECT = _button(0xAF, HIRE_SIZE)            # (342, 333, 426, 359)
REJECT_KEY, HIRE_KEY = ord("R"), ord("H")

#: `Print_Officer_Data_(-1, id, g_x + 0x5F, g_y + 0x35 + 5, g_x + 10,
#: g_y + 0x35 + 2, 0x50, 0x5A, 0xC3, 0xE)` (officer.cpp:3542-3546): in
#: the popup only the SKILL lines are printed (`_offscrn_ask_for_hire_
#: popup` suppresses the name, the cost column and the status line,
#: :3624, :3636, :3712) and they start at text_y itself (:3750-3752).
TEXT_X = ORIGIN[0] + 0x5F
TEXT_Y = ORIGIN[1] + 0x35 + 5
RIGHT_COLUMN = 0xC3
#: The portrait, `animate::Draw_(g_x + 0x0D, g_y + 0x37, …)`
#: (mainpups.cpp:1837).
PORTRAIT_AT = (ORIGIN[0] + 0x0D, ORIGIN[1] + 0x37)
#: The title — `Leader_Name_(id, 1)` — and the question, both centred
#: paragraphs (mainpups.cpp:1841-1846, :1909-1914):
TITLE_RECT = (ORIGIN[0] + 0x0B, ORIGIN[1] + 0x0C, 0x11D, 0x21)
MESSAGE_RECT = (ORIGIN[0] + 0x0E, ORIGIN[1] + 0x95, 0x119, 0x3E)
#: The skill help fields' column (officer.cpp:3881-3886, :3928-3937).
SKILL_HELP_X = ORIGIN[0] + 0x61
SKILL_HELP_TOP = ORIGIN[1] + 0x35 + 1
SKILL_HELP_W = 0xBE
SKILL_STEP = 0x11
SKILL_HELP_MAX = 5


def skill_help_rects(rec):
    """The popup's help fields for leader `rec`, as the engine adds them
    (`ldrgeom.skill_help_rects` at the popup's column)."""
    from . import ldrgeom
    special, general = split_skills(rec)
    return ldrgeom.skill_help_rects(SKILL_HELP_X, SKILL_HELP_TOP,
                                    len(special), len(general))


def split_skills(rec):
    """`(special, general)` displayed skill ids, in display order."""
    shown = ls.displayed_skills(rec)
    general = [s for s in shown if ls.SKILLS[s][2] == ls.GENERAL]
    return [s for s in shown if s not in general], general


def _in_column(f):
    return (f.field_type == TYPE_HIDDEN and f.x == SKILL_HELP_X
            and f.x_end == SKILL_HELP_X + SKILL_HELP_W
            and SKILL_HELP_TOP - 1 <= f.y
            <= SKILL_HELP_TOP + SKILL_HELP_MAX * SKILL_STEP)


def popup_rect():
    """The popup's native rectangle, inclusive."""
    x, y = ORIGIN
    return (x, y, x + POPUP_SIZE[0] - 1, y + POPUP_SIZE[1] - 1)


class Popup:
    """A recognised hire popup: its answers, and its leader if known."""

    def __init__(self, reject, hire, leader, skill_fields):
        self.reject = reject            # live FieldInfo
        self.hire = hire                # live FieldInfo, or None
        self.leader = leader            # leader id, or None
        self.skill_fields = skill_fields  # live help fields, top down

    @property
    def identified(self):
        return self.leader is not None


def detect(fields, view):
    """The popup the live list IS, or None."""
    reject = next((f for f in fields if livefields.rect(f) == REJECT_RECT
                   and f.field_type == TYPE_BUTTON), None)
    if reject is None:
        return None
    hire = next((f for f in fields if livefields.rect(f) == HIRE_RECT
                 and f.field_type == TYPE_BUTTON), None)
    skills = sorted((f for f in fields if _in_column(f)),
                    key=lambda f: f.y)
    return Popup(reject, hire, _leader(view, skills), skills)


def _leader(view, skill_fields):
    """The offered leader: the block's, or the ONE candidate whose own
    help-field rectangles are exactly the ones on the wire."""
    block = view.block
    if block is not None and int(block.get("popup_leader", -1)) >= 0:
        return int(block["popup_leader"])
    live = [livefields.rect(f) for f in skill_fields]
    fits = [idx for idx, rec in enumerate(view.leaders)
            if int(rec.player_index) == view.player
            and int(rec.status) == leader_struct.STATUS_FOR_HIRE
            and skill_help_rects(rec) == live]
    return fits[0] if len(fits) == 1 else None


def question(view, leader, hstrings, level_title, the_word):
    """The question `Ask_For_Hire_` puts (officer.cpp:449-461), or None.

    HESTRNGS 0x124 when the upkeep is exactly 1, else 0x125, formatted
    with `Leader_Name_(id, 1)`, the hiring cost and the upkeep — both
    `Get_Officer_Costs_` (:1993-2004), recomputed here from the stored
    skill_value exactly as the engine computes them.
    """
    if hstrings is None or leader is None:
        return None
    cost = ls.hire_cost(view.leaders, leader, view.player,
                        view._warlord_of)
    upkeep = ls.maintenance(view.leaders, leader, view.player,
                            view._warlord_of)
    template = hstrings.message(0x124 if upkeep == 1 else 0x125)
    if not template:
        return None
    from core.hestrings import printf
    name = ls.leader_name(view.leaders[leader], level_title, the_word)
    return printf(template, name, cost, upkeep)
