# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 061_core_no_archives_or_backup_copies_anywhere.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 10 check(s) it holds:
#   - no archives or backup copies anywhere in the tree
#   - every brief is in doc/briefs/README.md, every link resolves, and 1.. has no gap ( files, named e
#   - fundament decision numbers unique ( decisions)
#   - exceptions list == tools/linecount.py ( over code lines)
#   - extractors write into the project, not the working directory
#   - the research names and the panel's wording come from the player's own files, and absent, stale a
#   - App boots standalone
#   - the fallback view draws the game's picture and forwards a click to it by F12's own path
#   - window pixel -> native pixel round-trips at all four resolutions, letterbox bars included
#   - editor box classes derived from the frame rule, one FREE box ( free, bound, locked; refusals nam


# Tree hygiene: no archives or backup copies anywhere in the
# tree. A stars.zip sat next to the stars/ folder it duplicated;
# a Backup.zip plus an unpacked Backup/ of the old nebula masters
# sat inside nebula/; and a 9-slice.zip sat inside the very frame
# folder it copied, with a 9slice.json ten days older than the
# one beside it — that one survived two passes of this check
# because it only walked screens/. It walks the whole tree now.
# A backup that lives inside the tree it backs up ships with
# every delivery and drifts from the folder the moment either
# changes; the copy that is stale is never the one you notice.
_junk = []
_root_dir = os.path.dirname(SCREENS_DIR)
for _dir, _subs, _files in os.walk(_root_dir):
    if "__pycache__" in _dir or ".git" in _dir:
        continue
    for _sub in _subs:
        if _sub.lower() in ("backup", "backups", "old"):
            _junk.append(os.path.join(os.path.relpath(_dir), _sub))
    for _f in _files:
        if _f.endswith((".zip", ".bak", ".orig")) or _f.endswith("~"):
            _junk.append(os.path.join(os.path.relpath(_dir), _f))
assert not _junk, _junk
ok("no archives or backup copies anywhere in the tree")

# ── EVERY BRIEF IS IN THE BRIEFS INDEX, BOTH WAYS ────────────
#
# doc/briefs/README.md opens with "Every brief, work order and
# package this project has been given". On 19 September 2026 (work
# order 135) its table stopped at 128 while the folder held six more
# files, and four work orders — 125, 132, 133 and 134 — had never
# been imported at all. The index is a hand-maintained list, and
# this project's rule for one of those is that it is legitimate only
# with a checker (decision 36's shape).
#
# Both directions, because they fail differently: a file nobody
# indexed is a brief that is in the tree and invisible, and a link
# to a file that is not there is the citation fault briefs 109 and
# 110 already paid for — a document naming a brief by a filename
# that never existed.
_bi_dir = os.path.join(os.path.dirname(SCREENS_DIR), "doc", "briefs")
_bi_files = sorted(_f for _f in os.listdir(_bi_dir) if _f != "README.md")
_bi_text = io.open(os.path.join(_bi_dir, "README.md"),
                   encoding="utf-8").read()
_bi_linked = set(re.findall(r"\]\(([^)]+)\)", _bi_text))
_bi_re_num = re.compile(r"^(\d+)-")
_bi_missing = [_f for _f in _bi_files if _f not in _bi_linked]
assert not _bi_missing, (
    f"doc/briefs/README.md does not index {_bi_missing} — it says "
    f"it holds every brief this project has been given")
_bi_dangling = sorted(_l for _l in _bi_linked
                      if not os.path.exists(os.path.join(_bi_dir, _l)))
assert not _bi_dangling, (
    f"doc/briefs/README.md links {_bi_dangling}, which are not there")
assert len(_bi_files) >= 148, (
    f"the briefs folder holds {len(_bi_files)} files; it has only "
    f"ever grown, so this is a deletion rather than an import")

# AND NO NUMBER IS MISSING. The index check above asserts that every
# FILE is indexed; it cannot see a brief that was never imported at
# all, which is exactly how 125, 132, 133 and 134 went missing for a
# fortnight and how 135 went missing one day after the check was
# written. A gap is the shape of that fault.
#
# THE EXCEPTIONS ARE NAMED HERE WITH THEIR REASON, never waved
# through. A number that was taken and then withdrawn is a real
# thing and belongs on this list; a number nobody imported is not.
# The list is empty today, and that is the honest state: every
# number from 1 to the highest is in the folder.
_BI_ALLOWED_GAPS = {
    # number: why it will never have a file
}
_bi_nums = {int(_m.group(1)) for _m in
            (_bi_re_num.match(_f) for _f in _bi_files) if _m}
_bi_high = max(_bi_nums)
_bi_gaps = sorted(set(range(1, _bi_high + 1))
                  - _bi_nums - set(_BI_ALLOWED_GAPS))
assert not _bi_gaps, (
    f"doc/briefs/ has no file for {_bi_gaps} although it goes up to "
    f"{_bi_high}. A brief that was never imported is invisible to "
    f"the index check above, which is how 125, 132, 133, 134 and "
    f"135 went missing. Import it, or put the number in "
    f"_BI_ALLOWED_GAPS with the reason it will never have a file")
ok(f"every brief is in doc/briefs/README.md, every link resolves, "
   f"and 1..{_bi_high} has no gap "
   f"({len(_bi_files)} files, {len(_BI_ALLOWED_GAPS)} named "
   f"exception(s))")

# Decision numbers in the fundament are identities — references
# elsewhere use the bare number. Two same-day sessions each took
# "the next free number" and both landed on 36, which no rule in
# the document can prevent when neither session can see the
# other. A test can.
_fund = os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                     "v3_fundament.md")
with open(_fund, encoding="utf-8") as _fh:
    _nums = re.findall(r"^\*\*(\d+)\.", _fh.read(), re.M)
