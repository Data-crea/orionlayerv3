# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090r_core_the_orion2re_build_it_needs.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 8 check(s) it holds:
#   - the open fixes the engine needs are one list, and README, setup's report and the fundament's line name exactly them
#   - version_check requires every applied fix: a tree missing any one of them is reported by name
#   - open fixes 35-40 are applied and documented: status, hashes, one-line markers, each entry's diff the patch file's; on this disk each commit's diff the file's and each marker over its block
#   - open fix 41 is applied and documented: required, status and hash in entry, row and patch, two one-line markers, the entry's diff the file's; on this disk the commit's diff the file's
#   - open fix 42 is written and parked, not applied: reported and never required, NOT APPLIED in entry, row and patch, one one-line marker, the entry's diff the file's; on this disk its pre-image is orionlayer-local's and its marker absent
#   - open fixes 44 and 45 (the Ship Designer) are written and parked, not applied, 45 on top of 44: reported and never required, NOT APPLIED in entries, rows and patches, a one-line marker at every changed place, each entry's diff its file's; on this disk every pre-image is orionlayer-local's (45's ext_api.cpp hunk: 44's post-image) and no marker is in the tree
#   - open fixes 46 and 47 (the diplomacy audience) are written and parked, not applied, 47 on top of 46: reported and never required, NOT APPLIED in entries, rows and patches, a one-line marker at every changed place, each entry's diff its file's; on this disk every pre-image is orionlayer-local's (47's ext_api.h hunk: 46's post-image) and no marker is in the tree
#   - open fix 43 is written and parked, not applied, and amends 41: reported and never required, NOT APPLIED in entry, row and patch, a one-line marker at every changed place of its five files, the entry's diff the file's; on this disk every pre-image is orionlayer-local's and no marker is in the tree


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
ok("open fixes 35-40 are applied and documented: status, both hashes, "
   "one-line markers, each entry's diff the patch file's; on this disk each "
   "commit's diff the file's and each marker over its block")


# 4. OPEN FIX 41 — APPLIED by work order 183 on Data's approval (written,
#    proved and parked by 182), documented as 35-40 were: required, the
#    entry, its summary row and the patch file say so with the hash, each
#    of the two changed places carries the one-line marker, and the entry's
#    diff is the file's. The file's diff has TWO files, so the entry leaves
#    out git's `diff --git` and `index` lines between them too.
_vr_p41 = "doc/ext_engine_window_hidden.patch"
_vr_h41 = "4bf152e4"
assert _vr_p41 in _vr_vc.LOCAL_PATCHES and _vr_p41 not in _vr_vc.REPORTED_PATCHES
assert _vr_vc.LOCAL_PATCHES[_vr_p41][1] == "OrionLayer, open fix 41."
assert 41 in _vr_want
_vr_t41 = open(os.path.join(_vr_root, _vr_p41), encoding="utf-8").read()
assert "STATUS: APPLIED 27 September 2026 by work order 183" in _vr_t41 and \
    f"orion2re {_vr_h41} on orionlayer-local" in _vr_t41, _vr_p41
_vr_d41 = _vr_t41[_vr_t41.index("diff --git"):]
assert sum("OrionLayer, open fix 41." in _l for _l in _vr_d41.splitlines()
           if _l.startswith("+")) == 2, "fix 41: one marker per changed place"
_vr_41 = _vr_fixes[_vr_fixes.index("\n## 41. "):]
_vr_41 = _vr_41[:_vr_41.find("\n## ", 5)] if "\n## " in _vr_41[5:] else _vr_41
assert "**Status: APPLIED** — 27 September 2026 by work order 183" in \
    _vr_41[:600] and f"**`{_vr_h41}`**" in _vr_41, "entry 41's status"
# The OrionLayer commit that recorded it, named once it existed (183 Part 2).
assert "Recorded in OrionLayer by commit **`89ce660`**" in _vr_41[:1400], \
    "entry 41 must name the OrionLayer commit that recorded it"
for _vr_part in ("**The exact change.**", "**Live check**", "**Side effects",
                 "**How to revert.**", "presents without VSync",
                 "byte for byte", "fixes34-41.bundle"):
    assert _vr_part in _vr_41, f"entry 41 lacks {_vr_part}"
