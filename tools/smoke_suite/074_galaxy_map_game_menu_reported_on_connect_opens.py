# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 074_galaxy_map_game_menu_reported_on_connect_opens.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - GAME menu reported on connect opens over the galaxy map, not over the screen that happened to be


# 7a'. A CLIENT THAT CONNECTS WHILE THE MENU IS OPEN (work order 125
#      found it, 126 D fixed it). The app starts on the main menu; the
#      first snapshot already reports screen 8. The overlay must open
#      over the galaxy map (OVERLAY_PARENT, mainscr_main.cpp:609-613),
#      not over the main menu's backdrop — and the ordinary path, the
#      map already active, must not re-enter the map.
_cp_app, _ = _pv.build_screen(1920, 1080)
_cp_d = _cp_app.dispatcher
_cp_d.switch_to("main_menu")
assert _cp_d.active_name == "main_menu"
_cp_gs = _GmState()
_cp_gs.current_screen = 8
_cp_gs.settings_raw = _gm_live
_cp_gs.fields = _gm_fields(_gm_fix["menu"])
_cp_d.update_from_game(_cp_gs)
assert (_cp_d.active_name, _cp_d.overlay_name) == (
    "galaxy_map", "game_menu"), (_cp_d.active_name, _cp_d.overlay_name)
_cp_map = _cp_d.active
_cp_d.close_overlay()
_cp_d.update_from_game(_cp_gs)
assert _cp_d.active is _cp_map and _cp_d.overlay_name == "game_menu"
ok("GAME menu reported on connect opens over the galaxy map, not over the "
   "screen that happened to be active")
