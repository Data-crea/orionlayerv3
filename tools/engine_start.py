#!/usr/bin/env python3
"""Start orion2re for a live run, or say why it would hang — work order 174 A.

    python tools/engine_start.py                 # checks, start, wait
    python tools/engine_start.py --check         # the checks alone
    python tools/engine_start.py --log PATH --timeout 60

**WHY THIS EXISTS.** Session-launched engines stopped after
`mox2: data space allocated` while Data's own start worked (139 E, 169
P1, 170 P1). 174 A found where and why (open fix 31):

- WHERE, from backtraces of hung starts: the game thread in
  `JIM::Draw_Logos_` waits, with no timeout, for a present
  (`video::Submit_Palette_` / `Publish_Off_Page_`); the main thread is
  in that present, `SDL_RenderPresent` with VSync on (platform.cpp:644,
  :1390), inside the NVIDIA GLX swap (`drmSyncobjTimelineWait`).
  `SDL_LogInfo` goes to stderr unbuffered, so the last line IS where it
  stopped.
- WHEN: a VSync present to a window the compositor is not drawing can
  wait forever. On 26 September a full-screen game covered the monitor
  and 8 of 60 counted starts hung; on 25 September the screen had most
  likely blanked and locked (300 s idle). The command, the environment
  variables, the parent process and an idle inhibitor made no
  difference; neither did another renderer or disabling explicit sync.
  Only not waiting for VSync did — open fix 31
  (`doc/ext_present_no_vsync.patch`, `ORION2RE_NO_VSYNC=1`), APPLIED by
  work order 175 on the local branch.

What this tool does about it:

1. sets `ORION2RE_NO_VSYNC=1` — open fix 31, applied since 175 (an engine
   without it ignores the variable);
2. RECOGNISES the hang by its signature — the log standing at "data
   space allocated" while, over 3 s of samples, the main thread waits
   in the GPU sync and the game thread on its condition — and starts
   again (up to `--retries`), stopping ONLY the PID it started. Not by
   time alone: the intro cinematic also holds the log at that line;
3. refuses while the screen is blanked or locked (the screensaver's own
   D-Bus answer), and starts the engine under `gnome-session-inhibit
   --inhibit idle` so the screen does not blank during the run — an
   inhibitor held by this run's process, gone when the engine exits, no
   setting changed (Data's configuration is not ours to change);
4. BACKS UP every file a run can write before the engine exists
   (`tools/liveguard.py`, work order 175) and says how to verify after;
5. refuses while another orion2re runs or the port is taken — found
   WITHOUT connecting (a bind test): an engine Data started is never
   connected to (174's precondition).

The three display variables are CLAUDE.md's, determined, never typed.
"""
import argparse
import glob
import os
import socket
import subprocess
import sys
import time

ENGINE = os.path.expanduser("~/orion2re/out/build/Linux/linux-debug/orion2re")
GAME_DIR = os.path.expanduser("~/Master of Orion 2")
PORT = 17362
READY = "ext: server started"


def display_env(base=None):
    """The environment a live run needs (CLAUDE.md): DISPLAY :0, the
    newest mutter Xwayland auth file, SDL's x11 driver."""
    env = dict(os.environ if base is None else base)
    env["DISPLAY"] = ":0"
    auths = sorted(glob.glob(f"/run/user/{os.getuid()}/.mutter-Xwaylandauth.*"),
                   key=os.path.getmtime, reverse=True)
    if auths:
        env["XAUTHORITY"] = auths[0]
    env["SDL_VIDEODRIVER"] = "x11"
    # Open fix 31: present without waiting for VSync (a patched engine).
    env["ORION2RE_NO_VSYNC"] = "1"
    return env


def parse_bool(reply):
    """gdbus's `(true,)` / `(false,)`; None for anything else."""
    reply = (reply or "").strip()
    if reply == "(true,)":
        return True
    if reply == "(false,)":
        return False
    return None


