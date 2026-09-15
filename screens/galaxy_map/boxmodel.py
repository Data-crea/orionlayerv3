"""What the galaxy map's two movable boxes show, and whether HD may show it.

No pygame here, so every rule below is a plain function a test can call.

IDENTITY (Data's decision A2, brief 111). The star or stack a box belongs
to is not on the wire (`_moveable_box[].id`). HD takes it from its own
last map click that went out, and draws a box ONLY when the live field
list agrees with that click:

  * the window sits where `MAINSCR::Popup_XY_` (mainscr.cpp:1060-1082)
    puts a box for that star or icon — the quadrant rule — and a fleet
    box is then clamped into the map by
    `FLEETPOP::Set_Fleet_Box_Data_Dimensions_` (fleetpop.cpp:1441-1452).
    Measured live on three boxes (brief 110 Stop 1, run 113);
  * system window: every planet field lies on the orbit ellipse of one
    planet of that star, and every planet has one. A field is centred on
    the window corner plus (0x0D + 0xA1, 0x2F + 0x5A) plus
    `GEO::Get_Orbit_Display_X_Y_` (sys.cpp:1829-1834 with the offsets of
    `Wrapper_For_Normal_System_Fields_`, mainscr.cpp:4391-4406), and that
    position lies on `GEO::_orbit_consts[orbit + 1]` (geo.cpp:5-13). The
    engine sorts the display slots by their y (`qsort_sys_disp_`,
    sys.cpp:172 and :316), so the field ORDER says nothing about which
    planet it is; the ellipse does, with no angle and no stardate. Live on
    Yian: 1.015 on orbit 3 and 0.989 on orbit 4, and the orbit-3 field is
    the one that opened "Yian Prime is an outpost planet";
  * fleet box: one icon field per ship, at most nine
    (fleetpop.cpp:648-650), 0x35 square (:164).

A mismatch draws nothing and says why. A box HD did not open — the game
reopening the system window after the colony screen, a click in the game
window — is drawn only if the last HD click still explains it.

THE TEXTS ARE THE ORIGINAL'S (HESTRNGS, `core/hestrings.py`):
  * system title: H 0x16A "Star System %s" when the system may be viewed
    (visited or Galactic Lore, not a black hole: `SYS::Ok_To_View_System_`,
    sys.cpp:71-83) or when a colony there belongs to a player we have met
    (`HAROLD::Contact_With_One_Colony_`); else H 0x16B (sys.cpp:691-707);
  * an unviewable system's text: H (0x0F + spectral class)
    (`Print_Empty_System_Data_`, sys.cpp:176, black hole 0x15);
  * a viewable system with a wormhole: H 0x16C "Wormhole links %s" if its
    far end is visited, else H 0x16D (sys.cpp:740-780);
  * fleet title: H 0x66 "%s Fleet" with the race name for a player,
    the ship's own name in capitals for a monster (fleetpop.cpp:615-627);
  * fleet status (fleetpop.cpp:1094-1150 with
    `Get_Absolute_Location_Scan_Info_`): H 0x67 "Orbiting %s" while
    parked, H 0x69 / 0x6A "%d turn(s) to %s" on the way to a visited
    star, H 0x6B / 0x6C "ETA %d turn(s)" to an unvisited one, H 0x68 for
    Antares. `turns_left` carries no 20000 condition here, so on the turn
    of the order the box already says "3 turns to" — the "eta N" label on
    the MAP is the one that waits a turn (ships.cpp:472-475, run 114).
    DEVIATION: the original prints this line only while no icon is
    selected and nothing is hovered; HD does not know the selection (not
    on the wire), so HD prints the stack's own status always.
"""
from dataclasses import dataclass

from core import hestrings
from core import mapcoords as mc
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct
from screens.galaxy_map import ships as ship_icons

#: GEO::_orbit_consts, geo.cpp:5-13 — ellipse radii in TENTHS of a pixel;
#: orbit n uses row n + 1 (geo.cpp:367-368).
ORBIT_CONSTS = ((225, 118), (464, 242), (704, 372), (949, 502),
                (1199, 632), (1423, 751), (1650, 873))
#: The planet field's centre relative to the window corner, sys.cpp:1829-1834.
ORBIT_CENTRE = (0x0D + 0xA1, 0x2F + 0x5A)
#: Largest distance from 1.0 a planet field may sit off its ellipse. The
#: engine rounds a position to whole pixels and the field to an integer
#: half-diameter; the live fits were 0.989 and 1.015.
ELLIPSE_TOLERANCE = 0.2
#: A planet's field is square and no larger than this (`_rot_plan_dim`,
#: 0x13 to 0x18, harold.cpp:1491-1494).
PLANET_FIELD_MAX = 30
FLEET_ICON_SPAN = 0x35          # fleetpop.cpp:164, x_end - x
FLEET_ICONS_MAX = 9             # fleetpop.cpp:648-650
PLANET_TYPE_ASTEROID = 1        # orion2_consts.h:402
H_SYSTEM, H_UNEXPLORED = 0x16A, 0x16B
H_WORMHOLE, H_WORMHOLE_UNKNOWN = 0x16C, 0x16D
H_STAR_CLASS = 0x0F
H_FLEET, H_ORBITING, H_ANTARES = 0x66, 0x67, 0x68
H_TURN, H_TURNS, H_ETA_TURN, H_ETA_TURNS = 0x69, 0x6A, 0x6B, 0x6C


