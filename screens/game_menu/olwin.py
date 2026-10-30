"""The OrionLayer settings window — HD EXTENSION `orionlayer_window`, work order 251.

Data's decision of 13 October 2026: OrionLayer's own settings leave the
game's Settings dialog for a window of their own, as his mockup draws it
(`~/claude/references/251_game_menu/`), with the functions as they were —
"Es ist nur wie wir die einzelnen Punkte ablegen." Game Settings keeps
the thirteen engine rows and ACCEPT and gains one button, ORIONLAYER
SETTINGS (`gmdraw`), which opens this window over the dialog.

IN IT: the title, the close X, four tabs on the left — each its icon cut
from Data's picture (`core.hud.art.MASKS`) and its word, the chosen one
"selected" (decision 92) — the tab's heading and subtitle, its rows
(`TABS`, Data's grouping word for word), and APPLY & CLOSE. On APPEARANCE
the live preview (`olpreview`). The rows are `gmorion`'s: its controls,
its values, its saving; this module only gives them their places.

NOTHING IS SENT. The window belongs to the Settings dialog as the livery
window does: no click under it reaches the game, it closes with the
dialog, and APPLY & CLOSE, the X and ESC all write the player's settings
(`gmorion.save`) and go back to Game Settings — what ACCEPT and the
overlay's exit did for the rows before. Data's answer kept the functions;
RESET ALL of the mockup is not built (251 P1, 252); OPEN FOLDER is the
SYSTEM tab's "Open mod folder" (254, `core.openfolder`). The X keeps the
values as APPLY & CLOSE does — no cancel, as in the original's dialogs
(Data, 252 P3).

ONE GEOMETRY (decision 5): `geometry` is the only place the window's
rects are computed — for drawing, clicking and the right-click help.
"""
import logging

import pygame

from core import mouse as mouse_input
from core.hud import art
from core.hud import blocks as hud
from core.hud import text as hudtext

from . import gmorion, oldrop

log = logging.getLogger("game_menu")

#: The help regions' node while the window is up (help.json `node`).
NODE = "orionlayer"
#: Data's grouping (13 October 2026): tab -> its rows, top to bottom. The
#: livery row is there only while the livery window can do something
#: (work order 220, decision 2).
TABS = (("appearance", ("colours", "frame", "tone", "glass", "fill",
                        "fill_tone", "text_size")),
        ("gameplay", ("floor", "map_black", "monsters", "map_ships")),
        ("graphics", ("frame_rate", "idle_rate", "painted", "livery")),
        ("system", ("mods", "mod_files", "mod_open", "language")))
TAB_NAMES = tuple(name for name, _ in TABS)
#: The window in the game window: its height's share, its width capped by
#: the screen's width and by its own height.
HEIGHT, WIDTH, WIDTH_BY_HEIGHT = 0.83, 0.64, 1.25
#: Columns of a row, as shares of its width: the value column starts at
#: `value_x`, the colour bars end at `hue_end` (gmorion's rule keys), a
#: drop-down field is `field_w` wide.
#: The "Open mod folder" button is a share wider than the drop-downs: its
#: German word ("Mod-Ordner öffnen") filled it to within a pixel at some
#: window sizes, and the window follows the map's free area, which moves
#: with the HUD's boxes.
MOD_BUTTON_EXTRA = 0.04
ROW_RULE = {"value_x": 0.36, "hue_end": 0.80, "field_w": 0.36,
            "swatch_x": 0.75, "swatch_gap": 0.2}
#: The title plate's aspect: the cut piece's, 4780 x 240 (`hud_cut.TITLE`),
#: and the title's room on it: between the two orange lamps (measured on
#: the cut piece, 13 October 2026: lamps at x 1473-1583 and 3179-3296),
#: from the lit centre's top to its bottom (`blocks.TITLE_TEXT_BOX`).
PLATE_ASPECT = 4780 / 240
PLATE_TEXT = (1600, 27, 3160, 190)


class Window:
    """What the window shows: the chosen tab and an open drop-down."""

    def __init__(self):
        self.tab = TAB_NAMES[0]
        self.drop = None


