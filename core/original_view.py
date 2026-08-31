"""
Original view — shows the orion2re framebuffer scaled up.

Converts 640x480x8bit indexed pixels + 256-color palette
into a pygame surface and scales it to fill the window.
Used as fallback for screens not yet rebuilt in HD.
"""
import pygame


class OriginalView:
    """Renders the original framebuffer in the window."""

    FB_W = 640
    FB_H = 480

    def __init__(self):
        self._surface_8bit = pygame.Surface(
            (self.FB_W, self.FB_H), depth=8
        )
        self._scaled = None
        self._last_size = (0, 0)
        self._dirty = True

    def update(self, framebuffer, palette):
        """Update the internal surface with new data.

        framebuffer: bytes, 640x480 pixels (8-bit indices)
        palette: list of (r, g, b) tuples, 256 entries
        """
        if framebuffer is None or palette is None:
            return
        if len(framebuffer) < self.FB_W * self.FB_H:
            return

        # Set palette
        pygame_palette = [(r, g, b) for r, g, b in palette]
        self._surface_8bit.set_palette(pygame_palette)

        # Copy pixel data
        buf = self._surface_8bit.get_buffer()
        buf.write(framebuffer[:self.FB_W * self.FB_H])
        self._dirty = True

    def render(self, target, layout):
        """Draw the framebuffer scaled into the window.

        Computes the largest 4:3 area and centers it.
        """
        tw = target.get_width()
        th = target.get_height()

        # 4:3 scaling with letterbox
        scale = min(tw / self.FB_W, th / self.FB_H)
        dst_w = int(self.FB_W * scale)
        dst_h = int(self.FB_H * scale)
        dst_x = (tw - dst_w) // 2
        dst_y = (th - dst_h) // 2

        # Only convert + rescale when framebuffer changed or size changed
        size_changed = (dst_w, dst_h) != self._last_size
        if self._dirty or size_changed or self._scaled is None:
            self._last_size = (dst_w, dst_h)
            rgb_surface = self._surface_8bit.convert()
            self._scaled = pygame.transform.smoothscale(
                rgb_surface, (dst_w, dst_h)
            )
            self._dirty = False

        target.fill((0, 0, 0))
        target.blit(self._scaled, (dst_x, dst_y))

        return dst_x, dst_y, dst_w, dst_h, scale

    def screen_to_640(self, screen_x, screen_y, target_w, target_h):
        """Window coordinate -> 640x480 coordinate.

        For click forwarding in original mode.
        Returns (x, y) in 640x480 or None if outside.
        """
        scale = min(target_w / self.FB_W, target_h / self.FB_H)
        dst_w = int(self.FB_W * scale)
        dst_h = int(self.FB_H * scale)
        dst_x = (target_w - dst_w) // 2
        dst_y = (target_h - dst_h) // 2

        rx = screen_x - dst_x
        ry = screen_y - dst_y

        if rx < 0 or ry < 0 or rx >= dst_w or ry >= dst_h:
            return None

        x = int(rx / scale)
        y = int(ry / scale)
        return (min(x, self.FB_W - 1), min(y, self.FB_H - 1))


    # ── Original-mode interaction (moved from main.py) ─────

    RADIO_BUTTON_TYPE = 1

    def find_field_at(self, fields, x, y):
        """Find field at (x, y) in 640x480 coordinates.

        Skips dummy (index 0), offscreen (5000, 5000) and radio
        button fields — radio buttons must go through INJECT_CLICK.
        """
        if not fields:
            return None
        for f in fields:
            if f.index < 1:
                continue
            if f.x >= 5000 or f.y >= 5000:
                continue
            if f.field_type == self.RADIO_BUTTON_TYPE:
                continue
            if f.x <= x <= f.x_end and f.y <= y <= f.y_end:
                return f.index
        return None

    def forward_click(self, client, screen_x, screen_y,
                      target_w, target_h):
        """Route a window click into orion2re (original mode).

        Buttons resolve to ACTIVATE_FIELD; everything else
        (radio buttons, map areas, empty space) is an
        INJECT_CLICK at the converted 640x480 position.
        """
        coords = self.screen_to_640(screen_x, screen_y,
                                    target_w, target_h)
        if not coords:
            return
        field_id = self.find_field_at(client.state.fields, *coords)
        if field_id:
            client.activate_field(field_id)
        else:
            client.inject_click(*coords)

    def render_status_bar(self, surface, style, colors,
                          state, screen_name, render_mode):
        """Mode/screen/stardate info line at the bottom edge."""
        info = (f"[{render_mode.upper()}]  screen: {screen_name}"
                f"  |  F12: switch mode")
        if state and state.stardate > 0:
            info += f"  |  stardate: {state.stardate_str}"
        fs = max(8, int(16 * surface.get_height() / 1080))
        font = style.get_font(fs)
        col = colors.get("text", {}).get("secondary", [120, 135, 170])
        text = font.render(info, True, tuple(col[:3]))
        surface.blit(text, (10, surface.get_height() - 22))
