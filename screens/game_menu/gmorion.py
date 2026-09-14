"""The OrionLayer rows of the Game Settings dialog — an HD EXTENSION (fundament 63).

Below the thirteen engine rows, four row heights: a divider, the
"OrionLayer" heading, the map floor lift and the player-colour preset.
MOO2 has neither a user-adjustable floor nor a choice of player
colours; the game knows nothing about these rows.

**TWO STATE SOURCES, NEVER MERGED.** The thirteen engine checkboxes
keep their local copy seeded from `s_settings` (`screen.flags`). These
rows read and write `app.user_settings` (`core.usersettings`) and
nothing else. They have no field, and a click on them — divider and
heading included — is handled here BEFORE the engine rows' `row_at` /
`send`, and sends nothing on the wire.

**ONE GEOMETRY FOR DRAWING AND CLICKING** (decision 5): `bands` is the
only place the four rects and the swatch rects are computed.

**VALUES APPLY AT ONCE, THE FILE IS WRITTEN LATER.** The floor step
shows on the map behind the popup on the next frame (`floorlift` reads
it at draw time). The preset needs a restart — `palette.init` applies
it before any screen binds a colour — and the note that says so is
shown only while the saved preset differs from the active one. The
file is written by `save`, which ACCEPT and the overlay's exit both
call and which writes nothing when nothing changed.
"""
import pygame

from core import palette, playercolors, usersettings

BANDS = ("divider", "heading", "floor", "colours")

COL_DIVIDER = palette.require("game_menu", "orionlayer_divider")
COL_HEADING = palette.require("game_menu", "orionlayer_heading")
COL_OPTION = palette.require("game_menu", "option_text")
COL_STATE = palette.require("game_menu", "hd_state")

#: Floor steps in the order a click cycles them (screens/galaxy_map/floorlift).
FLOOR_STEPS = ("off", "light", "haze")


def _settings(screen):
    return getattr(screen.app, "user_settings", None)


def bands(screen):
    """{band name: Rect} for the four rows, plus "swatches": [Rect x 8].

    None when the box is missing. Drawing and hit-testing both use this.
    """
    box = next((b for b in screen.boxes if b.name == "orionlayer_rows"), None)
    if box is None or box.screen_rect is None:
        return None
    area = box.screen_rect
    edges = [area.y + (area.h * i) // len(BANDS) for i in range(len(BANDS) + 1)]
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
    return out


def selected(screen, key):
    settings = _settings(screen)
    return settings.get(key) if settings is not None else usersettings.DEFAULTS[key]


def restart_pending(screen):
    return selected(screen, "player_colors") != palette.active_preset()


def handle_click(screen, x, y):
    """True if the point is on these rows. Sends nothing, ever."""
    geo = bands(screen)
    if geo is None:
        return False
    area = geo["divider"].union(geo["colours"])
    if not area.collidepoint(x, y):
        return False
    settings = _settings(screen)
    if settings is None:
        return True
    if geo["floor"].collidepoint(x, y):
        now = settings.get("floor_lift")
        i = FLOOR_STEPS.index(now) if now in FLOOR_STEPS else 0
        settings.set("floor_lift", FLOOR_STEPS[(i + 1) % len(FLOOR_STEPS)])
    elif geo["colours"].collidepoint(x, y):
        names = playercolors.names(screen.app.colors)
        now = settings.get("player_colors")
        i = names.index(now) if now in names else 0
        settings.set("player_colors", names[(i + 1) % len(names)])
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
    size = screen.layout.font_size(box.style.get("font_size", 24))
    small = screen.layout.font_size(box.style.get("heading_font_size", 20))
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
