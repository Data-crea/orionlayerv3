# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 076_galaxy_map_galaxy_map_parks_only_while_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - galaxy map parks only while the game reports screen 0


# 12. THE GALAXY MAP DOES NOT PARK UNDER THE OVERLAY: field 9 is a
#     Load slot row there.
_gm_gal = d.screens["galaxy_map"]
d.switch_to("galaxy_map")
_gm_parks = []
_gm_real_park = _gm_gal._viewctl.park_game
_gm_gal._viewctl.park_game = lambda a, s, *_i: _gm_parks.append(
    s.current_screen)
try:
    _gm_gs8 = _GmState()
    _gm_gs8.current_screen = 8
    # The map's own list under both screen numbers, so the screen
    # number is the only thing that differs (work order 128 C added
    # the list-shape condition beside it).
    _gm_gs8.fields = _gm_fields(__import__("json").load(open(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools",
        "galaxy_box_fields.json")))["closed"])
    _gm_gal.update(_gm_gs8)
    _gm_gs8.current_screen = 0
    _gm_gal.update(_gm_gs8)
finally:
    _gm_gal._viewctl.park_game = _gm_real_park
assert _gm_parks == [0], _gm_parks
ok("galaxy map parks only while the game reports screen 0")
