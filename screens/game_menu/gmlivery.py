"""The livery window — work order 220, Data's decisions 1-6, 8 and 9.

HD EXTENSION `livery` (`core/livery.py`): MOO2 has no such window and draws
eight drawings of a ship, one per colour. Opened from Game Settings' "Livery"
button (on the Painted detail row, shown only while the mod folder is on and
holds painted ships with masks — decision 2), closed back to the settings by
BACK or ESC. The game knows nothing about it: the Settings dialog stays up
under it, nothing is sent, and every choice goes into the player's settings
(`core.usersettings`, written by `gmorion.save` as the rows' values are).

IN IT: the preview — a painted ship in the player's own colour, large, the
hull type and look stepped through; under it the same livery on all eight
owners' colours, small, the second colour on the player's own only
(decision 8) — and the choices: the pattern, stepped through one by one
(decision 3); the core variant (decision 4); the second colour, any colour
or none (decision 5), not available under Full; the strength (decision 9);
RESET to the defaults.

THE PREVIEW IS THE BATTLE'S OWN CODE (part B): two `CombatArt`s draw it
through `CombatArt.ship` — the battle's recolour, masks and all — with the
window's livery set on them (`set_livery`), the large one holding painted
pictures at 8 x, the small row at 2 x. Nothing here colours a pixel.

THE COLOUR CONTROL is the frame colour's (`gmorion`): three bars, a hue, a
saturation and a brightness bar, drawn and hit by the same mapping
(`gmorion.bar_value`, `bar_x`). Its colours are not: the frame colour turns
the panel edge's measured colour within floors (`core.hud.tint`), which
cannot reach a black or a white; the second colour is any HSV colour.

ONE GEOMETRY (decision 5): `geometry` is the only place the window's rects
are computed — for drawing, clicking and the right-click help.
"""
import colorsys
import logging

import pygame

from core import livery
from core import mouse as mouse_input
from core.hud import blocks as hud

from . import gmorion

log = logging.getLogger("game_menu")

#: The help regions' node while the window is up (help.json `node`).
NODE = "livery"
#: Hull types in picture order: picture = hull * 8 + look - 1 (looks 1-8);
#: picture 43 is the Doom Star (one look).
HULLS = ("frigate", "destroyer", "cruiser", "battleship", "titan")
DOOM_STAR = 43
#: The factor the preview holds painted pictures at: the large ship at the
#: finest a mod gives (8 x), the row of eight small.
PREVIEW_DETAIL, ROW_DETAIL = 8, 2
#: The window's size in the game window: a share of its width, capped by its
#: height (wide screens), and of its height.
WIDTH, WIDTH_BY_HEIGHT, HEIGHT = 0.70, 1.30, 0.80
#: The right column's rows, top to bottom (`geometry`).
ROWS = ("pattern_label", "pattern", "core_label", "core", "second_label",
        "hue", "sat", "val", "strength", "note")
BARS = ("hue", "sat", "val", "strength")

COL_LABEL = gmorion.COL_HEADING
COL_TEXT = gmorion.COL_OPTION
COL_STATE = gmorion.COL_STATE


def is_open(screen):
    return getattr(screen, "livery", None) is not None


def own_colour(screen):
    """The player's colour index from the game's player records, else 0."""
    state = getattr(screen, "state", None)
    try:
        from screens.combat import cbdraw
        return cbdraw.player_colours(state).get(
            int(getattr(state, "player_num", 0) or 0), 0)
    except Exception:          # no records on the wire: the first colour
        return 0


class Window:
    """What the window shows: the livery being composed and the ship."""

    def __init__(self, screen):
        self.own = own_colour(screen)
        self.liv = livery.from_settings(gmorion._settings(screen), self.own)
        self.offer = livery.offered()
        masked = [p for p, pats in self.offer.items() if pats]
        self.pictures = sorted(self.offer)
        self.picture = masked[0] if masked else (self.pictures[0]
                                                 if self.pictures else 0)
        found = {p for pats in self.offer.values() for p in pats}
        self.patterns = ("full",) + tuple(p for p in livery.MASK_PATTERNS
                                          if p in found)
        self.hsv = (colorsys.rgb_to_hsv(*(c / 255 for c in self.liv.second))
                    if self.liv.second is not None else (0.0, 1.0, 1.0))
        self.drag = None
        self.big = self.small = None
        self._shown = {}

    def arts(self):
        """The two `CombatArt`s, made when first drawn."""
        if self.big is None:
            from screens.combat import cbart
            self.big, self.small = cbart.CombatArt(), cbart.CombatArt()
            self.big.set_detail(PREVIEW_DETAIL)
            self.small.set_detail(ROW_DETAIL)
        return self.big, self.small


