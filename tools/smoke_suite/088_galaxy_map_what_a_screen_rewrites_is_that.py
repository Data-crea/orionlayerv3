# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 088_galaxy_map_what_a_screen_rewrites_is_that.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - what a screen rewrites is that screen's: come from screen 0 only — real bytes through parse_stat
#   - the galaxy map sends nothing while the game is not on screen 0 (decision 33), and still sends at


# ── WHAT A SCREEN REWRITES IS THAT SCREEN'S, NOT THE MAP'S ──────
#
# Work orders 135 B and 136 B, from question 15 of
# doc/fleet_screen_reading.md. The Fleets screen writes wire state it
# does not own — FLT::Set_Fltscrn_Small_Ship_Icon_XYs_ puts every
# s_ship_icon.x/y into fleet-inset space (flt.cpp:54-55) and sets
# _cur_map_scale = _max_map_scale (flt.cpp:14), and
# FLT2::Add_Fltscrn_Small_Icon_Fields_ puts a FIELD ID into stack_id
# (flt2.cpp:34). The Officers screen does both again at its own inset
# (officer.cpp:905, :857/:1191). All of it is serialized like any
# other frame (ext_api.cpp:111, :165-167).
#
# THE RULE IS WHAT IS ASSERTED, NOT THE FIELDS. This iterates
# ships.GATED_FIELDS, so a field added to the gate is covered here
# without a line being written, and a field REMOVED from the gate
# stops being covered loudly rather than quietly. The state goes in
# as BYTES through core.game_state.parse_state, so what the screen is
# offered is a snapshot that really carries another screen's numbers.
import struct as _ig_s
import colony_list_preview as _ig_plv
from screens.galaxy_map import ships as _ig_ships
from core.game_state import (parse_state as _ig_parse,
                             SETTINGS_SIZE as _IG_SET,
                             PLAYER_SIZE as _IG_PL,
                             LEADER_SIZE as _IG_LD,
                             ANTARAN_SIZE as _IG_AN)

# Every gated field must name where the engine writes it — a gate
# entry with no source is a rule nobody can check against the C++.
_ig_re_cite = re.compile(r"\.(?:cpp|h):\d+")
assert _ig_ships.GATED_FIELDS, "the gate has no fields at all"
for _ig_f, _ig_why in _ig_ships.GATED_FIELDS.items():
    assert _ig_re_cite.search(_ig_why), (
        f"gated field {_ig_f} cites no file:line for where the "
        f"engine rewrites it")
    assert _ig_f in _ig_ships.BLANK_FIELDS, (
        f"gated field {_ig_f} has no blank value, so the map would "
        f"read another screen's numbers before its first snapshot")
assert set(_ig_ships.GATED_FIELDS) == set(_ig_ships.BLANK_FIELDS)
# AND THE SET IS PINNED TO THE READING, because the rule iterates
# the set and therefore cannot notice a field taken OUT of it. Work
# order 136 A read every write in flt.cpp, flt1.cpp, flt2.cpp and
# officer.cpp against what ext_api.cpp serializes: these two are on
# the wire and rewritten, _cur_map_x/_cur_map_y are not written by
# either screen at all, and FSEL's stack is written once on exit
# (flt1.cpp:827). A field leaving this set is a re-reading of the
# engine and not a tidy-up, so it fails here and the status
# document moves with it.
assert set(_ig_ships.GATED_FIELDS) == {"ship_icons", "map_scale"}, (
    f"the gated set is now {sorted(_ig_ships.GATED_FIELDS)}; work "
    f"order 136 A measured it as ship_icons and map_scale")

