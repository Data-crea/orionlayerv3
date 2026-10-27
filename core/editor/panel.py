"""The editor's window — HD EXTENSION `editor_panel`, work order 334.

A side panel with what the hotkeys used to hide: the screen's boxes by
name, what the chosen one is for, its position and size as numbers, and
the buttons Save, Revert and Close. The mouse and the arrow keys still
move and resize on the picture; the panel is the way to choose, read and
type.

ONE LAYOUT FOR DRAWING AND HIT TEST (decision 5): `_layout` returns every
rectangle and both `draw` and `click` read it, so a button cannot be drawn
in one place and hit in another.

Boxes cannot be created or deleted here or anywhere in the editor: a box
is a named rectangle the screen's code looks up, so a deleted one left
its content gone or, on the colony list, crashed the screen (measured,
work order 334).
"""
import textwrap
import time
from types import SimpleNamespace

import pygame

from core.editor import boxclass, geometry, labels
from core.editor.constants import (C_ASN, C_DORMANT, C_FTX, C_HELP_HDR,
                                   C_HELP_KEY, C_ITX, C_SEL)

BG = (10, 14, 28, 235)
EDGE = (60, 80, 120)
BTN = (30, 44, 76)
BTN_ON = (60, 90, 150)
ROW_SEL = (50, 70, 120)
FIELD_BG = (18, 24, 44)
FIELDS = ("x", "y", "w", "h")
FIELD_NAMES = {"x": "X", "y": "Y", "w": "Width", "h": "Height"}


