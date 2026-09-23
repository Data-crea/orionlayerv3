#!/usr/bin/env python3
"""Frame by frame: does the window show the GAME's picture on entry?

    python tools/entry_glimpse.py [slot] [entries]

Work order 166 part A. Data saw the original flash up when change mode
opens — the game's own picture, with a description on the left, before
the HD panel appears. This measures it before anything is changed.

**THE VERDICT IS A PIXEL, NOT A FLAG.** `main.App._showing_original()`
is recorded, but it is a flag, and work order 129 reported one as an
observation and was wrong. The independent test renders the game's own
picture onto a scratch surface with the PRODUCT'S OWN renderer and
compares the window against it inside the picture area.

The first version of this tool sampled the LETTERBOX BARS instead, on
the reasoning that `original_view.render` fills the window black before
blitting: it read "no glimpse" on every one of 275 frames while the
flag said 111. `core/fallbacknote.render` draws the reason OUTSIDE the
picture — in the bars (work order 139 D) — so the bars are not black
when the fallback is up. Kept in the docstring because a test that can
be defeated by something drawing where it samples is worth recognising
the next time.

One frame per record line, `App._handle_events` / `_update` / `_render`
exactly as `main` runs them, so what is recorded is what was drawn.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
import livesend  # noqa: E402
from livedrive import Run, close, hashes  # noqa: E402
from researchchangephases import (SCREEN_CHANGE, SCREEN_MAP,  # noqa: E402
                                  ensure_on_map, hd, leave_change,
                                  pair, panel_ready)
from screens.galaxy_map import mapboxes  # noqa: E402

FOLDER = "work_order_166"

#: How many frames to watch after the activation goes out, and how many
#: settled ones end the watch. Generous on purpose: this is the
#: measurement the bound in the fix will be taken FROM.
WATCH_FRAMES = 240
SETTLED = 30


def probe_points(app):
    """Sample points INSIDE the 4:3 picture area, in window coordinates.

    Inside, and that is the correction: the first version of this tool
    sampled the LETTERBOX bars and asked whether they were pure black,
    because `core/original_view.render` fills the window black before
    it blits. It read "no glimpse" on every frame while the flag said
    111 — `core/fallbacknote.render` draws the reason **outside the
    picture**, i.e. in the bars (work order 139 D), so the bars are not
    black when the fallback is up. A test that can be defeated by
    something drawing where it samples is not a test.
    """
    dst_x, dst_y, dst_w, dst_h, _s = app.original_view.placement(
        app.win_w, app.win_h)
    xs = [dst_x + dst_w // 5, dst_x + dst_w // 2, dst_x + 4 * dst_w // 5]
    ys = [dst_y + dst_h // 5, dst_y + dst_h // 2, dst_y + 4 * dst_h // 5]
    return [(x, y) for x in xs for y in ys]


def shows_picture(app, points):
    """True when the window IS the fallback view — compared, not asked.

    The game's own picture is rendered onto a scratch surface by the
    PRODUCT'S OWN renderer, at the same size, and the window is
    compared against it where the picture is. So the answer comes from
    pixels rather than from `_showing_original()`, which is a flag, and
    work order 129 reported a flag as an observation and was wrong.
    """
    if not points:
        return None
    scratch = pygame.Surface((app.win_w, app.win_h))
    app.original_view.render(scratch, app.layout)
    surf = app.surface
    return all(surf.get_at(p)[:3] == scratch.get_at(p)[:3] for p in points)


def frame_line(run, points, n):
    """One rendered frame, as a record line."""
    app, st = run.app, run.state
    screen = hd(run) if "research_change" in app.dispatcher.screens else None
    return {
        "frame": n,
        "screen": getattr(st, "current_screen", None),
        "fields": len(getattr(st, "fields", None) or []),
        "overlay": app.dispatcher.overlay_name,
        "active": app.dispatcher.active_name,
        "hd_state": getattr(screen, "state", None),
        "flag_showing_original": app._showing_original(),
        "shows_picture": shows_picture(app, points),
    }


def one_entry(run, index, points):
    """Enter change mode once, recording every frame from the send on."""
    spec = run.app.dispatcher.screens["galaxy_map"]._data.get(
        "research_window_field")
    field = mapboxes.live_field(getattr(run.state, "fields", None), spec)
    if field is None:
        raise livesend.WrongDialog(
            "no research window in the list on the wire — not the galaxy "
            "map's own list, whatever the game reports")
    frames = [frame_line(run, points, -1)]        # the frame before the send
    livesend.activate(run.app.client, field.index, screen=SCREEN_MAP,
                      shape=livesend.on_galaxy_map,
                      field_type=spec["field_type"], rect=spec["rect"],
                      label=f"research window (entry {index})")
    settled = 0
    for n in range(WATCH_FRAMES):
        run.pump(1)
        line = frame_line(run, points, n)
        frames.append(line)
        if (line["screen"] == SCREEN_CHANGE and line["hd_state"] == "ok"
                and not line["shows_picture"]):
            settled += 1
            if settled >= SETTLED:
                break
        else:
            settled = 0
    glimpse = [f for f in frames if f["shows_picture"]]
    if glimpse:
        surf = run.app.surface.copy()
        path = os.path.join(run.dir, f"entry{index}_settled.png")
        pygame.image.save(surf, path)
    print(f"  entry {index}: {len(frames)} frames, "
          f"{len(glimpse)} of them showing the GAME's picture"
          + (f" (frames {glimpse[0]['frame']}..{glimpse[-1]['frame']}, "
             f"screen {sorted({f['screen'] for f in glimpse})}, "
             f"hd_state {sorted({str(f['hd_state']) for f in glimpse})}, "
             f"fields {sorted({f['fields'] for f in glimpse})})"
             if glimpse else ""))
    panel_ready(run)
    leave_change(run)
    return frames


def main():
    slot = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    entries = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run = Run("A_entry_glimpse", folder=FOLDER)
    saves = hashes()
    run.pump(30)
    ensure_on_map(run)
    record = gameload.load_slot(run, slot)
    if not record["loaded"]:
        return 1
    points = probe_points(run.app)
    print(f"  picture samples at {run.app.win_w}x{run.app.win_h}: "
          f"{len(points)} points")
    before = pair(run)
    runs = []
    for i in range(1, entries + 1):
        runs.append(one_entry(run, i, points))
    after = pair(run)
    glimpses = [len([f for f in fr if f["shows_picture"]]) for fr in runs]
    print(f"\n  {entries} entries, frames showing the game's picture: "
          f"{glimpses}")
    print(f"  the run changed nothing: {before} -> {after}: "
          f"{before == after}")
    run.save_record({"slot": slot, "entries": entries,
                     "picture_points": points,
                     "glimpse_frames_per_entry": glimpses,
                     "frames": runs, "before": list(before),
                     "after": list(after), **close(run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
