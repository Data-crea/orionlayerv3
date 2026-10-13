"""Ship stacks on a small galaxy map: drawn, found under the pointer, and
named — one implementation for every screen whose map shows them (work
order 248, F1 of 245: Fleets takes them over from Leaders, no copy).

  drawn   `Draw_Fltscrn_Small_Ship_Icons_` (flt1.cpp:216-235): the last
          icon first, each at `s_ship_icon.x/y`, which the screen's own
          `Set_Fltscrn_Small_Ship_Icon_XYs_` has put in its box's space on
          entry (Fleets flt1.cpp:531, Leaders officer.cpp:905); a player's
          stack in its colour's picture, a monster's in its own (picture
          `8 + owner - 8`). Each screen hands in its own pictures (Fleets:
          FLEET.LBX 19-33, flt1.cpp:1265-1290; Leaders: OFFICER.LBX
          0x73-0x81, officer.cpp:2765-2793) and its own native-to-window
          placement.
  found   `Add_Fltscrn_Small_Icon_Fields_` (flt2.cpp:28-44): a hidden field
          whose top-left is the icon's x / y; its extent is the art's, so
          the live field is found by its origin and its rectangle read
          off it (decision 20).
  named   `Print_Galmap_Scanned_Ship_` (officer.cpp:2094-2204), which the
          Fleets screen prints for `_scanned_small_ship` too (flt1.cpp:
          439-441): "<RACE> FLEET: " and the counts.
"""
from core import hestrings
from core.structs import player as player_struct
from core.structs import ship as ship_struct

#: The hidden field type (`fields.h`), as `ldrgeom` and `fltwire` name it.
TYPE_HIDDEN = 7
#: HESTRNGS "%s Fleet: " and the counts (officer.cpp:2155-2184).
H_FLEET = 0x131
H_OUTPOSTS, H_TRANSPORTS, H_COLONY_SHIPS = (0x102, 0x103), (0x104, 0x105), \
    (0x106, 0x107)
#: `SHIP_NODE_UI_TAG_BASE` (consts.h:28) and the owners past the players.
NODE_TAG_BASE = 10000
MAX_PLAYERS = 8
#: The first monster owner, and the monster pictures after the eight
#: player colours.
MONSTER_FIRST = 8
MONSTERS = 7
HULLS = 6                     # SHIP_SIZE_DOOM_STAR + 1 (sys.cpp:864)


def _inside(point, rect):
    return rect is not None and rect[0] <= point[0] <= rect[2] and \
        rect[1] <= point[1] <= rect[3]


def colour_of(game_state, owner):
    """A player's banner colour, from its record, or None."""
    raws = getattr(game_state, "player_raw", None) or []
    if 0 <= owner < len(raws):
        return int(player_struct.SPEC.parse(raws[owner]).color)
    return None


def picture_index(game_state, icon):
    """The stack picture's number: the owner's colour 0-7 for a player,
    `8 + owner - 8` for a monster (flt1.cpp:221-231), or None."""
    owner = getattr(icon, "owner", None)
    if owner is None:
        return None
    owner = int(owner)
    if owner < MAX_PLAYERS:
        return colour_of(game_state, owner)
    if 0 <= owner - MONSTER_FIRST < MONSTERS:
        return MAX_PLAYERS + owner - MONSTER_FIRST
    return None


def draw_stacks(surface, game_state, picture, place, fallback):
    """Every placed stack, the last icon first. `picture(n)` is the
    screen's picture n (already at window size) or None, `place(x, y)` its
    native-to-window point, `fallback(point, icon)` draws a stack without
    its picture. Answers `[(icon index, icon, window point, picture)]`."""
    icons = list(getattr(game_state, "ship_icons", None) or [])
    drawn = []
    for i in range(len(icons) - 1, -1, -1):
        icon = icons[i]
        x, y = int(icon.x), int(icon.y)
        if x < 0 or y < 0:
            continue                    # the -1 sentinel: not placed
        n = picture_index(game_state, icon)
        sprite = picture(n) if n is not None else None
        at = place(x, y)
        if sprite is not None:
            surface.blit(sprite, at)
        else:
            fallback(at, icon)
        drawn.append((i, icon, at, sprite))
    return drawn


def icon_field(fields, icon):
    """A stack icon's live field: hidden, at the icon's own origin."""
    return next((f for f in fields if f.field_type == TYPE_HIDDEN
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


def fleet_words(game_state, icon, hstring, parts):
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
    fleet = hstring(H_FLEET)
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
            part = hstring(ids[0] if count[t] == 1 else ids[1])
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
