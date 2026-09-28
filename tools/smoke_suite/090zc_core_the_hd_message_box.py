# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090zc_core_the_hd_message_box.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - open fix 29's MSGB block parses whole or not at all, LAST; each answer resolves to the live field the box reported, or to nothing
#   - the HD message box: drawn by the App over the held frame wherever a box is up, never the game's picture; one click or key answers once through the box's own field; F12 still shows the picture


# ── THE HD MESSAGE BOX (work order 188, open fix 29) ─────────────
import types as _mb_ns
from core import msgbox as _mb
from core import game_state as _mb_gsmod

# 1. THE BLOCK.
_mb_blk = _mb.build("confirmation", "Really?\rSure?", None, 1, 2)
_mb_g = _mb_ns.SimpleNamespace()
assert _mb.parse(_mb_g, _mb_blk + b"zz", 0) == len(_mb_blk)
assert _mb_g.message_box == {"kind": "confirmation", "field_a": 1,
                             "field_b": 2, "ticks": 0, "title": None,
                             "text": "Really?\rSure?"}, _mb_g.message_box
_mb_t = _mb.build("text", "A body.", "A title", 1)
assert _mb.parse(_mb_g, _mb_t, 0) == len(_mb_t) and \
    _mb_g.message_box["title"] == "A title"
for _mb_bad in (_mb_blk[:-1], b"MSGX" + _mb_blk[4:],
                _mb_blk[:4] + b"\x02" + _mb_blk[5:],        # version 2
                _mb_blk[:5] + b"\x09" + _mb_blk[6:]):       # no such kind
    _mb_g2 = _mb_ns.SimpleNamespace()
    assert _mb.parse(_mb_g2, _mb_bad, 0) == 0 and \
        _mb_g2.message_box is None, _mb_bad[:8]
_mb_src = io.open(_mb_gsmod.__file__, encoding="utf-8").read()
assert _mb_src.index("moveblocks.parse(gs, data, pos)") < \
    _mb_src.index("msgbox.parse(gs, data, pos)"), "MSGB is written LAST"
# the answers: the box's own ids, resolved in the LIVE list
_mb_F = lambda i, hk: _mb_ns.SimpleNamespace(index=i, hotkey=hk, x=0, y=0,
                                             x_end=9, y_end=9)
_mb_live = [_mb_F(0, 0), _mb_F(1, ord("Y")), _mb_F(2, ord("N"))]
assert [(k, f.index if f else None) for k, f in _mb.answers(
    {"kind": "confirmation", "field_a": 1, "field_b": 2}, _mb_live)] == \
    [("yes", 1), ("no", 2)]
assert _mb.answers({"kind": "text", "field_a": 5, "field_b": -1},
                   _mb_live) == [("close", None)], \
    "a list from before the box has no such field: nothing to send"
# the text as FMTPARA lays it out: \r breaks the line
assert [p for p, _b in _mb.lines_of("One\rTwo")] == ["One", "Two"]
ok("open fix 29's MSGB block parses whole or not at all, LAST; each answer "
   "resolves to the live field the box reported, or to nothing")

# 2. THE APP. The fallback fixture of 061 (app2, a client that records),
#    a box over the id HD has no screen for — the turn processing's case.
_mb_state = _FbState(12)
_mb_client = _FbClient(_mb_state)
app2._apply_resolution(1920, 1080)
app2.client, app2.connected = _mb_client, True
app2.render_mode = "hd"
_mb_state.fields = [_mb_F(0, 0), _mb_F(1, ord("Y")), _mb_F(2, ord("N"))]
_mb_state.message_box = {"kind": "confirmation", "field_a": 1,
                         "field_b": 2, "ticks": 0, "title": None,
                         "text": "Really risk war?"}
app2._update()
assert not app2._showing_original(), "a box HD can draw: never the picture"
assert app2._handover.holding and app2._handover.notice is None
_mb_before = app2.native_frames["without_f12"]
app2._render()
assert app2.native_frames["without_f12"] == _mb_before
_mb_rects = dict(app2._overlays.box_view.rects)
assert set(_mb_rects) == {"yes", "no"}, _mb_rects
# the picture's two colours of the 061 fixture never reach the window
for _mb_px in (240 + 1440 // 4, 240 + 3 * 1440 // 4):
    assert app2.surface.get_at((_mb_px, 30))[:3] not in ((0, 0, 255),
                                                        (255, 0, 0))
_mb_client.log.clear()
app2._handle_click(*_mb_rects["no"].center)
app2._handle_click(*_mb_rects["no"].center)
assert _mb_client.log == [("ACTIVATE_FIELD", 2)], (
    "one click, one answer, through the box's own field", _mb_client.log)
# a new box is answered again, by its hotkey
_mb_state.message_box = dict(_mb_state.message_box, text="Another?")
app2._showing_original()
_mb_client.log.clear()
import inspect as _mb_inspect
import main as _mb_main
assert "self._overlays.key(event)" in _mb_inspect.getsource(
    _mb_main.App._handle_events)
_mb_ev = _mb_ns.SimpleNamespace(key=pygame.K_y, unicode="y")
app2._overlays.answer_box(_mb.View.answer_key(app2._overlays.box, _mb_state.fields,
                                     _mb_ev))
assert _mb_client.log == [("ACTIVATE_FIELD", 1)], _mb_client.log
# a text box: CLOSE, or a click anywhere (its one full-screen field)
_mb_state.fields = [_mb_F(0, 0), _mb_F(1, 0x1B)]
_mb_state.message_box = {"kind": "warning", "field_a": 1, "field_b": -1,
                         "ticks": 0, "title": None, "text": "No."}
app2._showing_original()
app2._render()
assert set(app2._overlays.box_view.rects) == {"close"}
_mb_client.log.clear()
app2._handle_click(5, 5)
assert _mb_client.log == [("ACTIVATE_FIELD", 1)], _mb_client.log
# F12 is the player's own mode: the picture, the box not drawn by HD
app2.render_mode = "original"
assert app2._showing_original() and app2._overlays.box is None
app2.render_mode = "hd"
_mb_state.message_box = None
app2._showing_original()
assert app2._overlays.box is None and app2._overlays.box_sent is None
# the marking, three homes; the words are the HD string file's
assert "DEVIATION `hud_message_box`" in (_mb.__doc__ or "")
assert "DEVIATION `hud_message_box`" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
_mb_words = json.load(io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                                           "assets", "shared", "msgbox",
                                           "labels.json"),
                              encoding="utf-8"))
assert {k: _mb_words[k] for k in ("yes", "no", "close")} == \
    {"yes": "YES", "no": "NO", "close": "CLOSE"}
ok("the HD message box: drawn by the App over the held frame wherever a box "
   "is up, never the game's picture; one click or key answers once through "
   "the box's own field; F12 still shows the picture")