def is_open(screen):
    return getattr(screen, "orionlayer", None) is not None


def open_window(screen):
    from core import openfolder
    openfolder.forget()
    screen.orionlayer = Window()
    log.info("game menu: OrionLayer settings opened")


def close(screen):
    """Back to Game Settings: the settings are written (as ACCEPT did for
    the rows); nothing is sent."""
    if not is_open(screen):
        return
    from . import gmlivery
    gmlivery.close(screen)
    gmorion.save(screen)
    screen.orionlayer = None
    log.info("game menu: OrionLayer settings closed")


def rows_of(tab):
    from core import livery
    rows = dict(TABS)[tab]
    return tuple(r for r in rows
                 if r != "livery" or livery.window_available())


def geometry(screen):
    """{name: Rect} of everything the window draws and hits; None while
    it is closed."""
    if not is_open(screen):
        return None
    ww, wh = screen.app.win_w, screen.app.win_h
    h = int(wh * HEIGHT)
    w = int(min(ww * WIDTH, h * WIDTH_BY_HEIGHT))
    win = pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)
    body = next((b.screen_rect for b in screen.boxes
                 if b.name == "body" and b.screen_rect), None)
    if body is not None:
        # over the Settings dialog, covering it: no edge of it shows round
        win = win.union(body.inflate(2, 2))
        win.x = max(0, min(win.x, ww - win.w))
    pad = max(8, int(win.w * 0.028))
    row = max(14, int(win.h * 0.052))
    gap = max(3, int(row * 0.22))
    out = {"window": win}
    pw = win.w - 2 * gap
    ph = max(8, int(pw / PLATE_ASPECT))
    out["plate"] = pygame.Rect(win.centerx - pw // 2, win.y + gap, pw, ph)
    k = pw / (PLATE_ASPECT * 240)
    x0, y0, x1, y1 = PLATE_TEXT
    out["title"] = pygame.Rect(out["plate"].x + int(x0 * k),
                               out["plate"].y + int(y0 * k),
                               int((x1 - x0) * k), int((y1 - y0) * k))
    s = int(row * 0.9)
    out["close"] = pygame.Rect(win.right - pad - s, win.y + pad // 2 + ph
                               // 2 - s // 2 + gap, s, s)
    top = out["plate"].bottom + gap * 2
    bottom = win.bottom - pad
    aw = int(win.w * 0.38)
    out["apply"] = pygame.Rect(win.right - pad - aw, bottom - int(row * 1.25),
                               aw, int(row * 1.25))
    out["footer_y"] = out["apply"].y - gap * 2
    out["note"] = pygame.Rect(win.x + pad, out["apply"].y,
                              out["apply"].x - win.x - 2 * pad,
                              out["apply"].h)
    nav = pygame.Rect(win.x + pad, top, int(win.w * 0.26),
                      out["footer_y"] - gap * 2 - top)
    out["nav"] = nav
    th = int(row * 1.45)
    for i, name in enumerate(TAB_NAMES):
        out["tab_" + name] = pygame.Rect(nav.x, nav.y + i * (th + gap),
                                         nav.w, th)
    cx = nav.right + pad
    content = pygame.Rect(cx, top, win.right - pad - cx, nav.h)
    out["content"] = content
    out["heading"] = pygame.Rect(content.x, content.y, content.w,
                                 int(row * 1.1))
    out["subtitle"] = pygame.Rect(content.x, out["heading"].bottom,
                                  content.w, int(row * 0.75))
    y = out["subtitle"].bottom + gap * 2
    tab = screen.orionlayer.tab
    if tab == "appearance":
        ph = int(content.h * 0.27)
        out["preview"] = pygame.Rect(content.x, y, content.w, ph)
        y += ph + gap * 2
    names = rows_of(tab)
    rh = min(int(row * 1.05), (content.bottom - y) // max(1, len(names)))
    for i, name in enumerate(names):
        out[name] = pygame.Rect(content.x, y + i * rh, content.w, rh - 1)
    _row_parts(out, names)
    return out


def _row_parts(out, names):
    """The controls inside the rows: the drop-down fields, the swatches,
    the livery button, and gmorion's bars (its own geometry functions)."""
    for name in names:
        r = out[name]
        if name in oldrop.CHOICES:
            fx = r.x + int(r.w * ROW_RULE["value_x"])
            fh = max(8, int(r.h * 0.78))
            fw = int(r.w * ROW_RULE["field_w"])
            if name == "glass":
                fw = int(r.w * 0.16)
            out[name + "_field"] = pygame.Rect(fx, r.y + (r.h - fh) // 2, fw,
                                               fh)
    if "livery" in out:
        r = out["livery"]
        fh = max(8, int(r.h * 0.78))
        out["livery_button"] = pygame.Rect(
            r.x + int(r.w * ROW_RULE["value_x"]), r.y + (r.h - fh) // 2,
            int(r.w * 0.22), fh)
    if "mod_open" in out:
        r = out["mod_open"]
        fh = max(8, int(r.h * 0.78))
        out["mod_open_button"] = pygame.Rect(
            r.x + int(r.w * ROW_RULE["value_x"]), r.y + (r.h - fh) // 2,
            int(r.w * (ROW_RULE["field_w"] + MOD_BUTTON_EXTRA)), fh)
    if "colours" in out:
        gmorion.swatch_geometry(out, ROW_RULE)
    if "frame" in out:
        gmorion.colour_geometry(out, ROW_RULE)


def help_rect(screen, spec):
    geo = geometry(screen)
    return geo.get(spec.get("ol_part")) if geo else None


# ── input ────────────────────────────────────────────────────────────
def handle_click(screen, x, y):
    """Every click while the window is up lands here; nothing is sent."""
    geo = geometry(screen)
    w = screen.orionlayer
    if w.drop is not None:
        oldrop.handle_click(screen, geo, x, y)
        return
    if geo["close"].collidepoint(x, y) or geo["apply"].collidepoint(x, y):
        close(screen)
        return
    for name in TAB_NAMES:
        if geo["tab_" + name].collidepoint(x, y):
            w.tab = name
            return
    gmorion.handle_click(screen, x, y)


def handle_key(screen, key):
    """ESC closes an open list, else the window; no key reaches the game."""
    if key != pygame.K_ESCAPE:
        return
    if screen.orionlayer.drop is not None:
        screen.orionlayer.drop = None
    else:
        close(screen)


# ── drawing ──────────────────────────────────────────────────────────
def _words(screen):
    return screen.words.get("words", {}).get("orionlayer_window", {})


def say(screen, key, default):
    return _words(screen).get(key, default)


def render(screen, surface):
    if not is_open(screen):
        return
    geo = geometry(screen)
    scale = screen.layout.scale
    hud.popup(surface, geo["window"], scale)
    plate = art.fit(art.TITLE_PLATE, geo["plate"].h, geo["plate"].w)
    if plate is not None:
        surface.blit(plate, geo["plate"].topleft)
    title = hudtext.render(screen.style, say(screen, "title",
                                             "ORIONLAYER SETTINGS"),
                           "title", geo["title"].h)
    while title.get_width() > geo["title"].w and title.get_height() > 8:
        title = pygame.transform.smoothscale(
            title, (int(title.get_width() * 0.95),
                    int(title.get_height() * 0.95)))
    hudtext.blit(surface, title, geo["title"])
    _render_close(screen, surface, geo["close"], scale)
    _render_tabs(screen, surface, geo, scale)
    win = geo["window"]
    hud.separator(surface, geo["nav"].y, geo["nav"].bottom,
                  geo["nav"].right + (geo["content"].x - geo["nav"].right)
                  // 2, scale, vertical=True)
    hud.separator(surface, win.x + win.w // 40, win.right - win.w // 40,
                  geo["footer_y"], scale)
    _render_heading(screen, surface, geo)
    if "preview" in geo:
        from . import olpreview
        olpreview.render(screen, surface, geo["preview"])
    gmorion.render(screen, surface)
    _render_footer(screen, surface, geo, scale)
    oldrop.render_list(screen, surface, geo)


def _state(rect):
    return "hover" if rect.collidepoint(mouse_input.pos()) else "normal"


def _render_close(screen, surface, rect, scale):
    hud.small_button(surface, rect, scale, _state(rect))
    col = hudtext.colour("button")
    m = rect.w // 3
    w = max(2, rect.w // 12)
    # LOOK EXCEPTION marking: the close button's cross, in the button word's colour
    pygame.draw.line(surface, col, (rect.x + m, rect.y + m),
                     (rect.right - m, rect.bottom - m), w)
    pygame.draw.line(surface, col, (rect.right - m, rect.y + m),
                     (rect.x + m, rect.bottom - m), w)


def _render_tabs(screen, surface, geo, scale):
    for name in TAB_NAMES:
        r = geo["tab_" + name]
        on = screen.orionlayer.tab == name
        hud.small_button(surface, r, scale, "active" if on else _state(r))
        col = hudtext.colour("button")
        ic = art.mask(name, int(r.h * 0.5), col)
        x = r.x + int(r.h * 0.3)
        if ic is not None:
            surface.blit(ic, (x, r.y + (r.h - ic.get_height()) // 2))
            x += ic.get_width() + int(r.h * 0.25)
        word = hudtext.render(screen.style,
                              say(screen, "tab_" + name, name).upper(),
                              "button", r.h, col)
        room = r.right - x - int(r.h * 0.15)
        if word.get_width() > room > 0:
            word = pygame.transform.smoothscale(
                word, (room, max(1, word.get_height() * room
                                 // word.get_width())))
        hudtext.blit(surface, word, pygame.Rect(x, r.y, r.right - x, r.h),
                     align="left")


def _render_heading(screen, surface, geo):
    tab = screen.orionlayer.tab
    head = hudtext.render(screen.style, say(screen, "tab_" + tab, tab)
                          .upper(), "title", geo["heading"].h)
    hudtext.blit(surface, head, geo["heading"], align="left")
    sub = screen.style.render_text(
        say(screen, "sub_" + tab, ""),
        screen.layout.font_size(20 * getattr(screen, "content_scale", 1.0)),
        tuple(gmorion.COL_STATE[:3]))
    hudtext.blit(surface, sub, geo["subtitle"], align="left", ink=False)


def _render_footer(screen, surface, geo, scale):
    r = geo["apply"]
    hud.action_button(surface, r, scale, _state(r),
                      say(screen, "apply", "Apply & Close"), None,
                      screen.style)
    for rect, line in zip(_note_lines(geo["note"], len(notes(screen))),
                          notes(screen)):
        size = screen.layout.font_size(20 * getattr(screen, "content_scale",
                                                    1.0))
        img = screen.style.render_text(line, size,
                                       tuple(gmorion.COL_STATE[:3]))
        while img.get_width() > rect.w and size > 8:
            size -= 1
            img = screen.style.render_text(line, size,
                                           tuple(gmorion.COL_STATE[:3]))
        hudtext.blit(surface, img, rect, align="left", ink=False)


def notes(screen):
    """The footer's lines beside APPLY & CLOSE: "Restart to apply" while a
    value waits for the next start, and the mod folder's path when no file
    manager could show it (254, Data: "show the folder path instead")."""
    from core import lang, openfolder
    words = screen.words.get("words", {}).get("orionlayer", {})
    out = []
    if gmorion.restart_pending(screen):
        out.append(words.get("restart", "Restart to apply"))
    path = openfolder.failed()
    if path:
        # the path is the player's, never translated: only the label is
        out.append(lang.tr(words.get("mod_path", "Mod folder:")) + " " + path)
    return out


def _note_lines(rect, n):
    """`n` equal lines in the footer's note rect."""
    h = rect.h // max(1, n)
    return [pygame.Rect(rect.x, rect.y + i * h, rect.w, h) for i in range(n)]
