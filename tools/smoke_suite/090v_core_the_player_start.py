# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090v_core_the_player_start.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 2 check(s) it holds:
#   - the player's start (play.py) is the tools' start with the intro skip, on the player's desktop and audio, stops only the engine it started, and is the README's quick start
#   - the engine's window is hidden only because OrionLayer's start asks (open fix 43): ORION2RE_HIDE_WINDOW on both displays; F12 shows it and hides it again, and a client without a connection sends nothing


# ── THE PLAYER'S START (work order 183, part 2) ─────────────────
#
# Data decided (183) that a player skips the original's intro exactly as
# the tools do, lands in the HD main menu without a key, and hears nothing
# of the intro. Measured in 183: with the tools' key the engine plays
# nothing before the main menu's music, which starts after READY; without
# it, 108 s of intro sound. So what has to hold is that `play.py` IS the
# tools' start — `engine_start.start`, the function every live tool uses,
# with its skip left on — and not a second copy of it; that its client gets
# the player's own drivers, never the tools' forced dummy ones; that the
# engine it started is stopped when OrionLayer ends (since open fix 41 its
# window is never shown, so a leftover would be invisible and hold the
# port); and that the README's quick start is this command.
import ast as _ps_ast
import signal as _ps_signal
import subprocess as _ps_sp
import play as _ps_play
import engine_start as _ps_es

_ps_root = os.path.dirname(SCREENS_DIR)
assert _ps_play.engine_start is _ps_es, "play.py must start through tools/engine_start"

# 1. The tools' start, driven with stand-ins: a real child process stands in
#    for the engine so the stop is exercised on a process, zombie and all.
_ps_calls, _ps_lines = {}, []
_ps_child = _ps_sp.Popen([sys.executable, "-c", "import time; time.sleep(60)"])


def _ps_start(log, **kw):
    _ps_calls["start"] = dict(kw, log=log)
    return _ps_child.pid


def _ps_call(cmd, cwd=None, env=None):
    _ps_calls["client"] = (cmd, cwd, env)
    return 0


import tempfile as _ps_tmp
_ps_tmpdir = _ps_tmp.TemporaryDirectory()
_ps_saved = (_ps_es.start, _ps_play.subprocess.call, _ps_play.LOG)
_ps_play.LOG = os.path.join(_ps_tmpdir.name, "cache", "orion2re.log")
_ps_env_saved = {k: os.environ.get(k) for k in _ps_play.TOOL_ONLY}
try:
    _ps_es.start = _ps_start
    _ps_play.subprocess.call = _ps_call
    for _ps_k in _ps_play.TOOL_ONLY:
        os.environ[_ps_k] = "dummy"
    _ps_rc = _ps_play.main([], out=_ps_lines.append)
finally:
    _ps_es.start, _ps_play.subprocess.call, _ps_play.LOG = _ps_saved
    _ps_tmpdir.cleanup()
    for _ps_k, _ps_v in _ps_env_saved.items():
        if _ps_v is None:
            os.environ.pop(_ps_k, None)
        else:
            os.environ[_ps_k] = _ps_v
_ps_kw = _ps_calls["start"]
assert _ps_rc == 0, _ps_rc
assert not _ps_kw.get("intro"), "the player's start must skip the intro"
assert _ps_kw.get("real_desktop"), "the player's engine goes on the player's desktop"
assert _ps_kw.get("guard") is None and _ps_kw.get("inhibit") is False, _ps_kw
_ps_cmd, _ps_cwd, _ps_env = _ps_calls["client"]
assert _ps_cmd[-1] == os.path.join(_ps_root, "main.py") and _ps_cwd == _ps_root
assert not [k for k in _ps_play.TOOL_ONLY if k in _ps_env], \
    "the tools' forced drivers reached the player's OrionLayer"
# The stand-in exited on SIGTERM and was reaped: no zombie, no SIGKILL.
assert any("stopped (SIGTERM)" in _l for _l in _ps_lines), _ps_lines
assert _ps_child.poll() is not None
# An engine that already ended (QUIT from the GAME menu) is left alone.
_ps_done = _ps_sp.Popen([sys.executable, "-c", "pass"])
_ps_done.wait()
assert _ps_play.stop_engine(_ps_done.pid, out=_ps_lines.append) is None

# A refused start (an engine already running — somebody else's) starts no
# OrionLayer and signals nothing: play.py stops only what its start returned.
_ps_saved = (_ps_es.start, _ps_play.subprocess.call, _ps_play.stop_engine)
_ps_touched = []
try:
    _ps_es.start = lambda log, **kw: None
    _ps_play.subprocess.call = lambda *a, **k: _ps_touched.append("client")
    _ps_play.stop_engine = lambda pid, out=None: _ps_touched.append(pid)
    assert _ps_play.main([], out=_ps_lines.append) == 1
