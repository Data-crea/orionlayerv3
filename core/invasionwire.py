"""The invasion's TPOP tails — open fix 91 (work order 232 C).

Kind 10 (id 68) is the colony combat popup — `MAINPUPS::Colony_Combat_Popup_`,
the invasion choice (mode 0) and the bombing (mode 1); kind 11 (id 69) is
the ground combat, `COLGCBT::Colony_Combat_Screen_`. Their sixteen numbers
are TPOP's args (`core.turnpopupwire`); what does not fit them follows the
block's common part, as `doc/ext_invasion.patch`'s table in ext_api.cpp
writes it, byte for byte:

  kind 10   4 x int16 the attacker's unit counts, 4 x int16 the defender's
            (as the popup shows them), 8 x int16 the fields close, invade,
            bomb, destroy, mind control, drop all, cease fire, bomb (mode
            1) — -1000 when not added; then the frame's explosions
  kind 11   per side (attacker, defender) 4 x (int16 count, hits, combat),
            uint8 n lines, per line int16 length + the label raw, int16 the
            value; then the frame as the ground combat last drew it: uint16
            frames, uint8 n units (int8 side, uint8 state, int8 type, int8
            frame, int16 x, y), uint8 n beams (int8 side, int16 x1, y1, x2,
            y2, 10 x int16 colour), then the explosions
  explosions  uint8 n, each uint8 picture (1 the ground explosion, 2 a bomb,
            3 a biological bomb, 0 another), int16 frame, x, y
"""
import struct as _st

from core import lang

#: kind 10's fields, in the order the tail writes them (`_mp_fields` 6,
#: 12-18, mainpups.cpp:2813-2935).
POPUP_FIELDS = ("close", "invade", "bomb", "destroy", "mind_control",
                "drop_all", "cease_fire", "bomb_hits")
UNIT_COUNT = 4
#: An explosion's picture by the number the engine writes.
FLICS = {1: "ground", 2: "bomb", 3: "bio", 0: "other"}


def read_tail(kind, take):
    """The tail of kind `kind` ("colony_combat" or "ground_combat"), read
    with `take(fmt)` (TPOP's reader, which raises ValueError when short)."""
    def flics():
        (n,) = take("B")
        out = []
        for _ in range(n):
            pic, frame, x, y = take("Bhhh")
            out.append({"picture": FLICS.get(pic, "other"), "frame": frame,
                        "x": x, "y": y})
        return out

    if kind == "colony_combat":
        attacker = list(take(f"{UNIT_COUNT}h"))
        defender = list(take(f"{UNIT_COUNT}h"))
        fields = dict(zip(POPUP_FIELDS, take(f"{len(POPUP_FIELDS)}h")))
        return {"attacker_counts": attacker, "defender_counts": defender,
                "fields": fields, "flics": flics()}
    sides = []
    for _side in range(2):
        troops = [dict(zip(("count", "hits", "combat"), take("hhh")))
                  for _ in range(UNIT_COUNT)]
        (n,) = take("B")
        lines = []
        for _ in range(n):
            (length,) = take("h")
            if length < 0:
                raise ValueError("length")
            (raw,) = take(f"{length}s")
            (value,) = take("h")
            lines.append({"label": lang.wire_text(raw), "value": value})
        sides.append({"troops": troops, "lines": lines})
    (frames,) = take("H")
    (n,) = take("B")
    units = [dict(zip(("side", "state", "type", "frame", "x", "y"),
                      take("bBbbhh"))) for _ in range(n)]
    (n,) = take("B")
    beams = []
    for _ in range(n):
        side, x1, y1, x2, y2 = take("bhhhh")
        beams.append({"side": side, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                      "colour": list(take("10h"))})
    return {"sides": sides, "frames": frames, "units": units, "beams": beams,
            "flics": flics()}


def build_tail(kind, data):
    """The tail as the engine writes it — for the checks' stand-ins."""
    data = data or {}

    def flics():
        rows = data.get("flics") or []
        code = {v: k for k, v in FLICS.items()}
        out = _st.pack("<B", len(rows))
        for f in rows:
            out += _st.pack("<Bhhh", code.get(f.get("picture"), 0),
                            f.get("frame", 0), f.get("x", 0), f.get("y", 0))
        return out

    if kind == "colony_combat":
        att = (list(data.get("attacker_counts") or []) + [0] * 4)[:4]
        dfn = (list(data.get("defender_counts") or []) + [0] * 4)[:4]
        fields = data.get("fields") or {}
        out = _st.pack("<4h", *att) + _st.pack("<4h", *dfn)
        out += _st.pack(f"<{len(POPUP_FIELDS)}h",
                        *(fields.get(k, -1000) for k in POPUP_FIELDS))
        return out + flics()
    out = b""
    sides = (list(data.get("sides") or []) + [{}, {}])[:2]
    for side in sides:
        troops = (list(side.get("troops") or []) + [{}] * 4)[:4]
        for t in troops:
            out += _st.pack("<hhh", t.get("count", 0), t.get("hits", 0),
                            t.get("combat", 0))
        lines = side.get("lines") or []
        out += _st.pack("<B", len(lines))
        for line in lines:
            raw = line["label"].encode("latin-1")
            out += _st.pack("<h", len(raw)) + raw
            out += _st.pack("<h", line.get("value", 0))
    units = data.get("units") or []
    out += _st.pack("<HB", data.get("frames", 0), len(units))
    for u in units:
        out += _st.pack("<bBbbhh", u["side"], u["state"], u["type"],
                        u["frame"], u["x"], u["y"])
    beams = data.get("beams") or []
    out += _st.pack("<B", len(beams))
    for b in beams:
        out += _st.pack("<bhhhh", b["side"], b["x1"], b["y1"], b["x2"],
                        b["y2"])
        out += _st.pack("<10h", *(list(b.get("colour") or []) + [0] * 10)[:10])
    return out + flics()
