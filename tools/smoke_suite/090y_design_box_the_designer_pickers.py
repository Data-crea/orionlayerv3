# smoke-suite area: design_box
#
# Part of the OrionLayer smoke suite — 090y_design_box_the_designer_pickers.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 4 check(s) it holds:
#   - ids 54-56 are one overlay over the designer, claimed only with open fix 45's DSBX; the dispatcher keeps it across the three and hands 3 back to the page
#   - each picker reads its own list: the box's base off the catch-all, a field per printed row, the weapon picker's modifications one for one with DSBX — a box over it modal, a count that disagrees handed back
#   - the pickers send the field under the click or carrying the key, the full-screen field outside the box, and refuse Accept while only hidden and a click on the box's catch-all
#   - the three pickers draw at 1920, 2576 and 3840 from the recorded boxes, their text scaled once, and every mark they carry is named in their module and the status document


# ── THE DESIGNER'S PICKERS (work order 185, part 7) ─────────────
import types as _db_ns
from screens.design_box import dbgeom as _db_geom
from screens.design_box import dbwire as _db_wire
from screens.design_box import dbdraw as _db_draw

# 1. ONE OVERLAY, THREE IDS.
_db_app, _ = _pv.build_screen(1920, 1080)
_db_d = _db_app.dispatcher
assert all(_db_d.screen_map.get(i) == "design_box" for i in (54, 55, 56))
_db_scr = _db_d.screens["design_box"]
assert _db_scr.IS_OVERLAY and _db_scr.OVERLAY_PARENT == "ship_design"
assert (_db_scr.GAME_SCREEN_ID, tuple(_db_scr.EXTRA_SCREEN_IDS)) == \
    (_db_geom.GAME_SCREEN_ID, _db_geom.EXTRA_SCREEN_IDS) == (55, (54, 56))
_db_bare = _sd_he.design_state("weapon")
_db_bare.design_box = None
assert not _db_scr.claims(_db_bare), "no DSBX: no claim"
for _db_stop, _db_id in (("computer", 54), ("weapon", 55), ("special", 56)):
    _db_gs = _sd_he.design_state(_db_stop)
    assert _db_gs.current_screen == _db_id and _db_scr.claims(_db_gs)
    _db_d.update_from_game(_db_gs)
    assert (_db_d.active_name, _db_d.overlay_name) == \
        ("ship_design", "design_box"), (_db_stop, _db_d.active_name)
_db_d.update_from_game(_sd_he.design_state("designer"))
assert (_db_d.active_name, _db_d.overlay_name) == ("ship_design", ""), \
    "back on 3: the overlay closes, the page stays"
ok("ids 54-56 are one overlay over the designer, claimed only with open fix "
   "45's DSBX; the dispatcher keeps it across the three and hands 3 back "
   "to the page")

# 2. EACH PICKER READS ITS OWN LIST.
_db_boxes = {s: _db_wire.Box(_sd_he.design_state(s))
             for s in ("computer", "weapon", "special")}
assert all(b.state == _db_wire.READY for b in _db_boxes.values()), \
    {k: b.reason for k, b in _db_boxes.items()}
assert _db_boxes["computer"].origin == (3, 109)
assert _db_boxes["weapon"].origin == (2, 66)
assert _db_boxes["special"].origin == (3, 115)
_db_c = _db_boxes["computer"].rows()
assert [r["item"] for _y, r, _f in _db_c] == [0, 1] and \
    all(f is not None for _y, _r, f in _db_c), \
    "a printed row per researched computer, each with its field"
_db_wr = _db_boxes["weapon"].rows()
assert [r["extra"] for _y, r, _f in _db_wr] == [0, 14, 21, 3] and \
    [y for y, _r, _f in _db_wr] == [139, 153, 167, 181]
assert [i for i, _f, _on in _db_boxes["weapon"].mods()] == [10, 11, 12]
assert len(_db_boxes["weapon"].rack_fields()) == 5 and \
    not _db_boxes["weapon"].arc_fields(), "a missile: the rack list"
assert [f.hotkey for f in _db_boxes["weapon"].filter_fields()] == \
    [ord("B"), ord("M"), ord("O"), ord("S")]
assert len(_db_boxes["special"].rows()) == 4
assert _db_draw.lit_arc(0x10) == 4 and _db_draw.lit_arc(0x01) == 0 and \
    _db_draw.lit_arc(0x03) == 1 and _db_draw.lit_arc(0) == 0
_db_msg = _sd_he.design_state("weapon")
_db_msg.fields = [f for f in _db_msg.fields if f.hotkey != 27 or
                  f.field_type != 0]
assert _db_wire.Box(_db_msg).state == _db_wire.GAME_BOX
_db_scr.update(_db_msg)
assert _db_scr.handover_is_modal() and _db_scr.wants_original()
_db_mm = _sd_he.design_state("weapon")
_db_mm.design_box = dict(_db_mm.design_box, mods_offered=[10, 11])
assert _db_wire.Box(_db_mm).state == _db_wire.MISMATCH
_db_scr.update(_db_mm)
assert _db_scr.wants_original() and not _db_scr.handover_is_modal()
ok("each picker reads its own list: the box's base off the catch-all, a "
   "field per printed row, the weapon picker's modifications one for one "
   "with DSBX — a box over it modal, a count that disagrees handed back")

