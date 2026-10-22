"""The diplomacy system picker over the audience — work order 322 E, on open
fix 109's TPOP kind 25 (id 85).

`DIP_SCRN::Diplomacy_System_Display_` (dip_scrn.cpp:701-805) asks the
player to choose a system — one of his own to offer (Offer Gift > System,
mode 0) or one of the ambassador's to demand (Demand > Surrender System,
mode 1). Its auto function draws the audience as ever
(`Draw_Diplomacy_Synch_Mode_`: the room, the ambassador, the statement —
here "Choose a system to offer ..." / "... demand ... surrender to you.")
and over it `Draw_Diplomacy_System_Display_` (:834-850): a box with the
galaxy at (10, 171) 180 x 110 (`Draw_Diplomacy_System_`, :828-832),
"Choose A System:" at (10, 117), CANCEL at (18, 141), lit while hovered,
and for the hovered system of the giver's the lines of
`Draw_Diplomacy_System_Text_` from (10, 287) (:2329-2374).

TRANSCRIPTION `system_picker` — what a click does: a star's own hidden
field is activated, the one the engine's tail names for that star
(`core.systempickerwire.star_field`, resolved in the list just read by
its index, type and rectangle, P816); only a star the original takes —
the giver's, `May_Surrender_Star_` allowing it, no capitol (:775-790) —
is sent: any other click there the original reads and ignores, so HD
refuses it before it goes out (decision 33). CANCEL's own field (args[3],
:740) ends the picker with -1. No key does anything: no field carries a
hotkey and ESC ends it only in a network game (:771). The hover is HD's
pointer over the stars' own fields (the engine's pointer does not move);
the words are the engine's — the title, the statement, CANCEL and the
lines' templates, decoded as `Decode_Text_Message_` does for the two codes
they carry (0x81 the star's name, 0x82 the number) — narrower than the
original: the other codes are dropped and its length caps not applied
(`core.systempickerwire.decode` says where).
DEVIATION `hud_frameless` (the audience's): a HUD panel behind the title
and CANCEL and behind the hover's lines, where the original prints on the
room.
DEVIATION `picker_hud_box`: the galaxy box is a HUD panel and its stars
the inset maps' dots in the owners' colours (`colonyrows.
galaxy_inset_stars`, the colony screens' palette as the picker sets it,
:715), where the original draws DIPSTARS.LBX's background and FLEET.LBX's
star sprites (view mode 4, movebox.cpp:89-91) — neither is extracted.
DEVIATION `picker_special_colour`: the original prints a system it will
not take in its special colours (palette index 250 against 253,
dip_scrn.cpp:63-65, not measured); HD uses its `sub` text role.
UNVERIFIED `system_picker_live`: drawn from stand-in bytes only, not yet
from the engine (Data's decision of 20 October 2026: no live runs).
"""
import pygame

from core import lang
from core import systempickerwire as wire
from core.hud import blocks as hud
from core.hud import text as hudtext
from screens.colony_summary import colonyinset, colonyrows
from core import nativedraw as nd

from . import augeom as geom

#: The box `Draw_Diplomacy_System_` frames: `Box(9, 0xAA, 0xB6, 0x70)`
#: (:829) — x 9..191, y 170..282.
BOX = (9, 0xAA, 9 + 0xB6, 0xAA + 0x70)
TITLE_AT = (10, 0x75)
CANCEL_AT = (0x12, 0x8D)
#: The hover lines (:2348, :2356, :2370): the star line, the population,
#: then each planet 14 px apart from 323.
STAR_LINE_Y, POP_LINE_Y, PLANET_Y0, PLANET_STEP = 287, 309, 323, 14
LINES_W = 240
#: The HUD panel behind the title and CANCEL (DEVIATION `hud_frameless`,
#: as behind the menu): the galaxy box's own width, `augeom.MENU_MARGIN`
#: above the title (y 117) and below CANCEL's field (to y 162).
HEAD_PANEL = (BOX[0], 0x75 - geom.MENU_MARGIN, BOX[2],
              0xA2 + geom.MENU_MARGIN)
#: The hover lines' text starts at x 10 (:2348); their panel stands
#: `augeom.MENU_MARGIN` round it, as the menu's does.
LINES_X = 10
#: Font 3's share of font 4's height (the population and planet lines):
#: HD's two sizes, 16 and 13 native px.
SMALL = 13 / 16
#: The colony screens' black-hole index: the picker sets
#: `_using_colony_screen_palette` (:715; movebox.cpp:70).
BLACK_HOLE = 9


def popup_of(state):
    """TPOP kind 25 while the engine reports 85, else None."""
    tp = getattr(state, "turn_popup", None)
    if tp is None or tp.get("kind") != "system_picker" or \
            tp.get("picker") is None or \
            getattr(state, "current_screen", -1) != geom.PICKER_SCREEN_ID:
        return None
    return tp


