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

THE STAR BOXES (movebox.cpp:292-294, :410-448): in the colony view an
11 x 12 box round `_officer_star_displayed` — colour 0x1E, or the flashing
0x6E ramp when it is also `_officer_star_chosen` (HD draws the ramp's
middle, unanimated) — and round the star under HD's pointer, 0x71. In the
ship view the stack on show is outlined (`Draw_Flashing_Small_Ship_Icon_`,
officer.cpp:765-767, likewise unanimated).

THE VIEW BOX — two views, on a glass panel (work order 175: the
original's box art OFFICER.LBX 1 / 2 is no longer drawn — DEVIATION
`view_box_glass`, decision 71 as for the buttons).

  colony view   the system display of `_officer_star_displayed`
                (`SYS::Draw_System_Display_Popup_` at (306, 17),
                officer.cpp:1928-1946). **OMISSION `system_pictures`**:
                the star picture and the orbits; HD writes the star's
                name and draws each planet in orbit order as the colony
                screens' planet disc with its name, the colonies marked.
  ship view     the big icons of `_small_ship_stack_ptr`, 5 x 3 at
                (302, 19) stepping 62 x 60 (`Get_Fltscrn_Big_Icon_XY_`,
                flt2.cpp:116-128), each the ship's picture out of the
                player's own SHIPS.LBX through `screens/fleets/fltart`
                — the Fleets screen's extraction, reused — and its name;
                the scroll bar on its track (officer.cpp:741-744,
                `ldrgeom.SCROLL_TRACK`).

