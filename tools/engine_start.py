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
   WITHOUT connecting (a bind test). **THE LIVE PERMISSION**, standing
   since work order 190 (Data; it replaced 176's "while Data does not
   play", which replaced 171's "never connect, never kill"): an engine or
   client this tool did not start may be closed, never connected to, and
   `--close-foreign` closes it — `liveguard.snapshot` first, then
   SIGTERM, a few seconds, SIGKILL only if it is still there — and prints
   PID, command line, start time and how it ended for the progress file.
   Such an engine is still NEVER connected to.

The three display variables are dev:CLAUDE.md's, determined, never typed —
and since work order 182 they are used only with `--real-desktop REASON`.
By default the engine starts on the private Xvfb of `tools/vdisplay.py`,
so a live run shows nothing in Data's session (and plays no sound there);
the screen checks and the idle inhibitor apply only to the real desktop.
"""
import argparse
import os
import socket
import subprocess
import sys
import time

import intro_skip  # work order 179: one key skips the intro
from engine_close import _cmdline, close_foreign, foreign_clients  # noqa: F401 (176)
import workdirs  # work order 198: logs and guards under ~/claude/

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from core import paths  # noqa: E402 — work order 229 D
from core import ports  # noqa: E402 — work order 440

#: The engine and the game folder: the environment, the player's own
#: settings, else this machine's defaults (`core/paths.py`).
ENGINE = paths.engine()
#: The engine option that turns its logging on in a release build (WO 438).
ENGINE_LOG_FLAG = "-log"
GAME_DIR = paths.game_dir()
#: The player's port. A run asks `ports.ext_port()` (work order 440: the
#: variable ORION2RE_EXT_PORT, open fix 133); this stays for the old name.
PORT = ports.DEFAULT_PORT
READY = "ext: server started"


def display_env(base=None):
    """The REAL desktop's environment (dev:CLAUDE.md): DISPLAY :0, the mutter
    Xwayland auth file that opens it, SDL's x11 driver. Used only with
    `--real-desktop REASON` since work order 182 — see `run_env`."""
    import vdisplay
    return vdisplay.engine_env("real desktop", base, out=lambda *_: None)


def run_env(reason=None, out=print, port=None, display=None, extra=None):
    """The environment an engine STARTS in (work order 182): the private
    Xvfb of `tools/vdisplay.py`, never Data's session — unless the run
    names a reason for the real desktop. And the player's language (work
    order 200 C, open fix 70): `core/lang.engine_env` from the user
    settings — English adds nothing."""
    import vdisplay
    env = vdisplay.engine_env(reason, out=out, display=display)
    # WO 440: the engine's Extension API port is the run's, set explicitly
    # (a variable inherited from a shell must not decide for a slot's run)
    if port is not None:
        env[ports.ENV_VAR] = str(port)
    env.update(extra or {})
    if os.environ.get("ORIONLAYER_ENGINE_SHOWN") == "1":
        # work order 260: the original ALONE, no client — its window shown
        # from the start (open fix 43 hides it only on its starter's word),
        # so it draws and presents as the game does without OrionLayer
        env.pop("ORION2RE_HIDE_WINDOW", None)
        out("ENGINE SHOWN: the window is not hidden (ORIONLAYER_ENGINE_SHOWN)")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    from core import lang, usersettings
    extra, gone = lang.engine_env(usersettings.load().data,
                                  paths.game_dir())
    if extra:
        out("LANGUAGE (engine): " + ", ".join(f"{k}={v}" for k, v in
                                               sorted(extra.items())))
    elif gone:
        out(f"LANGUAGE (engine): English — {', '.join(gone)} in neither the "
            f"game's folder nor a named one (python tools/language_files.py "
            f"FOLDER); OrionLayer's own words stay in the chosen language")
    env.update(extra)
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


def port_free(port=None):
    """True if nothing listens on `port` — by BINDING it, never by
    connecting (a connection would be a client in somebody's game). With
    SO_REUSEADDR, as the engine binds it (ext_server.cpp:49): a closed
    session's connection lingers in TIME-WAIT for about a minute, which
    the engine starts over, and a plain bind refused — play.py said "the
    game did not start" to a player starting again after closing (work
    order 214). A listening engine still refuses the bind. No `port`: the
    one `ports.ext_port()` names (work order 440)."""
    port = ports.ext_port() if port is None else port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def verdict(engines, free, screen, blanked_ok=False, port=None):
    """(ok, [reasons]) — the decision, separate from asking, so the smoke
    suite can hold it without a desktop. `blanked_ok` (work order 177,
    `--blanked-ok`): with open fix 31 applied (175) the engine presents
    without VSync, and a hang that still came would be recognised and
    started again below — so a blanked screen may be accepted, on
    request, and the start says so."""
    reasons = []
    for pid, ppid, started in engines:
        reasons.append(f"orion2re PID {pid} (parent {ppid}, started {started}) "
                       f"is running and was not started by this run — never "
                       f"connected to; close it with --close-foreign (work "
                       f"order 190's standing live permission)")
    if not free:
        reasons.append(f"port {ports.ext_port() if port is None else port} "
                       f"is taken")
    if screen.get("blanked") is True and not blanked_ok:
        reasons.append("the screen is blanked or locked: orion2re would wait "
                       "in its first logo frame (a VSync present the "
                       "compositor never completes) — wake and unlock the "
                       "screen, then start again")
    return (not reasons), reasons


def command(inhibit=True, engine=None, extra_args=()):
    """The engine command, under an idle inhibitor when one exists.

    `-log` (WO 438): orion2re v2.0.2's release builds print no log at all
    without it (src/main.cpp `logging_enabled`, startup_options.cpp's "log"
    option); the start-hang signature and READY are read off that log, so a
    release engine would time out at '<empty log>'. The Debug build logs
    anyway and accepts the flag. It is the LAST argument. `extra_args`
    (WO 440: a slot's `-game-dir FOLDER`) come before it."""
    # engine read now: play.py may just have set it
    cmd = [engine or paths.engine(), *extra_args, ENGINE_LOG_FLAG]
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


#: The start deadline. 150 s since work order 177: the original's logo and
#: intro sequence plays whenever no key or mouse button is down at start
#: (`JIM::Draw_Logos_`, jim.cpp:18-120) and takes 112.9 s every time —
#: measured in 11 of 82 starts in work order 176 — so 174's 60 s read a
#: normal start as a timeout. The intro is also NAMED while it plays (the
#: log at "data space allocated" without the hang's signature).
START_DEADLINE = 150
INTRO_SECONDS = 112.9

#: Engine logs of earlier starts kept beside a log under ~/claude/ (work
#: order 229 E); older ones go to ~/claude/_to_delete/engine_logs/.
KEEP_LOGS = 30

#: A player's earlier engine logs kept beside play.py's, as `<log>.1` (the
#: last start) to `<log>.5` (Data's decision, work order 262 answering 229
#: P1): a crash while playing stays readable after the next start. A
#: player's cache, not this project's working files, so the oldest is
#: dropped rather than moved to ~/claude/_to_delete/.
PLAYER_KEEP = 5


def _rotate_player(log_path):
    for n in range(PLAYER_KEEP, 0, -1):
        newer = f"{log_path}.{n - 1}" if n > 1 else log_path
        if os.path.exists(newer):
            os.replace(newer, f"{log_path}.{n}")
    return f"{log_path}.1"


def keep_previous(log_path, out=print):
    """Before a start overwrites `log_path`: under ~/claude/, the previous
    engine log moves to `engine_logs/<its time>_<name>` beside it, the
    newest KEEP_LOGS stay. A crash's log was lost to the next start (the
    224-227 crashes). A player's own log (play.py's) turns over in place,
    PLAYER_KEEP deep."""
    import shutil
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        return None
    root = os.path.realpath(workdirs.ROOT) + os.sep
    if not os.path.realpath(log_path).startswith(root):
        return _rotate_player(log_path)
    keep = os.path.join(os.path.dirname(log_path), "engine_logs")
    os.makedirs(keep, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S",
                          time.localtime(os.path.getmtime(log_path)))
    dest = os.path.join(keep, f"{stamp}_{os.path.basename(log_path)}")
    shutil.move(log_path, dest)
    old = sorted(os.listdir(keep))
    for name in old[:-KEEP_LOGS] if len(old) > KEEP_LOGS else []:
        bin_ = os.path.join(workdirs.TO_DELETE, "engine_logs")
        os.makedirs(bin_, exist_ok=True)
        shutil.move(os.path.join(keep, name), os.path.join(bin_, name))
    return dest


def start(log_path, timeout=START_DEADLINE, inhibit=True, out=print, retries=3,
          engine=None, guard=None, blanked_ok=False, intro=False,
          real_desktop=None, slot=None):
    """Start, and start again after a recognised hang. `guard` is the
    folder the pre-run backup goes to (taken once, before the first
    attempt). `real_desktop` is the REASON for Data's session; None (the
    default since work order 182) is the virtual display. `slot` (WO 440,
    the store's live-run slots): a dict with `port`, `display` ((display, auth)),
    `extra_env`, `extra_args`, `on_pid`, `start_lock`, `guard_kw` (the slot's own folder for the
    backup) and `known_pids` (engines of OTHER slots,
    which are not foreign); None is today's single run on the default port
    and the single Xvfb."""
    for attempt in range(1, retries + 1):
        pid = _start_once(log_path, timeout, inhibit, out, engine,
                          guard if attempt == 1 else None, blanked_ok, intro,
                          real_desktop, slot)
        if pid != "hang":
            return pid
        out(f"start hang recognised (attempt {attempt} of {retries})")
    return None


def _start_once(log_path, timeout, inhibit, out, engine=None, guard=None,
                blanked_ok=False, intro=False, real_desktop=None, slot=None):
    """One start. A slot's start holds the slot start lock from its engine
    check until its engine's PID is registered (`on_pid`), so a sibling
    that starts at the same moment sees this engine as known, never as a
    stranger (WO 440 review); the lock is released on every way out."""
    slot = slot or {}
    lock = slot.get("start_lock")
    if lock is not None:
        lock.acquire()
    try:
        return _start_once_locked(log_path, timeout, inhibit, out, engine,
                                  guard, blanked_ok, intro, real_desktop,
                                  slot)
    finally:
        if lock is not None:
            lock.release()


def _start_once_locked(log_path, timeout, inhibit, out, engine, guard,
                       blanked_ok, intro, real_desktop, slot):
    port = slot.get("port")
    # The session's screen matters only when the engine goes onto it: a
    # blanked desktop cannot hold up a present on the virtual display.
    screen = screen_state() if real_desktop else {"blanked": False,
                                                  "idle_ms": None}
    # a slot's run: engines of the other slots are no strangers; a stranger
    # on THIS run's port is still refused by the bind test
    # (a callable is asked again at every attempt: a sibling's engine may
    # have been registered since the last one)
    known = slot.get("known_pids") or ()
    known = set(known() if callable(known) else known)
    engines = [e for e in running_engines() if e[0] not in known]
    free = port_free(port)
    ok, reasons = verdict(engines, free, screen, blanked_ok, port)
    if real_desktop:
        out(f"screen: blanked={screen['blanked']} idle={screen['idle_ms']} ms")
    if blanked_ok and screen.get("blanked") is True:
        out("BLANKED SCREEN ACCEPTED (--blanked-ok): open fix 31 presents "
            "without VSync; a hang would be recognised and retried")
    if not ok:
        for r in reasons:
            out("REFUSED: " + r)
        return None
    workdirs.makedirs(os.path.dirname(os.path.abspath(log_path)),
                      by="engine_start")
    keep_previous(log_path, out)
    handle = open(log_path, "w")
    if guard:
        # THE BACKUP COMES FIRST (work order 175): every file the game or
        # OrionLayer can write during a run, copied and hashed, before an
        # engine exists that could write one. `liveguard verify` after.
        import liveguard
        man = liveguard.snapshot(guard, **slot.get("guard_kw", {}))
        out(f"GUARD: {sum(1 for f in man['files'].values() if f)} files "
            f"backed up to {guard} — after the run: python "
            f"tools/liveguard.py verify {guard} [--restore]")
    env = run_env(real_desktop, out, port, slot.get("display"),
                  slot.get("extra_env"))
    proc = subprocess.Popen(command(inhibit and bool(real_desktop), engine,
                                    slot.get("extra_args", ())),
                            cwd=paths.game_dir(), env=env,
                            stdin=subprocess.DEVNULL, stdout=handle,
                            stderr=subprocess.STDOUT, start_new_session=True)
    # Ctrl+C while waiting must not leave the engine behind: it lives in
    # its own session (start_new_session), so the terminal never reaches
    # it, and play.py enters its try/finally only after this returns a
    # pid. The orphan would hold its port (17362 by default) and refuse the next start.
    # Audit TD-02.
    pid = None
    try:
        deadline = time.time() + timeout
        intro_named = False
        skips = 0
        # Found by NAME (`running_engines`): a binary not called `orion2re` is
        # never found, the wait below never runs, and the TIMEOUT line must
        # still be printable (work order 194 met it with a renamed copy).
        text = ""
        pid = _engine_pid(proc.pid, deadline)
        if pid and slot.get("on_pid"):
            slot["on_pid"](pid)         # registered as OURS before READY
        if slot.get("start_lock") is not None:
            slot["start_lock"].release()
        while time.time() < deadline:
            with open(log_path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            if not intro and pid and HANG_LINE in text:
                skips = intro_skip.step(pid, text, env, skips, out)
            if READY in text:
                out(f"READY: orion2re PID {pid} (launcher {proc.pid}), log {log_path}")
                return pid
            if proc.poll() is not None:
                out(f"EXITED with {proc.returncode} before {READY!r}")
                return None
            if pid and time.time() - (deadline - timeout) > 10:
                last = (text.strip().splitlines() or [""])[-1]
                if last == HANG_LINE and (intro or skips == 0 or
                                          time.time() - (deadline - timeout) > 20):
                    samples = []
                    for _ in range(6):
                        samples.append(thread_waits(pid))
                        time.sleep(0.5)
                    if is_hang(last, samples):
                        out(f"HANG: PID {pid} waits in its first present "
                            f"(open fix 31); stopping it (ours)")
                        _terminate(pid)
                        return "hang"
                    if not intro_named:
                        out(f"INTRO: the original's logos and intro are playing "
                            f"(about {INTRO_SECONDS:.0f} s; not a hang) — waiting")
                        intro_named = True
            time.sleep(0.5)
        last = text.strip().splitlines()[-1:] or ["<empty log>"]
        out(f"TIMEOUT after {timeout} s: last line {last[0]!r}, state "
            f"{_state(pid) if pid else 'unknown'}; stopping PID {pid} (ours)")
        if pid:
            _terminate(pid)
        return None
    except BaseException:
        try:
            _terminate(pid or proc.pid)
        except OSError:
            pass
        raise


def _terminate(pid, wait=5.0):
    """SIGTERM the engine this run started, SIGKILL it when it is still
    there after `wait` seconds. A hang is a main thread stuck in a GL or
    DRM swap; SDL's SIGTERM handler only posts a quit event, which that
    thread never reads, so the old engine kept the port and the retry was
    refused by its own half-dead engine (WO 427; `engine_close` and
    `play.stop_engine` escalate the same way)."""
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        return
    end = time.time() + wait
    while time.time() < end:
        state = _state(pid)             # "S 0.0 ..." or "gone"
        if state == "gone" or state.startswith("Z"):
            return
        time.sleep(0.2)
    try:
        os.kill(pid, 9)
    except ProcessLookupError:
        return
    time.sleep(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="checks only")
    ap.add_argument("--log", default=os.path.join(
        workdirs.LOGS, "orion2re_live.log"))
    ap.add_argument("--timeout", type=int, default=START_DEADLINE)
    ap.add_argument("--no-inhibit", action="store_true")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--guard", default=None,
                    help="the pre-run backup folder (default: a new one "
                         "under ~/claude/live/live_guard/, workdirs.py)")
    ap.add_argument("--no-guard", action="store_true",
                    help="no backup — only for a start that loads nothing")
    ap.add_argument("--engine", default=None,
                    help="another orion2re binary (a build with open fix 31)")
    ap.add_argument("--blanked-ok", action="store_true",
                    help="start on a blanked or locked screen (open fix 31 "
                         "applied; work order 177) — said in the output")
    ap.add_argument("--intro", action="store_true",
                    help="let the original's logos and intro play (by "
                         "default one key skips them, as in the original; "
                         "work order 179)")
    ap.add_argument("--real-desktop", metavar="REASON", default=None,
                    help="start the engine in Data's session instead of the "
                         "virtual display (work order 182) — only with a "
                         "reason, which the progress file names")
    ap.add_argument("--close-foreign", action="store_true",
                    help="close engines and clients this tool did not start "
                         "(work order 176: backup first, SIGTERM, SIGKILL "
                         "only if needed; never connect) and exit")
    args = ap.parse_args()
    if args.real_desktop is not None and not args.real_desktop.strip():
        ap.error("--real-desktop needs a reason (the progress file names it)")
    if args.close_foreign:
        targets = [(pid, _cmdline(pid), started)
                   for pid, _ppid, started in running_engines()]
        targets += foreign_clients()
        if not targets:
            print("no engine or client running that this tool did not start")
            return 0
        guard = args.guard or os.path.join(
            workdirs.LIVE_GUARD, time.strftime("close_%Y%m%d_%H%M%S"))
        rec = close_foreign(targets, guard)
        return 0 if all("STILL" not in r[3] for r in rec) else 1
    if args.check:
        ok, reasons = verdict(running_engines(), port_free(), screen_state())
        print("OK to start" if ok else "\n".join("REFUSED: " + r for r in reasons))
        return 0 if ok else 1
    guard = None if args.no_guard else (args.guard or os.path.join(
        workdirs.LIVE_GUARD, time.strftime("%Y%m%d_%H%M%S")))
    return 0 if start(args.log, args.timeout, not args.no_inhibit,
                      retries=args.retries, engine=args.engine,
                      guard=guard, blanked_ok=args.blanked_ok,
                      real_desktop=(args.real_desktop or "").strip() or None,
                      intro=args.intro) else 1


if __name__ == "__main__":
    sys.exit(main())
