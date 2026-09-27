#!/usr/bin/env python3
"""Play: start the game and OrionLayer together — work order 183.

    python play.py

THE PLAYER'S START. Until work order 183 a player started orion2re by hand
in one terminal and `main.py` in another (README's quick start), and the
original's logos and intro played for 113 s, with their sound, before the
Extension API came up. Data decided (183): a player skips the intro exactly
as the tools do and lands in the HD main menu without a key of their own;
nothing of the intro may be heard.

So this starts the engine through `tools/engine_start.start` — the SAME
function every live tool starts it with, so the skip is the tools' skip by
construction, not a copy of it: one space key to the engine's own window
while its log stands at "data space allocated" (`tools/intro_skip.py`,
the original's own skip, jim.cpp:59-61), and the original's intro is never
played (jim.cpp:150-152). Measured in work order 183: with the key, the
engine plays nothing before the main menu's music, which begins after
READY; without it, 108 s of intro sound from 5.0 s on.

What differs from a tool's start, and why:
  * the engine goes on the player's own desktop (`real_desktop`), with the
    player's own audio — the tools' virtual display plays no sound;
  * no liveguard backup (a player's saves are the player's to write) and no
    idle inhibitor (the tools hold the screen on for an unattended run);
  * OrionLayer is started after READY, in the player's own environment —
    never the tools' dummy drivers;
  * THE ENGINE IS STOPPED WHEN ORIONLAYER ENDS. Since open fix 41 its window
    is never shown, so an engine left behind would be invisible, would hold
    the port and could still play music — nothing the player could close.

Needs `xdotool` for the skip; without it the start says the intro will play.

OrionLayer ITSELF still starts no engine and stops none (work order 176,
smoke check 006e: main.py, core and the screens launch and signal nothing).
This is a launcher around it, like `tools/engine_start.py`: it stops only
the engine its own start returned, and an engine it did not start is never
touched — `engine_start` refuses to start beside one, and so does this.
"""
import os
import shutil
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import engine_start  # noqa: E402

#: Why the engine goes onto the player's desktop — `engine_start` requires a
#: reason for it, and prints it.
PLAYER_REASON = "player start (play.py)"
LOG = os.path.expanduser("~/.cache/orionlayer/orion2re.log")
#: The variables the tools force on a client (work order 182) — a player's
#: OrionLayer must not inherit them from a shell that set them for a tool.
TOOL_ONLY = ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER", "ORIONLAYER_REAL_DESKTOP")


def client_env(base=None):
    """OrionLayer's environment: the player's own, minus the tools' forcing."""
    env = dict(os.environ if base is None else base)
    for key in TOOL_ONLY:
        env.pop(key, None)
    return env


def gone(pid):
    """True once `pid` has exited. The engine is this process's own child,
    and an exited child stays a zombie — which `kill(pid, 0)` still finds —
    until it is reaped, so it is reaped here; `kill(pid, 0)` only for a
    process that is not ours. (The first version SIGKILLed a zombie and
    reported an engine that had ended in a second as one that would not.)"""
    try:
        return os.waitpid(pid, os.WNOHANG)[0] == pid
    except ChildProcessError:
        pass
    try:
        os.kill(pid, 0)
    except OSError:
        return True
    return False


def stop_engine(pid, out=print, wait=5.0):
    """SIGTERM the engine this start owns, SIGKILL if it stays. Returns how
    it ended, or None when it had already gone."""
    if gone(pid):
        return None
    os.kill(pid, signal.SIGTERM)
    end = time.time() + wait
    while time.time() < end:
        if gone(pid):
            out(f"orion2re PID {pid} stopped (SIGTERM)")
            return "SIGTERM"
        time.sleep(0.1)
    os.kill(pid, signal.SIGKILL)
    out(f"orion2re PID {pid} did not stop; SIGKILL")
    return "SIGKILL"


def main(argv=None, out=print):
    if not shutil.which("xdotool"):
        out("WARNING: xdotool is not installed — the original's intro cannot "
            "be skipped and will play, with its sound, for about two minutes")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    pid = engine_start.start(LOG, inhibit=False, guard=None, out=out,
                             real_desktop=PLAYER_REASON)
    if not pid:
        out(f"The game did not start — its log is {LOG}")
        return 1
    try:
        return subprocess.call([sys.executable, os.path.join(ROOT, "main.py")],
                               cwd=ROOT, env=client_env())
    finally:
        stop_engine(pid, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
