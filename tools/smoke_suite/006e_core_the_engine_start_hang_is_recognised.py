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
# The 4 check(s) it holds:
#   - engine start: the hang's signature, the refusals, the environment, no connect
#   - live guard: every file a run can write backed up, every change named and restored (175)
#   - a leftover engine or client is closed only after the backup: SIGTERM,
#     SIGKILL only if needed, each recorded; the rule stands in CLAUDE.md,
#     fundament part 09 and the tool (work order 176)
#   - OrionLayer itself starts no engine and stops none (176, measured live)


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
assert "287200" in _es_why[0] and "never connected to" in _es_why[0] \
    and "--close-foreign" in _es_why[0], _es_why[0]
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

# ── 3. WORK ORDER 176: A LEFTOVER IS CLOSED, NEVER CONNECTED TO ────────
# A process THIS CHECK starts stands in for the leftover: one that ends on
# SIGTERM, one that ignores it. The backup comes first, both are recorded.
import subprocess as _cf_sp
import tempfile as _cf_tmp
_cf_game = _cf_tmp.mkdtemp()
_cf_root = _cf_tmp.mkdtemp()
_cf_dest = os.path.join(_cf_tmp.mkdtemp(), "guard")
_cf_procs = []
try:
    with open(os.path.join(_cf_game, "SAVE4.GAM"), "wb") as _f:
        _f.write(b"scratch")
    _cf_procs.append(_cf_sp.Popen([sys.executable, "-c",
                                   "import time; time.sleep(60)"]))
    _cf_procs.append(_cf_sp.Popen([sys.executable, "-c",
                                   "import signal, time; signal.signal("
                                   "signal.SIGTERM, signal.SIG_IGN); "
                                   "time.sleep(60)"]))
    import time as _cf_time
    _cf_time.sleep(0.5)
    _cf_rec = _es.close_foreign(
        [(p.pid, "stand-in", "now") for p in _cf_procs], _cf_dest,
        out=lambda *_a: None, wait=1.0, game_dir=_cf_game, root=_cf_root)
    for p in _cf_procs:
        p.wait(timeout=5)
    assert os.path.exists(os.path.join(_cf_dest, "manifest.json")), \
        "no backup before closing"
    assert [r[3] for r in _cf_rec] == ["ended on SIGTERM",
                                       "SIGKILL after SIGTERM"], _cf_rec
    assert _es.close_foreign([], _cf_dest + "_none", out=lambda *_a: None) == []
finally:
    for p in _cf_procs:
        if p.poll() is None:
            p.kill()
    for _d in (_cf_game, _cf_root, os.path.dirname(_cf_dest)):
        shutil.rmtree(_d, ignore_errors=True)
_cf_src = open(_es.__file__, encoding="utf-8").read()
assert _cf_src.index("liveguard.snapshot(guard, game_dir, root)") < \
    _cf_src.index("os.kill(pid, signal.SIGTERM)")
for _cf_doc in ("CLAUDE.md", os.path.join("doc", "fundament",
                                          "09-facts-orion2re-and-pygame.md")):
    _cf_text = open(os.path.join(os.path.dirname(SCREENS_DIR), _cf_doc),
                    encoding="utf-8").read()
    assert "--close-foreign" in _cf_text and "Data does not play" in \
        " ".join(_cf_text.split()).replace("DATA DOES NOT PLAY",
                                           "Data does not play"), _cf_doc
ok("a leftover engine or client is closed only after the backup — SIGTERM, "
   "SIGKILL only if it stays, each recorded — and never connected to; the "
   "rule (while Data does not play) stands in CLAUDE.md, fundament 09 and "
   "tools/engine_start.py")

# ── 4. OrionLayer never starts an engine, and never stops one ─────────
# Asked on 26 September 2026 (work order 176, Data): does `python main.py`
# start an orion2re and leave it running when its window is closed? It does
# not start one: measured live the same day — no child process, no new
# orion2re, with an engine running (it connected) and without (standalone),
# and a normal window close (WM_DELETE_WINDOW) ended it with exit 0 and left
# the engine it had not started running (evidence/work_order_176/main_py/).
# So there is nothing of its own to stop, and a foreign engine is never
# stopped. This holds the rule in the source: nothing the app runs launches
# a process or signals one; its exit only disconnects.
import ast as _nx_ast
_nx_root = os.path.dirname(SCREENS_DIR)
_nx_files = [os.path.join(_nx_root, "main.py")]
for _nx_dir in ("core", "screens"):
    for _nx_dp, _nx_dn, _nx_fn in os.walk(os.path.join(_nx_root, _nx_dir)):
        _nx_dn[:] = [d for d in _nx_dn if d != "__pycache__"]
        _nx_files += [os.path.join(_nx_dp, f) for f in _nx_fn
                      if f.endswith(".py")]
_nx_bad = []
for _nx_f in _nx_files:
    _nx_tree = _nx_ast.parse(open(_nx_f, encoding="utf-8").read())
    for _nx_node in _nx_ast.walk(_nx_tree):
        if isinstance(_nx_node, _nx_ast.Call):
            _nx_fn = _nx_node.func
            _nx_name = (_nx_fn.attr if isinstance(_nx_fn, _nx_ast.Attribute)
                        else getattr(_nx_fn, "id", ""))
            if _nx_name in ("Popen", "spawnv", "spawnl", "system", "kill",
                            "killpg", "execv", "execvp", "startfile"):
                _nx_bad.append(f"{os.path.relpath(_nx_f, _nx_root)}:"
                               f"{_nx_node.lineno} {_nx_name}")
            if _nx_name == "run" and any(
                    isinstance(a, _nx_ast.List) and any(
                        isinstance(e, _nx_ast.Constant) and
                        "orion2re" in str(e.value) for e in a.elts)
                    for a in _nx_node.args):
                _nx_bad.append(f"{os.path.relpath(_nx_f, _nx_root)}:"
                               f"{_nx_node.lineno} runs orion2re")
assert not _nx_bad, ("OrionLayer itself launches or signals a process — it "
                     "must neither start an engine nor stop one", _nx_bad)
_nx_main = open(os.path.join(_nx_root, "main.py"), encoding="utf-8").read()
_nx_run = _nx_main[_nx_main.index("    def run(self):"):
                   _nx_main.index("    def _handle_events(self):")]
assert "self.client.disconnect()" in _nx_run, "the exit only disconnects"
ok("OrionLayer starts no engine and stops none: nothing main.py, core or a "
   "screen runs launches or signals a process, and closing the window only "
   "disconnects (measured live, work order 176)")
