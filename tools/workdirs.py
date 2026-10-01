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
"""
import os

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
