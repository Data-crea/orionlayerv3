"""The fleet box's cells: the ship under the pointer and the damage bars —
work order 313 (Data, 19 October 2026: "Bau beides ein").

No pygame in the rules, so a test can call each one; `draw_bar` is the one
drawing function.

TRANSCRIPTION `box_scanned_name`: with the fleet box open the ship under the
pointer is the scanned ship — `Scan_Fleet_Movement_Box_Fields_` finds the
cell whose field is the scanned field, any shown cell, offered or not
(mainscr.cpp:3337-3347), and the caller sets `_fleet_ship_scanned` to it and
`_eta_star_id` to -1 (:3422-3428). The box's info line is then info type 0
(`Print_Fleet_Box_Info_`, fleetpop.cpp:1028-1031), the text of
`Get_Fleetpop_Scanned_Ship_Info_` (fleetpop.cpp:1368-1392): an own ship its own name
(`ship->d.name`, the design's name), a foreign combat ship of a player or the
Antarans (owner <= 8) its hull class (`_hull_data[size].name`, read as
`shipparts`' "hulls"), anything else the ship's name. The move line to a
hovered star (info types 1-8, :1063-1150) needs `_eta_star_id > -1`, which
the scan has just cleared, so a hovered cell always wins and the move line
comes back when the pointer leaves the cells — and the map's ETA line goes
with it (mainscr_main.cpp:971: drawn only while no ship is scanned). Where
the player's install gave no hull names (a fresh clone) the line is empty,
as an empty text prints nothing in the original (fleetpop.cpp:1160).

TRANSCRIPTION `box_damage_bars`: each cell of an OWN stack holding a combat
ship gets `Draw_Damage_Bars_(icon.x - 1, icon.y, 0x35, 0x35, 4, ship)`
(fleetpop.cpp:748-762; fleetpop.cpp:41-84), after its picture: `eff = 0x35 - 4`, green
`current * eff / max` (at least 2), red the rest; nothing while current ==
max; a red of 1 becomes 2 with green `width - 6`; green outlined 0x70
(top, left) / 0x72 (right, bottom) filled 0x71, red 0x4B / 0x4E filled
0x4D, five native rows from `icon.y + 0x35 - 5`, from `icon.x + 3`. The
hits are `AIPOWER::Max_Ship_Hits_` / `Current_Ship_Hits_` (aipower.cpp:200-
248): structure (`Get_Ship_Structure_`) plus armour (`Get_Ship_Armor_Hits_`),
less `structural_damage` and `armor_damage` (`core/monsterhull` has both
sums). HD lays the native cell (0x35 square) over its cell, so the bar
scales with it and stands over the picture. The six colours are the main
palette's (FONTS.LBX entry 1, `Load_Palette_(0)`), in colors.json
`fleet_damage_green` / `fleet_damage_red`.

OMISSION `damage_bar_strategic`: with the strategic combat setting the
original's maximum is the hull's `strat_hits` plus an armour bonus and the
armour damage is not subtracted (aipower.cpp:201-224, :240-246); that
setting is not on HD's wire, so HD always computes the tactical hits.
"""
from core import monsterhull
from core import palette
from core.structs import ship as ship_struct

#: The fleet box icon's field, native px (fleetpop.cpp:164).
CELL = 0x35
#: `Draw_Damage_Bars_`'s arguments for the fleet box (fleetpop.cpp:754-760).
BAR_WIDTH, BAR_Y_OFFSET, BAR_X_OFFSET, BAR_X_SHIFT = 0x35, 0x35, 4, -1
#: Owners up to here are players or the Antarans (fleetpop.cpp:1384).
SCANNED_HULL_OWNER_MAX = 8
#: (outline top/left, fill, outline right/bottom) of each part, the main
#: palette's 0x70 / 0x71 / 0x72 and 0x4B / 0x4D / 0x4E (fleetpop.cpp:64-82).
GREEN = tuple(tuple(c) for c in palette.col(
    "galaxy_map", "fleet_damage_green", ((0, 76, 0), (0, 96, 0), (8, 112, 8))))
RED = tuple(tuple(c) for c in palette.col(
    "galaxy_map", "fleet_damage_red",
    ((80, 12, 12), (116, 24, 24), (136, 32, 32))))


def scanned_index(cells, pointer):
    """The shown cell under the pointer, or None."""
    if pointer is None:
        return None
    return next((i for i, c in enumerate(cells) if c.collidepoint(pointer)),
                None)


