# smoke-suite area: custom_race
#
# Part of the OrionLayer smoke suite — 003_custom_race_auto_routing_custom_race_select_race.py.
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
#   - auto-routing (custom_race ↔ select_race)


# ── Auto-routing for custom_race (GAME_SCREEN_ID=50) ──
if "custom_race" in d.screens:
    class GS50:
        current_screen = 50
    d.update_from_game(GS50())
    assert d.active_name == "custom_race"

    class GS51:
        current_screen = 51
    d.update_from_game(GS51())
    assert d.active_name == "select_race"
    ok("auto-routing (custom_race ↔ select_race)")
