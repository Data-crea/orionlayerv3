"""Open a folder in the system's file manager — HD EXTENSION `open_mod_folder`, work order 254.

Data's decision (252 P4): the SYSTEM tab of the OrionLayer window has a
button "Open mod folder". It creates the folder when it is not there yet
(a modder finds it before switching the mod folder on), then asks the
platform's own opener for it: `xdg-open` on Linux and the BSDs, `open` on
macOS, `os.startfile` on Windows. The game never waits for it: the opener
is started detached and watched from a thread for a few seconds, so an
opener that is missing, or exits with an error because no file manager
answers, is known — the window then shows the folder's path instead
(`failed`). Nothing here raises into the window.
"""
import logging
import os
import shutil
import subprocess
import sys
import threading

log = logging.getLogger("openfolder")

#: How long an opener may run before it counts as having found a file
#: manager: xdg-open exits at once with an error when none answers, and
#: either hands over or waits on the file manager when one does.
WATCH_S = 5.0

#: The last request: its path and whether it is known to have failed.
_last = {"path": None, "failed": False}


def command(path, platform=None, which=shutil.which):
    """The argv that opens `path`, or None where `os.startfile` does it
    (Windows) or no opener is installed."""
    platform = platform or sys.platform
    if platform.startswith("win"):
        return None
    tool = "open" if platform == "darwin" else "xdg-open"
    found = which(tool)
    return [found, path] if found else None


def _spawn(argv):
    """Start the opener detached; the returned process is only watched."""
    return subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True)


def _watch(proc, path):
    try:
        code = proc.wait(timeout=WATCH_S)
    except subprocess.TimeoutExpired:
        proc.wait()              # still running: a file manager has it;
        return                   # wait it out so it leaves no zombie
    if code != 0 and _last["path"] == path:
        _last["failed"] = True
        log.warning("opener exited %s for %s — the path is shown", code,
                    path)


def open_folder(path, spawn=None, platform=None, which=shutil.which):
    """Create `path` if needed and hand it to the file manager. Returns
    False when it is known at once that no opener can show it (then
    `failed()` is True); a later failure of the opener sets `failed()`
    from the watching thread."""
    _last.update(path=path, failed=False)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as err:
        log.warning("cannot create %s: %s", path, err)
        _last["failed"] = True
        return False
    platform = platform or sys.platform
    try:
        if platform.startswith("win"):
            os.startfile(path)   # noqa: S606 (the player's own folder)
            return True
        argv = command(path, platform, which)
        if argv is None:
            raise OSError("no file opener installed")
        proc = (spawn or _spawn)(argv)
    except (OSError, AttributeError, ValueError) as err:
        log.warning("cannot open %s: %s — the path is shown", path, err)
        _last["failed"] = True
        return False
    if proc is not None and hasattr(proc, "wait"):
        threading.Thread(target=_watch, args=(proc, path),
                         daemon=True).start()
    log.info("mod folder handed to the file manager: %s", path)
    return True


def failed():
    """The path to show, while the last request is known to have failed;
    else None."""
    return _last["path"] if _last["failed"] else None


def forget():
    _last.update(path=None, failed=False)
