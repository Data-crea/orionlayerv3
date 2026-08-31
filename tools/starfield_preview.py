"""Render the galaxy map star field to a PNG, without the game.

Judging density and dot size needs to be possible in one second, not
one game start. This composites `StarfieldLayer` over a background
image at a chosen size and writes the result.

    python tools/starfield_preview.py
    python tools/starfield_preview.py --count-scale 3 --dot 0.45
    python tools/starfield_preview.py --size 2400x1900 --out /tmp/sf.png

Defaults match the shipped configuration, so a bare run shows what
the game shows.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

from screens.galaxy_map import starfield  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GM = os.path.join(ROOT, "screens", "galaxy_map")
DEFAULT_BG = os.path.join(GM, "assets", "map_background.png")
DEFAULT_LAYOUT = os.path.join(GM, "layout.json")


def load_config():
    try:
        with open(DEFAULT_LAYOUT, "r", encoding="utf-8") as fh:
            return json.load(fh).get("starfield", {}) or {}
    except (OSError, ValueError) as exc:
        print("layout.json not readable (%s) — using module defaults"
              % exc.__class__.__name__)
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="2400x1896",
                    help="map box size in HD pixels, WxH")
    ap.add_argument("--background", default=DEFAULT_BG)
    ap.add_argument("--out", default="/tmp/starfield_preview.png")
    ap.add_argument("--count-scale", type=float)
    ap.add_argument("--dot", type=float, help="dot diameter in native px")
    ap.add_argument("--brightness", type=float)
    ap.add_argument("--clumping", type=float)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--no-background", action="store_true",
                    help="render on black, the way the original does")
    args = ap.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    pygame.init()
    pygame.display.set_mode((32, 32))

    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))
    if not args.no_background:
        if os.path.exists(args.background):
            bg = pygame.image.load(args.background).convert()
            surface.blit(pygame.transform.smoothscale(bg, (width, height)),
                         (0, 0))
        else:
            print("background not found: %s — rendering on black"
                  % args.background)

    cfg = load_config()
    for key, value in (("count_scale", args.count_scale),
                       ("dot_native", args.dot),
                       ("brightness", args.brightness),
                       ("clumping", args.clumping),
                       ("seed", args.seed)):
        if value is not None:
            cfg[key] = value

    layer = starfield.StarfieldLayer(cfg)
    native_px = width / float(starfield.NATIVE_MAP_W)
    layer.render(surface, (0, 0, width, height), native_px)

    pygame.image.save(surface, args.out)
    print("%d stars, dot %.2f native px = %.1f HD px, %dx%d -> %s"
          % (layer.star_count,
             layer._cfg["dot_native"],
             layer._cfg["dot_native"] * native_px,
             width, height, args.out))


if __name__ == "__main__":
    main()