finally:
    _ps_es.start, _ps_play.subprocess.call, _ps_play.stop_engine = _ps_saved
assert _ps_touched == [], _ps_touched

# 2. The tools' SKIP, not a copy: play.py neither imports the skip nor sends
#    a key of its own, and the start it calls skips unless asked not to.
_ps_tree = _ps_ast.parse(open(os.path.join(_ps_root, "play.py"), encoding="utf-8").read())
_ps_names = {a.name for n in _ps_ast.walk(_ps_tree)
             if isinstance(n, (_ps_ast.Import, _ps_ast.ImportFrom)) for a in n.names}
assert "intro_skip" not in _ps_names, "play.py must not carry its own skip"
assert not any(isinstance(n, _ps_ast.Constant) and n.value == "key"
               for n in _ps_ast.walk(_ps_tree)), "play.py sends no key itself"
import inspect as _ps_insp
assert _ps_insp.signature(_ps_es.start).parameters["intro"].default is False
assert "intro_skip.step(" in _ps_insp.getsource(_ps_es._start_once)

# 3. The README's quick start IS the player's start.
_ps_readme = open(os.path.join(_ps_root, "README.md"), encoding="utf-8").read()
_ps_qs = _ps_readme[_ps_readme.index("## Quick start"):]
_ps_qs = _ps_qs[:_ps_qs.index("\n## ", 5)]
_ps_block = _ps_qs[_ps_qs.index("```"):]
_ps_block = _ps_block[:_ps_block.index("```", 3)]
assert "python play.py" in _ps_block, \
    "README's quick start must open with python play.py"
ok("the player's start (play.py) is the tools' start with the intro skip, on "
   "the player's desktop and audio, stops only the engine it started, and is "
   "the README's quick start")


# ── THE ENGINE'S WINDOW ON REQUEST (open fix 43, work order 186) ─────
#
# Open fix 43 (applied by 186) hides the engine's window from the start
# ONLY when the starter asks, `ORION2RE_HIDE_WINDOW`, and lets a client
# show and hide it (`MSG_SHOW_WINDOW` 0x86, one byte). Without the variable
# every start — the tools' and `play.py`'s — would show the original's
# window on the player's desktop again (measured in 186 Part 1). So: the
# one environment every start uses carries it, on the virtual display and
# the real one alike; `GameClient.show_window` sends exactly the message;
# and F12 shows the window entering the original's picture and hides it
# returning to HD — asserted by calling the F12 handler on a stand-in App.
import struct as _pw_struct
import vdisplay as _pw_vd
from core.wire_protocol import MSG_SHOW_WINDOW as _PW_MSG
import main as _pw_main
from core.game_client import GameClient as _PwClient

assert _PW_MSG == 0x86
_pw_real_ensure = _pw_vd.ensure
_pw_vd.ensure = lambda out=print: (":97", 4242, "/nonexistent/xauth")
try:
    _pw_envs = {"virtual": _pw_vd.engine_env(base={}, out=lambda *a: None),
                "real": _pw_vd.engine_env("a stand-in reason", base={},
                                          out=lambda *a: None)}
finally:
    _pw_vd.ensure = _pw_real_ensure
for _pw_k, _pw_e in _pw_envs.items():
    assert _pw_e.get("ORION2RE_HIDE_WINDOW") == "1", (
        f"the {_pw_k} display's engine would show its own window (open fix 43)")
# play.py reaches the engine through engine_start, whose environment is
# engine_env (the check above holds the start itself).
assert "engine_env(" in _ps_insp.getsource(_ps_es)

_pw_sent = []
_pw_c = _PwClient()
_pw_c._send_message = lambda t, p=b"": _pw_sent.append((t, p))
_pw_c.show_window(True)
_pw_c.show_window(False)
assert _pw_sent == [(0x86, _pw_struct.pack("<B", 1)),
                    (0x86, _pw_struct.pack("<B", 0))], _pw_sent

_pw_calls = []


class _PwStandIn:
    render_mode = "hd"

    class client:
        connected = True

        @staticmethod
        def show_window(show):
            _pw_calls.append(show)


_pw_app = _PwStandIn()
_pw_main.App._cycle_render_mode(_pw_app)
assert _pw_app.render_mode == "original" and _pw_calls == [True], _pw_calls
_pw_main.App._cycle_render_mode(_pw_app)
assert _pw_app.render_mode == "hd" and _pw_calls == [True, False], _pw_calls
_PwStandIn.client.connected = False
_pw_main.App._cycle_render_mode(_pw_app)
assert _pw_calls == [True, False], "F12 without a connection sent something"
ok("the engine's window is hidden only because OrionLayer's start asks (open "
   "fix 43): ORION2RE_HIDE_WINDOW on both displays; F12 shows it and hides it "
   "again, and a client without a connection sends nothing")
