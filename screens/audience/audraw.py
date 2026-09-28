"""Drawing the diplomacy audience: the original's stage, HUD panels over it.

  ORIGINAL ART   the race's room and its ambassador (DIPLOMAT.LBX, `auart`),
                 stretched to the 4:3 stage; the ambassador not drawn when
                 the audience is refused (dip_scrn_main.cpp:1562)
  TRANSCRIPTION  the statement as the engine rendered it, in the
                 original's column (x 80, 470 wide, centred on y 440); the
                 menu's title and items at the fields the list built, a
                 disabled item dimmed (`Get_List_Field_` ignores it)
  DEVIATION      `hud_frameless` — HUD panels behind the statement and the
                 menu where the original prints on the room
  OMISSION       `talking_loop` — the ambassador's animation (its phase is
                 not on the wire; the still is the frame the original shows
                 with animations off); `header_line` — JIMTEXT2's "Player
                 n: name" / "race Ambassador" line at (320, 10), an
                 extraction this order does not add; `glass_remap` — the
                 ambassador's glassed pixels drawn as their indices (a
                 hatching) where the original remaps them against the room
                 (`Update_Glass_Remap_Colors_`, dip_scrn_main.cpp:476)
"""
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.textfit import wrap_text
from screens.colony import coldraw
from screens.leaders import ldrdraw as nd

from . import auart, augeom as geom


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def draw(surface, screen, view):
    _stage(surface, screen, view)
    _statement(surface, screen, view)
    if view.items():
        _menu(surface, screen, view)


def _stage(surface, screen, view):
    import pygame
    stage = nd.rect(screen.layout, geom.STAGE)
    art = auart.load()
    room = art.picture("rooms", view.race) if view.race is not None else None
    if room is None:
        return                    # no stage: the panels on the background
    # The original fills black and draws the room over it
    # (`Setup_Back_Page_`): the room's index 0 shows black.
    surface.fill((0, 0, 0), stage)
    surface.blit(nd.stretched(room, stage), stage.topleft)
    amb = None if view.refused else art.picture("ambassadors", view.race)
    if amb is not None:
        r = nd.rect(screen.layout, (0, 0, amb.get_width() - 1,
                                    amb.get_height() - 1))
        surface.blit(pygame.transform.scale(amb, r.size), r.topleft)


def _statement(surface, screen, view):
    words = view.audience["text"]
    if not words:
        return
    panel = nd.draw_box(surface, screen, geom.STATEMENT_PANEL)
    size = coldraw.font(screen.layout, "value")
    width = nd.rect(screen.layout, (0, 0, geom.STATEMENT_W, 1)).w
    lines = wrap_text(screen.style, words, size, width)
    step = int(size * 1.25)
    x, cy = nd.point(screen.layout, geom.STATEMENT_X, geom.STATEMENT_CY)
    y = max(panel.top + 4, cy - len(lines) * step // 2)
    for line in lines:
        nd.blit_text(surface, screen.style, line, x, y, width, size,
                     hudtext.colour("value"))
        y += step


def _menu(surface, screen, view):
    items = view.items()
    top = view.title_field.y if view.title_field else items[0][1].y
    bottom = items[-1][1].y_end
    m = geom.MENU_MARGIN
    nd.draw_box(surface, screen, (geom.MENU_X1 - m, top - m,
                                  geom.MENU_X2 + m, bottom + m))
    if view.title_field is not None and view.audience["title"]:
        coldraw.text(surface, screen, view.audience["title"].strip(),
                     view.title_field.x, view.title_field.y,
                     geom.MENU_X2 - geom.MENU_X1, "value", "label")
    for item, f in items:
        r = nd.rect(screen.layout, _rect(f))
        if item["enabled"] and screen.hovered(r):
            hud.panel(surface, r, screen.layout.scale, lit=True, dense=True)
        coldraw.text(surface, screen, item["text"].strip(), f.x + 4, f.y,
                     f.x_end - f.x - 4, "value",
                     "value" if item["enabled"] else "sub")
