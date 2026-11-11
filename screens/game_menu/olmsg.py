"""The TURN MESSAGES tab of the OrionLayer window — HD EXTENSION `turn_message_settings`,
work order 384 (Data's request: "a fitting menu
where one can define exactly which messages are shown at turn change").

The Turn Summary ranks the engine's messages (`core.turnsummary`); the
engine knows 34 kinds (`turnsummary.kinds()`). This tab lists them, grouped
by category under the words the popup itself uses, one checkbox each, and
the player's choice is `turn_summary_hidden`: a sorted list of the kind
keys switched OFF (`core.usersettings`; None, the default, shows
everything). The popup reads it through `turnsummary.hidden(settings)` each
time it draws, so a change shows at once and nothing needs pushing.

THE MODEL IS ONE LIST. The three severity switches at the top are not a
second filter: a switch is lit while NO kind of its severity is hidden, a
click hides every kind of that severity (when lit) or shows them all (when
not), and a single kind can then be switched back on by hand. SHOW ALL
clears the list.

The list is long (34 kinds and 5 headings), so it scrolls: the mouse wheel
(`screen.handle_mousewheel`), a click on the scroll track, and the track
draws through `hud.tables.scrollbar`. `Window.msg_first` is the index of
the first entry shown.

ONE GEOMETRY (decision 5): `geometry` computes the rects for drawing and
clicking alike; `olwin.geometry` calls it for this tab.
"""
import pygame

from core import lang, turnsummary as ts
from core import mouse as mouse_input
from core.hud import blocks as hud
from core.hud import tables

#: The tab's name in `olwin.TABS` (it has no rows of `gmorion`).
TAB = "messages"
SETTING = "turn_summary_hidden"
#: Entries a wheel notch moves.
WHEEL_STEP = 3
#: The category headings are the Turn Summary's own words
#: (`turnpopupcontent.DEFAULT_WORDS`).
HEADING_WORDS = {ts.COLONY: "sum_colony", ts.EMPIRE: "sum_empire",
                 ts.SHIPS: "sum_ships", ts.SPIES: "sum_spies",
                 ts.OTHER: "sum_other"}
SEVERITY_NAMES = {ts.RED: ("Red", "red"),
                  ts.YELLOW: ("Yellow", "yellow"),
                  ts.GREEN: ("Green", "green")}

_entries = []


def entries():
    """The flat list the tab scrolls: `("head", category)` and
    `("kind", key, label, severity)`, in the settings list's order."""
    if not _entries:
        last = None
        for key, label, sev, cat in ts.kinds():
            if cat != last:
                _entries.append(("head", cat))
                last = cat
            _entries.append(("kind", key, label, sev))
    return _entries


def keys_of(severity):
    return [k for k, _l, s, _c in ts.kinds() if s == severity]


def hidden(screen):
    settings = getattr(screen.app, "user_settings", None)
    return ts.hidden(settings) if settings is not None else set()


def store(screen, keys):
    """Write the hidden set: a sorted list, None when empty so the file
    never carries the default. Applies at once (the popup reads it)."""
    settings = getattr(screen.app, "user_settings", None)
    if settings is not None:
        known = {k for k, *_ in ts.kinds()}
        # a key this build does not know (a newer build's) is kept
        keep = [k for k in ts.hidden(settings) if k not in known]
        out = sorted(set(keys) | set(keep))
        settings.set(SETTING, out or None)


def toggle_kind(screen, key):
    now = hidden(screen)
    now.symmetric_difference_update({key})
    store(screen, now)


def severity_on(screen, severity):
    """Lit while no kind of the severity is hidden."""
    return not hidden(screen) & set(keys_of(severity))


def toggle_severity(screen, severity):
    now = hidden(screen)
    mine = set(keys_of(severity))
    if severity_on(screen, severity):
        now |= mine
    else:
        now -= mine
    store(screen, now)


def show_all(screen):
    store(screen, set())


def first(screen, total, visible):
    """The first entry shown, kept inside the list."""
    top = max(0, total - visible)
    return max(0, min(screen.orionlayer.msg_first, top))


def scroll(screen, steps):
    """Move the list `steps` entries (negative: up)."""
    geo = screen_geometry(screen)
    if geo is None:
        return
    total, vis = len(entries()), geo["msg_visible"]
    screen.orionlayer.msg_first = max(0, min(
        first(screen, total, vis) + steps, max(0, total - vis)))