_dupes = sorted({n for n in _nums if _nums.count(n) > 1})
assert not _dupes, f"duplicate decision numbers: {_dupes}"
ok(f"fundament decision numbers unique ({len(_nums)} decisions)")

# THE EXCEPTIONS LIST IS COMPUTED, NOT TYPED. Decision 6 counts
# CODE lines as of 4 September 2026, and the reason it had to
# change is the reason this check exists: the guideline was
# enforced on `wc -l` for as long as it existed, which counts
# this project's own docstrings, and 16 of the 24 non-exempt
# entries turned out never to have been exceptions at all. Three
# of those 16 had been ADDED by the three packages immediately
# before, each with a paragraph defending a length that was not
# there.
#
# So the list is held to `tools/linecount.py` rather than to a
# human's arithmetic, both ways: every file over the guideline is
# named, and every file named is over it. The one-directional
# version — "everything listed is over" — is the one that lets a
# new exception go unlisted, which is the whole failure the list
# exists to prevent.
import importlib.util as _lcu
_lc_spec = _lcu.spec_from_file_location(
    "_probe_linecount",
    os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                 "linecount.py"))
_lc = _lcu.module_from_spec(_lc_spec)
_lc_spec.loader.exec_module(_lc)
# The measure itself, on a file whose buckets are known by hand.
# Each line lands in exactly ONE bucket: a blank line inside a
# docstring is docstring, not blank. Summing overlapping buckets
# and taking code as the residual undercounts code by exactly the
# number of blank lines inside docstrings, which is how the
# pre-split screen.py was measured at 218 when it was 252.
_lc_probe = os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                         "linecount.py")
_lt, _lco, _ld, _lm, _lb = _lc.measure(_lc_probe)
assert _lco + _ld + _lm + _lb == _lt, (
    f"linecount's buckets overlap: {_lco}+{_ld}+{_lm}+{_lb} != "
    f"{_lt}. Each line must land in exactly one, or `code` as a "
    f"residual is wrong by the size of the overlap")
_status = os.path.join(os.path.dirname(SCREENS_DIR),
                       "v3_projektstatus.md")
import re as _lre
with open(_status, encoding="utf-8") as _fh:
    # Whitespace-collapsed, because the list is prose and wraps:
    # `tools/struct_probe.py`\n(**478** code, ...) is one entry
    # and a newline in the middle of it is a line break, not a
    # different claim.
    _st = _lre.sub(r"\s+", " ", _fh.read())
_over = _lc.over_guideline()
for _rel, (_t, _c, _d, _m, _b) in _over:
    # Listed under its path as the document spells it — the tail
    # after screens/ or core/, which is what a reader greps for.
    _short = _rel.split("/", 1)[1] if _rel.startswith(("screens/",
                                                      "core/")) else _rel
    assert (f"`{_rel}` (**{_c}** code" in _st
            or f"`{_short}` (**{_c}** code" in _st), (
        f"{_rel} is {_c} CODE lines, over the {_lc.GUIDELINE} "
        f"guideline, and v3_projektstatus.md's exceptions list "
        f"does not name it at that count. Decision 6: an "
        f"exception is allowed and must be LISTED")
# And nothing is listed that is not over — a list that keeps
# entries after they stop qualifying is the state this package
# found, sixteen deep.
_listed = set(_lre.findall(r"`([\w./]+\.py)` \(\*\*(\d+)\*\* code", _st))
_real = {_r.split("/", 1)[1] if _r.startswith(("screens/", "core/"))
         else _r: _c for _r, (_t, _c, _d, _m, _b) in _over}
_real.update({_r: _c for _r, (_t, _c, _d, _m, _b) in _over})
for _name, _claim in _listed:
    assert _name in _real and str(_real[_name]) == _claim, (
        f"the exceptions list names {_name} at {_claim} code "
        f"lines; linecount says "
        f"{_real.get(_name, 'it is not over the guideline')}")
assert len(_listed) == len(_over), (
    f"the list has {len(_listed)} entries and {len(_over)} files "
    f"are over the guideline")
ok(f"exceptions list == tools/linecount.py ({len(_over)} over "
   f"{_lc.GUIDELINE} code lines)")


# Every tool that WRITES into the tree must anchor its default
# output to the project, not to the working directory. Both
# extractors got this wrong in turn: help_extract.py wrote its
# JSON wherever the shell was, and nebula_extract.py did the same
# a week later — 61 sprite files landed in the repository root,
# got staged for the first commit, and the smoke test went on
# reporting the references as absent, because they were. Neither
# failure announced itself; both looked like success.
# Checked by importing and reading the value, not by matching the
# text: a first attempt grepped the assignment line and failed on
# help_extract.py, which anchors through a PROJECT_ROOT variable
# one line above. The question is what the path IS, not how it is
# spelled.
import importlib.util as _ilu
_root = os.path.dirname(SCREENS_DIR)
for _tool, _const in (("help_extract.py", "OUT_DIR"),
                      ("nebula_extract.py", "DEFAULT_OUT")):
    _spec = _ilu.spec_from_file_location(
        f"_probe_{_tool[:-3]}", os.path.join(_root, "tools", _tool))
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _out = getattr(_mod, _const, None)
    assert _out, f"{_tool}: no {_const} to check"
    assert os.path.isabs(_out), (
        f"{_tool}: {_const} is relative ({_out!r}) — it will write "
        f"wherever the shell happens to be")
    assert os.path.commonpath([_root, _out]) == _root, (
        f"{_tool}: {_const} points outside the project: {_out}")
