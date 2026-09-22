# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 075_core_game_menu_volume_bars_find_bar.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 6 check(s) it holds:
#   - GAME menu volume bars: Find_Bar_Position_ arithmetic round-trips every value the game can produc
#   - pressed words: SETTINGS and the GAME word orange while held (transcribed), a Load row too with i
#   - GAME menu: a double click sends once, the next dialog's field after the list changed, QUIT -> YE
#   - game client: a close after expect_shutdown ends it, one before reconnects
#   - injection: a paced step sends one key per PACE_STATES snapshots; a bool-returning step is not pa
#   - s_settings: the live bytes give the native dialog's 13 boxes, active slot 7, End Of Turn Wait of


# 7b. THE VOLUME BARS (work order 124 C), transcribed. The arithmetic
#     against the source's own numbers, the drawing against the value
#     the snapshot carries, and the gesture: nothing on press or drag,
#     ONE injected click on release, at a native point the game turns
#     into the chosen value.
from screens.game_menu import gmsliders as _gsl
_gsl_cfg = _gm_lay["sliders"]
assert (_gsl_cfg["native_x"], _gsl_cfg["width"], _gsl_cfg["height"],
        _gsl_cfg["range_max"], _gsl_cfg["music_y"],
        _gsl_cfg["sound_y"]) == (144 + 0x3e, 0x9b, 0xc, 0x9c,
                                 25 + 0xc2, 25 + 0xd8)
assert len(_gsl_cfg["blocks"]) == 10
_gsl_reach = {_gsl.native_value(_x, _gsl_cfg) for _x in range(
    _gsl_cfg["native_x"] - 2, _gsl_cfg["native_x"] + _gsl_cfg["width"] + 3)}
assert 155 not in _gsl_reach and {0, 154, 156} <= _gsl_reach
for _v in _gsl_reach:
    assert _gsl.native_value(_gsl.native_x_for(_v, _gsl_cfg),
                             _gsl_cfg) == _v, _v
# The live measurement of 16 September: native x 321 gave 74, 284 gave 50.
assert _gsl.value_to_level(_gsl.native_value(321, _gsl_cfg),
                           _gsl_cfg) == 74
assert _gsl.value_to_level(_gsl.native_value(284, _gsl_cfg),
                           _gsl_cfg) == 50
assert _gsl.value_to_level(8, _gsl_cfg) == 0      # 5 or less is off
_gsl_sent = []

class _GslClient:
    def inject_click(self, x, y): _gsl_sent.append((x, y))
    def activate_field(self, i): pass
    def hold_watchdog(self, s): pass

_gsl_real = (app.client, app.connected)
app.client, app.connected = _GslClient(), True
try:
    _gsl_raw = bytearray(_gm_live)
    _gsl_raw[18], _gsl_raw[20] = 50, 49           # sound, music levels
    _gm_gs.settings_raw = bytes(_gsl_raw)
    _gm_gs.fields = _gm_fields(_gm_fix["menu"])
    _gm_scr.update(_gm_gs)
    assert _gsl.wire_value(_gm_scr, "sound") == 77   # 50 * 155 // 100
    _gsl_bar = _gm_draw.rect(_gm_scr, "sound_bar")
    _gsl_probe = pygame.Surface((app.win_w, app.win_h))
    _gsl_probe.fill((0, 0, 0))
    _gm_scr.render(_gsl_probe)
    _gsl_row = pygame.surfarray.array3d(_gsl_probe)[
        _gsl_bar.x:_gsl_bar.right, _gsl_bar.centery]
    _gsl_on = tuple(_gsl.COL_ON[:3])
    _gsl_lit = [i for i, c in enumerate(map(tuple, _gsl_row))
                if c in (_gsl_on, tuple(_gsl.COL_GLOW[:3]))]
    assert _gsl_lit and abs(max(_gsl_lit) + 1 - round(
        77 * _gsl_bar.w / _gsl_cfg["width"])) <= 2, (_gsl_lit[-1:],)
    _gsl_x = _gsl_bar.x + int(_gsl_bar.w * 0.75)
    assert _gm_scr.handle_click(_gsl_x, _gsl_bar.centery) is None
    _gm_scr.handle_mouse_motion(_gsl_bar.x + int(_gsl_bar.w * 0.25),
                                _gsl_bar.centery)
    _gm_scr.handle_mouse_motion(_gsl_x, _gsl_bar.centery)
    assert _gsl_sent == [], "the press or the drag sent something"
    _gm_scr.handle_left_release(_gsl_x, _gsl_bar.centery)
    assert len(_gsl_sent) == 1, _gsl_sent
    _gsl_want = _gsl._value_at(_gm_scr, "sound", _gsl_x)
    assert _gsl.native_value(_gsl_sent[0][0], _gsl_cfg) == _gsl_want
    assert _gsl_sent[0][1] == _gsl_cfg["sound_y"] + 6
    # Held until the snapshot carries it, then the wire again.
    assert _gsl.shown_value(_gm_scr, "sound") == _gsl_want
    for _k in range(_gm_wp.EFFECT_PAIRS + 1):
        _gsl_next = _GmState()
        _gsl_next.settings_raw, _gsl_next.fields = \
            _gm_gs.settings_raw, _gm_gs.fields
        _gm_scr.update(_gsl_next)
    assert _gsl.shown_value(_gm_scr, "sound") == 77
    assert "OMISSION" not in _gsl.__doc__ and \
        "TRANSCRIBED" in _gsl.__doc__
