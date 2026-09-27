# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090r_core_the_orion2re_build_it_needs.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 3 check(s) it holds:
#   - the open fixes the engine needs are one list, and README, setup's report and the fundament's line name exactly them
#   - version_check requires every applied fix: a tree missing any one of them is reported by name
#   - open fixes 35-40 are applied and documented: status, hashes, one-line markers, each entry's diff the patch file's; on this disk each commit's diff the file's and each marker over its block


# ── THE ORION2RE BUILD IT NEEDS (work order 181) ────────────────
#
# Work order 181 applied open fixes 35-40 and asked that a fresh clone on
# another machine KNOWS it needs them. The list's one home is
# `version_check.LOCAL_PATCHES`; the numbers are `FIX_NUMBERS`. Three
# places tell a reader, and each is held to that list here rather than
# trusted: README's orion2re table (090j already holds its patch names),
# `tools/setup.py`'s report, and the line in fundament part 09.
import importlib.util as _vr_iu
import re as _vr_re
import subprocess as _vr_sp
import tempfile as _vr_tmp
import version_check as _vr_vc

_vr_root = os.path.dirname(SCREENS_DIR)
_vr_keys = set(_vr_vc.LOCAL_PATCHES) | set(_vr_vc.REPORTED_PATCHES)
assert set(_vr_vc.FIX_NUMBERS) == _vr_keys, (
    "FIX_NUMBERS and the two patch lists disagree: "
    f"{sorted(set(_vr_vc.FIX_NUMBERS) ^ _vr_keys)}")
_vr_want = _vr_vc.required_fixes()
assert {35, 36, 37, 38, 39, 40} <= set(_vr_want), _vr_want

# README: the row that names a patch names its number(s).
_vr_readme = open(os.path.join(_vr_root, "README.md"), encoding="utf-8").read()
_vr_sec = _vr_readme[_vr_readme.index("<!-- orion2re-patches -->"):]
_vr_sec = _vr_sec[:_vr_sec.index("\n## ")]
_vr_rows = [_l for _l in _vr_sec.splitlines() if _l.startswith("| ")]
for _vr_p in _vr_vc.LOCAL_PATCHES:
    _vr_row = next((_l for _l in _vr_rows if f"`{_vr_p}`" in _l), None)
    assert _vr_row is not None, f"README's orion2re table has no row for {_vr_p}"
    for _vr_n in _vr_vc.FIX_NUMBERS[_vr_p]:
        assert _vr_re.search(rf"\b{_vr_n}\b", _vr_row.split(" | ")[2]), \
            f"README's row for {_vr_p} does not name open fix {_vr_n}"

# setup's report, from the function setup prints.
_vr_spec = _vr_iu.spec_from_file_location(
    "_vr_setup", os.path.join(_vr_root, "tools", "setup.py"))
_vr_setup = _vr_iu.module_from_spec(_vr_spec)
_vr_spec.loader.exec_module(_vr_setup)
_vr_lines = _vr_setup.engine_report()
_vr_named = next(_l for _l in _vr_lines if "open fixes" in _l)
assert [int(_x) for _x in _vr_re.findall(
    r"\d+", _vr_named.split("open fixes", 1)[1])] == _vr_want, _vr_named
assert "orionlayer-local" in _vr_named

# The fundament's line (part 09).
_vr_f09 = open(os.path.join(_vr_root, "doc", "fundament",
                            "09-facts-orion2re-and-pygame.md"),
               encoding="utf-8").read()
_vr_i = _vr_f09.index("- **THE ENGINE ORIONLAYER NEEDS")
_vr_line = _vr_f09[_vr_i:_vr_f09.index("**", _vr_f09.index(
    "ones with a patch", _vr_i))]
assert sorted(int(_x) for _x in _vr_re.findall(
    r"\d+", _vr_line.split("ones with a patch are open fixes", 1)[1])) == \
    _vr_want, "fundament part 09's line does not name exactly the required fixes"
ok(f"the open fixes the engine needs are one list ({len(_vr_want)} numbers, "
   "35-40 among them), and README, setup's report and the fundament's line "
   "name exactly them")