@dataclass
class Identity:
    kind: str                   # "system" or "fleet"
    star: int = -1
    ship: int = -1              # the clicked icon's ship
    icon: tuple = None          # its native (x, y) when clicked


def remember(screen, plan, icons, ships):
    """Keep the click the game was sent as the next box's identity."""
    if plan.send is None:
        return
    if plan.what == "star":
        screen._box_identity = Identity("system", star=plan.target)
    elif plan.what == "icon":
        icon = icons[plan.target]
        nodes = ship_icons.build_node_map(ships)
        ship = nodes[icon.node_idx] if 0 <= icon.node_idx < len(nodes) else -1
        screen._box_identity = Identity("fleet", ship=ship,
                                        icon=(icon.x, icon.y))


def popup_xy(index, x, y, w, h):
    """MAINSCR::Popup_XY_: (253, 200) itself falls to the last branch."""
    tall = h if index == 0 else 0
    if x < 253 and y < 200:
        return 527 - w, 421 - tall
    if x < 253 and y > 200:
        return 527 - w, 22
    if x > 253 and y < 200:
        return 22, 421 - tall
    return 22, 22


def fleet_xy(icon_x, icon_y, w, h):
    """Set_Popup_Draw_XY_(2, icon) then the clamp into the map."""
    x, y = popup_xy(2, icon_x - 21, icon_y - 21, w, h)
    if x + w > mc.MAP_RIGHT:
        x = mc.MAP_RIGHT - w
    if y + h > mc.MAP_BOTTOM:
        y = mc.MAP_BOTTOM - h
    return x, y


def _size(box):
    x0, y0, x1, y1 = box.rect
    return x1 - x0, y1 - y0


def _msg(text, index, *values):
    template = text.message(index) if text is not None else None
    if template is None:
        return ""
    return hestrings.printf(template, *values) if values else template


def planet_fields(box):
    """The system window's planet fields: square hidden fields straight
    after the close button and the title strip (sys.cpp:1781-1843)."""
    out = []
    for f in box.fields[2:]:
        span = f.x_end - f.x
        if f.field_type != 7 or span != f.y_end - f.y \
                or span > PLANET_FIELD_MAX:
            break
        out.append(f)
    return out


def match_planets(box, planets):
    """{field index: planet record} by orbit ellipse, or None."""
    x0, y0 = box.rect[:2]
    ox, oy = x0 + ORBIT_CENTRE[0], y0 + ORBIT_CENTRE[1]
    matched = {}
    for f in planet_fields(box):
        cx = f.x + (f.x_end - f.x) // 2
        cy = f.y + (f.y_end - f.y) // 2
        best = None
        for p in planets:
            rx, ry = (v / 10.0 for v in ORBIT_CONSTS[p["orbit"] + 1])
            err = abs(((cx - ox) / rx) ** 2 + ((cy - oy) / ry) ** 2 - 1.0)
            if best is None or err < best[0]:
                best = (err, p)
        if best is None or best[0] > ELLIPSE_TOLERANCE:
            return None
        matched[f.index] = best[1]
    if sorted(p["planet"] for p in matched.values()) != \
            sorted(p["planet"] for p in planets):
        return None
    return matched


def star_planets(state, star):
    """The star's planets that get a field: not empty, not an asteroid."""
    raws = getattr(state, "planets_raw", None) or []
    out = []
    for slot, index in enumerate(star_struct.planet_indices(star)):
        if not 0 <= index < len(raws):
            continue
        p = planet_struct.parse(raws[index])
        if p.planet_type == PLANET_TYPE_ASTEROID:
            continue
        out.append({"planet": index, "slot": slot, "orbit": int(p.orbit),
                    "size": int(p.size), "climate": int(p.climate),
                    "type": int(p.planet_type),
                    "colony": int(p.colony_index)})
    return out


def _local(state):
    raws = getattr(state, "player_raw", None) or []
    n = getattr(state, "player_num", 0)
    return player_struct.parse(raws[n]) if 0 <= n < len(raws) else None


def _contact(state, planets, local):
    raws = getattr(state, "colonies_raw", None) or []
    met = player_struct.contacts(local) if local is not None else []
    me = getattr(state, "player_num", 0)
    for p in planets:
        if 0 <= p["colony"] < len(raws):
            owner = colony_struct.parse(raws[p["colony"]]).owner
            if owner == me or (0 <= owner < len(met) and met[owner]):
                return True
    return False