_vr_j = _vr_41.index("```diff\n", _vr_41.index("**The exact change.**")) + 8
_vr_n41 = "".join(_l for _l in _vr_norm(_vr_d41).splitlines(True)
                  if not _l.startswith(("diff --git ", "index ")))
assert _vr_41[_vr_j:_vr_41.index("\n```", _vr_j)] + "\n" == _vr_n41, \
    "entry 41's diff is not its patch file's"
_vr_r41 = next(_l for _l in _vr_fixes.splitlines() if _l.startswith("| 41 |"))
assert "**Applied** 27 September 2026 by work order 183" in _vr_r41
_vr_git41 = _vr_sp.run(["git", "-C", _vr_tree_dir, "diff", f"{_vr_h41}~1",
                        _vr_h41], capture_output=True, text=True) \
    if os.path.isdir(os.path.join(_vr_tree_dir, ".git")) else None
if _vr_git41 is not None and _vr_git41.returncode == 0:
    assert _vr_git41.stdout == _vr_d41, f"commit {_vr_h41} is not {_vr_p41}"
    for _vr_rel in (("src", "ext", "ext_api.cpp"), ("src", "game", "platform.cpp")):
        _vr_src = open(os.path.join(_vr_tree_dir, *_vr_rel), errors="replace").read()
        assert _vr_src.count("OrionLayer, open fix 41.") == 1, _vr_rel
else:
    report(f"open fix 41 NOT checked against its commit — no orion2re tree "
           f"with {_vr_h41} on this disk")
ok("open fix 41 is applied and documented: required by version_check, "
   "status and hash in the entry, its row and the patch file, two one-line "
   "markers, the entry's diff the file's; on this disk the commit's diff "
   "the file's")

# 5. OPEN FIX 42 — WRITTEN AND PARKED by work order 184, NOT APPLIED (no
#    engine patch may be applied in that order). The entry, its row and
#    the patch file say so; version_check REPORTS it and never requires
#    it; the one changed place carries the one-line marker; the entry's
#    diff is the file's. On a disk with the tree: the hunk's pre-image
#    (its context and removed lines) is exactly what `orionlayer-local`
#    holds, so the file still applies where the entry says it does — and
#    the marker is not in the tree, because nothing applied it.
_vr_p42 = "doc/ext_input_delay_tick.patch"
assert _vr_p42 in _vr_vc.REPORTED_PATCHES and _vr_p42 not in _vr_vc.LOCAL_PATCHES
assert _vr_vc.REPORTED_PATCHES[_vr_p42][:2] == (
    os.path.join("src", "game", "fields.cpp"), "OrionLayer, open fix 42.")
assert _vr_vc.FIX_NUMBERS[_vr_p42] == (42,) and 42 not in _vr_want
_vr_t42 = open(os.path.join(_vr_root, _vr_p42), encoding="utf-8").read()
assert "STATUS: NOT APPLIED" in _vr_t42 and "work order 184" in _vr_t42
_vr_d42 = _vr_t42[_vr_t42.index("diff --git"):]
assert sum("OrionLayer, open fix 42." in _l for _l in _vr_d42.splitlines()
           if _l.startswith("+")) == 1, "fix 42: one marker at its one place"
_vr_42 = _vr_fixes[_vr_fixes.index("\n## 42. "):]
_vr_42 = _vr_42[:_vr_42.find("\n## ", 5)] if "\n## " in _vr_42[5:] else _vr_42
assert "**Status: NOT APPLIED" in _vr_42[:400] and _vr_p42 in _vr_42[:600]
for _vr_part in ("**Proof.**", "no offset, no fuzz", "_current_scren",
                 "**Scratch results**", "0 native frames", "0 lost",
                 "**How to apply.**"):
    assert _vr_part in _vr_42, f"entry 42 lacks {_vr_part}"
_vr_j = _vr_42.index("```diff\n", _vr_42.index("**The exact change.**")) + 8
_vr_n42 = "".join(_l for _l in _vr_norm(_vr_d42).splitlines(True)
                  if not _l.startswith(("diff --git", "index ")))
assert _vr_42[_vr_j:_vr_42.index("\n```", _vr_j)] + "\n" == _vr_n42, \
    "entry 42's diff is not its patch file's"
