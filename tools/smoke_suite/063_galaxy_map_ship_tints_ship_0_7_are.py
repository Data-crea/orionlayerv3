# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 063_galaxy_map_ship_tints_ship_0_7_are.py.
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
#   - ship tints: ship_0..7 are colors.json values with no code default in ships.py


# 5. THE SHIP TINTS LIVE IN THE PALETTE TOO (decision 14): eight
#    ship_* keys in the skin, no literal default left in ships.py.
_sh_src = open(os.path.join(SCREENS_DIR, "galaxy_map", "ships.py"),
               encoding="utf-8").read()
assert not re.search(r'"ship_\d",\s*\(', _sh_src), \
    "ships.py carries a code default for a ship tint again"
_sh_sec = palette.section("galaxy_map")
assert all(len(_sh_sec.get(f"ship_{_i}", [])) == 3 for _i in range(8)), \
    "colors.json [galaxy_map] lacks a ship_N tint"
ok("ship tints: ship_0..7 are colors.json values with no code default "
   "in ships.py")
