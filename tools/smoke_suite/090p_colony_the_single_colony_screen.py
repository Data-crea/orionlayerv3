# smoke-suite area: colony
#
# Part of the OrionLayer smoke suite — 090p_colony_the_single_colony_screen.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 6 check(s) it holds:
#   - open fixes 35-40's blocks, as a scratch engine wrote them, parse whole; a tail cut short leaves every block None
#   - CRUNCH, TOGGLE and the full-screen field [0] are refused on screens 1 and 25, and every send there goes through that one guard
#   - screen 1 is claimed only with open fix 35: without it the game's picture, as before; with it WAITING until the pair and the handle agree, a box over it modal
#   - the colony screen's geometry is the source's: building cells on the live fields, the help table, _building_cr copied exactly
#   - the colony screen's words by the source's own ids, the status word an HD STATE without fix 37, and the autobuild label's encodings
#   - the colony screen draws at 1920, 2576 and 3840 from a READY snapshot, and every mark it carries is named in its module and the status document


# ── THE SINGLE-COLONY SCREEN (work order 180 B) ─────────────────
import json as _cs_json
import types as _cs_ns
from core import colony_guard as _cs_guard
from core import game_state as _cs_gsm
from core import colonyblocks as _cs_blocks
from core.structs import colony as _cs_colony
from core.structs import planet as _cs_planet
from core.structs import player as _cs_player
from screens.colony import colgeom as _cs_geom
from screens.colony import colwire as _cs_wire
from screens.colony import colwords as _cs_words

_cs_root = os.path.dirname(SCREENS_DIR)
with open(os.path.join(_cs_root, "tools", "fixtures", "colony_blocks_180.json"),
          encoding="utf-8") as _cs_fh:
    _cs_fix = _cs_json.load(_cs_fh)["stops"]

# 1. THE WIRE FORMAT, AS AN ENGINE WROTE IT. Each tail is what a scratch
# build carrying open fixes 35-40 sent after INFS's place (never applied
# to orionlayer-local). Whole, or not at all — a half-read block would draw
# a colony from half its data without saying so.
_cs_want = {1: ("colony_screen", "colony_placement", "colony_events",
                "colony_product"),
            25: ("colony_screen", "colony_product", "build_queue",
                 "build_lists")}
for _cs_stop in _cs_fix:
    _cs_tail = bytes.fromhex(_cs_stop["tail"])
    _cs_gs = _cs_gsm.GameState()
    assert _cs_blocks.parse(_cs_gs, _cs_tail, 0) == len(_cs_tail)
    _cs_have = {k for k in ("colony_screen", "colony_placement",
                            "colony_events", "colony_product", "build_queue",
                            "build_lists") if getattr(_cs_gs, k) is not None}
    assert _cs_have == set(_cs_want[_cs_stop["screen"]]), (_cs_stop["name"],
                                                          _cs_have)
    if _cs_stop["screen"] == 25:
        assert len(_cs_gs.build_lists["queue"]) == 7
    _cs_cut = _cs_gsm.GameState()
    _cs_blocks.parse(_cs_cut, _cs_tail[:10], 0)
    assert all(getattr(_cs_cut, k) is None for k in _cs_have), \
        "a short COLS must leave the block None"
_cs_none = _cs_gsm.GameState()
assert _cs_blocks.parse(_cs_none, b"", 0) == 0 and \
    _cs_none.colony_screen is None and _cs_none.build_lists is None
ok(f"open fixes 35-40's blocks, as a scratch engine wrote them, parse whole; "
   f"a tail cut short leaves every block None ({len(_cs_fix)} stops)")