# 3. WHAT A CLICK OR A KEY SENDS.
_db_log = []
_db_app.client = _db_ns.SimpleNamespace(
    state=_sd_he.design_state("weapon"),
    activate_field=lambda i: _db_log.append(("activate", i)),
    inject_click=lambda x, y: _db_log.append(("click", x, y)),
    inject_key=lambda k: _db_log.append(("key", k)))
_db_app.connected = True
_db_app.hstrings = derived(HStrings)
_db_scr._names = _sd_Names(_db_app, "en", root=DERIVED_ROOT)
from screens.ship_design import sdart as _db_art
_db_art_real = _db_art._loaded
# A picture set that answers every label: the send path does not depend
# on the player's DESIGN.LBX (the render check below needs none either).
_db_art._loaded = _db_ns.SimpleNamespace(
    folder=_db_art.GAMEDATA, available=True, reason="",
    label=lambda *a, **k: pygame.Surface((4, 4)),
    arc=lambda i: pygame.Surface((4, 4)))
try:
    _db_scr.update(_db_app.client.state)
    assert _db_scr.ready(), _db_scr.fallback_reason()
    _db_live = _db_app.client.state.fields

    def _db_hit(x, y):
        _db_log.clear()
        _db_scr.handle_click(x, y)
        return list(_db_log)

    def _db_centre(f):
        r = _sd_nd.rect(_db_scr.layout, (f.x, f.y, f.x_end, f.y_end))
        return r.centerx, r.centery

    _db_b = _db_wire.Box(_db_app.client.state)
    for _db_f in ([_db_b.cancel, _db_b.accept()] + _db_b.filter_fields() +
                  _db_b.rack_fields() + [f for _i, f, _o in _db_b.mods()] +
                  [f for _y, _r, f in _db_b.rows()]):
        assert _db_hit(*_db_centre(_db_f)) == [("activate", _db_f.index)], \
            (_db_f.x, _db_f.y)
    _db_x, _db_y = _sd_nd.point(_db_scr.layout, 1, 1)
    assert _db_hit(_db_x, _db_y) == [("activate", _db_b.full_screen.index)], \
        "outside the box: the full-screen field"
    _db_x, _db_y = _sd_nd.point(_db_scr.layout, 0x250, 0x80)
    assert _db_hit(_db_x, _db_y) == [], "the box's catch-all: nothing"
    for _db_key, _db_want in ((pygame.K_ESCAPE, _db_b.cancel),
                              (pygame.K_b, _db_b.filter_fields()[0]),
                              (pygame.K_a, _db_b.accept())):
        _db_log.clear()
        _db_scr.handle_key(_db_key)
        assert _db_log == [("activate", _db_want.index)], _db_key
    # Accept only hidden (not a valid choice): refused, by click and key.
    _db_inv = _sd_he.design_state("weapon")
    _db_acc = _db_wire.Box(_db_inv).accept()
    _db_acc.field_type, _db_acc.hotkey = 7, 0
    _db_app.client.state = _db_inv
    _db_scr.update(_db_inv)
    assert _db_hit(*_db_centre(_db_acc)) == []
    _db_log.clear()
    _db_scr.handle_key(pygame.K_a)
    assert _db_log == []
finally:
    _db_art._loaded = _db_art_real
_db_src = open(os.path.join(SCREENS_DIR, "design_box", "screen.py"),
               encoding="utf-8").read()
assert _db_src.count("activate_field(") == 1 and "inject_" not in _db_src
ok("the pickers send the field under the click or carrying the key, the "
   "full-screen field outside the box, and refuse Accept while only hidden "
   "and a click on the box's catch-all")

# 4. THEY DRAW (the shield / computer and special pickers need no art; the
# weapon picker with a stand-in picture set), and the marks are named.
_db_fonts = {}
_db_art._loaded = _db_ns.SimpleNamespace(
    folder=_db_art.GAMEDATA, available=True, reason="",
    label=lambda *a, **k: pygame.Surface((4, 4)),
    arc=lambda i: pygame.Surface((4, 4)))
try:
    for _db_size in ((1920, 1080), (2576, 1432), (3840, 2160)):
        _db_fonts[_db_size] = {}
        for _db_stop in ("computer", "weapon", "special"):
            _db_a, _ = _pv.build_screen(*_db_size)
            _db_gs = _sd_he.design_state(_db_stop)
            _db_a.dispatcher.update_from_game(_db_gs)
            _db_o = _db_a.dispatcher.overlay
            _db_a.hstrings = derived(HStrings)
            _db_o._names = _sd_Names(_db_a, "en", root=DERIVED_ROOT)
            _db_o.update(_db_gs)
            assert _db_o.ready(), (_db_stop, _db_o.fallback_reason())
            _db_s = pygame.Surface(_db_size)
            _db_fonts[_db_size][_db_stop] = _sd_he.font_sites(
                _db_o.style, lambda: _db_o.render(_db_s))
finally:
    _db_art._loaded = _db_art_real
for _db_stop in ("computer", "weapon", "special"):
    _db_a1 = _db_fonts[(1920, 1080)][_db_stop]
    assert len(_db_a1) >= 3 and not _sd_he.scaled_twice(
        _db_a1, _db_fonts[(3840, 2160)][_db_stop]), _db_stop
_db_nmarks = _sd_marks_named("design_box",
                             ("dbdraw.py", "screen.py", "dbwire.py"))
ok(f"the three pickers draw at 1920, 2576 and 3840 from the recorded boxes, "
   f"their text scaled once, and every mark they carry is named in their "
   f"module and the status document ({_db_nmarks} marks)")
