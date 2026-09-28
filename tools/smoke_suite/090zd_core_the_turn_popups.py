# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090zd_core_the_turn_popups.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - open fix 49's TPOP block parses whole or not at all, LAST, for every kind; each popup's content is its own texts and its own fields
#   - the turn popups: drawn by the App over the held frame, never the game's picture; an option or button answers through its own field — clicked where the original reads the pointer — once per state, again after RESEND_AFTER; a box wins over a popup, F12 shows the picture


# ── THE TURN-TIME POPUPS (work order 188 Part 4, open fix 49) ────
import types as _tp_ns
from core import turnpopup as _tp
from core import handover as _tp_ho

# 1. THE BLOCK, every kind; stand-in texts only (no game text committed).
_tp_msgs = [{"text": "Row one.", "jumps": 1, "colony": 3, "page": 1,
             "first_field": 4, "fields": 2},
            {"text": "Row two.", "jumps": 0, "colony": -1, "page": 1,
             "first_field": 6, "fields": 1},
            {"text": "Row three.", "jumps": 0, "colony": -1, "page": 2,
             "first_field": -1, "fields": 0}]
_tp_ts = _tp.build("turn_summary", [1, 2, 1, 2, 3, 4, 6, 7, 8, 0],
                   messages=_tp_msgs)
_tp_sys = {"star": 5, "grid_field": 9,
           "planets": [{"field": 6, "planet": 0}, {"field": 7, "planet": 1}],
           "ships": [{"field": 8, "ship": 2}]}
_tp_blocks = {
    "turn_summary": _tp_ts,
    "science": _tp.build("science", [1, 1, 1, 42], text="Footer."),
    "planet_choice": _tp.build("planet_choice", [5, 0, 0, 0, 3, 1],
                               title="Choose.", system=_tp_sys),
    "combat_target": _tp.build("combat_target", [5, 0, 3], system=_tp_sys,
                               targets={"colonies": [2], "players": [1]}),
    "gnn": _tp.build("gnn", [9, 7, 0, 9], text="News."),
    "leader_hire": _tp.build("leader_hire", [0, 100, 5, 0, 2, 3, -1000, 0,
                                             1]),
}
for _tp_k, _tp_b in _tp_blocks.items():
    _tp_g = _tp_ns.SimpleNamespace()
    assert _tp.parse(_tp_g, _tp_b + b"zz", 0) == len(_tp_b), _tp_k
    assert _tp_g.turn_popup["kind"] == _tp_k
    for _tp_cut in (_tp_b[:-1], b"TPOX" + _tp_b[4:],
                    _tp_b[:4] + b"\x02" + _tp_b[5:]):
        _tp_g2 = _tp_ns.SimpleNamespace()
        assert _tp.parse(_tp_g2, _tp_cut, 0) == 0 and \
            _tp_g2.turn_popup is None, (_tp_k, _tp_cut[:8])
_tp_g = _tp_ns.SimpleNamespace()
_tp.parse(_tp_g, _tp_ts, 0)
assert [m["text"] for m in _tp_g.turn_popup["messages"]] == \
    ["Row one.", "Row two.", "Row three."]
_tp_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                               "game_state.py"), encoding="utf-8").read()
assert _tp_src.index("msgbox.parse(gs, data, pos)") < \
    _tp_src.index("turnpopup.parse(gs, data, pos)"), "TPOP is written LAST"

# the content: its own texts and its own fields, the pointer where the
# original reads it
_tp_F = lambda i, x=0, y=0, w=9, h=9, hk=0: _tp_ns.SimpleNamespace(
    index=i, x=x, y=y, x_end=x + w, y_end=y + h, hotkey=hk, field_type=7)
_tp_state = _tp_ns.SimpleNamespace(
    fields=[_tp_F(i, 10 * i, 10 * i) for i in range(10)], stars=[],
    planets_raw=[], leaders_raw=[], ships_raw=[], player_raw=[])
_tp_W = dict(_tp.DEFAULT_WORDS)
_tp_c = _tp.content(_tp_g.turn_popup, _tp_state, _tp_W)
assert [o[0] for o in _tp_c["options"]] == ["Row one.", "Row two."], \
    "the page shown, and only it"
assert _tp_c["options"][0][1][0] == "click" and \
    _tp_c["options"][0][1][1].index == 4, "a jump row is CLICKED (the pointer)"
assert _tp_c["options"][1][1] is None, "a row that does not jump sends nothing"
assert [b[0] for b in _tp_c["buttons"]] == ["PREV", "NEXT", "CLOSE"] and \
    _tp_c["buttons"][0][1] is None and _tp_c["buttons"][1][1][1].index == 2
assert _tp_c["title"] == "TURN SUMMARY"
_tp_g2 = _tp_ns.SimpleNamespace()
_tp.parse(_tp_g2, _tp_blocks["science"], 0)
_tp_c2 = _tp.content(_tp_g2.turn_popup, _tp_state, _tp_W)
assert _tp_c2["lines"][0] == "Footer." and _tp_c2["buttons"][0][1] is None, \
    "no full-screen field in the list: CONTINUE sends nothing yet"
