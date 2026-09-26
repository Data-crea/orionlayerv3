#!/usr/bin/env python3
"""The Leaders screen rendered OFFLINE from a save's own arrays — work order 175.

    python tools/leaders_offline.py                        # the reference fixture
    python tools/leaders_offline.py --save ~/Master\\ of\\ Orion\\ 2/SAVE5.GAM
    python tools/leaders_offline.py --size 1920x1080 --out DIR

Reads the save; writes nothing but PNGs under
`~/orionlayer-fixtures/evidence/work_order_175/leaders/`, every name
carrying `offline` so no picture can be mistaken for a live capture.

WHAT IS THE SAVE'S AND WHAT IS MADE UP HERE:

  the save's    colonies, planets, stars, the 67 leaders, the players,
                the ships and MAP_MAX_X / MAP_MAX_Y, sliced in
                `SAVEGAME::Write_Game_State_`'s order (savegame.cpp:
                1367-1388) from the leader array `tools/leader_check`
                locates
  made here     the field list (`ldrgeom.field_shapes`, the smoke
                group's transcription), the OFFS block (a view state
                open fix 30 would report: the first star the player has
                a colony at, the player's biggest stack), the ship icons
                (one per stack at a star, `Set_Fltscrn_Small_Ship_Icon_
                XYs_`'s slot-0 rule with a 7 x 6 icon, flt.cpp:25-27;
                stacks in transit are left out) and the FSEL node table
                those icons point into; HD's pointer (`--scan`)

So the pictures show what HD DRAWS for a state; whether the game would be
in that state is the live test's question, not this tool's.
"""
import argparse
import os
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

OUT = os.path.expanduser(
    "~/orionlayer-fixtures/evidence/work_order_175/leaders")
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160), (2576, 1432)]
MOVABLE_BOX = 28              # 14 x int16, savegame.cpp:902-917
ICON_W, ICON_H = 7, 6


def arrays(path):
    """The save's arrays as the snapshot carries them, or SystemExit."""
    import leader_check as lc
    from core.structs import colony, leader, planet, player, ship, star
    blob = open(path, "rb").read()
    got = lc.arrays_from_save(blob, lc.herodata())
    if got is None or got[1] is None:
        raise SystemExit(f"{path}: no versioned leader array found")
    leaders, stars, ships = got
    k = lc.locate(blob, lc.herodata())
    n_col = struct.unpack_from("<h", blob, 605)[0]
    p = 607 + n_col * colony.SIZE
    colonies = [blob[607 + i * colony.SIZE: 607 + (i + 1) * colony.SIZE]
                for i in range(n_col)]
    n_pl = struct.unpack_from("<h", blob, p)[0]
    planets = [blob[p + 2 + i * planet.SIZE: p + 2 + (i + 1) * planet.SIZE]
               for i in range(n_pl)]
    assert p + 2 + n_pl * planet.SIZE + 2 + len(stars) * star.SIZE == k, \
        "the arrays before the leaders do not add up"
    q = k + leader.COUNT * leader.SIZE + 2
    players = [blob[q + i * player.SIZE: q + (i + 1) * player.SIZE]
               for i in range(8)]
    q += 8 * player.SIZE + 2 + len(ships) * ship.SIZE + 5 * MOVABLE_BOX + 10
    me, _scale, _zoom = struct.unpack_from("<hhh", blob, q)
    max_x, max_y = struct.unpack_from("<hh", blob, q + 7)
    return dict(leaders=leaders, stars=stars, ships=ships, colonies=colonies,
                planets=planets, players=players, player=me,
                map_max=(max_x, max_y))


