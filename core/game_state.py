"""
Parsed game state from orion2re Extension API.

Entpackt die binären Struct-Arrays in Python-Objekte.
Struct-Größen kommen aus orion2re sizes.h.
"""
import struct
from core import wire_protocol
from core.structs import star as star_struct
from core.structs import ship_icon as ship_icon_struct
from dataclasses import dataclass, field
from typing import Optional


# Struct sizes (from sizes.h, 64-bit build with MAX_STARS=1024)
SETTINGS_SIZE = 0x229       # 553
PLAYER_SIZE = 0xF0E         # 3854
STAR_SIZE = 0x6A + (1024 + 7) // 8  # 234 (with BITMAP(MAX_STARS))
SHIP_SIZE = 0x81            # 129
COLONY_SIZE = 0x169         # 361
PLANET_SIZE = 0x12          # 18
NEBULA_SIZE = 0x05          # 5
LEADER_SIZE = 0x3B          # 59
ANTARAN_SIZE = 0x42         # 66
SHIP_ICON_SIZE = 12
MAX_PLAYERS = 8
MAX_LEADERS = 67


@dataclass
class FieldInfo:
    index: int = 0
    x: int = 0
    y: int = 0
    x_end: int = 0
    y_end: int = 0
    field_type: int = 0
    hotkey: int = 0


@dataclass
class GameState:
    """Kompletter Spielzustand aus einem STATE_SNAPSHOT."""

    # Game Identity
    current_screen: int = -1
    previous_screen: int = -1
    stardate: int = 0
    player_num: int = 0
    num_players: int = 0
    num_stars: int = 0
    num_ships: int = 0
    num_colonies: int = 0
    num_nebulas: int = 0
    game_type: int = 0

    # Map state
    map_scale: int = 0
    map_x: int = 0
    map_y: int = 0
    map_max_x: int = 0
    map_max_y: int = 0

    # Parsed data
    settings_raw: bytes = b""
    player_raw: list = field(default_factory=list)
    stars: list = field(default_factory=list)
    ships_raw: list = field(default_factory=list)
    colonies_raw: list = field(default_factory=list)
    planets_raw: list = field(default_factory=list)
    nebulas_raw: list = field(default_factory=list)
    leaders_raw: list = field(default_factory=list)
    antaran_raw: bytes = b""
    ship_icons: list = field(default_factory=list)
    #: Open fix 20's FSEL block: {"stack": int, "ships": [ship_idx per
    #: node], "selected": [bool per node], "chain": [node, in the fleet
    #: box's cell order]}, or None on an engine without revision 2.
    fleet_selection: Optional[dict] = None
    #: Open fix 27's FLTS block — the fleet SCREEN's view state, which
    #: is a different thing from `fleet_selection` and comes from a
    #: different array. None unless screen 4 is up on a patched engine;
    #: `screens/fleets/fltwire.py` names every key and says why each one
    #: could not be reconstructed.
    fleet_screen: Optional[dict] = None
    #: Open fix 30's OFFS block — the Leaders screen's view state
    #: (`doc/ext_officer_screen_state.patch`, NOT APPLIED as of work
    #: order 167). None on every engine that exists today and on every
    #: screen but 29; `screens/leaders/ldrwire.py` names every key and
    #: what the screen does without it.
    officer_screen: Optional[dict] = None

    # Fields (from FIELD_LIST message)
    fields: list = field(default_factory=list)

    # Save slot list (MSG_SAVE_SLOTS, doc/ext_save_slots.patch). None
    # means the engine did not send one with the current field list —
    # not in a Load/Save dialog, or an engine without the patch.
    save_slots: Optional[list] = None

    # Visual (from VISUAL_FRAME message)
    framebuffer: Optional[bytes] = None
    palette: Optional[list] = None

    # Settings shortcuts (from MOX::_settings, only valid after Accept)
    difficulty: int = 0
    galaxy_size: int = 0
    galaxy_age: int = 0

    # Newgame screen local settings (from NEWGAME:: variables, live)
    ng_difficulty: int = 0
    ng_galaxy_size: int = 0
    ng_galaxy_age: int = 0
    ng_opponents: int = 0        # actual players = value + 2
    ng_tactical_combat: int = 0  # 0=tactical, 1=strategic (inverted)
    ng_tech_level: int = 0
    ng_random_events: int = 0
    ng_antarans: int = 0

    @property
    def stardate_str(self):
        """Stardate als lesbarer String (z.B. '350.1')."""
        return f"{self.stardate // 10}.{self.stardate % 10}"


