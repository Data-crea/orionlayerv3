# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 091_core_a_fallback_window_that_carries_one.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Renumbered 089 -> 091 when work order 162 part 5 added the suite's
# own size check: this module carries the two whole-run assertions —
# the push-only guards and the documents' check count — and they can
# only count what ran BEFORE them.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 7 check(s) it holds:
#   - a fallback window that carries one colour is blank, whatever `use_original` says — the reading w
#   - the orion2re tree is not uploaded from here: no engine source tracked by name or by content, no 
#   - livesend: wrong-shape sends refused with nothing sent, and the map's own list passes all three s
#   - all runnable tools import in a fresh process (the palette before any screen module, tools/toolen
#   - pre-commit hook refuses a commit on exit 139, on a failure and on a run without its PASSED line,
#   - the push-only tier is declared and guarded: checks, each with its reason, the guards and the lis
#   - CLAUDE.md paths resolve; both documents' check counts current


# ── A BLANK WINDOW IS NOT A PICTURE, AND A FLAG IS NOT EITHER ──
#
# Work order 129's report said the two turn-start dialogs appeared
# "as the original picture inside OrionLayer's window". Its own
# screenshots were ONE COLOUR, 100% (6, 8, 16) — the fill from
# main.py's else-branch — and its record.json carried
# `use_original: true`, which is the DISPATCHER'S FLAG and not the
# window. The flag's name was read as the observation.
#
# So the test for "the window shows the game's picture" is the
# window, and this is the one place that says what that means: a
# framebuffer the client HAS must reach the surface, and a surface
# carrying one distinct colour is blank however the flag reads.
# The live driver (tools/research_hd.py) records the same number
# beside every capture for the same reason.
_bw_state = _FbState(52)
_bw_client = _FbClient(_bw_state)
app2._apply_resolution(1920, 1080)
app2.client, app2.connected = _bw_client, True
app2.render_mode = "hd"
app2._update()
assert app2.dispatcher.use_original, "the fixture did not fall back"
app2._render()

def _bw_colours(surface):
    seen = set()
    for _y in range(0, surface.get_height(), 17):
        for _x in range(0, surface.get_width(), 23):
            seen.add(surface.get_at((_x, _y))[:3])
    return seen

_bw_seen = _bw_colours(app2.surface)
assert len(_bw_seen) > 1, (
    f"the window carries one colour, {_bw_seen} — that is the state "
    f"work order 129 reported as 'the original picture', and the "
    f"dispatcher flag says nothing about it")
# And the flag ALONE must not be able to stand in for it: with the
# same flag set and the renderer's picture suppressed, this check
# has to fail. Proven by suppressing it here.
_bw_real_render = app2.original_view.render
app2.original_view.render = lambda target, layout: target.fill((6, 8, 16))
try:
    app2._render()
    assert len(_bw_colours(app2.surface)) == 1, (
        "the control did not blank the window, so the check above "
        "proves less than it says")
finally:
    app2.original_view.render = _bw_real_render
app2._render()
assert len(_bw_colours(app2.surface)) > 1
ok("a fallback window that carries one colour is blank, whatever "
   "`use_original` says — the reading work order 129 got wrong")

# ── THE orion2re TREE IS NEVER UPLOADED (Data's hard rule) ─────
#
# CLAUDE.md: "the orion2re project is never uploaded anywhere — no
# push, no new remote, no fork, no copy of its tree or bundles to
# GitHub or any other host. Patch files under doc/ in orionlayerv3
# are explicitly allowed and not covered by this rule."
#
# The clone's disabled push URL holds one half. This holds the
# other, which is the half a mistake can reach: a source file of
# Joes' engine committed HERE is uploaded the next time this
# repository is pushed, and nothing else in the tree would notice.
# The patches are the deliberate exception — they carry engine
# lines on purpose and are how the work is handed over at all.
import subprocess as _o2_sp
_o2_root = os.path.dirname(SCREENS_DIR)
_o2_tracked = _o2_sp.run(["git", "-C", _o2_root, "ls-files"],
                       capture_output=True, text=True)
