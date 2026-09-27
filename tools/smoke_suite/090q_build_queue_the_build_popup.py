# smoke-suite area: build_queue
#
# Part of the OrionLayer smoke suite — 090q_build_queue_the_build_popup.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 4 check(s) it holds:
#   - screen 25 is claimed only with open fixes 35, 38, 39 and 40; a list the rows contradict hands over, a box over it is modal
#   - on every recorded popup the lists line up with the rows the game built, and every queued item has its numbers
#   - the popup sends a row's own field, nothing for a separator, and the Auto Build radio by an injected click
#   - the build popup draws at 1920, 2576 and 3840 from a recorded popup, its text scaled once, and every mark it carries is named in its module and the status document


# ── THE BUILD POPUP (work order 180 C) ──────────────────────────
from screens.build_queue import bqwire as _bq_w


def _bq_state(stop, blocks=True):
    """A recorded popup's own tail and field list, over planets and
    colonies of our own that put its colony where its block says."""
    gs = _cs_gsm.GameState()
    gs.current_screen, gs.player_num = 25, 0
    _cs_blocks.parse(gs, bytes.fromhex(stop["tail"]), 0)
    b = gs.colony_screen
    gs.planets_raw = [bytes(_lm_pack(_cs_planet.SPEC, _cs_planet.SIZE,
                                     colony_index=b["colony"],
                                     star_index=b["star"], orbit=b["orbit"],
                                     planet_type=3, size=2, climate=5))]
    gs.colonies_raw = [bytes(_lm_pack(
        _cs_colony.SPEC, _cs_colony.SIZE, owner=0, planet=0,
        producing=gs.build_queue["items"]))] * (b["colony"] + 1)
    gs.player_raw = [bytes(_cs_player.SIZE)] * 8
    fields = []
    for i, (x, y, xe, ye, t) in enumerate(stop["fields"]):
        f = _cs_gsm.FieldInfo()
        f.index, f.x, f.y, f.x_end, f.y_end, f.field_type = i + 1, x, y, \
            xe, ye, t
        f.hotkey = 0
        fields.append(f)
    gs.fields = fields
    if not blocks:
        gs.build_queue = gs.build_lists = None
    return gs


_bq_stops = [s for s in _cs_fix if s["screen"] == 25]
assert len(_bq_stops) >= 3

# 1. THE CLAIM — on a fresh app: the shared one carries overlays other
# checks opened for themselves.
_bq_d = _pv.build_screen(1920, 1080)[0].dispatcher
_bq_d.update_from_game(_bq_state(_bq_stops[0], blocks=False))
assert _bq_d.use_original, ("without fixes 39/40 the game's picture stands",
                            _bq_d.active_name, _bq_d.overlay_name,
                            _bq_d._locked_screen)
# Each of the four blocks the engine writes on 25 is required on its own
# (work order 181: 38 joined, for the summary's "Turn(s) Left").
assert _bq_w.BLOCKS == ("colony_screen", "colony_product", "build_queue",
                        "build_lists")
for _bq_k in _bq_w.BLOCKS:
    _bq_one = _bq_state(_bq_stops[0])
    setattr(_bq_one, _bq_k, None)
    assert not _bq_w.claims(_bq_one), f"claimed without {_bq_k}"
    _bq_d.update_from_game(_bq_one)
    assert _bq_d.use_original, f"without {_bq_k} the game's picture stands"
_bq_d.update_from_game(_bq_state(_bq_stops[0]))
assert _bq_d.active_name == "build_queue"
_bq_s = _bq_d.active
_bq_s.update(_bq_state(_bq_stops[0]))
assert _bq_s._view.draws, _bq_s._view.reason
_bq_bad = _bq_state(_bq_stops[0])
_bq_bad.fields = [f for f in _bq_bad.fields if f.x != 485]
_bq_s.update(_bq_bad)
assert _bq_s._view.state == _bq_w.MISMATCH and _bq_s.wants_original() \
    and not _bq_s.handover_is_modal(), \
    "a list the rows contradict is a screen that cannot vouch — a failure"
_bq_box = _bq_state(_bq_stops[0])
_bq_box.fields = [f for f in _bq_box.fields if (f.x, f.y) != (493, 447)]
_bq_s.update(_bq_box)
assert _bq_s._view.state == _bq_w.GAME_BOX and _bq_s.handover_is_modal()
_bq_d.switch_to("main_menu")
ok("screen 25 is claimed only with open fixes 35, 38, 39 and 40; a list the rows "
   "contradict hands over, a box over it is modal")

# 2. THE LISTS ARE THE GAME'S, ROW FOR ROW.
_bq_rows = 0
for _bq_stop in _bq_stops:
    _bq_v = _bq_w.View(_bq_state(_bq_stop))
    assert _bq_v.draws, (_bq_stop["name"], _bq_v.reason)
    assert len(_bq_v.building_rows) == len(_bq_v.buildings) >= 2
    assert len(_bq_v.other_rows) == len(_bq_v.others)
    assert [r.y for r in _bq_v.building_rows] == \
        [20 + 19 * i for i in range(len(_bq_v.buildings))]
    for _bq_item in _bq_v.items:
        if _bq_item != _bq_w.NONE:
            assert _bq_v.entry(_bq_item) is not None, (_bq_stop["name"],
                                                      _bq_item)
    _bq_rows += len(_bq_v.building_rows) + len(_bq_v.other_rows)