ok("extractors write into the project, not the working directory")

# ── THE RESEARCH SCREEN'S WORDS COME FROM THE PLAYER'S FILES ───
#
# Work order 130 D, decision 38's pattern for the sixth time. Two
# loaders, two derived files, neither ever committed — so this must
# pass on a clean clone where both are absent, and every check below
# is about the RULE and not about a string in one player's copy.
import json as _nm_json
from core import billtext as _bt
from core import research as _nm_res
from core import researchlist as _nm_rl
from core import technames as _tn
from core.structs import unverified as _nm_unv

# 1. THE OFFSETS ARE SUMS OF THE GAME'S OWN COUNTS, and the three
#    modules that each hold one must not drift apart. TECHNAME's
#    block is walked by every one of them.
from core import buildnames as _bn
assert _tn.FIELD_FIRST_STRING == 0
assert _tn.APP_FIRST_STRING == \
    _tn.FIELD_FIRST_STRING + _tn.TECH_FIELD_COUNT
assert _bn.BUILDING_FIRST_STRING == \
    _tn.APP_FIRST_STRING + _tn.TECH_APP_COUNT, (
        "the building names' first string is no longer the string "
        "after the last application — one of the two walks is wrong",
        _bn.BUILDING_FIRST_STRING, _tn.APP_FIRST_STRING,
        _tn.TECH_APP_COUNT)
assert _tn.TECH_FIELD_COUNT == _nm_res.FIELD_COUNT
assert _tn.TECH_APP_COUNT == _nm_unv.TECH_APPLICATIONS_COUNT

# 2. AN ABSENT FILE IS A STATE, NOT AN ERROR (decision 38). Both
#    loaders are asked for a language nothing has ever extracted.
for _mod, _cls in ((_tn, _tn.TechNames), (_bt, _bt.BillText)):
    _absent = _cls("zz")
    assert _absent.state == "missing", (_mod.__name__, _absent.state)
assert _tn.TechNames("zz").field_name(21) is None
assert _tn.TechNames("zz").application_name(25) is None
assert _bt.BillText("zz").message(62) is None
assert _bt.BillText("zz").group_name(4) is None

# 3. AND A STALE ONE IS A THIRD STATE. A file an older extractor
#    wrote renders ALMOST right, which is worse than not loading —
#    the help texts' lesson, and the reason for the format version.
import tempfile as _nm_tmp
_nm_dir = _nm_tmp.TemporaryDirectory()
for _mod, _cls, _path_of, _body in (
        (_tn, _tn.TechNames, _tn.name_file,
         {"fields": {"21": "x"}, "applications": {"25": "y"}}),
        (_bt, _bt.BillText, _bt.message_file,
         {"messages": {str(i): "x" for i in _bt.RESEARCH_MESSAGES}})):
    _nm_path = os.path.join(_nm_dir.name, *_path_of("en").split("/"))
    os.makedirs(os.path.dirname(_nm_path), exist_ok=True)
    with open(_nm_path, "w", encoding="utf-8") as _h:
        _nm_json.dump(dict({"format": 0}, **_body), _h)
    assert _cls("en", root=_nm_dir.name).state == "stale", _mod.__name__
    with open(_nm_path, "w", encoding="utf-8") as _h:
        _nm_json.dump(dict({"format": _mod.FORMAT_VERSION}, **_body), _h)
    assert _cls("en", root=_nm_dir.name).state == "ok", _mod.__name__
    with open(_nm_path, "w", encoding="utf-8") as _h:
        _h.write("{not json")
    assert _cls("en", root=_nm_dir.name).state == "missing", _mod.__name__

# 4. A BILLTEXT FILE SHORT OF WHAT THE PANEL READS IS NOT "ok".
#    Half the panel in the game's words and half in OrionLayer's
#    reads as a broken screen, not as an absent file.
_nm_path = os.path.join(_nm_dir.name, *_bt.message_file("en").split("/"))
with open(_nm_path, "w", encoding="utf-8") as _h:
    _nm_json.dump({"format": _bt.FORMAT_VERSION,
               "messages": {str(i): "x"
                            for i in _bt.RESEARCH_MESSAGES[1:]}}, _h)
assert _bt.BillText("en", root=_nm_dir.name).state == "missing", \
    "a billtext file missing a message the panel reads passed as ok"
_nm_dir.cleanup()

# 5. FIELDS 75..82 ARE NOT NAMED FROM THIS BLOCK. The block DOES
#    carry a string at 75 — "Biology" in the English file — and
#    `Technology_Fields_Name_` (tech.cpp:1086-1099) does not use it:
#    it returns `_hyper_field_title` out of ESTRINGS. Answering with
#    the block's string would be a plausible wrong name.
#    **AGAINST THE STAND-IN, WHICH IS WHAT MAKES THIS AN
#    ASSERTION.** With the player's file absent every name is
#    None and this passed for the wrong reason; the stand-in
#    carries all 83 fields, so "the hyper ones are None" now tests
#    `field_name`'s own boundary and nothing else.
_nm_names = derived(_tn.TechNames)
assert _nm_names.field_name(1), (
    "the stand-in has no name for field 1, so the None checks "
    "below would pass vacuously")
for _nm_f in range(_tn.FIELD_HYPER_FIRST, _tn.TECH_FIELD_COUNT):
    assert _nm_names.field_name(_nm_f) is None, (
        f"field {_nm_f} was named from the TECHNAME block; the "
        f"original names it from ESTRINGS 0x284")
assert _nm_names.field_name(0) is None    # the unused row
assert _tn.FIELD_HYPER_FIRST == _nm_rl.FIELD_HYPER_FIRST

