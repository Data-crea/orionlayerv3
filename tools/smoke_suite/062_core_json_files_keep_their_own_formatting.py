# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 062_core_json_files_keep_their_own_formatting.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - JSON files keep their own formatting ( exceptions, exact in both directions; of generated files 
#   - fixture table (every named save has checkable bytes, of them, none in the game's folder)
#   - window size is the surface's, not the request's (a refused size is adopted and reported, a grant
#   - user settings: absent file silent with defaults, corrupt file one error line, defaults, no raise
#   - user settings: a key this build does not know is kept through load and save; saving twice writes
#   - user settings: user_settings.json is in .gitignore and is the path the loader uses
#   - user settings: ignore rule reported (no .git to ask)
#   - banner tints: no literal table in core/banner.py; colors.json [banner] and [banner_hd] each hold


# ── A WRITER TAKES THE FILE'S OWN FORMATTING ────────────────
#
# `indent=2` is this tree's convention for hand-edited JSON, and a
# tool that rewrites one of these files with anything else turns
# every future two-line edit into a whole-file diff. It happened
# on 9 September 2026: a script rewrote `colors.json` at
# `indent=1` and the commit that added two colours showed 694
# insertions and 694 deletions, with the actual change buried in
# it. Nothing was wrong with the data and nothing could be read.
#
# The rule is stated as a ROUND TRIP rather than as "use
# indent=2": load the file, dump it back under the convention,
# and require the bytes. That also catches a writer that drops a
# trailing newline or reorders keys, which no indent constant
# would.
#
# THE EXCEPTIONS ARE EXACT IN BOTH DIRECTIONS, like the
# over-300-lines list: a file here that round-trips has stopped
# being an exception and must leave, or the list stops meaning
# anything.
_json_root = os.path.dirname(SCREENS_DIR)
_JSON_OTHER = {
    # extracted from the player's own LBX files; the extractors
    # own their formatting and the files are not hand-edited.
    os.path.join("assets", "shared", "help", "help_en.json"),
    # brief 107: the second techname range and MAINTEXT, both written
    # at indent=1 like the building names.
    os.path.join("assets", "shared", "names", "shipparts_en.json"),
    os.path.join("assets", "shared", "names", "maintext_en.json"),
    os.path.join("assets", "shared", "names", "buildings_en.json"),
    os.path.join("assets", "shared", "names", "estrings_en.json"),
    # work order 130 D: the research names, a third file out of the
    # same TECHNAME block, and BILLTEXT's messages — both written at
    # indent=1 like their siblings.
    os.path.join("assets", "shared", "names", "techfields_en.json"),
    os.path.join("assets", "shared", "names", "billtext_en.json"),
    # hand-written with inline arrays for readability; never
    # rewritten by a tool.
    os.path.join("screens", "_template", "boxes.json"),
    os.path.join("screens", "colony_summary", "help.json"),
    os.path.join("screens", "galaxy_map", "help.json"),
    os.path.join("screens", "galaxy_map", "layout.json"),
    os.path.join("screens", "main_menu", "help.json"),
    os.path.join("screens", "new_game", "help.json"),
    os.path.join("screens", "planets", "help.json"),
}
_json_seen, _json_bad = set(), []
for _dirpath, _dirnames, _filenames in os.walk(_json_root):
    _dirnames[:] = [_d for _d in _dirnames
                    if _d not in (".git", "__pycache__")]
    for _fn in _filenames:
        if not _fn.endswith(".json"):
            continue
        _full = os.path.join(_dirpath, _fn)
        _rel = os.path.relpath(_full, _json_root)
        _raw = io.open(_full, encoding="utf-8").read()
        try:
            _obj = _sjson.loads(
                _raw, object_pairs_hook=collections.OrderedDict)
        except ValueError:
            _json_bad.append((_rel, "not valid JSON"))
            continue
        _round = any(_sjson.dumps(_obj, indent=2) + _t == _raw
                     for _t in ("", "\n"))
        if _rel in _JSON_OTHER:
            _json_seen.add(_rel)
            if _round:
                _json_bad.append(
                    (_rel, "round-trips at indent=2 and is still "
                           "listed as an exception"))
        elif not _round:
            _json_bad.append(
                (_rel, "does not round-trip at indent=2 — a writer "
                       "has reformatted it, and the next real edit "
                       "will be invisible in the diff"))