_vr_r42 = next(_l for _l in _vr_fixes.splitlines() if _l.startswith("| 42 |"))
assert "**Written, NOT APPLIED** — work order 184" in _vr_r42
_vr_pre = [(_l[1:] if _l[:1] in " -" else None) for _l in
           _vr_d42[_vr_d42.index("\n@@") + 1:].splitlines()[1:]]
_vr_pre = "\n".join(_l for _l in _vr_pre if _l is not None)
_vr_f42 = _vr_sp.run(["git", "-C", _vr_tree_dir, "show",
                      "orionlayer-local:src/game/fields.cpp"],
                     capture_output=True, text=True, errors="replace") \
    if os.path.isdir(os.path.join(_vr_tree_dir, ".git")) else None
if _vr_f42 is not None and _vr_f42.returncode == 0:
    assert _vr_pre in _vr_f42.stdout, (
        "fix 42's pre-image is not orionlayer-local's fields.cpp any more — "
        "the patch no longer applies where its entry says")
    assert "OrionLayer, open fix 42." not in _vr_f42.stdout, (
        "fix 42's marker is in orionlayer-local: it was applied — move it "
        "to LOCAL_PATCHES and document it as applied")
else:
    report("open fix 42 NOT checked against orionlayer-local — no orion2re "
           "tree on this disk")
ok("open fix 42 is written and parked, not applied: reported and never "
   "required, NOT APPLIED in entry, row and patch, one one-line marker, the "
   "entry's diff the file's; on this disk its pre-image is "
   "orionlayer-local's and its marker absent")

# 6. OPEN FIX 43 — WRITTEN AND PARKED by work order 185, NOT APPLIED; it
#    AMENDS fix 41 (the window hidden only when the starter asks, shown
#    again on request). Five files, so the pre-image is checked per file
#    and the marker is counted per changed place: every hunk's added lines
#    carry it at least once.
_vr_p43 = "doc/ext_engine_window_on_request.patch"
assert _vr_p43 in _vr_vc.REPORTED_PATCHES and _vr_p43 not in _vr_vc.LOCAL_PATCHES
assert _vr_vc.REPORTED_PATCHES[_vr_p43][1] == "OrionLayer, open fix 43."
assert _vr_vc.FIX_NUMBERS[_vr_p43] == (43,) and 43 not in _vr_want
_vr_t43 = open(os.path.join(_vr_root, _vr_p43), encoding="utf-8").read()
assert "STATUS: NOT APPLIED" in _vr_t43 and "AMENDS open fix 41" in _vr_t43
_vr_d43 = _vr_t43[_vr_t43.index("diff --git"):]
_vr_files43 = _vr_re.findall(r"(?m)^\+\+\+ b/(\S+)$", _vr_d43)
assert sorted(_vr_files43) == sorted([
    "src/ext/ext_api.cpp", "src/ext/ext_api.h", "src/ext/ext_server.cpp",
    "src/ext/ext_server.h", "src/game/platform.cpp"]), _vr_files43
for _vr_h in _vr_re.split(r"(?m)^@@ ", _vr_d43)[1:]:
    _vr_add = [_l for _l in _vr_h.splitlines() if _l.startswith("+")]
    assert not _vr_add or any("OrionLayer, open fix 43." in _l
                              for _l in _vr_add), (
        f"fix 43: a changed place without its marker: {_vr_add[:2]}")
_vr_43 = _vr_fixes[_vr_fixes.index("\n## 43. "):]
_vr_43 = _vr_43[:_vr_43.find("\n## ", 5)] if "\n## " in _vr_43[5:] else _vr_43
assert "**Status: NOT APPLIED" in _vr_43[:400] and _vr_p43 in _vr_43[:700]
for _vr_part in ("AMENDS open fix 41", "**What F12 does today", "**Proof.**",
                 "no offset, no fuzz", "MSG_SHOW_WINDW", "**Scratch results**",
                 "IsViewable", "**The HD side, described, not committed**",
                 "**How to apply.**"):
    assert _vr_part in _vr_43, f"entry 43 lacks {_vr_part}"
_vr_j = _vr_43.index("```diff\n", _vr_43.index("**The exact change.**")) + 8
_vr_n43 = "".join(_l for _l in _vr_norm(_vr_d43).splitlines(True)
                  if not _l.startswith(("diff --git", "index ")))
