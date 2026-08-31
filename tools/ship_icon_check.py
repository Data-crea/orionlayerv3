"""Report what each ship icon on the galaxy map actually resolves to.

    python tools/ship_icon_check.py [--seconds N]

Needs orion2re RUNNING with a game loaded on the galaxy map — unlike
star_icon_check.py, the answer depends on live state.

Prints, per icon: the node it points at, the ship behind that node,
the owner value, the kind that owner maps to, which sprite file is
actually used, and the native footprint at the current zoom. That is
the fast way to answer the two questions this screen keeps raising:

    "why is this fleet grey?"          -> owner column says None
    "which monster is that?"           -> owner column says 9..14

The owner is what identifies a monster. orion2_consts.h:528:

    8  antaran   9  guardian   10 amoeba
    11 crystal   12 dragon     13 eel        14 hydra

If a monster renders as a ship, its kind has no artwork and falls back
to the player sprite — the SPRITE column shows that explicitly rather
than leaving you to infer it from the picture.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import config, resources  # noqa: E402
from core import zoomtables as zt  # noqa: E402
from core.game_client import GameClient  # noqa: E402
from core.structs import ship as ship_struct  # noqa: E402
from screens.galaxy_map import ships as shi  # noqa: E402

OWNER_NAMES = {
    8: "antaran", 9: "guardian", 10: "amoeba",
    11: "crystal", 12: "dragon", 13: "eel", 14: "hydra",
}


def sprite_path(res, kind, step):
    """The file the renderer would load, or None."""
    rel = os.path.join("screens", "galaxy_map", "assets", "ships",
                       kind, f"{step}.png")
    return res.resolve(rel)


def describe_sprite(res, kind, step):
    """Which artwork actually gets drawn, and whether it is a fallback."""
    path = sprite_path(res, kind, step)
    if path:
        return f"{kind}/{step}.png", ""
    path = sprite_path(res, kind, 0)
    if path:
        return f"{kind}/0.png", "STEP FALLBACK"
    if kind != shi.PLAYER_KIND:
        path = sprite_path(res, shi.PLAYER_KIND, step)
        if path:
            return f"player/{step}.png", f"NO {kind.upper()} ARTWORK"
    return "-", "MISSING"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=float, default=3.0,
                    help="how long to wait for a snapshot")
    args = ap.parse_args()

    settings = config.load_settings()
    res = resources.Resources(settings.get("active_mods", []),
                              settings.get("skin", "default"))

    client = GameClient()
    conn = settings.get("orion2re", {}) or {}
    if not client.connect(conn.get("host", "localhost"),
                          conn.get("port", 17362),
                          subscribe_visual=False):
        print("orion2re is not reachable. Start it first:")
        print('  cd "$HOME/Master of Orion 2" && '
              "~/orion2re/out/build/Linux/linux-debug/orion2re")
        return 1

    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        client.poll()
        if getattr(client.state, "num_stars", 0):
            break
        time.sleep(0.05)

    state = client.state
    client.disconnect()

    icons = getattr(state, "ship_icons", None) or []
    raw_ships = getattr(state, "ships_raw", None) or []
    ships = [ship_struct.parse(r) for r in raw_ships
             if len(r) >= ship_struct.SIZE]

    map_max_x = getattr(state, "map_max_x", 0)
    zoom = zt.zoom_level(state.map_scale or 10,
                         zt.max_zoom_count(map_max_x),
                         len(getattr(state, "stars", None) or []),
                         zt.max_map_scale(map_max_x) or state.map_scale)

    print(f"screen  : {state.current_screen} "
          f"(0 = galaxy map)")
    print(f"zoom    : {zoom}   map_scale {state.map_scale}   "
          f"MAP_MAX_X {getattr(state, 'map_max_x', 0)}")
    print(f"ships   : {len(ships)}   icons: {len(icons)}")

    if state.current_screen != 0:
        print("\nNot on the galaxy map — ship icons are only built there.")
    if not icons:
        print("\nNo ship icons in this snapshot.")
        return 0

    node_map = shi.build_node_map(ships)
    exact = shi.owners_from_nodes(icons, ships)
    print(f"nodes   : {len(node_map)} rebuilt from _ship[]   "
          f"validation: {'PASSED' if exact is not None else 'FAILED'}")
    if exact is None:
        print("          (falling back to the per-star guess; icons at a "
              "star with\n           more than one owner will stay grey)")

    owners = shi.resolve_owners(icons, ships)

    print()
    print(f"{'#':>3} {'node':>5} {'ship':>5} {'star':>6} {'slot':>4} "
          f"{'x,y':>9} {'owner':>7} {'kind':>9} {'native':>7}  sprite")
    print("-" * 88)
    for i, (icon, owner) in enumerate(zip(icons, owners)):
        node = icon.node_idx
        ship = node_map[node] if 0 <= node < len(node_map) else -1
        kind = shi.kind_for_owner(owner)
        nw, nh = shi.native_size(kind, zoom)
        label = ("-" if owner is None
                 else OWNER_NAMES.get(owner, f"player {owner}"))
        sprite, flag = describe_sprite(res, kind or shi.PLAYER_KIND, zoom)
        print(f"{i:>3} {node:>5} {ship:>5} {icon.star_idx:>6} "
              f"{icon.stack_slot:>4} {icon.x:>4},{icon.y:<4} "
              f"{str(owner):>7} {label:>9} {nw:>3}x{nh:<3} {sprite} {flag}")

    unknown = sorted({o for o in owners if o is not None and o >= 8
                      and shi.kind_for_owner(o) is None})
    if unknown:
        print("\nOwner values with no kind mapping: "
              + ", ".join(str(u) for u in unknown))
    grey = sum(1 for o in owners if o is None)
    if grey:
        print(f"\n{grey} icon(s) with an unresolved owner — these render "
              f"neutral grey.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
