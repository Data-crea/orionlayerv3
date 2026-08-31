#!/usr/bin/env python3
"""nebula_check — verify s_nebula offsets against verified star data.

s_nebula is 5 bytes. The candidate layout is x(i16) @0, y(i16) @2,
form(u8) @4. A hexdump alone cannot confirm this: any two bytes read
as int16 produce *some* number. What CAN confirm it is that the
candidate x/y land in the same coordinate space as the stars, whose
offsets are already verified (core/structs/star.py).

This script does that comparison numerically. For every nebula it
prints the candidate coordinates, checks them against the map bounds
reported by orion2re, and lists the nearest stars BY NAME.

Verification step (project lesson #1 — numeric, not visual):
  1. Run this with a game loaded.
  2. Look at the galaxy map in the game and note which star names the
     nebula actually sits on or next to.
  3. If those are the names this script prints as nearest, the x/y
     offsets are confirmed. If the script prints a completely
     different part of the galaxy, they are not.

The form byte cannot be confirmed with a single nebula — it needs a
galaxy with several nebulas of visibly different shapes. Until then
it stays unverified even if x/y check out.

Usage:
    python tools/nebula_check.py
    python tools/nebula_check.py --near 5
"""
import argparse
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core.game_client import GameClient  # noqa: E402

# Candidate layouts to evaluate. Each is (label, x_offset, y_offset).
# The first is the documented guess; the others exist so a wrong guess
# shows up as "some other layout fits the map bounds better".
CANDIDATES = [
    ("x@0 y@2 (documented guess)", 0, 2),
    ("x@1 y@3 (shifted by one)", 1, 3),
]


def fetch_state(host, port, timeout=10.0):
    """Connect and return the first usable STATE_SNAPSHOT."""
    client = GameClient()
    if not client.connect(host=host, port=port):
        print(f"Cannot reach orion2re at {host}:{port} — is the game "
              f"running with -DORION2RE_EXT=ON?")
        return None
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            client.poll()
            st = client.state
            if st and st.current_screen >= 0 and st.num_stars > 0:
                return st
            time.sleep(0.05)
    finally:
        client.disconnect()
    print(f"No usable snapshot within {timeout:.0f} s — load a game "
          f"first (the main menu has no map data).")
    return None


def star_bounds(stars):
    """Actual coordinate range the verified star records occupy."""
    xs = [s.x for s in stars]
    ys = [s.y for s in stars]
    return min(xs), max(xs), min(ys), max(ys)


def nearest_stars(stars, nx, ny, count):
    """Stars closest to (nx, ny), as (distance, star) pairs."""
    scored = [(((s.x - nx) ** 2 + (s.y - ny) ** 2) ** 0.5, s)
              for s in stars]
    scored.sort(key=lambda p: p[0])
    return scored[:count]


def report_candidate(label, raw, xo, yo, stars, gs, near):
    """Print one candidate layout and how well it fits."""
    x = struct.unpack_from("<h", raw, xo)[0]
    y = struct.unpack_from("<h", raw, yo)[0]
    lo_x, hi_x, lo_y, hi_y = star_bounds(stars)

    print(f"  {label}")
    print(f"    x = {x:6d}   y = {y:6d}")

    # Plausibility: does it land inside the area the stars occupy?
    margin_x = (hi_x - lo_x) * 0.25 or 50
    margin_y = (hi_y - lo_y) * 0.25 or 50
    inside = (lo_x - margin_x <= x <= hi_x + margin_x
              and lo_y - margin_y <= y <= hi_y + margin_y)
    verdict = "PLAUSIBLE — inside the star field" if inside \
        else "IMPLAUSIBLE — far outside the star field"
    print(f"    {verdict}")

    if gs.map_max_x or gs.map_max_y:
        in_map = (0 <= x <= gs.map_max_x and 0 <= y <= gs.map_max_y)
        print(f"    map bounds 0..{gs.map_max_x} x 0..{gs.map_max_y}: "
              f"{'inside' if in_map else 'OUTSIDE'}")

    if inside:
        print(f"    nearest stars — compare these against what the "
              f"nebula actually touches in game:")
        for dist, s in nearest_stars(stars, x, y, near):
            print(f"      {dist:7.1f} away  {s.name or '(unnamed)':<12} "
                  f"at ({s.x}, {s.y})")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--near", type=int, default=4,
                    help="how many nearby stars to list (default 4)")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    args = ap.parse_args()

    gs = fetch_state(args.host, args.port)
    if gs is None:
        return 1

    stars = gs.stars
    lo_x, hi_x, lo_y, hi_y = star_bounds(stars)
    print(f"Screen {gs.current_screen}, stardate {gs.stardate_str}")
    print(f"{len(stars)} stars spanning x {lo_x}..{hi_x}, "
          f"y {lo_y}..{hi_y}")
    print(f"map_scale={gs.map_scale}  "
          f"map_max=({gs.map_max_x}, {gs.map_max_y})")
    print(f"{gs.num_nebulas} nebula(s) reported\n")

    if not gs.nebulas_raw:
        print("No nebula records — this galaxy has none. Start a game "
              "with a larger galaxy to get nebulas to test against.")
        return 1

    for i, raw in enumerate(gs.nebulas_raw):
        hexpart = " ".join(f"{b:02x}" for b in raw)
        print(f"── nebula[{i}]  {hexpart}  " + "─" * 24)
        for label, xo, yo in CANDIDATES:
            report_candidate(label, raw, xo, yo, stars, gs, args.near)
        print(f"  byte @4 = {raw[4]}   (candidate form/type — needs "
              f"several nebulas of different shapes to confirm)\n")

    if len(gs.nebulas_raw) == 1:
        print("NOTE: only one nebula in this galaxy. x/y can be "
              "confirmed here, but the form byte cannot — it needs a "
              "galaxy with several visibly different nebulas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
