"""The OrionLayer rows of the Game Settings dialog — an HD EXTENSION (fundament 63, 64).

Below the thirteen engine rows, five row heights: a divider, the
"OrionLayer" heading, the map floor lift, the player-colour preset and
the switch for the monster values in the Planets panel — and since work
order 170 a sixth, the HUD FRAME COLOUR: a hue bar and RESET (HD
EXTENSION, `core/hud/tint.py`), applied at once and saved with the
rest; the divider became a thin band so the box did not grow. Since
work order 173 an eighth band, the MOD FOLDER switch (HD EXTENSION,
decision 72, `core/usermod.py`): on or off, applied at the next start
like the preset; and since work order 174 the PANEL GLASS slider (HD
EXTENSION, `core/hud/glass.py`), applied at once like the colour; and
since work order 200 C the LANGUAGE switch (HD EXTENSION
`language_switch`, `core/lang.py`): English or German, applied at the next
start like the preset; and since work order 212 the FRAME RATE (HD EXTENSION
`frame_rate`, decision 79, `core/framerate.py`): 30, 60, 120, the monitor's
rate (the default) or unlimited, applied at once; and since work order 219
the PAINTED DETAIL (HD EXTENSION `painted_detail`, `core/paintdetail.py`):
Auto (the default), Normal (4 x) or High (8 x), from the next battle on; and
since work order 220 the LIVERY button on that row (HD EXTENSION `livery`,
`gmlivery`), shown only while the mod folder is on and holds painted ships
with masks (decision 2), which opens the livery window. MOO2 has none of
them; the game knows nothing about these rows.

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

from core import (framerate, lang, livery, modsetup, paintdetail, palette,
                  playercolors, usermod, usersettings)
from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import glass
from core.hud import style as hudstyle
from core.hud import tint

from . import gmlang

BANDS = ("divider", "heading", "floor", "colours", "monsters", "frame",
         "tone", "glass", "frame_rate", "painted", "mods", "language")

#: Buttons a row carries besides its value, and the row each sits on: the
#: livery window's (work order 220), in the RESET column of Painted detail.
#: A help region each, named as the bands are (`orionlayer.<name>`).
ROW_BUTTONS = {"livery": "painted"}

#: Each band's share of the box. The divider is a line, so since work
#: order 170 it takes a third of a row and the frame-colour row fits in
#: the same box: nothing below it (ACCEPT, the body's edge) moves.
WEIGHTS = (1 / 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

COL_DIVIDER = palette.require("game_menu", "orionlayer_divider")
COL_HEADING = palette.require("game_menu", "orionlayer_heading")
COL_OPTION = palette.require("game_menu", "option_text")
COL_STATE = palette.require("game_menu", "hd_state")

#: Floor steps in the order a click cycles them (screens/galaxy_map/floorlift).
FLOOR_STEPS = ("off", "light", "haze")

#: The monster values switch (screens/planets/monsterpanel), default on.
MONSTER_STEPS = ("on", "off")

#: The mod folder switch (work order 173, decision 72), default off since
#: work order 197 (`core.usersettings`). Switching it ON starts the
#: extraction and the kit in the background (`core.modsetup`).
MOD_STEPS = ("off", "on")


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
    # THE PANEL GLASS ROW (work order 174): one bar in the hue bar's span,
    # see-through at the left, solid at the right, and its own RESET.
    gl = out["glass"]
    out["glass_bar"] = pygame.Rect(hb.x, gl.y + (gl.h - hb.h) // 2, hb.w,
                                   hb.h)
    rr = out["hue_reset"]
    out["glass_reset"] = pygame.Rect(rr.x, gl.y, rr.w, gl.h)
    # THE LIVERY BUTTON (work order 220) in the RESET column of the Painted
    # detail row — only when it can do something (decision 2)
    if livery.window_available():
        pa = out["painted"]
        out["livery"] = pygame.Rect(rr.x, pa.y + pa.h // 10, rr.w,
                                           pa.h - pa.h // 5)
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
    a file with hud_hue alone reads the other two as measured.

    What is stored is the PLAYER'S value, not the colour in force: a
    None stays None, so the mod folder's colour.json (decision 72) keeps
    filling it — and switching the mod off does not leave its colour
    behind in the player's file."""
    settings = _settings(screen)
    now = ((settings.get("hud_hue"), settings.get("hud_sat"),
            settings.get("hud_bright")) if settings is not None
           else (tint.hue(), tint._sat, tint._bright))
    h = now[0] if hue is ... else hue
    s = now[1] if sat is ... else sat
    b = now[2] if bright is ... else bright
    hudstyle.set_tone(h, s, b)
    if settings is not None:
        h, s, b = tint.normalise(h, s, b)
        settings.set("hud_hue", None if h is None else int(round(h)))
        settings.set("hud_sat", None if s is None else round(s, 2))
        settings.set("hud_bright", None if b is None else round(b, 2))


