"""The "eta N" label beside a travelling ship — work order 122, item 2.1.

TRANSCRIBED from SHIPS::Print_Eta_On_Ship_Icon_ (ships.cpp:482-506), which
`Do_Ship_Destination_Lines_` calls right after a ship's destination line
(:470-475):

  * only for an icon that gets a line (`maplines.destination_lines`) AND
    whose location is below the wormhole offset, 10000 <= location < 20000
    (:471). An order sets 20000 + star on its own turn, so the label
    appears from the next turn on while the line is already there
    (run 114);
  * the text is HESTRNGS 307, "eta %d", with `(uint8_t)turns_left`
    (:500-503);
  * in the owner's font colours (`Set_Player_Font_Style_`, :494); HD uses
    the owner's colour the map's star names use;
  * font style 1 at zoom 0 and 1, style 0 beyond (:496-497);
  * printed RIGHT-aligned (`fonts::Print_Right_`) with its right edge at
    the icon's left edge plus the width, and its top at the icon's top
    plus the height, of the OWNER's own sprite header — entry
    205 + colour * 4 + (3 - zoom), `Get_Ship_Icon_Pict_Seg_(player, 0)`
    (:490-492) — `zoomtables.SHIP_ICON_HEADER_DIM_BY_COLOUR`.

HD geometry follows the HD VIEWPORT, not the game's zoom (decision 35,
Data 16 September 2026): the header index is 3 - `ctx.zoom`
(`zoomtables.hd_zoom_level`), offsets are native pixels times `ctx.px`, and
the icon's top-left is where HD draws the icon — the mapped native corner
in a coupled view, the ship's own galaxy position less half of colour 0's
header at `ctx.zoom` when decoupled (the corner `Get_Ship_Icon_Coords_In_
Space_` computes, ships.cpp:516-531). The digits are sized to the style's
ink height (`zoomtables.ETA_DIGIT_INK_ROWS`) times `ctx.px`, and the text
goes through `Style.render_text` (decision 30).

DEVIATION — two locks the original has no need for (Data, 16 September
2026). HD keeps drawing the map under every overlay and between
snapshots, the original draws this label only from its own main loop:

  * the label is drawn only while the game reports screen 0 AND the field
    list is the galaxy map's own (`mapboxes.classify(...).known`, no modal
    box): not under the GAME menu, a popup, a dialog or a turn summary.
    The map's own fleet box and system window are part of that loop, and
    the original prints the label with them open;
  * after a star click HD sent as a move ORDER (`boxmodel.remember(order=
    True)`), no label until a snapshot shows the order took effect — a
    ship of the ordered stack changed location or status
    (`Make_Ships_Move_To_` sets both at once, shipmove.cpp:593-600) — or
    until more than `wire_protocol.EFFECT_PAIRS` newer snapshots show no
    change, which is a refused order. The snapshot before the effect
    carries the old `turns_left` ("A fresh message is not a fresh world").
"""
from core import zoomtables as zt
from core.hestrings import printf
from core.structs import ship as ship_struct
from core.wire_protocol import EFFECT_PAIRS
from screens.galaxy_map import mapboxes, maplines
from screens.galaxy_map.renderer import NEUTRAL_COLOR, OWNER_COLORS

#: HESTR_133_ETA_D (ships.cpp:500).
ETA_MESSAGE = 307
#: Used when HESTRNGS is not extracted: a label that does not come from the
#: game is still better than a number without a word.
FALLBACK_TEXT = "eta %d"


def in_own_loop(state):
    """Screen 0, and the list on the wire is the map's own."""
    if state is None or getattr(state, "current_screen", -1) != 0:
        return False
    boxes = mapboxes.classify(getattr(state, "fields", None))
    return boxes.known and not boxes.modal


