"""The grid's cells and the ship panel's lines, from the wire.

What reaches here has already been validated by `fltwire.View`: this
module turns ship indices into things to draw and nothing else. It makes
no decision about whether the screen may draw at all.

**THE CELLS CARRY NO SHIP PICTURE, AND THAT IS AN OMISSION, NOT A GAP
NOBODY NOTICED.** The original draws `SHIPS.LBX picture_num + 50 *
colour` (`KEN::Get_Ship_Id_Picture_Seg_`, ken.cpp:451-466) — MOO2's
artwork, which is never in this tree (CLAUDE.md). HD has the small map
marker, which is derived artwork it may ship (decision 42), and no big
design picture at all. A cell therefore shows the ship's NAME, its
owner's colour and whether it is selected. Marked in `layout.json`
`marks`, in the module docstring of `screen.py`, and in
`doc/briefs/134-parked-for-data.md`.

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
from core.structs import ship as ship_struct
from core.structs import star as star_struct


class Cell:
    """One big-icon cell: what the grid draws in slot `slot`."""

    def __init__(self, slot, ship_idx, selected, view):
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
        out.append(Cell(slot, ship_idx, selected, view))
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