def set_glass(screen, value):
    """The Panel glass slider (work order 174, HD EXTENSION): applied at
    once, stored as hud_glass — the PLAYER'S value, None for the
    default (the measured 0.5, or a mod's `chosen.glass.slider_default`)."""
    glass.set_value(value)
    settings = _settings(screen)
    if settings is not None:
        settings.set("hud_glass", None if value is None
                     else round(glass.value(), 2) if glass._value is not None
                     else None)


def set_hue(screen, value):
    """The hue alone (170)."""
    set_tone(screen, hue=value)


def selected(screen, key):
    settings = _settings(screen)
    return settings.get(key) if settings is not None else usersettings.DEFAULTS[key]


def restart_pending(screen):
    """The colour preset, the mod folder and the language are read at
    start: the note shows while a saved choice differs from the one in
    force."""
    started = usermod.started_enabled()
    chosen = selected(screen, "language")
    return (selected(screen, "player_colors") != palette.active_preset()
            or (started is not None
                and (selected(screen, "user_mod") != "off") != started)
            or (chosen is not None and chosen != lang.current()))


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
    elif geo["frame_rate"].collidepoint(x, y):
        _cycle(settings, "frame_rate", framerate.STEPS)
    elif "livery" in geo and geo["livery"].collidepoint(x, y):
        from . import gmlivery
        gmlivery.open_window(screen)
    elif geo["painted"].collidepoint(x, y):
        _cycle(settings, "painted_detail", paintdetail.STEPS)
    elif geo["mods"].collidepoint(x, y):
        _cycle(settings, "user_mod", MOD_STEPS)
        if settings.get("user_mod") == "on":
            # Data, 30 September 2026: switching it on says it can take a
            # while and starts the extraction (the row shows the progress).
            modsetup.start()
    elif geo["language"].collidepoint(x, y):
        gmlang.cycle(settings)
    elif geo["glass_reset"].collidepoint(x, y):
        set_glass(screen, None)
    elif geo["glass"].collidepoint(x, y) and \
            geo["glass_bar"].left <= x <= geo["glass_bar"].right:
        set_glass(screen, bar_value(geo["glass_bar"], x, 0.0, 1.0))
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