def _ig_snapshot(screen_id, icons, map_scale=15):
    """A STATE_SNAPSHOT payload. `icons` are
        (stack_id, node_idx, star_idx, stack_slot, x, y)."""
    _b = bytearray()
    _b += _ig_s.pack("<hbihhhhhB b", screen_id, 0, 35024,
                     0, 2, 0, 0, 0, 0, 0)
    _b += _ig_s.pack("<hhhhh", map_scale, 0, 0, 759, 600)
    _b += bytes(_IG_SET)
    _b += bytes(_IG_PL * 8)
    _b += _ig_s.pack("<h", 0)                     # stars
    _b += _ig_s.pack("<h", 0)                     # ships
    _b += _ig_s.pack("<h", 0)                     # colonies
    _b += _ig_s.pack("<h", 0)                     # planets
    _b += bytes([0])                              # nebulas
    _b += bytes(_IG_LD * 67)
    _b += bytes(_IG_AN)
    _b += _ig_s.pack("<h", len(icons))
    for _ic in icons:
        _b += _ig_s.pack("<6h", *_ic)
    _b += _ig_s.pack("<8h", 0, 0, 0, 0, 0, 0, 0, 0)
    return _ig_parse(bytes(_b))

def _ig_value(obj, name):
    """A gated field of a state, comparable by value. Icons are
        objects, so every field of every one of them goes in."""
    _v = getattr(obj, name, None)
    if name == "ship_icons":
        return [(i.stack_id, i.node_idx, i.star_idx, i.stack_slot,
                 i.x, i.y) for i in (_v or [])]
    return _v

def _ig_held(screen):
    return {_n: _ig_value(screen._state, _n)
            for _n in _ig_ships.GATED_FIELDS}

#: Two stacks on the map, at the map's own scale.
_IG_MAP_ICONS = [(0, 0, 5, 0, 260, 210), (1, 1, 6, 2, 300, 214)]
_IG_MAP_SCALE = 15
#: The same two while another screen is up: x/y inside that screen's
#: inset, a FIELD ID where stack_id was, and the scale the inset
#: needs to cover the galaxy (_max_map_scale for a 759x600 map).
_IG_INSET_ICONS = [(137, 0, 5, 0, 452, 61), (138, 1, 6, 2, 468, 73)]
_IG_INSET_SCALE = 30
#: A later screen-0 frame: both stacks moved and the player zoomed.
_IG_MOVED_ICONS = [(0, 0, 5, 0, 264, 218), (1, 1, 6, 2, 296, 206)]
_IG_MOVED_SCALE = 20

_ig_app, _ = _ig_plv.build_screen(1920, 1080)
_ig_app.dispatcher.switch_to("galaxy_map")
_ig_map = _ig_app.dispatcher.screens["galaxy_map"]

# 1. SCREEN 0 IS ADOPTED, and that is the state to be held to.
_ig_map.update(_ig_snapshot(0, _IG_MAP_ICONS, _IG_MAP_SCALE))
_ig_want = _ig_held(_ig_map)
assert _ig_want["ship_icons"] == _IG_MAP_ICONS, _ig_want
assert _ig_want["map_scale"] == _IG_MAP_SCALE, _ig_want
# The fixture has to differ from the map's in EVERY gated field, or
# a field would be "held" by never having changed.
_ig_probe = _ig_snapshot(4, _IG_INSET_ICONS, _IG_INSET_SCALE)
for _ig_f in _ig_ships.GATED_FIELDS:
    assert _ig_value(_ig_probe, _ig_f) != _ig_want[_ig_f], (
        f"the wrong-screen fixture carries the same {_ig_f} as the "
        f"map's, so holding it proves nothing")

