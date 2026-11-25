"""The build popup's two lists as the mockup draws them — HD EXTENSION
`build_lists_mockup` (work order 432, Data's mockup of 25 November 2026).

The original prints a row of words at a fixed step (`Calculate_Squish_Step_`,
coldraw.cpp:12-34) and squeezes a long list until every row fits. HD draws
the rows as the mockup does — a picture in front of each, a row that stands
tall enough to read, the chosen row on a bar, the long list scrolled with a
scroll bar and the wheel — and the right list's three groups (the game's
separators, colbldg.cpp:308-345) as boxes with a head.

NOTHING IS SENT FROM HERE. A row stands for the game's own field of the same
position in the list (`bqwire.View.building_rows` / `other_rows`): a click
activates THAT field (found live by its rectangle), wherever HD drew the row, so the engine
sees exactly the click it sees at the island. Scrolling is HD's alone.

INVENTION `group_heads`: the three words on the groups' heads (Ships,
Designs, Androids) are ours; the original has gaps there and no word.
"""
# HD EXTENSION `build_lists_mockup`: see the docstring.
import pygame

from core import buildingart, prodname
from core.hud import art as hudart
from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core import nativedraw as nd

from . import bqcolour as col
from . import bqproduct as prod
from . import bqwire as w

#: Row steps and the group head, as shares of the window's height.
PITCH_BUILDING, PITCH_OTHER, HEAD, GAP = 0.0245, 0.0335, 0.036, 0.010
BAR = 0.0115                                  # the scroll bar's width
#: The words on the three groups, by position (`layout.json` `words`).
GROUP_KEYS = ("group_ships", "group_designs", "group_androids")
#: The HUD glyphs on the groups' heads (they turn with the frame colour).
GROUP_ICONS = ("ship", "range", "person")


class Row:
    __slots__ = ("kind", "index", "product", "y", "h", "group")

    def __init__(self, kind, index, product, y, h, group=0):
        self.kind, self.index, self.product = kind, index, product
        self.y, self.h, self.group = y, h, group


def pitches(height):
    return (max(18, round(PITCH_BUILDING * height)),
            max(24, round(PITCH_OTHER * height)),
            max(26, round(HEAD * height)), max(6, round(GAP * height)))


def layout_rows(view, kind, height):
    """([Row], total height) of one list, in list space (y from 0)."""
    pb, po, head, gap = pitches(height)
    rows, y = [], 0
    if kind == "building":
        for i, e in enumerate(view.buildings):
            if e["id"] == w.SEPARATOR:
                y += gap
                continue
            rows.append(Row("item", i, e["id"], y, pb))
            y += pb
        return rows, y
    group, open_group = -1, False
    for i, e in enumerate(view.others):
        if e["id"] == w.SEPARATOR:
            open_group = False
            continue
        if not open_group:
            group += 1
            if group:
                y += gap
            rows.append(Row("head", -1, None, y, head, group))
            y += head
            open_group = True
        rows.append(Row("item", i, e["id"], y, po, group))
        y += po
    return rows, y


def viewport(screen, kind, height):
    """The window rect the rows scroll in, or None."""
    panel = screen.box_screen_rect("left_panel" if kind == "building"
                                   else "right_panel")
    if panel is None:
        return None
    inner = shell.inner(panel, screen.ref_layout)
    pad = shell.inset(screen.ref_layout)
    view = inner.inflate(-pad, -pad)
    if kind == "other":
        top = nd.rect(screen.layout, w.BUTTONS_BOX).top
        view.h = max(40, top - pad - view.y)
    return view


def _bar_width(height):
    return max(10, round(BAR * height))


