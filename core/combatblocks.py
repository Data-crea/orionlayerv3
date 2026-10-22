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
    "CRES"  57  how the last battle ended, kept until the next one starts
            (`gs.combat_result`), on any screen.
    "CTGT"  54  the engine's verdict of what each weapon slot of the acting
            unit can hit now, per unit and per missile (`gs.targets`).
    "CMEV"  56  what happened since the last snapshot, numbered: shots with
            their damage, moves, turns, launches, hits, deaths, retreats,
            boarding (`gs.combat_events`, `EVENTS`) — written on ANY screen
            while events are unsent, so a battle's last events arrive with
            the first snapshot after it.

ONE SNAPSHOT IS ONE MOMENT: its blocks describe the battle after every event
the engine recorded before it (open fix 56 drains them into the same
snapshot). A client that animates may show such a state, or a result, only
after it has played every event before it — Data's condition of 30
September 2026 for letting the engine run ahead of HD's animations.
"""
import struct as _st

from core import wire_protocol
from core.blockreader import Reader
from core.structs import combat as combat_struct

GRID_W, GRID_H = 81, 68
#: `s_combat_data` as CMBT writes it: the struct without its picture pointer
#: (`core/structs/combat.py` holds the record and follows the engine's
#: layout; 309 bytes on the old engine, which asserts both cut offsets and
#: the size, ext_api.cpp, open fix 53).
UNIT_SIZE = combat_struct.UNIT_SPEC.size
CMBT_HEAD = "<BHhhhhhhhhhhhhhhh"   # version .. super_fast_flag
CMBT_HEAD_SIZE = _st.calcsize(CMBT_HEAD)


def unit(raw):
    """One CMBT unit record as a dict; `name` is the engine's (game text)."""
    # the unit's stored name (work order 208 A6) — the spec's str field
    out = combat_struct.record(combat_struct.UNIT_SPEC, raw)
    out["weapons"] = combat_struct.weapon_slots(raw)
    return out


def legal(bits, x, y):
    """True when CMBT's legal-move bitmap marks cell (x, y) (x-major)."""
    i = x * GRID_H + y
    return bool(bits[i >> 3] >> (i & 7) & 1)


def acting_index(combat):
    """The index of the unit that acts, or None while none does.

    TRANSCRIPTION (work order 324): the engine sets `cur_ship = -1` at
    the end of a side's turn and at the end of the combat
    (combat1.cpp:418, :1862) and every one of its own readers asks first
    — the drawing of the cursor box and the hover block
    (cmbtdrw1.cpp:713 `cur_ship >= 0`), the status of the acting unit
    (:608 `!= -1`), the legal boxes and the internals (:532, :568
    `> -1`), the side wait (combat1.cpp:1659, :1985) and the serializer
    (ext_api.cpp:2117). A bare `units[cur_ship]` takes -1 for the LAST
    unit, so no HD site indexes with it: each asks here.
    """
    if not combat:
        return None
    cur, units = combat.get("cur_ship", -1), combat.get("units") or ()
    return cur if 0 <= cur < len(units) else None


def acting_unit(combat):
    """The acting unit (`acting_index`), None while none acts."""
    cur = acting_index(combat)
    return None if cur is None else combat["units"][cur]