assert _vr_43[_vr_j:_vr_43.index("```", _vr_j)] == _vr_n43, \
    "entry 43's diff is not its patch file's"
_vr_r43 = next(_l for _l in _vr_fixes.splitlines() if _l.startswith("| 43 |"))
assert "**Written, NOT APPLIED** — work order 185" in _vr_r43 and "AMENDS fix 41" in _vr_r43
_vr_ok43 = os.path.isdir(os.path.join(_vr_tree_dir, ".git"))
for _vr_f in _vr_files43 if _vr_ok43 else []:
    _vr_blk = _vr_d43.split(f"+++ b/{_vr_f}\n", 1)[1].split("\ndiff --git", 1)[0]
    _vr_src = _vr_sp.run(["git", "-C", _vr_tree_dir, "show",
                          f"orionlayer-local:{_vr_f}"], capture_output=True,
                         text=True, errors="replace")
    assert _vr_src.returncode == 0, _vr_f
    assert "OrionLayer, open fix 43." not in _vr_src.stdout, (
        f"fix 43's marker is in orionlayer-local's {_vr_f}: it was applied")
    for _vr_h in _vr_re.split(r"(?m)^@@[^\n]*\n", _vr_blk)[1:]:
        _vr_pre = "\n".join(_l[1:] for _l in _vr_h.splitlines()
                            if _l[:1] in (" ", "-"))
        assert _vr_pre in _vr_src.stdout, (
            f"fix 43's pre-image is not orionlayer-local's {_vr_f} any more")
if not _vr_ok43:
    report("open fix 43 NOT checked against orionlayer-local — no orion2re "
           "tree on this disk")
ok("open fix 43 is written and parked, not applied, and amends 41: reported "
   "and never required, NOT APPLIED in entry, row and patch, a one-line "
   "marker at every changed place of its five files, the entry's diff the "
   "file's; on this disk every pre-image is orionlayer-local's and no "
   "marker is in the tree")

# 7. OPEN FIXES 44 AND 45 — THE SHIP DESIGNER, written and parked by work
#    order 185, NOT APPLIED; 45 applies on top of 44 (both append to
#    SerializeState). The rules of #6, per patch; 45's one hunk that sits
#    on 44's new lines is held to 44's post-image instead of the tree.
_vr_sd = {44: ("doc/ext_ship_designer_state.patch", ["src/ext/ext_api.cpp"]),
          45: ("doc/ext_ship_designer_boxes.patch",
               ["src/ext/ext_api.cpp", "src/ext/ext_api.h",
                "src/game/desbox.cpp"])}
