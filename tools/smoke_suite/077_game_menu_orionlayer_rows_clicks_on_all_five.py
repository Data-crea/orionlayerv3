# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 077_game_menu_orionlayer_rows_clicks_on_all_five.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - OrionLayer rows: clicks on all five bands, their boundaries and a swatch send nothing; floor, pr
#   - Game Settings: each of the 13 engine rows still activates its own label field exactly once
#   - OrionLayer rows end above ACCEPT; restart note only while saved != active; swatches are the sele


# ── The OrionLayer rows in Game Settings (fundament 63) ──
from screens.game_menu import gmorion as _go
from core import usersettings as _go_us
import tempfile as _go_tmp

class _GoClient:
    def __init__(self):
        self.log, self.stats = [], {"state": 0}
    def activate_field(self, i):
        self.log.append(("activate", i))
        self.stats["state"] += 10
    def inject_click(self, x, y): self.log.append(("click", x, y))
    def inject_key(self, k): self.log.append(("key", k))
    def expect_shutdown(self): self.log.append(("shutdown",))
    def hold_watchdog(self, s): pass
    def cancel_field(self, i): self.log.append(("cancel", i))

_go_scr = d.screens["game_menu"]
_go_real = (app.client, app.connected, getattr(app, "user_settings", None))
_go_dir = _go_tmp.TemporaryDirectory()
app.client, app.connected = _GoClient(), True
app.user_settings = _go_us.UserSettings(
    path=os.path.join(_go_dir.name, "user_settings.json"))
try:
    _go_gs = _GmState()
    _go_gs.current_screen = 8
    _go_gs.settings_raw = _gm_live
    _go_gs.fields = _gm_fields(_gm_fix["settings"])
    _go_scr.enter(_go_gs)
    _go_scr.update(_go_gs)
    assert "HD EXTENSION" in (_go.__doc__ or ""), "gmorion lost its marking"
    _go_scr_src = open(os.path.join(SCREENS_DIR, "game_menu", "screen.py"),
                       encoding="utf-8").read()
    assert "they have no field (HD EXTENSION, fundament 63)" in _go_scr_src, \
        "the click branch in screen.py lost its HD EXTENSION marking"
    _go_geo = _go.bands(_go_scr)

    # 14. EVERY POINT OF THE ORIONLAYER ROWS SENDS NOTHING — the four
    #     bands, the boundaries between them, and the swatches; the
    #     floor and preset rows cycle their values.
    _go_pts = [(_r.centerx, _r.centery) for _n, _r in _go_geo.items()
               if _n in _go.BANDS]
    _go_pts += [(_go_geo["floor"].centerx, _go_geo["floor"].top),
                (_go_geo["colours"].centerx, _go_geo["colours"].top),
                _go_geo["swatches"][3].center]
    _go_before = (app.user_settings.get("floor_lift"),
                  app.user_settings.get("player_colors"),
                  app.user_settings.get("monster_values"))
    assert _go_before[2] == "on", "the monster values switch defaults on"
    # Since work order 170 the frame colour row adds its bar and RESET.
    # Since work order 174 the Panel glass row adds its bar and RESET.
    assert tuple(_go_geo) == _go.BANDS + ("swatches", "hue_bar",
                                          "hue_reset", "sat_bar",
                                          "bright_bar", "glass_bar",
                                          "glass_reset"), tuple(_go_geo)
    for _p in _go_pts:
        _go_scr.handle_click(*_p)
    assert app.client.log == [], app.client.log
    assert app.user_settings.get("floor_lift") != _go_before[0]
    assert app.user_settings.get("player_colors") != _go_before[1]
    assert app.user_settings.get("monster_values") == "off", (
        "one click on the monster row must turn the switch off")
    _go_scr.render(surf)
    ok("OrionLayer rows: clicks on all seven bands, their boundaries and a "
       "swatch send nothing; floor, preset and monster rows cycle their "
       "values")

    # 15. EVERY ENGINE ROW STILL SENDS EXACTLY WHAT IT SENT: its own
    #     label field, once.
    _go_labels = _gm_nodes.option_toggles(_go_gs.fields)
    _go_rows = _gm_draw.bands(_gm_draw.rect(_go_scr, "settings_rows"), 13)
    for _i, _r in enumerate(_go_rows):
        app.client.log.clear()
        _go_scr.handle_click(*_r.center)
        assert app.client.log == [("activate", _go_labels[_i].index)], \
            (_i, app.client.log)
    ok("Game Settings: each of the 13 engine rows still activates its own "
       "label field exactly once")

    # 16. THE ROWS END ABOVE ACCEPT; the restart note shows only while the
    #     saved preset differs from the active one; the swatches are the
    #     selected preset's; ACCEPT and exit write once.
    _go_acc = _gm_draw.rect(_go_scr, "settings_accept")
    assert _go_geo[_go.BANDS[-1]].bottom <= _go_acc.top, (
        _go_geo[_go.BANDS[-1]], _go_acc)
    assert _go_geo["divider"].top >= _gm_draw.rect(
        _go_scr, "settings_rows").bottom
    _go_said = []
    _go_rt = app.style.render_text
    app.style.render_text = lambda _t, *_a, **_k: (_go_said.append(_t),
                                                   _go_rt(_t, *_a, **_k))[1]
    try:
        _go_note = _go_scr.words["words"]["orionlayer"]["restart"]
        app.user_settings.set("player_colors", palette.active_preset())
        _go_scr.render(surf)
        assert _go_note not in _go_said
        app.user_settings.set("player_colors", "okabe_ito")
        _go_said.clear()
        _go_scr.render(surf)
        assert _go_note in _go_said, (
            f"restart note {_go_note!r} not drawn: active preset "
            f"{palette.active_preset()!r}, saved "
            f"{app.user_settings.get('player_colors')!r}, node "
            f"{_go_scr.node!r}, drawn {_go_said}")
    finally:
        app.style.render_text = _go_rt
    _go_sw = [tuple(surf.get_at(_r.center))[:3] for _r in _go_geo["swatches"]]
    assert _go_sw == [tuple(_c) for _c in
                      _pc.base(app.colors, "okabe_ito")], _go_sw
    app.client.log.clear()
    _go_scr.press("A")
    _go_path = app.user_settings.path
    assert os.path.exists(_go_path)
    _go_m = os.path.getmtime(_go_path)
    assert _go_us.save(app.user_settings) is False
    assert _go_us.load(_go_path).get("player_colors") == "okabe_ito"
    ok("OrionLayer rows end above ACCEPT; restart note only while saved != "
       "active; swatches are the selected preset's; ACCEPT writes, a second "
       "save does not")
finally:
    # The frame colour row's centre click turned the HUD's hue; the rest
    # of the suite measures the measured blue.
    from core.hud import style as _go_hs
    _go_hs.set_tone(None, None, None)
    # ...and the Panel glass row's centre click moved the slider (174).
    from core.hud import glass as _go_gl
    _go_gl.set_value(None)
    _go_scr.exit()
    d.close_overlay()
    app.client, app.connected = _go_real[0], _go_real[1]
    if _go_real[2] is None:
        del app.user_settings
    else:
        app.user_settings = _go_real[2]
    _go_dir.cleanup()