assert not _json_bad, "JSON formatting: " + "; ".join(
    f"{_f}: {_w}" for _f, _w in _json_bad)
# GENERATED FROM THE PLAYER'S INSTALL, GITIGNORED, AND THEREFORE
# ALLOWED TO BE ABSENT — 13 September 2026. Until then every
# exception had to exist, so a fresh clone (which has none of the
# extracted files, decision 40) failed this check before anyone
# had run an extractor. The list is separate from _JSON_OTHER
# because the two answer different questions: hestrings_en.json
# round-trips at indent=2 and is no formatting exception, but it is
# just as absent from a clone. Each entry must really be ignored by
# git — a committed file on this list could vanish unnoticed.
_JSON_ABSENT_OK = {
    os.path.join("assets", "shared", "help", "help_en.json"),
    os.path.join("assets", "shared", "names", "buildings_en.json"),
    os.path.join("assets", "shared", "names", "estrings_en.json"),
    os.path.join("assets", "shared", "names", "hestrings_en.json"),
    os.path.join("assets", "shared", "names", "shipparts_en.json"),
    os.path.join("assets", "shared", "names", "maintext_en.json"),
    # Work order 130 D's two, added here 18 September 2026 when a
    # fresh-clone run for the push found them missing. They went
    # into _JSON_OTHER and not into this list, and on a machine
    # where both had been extracted the suite stayed green — which
    # is the very trap the paragraph above describes, walked into a
    # second time by the session that read it.
    os.path.join("assets", "shared", "names", "techfields_en.json"),
    os.path.join("assets", "shared", "names", "billtext_en.json"),
    # THE TWO THE REGISTRY GAINED IN PIECE 1, and they were not
    # here — found by piece 4's cross-check the moment it was
    # written, which is the argument for tying the two lists
    # together instead of maintaining both.
    os.path.join("assets", "shared", "names", "kentext_en.json"),
    os.path.join("screens", "fleets", "assets", "gamedata",
                 "manifest.json"),
}
if os.path.isdir(os.path.join(_json_root, ".git")):
    import subprocess as _json_sp
    _json_ign = _json_sp.run(
        ["git", "-C", _json_root, "check-ignore", "--no-index",
         *sorted(_JSON_ABSENT_OK)], capture_output=True, text=True)
    _json_tracked = _JSON_ABSENT_OK - set(
        _json_ign.stdout.split())
    assert not _json_tracked, (
        f"these files may be absent from the tree but git does not "
        f"ignore them — a committed file must not be allowed to "
        f"go missing: {sorted(_json_tracked)}")
else:
    report("JSON absent-allowed list NOT checked against .gitignore "
           "— no .git directory")

# ── EVERY REGISTERED PATH IS IGNORED, AND THE TWO LISTS AGREE ──
#
# Piece 4 of the clone-only fault. `setup.from_game()` names every
# file derived from the player's install; each one must really be
# gitignored, because a COMMITTED file on that list could vanish
# and nothing would say so — the same argument `_JSON_ABSENT_OK`
# already carried, applied to the list that governs.
#
# **AND `_JSON_ABSENT_OK` IS HELD TO THE REGISTRY**, which is the
# fault `5402b7d` was: two new files went into `_JSON_OTHER`
# instead of the absent-allowed list, the suite stayed green on
# the machine that had extracted them, and a clone went red. The
# two lists are no longer independent — every .json the registry
# names has to be on the absent-allowed list, so forgetting one
# fails here rather than in a clone.
import importlib.util as _reg_ilu
_reg_spec = _reg_ilu.spec_from_file_location(
    "_setup_registry", os.path.join(_json_root, "tools", "setup.py"))
