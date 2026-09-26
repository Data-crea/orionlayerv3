# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006e_core_the_engine_start_hang_is_recognised.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 174 A: a session-launched orion2re hangs in its first logo
# frames when its window is not being drawn (open fix 31). The start
# tool recognises the hang, refuses what it must, and never connects to
# an engine it did not start. Offline: no engine, no desktop — the
# decisions are held, not the processes.
#
# The 2 check(s) it holds:
#   - engine start: the hang's signature, the refusals, the environment, no connect
#   - live guard: every file a run can write backed up, every change named and restored (175)


import engine_start as _es

# The signature: log at the line, every sample the two waits.
_es_hung = {"orion2re": _es.MAIN_WAIT, "MOX2::main2_": _es.GAME_WAIT}
assert _es.is_hang(_es.HANG_LINE, [_es_hung] * 6)
# The intro cinematic holds the log at the same line — and fails the samples.
assert not _es.is_hang(_es.HANG_LINE, [_es_hung] * 5 + [
    {"orion2re": "hrtimer_nanosleep", "MOX2::main2_": "hrtimer_nanosleep"}])
# A running engine waits in the GPU sync most of the time too — but its
# log has moved on.
assert not _es.is_hang("ext: server started on port 17362", [_es_hung] * 6)
# Too few samples are not a verdict.
assert not _es.is_hang(_es.HANG_LINE, [_es_hung] * 2)

# The replies it reads off D-Bus, and what it makes of an unreadable one.
assert _es.parse_bool("(true,)\n") is True
assert _es.parse_bool("(false,)") is False
assert _es.parse_bool("") is None and _es.parse_bool(None) is None
assert _es.parse_uint("(uint64 1403,)") == 1403
assert _es.parse_uint("garbage") is None

# The refusals: somebody's engine, a taken port, a blanked screen —
# each named; an unknown screen state is not read as blanked.
_es_ok, _es_why = _es.verdict([], True, {"blanked": False})
assert _es_ok and not _es_why
_es_ok, _es_why = _es.verdict([(287200, 35660, "Fr Sep 25 19:00:09 2026")],
                              False, {"blanked": True})
assert not _es_ok and len(_es_why) == 3, _es_why
assert "287200" in _es_why[0] and "not ours" in _es_why[0]
assert "blanked or locked" in _es_why[2]
assert _es.verdict([], True, {"blanked": None})[0]

# The environment: CLAUDE.md's three variables and open fix 31's switch.
_es_env = _es.display_env({})
assert _es_env["DISPLAY"] == ":0" and _es_env["SDL_VIDEODRIVER"] == "x11"
assert _es_env["ORION2RE_NO_VSYNC"] == "1"
_es_cmd = _es.command(inhibit=True)
assert _es_cmd[-1] == _es.ENGINE
assert _es.command(inhibit=False) == [_es.ENGINE]

# NEVER A CLIENT, NEVER SOMEBODY ELSE'S PROCESS: the port is tested by
# binding, nothing connects; nothing kills by name.
_es_src = open(_es.__file__, encoding="utf-8").read()
assert ".connect(" not in _es_src and "create_connection" not in _es_src
assert "pkill" not in _es_src and "killall" not in _es_src
assert "open fix 31" in _es_src
_es_fixes = open(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                              "orion2re_open_fixes.md"), encoding="utf-8").read()
assert "## 31. A session-launched engine hangs" in _es_fixes
# APPLIED by work order 175: the list, the patch and version_check say so.
assert "**Applied** 26 September 2026 by work order 175" in next(
    _l for _l in _es_fixes.splitlines() if _l.startswith("| 31 |"))
assert "STATUS: APPLIED 26 September 2026" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "doc", "ext_present_no_vsync.patch"),
    encoding="utf-8").read()
assert '"Present_VSync_Interval_"' in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "version_check.py"),
    encoding="utf-8").read()
ok("engine start: the start hang's signature (not the intro, not a "
   "running engine), three refusals named, CLAUDE.md's environment with "
   "ORION2RE_NO_VSYNC (open fix 31, applied), the port bound never "
   "connected, nothing killed by name")


