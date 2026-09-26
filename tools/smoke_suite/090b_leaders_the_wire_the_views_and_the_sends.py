# smoke-suite area: leaders
#
# Part of the OrionLayer smoke suite — 090b_leaders_the_wire_the_views_and_the_sends.py.
# Executed in the suite's one namespace, after 090a (whose `_ld_pack`
# it uses). Work order 167, the Leaders screen: what one snapshot lets
# HD believe, and what HD sends because of it.
#
# The snapshots here are REAL WIRE BYTES, parsed by core/game_state's
# own parser; the field lists are `Add_Officer_Screen_Fields_`
# (officer.cpp:2813-3021) transcribed field by field, with the engine's
# own slot 0 first (FIELD_ZERO_ROW).
#
# The 4 check(s) it holds:
#   - open fix 30's OFFS block parses after FSEL when it is there, and
#     absent or short it is None — a state, not a half-read block
#   - the six states on real snapshots: both views READY off the list,
#     MISMATCH, WAITING then UNVALIDATED at the bound, a native box, the
#     hire popup; only the two refusals hand over
#   - without the block HD sends exactly what it can see the effect of,
#     each to the live field; with it, the rest too
#   - the hire popup is identified only by an exact field shape, and its
#     question is 0x124 or 0x125 by the upkeep
from core import game_state as _ldw_gs
from screens.leaders import ldrgeom as _ldw_g
from screens.leaders import ldrpopup as _ldw_pop
from screens.leaders import ldrwire as _ldw
from core import leaderskills as _ldw_ls
from core.structs import leader as _ldw_leader


def _ldw_snapshot(leaders, player=0, screen=29, block=None, stars=(),
                  ships=(), cut=0, tail=b""):
    """A STATE_SNAPSHOT payload, every section at its size, the leader
    records where the engine writes them, FSEL empty, and — when given
    — the OFFS block after it, exactly where the patch writes it."""
    _S = _ld_st
    _b = bytearray()
    _b += _S.pack("<hbihhhhhBb", screen, 0, 35000, player, 2,
                  len(stars), len(ships), 0, 0, 0)
    _b += _S.pack("<hhhhh", 15, 0, 0, 759, 600)
    _b += bytes(_ldw_gs.SETTINGS_SIZE)
    _b += bytes(_ldw_gs.PLAYER_SIZE * 8)
    _b += _S.pack("<h", len(stars))
    for _st in stars:
        _b += _st
    _b += _S.pack("<h", len(ships))
    for _sh in ships:
        _b += _sh
    _b += _S.pack("<h", 0) + _S.pack("<h", 0) + bytes([0])
    for _r in leaders:
        _b += _r
    _b += bytes(_ldw_gs.ANTARAN_SIZE)
    _b += _S.pack("<h", 0)                        # ship icons
    _b += _S.pack("<8h", *([0] * 8))              # newgame temps
    _b += b"FSEL" + _S.pack("<hhh", -1, 0, 0)
    if block is not None:
        _b += b"OFFS" + _S.pack("<4b", block["view"], block["mode"],
                                block["selected"], block["scanned"])
        _b += _S.pack("<3h", block["star_displayed"],
                      block["star_chosen"], len(block["ids"]))
        _b += _S.pack("<4h", *(list(block["ids"]) + [-1] * 4)[:4])
        _b += _S.pack("<9h", block["stack"], block["head"],
                      block["first_row"], block["picked"], -1, -1, -1,
                      block["popup_leader"], block["popup_state"])
        _b += _S.pack("<h", len(block["icons"]))
        for _ship, _sel in block["icons"]:
            _b += _S.pack("<hB", _ship, _sel)
    _b += tail                                # a later block (090f: INFS)
    return _ldw_gs.parse_state(bytes(_b[:len(_b) - cut]))


def _ldw_f(index, rect, ftype, hotkey=0):
    _f = _ldw_gs.FieldInfo()
    _f.index = index
    _f.x, _f.y, _f.x_end, _f.y_end = rect
    _f.field_type, _f.hotkey = ftype, hotkey
    return _f


def _ldw_fields(gs, view, mode=-1, drop_row=None):
    """The engine's list for this snapshot: slot 0 first (FIELD_ZERO_ROW),
    then `ldrgeom.field_shapes` — `Add_Officer_Screen_Fields_` in its
    order. `drop_row` leaves one row's text field out: a list that
    disagrees with the rebuild."""
    _recs = _ldw_leader.parse_all(gs.leaders_raw)
    _rows = _ldw_ls.captain_id_list(_recs, gs.player_num, view)
    _pool = _ldw_ls.leaders_for_hire(_recs, gs.player_num, view)
    _split = [tuple(len(_p) for _p in _ldw_pop.split_skills(_recs[_i]))
              for _i in _rows]
    _drop = None if drop_row is None else _ldw_g.text_field(drop_row)
    _out = [_ldw_f(*FIELD_ZERO_ROW[:1], FIELD_ZERO_ROW[1:5],
                   FIELD_ZERO_ROW[5])]
    for _rect, _type, _hk in _ldw_g.field_shapes(len(_rows), _split, view,
                                                 mode, _pool):
        if _rect == _drop:
            continue
        _out.append(_ldw_f(len(_out), _rect, _type, _hk))
    return [f for f in _out if f.index != 0]