_reg_mod = _reg_ilu.module_from_spec(_reg_spec)
_reg_spec.loader.exec_module(_reg_mod)
_reg_rel = [os.path.relpath(_p, _json_root)
            for _p, _w, _c in _reg_mod.from_game()]
assert len(_reg_rel) >= 12, _reg_rel

if os.path.isdir(os.path.join(_json_root, ".git")):
    # **ASK WITH AND WITHOUT A TRAILING SLASH, and this check
    # learned why the hard way.** `.gitignore` line 75 is
    # `screens/galaxy_map/assets/nebula_ref/` — a DIRECTORY rule —
    # and `git check-ignore` can only tell a bare path is a
    # directory by looking at the disk. Here the directory exists
    # and it matched; in a clone, where every one of these files
    # is absent by definition, it did not, and the first version
    # of this check went red on `nebula_ref` in the clone while
    # staying green here.
    #
    # That is the fault the four pieces are about, committed
    # inside the check that enforces the rule against it, and the
    # fresh-clone run caught it — which is the argument the
    # fundament entry makes for keeping that run. The
    # trailing-slash form matches from the `.gitignore` text
    # alone, so asking both ways is machine-independent.
    _reg_ask = sorted(set(_reg_rel) | {_r + "/" for _r in _reg_rel})
    _reg_out = _json_sp.run(
        ["git", "-C", _json_root, "check-ignore", "--no-index",
         *_reg_ask], capture_output=True, text=True)
    _reg_hit = set(_reg_out.stdout.split())
    _reg_notign = sorted(_r for _r in set(_reg_rel)
                         if _r not in _reg_hit
                         and _r + "/" not in _reg_hit)
    assert not _reg_notign, (
        f"these are registered as derived from the player's own "
        f"installation and git does NOT ignore them: {_reg_notign}. "
        f"Either the file is committed, in which case it does not "
        f"belong in from_game(), or .gitignore has a hole and a "
        f"player's own data could be committed by accident")
else:
    report("the derived registry was NOT checked against "
           ".gitignore — no .git directory")

#    and the two lists cannot drift: every registered .json is on
#    the absent-allowed list
_reg_json = {_r for _r in _reg_rel if _r.endswith(".json")}
_reg_missing = sorted(_reg_json - set(_JSON_ABSENT_OK))
assert not _reg_missing, (
    f"{_reg_missing} are registered as derived from the player's "
    f"install and are not in _JSON_ABSENT_OK, so the formatting "
    f"check demands they exist and a fresh clone fails on them. "
    f"That is exactly what happened in 5402b7d")
_json_absent = sorted(_f for _f in _JSON_ABSENT_OK if not
                      os.path.exists(os.path.join(_json_root, _f)))
_json_missing = _JSON_OTHER - _json_seen - _JSON_ABSENT_OK
assert not _json_missing, (
    f"these files are listed as formatting exceptions and are not "
    f"in the tree: {sorted(_json_missing)}")
# ── AND EVERY TRACKED .json ENDS WITH EXACTLY ONE NEWLINE ─────
#
# The tree's convention, and two writers were breaking it:
# `core.box.save_boxes` (every F5 save) and
# `select_race.save_races`. Seven tracked files carried the
# fingerprint — two boxes.json, races.json, traits.json, a
# layout.json and two 9slice.json — and each showed up in a diff
# as "\ No newline at end of file" beside whatever had really
# changed. `tools/frame_holes.py` had already worked round it on
# its own side and its comment named `save_boxes` as the culprit;
# a comment is not a fix and the next writer would have done it
# again. Fixed at both sources, 20 September 2026, and held here
# so a third writer cannot reintroduce it.
#    TRACKED files only, which is also what makes this clone-safe
#    by construction: the extracted catalogues are gitignored, so
#    `git ls-files` never names them and their absence cannot fail
#    this.
import subprocess as _nl_sp
_nl_list = _nl_sp.run(["git", "ls-files", "*.json"], cwd=_json_root,
                      capture_output=True, text=True)
assert _nl_list.returncode == 0, _nl_list.stderr
_nl_files = [_f for _f in _nl_list.stdout.split("\n") if _f]
assert len(_nl_files) >= 30, (
    f"only {len(_nl_files)} tracked .json found; the newline check "
    f"would be close to vacuous")
