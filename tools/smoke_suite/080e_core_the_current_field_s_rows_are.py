# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080e_core_the_current_field_s_rows_are.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (98 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part E,
# the six "everyone gets everything" fields and Creative, which is
# work order 131 part C's offline half.
#
# The 2 check(s) it holds:
#   - the current field's rows are ALL marked for the six starting
#     fields and for a Creative player, and one otherwise, BY NAME
#   - TRAIT_CREATIVE comes off the wire and reaches the drawing

# ── WHAT THE SECOND COLOUR MARKS (tech.cpp:648-706) ──
#
# `Display_Entry_Text_` picks ONE colour for the current field's name
# and its cost, then marks its applications: ALL of them when the
# player is Creative or the field is one of the six
# `_starting_tech_field_ids` (techdata.cpp:548), otherwise the one
# whose NAME matches the current application's — `strcasecmp`, not an
# id comparison.
from core import researchpanel as _cr_panel

assert set(_rl.ALL_APPLICATIONS_FIELDS) == {29, 55, 22, 57, 28, 23}, \
    sorted(_rl.ALL_APPLICATIONS_FIELDS)
_cr_outside = next(f for f in _rl.FIRST_FIELD_IN_GROUP[1:]
                   if f and f not in _rl.ALL_APPLICATIONS_FIELDS)
for _cr_f in _rl.ALL_APPLICATIONS_FIELDS:
    assert _cr_panel.marks_every_row(_cr_f, False), _cr_f
    assert _cr_panel.marks_every_row(_cr_f, True), _cr_f
assert not _cr_panel.marks_every_row(_cr_outside, False), _cr_outside
assert _cr_panel.marks_every_row(_cr_outside, True), _cr_outside


class _CrNames:
    """Names by id, so the NAME comparison can be told from an id one."""

    def __init__(self, table):
        self.table = table

    def application_name(self, app, hyper_count=None):
        return self.table.get(app)


# THE COMPARISON IS THE NAME. Two applications that share one are both
# marked, which an id comparison cannot do — and that is the whole
# difference, so it is what is asserted.
_cr_names = _CrNames({1: "Ion Drive", 2: "ion drive ", 3: "Battle Pods"})
assert _cr_panel.marks_row(_cr_names, 1, 1)
assert _cr_panel.marks_row(_cr_names, 2, 1), (
    "an application with the current one's name is not marked; the "
    "original compares names with strcasecmp (tech.cpp:697-700)")
assert not _cr_panel.marks_row(_cr_names, 3, 1)
assert not _cr_panel.marks_row(_cr_names, 1, 0)
assert not _cr_panel.marks_row(_cr_names, 0, 1)
# A name the file does not carry falls back to the id rather than
# marking nothing — an absent extraction is a state, not a wrong colour.
assert _cr_panel.marks_row(_CrNames({}), 5, 5)
assert not _cr_panel.marks_row(_CrNames({}), 5, 6)
ok("the current field's rows are ALL marked for the six starting "
   "fields and for a Creative player, and one otherwise, BY NAME")

# ── THE TRAIT COMES OFF THE WIRE, AND IT REACHES THE DRAWING ──
#
# Two renders of the same state, one Creative and one not, on a field
# that is NOT one of the six: the pixels of that entry's rows have to
# differ. A flag that never reached the panel would draw the same
# picture twice — which is the shape of the fault work order 129 made
# one level up, reporting a flag's name as an observation.
_cr_group = next(g for g in _rl.ENTRY_TO_GROUP
                 if _rl.FIRST_FIELD_IN_GROUP[g] == _cr_outside)
_cr_field = _rl.FIRST_FIELD_IN_GROUP[_cr_group]
_cr_tf = [0] * _rl_res.FIELD_COUNT
_cr_tf[_cr_field] = _rl.FIELD_STATUS_OFFERABLE
_cr_ta = [_rl.APP_STATUS_AVAILABLE] * player_mod.TECH_APPLICATIONS_COUNT
_cr_entries = _rl.reconstruct(_cr_tf, _cr_ta, select_mode=False)
_cr_entry = next(e for e in _cr_entries if e.field == _cr_field)
assert len(_cr_entry.apps) >= 2, (
    f"field {_cr_field} offers {len(_cr_entry.apps)} row(s); this check "
    f"needs one the two colourings can disagree about")


def _cr_state(creative):
    _raw = bytearray(_dx_record(_cr_tf, _cr_ta, 0, _cr_field,
                                _cr_entry.apps[0]))
    _raw[player_mod.TRAITS_OFFSET + player_mod.TRAIT_CREATIVE] = \
        1 if creative else 0
    _st = _RsGameState()
    _st.current_screen = 36
    _st.fields = _rl_list(_cr_entries, select_mode=False)
    _st.player_raw = [bytes(_raw)]
    _st.player_num = 0
    return _st


def _cr_render(creative):
    _st = _cr_state(creative)
    _dx_scr.enter(_st)
    _dx_scr._names = derived(_dx_tn.TechNames)
    _dx_scr._wording = derived(_dx_bt.BillText)
    _dx_scr.update(_st)
    assert _dx_scr.state == _dx_core.READY, _dx_scr.problems
    assert _dx_scr._creative is creative, (
        f"TRAIT_CREATIVE {creative} on the wire, the screen read "
        f"{_dx_scr._creative} — offset {player_mod.TRAITS_OFFSET} + "
        f"{player_mod.TRAIT_CREATIVE}")
    _surf = pygame.Surface((1920, 1080))
    _surf.fill((0, 0, 0))
    _dx_scr.render(_surf)
    return _surf


_cr_plain, _cr_creative = _cr_render(False), _cr_render(True)
_cr_diff = 0
for _cr_row in range(1, len(_cr_entry.apps)):
    _cr_r = _dx_geo.window_rect(_cr_entry.row_rect(_cr_row), _dx_scr.layout)
    for _cr_y in range(_cr_r[1], _cr_r[1] + _cr_r[3]):
        for _cr_x in range(_cr_r[0], _cr_r[0] + _cr_r[2]):
            if _cr_plain.get_at((_cr_x, _cr_y))[:3] != \
                    _cr_creative.get_at((_cr_x, _cr_y))[:3]:
                _cr_diff += 1
assert _cr_diff > 20, (
    f"only {_cr_diff} pixels of the rows below the chosen one changed "
    f"when the player became Creative; the trait is not reaching the "
    f"drawing")
# …and the CHOSEN row is marked either way, so the difference above is
# about the others and not about the whole entry being repainted.
assert _cr_panel.marks_row(_dx_scr._names, _cr_entry.apps[0],
                           _cr_entry.apps[0])
_dx_scr.enter(_dx_state)
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_dx_scr.update(_dx_state)
ok("TRAIT_CREATIVE comes off the wire and reaches the drawing")