def scanned_name(ship, player_num, parts):
    """`Get_Fleetpop_Scanned_Ship_Info_`'s text for `ship` (a parsed
    record); `parts` the hull names (`ShipPartNames`), or None."""
    if ship is None:
        return ""
    owner = int(ship.owner)
    if owner == player_num:
        return str(ship.name)
    if owner <= SCANNED_HULL_OWNER_MAX and \
            int(ship.ship_type) == ship_struct.SHIP_TYPE_COMBAT:
        name = parts.name("hulls", int(ship.size)) if parts is not None \
            else None
        return name or ""
    return str(ship.name)


def info_line(scanned, over, status):
    """(text, refused) of the box's info line: the scanned ship's text when
    a cell is under the pointer (`scanned` not None), else the move to the
    hovered star (`over`, `boxmodel.hover_status`), else the status."""
    if scanned is not None:
        return scanned, False
    if over is not None:
        return over[0], bool(over[1])
    return status, False


def hits(ship):
    """(current, max) by `Current_Ship_Hits_` / `Max_Ship_Hits_` for the
    tactical game, or None where the tables have no row."""
    structure = monsterhull.structure(ship)
    armour = monsterhull.armour(ship)
    if structure is None or armour is None:
        return None
    most = structure + armour
    return (most - int(ship.structural_damage) - int(ship.armor_damage),
            most)


def bar_widths(current, most, width=BAR_WIDTH):
    """(green, red) of `Draw_Damage_Bars_`, or None while undamaged."""
    if most <= 0 or current == most:
        return None
    eff = width - 4
    green = max(2, int(current * eff / most))      # C division, positive
    red = eff - green
    if red == 1:
        red, green = 2, width - 6
    return green, red


def bar_pixels(green, red):
    """[(x0, y0, x1, y1, colour)] native, end-exclusive, relative to the
    icon field's corner: the two outlined parts as the original's lines and
    fills draw them (fleetpop.cpp:60-83)."""
    x = BAR_X_SHIFT + BAR_X_OFFSET
    y = BAR_Y_OFFSET - 5
    out = []

    def part(x0, x1, ramp):
        lit, fill, dark = ramp
        out.extend(((x0, y, x1 + 1, y + 1, lit), (x0, y, x0 + 1, y + 5, lit),
                    (x1, y + 1, x1 + 1, y + 5, dark),
                    (x0 + 1, y + 4, x1 + 1, y + 5, dark)))
        if x1 - 1 >= x0 + 1:
            out.append((x0 + 1, y + 1, x1, y + 4, fill))
    if green > 0:
        part(x, x + green, GREEN)
    if red > 1:
        start = x + green + 1
        part(start, start + red, RED)
    return out


def bar_for(ship, stack_owner, player_num):
    """The bar's native pixels for one cell, or [] — an own stack's combat
    ship that is damaged (fleetpop.cpp:748-750)."""
    if ship is None or stack_owner != player_num or \
            int(ship.ship_type) != ship_struct.SHIP_TYPE_COMBAT:
        return []
    got = hits(ship)
    widths = bar_widths(*got) if got is not None else None
    return bar_pixels(*widths) if widths is not None else []


def draw_bar(surface, cell, pixels):
    """The native pixels laid over the HD cell: the native field 0x35 square
    fitted to the cell, each native pixel edge rounded to device px."""
    if not pixels:
        return
    side = min(cell.w, cell.h)
    s = side / float(CELL)
    ox, oy = cell.centerx - side / 2.0, cell.centery - side / 2.0
    for x0, y0, x1, y1, colour in pixels:
        X0, X1 = int(round(ox + x0 * s)), int(round(ox + x1 * s))
        Y0, Y1 = int(round(oy + y0 * s)), int(round(oy + y1 * s))
        # a native pixel never rounds away: below one device px a native
        # px (a cell under 53 px, 1280 x 720) the one-pixel outlines would
        # drop out on some cells (the review of 313)
        X1, Y1 = max(X1, X0 + 1), max(Y1, Y0 + 1)
        if X1 > X0 and Y1 > Y0:
            # LOOK EXCEPTION transcription: the original's damage bar, its
            # lines and fills in the main palette's colours
            surface.fill(colour, (X0, Y0, X1 - X0, Y1 - Y0))