# 2. NO OTHER SCREEN ID CHANGES ANY GATED FIELD. Screen 4 is the
#    Fleets screen this was found on, 29 the Officers screen that
#    does the same two writes, 8 the GAME overlay that keeps the map
#    updating underneath it (decision 59), 20 and 32 two ordinary
#    screens. The rule is "0 only", never "not 4".
for _ig_id in (4, 29, 8, 20, 32):
    _ig_other = _ig_snapshot(_ig_id, _IG_INSET_ICONS, _IG_INSET_SCALE)
    _ig_map.update(_ig_other)
    assert _ig_held(_ig_map) == _ig_want, (
        f"screen {_ig_id} reached the map: {_ig_held(_ig_map)} "
        f"against {_ig_want}")
    # The refused snapshot is not touched — the Fleets screen reads
    # the same object in the same frame.
    assert _ig_value(_ig_other, "ship_icons") == _IG_INSET_ICONS and \
        _ig_other.map_scale == _IG_INSET_SCALE, (
            "the gate rewrote the snapshot instead of ignoring it")
    # Everything that is NOT gated stays LIVE, including a field
    # list set onto the snapshot AFTER it was parsed — which
    # core/game_client.py does, and which is what decides what may
    # be sent (decision 59, work order 128 C). A copy of the state
    # would pass every assertion above and fail this one.
    _ig_other.fields = [_gs_mod.FieldInfo()]
    assert _ig_map._state.fields is _ig_other.fields, (
        "the map holds a COPY of the snapshot, so its field list is "
        "one frame old")
    assert _ig_map._state.stardate == 35024
    assert _ig_map._state.map_max_x == 759

# 3. TWO WRONG SCREENS IN A ROW ARE STILL WRONG. A gate that held
#    "the previous snapshot" instead of "the last screen-0 one"
#    passes a single 4 and fails 0 -> 4 -> 4, which is the ordinary
#    case: the screen sends many frames before RETURN, and the frame
#    the map draws first after it is one of them.
_ig_map.update(_ig_snapshot(4, _IG_INSET_ICONS, _IG_INSET_SCALE))
_ig_map.update(_ig_snapshot(4, _IG_INSET_ICONS, _IG_INSET_SCALE))
assert _ig_held(_ig_map) == _ig_want, (
    f"0 -> 4 -> 4 left {_ig_held(_ig_map)} on the map")

# 4. A FRESH SCREEN-0 SNAPSHOT IS TAKEN, in every gated field. The
#    gate freezes while the id is wrong; it does not stop the map.
_ig_map.update(_ig_snapshot(0, _IG_MOVED_ICONS, _IG_MOVED_SCALE))
assert _ig_held(_ig_map) == {"ship_icons": _IG_MOVED_ICONS,
                             "map_scale": _IG_MOVED_SCALE}, \
    _ig_held(_ig_map)

# 5. ENTERING THE SCREEN FORGETS EVERYTHING. An empty map is an
#    honest state; yesterday's stacks over a new galaxy are not.
_ig_map.enter(None)
_ig_map.update(_ig_snapshot(4, _IG_INSET_ICONS, _IG_INSET_SCALE))
assert _ig_held(_ig_map) == {_n: _ig_ships.BLANK_FIELDS[_n]
                             for _n in _ig_ships.GATED_FIELDS}, (
    f"a re-entered map still holds {_ig_held(_ig_map)}")

# 6. THE GATE CANNOT BE WALKED AROUND. Exactly one adoption point in
#    the tree, and no galaxy map module fetches a snapshot of its
#    own — a second one would be ungated, and every reader
#    (render_fleets, maplines, mapeta, mapinput/mapclick,
#    boxmodel.remember, both map views) would be back to needing its
#    own rule.
_ig_dir = os.path.join(SCREENS_DIR, "galaxy_map")
_ig_src = {_f: io.open(os.path.join(_ig_dir, _f),
                       encoding="utf-8").read()
           for _f in sorted(os.listdir(_ig_dir)) if _f.endswith(".py")}
_ig_points = {_f: _t.count("_state_gate.state(")
              for _f, _t in _ig_src.items() if "_state_gate.state(" in _t}
assert _ig_points == {"screen.py": 1}, (
    f"the snapshot is adopted at {_ig_points or 'no point at all'}, "
    f"not at the one place it becomes the map's state")