_nl_bad = []
for _nl_rel in _nl_files:
    with open(os.path.join(_json_root, _nl_rel), "rb") as _nl_fh:
        _nl_raw = _nl_fh.read()
    if not _nl_raw.endswith(b"\n"):
        _nl_bad.append((_nl_rel, "no trailing newline"))
    elif _nl_raw.endswith(b"\n\n"):
        _nl_bad.append((_nl_rel, "more than one trailing newline"))
assert not _nl_bad, (
    "JSON trailing newline: " + "; ".join(
        f"{_f}: {_w}" for _f, _w in _nl_bad)
    + ". Every writer ends the file with exactly one; "
      "core.box.save_boxes and select_race.save_races were the two "
      "that did not")
_json_newline_n = len(_nl_files)

ok(f"JSON files keep their own formatting ({len(_JSON_OTHER)} "
   f"exceptions, exact in both directions; {len(_json_absent)} of "
   f"{len(_JSON_ABSENT_OK)} generated files absent, which a fresh "
   f"clone may be; {_json_newline_n} tracked files end in exactly "
   f"one newline; {len(_reg_rel)} registered derived paths all "
   f"ignored and every one of their .json on the absent list)")

# ── EVERY FIXTURE A RUN CAN NAME HAS BYTES IT CAN CHECK ─────
#
# `FIXTURES` is the fingerprint — stardate, stars, colonies — and
# `FIXTURE_FILES` is the file those bytes are compared against. A
# key in the first without an entry in the second is a save a run
# can claim and cannot verify, which is the exact gap that let a
# diagnostic make thirty pop moves while every line said "fixture:
# reference".
sys.path.insert(0, os.path.join(_root_fx := os.path.dirname(
    SCREENS_DIR), "tools"))
import fixtures as _fx
assert set(_fx.FIXTURES) == set(_fx.FIXTURE_FILES), (
    f"these fixtures can be named but not verified: "
    f"{sorted(set(_fx.FIXTURES) - set(_fx.FIXTURE_FILES))}; and "
    f"these have bytes but no fingerprint: "
    f"{sorted(set(_fx.FIXTURE_FILES) - set(_fx.FIXTURES))}")
# AND NONE OF THEM POINTS INTO THE GAME'S OWN FOLDER. `SAVE10.GAM`
# is the autosave slot and the game rewrites it at every turn end,
# so a fixture that named it would silently become "whatever was
# saved last" — and `verify_colonies` would compare a run against
# that and report a match. The fixture is a COPY, kept beside the
# other two.
for _fk, _fv in _fx.FIXTURE_FILES.items():
    _fp = _fv["file"]
    assert not os.path.isabs(_fp) and os.sep not in _fp, (
        f"fixture {_fk} names a path ({_fp!r}); it must be a file "
        f"inside the fixtures directory")
    assert "Master of Orion" not in _fp, (
        f"fixture {_fk} points into the game's own folder, which "
        f"the game overwrites")
    assert len(_fv["sha256"]) == 64 and _fv["colony_count"] > 0
# ── THE COUNT IS CHECKED AGAINST THE FILE, NOT AGAINST ITSELF ──
#
# `fixture_colonies` slices `colony_count` records and returns
# them; the count is the input AND the implicit expectation, so a
# wrong one returns fewer records and NO error. It happened:
# natives said 36 where the file holds 38, and the two it cut off
# included Urna I — the only colony in any fixture with native
# pops, and the one the fixture is named for. See "A READER WHOSE
# EXTENT COMES FROM THE SAME TABLE AS ITS CONTENTS" in the
# fundament's Diagnosis section.
#
# The second source here is the FILE'S OWN STRUCTURE: the record
# one past the end must NOT look like a colony. Past the array
# the bytes are some other structure, and on all three fixtures
# they read as owner -5 or -84 with planet -1 — outside any legal
# range — while every record inside reads as a real colony. A
# count that is too small leaves a plausible record sitting just
# past its own end, which is exactly what 36 did.
def _fx_plausible(_blob, _off, _i):
    """Does record `_i` read as a colony? (owner, planet, n_pops)"""
    _s = _off + _i * _fx.COLONY_SIZE
    if _s + _fx.COLONY_SIZE > len(_blob):
        return False
    _owner = struct.unpack_from("<b", _blob, _s)[0]
    _planet = struct.unpack_from("<h", _blob, _s + 2)[0]
    _n = _blob[_s + 10]
    return -1 <= _owner <= 7 and _n <= 42 and -1 <= _planet <= 2000