def state(a, view, scan_icon=False):
    """A GameState for screen 29 with an OFFS block (see the docstring)."""
    from core import game_state as gsm
    from core import leaderskills as ls
    from core.structs import leader, ship as ship_struct, ship_icon, star
    from screens.leaders import ldrgeom as g, ldrmap, ldrpopup
    gs = gsm.GameState()
    gs.current_screen, gs.player_num = 29, a["player"]
    gs.leaders_raw, gs.ships_raw = a["leaders"], a["ships"]
    gs.stars = star.parse_all(a["stars"])
    gs.planets_raw, gs.colonies_raw = a["planets"], a["colonies"]
    gs.player_raw = a["players"]
    gs.map_max_x, gs.map_max_y = a["map_max"]
    gs.num_colonies = len(a["colonies"])
    ships = [ship_struct.parse(r) for r in a["ships"]]
    stacks = {}
    for i, s in enumerate(ships):
        if s.status < ship_struct.STATUS_STACK_SKIP:
            stacks.setdefault((s.location, s.x, s.y, s.owner), []).append(i)
    nodes, icons, slot = [], [], {}
    for key, members in stacks.items():
        head = len(nodes)
        nodes += members
        loc = key[0]
        if not 0 <= loc < len(gs.stars):
            continue                 # in transit — left out offline
        p = ldrmap.star_point(gs, loc)
        n = slot.get(loc, 0)
        slot[loc] = n + 1
        x, y = ((p[0] + 4, p[1] - ICON_H // 2 - 3) if n == 0
                else (p[0] - ICON_W, p[1] - 5 + (n - 1) * ICON_H))
        raw = struct.pack("<6h", 0, head, loc, min(n, 4), x, y)
        icon = ship_icon.parse(raw)
        icon.set_derived("owner", key[3] if 0 <= key[3] < 15 else None)
        icons.append((icon, members))
    gs.ship_icons = [i for i, _m in icons]
    gs.fleet_selection = {"stack": -1, "ships": nodes,
                          "selected": [False] * len(nodes), "chain": []}
    recs = leader.parse_all(a["leaders"])
    me = gs.player_num
    rows = ls.captain_id_list(recs, me, view)
    mine = [(len(m), i) for i, (ic, m) in enumerate(icons)
            if ships[m[0]].owner == me]
    stack_icon = max(mine)[1] if mine else None
    star_shown = next((i for i in range(len(gs.stars))
                       if me in ldrmap.colony_owners(gs, gs.stars[i])), -1)
    grid = icons[stack_icon][1] if stack_icon is not None else []
    gs.officer_screen = {
        "view": view, "mode": -1, "selected": -1, "scanned": -1,
        "star_displayed": star_shown, "star_chosen": star_shown,
        "n_officers": len(rows), "id_list": rows + [-1] * (4 - len(rows)),
        "stack": 0 if grid else -1,
        "head_node": icons[stack_icon][0].node_idx if grid else -1,
        "first_row": 0, "picked_icon": -1, "scanned_big": -1,
        "scanned_small": -1, "scanned_star": -1, "popup_leader": -1,
        "popup_state": -1, "ship_idx": grid, "ship_selected":
        [False] * len(grid)}
    pool = ls.leaders_for_hire(recs, me, view)
    split = [tuple(len(x) for x in ldrpopup.split_skills(recs[i]))
             for i in rows]
    fields = []
    for rect, ftype, hk in g.field_shapes(len(rows), split, view, -1, pool):
        f = gsm.FieldInfo()
        f.index = len(fields) + 1
        f.x, f.y, f.x_end, f.y_end = rect
        f.field_type, f.hotkey = ftype, hk
        fields.append(f)
    gs.fields = fields
    scan = None
    if scan_icon and mine:
        scan = ("icon", stack_icon)
    elif star_shown >= 0:
        scan = ("star", star_shown)
    return gs, scan


def render(a, view, size, scan_icon=False):
    import hud_evidence as he
    app = he.make_app(*size)
    d = app.dispatcher
    gs, scan = state(a, view, scan_icon)
    d.switch_to("leaders")
    scr = d.active
    scr.update(gs)
    scr._scan = scan
    if view == 0 and gs.officer_screen["ship_idx"]:
        scr._big = 0
    surf = pygame.Surface(size)
    scr.render(surf)
    return surf, scr


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--save", default=None)
    ap.add_argument("--size", default=None)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    import fixtures
    path = args.save or os.path.join(fixtures.FIXTURE_DIR,
                                     fixtures.FIXTURE_FILES["reference"]
                                     ["file"])
    a = arrays(path)
    os.makedirs(args.out, exist_ok=True)
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else SIZES)
    tag = os.path.splitext(os.path.basename(path))[0]
    for size in sizes:
        for view, name, scan_icon in ((1, "colony_view", False),
                                      (0, "ship_view", True)):
            surf, _scr = render(a, view, size, scan_icon)
            out = os.path.join(args.out, f"leaders_{name}_offline_{tag}_"
                                         f"{size[0]}x{size[1]}.png")
            pygame.image.save(surf, out)
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
