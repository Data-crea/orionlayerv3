"""Skip the original's logos and intro with one key — work order 179.

`tools/engine_start.py` calls it while the log stands at "data space
allocated"; it lives here so that file stays one thing (the start and its
refusals).

SKIPPING THE INTRO (work order 179, Data: "always skip the intro — one
key is enough"). The original's own rule: any key while the logos play
ends them (`key::Keyboard_Status_`, jim.cpp:59-61) and the intro after
them is skipped with it (jim.cpp:93). The engine has a `_skip_intro`
flag (mox2.cpp:301) that nothing sets; setting it would be an engine
change, so the key is sent instead — to the engine's OWN window by id
(`xdotool key --window`, never to whatever has the focus). Space, because
it is no hotkey of the main menu (mainmenu.cpp:126-138: C L N M H Q), so
a key that arrives after the logos does nothing.
"""
import subprocess
import time

LOGOS_DONE = "mox2: logos drawn"
SKIP_KEY = "space"


def skip_intro(pid, env):
    """Press SKIP_KEY in `pid`'s windows. True if a window took it."""
    try:
        wids = subprocess.run(["xdotool", "search", "--pid", str(pid)],
                              capture_output=True, text=True, env=env,
                              timeout=5).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return False
    sent = False
    for wid in wids:
        try:
            sent |= subprocess.run(["xdotool", "key", "--window", wid,
                                    SKIP_KEY], env=env, timeout=5,
                                   capture_output=True).returncode == 0
        except (OSError, subprocess.SubprocessError):
            pass
    return sent




def step(pid, text, env, skips, out):
    """One pass of the start loop while the log stands at "data space
    allocated": press the key (at most 20 times, half a second apart) until
    the log says the logos are drawn. Returns the new count. A hang (open
    fix 31) is still told apart by the caller: a key cannot end a wait for
    a present."""
    if LOGOS_DONE in text or skips >= 20 or not skip_intro(pid, env):
        return skips
    if skips == 0:
        out(f"INTRO SKIPPED: one {SKIP_KEY!r} key sent to the engine's window "
            f"(the original's own skip, jim.cpp:59-61)")
    time.sleep(0.5)
    return skips + 1
