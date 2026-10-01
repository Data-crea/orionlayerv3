"""Where the developer tools keep their files outside the tree — work order 198.

One root, one variable: `ORIONLAYER_WORK`, by default `~/claude`, the
workshop Claude Code works in on the maintainer's machine. Every working
file a live run, a measuring tool or a check writes or reads outside the
repositories is a path below it; nothing is created loose in `~/`.

    bundles/     frozen orion2re series and archives (`orion2re_bundle_*`)
    clones/      throw-away player and developer clones for tests
    evidence/    evidence that stays on this machine (orders up to 193;
                 since 189 the store's `evidence/` takes new orders)
    extracted/   locally extracted original data — never in a repository
    fixtures/    the acceptance savegames and their README, incoming art
    live/        the live tools' state: `live_guard/`, `vdisplay/`
    logs/        engine logs of live starts
    scratch/     temporary, may be emptied at any time
    _to_delete/  quarantine before anything is deleted

`ORIONLAYER_FIXTURES` still names another fixtures folder, as before.
A player never needs any of this: `play.py` logs to `~/.cache/orionlayer/`.

A tool creates its folders through `makedirs`, which writes a line into
`CREATED_LOG` whenever that creates a NEW ENTRY AT THE TOP OF `~/` — the
run's own record of what it left there (work order 199). The smoke suite
fails on such an entry until Data has accepted it (dev:tools/home_check.py);
an entry nobody logged stays a warning, because it may be Data's own.
"""
import os
import time

ROOT = os.path.expanduser(os.environ.get("ORIONLAYER_WORK", "~/claude"))


def path(*parts):
    """A path below the workshop root."""
    return os.path.join(ROOT, *parts)


BUNDLES = path("bundles")
CLONES = path("clones")
EVIDENCE = path("evidence")
EXTRACTED = path("extracted")
FIXTURES = os.path.expanduser(os.environ.get("ORIONLAYER_FIXTURES")
                              or path("fixtures"))
LIVE = path("live")
LIVE_GUARD = path("live", "live_guard")
VDISPLAY = path("live", "vdisplay")
LOGS = path("logs")
SCRATCH = path("scratch")
TO_DELETE = path("_to_delete")
CREATED_LOG = path("logs", "home_created.txt")


def log_created(name, by, log=CREATED_LOG):
    """Record that this run created `name` at the top of `~/`."""
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{name}\t{time.strftime('%Y-%m-%d %H:%M:%S')}\t{by}\n")


def makedirs(folder, by="a tool", home=None, log=CREATED_LOG):
    """`os.makedirs(folder, exist_ok=True)`, logging a new top-level entry
    of `~/` it creates on the way (see the module's last paragraph)."""
    home = os.path.abspath(home or os.path.expanduser("~"))
    rel = os.path.relpath(os.path.abspath(folder), home)
    top = None if rel == "." or rel.startswith("..") else rel.split(os.sep)[0]
    new = top is not None and not os.path.lexists(os.path.join(home, top))
    os.makedirs(folder, exist_ok=True)
    if new:
        log_created(top, by, log)
    return folder
