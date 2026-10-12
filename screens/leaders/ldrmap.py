"""The Leaders screen's galaxy box and ship grid: which field is under a
point, what HD's pointer is over, and what the two strips say. Work
order 175 B, with open fix 30 applied.

THE FIELDS, as `Add_Officer_Screen_Fields_` builds them and ldrgeom's
transcription left out because they depend on the map and the stack:

  a star        `MOVEBOX::Add_Galaxy_Map_Fields_2_(0x132, 0xEB, 0x13E,
                0xA9, …, field_style 1)` (officer.cpp:2998-3011): one
                hidden field per star, `(sx - 3, sy - 3, sx + 8, sy + 9)`
                (movebox.cpp:504-511) at `Get_Galaxy_Map_Star_XY_`'s
                point — divisors `506000 / w + 1` and `400000 / h + 1`,
                minus 3 (movebox.cpp:365-386)
  a ship stack  `FLT2::Add_Fltscrn_Small_Icon_Fields_` (flt2.cpp:28-44):
                a hidden field whose TOP-LEFT is the icon's own x / y,
                which is on the wire; its extent is the art's, so the live
                field is found by its origin and its rectangle read off it
  a big icon    `Add_Fltscrn_Big_Icon_Fields_` (flt2.cpp:283-323):
                `(x, y, x + 0x39, y + 0x39)` on this screen, for the
                player's own stack only — `ldrgeom.grid_cell`

Each send is the live field with exactly that rectangle (decision 20);
none is guessed. Two stars whose fields overlap under the pointer go to
the one whose centre is nearer — the original resolves overlaps inside
the field scan, which HD does not see; this is HD's rule, stated.

WHAT THE POINTER IS OVER — TRANSCRIPTION, drawn by HD alone. The API has
no mouse motion, so the game's own `_scanned_small_ship`,
`_scanned_big_ship` and `_galaxy_map_scanned_star` stay where the game
left them; HD keeps its own three and applies the loop's rules
(officer.cpp:986-1086): only in mode -1; the small icon first, then the
big icon, then the star, each clearing the others when it finds one; the
big icon is only "scanned" while the pointer is on it, the other two stay
until replaced.

THE STRIPS:

  under the view box  colony view: `_officer_star_displayed` with its
                      leader (officer.cpp:810-826); ship view: the big
                      icon under the pointer, `Print_Scanned_Ship_Name_`
                      (:695-727)
  under the map       the star under the pointer (`Do_Officer_Screen_
                      Stuff_`, movebox.cpp:229-291) or the stack,
                      `Print_Galmap_Scanned_Ship_` (officer.cpp:2094-2204)
"""
from core import hestrings, zoomtables
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct

from . import ldrgeom as geom

MAP_X, MAP_Y, MAP_W, MAP_H = geom.GALAXY_BOX_XYWH
#: `field_style` 1's centre offset and field margins (movebox.cpp:374,
#: :504-511).
STAR_CENTRE = 3
STAR_FIELD = (-3, -3, 8, 9)
#: `Box_Officer_Screen_Chosen_Star_` / `_Scanned_Star_` (movebox.cpp:
#: 410-448): an 11 x 12 box 5 px up and left of the star's point, in
#: colour 0x1E for the displayed star, 0x6E + the flash value for the
#: chosen one, 0x71 for the one under the pointer.
STAR_BOX = (-5, -5, 0x0B, 0x0C)
BOX_DISPLAYED, BOX_CHOSEN, BOX_SCANNED = 0x1E, 0x6E, 0x71

#: HESTRNGS: "%s (%s) %d turn(s)" and the unknown star (movebox.cpp:
#: 276-285, officer.cpp:819-821); "%s Fleet: " and the counts
#: (officer.cpp:2155-2184).
H_ETA_ONE, H_ETA_MANY, H_UNKNOWN = 0x92, 0x93, 0x94
H_FLEET = 0x131
H_OUTPOSTS, H_TRANSPORTS, H_COLONY_SHIPS = (0x102, 0x103), (0x104, 0x105), \
    (0x106, 0x107)
#: `mox.cpp:940`.
STAR_WITH_LEADER = "%s (%s)"
#: `SHIP_NODE_UI_TAG_BASE` (consts.h:28) and the owners past the players.
NODE_TAG_BASE = 10000
MAX_PLAYERS = 8
HULLS = 6                     # SHIP_SIZE_DOOM_STAR + 1 (sys.cpp:864)


def _scale(game_state):
    return zoomtables.max_map_scale(getattr(game_state, "map_max_x", 0),
                                    getattr(game_state, "map_max_y", 0))


def _stars(game_state):
    return getattr(game_state, "stars", None) or []


