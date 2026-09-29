"""The multiplayer steps on the wire — open fix 51, "MPLY" (work order 188).

`doc/ext_multiplayer_state.patch`: written LAST (after HOFM) on any screen
while a multiplayer step's guard has set its phase. 'M''P''L''Y', uint8
version 1, uint8 phase, then the phase's payload — strings as uint8 length
+ raw bytes ("s8"), an input as int16 field id, uint8 max length, s8 the
field's buffer, uint8 editing, and s8 the typed text only while editing
("IN"); an absent field is -1000.

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

PHASES = {1: "setup", 2: "online", 3: "game_name", 4: "load_list",
          5: "hotseat", 6: "hotseat_switch", 7: "host_init",
          8: "host_wait", 9: "host_race_info", 10: "host_send",
          11: "host_pick", 12: "host_load_wait", 13: "join_init",
          14: "join_list", 15: "join_wait", 16: "join_map",
          17: "join_pick", 18: "join_get", 19: "net_turn"}
NONE = -1000


class _Reader:
    def __init__(self, data, pos):
        self.data, self.pos = data, pos

    def take(self, fmt):
        size = _st.calcsize("<" + fmt)
        if self.pos + size > len(self.data):
            raise ValueError("short")
        vals = _st.unpack_from("<" + fmt, self.data, self.pos)
        self.pos += size
        return vals if len(vals) > 1 else vals[0]

    def s8(self):
        n = self.take("B")
        if self.pos + n > len(self.data):
            raise ValueError("short")
        raw = self.data[self.pos:self.pos + n]
        self.pos += n
        return raw.decode("latin-1")

    def inp(self):
        field, limit = self.take("hB")
        buf = self.s8()
        editing = self.take("B")
        typed = self.s8() if editing else None
        return {"field": field, "max": limit, "text": buf,
                "editing": bool(editing), "typed": typed}


def _payload(r, phase):
    p = {}
    if phase == "setup":
        p["type"], p["game_type"], p["net_mode"] = r.take("BBB")
        p["fields"] = dict(zip(("network", "online", "hotseat", "cancel",
                                "start", "load", "join", "setup"),
                               r.take("8h")))
        p["endpoint"], p["game_name"] = r.s8(), r.s8()
    elif phase == "online":
        p["input"] = r.inp()
        p["ok"], p["cancel"] = r.take("hh")
    elif phase == "game_name":
        p["input"] = r.inp()
        p["cancel"] = r.take("h")
        p["prompt"] = r.s8()
    elif phase == "load_list":
        p["game_type"], p["cancel"], n = r.take("BhB")
        p["slots"] = []
        for _ in range(n):
            field, valid = r.take("hB")
            p["slots"].append({"field": field, "valid": bool(valid),
                               "description": r.s8(), "stardate": r.s8(),
                               "date": r.s8()})
    elif phase == "hotseat":
        p["players"], humans, p["join"], p["accept"], p["cancel"] = \
            r.take("bhhhh")
        p["humans"] = []
        for _ in range(max(0, humans)):
            race, colour = r.take("BB")
            p["humans"].append({"race": race, "colour": colour,
                                "name": r.s8(), "race_name": r.s8()})
    elif phase in ("hotseat_switch",):
        n = r.take("B")
        p["players"] = [dict(zip(("status", "row", "banner"), r.take("Bhh")))
                        for _ in range(n)]
    elif phase in ("host_init", "join_init", "join_wait"):
        p["net_mode"] = r.take("B")
        p["endpoint"], p["game_name"] = r.s8(), r.s8()
    elif phase in ("host_wait", "host_load_wait"):
        p["begin"], p["users"], p["players"] = r.take("hhb")
        p["game_name"] = r.s8()
        if phase == "host_load_wait":
            p["needed"], p["joining"] = r.take("bi")
    elif phase == "host_race_info":
        p["with_race"], p["users"], p["connected"] = r.take("hhb")
    elif phase in ("host_send", "join_get"):
        p["status"] = r.s8()
    elif phase in ("host_pick", "join_pick"):
        p["begin"], n = r.take("hB")
        p["players"] = [dict(zip(("shown", "taken", "row", "banner"),
                                 r.take("BBhh"))) for _ in range(n)]
    elif phase == "join_list":
        p["cancel"], n = r.take("hB")
        p["games"] = []
        for _ in range(n):
            field, cur, most, is_open = r.take("hhhB")
            p["games"].append({"field": field, "players": cur, "max": most,
                               "open": bool(is_open), "name": r.s8()})
    elif phase == "net_turn":
        p["chat"] = r.inp()
        p["c_field"] = r.take("h")
        n = r.take("B")
        p["humans"] = [dict(zip(("player", "done"), r.take("BB")))
                       for _ in range(n)]
        n = r.take("B")
        p["lines"] = []
        for _ in range(n):
            sender = r.take("B")
            p["lines"].append({"sender": sender, "text": r.s8()})
    return p


def parse(gs, data, pos):
    """Read MPLY at `pos` into `gs.multiplayer` (None when absent or short).
    Returns the new position."""
    gs.multiplayer = None
    if data[pos:pos + 4] != b"MPLY":
        return pos
    r = _Reader(data, pos + 4)
    try:
        version, code = r.take("BB")
        if version != 1 or code not in PHASES:
            return pos
        phase = PHASES[code]
        body = _payload(r, phase)
    except (ValueError, _st.error):
        return pos
    gs.multiplayer = {"phase": phase, **body}
    return r.pos


def claims(game_state):
    """A multiplayer step HD draws: MPLY on the wire (any id it runs under)."""
    return getattr(game_state, "multiplayer", None) is not None


def endpoint(game_state):
    """The Online endpoint as the engine holds it (MPLY), or None."""
    mp = getattr(game_state, "multiplayer", None) or {}
    if mp.get("phase") == "online":
        inp = mp["input"]
        return (inp["typed"] if inp["editing"] and inp["typed"] is not None
                else inp["text"]).rstrip("_")
    return mp.get("endpoint")


def endpoint_max(game_state):
    """What HD lets the player type: ONE LESS than the input's max — the
    engine's commit copies max + 1 bytes into its 30-byte endpoint
    (multplay.cpp; open fix 51's reading, finding 2), so a full-length
    endpoint would overrun it."""
    mp = getattr(game_state, "multiplayer", None) or {}
    return max(1, mp["input"]["max"] - 1) if mp.get("phase") == "online" \
        else None