# A small empire: player 0 has two ship officers (one in the pool, one
# FOR HIRE with a unique skill shape) and one colony leader; player 1
# has two for hire whose skill shapes are identical.
_ldw_recs = [_ld_pack(name=f"Leader {_i}") for _i in range(67)]
_ldw_recs[2] = _ld_pack(name="Leader 2", type=0, status=0, player_index=0,
                        special_skills=0x10, skill_value=4)
_ldw_recs[7] = _ld_pack(name="Leader 7", type=0, status=4, player_index=0,
                        eta=12, special_skills=0x1 | 0x4000,
                        general_skills=0x4, skill_value=7)
_ldw_recs[9] = _ld_pack(name="Leader 9", type=1, status=0, player_index=0,
                        general_skills=0x40, skill_value=5, xp=60)
_ldw_recs[20] = _ld_pack(name="Leader 20", type=0, status=4,
                         player_index=1, special_skills=0x1, skill_value=3)
_ldw_recs[21] = _ld_pack(name="Leader 21", type=0, status=4,
                         player_index=1, special_skills=0x2, skill_value=3)
_ldw_block = {"view": 0, "mode": -1, "selected": -1, "scanned": -1,
              "star_displayed": -1, "star_chosen": -1, "ids": [2, 7],
              "stack": 3, "head": 5, "first_row": 0, "picked": -1,
              "popup_leader": -1, "popup_state": -1,
              "icons": [(0, 0), (1, 1)]}

# ── 5. THE OFFS BLOCK ─────────────────────────────────────────
_ldw_s = _ldw_snapshot(_ldw_recs, block=_ldw_block)
_ldw_b = _ldw_s.officer_screen
assert _ldw_b is not None, "OFFS did not parse out of a real snapshot"
assert (_ldw_b["view"], _ldw_b["mode"], _ldw_b["id_list"],
        _ldw_b["stack"], _ldw_b["head_node"], _ldw_b["ship_idx"],
        _ldw_b["ship_selected"]) == (0, -1, [2, 7, -1, -1], 3, 5, [0, 1],
                                     [False, True]), _ldw_b
assert len(_ldw_s.leaders_raw) == 67
assert _ldw_snapshot(_ldw_recs).officer_screen is None
# A block whose last icon is cut off is None — never a block with one
# icon fewer, which would draw a grid missing a ship without saying so.
assert _ldw_snapshot(_ldw_recs, block=_ldw_block, cut=1).officer_screen \
    is None
assert _ldw_snapshot(_ldw_recs, block=_ldw_block, cut=0).officer_screen \
    is not None
ok("open fix 30's OFFS block parses after FSEL when it is there, and "
   "absent or short it is None")

# ── 6. THE SIX STATES, ON REAL SNAPSHOTS ─────────────────────
_ldw_s = _ldw_snapshot(_ldw_recs)
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP)
_ldw_v = _ldw.View(_ldw_s)
assert _ldw_v.state == _ldw.READY, (_ldw_v.state, _ldw_v.reason)
assert _ldw_v.view == _ldw_g.VIEW_SHIP and _ldw_v.rows == [2, 7]
assert set(_ldw_v.buttons) >= {"tab_ship", "tab_colony", "return", "hire",
                               "pool", "dismiss", "scroll_up",
                               "scroll_down", "prev", "next"}
assert not _ldw_v.hire_mode and _ldw_v.mode is None and _ldw_v.draws
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_COLONY)
_ldw_v = _ldw.View(_ldw_s)
assert (_ldw_v.state, _ldw_v.view, _ldw_v.rows) == (
    _ldw.READY, _ldw_g.VIEW_COLONY, [9])
assert "hire" not in _ldw_v.buttons, "no colony leader is for hire"
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP, mode=0)
_ldw_v = _ldw.View(_ldw_s)
assert _ldw_v.hire_mode and _ldw_v.mode == 0 and "cancel" in _ldw_v.buttons
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP, drop_row=1)
_ldw_v = _ldw.View(_ldw_s)
assert _ldw_v.state == _ldw.MISMATCH and not _ldw_v.draws and _ldw_v.reason
_ldw_s.fields = []                       # still the previous screen's
assert _ldw.View(_ldw_s, waited=1).state == _ldw.WAITING
assert _ldw.View(_ldw_s, waited=1).draws
assert _ldw.View(_ldw_s, waited=_ldw.WAIT_BOUND).state == _ldw.UNVALIDATED
_ldw_s.fields = [_ldw_f(1, (235, 302, 286, 323), 7, ord("Y")),
                 _ldw_f(2, (345, 302, 396, 323), 7, ord("N"))]
