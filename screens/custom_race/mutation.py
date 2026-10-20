"""The evolutionary mutation in HD — the Custom Race screen's mutation mode
(open fix 107, work order 318).

When the player researches Evolutionary Mutation, `Setup_Evolutionary_
Upgrade` (raceopt.cpp:188-211, from report.cpp:537) opens
`Evolutionary_Mutation_Screen` (:213-420): the Custom Race screen in
mutation mode, where the race spends the new picks. raceopt.cpp's lines
here are v2.0.0's (`core/mutationwire.py`). With open fix 107 the engine
reports id 83 and TPOP kind 23 for it; the Custom Race screen claims 83
and draws itself from the tail (`EXTRA_SCREEN_IDS`). Without the fix the
screen runs under the galaxy map's 0 and the F12 notice stands, as before.

**EVERY NUMBER IS THE ENGINE'S, HD DECIDES NOTHING.** The picks and the
score, which level of each group and which special ability is chosen,
which options the screen offers: all off the tail, every snapshot. A
click sends the field the original takes — group g's level l is
`group_button[g * 4 + l]` (:287-331), a special ability `option_button[i]`
(:333-376), ACCEPT `accept` (:378-390) — and nothing else; HD keeps no
selection of its own and computes no cost.

TRANSCRIPTION `mutation_view` (raceopt.cpp:680-934, `Draw_Racial_Option_
Screen`): every group, the government and every special ability drawn,
the chosen ones marked; an option the screen does not offer (no field,
:1219-1234, :1262-1306) drawn dimmed and not clickable; the Lithovore's
block on Farming dimmed (:756-758) but still answered: its click goes and
the engine refuses it with KEN 73 (:292-299). The picks and the score
(`(picks + 10) * 10` %, :705-713) in the bar. No CLEAR, no race name, no
key: `Add_Race_Options_Fields_EM` adds none (:1189-1191).

TRANSCRIPTION `mutation_refusals`: the opening text (KEN 77 + 78,
:269-273) and the refusals — Farming under Lithovore (KEN 73, :293), the
negative limit (KEN 74, :310, :345), ACCEPT with picks below zero (KEN
75, :380) — are the engine's own boxes, MSGB on the wire, so HD's message
box draws them over this view (`core.overlays`); HD tests nothing before
it sends (unlike Custom Race's ACCEPT, [custom_race.accept_guard]).

DEVIATION `mutation_dim`: original = an offered option the picks cannot
pay now, or one that would pass the negative limit, is greyed too
(:739-753, :884-897) ; HD = only what the screen does not offer is
dimmed; a click on such an option goes to the engine, which refuses it
with KEN 74 or takes it and refuses ACCEPT with KEN 75.

HD STATE `mutation_look`: the Custom Race screen's three columns, labels
from `traits.json` and the description column, in place of RACEOPT.LBX 4
and RACESTUF.LBX's strings (:474, :439) — the same deviation as the
Custom Race screen ([custom_race.screen]); the title plate says
"Evolutionary Mutation". The government column: the original draws the
off button at every government, the chosen one too (no government has a
field here, :815-826), and lights only the chosen one's text (:832-835);
HD marks the chosen one with its lit radio, the others dimmed.

UNVERIFIED `mutation_live`: drawn and answered from the committed
stand-in only (check 090zzzzz) — no live run (Data's decision of 20
October 2026). A live run must show id 83 with TPOP 23 and its 186-byte
tail as `core.mutationwire.build` writes it, a pick moving the tail, a
refusal box over this view, ACCEPT ending it with the race's traits as the
engine's — and no F12-notice frame between the view and the map:
`TurnPopupGuard::end()` restores the view and then the reported id in one
call with no tick between (ext_api.cpp, `TurnPopupGuard::end`), so no snapshot should
carry 83 without TPOP 23.
"""
import logging

from core import mutationwire
from screens.custom_race import governments

log = logging.getLogger("custom_race")

