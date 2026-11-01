"""Drawing the diplomacy audience: the original's stage, HUD panels over it.

  ORIGINAL ART   the race's room and its ambassador (DIPLOMAT.LBX, `auart`),
                 stretched to the 4:3 stage; the ambassador not drawn when
                 the audience is refused (dip_scrn_main.cpp:1562)
  TRANSCRIPTION  the statement as the engine rendered it, in the
                 original's column (x 80, 470 wide, centred on y 440), each
                 line centred (FMTPARA mode 2, fmtpara.cpp:1701-1702); the
                 menu's title and items at the fields the list built, a
                 disabled item dimmed (`Get_List_Field_` ignores it) at the
                 original's own ratio, `augeom.DISABLED_DIM` (work order 187)
  DEVIATION      `hud_frameless` — HUD panels behind the statement and the
                 menu where the original prints on the room
  OMISSION       `talking_loop` — the ambassador's animation (its phase is
                 not on the wire; the still is the frame the original shows
                 with animations off); `header_line` — JIMTEXT2's "Player
                 n: name" / "race Ambassador" line at (320, 10), an
                 extraction this order does not add; `glass_remap` — the
                 ambassador's glassed pixels drawn as their indices (a
                 hatching) where the original remaps them against the room
                 (`Update_Glass_Remap_Colors_`, dip_scrn_main.cpp:476) —
                 the engine's framebuffer shows the same hatching; `fade_in`
                 — the room's fade-in (dip_scrn_main.cpp:1985-2016) is not
                 played, the ambassador and the statement show at once
"""
from core import lang
from core.hud import blocks as hud
from core.hud import text as hudtext
from core.textfit import wrap_text
from core import nativedraw as nd

from . import auart, augeom as geom


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def draw(surface, screen, view):
    # every word of the audience is the game's (work order 200 C)
    with lang.verbatim():
        screen.film_box = screen.film_rows = None
        film = _stage(surface, screen, view)
        _statement(surface, screen, view, film)
        if view.items():
            (_gold_menu if film else _menu)(surface, screen, view)
    if view.picker is not None:
        from . import aupicker
        aupicker.draw(surface, screen, view, screen.pointer_native())


def _stage(surface, screen, view):
    import pygame
    stage = nd.rect(screen.layout, geom.STAGE)
    if _video(surface, screen, view, stage):
        return True
    art = auart.load()
    room = art.picture("rooms", view.race) if view.race is not None else None
    if room is None:
        return False              # no stage: the panels on the background
    # The original fills black and draws the room over it
    # (`Setup_Back_Page_`): the room's index 0 shows black.
    # LOOK EXCEPTION picture: the ambassador's stage, black as the original's
    surface.fill((0, 0, 0), stage)
    surface.blit(nd.stretched(room, stage), stage.topleft)
    amb = None if view.refused else art.picture("ambassadors", view.race)
    if amb is not None:
        r = nd.rect(screen.layout, (0, 0, amb.get_width() - 1,
                                    amb.get_height() - 1))
        surface.blit(pygame.transform.scale(amb, r.size), r.topleft)
    return False


def _video(surface, screen, view, stage):
    """HD EXTENSION `ambassador_video` (`auvideo`): the clip in the 4:3
    stage in place of the room and the ambassador. False: draw the still."""
    import pygame
    if view.refused or view.audience is None or view.race is None:
        return False
    from . import aumood, auvideo
    mood = aumood.mood(view.game_state, view.audience)
    if not auvideo.PLAYER.want(view.race, mood):
        return False
    got = auvideo.PLAYER.frame(stage, surface.get_rect())
    if got is None:
        return False
    surface.blit(*got)
    screen.film_box = pygame.Rect(got[1], got[0].get_size())
    return True


