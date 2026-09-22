# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 068_core_game_menu_esc_targets_per_dialog.py.
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
#   - GAME menu: ESC targets per dialog as measured, 13 toggles, 10 slot rows, 10 strips, 10 name inpu


# 2. WHAT ESC REACHES is the first ESC field (fields.cpp:2608): RETURN
#    in the menu, the whole-screen field elsewhere, nothing in the
#    confirmation. And the row readers find their ten and thirteen.
_gm_esc = {n: _gm_nodes.esc_field(_gm_fields(_gm_fix[n]))
           for n in ("menu", "settings", "load", "save", "confirm")}
assert _gm_esc["menu"].field_type == 0 and _gm_esc["menu"].index == 6
for _n in ("settings", "load", "save"):
    assert (_gm_esc[_n].x, _gm_esc[_n].x_end) == (0, 639), _n
assert _gm_esc["confirm"] is None
assert len(_gm_nodes.option_toggles(_gm_fields(_gm_fix["settings"]))) == 13
assert len(_gm_nodes.slot_rows(_gm_fields(_gm_fix["load"]))) == 10
assert len(_gm_nodes.save_strips(_gm_fields(_gm_fix["save"]))) == 10
assert len(_gm_nodes.save_inputs(_gm_fields(_gm_fix["save"]))) == 10
ok("GAME menu: ESC targets per dialog as measured, 13 toggles, 10 "
   "slot rows, 10 strips, 10 name inputs")
