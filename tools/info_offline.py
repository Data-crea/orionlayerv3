#!/usr/bin/env python3
"""The Info screen rendered OFFLINE from a save's own arrays — work order 175 D.

    python tools/info_offline.py                   # every page, four sizes
    python tools/info_offline.py --size 1920x1080 --mod DIR

Reads the save; writes PNGs under
`~/orionlayer-fixtures/evidence/work_order_175/info/`, every name carrying
`offline`. The save's: the players and the leaders
(`tools/leaders_offline.arrays`). Made here: the stardate (3502.4, the
reference fixture's own, from `tools/fixtures`), the field list (RETURN
only), which page is up and what is selected on it.

`--mod DIR` renders with DIR as the player's mod folder, so the demo text
mod of work order 175 can be seen replacing texts (`core/usermod`).
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

OUT = os.path.expanduser("~/orionlayer-fixtures/evidence/work_order_175/info")
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160), (2576, 1432)]
#: (file tag, page, extra state)
VIEWS = (("history", 0, {}), ("tech", 1, {"tech_tab": 1}),
         ("races", 2, {}), ("turns", 3, {}), ("reference", 4, {}),
         ("reference_category", 4, {"ref_mode": "category", "ref_ix": 7}),
         ("reference_howto", 4, {"ref_mode": "howto", "ref_ix": 213}))


def state(a):
    from core import game_state as gsm
    import fixtures
    from screens.info import infogeom as g
    gs = gsm.GameState()
    gs.current_screen, gs.player_num = g.GAME_SCREEN_ID, a["player"]
    gs.player_raw, gs.leaders_raw = a["players"], a["leaders"]
    gs.stardate = fixtures.FIXTURES["reference"]["stardate"]
    gs.num_players = sum(1 for r in a["players"] if r[1:2] != b"\0")
    f = gsm.FieldInfo()
    f.index = 1
    f.x, f.y, f.x_end, f.y_end = g.EXIT
    f.field_type, f.hotkey = g.TYPE_BUTTON, g.ESC
    gs.fields = [f]
    return gs


def render(a, size, page, extra):
    import hud_evidence as he
    app = he.make_app(*size)
    d = app.dispatcher
    d.switch_to("info")
    scr = d.active
    scr.update(state(a))
    scr.page = page
    for k, v in extra.items():
        setattr(scr, k, v)
    surf = pygame.Surface(size)
    scr.render(surf)
    return surf, scr


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--save", default=None)
    ap.add_argument("--size", default=None)
    ap.add_argument("--mod", default=None)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    import fixtures
    import leaders_offline
    from core import usermod
    path = args.save or os.path.join(fixtures.FIXTURE_DIR,
                                     fixtures.FIXTURE_FILES["reference"]
                                     ["file"])
    a = leaders_offline.arrays(path)
    if args.mod:
        usermod.init(True, root=args.mod)
    os.makedirs(args.out, exist_ok=True)
    tag = os.path.splitext(os.path.basename(path))[0]
    tag += "_MOD" if args.mod else ""
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else SIZES)
    for size in sizes:
        for name, page, extra in VIEWS:
            surf, _scr = render(a, size, page, extra)
            out = os.path.join(args.out, f"info_{name}_offline_{tag}_"
                                         f"{size[0]}x{size[1]}.png")
            pygame.image.save(surf, out)
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
