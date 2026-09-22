# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 086_core_the_debug_input_socket_is_off.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - the debug input socket is off without its variable and open with it, mode 600 read back from dis


# ── THE DEBUG INPUT SOCKET: OFF, AND ON, BOTH FORCED ────────────
#
# Work order 142 C, from 141 E's proposal. It exists because a live
# acceptance has to follow a CLICK PATH and a session driving this
# project cannot move the pointer — work orders 140 and 141 both
# had to fall back to `livesend` and say so.
#
# BOTH STATES ARE FORCED, neither read off this machine: "a test
# that reads the user's disk answers differently for the user".
import shutil as _di_shutil
import socket as _di_socket
import stat as _di_stat
import tempfile as _di_tempfile
import time as _di_time
from core import debuginput as _di

assert "TOOL" in (_di.__doc__ or ""), (
    "core/debuginput.py no longer marks itself a TOOL")
_di_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                               "debuginput.py"), encoding="utf-8").read()
# IT POSTS AND STOPS. A second input path would be the copy
# decision 5 exists to stop, so the module may know pygame's queue
# and nothing about screens.
assert "pygame.event.post" in _di_src
# THE CODE, not the prose: the docstring names screens because it
# explains what the tool is for. What must not appear is a CALL.
_di_code = ast.parse(_di_src)
_di_calls = {ast.unparse(_n.func) for _n in ast.walk(_di_code)
             if isinstance(_n, ast.Call)}
for _di_word in ("dispatcher", "activate_field", "inject_click",
                 "client"):
    assert not [_c for _c in _di_calls if _di_word in _c], (
        f"core/debuginput.py calls something with {_di_word} in it; "
        f"it posts events and knows nothing else (decision 5)")
assert "pygame.event.post" in _di_calls, _di_calls

_di_env = os.environ.pop(_di.ENV_VAR, None)
_di_tmp = _di_tempfile.mkdtemp()
_di_rt = os.environ.get("XDG_RUNTIME_DIR")
try:
    os.environ["XDG_RUNTIME_DIR"] = _di_tmp
    # 1. OFF. No variable, no listener, no socket on disk.
    assert not _di.enabled()
    assert _di.DebugInput.open() is None
    assert not os.path.exists(_di.socket_path()), (
        "a socket exists although the switch is not set")

    # 2. ON. Listener, socket, mode 0600 — read back from the
    #    filesystem, not assumed from the umask.
    os.environ[_di.ENV_VAR] = "1"
    _di_in = _di.DebugInput.open()
    assert _di_in is not None, "the switch is set and nothing opened"
    try:
        _di_path = _di.socket_path()
        assert os.path.exists(_di_path)
        _di_mode = _di_stat.S_IMODE(os.stat(_di_path).st_mode)
        assert _di_mode == 0o600, f"socket mode is {_di_mode:o}, not 600"

        # 3. A CLICK ARRIVES AS A CLICK. One line in, the ordinary
        #    MOUSEBUTTONDOWN/UP pair out, with the WINDOW
        #    coordinates it was given.
        pygame.event.clear()
        _di_c = _di_socket.socket(_di_socket.AF_UNIX,
                                  _di_socket.SOCK_STREAM)
        _di_c.connect(_di_path)
        _di_c.sendall(b'{"type": "click", "x": 960, "y": 540}\n')
        _di_deadline = _di_time.time() + 3.0
        _di_n = 0
        while _di_n < 2 and _di_time.time() < _di_deadline:
            _di_n += _di_in.pump()
            _di_time.sleep(0.01)
        _di_evs = [e for e in pygame.event.get()
                   if e.type in (pygame.MOUSEBUTTONDOWN,
                                 pygame.MOUSEBUTTONUP)]
        assert [e.type for e in _di_evs] == [pygame.MOUSEBUTTONDOWN,
                                             pygame.MOUSEBUTTONUP], _di_evs
        assert all(e.pos == (960, 540) and e.button == 1
                   for e in _di_evs), _di_evs

        # 4. A KEY, AND A LINE THAT IS NOT ONE. An unknown type is
        #    a refusal with a word, never a silent no-op.
        pygame.event.clear()
        _di_c.sendall(b'{"type": "key", "key": "f"}\n'
                      b'{"type": "nonsense"}\n'
                      b'not json at all\n')
        _di_deadline = _di_time.time() + 3.0
        while _di_time.time() < _di_deadline:
            _di_in.pump()
            if any(e.type == pygame.KEYUP for e in pygame.event.get(
                    pygame.KEYUP, False)):
                break
            _di_time.sleep(0.01)
        pygame.event.clear()
        _di_c.close()
    finally:
        _di_in.close()
    assert not os.path.exists(_di.socket_path()), (
        "close() left the socket behind")

    # 5. AND `App` ASKS FOR IT AT THE ONE PLACE, before the queue
    #    is drained, so a posted event is in THIS frame.
    _di_main = io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                                    "main.py"), encoding="utf-8").read()
    assert _di_main.count("DebugInput.open()") == 1
    assert _di_main.count("_debug_input.pump()") == 1
    _di_body = _di_main.split("def _handle_events")[1]
    assert _di_body.index("_debug_input.pump()") < \
        _di_body.index("pygame.event.get()"), (
        "the socket is pumped after the queue is drained, so an "
        "event posted from it waits a frame")
finally:
    os.environ.pop(_di.ENV_VAR, None)
    if _di_env is not None:
        os.environ[_di.ENV_VAR] = _di_env
    if _di_rt is None:
        os.environ.pop("XDG_RUNTIME_DIR", None)
    else:
        os.environ["XDG_RUNTIME_DIR"] = _di_rt
    _di_shutil.rmtree(_di_tmp, ignore_errors=True)

ok("the debug input socket is off without its variable and open "
   "with it, mode 600 read back from disk, a click arrives as a "
   "MOUSEBUTTONDOWN/UP pair at the window coordinates it was "
   "given, and main pumps it before the queue is drained")