class Panel:
    def __init__(self, ed):
        self.ed = ed
        self.visible = True
        self.scroll = 0
        self.focus = None          # "x" / "y" / "w" / "h" while typing
        self.buf = ""
        self.message = ""
        self._last = None          # the box the list last scrolled to
        self.side = "right"        # the edge the panel stands on
        self._dock_for = None
        self._scr = None
        #: Where the person put the panel (window px, top left), or None
        #: while it docks itself at an edge.
        self.pos = None
        self.dragging = None       # grab offset while the header is held
        self._hdr_t = 0.0
        self._moved = False        # the held header actually moved

    # ── what the panel knows ─────────────────────────────────────
    def _screen(self):
        return self.ed.app.dispatcher.top

    def entries(self):
        """The boxes the list offers: those with a rect to move."""
        scr = self._screen()
        return [b for b in scr.boxes if b.ref_rect is not None] if scr else []

    def _labels(self):
        scr = self._screen()
        return labels.load(getattr(scr, "_screen_dir", "")) if scr else {}

    def _title(self, box):
        return labels.title(self._labels(), box.name)

    def _dormant(self, box):
        scr = self._screen()
        return bool(scr and scr.editor_dormant(box))

    def editable(self, box):
        """Which of x y w h the class lets a number change. Position is
        free for every box (a drag moves them all); a side only where
        the class offers a handle on it."""
        handles = boxclass.HANDLES[boxclass.classify(
            self.ed._screen_name(), box.name)]
        place = self.ed.place_refusal(box) is None
        return {"x": place, "y": place,
                "w": bool(handles & {"l", "r"}),
                "h": bool(handles & {"t", "b"})}

    # ── geometry ─────────────────────────────────────────────────
    def _font(self, size):
        L = self.ed.app.layout
        return self.ed.app.style.get_font(L.font_size(size))

    def _layout(self):
        """Every rect of the panel, in window pixels."""
        app, L = self.ed.app, self.ed.app.layout
        s = max(0.6, L.scale)
        width = int(max(300, 360 * s))
        bar = max(24, int(28 * s))             # the editor's info bar
        pad = int(10 * s)
        r = SimpleNamespace(s=s, pad=pad)
        #: Clear of the editor's badge and its save note (top left).
        top = int(64 * s)
        if self.pos is not None:
            # PLACED BY THE PERSON: it stays where it was put (inside the
            # window), and the docking rule leaves it alone.
            height = min(app.win_h - bar - top, int(720 * s))
            px = max(0, min(self.pos[0], app.win_w - width))
            py = max(0, min(self.pos[1], app.win_h - bar - height))
            r.panel = pygame.Rect(px, py, width, height)
            top = py
            left = px + width // 2 < app.win_w // 2
        else:
            left = self._dock(width, bar) == "left"
            r.panel = pygame.Rect(0 if left else app.win_w - width, top,
                                  width, app.win_h - bar - top)
        r.top = top
        r.header = pygame.Rect(r.panel.x, r.panel.y, width, int(40 * s))
        r.tab = pygame.Rect(4 if left else app.win_w - int(150 * s),
                            top, int(146 * s), int(26 * s))
        x, w = r.panel.x + pad, width - 2 * pad
        y = top + int(42 * s)
        bh, gap = int(30 * s), int(6 * s)
        bw = (w - 3 * gap) // 4
        r.buttons = {}
        for i, name in enumerate(("save", "revert", "hide", "close")):
            r.buttons[name] = pygame.Rect(x + i * (bw + gap), y, bw, bh)
        y += bh + int(8 * s)
        r.target_y = y
        y += int(50 * s)
        row_h = max(self._font(13).get_linesize() + 4, int(22 * s))
        r.row_h = row_h
        list_h = row_h * max(6, int((r.panel.h - y) * 0.38 // row_h))
        r.list = pygame.Rect(x, y, w, list_h)
        y = r.list.bottom + int(10 * s)
        r.detail_y = y
        r.x, r.w = x, w
        r.bottom = r.panel.bottom - pad
        return r

    def _dock(self, width, bar):
        """THE PANEL STEPS ASIDE FOR WHAT IS BEING EDITED. A box under
        the panel could be chosen from the list but not seen or dragged,
        and the galaxy map's sidebar boxes are exactly there. So when the
        selected box lies under the panel, the panel goes to the other
        edge; it does not move otherwise, so a click in the list never
        makes the list jump."""
        if not self.visible:
            return self.side         # decided again when it is shown
        sel = self.ed.selected
        if sel is not self._dock_for:
            self._dock_for = sel
            if sel is not None and sel.screen_rect is not None:
                win_w, win_h = self.ed.app.win_w, self.ed.app.win_h
                mine = pygame.Rect(0 if self.side == "left"
                                   else win_w - width, 0, width,
                                   win_h - bar)
                if self.visible and sel.screen_rect.colliderect(mine):
                    self.side = "left" if self.side == "right" else "right"
        return self.side

    def _detail_rects(self, r, about_lines):
        """Field and font rows, below the title and the wrapped text."""
        s = r.s
        y = r.detail_y + int(26 * s) + about_lines * int(17 * s) \
            + int(26 * s)
        fh = int(30 * s)
        gap = int(6 * s)
        fw = (r.w - 3 * gap) // 4
        fields = {}
        for i, name in enumerate(FIELDS):
            fields[name] = pygame.Rect(r.x + i * (fw + gap),
                                       y + int(16 * s), fw, fh)
        out = SimpleNamespace(fields=fields, y_after=y + int(16 * s) + fh)
        font_y = out.y_after + int(14 * s)
        out.font_minus = pygame.Rect(r.x + int(110 * s), font_y,
                                     int(30 * s), fh)
        out.font_plus = pygame.Rect(r.x + int(190 * s), font_y,
                                    int(30 * s), fh)
        out.font_y = font_y
        out.hint_y = font_y + fh + int(14 * s)
        return out

    def hit(self, sx, sy):
        r = self._layout()
        if self.visible:
            return r.panel.collidepoint(sx, sy)
        return r.tab.collidepoint(sx, sy)

    # ── input ────────────────────────────────────────────────────
    def click(self, sx, sy):
        r = self._layout()
        ed = self.ed
        if not self.visible:
            if r.tab.collidepoint(sx, sy):
                self.visible = True
            return True
        pos = (sx, sy)
        if r.header.collidepoint(pos):
            self.blur()
            self._moved = False
            now = time.monotonic()
            if now - self._hdr_t < 0.4:
                self.pos, self.dragging = None, None   # double click: dock
                self._hdr_t = 0.0          # a third click starts a new pair
            else:
                self.dragging = (sx - r.panel.x, sy - r.panel.y)
                self._hdr_t = now
            return True
        for name, rect in r.buttons.items():
            if rect.collidepoint(pos):
                self._button(name)
                return True
        if r.list.collidepoint(pos):
            idx = self.scroll + (sy - r.list.y) // r.row_h
            rows = self.entries()
            if 0 <= idx < len(rows):
                self.blur()
                ed.select(rows[idx])
            return True
        box = ed.selected
        if box is not None:
            lines = self._about_lines(box, r)
            d = self._detail_rects(r, len(lines))
            ok = self.editable(box)
            for name, rect in d.fields.items():
                if rect.collidepoint(pos):
                    self.blur()
                    if ok[name]:
                        self.focus, self.buf = name, str(self._value(box, name))
                    else:
                        self.message = (f"{FIELD_NAMES[name]} of this box "
                                        f"is set by the screen.")
                    return True
            if "font_scale" in box.style:
                if d.font_minus.collidepoint(pos):
                    ed._change_font_scale(-1)
                    return True
                if d.font_plus.collidepoint(pos):
                    ed._change_font_scale(1)
                    return True
        self.blur()
        return True

    def _button(self, name):
        ed = self.ed
        self.blur()
        if name == "save":
            ed._save()
            self.message = ed._save_note
        elif name == "revert":
            ed.revert()
            self.message = "Unsaved changes dropped."
        elif name == "hide":
            self.visible = False
        elif name == "close":
            ed.toggle()

    def drag_to(self, sx, sy):
        """The header is held and the pointer moved."""
        if self.dragging is not None:
            self.pos = (sx - self.dragging[0], sy - self.dragging[1])
            self._moved = True

    def release(self):
        was = self.dragging is not None
        self.dragging = None
        if self._moved:
            self._hdr_t = 0.0      # a drag is not the first half of a double click
        return was

    def wheel(self, dy):
        n = len(self.entries())
        shown = self._layout().list.h // self._layout().row_h
        self.scroll = max(0, min(max(0, n - shown), self.scroll - dy))

    def key(self, event):
        """Typing into a number field. True when the key was taken."""
        k = event.key
        if self.ed.selected is None:
            self.blur()
            return False
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.apply()
        elif k == pygame.K_TAB:
            self.apply()
            ok = self.editable(self.ed.selected) if self.ed.selected else {}
            order = [n for n in FIELDS if ok.get(n)]
            if self.focus in order or not self.focus:
                nxt = order[(order.index(self.focus) + 1) % len(order)] \
                    if self.focus in order and order else None
                self.focus = nxt
                self.buf = str(self._value(self.ed.selected, nxt)) \
                    if nxt else ""
        elif k == pygame.K_ESCAPE:
            self.blur()
        elif k == pygame.K_BACKSPACE:
            self.buf = self.buf[:-1]
        elif (event.unicode and event.unicode.isascii()
              and event.unicode.isdecimal() and len(self.buf) < 5):
            self.buf += event.unicode
        return True

    def blur(self):
        self.focus, self.buf = None, ""

    @staticmethod
    def _value(box, name):
        x, y, w, h = box.ref_rect
        return {"x": x, "y": y, "w": w, "h": h}[name]

    def apply(self):
        """Set the focused number on the selected box, inside the area."""
        box, name = self.ed.selected, self.focus
        if box is None or name is None or not self.buf:
            return
        x, y, w, h = box.ref_rect
        new = dict(x=x, y=y, w=w, h=h)
        new[name] = int(self.buf)
        rect = (new["x"], new["y"], new["w"], new["h"])
        out = geometry.clamp_resize(rect) if name in "wh" \
            else geometry.clamp_move(rect)
        if name in "wh":     # a transcribed aspect holds for a typed size too
            out = boxclass.hold_aspect(self.ed._screen_name(), box.name,
                                       out, "r" if name == "w" else "b")
        box.ref_rect = out
        box.update_layout(self.ed.app.layout)
        self.message = ("Kept inside the screen." if out != rect else "")
        self.buf = str(self._value(box, name))

    # ── drawing ──────────────────────────────────────────────────
    def _about_lines(self, box, r):
        text = labels.about(self._labels(), box.name)
        if self._dormant(box):
            text = (text + " " if text else "") + \
                "(Its popup is not open now; it is shown dimmed.)"
        if not text:
            return []
        chars = max(20, int(r.w / (self._font(13).size("n")[0] or 7)))
        return textwrap.wrap(text, chars)[:5]

    def _text(self, surface, text, pos, size, colour, clip=None):
        img = self._font(size).render(text, True, colour)
        if clip is not None:
            surface.set_clip(clip)
        surface.blit(img, pos)
        if clip is not None:
            surface.set_clip(None)

    def _button_draw(self, surface, rect, text, on=False):
        pygame.draw.rect(surface, BTN_ON if on else BTN, rect)
        pygame.draw.rect(surface, EDGE, rect, 1)
        img = self._font(14).render(text, True, C_ITX)
        surface.blit(img, (rect.centerx - img.get_width() // 2,
                           rect.centery - img.get_height() // 2))

    def draw(self, surface):
        ed = self.ed
        if self._screen() is not self._scr:
            # A NEW SCREEN REPLACES EVERY BOX: the chosen one, the typing
            # focus and the last message belonged to the old screen.
            self._scr = self._screen()
            ed.selected = None
            self.blur()
            self.message = ""
        r = self._layout()
        if not self.visible:
            self._button_draw(surface, r.tab, "Layout panel")
            return
        bg = pygame.Surface(r.panel.size, pygame.SRCALPHA)
        bg.fill(BG)
        surface.blit(bg, r.panel.topleft)
        pygame.draw.rect(surface, EDGE, r.panel, 1)
        scr = self._screen()
        name = getattr(scr, "SCREEN_NAME", "")
        self._text(surface, "LAYOUT EDITOR", (r.x, r.top + int(8 * r.s)), 18,
                   C_SEL)
        self._text(surface, f"{name.replace('_', ' ')}  "
                   f"{ed.app.win_w}x{ed.app.win_h}  -  drag here to move",
                   (r.x, r.top + int(26 * r.s)), 12, C_FTX)
        for key, text in (("save", "Save"), ("revert", "Revert"),
                          ("hide", "Hide"), ("close", "Close")):
            self._button_draw(surface, r.buttons[key], text)
        self._draw_target(surface, r)
        self._draw_list(surface, r)
        if ed.selected is not None and ed.selected.ref_rect is not None:
            self._draw_detail(surface, r, ed.selected)
        else:
            self._text(surface, "Click a box in the list or on the screen.",
                       (r.x, r.detail_y), 13, C_FTX)
        msg = ed.refusal or self.message
        if msg:
            lines = textwrap.wrap(msg, max(20, int(r.w / 8)))[:3]
            for i, line in enumerate(lines):
                self._text(surface, line, (r.x, r.bottom - (len(lines) - i)
                                           * int(16 * r.s)), 12, C_ASN)

    def _draw_target(self, surface, r):
        t = self.ed.target()
        lines = textwrap.wrap("Saves to: " + t.label, max(20, int(r.w / 8)))
        if t.hint and not t.active:
            lines += textwrap.wrap(t.hint, max(20, int(r.w / 8)))
        for i, line in enumerate(lines[:3]):
            self._text(surface, line, (r.x, r.target_y + i * int(15 * r.s)),
                       12, C_DORMANT if (t.hint and i > 0) else C_FTX)

    def _draw_list(self, surface, r):
        rows = self.entries()
        shown = r.list.h // r.row_h
        sel = self.ed.selected
        if sel is not self._last:
            self._last = sel
            self.message = ""
            if sel in rows:
                i = rows.index(sel)
                if i < self.scroll or i >= self.scroll + shown:
                    self.scroll = max(0, min(i, max(0, len(rows) - shown)))
        pygame.draw.rect(surface, FIELD_BG, r.list)
        pygame.draw.rect(surface, EDGE, r.list, 1)
        kinds = self.ed._screen_name()
        for n in range(shown):
            i = self.scroll + n
            if i >= len(rows):
                break
            box = rows[i]
            row = pygame.Rect(r.list.x, r.list.y + n * r.row_h,
                              r.list.w, r.row_h)
            if box is sel:
                pygame.draw.rect(surface, ROW_SEL, row)
            text = self._title(box)
            if boxclass.classify(kinds, box.name) == boxclass.LOCKED:
                text += "  (fixed size)"
            colour = C_DORMANT if self._dormant(box) else (
                C_SEL if box is sel else C_ITX)
            if self._dormant(box):
                text += "  (popup)"
            self._text(surface, text, (row.x + 6, row.y + 2), 13, colour,
                       clip=row)
        if len(rows) > shown:
            self._text(surface, f"{self.scroll + 1}-"
                       f"{min(len(rows), self.scroll + shown)} of {len(rows)}",
                       (r.list.right - int(86 * r.s), r.list.bottom + 1),
                       11, C_FTX)

    def _draw_detail(self, surface, r, box):
        lines = self._about_lines(box, r)
        d = self._detail_rects(r, len(lines))
        self._text(surface, self._title(box), (r.x, r.detail_y), 17, C_HELP_KEY)
        y = r.detail_y + int(26 * r.s)
        for line in lines:
            self._text(surface, line, (r.x, y), 13, C_ITX)
            y += int(17 * r.s)
        kind = boxclass.classify(self.ed._screen_name(), box.name)
        self._text(surface, f"{box.name}  ·  {kind}",
                   (r.x, y + int(2 * r.s)), 11, C_FTX)
        ok = self.editable(box)
        for name, rect in d.fields.items():
            self._text(surface, FIELD_NAMES[name],
                       (rect.x, rect.y - int(15 * r.s)), 11, C_HELP_HDR)
            pygame.draw.rect(surface, FIELD_BG, rect)
            edge = C_SEL if self.focus == name else EDGE
            pygame.draw.rect(surface, edge, rect, 2 if self.focus == name
                             else 1)
            shown = self.buf + "|" if self.focus == name \
                else str(self._value(box, name))
            self._text(surface, shown, (rect.x + 6, rect.y + 6), 14,
                       C_ITX if ok[name] else (110, 118, 140), clip=rect)
        if "font_scale" in box.style:
            self._text(surface, "Text size", (r.x, d.font_y + 6), 13,
                       C_HELP_HDR)
            self._button_draw(surface, d.font_minus, "-")
            self._button_draw(surface, d.font_plus, "+")
            self._text(surface, f"{box.style['font_scale']:.1f}",
                       (r.x + int(148 * r.s), d.font_y + 6), 14, C_ITX)
        hint = ("Drag the box to move it, drag a handle to resize it. "
                "Arrow keys nudge by 1, Shift by 5.")
        for i, line in enumerate(textwrap.wrap(hint, max(20, int(r.w / 7)))):
            self._text(surface, line, (r.x, d.hint_y + i * int(15 * r.s)),
                       11, C_FTX)