def screen_geometry(screen):
    from . import olwin
    geo = olwin.geometry(screen)
    return geo if geo and "msg_list" in geo else None


def handle_wheel(screen, direction, x, y):
    """The wheel scrolls while the pointer is over the tab's content."""
    geo = screen_geometry(screen)
    if geo is None or not geo["content"].collidepoint(x, y):
        return False
    scroll(screen, -WHEEL_STEP * (1 if direction > 0 else -1))
    return True


# ── geometry ─────────────────────────────────────────────────────────
def geometry(screen, out, y, row, gap):
    """Add the tab's rects to `out` (olwin.geometry's dict): the three
    severity switches and SHOW ALL on one line, the list below it, its
    scroll track right of it, and the visible entries' rects."""
    content = out["content"]
    rh = max(12, int(row * 1.0))
    cells = 4
    cw = (content.w - gap * (cells - 1)) // cells
    for i, sev in enumerate(ts.SEVERITIES):
        out["msg_sev_%d" % sev] = pygame.Rect(
            content.x + i * (cw + gap), y, cw, rh)
    out["msg_all"] = pygame.Rect(content.x + 3 * (cw + gap), y, cw, rh)
    y += rh + gap * 2
    bar_w = max(8, int(row * 0.5))
    lst = pygame.Rect(content.x, y, content.w - bar_w - gap,
                      max(rh, out["footer_y"] - gap * 2 - y))
    out["msg_list"] = lst
    out["msg_bar"] = pygame.Rect(lst.right + gap, lst.y, bar_w, lst.h)
    vis = max(1, lst.h // rh)
    items = entries()
    out["msg_visible"] = min(vis, len(items))
    top = first(screen, len(items), vis)
    out["msg_first"] = top
    out["msg_rows"] = [
        (i, pygame.Rect(lst.x, lst.y + n * rh, lst.w, rh))
        for n, i in enumerate(range(top, min(len(items), top + vis)))]


def box_rect(rect):
    """The checkbox square at a row's left."""
    side = max(8, int(rect.h * 0.8))
    return pygame.Rect(rect.x, rect.y + (rect.h - side) // 2, side, side)


# ── input ────────────────────────────────────────────────────────────
def handle_click(screen, geo, x, y):
    """A click on the tab's content; True if it acted."""
    for sev in ts.SEVERITIES:
        if geo["msg_sev_%d" % sev].collidepoint(x, y):
            toggle_severity(screen, sev)
            return True
    if geo["msg_all"].collidepoint(x, y):
        show_all(screen)
        return True
    for i, rect in geo["msg_rows"]:
        if rect.collidepoint(x, y) and entries()[i][0] == "kind":
            toggle_kind(screen, entries()[i][1])
            return True
    bar = geo["msg_bar"]
    if bar.collidepoint(x, y):
        total, vis = len(entries()), geo["msg_visible"]
        span = max(0, total - vis)
        screen.orionlayer.msg_first = max(0, min(span, round(
            (y - bar.y) / max(1, bar.h) * span)))
        return True
    return False


# ── drawing ──────────────────────────────────────────────────────────
def _marker(surface, rect, severity):
    """The severity's picture, the one the Turn Summary's rows wear; a
    plain disc in its signal colour where the picture is absent."""
    from core import turnsummaryview as view
    pic = view.icon(severity, max(6, int(rect.h * 0.74)))
    if pic is not None:
        surface.blit(pic, (rect.x + (rect.w - pic.get_width()) // 2,
                           rect.y + (rect.h - pic.get_height()) // 2))
        return
    # LOOK EXCEPTION data: the severity's signal colour, as the popup's rows
    pygame.draw.circle(surface, view.SIGNAL[severity], rect.center,
                       max(3, rect.h // 3))


def _label(screen, surface, rect, text, x, colour, size):
    from . import gmorion
    gmorion._text(screen, surface, lang.tr(text), size, colour, x, rect,
                  rect.right - x, fit=True)


#: HD EXTENSION `turn_message_icon` (Data, 10 Nov 2026): the tab's picture is
#: Data's glowing tile (document and speech bubble), a slot of the player's
#: mod folder (`popups/turn_messages_icon.png`), never in a tree.
ICON_SLOT = "assets/shared/turnpopup/turn_messages_icon.png"
_icons = {}


def _glyph(path):
    """The tile's glyph as a white mask with alpha, or None: the picture's
    middle (the glyph, inside the tile's own border) turned from brightness into
    alpha, cut to its ink. Works for the supplied tile; another picture
    with a bright border inside that middle would show it."""
    try:
        import numpy as np
        src = pygame.image.load(path)
        w, h = src.get_size()
        mid = pygame.Rect(int(w * 0.28), int(h * 0.19), int(w * 0.44),
                          int(h * 0.60))
        rgb = pygame.surfarray.array3d(src.subsurface(mid)).astype(
            np.float32)
        lum = rgb.max(axis=2)                        # (x, y)
        alpha = np.clip((lum - 85.0) / 60.0, 0.0, 1.0)
        xs, ys = np.where(alpha > 0.15)
        if not len(xs):
            return None
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        out = pygame.Surface((x1 - x0, y1 - y0), pygame.SRCALPHA)
        out.fill((255, 255, 255, 0))
        pygame.surfarray.pixels_alpha(out)[:] = (
            alpha[x0:x1, y0:y1] * 255).astype(np.uint8)
        return out
    except (pygame.error, OSError, ValueError, ImportError):
        return None


def tab_icon(height, colour):
    """The tab's icon `height` px high in `colour` (the word's colour, as
    the other tabs' masks), or None without the mod folder's picture."""
    import os
    from core import resources
    path = resources.res.resolve(ICON_SLOT)
    if not path or height < 1:
        return None
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    key = (path, stamp, int(height), tuple(colour[:3]))
    if key in _icons:
        return _icons[key] or None
    glyph = _glyph(path)
    out = None
    if glyph is not None:
        w = max(1, round(glyph.get_width() * height / glyph.get_height()))
        out = pygame.transform.smoothscale(glyph, (w, int(height)))
        out.fill(tuple(colour[:3]) + (255,),
                 special_flags=pygame.BLEND_RGBA_MULT)
    if len(_icons) > 16:
        _icons.clear()
    _icons[key] = out or False
    return out


def render(screen, surface, geo):
    from . import gmorion
    from core import turnpopupcontent as tpc
    scale = screen.layout.scale
    size = gmorion.row_font(screen)
    now = hidden(screen)
    mouse = mouse_input.pos()
    for sev in ts.SEVERITIES:
        r = geo["msg_sev_%d" % sev]
        b = box_rect(r)
        hud.checkbox(surface, b, scale, severity_on(screen, sev),
                     hover=r.collidepoint(mouse))
        marker = pygame.Rect(b.right + b.w // 3, r.y, b.w, r.h)
        _marker(surface, marker, sev)
        _label(screen, surface, r, SEVERITY_NAMES[sev][0],
               marker.right + b.w // 3, gmorion.COL_OPTION, size)
    r = geo["msg_all"]
    hud.small_button(surface, r, scale,
                     "hover" if r.collidepoint(mouse) else "normal")
    word = screen.style.render_text(lang.tr("Show all"), size,
                                    tuple(gmorion.COL_OPTION[:3]))
    while word.get_width() > r.w * 0.9 and size > 8:
        size -= 1
        word = screen.style.render_text(lang.tr("Show all"), size,
                                        tuple(gmorion.COL_OPTION[:3]))
    surface.blit(word, (r.centerx - word.get_width() // 2,
                        r.centery - word.get_height() // 2))
    size = gmorion.row_font(screen)
    items = entries()
    for i, rect in geo["msg_rows"]:
        item = items[i]
        if item[0] == "head":
            text = tpc.DEFAULT_WORDS[HEADING_WORDS[item[1]]]
            _label(screen, surface, rect, text, rect.x,
                   gmorion.COL_HEADING, size)
            hud.separator(surface, rect.x, rect.right, rect.bottom - 1,
                          scale)
            continue
        _kind, key, label, sev = item
        b = box_rect(rect)
        b.x += b.w // 2
        hud.checkbox(surface, b, scale, key not in now,
                     hover=rect.collidepoint(mouse))
        marker = pygame.Rect(b.right + b.w // 3, rect.y, b.w, rect.h)
        _marker(surface, marker, sev)
        _label(screen, surface, rect, label, marker.right + b.w // 3,
               gmorion.COL_OPTION, size)
    tables.scrollbar(surface, geo["msg_bar"], scale, geo["msg_first"],
                     geo["msg_visible"], len(items))
