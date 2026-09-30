"""The tactical battle in the snapshot — open fixes 52-57 (work order 194).

WIRE ONLY: no screen reads these yet — work order 194 built the wire, the
combat screen comes later. Every block is written by the engine only while
its state is live and is read here WHOLE or not at all (`core/colonyblocks.py`'s
rule): a short or unknown block leaves its attribute None and the chain
position where it was.

    52  no block: a battle reports 65, its scan view 66, its board popup 67
        (`core.screen_names`); the gate the blocks below are written under
        (`ext::g_combat_live`) and the battle's serial number.
    "CMBT"  53  the battle's state: turn, sides, the acting unit, the view
            origin, the turn order, every unit field by field (the packed
            `s_combat_data` without its picture pointer, 309 bytes), and the
            acting unit's legal moves as a bitmap over the 81 x 68 grid.
    "CMSL"  55  the ordnance in flight: each live `s_missile` (26 bytes) with
            its index (`gs.ordnance`).
    "CRES"  57  how the last battle ended, kept until the next one starts.
    "CTGT"  54  the engine's verdict of what each weapon slot of the acting
            unit can hit now, per unit and per missile.

ONE SNAPSHOT IS ONE MOMENT: its blocks describe the battle after every event
the engine recorded before it (open fix 56 drains them into the same
snapshot). A client that animates may show such a state, or a result, only
after it has played every event before it — Data's condition of 30
September 2026 for letting the engine run ahead of HD's animations.
"""
import struct as _st

GRID_W, GRID_H = 81, 68
#: `s_combat_data` as CMBT writes it: the packed struct's bytes before
#: `ship_image_seg` (0..197) and after it (206..316) — 309 bytes; the
#: engine asserts both offsets and the size (ext_api.cpp, open fix 53).
UNIT_SIZE = 309
#: (name, offset in the 309-byte record, format) — orion2.h:595-658; after
#: the pointer every offset is the struct's minus 8.
UNIT_FIELDS = (
    ("ship_idx", 30, "h"), ("owner", 32, "b"), ("x", 33, "b"),
    ("y", 34, "b"), ("facing_dir", 35, "b"), ("unit_status", 36, "b"),
    ("size_class", 37, "b"), ("shield_type", 38, "b"),
    ("shield_arc_max", 39, "h"), ("shield_arc_current", 41, "4h"),
    ("ftl_type", 49, "b"), ("computer_type", 50, "b"),
    ("armor_type", 51, "b"), ("tac_val_attack", 52, "h"),
    ("tac_val_defense", 54, "h"), ("tac_val_evade", 56, "h"),
    ("combat_speed_base", 58, "b"), ("current_speed", 59, "h"),
    ("movement_left", 61, "h"), ("special_status_flag", 64, "b"),
    ("special_status_timer", 65, "B"), ("combat_status_flags", 72, "B"),
    ("stasis_source_idx", 74, "B"), ("is_retreating", 75, "b"),
    ("structure_max", 170, "h"), ("crew_quality", 172, "b"),
    ("officer_idx", 173, "h"), ("marine_count", 175, "B"),
    ("is_captured", 176, "b"), ("weapon_ready_flags", 184, "8B"),
    ("structure_damage", 192, "h"), ("armor_remaining", 194, "h"),
    ("picture_num", 196, "h"),
    ("drive_max_hits", 198, "h"), ("computer_max_hits", 200, "h"),
    ("shield_max_hits", 250, "h"), ("drive_current_hits", 252, "h"),
    ("computer_current_hits", 254, "h"), ("shield_current_hits", 304, "h"),
    ("black_hole_flag", 306, "b"), ("black_hole_source_idx", 307, "B"),
    ("previous_owner", 308, "B"),
)
#: `s_combat_weapon_slot` x 8 at 82, 11 bytes each (sizes.h asserts 11).
WEAPON_OFFSET, WEAPON_SIZE = 82, 11
WEAPON_FORMAT = "<hbbHhbbB"
CMBT_HEAD = "<BHhhhhhhhhhhhhhhh"   # version .. super_fast_flag
CMBT_HEAD_SIZE = _st.calcsize(CMBT_HEAD)


def unit(raw):
    """One CMBT unit record as a dict; `name` is the engine's (game text)."""
    out = {"name": raw[:30].split(b"\0", 1)[0].decode("latin-1")}
    for name, at, fmt in UNIT_FIELDS:
        vals = _st.unpack_from("<" + fmt, raw, at)
        out[name] = list(vals) if len(vals) > 1 else vals[0]
    out["weapons"] = []
    for k in range(8):
        (wid, count, arc, specials, ammo, active, shots,
         status) = _st.unpack_from(WEAPON_FORMAT, raw,
                                   WEAPON_OFFSET + k * WEAPON_SIZE)
        out["weapons"].append({"weapon_id": wid, "count": count, "arc": arc,
                               "specials": specials, "ammo": ammo,
                               "active": active, "shots_left": shots,
                               "status": status})
    return out


