"""What one leader row SAYS — the words and numbers, before any pixel.

`OFFICER::Print_Officer_Data_` (officer.cpp:3578-3838) draws a row in
four parts, and `Row` carries exactly those four, as data:

  the name        `Leader_Name_(id, 0)`: level title, space, name
                  (:3624-3634, :3099-3147)
  the cost        two lines right of the name. A leader FOR HIRE:
                  "%d BC" right-aligned, and HESTR 0x108 "to hire" under
                  it, right-aligned too. Anyone else: the upkeep "%d BC"
                  — or HESTR 0x10A "no" when it is 0 — printed LEFT-
                  aligned at the x where the label HESTR 0x109 "maint"
                  starts, and the label under it (:3636-3675). The two
                  alignments differ in the original and are kept apart.
  the status      under the portrait (:3677-3738): 0 "Officer Pool"
                  (0x10B), 2 "(Unassigned)" (0x10C), 1 the ship's or the
                  star's NAME, 4 "For Hire (%d)" (0x10D) with 30 - eta in
                  RED; and "ETA: %d" (0x12F) over the portrait while a
                  status-1 leader is still travelling (:3742-3745)
  the skills      special skills of the leader's type, then general ones
                  (`leaderskills.displayed_skills`), each icon, name and
                  bonus formatted with the table's own format

The unit after a number is `Get_Monetary_Unit_String_` — "BC", "MC" in
German (harold.cpp:1188-1203). Nothing here imports pygame.
"""
from core import leaderskills as ls
from core.hestrings import printf
from core.structs import leader as leader_struct

#: HESTRNGS ids, each at the line that prints it (officer.cpp).
H_TO_HIRE, H_MAINT, H_NO = 0x108, 0x109, 0x10A      # :3641, :3657, :3661
H_POOL, H_UNASSIGNED = 0x10B, 0x10C                  # :3681, :3684
H_FOR_HIRE = 0x10D                                   # :3703
H_ETA = 0x12F                                        # :3084
#: The strips under the view box: "%s (%s, %d turn[s])" while a
#: leader is travelling there (officer.cpp:716-721, :820-821).
H_STRIP_ETA1, H_STRIP_ETAN = 0x92, 0x93

#: `Get_Monetary_Unit_String_` (harold.cpp:1188-1203).
UNIT = {"de": "MC"}
UNIT_DEFAULT = "BC"


def the_word(words, index):
    """`Leader_Name_`'s ", the " for leader `index`, or None — HESTRNGS
    0x110 / 0x182 AS THE FILE HAS THEM, trailing space included.

    Until work order 175 the shared extraction stripped that space and
    this function put it back (167's parked item X, a workaround marked
    to expire); the extractor keeps the bytes now (format 2), so the
    string is used as it is.
    """
    return words.hstring(ls.the_word_hestring(index))


class Row:
    """One listed leader, as words and flags. See the module docstring."""

    __slots__ = ("slot", "index", "rec", "name", "cost_value", "cost_label",
                 "cost_align", "status", "status_red", "eta", "dark",
                 "skills", "special_count", "general_count", "level")

    def __init__(self, **kw):
        for key in self.__slots__:
            setattr(self, key, kw.get(key))


class Words:
    """The two string tables a row needs, and how to say a missing one."""

    def __init__(self, estrings=None, hstrings=None, language="en"):
        self.e = estrings if estrings is not None and \
            getattr(estrings, "state", None) == "ok" else None
        self.h = hstrings if hstrings is not None and \
            getattr(hstrings, "state", None) == "ok" else None
        self.unit = UNIT.get(language, UNIT_DEFAULT)

    def estring(self, index):
        return self.e.string(index) if self.e is not None else None

    def hstring(self, index):
        return self.h.message(index) if self.h is not None else None