for _fk, _fv in sorted(_fx.FIXTURE_FILES.items()):
    _fpath = os.path.join(_fx.FIXTURE_DIR, _fv["file"])
    if not os.path.exists(_fpath):
        continue                      # absence is a state
    with open(_fpath, "rb") as _fh:
        _fblob = _fh.read()
    _fn, _foff = _fv["colony_count"], _fv["colony_offset"]
    assert _fx_plausible(_fblob, _foff, _fn - 1), (
        f"fixture {_fk}: record {_fn - 1}, the last one "
        f"colony_count claims, does not read as a colony — the "
        f"count is too BIG or the offset is wrong")
    assert not _fx_plausible(_fblob, _foff, _fn), (
        f"fixture {_fk}: record {_fn} reads as a colony and "
        f"colony_count says the array ended at {_fn}. The count "
        f"is TOO SMALL and `fixture_colonies` is returning a "
        f"short array with no error — this is the natives/Urna I "
        f"fault, which cost a false 'no fixture has a native pop'")
    # AND THE TWO TABLES AGREE. `FIXTURES` fingerprints a live
    # snapshot and `FIXTURE_FILES` slices the file; they carry
    # the same number for different reasons, and the fingerprint
    # is what a running game is matched against.
    assert _fx.FIXTURES[_fk]["colonies"] == _fn, (
        f"fixture {_fk}: the fingerprint says "
        f"{_fx.FIXTURES[_fk]['colonies']} colonies and the file "
        f"table says {_fn}; a snapshot cannot match both")

# ── `fixture_name` NEVER ANSWERS None FOR A FIXTURE ON DISK ──
#
# It returns "the name, or None", and while the count above was
# wrong it returned None for a save sitting right in front of
# it — which nothing treats as a fault, because None is also the
# legitimate answer for an unknown save. That is why the wrong
# count survived: the one function positioned to notice reported
# it in the one way nobody reads. So the answer is DEMANDED here
# rather than left to a caller that has no way to tell the two
# apart. See "A FUNCTION THAT FAILS BY RETURNING None" in the
# fundament.
class _FxState:
    """The three fields `fixture_name` fingerprints on.

        **ONLY `colonies` IS A SECOND SOURCE HERE** — it comes from
        `fixture_colonies`, i.e. from the file, which is what makes
        the natives/Urna I fault reachable offline. `stardate` and
        `stars` are echoed back out of `FIXTURES`, so this check
        cannot say they are right; it says the lookup ANSWERS. Those
        two are verified only against a running game, and the live
        runs in `v3_projektstatus.md` are where that happened.
        Written out because a check that looks like it validates
        three fields and validates one is worse than a check that
        says so.
        """

    def __init__(self, _recs, _stardate, _stars):
        self.colonies_raw = _recs
        self.num_colonies = len(_recs)
        self.stardate = _stardate
        self.stars = [None] * _stars

for _fk in sorted(_fx.FIXTURE_FILES):
    _frecs, _fwhy = _fx.fixture_colonies(_fk)
    if _frecs is None:
        continue                      # absence is a state
    _fstate = _FxState(_frecs, _fx.FIXTURES[_fk]["stardate"],
                       _fx.FIXTURES[_fk]["stars"])
    assert _fx.fixture_name(_fstate) == _fk, (
        f"fixture_name answered {_fx.fixture_name(_fstate)!r} for "
        f"{_fk} built from its own file. It fails by returning "
        f"None, which every caller renders as 'not a known "
        f"fixture' — so a broken table looks exactly like an "
        f"unknown save")

