# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 043_core_class_a_no_glyph_our_code.py.
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
#   - class A: no glyph our code places lands under the frame ( screens, sizes, window(s) drawing text


report("class C, text on a plate we paint over the frame: "
       + (", ".join(f"{_k} {_v} px" for _k, _v
                    in sorted(_class_c.items())) or "none"))
ok(f"class A: no glyph our code places lands under the frame "
   f"({len(_FRAME_SCREENS)} screens, {len(_SIZES)} sizes, "
   f"{len(_class_c)} window(s) drawing text over it)")
