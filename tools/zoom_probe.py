#!/usr/bin/env python3
"""zoom_probe — what the galaxy map's zoom does to the view origin.

Cursor-anchored zoom needs two facts about orion2re that no header
answers, because both live in the game's own input loop rather than
in a table:

  1. **What does a zoom step keep fixed?** `_cur_map_scale` changes,
     but `_cur_map_x/_cur_map_y` are the top-left of the visible
     slice, so the game must move them too. If it keeps the viewport
     CENTRE fixed, an anchored zoom is "zoom, then scroll by a known
     offset". If it keeps the top-left fixed, the correction is a
     different one. If it anchors on the selected star, there may be
     nothing to correct at all.

  2. **Can a client move the origin at all?** The Extension API sends
     ACTIVATE_FIELD, INJECT_KEY, INJECT_CLICK and CANCEL_FIELD, and
     none of them is "scroll the map". Whether the arrow keys move
     `_cur_map_x/_cur_map_y`, and by how much per press, decides
     whether an anchored zoom is implementable from outside at all.

The probe answers both from live data instead of from a theory. It
does not change anything permanently: every zoom-in is followed by a
zoom-out and every scroll by its opposite, and the closing summary
reports whether the origin came back to where it started.

Usage (game running with -DORION2RE_EXT=ON, a savegame loaded, the
galaxy map on screen):

    python tools/zoom_probe.py
    python tools/zoom_probe.py --steps 3      # deeper zoom sweep
    python tools/zoom_probe.py --no-scroll    # zoom questions only

Read the result, then write the finding into
`doc/v3_orion2re_index.md` — the probe is the second source, the
function in `mainscr.cpp` that moves the origin is the first.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core.game_client import GameClient          # noqa: E402
from core import mapcoords as mc                 # noqa: E402

SCREEN_GALAXY_MAP = 0
ZOOM_IN_FIELD = 8
ZOOM_OUT_FIELD = 9

# SDL keysyms for the arrow keys. pygame's constants are the same
# values, but this tool does not import pygame — it has to run
# without a display.
KEY_LEFT, KEY_RIGHT = 1073741904, 1073741903
KEY_UP, KEY_DOWN = 1073741906, 1073741905

SETTLE_S = 0.6          # generous: the game only republishes on tick


def view(state):
    """(map_x, map_y, map_scale) as a plain tuple."""
    return (state.map_x, state.map_y, state.map_scale)


def centre(state):
    """Galaxy coordinate at the centre of the visible slice.

    The native viewport is MAP_LEFT..MAP_RIGHT, so its centre sits at
    ((22 + 527) / 2, (22 + 421) / 2) in 640x480 space; running that
    back through the inverse transform gives the galaxy point the
    player is looking at.
    """
    nx = (mc.MAP_LEFT + mc.MAP_RIGHT) / 2
    ny = (mc.MAP_TOP + mc.MAP_BOTTOM) / 2
    ms = state.map_scale or mc.SCALE_UNIT
    return (round((nx - mc.MAP_ORIGIN) * ms / mc.SCALE_UNIT
                  + state.map_x, 1),
            round((ny - mc.MAP_ORIGIN) * ms / mc.SCALE_UNIT
                  + state.map_y, 1))


def wait_state(client, timeout=3.0):
    """Poll until a real STATE_SNAPSHOT has been parsed.

    `client.state` is never None — it starts as an empty GameState —
    so waiting on that would return the default record and report a
    scale of 0. `map_scale` is only non-zero once the game has
    published, which makes it the honest readiness flag.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        client.poll()
        if client.state.map_scale:
            return client.state
        time.sleep(0.02)
    return None


def settle(client, seconds=SETTLE_S):
    """Drain frames for a while and return the last state."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        client.poll()
        time.sleep(0.02)
    return client.state


def report(label, before, after):
    """One before/after line plus the derived reading."""
    bx, by, bs = before
    ax, ay, asc = after
    print(f"  {label}")
    print(f"    origin  ({bx}, {by}) scale {bs}"
          f"   ->   ({ax}, {ay}) scale {asc}"
          f"   delta ({ax - bx:+d}, {ay - by:+d})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    ap.add_argument("--steps", type=int, default=1,
                    help="zoom-in steps to sweep (default 1)")
    ap.add_argument("--no-scroll", action="store_true",
                    help="skip the arrow-key scroll probe")
    args = ap.parse_args()

    client = GameClient()
    if not client.connect(host=args.host, port=args.port):
        print(f"Cannot connect to orion2re at {args.host}:{args.port}")
        return 1

    state = wait_state(client)
    if state is None:
        print("No STATE_SNAPSHOT received.")
        return 1
    if state.current_screen != SCREEN_GALAXY_MAP:
        print(f"Screen is {state.current_screen}, not the galaxy map "
              f"({SCREEN_GALAXY_MAP}). Open the map and run again.")
        return 1

    start = view(state)
    print(f"Galaxy map, MAP_MAX {state.map_max_x}x{state.map_max_y}")
    print(f"Start: origin ({start[0]}, {start[1]}) scale {start[2]}, "
          f"centre {centre(state)}\n")

    # ── 1. What does a zoom step keep fixed? ──
    print("Zoom in:")
    for step in range(args.steps):
        before, before_c = view(state), centre(state)
        client.activate_field(ZOOM_IN_FIELD)
        state = settle(client)
        after, after_c = view(state), centre(state)
        report(f"step {step + 1}", before, after)
        if after[2] == before[2]:
            print("    scale did not change — already at maximum zoom, "
                  "or field 8 is not the zoom button here")
            break
        print(f"    centre  {before_c} -> {after_c}"
              f"   {'HELD' if before_c == after_c else 'MOVED'}")
        if before[:2] == after[:2]:
            print("    origin held: the game anchors the TOP-LEFT")

    print("\nZoom out (back to where we started):")
    for step in range(args.steps):
        before = view(state)
        client.activate_field(ZOOM_OUT_FIELD)
        state = settle(client)
        report(f"step {step + 1}", before, view(state))

    # ── 2. Can a client move the origin at all? ──
    if not args.no_scroll:
        print("\nArrow keys (does anything move the origin?):")
        for name, key, back in (("right", KEY_RIGHT, KEY_LEFT),
                                ("down", KEY_DOWN, KEY_UP)):
            before = view(state)
            client.inject_key(key)
            state = settle(client)
            after = view(state)
            report(name, before, after)
            if before[:2] == after[:2]:
                print("    no movement — this key does not scroll")
            else:
                dx = after[0] - before[0]
                dy = after[1] - before[1]
                print(f"    scroll step: ({dx}, {dy}) galaxy units "
                      f"at scale {after[2]}")
                client.inject_key(back)
                state = settle(client)

    end = view(state)
    print(f"\nEnd: origin ({end[0]}, {end[1]}) scale {end[2]}")
    if end == start:
        print("Restored to the starting view.")
    else:
        print("NOT restored — zoom or scroll manually before playing on.")

    client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
