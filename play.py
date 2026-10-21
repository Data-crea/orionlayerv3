#!/usr/bin/env python3
"""Play: start the game and OrionLayer together — work order 183.

    python play.py

THE PLAYER'S START. Until work order 183 a player started orion2re by hand
in one terminal and `main.py` in another, and the
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
  * THE ENGINE IS STOPPED WHEN ORIONLAYER ENDS. Its window is hidden (open
    fix 41; since open fix 43, work order 186, because this start asks for
    it — `ORION2RE_HIDE_WINDOW` in `tools/vdisplay.engine_env` — and F12
    shows it on request), so an engine left behind would be invisible,
    would hold the port and could still play music — nothing the player
    could close.

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
#: The two this start sets itself (work order 322 C), which no shell may
#: hand down from another start.
ENGINE_ENV = ("ORIONLAYER_ENGINE_PID", "ORIONLAYER_ENGINE_LOG")


def client_env(base=None, pid=None, log=None):
    """OrionLayer's environment: the player's own, minus the tools' forcing
    — and, with `pid`, the engine this start owns and its log, so that a
    lost connection to an engine that has ENDED is said, not retried
    forever (HD EXTENSION `engine_lost`, `core/enginelink.py`; the names
    are its ENV_PID and ENV_LOG)."""
    env = dict(os.environ if base is None else base)
    for key in TOOL_ONLY + ENGINE_ENV:
        env.pop(key, None)
    if pid:
        env["ORIONLAYER_ENGINE_PID"] = str(pid)
        if log:
            env["ORIONLAYER_ENGINE_LOG"] = log
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


def ending(rc):
    """The line that says how OrionLayer ended, from its return code — work
    order 213: Data's client died with SIGSEGV as a battle opened and his
    terminal showed only the engine being stopped. The client's own last
    word (`core/lastword.py`) says why from inside; this line is the one
    that is always there, SIGKILL included, and it comes BEFORE the
    engine's, so the terminal shows which side ended first."""
    if rc is None:
        # play.py itself was interrupted (Ctrl+C reaches both processes)
        return "OrionLayer ended: play.py was interrupted before it returned"
    if rc < 0:
        try:
            name = signal.Signals(-rc).name
        except ValueError:
            name = f"signal {-rc}"
        why = "it crashed — the lines above say where; `coredumpctl " \
            "list python` names the core" if -rc in (
                signal.SIGSEGV, signal.SIGFPE, signal.SIGABRT, signal.SIGBUS,
                signal.SIGILL) else "it was stopped from outside"
        return f"OrionLayer ended: {name} ({why})"
    return f"OrionLayer ended: exit status {rc}"


def stop_engine(pid, out=print, wait=5.0):
    """SIGTERM the engine this start owns, SIGKILL if it stays. Returns how
    it ended, or None when it had already gone."""
    if gone(pid):
        out(f"orion2re PID {pid} had already ended")
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


def configure(argv, out=print):
    """`--engine PATH` and `--game DIR`, saved into the player's own
    settings (work order 229 D, `core/paths.py`); then what is still
    missing, in plain words. Returns the list of problems ([] to go on)."""
    from core import paths
    argv = list(argv or [])
    want = {}
    for flag in ("--engine", "--game"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv):
                return [f"{flag} needs a path after it"]
            want[flag] = argv[i + 1]
    if want:
        where = paths.remember(want.get("--engine"), want.get("--game"))
        out(f"Saved in {where}: " + ", ".join(
            f"{k[2:]} = {v}" for k, v in want.items()))
    from core import basepack
    return paths.problems() + basepack.problems()


USAGE = """python play.py [--engine PATH] [--game DIR]

Starts the game (orion2re) and OrionLayer together. --engine and --game are
saved in your OrionLayer settings, so they are needed once."""


#: How long the client is given to end itself after Ctrl+C before it is
#: asked to, and then made to.
INTERRUPT_GRACE_S = 5.0


def run_client(argv, **kwargs):
    """Run the client and return its exit code.

    `subprocess.call` kills its child (SIGKILL) when the caller is
    interrupted, and Ctrl+C reaches both: the client was ending itself —
    its last word (`core/lastword.py`) and its log flushed — while play.py
    killed it from under that. Here an interrupt waits for the client,
    then asks (SIGTERM), and only then kills."""
    proc = subprocess.Popen(argv, **kwargs)
    try:
        return proc.wait()
    except KeyboardInterrupt:
        try:
            for step in (lambda: proc.wait(INTERRUPT_GRACE_S),
                         proc.terminate,
                         lambda: proc.wait(INTERRUPT_GRACE_S), proc.kill):
                try:
                    step()
                    if proc.poll() is not None:
                        break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            # also when the player presses it again while we wait: the
            # engine is stopped next, and a client left running under it
            # is an orphan
            if proc.poll() is None:
                proc.kill()
            proc.wait()
        raise


def main(argv=None, out=print):
    if argv and any(a in ("-h", "--help") for a in argv):
        out(USAGE)
        return 0
    sys.path.insert(0, ROOT)
    problems = configure(argv, out)
    if problems:
        out("OrionLayer cannot start the game yet:")
        for line in problems:
            out("  - " + line)
        return 2
    if not shutil.which("xdotool"):
        out("WARNING: xdotool is not installed — the original's intro cannot "
            "be skipped and will play, with its sound, for about two minutes")
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    pid = engine_start.start(LOG, inhibit=False, guard=None, out=out,
                             real_desktop=PLAYER_REASON)
    if not pid:
        out(f"The game did not start — its log is {LOG}")
        return 1
    rc = None
    try:
        rc = run_client([sys.executable, os.path.join(ROOT, "main.py")],
                        cwd=ROOT, env=client_env(pid=pid, log=LOG))
        return rc
    finally:
        out(ending(rc))
        stop_engine(pid, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