_vr_post44 = ""
for _vr_n, (_vr_p, _vr_files) in sorted(_vr_sd.items()):
    _vr_mark = f"OrionLayer, open fix {_vr_n}."
    assert _vr_p in _vr_vc.REPORTED_PATCHES and _vr_p not in _vr_vc.LOCAL_PATCHES
    assert _vr_vc.REPORTED_PATCHES[_vr_p][1] == _vr_mark
    assert _vr_vc.FIX_NUMBERS[_vr_p] == (_vr_n,) and _vr_n not in _vr_want
    _vr_t = open(os.path.join(_vr_root, _vr_p), encoding="utf-8").read()
    assert "STATUS: NOT APPLIED" in _vr_t and "work order 185" in _vr_t
    _vr_d = _vr_t[_vr_t.index("diff --git"):]
    assert sorted(_vr_re.findall(r"(?m)^\+\+\+ b/(\S+)$", _vr_d)) == \
        sorted(_vr_files), (_vr_n, _vr_files)
    for _vr_h in _vr_re.split(r"(?m)^@@ ", _vr_d)[1:]:
        _vr_add = [_l for _l in _vr_h.splitlines() if _l.startswith("+")]
        assert not _vr_add or any(_vr_mark in _l for _l in _vr_add), (
            f"fix {_vr_n}: a changed place without its marker: {_vr_add[:2]}")
    _vr_e = _vr_fixes[_vr_fixes.index(f"\n## {_vr_n}. "):]
    _vr_e = _vr_e[:_vr_e.find("\n## ", 5)] if "\n## " in _vr_e[5:] else _vr_e
    assert "**Status: NOT APPLIED" in _vr_e[:400] and _vr_p in _vr_e[:900]
    for _vr_part in ("**Proof.**", "no offset, no fuzz", "**Recorded live**",
                     "**How to apply.**", "ship_designer_reading.md"
                     if _vr_n == 44 else "on top of open fix"):
        assert _vr_part in _vr_e, f"entry {_vr_n} lacks {_vr_part}"
    _vr_j = _vr_e.index("```diff\n", _vr_e.index("**The exact change.**")) + 8
    _vr_nd = "".join(_l for _l in _vr_norm(_vr_d).splitlines(True)
                     if not _l.startswith(("diff --git", "index ")))
    assert _vr_e[_vr_j:_vr_e.index("```", _vr_j)] == _vr_nd, \
        f"entry {_vr_n}'s diff is not its patch file's"
    _vr_r = next(_l for _l in _vr_fixes.splitlines()
                 if _l.startswith(f"| {_vr_n} |"))
    assert "**Written, NOT APPLIED** — work order 185" in _vr_r
    if not os.path.isdir(os.path.join(_vr_tree_dir, ".git")):
        report(f"open fix {_vr_n} NOT checked against orionlayer-local — no "
               f"orion2re tree on this disk")
        continue
    for _vr_f in _vr_files:
        _vr_blk = _vr_d.split(f"+++ b/{_vr_f}\n", 1)[1].split("\ndiff --git", 1)[0]
        _vr_src = _vr_sp.run(["git", "-C", _vr_tree_dir, "show",
                              f"orionlayer-local:{_vr_f}"], capture_output=True,
                             text=True, errors="replace").stdout
        assert _vr_mark not in _vr_src, (
            f"fix {_vr_n}'s marker is in orionlayer-local's {_vr_f}")
        for _vr_h in _vr_re.split(r"(?m)^@@[^\n]*\n", _vr_blk)[1:]:
            _vr_pre = "\n".join(_l[1:] for _l in _vr_h.splitlines()
                                if _l[:1] in (" ", "-"))
            _vr_post = "\n".join(_l[1:] for _l in _vr_h.splitlines()
                                 if _l[:1] in (" ", "+"))
            if _vr_n == 44:
                _vr_post44 += _vr_post + "\n"
            if _vr_n == 45 and _vr_f == "src/ext/ext_api.cpp" and \
                    _vr_pre not in _vr_src:
                assert _vr_pre in _vr_post44, (
                    "fix 45's ext_api.cpp hunk is neither on orionlayer-local "
                    "nor on fix 44's post-image")
                continue
            assert _vr_pre in _vr_src, (
                f"fix {_vr_n}'s pre-image is not orionlayer-local's {_vr_f}")
ok("open fixes 44 and 45 (the Ship Designer) are written and parked, not "
   "applied, 45 on top of 44: reported and never required, NOT APPLIED in "
   "entries, rows and patches, a one-line marker at every changed place, "
   "each entry's diff its file's; on this disk every pre-image is "
   "orionlayer-local's (45's ext_api.cpp hunk: 44's post-image) and no "
   "marker is in the tree")

# 8. OPEN FIXES 46 AND 47 — THE DIPLOMACY AUDIENCE, written and parked by
#    work order 185 part 9, NOT APPLIED; 47 applies on top of 46. The rules
#    of #7; 47's ext_api.h hunk sits on 46's new comment and is held to
#    46's post-image instead of the tree.
_vr_au = {46: ("doc/ext_audience_screen.patch",
               ["src/ext/ext_api.h", "src/game/dip_scrn_main.cpp"]),
          47: ("doc/ext_audience_state.patch",
               ["src/ext/ext_api.cpp", "src/ext/ext_api.h",
                "src/game/fields.cpp"])}