GAME_SCREEN_ID = 83
TYPE_BUTTON, TYPE_HIDDEN = 0, 7
TITLE = "Evolutionary Mutation"

#: `primary_pick_traits` (raceopt_config.cpp:48-58): group g is trait g + 1.
PRIMARY_TRAITS = tuple(range(1, 10))
#: `e_primary_choice` (raceopt.h): a level's position — penalty, bonus,
#: major bonus — keyed by the value `traits.json` gives it.
LEVEL_OF_VALUE = {-1: 1, 1: 2, 2: 3}
#: `selectable_governments` (raceopt_config.cpp:60-65): button_variable[9]
#: indexes this.
GOVERNMENT_PICKS = (governments.GOVERNMENTS["Feudal"],
                    governments.GOVERNMENTS["Dictatorship"],
                    governments.GOVERNMENTS["Democracy"],
                    governments.GOVERNMENTS["Unification"])
#: `special_pick_identities` (raceopt_config.cpp:67-90): special ability i
#: as (trait, selected value) — Rich and Poor Home World share trait 15.
SPECIALS = ((10, 1), (11, 1), (12, 1), (13, 1), (14, 1), (15, 1), (15, -1),
            (16, 1), (17, 1), (18, 1), (19, 1), (20, 1), (21, 1), (22, 1),
            (23, 1), (24, 1), (25, 1), (26, 1), (27, 1), (28, 1), (29, 1),
            (30, 1))
#: `SPECIAL_PICK_LITHOVORE` (raceopt.h) and Farming's trait.
LITHOVORE, FARMING = 9, 2

#: The fields' native rectangles (`Add_Race_Options_Fields_EM`,
#: raceopt.cpp:1185-1186, :1191, :1230-1232, :1291-1292; `Add_Hidden_Field` keeps
#: them as given, fields.cpp:324-327), so a send names a field the live
#: list holds in that place (P816, decision 20) — never a number alone.
X_COORDS = (80, 254, 442, 643)
Y_COORDS = (72, 147, 222, 297, 372)
ACCEPT_AT = (506, 448)


def group_rect(group, level):
    """Group `group`'s level `level` (1-3): five groups a column (:1242-
    1246), 13 px a level from the row's y + 9 (:1205, :1237)."""
    col, row = divmod(group, 5)
    y = Y_COORDS[row] + 9 + 13 * (level - 1)
    return (X_COORDS[col] - 20, y - 9, X_COORDS[col + 1] - 50, y)


def option_rect(index):
    """Special ability `index`: the third column, 16 px a row from 72
    (:1256, :1259, :1298)."""
    y = 72 + 16 * index
    return (X_COORDS[2] - 20, y, X_COORDS[2] + 152, y + 9)


def popup_of(state):
    """TPOP kind 23 while the engine reports 83, else None."""
    tp = getattr(state, "turn_popup", None)
    if tp is None or tp.get("kind") != "mutation" or \
            getattr(state, "current_screen", -1) != GAME_SCREEN_ID:
        return None
    return tp


def active(state):
    return popup_of(state) is not None


def trait_state(popup, categories, specials):
    """Custom Race's `trait_id -> value` from the engine's selections."""
    m = popup["mutation"]
    out = {cat["trait_id"]: 0 for cat in categories}
    out.update({spec["trait_id"]: 0 for spec in specials})
    for cat in categories:
        tid = cat["trait_id"]
        if tid == governments.TRAIT_ID:
            idx = m["button_variable"][9]
            if 0 <= idx < len(GOVERNMENT_PICKS):
                out[tid] = GOVERNMENT_PICKS[idx]
        elif tid in PRIMARY_TRAITS:
            level = m["button_variable"][PRIMARY_TRAITS.index(tid)]
            out[tid] = next((opt["value"] for opt in cat["options"]
                             if LEVEL_OF_VALUE.get(opt["value"]) == level), 0)
    for i, (tid, value) in enumerate(SPECIALS):
        if m["option_toggle"][i] == 1:
            out[tid] = value
    return out


