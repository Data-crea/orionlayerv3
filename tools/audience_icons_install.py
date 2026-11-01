"""Cut the diplomacy menu's icons out of the player's icon sheet — WO 359.

    python tools/audience_icons_install.py <sheet.png>

The sheet is a black ground with a divider on top and eight icons in two
columns (handshake, chain / scales, gift / arrows, swords / flag, door).
Each is cut out of its cell, the black turned into transparency (the glow
stays, as light over black), trimmed, and written to
`<mod folder>/files/screens/audience/assets/icons/<name>.png` — where the
audience's gold menu (`audeco`, HD EXTENSION `audience_gold_menu`) reads
them. Sheet proportions are measured, not scaled: the cells are fractions
of the sheet (1086 x 1448 for Data's sheet).
"""
import os
import sys

# Cutting pictures needs no window and no sound: never open one in the
# player's session (the check of the live runs holds every tool to this).
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import pygame  # noqa: E402

from core import usermod  # noqa: E402

REL = "screens/audience/assets/icons"
#: name -> (column 0/1 or None for the divider, row 0..3) in the sheet
CELLS = {"divider": (None, -1), "propose": (0, 0), "break": (1, 0),
         "demand": (0, 1), "gift": (1, 1), "exchange": (0, 2),
         "war": (1, 2), "surrender": (0, 3), "bye": (1, 3)}
#: the rows' vertical extent as fractions of the sheet's height
ROWS = ((0.115, 0.325), (0.325, 0.52), (0.52, 0.72), (0.72, 0.945))
DIVIDER = (0.01, 0.115)
FLOOR, FULL = 16, 44


def cut(sheet):
    w, h = sheet.get_size()
    out = {}
    for name, (col, row) in CELLS.items():
        y0, y1 = DIVIDER if col is None else ROWS[row]
        x0, x1 = (0, w) if col is None else (col * w // 2, (col + 1) * w // 2)
        cell = sheet.subsurface(pygame.Rect(x0, int(y0 * h), x1 - x0,
                                            int((y1 - y0) * h))).copy()
        px = pygame.surfarray.pixels3d(cell)
        peak = px.max(axis=2).astype("float32")   # light over black
        # The black ground of the sheet is not pure: its noise (a few
        # levels) must stay clear. Nothing below FLOOR is opaque, full
        # opacity from FULL, and the colour is kept AS IT IS: dividing it
        # out by the brightness (the first cut) brightened dim pixels into
        # an orange fog round the silver chain and over-saturated the gold.
        alpha = ((peak - FLOOR) * 255.0 / (FULL - FLOOR)).clip(0, 255)
        rgba = pygame.Surface(cell.get_size(), pygame.SRCALPHA)
        view = pygame.surfarray.pixels3d(rgba)
        view[:] = px
        pygame.surfarray.pixels_alpha(rgba)[:] = alpha.astype("uint8")
        del px, view
        rect = rgba.get_bounding_rect(min_alpha=24)
        out[name] = rgba.subsurface(rect).copy()
    return out


def install(path):
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    sheet = pygame.image.load(path)
    folder = os.path.join(usermod.mod_dir(), usermod.FILES, *REL.split("/"))
    os.makedirs(folder, exist_ok=True)
    for name, surf in cut(sheet).items():
        target = os.path.join(folder, name + ".png")
        pygame.image.save(surf, target)
        print(f"{name}: {surf.get_size()} -> {target}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    install(sys.argv[1])