def system_model(state, ident, box, text, omniscient):
    """(model, None) or (None, reason)."""
    if ident is None or ident.kind != "system":
        return None, "no HD star click to name this window"
    stars = getattr(state, "stars", None) or []
    if not 0 <= ident.star < len(stars):
        return None, f"star {ident.star} is not in the snapshot"
    star = stars[ident.star]
    w, h = _size(box)
    nx, ny = mc.galaxy_to_native(star.x, star.y, state)
    want = popup_xy(0, nx, ny, w, h)
    if want != tuple(box.rect[:2]):
        return None, (f"window at {tuple(box.rect[:2])}, {star.name} would "
                      f"put it at {want}")
    me = getattr(state, "player_num", 0)
    viewable = (not star_struct.is_black_hole(star)
                and (star_struct.visited_by(star, me) or omniscient))
    planets = star_planets(state, star)
    matched = match_planets(box, planets) if viewable else {}
    if matched is None:
        return None, f"the planet fields do not fit {star.name}'s orbits"
    model = {"kind": "system", "star": ident.star, "name": star.name,
             "viewable": viewable, "planets": [],
             "close": box.close.index if box.close is not None else None,
             "body": "", "wormhole": ""}
    if viewable or _contact(state, planets, _local(state)):
        model["title"] = _msg(text, H_SYSTEM, star.name)
    else:
        model["title"] = _msg(text, H_UNEXPLORED)
    if not viewable:
        model["body"] = _msg(text, H_STAR_CLASS + int(star.spectral_class))
        return model, None
    for index, p in sorted(matched.items(), key=lambda kv: kv[1]["orbit"]):
        model["planets"].append(dict(p, field=index))
    far = getattr(star, "wormhole_star_id", -1)
    if far is not None and 0 <= far < len(stars):
        if star_struct.visited_by(stars[far], me):
            model["wormhole"] = _msg(text, H_WORMHOLE, stars[far].name)
        else:
            model["wormhole"] = _msg(text, H_WORMHOLE_UNKNOWN)
    return model, None


def stack_of(ships, lead):
    """SHIPSTAK::Find_Ship_Stacks_ (shipstak.cpp:45-100): status below 3,
    same location, x, y and owner, in array order."""
    key = (lead.location, lead.x, lead.y, lead.owner)
    return [i for i, s in enumerate(ships)
            if s.status < ship_struct.STATUS_STACK_SKIP
            and (s.location, s.x, s.y, s.owner) == key]


def fleet_model(state, ident, box, text):
    """(model, None) or (None, reason)."""
    if ident is None or ident.kind != "fleet":
        return None, "no HD icon click to name this box"
    raws = getattr(state, "ships_raw", None) or []
    if not 0 <= ident.ship < len(raws):
        return None, f"ship {ident.ship} is not in the snapshot"
    ships = [ship_struct.parse(r) for r in raws]
    lead = ships[ident.ship]
    stack = stack_of(ships, lead)
    w, h = _size(box)
    want = fleet_xy(ident.icon[0], ident.icon[1], w, h)
    if want != tuple(box.rect[:2]):
        return None, (f"box at {tuple(box.rect[:2])}, the clicked icon "
                      f"would put it at {want}")
    icon_fields = [f for f in box.fields if f.field_type == 7
                   and f.x_end - f.x == FLEET_ICON_SPAN
                   and f.y_end - f.y == FLEET_ICON_SPAN]
    if len(icon_fields) != min(FLEET_ICONS_MAX, len(stack)):
        return None, (f"{len(icon_fields)} icon fields for a stack of "
                      f"{len(stack)}")
    stars = getattr(state, "stars", None) or []
    first = ships[stack[0]]
    if first.owner < 9:
        local = player_struct.parse(state.player_raw[first.owner]) \
            if first.owner < len(state.player_raw or []) else None
        title = _msg(text, H_FLEET, getattr(local, "race_name", ""))
    else:
        title = str(first.name).upper()
    return {"kind": "fleet", "ship": ident.ship, "stack": stack[:FLEET_ICONS_MAX],
            "owners": [ships[i].owner for i in stack[:FLEET_ICONS_MAX]],
            "title": title, "status": fleet_status(state, first, stars, text),
            "close": box.close.index if box.close is not None else None}, None


def fleet_status(state, ship, stars, text):
    """The status line for the stack's first ship (see the module note)."""
    if ship.status == 0:
        if 0 <= ship.location < len(stars):
            return _msg(text, H_ORBITING, stars[ship.location].name)
        return ""
    dest = ship_struct.absolute_location(ship.location)
    turns = int(ship.turns_left)
    if dest == len(stars):
        return _msg(text, H_ANTARES)
    if not 0 <= dest < len(stars):
        return ""
    if not star_struct.visited_by(stars[dest], getattr(state, "player_num", 0)):
        return _msg(text, H_ETA_TURN if turns == 1 else H_ETA_TURNS, turns)
    return _msg(text, H_TURN if turns == 1 else H_TURNS, turns,
                stars[dest].name)
