"""Every ffmpeg a tool starts, with a limit on its time and its output.

    import ffrun
    ffrun.run([... ffmpeg arguments, the output last ...], seconds=, max_bytes=)
    proc = ffrun.popen([...], seconds=, max_bytes=, stdin=subprocess.PIPE)

Data's rule (work order 243): a failed capture must not write on
unnoticed. Work order 201's combat lag measurement left
`~/claude/scratch/201/out.raw` at 974 GB, 95 % of `/home`, and nothing
said so until work order 242 looked at the disk.

Two limits, both always on:

- **Output size:** ffmpeg's own `-fs`, placed before the output (the
  last argument), so ffmpeg itself stops writing at the limit. A file
  output that reaches it raises `LimitReached` after the run: a cut-off
  film is a failed film, not a short one.
- **Time:** `run` passes `timeout=` (subprocess raises
  `TimeoutExpired` and kills ffmpeg); `popen` arms a timer that kills
  the process when the time is up.

The defaults fit every tool here today (the longest film is a few
minutes of 4K); a tool that needs more says so at its call. A check
holds every `ffmpeg` a tool starts to this module.
"""
import os
import subprocess
import threading

#: Wall time one ffmpeg may take.
DEFAULT_SECONDS = 1800
#: Bytes one ffmpeg may write to its output.
DEFAULT_BYTES = 8 * 1024 ** 3


class LimitReached(RuntimeError):
    """The output reached `max_bytes`: ffmpeg stopped writing there."""


def command(args, max_bytes=DEFAULT_BYTES):
    """`ffmpeg` + `args` with `-fs` before the output (the last argument)."""
    args = list(args)
    if not args:
        raise ValueError("ffmpeg needs an output")
    return ["ffmpeg", *args[:-1], "-fs", str(int(max_bytes)), args[-1]]


def _file_output(args):
    out = args[-1]
    return None if out in ("-", "pipe:", "pipe:1") or out.startswith(
        "pipe:") else out


def _check_size(args, max_bytes):
    out = _file_output(args)
    if out and os.path.isfile(out) and os.path.getsize(out) >= \
            int(max_bytes) * 0.999:
        raise LimitReached(f"ffmpeg stopped at {max_bytes} bytes: {out}")


def run(args, seconds=DEFAULT_SECONDS, max_bytes=DEFAULT_BYTES, **kwargs):
    """`subprocess.run` of ffmpeg with both limits."""
    done = subprocess.run(command(args, max_bytes), timeout=seconds, **kwargs)
    _check_size(args, max_bytes)
    return done


def popen(args, seconds=DEFAULT_SECONDS, max_bytes=DEFAULT_BYTES, **kwargs):
    """`subprocess.Popen` of ffmpeg with both limits; the timer is
    `proc.ffrun_timer` (cancelled when the process ends in time)."""
    proc = subprocess.Popen(command(args, max_bytes), **kwargs)

    def _expire():
        if proc.poll() is None:
            proc.kill()

    timer = threading.Timer(seconds, _expire)
    timer.daemon = True
    timer.start()
    proc.ffrun_timer = timer
    proc.ffrun_check = lambda: _check_size(args, max_bytes)
    return proc