# 2 — THE LIVE GUARD (work order 175): 174 hashed SAVE1-11 and the game
#     still rewrote MOX.SET. Every file a run can write is backed up
#     before the engine starts, and every change is named afterwards —
#     changed, appeared, vanished — and put back; the scratch slot a run
#     names may change; the game's case-blind file names are honoured.
import liveguard as _lg
import shutil
import tempfile as _lg_tmp
_lg_game = _lg_tmp.mkdtemp()
_lg_root = _lg_tmp.mkdtemp()
_lg_dest = _lg_tmp.mkdtemp()
try:
    for _n in ("SAVE4.GAM", "SAVE10.GAM", "mox.set", "HOF.M2"):
        with open(os.path.join(_lg_game, _n), "wb") as _f:
            _f.write(_n.encode() * 10)
    with open(os.path.join(_lg_root, "user_settings.json"), "w") as _f:
        _f.write('{"hud_hue": 161}\n')
    _lg_man = _lg.snapshot(_lg_dest, _lg_game, _lg_root)
    assert _lg_man["files"]["game/MOX.SET"]["path"].endswith("mox.set"), \
        "the game opens MOX.SET case-blind; the guard must find mox.set"
    assert _lg_man["files"]["game/TEMP.TMP"] is None
    assert set(_lg.GAME_FILES) >= {"MOX.SET", "HOF.M2", "lastrace.rac",
                                   "TEMP.TMP", "SAVE10.GAM", "SAVE11.GAM"}
    _lg_ch, _ = _lg.verify(_lg_dest, log=lambda *_a: None)
    assert _lg_ch == [], _lg_ch
    # A run: TURN rewrites SAVE10, leaving the game rewrites MOX.SET, a
    # swap file appears, the Hall of Fame goes, the settings rows write,
    # and the run saved to its scratch slot SAVE4.
    for _n, _b in (("SAVE10.GAM", b"turn"), ("mox.set", b"scratch settings"),
                   ("TEMP.TMP", b"swap"), ("SAVE4.GAM", b"scratch save")):
        with open(os.path.join(_lg_game, _n), "wb") as _f:
            _f.write(_b)
    os.remove(os.path.join(_lg_game, "HOF.M2"))
    with open(os.path.join(_lg_root, "user_settings.json"), "w") as _f:
        _f.write('{"hud_hue": 280}\n')
    _lg_ch, _ = _lg.verify(_lg_dest, allow=("SAVE4.GAM",), log=lambda *_a: None)
    assert dict(_lg_ch) == {"game/SAVE10.GAM": "changed",
                            "game/MOX.SET": "changed",
                            "game/TEMP.TMP": "appeared",
                            "game/HOF.M2": "vanished",
                            "layer/user_settings.json": "changed"}, _lg_ch
    _lg_ch, _lg_back = _lg.verify(_lg_dest, restore=True, allow=("SAVE4.GAM",),
                                  log=lambda *_a: None)
    assert len(_lg_back) == 5, _lg_back
    assert _lg.verify(_lg_dest, allow=("SAVE4.GAM",), log=lambda *_a: None)[0] == []
    assert open(os.path.join(_lg_game, "SAVE4.GAM"), "rb").read() == b"scratch save", \
        "the allowed scratch slot was restored"
    # engine_start takes the backup before the engine exists.
    _lg_src = open(_es.__file__, encoding="utf-8").read()
    assert _lg_src.index("liveguard.snapshot(guard)") < _lg_src.index(
        "proc = subprocess.Popen(")
finally:
    for _d in (_lg_game, _lg_root, _lg_dest):
        shutil.rmtree(_d, ignore_errors=True)
ok("live guard: every file a run can write (SAVE1-11, MOX.SET, HOF.M2, "
   "lastrace.rac, TEMP.TMP, user_settings.json, the tree) backed up before "
   "the engine starts; changed, appeared and vanished named and put back; "
   "the scratch slot allowed")