# 6. THE ROMAN NUMERAL IS THE ORIGINAL'S, INCLUDING WHERE IT STOPS
#    (`Technology_Applications_Name_`, tech.cpp:1117-1136, and
#    `MOX::_roman_literals`, mox.cpp:426: name, space, numeral at
#    hyper count + 1, and a plain number above twenty).
assert _tn.roman(0) == "I" and _tn.roman(2) == "III"
assert _tn.roman(_tn.ROMAN_MAX - 1) == "XX"
assert _tn.roman(_tn.ROMAN_MAX) == str(_tn.ROMAN_MAX + 1)
assert _tn.roman(None) == ""
# No count means NO SUFFIX, not numeral I: hyper_advanced_tech is
# unverified (core/structs/unverified.py), and a screen that printed
# "Biology I" off an unread byte would be inventing the level.
if _nm_names.state == "ok":
    _nm_bare = _nm_names.application_name(_nm_rl.APP_HYPER_FIRST)
    assert _nm_bare and not _nm_bare.endswith(" I"), _nm_bare
    assert _nm_names.application_name(_nm_rl.APP_HYPER_FIRST, 0) == \
        f"{_nm_bare} I"
    report(f"research names extracted: "
           f"{len(_nm_names.fields)} fields, "
           f"{len(_nm_names.applications)} applications")
else:
    report("research names NOT extracted on this disk — the loaders' "
           "absent-file behaviour is what was checked")
ok("the research names and the panel's wording come from the player's "
   "own files, and absent, stale and short are three stated states")

# ── Full App boot (standalone, no orion2re) ──
import main as main_module
# THE PLAYER'S OWN user_settings.json STAYS OUT OF THE RUN. `App()`
# loads it and hands its preset to `palette.init` — right for the
# app, and until 14 September 2026 it leaked into this suite: a
# player who had picked Okabe-Ito in the dialog left every later
# check running under that palette, and the Game Settings restart
# note (drawn only while saved != active) failed on a clean tree.
# The boot gets an empty settings object in a scratch directory, and
# the palette must come out of it as the original.
import tempfile as _boot_tmp
from core import playercolors as _boot_pc
_boot_dir = _boot_tmp.TemporaryDirectory()
_boot_load = main_module.usersettings.load
main_module.usersettings.load = lambda *_a, **_k: \
    main_module.usersettings.UserSettings(
        path=os.path.join(_boot_dir.name, "user_settings.json"))
try:
    app2 = main_module.App()
finally:
    main_module.usersettings.load = _boot_load
assert palette.active_preset() == _boot_pc.ORIGINAL, (
    f"App() booted under preset {palette.active_preset()!r} — the "
    f"player's user_settings.json reached the smoke test")
assert app2.dispatcher.active_name == "main_menu"
app2._update()
app2._render()
_before = _cur.last_size()
app2._cycle_resolution()
# A resolution change has to re-apply the cursor, or it keeps the
# size of a window that no longer exists — the exact bug this
# module replaced, one step removed.
assert _cur.last_size() == _cur.target_size(
    app2.win_h, app2.settings, _cur._source.get_size()), \
    (_cur.last_size(), app2.win_h, _before)
# AND NO BOX SURVIVES THE RESIZE THAT REPLACED IT. `Editor.selected`
# is the one place outside a screen that holds a Box across frames,
# and `dispatcher.on_resize` reaches `_reload_boxes`, which builds
# new objects — so a selection kept over a resize outlines a device
# rect from the previous window and, because `save_boxes` writes
# `scr.boxes`, throws a drag away without a word.
app2.editor.selected = app2.dispatcher.active.boxes[0]
app2._cycle_resolution()
assert app2.editor.selected is None, (
    "the editor kept a Box across a resize that replaced every "
    "Box the screen has")
ok("App boots standalone")

# ── THE FALLBACK VIEW IS A VIEW, NOT A HOLE (work order 130 A) ──
#
# Decision 22 ("Graceful fallback.") promises the game stays playable
# on a screen HD does not know. It was not kept. `use_original` was
# set by the dispatcher and read by NOTHING in the product: the
# window filled with a flat colour and swallowed every click, so the
# two turn-start research dialogs (52, 53) were a dead end inside
# OrionLayer's window — the player could neither see nor answer them.
# Work order 129's Stop 1 reported the click half of this; the
# picture half is worse and was found by measuring rather than
# reading (doc/research_screen_stop1.md §5.1 says "shows the picture",
# the tree showed (6, 8, 16)).
#
# Both halves now take F12's own path (decision 9), so this asserts
# against the DRAWN PIXELS and not only against the arithmetic —
# a shared function guarantees agreement, not correctness, and the
# stacked colony figures are what that lesson cost (decision 5).
class _FbState:
    stardate = 0
    stardate_str = ""
    map_scale = 10

    def __init__(self, screen_id):
        self.current_screen = screen_id
        # Left half of the native picture one colour, right half
        # another, so a click mapping that is off by the bar's
        # width lands in the wrong half and is caught.
        self.framebuffer = bytes(
            (3 if (i % 640) < 320 else 7) for i in range(640 * 480))
        self.palette = [(0, 0, 0)] * 256
        self.palette[3] = (0, 0, 255)
        self.palette[7] = (255, 0, 0)
        self.fields = []

class _FbClient:
    game_ended = False

    def __init__(self, state):
        self.state = state
        self.log = []

    def poll(self):
        pass

    def activate_field(self, fid):
        self.log.append(("ACTIVATE_FIELD", fid))

    def inject_click(self, x, y):
        self.log.append(("INJECT_CLICK", x, y))