def open_window(screen):
    screen.livery = Window(screen)
    log.info("game menu: livery window opened (%r, ships %s)",
             screen.livery.liv, screen.livery.pictures)


def close(screen):
    """Back to the settings: the choices are in the settings already; the
    file is written now too, and the preview's pictures are let go."""
    if is_open(screen):
        gmorion.save(screen)
        screen.livery = None


def _choose(screen, **change):
    w = screen.livery
    now = {"pattern": w.liv.pattern, "core": w.liv.core,
           "second": w.liv.second, "strength": w.liv.strength}
    now.update(change)
    w.liv = livery.Livery(own=w.own, **now)
    settings = gmorion._settings(screen)
    if settings is not None:
        livery.store(settings, w.liv)


def reset(screen):
    w = screen.livery
    w.hsv = (0.0, 1.0, 1.0)
    _choose(screen, pattern=livery.DEFAULT_PATTERN, core=livery.DEFAULT_CORE,
            second=livery.DEFAULT_SECOND, strength=livery.DEFAULT_STRENGTH)
    if w.liv.pattern not in w.patterns:
        _choose(screen, pattern="full")


# ── geometry (decision 5) ────────────────────────────────────────────
def geometry(screen):
    """{name: Rect} of everything the window draws and hits."""
    ww, wh = screen.app.win_w, screen.app.win_h
    w = int(min(ww * WIDTH, wh * WIDTH_BY_HEIGHT))
    h = int(wh * HEIGHT)
    win = pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)
    # over the Settings dialog, covering it: no edge of it shows around
    body = next((b.screen_rect for b in screen.boxes
                 if b.name == "body" and b.screen_rect), None)
    if body is not None:
        win = win.union(body.inflate(2, 2))
        win.x = max(0, min(win.x, ww - win.w))
    pad = max(8, int(w * 0.03))
    inner = win.inflate(-2 * pad, -2 * pad)
    gap = max(4, int(inner.h * 0.012))
    row = max(14, int(inner.h * 0.058))
    out = {"window": win, "title": pygame.Rect(inner.x, inner.y, inner.w,
                                               int(row * 1.2))}
    bottom = pygame.Rect(inner.x, inner.bottom - row, inner.w, row)
    bw = int(inner.w * 0.18)
    out["back"] = pygame.Rect(bottom.right - bw, bottom.y, bw, row)
    out["reset"] = pygame.Rect(out["back"].x - gap * 2 - bw, bottom.y, bw,
                               row)
    owners_h = int(inner.h * 0.14)
    out["owners"] = pygame.Rect(inner.x, bottom.y - gap * 2 - owners_h,
                                inner.w, owners_h)
    top = out["title"].bottom + gap
    left_w = int(inner.w * 0.50)
    right_x = inner.x + left_w + int(inner.w * 0.04)
    right = pygame.Rect(right_x, top, inner.right - right_x,
                        out["owners"].y - gap * 2 - top)
    # the left column: the preview, then the hull and the look steppers
    out["look"] = pygame.Rect(inner.x, out["owners"].y - gap * 2 - row,
                              left_w, row)
    out["hull"] = pygame.Rect(inner.x, out["look"].y - gap - row, left_w,
                              row)
    out["preview"] = pygame.Rect(inner.x, top, left_w,
                                 out["hull"].y - gap * 2 - top)
    # the right column, row by row
    rh = right.h / len(ROWS)
    for i, name in enumerate(ROWS):
        out[name] = pygame.Rect(right.x, int(right.y + i * rh), right.w,
                                int(rh) - 1)
    for name in ("hull", "look", "pattern"):
        r = out[name]
        out[name + "_prev"] = pygame.Rect(r.x, r.y, r.h, r.h)
        out[name + "_next"] = pygame.Rect(r.right - r.h, r.y, r.h, r.h)
    core = out["core"]
    n = len(livery.CORES)
    cw = (core.w - (n - 1) * gap) // n
    for i, name in enumerate(livery.CORES):
        out["core_" + name] = pygame.Rect(core.x + i * (cw + gap), core.y,
                                          cw, core.h)
    lab = out["second_label"]
    out["second_none"] = pygame.Rect(lab.right - bw, lab.y, bw, lab.h)
    out["second_swatch"] = pygame.Rect(out["second_none"].x - gap * 2 -
                                       lab.h, lab.y, lab.h, lab.h)
    for name in BARS:
        r = out[name]
        bh = max(4, int(r.h * 0.45))
        out[name + "_bar"] = pygame.Rect(r.x + int(r.w * 0.30),
                                         r.y + (r.h - bh) // 2,
                                         int(r.w * 0.70), bh)
        out[name + "_label"] = pygame.Rect(r.x, r.y, int(r.w * 0.28), r.h)
    out["second"] = out["second_label"].union(out["val"])
    return out


