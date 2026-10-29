"""Box editor — F3 toggle (`core/hdkeys.py`); the side panel lists the boxes.

Input/state half of the editor; overlay rendering lives in
overlay.py. Public API unchanged: Editor(app), .toggle(),
.handle_event(event), .render(surface), .active.
"""
import logging
import os
import time
import pygame
from core import mouse as mouse_input
from core.box import save_boxes
from core.editor import boxclass, geometry, overlay, target
from core.editor.panel import Panel
from core.editor.constants import H_REF

log = logging.getLogger("editor")


class Editor:
    def __init__(self, app):
        self.app = app
        self.active = False
        self.selected = None
        self._drag = None
        self._dstart = None
        self._dorig = None
        self._save_flash = 0.0
        self._save_note = ""
        #: Why the last handle was refused, for the info bar. Cleared
        #: on the next click that is not a refusal, so it reads as an
        #: answer to what was just tried and not as a standing state.
        self.refusal = None
        self.panel = Panel(self)
        #: Developer mode keeps the base route for saving; a player's save
        #: goes into a mod (`core.editor.target`).
        self.developer = target.developer()

    def target(self):
        return target.resolve(self.app, self.app.dispatcher.top)

    def select(self, box):
        self.selected = box
        self.refusal = None

    def place_refusal(self, box):
        """Why `box` cannot be moved, or None. A box whose rect the screen
        derives is rebuilt from its reference at every load, so a move of
        it was never saved anywhere (decision 3), unless the screen writes
        it back (`ScreenBase.editor_moves`)."""
        scr = self.app.dispatcher.top
        if scr is not None and not scr.editor_moves(box):
            return ("The place of this box is derived by the screen and "
                    "cannot be moved (decision 3).")
        return None

    def revert(self):
        """Drop every unsaved change: the boxes are read again."""
        scr = self.app.dispatcher.top
        if scr is None:
            return
        scr._reload_boxes()
        scr._update_box_layout()
        self.selected = None
        self._drag = None

    def toggle(self):
        self.active = not self.active
        log.info("Editor %s", "ON" if self.active else "OFF")
        if not self.active:
            self.selected = None
            self._drag = None
        self.panel.blur()
        self.panel.dragging = None

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.panel.hit(*event.pos):
                return self.panel.click(*event.pos)
            self.panel.blur()
            return self._on_click(*event.pos)
        if event.type == pygame.MOUSEMOTION and self.panel.dragging:
            self.panel.drag_to(*event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 \
                and self.panel.release():
            return True
        if event.type == pygame.MOUSEMOTION and self._drag:
            self._on_drag(*event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._drag:
                self._drag = None
                return True
        if event.type == pygame.MOUSEWHEEL and self.panel.visible \
                and self.panel.hit(*mouse_input.pos()):
            self.panel.wheel(event.y)
            return True
        if event.type == pygame.KEYDOWN:
            return self._on_key(event)
        return False

    def _ref(self, sx, sy):
        return self.app.layout.to_ref(sx, sy)

    def _screen_name(self):
        """Which screen is being edited, or "" — the class is a
        property of (screen, box) and not of the box alone."""
        scr = self.app.dispatcher.top
        return getattr(scr, "SCREEN_NAME", "") if scr else ""

    def _on_click(self, sx, sy):
        rx, ry = self._ref(sx, sy)
        if self.selected:
            rh = self._hit_resize(rx, ry)
            if rh:
                # THE CLASS DECIDES, AND A REFUSAL SAYS WHY. A cutout
                # box and a hand-placed one look identical on screen,
                # so a handle that silently does nothing reads as a
                # broken editor rather than as a rule — see
                # `core.editor.boxclass`.
                why = boxclass.refusal(self._screen_name(),
                                       self.selected.name, rh)
                if why:
                    self.refusal = why
                    log.info("resize refused: %s", why)
                    return True
                self.refusal = None
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
                self.refusal = self.place_refusal(box)
                if self.refusal:
                    return True
                self._drag = "move"
                self._dstart = (rx, ry)
                self._dorig = tuple(box.ref_rect)
                return True
        self.selected = None
        self.refusal = None
        return True

    def _on_drag(self, sx, sy):
        rx, ry = self._ref(sx, sy)
        dx, dy = rx - self._dstart[0], ry - self._dstart[1]
        box = self.selected
        if not box:
            return
        if self._drag == "move":
            ox, oy, ow, oh = self._dorig
            box.ref_rect = geometry.clamp_move((ox + dx, oy + dy, ow, oh))
            box.update_layout(self.app.layout)
        elif self._drag.startswith("resize_"):
            handle = self._drag[7:]
            rect = self._calc_resize(self._dorig, dx, dy, handle)
            # A BOX WITH A TRANSCRIBED ASPECT KEEPS IT ON ANY EDGE.
            # The galaxy inset is the case and it is locked today; the
            # rule is here so the first person to unlock it cannot
            # break a ratio held to a thousandth by a smoke check.
            box.ref_rect = geometry.clamp_resize(boxclass.hold_aspect(
                self._screen_name(), box.name, rect, handle), handle)
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
        if self.panel.focus and (k == pygame.K_F2 or (
                k == pygame.K_s and m & pygame.KMOD_CTRL)):
            self.panel.apply()     # a typed number is part of the save
            self._save(); return True
        if self.panel.focus:
            return self.panel.key(event)
        if k == pygame.K_s and m & pygame.KMOD_CTRL:
            self._save(); return True
        if k == pygame.K_F2:
            self._save(); return True
        if k == pygame.K_p:
            self.panel.visible = not self.panel.visible; return True
        if k == pygame.K_ESCAPE:
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
        if k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT,
                 pygame.K_RIGHT) and self.selected:
            s = 5 if m & pygame.KMOD_SHIFT else 1
            dx = s if k == pygame.K_RIGHT else (
                -s if k == pygame.K_LEFT else 0)
            dy = s if k == pygame.K_DOWN else (
                -s if k == pygame.K_UP else 0)
            self._arrow_move(dx, dy)
            return True
        return False

    def _arrow_move(self, dx, dy):
        box = self.selected
        if self.place_refusal(box):
            self.refusal = self.place_refusal(box)
            return
        x, y, w, h = box.ref_rect
        box.ref_rect = geometry.clamp_move((x + dx, y + dy, w, h))
        box.update_layout(self.app.layout)

    def _change_font_scale(self, direction):
        box = self.selected
        cur = box.style.get("font_scale", 1.0)
        new = round(cur + direction * 0.1, 1)
        new = max(0.5, min(3.0, new))
        box.style["font_scale"] = new
        log.info("'%s' font_scale: %.1f", box.name, new)

    def _save(self):
        scr = self.app.dispatcher.top
        if not scr:
            return
        tgt = self.target()
        # The seed is the file the boxes were LOADED from, so a mod file
        # made now keeps that file's other resolutions.
        base = None if self.developer else (
            getattr(scr, "_boxes_dir", None) or scr._screen_dir)
        try:
            target.prepare(tgt)      # makes the mod folder: it can fail too
            save_boxes(tgt.folder, scr.boxes, self.app.win_w, self.app.win_h,
                       seed_dir=base)
        except OSError as err:
            # a full disk or a read-only folder: say so in the editor
            # instead of raising into the frame guard (audit TD-03)
            self._save_note = f"NOT SAVED: {err}"
            log.error("Saving boxes for %s failed: %s", tgt.folder, err)
            self._save_flash = time.monotonic()
            return
        res_key = f"{self.app.win_w}x{self.app.win_h}"
        note = f"SAVED [{res_key}] -> {tgt.label}"
        if not tgt.active:
            note += ". " + tgt.hint
        self._save_note = note
        log.info("Saved %d boxes for %s -> %s", len(scr.boxes), res_key,
                 tgt.folder)
        self._save_flash = time.monotonic()
        # THE SCREENS' OWN EXTRA FILES go where boxes.json went: into the
        # mod for a player (`folder`), into the base project for a developer.
        folder = None if self.developer else tgt.folder
        root = os.path.dirname(os.path.dirname(os.path.normpath(tgt.folder)))
        if not self.developer and os.path.normpath(root) not in [
                os.path.normpath(m) for m in self.app.res.mod_dirs]:
            # the mod loads from the next start; this session reads it too,
            # so Revert brings back what was saved and not the base
            self.app.res.mod_dirs.insert(0, root)
        if hasattr(scr, "save_races"):
            scr.save_races(folder)
            log.info("Saved races.json (portrait crops)")
        # A SCREEN MAY OWN GEOMETRY boxes.json CANNOT HOLD. The colony
        # summary derives every rect from `layout_reference.json` at
        # load, so a box the editor is allowed to move has to be
        # written back THERE or the next start rebuilds it.
        if hasattr(scr, "save_geometry"):
            for _name, _rect in scr.save_geometry(folder) or ():
                log.info("Saved %s %s -> layout_reference.json",
                         _name, _rect)

    # -- Rendering --

    def render(self, surface):
        """Draw editor overlay (delegates to overlay module)."""
        overlay.render(self, surface)
