"""What choosing a language starts — work order 200 C.

The game's words in German come from the player's own German files
(`dev:doc/briefs/200-german-inventory.md`); `tools/setup.from_game()` names
each derived file and the extractor that writes it, per language. Choosing
German in Game Settings runs, in the background, every German extractor
whose file is absent (each its own process, as the mod switch's do,
`core/modsetup`). An extractor whose German source the installation lacks
fails, and its file stays absent — `core/lang.source` then reads the English
one. Nothing drawn changes before the restart the switch asks for.

`state()` is what the language row shows: idle, running (i of n), done
(how many German files exist now).
"""
import logging
import os
import shlex
import sys
import threading

from core import modsetup
from core.config import BASE_DIR

log = logging.getLogger("langsetup")

_lock = threading.Lock()
_state = {"phase": "idle", "i": 0, "n": 0, "made": 0}


def plan(language, entries=None):
    """[(path, argv)]: the absent derived files of `language` with their
    extractor (the commands `setup.from_game` gives for that language)."""
    if entries is None:
        tools = os.path.join(BASE_DIR, "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import setup as _setup
        entries = _setup.from_game({"language": language})
    steps, seen = [], set()
    for path, _what, command in entries:
        if not path.endswith(f"_{language}.json") or os.path.exists(path) \
                or modsetup.PLACEHOLDER in command or command in seen:
            continue
        seen.add(command)           # one TECHNAME run writes three files
        argv = shlex.split(command)
        steps.append((path, argv[1:] if argv[:1] == ["python"] else argv))
    return steps


def state():
    with _lock:
        return dict(_state)


def plan_from(language, folder):
    """[(path, argv)] against the other install the player named
    (`language_dir`, `tools/language_files.py`): every extractor of the
    language, its files read from there."""
    tools = os.path.join(BASE_DIR, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import language_files
    return [(os.path.join(BASE_DIR, "assets", "shared", "names"), argv)
            for argv in language_files.steps(language, folder)]


def start(language, steps=None, runner=None, folder=None):
    """Begin in the background; nothing while one runs or for English.
    `folder`: the other install holding the language's files, if any."""
    if language == "en":
        return False
    with _lock:
        if _state["phase"] == "running":
            return False
        if steps is None:
            steps = plan_from(language, folder) if folder else plan(language)
        _state.update(phase="running", i=0, n=len(steps), made=0)
    threading.Thread(target=_work, args=(steps, runner or modsetup._run),
                     name="langsetup", daemon=True).start()
    return True


def _work(steps, runner):
    made = 0
    for i, (path, argv) in enumerate(steps, 1):
        with _lock:
            _state.update(i=i)
        ok = False
        try:
            ok = runner(argv)
        except OSError as err:
            log.warning("language setup: %s: %s", " ".join(argv), err)
        # a step against the named folder writes where its extractor says:
        # it counts by its own success; a planned file by being there
        made += bool(ok) if os.path.isdir(path) else os.path.exists(path)
    with _lock:
        _state.update(phase="done", made=made)
    log.info("language setup done: %d of %d file(s) written", made,
             len(steps))