assert _o2_tracked.returncode == 0, _o2_tracked.stderr
_o2_files = [f for f in _o2_tracked.stdout.split("\n") if f]

def _o2_exempt(rel):
    """The rule's own exception, and only it."""
    return rel.startswith("doc/") and rel.endswith(".patch")

# 1. BY NAME. orionlayerv3 is Python; a C or C++ source here is
#    either a copy of the engine or the start of one. Checked
#    without needing ~/orion2re at all, so it holds on any machine.
_o2_src = sorted(f for f in _o2_files
                 if f.lower().endswith((".c", ".cc", ".cpp", ".cxx",
                                        ".h", ".hpp", ".inc"))
                 and not _o2_exempt(f))
assert not _o2_src, (
    f"C/C++ sources are tracked in orionlayerv3: {_o2_src}. The "
    f"orion2re project is never uploaded anywhere; only *.patch "
    f"under doc/ may carry engine lines")

# 2. AS A WHOLE TREE. A bundle or an archive of it is the same
#    upload in one file, and `git bundle --all` is exactly what
#    this project writes after every engine commit.
_o2_pack = sorted(f for f in _o2_files
                  if f.lower().endswith((".bundle", ".tar", ".tgz",
                                         ".tar.gz", ".zip", ".7z")))
assert not _o2_pack, (
    f"an archive or bundle is tracked in orionlayerv3: {_o2_pack}. "
    f"Bundles of the engine stay beside the tar backup in ~/")

# 3. BY CONTENT, when the engine tree is on this disk. Renaming a
#    file defeats check 1 and nothing else would catch it. Sizes
#    first, hashes only where a size collides, so this costs a
#    stat per tracked file and not a read.
_o2_tree = None
for _cand in ("~/orion2re", "~/src/orion2re", "/tmp/orion2re-main"):
    _c = os.path.expanduser(_cand)
    if os.path.isfile(os.path.join(_c, "src", "version.h")):
        _o2_tree = _c
        break
if _o2_tree is None:
    report("orion2re source tree not on this disk — the name and "
           "bundle halves of the upload rule were checked, the "
           "content half could not be")
else:
    _o2_by_size = {}
    for _dirpath, _dirnames, _filenames in os.walk(
            os.path.join(_o2_tree, "src")):
        for _fn in _filenames:
            _full = os.path.join(_dirpath, _fn)
            try:
                _o2_by_size.setdefault(
                    os.path.getsize(_full), []).append(_full)
            except OSError:
                continue
    _o2_hits = []
    _o2_hashed = 0
    for _rel in _o2_files:
        if _o2_exempt(_rel):
            continue
        _here = os.path.join(_o2_root, _rel)
        try:
            _size = os.path.getsize(_here)
        except OSError:
            continue
        _same = _o2_by_size.get(_size)
        if not _same:
            continue
        _o2_hashed += 1
        _mine = hashlib.sha256(
            io.open(_here, "rb").read()).hexdigest()
        for _theirs in _same:
            if hashlib.sha256(io.open(_theirs, "rb").read()
                              ).hexdigest() == _mine:
                _o2_hits.append((_rel, os.path.relpath(_theirs,
                                                       _o2_tree)))
                break
    assert not _o2_hits, (
        f"these tracked files are byte-identical to files in the "
        f"orion2re tree: {_o2_hits}. Renaming one does not make it "
        f"ours to upload")
    report(f"upload rule: {len(_o2_by_size)} distinct sizes in "
           f"{os.path.relpath(_o2_tree, os.path.expanduser('~'))}"
           f"/src, {_o2_hashed} tracked files hashed on a size "
           f"collision")

