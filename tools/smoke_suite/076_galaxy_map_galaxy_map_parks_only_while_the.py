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
# The 2 check(s) it holds:
#   - galaxy map parks only while the game reports screen 0
#   - galaxy map does not park while a research screen is up (36, 53)


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


# 12b. AND IT DOES NOT PARK WHILE A RESEARCH SCREEN IS UP — work
#      order 165, closing the item its "status of the twelve
#      questions" leaves owed under Q4 ("map parking: select mode now
#      reports 53, change mode 36. Owed: a check that parking fires on
#      neither").
#
# WHY IT IS ITS OWN CHECK AND NOT A THIRD NUMBER IN THE ONE ABOVE:
# screen 8 is the GAME popup, where field 9 is a Load slot row that
# loads at once. 36 and 53 are worse than that. In the research list
# field 9 is a CHOICE ROW, and its commit reads the game's own pointer
# (tech.cpp:354-369) — so a park sent there either commits whatever the
# player's mouse happens to rest on, or dereferences null in the game
# process when it rests on nothing (open fix 23, seen as a SIGSEGV in
# work order 128 C). The guard that stops it is the same one, but what
# it is stopping is not the same kind of accident.
#
# 36 is TECH_CHANGE, the engine's own number (core/screen_names.py:53).
# 53 is synthetic and wire-only (open fix 24, :80). Both are read from
# that table rather than typed here, so a renumbering cannot leave this
# check asserting about an id nothing uses.
from core import screen_names as _gm_scr_names
_gm_res_ids = sorted(_i for _i, (_n, _slug) in _gm_scr_names.SCREENS.items()
                     if _slug in ("research", "research_select"))
assert _gm_res_ids == [36, 53], (
    f"the research screen ids are {_gm_res_ids}, not [36, 53] — this "
    f"check is about the two lists whose field 9 is a choice row, and "
    f"it has to be about the ids the tree actually uses")
_gm_res_parks = []
_gm_real_park2 = _gm_gal._viewctl.park_game
_gm_gal._viewctl.park_game = lambda a, s, *_i: _gm_res_parks.append(
    s.current_screen)
try:
    _gm_res_gs = _GmState()
    # THE MAP'S OWN FIELD LIST under every id, so the id is the only
    # thing that differs. That is the harder case on purpose: the real
    # research list would fail the shape test as well, and a check that
    # passed for THAT reason would not be testing the id at all.
    _gm_res_gs.fields = _gm_gs8.fields
    for _gm_res_id in _gm_res_ids:
        _gm_res_gs.current_screen = _gm_res_id
        _gm_gal.update(_gm_res_gs)
    # …and the control: the same state at screen 0 still parks, so the
    # run above proves the id stopped it and not the harness.
    _gm_res_gs.current_screen = 0
    _gm_gal.update(_gm_res_gs)
finally:
    _gm_gal._viewctl.park_game = _gm_real_park2
assert _gm_res_parks == [0], (
    f"the galaxy map parked while a research screen was up: "
    f"{_gm_res_parks}. Field 9 in that list is a choice row, and the "
    f"commit reads the game's own pointer — a park sent there commits "
    f"the player's hover or crashes the game")
ok("galaxy map does not park while a research screen is up (36 "
   "TECH_CHANGE, 53 select — field 9 is a choice row there, not a "
   "zoom-out), and the same state at screen 0 still parks")