_ldw_v = _ldw.View(_ldw_s, last_view=_ldw_g.VIEW_SHIP)
assert _ldw_v.state == _ldw.IN_BOX and _ldw_v.in_box and _ldw_v.draws
assert _ldw_v.rows == [2, 7], "under a box the last view's rows stand"
# A block contradicting the rebuild is a refusal too.
_ldw_s2 = _ldw_snapshot(_ldw_recs, block=dict(_ldw_block, ids=[7, 2]))
_ldw_s2.fields = _ldw_fields(_ldw_s2, _ldw_g.VIEW_SHIP)
assert _ldw.View(_ldw_s2).state == _ldw.MISMATCH
ok("the six states on real snapshots: both views READY off the list, "
   "MISMATCH, WAITING then UNVALIDATED at the bound, a native box; only "
   "the refusals hand over")

# ── 7. WHAT IS SENT, AND WHERE ────────────────────────────────
import colony_list_preview as _ldw_plv
_ldw_app, _ldw_other = _ldw_plv.build_screen(1920, 1080)
_ldw_sent = []
_ldw_app.client.activate_field = lambda fid: _ldw_sent.append(("act", fid))
_ldw_app.client.inject_click = lambda x, y: _ldw_sent.append(("click", x, y))
_ldw_app.client.cancel_field = lambda fid: _ldw_sent.append(("cancel", fid))
_ldw_app.client.inject_key = lambda k: _ldw_sent.append(("key", k))
_ldw_app.dispatcher.switch_to("leaders")
_ldw_scr = _ldw_app.dispatcher.screens["leaders"]


def _ldw_centre(native_rect):
    from core import researchnative as _n
    _r = _n.window_rect(native_rect, _ldw_scr.layout)
    return (_r[0] + _r[2] // 2, _r[1] + _r[3] // 2)


def _ldw_click(native_rect):
    _ldw_sent.clear()
    _ldw_scr.handle_click(*_ldw_centre(native_rect))
    return list(_ldw_sent)


def _ldw_index(fields, rect):
    return next(f.index for f in fields
                if (f.x, f.y, f.x_end, f.y_end) == tuple(rect))


_ldw_s = _ldw_snapshot(_ldw_recs)
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP)
_ldw_scr.update(_ldw_s)
for _ldw_name in ("tab_colony", "tab_ship", "hire", "return"):
    _ldw_r = _ldw_g.button_rect(_ldw_name)
    assert _ldw_click(_ldw_r) == [("act", _ldw_index(_ldw_s.fields,
                                                    _ldw_r))], _ldw_name
for _ldw_name in ("pool", "dismiss", "prev", "next", "scroll_up"):
    assert _ldw_click(_ldw_g.button_rect(_ldw_name)) == [], (
        f"{_ldw_name} went out without the mode on the wire")
# The leader FOR HIRE (row 1) goes, to its own text field; the one in
# the pool (row 0) does not — that click would select, invisibly.
assert _ldw_click(_ldw_g.text_field(1)) == [
    ("act", _ldw_index(_ldw_s.fields, _ldw_g.text_field(1)))]
assert _ldw_click(_ldw_g.text_field(0)) == []
# ESC is RETURN's field; the right button on a portrait asks the game
# where the leader is, and on a skill line opens HD's own box, unsent.
_ldw_sent.clear()
_ldw_scr.handle_key(27)
assert _ldw_sent == [("act", _ldw_index(_ldw_s.fields,
                                         _ldw_g.button_rect("return")))]
_ldw_sent.clear()
_ldw_scr.handle_right_button(True, *_ldw_centre(_ldw_g.portrait_field(0)))
assert _ldw_sent == [("cancel", _ldw_index(_ldw_s.fields,
                                            _ldw_g.portrait_field(0)))]
from screens.leaders import ldrdraw as _ldw_draw
_ldw_sent.clear()
_ldw_line = _ldw_draw.skill_line_rects(_ldw_scr, _ldw_scr._rows[1])[0]
_ldw_scr.handle_right_button(True, *_ldw_line.center)
assert _ldw_sent == [] and _ldw_scr._skill_help is not None
_ldw_scr.handle_click(10, 10)
assert _ldw_scr._skill_help is None and _ldw_sent == []
# Hire mode: ANY leader goes to Do_Hire_Officer_ (officer.cpp:1409).
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP, mode=0)
_ldw_scr.update(_ldw_s)
assert _ldw_click(_ldw_g.text_field(0)) == [
    ("act", _ldw_index(_ldw_s.fields, _ldw_g.text_field(0)))]