# 2. THE SAFETY RULE (work order 126, and 180 B): never CRUNCH, TOGGLE or
# the full-screen field [0] on screen 1 — nor any full-screen field or
# type-8 field on 1 or 25. Held on every field the recorded screens held,
# and on the code: every send on those screens goes through the guard.
_cs_refused = _cs_sent = 0
for _cs_stop in _cs_fix:
    for _x, _y, _xe, _ye, _t in _cs_stop["fields"]:
        _f = _cs_ns.SimpleNamespace(x=_x, y=_y, x_end=_xe, y_end=_ye,
                                    field_type=_t)
        _why = _cs_guard.refusal(_f, _cs_stop["screen"])
        _bad = _t == 8 or (_x, _y, _xe, _ye) == (0, 0, 639, 479)
        assert bool(_why) == _bad, (_cs_stop["name"], (_x, _y, _xe, _ye, _t))
        _cs_refused += bool(_why)
        _cs_sent += not _why
        if _bad:
            try:
                _cs_guard.check(_f, _cs_stop["screen"])
                raise AssertionError("the guard let a forbidden field pass")
            except _cs_guard.Refused:
                pass
assert _cs_refused >= 3 * sum(1 for s in _cs_fix if s["screen"] == 1)
assert _cs_guard.refusal(_cs_ns.SimpleNamespace(
    x=0, y=0, x_end=639, y_end=479, field_type=7), 0) is None, \
    "the rule is screen 1 and 25's, not the galaxy map's"
for _cs_rel in ("screens/colony/screen.py", "tools/colony_record.py",
                "tools/colony_live.py"):
    _cs_src = open(os.path.join(_cs_root, _cs_rel), encoding="utf-8").read()
    assert "colony_guard" in _cs_src, _cs_rel
for _cs_rel in ("screens/colony/screen.py",):
    _cs_src = open(os.path.join(_cs_root, _cs_rel), encoding="utf-8").read()
    _cs_i = _cs_src.index("    def send(self, field, label):")
    _cs_body = _cs_src[_cs_i:_cs_src.index("\n    def ", _cs_i + 10)]
    assert _cs_src.count("activate_field(") == 1 and \
        "activate_field(" in _cs_body and "colony_guard.check" in _cs_body, \
        f"{_cs_rel}: every activation must be `send`'s, behind the guard"
ok(f"CRUNCH, TOGGLE and the full-screen field [0] are refused on screens 1 "
   f"and 25, and every send there goes through that one guard "
   f"({_cs_refused} refused, {_cs_sent} allowed)")


# A READY snapshot of our own making: one player, one star with one
# planet, one colony — no player's data.
def _cs_state(handle=0, fields=True, blocks=True):
    gs = _cs_gsm.GameState()
    gs.current_screen, gs.player_num = 1, 0
    gs.player_raw = [bytes(_lm_pack(_cs_player.SPEC, _cs_player.SIZE,
                                    race_name="Us"))] + \
        [bytes(_cs_player.SIZE)] * 7
    gs.stars = _lm_star_mod.parse_all([_lm_star_raw(
        "Sol", 100, 100, 0, 1, [0, -1, -1, -1, -1], [-1] * 8)])
    gs.planets_raw = [bytes(_lm_pack(_cs_planet.SPEC, _cs_planet.SIZE,
                                     colony_index=0, star_index=0, orbit=0,
                                     planet_type=3, size=2, gravity_class=1,
                                     climate=5, mineral_class=2))]
    pops = [0x280, 0x280, 0x300, 0x200]
    gs.colonies_raw = [bytes(_lm_pack(
        _cs_colony.SPEC, _cs_colony.SIZE, owner=0, planet=0, n_pops=4,
        pop=pops + [0] * 38, producing=[1, -1, -1, -1, -1, -1, -1],
        buildings=[0] * 5 + [1] + [0] * 43, military=[3, 0]))]
    if blocks:
        gs.colony_screen = {"star": 0, "orbit": 0, "colony": handle,
                            "drawing_display": 0, "field_mode": 0,
                            "autobuild_enabled": 0}
    if fields:
        gs.fields = [_cs_gsm.FieldInfo() for _ in range(3)]
        for _i, (_r, _t) in enumerate((((556, 459, 628, 478), 0),
                                       ((519, 123, 580, 144), 0),
                                       ((0, 0, 639, 479), 7))):
            _f = gs.fields[_i]
            _f.index, _f.field_type, _f.hotkey = _i + 1, _t, 0
            _f.x, _f.y, _f.x_end, _f.y_end = _r
    return gs


