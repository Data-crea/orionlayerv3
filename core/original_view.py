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

    def placement(self, target_w, target_h):
        """Where the 640x480 picture lands in a window that size.

        Returns `(dst_x, dst_y, dst_w, dst_h, scale)`: the largest 4:3
        area that fits, centred, so the bars are shared evenly.

        ONE FUNCTION, because drawing and clicking both need it
        (decision 5). Until work order 130 A the two carried the same
        four lines of arithmetic each; they agreed, and a second copy
        that agrees today is the shape every drift in this project has
        started from. It became load-bearing in that order: the
        fallback view now forwards clicks for every screen HD does not
        claim, so a disagreement here would put the click a bar's
        width away from the pixel the player aimed at.
        """
        scale = min(target_w / self.FB_W, target_h / self.FB_H)
        dst_w = int(self.FB_W * scale)
        dst_h = int(self.FB_H * scale)
        dst_x = (target_w - dst_w) // 2
        dst_y = (target_h - dst_h) // 2
        return dst_x, dst_y, dst_w, dst_h, scale

    def render(self, target, layout):
        """Draw the framebuffer scaled into the window.

        Computes the largest 4:3 area and centers it.
        """
        tw = target.get_width()
        th = target.get_height()
        dst_x, dst_y, dst_w, dst_h, scale = self.placement(tw, th)

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

        For click forwarding in original mode AND in the fallback
        view, which since work order 130 A takes the same path.
        Returns (x, y) in 640x480 or None if outside — outside is the
        letterbox bar, where the game has no pixel and a click has
        nothing to mean.
        """
        dst_x, dst_y, dst_w, dst_h, scale = self.placement(
            target_w, target_h)

        rx = screen_x - dst_x
        ry = screen_y - dst_y

        if rx < 0 or ry < 0 or rx >= dst_w or ry >= dst_h:
            return None

        x = int(rx / scale)
        y = int(ry / scale)
        return (min(x, self.FB_W - 1), min(y, self.FB_H - 1))


    # ── Original-mode interaction (moved from main.py) ─────

    RADIO_BUTTON_TYPE = 1
    #: `FIELD_TYPE_CONTINUOUS_INPUT` (orion2_consts.h): a string field — the
    #: Ship Designer's name, a save slot's description. An ACTIVATE_FIELD
    #: never opens it for typing (the early exit returns the field without
    #: the mouse path that sets `_input_field_active`), so typed keys went
    #: nowhere and Enter then pressed the field under the engine's pointer
    #: (`Scan_Field_`, fields.cpp) — measured, work order 186 part 3: the
    #: designer's hull changed. An INJECT_CLICK opens it, and it also puts
    #: the pointer on the field: the keys append, Enter commits.
    CONTINUOUS_INPUT_TYPE = 11
    #: `FIELD_TYPE_MULTI_BUTTON` (orion2_consts.h): one of a group writing
    #: one variable (the designer's hulls, the Colonies sort, the Info
    #: tabs). Its value is written in the mouse path an activation skips —
    #: measured, work order 187 part 3: every one of 18 clicks through F12
    #: went out as ACTIVATE_FIELD and changed nothing (the hull stayed, the
    #: Info page stayed). The same fault as the string field's, the same way.
    MULTI_BUTTON_TYPE = 3
    #: `FIELD_TYPE_GRID` (orion2_consts.h): an area that reads WHERE it was
    #: clicked — `_xpos/_ypos`, written in the mouse path an activation
    #: skips (fields.cpp:173-189). The battle map is one (combat1.cpp:111):
    #: a move goes to `_cur_combat_x + _xpos / 2` (:712-757), so an
    #: ACTIVATE_FIELD moved the ship wherever the pointer had last been
    #: (work order 193's survey, fixed in 194). Same fault, same way.
    GRID_TYPE = 12

    def find_field_at(self, fields, x, y):
        """Find field at (x, y) in 640x480 coordinates.

        Skips dummy (index 0) and offscreen (5000, 5000) fields. The first
        field covering the point decides, as in the engine; a radio button,
        a continuous string field, a multi-button or a grid answers None —
        all four must go through INJECT_CLICK.
        """
        if not fields:
            return None
        for f in fields:
            if f.index < 1:
                continue
            if f.x >= 5000 or f.y >= 5000:
                continue
            if f.x <= x <= f.x_end and f.y <= y <= f.y_end:
                # The FIRST field that covers the point is the one the
                # engine's own hit test takes (`Scan_Field_`, fields.cpp:
                # 710-715, from index 1) — so it decides. Skipping it and
                # taking the next was wrong: the designer's name field lies
                # over a full-screen hidden field, which an activation then
                # "clicked" (work order 186).
                if f.field_type in (self.RADIO_BUTTON_TYPE,
                                    self.CONTINUOUS_INPUT_TYPE,
                                    self.MULTI_BUTTON_TYPE,
                                    self.GRID_TYPE):
                    return None
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

    def forward_right_click(self, client, screen_x, screen_y,
                            target_w, target_h):
        """Route a window RIGHT click into orion2re (the F12 view).

        Always the point, never a field: the original reads a right
        click where it lands — help over a help region, turn to face on
        the battle map (combat1.cpp:696-710) — and CANCEL_FIELD would
        answer at a field's centre. Open fix 61 carries it; the letterbox
        bar sends nothing. Returns the 640x480 point sent, or None."""
        coords = self.screen_to_640(screen_x, screen_y,
                                    target_w, target_h)
        if coords:
            client.inject_right_click(*coords)
        return coords

    @staticmethod
    def key_code(event):
        """The code the engine's INJECT_KEY takes for a KEYDOWN, or None.

        Typed characters go as their own code — `ord` of the character,
        upper case included, the way `core/injection.name_keys` has typed
        names into the game since work order 128 — and the editing keys as
        pygame's codes, which are the ASCII control codes the game reads
        (Backspace 8, Tab 9, Enter 13, ESC 27, Delete 127). Keys with no
        such code (arrows, function keys) are None: INJECT_KEY takes an
        int16 and the game has no reading for them."""
        editing = (pygame.K_BACKSPACE, pygame.K_TAB, pygame.K_RETURN,
                   pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_DELETE)
        if event.key in editing:
            return pygame.K_RETURN if event.key == pygame.K_KP_ENTER \
                else event.key
        ch = getattr(event, "unicode", "") or ""
        if len(ch) == 1 and 32 <= ord(ch) < 127:
            return ord(ch)
        return None

    def forward_key(self, client, event):
        """A key pressed while the window shows the game's own picture
        goes to the game (work order 177's safety net: 174 found the
        fallback forwarding clicks and swallowing keys — a dialog that
        wants a name or Enter was a dead end). Returns the code sent."""
        code = self.key_code(event)
        if code is not None:
            client.inject_key(code)
        return code

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