# ── drawing ──────────────────────────────────────────────────────────
def _words(screen):
    return screen.words.get("words", {}).get("livery", {})


def _say(screen, key, default=None):
    return _words(screen).get(key, default if default is not None else key)


def _text(screen, surface, text, rect, size, colour, align="left"):
    img = screen.style.render_text(text, size, tuple(colour[:3]))
    while img.get_width() > rect.w and size > 8:
        size -= 1
        img = screen.style.render_text(text, size, tuple(colour[:3]))
    x = rect.x if align == "left" else \
        rect.x + (rect.w - img.get_width()) // 2
    surface.blit(img, (x, rect.y + (rect.h - img.get_height()) // 2))


def _button(screen, surface, rect, label, size, state=None):
    if state is None:
        state = "hover" if rect.collidepoint(mouse_input.pos()) else "normal"
    hud.small_button(surface, rect, screen.layout.scale, state)
    _text(screen, surface, label, rect.inflate(-rect.h // 3, 0), size,
          COL_TEXT if state != "disabled" else COL_STATE, "centre")


def _stepper(screen, surface, geo, name, label, size):
    _button(screen, surface, geo[name + "_prev"], "<", size)
    _button(screen, surface, geo[name + "_next"], ">", size)
    r = geo[name]
    mid = pygame.Rect(geo[name + "_prev"].right, r.y,
                      geo[name + "_next"].x - geo[name + "_prev"].right, r.h)
    _text(screen, surface, label, mid.inflate(-8, 0), size, COL_TEXT,
          "centre")


def _ship(art, liv, colour, picture):
    """The painted ship of `colour` in `liv`, cropped to its pixels, drawn
    by the battle's own `CombatArt.ship` (facing 0, glow frame 1: the ship
    at rest; frame 0 is its engines off since work order 222)."""
    art.set_livery(liv)
    pic = art.ship(colour, picture, 0, 1)
    if pic is None:
        return None
    return pic.subsurface(pic.get_bounding_rect(min_alpha=8))


def _fit(pic, rect):
    k = min(rect.w / max(1, pic.get_width()), rect.h / max(1,
                                                            pic.get_height()))
    size = (max(1, int(pic.get_width() * k)), max(1, int(pic.get_height() * k)))
    from screens.combat import cbart
    img = cbart.smooth(pic.copy(), size)
    return img, (rect.x + (rect.w - size[0]) // 2,
                 rect.y + (rect.h - size[1]) // 2)


def _shown(w, key, make):
    """The preview's scaled pictures, kept for the livery they show only."""
    if key not in w._shown:
        if len(w._shown) > 32:
            w._shown.clear()
        w._shown[key] = make()
    return w._shown[key]


def hull_label(screen, picture):
    if picture == DOOM_STAR:
        return _say(screen, "doom_star", "Doom Star")
    if 0 <= picture < 8 * len(HULLS):
        return _say(screen, HULLS[picture // 8])
    return _say(screen, "station", "Station")


def look_label(screen, picture):
    if 0 <= picture < 8 * len(HULLS):
        return _say(screen, "look", "Look {n}").format(n=picture % 8 + 1)
    return "—"


def second_rgb(hsv):
    return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(*hsv))


def render(screen, surface):
    if not is_open(screen):
        return
    w = screen.livery
    geo = geometry(screen)
    scale = screen.layout.scale
    hud.popup(surface, geo["window"], scale)
    size = screen.layout.font_size(24)
    small = screen.layout.font_size(20)
    _text(screen, surface, _say(screen, "title", "LIVERY"), geo["title"],
          screen.layout.font_size(30), COL_LABEL)
    big, row = w.arts()
    liv = w.liv
    # the preview: the player's own colour, large
    hud.panel(surface, geo["preview"], scale, dense=True)
    area = geo["preview"].inflate(-geo["preview"].w // 10,
                                  -geo["preview"].h // 10)
    shown = _shown(w, ("big", liv.key(), w.picture, area.size),
                   lambda: _scaled(big, liv, w.own, w.picture, area))
    if shown is not None:
        surface.blit(*shown)
    _stepper(screen, surface, geo, "hull", hull_label(screen, w.picture),
             size)
    _stepper(screen, surface, geo, "look", look_label(screen, w.picture),
             size)
    # the eight owners, small; the second colour on the player's own only
    hud.panel(surface, geo["owners"], scale, dense=True)
    cells = _owner_cells(geo["owners"])
    for colour, cell in enumerate(cells):
        shown = _shown(w, ("row", liv.key(), w.picture, colour, cell.size),
                       lambda c=colour, r=cell: _scaled(row, liv, c,
                                                        w.picture, r))
        if shown is not None:
            surface.blit(*shown)
        if colour == w.own:
            pygame.draw.line(surface, tuple(COL_LABEL[:3]),
                             (cell.x, cell.bottom), (cell.right, cell.bottom),
                             max(1, int(2 * scale)))
    # the choices
    _text(screen, surface, _say(screen, "pattern", "Pattern"),
          geo["pattern_label"], size, COL_LABEL)
    _stepper(screen, surface, geo, "pattern",
             _say(screen, "pattern_" + liv.pattern), size)
    _text(screen, surface, _say(screen, "core", "Core colour"),
          geo["core_label"], size, COL_LABEL)
    for name in livery.CORES:
        _button(screen, surface, geo["core_" + name],
                _say(screen, "core_" + name), small,
                "active" if liv.core == name else None)
    _render_second(screen, surface, geo, size, small)
    _text(screen, surface, _say(screen, "strength", "Strength"),
          geo["strength_label"], size, COL_LABEL)
    _render_strength(screen, surface, geo)
    _text(screen, surface, _say(screen, "note", "From the next battle on"),
          geo["note"], small, COL_STATE)
    _button(screen, surface, geo["reset"], _say(screen, "reset", "Reset"),
            size)
    _button(screen, surface, geo["back"], _say(screen, "back", "Back"), size)


def _owner_cells(area):
    inner = area.inflate(-area.h // 8, -area.h // 8)
    cw = inner.w / 8
    return [pygame.Rect(int(inner.x + i * cw), inner.y, int(cw) - 2,
                        inner.h) for i in range(8)]


def _scaled(art, liv, colour, picture, rect):
    pic = _ship(art, liv, colour, picture)
    return _fit(pic, rect) if pic is not None else None


def _render_second(screen, surface, geo, size, small):
    w = screen.livery
    off = w.liv.pattern == "full"
    _text(screen, surface, _say(screen, "second", "Second colour"),
          geo["second_label"], size, COL_LABEL)
    if off:
        _button(screen, surface, geo["second_none"],
                _say(screen, "none", "None"), small, "disabled")
        for name in ("hue", "sat", "val"):
            _text(screen, surface, _say(screen, "second_full",
                                        "Not with Full") if name == "hue"
                  else "", geo[name], small, COL_STATE)
        return
    _button(screen, surface, geo["second_none"], _say(screen, "none",
                                                      "None"), small,
            "active" if w.liv.second is None else None)
    sw = geo["second_swatch"]
    if w.liv.second is not None:
        # LOOK EXCEPTION data: a colour swatch: the livery's second colour
        surface.fill(w.liv.second, sw)
    screen.style.draw_plate(surface, sw, screen.layout.scale)
    h, s, v = w.hsv
    for name, label in (("hue", "Hue"), ("sat", "Saturation"),
                        ("val", "Brightness")):
        _text(screen, surface, _say(screen, name, label),
              geo[name + "_label"], small, COL_TEXT)
        bar = geo[name + "_bar"]
        for i in range(bar.w):
            f = i / max(1, bar.w - 1)
            hsv = (f, 1.0, 1.0) if name == "hue" else \
                (h, f, v) if name == "sat" else (h, s, f)
            pygame.draw.line(surface, second_rgb(hsv), (bar.x + i, bar.y),
                             (bar.x + i, bar.bottom - 1))
        screen.style.draw_plate(surface, bar, screen.layout.scale)
        if w.liv.second is not None:
            _thumb(screen, surface, bar,
                   {"hue": h, "sat": s, "val": v}[name], 0.0, 1.0)


def _render_strength(screen, surface, geo):
    w = screen.livery
    bar = geo["strength_bar"]
    lo, hi = livery.STRENGTH_RANGE
    core = livery.core_rgb(_owner_rgb(w.own), w.liv.core)
    for i in range(bar.w):
        f = lo + (hi - lo) * i / max(1, bar.w - 1)
        c = tuple(int(118 + (k - 118) * f) for k in core)
        pygame.draw.line(surface, c, (bar.x + i, bar.y),
                         (bar.x + i, bar.bottom - 1))
    screen.style.draw_plate(surface, bar, screen.layout.scale)
    _thumb(screen, surface, bar, w.liv.strength, lo, hi)


def _owner_rgb(colour):
    from screens.combat import cbpaint
    return cbpaint.owner_rgb(colour)


def _thumb(screen, surface, bar, value, lo, hi):
    t = max(2, int(3 * screen.layout.scale))
    x = gmorion.bar_x(bar, value, lo, hi)
    # LOOK EXCEPTION marking: the slider's position tick
    surface.fill((255, 255, 255), (x - t // 2, bar.y - t, t, bar.h + 2 * t))


# ── input ────────────────────────────────────────────────────────────
def _step(seq, now, d):
    seq = list(seq)
    i = seq.index(now) if now in seq else 0
    return seq[(i + d) % len(seq)]


def _step_hull(w, d):
    """The same look on the next hull type that has it (or the Doom Star)."""
    if not w.pictures:
        return
    hulls = sorted({p // 8 if p < 40 else p for p in w.pictures})
    now = w.picture // 8 if w.picture < 40 else w.picture
    nxt = _step(hulls, now, d)
    if nxt >= 40:
        w.picture = nxt
        return
    look = w.picture % 8 if w.picture < 40 else 0
    have = [p for p in w.pictures if p // 8 == nxt and p < 40]
    w.picture = nxt * 8 + look if nxt * 8 + look in have else have[0]


def _step_look(w, d):
    if w.picture >= 40:
        return
    have = [p for p in w.pictures if p < 40 and p // 8 == w.picture // 8]
    w.picture = _step(have, w.picture, d)


def _bar_set(screen, name, x):
    w = screen.livery
    geo = geometry(screen)
    if name == "strength":
        _choose(screen, strength=round(gmorion.bar_value(
            geo["strength_bar"], x, *livery.STRENGTH_RANGE), 2))
        return
    if w.liv.pattern == "full":
        return
    f = gmorion.bar_value(geo[name + "_bar"], x, 0.0, 1.0)
    h, s, v = w.hsv
    w.hsv = (f, s, v) if name == "hue" else (h, f, v) if name == "sat" \
        else (h, s, f)
    _choose(screen, second=second_rgb(w.hsv))


def handle_click(screen, x, y):
    """Every left click while the window is up lands here; nothing is sent."""
    w = screen.livery
    geo = geometry(screen)
    if geo["back"].collidepoint(x, y):
        close(screen)
    elif geo["reset"].collidepoint(x, y):
        reset(screen)
    elif geo["hull_prev"].collidepoint(x, y) or \
            geo["hull_next"].collidepoint(x, y):
        _step_hull(w, -1 if geo["hull_prev"].collidepoint(x, y) else 1)
    elif geo["look_prev"].collidepoint(x, y) or \
            geo["look_next"].collidepoint(x, y):
        _step_look(w, -1 if geo["look_prev"].collidepoint(x, y) else 1)
    elif geo["pattern_prev"].collidepoint(x, y) or \
            geo["pattern_next"].collidepoint(x, y):
        _choose(screen, pattern=_step(
            w.patterns, w.liv.pattern,
            -1 if geo["pattern_prev"].collidepoint(x, y) else 1))
    elif any(geo["core_" + n].collidepoint(x, y) for n in livery.CORES):
        _choose(screen, core=next(n for n in livery.CORES
                                  if geo["core_" + n].collidepoint(x, y)))
    elif geo["second_none"].collidepoint(x, y):
        if w.liv.pattern != "full":
            _choose(screen, second=None)
    else:
        for name in BARS:
            bar = geo[name + "_bar"]
            if bar.inflate(0, geo[name].h - bar.h).collidepoint(x, y):
                w.drag = name
                _bar_set(screen, name, x)
                break
    return True


def motion(screen, x, y):
    if is_open(screen) and screen.livery.drag:
        _bar_set(screen, screen.livery.drag, x)


def release(screen, x, y):
    if is_open(screen):
        screen.livery.drag = None


def help_rect(screen, spec):
    """A help.json region of the window (`livery_part`)."""
    part = spec.get("livery_part")
    if not part or not is_open(screen):
        return None
    return geometry(screen).get(part)
