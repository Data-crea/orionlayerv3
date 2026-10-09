"""The battle's scan view and board popup in HD — work order 199 C1.

Until 199 both were the "F12 to answer" notice (open fix 52 reports them as
66 and 67, but nothing said what they showed). Open fix 66's CPOP carries
it (`core/combatpopup.py`), and the scan view's contents are a unit's CMBT
record, which HD already holds.

THE BOARD POPUP (67) — `CMBTDRW1::Board_Popup_`, cmbtdrw1.cpp:1581-1666,
drawn by `Draw_Board_Popup_` (:2744-2763): the game's message (KENTEXT 41),
the range's two ends and the marines chosen between them, the bar, the two
arrows that step the choice, RAID and CAPTURE, ESC to cancel. TRANSCRIPTION
`board_popup`: HD shows the CHOICE FROM THE WIRE (`_g_var`), never one of its own, and an
arrow is the original's own button field (164, 253) / (406, 253) — the
next only after the last one's effect has arrived (decision 21) — and
steps as the original's do: down while the choice is above 0, up while it
is below the range's top (:1638-1644). RAID and CAPTURE are the button
fields at (163, 273) and (345, 273); ESC is the popup's own hotkey.

TRANSCRIPTION `board_slider` (work order 200, replacing 199's omission):
the bar is the original's scroll field (`Add_Scroll_Field_(0xBB, 0xF9, min,
max + 1, min, max, 0xCF, 0xD, &_g_var)`, :1602) and dragging it sets the
choice as `Find_Bar_Position_` does (fields.cpp:1720-1762): the pointer's
place along the field's 207 px, times the range (max + 1 - min), over the
width, plus min, held to min .. max. HD's bar is that field drawn wider;
while the pointer drags it the bar shows the choice the place gives, and on
release HD clicks the field at the place the original's arithmetic maps to
that choice — open fix 3 keeps an injected click's pointer until the game
has read it — and the choice on the wire is the one shown after.

THE SCAN VIEW (66) — `Detailed_View_Ship_` / `Combat_Draw_View_Ship_`
(cmbtdrw1.cpp:156-247, :3114-…): one unit, large, its combat bonuses, crew,
marines, drive, armour, structure, speed, computer and weapons; any click
closes it. TRANSCRIPTION `scan_contents`: WHAT it shows and when it closes; DEVIATION
`scan_view` (with `hud_panel`): a HUD popup in OrionLayer's words over the
battle, not COMBAT.LBX 5. HD's SCAN button opens it LOCALLY and sends
nothing — the original's scan changes nothing in the game (it reads
`_combat_data[i]` into a copy, cmbtdrw1.cpp:1550) — HD EXTENSION
`scan_local`; when the ENGINE is in its scan view (only reachable under
F12), HD draws the unit CPOP names and a click activates the view's own
full-screen exit field.
"""
import time

import pygame

from core import combatpopup
from core import msgbox
from core import textfit
from core.hud import blocks as hud
from core.hud import text as hudtext

#: Board_Popup_'s four buttons, by their native top-left (cmbtdrw1.cpp:1603-1607).
BOARD_FIELDS = {"less": (0xA4, 0xFD), "more": (0x196, 0xFD),
                "raid": (0xA3, 0x111), "capture": (0x159, 0x111)}
ESC = 27
ARROW_WAIT = 3.0           # s: an arrow whose effect never arrives
#: the board popup's scroll field (cmbtdrw1.cpp:1602): x, y, width, height
SLIDER = (0xBB, 0xF9, 0xCF, 0xD)


def slider_value(native_x, low, high):
    """`Find_Bar_Position_` for the popup's field (range max + 1)."""
    x, _y, w, _h = SLIDER
    if native_x >= x + w:
        v = high + 1
    elif native_x <= x:
        v = low
    else:
        v = (native_x - x) * (high + 1 - low) // w + low
    return max(low, min(high, v))