from core.structs import star as _lm_star_mod
# 3. THE CLAIM. Without open fix 35 id 1 is no HD screen's — the game's
# picture, the path it always took; with it the screen WAITS on the first
# tick's stale handle (the gate holds), and a box over it is a modal.
assert not _cs_wire.claims(_cs_state(blocks=False))
_cs_d = app.dispatcher
_cs_d.update_from_game(_cs_state(blocks=False))
assert _cs_d.use_original and _cs_d.active is None, \
    "without the block the game's picture must stand, as before"
_cs_d.update_from_game(_cs_state())
assert _cs_d.active_name == "colony" and not _cs_d.use_original
_cs_scr = _cs_d.active
_cs_scr.update(_cs_state())
assert _cs_scr._view.draws and not _cs_scr.wants_original()
_cs_scr.update(_cs_state(handle=5))
assert _cs_scr._view.state == _cs_wire.WAITING and _cs_scr.wants_original() \
    and not _cs_scr.handover_is_modal(), "a stale handle is waited for"
_cs_scr.update(_cs_state(fields=False))
assert _cs_scr._view.state == _cs_wire.GAME_BOX and \
    _cs_scr.handover_is_modal(), "a box over the screen is the net's"
_cs_d.switch_to("main_menu")
ok("screen 1 is claimed only with open fix 35: without it the game's picture, "
   "as before; with it WAITING until the pair and the handle agree, a box "
   "over it modal")

# 4. GEOMETRY IS THE SOURCE'S. The building cells of every recorded grid
# land on the live building fields (the second source for fix 36's
# cells); the help table is erichelp.cpp's; `_building_cr` is copied.
_cs_cells = 0
for _cs_stop in _cs_fix:
    if _cs_stop["screen"] != 1:
        continue
    _cs_gs = _cs_gsm.GameState()
    _cs_blocks.parse(_cs_gs, bytes.fromhex(_cs_stop["tail"]), 0)
    _cs_live = {tuple(f[:4]) for f in _cs_stop["fields"] if f[4] == 7}
    for _r, _row in enumerate(_cs_gs.colony_placement["grid"]):
        for _c, _b in enumerate(_row):
            if _b:
                assert _cs_geom.building_field(_r, _c) in _cs_live, \
                    (_cs_stop["name"], _r, _c)
                _cs_cells += 1
assert _cs_cells >= 20
with open(os.path.join(_cs_root, "screens", "colony", "help.json"),
          encoding="utf-8") as _cs_fh:
    _cs_help = _cs_json.load(_cs_fh)["regions"]
assert [(h["help_id"], tuple(h["native"])) for h in _cs_help] == \
    [(i, tuple(r)) for i, r in _cs_geom.HELP] and len(_cs_help) == 17 \
    and _cs_help[-1]["help_id"] == 483
_cs_cpp = os.path.expanduser("~/orion2re/src/game/colony.cpp")
if os.path.exists(_cs_cpp):
    import re as _cs_re
    _cs_m = _cs_re.search(r"_building_cr\[170\] = \{(.*?)\};",
                          open(_cs_cpp, encoding="utf-8").read(), _cs_re.S)
    assert tuple(int(v) for v in _cs_m.group(1).split(",") if v.strip()) \
        == _cs_geom.BUILDING_CR, "_building_cr drifted from colony.cpp"
    _cs_src_note = "checked against colony.cpp"
else:
    _cs_src_note = "orion2re absent: colony.cpp not compared"
assert len(_cs_geom.BUILDING_CR) == 170
ok(f"the colony screen's geometry is the source's: building cells on the "
   f"live fields, the help table, _building_cr copied exactly ({_cs_cells} "
   f"cells; {_cs_src_note})")

# 5. THE WORDS, by the source's own ids, over stand-in templates shaped
# like the originals (orion2_str.h's comments) — never the player's.
_cs_tpl = {97: "%sColony of %s", 601: "Industrial ", 424:
           "Pop %d,%03d k (%+dk)", 32: "%d turn(s)", 202: "Blockaded",
           415: "Plague", 426: "Pop. Boom", 0x0BD: "Autobuilding", 12: ""}
