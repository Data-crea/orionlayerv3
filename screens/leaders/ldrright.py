"""The Leaders screen's right half: the view box and the galaxy box.

THE GALAXY BOX — TRANSCRIPTION. `MOVEBOX::Draw_Galaxy_Map_Box_(…, 306,
235, 318, 169, …)` (officer.cpp:756): the stars through
`colonyrows.galaxy_inset_stars` — the one transform all the inset maps
share, given this screen's box — with the black-hole index 10, because
this screen clears `_using_colony_screen_palette` (officer.cpp:866;
movebox.cpp:70), and each star the original's own sprite, OFFICER.LBX
`0x82 + colour` (officer.cpp:2206-2214) at frame 0, offset (-2, -2)
(movebox.cpp:84-85). The ship stacks: `Draw_Fltscrn_Small_Ship_Icons_`
(flt1.cpp:216-235) — OFFICER.LBX `0x73 + player colour` for a player,
`0x7B + (owner - 8)` for a monster, at `s_ship_icon.x/y`, which
`Set_Fltscrn_Small_Ship_Icon_XYs_(0x132, 0xEB, 0x13E, 0xA9)` has put in
this box's space on entry (officer.cpp:905). Last drawn first: the loop
runs from the last icon down.

THE VIEW BOX — two views, and the original's own box art behind each
(OFFICER.LBX 2 colony, 1 ship, at (300, 12), officer.cpp:1197-1203).

  colony view   the system display of `_officer_star_displayed`
                (`SYS::Draw_System_Display_Popup_` at (306, 17),
                officer.cpp:1928-1946). **OMISSION `system_pictures`**:
                the star and planet pictures, whose artwork this order
                has not extracted — HD writes the star's name and its
                planet slots instead; the strip under the box names the
                leader stationed there, as the original's does.
  ship view     the big icons of `_small_ship_stack_ptr`, 5 x 3 at
                (302, 19) stepping 62 x 60 (`Get_Fltscrn_Big_Icon_XY_`,
                flt2.cpp:116-128), each the ship's picture out of the
                player's own SHIPS.LBX through `screens/fleets/fltart`
                — the Fleets screen's extraction, reused — and its name.

**HD STATE, open fix 30.** Which star and which stack are on show is
not on the wire without `doc/ext_officer_screen_state.patch` (NOT
APPLIED). Until then both views draw a marked placeholder in the box
that names the item, rather than a star or a stack HD chose.
"""
import pygame

from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

from . import ldrdraw as draw
from . import ldrgeom as geom

#: `_using_colony_screen_palette ? 9 : 10` (movebox.cpp:70), cleared here.
BLACK_HOLE_INDEX = 10
#: The star sprite's offset from its point (movebox.cpp:85).
STAR_OFFSET = (-2, -2)
#: OFFICER.LBX small ship icons: eight player colours from 0x73, then
#: the seven monster owners from 0x7B (officer.cpp:2765-2793).
MONSTER_FIRST = 8
MAX_PLAYERS = 8

#: What the placeholder says. Words of ours, marked HD STATE.
PLACEHOLDER = ("Not on the wire yet: which {what} the game shows here "
               "(open fix 30, doc/ext_officer_screen_state.patch).")


def _colour_of(game_state, owner):
    raws = getattr(game_state, "player_raw", None) or []
    if 0 <= owner < len(raws):
        return int(player_struct.SPEC.parse(raws[owner]).color)
    return None


def draw_galaxy_box(surface, screen, game_state, art):
    """Stars and stacks in the galaxy box, clipped to it
    (`Set_Window_` + `Clip_On_`, movebox.cpp:57-59)."""
    if game_state is None:
        return
    layout = screen.layout
    box = draw.rect(layout, geom.GALAXY_BOX)
    bx, by, bw, bh = geom.GALAXY_BOX_XYWH
    fx, fy = box.w / float(bw), box.h / float(bh)
    have_art = art is not None and art.available
    previous = surface.get_clip()
    surface.set_clip(box)
    dot = max(2, int(round(2 * layout.scale)))
    for sx, sy, colour in colonyrows.galaxy_inset_stars(
            game_state, geom.GALAXY_BOX_XYWH, black_hole=BLACK_HOLE_INDEX):
        x, y = box.x + sx * fx, box.y + sy * fy
        sprite = art.star(colour) if have_art else None
        if sprite is not None:
            big = draw.magnified(sprite, layout)
            step = big.get_width() // max(1, sprite.get_width())
            surface.blit(big, (int(x) + STAR_OFFSET[0] * step,
                               int(y) + STAR_OFFSET[1] * step))
        else:
            pygame.draw.rect(surface, draw.TEXT_FALLBACK["normal"],
                             (int(x), int(y), dot, dot))
    icons = list(getattr(game_state, "ship_icons", None) or [])
    for icon in reversed(icons):
        x, y = int(icon.x), int(icon.y)
        if x < 0 or y < 0:
            continue
        owner = getattr(icon, "owner", None)
        sprite = None
        if have_art and owner is not None:
            if owner < MAX_PLAYERS:
                colour = _colour_of(game_state, owner)
                if colour is not None:
                    sprite = art.sprite(f"small_ship_{colour}")
            elif owner - MONSTER_FIRST < 7:
                sprite = art.sprite(f"small_ship_{8 + owner - MONSTER_FIRST}")
        at = draw.point(layout, x, y)
        if sprite is not None:
            surface.blit(draw.magnified(sprite, layout), at)
        else:
            pygame.draw.rect(surface, draw.TEXT_FALLBACK["selected"],
                             (at[0], at[1], dot * 2, dot * 2))
    surface.set_clip(previous)