# 2. A TREE WITHOUT ONE IS REPORTED. A stand-in tree carrying every
#    required marker but one, for each required patch in turn — the
#    checker must fail and name exactly that one. Built here, not read off
#    this disk, so it holds the same in a clone.
def _vr_tree(dirpath, skip):
    os.makedirs(os.path.join(dirpath, "src", "game"), exist_ok=True)
    os.makedirs(os.path.join(dirpath, "src", "ext"), exist_ok=True)
    from core.config import ORION2RE_VERSION as _v
    open(os.path.join(dirpath, "src", "version.h"), "w").write(
        f'static const char ENGINE_VERSION[] = "{_v}";\n')
    open(os.path.join(dirpath, "src", "game", "consts.h"), "w").write(
        f'static const char GAME_VERSION_LABEL[] = "Version {_v}";\n')
    per_file = {}
    for _p, (_rel, _marker, _b) in _vr_vc.LOCAL_PATCHES.items():
        if _p != skip:
            per_file.setdefault(_rel, []).append(_marker)
    for _p, (_rel, _marker, _b) in _vr_vc.LOCAL_PATCHES.items():
        per_file.setdefault(_rel, [])
    for _rel, _markers in per_file.items():
        _full = os.path.join(dirpath, _rel)
        os.makedirs(os.path.dirname(_full), exist_ok=True)
        open(_full, "w").write("\n".join(f"// {_m}" for _m in _markers) + "\n")


_vr_seen = 0
for _vr_skip in [None] + sorted(_vr_vc.LOCAL_PATCHES):
    with _vr_tmp.TemporaryDirectory() as _vr_t:
        _vr_tree(_vr_t, _vr_skip)
        _vr_run = _vr_sp.run([sys.executable, os.path.join(
            _vr_root, "tools", "version_check.py"), _vr_t],
            capture_output=True, text=True)
        _vr_miss = [_l.split(":")[0].strip() for _l in
                    _vr_run.stdout.splitlines() if _l.rstrip().endswith("MISSING")]
        if _vr_skip is None:
            assert _vr_run.returncode == 0 and not _vr_miss, _vr_run.stdout
        else:
            assert _vr_run.returncode == 1 and _vr_miss == [_vr_skip], \
                (_vr_skip, _vr_miss, _vr_run.returncode)
            _vr_seen += 1
assert _vr_seen == len(_vr_vc.LOCAL_PATCHES) >= 20
ok(f"version_check requires every applied fix: a tree missing any one of "
   f"its {_vr_seen} patches is reported by name, and the full tree passes")


# 3. OPEN FIXES 35-40 — APPLIED by work order 181, and documented as fix 34
#    was: the entry says so with both hashes and carries the diff; the
#    patch file says so, carries its marker on ONE line (fix 39's was
#    broken over two until 181), and its diff is the entry's.
_vr_series = {35: ("doc/ext_colony_screen_colony.patch", "c5d4dacd", "COLS"),
              36: ("doc/ext_colony_building_placement.patch", "01bafd9c", "CBLD"),
              37: ("doc/ext_colony_status_word.patch", "a10e20ba", "CEVT"),
              38: ("doc/ext_colony_product_cost.patch", "8a6acc08", "CPRD"),
              39: ("doc/ext_build_popup_queue.patch", "2be953d4", "BLDQ"),
              40: ("doc/ext_build_popup_lists.patch", "2097b0c6", "BLDL")}
assert tuple(_p for _p, _h, _t in _vr_series.values()) == _vr_vc.COLONY_SERIES
_vr_fixes = open(os.path.join(_vr_root, "doc", "orion2re_open_fixes.md"),
                 encoding="utf-8").read()


def _vr_norm(diff):
    """A diff as an entry prints it: from `--- a/`, without git's text
    after the closing `@@` (fix 34's convention)."""
    diff = diff[diff.index("--- a/"):]
    return _vr_re.sub(r"(?m)^(@@ [^@]* @@).*$", r"\1", diff)


for _vr_n, (_vr_p, _vr_h, _vr_tag) in _vr_series.items():
    assert _vr_p in _vr_vc.LOCAL_PATCHES and _vr_p not in _vr_vc.REPORTED_PATCHES
    _vr_marker = f"OrionLayer, open fix {_vr_n}."
    assert _vr_vc.LOCAL_PATCHES[_vr_p][1] == _vr_marker
    _vr_ptext = open(os.path.join(_vr_root, _vr_p), encoding="utf-8").read()
    assert f"STATUS: APPLIED 27 September 2026 by work order 181" in _vr_ptext \
        and f"orion2re {_vr_h} on orionlayer-local" in _vr_ptext, _vr_p
    _vr_pdiff = _vr_ptext[_vr_ptext.index("diff --git"):]
    assert any(_vr_marker in _l for _l in _vr_pdiff.splitlines()
               if _l.startswith("+")), f"{_vr_p}: no one-line marker"
    _vr_a = _vr_fixes.index(f"\n## {_vr_n}. ")
    _vr_b = _vr_fixes.find("\n## ", _vr_a + 5)
    _vr_sec = _vr_fixes[_vr_a:_vr_b if _vr_b > 0 else len(_vr_fixes)]
    assert "**Status: APPLIED** — 27 September 2026 by work order 181" in \
        _vr_sec and f"**`{_vr_h}`**" in _vr_sec, f"entry {_vr_n}"
    for _vr_part in ("**The exact change.**", "**Live check**",
                     "**Side effects", "**How to revert.**",
                     "181-fixes35-40-wire.txt"):
        assert _vr_part in _vr_sec, f"entry {_vr_n} lacks {_vr_part}"
    _vr_j = _vr_sec.index("```diff\n", _vr_sec.index("**The exact change.**")) + 8
    assert _vr_sec[_vr_j:_vr_sec.index("\n```", _vr_j)] + "\n" == \
        _vr_norm(_vr_pdiff), f"entry {_vr_n}'s diff is not its patch file's"
    _vr_row = next(_l for _l in _vr_fixes.splitlines()
                   if _l.startswith(f"| {_vr_n} |"))
    assert "**Applied** 27 September 2026 by work order 181" in _vr_row
    assert _vr_tag in open(os.path.join(_vr_root, "doc", "briefs",
                                        "181-fixes35-40-wire.txt"),
                           encoding="utf-8").read()
