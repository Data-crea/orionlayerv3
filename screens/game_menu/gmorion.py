"""The OrionLayer rows of the Game Settings dialog — an HD EXTENSION (fundament 63, 64).

Below the thirteen engine rows, five row heights: a divider, the
"OrionLayer" heading, the map floor lift, the player-colour preset and
the switch for the monster values in the Planets panel — and since work
order 170 a sixth, the HUD FRAME COLOUR: a hue bar and RESET (HD
EXTENSION, `core/hud/tint.py`), applied at once and saved with the
rest; the divider became a thin band so the box did not grow. MOO2 has none
of the three; the game knows nothing about these rows.

**TWO STATE SOURCES, NEVER MERGED.** The thirteen engine checkboxes
keep their local copy seeded from `s_settings` (`screen.flags`). These
rows read and write `app.user_settings` (`core.usersettings`) and
nothing else. They have no field, and a click on them — divider and
heading included — is handled here BEFORE the engine rows' `row_at` /
`send`, and sends nothing on the wire.

**ONE GEOMETRY FOR DRAWING AND CLICKING** (decision 5): `bands` is the
only place the five rects and the swatch rects are computed.

**VALUES APPLY AT ONCE, THE FILE IS WRITTEN LATER.** The floor step
shows on the map behind the popup on the next frame (`floorlift` reads
it at draw time), and the monster switch on the next Planets frame. The
preset needs a restart — `palette.init` applies it before any screen
binds a colour — and the note that says so is shown only while the
saved preset differs from the active one. The file is written by
`save`, which ACCEPT and the overlay's exit both call and which writes
nothing when nothing changed.
"""
import pygame

from core import palette, playercolors, usersettings
from core.hud import style as hudstyle
from core.hud import tint

BANDS = ("divider", "heading", "floor", "colours", "monsters", "frame",
         "tone")

#: Each band's share of the box. The divider is a line, so since work
#: order 170 it takes a third of a row and the frame-colour row fits in
#: the same box: nothing below it (ACCEPT, the body's edge) moves.
WEIGHTS = (1 / 3, 1, 1, 1, 1, 1, 1)

COL_DIVIDER = palette.require("game_menu", "orionlayer_divider")
COL_HEADING = palette.require("game_menu", "orionlayer_heading")
COL_OPTION = palette.require("game_menu", "option_text")
COL_STATE = palette.require("game_menu", "hd_state")

#: Floor steps in the order a click cycles them (screens/galaxy_map/floorlift).
FLOOR_STEPS = ("off", "light", "haze")

#: The monster values switch (screens/planets/monsterpanel), default on.
MONSTER_STEPS = ("on", "off")


def _settings(screen):
    return getattr(screen.app, "user_settings", None)


