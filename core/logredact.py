"""Keep the player's name and folders out of the logs a tester posts.

Work order 333 (Data's decision, 27 October 2026, questions 8 and 9 of
`333-parked-for-data.md`): `faults.log` holds whole tracebacks, and every
frame of one prints the absolute path of its file (`/home/<name>/…`,
`C:\\Users\\<name>\\…`); an exception message can name the game folder. A
tester who pastes the log into a bug report would hand over the user name.
So the text is redacted BEFORE it is written to a file, and the line numbers
stay: nothing a developer reads a traceback for is lost.

What is replaced, longest first: the folder OrionLayer runs from
(`<orionlayer>`), the home folder (`~`), then any `/home/<x>`, `/Users/<x>`
or `X:\\Users\\<x>` that is left (another account's, a game folder on
another drive). A bare user name that stands alone in a message is NOT
found — a name is not a path — and another account's name with a space in
it keeps its tail after the space (`/Users/Al Bob` -> `/Users/<user> Bob`):
where a path ends cannot be told from its text. The tester guide says to
look before posting.

A log must never be the next fault: every function here returns the text it
was given if it cannot do its job.
"""
import logging
import logging.handlers
import os
import re

#: The client's own log beside faults.log: what the console shows, kept, so
#: a report can carry the build line (`core.config.build_line`).
CLIENT_LOG = "client.log"
LOG_BYTES = 1024 * 1024
LOG_KEEP = 2
FORMAT = "%(asctime)s.%(msecs)03d %(name)s: %(message)s"
DATEFMT = "%H:%M:%S"

#: What may follow a folder for it to be that folder and not the start of a
#: longer name (`/home/data` is not `/home/database`).
_END = r"(?=$|[/\\\s\"'):,;\]])"
_LEFT = (re.compile(r"(/home|/Users)/[^/\s\"'\\]+"),
         re.compile(r"(?i)\b([a-z]:\\+Users\\+)[^\\\s\"']+"))
_cache = {}


def _roots():
    """[(compiled pattern, replacement)], the longest folder first. A
    Windows path inside an exception message is shown by `repr`, which
    doubles its backslashes, so both spellings are looked for."""
    from core import config
    home = os.path.expanduser("~")
    if (config.BASE_DIR, home) in _cache:
        return _cache[(config.BASE_DIR, home)]
    out = []
    for text, label in ((config.BASE_DIR, "<orionlayer>"), (home, "~")):
        text = (text or "").rstrip("/\\")
        if len(text) > 1:
            for spelled in {text, text.replace("\\", "\\\\")}:
                out.append((len(spelled),
                            re.compile(re.escape(spelled) + _END), label))
    _cache.clear()
    _cache[(config.BASE_DIR, home)] = [
        (pat, label) for _, pat, label in sorted(out, key=lambda t: -t[0])]
    return _cache[(config.BASE_DIR, home)]


def redact(text):
    """`text` without the folders of this machine's user."""
    try:
        for pattern, label in _roots():
            text = pattern.sub(label, text)
        text = _LEFT[0].sub(lambda m: m.group(1) + "/<user>", text)
        return _LEFT[1].sub(lambda m: m.group(1) + "<user>", text)
    except Exception:                  # noqa: BLE001 — see the docstring
        return text


class Formatter(logging.Formatter):
    """The console's format, redacted: for the files only."""

    def format(self, record):
        return redact(super().format(record))


def attach_file(path=None, logger=None):
    """Add the rotating client log to the root logger; the path, or None
    when it could not be opened (a read-only folder must not stop the
    start). Called by `main.py`'s program entry only, so a check or a tool
    that imports `main` writes no file."""
    try:
        if path is None:
            from core import usermod
            path = os.path.join(usermod.user_dir(), "logs", CLIENT_LOG)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=LOG_BYTES, backupCount=LOG_KEEP,
            encoding="utf-8")
        handler.setFormatter(Formatter(FORMAT, DATEFMT))
        (logger or logging.getLogger()).addHandler(handler)
        return path
    except OSError:
        return None
