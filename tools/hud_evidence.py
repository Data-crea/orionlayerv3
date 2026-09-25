#!/usr/bin/env python3
"""Renders of every HD screen in the HUD style, for Data to look at.

    python tools/hud_evidence.py                     # all, 3 sizes
    python tools/hud_evidence.py galaxy_map --size 1920x1080
    python tools/hud_evidence.py --mockups           # + side by sides

Work order 169's evidence: every screen at 1080p, 1440p and 2160p, and
the galaxy map and the colony summary beside Data's mockups. Written to
`~/orionlayer-fixtures/evidence/work_order_169/`. Pictures, not findings
— what they are FOR is the list in `doc/briefs/169-progress.md`.

**OFFLINE, AND SAYS SO.** No game runs here. Each screen gets the state
the smoke suite's own fixtures give it — a synthetic galaxy of forty
named stars, the colony preview's eight colonies (`colony_list_preview`),
the recorded GAME menu field list — or none, and a screen that needs a
live game to show content shows its empty state. Every file name says
`offline`, so no render can be mistaken for a live capture.
"""
import argparse
import json
import os
import random
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

OUT = os.path.expanduser("~/orionlayer-fixtures/evidence/work_order_169")
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160)]
MOCKUPS = {"galaxy_map": os.path.join(ROOT, "doc", "briefs",
                                      "169-mockup-galaxy.png"),
           "colony_summary": os.path.expanduser(
               "~/Downloads/colony_screen.png")}

STAR_NAMES = ["Poculum", "Cephee", "Revati", "Zak", "Obelus", "Dante",
              "Thaur", "Inak", "Galileo", "Draconis", "Zin", "Hamete",
              "Goi", "Tond", "Hase", "Ascellus", "Habor", "Zhadoom",
              "Hammis", "Zib", "Gorgonis", "Beta Ceti", "Taq", "Lemuria",
              "Mirak", "Sal", "Kae", "Kadath", "Helios", "Orion",
              "Ivielda", "Tal", "Kyusho", "Lawdon", "Min", "Lurnis",
              "Hircus", "Castor", "Hali", "Sahu"]


def make_app(width, height):
    """The real screens, on an app-shaped host (colony_list_preview's
    pattern, generalised to every screen)."""
    pygame.init()
    pygame.display.set_mode((64, 64))
    from core import palette, resources
    from core.config import SCREENS_DIR, load_settings
    from core.dispatcher import Dispatcher
    from core.layout import Layout
    from core.screens_loader import register_all
    from core.style import StyleRenderer
    settings = load_settings()
    res = resources.init(settings)
    colors = res.load_json(f"assets/shared/skins/{res.skin}/colors.json",
                           {}) or {}
    palette.init(colors)

    class _Client:
        class state:
            fields = []

        def activate_field(self, fid):
            pass

        def inject_click(self, x, y):
            pass

        def inject_key(self, key):
            pass

        def send_raw(self, *a, **k):
            pass

    class _App:
        _fs_offset = None

        def __init__(self):
            self.win_w, self.win_h = width, height
            self.res = res
            self.colors = colors
            self.settings = settings
            self.layout = Layout(width, height)
            self.style = StyleRenderer(res.skin_dir(), res.font(), colors)
            self.screens_dir = SCREENS_DIR
            self.connected = False
            self.client = _Client()
            self.dispatcher = Dispatcher()
            self.user_settings = {}

    app = _App()
    register_all(app, app.dispatcher, res)
    return app