def legal(bits, x, y):
    """True when CMBT's legal-move bitmap marks cell (x, y) (x-major)."""
    i = x * GRID_H + y
    return bool(bits[i >> 3] >> (i & 7) & 1)


def _cmbt(data, pos):
    at = pos + 4
    head = _st.unpack_from(CMBT_HEAD, data, at)
    at += CMBT_HEAD_SIZE
    if head[0] != 1:
        return None, pos
    keys = ("serial", "turn", "attacker", "defender", "initiative",
            "auto_attacker", "auto_defender", "cur_ship", "cur_ptr",
            "view_x", "view_y", "in_nebula", "colony", "scan_flag",
            "board_flag", "super_fast")
    out = dict(zip(keys, head[1:]))
    (n_order,) = _st.unpack_from("<B", data, at)
    at += 1
    out["turn_order"] = list(_st.unpack_from(f"<{n_order}h", data, at))
    at += 2 * n_order
    size, units = _st.unpack_from("<Hh", data, at)
    at += 4
    if size != UNIT_SIZE or not 0 <= units <= 210:
        return None, pos
    out["units"] = []
    for _ in range(units):
        rec = data[at:at + UNIT_SIZE]
        if len(rec) != UNIT_SIZE:
            return None, pos
        out["units"].append(unit(rec))
        at += UNIT_SIZE
    nbytes = (GRID_W * GRID_H + 7) // 8
    bits = data[at:at + nbytes]
    if len(bits) != nbytes:
        return None, pos
    out["legal"] = bytes(bits)
    return out, at + nbytes


#: `s_missile` (orion2.h:1249-1266), 0x1A bytes — sizes.h asserts it.
MISSILE_SIZE = 26
MISSILE_FIELDS = (("type", "h"), ("owner", "h"), ("source_unit_idx", "h"),
                  ("target_unit_idx", "h"), ("is_anti_missile_rocket", "b"),
                  ("x", "h"), ("y", "h"), ("hits_taken", "h"),
                  ("quantity", "h"), ("specials", "H"), ("travel_dist", "h"),
                  ("facing_dir", "b"), ("speed", "B"), ("fighter_count", "b"),
                  ("pad", "b"), ("is_active", "b"))
MISSILE_FORMAT = "<" + "".join(f for _n, f in MISSILE_FIELDS)
assert _st.calcsize(MISSILE_FORMAT) == MISSILE_SIZE


def _cmsl(data, pos):
    """CMSL: version, serial, the record size, n, n x (int16 index, the
    live `s_missile` — type above 0)."""
    version, serial, size, n = _st.unpack_from("<BHBh", data, pos + 4)
    at = pos + 10
    if version != 1 or size != MISSILE_SIZE or not 0 <= n <= 300 or \
            at + n * (2 + size) > len(data):
        return None, pos
    missiles = []
    for _ in range(n):
        (index,) = _st.unpack_from("<h", data, at)
        vals = _st.unpack_from(MISSILE_FORMAT, data, at + 2)
        m = dict(zip((k for k, _f in MISSILE_FIELDS), vals))
        m["index"] = index
        missiles.append(m)
        at += 2 + size
    return {"serial": serial, "missiles": missiles}, at


def build_cmsl(missiles, serial=1):
    """CMSL as the engine writes it — for the checks' stand-ins."""
    out = b"CMSL" + _st.pack("<BHBh", 1, serial, MISSILE_SIZE, len(missiles))
    for m in missiles:
        out += _st.pack("<h", m["index"])
        out += _st.pack(MISSILE_FORMAT, *(int(m.get(k, 0))
                                          for k, _f in MISSILE_FIELDS))
    return out


#: tag -> (reader, the GameState attribute); the ENGINE's order, which is
#: the order the blocks are read in.
PARSERS = {"CMBT": (_cmbt, "combat"), "CMSL": (_cmsl, "ordnance")}


def cut(data, at, tag):
    """The bytes of the `tag` block at `at`, or None when it does not read
    whole — for the fixture cutter (`tools/combat_fixture.py`)."""
    reader, _attr = PARSERS[tag]
    try:
        value, end = reader(data, at)
    except (_st.error, IndexError):
        return None
    return None if value is None else bytes(data[at:end])


def weight(tag, block):
    """How much a recorded block shows, to keep the richest one."""
    value, _end = PARSERS[tag][0](block, 0)
    if tag == "CMBT":
        return len(value["units"])
    if tag == "CMSL":
        return len(value["missiles"])
    return len(block)


def parse(gs, data, pos):
    """Read the combat blocks at `pos`, in the engine's order, each into its
    attribute (`gs.combat` for CMBT) — None when absent or short, and a
    short block leaves `pos` where it was. Returns the new position."""
    for tag, (reader, attr) in PARSERS.items():
        setattr(gs, attr, None)
        if data[pos:pos + 4] != tag.encode():
            continue
        try:
            value, end = reader(data, pos)
        except (_st.error, IndexError):
            value = None
        if value is not None:
            setattr(gs, attr, value)
            pos = end
    return pos
