#!/usr/bin/env python3
"""Every dark box on every HD screen and popup — work order 174 B1.

    python tools/glass_inventory.py                  # table to stdout
    python tools/glass_inventory.py --json out.json --size 1920x1080

Analysis only; writes nothing into the tree.

**HOW A BOX IS FOUND, not listed by hand.** Each stage (a screen, a GAME
menu node, a popup) is rendered twice, once over a magenta and once over
a green background (`core.backgrounds.scaled` swapped). A pixel that is
the same in both is OPAQUE — something was drawn over the background
there. Of those, the DARK ones (every channel under `DARK`) are joined
into regions; a region counts as a BOX when it is large (`MIN_AREA`
reference px²) and flat (its colour's spread under `FLAT` levels), which
is what a fill is and a picture — portraits, planets, the map's art — is
not. Each box is then named by the draw call that covers it: the HUD
blocks and the other fill helpers are spied on while the stage renders
(`SOURCES`), and a box no spy covers is reported as "own fill" — a
screen drawing its own, which is what B2 must route through the block.
"""
import argparse
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

DARK = 48
FLAT = 6.0
MIN_AREA = 1500          # reference px² at 1920x1080
MAGENTA, GREEN = (255, 0, 255), (0, 255, 0)

#: The stages: every screen, every GAME menu node, and the popups an
#: offline state can open (`open_popup`).
GM_NODES = ("game_menu", "game_menu_settings", "game_menu_load",
            "game_menu_save", "game_menu_confirm", "game_menu_warning")
POPUPS = ("help_popup", "custom_race_message")


def stages():
    from core.config import SCREENS_DIR
    names = sorted(n for n in os.listdir(SCREENS_DIR)
                   if os.path.isfile(os.path.join(SCREENS_DIR, n, "screen.py"))
                   and not n.startswith("_") and n not in ("game_menu",))
    return names + list(GM_NODES) + list(POPUPS)


def _spies(record):
    """Wrap the fill helpers; `record(name, rect)` gets each call."""
    from core.hud import blocks, tables
    from core import listgrid
    real = {}

    def wrap(mod, name, label, rect_of):
        fn = getattr(mod, name)
        real[(mod, name)] = fn

        def w(*a, **k):
            r = rect_of(*a, **k)
            if r is not None:
                record(label, pygame.Rect(r))
            return fn(*a, **k)
        setattr(mod, name, w)

    def panel_rect(surface, rect, scale, lit=False, filled=True, **k):
        return rect if filled else None
    wrap(blocks, "panel", "hud.panel", panel_rect)
    wrap(blocks, "popup", "hud.popup", lambda s, r, sc, *a, **k: r)
    for n in ("table_header", "table_row"):
        wrap(tables, n, "hud." + n, lambda s, r, *a, **k: r)
    wrap(listgrid, "draw_row_fills", "listgrid.row_fills",
         lambda s, bands, cols, skip, *a, **k: None)
    return real


def _restore(real):
    for (mod, name), fn in real.items():
        setattr(mod, name, fn)


def render(stage_name, w, h, bg):
    import hud_evidence as he
    from core import backgrounds
    real_scaled = backgrounds.scaled

    def solid(screen_name, ww, hh):
        s = pygame.Surface((ww, hh))
        s.fill(bg)
        # What the panel glass shows through, as the real function sets it.
        backgrounds._current[0] = (("solid", bg, ww, hh), s)
        return s
    backgrounds.reset()
    backgrounds.scaled = solid
    calls = []
    real = _spies(lambda label, r: calls.append((label, r)))
    try:
        app = he.make_app(w, h)
        he.stage(app, stage_name)
        s = pygame.Surface((w, h))
        d = app.dispatcher
        d.active.render(s)
        if d.overlay_name:
            d.screens[d.overlay_name].render(s)
        return pygame.surfarray.array3d(s).transpose(1, 0, 2), calls
    finally:
        _restore(real)
        backgrounds.scaled = real_scaled
        backgrounds.reset()


def boxes(stage_name, w=1920, h=1080):
    from scipy import ndimage
    a, calls = render(stage_name, w, h, MAGENTA)
    b, _ = render(stage_name, w, h, GREEN)
    opaque = (a == b).all(axis=2)
    dark = opaque & (a.max(axis=2) < DARK)
    labels, n = ndimage.label(dark)
    k = (h / 1080.0) ** 2
    out = []
    for i, sl in enumerate(ndimage.find_objects(labels), start=1):
        mine = labels[sl] == i
        area = int(mine.sum())
        if area < MIN_AREA * k:
            continue
        px = a[sl][mine].astype(float)
        spread = float(px.std(axis=0).max())
        if spread > FLAT:
            continue
        y, x = sl
        rect = pygame.Rect(x.start, y.start, x.stop - x.start, y.stop - y.start)
        cover = [lab for lab, r in calls if r.inflate(8, 8).contains(rect)]
        src = cover[-1] if cover else "own fill"
        out.append({"rect": tuple(rect), "area": area, "source": src,
                    "colour": tuple(int(v) for v in px.mean(axis=0))})
    out.sort(key=lambda b: -b["area"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("stages", nargs="*")
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.split("x"))
    pygame.init()
    pygame.display.set_mode((64, 64))
    report = {}
    for name in args.stages or stages():
        report[name] = boxes(name, w, h)
        for bx in report[name]:
            print(f"{name:22s} {str(bx['rect']):26s} {bx['area']:8d}  "
                  f"{bx['colour']}  {bx['source']}")
        if not report[name]:
            print(f"{name:22s} no dark box")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