def _text(screen, surface, text, size, color, x, rect, width=None,
          fit=False):
    img = screen.style.render_text(text, size, tuple(color[:3]))
    # the text-fit rule outside English (work order 200 C: "Zurücksetzen"
    # ran past the dialog); English is drawn exactly as before — but for a
    # row new with that order (`fit`), which fits in every language
    while width and img.get_width() > width and size > 8 and \
            (fit or lang.current() != lang.DEFAULT):
        size -= 1
        img = screen.style.render_text(text, size, tuple(color[:3]))
    surface.blit(img, (x, rect.y + (rect.h - img.get_height()) // 2))
    return img


def _reset_room(screen, reset):
    """The width a word from `reset.x` on has: to the dialog's inner edge."""
    body = next((b for b in screen.boxes if b.name == "body"), None)
    if body is None or body.screen_rect is None:
        return None
    return body.screen_rect.right - reset.x - (reset.x - body.screen_rect.x) \
        // 20


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
        # LOOK EXCEPTION data: a colour swatch: the colour the setting stands for
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
    _render_glass_row(screen, surface, geo, words, size, lx)
    _render_frame_rate_row(screen, surface, geo["frame_rate"], words, size,
                           lx, vx)
    _render_painted_row(screen, surface, geo["painted"], words, size, lx, vx)
    _render_livery_button(screen, surface, geo, words, size)
    _render_mod_row(screen, surface, geo["mods"], words, size, lx, vx)
    gmlang.render(screen, surface, geo["language"], words, size, lx, vx,
                  lambda *a, fit=False: _text(
                      screen, surface, *a, fit=fit, width=_reset_room(
                          screen, pygame.Rect(a[3], 0, 0, 0)) if fit else None),
                  selected(screen, "language"))


def _render_glass_row(screen, surface, geo, words, size, lx):
    """Panel glass: the bar shows what each position does — a light
    sample seen through the glass, see-through at the left, solid at the
    right — and the thumb; RESET is lit while the value is the player's."""
    row, bar = geo["glass"], geo["glass_bar"]
    _text(screen, surface, words.get("glass", "Panel glass"), size,
          COL_OPTION, lx, row)
    sample = (90, 120, 170)
    for i in range(bar.w):
        v = bar_value(bar, bar.x + i, 0.0, 1.0)
        alpha, col = glass.profile(2, glass.transparency(v=v))
        a = float(alpha[0])
        c = tuple(int(sample[k] * (1 - a) + col[0][k] * a) for k in range(3))
        pygame.draw.line(surface, c, (bar.x + i, bar.y),
                         (bar.x + i, bar.bottom - 1))
    screen.style.draw_plate(surface, bar, screen.layout.scale)
    w = max(2, int(3 * screen.layout.scale))
    tx = bar_x(bar, glass.value(), 0.0, 1.0)
    # LOOK EXCEPTION marking: the slider's position tick
    surface.fill((255, 255, 255), (tx - w // 2, bar.y - w, w, bar.h + 2 * w))
    reset = geo["glass_reset"]
    _text(screen, surface, words.get("reset", "Reset"), size,
          COL_OPTION if glass._value is None else COL_STATE, reset.x, reset,
          _reset_room(screen, reset))


def _render_frame_rate_row(screen, surface, row, words, size, lx, vx):
    """The frame rate (decision 79): the choice, the monitor's with its rate."""
    _text(screen, surface, words.get("frame_rate", "Frame rate"), size,
          COL_OPTION, lx, row)
    value = selected(screen, "frame_rate")
    shown = value if value in framerate.STEPS else framerate.DEFAULT
    word = words.get("frame_rate_steps", {}).get(shown, shown)
    if shown == "monitor":
        hz = getattr(screen.app, "_hz", None) or framerate.monitor_hz()
        word = word.format(hz=hz)
    _text(screen, surface, word, size, COL_OPTION, row.x + vx, row)


def _render_painted_row(screen, surface, row, words, size, lx, vx):
    """The painted pictures' detail (`core/paintdetail`); Auto says what it
    picks for this window: a battle's field is the window's width, and its
    opening view 32 cells of 20 px across it (`cbview.Camera.framing`)."""
    _text(screen, surface, words.get("painted", "Painted detail"), size,
          COL_OPTION, lx, row)
    value = selected(screen, "painted_detail")
    shown = value if value in paintdetail.STEPS else paintdetail.DEFAULT
    word = words.get("painted_steps", {}).get(shown, shown)
    if shown == "auto":
        word = word.format(k=paintdetail.cap(shown, surface.get_width()
                                             / paintdetail.OPENING_PX))
    _text(screen, surface, word, size, COL_OPTION, row.x + vx, row)


def _render_livery_button(screen, surface, geo, words, size):
    """The button that opens the livery window, where it is offered."""
    rect = geo.get("livery")
    if rect is None:
        return
    hud.small_button(surface, rect, screen.layout.scale,
                     "hover" if rect.collidepoint(mouse_input.pos())
                     else "normal")
    img = screen.style.render_text(words.get("livery", "Livery"), size,
                                   tuple(COL_OPTION[:3]))
    while img.get_width() > rect.w * 0.9 and size > 8:
        size -= 1
        img = screen.style.render_text(words.get("livery", "Livery"), size,
                                       tuple(COL_OPTION[:3]))
    surface.blit(img, (rect.x + (rect.w - img.get_width()) // 2,
                       rect.y + (rect.h - img.get_height()) // 2))


def _render_mod_row(screen, surface, row, words, size, lx, vx):
    """The mod folder switch; with it on, how many of the folder's
    files are in use, so a player can see the folder was found."""
    _text(screen, surface, words.get("mods", "Mod folder"), size,
          COL_OPTION, lx, row)
    value = selected(screen, "user_mod")
    shown = value if value in MOD_STEPS else MOD_STEPS[0]
    img = _text(screen, surface, words.get("mod_steps", {}).get(shown, shown),
                size, COL_OPTION, row.x + vx, row)
    job = modsetup.state()
    note = None
    if job["phase"] == "running":
        note = words.get("mod_wait", "Extracting — this can take a while "
                         "({i}/{n})").format(i=job["i"], n=job["n"])
    elif job["phase"] == "done":
        note = (words.get("mod_failed", "{n} step(s) failed — see the log")
                .format(n=len(job["failed"])) if job["failed"]
                else words.get("mod_done", "Ready — restart to use it"))
    elif shown == "on" and usermod.started_enabled():
        n = usermod.in_use()
        note = (words.get("mod_files", "{n} files").format(n=n)
                if usermod.active() else words.get("mod_none", "no folder"))
    if note is not None:
        nx = row.x + vx + img.get_width() + int(row.h * 0.6)
        _text(screen, surface, note, size, COL_STATE, nx, row,
              _reset_room(screen, pygame.Rect(nx, row.y, 0, 0)))


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
    # LOOK EXCEPTION marking: the slider's position tick
    surface.fill((255, 255, 255), (tx - w // 2, bar.y - w, w, bar.h + 2 * w))
    reset = geo["hue_reset"]
    _text(screen, surface, words.get("reset", "Reset"), size,
          COL_OPTION if tint.is_default() else COL_STATE,
          reset.x, reset, _reset_room(screen, reset))
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
        # LOOK EXCEPTION marking: the slider's position tick
        surface.fill((255, 255, 255), (tx - w // 2, bar.y - w, w,
                                       bar.h + 2 * w))
