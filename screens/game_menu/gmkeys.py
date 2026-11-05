"""The hotkeys window — HD EXTENSION `hotkey_remap` (work order 364).

Opened from the OrionLayer window's SYSTEM tab ("Hotkeys"), closed back to it
by BACK, the X or ESC. MOO2 has no such window: its keys are fixed. The game
knows nothing of it and nothing is sent; every choice goes into the player's
settings (`core.hotkeys`, written as the rows' values are).

IN IT: a selector that steps through the screens with listed keys (`core.
hotkeys.TABLE`), and for the chosen screen one row per action: its name, the
original's key and the key it has now. A click on the key starts a choice —
"Press a key" — and the next letter or digit becomes the action's key; ESC
cancels it. A key another action has is refused with a word, never swapped.
RESET gives the screen its original keys back.

ONE GEOMETRY (decision 5): `geometry` is the only place the window's rects
are computed — for drawing and for clicking.
"""
import logging

import pygame

from core import hotkeys, lang
from core import mouse as mouse_input
from core.hud import art
from core.hud import blocks as hud
from core.hud import text as hudtext
from . import gmorion, olwin

log = logging.getLogger("game_menu")

#: The rows' room: the most actions a screen lists (combat, 10).
MAX_ROWS = 10


class Window:
    """What the window shows: the screen being edited, the action whose key
    is being chosen (its original key) and the last word said."""

    def __init__(self):
        self.index = 0
        self.capture = None
        self.message = ""


def is_open(screen):
    return getattr(screen, "hotkeys_win", None) is not None


def open_window(screen):
    screen.hotkeys_win = Window()
    log.info("game menu: hotkeys window opened")


def close(screen):
    if not is_open(screen):
        return
    gmorion.save(screen)
    screen.hotkeys_win = None
    log.info("game menu: hotkeys window closed")


def _screen_name(screen):
    return hotkeys.SCREEN_ORDER[screen.hotkeys_win.index]


