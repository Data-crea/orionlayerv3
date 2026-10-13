"""The OrionLayer rows — an HD EXTENSION (fundament 63, 64).

OrionLayer's own settings: the map floor lift and the player-colour
preset (63), the monster values (64), the HUD frame colour and tone (work
orders 170, 171, `core/hud/tint.py`), the panel glass (174), the mod
folder (decision 72), the language (HD EXTENSION `language_switch`, 200
C), the frame rate (HD EXTENSION `frame_rate`, decision 79), the painted
detail (HD EXTENSION `painted_detail`, `core/paintdetail.py`, 219), the
livery window (HD EXTENSION `livery`, 220), the box fill (HD EXTENSION,
decision 94, `gmfill`). MOO2 has none of them; the game knows nothing
about them.

**WHERE THEY ARE (work order 251, Data).** Until then rows below the
thirteen engine rows of Game Settings; since then the rows of the OrionLayer
settings window (`olwin`), grouped into Data's four tabs. This module keeps
what they DO — their values, their controls, their drawing — and the
window gives them their places (`olwin.geometry`, which calls
`swatch_geometry` and `colour_geometry` here). A row with a set of values
is a drop-down list (`oldrop`); the colour rows keep their bars.

**TWO STATE SOURCES, NEVER MERGED.** The thirteen engine checkboxes
keep their local copy seeded from `s_settings` (`screen.flags`). These
rows read and write `app.user_settings` (`core.usersettings`) and
nothing else. They have no field, and a click on them sends nothing.

**ONE GEOMETRY FOR DRAWING AND CLICKING** (decision 5): `bands` is the
window's geometry, the only place the rows' rects are computed.

**VALUES APPLY AT ONCE, THE FILE IS WRITTEN LATER.** The floor step
shows on the map behind the popup on the next frame (`floorlift` reads
it at draw time), and the monster switch on the next Planets frame. The
preset needs a restart — `palette.init` applies it before any screen
binds a colour — and the note that says so is shown only while the
saved preset differs from the active one. The file is written by
`save`, which closing the window, ACCEPT and the overlay's exit call and
which writes nothing when nothing changed.
"""
import pygame

from core import (lang, modsetup, palette, playercolors, usermod,
                  usersettings)
from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import glass
from core.hud import style as hudstyle
from core.hud import tint

from . import gmfill, gmlang

#: Every row, in Data's order of the tabs (`olwin.TABS`): what the right-
#: click help regions name (help.json `orionlayer_band`).
BANDS = ("colours", "frame", "tone", "glass", "fill", "fill_tone", "floor",
         "monsters", "frame_rate", "painted", "livery", "mods", "mod_files",
         "language")

#: the heading colour of the rows until work order 251, the livery
#: window's labels since 220
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
    """{name: Rect} of the window's rows and controls (`olwin.geometry`);
    None while the window is closed. Drawing and hit-testing both use it."""
    from . import olwin
    return olwin.geometry(screen)


def swatch_geometry(out, rule):
    """The eight swatches right of the player-colour field."""
    row = out["colours"]
    x0 = row.x + int(row.w * rule.get("swatch_x", 0.70))
    gap = rule.get("swatch_gap", 0.2)
    side = max(2, int(min(row.h * 0.6, (row.right - x0) / (8 + 7 * gap))))
    y = row.y + (row.h - side) // 2
    out["swatches"] = [pygame.Rect(x0 + int(i * side * (1 + gap)), y, side,
                                   side) for i in range(8)]