def slider_point(value, low, high):
    """The native point inside the field whose bar position is `value`:
    the middle of the pixels that map to it."""
    x, y, w, h = SLIDER
    span = high + 1 - low
    return x + int((value - low + 0.5) * w / span), y + h // 2


def board_field(fields, key):
    """The board popup's own field for `key`, by its native position."""
    x, y = BOARD_FIELDS[key]
    return next((f for f in fields or [] if f.index and f.x == x and
                 f.y == y and f.field_type == 0), None)


def exit_field(fields):
    """The scan view's exit: one hidden field over the whole screen
    (cmbtdrw1.cpp:221, `Add_Hidden_Field_(0, 0, 0x27F, 0x1DF)`)."""
    return next((f for f in fields or [] if f.index and
                 (f.x, f.y, f.x_end, f.y_end) == (0, 0, 0x27F, 0x1DF)), None)


def engine_popup(state):
    """CPOP while the engine is IN the scan view or the board popup of the
    battle on the wire, else None."""
    cp = getattr(state, "combat_popup", None)
    combat = getattr(state, "combat", None)
    if cp is None or combat is None or cp["serial"] != combat["serial"] or \
            getattr(state, "current_screen", None) != cp["screen"]:
        return None
    return cp


class Popups:
    def __init__(self):
        self.scan_mode = False       # SCAN lit: the next unit clicked is scanned
        self.local_unit = None       # HD's own scan view of this unit
        self.rects = {}
        self._pending = None         # (marines before, time) after an arrow
        self._drag = None            # (low, high, value) while the bar is held

    def reset(self):
        self.scan_mode, self.local_unit, self._pending = False, None, None
        self._drag = None

    def showing(self, state):
        """'board', 'scan' (the engine's), 'local' or None."""
        cp = engine_popup(state)
        if cp is not None:
            return "board" if cp["screen"] == combatpopup.BOARD else "scan"
        return "local" if self.local_unit is not None else None

    # ── drawing ────────────────────────────────────────────────────
    def draw(self, surface, style, scale, state, shown, names):
        """Over the battle as it is drawn this frame, dimmed as every box
        (`msgbox.dimmed_base`, work order 196 A: the screen stays visible)."""
        kind = self.showing(state)
        self.rects = {}
        if kind is None:
            return
        surface.blit(msgbox.dimmed_base(surface, None, msgbox.DIM_ALPHA),
                     (0, 0))
        if kind == "board":
            self._draw_board(surface, style, scale, engine_popup(state))
        else:
            cp = engine_popup(state)
            i = cp["unit"] if kind == "scan" else self.local_unit
            if shown and 0 <= i < len(shown["units"]):
                self._draw_scan(surface, style, scale, shown["units"][i],
                                names)

    @staticmethod
    def _k(surface):
        w, h = surface.get_size()
        return min(w / 1920, h / 1080)

    def _box(self, surface, scale, w_ref, inner_h):
        """A popup `w_ref` reference px wide round content `inner_h` device
        px high — the content is measured first, so the box fits it."""
        w, h = surface.get_size()
        k = self._k(surface)
        rect = pygame.Rect(0, 0, int(w_ref * k), inner_h + int(40 * k))
        rect.center = (w // 2, int(h * 0.42))
        hud.popup(surface, rect, scale)
        return rect.inflate(-int(48 * k), -int(40 * k)), k

    def _draw_board(self, surface, style, scale, cp):
        k = self._k(surface)
        size = max(10, int(26 * k))
        lines = textfit.wrap_rendered(style, cp["message"], size,
                                      int((820 - 48) * k),
                                      hudtext.colour("value"))
        bh = max(size + 10, int(46 * k))
        inner, k = self._box(surface, scale, 820, sum(
            ln.get_height() + 4 for ln in lines) + int(18 * k) + size +
            int(14 * k) + bh // 2 + int(34 * k) + bh + int(8 * k))
        y = inner.y
        for line in lines:
            hudtext.blit(surface, line, pygame.Rect(inner.x, y, inner.w,
                                                    line.get_height()))
            y += line.get_height() + 4
        # the range and the choice (Draw_Board_Popup_, :2750-2762)
        y += int(18 * k)
        cols = (inner.x + inner.w // 6, inner.centerx, inner.right - inner.w // 6)
        for x, v in zip(cols, (cp["min"], cp["marines"], cp["max"])):
            t = style.render_text(str(v), size, hudtext.colour(
                "value" if v == cp["marines"] else "label")[:3])
            surface.blit(t, t.get_rect(midtop=(x, y)))
        y += size + int(14 * k)
        bar = pygame.Rect(cols[0], y, cols[2] - cols[0], max(6, int(16 * k)))
        hud.field(surface, bar, scale)
        self.rects["bar"] = bar
        span = max(1, cp["max"] - cp["min"])
        shown = self._drag[2] if self._drag else cp["marines"]
        fill = bar.copy()
        fill.w = int(bar.w * (shown - cp["min"]) / span)
        pygame.draw.rect(surface, hudtext.colour("value")[:3], fill)
        less = pygame.Rect(bar.x - bh - 8, bar.centery - bh // 2, bh, bh)
        more = pygame.Rect(bar.right + 8, bar.centery - bh // 2, bh, bh)
        busy = self._pending is not None
        for key, r, word in (("less", less, "<"), ("more", more, ">")):
            hud.small_button(surface, r, scale, "disabled" if busy else
                             "normal", word, style_renderer=style)
            self.rects[key] = r
        y = bar.bottom + int(34 * k)
        bw = (inner.w - int(40 * k)) // 2
        for n, (key, word) in enumerate((("raid", "RAID"),
                                         ("capture", "CAPTURE"))):
            r = pygame.Rect(inner.x + n * (bw + int(40 * k)), y, bw, bh)
            hud.small_button(surface, r, scale, "normal", word,
                             style_renderer=style)
            self.rects[key] = r

    def _draw_scan(self, surface, style, scale, unit, names):
        k = self._k(surface)
        size, small = max(10, int(30 * k)), max(9, int(22 * k))
        n = max(12, sum(1 for w in unit["weapons"]
                        if w["count"] > 0 and w["weapon_id"] > 0))
        inner, k = self._box(surface, scale, 900, size + int(20 * k) +
                             n * (small + int(10 * k)))
        name = style.render_text(unit["name"], size,
                                 hudtext.colour("value")[:3])
        surface.blit(name, name.get_rect(midtop=(inner.centerx, inner.y)))
        y = inner.y + size + int(20 * k)
        sign = lambda v: f"{v:+d}"          # Build_Signed_Bonus_String
        rows = [("Beam attack", sign(unit["tac_val_attack"])),
                ("Beam defense", sign(unit["tac_val_defense"])),
                ("Missile evasion", sign(unit["tac_val_evade"])),
                ("Crew level", str(unit["crew_quality"])),
                ("Marines", str(unit["marine_count"])
                 if unit["marine_count"] != 255 else None),
                ("Drive", f"{unit['drive_current_hits']} / "
                          f"{unit['drive_max_hits']}"),
                ("Computer", f"{unit['computer_current_hits']} / "
                             f"{unit['computer_max_hits']}"),
                ("Structure", f"{unit['structure_max'] - unit['structure_damage']}"
                              f" / {unit['structure_max']}"),
                ("Armor", str(unit["armor_remaining"])),
                ("Shields", f"{max(unit['shield_arc_current'])} / "
                            f"{unit['shield_arc_max']}"),
                ("Combat speed", str(unit["current_speed"])),
                ("Captured", "" if unit["is_captured"] == 1 else None)]
        half = inner.w // 2 - int(20 * k)
        for label, value in rows:
            if value is None:
                continue
            for x, text, role, align in (
                    (inner.x, label, "label", "left"),
                    (inner.x, value, "value", "right")):
                surf = style.render_text(text, small,
                                         hudtext.colour(role)[:3])
                hudtext.blit(surface, surf, pygame.Rect(x, y, half,
                                                        small + 4),
                             align=align)
            y += small + int(10 * k)
        y = inner.y + size + int(20 * k)
        wx = inner.x + half + int(40 * k)
        for w in unit["weapons"]:
            if w["count"] <= 0 or w["weapon_id"] <= 0:
                continue
            word = names(w["weapon_id"]) or f"weapon {w['weapon_id']}"
            surf = style.render_text(f"{w['count']}  {word}", small,
                                     hudtext.colour("label")[:3])
            hudtext.blit(surface, surf, pygame.Rect(wx, y, half, small + 4),
                         align="left")
            y += small + int(10 * k)

    # ── input ──────────────────────────────────────────────────────
    def click(self, x, y, state, client):
        """True when a popup took the click."""
        kind = self.showing(state)
        if kind is None:
            return False
        if kind == "local":
            self.local_unit = None          # any click closes it (:221)
            return True
        fields = getattr(state, "fields", None)
        if kind == "scan":
            f = exit_field(fields)
            if f is not None:
                client.activate_field(f.index)
            return True
        cp = engine_popup(state)
        if self._pending and (cp["marines"] != self._pending[0] or
                              time.monotonic() - self._pending[1] > ARROW_WAIT):
            self._pending = None
        key = next((k for k, r in self.rects.items()
                    if r.collidepoint(x, y)), None)
        if key is None or (key in ("less", "more", "bar") and self._pending):
            return True
        if key == "bar":                    # the scroll field, held
            self._drag = (cp["min"], cp["max"], None)
            self.motion(x)
            return True
        if key == "less" and cp["marines"] <= 0 or \
                key == "more" and cp["marines"] >= cp["max"]:
            return True                     # the original's own guards (:1638-1644)
        f = board_field(fields, key)
        if f is not None:
            client.activate_field(f.index)
            if key in ("less", "more"):
                self._pending = (cp["marines"], time.monotonic())
        return True

    def _native_x(self, x):
        bar = self.rects["bar"]
        return SLIDER[0] + (x - bar.x) * SLIDER[2] / max(1, bar.w)

    def motion(self, x):
        """The bar under the pointer shows the choice its place gives."""
        if self._drag and "bar" in self.rects:
            low, high, _v = self._drag
            self._drag = (low, high, slider_value(int(self._native_x(x)),
                                                  low, high))

    def release(self, state, client):
        """Letting go of the bar clicks the scroll field at the place that
        gives the shown choice; the wire's choice is shown after."""
        drag, self._drag = self._drag, None
        cp = engine_popup(state)
        if not drag or drag[2] is None or cp is None or \
                drag[2] == cp["marines"]:
            return
        f = next((f for f in getattr(state, "fields", None) or []
                  if f.index and (f.x, f.y) == SLIDER[:2]), None)
        if f is not None:
            client.inject_click(*slider_point(drag[2], cp["min"], cp["max"]))
            self._pending = (cp["marines"], time.monotonic())

    def cancel(self):
        """The bar let go while HD holds its frame or shows the game's
        picture (work order 226 A, D13): the drag ends, nothing is sent."""
        self._drag = None

    def key(self, key, state, client):
        """ESC: the board popup's own hotkey; closes HD's scan view."""
        kind = self.showing(state)
        if kind is None or key != pygame.K_ESCAPE:
            return kind is not None
        if kind == "local":
            self.local_unit = None
        elif kind == "board":
            f = next((f for f in getattr(state, "fields", None) or []
                      if f.index and f.hotkey == ESC), None)
            if f is not None:
                client.activate_field(f.index)
        else:
            f = exit_field(getattr(state, "fields", None))
            if f is not None:
                client.activate_field(f.index)
        return True

    def update(self, state):
        """Clear the arrow's wait once its effect is on the wire."""
        cp = engine_popup(state)
        if self._pending and (cp is None or cp["marines"] != self._pending[0]):
            self._pending = None