_ig_own = sorted(_f for _f, _t in _ig_src.items() if "client.state" in _t)
assert not _ig_own, (
    f"{_ig_own} read the client's snapshot directly, behind the gate")

# 7. AND PARKING IS DELIBERATELY OUTSIDE IT. viewctl.park_game stops
#    on an ABSOLUTE target (`map_scale >= fit`) rather than on a
#    comparison with the previous reading — that is what makes it
#    safe against a stale snapshot (fundament, "A fresh message is
#    not a fresh world"). A GATED scale would turn that strength
#    into a target it can never reach, so it is handed the raw
#    snapshot. A grep, because the two differ only in a state this
#    branch already refuses to run in, so no fixture can tell them
#    apart — which is exactly why it needs saying in the file.
assert "park_game(self.app, game_state," in _ig_src["screen.py"], (
    "park_game is no longer handed the raw snapshot")
assert "park_game(self.app, self._state" not in _ig_src["screen.py"], (
    "park_game is handed the GATED state; it stops on an absolute "
    "target and a frozen scale is one it can never reach")

ok(f"what a screen rewrites is that screen's: "
   f"{sorted(_ig_ships.GATED_FIELDS)} come from screen 0 only — "
   f"real bytes through parse_state, five wrong screen ids and "
   f"0->4->4 leave every gated field exactly as it was, a fresh "
   f"screen-0 frame is taken, re-entry forgets, parking stays raw")

# ── AND THE MAP SENDS NOTHING WHILE THE GAME IS ELSEWHERE ───────
#
# Work order 137 B. Decision 33's shape: refuse what the game would
# refuse. The native point `map_click` computes belongs to the MAP's
# field space, and another screen's list is a different space
# (decision 20, work order 128 C) — so every click it could send
# there is one the game would answer somewhere else.
#
# It was already true and it was true BY ACCIDENT, which is why it
# is a check now: the dispatcher routes input to the top screen, so
# the map has no clicks to send while the game is elsewhere. An
# exclusion that happens to hold is not a rule. And the gate above
# made saying it out loud worth doing: while the id is not 0 the
# state `map_click` reads is the last SCREEN-0 one, so a click
# computed from it would look perfectly reasonable.
from screens.galaxy_map import mapinput as _mi
_mi_sent = []
_ig_app.client.inject_click = lambda x, y: _mi_sent.append(("click", x, y))
_ig_app.client.activate_field = lambda fid: _mi_sent.append(("act", fid))
_ig_app.connected = True

def _mi_click(screen_id):
    # No stars and no boxes: the click is an EMPTY-MAP one, which
    # `mapclick.plan` still turns into a native point and a send
    # (`Plan("empty", pointer, …)`). That is the simplest send the
    # map has and the one this refusal has to stop.
    _mi_gs = _ig_snapshot(screen_id, _IG_MAP_ICONS, _IG_MAP_SCALE)
    _mi_gs.fields = []
    _ig_map.update(_mi_gs)
    _view = _ig_map._map_view()
    assert _view is not None, "the map has no view to click in"
    _mi_sent.clear()
    _x, _y, _w, _h = _view.box
    _mi.map_click(_ig_map, _view, _x + _w // 2, _y + _h // 2)
    return list(_mi_sent)

# The map must be back on a screen-0 state first, or the gate is
# holding blanks and the view cannot be built.
_ig_map.enter(None)
_ig_map.update(_ig_snapshot(0, _IG_MAP_ICONS, _IG_MAP_SCALE))
assert _mi_click(0), (
    "a click on the map at screen 0 sent nothing; the control for "
    "this check is dead and the refusals below prove nothing")
for _mi_id in (4, 29, 8, 20, 32):
    assert _mi_click(_mi_id) == [], (
        f"the map sent something while the game reported screen "
        f"{_mi_id}: {_mi_sent}")
_ig_app.connected = False
ok("the galaxy map sends nothing while the game is not on screen 0 "
   "(decision 33), and still sends at screen 0")