# Absence is a state: a clone has no fixtures and says so rather
# than skipping (decision 42's pattern), so this reports what it
# found instead of demanding the files exist.
_fx_have = [k for k in sorted(_fx.FIXTURE_FILES)
            if _fx.fixture_colonies(k)[0] is not None]
print(f"      fixtures readable on this disk: "
      f"{_fx_have or 'none — verify_colonies will say so'}")
ok(f"fixture table (every named save has checkable bytes, "
   f"{len(_fx.FIXTURE_FILES)} of them, none in the game's folder)")

# ── THE WINDOW IS WHAT WAS GRANTED, NOT WHAT WAS ASKED FOR ──
#
# `Layout`, every box, the cursor and the frame plate are built
# from `win_w`/`win_h`, so if those are the REQUESTED size and the
# window manager gave less, the whole screen is laid out for a
# window that does not exist. Measured 9 September 2026 on a
# single 3440x1440 display: 2560x1440 is granted 2560x1371,
# 3840x2160 — one of the four sizes F9 offers — is granted
# 3440x1371, and **no `VIDEORESIZE` is delivered for either**, so
# nothing downstream could notice. That is the second fault
# behind Data's screenshots, and the one that made every panel
# overflow at F9 "4K".
#
# THE STATE IS FORCED, because it cannot be reached here: the
# dummy video driver grants every request exactly, so a check
# that merely called `_set_mode` would pass against the bug. Same
# shape as the help-file check that builds both of its states
# rather than reading the tester's disk.
_grant = [None]
_real_set_mode = pygame.display.set_mode

def _stingy_set_mode(size, *a, **kw):
    _real_set_mode((64, 64), *a, **kw)
    return pygame.Surface(_grant[0] or size)

class _WinStub:
    win_w = win_h = 0

_logged = []

class _Catch(logging.Handler):
    def emit(self, record):
        _logged.append(record.getMessage())

_mlog = logging.getLogger("orionlayer")
_catch = _Catch()
_mlog.addHandler(_catch)
try:
    pygame.display.set_mode = _stingy_set_mode
    _stub = _WinStub()
    _grant[0] = (3440, 1371)
    main_module.App._set_mode(_stub, 3840, 2160, 0)
    assert (_stub.win_w, _stub.win_h) == (3440, 1371), (
        f"_set_mode kept the REQUESTED size {_stub.win_w}x"
        f"{_stub.win_h} — the layout would be built for a window "
        f"that does not exist")
    assert any("3840x2160" in _m and "3440x1371" in _m
               for _m in _logged), (
        f"a window smaller than the one asked for was not "
        f"reported: {_logged}")
    # AND IT IS SILENT WHEN THE REQUEST IS GRANTED, or the line
    # is noise and stops being read.
    _logged.clear()
    _grant[0] = (1920, 1080)
    main_module.App._set_mode(_stub, 1920, 1080, 0)
    assert (_stub.win_w, _stub.win_h) == (1920, 1080)
    assert not _logged, (
        f"a granted request still logged: {_logged}")
finally:
    pygame.display.set_mode = _real_set_mode
    _mlog.removeHandler(_catch)
    _real_set_mode((1920, 1080))
# AND NOBODY READS THE REQUEST BACK OUT OF THE TABLE. The fault
# was `_apply_resolution` assigning `win_w`/`win_h` itself from
# its arguments; a future edit that reinstates that assignment
# puts the whole thing back with every check above still green.
_main_src = open(os.path.join(_root_main := os.path.dirname(
    SCREENS_DIR), "main.py"), encoding="utf-8").read()
_apply_body = _main_src.split("def _apply_resolution(")[1].split(
    "\n    def ")[0]
assert "self.win_w = w" not in _apply_body, (
    "_apply_resolution assigns win_w from its argument again — "
    "the window size has to come from the surface that was "
    "actually created")
ok("window size is the surface's, not the request's (a refused "
   "size is adopted and reported, a granted one is silent)")

# ── User settings (brief: OLED floor lift and colour presets) ──
import logging as _us_logging
import tempfile as _us_tmp
from core import usersettings as _us