_tp_g3 = _tp_ns.SimpleNamespace()
_tp.parse(_tp_g3, _tp_blocks["planet_choice"], 0)
_tp_c3 = _tp.content(_tp_g3.turn_popup, _tp_state, _tp_W)
assert [a[1].index for _l, a in _tp_c3["options"]] == [6, 7] and \
    all(a[0] == "click" for _l, a in _tp_c3["options"])
assert _tp_c3["buttons"] == [("CLOSE", ("click", _tp_state.fields[3]))]
_tp_g4 = _tp_ns.SimpleNamespace()
_tp.parse(_tp_g4, _tp_blocks["leader_hire"], 0)
_tp_c4 = _tp.content(_tp_g4.turn_popup, _tp_state, _tp_W)
assert [(l, a[1].index) for l, a in _tp_c4["buttons"]] == \
    [("REJECT", 3), ("HIRE", 2)], "REJECT left, HIRE right, their own fields"
# the kinds no live run reached (work order 188: a new system and a
# leader's level) — their content from stand-in blocks, and the landing's
for _tp_k, _tp_b, _tp_want in (
        ("discovery", _tp.build("discovery", [5, 0, 2], title="A star.",
                                system=_tp_sys), 2),
        ("leader_level", _tp.build("leader_level", [0, 0, 5, 1]), 1),
        ("landing", _tp.build("landing", [0, 1, 5, 3], title="A planet."),
         3),
        ("gnn", _tp.build("gnn", [9, 7, 0, 9], text="News."), None)):
    _tp_gk = _tp_ns.SimpleNamespace()
    _tp.parse(_tp_gk, _tp_b, 0)
    _tp_ck = _tp.content(_tp_gk.turn_popup, _tp_state, _tp_W)
    _tp_act = _tp_ck["buttons"][-1][1]
    if _tp_want is None:        # the GNN: its one full-screen field
        assert _tp_act is None, (_tp_k, "no full-screen field listed")
    else:
        assert _tp_act is not None and _tp_act[1].index == _tp_want, \
            (_tp_k, _tp_act)
    if _tp_k == "discovery":
        assert [o[1] for o in _tp_ck["options"]] == [None, None], \
            "a discovery's planets are shown, not chosen"
ok("open fix 49's TPOP block parses whole or not at all, LAST, for every "
   "kind; each popup's content is its own texts and its own fields")

# 2. THE APP (061's fallback fixture, app2): the Turn Summary under 40.
_tp_st = _FbState(40)
_tp_client = _FbClient(_tp_st)
_tp_client.inject_click = lambda x, y: _tp_client.log.append(
    ("INJECT_CLICK", x, y))
app2._apply_resolution(1920, 1080)
app2.client, app2.connected = _tp_client, True
app2.render_mode = "hd"
_tp_st.fields = [_tp_F(i, 10 * i, 10 * i) for i in range(10)]
_tp_st.message_box = None
_tp_st.turn_popup = _tp_g.turn_popup
app2._update()
assert not app2._showing_original() and app2._handover.holding
_tp_n = app2.native_frames["without_f12"]
app2._render()
assert app2.native_frames["without_f12"] == _tp_n
_tp_rects = [(r, a) for r, a in app2._overlays.popup_view.rects if a is not None]
_tp_row = next(r for r, a in _tp_rects if a[1].index == 4)
_tp_client.log.clear()
app2._handle_click(*_tp_row.center)
app2._handle_click(*_tp_row.center)
assert _tp_client.log == [("INJECT_CLICK", 44, 44)], _tp_client.log
# the popup stands still: a resend only after RESEND_AFTER snapshots
_tp_client.stats["state"] = _tp.RESEND_AFTER + 1
app2._handle_click(*_tp_row.center)
assert len(_tp_client.log) == 2, _tp_client.log
# a box over the popup wins, F12 shows the picture, leaving forgets
_tp_st.message_box = {"kind": "text", "field_a": 1, "field_b": -1,
                      "ticks": 0, "title": None, "text": "Box."}
assert _tp_ho.overlay_for(app2)[0] == "box"
_tp_st.message_box = None
app2.render_mode = "original"
assert _tp_ho.overlay_for(app2) is None and app2._showing_original()
app2.render_mode = "hd"
# the Leaders screen draws its own hire popup: not ours there
_tp_st.turn_popup = dict(_tp_g4.turn_popup)
_tp_st.turn_popup["args"] = list(_tp_st.turn_popup["args"])
_tp_st.turn_popup["args"][7] = 1
assert _tp_ho.overlay_for(app2) is None
_tp_st.turn_popup = None
app2._showing_original()
assert app2._overlays.popup is None and app2._overlays.popup_view.sent is None
# the marking, three homes; the ids named where the table lives
assert "DEVIATION `hud_turn_popup`" in (_tp.__doc__ or "")
assert "DEVIATION `hud_turn_popup`" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
from core import screen_names as _tp_sn
assert all(_tp_sn.SCREENS[i] == ("(synthetic)", None) for i in range(59, 65))
assert set(_tp.IDS) == {40, 52, 33, 59, 60, 61, 62, 63, 64}
ok("the turn popups: drawn by the App over the held frame, never the game's "
   "picture; an option or button answers through its own field — clicked "
   "where the original reads the pointer — once per state, again after "
   "RESEND_AFTER; a box wins over a popup, F12 shows the picture")