_cs_es = _cs_ns.SimpleNamespace(string=lambda i: _cs_tpl.get(i))
_cs_w = _cs_words.Words(_cs_es)
_cs_v = _cs_wire.View(_cs_state())
_cs_v.colony = _cs_ns.SimpleNamespace(**{**_cs_v.colony.__dict__})  \
    if hasattr(_cs_v.colony, "__dict__") else _cs_v.colony
assert _cs_w.turns(3) == "3 turn(s)"
assert _cs_w.pop(_cs_v) == "Pop 4,000 k (+0k)", _cs_w.pop(_cs_v)
_cs_g = _cs_state()
assert _cs_w.status(_cs_v, 0, _cs_g) is None, \
    "without open fix 37 the status word is an HD STATE: nothing"
_cs_g.colony_events = {"plague": False, "pop_boom": True}
assert _cs_w.status(_cs_v, 0, _cs_g) == "Pop. Boom"
_cs_g.colony_events = {"plague": True, "pop_boom": True}
assert _cs_w.status(_cs_v, 0, _cs_g) == "Plague"
for _enabled, _value, _want in ((False, 0, ""), (False, 1, "Autobuilding"),
                                (False, 5, "Autobuilding"),
                                (True, 1, "Autobuilding"),
                                (True, 5, "Auto Build Queue 3"),
                                (True, 0, "")):
    _cs_v.autobuild_enabled = _enabled
    _cs_v.colony = _cs_ns.SimpleNamespace(auto_building=_value,
                                          occupation_policy=1, specialty=1)
    assert _cs_w.autobuild(_cs_v) == _want, (_enabled, _value)
assert _cs_w.title(_cs_v, "Sol I") == "Industrial Colony of Sol I"
ok("the colony screen's words by the source's own ids, the status word an "
   "HD STATE without fix 37, and the autobuild label's encodings")

# 6. IT DRAWS, and its marks are named where the rule says.
import pygame as _cs_pg
_cs_inked = []
for _cs_size in ((1920, 1080), (2576, 1432), (3840, 2160)):
    _cs_app, _cs_s = _pv.build_screen(*_cs_size)
    _cs_app.dispatcher.update_from_game(_cs_state())
    _cs_c = _cs_app.dispatcher.active
    _cs_c.update(_cs_state())
    _cs_surf = _cs_pg.Surface(_cs_size)
    _cs_c.render(_cs_surf)
    from screens.leaders import ldrdraw as _cs_nd
    _cs_r = _cs_nd.rect(_cs_c.layout, _cs_geom.PROD_ROWS[1])
    _cs_inked.append(len({_cs_surf.get_at((x, _cs_r.centery))[:3]
                          for x in range(_cs_r.x, _cs_r.right, 3)}))
assert min(_cs_inked) > 3, _cs_inked
with open(os.path.join(_cs_root, "screens", "colony", "layout.json"),
          encoding="utf-8") as _cs_fh:
    _cs_marks = _cs_json.load(_cs_fh)["marks"]
_cs_mod = "".join(open(os.path.join(_cs_root, "screens", "colony", _f),
                       encoding="utf-8").read()
                  for _f in ("coldraw.py", "screen.py", "colwire.py"))
_cs_status = open(os.path.join(_cs_root, "v3_projektstatus.md"),
                  encoding="utf-8").read()
for _cs_key in _cs_marks:
    _cs_label, _cs_name = _cs_key.split("_", 1) if not _cs_key.startswith(
        "hd_") else ("hd_" + _cs_key.split("_")[1],
                     _cs_key.split("_", 2)[2])
    assert f"`{_cs_name}`" in _cs_mod, f"{_cs_key}: not named in the module"
    assert f"`{_cs_name}`" in _cs_status, f"{_cs_key}: not in the status doc"
ok(f"the colony screen draws at 1920, 2576 and 3840 from a READY snapshot, "
   f"and every mark it carries is named in its module and the status "
   f"document ({len(_cs_marks)} marks)")
