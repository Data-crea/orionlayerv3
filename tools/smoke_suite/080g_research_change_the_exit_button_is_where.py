# smoke-suite area: research_change
#
# Part of the OrionLayer smoke suite — 080g_research_change_the_exit_button_is_where.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (100 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part G,
# the exit button change mode was missing.
#
# The 2 check(s) it holds:
#   - the exit button is drawn and clickable at the rectangle THE WIRE
#     reports, and nowhere when the wire has no such field
#   - a click on it sends exactly what ESC sends, and a click beside it
#     sends nothing

# ── A RECTANGLE THE SOURCE DOES NOT HAVE ──
#
# `Add_Button_Field_(s + 0xBD, 0x1C4, "", TECHSEL 0x1B, "\x1B", '(')`
# (tech.cpp:208-210, art at :176) takes its rectangle from the ART
# (fields.cpp:366-367), so tech.cpp gives the ORIGIN and nothing else —
# `doc/tech_change_reading.md` §2 carried the end as NOT SETTLED until
# the live list was read. So the button follows the wire, and a
# remembered size would put a clickable word where the game may have no
# field at all (decision 20, one step before a send).
from core import researchpanel as _ex_panel

#: What the live list reported on 22 September 2026, 91 x 18 px.
_EX_LIVE = (269, 452, 360, 470)
#: And a DIFFERENT end, to tell "reads the wire" from "remembers 91".
_EX_OTHER = (269, 452, 330, 466)


#: The same button one pixel off its own origin. NOT a missing field —
#: the list would be one short and the screen would refuse to draw at
#: all, which is a different claim. This is a button that IS there and
#: is not where `_tech_button_pos + _g_scrn_x` puts it, which is what
#: "found by origin, never assumed" has to survive.
_EX_WRONG = (_EX_LIVE[0] + 1, _EX_LIVE[1], _EX_LIVE[2], _EX_LIVE[3])


def _ex_state(exit_rect):
    """The change-mode list with the exit field at `exit_rect`.

    `_rl_list` gives the exit entry a zero rectangle, because
    `expected_fields` reports it as unpredictable — which is exactly
    why this check has to place it by hand.
    """
    _rows = _rl_list(_dx_entries, select_mode=False)
    for _f in _rows:
        if _f.field_type == _rl.TYPE_BUTTON:
            (_f.x, _f.y, _f.x_end, _f.y_end) = exit_rect
            break
    _st = _RsGameState()
    _st.current_screen = 36
    _st.fields = _rows
    _st.player_raw = list(_dx_state.player_raw)
    _st.player_num = 0
    return _st


def _ex_enter(state):
    _dx_scr.app.client, _dx_scr.app.connected = _rs_client, True
    _rs_client.state = state
    _dx_scr.enter(state)
    _dx_scr._names = derived(_dx_tn.TechNames)
    _dx_scr._wording = derived(_dx_bt.BillText)
    _dx_scr.update(state)
    assert _dx_scr.state == _dx_core.READY, _dx_scr.problems


