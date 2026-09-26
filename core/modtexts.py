"""Texts by stable key, replaceable from the player's mod folder.

HD EXTENSION, work order 175, decision 73 (beside decision 72).

**ONE RESOLVER FOR WORDS, as `core.usermod` is for pictures.** A screen
asks `text(key)` and gets the player's text when the mod folder has a
good one, else the default the screen registered. No screen reads a mod
file itself; the folder itself is read only by `core.usermod`
(`usermod.read_text`), which keeps decision 72's "one reader" true.

**THE KEYS** are dotted and stable: `<screen>.<what>[.<more>]`, e.g.
`info.tab.history` or `info.reference.12.body`. A key is registered once,
in the screen's own text table (a module listed in `TABLES`), with:

  default    the text used when there is no mod file
  source     "own"  — OrionLayer's words: the template may copy them
             "moo2" — the original's words, from the player's own files
                      (an LBX text, HESTRNGS …): the template lists the KEY
                      only and never writes the text into anything
             "game" — a value the game supplies at run time (a name, a
                      number): not replaceable, listed for completeness

A "moo2" default is a CALLABLE — the text is read from the player's
extracted file when the screen asks, and is never in this tree.

**THE FILES** (the format is parked for Data, 175 item 3): one plain
UTF-8 text file per key, `texts/<first segment>/<rest of the key>.txt` —
`info.tab.history` is `texts/info/tab.history.txt`. The whole file is the
text; one trailing newline is dropped; a blank line is a paragraph break.
Somebody who is not a programmer opens the file OrionLayer's template
wrote, types, saves.

**NEVER A CRASH.** Missing folder, file or key: the default. A file that
is not UTF-8, is empty, or is over `MAX_BYTES`: ONE log line, the
default (`usermod.read_text`).

WHICH SCREENS COULD USE IT (work order 175 D): every screen with words
of its own — the main menu's and the GAME menu's labels, Custom Race's
messages, the HUD screens' headings, the Leaders screen's button words,
the help popup's HD-only entries. The Info screen is the first; the
resolver knows nothing Info-specific.
"""
import importlib
import logging

from core import usermod

log = logging.getLogger("modtexts")

#: The text tables: modules with a `TEXTS` dict {key: (default, source)}.
TABLES = ("screens.info.infotexts",)
SOURCES = ("own", "moo2", "game")
MAX_BYTES = 64 * 1024

_registry = {}
_loaded = [False]


def register(key, default, source="own"):
    """Add one key. A second registration of the same key must agree."""
    if source not in SOURCES:
        raise ValueError(f"{key}: source {source!r} is not one of {SOURCES}")
    if "." not in key or key != key.strip() or " " in key:
        raise ValueError(f"{key!r} is not a dotted key")
    old = _registry.get(key)
    if old is not None and old[1] != source:
        raise ValueError(f"{key} registered twice with different sources")
    _registry[key] = (default, source)


def _load_tables():
    if _loaded[0]:
        return
    _loaded[0] = True
    for name in TABLES:
        try:
            mod = importlib.import_module(name)
        except ImportError as err:          # a table that is not there
            log.warning("text table %s not loaded: %s", name, err)
            continue
        for key, (default, source) in getattr(mod, "TEXTS", {}).items():
            register(key, default, source)


def keys():
    """{key: source} for every registered key, sorted."""
    _load_tables()
    return {k: _registry[k][1] for k in sorted(_registry)}


def file_name(key):
    """The mod file that replaces `key`: texts/<first>/<rest>.txt."""
    first, _, rest = key.partition(".")
    return f"texts/{first}/{rest}.txt"


def default(key):
    """The registered default, with a "moo2" callable called; None for an
    unknown key or an original text that is not extracted."""
    _load_tables()
    got = _registry.get(key)
    if got is None:
        return None
    value = got[0]
    if callable(value):
        try:
            value = value()
        except Exception as err:            # a loader must never crash a screen
            log.warning("text %s: its default could not be read (%s)",
                        key, err)
            return None
    return value


def text(key, fallback=None):
    """The player's text for `key`, else the default, else `fallback`.
    A "game" key is never replaced: it is the caller's value, `fallback`."""
    _load_tables()
    got = _registry.get(key)
    if got is not None and got[1] == "game":
        return fallback
    if got is not None:
        mine = usermod.read_text(file_name(key), MAX_BYTES)
        if mine is not None:
            return mine
    value = default(key)
    return fallback if value is None else value


def reset():
    """Forget the registry (the smoke suite, after a check)."""
    _registry.clear()
    _loaded[0] = False
