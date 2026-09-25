"""The galaxy map's HUD: title plate, info panel and nav row (decision 71).

Split out of `screen.py` by work order 169 along the seam the screen
already had — `screen.py` keeps loading, geometry of the map and input
hooks; this draws the HUD over the map's floor and answers where its
buttons are. Every shape is a `core.hud` block; nothing here draws its
own panel or button.

**One function per place, for drawing AND hitting** (decision 5):
`title_rect` is the GAME button's click area, its help region and where
its word goes; `nav_rect` / `nav_hit` are where a nav button is drawn
and the shape it is hit as.
"""
import pygame

from core import mouse as mouse_input
from core.config import REF_W
from core.hud import art as hudart
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.galaxy_map import boxdraw
from screens.galaxy_map import sidebar as sb


def plate_centre_x(screen):
    """Where the title plate is centred: the MAP's horizontal centre
    (work order 171). Since 170 the map ends at the info panel, so the
    window's centre put the plate visibly right of the map's. Falls back
    to the content area's centre while the map box has no rect."""
    L = screen.layout
    box = screen.box_screen_rect("map_area")
    if box is None:
        return L.offset_x + REF_W * L.scale / 2
    return box.x + box.w / 2


def title_rect(screen):
    """The title plate's text box in device px."""
    # From the WINDOW's top edge (work order 170), as the bar hangs from
    # its bottom one: on a window taller than 16:9 both reach the edge.
    return hud.title_plate_rect(plate_centre_x(screen), 0,
                                screen.layout.scale)[1]


def render_title(screen, surface):
    """The HUD title plate and its word (layout.json `frame.title`).

    The pressed GAME word is orange, as BUFFER0.LBX 1's frame 1 is.
    The word is centred BY INK (`core.hud.text.blit`), the fix of
    16 September 2026 for an all-caps word sitting high."""
    cfg = screen._data.get("frame", {})
    title = cfg.get("title", screen.FRAME_TITLE)
    L = screen.layout
    hud.title_plate(surface, plate_centre_x(screen),
                    0, L.scale, title, screen.style,
                    colour=screen.pressed.colour(
                        "title", hudtext.colour("title"))[:3])


def render_sidebar(screen, surface):
    """The info panel: a HUD panel, its separators where the HUD has
    them (above every row but the first), the HUD's own icons, and the
    readouts in code."""
    box = screen.box_rect("sidebar")
    if not box:
        return
    L = screen.layout
    panel = pygame.Rect(*L.rect(box))
    hud.panel(surface, panel, L.scale)
    state = screen._state
    stardate = (str(getattr(state, "stardate_str", "--"))
                if state is not None else "--")
    rows = screen._data.get("sidebar_rows") or sb.DEFAULT_ROWS
    geometry = screen._sidebar_geometry(rows, set(hudart.ICONS))
    x0, x1 = hud.separator_span(panel, L.scale)
    pad = int(screen._data.get("sidebar_row_pad", 8) * L.scale)
    tops = sorted(L.rect(text)[1] for text, _ in geometry.values())
    for top in tops[1:]:
        hud.separator(surface, x0, x1, top - pad, L.scale)
    for key, (_text, icon) in geometry.items():
        if icon is not None and key in hudart.ICONS:
            _blit_icon(surface, key, pygame.Rect(*L.rect(icon)))
    sb.render(surface, L, screen.style, geometry,
              screen._local, screen._data.get("labels", {}), rows,
              font_scales=screen._sidebar_font_scales(rows),
              aligns=screen._sidebar_aligns(rows),
              monetary=screen._data.get("monetary_unit", "BC"),
              extras={"stardate": (stardate, "")},
              icons={}, cache=screen._cache,
              fonts=screen._data.get("sidebar_fonts", sb.DEFAULT_FONTS),
              panel_box=box, dividers=False,
              hstrings=boxdraw._texts(screen))


def _blit_icon(surface, key, r):
    """The HUD's icon for `key`, fitted into `r`, aspect kept."""
    img = hudart.icon(key, r.h)
    if img is None:
        return
    if img.get_width() > r.w:
        img = hudart.fit("icon_" + key,
                         max(1, int(r.h * r.w / img.get_width())), r.w)
    surface.blit(img, (r.x + (r.w - img.get_width()) // 2,
                       r.y + (r.h - img.get_height()) // 2))


def render_nav(screen, surface):
    """The six nav buttons (HUD slanted buttons, each with the HUD's
    icon for it) and TURN (the action button). Hover lights a button;
    the pressed one is drawn active."""
    # Window coordinates, not desktop coordinates: in fullscreen the
    # content sits inside black bars and a raw get_pos() puts the
    # highlight one bar-width off the pointer.
    mouse = mouse_input.pos()
    for spec in screen._data.get("buttons", []):
        key = spec["key"]
        rect = nav_rect(screen, key)
        if rect is None:
            continue
        if screen.pressed.is_down(key):
            state = "active"
        elif nav_hit(screen, key, *mouse):
            state = "hover"
        else:
            state = "normal"
        icon = key if key in hudart.ICONS else None
        draw = hud.action_button if key == "turn" else hud.slant_button
        draw(surface, rect, screen.layout.scale, state, spec["label"],
             icon=icon, style_renderer=screen.style)


def nav_rect(screen, key):
    """The window rect, anchors included: the bar hangs from the
    window's bottom edge (work order 170)."""
    return screen.box_screen_rect(f"nav_{key}")


def nav_hit(screen, key, x, y):
    """A nav button is hit as the shape it is drawn as: TURN's
    rectangle, the others' parallelogram."""
    rect = nav_rect(screen, key)
    if rect is None:
        return False
    return (rect.collidepoint(x, y) if key == "turn"
            else hud.slant_hit(rect, x, y))
