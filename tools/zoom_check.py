"""Report the zoom state of the live galaxy map, one line per poll.

    python tools/zoom_check.py [--seconds N]

Needs orion2re RUNNING on the galaxy map. Press + and - while this
runs and step through every zoom level; each change prints a row.

What it answers, and why the question exists:

MOX::_max_map_scale and _max_zoom_count are NOT serialized. Both are
recovered from MAP_MAX_X, on the strength of MAP_MAX_X/max_map_scale
being 50.6 for every galaxy size — measured from the FOUR stock sizes
in mapgen.cpp (506/10, 759/15, 1012/20, 1518/30). A community map at
Maximum size is a fifth value that was never part of that derivation,
and two behaviours hang off getting it right:

    star names    Print_Star_Names_ bails at Is_Extended_Max_Map_View_
                  (more than 72 stars AND map_scale == max_map_scale)
    black holes   Advance_Black_Hole_Animation_ only runs while
                  Star_Scale_Percent_ is 100 (i.e. map_scale <= 30)

So on an extended map both switch off at the widest view. That is
transcribed behaviour, not a bug — but only if max_map_scale is the
number the game actually uses. The MEASURED column is the check: the
largest map_scale the game will go to IS max_map_scale, and it has to
equal the DERIVED column. If it does not, MAP_MAX_X_PER_SCALE does not
hold for this galaxy size and the recovery needs a real source.

The ladder line shows the scale each zoom level should sit at
(Extended_Scale_For_Zoom_Level_, repeated halving). Compare it against
the scales the game reports as you zoom: a mismatch means
_extended_scale_for_zoom is not the function orion2re runs.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config  # noqa: E402
from core import zoomtables as zt  # noqa: E402
from core.game_client import GameClient  # noqa: E402


def row(state):
    """One line of derived zoom state, or None when unusable."""
    map_max_x = getattr(state, "map_max_x", 0) or 0
    scale = getattr(state, "map_scale", 0) or 0
    stars = len(getattr(state, "stars", None) or [])
    if not scale:
        return None

    derived = zt.max_map_scale(map_max_x)
    max_zoom = zt.max_zoom_count(map_max_x)
    zoom = zt.zoom_level(scale, max_zoom, stars, derived or scale)
    pct = zt.star_scale_percent(stars, scale)
    return {
        "stars": stars,
        "scale": scale,
        "map_max_x": map_max_x,
        "max_map_scale": derived,
        "max_zoom": max_zoom,
        "zoom": zoom,
        "extended": stars > zt.ORIGINAL_MAX_STARS,
        "star_px": zt.star_dimension(0, zoom, stars, scale),
        "pct": pct,
        "names": not zt.names_suppressed(stars, scale, derived or scale),
        "spin": zt.black_hole_animates(stars, scale),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=float, default=60.0,
                    help="how long to watch (zoom around while it runs)")
    args = ap.parse_args()

    settings = config.load_settings()
    client = GameClient()
    conn = settings.get("orion2re", {}) or {}
    if not client.connect(conn.get("host", "localhost"),
                          conn.get("port", 17362),
                          subscribe_visual=False):
        print("orion2re is not reachable. Start it first:")
        print('  cd "$HOME/Master of Orion 2" && '
              "~/orion2re/out/build/Linux/linux-debug/orion2re")
        return 1

    print("Zoom with + and -. Ctrl-C to stop.\n")
    header = ("  scale  zoom  star_px  scale%  names  spin")
    seen = set()
    first = None
    widest = 0
    deadline = time.monotonic() + args.seconds
    try:
        while time.monotonic() < deadline:
            client.poll()
            r = row(client.state)
            if r is None:
                time.sleep(0.1)
                continue
            if first is None:
                first = r
                print(f"stars         : {r['stars']}"
                      f"{'   EXTENDED (> 72)' if r['extended'] else ''}")
                print(f"MAP_MAX_X     : {r['map_max_x']}")
                print(f"max_map_scale : {r['max_map_scale']}  (derived)")
                print(f"max_zoom_count: {r['max_zoom']}  (derived)")
                if r["extended"] and r["max_map_scale"]:
                    ladder = [zt._extended_scale_for_zoom(
                        r["max_map_scale"], r["max_zoom"], lvl)
                        for lvl in range(r["max_zoom"] + 1)]
                    print("expected ladder: " + "  ".join(
                        f"zoom {i} = scale {s}"
                        for i, s in enumerate(ladder)))
                print()
                print(header)
            widest = max(widest, r["scale"])
            key = r["scale"]
            if key not in seen:
                seen.add(key)
                print(f"  {r['scale']:5d}  {r['zoom']:4d}  {r['star_px']:7d}"
                      f"  {r['pct']:5d}%  {str(r['names']):5s}"
                      f"  {r['spin']}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()

    if first is None:
        print("No snapshot with a map scale arrived — is a game loaded?")
        return 1

    print()
    print(f"widest scale seen: {widest}")
    derived = first["max_map_scale"]
    if widest and derived:
        if widest == derived:
            print("MEASURED == DERIVED — MAP_MAX_X_PER_SCALE holds here.")
        elif widest > derived:
            print(f"MEASURED {widest} > DERIVED {derived}: the recovery is "
                  f"WRONG for this galaxy size. Star names would switch off "
                  f"at scale {derived} instead of {widest}.")
        else:
            print(f"widest seen {widest} < derived {derived} — zoom all the "
                  f"way out and run again before drawing a conclusion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