def _ex_centre(rect):
    _x, _y, _w, _h = _dx_geo.window_rect(rect, _dx_scr.layout)
    return (_x + _w // 2, _y + _h // 2)


# 1. THE RECTANGLE IS THE WIRE'S, and it moves when the wire moves.
for _ex_rect in (_EX_LIVE, _EX_OTHER):
    _ex_enter(_ex_state(_ex_rect))
    assert _dx_scr.exit_rect() == _ex_rect, (_dx_scr.exit_rect(),
                                             _ex_rect)
    assert _dx_scr.exit_at(*_ex_centre(_ex_rect)), _ex_rect
# The narrower button is NOT clickable where the wider one ended: if
# the size were remembered, this point would still answer.
_ex_enter(_ex_state(_EX_OTHER))
_ex_gap = _ex_centre((_EX_OTHER[2] + 6, _EX_LIVE[1], _EX_LIVE[2],
                      _EX_LIVE[3]))
assert not _dx_scr.exit_at(*_ex_gap), (
    "a point past the end the WIRE reported is still on the button — "
    "the rectangle is remembered, not read")

# 2. AND IT IS DRAWN THERE — which is a comparison and not a colour
#    test, because the button sits INSIDE the panel's own fill rect
#    `(s+4, 4)-(s+471, 472)` (tech.cpp:290) and that fill covers its
#    area whether the button is drawn or not. So: the same state twice,
#    once with the field at its own origin and once one pixel off it.
#    Inside the button the two frames must differ; everywhere else in
#    the panel they must not.
def _ex_frame(state):
    _ex_enter(state)
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _dx_scr.render(_s)
    return _s


_ex_on = _ex_frame(_ex_state(_EX_LIVE))
_ex_off = _ex_frame(_ex_state(_EX_WRONG))
_bx, _by, _bw, _bh = _dx_geo.window_rect(_EX_LIVE, _dx_scr.layout)
_ex_drawn = sum(1 for _y in range(_by + 2, _by + _bh - 2, 2)
                for _x in range(_bx + 2, _bx + _bw - 2, 2)
                if _ex_on.get_at((_x, _y))[:3] !=
                _ex_off.get_at((_x, _y))[:3])
assert _ex_drawn > 200, (
    f"only {_ex_drawn} pixels of the button's rectangle change when "
    f"the field is at its origin rather than beside it — the button is "
    f"not being drawn")
# …and it draws ONLY there. The rest of the panel is untouched.
_px2, _py2, _pw2, _ph2 = _dx_geo.window_rect(_dx_scr.geom.panel_rect,
                                             _dx_scr.layout)
_ex_spill = sum(
    1 for _y in range(_py2, _py2 + _ph2, 3)
    for _x in range(_px2, _px2 + _pw2, 3)
    if not (_bx <= _x <= _bx + _bw and _by <= _y <= _by + _bh)
    and _ex_on.get_at((_x, _y))[:3] != _ex_off.get_at((_x, _y))[:3])
assert _ex_spill == 0, (
    f"{_ex_spill} pixels outside the button changed with it — it is "
    f"drawing somewhere it was not asked to")

# 3. WITH THE BUTTON OFF ITS OWN ORIGIN, it is not clickable either,
#    while the panel itself still draws — or this proves nothing.
_ex_enter(_ex_state(_EX_WRONG))
assert _dx_scr.exit_rect() is None
assert not _dx_scr.exit_at(*_ex_centre(_EX_LIVE))
assert _dx_scr.state == _dx_core.READY
# SELECT MODE HAS NO BUTTON AT ALL — `accept_btn_id = -1`
# (tech.cpp:216) — so `HAS_EXIT` keeps it from ever finding one.
assert _rs_scr.exit_field() is None and _rs_scr.exit_rect() is None
assert _rs_scr.HAS_EXIT is False
ok("the exit button is drawn and clickable at the rectangle THE WIRE "
   "reports, and nowhere when the wire has no such field")

# ── A CLICK ON IT IS ESC ──
#
# `input_val == accept_btn_id` is tested BEFORE the commit branch
# (tech.cpp:357) and is the one branch that does not commit. ESC
# resolves to the same field, because it is the first ESC field of the
# list (`Interpret_Keyboard_Input_`, fields.cpp:2608-2613). So the two
# have to send the same thing — asserted by comparing them, not by
# reading the code twice.
_ex_state_live = _ex_state(_EX_LIVE)
_ex_enter(_ex_state_live)
_rs_client.log.clear()
_dx_scr.handle_key(pygame.K_ESCAPE)
_ex_by_key = list(_rs_client.log)
assert _ex_by_key, "ESC sent nothing at all; this comparison is empty"

_ex_enter(_ex_state_live)
_rs_client.log.clear()
_dx_scr.handle_click(*_ex_centre(_EX_LIVE))
_ex_by_click = list(_rs_client.log)
assert _ex_by_click == _ex_by_key, (_ex_by_click, _ex_by_key)

# A CLICK BESIDE IT SENDS NOTHING. Two points: just under the button,
# and the panel's own empty bottom-left corner. Neither is a row, so
# neither may commit — and the exit must not answer for them either.
for _ex_miss in (_ex_centre((_EX_LIVE[0], _EX_LIVE[3] + 4,
                             _EX_LIVE[2], _EX_LIVE[3] + 8)),
                 _ex_centre((_dx_scr.geom.origin + 6, 440,
                             _dx_scr.geom.origin + 20, 450))):
    _ex_enter(_ex_state_live)
    _rs_client.log.clear()
    _dx_scr.handle_click(*_ex_miss)
    assert _rs_client.log == [], (_ex_miss, _rs_client.log)
    assert not _dx_scr._left, _ex_miss

# AND THE LABEL IS THE ONE layout.json CARRIES, printed as text
# because the original has no string to transcribe.
_ex_layout = _sjson.load(open(os.path.join(
    SCREENS_DIR, "research_change", "layout.json"), encoding="utf-8"))
assert _ex_layout["exit_label"], "no exit label in layout.json"
assert "DEVIATION" in _ex_layout["exit_label_note"]
assert "exit_button_as_text" in _rcs.MARKED
assert _ex_panel.draw_exit.__doc__ and \
    "DEVIATION" in _ex_panel.draw_exit.__doc__
_ex_enter(_dx_state)
ok("a click on it sends exactly what ESC sends, and a click beside it "
   "sends nothing")
