# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 069_galaxy_map_game_menu_overlay_opens_over_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - GAME menu: overlay opens over the galaxy map at screen 8, undimmed, and closes when the game lea


# 3. THE OVERLAY CLAIMS SCREEN 8 over the galaxy map, undimmed, and
#    closes itself when the game leaves 8 (decision 59).
_gm_scr = d.screens["game_menu"]
assert d.screen_map.get(8) == "game_menu" and _gm_scr.IS_OVERLAY
assert _gm_scr.OVERLAY_DIM == 0
d.switch_to("galaxy_map")
_gm_gs = _GmState()
_gm_gs.current_screen = 8
_gm_gs.fields = _gm_fields(_gm_fix["menu"])
d.update_from_game(_gm_gs)
assert d.overlay_name == "game_menu" and d.active_name == "galaxy_map"
_gm_gs0 = _GmState()
_gm_gs0.current_screen = 0
d.update_from_game(_gm_gs0)
assert d.overlay is None and d.active_name == "galaxy_map"
ok("GAME menu: overlay opens over the galaxy map at screen 8, "
   "undimmed, and closes when the game leaves it")
