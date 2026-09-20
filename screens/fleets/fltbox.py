"""Drawing the game's own message box into the HD screen.

`core.gamebox` says WHICH box is up, where its pixels are and which
fields answer it. This puts them on the screen: an HD panel, the crop
of the game's own 640x480 pixels inside it, and a hit rect per button
taken from the box's own field rectangles mapped through the same
scale the crop is drawn at.

**THE CROP IS THE LIMITATION AND IT IS MEANT TO SHOW.** The box's text
is `H_Message_(n)` formatted with values the engine computed and it
reaches a client only as pixels, so HD cannot set it in its own font.
The replacement is open fix 29; until then this is a transcription of
the original's own rendering rather than an invention of ours, which is
the better of the two trades. Marked in `v3_projektstatus.md` and held
by a smoke check.
"""
import pygame

from core import gamebox, palette

#: Integer magnification only, and for the same reason `fltart.magnified`
#: gives: these are the game's own pixels and a smooth resample of them
#: is a picture of something the game never drew (decision 28).
MAX_SCALE = 6

DEFAULTS = {
    "box_panel": (18, 20, 26),
    "box_edge": (150, 170, 200),
}


def col(key):
    return palette.col("fleets", key, DEFAULTS[key])


def _framebuffer_surface(game_state):
    """The game's 640x480 picture as a surface, or None."""
    fb = getattr(game_state, "framebuffer", None)
    pal = getattr(game_state, "palette", None)
    if not fb or not pal or len(fb) < gamebox.NATIVE_W * gamebox.NATIVE_H:
        return None
    # THE SAME TWO STEPS `core/original_view.py` USES, and deliberately
    # not a second way of doing it: an 8-bit surface with the game's own
    # palette, filled from the raw indices through the surface buffer.
    surf = pygame.Surface((gamebox.NATIVE_W, gamebox.NATIVE_H), depth=8)
    surf.set_palette([(r, g, b) for r, g, b in pal])
    buf = surf.get_buffer()
    buf.write(bytes(fb[:gamebox.NATIVE_W * gamebox.NATIVE_H]))
    del buf
    return surf.convert()


def placement(screen, box):
    """`(scale, dest_rect)` for the box, centred in the window."""
    _x, _y, w, h = box.rect
    win_w, win_h = screen.app.win_w, screen.app.win_h
    scale = max(1, min(MAX_SCALE, int(min(win_w * 0.8 / w,
                                          win_h * 0.8 / h))))
    dw, dh = w * scale, h * scale
    return scale, pygame.Rect((win_w - dw) // 2, (win_h - dh) // 2, dw, dh)


def button_rects(screen):
    """`[(key, field, window rect)]` for the box that is up, or []."""
    view = getattr(screen, "_view", None)
    if view is None or not view.in_box:
        return []
    box = view.box
    scale, dest = placement(screen, box)
    bx, by, _w, _h = box.rect
    out = []
    for key, field in box.buttons():
        # A button whose field is the whole screen — the warning box's
        # single ESC catcher — is the PANEL, not a rectangle inside it.
        if (field.x, field.y, field.x_end, field.y_end) == (
                0, 0, gamebox.NATIVE_W - 1, gamebox.NATIVE_H - 1):
            out.append((key, field, dest))
            continue
        out.append((key, field, pygame.Rect(
            dest.x + (field.x - bx) * scale,
            dest.y + (field.y - by) * scale,
            (field.x_end - field.x + 1) * scale,
            (field.y_end - field.y + 1) * scale)))
    return out


def draw(surface, screen, game_state):
    """The box, or nothing. Returns True if it drew."""
    view = getattr(screen, "_view", None)
    if view is None or not view.in_box:
        return False
    box = view.box
    fb = _framebuffer_surface(game_state)
    piece = gamebox.crop(fb, box.rect)
    scale, dest = placement(screen, box)
    pad = max(2, int(round(6 * screen.layout.scale)))
    panel = dest.inflate(2 * pad, 2 * pad)
    surface.fill(col("box_panel"), panel)
    pygame.draw.rect(surface, col("box_edge"), panel,
                     max(1, int(round(2 * screen.layout.scale))))
    if piece is None:
        # NO FRAMEBUFFER, so no text — and an empty panel would be a
        # dialog with no question in it. Say which box it is and let
        # the buttons still work (decision 22).
        label = screen.style.render_text(
            box.name.upper(), max(10, int(dest.height * 0.12)),
            col("box_edge"))
        surface.blit(label, label.get_rect(center=dest.center))
        return True
    surface.blit(pygame.transform.scale(piece, dest.size), dest.topleft)
    return True