Both come from open fix 30's block (applied, work order 175). An engine
without it sends none, and the box stays empty — nothing HD chose.
"""
import pygame

from core.hud import blocks as hud

from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

from . import ldrdraw as draw
from . import ldrgeom as geom
from . import ldrmap

#: `_using_colony_screen_palette ? 9 : 10` (movebox.cpp:70), cleared here.
BLACK_HOLE_INDEX = 10
#: The star sprite's offset from its point (movebox.cpp:85).
STAR_OFFSET = (-2, -2)
#: OFFICER.LBX small ship icons: eight player colours from 0x73, then
#: the seven monster owners from 0x7B (officer.cpp:2765-2793).
MONSTER_FIRST = 8
MAX_PLAYERS = 8

#: The star boxes' colours where the palette is not extracted — the
#: grey, the gold and the cyan those indices hold in the colony palette.
BOX_FALLBACK = {ldrmap.BOX_DISPLAYED: (150, 150, 150),
                ldrmap.BOX_CHOSEN: (236, 200, 90),
                ldrmap.BOX_SCANNED: (110, 190, 240)}


def _box_colour(art, index):
    rgb = art.palette_rgb(index) if art is not None else None
    return tuple(rgb) if rgb else BOX_FALLBACK.get(index, (200, 200, 200))


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
    view = screen._view
    block = view.block if view is not None else None
    stack_head = (int(block.get("head_node", -1)) if block is not None
                  and view.view == geom.VIEW_SHIP
                  and int(block.get("stack", -1)) >= 0 else None)
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
        if stack_head is not None and int(icon.node_idx) == stack_head:
            size = sprite.get_size() if sprite is not None else (2, 2)
            r = draw.rect(layout, (x - 1, y - 1, x + size[0], y + size[1]))
            pygame.draw.rect(surface, _box_colour(art, ldrmap.BOX_CHOSEN + 2),
                             r, max(1, int(draw.native_scale(layout))))
    _draw_star_boxes(surface, screen, game_state, art)
    surface.set_clip(previous)


def _draw_star_boxes(surface, screen, game_state, art):
    view = screen._view
    block = view.block if view is not None else None
    width = max(1, int(draw.native_scale(screen.layout)))
    boxes = []
    if block is not None and view.view == geom.VIEW_COLONY:
        shown = int(block.get("star_displayed", -1))
        chosen = shown >= 0 and shown == int(block.get("star_chosen", -1))
        boxes.append((shown, ldrmap.BOX_CHOSEN + 2 if chosen
                      else ldrmap.BOX_DISPLAYED))
    scan = getattr(screen, "_scan", None)
    if scan is not None and scan[0] == "star":
        boxes.append((scan[1], ldrmap.BOX_SCANNED))
    for star, colour in boxes:
        r = ldrmap.star_box_rect(game_state, star)
        if r is not None:
            pygame.draw.rect(surface, _box_colour(art, colour),
                             draw.rect(screen.layout, r), width)


def draw_view_box(surface, screen, view, game_state, art):
    """What is in the view box (the glass panel is `ldrdraw`'s)."""
    block = view.block
    if block is None:
        return
    if view.view == geom.VIEW_COLONY:
        _draw_system(surface, screen, view, game_state, art,
                     int(block.get("star_displayed", -1)))
    else:
        _draw_grid(surface, screen, view, game_state, art, block)
        _draw_scroll(surface, screen, block)


def _draw_scroll(surface, screen, block):
    """`Draw_Generic_Vertical_Scroll_Bar_` on its track: the thumb at the
    block's first row of the stack's rows (flt2.cpp:84-107)."""
    ships = block.get("ship_idx") or []
    rows = -(-len(ships) // geom.GRID_COLUMNS)
    if rows <= geom.GRID_ROWS:
        return
    hud.scrollbar(surface, draw.rect(screen.layout, geom.SCROLL_TRACK),
                  screen.layout.scale, max(0, int(block.get("first_row", 0))),
                  geom.GRID_ROWS, rows)


def _draw_system(surface, screen, view, game_state, art, star):
    """The star's name, then each planet in orbit order as a disc with its
    name under it, a colony's name in the selected ink (OMISSION
    `system_pictures`). The leader stationed there is the strip's, under
    the box (officer.cpp:810-826)."""
    stars = getattr(game_state, "stars", None) or []
    if not 0 <= star < len(stars):
        return
    from screens.colony_summary import colonyplanets, colonyrows
    layout = screen.layout
    r = draw.rect(layout, (geom.SYSTEM_AT[0], geom.SYSTEM_AT[1],
                           geom.VIEW_BOX[2] - 8, geom.VIEW_BOX[3] - 8))
    size = draw.font_px(layout, "strip")
    draw.blit_text(surface, screen.style, stars[star].name, r.centerx,
                   r.y + size // 2, r.w - 8, int(size * 1.2),
                   draw.text_colour(art, "normal"), "center")
    raws = getattr(game_state, "planets_raw", None) or []
    planets = [(i, planet_struct.parse(raws[i]))
               for i in star_struct.planet_indices(stars[star])
               if 0 <= i < len(raws)]
    if not planets:
        return
    note = draw.font_px(layout, "note")
    cell = r.w // max(5, len(planets))
    top = r.y + size * 2
    disc_max = min(cell - 6, r.bottom - top - 3 * note)
    left = r.centerx - cell * len(planets) // 2
    for k, (index, p) in enumerate(planets):
        side = max(6, disc_max * (6 + min(4, int(p.size))) // 10)
        centre = (left + cell * k + cell // 2, top + disc_max // 2)
        disc = None
        if int(p.planet_type) != 2:        # not a gas giant
            discs = colonyplanets.set_for(screen, side)
            disc = discs.get(int(p.climate)) if discs is not None else None
        if disc is not None:
            surface.blit(disc, disc.get_rect(center=centre))
        else:
            pygame.draw.circle(surface, draw.text_colour(art, "normal"),
                               centre, side // 2, max(1, side // 12))
        ink = draw.text_colour(art, "selected" if p.colony_index >= 0
                               else "normal")
        draw.blit_text(surface, screen.style,
                       colonyrows.star_planet_name(stars[star], index),
                       centre[0], top + disc_max + note // 2, cell - 4,
                       note, ink, "center")


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