class Geometry:
    """One list's current layout: its rows, the window rect they show in,
    the scroll offset (clamped) and the scroll bar's parts."""

    def __init__(self, screen, view, kind, height):
        self.kind = kind
        self.rows, self.total = layout_rows(view, kind, height)
        vp = viewport(screen, kind, height)
        self.vp = vp
        self.scroll = 0
        self.bar = None
        if vp is None:
            return
        self.limit = max(0, self.total - vp.h)
        self.scroll = max(0, min(self.limit,
                                 screen._scroll.get(kind, 0)))
        screen._scroll[kind] = self.scroll
        if self.limit > 0:
            bw = _bar_width(height)
            self.bar = pygame.Rect(vp.right - bw, vp.y, bw, vp.h)
            self.rows_x1 = vp.right - bw - max(3, bw // 3)
        else:
            self.rows_x1 = vp.right

    def row_rect(self, r):
        vp = self.vp
        return pygame.Rect(vp.x, vp.y + r.y - self.scroll,
                           self.rows_x1 - vp.x, r.h)

    def thumb(self):
        bar = self.bar
        arrow = bar.w
        track = pygame.Rect(bar.x, bar.y + arrow, bar.w, bar.h - 2 * arrow)
        size = max(arrow * 2, int(track.h * self.vp.h / self.total))
        size = min(size, track.h)
        at = track.y + int((track.h - size) * self.scroll / self.limit)
        return track, pygame.Rect(bar.x, at, bar.w, size)


def geometries(screen, view, height):
    return {k: Geometry(screen, view, k, height)
            for k in ("building", "other")}


def hit(geoms, x, y):
    """What is under a window point: ("item", kind, index, product),
    ("bar", kind, part) with part up / down / page_up / page_down / thumb,
    or None."""
    for kind, g in geoms.items():
        if g.vp is None or not g.vp.collidepoint(x, y):
            continue
        if g.bar is not None and g.bar.collidepoint(x, y):
            bar = g.bar
            if y < bar.y + bar.w:
                return ("bar", kind, "up")
            if y >= bar.bottom - bar.w:
                return ("bar", kind, "down")
            track, thumb = g.thumb()
            if thumb.collidepoint(x, y):
                return ("bar", kind, "thumb")
            return ("bar", kind, "page_up" if y < thumb.y else "page_down")
        for r in g.rows:
            if r.kind == "item" and g.row_rect(r).collidepoint(x, y):
                return ("item", kind, r.index, r.product)
    return None


def scroll_by(screen, geoms, kind, amount):
    g = geoms.get(kind)
    if g is None or g.vp is None:
        return
    screen._scroll[kind] = max(0, min(g.limit, g.scroll + int(amount)))


_made = {}


class Context:
    """What a product's icon needs from the frame being drawn."""

    def __init__(self, spec_of, world, colour, app, state):
        self.spec_of, self.world, self.colour = spec_of, world, colour
        self.app, self.state = app, state


def _cut(pic, h):
    r = pic.get_bounding_rect(min_alpha=40)
    if not (r.w and r.h):
        return None
    return pygame.transform.smoothscale(
        pic.subsurface(r), (max(1, round(r.w * h / r.h)), h))


def _product_icon(spec, ctx, h):
    """A product's own drawing, cut to its pixels and `h` tall: a ship by
    the painted pictures every list uses (`core.shippicture`), else the
    game's own drawing the picture box stands (`colroom.product_only`); None
    where neither exists."""
    from core import shippicture
    from screens.colony import colroom
    from core import livery, palette, usermod
    # what `shippicture.fitted` keys on too: the livery (its second colour,
    # pattern, strength), the painted detail, the mod folder and the palette
    us = getattr(ctx.app, "user_settings", None)
    key = (spec, ctx.world, ctx.colour, h, id(ctx.app),
           livery.from_settings(us, ctx.colour).key(),
           us.get("painted_detail") if us is not None else None,
           shippicture.usermod_generation(), palette.generation(),
           id(usermod._state["index"]))
    if key in _made:
        return _made[key]
    if len(_made) > 200:
        _made.clear()
    got = None
    if spec[0] == "ship":
        size = spec[4] if len(spec) > 4 else None
        made = shippicture.fitted(ctx.app, ctx.colour, spec[1],
                                  pygame.Rect(0, 0, h * 4, h * 2),
                                  state=ctx.state, size=size)
        if made is not None:
            got = _cut(made[0], h)
    if got is None:
        pic = colroom.product_only(spec, ctx.world[0], ctx.world[1],
                                   colour=ctx.colour)
        got = _cut(pic, h) if pic is not None else None
    # a miss is not kept: the mod folder may be switched on a moment later
    if got is not None:
        _made[key] = got
    return got


def _icon(product, pitch, ctx):
    """The picture in front of a row, or None."""
    special = {prod.TRADE_GOODS: buildingart.TRADE_GOODS,
               prod.HOUSING: buildingart.HOUSING}
    if product in special or prodname.kind(product) == \
            prodname.KIND_BUILDING:
        bid = special.get(product, product)
        return buildingart.fit(int(bid), int(pitch * 1.9), pitch - 1)
    spec = ctx.spec_of(product)
    if spec is None:
        return None
    return _product_icon(spec, ctx, int(pitch * 0.8))


def _bar(surface, rect, accent):
    """The chosen row's bar: a dark gold fill under a lit outline."""
    # LOOK EXCEPTION marking: the chosen row's bar in the frame colour's accent (Data's mockup of 25 November 2026)
    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(fill, (*accent, 58), fill.get_rect(),
                     border_radius=max(3, rect.h // 5))
    surface.blit(fill, rect.topleft)
    pygame.draw.rect(surface, accent, rect, width=2,
                     border_radius=max(3, rect.h // 5))


def _scroll_bar(surface, g, accent):
    bar = g.bar
    # LOOK EXCEPTION marking: the scroll bar's track and outline in the frame colour's accent (HD EXTENSION build_lists_mockup)
    pygame.draw.rect(surface, (14, 14, 14), bar)
    pygame.draw.rect(surface, accent, bar, width=1)
    track, thumb = g.thumb()
    a = bar.w
    for rect, up in ((pygame.Rect(bar.x, bar.y, a, a), True),
                     (pygame.Rect(bar.x, bar.bottom - a, a, a), False)):
        cx, m = rect.centerx, max(2, a // 4)
        if up:
            pts = [(cx, rect.y + m), (rect.x + m, rect.bottom - m),
                   (rect.right - m, rect.bottom - m)]
        else:
            pts = [(cx, rect.bottom - m), (rect.x + m, rect.y + m),
                   (rect.right - m, rect.y + m)]
        # LOOK EXCEPTION marking: the scroll bar's arrows in the frame colour's accent (HD EXTENSION build_lists_mockup)
        pygame.draw.polygon(surface, accent, pts)
    # LOOK EXCEPTION marking: the scroll bar's thumb in the frame colour's accent (HD EXTENSION build_lists_mockup)
    pygame.draw.rect(surface, tuple(int(c * 0.55) for c in accent),
                     thumb.inflate(-2, -2), border_radius=max(2, a // 3))
    pygame.draw.rect(surface, accent, thumb.inflate(-2, -2), width=1,
                     border_radius=max(2, a // 3))


def draw(surface, screen, view, state, names, hover, geoms, row_bright,
         ctx):
    """Both lists. `row_bright(product, building)` is the screen's rule for
    a dimmed row (`bqdraw.row_bright`)."""
    height = surface.get_height()
    accent = hudtext.colour("label")
    dim = hudtext.colour("sub")
    chosen = hover if hover is not None else view.items[0]
    pb, po, head, _gap = pitches(height)
    for kind, g in geoms.items():
        if g.vp is None:
            continue
        building = kind == "building"
        pitch = pb if building else po
        size = max(nd.MIN_FONT, int(pitch * (0.68 if building else 0.54)))
        was = surface.get_clip()
        surface.set_clip(g.vp)
        groups = {}
        for r in g.rows:
            rect = g.row_rect(r)
            span = groups.setdefault(r.group, [rect, rect])
            span[1] = rect
        if not building:
            for gi, (top, bottom) in sorted(groups.items()):
                box = pygame.Rect(top.x, top.y, top.w,
                                  bottom.bottom - top.y)
                hud.field(surface, box, screen.layout.scale)
        for r in g.rows:
            rect = g.row_rect(r)
            if rect.bottom < g.vp.y or rect.y > g.vp.bottom:
                continue
            if r.kind == "head":
                _head(surface, screen, rect, r.group, size, accent)
                continue
            e = view.buildings[r.index] if building else view.others[r.index]
            bright = row_bright(e["id"], building)
            if e["id"] != chosen:
                # LOOK EXCEPTION marking: the faint rule between two rows, the frame colour's accent at a quarter of its light (Data's mockup)
                pygame.draw.line(surface, tuple(int(c * 0.28) for c in accent),
                                 (rect.x + 6, rect.bottom - 1),
                                 (rect.right - 6, rect.bottom - 1))
            if e["id"] == chosen:
                _bar(surface, rect.inflate(-4, -2), accent)
            name, _st = names.product(e["id"], state)
            icon = _icon(e["id"], pitch, ctx)
            x = rect.x + max(6, pitch // 3)
            if icon is not None:
                surface.blit(icon, (x, rect.centery - icon.get_height() // 2))
            x += int(pitch * (1.9 if building else 2.1)) + 6
            ink = col.SELECTED if e["id"] == chosen else col.ROW
            ink = ink if bright or building else dim
            nd.blit_text(surface, screen.style, name, x,
                         rect.centery - size // 2 - 1, rect.right - x - 4,
                         size, ink)
        surface.set_clip(was)
        if g.bar is not None:
            _scroll_bar(surface, g, accent)


def _head(surface, screen, rect, group, size, accent):
    """A group's head: its picture, its word, a rule under it."""
    key = GROUP_KEYS[group] if group < len(GROUP_KEYS) else None
    word = screen.word(key) if key else ""
    icon = hudart.icon(GROUP_ICONS[group] if group < len(GROUP_ICONS)
                       else "ship", int(rect.h * 0.62))
    x = rect.x + max(6, rect.h // 4)
    if icon is not None:
        surface.blit(icon, (x, rect.centery - icon.get_height() // 2))
        x += icon.get_width() + max(6, rect.h // 4)
    nd.blit_text(surface, screen.style, word, x,
                 rect.centery - int(size * 0.62), rect.right - x - 4,
                 int(size * 1.25), accent)
    # LOOK EXCEPTION marking: the rule under a group's head in the frame colour's accent (HD EXTENSION build_lists_mockup)
    pygame.draw.line(surface, tuple(int(c * 0.6) for c in accent),
                     (rect.x + 4, rect.bottom - 1),
                     (rect.right - 4, rect.bottom - 1))