def colour_geometry(out, rule):
    """The colour rows' bars and RESETs (work orders 170, 171, 174, 227),
    in the columns `rule` gives: a hue bar from the value column to
    `hue_end`, RESET right of it; the tone row's two bars in its span."""
    fr = out["frame"]
    bx = fr.x + int(fr.w * rule.get("value_x", 0.5))
    bw = int(fr.w * rule.get("hue_end", 0.84)) - (bx - fr.x)
    bh = max(4, int(fr.h * 0.42))
    out["hue_bar"] = pygame.Rect(bx, fr.y + (fr.h - bh) // 2, max(8, bw), bh)
    rx = out["hue_bar"].right + int(fr.w * 0.02)
    out["hue_reset"] = pygame.Rect(rx, fr.y, fr.right - rx, fr.h)
    to = out["tone"]
    hb = out["hue_bar"]
    gap = max(4, int(hb.w * 0.06))
    half = (hb.w - gap) // 2
    ty = to.y + (to.h - hb.h) // 2
    out["sat_bar"] = pygame.Rect(hb.x, ty, half, hb.h)
    out["bright_bar"] = pygame.Rect(hb.x + half + gap, ty, half, hb.h)
    gl = out["glass"]
    out["glass_bar"] = pygame.Rect(hb.x, gl.y + (gl.h - hb.h) // 2, hb.w,
                                   hb.h)
    rr = out["hue_reset"]
    out["glass_reset"] = pygame.Rect(rr.x, gl.y, rr.w, gl.h)
    # the glass switch is the row's drop-down field (`oldrop`), the bar
    # right of it; the fill colour in the frame colour's columns (`gmfill`)
    gmfill.geometry(out, rule)


def row_font(screen):
    """The rows' font size."""
    k = getattr(screen, "content_scale", 1.0)
    return screen.layout.font_size(24 * k)


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


def handle_click(screen, x, y):
    """True if the point is on a row (which then acted). Sends nothing,
    ever. A drop-down field opens its list (`oldrop`)."""
    geo = bands(screen)
    if geo is None:
        return False
    names = [n for n in BANDS if n in geo]
    if not any(geo[n].collidepoint(x, y) for n in names):
        return False
    from . import oldrop
    for name in oldrop.CHOICES:
        field = geo.get(name + "_field")
        if field is not None and field.collidepoint(x, y):
            screen.orionlayer.drop = name
            return True
    if "livery_button" in geo and geo["livery_button"].collidepoint(x, y):
        from . import gmlivery
        gmlivery.open_window(screen)
    elif "frame" not in geo:
        pass                     # the colour rows are on APPEARANCE only
    elif gmfill.handle_click(screen, geo, x, y):
        pass
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
    """The width a word from `reset.x` on has: to the rows' right edge."""
    geo = bands(screen)
    if geo is None:
        return None
    return geo["content"].right - reset.x


def render(screen, surface):
    """The current tab's rows (`olwin.geometry` holds only those)."""
    geo = bands(screen)
    if geo is None:
        return
    from . import oldrop
    size = row_font(screen)
    words = screen.words.get("words", {}).get("orionlayer", {})
    lx = geo["content"].x
    labels = {"colours": ("colours", "Player colours"),
              "floor": ("floor", "Map floor"),
              "monsters": ("monsters", "Monster values"),
              "frame_rate": ("frame_rate", "Frame rate"),
              "painted": ("painted", "Painted detail"),
              "livery": ("livery", "Livery"),
              "mods": ("mods", "Mod folder"),
              "mod_files": ("mod_files_label", "Mod files"),
              "language": ("language", "Language")}
    for name, (key, default) in labels.items():
        if name in geo:
            _text(screen, surface, words.get(key, default), size, COL_OPTION,
                  lx, geo[name], geo[name].w * 0.34, fit=True)
    for name in oldrop.CHOICES:
        if name + "_field" in geo:
            oldrop.render_field(screen, surface, geo, name, size, COL_OPTION)
    if "colours" in geo:
        shown = oldrop.current(screen, "colours")
        for rect, rgb in zip(geo["swatches"],
                             playercolors.base(screen.app.colors, shown)):
            # LOOK EXCEPTION data: a colour swatch: the colour the setting stands for
            surface.fill(tuple(rgb[:3]), rect)
            screen.style.draw_plate(surface, rect, screen.layout.scale)
    if "frame" in geo:
        _render_frame_row(screen, surface, geo, words, size, lx)
        _render_glass_row(screen, surface, geo, words, size, lx)
        gmfill.render(screen, surface, geo, words, size, lx)
    if "livery_button" in geo:
        _render_livery_button(screen, surface, geo, words, size)
    if "mod_files" in geo:
        _render_mod_files(screen, surface, geo, words, size)
    if "language" in geo:
        gmlang.render_note(screen, surface, geo, words, size)


def _render_glass_row(screen, surface, geo, words, size, lx):
    """Panel glass: the switch (work order 227), then the bar showing what
    each position does — a light sample seen through the glass,
    see-through at the left, solid at the right — and the thumb, dimmed
    while the switch is off; RESET is lit while the value is the
    player's."""
    row, bar = geo["glass"], geo["glass_bar"]
    _text(screen, surface, words.get("glass", "Panel glass"), size,
          COL_OPTION, lx, row)
    gmfill.render_glass_bar(screen, surface, bar)
    reset = geo["glass_reset"]
    _text(screen, surface, words.get("reset", "Reset"), size,
          COL_OPTION if glass._value is None or gmfill.glass_dim()
          else COL_STATE, reset.x, reset, _reset_room(screen, reset))


def _render_livery_button(screen, surface, geo, words, size):
    """The button that opens the livery window, where it is offered."""
    rect = geo.get("livery_button")
    if rect is None:
        return
    hud.small_button(surface, rect, screen.layout.scale,
                     "hover" if rect.collidepoint(mouse_input.pos())
                     else "normal")
    word = words.get("livery_open", "Open")
    img = screen.style.render_text(word, size, tuple(COL_OPTION[:3]))
    while img.get_width() > rect.w * 0.9 and size > 8:
        size -= 1
        img = screen.style.render_text(word, size, tuple(COL_OPTION[:3]))
    surface.blit(img, (rect.x + (rect.w - img.get_width()) // 2,
                       rect.y + (rect.h - img.get_height()) // 2))


def _render_mod_files(screen, surface, geo, words, size):
    """How many of the folder's files are in use, so a player can see the
    folder was found — or the extraction's progress after switching it on
    (until work order 251 a note beside the switch)."""
    row = geo["mod_files"]
    x = row.x + int(row.w * 0.36)
    job = modsetup.state()
    if job["phase"] == "running":
        note = words.get("mod_wait", "Extracting — this can take a while "
                         "({i}/{n})").format(i=job["i"], n=job["n"])
    elif job["phase"] == "done":
        note = (words.get("mod_failed", "{n} step(s) failed — see the log")
                .format(n=len(job["failed"])) if job["failed"]
                else words.get("mod_done", "Ready — restart to use it"))
    elif selected(screen, "user_mod") == "on" and usermod.started_enabled():
        note = (words.get("mod_files", "{n} files").format(n=usermod.in_use())
                if usermod.active() else words.get("mod_none", "no folder"))
    else:
        note = words.get("mod_off", "—")
    _text(screen, surface, note, size, COL_STATE, x, row, row.right - x,
          fit=True)


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
