#!/usr/bin/env python3
"""The Races screen rendered OFFLINE from a save's own arrays — work order 175 C.

    python tools/races_offline.py                  # the reference fixture
    python tools/races_offline.py --save FILE.GAM --size 1920x1080

Reads the save; writes PNGs under
`~/orionlayer-fixtures/evidence/work_order_175/races/`, every name carrying
`offline`. The save's: the eight players and the 67 leaders
(`tools/leaders_offline.arrays`). Made here: the field list — the main
mode's shape (`racesgeom.main_shape`) or, with `--who`, the WHO mode's —
and HD's pointer (over the first race's bar, or its panel in WHO mode).
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

OUT = os.path.expanduser("~/orionlayer-fixtures/evidence/work_order_175/races")
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160), (2576, 1432)]


def state(a, who=False):
    from core import game_state as gsm
    from screens.races import racesgeom as g, raceswire
    gs = gsm.GameState()
    gs.current_screen, gs.player_num = g.GAME_SCREEN_ID, a["player"]
    gs.player_raw, gs.leaders_raw = a["players"], a["leaders"]
    gs.num_players = sum(1 for r in a["players"] if r[1:2] != b"\0")
    players = raceswire.players_of(gs)
    n = len(raceswire.active_players(players, gs.player_num, gs.num_players))
    fields = []
    for rect, ftype, hk in (g.who_shape(n) if who else g.main_shape(n)):
        f = gsm.FieldInfo()
        f.index = len(fields) + 1
        f.x, f.y, f.x_end, f.y_end = rect
        f.field_type, f.hotkey = ftype, hk
        fields.append(f)
    gs.fields = fields
    return gs


def render(a, size, who=False):
    import hud_evidence as he
    from screens.races import racesgeom as g
    app = he.make_app(*size)
    d = app.dispatcher
    d.switch_to("races")
    scr = d.active
    scr.update(state(a, who))
    if who:
        scr._armed = "report"
        r = g.who_field(0)
    else:
        r = g.bar_field(0)
    scr._hover = ((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)
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
    import leaders_offline
    path = args.save or os.path.join(fixtures.FIXTURE_DIR,
                                     fixtures.FIXTURE_FILES["reference"]
                                     ["file"])
    a = leaders_offline.arrays(path)
    os.makedirs(args.out, exist_ok=True)
    tag = os.path.splitext(os.path.basename(path))[0]
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else SIZES)
    for size in sizes:
        for who in (False, True):
            surf, _scr = render(a, size, who)
            out = os.path.join(args.out, f"races_{'who' if who else 'main'}"
                                         f"_offline_{tag}_{size[0]}x"
                                         f"{size[1]}.png")
            pygame.image.save(surf, out)
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
