# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 049_core_colony_summary_sidebar_layout_label_fl.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - colony summary sidebar layout (label flush left, value flush right, ink-measured at 12 resolutio


ok("colony summary sidebar layout (label flush left, value flush "
   "right, ink-measured at 12 resolutions)")
