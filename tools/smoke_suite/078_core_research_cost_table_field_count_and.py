# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 078_core_research_cost_table_field_count_and.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - research cost table, field count and hyper-advanced surcharge agree with techdata.cpp and colcal
#   - every covered core/structs spec matches orion2re's own headers, sizes.h included, and the off-by


# THE COST TABLE IS A COPY, SO IT HAS A CHECKER (decision 36, work
# order 129 C): tools/research_cost_check.py reads the 83 costs and the
# surcharge out of techdata.cpp and colcalc.cpp. Run here as the hull
# tables' checker is, so a tree whose engine moved fails the suite.
import subprocess as _rc_sp
_rc = _rc_sp.run([sys.executable, os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "research_cost_check.py")],
    capture_output=True, text=True, timeout=120)
if _rc.returncode == 2:
    report("research cost table NOT checked — no orion2re tree on this "
           "disk")
else:
    assert _rc.returncode == 0, _rc.stdout + _rc.stderr
    ok("research cost table, field count and hyper-advanced surcharge "
       "agree with techdata.cpp and colcalc.cpp")

# AND THE HEADER ROUTE, MECHANICALLY (decision 23's first source, work
# order 130 C): tools/struct_header_check.py compiles orion2re's own
# headers with their packing and asserts every offset in every covered
# spec, plus each struct's size against the assert in sizes.h. It was
# done by hand twice — s_settings on 14 September, s_player.tech_fields
# on 17 — and a check done by hand is done once. Its own control moves
# one offset by a byte and requires the compile to fail, so a green run
# here is not a compiler that stopped looking.
_sh = _rc_sp.run([sys.executable, os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "struct_header_check.py")],
    capture_output=True, text=True, timeout=600)
if _sh.returncode == 2:
    report("struct offsets NOT checked against the headers — no "
           "orion2re tree and/or no C++ compiler on this disk")
else:
    assert _sh.returncode == 0, _sh.stdout + _sh.stderr
    ok("every covered core/structs spec matches orion2re's own headers, "
       "sizes.h included, and the off-by-one control is refused")