assert _ldw_click(_ldw_g.button_rect("cancel")) == [
    ("act", _ldw_index(_ldw_s.fields, _ldw_g.button_rect("cancel")))]
# With the block every control is the game's to answer.
_ldw_s = _ldw_snapshot(_ldw_recs, block=_ldw_block)
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP)
_ldw_scr.update(_ldw_s)
for _ldw_name in ("pool", "dismiss", "prev", "next"):
    _ldw_r = _ldw_g.button_rect(_ldw_name)
    assert _ldw_click(_ldw_r) == [("act", _ldw_index(_ldw_s.fields,
                                                    _ldw_r))], _ldw_name
assert _ldw_click(_ldw_g.text_field(0)) != []
# Refusing: nothing at all goes out.
_ldw_s.fields = _ldw_fields(_ldw_s, _ldw_g.VIEW_SHIP, drop_row=1)
_ldw_scr.update(_ldw_s)
assert _ldw_scr.wants_original() and _ldw_scr.fallback_reason()
for _ldw_name in ("tab_colony", "return", "hire"):
    assert _ldw_click(_ldw_g.button_rect(_ldw_name)) == [], _ldw_name
ok("without the block HD sends exactly what it can see the effect of, "
   "each to its live field; with the block the rest too; refusing, "
   "nothing")

# ── 8. THE HIRE POPUP ─────────────────────────────────────────
def _ldw_popup_fields(rec):
    _fl = [_ldw_f(1, _ldw_pop.REJECT_RECT, 0, ord("R")),
           _ldw_f(2, _ldw_pop.HIRE_RECT, 0, ord("H"))]
    for _k, _r in enumerate(_ldw_pop.skill_help_rects(rec)):
        _fl.append(_ldw_f(3 + _k, _r, 7))
    return _fl


_ldw_s = _ldw_snapshot(_ldw_recs, player=0)
_ldw_s.fields = _ldw_popup_fields(_ldw_leader.parse(_ldw_recs[7]))
_ldw_v = _ldw.View(_ldw_s, last_view=_ldw_g.VIEW_SHIP)
assert _ldw_v.state == _ldw.POPUP and _ldw_v.popup.leader == 7
# The special line's field starts a pixel HIGHER than the general one's
# (officer.cpp:3928-3935 against :3956-3963): that is the shape.
_ldw_sh = _ldw_pop.skill_help_rects(_ldw_leader.parse(_ldw_recs[7]))
assert _ldw_sh[1][1] - _ldw_sh[0][1] == 17 and \
    _ldw_sh[2][1] - _ldw_sh[1][1] == 18, _ldw_sh
# Player 1's two candidates share a shape: not identified, not guessed.
_ldw_s = _ldw_snapshot(_ldw_recs, player=1)
_ldw_s.fields = _ldw_popup_fields(_ldw_leader.parse(_ldw_recs[20]))
assert _ldw.View(_ldw_s).popup.leader is None
# …and the block names it.
_ldw_s = _ldw_snapshot(_ldw_recs, player=1,
                       block=dict(_ldw_block, popup_leader=21, ids=[]))
_ldw_s.fields = _ldw_popup_fields(_ldw_leader.parse(_ldw_recs[20]))
assert _ldw.View(_ldw_s).popup.leader == 21
# The question: 0x124 when the upkeep is exactly one, else 0x125.
from core.hestrings import HStrings
_ldw_h = derived(HStrings)
_ldw_s = _ldw_snapshot(_ldw_recs, player=0)
_ldw_s.fields = _ldw_popup_fields(_ldw_leader.parse(_ldw_recs[7]))
_ldw_v = _ldw.View(_ldw_s)
_ldw_q = _ldw_pop.question(_ldw_v, 7, _ldw_h, "Title", ", the ")
_ldw_up = _ldw_ls.maintenance(_ldw_v.leaders, 7, 0, lambda p: False)
assert _ldw_up == 1 and _ldw_q is not None
assert _ldw_q.startswith(_ldw_h.message(0x124).split("%")[0]), _ldw_q
_ldw_sent.clear()
_ldw_scr.update(_ldw_s)
for _ldw_key, _ldw_rect in (("reject", _ldw_pop.REJECT_RECT),
                            ("hire", _ldw_pop.HIRE_RECT)):
    _ldw_sent.clear()
    _ldw_scr.handle_click(*_ldw_centre(_ldw_rect))
    assert _ldw_sent == [("act", 1 if _ldw_key == "reject" else 2)], (
        _ldw_key, _ldw_sent)
ok("the hire popup is identified only by an exact field shape (or the "
   "block), its question is 0x124 or 0x125 by the upkeep, and its two "
   "answers go to their own fields")