finally:
    app.client, app.connected = _gsl_real
ok("GAME menu volume bars: Find_Bar_Position_ arithmetic round-trips "
   "every value the game can produce, the live 74/50, lit width from _settings, one click on "
   "release and none on press or drag, preview held to the effect")

# 7c. THE PRESSED WORD (work order 124 B). Transcribed: a held button
#     draws frame 1 of its picture, the word in orange (palette 126);
#     the rows have no pressed state in the original, so theirs is an
#     HD INVENTION and has to stay marked. Drawn on the press, whatever
#     the game does with it, and gone on release.
import core.mouse as _pf_mouse
from core import pressfeedback as _pf
assert tuple(_pf.pressed_colour()[:3]) == (252, 136, 0)
for _pf_mark in ("TRANSCRIBED", "HD INVENTION", "OMISSION"):
    assert _pf_mark in _pf.__doc__, _pf_mark
assert "HD INVENTION — the load and save rows" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
_pf_saved = _pf_mouse.pos
_pf_real = (app.client, app.connected)
try:
    app.client, app.connected = _GslClient(), True
    _gm_gs.fields = _gm_fields(_gm_fix["menu"])
    _gm_scr.update(_gm_gs)
    _pf_r = _gm_draw.rect(_gm_scr, "menu_settings")
    _pf_mouse.pos = lambda: _pf_r.center
    _pf_said = []
    _pf_rt = app.style.render_text
    app.style.render_text = lambda _t, _s, _c, *a, **k: (
        _pf_said.append((_t, tuple(_c))), _pf_rt(_t, _s, _c, *a, **k))[1]
    _gm_scr.handle_click(*_pf_r.center)
    _gm_scr.render(surf)
    _pf_word = _gm_draw.word(_gm_scr, "menu", "settings")
    assert (_pf_word, (252, 136, 0)) in _pf_said, "no pressed SETTINGS"
    _pf_said.clear()
    _gm_scr.handle_left_release(*_pf_r.center)
    _gm_scr.render(surf)
    assert (_pf_word, (252, 136, 0)) not in _pf_said, "still pressed"
    # A row, in the Load dialog: the invention. The row draws the
    # engine's name (open fix 14 applied), so the slot message is here.
    _gm_gs.save_slots = _gm_wp.parse_save_slots(bytes([2, 10]) + (
        bytes([0, 0]) + b"Pressed Row".ljust(37, b"\0")
        + b"Stardate:3500.0".ljust(25, b"\0")
        + b"31, 126 13:52".ljust(25, b"\0")) * 10)
    _gm_gs.fields = _gm_fields(_gm_fix["load"])
    _gm_scr.update(_gm_gs)
    _pf_band = _gm_draw.bands(_gm_draw.rect(_gm_scr, "slot_list"),
                              _gm_nodes.SLOTS)[2]
    _pf_mouse.pos = lambda: _pf_band.center
    _pf_said.clear()
    _gm_scr._sent = object()          # the gate closed: nothing may go
    _gm_scr.can_send = lambda: False
    _gm_scr.handle_click(*_pf_band.center)
    _gm_scr.render(surf)
    assert ("Pressed Row", (252, 136, 0)) in _pf_said, \
        "a pressed row is not drawn pressed while the send is refused"
    _gm_scr.handle_left_release(*_pf_band.center)
    _gm_gs.save_slots = None
    del _gm_scr.can_send
    _gm_scr._sent = None
    # The GAME word in the galaxy frame.
    _pf_gm = d.screens["galaxy_map"]
    _pf_title = pygame.Rect(*app.layout.rect(
        _pf_gm._data["frame"]["title_rect"]))
    _pf_mouse.pos = lambda: _pf_title.center
    _pf_gm.pressed.press("title", _pf_title)
    _pf_seen = []
    _pf_gf = app.style.get_font
    class _PfFont:
        def __init__(self, f): self.f = f
        def __getattr__(self, n): return getattr(self.f, n)
        def render(self, txt, aa, col, *a):
            _pf_seen.append((txt, tuple(col[:3])))
            return self.f.render(txt, aa, col, *a)
    app.style.get_font = lambda s: _PfFont(_pf_gf(s))
    try:
        _pf_gm._render_title(surf)
    finally:
        app.style.get_font = _pf_gf
    assert ("GAME", (252, 136, 0)) in _pf_seen, _pf_seen
    _pf_gm.handle_left_release(*_pf_title.center)
    assert not _pf_gm.pressed.is_down("title")
