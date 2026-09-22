# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 023_core_modding_figures_md_regenerates_byte_fo.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - modding_figures.md regenerates byte for byte; the figure extractor is in setup.py
#   - colony header plates (the window is a marked DEVIATION, the plate height is a transcribed number
#   - marker inventory ( files carry an HD EXTENSION or DEVIATION and every one of them is read by a c


# ── `doc/modding_figures.md` IS GENERATED, AND CHECKED ──
#
# A hand-written list of 54 names is wrong within a month, and a
# modder following a stale name gets SILENCE — a file nothing
# looks for is indistinguishable from a file that is not there.
# Regenerated here and compared byte for byte, the same trade the
# check count makes.
import importlib.util as _ilu
_mdspec = _ilu.spec_from_file_location(
    "_make_modding_doc", os.path.join(_proj, "tools",
                                      "make_modding_doc.py"))
_mdmod = _ilu.module_from_spec(_mdspec)
_mdspec.loader.exec_module(_mdmod)
_mdpath = os.path.join(_proj, "doc", "modding_figures.md")
assert os.path.exists(_mdpath), (
    "doc/modding_figures.md is absent — run "
    "`python tools/make_modding_doc.py`")
_mdtext = open(_mdpath, encoding="utf-8").read()
assert _mdtext == _mdmod.render(), (
    "doc/modding_figures.md no longer matches the loader's table. "
    "It is GENERATED — run `python tools/make_modding_doc.py` "
    "rather than editing it, or the names a modder copies stop "
    "being the names the loader looks for")
for _need in ("@2x.png", "@3x.png", "@4x.png", "28 x 28",
              "refused", "human_farmer.png"):
    assert _need in _mdtext, (
        f"the generated modding document no longer carries "
        f"{_need!r} — both conventions, the master size and the "
        f"refusal have to reach the person writing the mod")
# AND THE EXTRACTOR IS IN setup.py, which it was not until now:
# help, nebula, techname and estrings were all listed and this
# one had never been added.
_sp = open(os.path.join(_proj, "tools", "setup.py"),
           encoding="utf-8").read()
assert "raceicon_extract.py" in _sp, (
    "tools/setup.py does not name the figure extractor, so an "
    "install without figures is never told what to run")
ok("modding_figures.md regenerates byte for byte; the figure "
   "extractor is in setup.py")

ok("colony header plates (the window is a marked DEVIATION, the "
   "plate height is a transcribed number that does not fit, the "
   "job columns are colsum.cpp's unequal three)")

ok(f"marker inventory ({len(_MARKED)} files carry an HD EXTENSION "
   f"or DEVIATION and every one of them is read by a check)")