def galaxy_state():
    """Forty stars, a nebula and the player record the mockup shows."""
    from core.game_state import GameState, PLAYER_SIZE, STAR_SIZE
    from core.structs import star as st
    rng = random.Random(169)
    raws = []
    for i, name in enumerate(STAR_NAMES):
        r = bytearray(STAR_SIZE)
        r[0:len(name)] = name.encode()
        struct.pack_into("<hh", r, 15, 40 + (i % 8) * 88 + rng.randint(-20, 20),
                         40 + (i // 8) * 110 + rng.randint(-25, 25))
        r[19] = rng.randint(0, 2)
        struct.pack_into("<b", r, 20, 0 if i in (3, 9, 13, 14) else -1)
        r[22] = rng.randint(0, 5)
        struct.pack_into("<h", r, 160, -1)
        r[171] = 1
        raws.append(bytes(r))
    gs = GameState()
    gs.current_screen = 0
    gs.player_num = 0
    gs.map_scale, gs.map_max_x, gs.map_max_y = 15, 759, 600
    gs.stars = st.parse_all(raws)
    p = bytearray(PLAYER_SIZE)
    p[38] = 2
    struct.pack_into("<i", p, 50, 304)
    struct.pack_into("<h", p, 58, 47)
    struct.pack_into("<h", p, 60, 19)
    struct.pack_into("<h", p, 276, -11)
    gs.player_raw = [bytes(p)] + [bytes(PLAYER_SIZE)] * 7
    gs.nebulas_raw = [struct.pack("<hhb", 374, 170, 1)]
    gs.stardate = 35004
    return gs


def colony_state():
    import colony_list_preview as clp
    return clp._Snapshot(clp.COLONIES) if hasattr(clp, "COLONIES") else None


def game_menu_state(node="menu"):
    from core.game_state import GameState

    class _F:
        pass
    fix = json.load(open(os.path.join(ROOT, "tools", "game_menu_fields.json")))
    gs = GameState()
    gs.current_screen = 8
    fields = []
    for row in fix[node]:
        f = _F()
        (f.index, f.x, f.y, f.x_end, f.y_end, f.field_type, f.hotkey) = row
        fields.append(f)
    gs.fields = fields
    return gs


def stage(app, name):
    """Put `name` on screen with its offline state; return the state."""
    d = app.dispatcher
    if name in ("game_menu", "game_menu_settings"):
        d.switch_to("galaxy_map")
        d.active.update(galaxy_state())
        gs = game_menu_state("settings" if name.endswith("settings")
                             else "menu")
        # The settings record the suite's GAME menu fixture uses (070).
        from core.structs import settings as _set
        gs.settings_raw = bytes([1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0,
                                 0, 0, 0, 1, 50, 1, 49, 7]) + bytes(
                                     _set.SIZE - 22)
        d.update_from_game(gs)
        d.overlay.update(gs)
        return gs
    d.switch_to(name)
    gs = {"galaxy_map": galaxy_state, "colony_summary": colony_state}.get(
        name, lambda: None)()
    d.active.update(gs)
    return gs


def render(name, width, height):
    app = make_app(width, height)
    stage(app, name)
    surf = pygame.Surface((width, height))
    d = app.dispatcher
    d.active.render(surf)
    if d.overlay_name:
        d.screens[d.overlay_name].render(surf)
    return surf


def side_by_side(hd, mockup_path):
    from PIL import Image
    m = Image.open(mockup_path).convert("RGB")
    h = 1080
    m = m.resize((round(m.width * h / m.height), h), Image.LANCZOS)
    raw = pygame.image.tostring(hd, "RGB")
    a = Image.frombytes("RGB", hd.get_size(), raw).resize(
        (round(hd.get_width() * h / hd.get_height()), h), Image.LANCZOS)
    out = Image.new("RGB", (a.width + m.width + 20, h), (90, 200, 90))
    out.paste(a, (0, 0))
    out.paste(m, (a.width + 20, 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("screens", nargs="*")
    ap.add_argument("--size", help="WxH, default all three")
    ap.add_argument("--mockups", action="store_true")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--hue", type=float, default=None,
                    help="the HUD frame colour to render in (degrees); "
                         "file names then carry it")
    ap.add_argument("--sat", type=float, default=None,
                    help="the frame colour's saturation factor, 0..1")
    ap.add_argument("--bright", type=float, default=None,
                    help="the frame colour's brightness factor, 0.1..1.6")
    ap.add_argument("--tag", default=None,
                    help="a name for the colour in the file names")
    args = ap.parse_args()
    from core.hud import style as hudstyle
    hudstyle.set_tone(args.hue, args.sat, args.bright)
    tag = ("" if args.hue is None else f"_hue{int(args.hue):03d}")
    if args.tag:
        tag = f"_{args.tag}"
    os.makedirs(args.out, exist_ok=True)
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else SIZES)
    names = args.screens or sorted(
        n for n in os.listdir(os.path.join(ROOT, "screens"))
        if os.path.isfile(os.path.join(ROOT, "screens", n, "screen.py"))
        and not n.startswith("_"))
    for name in names:
        for w, h in sizes:
            surf = render(name, w, h)
            path = os.path.join(args.out,
                                f"{name}_{w}x{h}{tag}_offline.png")
            pygame.image.save(surf, path)
            print(path)
            if args.mockups and (w, h) == (3840, 2160) and name in MOCKUPS \
                    and os.path.exists(MOCKUPS[name]):
                sbs = side_by_side(surf, MOCKUPS[name])
                p = os.path.join(args.out, f"{name}_beside_mockup_offline.png")
                sbs.save(p)
                print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