def parse_state(data: bytes) -> GameState:
    """Parst einen STATE_SNAPSHOT Payload in ein GameState-Objekt."""
    gs = GameState()
    pos = 0

    def read_i16():
        nonlocal pos
        v = struct.unpack_from('<h', data, pos)[0]
        pos += 2
        return v

    def read_u8():
        nonlocal pos
        v = data[pos]
        pos += 1
        return v

    def read_i8():
        nonlocal pos
        v = struct.unpack_from('<b', data, pos)[0]
        pos += 1
        return v

    def read_i32():
        nonlocal pos
        v = struct.unpack_from('<i', data, pos)[0]
        pos += 4
        return v

    def read_bytes(n):
        nonlocal pos
        v = data[pos:pos + n]
        pos += n
        return v

    # Game Identity
    gs.current_screen = read_i16()
    gs.previous_screen = read_i8()
    gs.stardate = read_i32()
    gs.player_num = read_i16()
    gs.num_players = read_i16()
    gs.num_stars = read_i16()
    gs.num_ships = read_i16()
    gs.num_colonies = read_i16()
    gs.num_nebulas = read_u8()
    gs.game_type = read_i8()

    # Map state
    gs.map_scale = read_i16()
    gs.map_x = read_i16()
    gs.map_y = read_i16()
    gs.map_max_x = read_i16()
    gs.map_max_y = read_i16()

    # Settings
    gs.settings_raw = read_bytes(SETTINGS_SIZE)
    # Shortcuts: difficulty at offset 0xD4, galaxy_size at 0xD6
    gs.difficulty = gs.settings_raw[0xD4]
    gs.galaxy_size = gs.settings_raw[0xD6]
    gs.galaxy_age = gs.settings_raw[0xD7]

    # Players
    gs.player_raw = []
    for i in range(MAX_PLAYERS):
        gs.player_raw.append(read_bytes(PLAYER_SIZE))

    # Stars (verified spec: core/structs/star.py)
    n_stars = read_i16()
    star_raws = [read_bytes(STAR_SIZE) for _ in range(n_stars)]
    gs.stars = star_struct.parse_all(star_raws)

    # Ships
    n_ships = read_i16()
    gs.ships_raw = []
    for i in range(n_ships):
        gs.ships_raw.append(read_bytes(SHIP_SIZE))

    # Colonies
    n_colonies = read_i16()
    gs.colonies_raw = []
    for i in range(n_colonies):
        gs.colonies_raw.append(read_bytes(COLONY_SIZE))

    # Planets
    n_planets = read_i16()
    gs.planets_raw = []
    for i in range(n_planets):
        gs.planets_raw.append(read_bytes(PLANET_SIZE))

    # Nebulas
    n_nebulas = read_u8()
    gs.nebulas_raw = []
    for i in range(n_nebulas):
        gs.nebulas_raw.append(read_bytes(NEBULA_SIZE))

    # Leaders
    gs.leaders_raw = []
    for i in range(MAX_LEADERS):
        gs.leaders_raw.append(read_bytes(LEADER_SIZE))

    # Antarans
    gs.antaran_raw = read_bytes(ANTARAN_SIZE)

    # Ship icons (verified spec: core/structs/ship_icon.py)
    n_icons = read_i16()
    icon_raws = [read_bytes(SHIP_ICON_SIZE) for _ in range(n_icons)]
    gs.ship_icons = ship_icon_struct.parse_all(icon_raws)

    # Newgame screen local settings (8 × int16, appended by ext_api)
    if pos + 16 <= len(data):
        gs.ng_difficulty = read_i16()
        gs.ng_galaxy_size = read_i16()
        gs.ng_galaxy_age = read_i16()
        gs.ng_opponents = read_i16()
        gs.ng_tactical_combat = read_i16()
        gs.ng_tech_level = read_i16()
        gs.ng_random_events = read_i16()
        gs.ng_antarans = read_i16()

    # Ship icon owners — OPTIONAL trailing block, one uint8 per icon,
    # 0xFF meaning "no ship behind this icon".
    #
    # s_ship_icon itself carries no owner: the C++ resolves it via
    # node_idx -> MOX::_ship_node[] -> MOX::_ship[].owner, and
    # _ship_node is not serialized. doc/ext_ship_icon_owner.patch
    # appends this block; without it every icon stays owner=None and
    # screens/galaxy_map/ships.py falls back to inferring the owner
    # from the ships parked at the star.
    #
    # Deliberately LAST in the snapshot so an unpatched orion2re and a
    # patched one both parse — never insert a field above this line
    # without moving it.
    if n_icons and pos + n_icons <= len(data):
        for icon in gs.ship_icons:
            owner = read_u8()
            icon.set_derived("owner", None if owner == 0xFF else owner)

    # Ship node table and fleet box selection — OPTIONAL block after the
    # owners, open fix 20 revision 2 (doc/ext_fleet_selection.patch):
    # "FSEL", int16 the stack the fleet box shows (-1 while closed), int16
    # N nodes, N x (int16 _ship_node[i].ship_idx, uint8 selected), int16 L,
    # L x int16 node — the box's chain in the order its cells are built.
    # The table is read, never rebuilt: Sort_Ships_In_Stack_ rewrites
    # ship_idx inside every chain (brief 119). Absent on an unpatched
    # engine and short on a revision-1 one (one byte per node, no chain):
    # then `fleet_selection` stays None — a state, not an error.
    gs.fleet_selection = None
    if data[pos:pos + 4] == b"FSEL" and pos + 8 <= len(data):
        pos += 4
        stack = read_i16()
        nodes = read_i16()
        if 0 <= nodes and pos + 3 * nodes + 2 <= len(data):
            ships, selected = [], []
            for _ in range(nodes):
                ships.append(read_i16())
                selected.append(read_u8() != 0)
            length = read_i16()
            if 0 <= length and pos + 2 * length <= len(data):
                chain = [read_i16() for _ in range(length)]
                if all(0 <= n < nodes for n in chain) \
                        and (stack >= 0 or not chain):
                    gs.fleet_selection = {"stack": stack, "ships": ships,
                                          "selected": selected,
                                          "chain": chain}

    # The fleet SCREEN's view state — OPTIONAL block after FSEL, open
    # fix 27 (doc/ext_fleet_screen_state.patch). Written by the engine
    # only while screen 4 is up, so its ABSENCE is three different
    # states and the screen has to tell them apart itself: another
    # screen, an unpatched engine, or a truncated block. All three land
    # on None here, and `screens/fleets/fltwire.py` turns None into a
    # named refusal rather than an empty grid.
    #
    # Fourteen scalars, then N x (int16 ship_idx, uint8 selected) in the
    # screen's DISPLAY order. Read whole or not at all: a short block is
    # None, never a half-filled dict, because a half-filled one would
    # draw a grid that is missing its last ships without saying so.
    gs.fleet_screen = None
    if data[pos:pos + 4] == b"FLTS" and pos + 4 + 26 + 2 <= len(data):
        pos += 4
        _flt = {}
        for _key in ("stack", "head_node", "owner", "icons", "icons_added",
                     "rows", "first_row", "selected_count", "scanned_big",
                     "scanned_small", "support_filter", "combat_filter"):
            _flt[_key] = read_i16()
        _flt["relocate_mode"] = read_u8()
        _flt["merging_relocations"] = read_u8() != 0
        _n = read_i16()
        if 0 <= _n == _flt["icons"] and pos + 3 * _n <= len(data):
            _ships, _sel = [], []
            for _ in range(_n):
                _ships.append(read_i16())
                _sel.append(read_u8() != 0)
            _flt["ship_idx"] = _ships
            _flt["ship_selected"] = _sel
            gs.fleet_screen = _flt

    # The Leaders screen's view state — OPTIONAL block after FSEL, open
    # fix 30 (doc/ext_officer_screen_state.patch). Written only while
    # screen 29 is up, so it never meets FLTS. Four int8, sixteen int16,
    # a count, then N x (int16 ship_idx, uint8 selected). Read whole or
    # not at all, for FLTS's reason: a half-read block would draw a grid
    # missing its last ships without saying so.
    gs.officer_screen = None
    if data[pos:pos + 4] == b"OFFS" and pos + 4 + 4 + 32 + 2 <= len(data):
        pos += 4
        _off = {}
        for _key in ("view", "mode", "selected", "scanned"):
            _off[_key] = read_i8()
        for _key in ("star_displayed", "star_chosen", "n_officers"):
            _off[_key] = read_i16()
        _off["id_list"] = [read_i16() for _ in range(4)]
        for _key in ("stack", "head_node", "first_row", "picked_icon",
                     "scanned_big", "scanned_small", "scanned_star",
                     "popup_leader", "popup_state"):
            _off[_key] = read_i16()
        _n = read_i16()
        if 0 <= _n and pos + 3 * _n <= len(data):
            _ships, _sel = [], []
            for _ in range(_n):
                _ships.append(read_i16())
                _sel.append(read_u8() != 0)
            _off["ship_idx"] = _ships
            _off["ship_selected"] = _sel
            gs.officer_screen = _off

    return gs


