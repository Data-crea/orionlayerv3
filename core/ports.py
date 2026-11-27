"""The Extension API's port — one source of truth (work order 440, open fix 133).

The engine takes its port from the environment variable `ORION2RE_EXT_PORT`
(decimal 1024-65535; unset or anything else keeps 17362 —
src/ext/ext_api.cpp, `Init`, which reads it with `strtol` base 10 and takes
the value only when the whole string parsed). Every OrionLayer client and
tool reads the SAME variable by the SAME rule through `ext_port`, so a live
run that gives its engine a port gives its client the same one without a
second setting. The player's default is the constant 17362: nothing sets the
variable for a player.

A bad value is ignored, as the engine ignores it: the tool and the engine
then agree on 17362 instead of one of them failing alone.
"""
import os
import re

DEFAULT_PORT = 17362
ENV_VAR = "ORION2RE_EXT_PORT"
LOW, HIGH = 1024, 65535

#: `strtol(s, &end, 10)` skips leading C-locale white space (ASCII only),
#: takes one optional sign and ASCII digits, and the engine requires
#: `*end == '\0'`: no trailing character at all, not even a newline.
_DECIMAL = re.compile(r"[ \t\n\v\f\r]*[+-]?[0-9]+")


def parse_port(text):
    """The port `text` names under the engine's rule, or None."""
    if text is None or not _DECIMAL.fullmatch(text):
        return None
    value = int(text)
    return value if LOW <= value <= HIGH else None


def ext_port(environ=None):
    """The port this process talks to: the variable if valid, else 17362."""
    environ = os.environ if environ is None else environ
    port = parse_port(environ.get(ENV_VAR))
    return DEFAULT_PORT if port is None else port


def resolve_port(configured=None, environ=None):
    """The port a client uses: a set, valid ORION2RE_EXT_PORT first (the
    run's own, which a settings file shared by every run must not
    override), then the settings file's `configured` value, then 17362."""
    environ = os.environ if environ is None else environ
    port = parse_port(environ.get(ENV_VAR))
    if port is not None:
        return port
    return configured or DEFAULT_PORT
