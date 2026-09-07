"""Which frame image the colony screen draws — and nothing else.

**THE PREVIEW FLAG SELECTS A SOURCE, NOT A CODE PATH.** The built
plate (`tools/frame_build.py`, decision 49) and the shipped artwork
are both one RGBA image stretched over the 1920x1080 reference area,
so `screen._scale_frame` and `screen._render_frame_image` never learn
which of the two they were handed. That is decision 5 in the form it
takes for assets rather than for geometry: one drawing routine, two
possible inputs. **If this ever needs a second drawing routine, the
switch is the wrong shape and the plate is not a frame.**

Its own module because the switch is its own concern and because
`screen.py` was 316 code lines before it and would have been 329
after — decision 6 says split rather than extend the exceptions list,
and this package is one file per concern already.

WHERE THE FLAG LIVES. `frame_preview` in `settings.json`, default
False, stated there and in `core.config.load_settings`'s fallback so
a clone with no settings file and a clone with one agree about what
"not configured" means. It is runtime state, so it does NOT go in
`boxes.json` — `Box.to_dict` serializes a fixed key set and would
drop it the first time the F5 editor saved (decision 37), and a
render toggle is not layout in any case.

WHICH PLATE. `core.box.closest_resolution` — decision 1's exact-then-
closest-by-area chain, called in its one home rather than copied —
over the sizes `layout_reference.json` declares. That file is what
`frame_build.py` and `frame_mask.py` read too, so "which sizes exist"
has one answer and not three.

AN ABSENT PLATE IS A STATE TO EXPLAIN. The plates are generated and
not committed, so a clone that has not run `tools/setup.py` has none.
That draws the shipped frame and logs the command that makes them,
the same shape as the missing help texts (decision 38) — never an
exception, and never a silently blank frame.
"""
import hashlib
import logging
import os

from core import box
from core.config import BASE_DIR

log = logging.getLogger("colony_summary.frame")

#: The generator, named in the one message that reports its absence.
BUILD_COMMAND = "python tools/frame_build.py"


def plate_resolutions(res, screen_name):
    """The sizes the built plates exist at, from their own source."""
    data = res.load_json(
        os.path.join("screens", screen_name, "layout_reference.json"),
        {}) or {}
    return data.get("_resolutions", [])


def frame_source(screen):
    """(path, note) — the frame image to load, and what to log.

    `note` is None when the flag is off, so the log says nothing at
    all in the shipped configuration.
    """
    cfg = screen._data.get("frame", {})
    shipped = screen.asset_path("assets", cfg.get("image", "frame.png"))
    if not screen.app.settings.get("frame_preview"):
        return shipped, None

    win = (screen.app.win_w, screen.app.win_h)
    key = box.closest_resolution(
        plate_resolutions(screen.app.res, screen.SCREEN_NAME), *win)
    path = (screen.asset_path("assets", "frames", f"frame_{key}.png")
            if key else None)
    if not path:
        return shipped, (
            f"frame_preview is on and no built plate is present "
            f"(wanted {win[0]}x{win[1]}); drawing the shipped frame. "
            f"Run: {BUILD_COMMAND}")

    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()[:16]
    return path, (
        f"PREVIEW: built plate {os.path.relpath(path, BASE_DIR)} "
        f"({key} for a {win[0]}x{win[1]} window), sha256 {digest}")


def resolve(screen):
    """The frame path, with the one log line this module owns.

    The decision and the report live together on purpose: a caller
    that picked the source and a caller that announced it would be
    two places to keep in step, and the announcement is the only way
    a screenshot can be matched to the build that made it.
    """
    path, note = frame_source(screen)
    if note:
        log.info("%s", note)
    return path