# 52, the science-room dialog: no HD screen claims it, and none is
# planned (work order 130's NOT IN THIS ORDER). 53 was the example
# here until the research screen took it — which is exactly the
# drift this comment is for.
_fb_state = _FbState(52)
_fb_client = _FbClient(_fb_state)
app2._apply_resolution(1920, 1080)
app2.client, app2.connected = _fb_client, True
app2.render_mode = "hd"
app2._update()
assert app2.dispatcher.use_original and app2.dispatcher.active is None, \
    (app2.dispatcher.use_original, app2.dispatcher.active_name)
assert app2._showing_original(), (
    "the dispatcher fell back and the window still does not show the "
    "game's picture — decision 22 is a promise, not a comment")
app2._render()
# 640x480 into 1920x1080 is pillarboxed: scale 2.25, a 1440-wide
# picture at x 240. The numbers come from the view's own placement,
# never from this check — a check that recomputes the geometry is
# the second copy decision 5 is about.
_fb_x, _fb_y, _fb_w, _fb_h, _fb_s = app2.original_view.placement(
    1920, 1080)
assert (_fb_x, _fb_y, _fb_w, _fb_h) == (240, 0, 1440, 1080), \
    (_fb_x, _fb_y, _fb_w, _fb_h, _fb_s)
_fb_mid = _fb_x + _fb_w // 2      # the native x=320 seam
for _fb_px, _fb_want, _fb_where in (
        (_fb_x + _fb_w // 4, (0, 0, 255), "the picture's left half"),
        (_fb_x + 3 * _fb_w // 4, (255, 0, 0), "its right half"),
        (_fb_x // 2, (0, 0, 0), "the letterbox bar")):
    _fb_got = app2.surface.get_at((_fb_px, 540))[:3]
    assert _fb_got == _fb_want, (
        f"{_fb_where} drew {_fb_got}, wanted {_fb_want} at x={_fb_px} "
        f"— the fallback is not showing the framebuffer")
# AND THE CLICK LANDS IN THE HALF THE PLAYER SEES. Same two points,
# now through the click path: the drawn seam and the mapped seam are
# the same seam, which is what shared geometry has to earn.
for _fb_px, _fb_half in ((_fb_x + _fb_w // 4, 0),
                         (_fb_x + 3 * _fb_w // 4, 1)):
    _fb_nat = app2.original_view.screen_to_640(_fb_px, 540, 1920, 1080)
    assert _fb_nat is not None and (_fb_nat[0] >= 320) == bool(_fb_half), \
        (_fb_px, _fb_nat, _fb_half)
# A click reaches the game — by ACTIVATE_FIELD where a field covers
# the point, by INJECT_CLICK where none does (original_view's own
# rule, unchanged), and by NEITHER from inside the bar.
_fb_client.log.clear()
app2._handle_click(_fb_mid, 540)
assert _fb_client.log == [("INJECT_CLICK", 320, 240)], _fb_client.log
_fb_client.log.clear()
app2._handle_click(_fb_x // 2, 540)
assert _fb_client.log == [], (
    "a click in the letterbox bar was forwarded — the game has no "
    "pixel there", _fb_client.log)
# A field under the point wins, and the fallback resolves it exactly
# as F12 does: same call, same arguments, for the same pixel.
from core.game_state import FieldInfo as _FbField
_fb_f = _FbField()
(_fb_f.index, _fb_f.x, _fb_f.y, _fb_f.x_end, _fb_f.y_end,
 _fb_f.field_type, _fb_f.hotkey) = (4, 300, 200, 400, 300, 7, 0)
# FIELD 0 FIRST, AND IT COVERS THE POINT. The engine cannot send a
# list without slot 0 (FIELD_ZERO_ROW), and decision 59 says that
# slot "carries whatever geometry the list held before" — a
# full-screen rect is exactly what a message box leaves there. So
# the fixture gives it one: a resolver that walks the list and
# takes the first hit answers 0, and the click goes nowhere.
# `OriginalView.find_field_at` skips `index < 1` and is the one
# place in the tree that already knew (original_view.py:127).
_fb_zero = _FbField()
(_fb_zero.index, _fb_zero.x, _fb_zero.y, _fb_zero.x_end,
 _fb_zero.y_end, _fb_zero.field_type, _fb_zero.hotkey) = \
    (0, 0, 0, 639, 479, 7, 0)
_fb_state.fields = [_fb_zero, _fb_f]
_fb_client.log.clear()
app2._handle_click(_fb_mid, 540)
_fb_fallback_call = list(_fb_client.log)
assert _fb_fallback_call == [("ACTIVATE_FIELD", 4)], _fb_fallback_call
_fb_client.log.clear()
app2.render_mode = "original"     # F12: the other way into one view
app2._handle_click(_fb_mid, 540)
assert _fb_client.log == _fb_fallback_call, (
    "F12 and the fallback forward the same click differently — "
    "there is a second click path (decision 9)",
    _fb_client.log, _fb_fallback_call)
app2.render_mode = "hd"
# And the editor still eats every click before either of them.
app2.editor.active = True
_fb_client.log.clear()
app2._handle_click(_fb_mid, 540)
assert _fb_client.log == [], _fb_client.log
app2.editor.active = False
ok("the fallback view draws the game's picture and forwards a click "
   "to it by F12's own path")

# ── WINDOW PIXEL -> NATIVE PIXEL, AT ALL FOUR SIZES ────────────
#
# Every forwarded click is converted here, and since work order 130 A
# that is every screen HD does not claim — the research dialogs among
# them. All four presets are WIDER than 4:3, so all four pillarbox,
# and the bar is where an off-by-a-bar error hides: the click still
# lands on a plausible field, just the wrong one.
_mp_view = app2.original_view
for _mp_w, _mp_h, _mp_name in app2._resolutions:
    _mp_x, _mp_y, _mp_dw, _mp_dh, _mp_s = _mp_view.placement(_mp_w, _mp_h)
    # The picture is the largest 4:3 area that fits, and it is centred.
    assert _mp_s == min(_mp_w / 640, _mp_h / 480), (_mp_name, _mp_s)
    assert _mp_dw <= _mp_w and _mp_dh <= _mp_h, (_mp_name,)
    assert abs((_mp_w - _mp_dw) - 2 * _mp_x) <= 1, (
        f"{_mp_name}: the bars are not equal ({_mp_x} left of a "
        f"{_mp_w - _mp_dw} px remainder)")
    assert abs((_mp_h - _mp_dh) - 2 * _mp_y) <= 1, (_mp_name,)
    assert _mp_x > 0 or _mp_y > 0, (
        f"{_mp_name}: no bar at all — then this check proves nothing "
        f"about letterboxing and the case has stopped being covered")
    # Every native pixel's own centre comes back as that pixel.
    for _mp_nx in (0, 1, 319, 320, 638, 639):
        for _mp_ny in (0, 1, 239, 240, 478, 479):
            _mp_sx = _mp_x + int((_mp_nx + 0.5) * _mp_s)
            _mp_sy = _mp_y + int((_mp_ny + 0.5) * _mp_s)
            _mp_got = _mp_view.screen_to_640(_mp_sx, _mp_sy,
                                             _mp_w, _mp_h)
            assert _mp_got == (_mp_nx, _mp_ny), (
                f"{_mp_name}: window ({_mp_sx}, {_mp_sy}) read back as "
                f"{_mp_got}, not ({_mp_nx}, {_mp_ny})")
    # The picture's own corners are the picture's own corners.
    assert _mp_view.screen_to_640(_mp_x, _mp_y, _mp_w, _mp_h) == (0, 0)
    assert _mp_view.screen_to_640(_mp_x + _mp_dw - 1, _mp_y + _mp_dh - 1,
                                  _mp_w, _mp_h) == (639, 479)
    # And one pixel outside any edge is the bar, not pixel 0 or 639.
    for _mp_out in ((_mp_x - 1, _mp_h // 2), (_mp_x + _mp_dw, _mp_h // 2),
                    (_mp_w // 2, _mp_y - 1), (_mp_w // 2, _mp_y + _mp_dh)):
        if _mp_out[0] < 0 or _mp_out[1] < 0:
            continue          # that edge has no bar at this size
        assert _mp_view.screen_to_640(*_mp_out, _mp_w, _mp_h) is None, (
            f"{_mp_name}: {_mp_out} is outside the picture and mapped "
            f"to a native pixel anyway")
ok("window pixel -> native pixel round-trips at all four resolutions, "
   "letterbox bars included")

# ── THE EDITOR'S BOX CLASSES, DERIVED AND NOT DECLARED ──────
#
# A box is LOCKED because the screen's `frame_holes` rule produces
# its name — decision 3, whose failure is "moving one by hand
# slides content out from under its hole". `Box.locked` exists in
# the data model and has never been read; filling it in would be a
# hand-copy of what `frame_holes` already knows.
from core.editor import boxclass as _bcl
import frame_holes as _fh_mod

# 1. RULE_NAMES IS THE RULE'S OWN VOCABULARY. Run the real namer
#    over the real plate and require that every name it produces
#    is in the list — otherwise the list is a second copy that
#    goes stale the first time a plate gains a hole.
# THE FRAME THE SCREEN DRAWS, not a plate by path — corrected
# 12 September 2026. This read `assets/frames/frame_1920x1080.png`
# whether or not anything blitted it, and called the namer with no
# image size, which since the namer began matching against
# `layout_reference.json` means "no reference": it named nothing
# and the row check then failed on an empty answer.
_plate = res.screen_file("colony_summary", "assets", "frame.png")
if _plate and os.path.exists(_plate):
    _iw, _ih, _holes = _fh_mod.find_holes(_plate)
    _named = set(_fh_mod.name_holes(_holes, "colony_summary",
                                    (_iw, _ih)))
    _listed = _fh_mod.RULE_NAMES["colony_summary"]
    assert _named <= _listed, (
        f"the colony rule produced names RULE_NAMES does not "
        f"list: {sorted(_named - _listed)} — the editor would "
        f"offer handles on a cutout")
    # `title` is never produced, and a window declared to have no
    # hole cannot be either — the colony header is a strip of the
    # list's hole, and the editor still LOCKS it because it is a
    # derived rect whatever it is derived from.
    # IN THE BOX'S SPELLING, like `RULE_NAMES` itself — the
    # reference says `return_button` and the rule says `return`.
    _unproducible = {"title"} | {
        _cpl.BOX_NAME.get(_n, _n)
        for _n in _lr.get("_windows_without_a_hole", ())}
    assert _listed - _named <= _unproducible, (
        f"RULE_NAMES lists names the rule cannot produce: "
        f"{sorted(_listed - _named - _unproducible)}")
    print(f"      frame rule produced {len(_named)} names, all "
          f"listed; {sorted(_listed - _named)} have no hole")
else:
    print("      no frame on this path; RULE_NAMES checked against "
          "its own constants only")
# AND IT IS BUILT FROM THE CONSTANTS THE RULE USES, not typed out.
assert set(_fh_mod.BAND_KEYS) <= _fh_mod.RULE_NAMES["colony_summary"]
assert {f"nav_{k}" for k in _fh_mod.NAV_KEYS} <= \
    _fh_mod.RULE_NAMES["galaxy_map"]

# 2. THE COLUMN NAMES AGREE WITH THE SCREEN'S OWN. `core` may not
#    import a screen package, so the six live in two places and
#    this is the checker that makes the copy legitimate.
from screens.colony_summary import colonyheader as _bch
assert all(n.startswith(_bcl.COLUMN_PREFIX)
           for n in _bch.COLUMN_BOXES), (
    f"colonyheader.COLUMN_BOXES no longer all start with "
    f"{_bcl.COLUMN_PREFIX!r}, which is how the editor recognises "
    f"a BOUND box")

# 3. THE TABLE, RE-RUN AGAINST THE CODE. Counted here rather than
#    carried as numbers, so a new box lands in a class by running
#    rather than by somebody remembering to update a total.
_cls_rows = []
for _scr_name in sorted(os.listdir(SCREENS_DIR)):
    _bp = os.path.join(SCREENS_DIR, _scr_name, "boxes.json")
    if not os.path.exists(_bp):
        continue
    _raw = _sjson.load(open(_bp, encoding="utf-8"))
    _lst = list(_raw.values())[0] if isinstance(_raw, dict) else _raw
    _counts = collections.Counter(
        _bcl.classify(_scr_name, _b["name"]) for _b in _lst)
    _cls_rows.append((_scr_name, len(_lst), _counts[_bcl.FREE],
                      _counts[_bcl.BOUND], _counts[_bcl.LOCKED]))
for _n, _t, _f, _b, _l in _cls_rows:
    assert _f + _b + _l == _t, (_n, _t, _f, _b, _l)
    print(f"      {_n:18s} {_t:3d} boxes | free {_f:2d} "
          f"bound {_b} locked {_l:2d}")
# DERIVED, NOT TYPED: every cutout the rule can name is LOCKED
# and the six columns are BOUND, so the expected counts come out
# of the same two constants the classifier reads. It was
# `0 / 6 / 8` as literals and went stale the moment the sort bar
# became seven slots — which is the fault this file writes down
# about every hand-copied number.
# AND THE FREE ONES ARE THE DECLARED ONES — 12 September 2026.
# This expected ZERO free boxes as a literal, which was true while
# every box was a cutout; then RETURN spent a day with no hole,
# drawn over the metal at a rect Data placed in the editor, and
# the zero was wrong. Data's frame of that evening gives it the
# eighth slot and the count is a zero again — so what is asserted
# is the DECLARATION either way, and `_editor_free` is empty
# today rather than absent, which is the difference between "no
# box may be dragged" and "nobody has said".
_cs_row = next(r for r in _cls_rows if r[0] == "colony_summary")
_cs_free = _fh_mod.editor_free("colony_summary")
_cs_locked = len(_fh_mod.cutout_names("colony_summary"))
assert _cs_row[2] == len(_cs_free) \
    and _cs_row[3] == len(_bch.COLUMN_BOXES) \
    and _cs_row[4] == _cs_locked, (
    f"colony_summary classifies as {_cs_row[2]} free / "
    f"{_cs_row[3]} bound / {_cs_row[4]} locked, expected "
    f"{len(_cs_free)} / {len(_bch.COLUMN_BOXES)} / {_cs_locked}")
assert set(_cs_free) <= (_fh_mod.RULE_NAMES["colony_summary"]
                         | set(_cpl.part_rects(app.res.load_json(
                             "screens/colony_summary/"
                             "layout_reference.json", {}) or {}))), (
    f"the editor-free names {sorted(_cs_free)} are not boxes the "
    f"colony rule knows about")
assert "_editor_free" in (app.res.load_json(
    "screens/colony_summary/layout_reference.json", {}) or {}), (
    "layout_reference.json no longer declares `_editor_free` at "
    "all — an empty list says NO box may be dragged and a missing "
    "key says nobody has said, and the editor cannot tell them "
    "apart on its own")
report(f"editor classes, colony_summary: {_cs_row[2]} free / "
       f"{_cs_row[3]} bound / {_cs_row[4]} locked"
       + (f" (free: {sorted(_cs_free)})" if _cs_free else ""))

# 4. HANDLES PER CLASS, and a refusal that says why.
assert len(_bcl.HANDLES[_bcl.FREE]) == 8
assert _bcl.HANDLES[_bcl.BOUND] == {"l", "r"}
assert _bcl.HANDLES[_bcl.LOCKED] == set()
for _h in ("t", "b", "tl", "br"):
    _why = _bcl.refusal("colony_summary", "col_name", _h)
    assert _why and "list_area" in _why, _why
assert _bcl.refusal("colony_summary", "col_name", "l") is None
for _h in _bcl.HANDLES[_bcl.FREE]:
    _why = _bcl.refusal("colony_summary", "list_area", _h)
    assert _why and "frame_holes" in _why, _why
    assert _bcl.refusal("galaxy_map", "sb_food_text", _h) is None
# AND THE OVERLAY DRAWS ONLY WHAT THE CLASS OFFERS — one table,
# so the picture and the hit test cannot disagree (decision 5).
from core.editor import overlay as _bov
assert set(_bov.HANDLE_AT) == _bcl.HANDLES[_bcl.FREE], (
    "the overlay's handle table and the FREE handle set differ")

# 5. THE TRANSCRIBED ASPECT SURVIVES ANY EDGE. The galaxy inset is
#    locked today; the rule is in so the first person to unlock it
#    cannot break a ratio held to a thousandth.
_asp = _bcl.ASPECT["colony_summary"]["galaxy_inset"]
assert abs(_asp - 1.2651) < 0.001, _asp
for _h in ("l", "r", "t", "b", "tl", "br"):
    _x, _y, _w, _hh = _bcl.hold_aspect(
        "colony_summary", "galaxy_inset", (0, 0, 300, 40), _h)
    assert abs(_w / _hh - _asp) < 0.01, (_h, _w, _hh)
# 6. ONE FREE BOX RESIZES, AND A SAVE WRITES ONLY ITS RECT.
#    The stop this part was cut at: the classification is in and
#    one box actually moves through it. Asserted through a real
#    save and reload rather than on the in-memory box, because
#    the failure worth catching is a writer adding a key —
#    `Box.to_dict` serializes a fixed set and a derived value
#    landing in `boxes.json` is what decision 14's F5 path must
#    never do.
# A SAVE WITH NO EDIT CHANGES NOTHING, on every screen — the
# premise the resize test rests on, and it was FALSE until
# 9 September 2026. Five galaxy_map boxes carried `"style": {}`
# and `Box.to_dict` writes `style` only when it is truthy, so
# every F5 save rewrote them: a one-box edit arrived as a six-box
# diff and the existing check never saw it, because that one
# compares rects and the difference was a dropped empty dict. The
# empty containers are gone from the data; this is what keeps
# them gone.
for _idem in sorted(glob.glob(os.path.join(SCREENS_DIR, "*",
                                           "boxes.json"))):
    _id_raw = _sjson.load(open(_idem, encoding="utf-8"))
    if not isinstance(_id_raw, dict):
        continue
    _id_key = next(iter(_id_raw))
    _id_w, _id_h = (int(v) for v in _id_key.split("x"))
    with _tf.TemporaryDirectory() as _id_dir:
        __import__("shutil").copy(
            _idem, os.path.join(_id_dir, "boxes.json"))
        _save_boxes(_id_dir, load_boxes(_idem, _id_w, _id_h),
                    _id_w, _id_h)
        _id_after = _sjson.load(open(
            os.path.join(_id_dir, "boxes.json"), encoding="utf-8"))
    _id_b = {b["name"]: b for b in _id_raw[_id_key]}
    _id_a = {b["name"]: b for b in _id_after[_id_key]}
    _id_moved = [n for n in _id_b if _id_b[n] != _id_a.get(n)]
    assert not _id_moved, (
        f"{os.path.relpath(_idem, SCREENS_DIR)}: a save with no "
        f"edit rewrites {_id_moved} — an F5 save must be a no-op "
        f"until something is dragged, or every edit arrives as a "
        f"wider diff than it is")

_rz_screen = "galaxy_map"
_rz_src = os.path.join(SCREENS_DIR, _rz_screen, "boxes.json")
_rz_before = _sjson.load(open(_rz_src, encoding="utf-8"))
_rz_key = next(iter(_rz_before))
_rz_name = next(_b["name"] for _b in _rz_before[_rz_key]
                if _bcl.classify(_rz_screen, _b["name"]) == _bcl.FREE)
with _tf.TemporaryDirectory() as _rz_dir:
    __import__("shutil").copy(_rz_src,
                              os.path.join(_rz_dir, "boxes.json"))
    _rz_w, _rz_h = (int(v) for v in _rz_key.split("x"))
    _rz_boxes = load_boxes(_rz_src, _rz_w, _rz_h)
    _rz_box = next(b for b in _rz_boxes if b.name == _rz_name)
    _rz_orig = tuple(_rz_box.ref_rect)
    # Through the editor's own arithmetic, both axes, and through
    # the aspect hook so a box with no ratio is unchanged by it.
    _rz_new = Editor._calc_resize(None, _rz_orig, 17, 11, "br")
    _rz_new = _bcl.hold_aspect(_rz_screen, _rz_name, _rz_new, "br")
    assert _rz_new[2] == _rz_orig[2] + 17 and \
        _rz_new[3] == _rz_orig[3] + 11, (
        f"a FREE box did not take the drag: {_rz_orig} -> {_rz_new}")
    _rz_box.ref_rect = _rz_new
    _save_boxes(_rz_dir, _rz_boxes, _rz_w, _rz_h)
    _rz_after = _sjson.load(
        open(os.path.join(_rz_dir, "boxes.json"), encoding="utf-8"))
assert set(_rz_after) == set(_rz_before), "a save changed the keys"
_rz_b = {b["name"]: b for b in _rz_before[_rz_key]}
_rz_a = {b["name"]: b for b in _rz_after[_rz_key]}
assert set(_rz_a) == set(_rz_b), "a save changed which boxes exist"
_rz_moved = [n for n in _rz_b if _rz_b[n] != _rz_a[n]]
assert _rz_moved == [_rz_name], (
    f"the save touched {_rz_moved}, wanted only [{_rz_name!r}]")
_rz_diff = [k for k in set(_rz_a[_rz_name]) | set(_rz_b[_rz_name])
            if _rz_a[_rz_name].get(k) != _rz_b[_rz_name].get(k)]
assert _rz_diff == ["rect"], (
    f"the save wrote {_rz_diff} for {_rz_name}; a resize changes "
    f"ref_rect and nothing else")
assert _rz_a[_rz_name]["rect"] == list(_rz_new)

ok(f"editor box classes derived from the frame rule, one FREE box "
   f"({sum(r[2] for r in _cls_rows)} free, "
   f"{sum(r[3] for r in _cls_rows)} bound, "
   f"{sum(r[4] for r in _cls_rows)} locked; refusals name what to "
   f"change, the inset keeps 1.2651 on any edge)")