def location_name(rec, game_state):
    """A status-1 leader's ship or star name (officer.cpp:3688-3692)."""
    loc = int(rec.location)
    if loc < 0:
        return ""
    if int(rec.type) == leader_struct.TYPE_SHIP:
        ships = getattr(game_state, "ships_raw", None) or []
        if loc < len(ships):
            from core.structs import ship as ship_struct
            return ship_struct.SPEC.parse(ships[loc]).name
        return ""
    stars = getattr(game_state, "stars", None) or []
    return stars[loc].name if loc < len(stars) else ""


def build(view, game_state, words, warlord_of):
    """`[Row]` for the leaders `view` lists, in its order."""
    out = []
    for slot, idx, rec in view.listed():
        out.append(row(slot, idx, rec, view, game_state, words, warlord_of))
    return out


def row(slot, idx, rec, view, game_state, words, warlord_of):
    level = ls.shown_level(rec, idx, warlord_of)
    title = words.estring(ls.level_name_estring(rec, level))
    name = ls.leader_name(rec, title) if title else str(rec.name)
    status = int(rec.status)
    cost = ls.hire_cost(view.leaders, idx, view.player, warlord_of)
    upkeep = ls.maintenance(view.leaders, idx, view.player, warlord_of)
    if status == leader_struct.STATUS_FOR_HIRE:
        cost_value = f"{cost} {words.unit}"
        cost_label = words.hstring(H_TO_HIRE) or ""
        align = "right"
    else:
        cost_value = (words.hstring(H_NO) or "") if upkeep == 0 \
            else f"{upkeep} {words.unit}"
        cost_label = words.hstring(H_MAINT) or ""
        align = "label_left"
    status_text, red = "", False
    if status == leader_struct.STATUS_POOL:
        status_text = words.hstring(H_POOL) or ""
    elif status == leader_struct.STATUS_LIMBO:
        status_text = words.hstring(H_UNASSIGNED) or ""
    elif status == leader_struct.STATUS_ASSIGNED:
        status_text = location_name(rec, game_state)
    elif status == leader_struct.STATUS_FOR_HIRE:
        template = words.hstring(H_FOR_HIRE)
        status_text = printf(template, ls.HIRE_WINDOW - int(rec.eta)) \
            if template else ""
        red = True
    eta = None
    if int(rec.eta) > 0 and status == leader_struct.STATUS_ASSIGNED:
        template = words.hstring(H_ETA)
        eta = printf(template, int(rec.eta)) if template else None
    shown = ls.displayed_skills(rec)
    skills = []
    for sid in shown:
        name_id = ls.SKILL_NAME_ESTRINGS[sid]
        value = ls.c_format(ls.SKILLS[sid][6], ls.skill_bonus(level, sid))
        skills.append((sid, words.estring(name_id) or "", value))
    general = sum(1 for s in shown if ls.SKILLS[s][2] == ls.GENERAL)
    return Row(slot=slot, index=idx, rec=rec, name=name, level=level,
               cost_value=cost_value, cost_label=cost_label,
               cost_align=align, status=status_text, status_red=red,
               eta=eta,
               # the darkened portrait while travelling or for hire
               # (officer.cpp:634-638)
               dark=int(rec.eta) > 0 or status == leader_struct.STATUS_FOR_HIRE,
               skills=skills, special_count=len(shown) - general,
               general_count=general)


def skill_help_text(rec, idx, skill_id, level, words, skilldesc, the_word):
    """`(title, body)` of a skill's help box, or None.

    `Print_Officer_Skill_Help_` (officer.cpp:1761-1792): the leader's
    name WITH its title, then "," when the title exists (not in
    Italian), into the description with the bonus — 10 and 15 for the
    two Megawealth skills. The title is the SKILDESC name with `_` as
    spaces. A display-only box: it changes nothing in the game.
    """
    if skilldesc is None or getattr(skilldesc, "state", None) != "ok":
        return None
    title_word = words.estring(ls.level_name_estring(rec, level))
    who = ls.leader_name(rec, title_word or "", the_word)
    if rec.title:
        who += ","
    value = ls.MEGAWEALTH_HELP_VALUE.get(
        skill_id, ls.skill_bonus(level, skill_id))
    body = printf(skilldesc.description(skill_id) or "", who, value)
    return skilldesc.title(skill_id), body
