"""Drop-down lists in the OrionLayer settings window — work order 251.

Data's answer of 13 October 2026: a row with a set of values is a real
drop-down list — a click on the field opens every value, a click on one
picks it, a click anywhere else or ESC closes the list unchanged. Until
then a click stepped to the next value (`gmorion._cycle`).

`CHOICES` is the one table: each row's setting, its values and the words
they are shown in. Picking does what stepping did, value by value: a player-colour preset
applies at once (`palette.apply_preset`, work order 312), the mod
folder switched on starts the extraction (`core.modsetup`), a language
starts reading its game files (`core.langsetup`), the glass switch goes
through `gmfill.set_glass`. Nothing is sent.

The list is drawn with the HUD's own blocks (a panel, a field per value,
the chosen one "selected", decision 92), so it follows the global colour
control as every window does.
"""
import pygame

from core import (framerate, lang, langsetup, modsetup, paintdetail,
                  playercolors)
from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import fill

#: row -> (settings key, words key in layout.json `words.orionlayer`).
CHOICES = {
    "colours": ("player_colors", "presets"),
    "glass": ("hud_glass_on", "glass_steps"),
    "floor": ("floor_lift", "floor_steps"),
    "map_black": ("map_black_floor", "map_black_steps"),
    "monsters": ("monster_values", "monster_steps"),
    "map_ships": ("map_ship_pictures", "map_ships_steps"),
    "frame_rate": ("frame_rate", "frame_rate_steps"),
    "idle_rate": ("idle_frame_rate", "idle_rate_steps"),
    "painted": ("painted_detail", "painted_steps"),
    "mods": ("user_mod", "mod_steps"),
    "language": ("language", "language_steps"),
}


def values(screen, name):
    """The row's values, in the order the list shows them."""
    from . import gmorion
    return {
        "colours": lambda: tuple(playercolors.names(screen.app.colors)),
        "glass": lambda: ("on", "off"),
        "floor": lambda: gmorion.FLOOR_STEPS,
        # Data's black map background (work order 326; the map reads it
        # in `galaxy_map/floorlift`), off by default
        "map_black": lambda: ("off", "on"),
        "monsters": lambda: gmorion.MONSTER_STEPS,
        "map_ships": lambda: gmorion.MAP_SHIP_STEPS,
        "frame_rate": lambda: tuple(framerate.STEPS),
        "idle_rate": lambda: tuple(framerate.IDLE_STEPS),
        "painted": lambda: tuple(paintdetail.STEPS),
        "mods": lambda: gmorion.MOD_STEPS,
        "language": lambda: tuple(lang.LANGUAGES),
    }[name]()


def current(screen, name):
    """The value the row stands at — the shown one when the stored value
    is unknown, as the rows always showed it."""
    from . import gmorion
    if name == "glass":
        return "on" if fill.glass_on() else "off"
    if name == "language":
        return gmorion.selected(screen, "language") or lang.current()
    steps = values(screen, name)
    now = gmorion.selected(screen, CHOICES[name][0])
    if now in steps:
        return now
    return {"colours": playercolors.ORIGINAL, "frame_rate": framerate.DEFAULT,
            "idle_rate": framerate.IDLE_DEFAULT,
            "painted": paintdetail.DEFAULT}.get(name, steps[0])


def word(screen, name, value, surface_w=None):
    """`value` in the row's words; the monitor's rate and Auto's factor
    filled in as the rows did."""
    words = screen.words.get("words", {}).get("orionlayer", {})
    out = words.get(CHOICES[name][1], {}).get(value, value)
    if name == "frame_rate" and value == "monitor":
        out = out.format(hz=getattr(screen.app, "_hz", None)
                         or framerate.monitor_hz())
    elif name == "painted" and value == "auto":
        w = surface_w or screen.app.win_w
        out = out.format(k=paintdetail.cap(value, w / paintdetail.OPENING_PX))
    return out


def pick(screen, name, value):
    """Set the row to `value`, with what the old step did on the way."""
    from . import gmfill, gmorion
    settings = gmorion._settings(screen)
    if name == "glass":
        gmfill.set_glass(screen, value == "on")
        return
    if settings is None:
        return
    settings.set(CHOICES[name][0], value)
    if name == "colours":
        # HD EXTENSION `preset_at_once` (work order 312, decision 99): the
        # preset applies at once, every screen's player colours with it
        from core import palette
        palette.apply_preset(value, settings.get("player_color_base"))
    elif name == "mods" and value == "on":
        # Data, 30 September 2026: switching it on says it can take a while
        # and starts the extraction (the Mod files row shows the progress)
        modsetup.start()
    elif name == "language":
        langsetup.start(value, folder=settings.get("language_dir"))


def options(geo, name, n):
    """The list's rects under the field — above it where the window ends
    first."""
    field = geo[name + "_field"]
    w = max(field.w, int(geo[name].w * 0.36))
    down = field.bottom + n * field.h <= geo["window"].bottom
    y0 = field.bottom if down else field.y - n * field.h
    return [pygame.Rect(field.x, y0 + i * field.h, w, field.h)
            for i in range(n)]


def handle_click(screen, geo, x, y):
    """A click while a list is open: a value picks it, anything else
    closes the list. Always consumed."""
    w = screen.orionlayer
    name = w.drop
    w.drop = None
    vals = values(screen, name)
    for value, rect in zip(vals, options(geo, name, len(vals))):
        if rect.collidepoint(x, y):
            pick(screen, name, value)
            return


def render_field(screen, surface, geo, name, size, colour):
    """The closed field: the value and the arrow."""
    from . import gmorion
    rect = geo[name + "_field"]
    hud.field(surface, rect, screen.layout.scale,
              on=screen.orionlayer.drop == name)
    pad = max(4, rect.h // 4)
    gmorion._text(screen, surface, word(screen, name, current(screen, name),
                                        surface.get_width()),
                  size, colour, rect.x + pad, rect,
                  rect.w - pad * 2 - rect.h // 2, fit=True)
    _arrow(surface, rect, colour)


def _arrow(surface, rect, colour):
    s = max(3, rect.h // 5)
    cx, cy = rect.right - rect.h // 2, rect.centery
    # LOOK EXCEPTION marking: the drop-down's arrow, in its word's colour
    pygame.draw.polygon(surface, tuple(colour[:3]),
                        [(cx - s, cy - s // 2), (cx + s, cy - s // 2),
                         (cx, cy + s // 2 + 1)])


def render_list(screen, surface, geo):
    """The open list, over everything else in the window."""
    from . import gmorion
    w = screen.orionlayer
    if w.drop is None or w.drop + "_field" not in geo:
        return
    vals = values(screen, w.drop)
    rects = options(geo, w.drop, len(vals))
    hud.panel(surface, rects[0].union(rects[-1]).inflate(4, 4),
              screen.layout.scale, dense=True)
    now = current(screen, w.drop)
    size = gmorion.row_font(screen)
    for value, rect in zip(vals, rects):
        hud.field(surface, rect, screen.layout.scale, on=value == now)
        if rect.collidepoint(mouse_input.pos()) and value != now:
            hud.outline(surface, rect, screen.layout.scale, lit=True)
        pad = max(4, rect.h // 4)
        gmorion._text(screen, surface, word(screen, w.drop, value,
                                            surface.get_width()),
                      size, gmorion.COL_OPTION, rect.x + pad, rect,
                      rect.w - 2 * pad, fit=True)
