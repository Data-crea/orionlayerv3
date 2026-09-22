# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 072_core_game_menu_help_44_regions_over.py.
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
#   - GAME menu help: 44 regions over four dialogs as evanhelp.cpp:40-116, 420/421 over the volume bar


# 6. HELP: the four transcribed tables, 420/421 left out WITH the
#    sliders and saying so, each region carrying its native rect.
_gm_help = _gm_json.load(open(os.path.join(
    SCREENS_DIR, "game_menu", "help.json")))
_gm_ids = {}
for _r in _gm_help["regions"]:
    assert "native" in _r and "node" in _r, _r
    _gm_ids.setdefault(_r["node"], []).append(_r["help_id"])
assert sorted(_gm_ids["menu"]) == [415] * 4 + list(range(416, 424))
assert sorted(_gm_ids["settings"]) == [415] * 4 + list(range(429, 443))
assert sorted(_gm_ids["load"]) == [415] * 4 + [424, 425, 426]
assert sorted(_gm_ids["save"]) == [415] * 4 + [425, 427, 428]
# 420/421 came back with the volume bars (work order 124 C): nothing
# of the menu's table is omitted any more, and the file says so.
assert "_omitted" not in _gm_help, "a stale omission note in help.json"
ok("GAME menu help: 44 regions over four dialogs as evanhelp.cpp:40-116, "
   "420/421 over the volume bars")