def _size(screen, small=False):
    px = geom.TEXT_PX * (SMALL if small else 1.0)
    return max(nd.MIN_FONT, int(round(px * nd.native_scale(screen.layout))))


def _print(surface, screen, words, at, w, colour, small=False):
    x, y = nd.point(screen.layout, *at)
    width = nd.rect(screen.layout, (0, 0, w, 1)).w
    return nd.blit_text(surface, screen.style, words, x, y, width,
                        _size(screen, small), colour)


def star_under(popup, state, native):
    """The star whose live field holds native point `native`, or None."""
    if native is None:
        return None
    nx, ny = native
    for star in range(len(popup["picker"]["fields"])):
        f = wire.star_field(popup, state, star)
        if f is not None and f.x <= nx <= f.x_end and f.y <= ny <= f.y_end:
            return star
    return None


def cancel_rect(screen):
    return nd.rect(screen.layout, wire.CANCEL_RECT)


def draw(surface, screen, view, native):
    """The picker's box, title, CANCEL and the hovered system's lines;
    `native` is the pointer's native point (None off the picture). The
    popup, the fields and the stars all come from the one state the view
    was read from."""
    popup, state = view.picker, view.game_state
    with lang.verbatim():          # every word is the engine's
        nd.draw_box(surface, screen, HEAD_PANEL)
        box = nd.draw_box(surface, screen, BOX)
        _stars(surface, box, state)
        value = hudtext.colour("value")
        if popup.get("title"):
            _print(surface, screen, popup["title"].strip(), TITLE_AT,
                   LINES_W, value)
        c = cancel_rect(screen)
        if screen.hovered(c):
            hud.panel(surface, c, screen.layout.scale, lit=True, dense=True)
        _print(surface, screen, popup["picker"]["cancel"].strip(),
               CANCEL_AT, wire.CANCEL_RECT[2] - CANCEL_AT[0], value)
        star = star_under(popup, state, native)
        system = wire.system_of(popup, star) if star is not None else None
        if system is not None:
            _hover_lines(surface, screen, popup, system, state)


def _stars(surface, box, state):
    x0, y0, w, h = wire.MAP
    fx, fy = box.w / float(BOX[2] - BOX[0]), box.h / float(BOX[3] - BOX[1])
    ox, oy = box.x + (x0 - BOX[0]) * fx, box.y + (y0 - BOX[1]) * fy
    dot = max(2, int(round(3 * fx)))
    clip = surface.get_clip()
    surface.set_clip(box)
    for sx, sy, cidx in colonyrows.galaxy_inset_stars(
            state, wire.MAP, black_hole=BLACK_HOLE):
        colour = colonyinset.INSET_COLORS.get(
            cidx, colonyinset.INSET_COLORS[8])[:3]
        cx, cy = int(ox + sx * fx), int(oy + sy * fy)
        # LOOK EXCEPTION picture: the picker's stars in the owners' colours (movebox.cpp)
        pygame.draw.rect(surface, colour,
                         (cx - dot // 2, cy - dot // 2, dot, dot))
    surface.set_clip(clip)


def _star_name(state, star):
    stars = getattr(state, "stars", None) or []
    if 0 <= star < len(stars):
        return str(getattr(stars[star], "name", "") or "")
    return ""


def _hover_lines(surface, screen, popup, system, state):
    rows = wire.lines(popup, system, _star_name(state, system["star"]))
    ys = [STAR_LINE_Y, POP_LINE_Y] + [
        PLANET_Y0 + PLANET_STEP * i for i in range(len(rows) - 2)]
    m = geom.MENU_MARGIN
    nd.draw_box(surface, screen, (LINES_X - m, STAR_LINE_Y - m,
                                  LINES_X + LINES_W + m,
                                  ys[-1] + geom.TEXT_PX + m))
    for k, ((words, special), y) in enumerate(zip(rows, ys)):
        colour = hudtext.colour("sub" if special else "value")
        _print(surface, screen, words, (LINES_X, y), LINES_W, colour,
               small=k > 0)


def click(screen, state, popup, x, y, native):
    """The field a click at window (x, y) sends, as (field, label), or
    None: CANCEL's, or a star's the original takes."""
    if cancel_rect(screen).collidepoint(x, y):
        f = wire.cancel_field(popup, state)
        return (f, "cancel") if f is not None else None
    star = star_under(popup, state, native)
    if star is None:
        return None
    system = wire.system_of(popup, star)
    if system is None or not wire.selectable(system):
        return None                 # the original reads it and ignores it
    f = wire.star_field(popup, state, star)
    return (f, f"system {star}") if f is not None else None
