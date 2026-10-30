"""The text size, shown for a moment when Ctrl + mouse wheel changes it
(work order 356). Drawn over the HD screen by `main.App`; it lasts
`SHOW` seconds, shorter than the draw gate's idle time, so the frame that
removes it is drawn too (`core/drawgate`)."""
import time

import pygame

from core import fontscale, usersettings

SHOW = 0.9


class Toast:
    def __init__(self):
        self._until = 0.0

    def show(self, now=None):
        self._until = (time.monotonic() if now is None else now) + SHOW

    def live(self, now=None):
        return (time.monotonic() if now is None else now) < self._until

    def render(self, surface, style, now=None):
        if not self.live(now):
            return
        w, h = surface.get_size()
        text = f"Text size {round(fontscale.factor() * 100)} %"
        img = style.render_text(text, max(14, h // 45), (235, 240, 250))
        pad = img.get_height() // 2
        box = pygame.Surface((img.get_width() + 2 * pad,
                              img.get_height() + pad), pygame.SRCALPHA)
        box.fill((8, 12, 24, 215))
        box.blit(img, (pad, pad // 2))
        surface.blit(box, ((w - box.get_width()) // 2, h // 12))


def _toast(app):
    """The app's one toast, made on first use: `main.App` is at the 40 KB
    limit and carries no field for it."""
    toast = getattr(app, "_fs_toast", None)
    if toast is None:
        toast = app._fs_toast = Toast()
    return toast


def render(app):
    """Over the HD screen, while the toast lives."""
    toast = getattr(app, "_fs_toast", None)
    if toast is not None:
        toast.render(app.surface, app.style)


def wheel(app, event):
    """Ctrl + the mouse wheel is the player's text size: one step stored
    and applied at once (the file written when the value changed), the
    value shown for a moment. True when the event was ours; a wheel
    without Ctrl is left to the screens."""
    if not (pygame.key.get_mods() & pygame.KMOD_CTRL and event.y):
        return False
    step = fontscale.STEP if event.y > 0 else -fontscale.STEP
    if fontscale.set_factor(fontscale.factor() + step):
        app.user_settings.set(
            "font_scale", None if fontscale.factor() == fontscale.DEFAULT
            else fontscale.factor())
        usersettings.save(app.user_settings)
    _toast(app).show()
    return True
