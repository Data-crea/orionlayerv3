#!/usr/bin/env python3
"""The battle's monster pictures, cut from Data's HD masters — work order 392.

    python tools/monster_battle_cut.py [--out DIR] [--only dragon,hydra]

The galaxy map draws a monster from its master (`ships/masters/<kind>.png`,
one 1536 x 1024 picture); the battle drew MONSTER.LBX's 59 x 59 sprite
(Data, 13 Nov 2026: "nicht mit den HD Bildern"). The battle takes a painted
picture as the stored drawing's size or a whole multiple of it (HD EXTENSION
`hd_painted`), `monster/<entry>_<frame>.png`, frame = 4 * stored direction
+ glow; a painted file without the other glow frames is made from its frame 0
(`cbpulse`), so ONE file per stored direction 0..4 is enough. The stored
directions are the sprite turned counter-clockwise in 22.5 degree steps from
facing right (measured: the Dragon's head right, up, at 0 and 4); the
masters are the stored direction 0 pose (head right), so direction k is the
master turned 22.5 * k degrees.

HD EXTENSION `monster_masters` (INVENTION of the cut, not of the original):
the master is scaled so its content box is as wide as the stored drawing's
direction 0 content box (measured from the game's own sprite under the
monster's own ramp, `CombatArt.monster_ramp`), centred on that box's centre,
and turned about it. Output at 8 x the drawing (472 x 472 for 59 x 59).
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import vdisplay  # noqa: E402
vdisplay.headless_clients()

from PIL import Image  # noqa: E402

#: master name -> (MONSTER.LBX entry, the monster's player index)
MONSTERS = {"amoeba": (20, 10), "crystal": (21, 11), "dragon": (22, 12),
            "eel": (23, 13), "hydra": (24, 14), "guardian": (7, 9)}
K = 8                       # output pixels per drawing pixel
ALPHA_FLOOR = 12            # as core.shipcut: the masters' soft halo
DEFAULT_MASTERS = os.path.expanduser("~/.config/orionlayer/mod/ships/masters")
DEFAULT_OUT = os.path.expanduser(
    "~/.config/orionlayer/mod/files/screens/combat/assets/gamedata/monster")


def content_box(img):
    """Bounding box of the pixels that count (alpha above the floor)."""
    a = img.getchannel("A").point(lambda v: 255 if v >= ALPHA_FLOOR else 0)
    return a.getbbox()


def cut(master, art, entry, player):
    """{stored direction: RGBA image at K x the drawing}."""
    import pygame
    surf = art.surface("monster", entry, 0, art.monster_ramp(player),
                       False, False)
    nb = surf.get_bounding_rect()
    w, h = surf.get_size()
    img = Image.open(master).convert("RGBA")
    a = img.getchannel("A").point(lambda v: v if v >= ALPHA_FLOOR else 0)
    img.putalpha(a)
    mb = content_box(img)
    k = (nb.w * K) / (mb[2] - mb[0])
    img = img.resize((round(img.width * k), round(img.height * k)),
                     Image.LANCZOS)
    cx, cy = (mb[0] + mb[2]) / 2 * k, (mb[1] + mb[3]) / 2 * k
    out = {}
    for d in range(5):
        # PIL turns counter-clockwise about `center`; the result is
        # expanded, so the content centre is found again by its box
        rot = img.rotate(22.5 * d, resample=Image.BICUBIC, expand=True,
                         center=(cx, cy))
        ang = math.radians(22.5 * d)
        # the content centre moves with the expanded canvas
        ex, ey = (rot.width - img.width) / 2, (rot.height - img.height) / 2
        dx, dy = cx - img.width / 2, cy - img.height / 2
        rx = rot.width / 2 + dx * math.cos(ang) + dy * math.sin(ang)
        ry = rot.height / 2 - dx * math.sin(ang) + dy * math.cos(ang)
        canvas = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
        tx = round((nb.x + nb.w / 2) * K - rx)
        ty = round((nb.y + nb.h / 2) * K - ry)
        canvas.alpha_composite(rot, (max(0, tx), max(0, ty)),
                               (max(0, -tx), max(0, -ty)))
        out[d] = canvas
        del ex, ey
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--masters", default=DEFAULT_MASTERS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    import pygame
    pygame.init()
    pygame.display.set_mode((10, 10))
    from screens.combat import cbart
    art = cbart.CombatArt()
    if not art.available:
        sys.exit("no extracted MONSTER.LBX: nothing to measure against")
    os.makedirs(a.out, exist_ok=True)
    only = [s for s in a.only.split(",") if s]
    for name, (entry, player) in MONSTERS.items():
        if only and name not in only:
            continue
        master = os.path.join(a.masters, f"{name}.png")
        if not os.path.isfile(master):
            print(f"  {name}: no master at {master}")
            continue
        for d, img in cut(master, art, entry, player).items():
            path = os.path.join(a.out, f"{entry}_{4 * d}.png")
            if os.path.exists(path):      # nothing is deleted outright
                os.replace(path, path + ".old")
            img.save(path)
        print(f"  {name}: entry {entry}, 5 directions -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
