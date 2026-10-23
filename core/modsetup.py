"""What switching the mod folder ON starts — work order 197 E (Data, 30
September 2026: "switching it on shows 'can take a while' and starts the
extraction").

A mod replaces a picture by its name, and the names a modder needs are the
game's pictures OrionLayer reads; several of them exist only once the
player's own MOO2 files have been extracted (`tools/setup.py`'s
`from_game()`: reported there, never run). So the switch runs, in the
background, every extractor whose file is absent — in `from_game()`'s
order, each as its own process in the project folder, skipping the one that
needs a path only the player knows — and then writes the mod kit
(`tools/mod_template.py`: the guide, the names, OrionLayer's own starting
points; never a MOO2 file, decision 72) and the frame templates
(`tools/frame_template.py`). Nothing of it changes what is drawn before
the restart the switch asks for anyway (decision 18).

`state()` is what the GAME menu's mod row shows: "idle", ("running", i, n,
what), a dict with phase, i, n, what, failed (names) and error — and the row prints "can take a
while" while it runs, and a failure (a failed step, or an `error` from a
plan that could not be made or a job that stopped) as a failure (work
order 326 H1), never as "Ready".
"""
import contextlib
import importlib
import logging
import os
import shlex
import subprocess
import sys
import threading

from core.config import BASE_DIR

log = logging.getLogger("modsetup")

#: An extractor whose command needs a path only the player can give
#: (`tools/nebula_extract.py /path/to/starbg.lbx`) is not run here.
PLACEHOLDER = "/path/to/"
KIT = (("the mod kit", ["tools/mod_template.py"]),
       ("the frame templates", ["tools/frame_template.py"]))

#: HD EXTENSION `setup_job_timeout` (work order 324 b, UNVERIFIED live): the longest one
#: extractor may run. An extractor that hangs held the state at "running"
#: for ever and every later `start()` refused.
RUN_TIMEOUT = 1800

_lock = threading.Lock()
_state = {"phase": "idle", "i": 0, "n": 0, "what": "", "failed": [],
          "error": ""}
_thread = None


@contextlib.contextmanager
def tools_on_path():
    """`tools/` at the front of `sys.path` for the length of an import and
    not a moment longer: its `basepack.py` is not `core/basepack.py`, and
    `tools/setup.py` itself puts the tree and `tools/` at the front. The
    path is put back as it was, and the tool modules the import brought
    in leave `sys.modules` with it (their functions keep what they need)."""
    tools = os.path.join(BASE_DIR, "tools")
    saved_path, before = list(sys.path), set(sys.modules)
    sys.path.insert(0, tools)
    try:
        yield
    finally:
        sys.path[:] = saved_path
        for name in set(sys.modules) - before:
            file = getattr(sys.modules[name], "__file__", None) or ""
            if os.path.dirname(os.path.abspath(file)) == tools:
                del sys.modules[name]


def import_tool(name):
    """The module `tools/<name>.py`, imported under `tools_on_path`."""
    with tools_on_path():
        return importlib.import_module(name)


def plan(entries=None):
    """[(what, argv)] to run: the absent extractors, then the kit."""
    if entries is None:
        entries = _from_game()
    steps = []
    for path, what, command in entries:
        if os.path.exists(path) or PLACEHOLDER in command:
            continue
        argv = shlex.split(command)
        if argv and argv[0] == "python":
            argv = argv[1:]
        steps.append((what.split(" — ")[0], argv))
    return steps + [(what, list(argv)) for what, argv in KIT]


def _from_game():
    """`tools/setup.from_game()` — the one registry of extracted files."""
    return import_tool("setup").from_game()


def state():
    with _lock:
        return dict(_state, failed=list(_state["failed"]))


def running():
    return state()["phase"] == "running"


def start(steps=None, runner=None):
    """Begin in the background; a second start while running does nothing.
    `runner(argv) -> bool` is the subprocess call (a check replaces it)."""
    global _thread
    with _lock:
        if _state["phase"] == "running":
            return False
        _state.update(phase="running", i=0, n=len(steps or ()), what="",
                      failed=[], error="")
    if steps is None:
        # The import and the registry walk run here, on the caller's thread
        # — the UI thread (`screens/game_menu/oldrop.py`), so the frame
        # waits for them — and outside the lock: the job thread only
        # starts after them and holds the lock just for its short updates.
        try:
            steps = plan()
        except Exception as err:
            _fail(f"could not plan: {err}")
            return True
        with _lock:
            _state["n"] = len(steps)
    _thread = threading.Thread(target=_work, args=(steps, runner or _run),
                               name="modsetup", daemon=True)
    _thread.start()
    return True


def wait(timeout=None):
    if _thread is not None:
        _thread.join(timeout)


def _fail(reason):
    """End the job as done-with-an-error: the state is never left
    "running" by a step that raised."""
    log.warning("mod setup: %s", reason)
    with _lock:
        _state.update(phase="done", what="", error=reason)


def _run(argv, timeout=None):
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    try:
        # errors="replace": an extractor's output is only read for the
        # log, and a byte that is not UTF-8 must not kill the thread.
        proc = subprocess.run([sys.executable] + argv, cwd=BASE_DIR,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=env,
                              timeout=timeout or RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        log.warning("mod setup: %s timed out after %ss", " ".join(argv),
                    timeout or RUN_TIMEOUT)
        return False
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        log.warning("mod setup: %s failed: %s", " ".join(argv),
                    " | ".join(tail))
    return proc.returncode == 0


def _work(steps, runner):
    try:
        for i, (what, argv) in enumerate(steps, 1):
            with _lock:
                _state.update(i=i, what=what)
            log.info("mod setup %d/%d: %s", i, len(steps), what)
            try:
                ok = runner(argv)
            except Exception as err:      # one step never ends the job
                log.warning("mod setup: %s: %s", what, err)
                ok = False
                with _lock:
                    _state["error"] = f"{what}: {err}"
            if not ok:
                with _lock:
                    _state["failed"].append(what)
    except Exception as err:
        _fail(f"stopped: {err}")
        return
    with _lock:
        _state.update(phase="done", what="")
        failed = len(_state["failed"])
    log.info("mod setup done (%d step(s), %d failed)", len(steps), failed)