def hold(state, ships):
    """The lock an HD move order starts: the ordered stack as it stood."""
    sel = getattr(state, "fleet_selection", None) or {}
    chain = sel.get("chain") or []
    nodes = sel.get("ships") or []
    stack = [nodes[n] for n in chain if 0 <= n < len(nodes)]
    # The snapshot itself, not its id(): a freed GameState's address is
    # reused by the next one, and an id comparison then never advances.
    return {"state": state, "seen": 0,
            "ships": {i: (ships[i].location, ships[i].status)
                      for i in stack if 0 <= i < len(ships)}}


def advance(lock, state, ships):
    """The lock after one update; None once released."""
    if lock is None or state is None or state is lock["state"]:
        return lock
    lock = dict(lock, state=state, seen=lock["seen"] + 1)
    for i, before in lock["ships"].items():
        if 0 <= i < len(ships) and (ships[i].location,
                                    ships[i].status) != before:
            return None
    return None if lock["seen"] > EFFECT_PAIRS or not lock["ships"] \
        else lock


def labels(state, ships, stars, players):
    """[(icon index, ship index, owner colour, turns_left)] the original
    prints for this snapshot."""
    out = []
    for line in maplines.destination_lines(state, ships, stars, 0):
        ship = ships[line["ship"]]
        if not ship_struct.LOCATION_MOVING_OFFSET <= ship.location \
                < 2 * ship_struct.LOCATION_MOVING_OFFSET:
            continue
        colour = (getattr(players[ship.owner], "color", 0)
                  if 0 <= ship.owner < len(players) else 0)
        out.append((line["icon"], line["ship"], colour,
                    ship.turns_left & 0xFF))
    return out


def anchor_point(icon, ship, colour, ctx, anchor):
    """HD (right, top) of the label: the icon corner plus the owner's
    header, both from the HD viewport."""
    from core import mapcoords as mc
    view = ctx.view
    if anchor is None:
        left = view.off_x + (icon.x - mc.MAP_LEFT) * view.scale
        top = view.off_y + (icon.y - mc.MAP_TOP) * view.scale
    else:
        cw, ch = zt.ship_icon_header_dimension(ctx.zoom)
        hx, hy = view.to_screen(ship.x, ship.y)
        left, top = hx - (cw >> 1) * ctx.px, hy - (ch >> 1) * ctx.px
    w, h = zt.ship_icon_header_dimension_for_colour(colour, 3 - ctx.zoom)
    return left + w * ctx.px, top + h * ctx.px


def _size(style, rows, px, cache):
    """Font size whose digit ink is `rows * px` HD pixels tall."""
    if "per_px" not in cache:
        probe = style.render_text("0123456789", 100, (255, 255, 255))
        cache["per_px"] = 100 / max(1, probe.get_bounding_rect().h)
    return max(8, round(rows * px * cache["per_px"]))


def render(surface, ctx, state, ships, stars, players, anchor, style,
           strings, lock, cache):
    """Draw every label, or none while a lock stands. Returns what was
    drawn as [(ship, text, (right, top))] for the checks."""
    if lock is not None or not in_own_loop(state):
        return []
    icons = getattr(state, "ship_icons", None) or []
    template = (strings.message(ETA_MESSAGE) if strings is not None
                else None) or FALLBACK_TEXT
    rows = zt.ETA_DIGIT_INK_ROWS[zt.ETA_FONT_STYLE_BY_ZOOM[ctx.zoom]]
    size = _size(style, rows, ctx.px, cache)
    drawn = []
    for icon_i, ship_i, colour, turns in labels(state, ships, stars,
                                                 players):
        text = printf(template, turns)
        right, top = anchor_point(icons[icon_i], ships[ship_i], colour,
                                  ctx, anchor)
        img = style.render_text(text, size,
                                OWNER_COLORS.get(colour, NEUTRAL_COLOR)[:3])
        ink = img.get_bounding_rect()
        surface.blit(img, (round(right) - ink.right, round(top) - ink.y))
        drawn.append((ship_i, text, (right, top)))
    return drawn