# AND THE RULE IS WRITTEN DOWN WHERE IT IS READ. A check without
# the sentence it enforces is a check nobody can act on, and the
# exception has to travel with it or the patches look like a
# violation.
_o2_claude = _lre.sub(r"\s+", " ", io.open(
    os.path.join(_o2_root, "CLAUDE.md"), encoding="utf-8").read())
for _o2_phrase in (
        "the orion2re project is never uploaded anywhere",
        "no push, no new remote, no fork",
        "patch files under `doc/` in orionlayerv3 are explicitly "
        "allowed"):
    assert _o2_phrase.lower() in _o2_claude.lower(), (
        f"CLAUDE.md no longer says {_o2_phrase!r} — the rule this "
        f"check enforces has left the only place a reader looks "
        f"for it")
assert len([f for f in _o2_files if _o2_exempt(f)]) >= 1, (
    "no doc/*.patch is tracked any more; the exemption in this "
    "check now protects nothing and should be re-read before it "
    "quietly widens")
ok("the orion2re tree is not uploaded from here: no engine source "
   "tracked by name or by content, no bundle, and CLAUDE.md still "
   "carries the rule and its patch exception")

# A LIVE TOOL IS A CLIENT (work order 129 A): `tools/livesend.py`
# identifies the dialog from the field list of the state it is handed
# at that moment and refuses otherwise. Twice a tool sent into a dialog
# it had misread — the scrapped colony base (122) and the SIGSEGV in
# the research prompt (128 C, open fix 23). Handed the wrong shape, the
# helper must send NOTHING and say so.
sys.path.insert(0, os.path.join(os.path.dirname(SCREENS_DIR), "tools"))
import livesend as _ls
from core.game_state import FieldInfo as _LsField
from screens.game_menu import nodes as _ls_nodes

class _LsClient:
    def __init__(self, fields, screen):
        self.log = []
        self.state = type("S", (), {})()
        self.state.fields = fields
        self.state.current_screen = screen

    def activate_field(self, i):
        self.log.append(("act", i))

    def inject_click(self, x, y):
        self.log.append(("click", x, y))

    def inject_key(self, k):
        self.log.append(("key", k))

def _ls_fields(rows):
    out = []
    for _r in rows:
        _f = _LsField()
        (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
         _f.hotkey) = _r
        out.append(_f)
    return out
import json as _ls_json
_ls_map = _ls_fields(_ls_json.load(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools",
    "galaxy_box_fields.json")))["closed"])
# The research prompt's shape under the map's own screen number — the
# list 128 C crashed the game in.
_ls_research = _ls_fields(
    [(0, 0, 0, 0, 0, 0, 0)]
    + [(_i + 1, 176, 51 + _i * 15, 394, 84 + _i * 15, 7, 0)
       for _i in range(8)]
    + [(9, 102, 30, 162, 45, 1, 0), (10, 0, 0, 639, 479, 7, 0)])
_ls_refused = 0
for _ls_name, _ls_call, _ls_state in (
        ("activate into the research prompt",
         lambda c: _ls.activate(c, 9, screen=0,
                                shape=_ls.on_galaxy_map, label="probe"),
         (_ls_research, 0)),
        ("activate an index the list does not hold",
         lambda c: _ls.activate(c, 99, screen=0,
                                shape=_ls.on_galaxy_map, label="probe"),
         (_ls_map, 0)),
        ("activate a field of another type",
         lambda c: _ls.activate(c, 9, screen=0, field_type=12,
                                shape=_ls.on_galaxy_map, label="probe"),
         (_ls_map, 0)),
        ("click where no field is",
         lambda c: _ls.click(c, 5, 5, screen=0,
                             shape=_ls.on_galaxy_map, label="probe"),
         (_ls_map, 0)),
        ("key into a list of the wrong shape",
         lambda c: _ls.key(c, ord("n"), screen=20,
                           shape=_ls.on_colony_summary, label="probe"),
         (_ls_map, 20)),
        ("key with neither screen nor shape",
         lambda c: _ls.key(c, 27, label="probe"),
         (_ls_map, 0)),
        ("the game on another screen",
         lambda c: _ls.activate(c, 9, screen=0,
                                shape=_ls.on_galaxy_map, label="probe"),
         (_ls_map, 8)),
        ("a dialog the GAME menu is not showing",
         lambda c: _ls.activate(c, 1, screen=8,
                                shape=_ls.in_game_menu(_ls_nodes.SAVE),
                                label="probe"),
         (_ls_map, 8))):
    _ls_c = _LsClient(*_ls_state)
    try:
        _ls_call(_ls_c)
    except _ls.WrongDialog as _ls_err:
        _ls_refused += 1
        assert "nothing sent" in str(_ls_err), _ls_err
    assert _ls_c.log == [], (_ls_name, _ls_c.log)