_vr_s36 = _vr_fixes[_vr_fixes.index("\n## 36. "):_vr_fixes.index("\n## 37. ")]
assert "UNVERIFIED `building_placement`" in _vr_s36 and \
    "does not place buildings yet" in _vr_s36, \
    "entry 36 must keep saying HD does not place buildings, and why"

# On a disk that has the engine tree: each commit's diff IS the patch
# file's, and each marker sits in the comment directly over its block.
_vr_tree_dir = os.path.expanduser("~/orion2re")
_vr_api = os.path.join(_vr_tree_dir, "src", "ext", "ext_api.cpp")
_vr_live = os.path.exists(_vr_api) and all(
    f"OrionLayer, open fix {_n}." in open(_vr_api, errors="replace").read()
    for _n in _vr_series)
if _vr_live:
    _vr_lines = open(_vr_api, errors="replace").read().splitlines()
    for _vr_n, (_vr_p, _vr_h, _vr_tag) in _vr_series.items():
        _vr_git = _vr_sp.run(["git", "-C", _vr_tree_dir, "diff",
                              f"{_vr_h}~1", _vr_h], capture_output=True,
                             text=True)
        if _vr_git.returncode == 0:
            _vr_ptext = open(os.path.join(_vr_root, _vr_p),
                             encoding="utf-8").read()
            assert _vr_git.stdout == _vr_ptext[_vr_ptext.index("diff --git"):], \
                f"commit {_vr_h} is not {_vr_p}"
        _vr_m = [_i for _i, _l in enumerate(_vr_lines)
                 if f"OrionLayer, open fix {_vr_n}." in _l
                 and _l.lstrip().startswith("//")]
        assert len(_vr_m) == 1, (_vr_n, _vr_m)
        _vr_k = _vr_m[0] + 1
        while _vr_lines[_vr_k].lstrip().startswith("//"):
            _vr_k += 1
        assert _vr_lines[_vr_k].lstrip().startswith("if (current_screen"), \
            f"fix {_vr_n}'s marker is not over its block"
        _vr_body = "\n".join(_vr_lines[_vr_k:_vr_k + 6])
        assert "".join(_vr_re.findall(r"push_back\(\(uint8_t\)'(.)'\)",
                                      _vr_body)[:4]) == _vr_tag, _vr_n
else:
    report("open fixes 35-40 NOT checked against ext_api.cpp — no orion2re "
           "tree with the series on this disk")
# Open fix 41 (work order 182): WRITTEN AND PARKED, not applied — the
# entry says so, the patch is reported (never required), and each of its
# two changed places carries the one-line marker.
_vr_41 = _vr_fixes[_vr_fixes.index("\n## 41. "):]
assert "NOT APPLIED" in _vr_41[:400] and "ext_engine_window_hidden.patch" in _vr_41
assert "doc/ext_engine_window_hidden.patch" in _vr_vc.REPORTED_PATCHES and \
    "doc/ext_engine_window_hidden.patch" not in _vr_vc.LOCAL_PATCHES
_vr_p41 = open(os.path.join(_vr_root, "doc", "ext_engine_window_hidden.patch"),
               encoding="utf-8").read()
assert "STATUS: NOT APPLIED" in _vr_p41
assert sum("OrionLayer, open fix 41." in _l for _l in
           _vr_p41[_vr_p41.index("diff --git"):].splitlines()
           if _l.startswith("+")) == 2, "fix 41: one marker per changed place"
ok("open fixes 35-40 are applied and documented: status, both hashes, "
   "one-line markers, each entry's diff the patch file's; on this disk each "
   "commit's diff the file's and each marker over its block")
