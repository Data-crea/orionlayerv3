"""Live runs on a virtual display — work order 182, part 1.

Data works at the same desktop while live runs happen. Until 182 the
engine's window opened in front of him and his clicks and focus changes
could land between a run's inputs. Measured on this machine
(`dev:doc/briefs/182-virtual-display.md`): a private **Xvfb** carries the
engine (SDL x11), the intro skip (`xdotool key --window`), screenshots
(`import`) and a pygame window exactly as `:0` does, at the same snapshot
pacing, and nothing of it reaches Data's session. `mutter --headless`
works too and was not chosen (it needs its own D-Bus session and writes a
`.mutter-Xwaylandauth.*` that `display_env`'s "newest auth file" rule then
picks for the REAL desktop).

THE RULE, held by smoke check 090s:

- an ENGINE a tool starts gets `engine_env()`: this module's Xvfb, never
  the session's display, unless the run names a reason for the real one;
- a CLIENT (a pygame App a tool drives) gets `headless_clients()`: SDL's
  dummy video and audio drivers, FORCED — a `setdefault` lost to a shell
  that exports `SDL_VIDEODRIVER=x11`, which is what dev:CLAUDE.md's live recipe
  says to export;
- the real desktop is `--real-desktop REASON` on the command line, or
  `ORIONLAYER_REAL_DESKTOP=<reason>` in the environment; a flag without a
  reason is refused, and every use prints the reason for the progress file.

The engine's sound goes to SDL's dummy audio driver on the virtual display
too: a run Data cannot see should not be one he hears.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

import workdirs

#: Display numbers tried for the live Xvfb, first free wins. Far from the
#: session's own (:0, :1) and from anything mutter hands out (:2, :3).
DISPLAYS = range(91, 100)
#: One screen large enough for the engine's 640x480 window at any origin.
GEOMETRY = "1920x1080x24"
STATE_DIR = workdirs.VDISPLAY      # work order 198
FLAG = "--real-desktop"
ENV_FLAG = "ORIONLAYER_REAL_DESKTOP"


class RealDesktopRefused(SystemExit):
    pass


def real_desktop_reason(argv=None, environ=None):
    """The reason given for the real desktop, or None for the virtual one.
    `--real-desktop REASON`, `--real-desktop=REASON` or the environment
    variable; a flag without a reason raises."""
    argv = sys.argv[1:] if argv is None else list(argv)
    environ = os.environ if environ is None else environ
    for i, a in enumerate(argv):
        if a == FLAG or a.startswith(FLAG + "="):
            reason = a.split("=", 1)[1] if "=" in a else (
                argv[i + 1] if i + 1 < len(argv) else "")
            if not reason.strip() or reason.startswith("--"):
                raise RealDesktopRefused(
                    f"{FLAG} needs a reason (it goes into the progress file)")
            return reason.strip()
    reason = (environ.get(ENV_FLAG) or "").strip()
    return reason or None


def strip_flag(argv):
    """argv without `--real-desktop [REASON]`, for a tool's own parser."""
    out, skip = [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == FLAG:
            skip = True
            continue
        if a.startswith(FLAG + "="):
            continue
        out.append(a)
    return out


def headless_clients(argv=None, environ=None, out=print):
    """Force SDL's dummy drivers for every pygame window this process
    opens — unless the run names a reason for the real desktop."""
    environ = os.environ if environ is None else environ
    reason = real_desktop_reason(argv, environ)
    if reason:
        out(f"REAL DESKTOP (client): {reason}")
        return reason
    environ["SDL_VIDEODRIVER"] = "dummy"
    environ["SDL_AUDIODRIVER"] = "dummy"
    return None


def _free(n):
    return not os.path.exists(f"/tmp/.X11-unix/X{n}") and \
        not os.path.exists(f"/tmp/.X{n}-lock")


def _state_file():
    return os.path.join(STATE_DIR, "xvfb.txt")


def running():
    """(display, pid, auth) of this module's Xvfb if it is alive, else None."""
    try:
        with open(_state_file(), encoding="utf-8") as fh:
            display, pid, auth = fh.read().split()
        os.kill(int(pid), 0)
        if os.path.exists(f"/tmp/.X11-unix/X{display.lstrip(':')}"):
            return display, int(pid), auth
    except (OSError, ValueError):
        pass
    return None


def ensure(out=print):
    """This module's Xvfb, started if needed: (display, pid, auth). Access
    by a private MIT cookie (`xauth`), so only this user's tools connect."""
    got = running()
    if got:
        return got
    if shutil.which("Xvfb") is None:
        raise SystemExit("Xvfb is not installed (xorg-server-xvfb) — the "
                         "virtual display cannot start")
    workdirs.makedirs(STATE_DIR, by="vdisplay")
    n = next((n for n in DISPLAYS if _free(n)), None)
    if n is None:
        raise SystemExit(f"no free display in :{DISPLAYS[0]}..:{DISPLAYS[-1]}")
    display = f":{n}"
    auth = os.path.join(STATE_DIR, "xauth")
    cookie = subprocess.run(["mcookie"], capture_output=True,
                            text=True).stdout.strip()
    subprocess.run(["xauth", "-f", auth, "add", display, ".", cookie],
                   check=True, capture_output=True)
    log = open(os.path.join(STATE_DIR, "xvfb.log"), "w")
    proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", GEOMETRY, "-nolisten", "tcp",
         "-auth", auth], stdin=subprocess.DEVNULL, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(50):
        if os.path.exists(f"/tmp/.X11-unix/X{n}"):
            break
        time.sleep(0.1)
    else:
        proc.kill()
        raise SystemExit(f"Xvfb {display} did not come up (log in {STATE_DIR})")
    with open(_state_file(), "w", encoding="utf-8") as fh:
        fh.write(f"{display} {proc.pid} {auth}\n")
    out(f"VIRTUAL DISPLAY: Xvfb {display} (PID {proc.pid}), {GEOMETRY}")
    return display, proc.pid, auth


