#!/usr/bin/env python3
"""Templates to paint a screen's frame over — work order 197 E (195's Q3).

    python tools/frame_template.py                    # every screen
    python tools/frame_template.py galaxy_map races   # these
    python tools/frame_template.py --to DIR           # elsewhere

Writes `<mod folder>/templates/frames/<screen>.png`: 3840x2160, see-through,
every box the screen places at that size outlined and named — placed by the
screen's own boxes and `Box.update_layout`, the code the screen draws with
(decision 5), so the template cannot disagree with the screen. The PNG
carries the screen's layout hash (`core.frameslot.layout_hash`) in its text
chunk `orionlayer-layout`.

To make a frame: paint over the template, keep the see-through parts
see-through, save it as `<mod folder>/frames/<screen>.png`. A painter that
drops PNG text chunks loses the hash: then put it in `<mod folder>/mod.json`
as `{"frames": {"<screen>": "<hash>"}}` — this tool prints every hash.
`core.frameslot` draws the frame only at 16:9 and only while the screen's
layout is the one it was painted for; a moved box makes a new hash, and the
old frame waits for a repaint.

NEVER INSIDE THE TREE: a target in the repository is refused.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vdisplay  # noqa: E402

vdisplay.headless_clients()

import pygame  # noqa: E402

from core import frameslot, resources, usermod  # noqa: E402
from core.box import load_boxes  # noqa: E402
from core.config import SCREENS_DIR, load_settings  # noqa: E402
from core.layout import Layout  # noqa: E402

OUTLINE = (255, 64, 200, 255)
LABEL = (255, 255, 255, 255)


def screens_with_boxes():
    return sorted(n for n in os.listdir(SCREENS_DIR)
                  if not n.startswith(("_", "."))
                  and os.path.isfile(os.path.join(SCREENS_DIR, n, "screen.py"))
                  and os.path.isfile(os.path.join(SCREENS_DIR, n, "boxes.json")))


def render(res, screen):
    """The template surface and its layout hash."""
    surf = pygame.Surface(frameslot.SIZE, pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    font = pygame.font.Font(None, 34)
    layout = Layout(*frameslot.SIZE)
    for box in load_boxes(res.screen_file(screen, "boxes.json"),
                          *frameslot.SIZE):
        box.update_layout(layout)
        if box.screen_rect is None:
            continue
        r = pygame.Rect(box.screen_rect)
        pygame.draw.rect(surf, OUTLINE, r, 3)
        surf.blit(font.render(str(box.name), True, LABEL), (r.x + 6, r.y + 4))
    return surf, frameslot.layout_hash(res, screen)


def save(surf, digest, path):
    """PNG with the hash in its text chunk (Pillow)."""
    from PIL import Image, PngImagePlugin
    raw = pygame.image.tobytes(surf, "RGBA")
    img = Image.frombytes("RGBA", surf.get_size(), raw)
    meta = PngImagePlugin.PngInfo()
    meta.add_text(frameslot.CHUNK, digest)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, pnginfo=meta)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("screens", nargs="*")
    ap.add_argument("--to", default=None)
    a = ap.parse_args(argv)
    out = os.path.abspath(a.to or os.path.join(usermod.mod_dir(),
                                               usermod.TEMPLATES, "frames"))
    if os.path.commonpath([out, ROOT]) == ROOT:
        sys.exit(f"refused: {out} is inside the tree — templates go to the "
                 f"player's mod folder or elsewhere")
    pygame.init()
    res = resources.init(load_settings())
    names = a.screens or screens_with_boxes()
    for name in names:
        surf, digest = render(res, name)
        path = os.path.join(out, f"{name}.png")
        save(surf, digest, path)
        print(f"{name:18s} {digest}  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