def parse_fields(data: bytes) -> list:
    """Parst einen FIELD_LIST Payload in eine Liste von FieldInfo.

    Byte layout lives in core.wire_protocol.parse_field_list_raw
    (single source, also used by the standalone ext_diag* tools).

    **SLOT 0 IS DROPPED HERE, ONCE.** `fields::Clear_Fields_` sets
    `_fields_count = 1`, not 0 (fields.cpp:207), so slot 0 is never
    cleared and no `Add_*_Field_` ever writes it — while
    `SerializeFields` sends every field from `i = 0`
    (ext_api.cpp:326). Nothing in the engine sets the count to 0, so a
    real field can never land there.

    Decision 59 has said "never field 0" since 14 September 2026, and
    until work order 142 B that was an INTENTION every consumer had to
    keep on its own — sixteen of them, of which two did not: the
    Planets screen's `_send_available` asked the whole list for a
    hotkey, and its `_return` took the first ESC field and ACTIVATED
    ITS INDEX, so a stale hotkey in slot 0 would have sent
    `ACTIVATE_FIELD 0`. Work order 141 A had already paid for the same
    shape on the Fleets screen. "A labelling rule without a check is
    an intention, and it decays": dropping it once makes it a property
    instead.

    **THE INDICES STAY THE ENGINE'S.** `FieldInfo.index` carries the
    array index `ACTIVATE_FIELD` sends; leaving the entry out
    renumbers nothing.

    The per-consumer filters stay where they are. They cost nothing,
    they document the rule where a reader meets it, and one of them —
    `injection._signature` — legitimately wants to see the whole list.
    `tools/ext_diag.py` builds its own list straight from the bytes,
    deliberately redundant, and still sees slot 0.
    """
    fields = []
    for idx, x, y, xe, ye, ft, hk in wire_protocol.parse_field_list_raw(data):
        if idx == 0:
            continue
        f = FieldInfo()
        f.index, f.x, f.y = idx, x, y
        f.x_end, f.y_end = xe, ye
        f.field_type, f.hotkey = ft, hk
        fields.append(f)
    return fields


def parse_visual(data: bytes):
    """Parst einen VISUAL_FRAME Payload in Framebuffer + Palette."""
    fb_size = 640 * 480
    framebuffer = data[:fb_size]
    palette = []
    pos = fb_size
    for i in range(256):
        r = data[pos]; pos += 1
        g = data[pos]; pos += 1
        b = data[pos]; pos += 1
        palette.append((r, g, b))
    return framebuffer, palette