def stop(out=print):
    got = running()
    if got:
        os.kill(got[1], 15)
        out(f"VIRTUAL DISPLAY: Xvfb {got[0]} (PID {got[1]}) stopped")


def session_auth(display=":0"):
    """The mutter Xwayland auth file that actually opens `display` — the
    newest that answers, not merely the newest (a headless mutter writes
    one too, work order 182)."""
    auths = sorted(glob.glob(f"/run/user/{os.getuid()}/.mutter-Xwaylandauth.*"),
                   key=os.path.getmtime, reverse=True)
    for a in auths:
        ok = subprocess.run(["xwininfo", "-root", "-display", display],
                            env=dict(os.environ, XAUTHORITY=a),
                            capture_output=True).returncode == 0
        if ok:
            return a
    return auths[0] if auths else None


def engine_env(reason=None, base=None, out=print):
    """The environment an ENGINE starts in: this module's Xvfb, or — with a
    reason — the real session's `:0` (dev:CLAUDE.md's three variables)."""
    env = dict(os.environ if base is None else base)
    env.pop("WAYLAND_DISPLAY", None)
    env["SDL_VIDEODRIVER"] = "x11"
    # Open fix 31: present without waiting for VSync (a patched engine).
    env["ORION2RE_NO_VSYNC"] = "1"
    # Open fix 43 (applied by work order 186): the engine's own window is
    # hidden from the start only when its starter asks — every OrionLayer
    # start does, the tools' and play.py's alike. F12 shows it on request.
    env["ORION2RE_HIDE_WINDOW"] = "1"
    if reason:
        out(f"REAL DESKTOP (engine): {reason}")
        env["DISPLAY"] = ":0"
        auth = session_auth(":0")
        if auth:
            env["XAUTHORITY"] = auth
        return env
    display, _pid, auth = ensure(out)
    env["DISPLAY"] = display
    env["XAUTHORITY"] = auth
    env["SDL_AUDIODRIVER"] = "dummy"
    return env


def is_session_display(env):
    """True when `env` would put a window into the user's own session."""
    d = env.get("DISPLAY", "")
    return d in (":0", ":1", ":0.0", ":1.0") or bool(env.get("WAYLAND_DISPLAY"))


def main(argv):
    """`python tools/vdisplay.py [status|start|stop]`."""
    cmd = argv[0] if argv else "status"
    if cmd == "start":
        ensure()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        got = running()
        print(f"Xvfb {got[0]} PID {got[1]}" if got else "no virtual display")
    else:
        print(main.__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
