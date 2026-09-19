"""The grid's cells and the ship panel's lines, from the wire.

What reaches here has already been validated by `fltwire.View`: this
module turns ship indices into things to draw and nothing else. It makes
no decision about whether the screen may draw at all.

**THE CELLS CARRY THE SHIP'S OWN PICTURE — THE OMISSION IS LIFTED**
(work order 142 D1). It used to read "SHIPS.LBX is MOO2's artwork,
which is never in this tree, so a cell shows a name and a colour".
The artwork is still never in this tree and never will be (decisions
40 and 42); what changed is that this stopped being the same statement
as "HD cannot draw it". `tools/fleet_art_extract.py` reads the
player's OWN installation and `screens/fleets/fltart.py` decodes it at
load time (decision 38), so the cell draws
`SHIPS.LBX ship_type + colour * 50` — `KEN::Do_Get_Ship_Picture_Seg`,
ken.cpp:451-466 — whenever the player has extracted it.

WITHOUT those files, which is the state of every fresh clone, the cell
falls back to the NAME and the builder's colour exactly as before, and
the screen says how to get them. That fallback is not documentation:
the smoke test forces both states.

**THE DAMAGE BAR IS AN OMISSION FOR A DIFFERENT REASON.**
`FLEETPOP::Draw_Damage_Bars_` (fleetpop.cpp:41-81) reads
`structural_damage` and `armor_damage`, which `core/structs/ship.py`
does NOT carry: they are hand-counted offsets 125 and 123 that no second
source has confirmed (decision 23), and the reading marks them
UNVERIFIED. A bar drawn from an unverified offset is a bar that can be
wrong without looking wrong. The bar's own geometry is unsettled too —
`Draw_Fltscrn_Big_Ship_Icons_` passes width 1 on this screen
(flt1.cpp:56-59, :110), which `Draw_Damage_Bars_` turns into an
effective width of -3.

**THE ATTACK AND DEFENSE BONUSES ARE AN OMISSION** because
`INITSHIP::Get_Ship_Combat_Bonuses_` (initship.cpp:638-687) needs
officer skills from `s_leader_data` (unverified), the crew fields at
113-116 (unverified), `strategic_combat_flag` (not in
`core/structs/settings.py`), tech applications and
`_td_combat_speed_bonus` — five inputs, three of them unverified and one
undecoded.

What IS here is what the verified spec carries: the name, the location,
the shield, the weapon list and the specials.
"""
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct

#: `Do_Get_Ship_Picture_Seg`'s set for an owner that is not a player
#: (ken.cpp:459-462, MAX_PLAYERS is 8 at consts.h:7).
MONSTER_SET = 8


class Cell:
    """One big-icon cell: what the grid draws in slot `slot`."""

    def __init__(self, slot, ship_idx, selected, view, sprite_set=None,
                 ramp=None):
        self.slot = slot
        self.ship_idx = ship_idx
        self.selected = selected
        self.view = view                      # parsed s_ship_data, or None
        self.name = getattr(view, "name", "") if view else ""
        # THE COLOUR IS THE BUILDER'S, NOT THE OWNER'S. The original
        # picks the picture by `previous_owner` (ken.cpp:451-466), which
        # is who BUILT the hull — a captured ship keeps the colours it
        # was built in. Transcribed, including for a cell that has no
        # picture to show: the marker beside the name follows the same
        # rule, so a captured ship reads the same way it does in the
        # original.
        self.builder = (getattr(view, "previous_owner", None)
                        if view else None)
        self.owner = getattr(view, "owner", None) if view else None
        # WHICH PICTURE, AND WHICH COLOURS — two different owners, and
        # they were read as one until work order 142 D1. `picture_num`
        # (offset 92) picks the hull; `sprite_set` is the BUILDER's
        # colour and selects the artwork set (ken.cpp:453, :466);
        # `ramp` is the CURRENT owner's colour and selects the palette
        # the screen installs over 192..239 (flt1.cpp:561). A captured
        # ship therefore keeps its old hull in its new colours.
        self.picture = getattr(view, "picture_num", None) if view else None
        self.sprite_set = sprite_set
        self.ramp = ramp