def _statement(surface, screen, view, film=False):
    words = view.statement
    if not words:
        return
    size = _size(screen)
    width = nd.rect(screen.layout, (0, 0, geom.STATEMENT_W, 1)).w
    x, cy = nd.point(screen.layout, geom.STATEMENT_X + geom.STATEMENT_W // 2,
                     geom.STATEMENT_CY)
    if film:
        # HD EXTENSION `audience_gold_menu`: the gold bar of the mockup
        from . import audeco
        audeco.bar(surface, screen, view, audeco.Layout(
            screen.film_box, len(view.items())), _text_at(surface, screen),
            audeco.header_line(view))
        return
    else:
        panel = nd.draw_box(surface, screen, geom.STATEMENT_PANEL)
    lines = wrap_text(screen.style, words, size, width)
    step = int(size * 1.25)
    y = max(panel.top + 4, cy - len(lines) * step // 2)
    for line in lines:
        nd.blit_text(surface, screen.style, line, x, y, width, size,
                     hudtext.colour("value"), align="center")
        y += step


def _size(screen):
    return max(nd.MIN_FONT, int(round(geom.TEXT_PX *
                                      nd.native_scale(screen.layout))))


def _line(surface, screen, words, x, y, w, role, colour=None):
    wx, wy = nd.point(screen.layout, x, y)
    width = nd.rect(screen.layout, (0, 0, w, 1)).w
    nd.blit_text(surface, screen.style, words, wx, wy, width, _size(screen),
                 colour or hudtext.colour(role))


def disabled_colour():
    """An enabled item's colour at the original's disabled brightness —
    the original draws a disabled item (0, 92, 0) beside (44, 164, 28), about
    half as bright (`augeom.DISABLED_DIM`), in the same hue; 185-186's light
    blue `sub` read as a heading or a highlight (work order 187 part 4)."""
    return tuple(int(round(c * geom.DISABLED_DIM))
                 for c in hudtext.colour("value")[:3])


#: The menu title's text role: the items' (`value`) — the original draws
#: the title in the items' colour (work order 188 part 2).
TITLE_ROLE = ITEM_ROLE = "value"


def _gold_menu(surface, screen, view):
    from . import audeco
    lay = audeco.Layout(screen.film_box, len(view.items()))
    screen.film_rows = lay.rows     # where a click and a help look hit
    audeco.menu(surface, screen, view, lay, _text_at(surface, screen),
                screen.hovered)


def _text_at(surface, screen):
    """`text_at(words, x, cy, w, colour, px, centre)`: one line whose
    MIDDLE is at `cy` (its drawn height, not a guessed line box), shrunk
    to `w`; `x` is its left, or its centre when `centre`."""
    def text_at(words, x, cy, w, colour, px, centre):
        if not words:
            return
        size = nd.fit(screen.style, words, max(1, w), px)
        pic = screen.style.render_text(words, size, colour)
        left = x - pic.get_width() // 2 if centre else x
        surface.blit(pic, (left, cy - pic.get_height() // 2))
    return text_at


def _menu(surface, screen, view):
    items = view.items()
    top = view.title_field.y if view.title_field else items[0][1].y
    bottom = items[-1][1].y_end
    m = geom.MENU_MARGIN
    nd.draw_box(surface, screen, (geom.MENU_X1 - m, top - m,
                                  geom.MENU_X2 + m, bottom + m))
    if view.title_field is not None and view.audience["title"]:
        # THE ITEMS' OWN COLOUR (work order 188 part 2, Data's answer to
        # 187's parked 2a, "The audience menu's title colour"): the original
        # prints "How may I serve you:" in the menu items' green, not in a
        # heading colour; HD draws it in the items' role, as the items are.
        _line(surface, screen, view.audience["title"].strip(),
              view.title_field.x, view.title_field.y,
              geom.MENU_X2 - geom.MENU_X1, TITLE_ROLE)
    for item, f in items:
        r = nd.rect(screen.layout, _rect(f))
        if item["enabled"] and screen.hovered(r):
            hud.panel(surface, r, screen.layout.scale, lit=True, dense=True)
        _line(surface, screen, item["text"].strip(), f.x + 4, f.y,
              f.x_end - f.x - 4, ITEM_ROLE,
              None if item["enabled"] else disabled_colour())