def bands(screen):
    """{band name: Rect} for the five rows, plus "swatches": [Rect x 8].

    None when the box is missing. Drawing and hit-testing both use this.
    """
    box = next((b for b in screen.boxes if b.name == "orionlayer_rows"), None)
    if box is None or box.screen_rect is None:
        return None
    area = box.screen_rect
    total, acc, edges = sum(WEIGHTS), 0.0, [area.y]
    for w in WEIGHTS:
        acc += w
        edges.append(area.y + int(area.h * acc / total))
    out = {name: pygame.Rect(area.x, edges[i], area.w, edges[i + 1] - edges[i])
           for i, name in enumerate(BANDS)}
    rule = screen.words.get("orionlayer_rows", {})
    row = out["colours"]
    x0 = row.x + int(row.w * rule.get("swatch_x", 0.70))
    gap = rule.get("swatch_gap", 0.2)
    side = max(2, int(min(row.h * 0.6, (row.right - x0) / (8 + 7 * gap))))
    y = row.y + (row.h - side) // 2
    out["swatches"] = [pygame.Rect(x0 + int(i * side * (1 + gap)), y, side, side)
                       for i in range(8)]
    # THE FRAME COLOUR ROW (work order 170): a hue bar from the value
    # column to `hue_end`, and RESET right of it.
    fr = out["frame"]
    bx = fr.x + int(fr.w * rule.get("value_x", 0.5))
    bw = int(fr.w * rule.get("hue_end", 0.84)) - (bx - fr.x)
    bh = max(4, int(fr.h * 0.42))
    out["hue_bar"] = pygame.Rect(bx, fr.y + (fr.h - bh) // 2, max(8, bw), bh)
    rx = out["hue_bar"].right + int(fr.w * 0.02)
    out["hue_reset"] = pygame.Rect(rx, fr.y, fr.right - rx, fr.h)
    # THE TONE ROW (work order 171): saturation and brightness, two
    # bars in the hue bar's span, side by side with a gap.
    to = out["tone"]
    hb = out["hue_bar"]
    gap = max(4, int(hb.w * 0.06))
    half = (hb.w - gap) // 2
    ty = to.y + (to.h - hb.h) // 2
    out["sat_bar"] = pygame.Rect(hb.x, ty, half, hb.h)
    out["bright_bar"] = pygame.Rect(hb.x + half + gap, ty, half, hb.h)
    return out


def bar_value(bar, x, lo, hi):
    """The value under window x on a bar spanning lo..hi — the one
    mapping, for the click and for the thumb (decision 5)."""
    f = max(0.0, min(1.0, (x - bar.x) / max(1, bar.w)))
    return lo + f * (hi - lo)


def bar_x(bar, value, lo, hi):
    return bar.x + int((value - lo) / (hi - lo) * bar.w)


def hue_at(geo, x):
    """The hue in degrees under window x on the bar — the one mapping,
    for the click and for the thumb (decision 5)."""
    bar = geo["hue_bar"]
    return max(0.0, min(359.0, (x - bar.x) * 360.0 / max(1, bar.w)))


def thumb_x(geo, hue):
    bar = geo["hue_bar"]
    return bar.x + int(hue * bar.w / 360.0)


def set_tone(screen, hue=..., sat=..., bright=...):
    """Store the frame colour and apply it at once (no restart): the
    style's caches are rebuilt for the new colour on the next draw.
    An argument left out keeps its current value; None is the measured
    one. Stored as hud_hue / hud_sat / hud_bright (work orders 170, 171);
    a file with hud_hue alone reads the other two as measured."""
    h = tint.hue() if hue is ... else hue
    s = tint._sat if sat is ... else sat
    b = tint._bright if bright is ... else bright
    hudstyle.set_tone(h, s, b)
    settings = _settings(screen)
    if settings is not None:
        settings.set("hud_hue", None if tint.hue() is None
                     else int(round(tint.hue())))
        settings.set("hud_sat", None if tint._sat is None
                     else round(tint._sat, 2))
        settings.set("hud_bright", None if tint._bright is None
                     else round(tint._bright, 2))


def set_hue(screen, value):
    """The hue alone (170)."""
    set_tone(screen, hue=value)


def selected(screen, key):
    settings = _settings(screen)
    return settings.get(key) if settings is not None else usersettings.DEFAULTS[key]


def restart_pending(screen):
    return selected(screen, "player_colors") != palette.active_preset()


def _cycle(settings, key, steps):
    now = settings.get(key)
    i = steps.index(now) if now in steps else 0
    settings.set(key, steps[(i + 1) % len(steps)])


def handle_click(screen, x, y):
    """True if the point is on these rows. Sends nothing, ever."""
    geo = bands(screen)
    if geo is None:
        return False
    area = geo["divider"].union(geo[BANDS[-1]])
    if not area.collidepoint(x, y):
        return False
    settings = _settings(screen)
    if settings is None:
        return True
    if geo["floor"].collidepoint(x, y):
        _cycle(settings, "floor_lift", FLOOR_STEPS)
    elif geo["colours"].collidepoint(x, y):
        _cycle(settings, "player_colors",
               tuple(playercolors.names(screen.app.colors)))
    elif geo["monsters"].collidepoint(x, y):
        _cycle(settings, "monster_values", MONSTER_STEPS)
    elif geo["hue_reset"].collidepoint(x, y):
        set_tone(screen, None, None, None)
    elif geo["sat_bar"].inflate(0, geo["tone"].h - geo["sat_bar"].h) \
            .collidepoint(x, y):
        set_tone(screen, sat=bar_value(geo["sat_bar"], x, *tint.SAT_RANGE))
    elif geo["bright_bar"].inflate(0, geo["tone"].h - geo["bright_bar"].h) \
            .collidepoint(x, y):
        set_tone(screen, bright=bar_value(geo["bright_bar"], x,
                                          *tint.BRIGHT_RANGE))
    elif geo["frame"].collidepoint(x, y) and \
            geo["hue_bar"].left <= x <= geo["hue_bar"].right:
        set_hue(screen, hue_at(geo, x))
    return True


def save(screen):
    """Write the file if anything changed; idempotent."""
    settings = _settings(screen)
    return usersettings.save(settings) if settings is not None else False


def _text(screen, surface, text, size, color, x, rect):
    img = screen.style.render_text(text, size, tuple(color[:3]))
    surface.blit(img, (x, rect.y + (rect.h - img.get_height()) // 2))
    return img


def render(screen, surface):
    geo = bands(screen)
    if geo is None:
        return
    box = next(b for b in screen.boxes if b.name == "orionlayer_rows")
    k = getattr(screen, "content_scale", 1.0)
    size = screen.layout.font_size(box.style.get("font_size", 24) * k)
    small = screen.layout.font_size(box.style.get("heading_font_size", 20) * k)
    words = screen.words.get("words", {}).get("orionlayer", {})
    rule = screen.words.get("orionlayer_rows", {})

    div = geo["divider"]
    ly = div.y + int(div.h * rule.get("divider_y", 0.5))
    pygame.draw.line(surface, tuple(COL_DIVIDER[:3]), (div.x, ly), (div.right, ly))

    head = geo["heading"]
    lx = head.x + int(head.w * rule.get("label_x", 0.114))
    _text(screen, surface, words.get("heading", "OrionLayer"), small, COL_HEADING, lx, head)
    if restart_pending(screen):
        note = screen.style.render_text(words.get("restart", ""), small, tuple(COL_STATE[:3]))
        surface.blit(note, (head.right - note.get_width(),
                            head.y + (head.h - note.get_height()) // 2))

    vx = int(head.w * rule.get("value_x", 0.46))
    floor = geo["floor"]
    _text(screen, surface, words.get("floor", "Map floor"), size, COL_OPTION, lx, floor)
    step = selected(screen, "floor_lift")
    _text(screen, surface, words.get("floor_steps", {}).get(step, step), size,
          COL_OPTION, floor.x + vx, floor)

    row = geo["colours"]
    _text(screen, surface, words.get("colours", "Player colours"), size, COL_OPTION, lx, row)
    preset = selected(screen, "player_colors")
    names = playercolors.names(screen.app.colors)
    shown = preset if preset in names else playercolors.ORIGINAL
    _text(screen, surface, words.get("presets", {}).get(shown, shown), size,
          COL_OPTION, row.x + vx, row)
    for rect, rgb in zip(geo["swatches"], playercolors.base(screen.app.colors, shown)):
        surface.fill(tuple(rgb[:3]), rect)
        screen.style.draw_plate(surface, rect, screen.layout.scale)

    mon = geo["monsters"]
    _text(screen, surface, words.get("monsters", "Monster values"), size,
          COL_OPTION, lx, mon)
    value = selected(screen, "monster_values")
    shown = value if value in MONSTER_STEPS else MONSTER_STEPS[0]
    _text(screen, surface, words.get("monster_steps", {}).get(shown, shown),
          size, COL_OPTION, mon.x + vx, mon)

    _render_frame_row(screen, surface, geo, words, size, lx)


def _render_frame_row(screen, surface, geo, words, size, lx):
    """The frame colour row: label, the hue bar, its thumb, RESET."""
    row = geo["frame"]
    _text(screen, surface, words.get("frame", "Frame colour"), size,
          COL_OPTION, lx, row)
    bar = geo["hue_bar"]
    # The bar shows every hue the setting can take, at the measured
    # accent's lightness and saturation — the colour a panel edge would
    # have at that point.
    base = hudstyle.get().get("panel.edge")
    for i in range(bar.w):
        h = i * 360.0 / bar.w
        c = tint.rotate(base, h - tint.REFERENCE)
        pygame.draw.line(surface, c, (bar.x + i, bar.y), (bar.x + i, bar.bottom - 1))
    screen.style.draw_plate(surface, bar, screen.layout.scale)
    now = tint.hue()
    tx = thumb_x(geo, tint.REFERENCE if now is None else now)
    w = max(2, int(3 * screen.layout.scale))
    surface.fill((255, 255, 255), (tx - w // 2, bar.y - w, w, bar.h + 2 * w))
    reset = geo["hue_reset"]
    _text(screen, surface, words.get("reset", "Reset"), size,
          COL_OPTION if tint.is_default() else COL_STATE,
          reset.x, reset)
    _render_tone_row(screen, surface, geo, words, size, lx, base)


def _render_tone_row(screen, surface, geo, words, size, lx, base):
    """Saturation (grey -> the chosen colour) and brightness (black ->
    silver), each bar drawn with the colours its positions give."""
    _text(screen, surface, words.get("tone", "Frame tone"), size,
          COL_OPTION, lx, geo["tone"])
    w = max(2, int(3 * screen.layout.scale))
    d = tint.delta()
    for key, (lo, hi), now in (("sat_bar", tint.SAT_RANGE, tint.sat()),
                               ("bright_bar", tint.BRIGHT_RANGE,
                                tint.bright())):
        bar = geo[key]
        for i in range(bar.w):
            v = bar_value(bar, bar.x + i, lo, hi)
            c = (tint.transform(base, d=d, s_factor=v, b_factor=1.0)
                 if key == "sat_bar" else
                 tint.transform(base, d=d, s_factor=tint.sat(), b_factor=v,
                                floors=False))
            pygame.draw.line(surface, c, (bar.x + i, bar.y),
                             (bar.x + i, bar.bottom - 1))
        screen.style.draw_plate(surface, bar, screen.layout.scale)
        tx = bar_x(bar, now, lo, hi)
        surface.fill((255, 255, 255), (tx - w // 2, bar.y - w, w,
                                       bar.h + 2 * w))
