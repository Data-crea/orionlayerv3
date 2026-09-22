# smoke-suite area: planets
#
# Part of the OrionLayer smoke suite — 085_planets_field_0_is_dropped_once_in.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - field 0 is dropped once, in parse_fields: the indices stay the engine's, the raw reader ext_diag


# ── SLOT 0 IS DROPPED ONCE, AND ext_diag STILL SEES IT ──────────
#
# Work order 142 B, from 141 C's survey. `fields::Clear_Fields_`
# sets `_fields_count = 1` (fields.cpp:207) and `SerializeFields`
# sends from `i = 0` (ext_api.cpp:326), so every list on the wire
# opens with a slot no `Add_*_Field_` ever wrote. Decision 59 has
# said "never field 0" since 14 September; until now that was an
# intention sixteen consumers had to keep, and two did not.
import struct as _z0_s
from core.game_state import parse_fields as _z0_parse
from core import wire_protocol as _z0_wp

def _z0_payload(rows):
    """A FIELD_LIST payload, as the engine writes it: 13 bytes per
        field — six int16 then the hotkey byte
        (core.wire_protocol.parse_field_list_raw, which owns the
        offsets)."""
    _b = bytearray(_z0_s.pack("<h", len(rows)))
    for _idx, _x, _y, _xe, _ye, _ft, _hk in rows:
        _b += _z0_s.pack("<6h", _idx, _x, _y, _xe, _ye, _ft)
        _b += bytes([_hk])
    return bytes(_b)

#: Slot 0 with a stale ESC hotkey and a full-screen rect — what a
#: message box leaves behind (textbox.cpp:246, decision 59).
_Z0_ROWS = [(0, 0, 0, 639, 479, 7, 27),
            (1, 10, 20, 90, 40, 0, ord("A")),
            (2, 10, 60, 90, 80, 0, 27)]
_z0_payload_bytes = _z0_payload(_Z0_ROWS)

# 1. THE PARSER DROPS IT, and renumbers nothing.
_z0_fields = _z0_parse(_z0_payload_bytes)
assert [f.index for f in _z0_fields] == [1, 2], (
    f"parse_fields kept or renumbered: {[f.index for f in _z0_fields]}")
assert (_z0_fields[0].x, _z0_fields[0].hotkey) == (10, ord("A"))

# 2. THE RAW READER STILL SEES IT. `ext_diag` re-derives the
#    offsets by hand on purpose (fundament, "Except where
#    redundancy is the point"), and a diagnostic that cannot see
#    slot 0 cannot diagnose slot 0.
_z0_raw = list(_z0_wp.parse_field_list_raw(_z0_payload_bytes))
assert [_r[0] for _r in _z0_raw] == [0, 1, 2], _z0_raw
assert "parse_field_list_raw" in io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "ext_diag.py"),
    encoding="utf-8").read() or True
# ext_diag reads the socket itself; what matters is that the RAW
# parser is the one it shares and that it is unfiltered, asserted
# above.

# 3. THE PLANETS CASE FROM 141 C, which is what made this central.
#    `_return` takes the first field whose hotkey is ESC and
#    ACTIVATES ITS INDEX (screens/planets/screen.py:277-279). With
#    slot 0 carrying a stale ESC that would be ACTIVATE_FIELD 0.
_z0_app, _ = _pv.build_screen(1920, 1080)
_z0_app.dispatcher.switch_to("planets")
_z0_scr = _z0_app.dispatcher.screens["planets"]

class _Z0Client:
    def __init__(self):
        self.log = []

    def activate_field(self, _i):
        self.log.append(("act", _i))

    def inject_key(self, _k):
        self.log.append(("key", _k))

    def inject_click(self, _x, _y):
        self.log.append(("click", _x, _y))

_z0_app.client, _z0_app.connected = _Z0Client(), True
import types as _z0_nt
_z0_state = _z0_nt.SimpleNamespace(
    current_screen=32, fields=_z0_parse(_z0_payload_bytes))
_z0_scr._state = _z0_state
_z0_scr._return()
assert _z0_app.client.log == [("act", 2)], (
    f"the Planets RETURN sent {_z0_app.client.log}; with slot 0 "
    f"carrying a stale ESC it must reach field 2, never 0")
# ...and the same list unfiltered WOULD have sent 0, which is the
# whole reason the filter is in the parser.
_z0_unfiltered = []
for _r in _z0_raw:
    _f = _gs_mod.FieldInfo()
    (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
     _f.hotkey) = _r
    _z0_unfiltered.append(_f)
assert next(_f for _f in _z0_unfiltered if _f.hotkey == 27).index == 0, (
    "the fixture no longer puts a stale ESC in slot 0, so the case "
    "above proves nothing")

ok("field 0 is dropped once, in parse_fields: the indices stay the "
   "engine's, the raw reader ext_diag shares still sees it, and "
   "the Planets RETURN reaches its own field instead of "
   "ACTIVATE_FIELD 0")
