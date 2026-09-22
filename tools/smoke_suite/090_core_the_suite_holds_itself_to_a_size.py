# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090_core_the_suite_holds_itself_to_a_size.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 162 part 5,
# the rule that keeps the split from growing back, written after the
# cut and the only check the cut added.
#
# The 1 check(s) it holds:
#   - the suite holds itself: every module declares its group, stays under
#     the reading limit or is listed with a reason, and binds no name the
#     runner owns

# ── THE RULE THAT KEEPS IT FROM GROWING BACK ──
#
# `main()` reached 21 883 lines because nothing ever said no. Three
# things are asserted here, and each one is the shape of a fault the
# split would otherwise re-acquire:
#
#   1. every module declares its GROUP, and the group is a real screen
#      or the core. A module whose group is a typo is a module every
#      `--screen` run silently leaves out of its output.
#   2. no module is over CHECK_MODULE_LIMIT unless it is listed in
#      `v3_projektstatus.md` with a reason, both directions — decision
#      6's shape, because a hand-kept list is legitimate only with a
#      checker.
#   3. no module binds a name `tools/smoke_test.py` binds at module
#      level. The modules are EXECUTED into the runner's own namespace,
#      so a bare `_why` at module level is a name ninety files can
#      rebind — and one of them did, which cost the `--screen`
#      widening line its second printing before this check existed.
import ast as _ss_ast

_ss_root = os.path.dirname(SCREENS_DIR)
_ss_files = sorted(f for f in os.listdir(SUITE_DIR) if f.endswith(".py"))
assert len(_ss_files) >= 50, (
    f"only {len(_ss_files)} check modules — the suite is "
    f"tools/smoke_suite/, and finding it nearly empty means this "
    f"check is measuring the wrong directory")
assert len(_ss_files) == len(os.listdir(SUITE_DIR)), (
    f"tools/smoke_suite/ holds something that is not a .py file: "
    f"{sorted(set(os.listdir(SUITE_DIR)) - set(_ss_files))}. The "
    f"runner executes every file in there")

# 1. THE GROUP, off each module's own first line.
_ss_screens = {d for d in os.listdir(SCREENS_DIR)
               if os.path.isdir(os.path.join(SCREENS_DIR, d))
               and not d.startswith("_")}
_ss_areas = {f: module_area(os.path.join(SUITE_DIR, f)) for f in _ss_files}
_ss_wrong = {f: a for f, a in _ss_areas.items()
             if a != "core" and a not in _ss_screens}
assert not _ss_wrong, (
    f"these check modules name a group that is neither the core nor a "
    f"screen folder: {_ss_wrong}. A group nothing matches is a module "
    f"no --screen run ever shows")
assert _ss_areas[_ss_files[0]] == "core", (
    f"the first module is {_ss_areas[_ss_files[0]]!r}; it stands the "
    f"app up for everything after it and belongs to the core")

# 2. THE SIZE, and the exceptions list in both directions.
_ss_size = {f: os.path.getsize(os.path.join(SUITE_DIR, f))
            for f in _ss_files}
_ss_over = {f: s for f, s in _ss_size.items() if s > CHECK_MODULE_LIMIT}
import re as _ss_re
with open(os.path.join(_ss_root, "v3_projektstatus.md"),
          encoding="utf-8") as _ss_fh:
    # Whitespace-collapsed: the list is prose and wraps, and a line
    # break in the middle of an entry is a line break, not a
    # different claim (the same reading the decision-6 list gets).
    _ss_doc = _ss_re.sub(r"\s+", " ", _ss_fh.read())
for _ss_f, _ss_s in sorted(_ss_over.items()):
    assert f"`{_ss_f}` (**{_ss_s // 1024}** KB" in _ss_doc, (
        f"{_ss_f} is {_ss_s} bytes, over the "
        f"{CHECK_MODULE_LIMIT} the limit allows, and "
        f"v3_projektstatus.md does not list it at that size. Work "
        f"order 162 part 5: an exception is allowed and must be "
        f"LISTED, with the reason — which is always the same one, a "
        f"single section bigger than the limit, and a section is one "
        f"check's block")
_ss_listed = dict(_ss_re.findall(
    r"`(\d\d\d_[\w.]+\.py)` \(\*\*(\d+)\*\* KB", _ss_doc))
for _ss_f, _ss_kb in sorted(_ss_listed.items()):
    assert _ss_f in _ss_over and str(_ss_over[_ss_f] // 1024) == _ss_kb, (
        f"the check-module exceptions list names {_ss_f} at {_ss_kb} KB; "
        f"it is "
        + (f"{_ss_size[_ss_f] // 1024} KB and under the limit"
           if _ss_f in _ss_size else "not in the suite at all")
        + ". A list that keeps an entry after it stops qualifying is "
          "the state work order 135 found, six deep")
assert len(_ss_listed) == len(_ss_over), (
    f"the list has {len(_ss_listed)} entries and {len(_ss_over)} "
    f"modules are over the limit")

# 3. NO MODULE MAY REBIND A NAME THE RUNNER OWNS.
#
# `tools/smoke_names.py` is loaded by path rather than imported, so
# this check adds nothing to `sys.path` that a later one would find
# there. `__file__` is the RUNNER's path in this namespace — that is
# the whole reason the ten project-root expressions in the moved code
# still work — so it is exactly the source to read here.
import importlib.util as _ss_ilu
_ss_spec = _ss_ilu.spec_from_file_location(
    "_ss_names", os.path.join(_ss_root, "tools", "smoke_names.py"))
_ss_names = _ss_ilu.module_from_spec(_ss_spec)
_ss_spec.loader.exec_module(_ss_names)
_, _ss_own, _ = _ss_names.touches(
    _ss_ast.parse(io.open(os.path.abspath(__file__),
                          encoding="utf-8").read()).body)
_ss_clash = {}
for _ss_f in _ss_files:
    _ss_tree = _ss_ast.parse(
        io.open(os.path.join(SUITE_DIR, _ss_f), encoding="utf-8").read())
    _, _ss_binds, _ = _ss_names.touches(_ss_tree.body)
    for _ss_n in sorted(_ss_binds & _ss_own):
        _ss_clash.setdefault(_ss_n, []).append(_ss_f)
assert not _ss_clash, (
    f"these check modules rebind a name tools/smoke_test.py owns at "
    f"module level: {_ss_clash}. The modules are executed INTO that "
    f"namespace, so the runner's own `ok`, `PASS`, `SCREEN` or "
    f"`_cli_why` is one assignment away from being replaced")

ok(f"the suite holds itself: {len(_ss_files)} check modules, every one "
   f"declaring its group ({len(set(_ss_areas.values()))} groups), "
   f"{len(_ss_over)} listed exception(s) over "
   f"{CHECK_MODULE_LIMIT // 1024} KB and none unlisted, and not one "
   f"rebinding any of the runner's {len(_ss_own)} names")