_vr_post46 = ""
for _vr_n, (_vr_p, _vr_files) in sorted(_vr_au.items()):
    _vr_mark = f"OrionLayer, open fix {_vr_n}."
    assert _vr_p in _vr_vc.REPORTED_PATCHES and _vr_p not in _vr_vc.LOCAL_PATCHES
    assert _vr_vc.REPORTED_PATCHES[_vr_p][1] == _vr_mark
    assert _vr_vc.FIX_NUMBERS[_vr_p] == (_vr_n,) and _vr_n not in _vr_want
    _vr_t = open(os.path.join(_vr_root, _vr_p), encoding="utf-8").read()
    assert "STATUS: NOT APPLIED" in _vr_t and "work order 185" in _vr_t
    _vr_d = _vr_t[_vr_t.index("diff --git"):]
    assert sorted(_vr_re.findall(r"(?m)^\+\+\+ b/(\S+)$", _vr_d)) == \
        sorted(_vr_files), (_vr_n, _vr_files)
    for _vr_h in _vr_re.split(r"(?m)^@@ ", _vr_d)[1:]:
        _vr_add = [_l for _l in _vr_h.splitlines() if _l.startswith("+")]
        assert not _vr_add or any(_vr_mark in _l for _l in _vr_add), (
            f"fix {_vr_n}: a changed place without its marker: {_vr_add[:2]}")
    _vr_e = _vr_fixes[_vr_fixes.index(f"\n## {_vr_n}. "):]
    _vr_e = _vr_e[:_vr_e.find("\n## ", 5)] if "\n## " in _vr_e[5:] else _vr_e
    assert "**Status: NOT APPLIED" in _vr_e[:400] and _vr_p in _vr_e[:900]
    for _vr_part in ("**Proof.**", "no offset, no fuzz", "**Recorded live**",
                     "**How to apply.**", "audience_reading.md"
                     if _vr_n == 46 else "on top of open fix"):
        assert _vr_part in _vr_e, f"entry {_vr_n} lacks {_vr_part}"
    _vr_j = _vr_e.index("```diff\n", _vr_e.index("**The exact change.**")) + 8
    _vr_nd = "".join(_l for _l in _vr_norm(_vr_d).splitlines(True)
                     if not _l.startswith(("diff --git", "index ")))
    assert _vr_e[_vr_j:_vr_e.index("```", _vr_j)] == _vr_nd, \
        f"entry {_vr_n}'s diff is not its patch file's"
    _vr_r = next(_l for _l in _vr_fixes.splitlines()
                 if _l.startswith(f"| {_vr_n} |"))
    assert "**Written, NOT APPLIED** — work order 185" in _vr_r
    if not os.path.isdir(os.path.join(_vr_tree_dir, ".git")):
        report(f"open fix {_vr_n} NOT checked against orionlayer-local — no "
               f"orion2re tree on this disk")
        continue
    for _vr_f in _vr_files:
        _vr_blk = _vr_d.split(f"+++ b/{_vr_f}\n", 1)[1].split("\ndiff --git", 1)[0]
        _vr_src = _vr_sp.run(["git", "-C", _vr_tree_dir, "show",
                              f"orionlayer-local:{_vr_f}"], capture_output=True,
                             text=True, errors="replace").stdout
        assert _vr_mark not in _vr_src, (
            f"fix {_vr_n}'s marker is in orionlayer-local's {_vr_f}")
        for _vr_h in _vr_re.split(r"(?m)^@@[^\n]*\n", _vr_blk)[1:]:
            _vr_pre = "\n".join(_l[1:] for _l in _vr_h.splitlines()
                                if _l[:1] in (" ", "-"))
            _vr_post = "\n".join(_l[1:] for _l in _vr_h.splitlines()
                                 if _l[:1] in (" ", "+"))
            if _vr_n == 46:
                _vr_post46 += _vr_post + "\n"
            if _vr_n == 47 and _vr_f == "src/ext/ext_api.h" and \
                    _vr_pre not in _vr_src:
                assert _vr_pre in _vr_post46, (
                    "fix 47's ext_api.h hunk is neither on orionlayer-local "
                    "nor on fix 46's post-image")
                continue
            assert _vr_pre in _vr_src, (
                f"fix {_vr_n}'s pre-image is not orionlayer-local's {_vr_f}")
ok("open fixes 46 and 47 (the diplomacy audience) are written and parked, "
   "not applied, 47 on top of 46: reported and never required, NOT APPLIED "
   "in entries, rows and patches, a one-line marker at every changed "
   "place, each entry's diff its file's; on this disk every pre-image is "
   "orionlayer-local's (47's ext_api.h hunk: 46's post-image) and no "
   "marker is in the tree")