finally:
    _pf_mouse.pos = _pf_saved
    app.style.render_text = _pf_rt
    app.client, app.connected = _pf_real
ok("pressed words: SETTINGS and the GAME word orange while held "
   "(transcribed), a Load row too with its send refused (HD INVENTION, "
   "marked), all gone on release")

# 8. THE GATE: a second click before the list changes sends nothing;
#    after the change it goes. QUIT -> YES stands the watchdog down
#    FIRST (decision 62).
class _GmClient:
    def __init__(self):
        self.log, self.stats = [], {"state": 0}
    def activate_field(self, i): self.log.append(("activate", i))
    def expect_shutdown(self): self.log.append(("shutdown",))
    def hold_watchdog(self, s): pass
    def inject_key(self, k): self.log.append(("key", k))
_gm_real_client, _gm_real_conn = app.client, app.connected
app.client, app.connected = _GmClient(), True
try:
    _gm_scr.enter(_gm_gs)
    _gm_gs.fields = _gm_fields(_gm_fix["menu"])
    _gm_scr.update(_gm_gs)
    _gm_scr.press("O")
    _gm_scr.press("O")
    assert app.client.log == [("activate", 5)], app.client.log
    _gm_gs.fields = _gm_fields(_gm_fix["settings"])
    _gm_scr.update(_gm_gs)
    _gm_scr.press("A")
    assert app.client.log[-1] == ("activate", 27), app.client.log
    app.client.log.clear()
    _gm_gs.fields = _gm_fields(_gm_fix["menu"])
    _gm_scr.update(_gm_gs)
    _gm_scr.press("Q")
    _gm_gs.fields = _gm_fields(_gm_fix["confirm"])
    _gm_scr.update(_gm_gs)
    _gm_scr.press("Y")
    assert app.client.log[-2:] == [("shutdown",), ("activate", 1)], \
        app.client.log
finally:
    app.client, app.connected = _gm_real_client, _gm_real_conn
    _gm_scr.exit()
    d.close_overlay()
ok("GAME menu: a double click sends once, the next dialog's field "
   "after the list changed, QUIT -> YES disarms before YES")

# 9. A REQUESTED END IS NOT A LOST LINK: after expect_shutdown a close
#    ends the client and never reconnects.
_gm_c = _gm_gc.GameClient()
_gm_rc = []
_gm_c._reconnect = lambda: _gm_rc.append(1)
_gm_c._lost("before")
assert _gm_rc == [1] and not _gm_c.game_ended
_gm_c.expect_shutdown()
_gm_c._lost("after")
assert _gm_rc == [1] and _gm_c.game_ended
ok("game client: a close after expect_shutdown ends it, one before "
   "reconnects")

# 10. A PACED STEP sends one item per PACE_STATES snapshots, and a
#     run that returns a bool (click_banner) is not paced.
class _GmPC:
    def __init__(self):
        self.stats, self.keys = {"state": 0}, []
    def inject_key(self, k): self.keys.append(k)
    def hold_watchdog(self, s): pass
_gm_pc = _GmPC()
_gm_ch = _gm_inj.InjectionChain(_gm_pc, [(
    "paced", lambda f: True,
    lambda c, f: _gm_inj.paced_keys(None, [1, 2, 3]))])
_gm_st = _GmState()
_gm_st.fields = _gm_fields(_gm_fix["save"])
for _tick in range(12):
    _gm_ch.update(_gm_st)
    _gm_pc.stats["state"] += 1
    assert len(_gm_pc.keys) <= _tick // _gm_inj.PACE_STATES + 1
assert _gm_pc.keys == [1, 2, 3] and _gm_ch.done
_gm_ch2 = _gm_inj.InjectionChain(_gm_pc, [(
    "bool", lambda f: True, lambda c, f: True)])
_gm_ch2.update(_gm_st)
assert _gm_ch2.done
ok("injection: a paced step sends one key per PACE_STATES snapshots; "
   "a bool-returning step is not paced")

# 11. THE SETTINGS SPEC reproduces the native dialog of the live
#     snapshot (row order skips random_events), and row 1 reads 0
#     outside single player (loadsave.cpp:1147-1151).
assert _gm_set.SPEC.verified
assert _gm_set.option_flags(_gm_live, 0) == \
    [1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0]
assert _gm_set.option_flags(_gm_live, 2)[1] == 0
assert _gm_set.parse(_gm_live).active_save_slot == 7
ok("s_settings: the live bytes give the native dialog's 13 boxes, "
   "active slot 7, End Of Turn Wait off in multiplayer")