def draw_view_box(surface, screen, view, game_state, art):
    """The box art of the view that is up, and what is in it."""
    layout = screen.layout
    name = "colony_box" if view.view == geom.VIEW_COLONY else "fleet_box"
    sprite = art.sprite(name) if art is not None and art.available else None
    if sprite is not None:
        w, h = sprite.get_size()
        x, y = geom.VIEW_BOX[:2]
        r = draw.rect(layout, (x, y, x + w - 1, y + h - 1))
        surface.blit(draw.stretched(sprite, r), r.topleft)
    block = view.block
    if block is None:
        _placeholder(surface, screen, "star" if view.view == geom.VIEW_COLONY
                     else "fleet", art)
        return
    if view.view == geom.VIEW_COLONY:
        _draw_system(surface, screen, view, game_state, art,
                     int(block.get("star_displayed", -1)))
    else:
        _draw_grid(surface, screen, view, game_state, art, block)


def _placeholder(surface, screen, what, art):
    r = draw.rect(screen.layout, (geom.SYSTEM_AT[0], geom.SYSTEM_AT[1],
                                  geom.VIEW_BOX[2] - 8, geom.VIEW_BOX[3] - 8))
    size = draw.font_px(screen.layout, "note")
    from core import textfit
    lines = textfit.wrap_text(screen.style, PLACEHOLDER.format(what=what),
                              size, r.w - 40)
    # A panel of its own behind the words, so they never sit on the box
    # art's cell lines (the order: text fits its box cleanly).
    step = int(size * 1.2)
    panel = pygame.Rect(0, 0, r.w - 20, step * len(lines) + size)
    panel.center = r.center
    surface.fill(tuple(draw.BOX_FILL)[:3], panel)
    screen.style.draw_plate(surface, panel, screen.layout.scale,
                            draw.BOX_OUTLINE)
    y = panel.y + size // 2
    for line in lines:
        draw.blit_text(surface, screen.style, line, r.centerx, y, r.w - 40,
                       size, draw.text_colour(art, "normal"), "center")
        y += step


def _draw_system(surface, screen, view, game_state, art, star):
    """The star's name and its planet slots by orbit — words where the
    original draws pictures (OMISSION `system_pictures`). The leader
    stationed there is the strip's, under the box (officer.cpp:810-826)."""
    stars = getattr(game_state, "stars", None) or []
    if not 0 <= star < len(stars):
        return
    layout = screen.layout
    r = draw.rect(layout, (geom.SYSTEM_AT[0], geom.SYSTEM_AT[1],
                           geom.VIEW_BOX[2] - 8, geom.VIEW_BOX[3] - 8))
    size = draw.font_px(layout, "strip")
    ink = draw.text_colour(art, "normal")
    y = r.y + size // 2
    draw.blit_text(surface, screen.style, stars[star].name, r.centerx, y,
                   r.w - 8, int(size * 1.2), ink, "center")
    y += int(size * 2)
    raws = getattr(game_state, "planets_raw", None) or []
    for slot, index in enumerate(star_struct.planet_indices(stars[star])):
        if not 0 <= index < len(raws):
            continue
        p = planet_struct.parse(raws[index])
        line = f"{slot + 1}.  " + ("colony" if p.colony_index >= 0 else
                                   "—")
        draw.blit_text(surface, screen.style, line, r.x + 12, y, r.w - 24,
                       size, ink)
        y += int(size * 1.3)


def _draw_grid(surface, screen, view, game_state, art, block):
    """The ship view's big icons, from the block, in its display order."""
    ships = block.get("ship_idx") or []
    first = max(0, int(block.get("first_row", 0))) * geom.GRID_COLUMNS
    raws = getattr(game_state, "ships_raw", None) or []
    layout = screen.layout
    size = draw.font_px(layout, "note")
    ink = draw.text_colour(art, "normal")
    for slot in range(geom.GRID_COLUMNS * geom.GRID_ROWS):
        k = first + slot
        if k >= len(ships):
            break
        idx = ships[k]
        if not 0 <= idx < len(raws):
            continue
        rec = ship_struct.SPEC.parse(raws[idx])
        cell = draw.rect(layout, geom.grid_cell(slot))
        _draw_ship_picture(surface, layout, cell, rec, game_state)
        draw.blit_text(surface, screen.style, rec.name, cell.centerx,
                       cell.bottom - size - 2, cell.w - 4, size, ink,
                       "center")
        if int(block.get("picked_icon", -1)) == k:
            pygame.draw.rect(surface, draw.text_colour(art, "selected"),
                             cell, max(1, int(layout.scale * 2)))


def _draw_ship_picture(surface, layout, cell, rec, game_state):
    """The ship's own picture, the Fleets screen's way: the SPRITE set by
    `previous_owner`, the colour RAMP by `owner` (ken.cpp:451-466,
    `screens/fleets/fltrows.cells`), centred in the 0x39 cell by the
    original's own rounding (`fltart.cell_offset`, flt1.cpp:81-86), at
    an integer magnification (HD EXTENSION `sprite_scale`). Absent art
    draws nothing and the name below still stands."""
    from screens.fleets import fltart, fltrows
    art = fltart.load()
    if not art.available:
        return
    built = fltrows.player_colour(game_state, getattr(rec, "previous_owner",
                                                      None))
    held = fltrows.player_colour(game_state, getattr(rec, "owner", None))
    sprite = art.ship(int(rec.picture_num),
                      fltrows.MONSTER_SET if built is None else built,
                      owner=fltrows.MONSTER_SET if held is None else held)
    if sprite is None:
        return
    step = max(1, int(draw.native_scale(layout)))
    ox, oy = fltart.cell_offset(sprite.get_width(), sprite.get_height(),
                                cell=geom.GRID_CELL)
    surface.blit(fltart.magnified(sprite, step),
                 (cell.x + ox * step, cell.y + oy * step))