def geometry(screen):
    """{name: Rect} of everything the window draws and hits; None while it
    is closed."""
    if not is_open(screen):
        return None
    ww, wh = screen.app.win_w, screen.app.win_h
    h = int(wh * olwin.HEIGHT)
    w = int(min(ww * 0.5, h * 1.0))
    win = pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)
    pad = max(8, int(win.w * 0.04))
    row = max(14, int(win.h * 0.052))
    gap = max(3, int(row * 0.22))
    out = {"window": win}
    pw = win.w - 2 * gap
    ph = max(8, int(pw / olwin.PLATE_ASPECT))
    out["plate"] = pygame.Rect(win.centerx - pw // 2, win.y + gap, pw, ph)
    k = pw / (olwin.PLATE_ASPECT * 240)
    x0, y0, x1, y1 = olwin.PLATE_TEXT
    out["title"] = pygame.Rect(out["plate"].x + int(x0 * k),
                               out["plate"].y + int(y0 * k),
                               int((x1 - x0) * k), int((y1 - y0) * k))
    s = int(row * 0.9)
    out["close"] = pygame.Rect(win.right - pad - s, win.y + pad // 2 + ph
                               // 2 - s // 2 + gap, s, s)
    y = out["plate"].bottom + gap * 3
    cw = win.w - 2 * pad
    out["prev"] = pygame.Rect(win.x + pad, y, int(row * 1.5), int(row * 1.3))
    out["next"] = pygame.Rect(win.right - pad - out["prev"].w, y,
                              out["prev"].w, out["prev"].h)
    out["screen"] = pygame.Rect(out["prev"].right + gap, y,
                                out["next"].x - out["prev"].right - 2 * gap,
                                out["prev"].h)
    y = out["prev"].bottom + gap * 2
    out["head"] = pygame.Rect(win.x + pad, y, cw, int(row * 0.8))
    y = out["head"].bottom + gap
    bottom = win.bottom - pad
    bh = int(row * 1.25)
    out["note"] = pygame.Rect(win.x + pad, bottom - bh - int(row * 1.4),
                              cw, int(row * 1.2))
    rh = min(int(row * 1.15), (out["note"].y - gap - y) // MAX_ROWS)
    for i in range(MAX_ROWS):
        r = pygame.Rect(win.x + pad, y + i * rh, cw, rh - 1)
        out[f"row_{i}"] = r
        out[f"orig_{i}"] = pygame.Rect(r.x + int(r.w * 0.58), r.y,
                                       int(r.w * 0.16), r.h)
        out[f"key_{i}"] = pygame.Rect(r.x + int(r.w * 0.78), r.y + 1,
                                      int(r.w * 0.22), r.h - 2)
    out["back"] = pygame.Rect(win.right - pad - int(win.w * 0.3),
                              bottom - bh, int(win.w * 0.3), bh)
    out["reset"] = pygame.Rect(out["back"].x - gap * 2 - int(win.w * 0.3),
                               bottom - bh, int(win.w * 0.3), bh)
    out["row_h"] = pygame.Rect(0, 0, 0, row)       # the text size's source
    return out


# ── words ──────────────────────────────────────────────
def _words(screen):
    return screen.words.get("words", {}).get("hotkeys_window", {})


def say(screen, key, default):
    return _words(screen).get(key, default)


def _size(geo):
    return max(9, int(geo["row_h"].h * 0.62))


def _text(screen, surface, text, rect, size, colour, align="left"):
    img = screen.style.render_text(text, size, tuple(colour[:3]))
    while img.get_width() > rect.w and size > 8:
        size -= 1
        img = screen.style.render_text(text, size, tuple(colour[:3]))
    x = rect.x if align == "left" else rect.x + (rect.w - img.get_width()) \
        // (2 if align == "center" else 1)
    surface.blit(img, (x, rect.y + (rect.h - img.get_height()) // 2))


def _button(screen, surface, rect, word, size, state=None):
    hud.small_button(surface, rect, screen.layout.scale,
                     state or ("hover" if rect.collidepoint(
                         mouse_input.pos()) else "normal"))
    _text(screen, surface, word, rect.inflate(-rect.w // 10, 0), size,
          gmorion.COL_OPTION, "center")


def _key_word(char):
    return char.upper()


# ── drawing ────────────────────────────────────────────
def render(screen, surface):
    if not is_open(screen):
        return
    geo = geometry(screen)
    w = screen.hotkeys_win
    scale = screen.layout.scale
    size = _size(geo)
    hud.popup(surface, geo["window"], scale)
    plate = art.fit(art.TITLE_PLATE, geo["plate"].h, geo["plate"].w)
    if plate is not None:
        surface.blit(plate, geo["plate"].topleft)
    title = hudtext.render(screen.style, say(screen, "title", "HOTKEYS"),
                           "title", geo["title"].h)
    while title.get_width() > geo["title"].w and title.get_height() > 8:
        title = pygame.transform.smoothscale(
            title, (int(title.get_width() * 0.95),
                    int(title.get_height() * 0.95)))
    hudtext.blit(surface, title, geo["title"])
    olwin._render_close(screen, surface, geo["close"], scale)
    name = _screen_name(screen)
    _button(screen, surface, geo["prev"], "<", size)
    _button(screen, surface, geo["next"], ">", size)
    _text(screen, surface, lang.tr(hotkeys.SCREEN_LABELS[name]),
          geo["screen"], int(size * 1.15), hudtext.colour("button"), "center")
    head = geo["head"]
    _text(screen, surface, say(screen, "col_action", "Action"), head, size,
          gmorion.COL_STATE)
    _text(screen, surface, say(screen, "col_original", "Original"),
          pygame.Rect(geo["orig_0"].x, head.y, geo["orig_0"].w, head.h),
          size, gmorion.COL_STATE, "center")
    _text(screen, surface, say(screen, "col_key", "Key"),
          pygame.Rect(geo["key_0"].x, head.y, geo["key_0"].w, head.h), size,
          gmorion.COL_STATE, "center")
    for i, (orig, _ident, label, now) in enumerate(
            hotkeys.entries(screen.app, name)):
        row = geo[f"row_{i}"]
        _text(screen, surface, lang.tr(label),
              pygame.Rect(row.x, row.y, geo[f"orig_{i}"].x - row.x, row.h),
              size, hudtext.colour("button"))
        _text(screen, surface, _key_word(orig), geo[f"orig_{i}"], size,
              gmorion.COL_STATE, "center")
        asking = w.capture == orig
        word = say(screen, "press_key", "Press a key") if asking \
            else _key_word(now)
        _button(screen, surface, geo[f"key_{i}"], word, size,
                "active" if asking else ("normal" if now == orig else None))
    if w.message:
        _text(screen, surface, w.message, geo["note"], size,
              gmorion.COL_STATE)
    _button(screen, surface, geo["reset"], say(screen, "reset", "Reset"),
            size)
    hud.action_button(surface, geo["back"], scale,
                      "hover" if geo["back"].collidepoint(mouse_input.pos())
                      else "normal", say(screen, "back", "Back"), None,
                      screen.style)


# ── input ──────────────────────────────────────────────
def _step(screen, d):
    w = screen.hotkeys_win
    w.index = (w.index + d) % len(hotkeys.SCREEN_ORDER)
    w.capture = None
    w.message = ""


def handle_click(screen, x, y):
    """Every click while the window is up lands here; nothing is sent."""
    geo = geometry(screen)
    w = screen.hotkeys_win
    if geo["close"].collidepoint(x, y) or geo["back"].collidepoint(x, y):
        close(screen)
        return
    if geo["prev"].collidepoint(x, y):
        _step(screen, -1)
        return
    if geo["next"].collidepoint(x, y):
        _step(screen, 1)
        return
    name = _screen_name(screen)
    if geo["reset"].collidepoint(x, y):
        hotkeys.reset(screen.app, name)
        gmorion.save(screen)
        w.capture, w.message = None, say(screen, "was_reset",
                                         "The original keys are back.")
        return
    for i, (orig, _id, _label, _now) in enumerate(
            hotkeys.entries(screen.app, name)):
        if geo[f"key_{i}"].collidepoint(x, y):
            w.capture = None if w.capture == orig else orig
            w.message = ""
            return
    w.capture = None


def handle_key_event(screen, event):
    """A key while the window is up: the one being chosen, or ESC."""
    w = screen.hotkeys_win
    if event.key == pygame.K_ESCAPE:
        if w.capture is not None:
            w.capture, w.message = None, ""
        else:
            close(screen)
        return
    if w.capture is None:
        return
    # the key's own code, which is what `hotkeys.translate` compares, and
    # none of the keys it lets through (Alt, Ctrl, Meta)
    char = chr(event.key) if 32 <= event.key < 127 and not (
        getattr(event, "mod", 0) & hotkeys.BLOCKING_MODS) else ""
    why = hotkeys.rebind(screen.app, _screen_name(screen), w.capture, char)
    if why == "key":
        w.message = say(screen, "bad_key", "Only a letter or a digit.")
        return
    if why == "reserved":
        w.message = say(screen, "reserved",
                        "That key has another job on this screen.")
        return
    if why == "taken":
        w.message = say(screen, "taken", "That key is already used.")
        return
    w.capture, w.message = None, ""
    gmorion.save(screen)
