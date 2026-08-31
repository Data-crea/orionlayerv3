"""Box editor — F5 toggle. H=help. Ctrl+N=button, Ctrl+I=panel.

Input/state half of the editor; overlay rendering lives in
overlay.py. Public API unchanged: Editor(app), .toggle(),
.handle_event(event), .render(surface), .active.
"""
import logging
import time
import pygame
from core import mouse as mouse_input
from core.box import Box, save_boxes
from core.editor import overlay
from core.editor.constants import GLOW_KEYS, H_REF

log = logging.getLogger("editor")


class Editor:
    def __init__(self, app):
        self.app = app
        self.active = False
        self.selected = None
        self._drag = None
        self._dstart = None
        self._dorig = None
        self.show_fields = False
        self.show_help = False
        self._glow_idx = -1
        self._save_flash = 0.0

    @property
    def glow_key(self):
        return GLOW_KEYS[self._glow_idx] if 0 <= self._glow_idx < 4 else None

    def toggle(self):
        self.active = not self.active
        log.info("Editor %s", "ON" if self.active else "OFF")
        if self.active:
            self.show_help = True
        else:
            self.selected = None
            self._drag = None
            self._glow_idx = -1
            self.show_help = False

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.show_help:
                self.show_help = False
                return True
            return self._on_click(*event.pos)
        if event.type == pygame.MOUSEMOTION and self._drag:
            self._on_drag(*event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._drag:
                self._drag = None
                return True
        if event.type == pygame.MOUSEWHEEL and self.selected:
            mods = pygame.key.get_mods()
            if self.selected.name == "race_grid":
                # Portrait zoom/pan when hovering over grid
                screen = self.app.dispatcher.top
                if screen and hasattr(screen, "_race_at_screen_pos"):
                    mx, my = mouse_input.pos()
                    rid = screen._race_at_screen_pos(mx, my)
                    if rid is not None:
                        race = screen._race_by_id(rid)
                        if race:
                            if mods & pygame.KMOD_SHIFT:
                                # Pan vertical
                                crop = list(race.get("portrait_crop", [0.5, 0.5]))
                                crop[1] = round(max(0, min(1, crop[1] - event.y * 0.03)), 3)
                                race["portrait_crop"] = crop
                            elif mods & pygame.KMOD_ALT:
                                # Pan horizontal
                                crop = list(race.get("portrait_crop", [0.5, 0.5]))
                                crop[0] = round(max(0, min(1, crop[0] - event.y * 0.03)), 3)
                                race["portrait_crop"] = crop
                            else:
                                # Zoom
                                zoom = race.get("portrait_zoom", 1.0)
                                zoom = round(max(0.3, min(3.0, zoom + event.y * 0.1)), 2)
                                race["portrait_zoom"] = zoom
                            screen._invalidate_thumb(rid)
                            return True
            if (self.selected.style.get("pannable")
                    and not mods & pygame.KMOD_CTRL):
                self._image_wheel(self.selected, event.y, mods)
                return True
            if mods & pygame.KMOD_CTRL:
                self._change_font_scale(event.y)
                return True
        # Right-drag pans the image inside a pannable box
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 3
                and self.selected and self.selected.style.get("pannable")):
            self._drag = "pan"
            self._dstart = self._ref(*event.pos)
            self._dorig = tuple(self.selected.style.get("crop", [0.5, 0.5]))
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            if self._drag == "pan":
                self._drag = None
                return True
        if event.type == pygame.KEYDOWN:
            return self._on_key(event)
        return False

    def _ref(self, sx, sy):
        return self.app.layout.to_ref(sx, sy)

    def _on_click(self, sx, sy):
        rx, ry = self._ref(sx, sy)
        if self.show_fields and self._field_click(sx, sy):
            return True
        if self.selected:
            rh = self._hit_resize(rx, ry)
            if rh:
                self._drag = f"resize_{rh}"
                self._dstart = (rx, ry)
                self._dorig = tuple(self.selected.ref_rect)
                return True
        screen = self.app.dispatcher.top
        if screen:
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            hits = [b for b in screen.boxes if b.contains(sx, sy)]
            if hits and shift and self.selected in hits:
                idx = hits.index(self.selected)
                box = hits[(idx + 1) % len(hits)]
            elif hits:
                box = hits[-1]
            else:
                box = None
            if box:
                self.selected = box
                self._glow_idx = -1
                self._drag = "move"
                self._dstart = (rx, ry)
                self._dorig = tuple(box.ref_rect)
                return True
        self.selected = None
        self._glow_idx = -1
        return True

    def _on_drag(self, sx, sy):
        rx, ry = self._ref(sx, sy)
        if self._drag == "pan":
            self._image_pan_drag(rx, ry)
            return
        dx, dy = rx - self._dstart[0], ry - self._dstart[1]
        box = self.selected
        if not box:
            return
        if self._drag == "move":
            ox, oy, ow, oh = self._dorig
            box.ref_rect = (ox + dx, oy + dy, ow, oh)
            box.update_layout(self.app.layout)
        elif self._drag.startswith("resize_"):
            box.ref_rect = self._calc_resize(self._dorig, dx, dy,
                                              self._drag[7:])
            box.update_layout(self.app.layout)

    def _calc_resize(self, o, dx, dy, h):
        x, y, w, hh = o
        ms = 20
        nx, ny, nw, nh = x, y, w, hh
        if 'l' in h: nw = max(ms, w - dx); nx = x + w - nw
        if 'r' in h: nw = max(ms, w + dx)
        if 't' in h: nh = max(ms, hh - dy); ny = y + hh - nh
        if 'b' in h: nh = max(ms, hh + dy)
        return (int(nx), int(ny), int(nw), int(nh))

    def corners(self, box):
        bx, by, bw, bh = box.ref_rect
        return {'tl': (bx, by), 'tr': (bx+bw, by),
                'bl': (bx, by+bh), 'br': (bx+bw, by+bh)}

    def _hit_resize(self, rx, ry):
        bx, by, bw, bh = self.selected.ref_rect
        pts = {**self.corners(self.selected),
               't': (bx+bw//2, by), 'b': (bx+bw//2, by+bh),
               'l': (bx, by+bh//2), 'r': (bx+bw, by+bh//2)}
        for key, (hx, hy) in pts.items():
            if abs(rx-hx) <= H_REF and abs(ry-hy) <= H_REF:
                return key
        return None

    def _on_key(self, event):
        k, m = event.key, event.mod
        if k == pygame.K_h:
            self.show_help = not self.show_help
            return True
        if self.show_help:
            self.show_help = False
            return True
        if k == pygame.K_s and m & pygame.KMOD_CTRL:
            self._save(); return True
        if k == pygame.K_F2:
            self._save(); return True
        if k == pygame.K_n and m & pygame.KMOD_CTRL:
            self._new_box("button"); return True
        if k == pygame.K_i and m & pygame.KMOD_CTRL:
            self._new_box("inner_panel"); return True
        if k == pygame.K_DELETE and self.selected:
            self._delete(); return True
        if k == pygame.K_TAB:
            self.show_fields = not self.show_fields; return True
        if k == pygame.K_ESCAPE:
            if self._glow_idx >= 0:
                self._glow_idx = -1
            elif self.show_fields:
                self.show_fields = False
            else:
                self.selected = None
            return True
        if k == pygame.K_s and not (m & pygame.KMOD_CTRL):
            # Hide decorative background layers while placing boxes.
            # Duck-typed on purpose: a screen that has no star field
            # simply does not answer, and the editor stays ignorant of
            # what any individual screen draws.
            layer = getattr(self.app.dispatcher.top, "_starfield", None)
            if layer is not None:
                log.info("Star field: %s",
                         "on" if layer.toggle() else "off")
            return True
        if k == pygame.K_g and self.selected:
            if self.selected.style.get("skin") == "button":
                self._glow_idx = (self._glow_idx + 1) % 4
                log.info("Glow corner: %s", self.glow_key)
            return True
        if k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT,
                 pygame.K_RIGHT) and self.selected:
            s = 5 if m & pygame.KMOD_SHIFT else 1
            dx = s if k == pygame.K_RIGHT else (
                -s if k == pygame.K_LEFT else 0)
            dy = s if k == pygame.K_DOWN else (
                -s if k == pygame.K_UP else 0)
            if m & pygame.KMOD_ALT:
                self._content_offset_move(dx, dy)
            else:
                self._arrow_move(dx, dy)
            return True
        if k == pygame.K_r and self._glow_idx >= 0 and self.selected:
            self._rotate_glow(); return True
        return False

    def _arrow_move(self, dx, dy):
        box = self.selected
        if self._glow_idx >= 0 and box.style.get("skin") == "button":
            key = self.glow_key
            if "glows" not in box.style:
                box.style["glows"] = {}
            off = box.style["glows"].get(key, [0, 0])
            box.style["glows"][key] = [off[0] + dx, off[1] + dy]
        else:
            x, y, w, h = box.ref_rect
            box.ref_rect = (x + dx, y + dy, w, h)
            box.update_layout(self.app.layout)

    def _content_offset_move(self, dx, dy):
        """Alt+Arrow: move content inside the box."""
        box = self.selected
        off = list(box.style.get("content_offset", [0, 0]))
        off[0] += dx
        off[1] += dy
        box.style["content_offset"] = off

    def _rotate_glow(self):
        box = self.selected
        key = self.glow_key
        if "glow_rot" not in box.style:
            box.style["glow_rot"] = {}
        cur = box.style["glow_rot"].get(key, 0)
        box.style["glow_rot"][key] = (cur + 90) % 360

    def _change_font_scale(self, direction):
        box = self.selected
        cur = box.style.get("font_scale", 1.0)
        new = round(cur + direction * 0.1, 1)
        new = max(0.5, min(3.0, new))
        box.style["font_scale"] = new
        log.info("'%s' font_scale: %.1f", box.name, new)

    # ── Pannable image boxes (style: pannable/zoom/crop) ──

    @staticmethod
    def _image_wheel(box, dy, mods):
        """Scroll = zoom, Shift+Scroll = pan vertical, Alt+Scroll =
        pan horizontal. Stored in box.style, saved with Ctrl+S."""
        st = box.style
        if mods & pygame.KMOD_SHIFT:
            crop = list(st.get("crop", [0.5, 0.5]))
            crop[1] = round(max(0, min(1, crop[1] - dy * 0.03)), 3)
            st["crop"] = crop
        elif mods & pygame.KMOD_ALT:
            crop = list(st.get("crop", [0.5, 0.5]))
            crop[0] = round(max(0, min(1, crop[0] - dy * 0.03)), 3)
            st["crop"] = crop
        else:
            st["zoom"] = round(max(0.3, min(4.0,
                                            st.get("zoom", 1.0) + dy * 0.05)), 2)

    def _image_pan_drag(self, rx, ry):
        """Right-drag: the image follows the mouse 1:1. The screen may
        expose image_size(box_name) -> (w, h) so the cover-fill
        overflow is exact; otherwise a coarse range is assumed."""
        box = self.selected
        st = box.style
        bw, bh = box.ref_rect[2], box.ref_rect[3]
        zoom = max(0.3, st.get("zoom", 1.0))
        scr = self.app.dispatcher.top
        size = (scr.image_size(box.name)
                if scr and hasattr(scr, "image_size") else None)
        if size and size[0] > 0 and size[1] > 0:
            scale = max(bw / size[0], bh / size[1]) * zoom
            range_x = max(1.0, size[0] * scale - bw)
            range_y = max(1.0, size[1] * scale - bh)
        else:
            range_x = max(1.0, bw * zoom * 0.5)
            range_y = max(1.0, bh * zoom * 0.5)
        dx = rx - self._dstart[0]
        dy = ry - self._dstart[1]
        cx = round(max(0, min(1, self._dorig[0] - dx / range_x)), 3)
        cy = round(max(0, min(1, self._dorig[1] - dy / range_y)), 3)
        st["crop"] = [cx, cy]

    def _save(self):
        scr = self.app.dispatcher.top
        if not scr: return
        save_boxes(scr._screen_dir, scr.boxes,
                   self.app.win_w, self.app.win_h)
        res_key = f"{self.app.win_w}x{self.app.win_h}"
        log.info("Saved %d boxes for %s -> %s",
                 len(scr.boxes), res_key, scr._screen_dir)
        if hasattr(scr, "save_races"):
            scr.save_races()
            log.info("Saved races.json (portrait crops)")
        self._save_flash = time.monotonic()

    def _new_box(self, skin="button"):
        scr = self.app.dispatcher.top
        if not scr: return
        rx, ry = self._ref(*mouse_input.pos())
        n = len(scr.boxes)
        if skin == "inner_panel":
            data = {"name": f"panel_{n}", "role": ["layout"],
                    "rect": [rx - 100, ry - 75, 200, 150],
                    "style": {"skin": "inner_panel"}}
        else:
            data = {"name": f"btn_{n}", "role": ["click"],
                    "rect": [rx - 75, ry - 25, 150, 50],
                    "style": {"skin": "button", "label": "NEW",
                              "font_size": 16}}
        b = Box(data)
        b.update_layout(self.app.layout)
        scr.boxes.append(b)
        self.selected = b
        log.info("Created '%s' (%s)", b.name, skin)

    def _delete(self):
        scr = self.app.dispatcher.top
        if scr and self.selected in scr.boxes:
            scr.boxes.remove(self.selected)
            log.info("Deleted '%s'", self.selected.name)
            self.selected = None

    def _field_click(self, sx, sy):
        L = self.app.layout
        px, py, pw, ph = L.rect((1500, 80, 380, 700))
        if not (px <= sx <= px+pw and py <= sy <= py+ph):
            return False
        if not self.selected: return True
        fields = (self.app.client.state.fields
                  if self.app.connected else [])
        row_h = L.font_size(12) + 6
        idx = (sy - py - 32) // row_h
        vis = [f for f in fields if f.index >= 1]
        if 0 <= idx < len(vis):
            self.selected.field_id = vis[idx].index
            log.info("Field %d -> '%s'", vis[idx].index,
                     self.selected.name)
        return True

    # -- Rendering --

    def render(self, surface):
        """Draw editor overlay (delegates to overlay module)."""
        overlay.render(self, surface)