def star_point(game_state, index):
    """`Get_Galaxy_Map_Star_XY_` for this box and field_style 1, or None."""
    stars, scale = _stars(game_state), _scale(game_state)
    if not scale or not 0 <= index < len(stars):
        return None
    s = stars[index]
    x = (int(s.x) * 1000 // scale * 10) // (506000 // MAP_W + 1)
    y = (int(s.y) * 1000 // scale * 10) // (400000 // MAP_H + 1)
    return (x - STAR_CENTRE + MAP_X, y - STAR_CENTRE + MAP_Y)


def star_field_rect(game_state, index):
    p = star_point(game_state, index)
    if p is None:
        return None
    a, b, c, d = STAR_FIELD
    return (p[0] + a, p[1] + b, p[0] + c, p[1] + d)


def star_box_rect(game_state, index):
    """The box around a star (movebox.cpp:410-433), inclusive."""
    stars, scale = _stars(game_state), _scale(game_state)
    if not scale or not 0 <= index < len(stars):
        return None
    s = stars[index]
    x = MAP_X + (int(s.x) * 1000 // scale * 10) // (506000 // MAP_W)
    y = MAP_Y + (int(s.y) * 1000 // scale * 10) // (400000 // MAP_H)
    dx, dy, w, h = STAR_BOX
    return (x + dx, y + dy, x + dx + w - 1, y + dy + h - 1)


def _inside(point, rect):
    return rect is not None and rect[0] <= point[0] <= rect[2] and \
        rect[1] <= point[1] <= rect[3]


def _field(fields, rect):
    return next((f for f in fields if f.field_type == geom.TYPE_HIDDEN
                 and (f.x, f.y, f.x_end, f.y_end) == tuple(rect)), None)


def star_at(game_state, point):
    """The star whose field holds the native point, nearest centre first."""
    best = None
    for i in range(len(_stars(game_state))):
        r = star_field_rect(game_state, i)
        if not _inside(point, r):
            continue
        d = (point[0] - (r[0] + r[2]) / 2) ** 2 + \
            (point[1] - (r[1] + r[3]) / 2) ** 2
        if best is None or d < best[0]:
            best = (d, i)
    return None if best is None else best[1]


def star_field(game_state, fields, index):
    r = star_field_rect(game_state, index)
    return _field(fields, r) if r is not None else None


def icon_field(fields, icon):
    """A stack icon's live field: hidden, at the icon's own origin."""
    return next((f for f in fields if f.field_type == geom.TYPE_HIDDEN
                 and (f.x, f.y) == (int(icon.x), int(icon.y))), None)


def icon_at(game_state, fields, point):
    """`(icon index, live field)` of the stack icon under the point."""
    for i, icon in enumerate(getattr(game_state, "ship_icons", None) or []):
        if int(icon.x) < 0 or int(icon.y) < 0:
            continue
        f = icon_field(fields, icon)
        if f is not None and _inside(point, (f.x, f.y, f.x_end, f.y_end)):
            return i, f
    return None


def big_icon_at(block, point):
    """`(index into the block's list, grid slot)` under the point."""
    if block is None:
        return None
    ships = block.get("ship_idx") or []
    first = max(0, int(block.get("first_row", 0))) * geom.GRID_COLUMNS
    for slot in range(geom.GRID_COLUMNS * geom.GRID_ROWS):
        if first + slot < len(ships) and _inside(point, geom.grid_cell(slot)):
            return first + slot, slot
    return None


def scan(screen, point):
    """HD's own `_scanned_*` after the pointer moved to `point` (see the
    module docstring). `screen._scan` is ("icon", i) / ("star", i) / None,
    `screen._big` an index into the block's list or None."""
    view = screen._view
    block = view.block if view is not None else None
    if block is None or int(block.get("mode", -1)) != -1 or point is None:
        screen._big = None
        return
    state = screen._state
    hit = icon_at(state, view.fields, point)
    if hit is not None:
        screen._scan = ("icon", hit[0])
    big = big_icon_at(block, point) if view.view == geom.VIEW_SHIP else None
    screen._big = big[0] if big is not None else None
    if big is not None:
        screen._scan = None
    star = star_at(state, point)
    if star is not None:
        screen._scan, screen._big = ("star", star), None


# ── The strips' words ─────────────────────────────────────

def with_leader(name, rec, words):
    """`name`, "%s (%s)" with the leader, or HESTR 0x92 / 0x93 while the
    leader is still on the way (officer.cpp:714-722, :816-822)."""
    if rec is None:
        return name
    eta = int(rec.eta)
    if eta < 1:
        return STAR_WITH_LEADER % (name, rec.name)
    template = words.hstring(H_ETA_ONE if eta == 1 else H_ETA_MANY)
    return hestrings.printf(template, name, rec.name, eta) if template \
        else name


def _leader(leaders, index):
    return leaders[index] if 0 <= int(index) < len(leaders) else None


def displayed_star_words(game_state, view, words, star):
    stars = _stars(game_state)
    if not 0 <= star < len(stars):
        return ""
    slots = list(getattr(stars[star], "officer_index", []) or [])
    me = view.player
    index = slots[me] if 0 <= me < len(slots) else -1
    return with_leader(stars[star].name, _leader(view.leaders, index)
                       if index >= 0 else None, words)


def big_ship_words(game_state, view, words, k):
    """`Print_Scanned_Ship_Name_` (officer.cpp:695-727)."""
    ships = (view.block or {}).get("ship_idx") or []
    raws = getattr(game_state, "ships_raw", None) or []
    if k is None or not 0 <= k < len(ships) or \
            not 0 <= ships[k] < len(raws):
        return ""
    ship = ship_struct.SPEC.parse(raws[ships[k]])
    officer = int(ship.officer_index)
    return with_leader(ship.name, _leader(view.leaders, officer)
                       if officer >= 0 else None, words)


def colony_owners(game_state, star):
    planets = getattr(game_state, "planets_raw", None) or []
    colonies = getattr(game_state, "colonies_raw", None) or []
    for index in star_struct.planet_indices(star):
        if not 0 <= index < len(planets):
            continue
        c = planet_struct.parse(planets[index]).colony_index
        if 0 <= c < len(colonies):
            yield int(colony_struct.parse(colonies[c]).owner)


def scanned_star_words(game_state, view, words, index):
    """`Do_Officer_Screen_Stuff_` (movebox.cpp:257-285): the name with its
    leader where the player has a colony, or HESTR 0x94 for a star the
    player has neither visited, nor sees by omniscience, nor has contact
    with a colony in (`Contact_With_One_Colony_`, harold.cpp:730-748)."""
    stars = _stars(game_state)
    if not 0 <= index < len(stars):
        return ""
    star, me = stars[index], view.player
    raws = getattr(game_state, "player_raw", None) or []
    local = player_struct.parse(raws[me]) if 0 <= me < len(raws) else None
    met = player_struct.contacts(local) if local is not None else []
    owners = list(colony_owners(game_state, star))
    seen = (star_struct.visited_by(star, me)
            or (local is not None and player_struct.has_omniscience(local))
            or any(0 <= o < len(met) and met[o] for o in owners))
    if not seen:
        return words.hstring(H_UNKNOWN) or ""
    slots = list(getattr(star, "officer_index", []) or [])
    officer = slots[me] if 0 <= me < len(slots) else -1
    if officer < 0 or me not in owners:
        return star.name
    return with_leader(star.name, _leader(view.leaders, officer), words)


def stack_ships(game_state, icon):
    """The ship indices of the stack behind a small icon, or None.

    The head ship is the FSEL node table's entry for the icon's node; the
    rest is `SHIPSTAK::Find_Ship_Stacks_`'s own rule — status below 3,
    same location, x, y and owner (shipstak.cpp:45-100) — because the
    nodes' `next_node` is not on the wire. `Remove_Non_Detected_Ships_`
    drops whole stacks (shipstak.cpp:130-135), so a stack that has an
    icon has all its ships."""
    sel = getattr(game_state, "fleet_selection", None)
    node = int(icon.node_idx)
    if not sel or not 0 <= node < len(sel["ships"]):
        return None
    raws = getattr(game_state, "ships_raw", None) or []
    ships = [ship_struct.parse(r) for r in raws]
    head = sel["ships"][node]
    if not 0 <= head < len(ships):
        return None
    h = ships[head]
    key = (h.location, h.x, h.y, h.owner)
    return [i for i, s in enumerate(ships)
            if s.status < ship_struct.STATUS_STACK_SKIP
            and (s.location, s.x, s.y, s.owner) == key]


def fleet_words(game_state, icon, words, parts):
    """`Print_Galmap_Scanned_Ship_`'s paragraph for a player's stack, or
    "" where it prints a race name HD does not have (a tagged node or an
    owner past the players — OMISSION `map_strip_monsters`)."""
    if int(icon.node_idx) >= NODE_TAG_BASE:
        return ""
    stack = stack_ships(game_state, icon)
    raws = getattr(game_state, "ships_raw", None) or []
    if not stack:
        return ""
    ships = [ship_struct.parse(raws[i]) for i in stack]
    owner = int(ships[0].owner)
    players = getattr(game_state, "player_raw", None) or []
    if not 0 <= owner < min(MAX_PLAYERS, len(players)):
        return ""
    fleet = words.hstring(H_FLEET)
    if not fleet:
        return ""
    race = player_struct.parse(players[owner]).race_name
    text = hestrings.printf(fleet, race).upper()
    count = {t: sum(1 for s in ships if s.ship_type == t)
             for t in (ship_struct.SHIP_TYPE_OUTPOST,
                       ship_struct.SHIP_TYPE_TRANSPORT,
                       ship_struct.SHIP_TYPE_COLONY)}
    for t, ids in ((ship_struct.SHIP_TYPE_OUTPOST, H_OUTPOSTS),
                   (ship_struct.SHIP_TYPE_TRANSPORT, H_TRANSPORTS),
                   (ship_struct.SHIP_TYPE_COLONY, H_COLONY_SHIPS)):
        if count[t] > 0:
            part = words.hstring(ids[0] if count[t] == 1 else ids[1])
            text += hestrings.printf(part, count[t]) if part else ""
    hulls = [0] * HULLS
    for s in ships:
        if s.ship_type == ship_struct.SHIP_TYPE_COMBAT:
            hulls[min(max(0, int(s.size)), HULLS - 1)] += 1
    for size, n in enumerate(hulls):
        if n > 0:
            name = parts.name("hulls" if n == 1 else "hull_plurals", size)
            text += f"{n} {name or ''}, "
    return text[:-2] if len(text) > 2 else text