ok(f"on every recorded popup the lists line up with the rows the game built, "
   f"and every queued item has its numbers ({len(_bq_stops)} popups, "
   f"{_bq_rows} rows)")

# 3. WHAT A CLICK SENDS. A fake client records the three send paths.
_bq_app, _bq_scr = _pv.build_screen(1920, 1080)
_bq_log = []
_bq_app.client = _cs_ns.SimpleNamespace(
    state=_bq_state(_bq_stops[0]),
    activate_field=lambda i: _bq_log.append(("activate", i)),
    inject_click=lambda x, y: _bq_log.append(("click", x, y)),
    inject_key=lambda k: _bq_log.append(("key", k)))
_bq_app.connected = True
_bq_app.dispatcher.update_from_game(_bq_app.client.state)
_bq_p = _bq_app.dispatcher.active
_bq_p.update(_bq_app.client.state)
_bq_v = _bq_p._view
from screens.leaders import ldrdraw as _bq_nd


def _bq_click(f):
    r = _bq_nd.rect(_bq_p.layout, (f.x, f.y, f.x_end, f.y_end))
    _bq_log.clear()
    _bq_p.handle_click(r.centerx, r.centery)
    return list(_bq_log)


_bq_f = _bq_v.building_rows[0]
assert _bq_click(_bq_f) == [("activate", _bq_f.index)]
_bq_sep = next((f for e, f in zip(_bq_v.others, _bq_v.other_rows)
                if e["id"] == _bq_w.SEPARATOR), None)
assert _bq_sep is not None and _bq_click(_bq_sep) == [], \
    "a separator row sends nothing (colbldg.cpp:1681-1718)"
_bq_radio = _bq_w.live_field(_bq_app.client.state.fields, _bq_w.AUTO_BUILD)
assert _bq_click(_bq_radio) == [("click", (_bq_radio.x + _bq_radio.x_end)
                                  // 2, (_bq_radio.y + _bq_radio.y_end)
                                  // 2)], "the radio is a click"
_bq_ok = _bq_w.live_field(_bq_app.client.state.fields, _bq_w.OK)
assert _bq_click(_bq_ok) == [("activate", _bq_ok.index)]
# And every activation on this screen is `send`'s, behind the guard.
_bq_src = open(os.path.join(_cs_root, "screens", "build_queue", "screen.py"),
               encoding="utf-8").read()
_bq_i = _bq_src.index("    def send(self, field, label):")
_bq_body = _bq_src[_bq_i:_bq_src.index("\n    def ", _bq_i + 10)]
assert _bq_src.count("activate_field(") == 1 and "activate_field(" in \
    _bq_body and "colony_guard.check" in _bq_body
ok("the popup sends a row's own field, nothing for a separator, and the Auto "
   "Build radio by an injected click")

# 4. IT DRAWS, and its marks are named where the rule says.
_bq_inked = []
_bq_fonts = {}
for _bq_size in ((1920, 1080), (2576, 1432), (3840, 2160)):
    _bq_a, _bq_x = _pv.build_screen(*_bq_size)
    _bq_a.dispatcher.update_from_game(_bq_state(_bq_stops[0]))
    _bq_c = _bq_a.dispatcher.active
    # Committed stand-ins, as 090p's drawing check (a clone must count the
    # same texts).
    _bq_c._strings = derived(EStrings)
    _bq_c._buildings = derived(BuildingNames)
    _bq_c.update(_bq_state(_bq_stops[0]))
    _bq_surf = _cs_pg.Surface(_bq_size)
    # Every font by call site: the window's factor once (090t's rule,
    # work order 182), measured where the popup has a recorded state.
    _bq_fonts[_bq_size] = _cs_he.font_sites(
        _bq_c.style, lambda: _bq_c.render(_bq_surf))
    _bq_r = _bq_nd.rect(_bq_c.layout, _bq_w.QUEUE_BOX)
    _bq_inked.append(len({_bq_surf.get_at((x, y))[:3]
                          for x in range(_bq_r.x, _bq_r.right, 4)
                          for y in range(_bq_r.y, _bq_r.bottom, 7)}))
assert min(_bq_inked) > 3, _bq_inked
assert len(_bq_fonts[(1920, 1080)]) >= 3 and not _cs_he.scaled_twice(
    _bq_fonts[(1920, 1080)], _bq_fonts[(3840, 2160)]), \
    _cs_he.scaled_twice(_bq_fonts[(1920, 1080)], _bq_fonts[(3840, 2160)])
with open(os.path.join(_cs_root, "screens", "build_queue", "layout.json"),
          encoding="utf-8") as _bq_fh:
    _bq_marks = _cs_json.load(_bq_fh)["marks"]
_bq_mod = "".join(open(os.path.join(_cs_root, "screens", "build_queue", _f),
                       encoding="utf-8").read()
                  for _f in ("bqdraw.py", "screen.py", "bqwire.py"))
for _bq_key in _bq_marks:
    _bq_name = (_bq_key.split("_", 2)[2] if _bq_key.startswith("hd_")
                else _bq_key.split("_", 1)[1])
    assert f"`{_bq_name}`" in _bq_mod, f"{_bq_key}: not named in the module"
    assert f"`{_bq_name}`" in _cs_status, f"{_bq_key}: not in the status doc"
ok(f"the build popup draws at 1920, 2576 and 3840 from a recorded popup, its "
   f"text scaled once, and "
   f"every mark it carries is named in its module and the status document "
   f"({len(_bq_marks)} marks)")
