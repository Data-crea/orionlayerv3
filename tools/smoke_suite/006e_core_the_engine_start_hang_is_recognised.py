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
# The 1 check(s) it holds:
#   - engine start: the hang's signature, the refusals, the environment, no connect


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
assert "## 31. A session-launched engine hangs" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "doc", "orion2re_open_fixes.md"),
    encoding="utf-8").read()
ok("engine start: the start hang's signature (not the intro, not a "
   "running engine), three refusals named, CLAUDE.md's environment with "
   "ORION2RE_NO_VSYNC, the port bound never connected, nothing killed by "
   "name")