def parse_uint(reply):
    """gdbus's `(uint64 1234,)`; None for anything else."""
    reply = (reply or "").strip()
    if reply.startswith("(uint64 ") and reply.endswith(",)"):
        try:
            return int(reply[8:-2])
        except ValueError:
            return None
    return None


def _gdbus(dest, path, method):
    try:
        out = subprocess.run(["gdbus", "call", "--session", "--dest", dest,
                              "--object-path", path, "--method", method],
                             capture_output=True, text=True, timeout=5)
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def screen_state():
    """{"blanked": True/False/None, "idle_ms": int/None}. None = could
    not ask, which is said, never read as 'fine'."""
    return {
        "blanked": parse_bool(_gdbus("org.gnome.ScreenSaver",
                                     "/org/gnome/ScreenSaver",
                                     "org.gnome.ScreenSaver.GetActive")),
        "idle_ms": parse_uint(_gdbus(
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor.GetIdletime")),
    }


def running_engines():
    """[(pid, ppid, started)] of every orion2re on this machine."""
    out = subprocess.run(["ps", "-o", "pid=,ppid=,lstart=", "-C", "orion2re"],
                         capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            rows.append((int(parts[0]), int(parts[1]), parts[2].strip()))
    return rows


def port_free(port=PORT):
    """True if nothing listens on `port` — by BINDING it, never by
    connecting (a connection would be a client in somebody's game)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def verdict(engines, free, screen):
    """(ok, [reasons]) — the decision, separate from asking, so the smoke
    suite can hold it without a desktop."""
    reasons = []
    for pid, ppid, started in engines:
        reasons.append(f"orion2re PID {pid} (parent {ppid}, started {started}) "
                       f"is running — not ours to connect to or stop")
    if not free:
        reasons.append(f"port {PORT} is taken")
    if screen.get("blanked") is True:
        reasons.append("the screen is blanked or locked: orion2re would wait "
                       "in its first logo frame (a VSync present the "
                       "compositor never completes) — wake and unlock the "
                       "screen, then start again")
    return (not reasons), reasons


def command(inhibit=True, engine=None):
    """The engine command, under an idle inhibitor when one exists."""
    cmd = [engine or ENGINE]
    if inhibit and _which("gnome-session-inhibit"):
        cmd = ["gnome-session-inhibit", "--inhibit", "idle", "--reason",
               "OrionLayer live run: orion2re needs the screen on"] + cmd
    return cmd


def _which(name):
    return any(os.access(os.path.join(p, name), os.X_OK)
               for p in os.environ.get("PATH", "").split(os.pathsep))


def _state(pid):
    out = subprocess.run(["ps", "-o", "stat=,%cpu=,wchan:32=", "-p", str(pid)],
                         capture_output=True, text=True).stdout.strip()
    return out or "gone"


def _engine_pid(launcher_pid, deadline):
    """The orion2re PID: the launcher itself, or its child under the
    inhibitor."""
    while time.time() < deadline:
        for pid, ppid, _ in running_engines():
            if pid == launcher_pid or ppid == launcher_pid:
                return pid
        time.sleep(0.2)
    return None


HANG_LINE = "mox2: data space allocated"
MAIN_WAIT = "drm_syncobj_array_wait_timeout"
GAME_WAIT = "futex_wait"


def thread_waits(pid):
    """{thread name: wait channel} of a running process."""
    out = {}
    try:
        for tid in os.listdir(f"/proc/{pid}/task"):
            try:
                with open(f"/proc/{pid}/task/{tid}/comm") as f:
                    name = f.read().strip()
                with open(f"/proc/{pid}/task/{tid}/wchan") as f:
                    out[name] = f.read().strip()
            except OSError:
                pass
    except OSError:
        pass
    return out


def is_hang(last_line, samples):
    """THE START HANG's signature (open fix 31): the log at "data space
    allocated" and, in every sample, the main thread in the GPU sync and
    the game thread on its condition. The intro cinematic holds the log
    at the same line and fails the samples."""
    return (last_line == HANG_LINE and len(samples) >= 3 and all(
        s.get("orion2re") == MAIN_WAIT and s.get("MOX2::main2_") == GAME_WAIT
        for s in samples))


def start(log_path, timeout=60, inhibit=True, out=print, retries=3,
          engine=None, guard=None):
    """Start, and start again after a recognised hang. `guard` is the
    folder the pre-run backup goes to (taken once, before the first
    attempt)."""
    for attempt in range(1, retries + 1):
        pid = _start_once(log_path, timeout, inhibit, out, engine,
                          guard if attempt == 1 else None)
        if pid != "hang":
            return pid
        out(f"start hang recognised (attempt {attempt} of {retries})")
    return None


def _start_once(log_path, timeout, inhibit, out, engine=None, guard=None):
    engines, free, screen = running_engines(), port_free(), screen_state()
    ok, reasons = verdict(engines, free, screen)
    out(f"screen: blanked={screen['blanked']} idle={screen['idle_ms']} ms")
    if not ok:
        for r in reasons:
            out("REFUSED: " + r)
        return None
    handle = open(log_path, "w")
    if guard:
        # THE BACKUP COMES FIRST (work order 175): every file the game or
        # OrionLayer can write during a run, copied and hashed, before an
        # engine exists that could write one. `liveguard verify` after.
        import liveguard
        man = liveguard.snapshot(guard)
        out(f"GUARD: {sum(1 for f in man['files'].values() if f)} files "
            f"backed up to {guard} — after the run: python "
            f"tools/liveguard.py verify {guard} [--restore]")
    proc = subprocess.Popen(command(inhibit, engine), cwd=GAME_DIR,
                            env=display_env(),
                            stdin=subprocess.DEVNULL, stdout=handle,
                            stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.time() + timeout
    pid = _engine_pid(proc.pid, deadline)
    while time.time() < deadline:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if READY in text:
            out(f"READY: orion2re PID {pid} (launcher {proc.pid}), log {log_path}")
            return pid
        if proc.poll() is not None:
            out(f"EXITED with {proc.returncode} before {READY!r}")
            return None
        if pid and time.time() - (deadline - timeout) > 10:
            last = (text.strip().splitlines() or [""])[-1]
            if last == HANG_LINE:
                samples = []
                for _ in range(6):
                    samples.append(thread_waits(pid))
                    time.sleep(0.5)
                if is_hang(last, samples):
                    out(f"HANG: PID {pid} waits in its first present "
                        f"(open fix 31); stopping it (ours)")
                    os.kill(pid, 15)
                    time.sleep(2)
                    return "hang"
        time.sleep(0.5)
    last = text.strip().splitlines()[-1:] or ["<empty log>"]
    out(f"TIMEOUT after {timeout} s: last line {last[0]!r}, state "
        f"{_state(pid) if pid else 'unknown'}; stopping PID {pid} (ours)")
    if pid:
        os.kill(pid, 15)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="checks only")
    ap.add_argument("--log", default=os.path.join(
        os.path.expanduser("~/orionlayer-fixtures"), "orion2re_live.log"))
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--no-inhibit", action="store_true")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--guard", default=None,
                    help="the pre-run backup folder (default: a new one "
                         "under ~/orionlayer-fixtures/live_guard/)")
    ap.add_argument("--no-guard", action="store_true",
                    help="no backup — only for a start that loads nothing")
    ap.add_argument("--engine", default=None,
                    help="another orion2re binary (a build with open fix 31)")
    args = ap.parse_args()
    if args.check:
        ok, reasons = verdict(running_engines(), port_free(), screen_state())
        print("OK to start" if ok else "\n".join("REFUSED: " + r for r in reasons))
        return 0 if ok else 1
    guard = None if args.no_guard else (args.guard or os.path.join(
        os.path.expanduser("~/orionlayer-fixtures"), "live_guard",
        time.strftime("%Y%m%d_%H%M%S")))
    return 0 if start(args.log, args.timeout, not args.no_inhibit,
                      retries=args.retries, engine=args.engine,
                      guard=guard) else 1


if __name__ == "__main__":
    sys.exit(main())