assert _ls_refused == 8, _ls_refused
# And it does send when the shape holds: the map's own list.
_ls_ok = _LsClient(_ls_map, 0)
_ls.activate(_ls_ok, 9, screen=0, shape=_ls.on_galaxy_map,
             field_type=0, rect=(244, 455, 298, 473), label="probe")
_ls.click(_ls_ok, 300, 200, screen=0, shape=_ls.on_galaxy_map,
          label="probe")
_ls.key(_ls_ok, ord("g"), screen=0, shape=_ls.on_galaxy_map,
        label="probe")
assert _ls_ok.log == [("act", 9), ("click", 300, 200), ("key", ord("g"))], \
    _ls_ok.log
ok(f"livesend: {_ls_refused} wrong-shape sends refused with nothing sent, "
   f"and the map's own list passes all three send kinds")

# EVERY RUNNABLE TOOL IMPORTS IN A FRESH PROCESS (work order 126 D).
# Screen modules read colours with no code default at import, and five
# tools imported them before anything had initialised the palette —
# `colony_move_hd.py` could not even print --help for three days while
# every check stayed green, because THIS process initialised the
# palette long before any check touched a tool. So the import runs in a
# new interpreter, from outside the tree, with only `tools/` on the path
# (what `python tools/x.py` gives it). Libraries without `__main__`
# (fixtures, colony_roundtrip, raceicon_sheets) are imported by the
# tools that need them and are covered through those.
if slow("tools_import"):
    import subprocess as _ti_sp
    import tempfile as _ti_tf
    _ti_root = os.path.dirname(SCREENS_DIR)
    _ti_tools = os.path.join(_ti_root, "tools")
    _ti_env = dict(os.environ, SDL_VIDEODRIVER="dummy",
                   SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
    _ti_bad, _ti_n = [], 0
    with _ti_tf.TemporaryDirectory() as _ti_cwd:
        for _ti_path in sorted(glob.glob(os.path.join(_ti_tools, "*.py"))):
            _ti_name = os.path.basename(_ti_path)[:-3]
            if _ti_name == "smoke_test":
                continue
            with open(_ti_path, encoding="utf-8") as _fh:
                if "__main__" not in _fh.read():
                    continue
            _ti_n += 1
            _ti_r = _ti_sp.run(
                [sys.executable, "-c",
                 f"import sys; sys.path[0] = {_ti_tools!r}; import {_ti_name}"],
                cwd=_ti_cwd, capture_output=True, text=True, env=_ti_env,
                timeout=120)
            if _ti_r.returncode != 0:
                _ti_bad.append((_ti_name, (_ti_r.stderr.strip().splitlines()
                                           or ["?"])[-1]))
    assert _ti_n >= 30, f"only {_ti_n} runnable tools found"
    assert not _ti_bad, f"tools that cannot be imported: {_ti_bad}"
    ok(f"all {_ti_n} runnable tools import in a fresh process (the palette "
       f"before any screen module, tools/toolenv.py)")

# THE COMMIT IS COUPLED TO THIS SUITE (work order 126 part B, decision
# 31). A commit once went through after a run had exited 139, because
# nothing connected the two; `tools/githooks/pre-commit` now refuses
# any exit but 0. The rule is asserted by RUNNING the hook against a
# stub suite in a throwaway tree — a real SIGSEGV, a plain failure, a
# clean exit that never printed its PASSED line, and a pass — so a
# hook edited into a formality fails here rather than at the next
# crashed run. Whether THIS clone has the hook switched on is git
# config, which a clone does not inherit: reported, not asserted,
# because `tools/setup.py` is what switches it on (decision 38's
# shape — a state to explain, not an error).
import shutil as _hk_sh
import subprocess as _hk_sp
import tempfile as _hk_tf
_hk_root = os.path.dirname(SCREENS_DIR)
_hk_src = os.path.join(_hk_root, "tools", "githooks", "pre-commit")
assert os.path.isfile(_hk_src) and os.access(_hk_src, os.X_OK), _hk_src
with open(os.path.join(_hk_root, "tools", "setup.py"),
          encoding="utf-8") as _fh:
    _hk_setup = _fh.read()
assert 'HOOKS_PATH = "tools/githooks"' in _hk_setup, (
    "tools/setup.py no longer points core.hooksPath at tools/githooks")
_hk_stubs = {
    "segfault": ("import os, signal\nprint('  ok  one')\n"
                 "os.kill(os.getpid(), signal.SIGSEGV)\n", 139, 1),
    "failure": ("raise AssertionError('red')\n", 1, 1),
    "silent": ("print('nothing')\n", 0, 1),
    "green": ("print('SMOKE TEST PASSED — 1 checks green')\n", 0, 0),
}
with _hk_tf.TemporaryDirectory() as _hk_tmp:
    os.makedirs(os.path.join(_hk_tmp, "tools", "githooks"))
    _hk_dst = os.path.join(_hk_tmp, "tools", "githooks", "pre-commit")
    _hk_sh.copy2(_hk_src, _hk_dst)
    for _hk_name, (_hk_body, _hk_suite_exit, _hk_want) in _hk_stubs.items():
        with open(os.path.join(_hk_tmp, "tools", "smoke_test.py"), "w",
                  encoding="utf-8") as _fh:
            _fh.write(_hk_body)
        _hk_suite = _hk_sp.run(
            ["sh", "-c", "python tools/smoke_test.py >/dev/null 2>&1"],
            cwd=_hk_tmp).returncode
        assert _hk_suite == _hk_suite_exit, (_hk_name, _hk_suite)
        _hk_got = _hk_sp.run(["sh", _hk_dst], cwd=_hk_tmp,
                             capture_output=True, text=True,
                             env=dict(os.environ, TMPDIR=_hk_tmp))
        assert _hk_got.returncode == _hk_want, (
            _hk_name, _hk_got.returncode, _hk_got.stdout[-400:])
_hk_cfg = _hk_sp.run(["git", "config", "--get", "core.hooksPath"],
                     cwd=_hk_root, capture_output=True, text=True)
report("pre-commit hook in this clone: " + (
    "ON (core.hooksPath = tools/githooks)"
    if _hk_cfg.stdout.strip() == "tools/githooks"
    else "OFF — run: python tools/setup.py"))
ok("pre-commit hook refuses a commit on exit 139, on a failure and on a "
   "run without its PASSED line, and allows it on a pass")

# CLAUDE.md is what a Claude Code session reads before touching
# anything, so a stale pointer in it misleads at exactly the
# moment nobody is watching. Two things can rot: a path that no
# longer exists, and the check count, which this test knows
# better than any document does.
_root = os.path.dirname(SCREENS_DIR)
_cmd_path = os.path.join(_root, "CLAUDE.md")
assert os.path.exists(_cmd_path), "CLAUDE.md is missing"
with open(_cmd_path, encoding="utf-8") as _fh:
    _cmd = _fh.read()
for _ref in re.findall(r"`([\w./]+\.(?:md|py|json|txt))`", _cmd):
    if _ref.startswith(("file.", "screen.", "layout.", "boxes.",
                        "help.")):
        continue          # generic examples, not paths
    assert os.path.exists(os.path.join(_root, _ref)), \
        f"CLAUDE.md points at a missing file: {_ref}"

# THE COUNT IS HAND-COPIED IN TWO DOCUMENTS, so per decision 36 it
# needs a checker or it is an intention. CLAUDE.md had one and
# v3_projektstatus.md's Snapshot table did not; the table said 55
# against a suite of 63 for four sessions, in the file that
# declares itself the count's single home.
#
# BOTH ARE ASSERTED AGAINST THIS RUN, never against each other.
# Two documents agreeing with one another and not with the suite
# is precisely the state a cross-check would call green, and it is
# the state this replaces.
# ── THE PUSH-ONLY LIST IS DECLARED, AND THIS HOLDS THE TREE TO IT ──
#
# Work order 158. The same shape as the marker inventory, and for
# the same reason: SLOW_TIER is a list kept by hand, and a list
# kept by hand is legitimate only with a checker. Both directions,
# because they fail differently — a `slow(...)` guard nobody
# declared is a check that leaves the commit gate silently, and a
# declaration with no guard is a name that says a check is slow
# when nothing is skipping it.
#
# This runs in BOTH tiers, and it must: the fast tier is the one a
# commit goes through, so it is the tier that has to notice.
_st_src = suite_source()
_st_used = set(re.findall(r'^\s*if slow\("([^"]+)"\):', _st_src, re.M))
_st_declared = set(SLOW_TIER)
assert _st_used == _st_declared, (
    f"the push-only list and the guards disagree — "
    f"guarded but undeclared: {sorted(_st_used - _st_declared)}; "
    f"declared but unguarded: {sorted(_st_declared - _st_used)}. "
    f"SLOW_TIER is the one place the list lives")
for _st_n, (_st_c, _st_why) in SLOW_TIER.items():
    assert _st_c >= 1, f"{_st_n} declares {_st_c} checks"
    assert len(_st_why) > 40, (
        f"{_st_n} carries no reason. Every push-only check says "
        f"what makes it expensive, beside its name")
assert SLOW_SEEN == _st_declared, (
    f"this run never reached {sorted(_st_declared - SLOW_SEEN)} — a "
    f"guard behind a branch that did not run cannot be tiered")
if TIER == "fast":
    assert set(SKIPPED) == _st_declared, sorted(_st_declared - set(SKIPPED))
else:
    assert not SKIPPED, SKIPPED
ok(f"the push-only tier is declared and guarded: "
   f"{len(_st_declared)} checks, each with its reason, the guards "
   f"and the list agreeing in both directions")

_counts = [("CLAUDE.md", _cmd, r"(\d+) checks, headless"),
           ("v3_projektstatus.md", None,
            r"smoke_test\.py` — \*\*(\d+) checks\*\*")]
for _doc, _text, _pat in _counts:
    if _text is None:
        with open(os.path.join(_root, _doc), encoding="utf-8") as _fh:
            _text = _fh.read()
    _claimed = re.search(_pat, _text)
    assert _claimed, f"{_doc} no longer states a check count"
    # PASS + 1 for the check this loop is inside, + whatever the
    # fast tier skipped: BOTH TIERS ASSERT THE FULL COUNT, so a
    # fast run still holds the two documents to the whole suite
    # and cannot go green against a number it did not reach.
    _full = PASS + 1 + sum(SKIPPED.values())
    assert int(_claimed.group(1)) == _full, (
        f"{_doc} says {_claimed.group(1)} checks, this run has "
        f"{_full} ({PASS + 1} run"
        + (f" + {sum(SKIPPED.values())} push-only" if SKIPPED else "")
        + ")")
ok("CLAUDE.md paths resolve; both documents' check counts current")
