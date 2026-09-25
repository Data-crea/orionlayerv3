"""The evidence half of `tools/frame_ring_measure.py` (work order 168):
renders of every frame at the three window sizes, crops of the same ring
spots on every frame, and 2 x 2 views of the cockpit family. Pictures for
Data to look at, not findings; the numbers are the measuring script's.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from frame_ring_measure import RENDERS, load, render, render_size  # noqa: E402


#: Spots on the ring, in REFERENCE px (1920x1080), each (x, y, w, h):
#: the same four places on every frame, taken from its 2160p render.
SPOTS = {"top_left_corner": (0, 0, 160, 120),
         "top_edge_mid": (880, 0, 160, 80),
         "left_edge_mid": (0, 480, 100, 120),
         "bottom_right_corner": (1760, 960, 160, 120)}


#: The 2 x 2 views: the four cockpit frames (one style family), one
#: 90x60 ref px region each, top-left (x, y) in ref px.
COCKPIT = ("galaxy_map", "colony_summary", "planets", "fleets")
VIEWS = {"tl": (20, 10), "top": (900, 5)}


def evidence(results, folder):
    os.makedirs(folder, exist_ok=True)
    font = pygame.font.SysFont(None, 28)
    rows, tiles = [], []
    for res in results:
        surf, _rgb, _a = load(res["path"])
        for rw, rh in RENDERS:
            size = render_size(tuple(res["size"]), (rw, rh), res["popup"])
            pygame.image.save(render(surf, size), os.path.join(
                folder, f"render_{res['name'].replace(':', '_')}_{rw}x{rh}.png"))
        big = render(surf, render_size(tuple(res["size"]), (3840, 2160),
                                       res["popup"]))
        tile = pygame.Surface((480, 270))
        small = pygame.transform.smoothscale_by(big, 480 / 3840)
        tile.blit(small, ((480 - small.get_width()) // 2, 0))
        tiles.append((res["name"], tile))
        # The spots are window places; the popup is not a window frame.
        if not res["popup"]:
            rows.append((res["name"], big))
    contact = pygame.Surface((4 * 490, 2 * 310))
    for i, (name, tile) in enumerate(tiles):
        at = ((i % 4) * 490, (i // 4) * 310)
        contact.blit(tile, (at[0], at[1] + 36))
        contact.blit(font.render(name, True, (230, 230, 230)), (at[0] + 4, at[1] + 8))
    pygame.image.save(contact, os.path.join(folder, "00_contact_sheet.png"))
    for spot, (x, y, w, h) in SPOTS.items():
        for zoom, label in ((1, "100"), (2, "200")):
            cw, ch = w * 2 * zoom, h * 2 * zoom
            sheet = pygame.Surface((cw + 20, (ch + 40) * len(rows)))
            sheet.fill((90, 200, 90))
            for i, (name, big) in enumerate(rows):
                crop = big.subsurface(pygame.Rect(x * 2, y * 2, w * 2, h * 2)).copy()
                if zoom != 1:
                    crop = pygame.transform.scale(crop, (cw, ch))
                bg = pygame.Surface((cw, ch))
                bg.fill((200, 60, 200))
                bg.blit(crop, (0, 0))
                yy = i * (ch + 40)
                sheet.blit(font.render(name, True, (0, 0, 0)), (4, yy + 8))
                sheet.blit(bg, (10, yy + 34))
            pygame.image.save(sheet, os.path.join(
                folder, f"crop_{spot}_2160p_{label}pct.png"))
    cockpit = [(n, b) for n, b in rows if n in COCKPIT]
    for view, (x, y) in VIEWS.items():
        # 90x60 ref px = 180x120 at 2160p, shown at 200 %, 2 x 2.
        sheet = pygame.Surface((730, 490))
        sheet.fill((0, 200, 0))
        for i, (name, big) in enumerate(cockpit):
            crop = big.subsurface(pygame.Rect(x * 2, y * 2, 180, 120))
            at = ((i % 2) * 370, (i // 2) * 250)
            sheet.blit(pygame.transform.scale(crop, (360, 240)), at)
            sheet.blit(font.render(name, True, (0, 220, 0)), (at[0] + 4, at[1] + 4))
        pygame.image.save(sheet, os.path.join(folder, f"view_cockpit_{view}_2160p_200pct.png"))