# 1. ABSENT IS SILENT, CORRUPT IS ONE LOUD LINE, and neither raises.
class _UsCatch(_us_logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []
    def emit(self, record):
        self.lines.append((record.levelno, record.getMessage()))
_us_catch = _UsCatch()
_us_logging.getLogger("usersettings").addHandler(_us_catch)
try:
    with _us_tmp.TemporaryDirectory() as _us_dir:
        _us_path = os.path.join(_us_dir, "user_settings.json")
        _us_abs = _us.load(_us_path)
        assert _us_abs.state == "absent" and not _us_catch.lines
        assert _us_abs.get("floor_lift") == "off"
        assert _us_abs.get("player_colors") == "original"
        with open(_us_path, "w") as _fh:
            _fh.write("{ this is not json")
        _us_bad = _us.load(_us_path)
        assert _us_bad.state == "corrupt"
        assert _us_bad.get("player_colors") == "original"
        assert any(_lvl >= _us_logging.ERROR for _lvl, _m in
                   _us_catch.lines), _us_catch.lines
        _us_bad.set("floor_lift", "light")
        assert _us.save(_us_bad)
        assert os.path.exists(_us_path + ".corrupt"), \
            "the unreadable file was not kept"
finally:
    _us_logging.getLogger("usersettings").removeHandler(_us_catch)
ok("user settings: absent file silent with defaults, corrupt file one "
   "error line, defaults, no raise, kept aside on save")

# 2. UNKNOWN KEYS SURVIVE, AND SAVE IS IDEMPOTENT.
with _us_tmp.TemporaryDirectory() as _us_dir:
    _us_path = os.path.join(_us_dir, "user_settings.json")
    with open(_us_path, "w") as _fh:
        _fh.write('{"from_a_newer_build": [1, 2], "floor_lift": "off"}')
    _us_ok = _us.load(_us_path)
    _us_ok.set("player_colors", "original")
    assert _us.save(_us_ok) is True
    assert _us.save(_us_ok) is False, "a second save rewrote the file"
    _us_back = _us.load(_us_path)
    assert _us_back.data.get("from_a_newer_build") == [1, 2]
ok("user settings: a key this build does not know is kept through "
   "load and save; saving twice writes once")

# 3. THE FILE IS NEVER COMMITTED.
if os.path.isdir(os.path.join(os.path.dirname(SCREENS_DIR), ".git")):
    import subprocess as _us_sp
    _us_ign = _us_sp.run(
        ["git", "-C", os.path.dirname(SCREENS_DIR), "check-ignore",
         "--no-index", "user_settings.json"],
        capture_output=True, text=True)
    assert _us_ign.returncode == 0, "user_settings.json is not ignored"
    assert os.path.relpath(_us.PATH, os.path.dirname(SCREENS_DIR)) == \
        "user_settings.json"
    ok("user settings: user_settings.json is in .gitignore and is the "
       "path the loader uses")
else:
    report("user_settings.json ignore rule NOT checked — no .git")
    ok("user settings: ignore rule reported (no .git to ask)")

# 4. THE BANNER COLOURS LIVE IN THE PALETTE (decision 14): no colour
#    table left in core/banner.py, both skin tables complete.
_bn_src = open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                            "banner.py"), encoding="utf-8").read()
for _bn_name in ("red", "yellow", "green", "silver", "blue", "brown",
                 "purple", "orange"):
    assert not re.search(rf'"{_bn_name}":\s*\(\(', _bn_src), \
        f"core/banner.py carries a literal {_bn_name} tint again"
for _bn_sec in ("banner", "banner_hd"):
    _bn_tab = palette.banner_table(_bn_sec)
    assert len(_bn_tab) == 8, (_bn_sec, len(_bn_tab))
    assert all(len(_m) == 3 and len(_a) == 3
               for _m, _a in _bn_tab.values()), _bn_sec
ok("banner tints: no literal table in core/banner.py; colors.json "
   "[banner] and [banner_hd] each hold eight (multiply, add) pairs")