def _level(opt):
    return LEVEL_OF_VALUE.get(opt["value"])


def _field_of_pick(m, cat, opt):
    """(field, rect) of a group option, or None (the wire's
    `group_field`)."""
    tid = cat["trait_id"]
    level = _level(opt)
    if tid not in PRIMARY_TRAITS or level is None:
        return None          # the government: no field in mutation mode
    g = PRIMARY_TRAITS.index(tid)
    f = mutationwire.group_field(m, g, level)
    return (f, group_rect(g, level)) if f is not None else None


def _field_of_special(m, spec):
    key = (spec["trait_id"], spec.get("value", 1))
    if key not in SPECIALS:
        return None
    i = SPECIALS.index(key)
    f = mutationwire.option_field(m, i)
    return (f, option_rect(i)) if f is not None else None


def blocked(popup, categories, specials, state):
    """What is drawn dimmed: every option not chosen and not offered —
    `(trait, value)` — and Farming whole under Lithovore (`(2, "all")`)."""
    m = popup["mutation"]
    out = set()
    for cat in categories:
        for opt in cat["options"]:
            if state.get(cat["trait_id"]) != opt["value"] and \
                    _field_of_pick(m, cat, opt) is None:
                out.add((cat["trait_id"], opt["value"]))
    for spec in specials:
        value = spec.get("value", 1)
        if state.get(spec["trait_id"]) != value and \
                _field_of_special(m, spec) is None:
            out.add((spec["trait_id"], value))
    if m["option_toggle"][LITHOVORE] == 1:
        out.add((FARMING, "all"))
    return out


def live(game_state, found, ftype):
    """The live field `found` names — (index, native rect) — when the list
    of now holds it with that type and rectangle, else None."""
    if found is None:
        return None
    index, rect = found
    return next((f for f in (getattr(game_state, "fields", None) or [])
                 if f.index == index and f.field_type == ftype and
                 (f.x, f.y, f.x_end, f.y_end) == tuple(rect)), None)


def accept_field(game_state, popup):
    a = popup["mutation"]["accept"]
    return next((f for f in (getattr(game_state, "fields", None) or [])
                 if a > 0 and f.index == a and f.field_type == TYPE_BUTTON
                 and (f.x, f.y) == ACCEPT_AT), None)


def pick_field(game_state, popup, cat, opt):
    return live(game_state, _field_of_pick(popup["mutation"], cat, opt),
                TYPE_HIDDEN)


def special_field(game_state, popup, spec):
    return live(game_state, _field_of_special(popup["mutation"], spec),
                TYPE_HIDDEN)


class Sender:
    """One answer per state of the screen: a second click before the
    engine has moved would land in a list it has since rebuilt (the loop
    adds every field again after an input, :402) — sent again only after
    `turnpopup.RESEND_AFTER` unchanged snapshots, the turn popups' rule.

    The second activation is safe because nothing moved: an input the
    engine takes changes the tail (a level set or cleared, a toggle, the
    picks), and one it refuses opens a box, which takes the input instead
    (MSGB); a tail that stands still for twenty snapshots means the click
    was lost or was a no-op (a level clamped back to the baseline, :325-
    329), and repeating it does the same. The field is resolved again in the
    list of now, never remembered."""

    def __init__(self):
        self.sent = None

    def send(self, app, popup, field, what):
        from core import turnpopup
        if field is None or not getattr(app, "connected", False):
            return False
        m = popup["mutation"]
        key = (tuple(popup["args"]), tuple(sorted(
            (k, tuple(v) if isinstance(v, list) else v)
            for k, v in m.items())))
        snap = app.client.stats.get("state", 0)
        if self.sent is not None and self.sent[0] == key and \
                snap - self.sent[1] < turnpopup.RESEND_AFTER:
            return False
        self.sent = (key, snap)
        log.info("mutation: %s -> field %d", what, field.index)
        app.client.activate_field(field.index)
        return True