def _cmbt(data, pos):
    r = Reader(data, pos + 4)
    head = r.take(CMBT_HEAD)
    if head[0] != 1:
        wire_protocol.refused("CMBT", f"version {head[0]}")
        return None, pos
    keys = ("serial", "turn", "attacker", "defender", "initiative",
            "auto_attacker", "auto_defender", "cur_ship", "cur_ptr",
            "view_x", "view_y", "in_nebula", "colony", "scan_flag",
            "board_flag", "super_fast")
    out = dict(zip(keys, head[1:]))
    n_order = r.one("B")
    out["turn_order"] = list(r.take(f"{n_order}h"))
    size, units = r.take("Hh")
    if size != combat_struct.UNIT_SPEC.resolved()[0] or not 0 <= units <= 210:
        wire_protocol.refused("CMBT", "unit record size or count",
                              f"record {size}, {units} units")
        return None, pos
    if out["cur_ship"] >= units:
        # -1 is the engine's own "no ship acts" (combat1.cpp:418, :1862)
        # and passes — the screen asks `acting_unit`, never the list with
        # it (work order 324) — and so does a block of no unit at all (the
        # engine writes CMBT whenever a battle is live, also while it sets
        # up or ends, ext_api.cpp), which refusing would cost every block
        # after it. A value past the end would raise in every frame that
        # follows.
        wire_protocol.refused("CMBT", "acting unit past the end",
                              f"{units} units, acting {out['cur_ship']}")
        return None, pos
    out["units"] = []
    for _ in range(units):
        out["units"].append(unit(r.raw(size)))
    out["legal"] = bytes(r.raw((GRID_W * GRID_H + 7) // 8))
    return out, r.pos


#: `s_missile`, whole: `core/structs/combat.py` (it follows the layout).
MISSILE_SIZE = combat_struct.MISSILE_SPEC.size


def _cmsl(data, pos):
    """CMSL: version, serial, the record size, n, n x (int16 index, the
    live `s_missile` — type above 0)."""
    r = Reader(data, pos + 4)
    version, serial, size, n = r.take("BHBh")
    want = combat_struct.MISSILE_SPEC.resolved()[0]
    if version != 1 or size != want or not 0 <= n <= 300 or \
            not r.fits(n * (2 + size)):
        return None, pos
    missiles = []
    for _ in range(n):
        index = r.one("h")
        m = combat_struct.record(combat_struct.MISSILE_SPEC, r.raw(size))
        m["index"] = index
        missiles.append(m)
    return {"serial": serial, "missiles": missiles}, r.pos


CRES_HEAD = "<BHHBhhhhhhhih"
CRES_UNIT = "<hbBbbbhhh"
CRES_UNIT_SIZE = _st.calcsize(CRES_UNIT)


def _cres(data, pos):
    """CRES: how the last battle ended — kept by the engine until the next
    battle starts, so a client tells results apart by `number`."""
    r = Reader(data, pos + 4)
    head = r.take(CRES_HEAD)
    (version, number, serial, fought, winner, turn, star, colony, attacker,
     defender, pop_lost, stardate, units) = head
    if version != 1 or not 0 <= units <= 210 or \
            not r.fits(units * CRES_UNIT_SIZE):
        return None, pos
    out = {"number": number, "serial": serial, "fought": bool(fought),
           # 1 attacker, -1 defender (also after the 50-turn timeout: `turn`
           # above 50), 666 both gone (combat1.cpp: Check_For_Winner_)
           "winner": winner, "turn": turn, "star": star, "colony": colony,
           "attacker": attacker, "defender": defender,
           "colony_pop_lost": pop_lost, "stardate": stardate, "units": []}
    keys = ("ship_idx", "owner", "previous_owner", "unit_status",
            "is_retreating", "is_captured", "structure_damage",
            "armor_remaining", "structure_max")
    for _ in range(units):
        out["units"].append(dict(zip(keys, r.take(CRES_UNIT))))
    return out, r.pos


def _ctgt(data, pos):
    """CTGT: the engine's verdict for the ACTING unit — per unit and per live
    missile one byte, bit k = weapon slot k can hit it now (arc, ammunition,
    range, legality: what Fire_Ship_ tests; not whether the player has the
    slot switched on, which CMBT's `active` says)."""
    r = Reader(data, pos + 4)
    version, serial, source, units = r.take("BHhh")
    if version != 1 or not 0 <= units <= 210 or not r.fits(units + 2):
        return None, pos
    masks = list(r.raw(units))
    n = r.one("h")
    if not 0 <= n <= 300 or not r.fits(3 * n):
        return None, pos
    missiles = {}
    for _ in range(n):
        index, mask = r.take("hB")
        missiles[index] = mask
    return {"serial": serial, "unit": source, "units": masks,
            "missiles": missiles}, r.pos


#: The event kinds (ext_api.h, `CombatEventType`) and what their eight
#: int16 arguments are, in order — the engine's own values at the hook.
EVENTS = {
    1: ("beam_shot", ("source", "target", "at_missile", "slot", "weapon",
                      "result", "past_shields", "absorbed")),
    2: ("reflect", ("reflector", "shooter", "past_shields", "absorbed")),
    3: ("bomb", ("source", "target", "slot", "weapon", "hits")),
    4: ("special", ("source", "target", "at_missile", "slot", "weapon")),
    5: ("missile_launch", ("missile", "source", "target", "anti_missile",
                           "slot", "type", "quantity", "speed")),
    6: ("missile_merge", ("missile", "into", "quantity")),
    7: ("missile_hit", ("missile", "source", "target", "type", "quantity",
                        "past_shields", "absorbed", "anti_missile")),
    8: ("fighter_pass", ("missile", "source", "target", "type", "passes_left",
                         "past_shields", "absorbed")),
    9: ("missile_gone", ("missile", "type", "quantity", "x", "y")),
    10: ("move", ("unit", "from_x", "from_y", "to_x", "to_y", "cost",
                  "teleport")),
    11: ("rotate", ("unit", "from_facing", "to_facing", "step")),
    12: ("destroy", ("unit", "death_state", "status_before", "owner",
                     "previous_owner", "x_px", "y_px")),
    13: ("retreat", ("unit", "x", "y", "owner", "status")),
    # the blast's own kind is `blast`: an argument named "kind" overwrote
    # the event's kind in `_cmev` (work order 197's pulsar, seen as "1")
    14: ("blast_hit", ("source", "unit", "blast", "past_shields", "absorbed")),
    15: ("web_damage", ("unit", "past_shields", "absorbed")),
    16: ("capture", ("attacker", "defender", "result", "marines",
                     "defenders_left", "owner_after")),
    17: ("raid", ("attacker", "target", "sent", "back", "defenders_left",
                  "damage")),
    # open fix 58: a command taken (result 0) or refused, and why
    18: ("command", ("op", "result", "a", "b")),
    # open fix 79: a battle sound HD plays, and a change of one (1 fade,
    # 2 loop, 3 pitch; handle -1 every sound), each with the engine's 55 ms
    # ticks since the event before it
    19: ("sound", ("sound", "handle", "ticks")),
    20: ("sound_change", ("handle", "change", "value", "ticks")),
    # open fix 77: what a fighter pass draws — the owner's fighter beam, the
    # group's place (px), facing and quantity, the point it fires at (px)
    21: ("fighter_beam", ("missile", "beam", "x", "y", "facing", "quantity",
                          "target_x", "target_y")),
    # open fix 82: the points a FIRE's entry is drawn between (world px) —
    # its last fire point and the target point with the original's own miss
    # offset (beams.cpp:1381-1459), one per entry as the loop starts it
    22: ("beam_aim", ("source", "target", "weapon", "fire_points", "from_x",
                      "from_y", "to_x", "to_y")),
    # open fix 83: the sixteenths of a turn the gyro destabilizer spins its
    # target after the line — the engine's random draw (cmbtspec.cpp:566-575)
    23: ("gyro_spin", ("source", "target", "turns")),
    # open fix 94 (work order 259): the Energy Absorber's charge
    # (`reflected_damage_pool`) after a hit charged it, or 0 after its
    # discharge emptied it or the engine did after its side's units had
    # acted (work order 260), and the change
    24: ("absorb", ("unit", "pool", "change")),
    # open fix 95 (work order 266): the Stellar Converter's two totals after
    # its four hits — the numbers the original shows over the target
    # (cmbtspec.cpp:1060-1084), named as every other hit's pair
    25: ("converter_hit", ("source", "target", "past_shields", "absorbed")),
}
#: MSG_COMBAT_COMMAND's ops (ext_api.h, `CombatCommandOp`), open fix 58.
COMMANDS = {"move": 1, "fire": 2, "fire_missile": 3, "face": 4,
            "select": 5, "remove_stasis": 6, "board": 7}
#: Why the engine refused one (CEV_COMMAND's result).
REFUSALS = {1: "stale: another battle or unit", 2: "no orders now",
            3: "not a legal cell", 4: "not a valid target",
            5: "board or scan mode", 6: "a weapon mask in a network game",
            7: "board mode refused", 8: "no field for that missile",
            9: "unknown op",
            # open fix 65: a move longer than the original's view (less a
            # ship's margin) — the view the engine centres on the action
            10: "longer than the original's view"}
EVENT_FORMAT = "<HB8h"
EVENT_SIZE = _st.calcsize(EVENT_FORMAT)


def _cmev(data, pos):
    """CMEV: the events recorded since the last snapshot, numbered from
    `first` — a first above the client's next number is a GAP (the ring
    holds 1024, or no client was connected). An unknown kind is kept by its
    number: a newer engine's event must not end the stream."""
    r = Reader(data, pos + 4)
    version, first, n = r.take("BIH")
    if version != 1 or not r.fits(n * EVENT_SIZE):
        return None, pos
    events = []
    for k in range(n):
        serial, kind, *args = r.take(EVENT_FORMAT)
        name, keys = EVENTS.get(kind, (f"kind_{kind}", ()))
        ev = {"seq": first + k, "serial": serial, "kind": name}
        ev.update({key: args[i] for i, key in enumerate(keys)})
        events.append(ev)
    return {"first": first, "events": events}, r.pos


def build_cmsl(missiles, serial=1):
    """CMSL as the engine writes it — for the checks' stand-ins."""
    out = b"CMSL" + _st.pack("<BHBh", 1, serial, MISSILE_SIZE, len(missiles))
    for m in missiles:
        out += _st.pack("<h", m["index"])
        out += combat_struct.MISSILE_SPEC.pack(
            {k: int(m.get(k, 0)) for k, _o, _f in
             combat_struct.MISSILE_SPEC.fields})
    return out


#: tag -> (reader, the GameState attribute); the ENGINE's order, which is
#: the order the blocks are read in.
PARSERS = {"CMBT": (_cmbt, "combat"), "CMSL": (_cmsl, "ordnance"),
           "CRES": (_cres, "combat_result"), "CTGT": (_ctgt, "targets"),
           "CMEV": (_cmev, "combat_events")}


def parse_events_after(gs, data, pos):
    """CMEV where the engine writes it when FBSC is present: after FBSC
    (ext_api.cpp's sections 23, 24). Read only when `parse` found none."""
    if getattr(gs, "combat_events", None) is None and \
            data[pos:pos + 4] == b"CMEV":
        try:
            value, end = _cmev(data, pos)
        except (_st.error, IndexError, ValueError):
            return pos
        if value is not None:
            gs.combat_events = value
            return end
    return pos


def cut(data, at, tag):
    """The bytes of the `tag` block at `at`, or None when it does not read
    whole — for the fixture cutter (`dev:tools/combat_fixture.py`)."""
    reader, _attr = PARSERS[tag]
    try:
        value, end = reader(data, at)
    except (_st.error, IndexError, ValueError):
        return None
    return None if value is None else bytes(data[at:end])


def weight(tag, block):
    """How much a recorded block shows, to keep the richest one."""
    value, _end = PARSERS[tag][0](block, 0)
    if tag == "CMBT":
        return len(value["units"])
    if tag == "CMSL":
        return len(value["missiles"])
    if tag == "CRES":
        return len(value["units"])
    if tag == "CTGT":
        return sum(bin(m).count("1") for m in value["units"])
    if tag == "CMEV":
        return len(value["events"])
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
        except (_st.error, IndexError, ValueError):
            value = None
        if value is not None:
            setattr(gs, attr, value)
            pos = end
    return pos
