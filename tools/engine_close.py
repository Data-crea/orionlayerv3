"""Close an engine or client this session did not start — work order 176.

The rule (Data's live permission, standing since work order 190): a leftover is closed, never
connected to — `tools/liveguard.py` backs up every file a run can write
first, then SIGTERM, a few seconds, SIGKILL only if it is still there, each
recorded. `python tools/engine_start.py --close-foreign` runs it; the code
lives here since work order 179 split it out of `engine_start.py`, which
had passed the 300-line guideline, so that file stays the start and its
refusals.
"""
import os
import signal
import subprocess
import time


def foreign_clients(root=None):
    """[(pid, command line, started)] of OrionLayer clients (`python
    main.py` run in this tree) — found by their working directory."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = subprocess.run(["ps", "-eo", "pid=,lstart=,args="],
                         capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 6)
        if len(parts) < 7 or "main.py" not in parts[6] or \
                int(parts[0]) == os.getpid():
            continue
        try:
            cwd = os.readlink(f"/proc/{parts[0]}/cwd")
        except OSError:
            continue
        if os.path.realpath(cwd) == os.path.realpath(root):
            rows.append((int(parts[0]), parts[6], " ".join(parts[1:6])))
    return rows


def _alive(pid):
    try:
        with open(f"/proc/{pid}/stat") as fh:
            return fh.read().split()[2] != "Z"
    except OSError:
        return False


def close_foreign(targets, guard, out=print, wait=5.0, game_dir=None,
                  root=None):
    """Work order 176: back up (liveguard), then SIGTERM, wait, SIGKILL only
    if still there. `targets` [(pid, command line, started)]. Returns
    [(pid, command line, started, how it ended)]. Never connects."""
    import liveguard
    if targets:
        man = liveguard.snapshot(guard, game_dir, root)
        out(f"backup before closing: {guard} "
            f"({sum(1 for f in man['files'].values() if f)} files)")
    record = []
    for pid, cmdline, started in targets:
        os.kill(pid, signal.SIGTERM)
        deadline = time.time() + wait
        while time.time() < deadline and _alive(pid):
            time.sleep(0.2)
        how = "ended on SIGTERM"
        if _alive(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            how = "SIGKILL after SIGTERM" + ("" if not _alive(pid)
                                             else " — STILL THERE")
        record.append((pid, cmdline, started, how))
        out(f"closed PID {pid} ({cmdline}, started {started}): {how}")
    return record


def _cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            return fh.read().replace(b"\0", b" ").decode().strip()
    except OSError:
        return "?"
