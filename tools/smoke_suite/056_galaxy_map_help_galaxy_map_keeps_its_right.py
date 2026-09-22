# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 056_galaxy_map_help_galaxy_map_keeps_its_right.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - help: galaxy map keeps its right-drag pan over the map
#   - galaxy map right click: CANCEL_FIELD on the live grid field exactly once before the pan; nothing


# The galaxy map uses the right button for its pan drag. The
# original's help list for that screen deliberately does not
# cover the map area (evanhelp.cpp:4), so the two never collide —
# asserted here because the collision would be silent: a help box
# would simply appear instead of the map moving.
d.switch_to("galaxy_map")
_gm = d.active
_gm.update(None)
_nav = next(b for b in _gm.boxes if b.name == "nav_colonies")
assert _gm.handle_right_button(True, *_nav.screen_rect.center) is True
assert _gm.help.visible and _gm._pan_from is None
_gm.handle_right_button(True, *_nav.screen_rect.center)   # closes
assert not _gm.help.visible
_map = next(b for b in _gm.boxes if b.name == "map_area")
_gm.handle_right_button(True, *_map.screen_rect.center)
assert not _gm.help.visible, "the map area must not open help"
assert _gm._pan_from is not None, "right drag over the map broke"
_gm.handle_right_button(False, *_map.screen_rect.center)
ok("help: galaxy map keeps its right-drag pan over the map")

# THE RIGHT CLICK ON THE MAP IS THE GAME'S CANCEL, AND NOTHING ELSE
# (layout.json `map_cancel`; mainscr_main.cpp:397-404, fields.cpp:
# 1360). CANCEL_FIELD on the grid field found in the live list, once,
# before the pan; a press over a help region sends nothing (decision
# 38); no grid field in the list, or no connection, sends nothing.
from core.game_state import FieldInfo as _MvField

class _MvRec:
    def __init__(self):
        self.log = []

    def cancel_field(self, _i):
        self.log.append(("cancel", _i))

    def activate_field(self, _i):
        self.log.append(("act", _i))

    def inject_click(self, _x, _y):
        self.log.append(("click", _x, _y))

    def inject_key(self, _k):
        self.log.append(("key", _k))

assert _gm._state is not None, "the galaxy map has no state to test on"
# FIELD 0 FIRST — the engine cannot send a list without one
# (FIELD_ZERO_ROW). It matters here: `mapboxes.live_field` matches
# on type and rect, and slot 0 carries whatever the last list left.
_mv_zero = _MvField(index=FIELD_ZERO_ROW[0], x=FIELD_ZERO_ROW[1],
                    y=FIELD_ZERO_ROW[2], x_end=FIELD_ZERO_ROW[3],
                    y_end=FIELD_ZERO_ROW[4],
                    field_type=FIELD_ZERO_ROW[5],
                    hotkey=FIELD_ZERO_ROW[6])
_mv_grid = _MvField(index=23, x=22, y=22, x_end=527, y_end=421,
                    field_type=12, hotkey=0)
_mv_game = _MvField(index=6, x=249, y=5, x_end=300, y_end=30,
                    field_type=0, hotkey=ord("G"))
_mv_real = (app.client, app.connected, _gm._state.fields)
_mv_c = _map.screen_rect.center
try:
    app.client, app.connected = _MvRec(), True
    _gm._state.fields = [_mv_zero, _mv_game, _mv_grid]
    _gm.handle_right_button(True, *_mv_c)
    assert app.client.log == [("cancel", 23)], app.client.log
    assert _gm._pan_from is not None, "the pan must still start"
    _gm.handle_right_button(False, *_mv_c)
    app.client.log.clear()
    assert _gm.handle_right_button(True, *_nav.screen_rect.center) is True
    assert _gm.help.visible and app.client.log == [], app.client.log
    _gm.handle_right_button(True, *_nav.screen_rect.center)   # closes
    _gm._state.fields = [_mv_zero, _mv_game]
    _gm.handle_right_button(True, *_mv_c)
    _gm.handle_right_button(False, *_mv_c)
    _gm._state.fields = [_mv_zero, _mv_game, _mv_grid]
    app.connected = False
    _gm.handle_right_button(True, *_mv_c)
    _gm.handle_right_button(False, *_mv_c)
    assert app.client.log == [], app.client.log
finally:
    app.client, app.connected, _gm._state.fields = _mv_real
assert "TRANSCRIBED" in _gm._data["map_cancel"]["_transcribed"]
ok("galaxy map right click: CANCEL_FIELD on the live grid field exactly "
   "once before the pan; nothing over help, without the field or "
   "without a connection")
