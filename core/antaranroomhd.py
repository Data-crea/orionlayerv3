"""The Antaran room in HD — work order 402 (turn popup kind 22, id 82).

TRANSCRIPTION `antaran_room_scene`: `ANTAROOM::Main_Antaran_Room_Screen`
(antaroom.cpp:26-80) fills the whole 640 x 480 screen with ANTAROOM.LBX's
file animation (`core/popupart.py`), prints ONE ANTARMSG.LBX message over it
at the bottom (`Draw_Main_Antaran_Room_Screen`, :14-24: the paragraph's left
edge 0x37 = 55, width 0x226 = 550, its bottom 0x1D6 - height = 470, centred
(alignment 2, bill.cpp:79-81), in the room's palette colour 255 with a
colour-250 outline), and ends on a click anywhere or any key (:56-70). HD
draws the picture as large as the window holds, its 4:3 kept (decision 28:
an integer magnification when one fits, else the smoothest the window
allows), on black, and the message in the same place in picture units.
The music (`Play_Streaming_Music(0x78)`, :23, :39) is the engine's.

Without the player's files (`tools/popup_art_extract.py`) `render` answers
False and the HUD text panel is drawn (`hud_turn_popup`, core/turnpopup.py),
as before this order. UNVERIFIED `antaran_room_live`: no
test save brings an Antaran attack, so the scene is checked against the
extracted files and the C++ only.
"""
import time

import pygame

from core import popupart

#: Native layout of the message (antaroom.cpp:21-22).
TEXT_X, TEXT_W, TEXT_BOTTOM = 0x37, 0x226, 0x1D6
#: A native text line (the paragraph font of the room, in picture pixels).
LINE_H, FONT_H = 20, 18


def fit(win, size):
    """The picture's rectangle in a window of `win`: centred, 4:3 kept."""
    k = min(win[0] / size[0], win[1] / size[1])
    w, h = max(1, round(size[0] * k)), max(1, round(size[1] * k))
    return pygame.Rect((win[0] - w) // 2, (win[1] - h) // 2, w, h)


def wrap(style, text, size, width, colour):
    """`text` broken into lines no wider than `width` (the paragraph the
    original lays out in `_Print_Paragraph_Bill`, a word at a time)."""
    lines, cur = [], ""
    for word in str(text).split():
        trial = word if not cur else cur + " " + word
        if cur and style.render_text(trial, size, colour).get_width() > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def render(surface, style, popup, now=None):
    """Draw the room over the whole window; False when it cannot (the
    player's pictures are not extracted), so the panel is drawn instead."""
    scene = popupart.room()
    if scene is None:
        return False
    now = time.monotonic() if now is None else now
    pic = scene.frame(now)
    win = surface.get_size()
    rect = fit(win, scene.size)
    surface.fill((0, 0, 0))
    surface.blit(pygame.transform.smoothscale(pic, rect.size)
                 if rect.size != pic.get_size() else pic, rect)
    text = popup.get("text")
    if text:
        k = rect.w / scene.size[0]
        size = max(10, round(FONT_H * k))
        light, dark = scene.colour(popupart.TEXT_INDEX), \
            scene.colour(popupart.OUTLINE_INDEX)
        lines = wrap(style, text, size, TEXT_W * k, light)
        step = round(LINE_H * k)
        y = rect.y + TEXT_BOTTOM * k - len(lines) * step
        for line in lines:
            img = style.render_text(line, size, light)
            shadow = style.render_text(line, size, dark)
            x = rect.x + (TEXT_X + TEXT_W / 2) * k - img.get_width() / 2
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(shadow, (round(x) + dx, round(y) + dy))
            surface.blit(img, (round(x), round(y)))
            y += step
    return True
