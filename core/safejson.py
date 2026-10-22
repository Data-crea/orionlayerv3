"""The one place a JSON file's SHAPE is checked — work order 324 c.

HD EXTENSION `safe_json` (UNVERIFIED live). `layout.json`, `boxes.json`, `help.json`
and `settings.json` are hand-edited, and a mod ships its own copies of
them. A file that does not parse, is not UTF-8, is the wrong kind of
object or lacks a key its reader indexes used to raise out of `enter()`,
`on_resize()` or the start, and the frame loop is not a place to survive
that. `read` answers None for such a file and says so ONCE per path and
reason (a reader runs per entry and per resize, so a line per call would
be a line per frame); the caller keeps the base file's value or its
defaults.
"""
import json
import logging

log = logging.getLogger("safejson")

_said = set()


def _say(path, why):
    if (path, why) not in _said:
        _said.add((path, why))
        log.warning("%s: %s — keeping the base value / the defaults",
                    path, why)


def read(path, shape=None, required=()):
    """The parsed file, or None (and one log line) when it is missing,
    unreadable, not UTF-8, not valid JSON, not a `shape` (a type or a
    tuple of types) or lacks a key of `required` (objects only)."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as err:     # UnicodeDecodeError is one
        _say(path, f"will not load ({err})")
        return None
    if shape is not None and not isinstance(data, shape):
        _say(path, f"top level is {type(data).__name__}, expected "
                   f"{getattr(shape, '__name__', shape)}")
        return None
    missing = [k for k in required if not isinstance(data, dict)
               or k not in data]
    if missing:
        _say(path, f"lacks the key(s) {', '.join(map(str, missing))}")
        return None
    return data