def player_colour(game_state, index):
    """`_player[index].color`, or None when there is no such player.

    The indirection the original makes at ken.cpp:459-462 and that
    this screen made nowhere: a player INDEX is not a colour, and the
    two coincide often enough in a fresh game to hide the difference.

    **A DELIBERATE DIVERGENCE, MARKED.** The original tests
    `player_idx < MAX_PLAYERS` on a value it has already sign-extended
    (ken.cpp:453), so `previous_owner` 0xFF reaches `_player[-1]` and
    reads whatever is in front of the table. None comes back here
    instead and the caller falls to the monster set. Reproducing an
    out-of-bounds read is not transcription.
    """
    raws = getattr(game_state, "player_raw", None) or []
    if index is None or not 0 <= int(index) < len(raws):
        return None
    try:
        return int(player_struct.parse(raws[int(index)]).color)
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def cells(fleet_view, game_state):
    """The `Cell` list for the displayed rows, in display order."""
    raws = getattr(game_state, "ships_raw", None) or []
    out = []
    for slot, ship_idx, selected in fleet_view.rows:
        view = None
        if 0 <= ship_idx < len(raws):
            raw = raws[ship_idx]
            if len(raw) >= ship_struct.SIZE:
                view = ship_struct.parse(raw)
        built = player_colour(game_state,
                              getattr(view, "previous_owner", None))
        held = player_colour(game_state, getattr(view, "owner", None))
        out.append(Cell(slot, ship_idx, selected, view,
                        sprite_set=MONSTER_SET if built is None else built,
                        ramp=MONSTER_SET if held is None else held))
    return out


def panel_lines(ship_idx, game_state, parts):
    """The ship panel's lines for one ship, as (label, value) pairs.

    `FLT2::Print_Scanned_Ship_Data_` (flt2.cpp:524-747) in the order it
    prints, minus what this screen omits (see the module docstring).
    Empty when nothing is scanned, which is the original's state too:
    it prints on HOVER only (flt1.cpp:401-407).
    """
    raws = getattr(game_state, "ships_raw", None) or []
    if not (0 <= ship_idx < len(raws)):
        return []
    raw = raws[ship_idx]
    if len(raw) < ship_struct.SIZE:
        return []
    view = ship_struct.parse(raw)
    lines = [("", view.name)]

    where = _location(view, game_state)
    if where:
        lines.append(("Location", where))

    shield = parts.name("shields", view.shield_type) if parts else None
    if shield:
        lines.append(("Shields", shield))

    # "n Name" per weapon. THE LIST STOPS AT THE FIRST EMPTY SLOT on
    # this screen — `no_weapons` breaks the loop (flt2.cpp:696-701) —
    # which is NOT what `ship.weapons()` does: it skips empty slots and
    # keeps going. Transcribed here rather than changed there, because
    # the fleet box reads the same helper and this screen's break is a
    # property of this screen's printer.
    for slot in ship_struct.weapons(view):
        count = int(getattr(slot, "count", 0) or 0)
        if count <= 0:
            break
        label = (parts.name("weapons", slot.type) if parts else None) \
            or f"#{slot.type}"
        lines.append(("", f"{count} {label}"))

    for bit in ship_struct.special_bits(view):
        label = parts.name("specials", bit) if parts else None
        if label:
            lines.append(("", label))
    return lines


def _location(view, game_state):
    """The star the ship is at, or "" — `s_ship.location` through
    `absolute_location` (flt2.cpp:645-677)."""
    stars = getattr(game_state, "stars", None) or []
    idx = ship_struct.absolute_location(int(view.location))
    if idx is None or not (0 <= idx < len(stars)):
        return ""
    return getattr(stars[idx], "name", "") or ""


def star_name(game_state, star_idx):
    """One star's name, or ""."""
    stars = getattr(game_state, "stars", None) or []
    if not (0 <= star_idx < len(stars)):
        return ""
    return getattr(stars[star_idx], "name", "") or ""


def is_black_hole(game_state, star_idx):
    stars = getattr(game_state, "stars", None) or []
    if not (0 <= star_idx < len(stars)):
        return False
    return star_struct.is_black_hole(stars[star_idx])
