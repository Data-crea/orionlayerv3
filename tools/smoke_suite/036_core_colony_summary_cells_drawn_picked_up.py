# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 036_core_colony_summary_cells_drawn_picked_up.py.
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
#   - colony summary cells: drawn, picked up and dropped are one and the same cell (read back from the


ok("colony summary cells: drawn, picked up and dropped are one "
   "and the same cell (read back from the render)")
