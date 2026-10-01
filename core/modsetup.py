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
what), ("done", failed names) — and the row prints "can take a while"
while it runs.
"""
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

_lock = threading.Lock()
_state = {"phase": "idle", "i": 0, "n": 0, "what": "", "failed": []}
_thread = None


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
    tools = os.path.join(BASE_DIR, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import setup as _setup
    return _setup.from_game()


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
        steps = plan() if steps is None else steps
        _state.update(phase="running", i=0, n=len(steps), what="",
                      failed=[])
    _thread = threading.Thread(target=_work, args=(steps, runner or _run),
                               name="modsetup", daemon=True)
    _thread.start()
    return True


def wait(timeout=None):
    if _thread is not None:
        _thread.join(timeout)


def _run(argv):
    proc = subprocess.run([sys.executable] + argv, cwd=BASE_DIR,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        log.warning("mod setup: %s failed: %s", " ".join(argv),
                    " | ".join(tail))
    return proc.returncode == 0


def _work(steps, runner):
    for i, (what, argv) in enumerate(steps, 1):
        with _lock:
            _state.update(i=i, what=what)
        log.info("mod setup %d/%d: %s", i, len(steps), what)
        try:
            ok = runner(argv)
        except OSError as err:
            log.warning("mod setup: %s: %s", what, err)
            ok = False
        if not ok:
            with _lock:
                _state["failed"].append(what)
    with _lock:
        _state.update(phase="done", what="")
    log.info("mod setup done (%d step(s), %d failed)", len(steps),
             len(_state["failed"]))
