# smoke-suite area: leaders
#
# Part of the OrionLayer smoke suite — 090d_leaders_the_map_the_grid_and_the_strips.py.
# Executed in the suite's one namespace, after 090a-090c (whose `_ld_pack`,
# `_ldw_snapshot`, `_ldw_fields`, `_ldw_f`, `_ldw_recs`, `_ldw_block` and
# the Leaders screen `_ldw_scr` with its send recorder it uses). Work order
# 175 B: the Leaders screen complete, with open fix 30 applied.
#
# The 4 check(s) it holds:
#   - with the OFFS block every Leaders button in both views goes to its
#     own live field, ESC too; without it the ones needing the mode stay
#     home
#   - the galaxy box and the grid: a big icon and a stack icon (ship view)
#     and a star with the player's colony (colony view) go to their live
#     fields; a star without one, any map click outside mode -1 or
#     without the block, and a stack in the colony view do not; a right
#     click on a big icon asks the game for its ship view
#   - the two strips say what the original prints: "%s (%s)" and the ETA
#     forms, the unknown star, the fleet paragraph with singular and
#     plural hull names and its last ", " cut, the scanned big ship; HD's
#     pointer follows the loop's rules
#   - nothing on the screen says "open fix 30" any more, the placeholder
#     is gone from the code, and 006f's glass check no longer excuses the
#     black mini-map
import struct as _lm_st

from core.structs import Spec as _LmSpec
from core.structs import colony as _lm_colony
from core.structs import planet as _lm_planet
from core.structs import player as _lm_player
from core.structs import ship as _lm_ship
from core.structs import ship_icon as _lm_icon
from core.structs import star as _lm_star
from screens.leaders import ldrmap as _lm
from core.shipparts import ShipPartNames


def _lm_pack(_spec, _size, **kw):
    """One record through a verified spec's own offsets and kinds."""
    _b = bytearray(_size)
    _fmt = {"u8": "<B", "i8": "<b", "i16": "<h", "u16": "<H",
            "i32": "<i", "u32": "<I"}
    for _n, _o, _k in _spec.fields:
        if _n not in kw:
            continue
        _v = kw[_n]
        if _k.startswith("str"):
            _raw = _v.encode("latin-1")[:int(_k[3:]) - 1]
            _b[_o:_o + len(_raw)] = _raw
        elif "[" in _k:
            _base = _k.split("[")[0]
            _w = _LmSpec.kind_width(_base)
            for _i, _x in enumerate(_v):
                _b[_o + _i * _w:_o + (_i + 1) * _w] = _lm_st.pack(
                    _fmt[_base], _x)
        else:
            _b[_o:_o + _LmSpec.kind_width(_k)] = _lm_st.pack(_fmt[_k], _v)
    return _b


def _lm_star_raw(name, x, y, owner, visited, planets, officers):
    _b = _lm_pack(_lm_star.SPEC, _lm_star.SIZE, name=name, x=x, y=y,
                  owner=owner, visited=visited, officer_index=officers)
    for _i, _p in enumerate((list(planets) + [-1] * 5)[:5]):
        _lm_st.pack_into("<h", _b, _lm_star.PLANET_INDEX_OFFSET + 2 * _i, _p)
    return bytes(_b)


def _lm_ship_raw(name, owner, loc, x, y, kind, size, officer=-1):
    return bytes(_lm_pack(_lm_ship.SPEC, _lm_ship.SIZE, name=name,
                          owner=owner, status=0, location=loc, x=x, y=y,
                          ship_type=kind, size=size, officer_index=officer))


def _lm_state(view, block=True, mode=-1):
    """Two stars — Alpha with the player's colony and leader 9, Beta
    unvisited — a stack of four of player 0's at Alpha (an outpost, a
    size-2 and two size-3 warships) and one of player 1's at Beta, their
    icons and FSEL node table, and the fields the engine adds for them."""
    _blk = None
    if block:
        _blk = dict(_ldw_block, view=view, mode=mode,
                    ids=[9] if view == 1 else [2, 7], star_displayed=0,
                    star_chosen=0, stack=0, head=0,
                    icons=[(0, 0), (1, 0), (2, 0), (3, 0)])
    _recs = list(_ldw_recs)
    _recs[9] = _ld_pack(name="Leader 9", type=1, status=1, player_index=0,
                        location=0, general_skills=0x40, skill_value=5)
    _gs = _ldw_snapshot(_recs, block=_blk)
    _gs.stars = _lm_star.parse_all([
        _lm_star_raw("Alpha", 200, 150, 0, 1, [0], [9] + [-1] * 7),
        _lm_star_raw("Beta", 600, 450, -1, 0, [], [-1] * 8)])
    _gs.planets_raw = [bytes(_lm_pack(_lm_planet.SPEC, _lm_planet.SIZE,
                                      colony_index=0, star_index=0))]
    _gs.colonies_raw = [bytes(_lm_pack(_lm_colony.SPEC, _lm_colony.SIZE,
                                       owner=0))]
    _gs.player_raw = [bytes(_lm_pack(_lm_player.SPEC, _lm_player.SIZE,
                                     race_name=_n))
                      for _n in ("Zorg", "Quux")] + \
        [bytes(_lm_player.SIZE)] * 6
    _gs.ships_raw = [
        _lm_ship_raw("Post", 0, 0, 200, 150, _lm_ship.SHIP_TYPE_OUTPOST, 0),
        _lm_ship_raw("Mid", 0, 0, 200, 150, _lm_ship.SHIP_TYPE_COMBAT, 2),
        _lm_ship_raw("Big A", 0, 0, 200, 150, _lm_ship.SHIP_TYPE_COMBAT, 3,
                     officer=2),
        _lm_ship_raw("Big B", 0, 0, 200, 150, _lm_ship.SHIP_TYPE_COMBAT, 3),
        _lm_ship_raw("Them", 1, 1, 600, 450, _lm_ship.SHIP_TYPE_COMBAT, 0)]
    _gs.fleet_selection = {"stack": -1, "ships": [0, 1, 2, 3, 4],
                           "selected": [False] * 5, "chain": []}
    _icons = []
    for _node, _star in ((0, 0), (4, 1)):
        _p = _lm.star_point(_gs, _star)
        _icons.append(_lm_icon.parse(_lm_st.pack(
            "<6h", 0, _node, _star, 0, _p[0] + 4, _p[1] - 6)))
    _gs.ship_icons = _icons
    _fl = _ldw_fields(_gs, view, mode=mode if block else -1)
    for _i in range(2):
        _fl.append(_ldw_f(len(_fl) + 1, _lm.star_field_rect(_gs, _i), 7))
    for _ic in _icons:
        _fl.append(_ldw_f(len(_fl) + 1, (_ic.x, _ic.y, _ic.x + 7,
                                         _ic.y + 6), 7))
    if view == 0:
        for _slot in range(4):
            _fl.append(_ldw_f(len(_fl) + 1, _ldw_g.grid_cell(_slot), 7))
    _gs.fields = _fl
    return _gs


def _lm_field(gs, rect):
    return _ldw_index(gs.fields, rect)


def _lm_mid(rect):
    return ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)


def _lm_pt(native):
    from core import researchnative as _n
    return _n.window_point(native, _ldw_scr.layout)


# ── 14. EVERY BUTTON, BOTH VIEWS ─────────────────────────────
for _lm_view, _lm_names in (
        (0, ("tab_colony", "tab_ship", "hire", "pool", "dismiss", "return",
             "prev", "next", "scroll_up", "scroll_down")),
        (1, ("tab_colony", "tab_ship", "pool", "dismiss", "return", "prev",
             "next"))):
    _lm_s = _lm_state(_lm_view)
    _ldw_scr.update(_lm_s)
    assert _ldw_scr._view.state == _ldw.READY, _ldw_scr._view.reason
    for _lm_name in _lm_names:
        _lm_r = _ldw_g.button_rect(_lm_name)
        assert _ldw_click(_lm_r) == [("act", _lm_field(_lm_s, _lm_r))], (
            _lm_view, _lm_name)
    _ldw_sent.clear()
    _ldw_scr.handle_key(27)
    assert _ldw_sent == [("act", _lm_field(_lm_s,
                                           _ldw_g.button_rect("return")))]
_lm_s = _lm_state(0, block=False)
_ldw_scr.update(_lm_s)
for _lm_name in ("pool", "dismiss", "prev", "next", "scroll_down"):
    assert _ldw_click(_ldw_g.button_rect(_lm_name)) == [], _lm_name
ok("with the OFFS block every Leaders button in both views goes to its own "
   "live field, ESC too; without it POOL, DISMISS, PREV/NEXT and the "
   "arrows stay home")

# ── 15. THE GALAXY BOX AND THE GRID ──────────────────────────
_lm_s = _lm_state(0)
_ldw_scr.update(_lm_s)
_lm_cell = _ldw_g.grid_cell(2)
assert _ldw_click(_lm_cell) == [("act", _lm_field(_lm_s, _lm_cell))]
_lm_ic = _lm_s.ship_icons[1]
_lm_icr = (_lm_ic.x, _lm_ic.y, _lm_ic.x + 7, _lm_ic.y + 6)
assert _ldw_click(_lm_icr) == [("act", _lm_field(_lm_s, _lm_icr))]
_lm_st1 = _lm.star_field_rect(_lm_s, 1)
assert _ldw_click((_lm_st1[0] + 5, _lm_st1[1] + 9, _lm_st1[0] + 5,
                   _lm_st1[1] + 9)) == [], "a star in the ship view went out"
_ldw_sent.clear()
_ldw_scr.handle_right_button(True, *_ldw_centre(_lm_cell))
assert _ldw_sent == [("cancel", _lm_field(_lm_s, _lm_cell))]
_lm_s = _lm_state(1)
_ldw_scr.update(_lm_s)
_lm_st0 = _lm.star_field_rect(_lm_s, 0)
assert _ldw_click(_lm_st0) == [("act", _lm_field(_lm_s, _lm_st0))]
assert _ldw_click(_lm_st1) == [], "a star without a colony went out"
_lm_ic = _lm_s.ship_icons[1]
assert _ldw_click((_lm_ic.x, _lm_ic.y, _lm_ic.x + 7, _lm_ic.y + 6)) == [], \
    "a stack icon went out in the colony view"
for _lm_kw in ({"mode": 2}, {"block": False}):
    _lm_s = _lm_state(1, **_lm_kw)
    _ldw_scr.update(_lm_s)
    assert _ldw_click(_lm.star_field_rect(_lm_s, 0)) == [], _lm_kw
ok("the galaxy box and the grid send to their live fields only where the "
   "loop acts (mode -1, the right view, a colony at the star), and a right "
   "click on a big icon asks for its ship view")

# ── 16. THE STRIPS ────────────────────────────────────────────
# Stand-in templates of the originals' SHAPE — no MOO2 text in the tree.
_LmW = type("_LmW", (), {"hstring": lambda self, i: {
    0x92: "%s <%s, %d day>", 0x93: "%s <%s, %d days>", 0x94: "dark",
    0x131: "%s Navy: ", 0x102: "%d Post, ", 0x103: "%d Posts, ",
    0x104: "%d Hauler, ", 0x105: "%d Haulers, ", 0x106: "%d Seed, ",
    0x107: "%d Seeds, "}.get(i)})()
_lm_parts = derived(ShipPartNames)
_lm_s = _lm_state(1)
_ldw_scr.update(_lm_s)
_lm_v = _ldw_scr._view
assert _lm.fleet_words(_lm_s, _lm_s.ship_icons[0], _LmW, _lm_parts) == (
    "ZORG NAVY: 1 Post, 1 " + _lm_parts.name("hulls", 2) + ", 2 "
    + _lm_parts.name("hull_plurals", 3)), "the fleet paragraph"
assert _lm.displayed_star_words(_lm_s, _lm_v, _LmW, 0) == "Alpha (Leader 9)"
assert _lm.scanned_star_words(_lm_s, _lm_v, _LmW, 1) == "dark"
assert _lm.scanned_star_words(_lm_s, _lm_v, _LmW, 0) == "Alpha (Leader 9)"
for _lm_eta, _lm_want in ((1, "Alpha <L, 1 day>"), (3, "Alpha <L, 3 days>")):
    _lm_rec = _ldw_leader.parse(_ld_pack(name="L", eta=_lm_eta))
    assert _lm.with_leader("Alpha", _lm_rec, _LmW) == _lm_want
_lm_s = _lm_state(0)
_ldw_scr.update(_lm_s)
_lm_v = _ldw_scr._view
assert _lm.big_ship_words(_lm_s, _lm_v, _LmW, 2) == "Big A (Leader 2)"
assert _lm.big_ship_words(_lm_s, _lm_v, _LmW, 1) == "Mid"
# The pointer: a big icon while on it; a stack stays until replaced; a
# star wins over an icon under the same point (the loop's order).
_ldw_scr.handle_mouse_motion(*_lm_pt(_lm_mid(_ldw_g.grid_cell(3))))
assert _ldw_scr._big == 3 and _ldw_scr._scan is None
_lm_ic = _lm_s.ship_icons[1]
_ldw_scr.handle_mouse_motion(*_lm_pt((_lm_ic.x + 5, _lm_ic.y + 5)))
assert _ldw_scr._scan == ("icon", 1) and _ldw_scr._big is None
_ldw_scr.handle_mouse_motion(*_lm_pt((5, 5)))
assert _ldw_scr._scan == ("icon", 1), "a stack stays scanned"
_ldw_scr.handle_mouse_motion(*_lm_pt(_lm_mid(_lm.star_field_rect(_lm_s, 0))))
assert _ldw_scr._scan == ("star", 0)
ok("the two strips say what the original prints (the leader and ETA forms, "
   "the unknown star, the fleet paragraph with plural hulls and its last "
   "separator cut, the scanned big ship), and HD's pointer follows the "
   "loop's rules")

# ── 17. NO PLACEHOLDER, NO BLACK BOX ─────────────────────────
import pygame as _lm_pg
_lm_seen = []
_lm_real = _ldw_scr.style.render_text


def _lm_spy(text, *a, **k):
    _lm_seen.append(text)
    return _lm_real(text, *a, **k)


for _lm_view in (0, 1):
    for _lm_blk in (True, False):
        _ldw_scr.update(_lm_state(_lm_view, block=_lm_blk))
        _ldw_scr.style.render_text = _lm_spy
        try:
            _ldw_scr.render(_lm_pg.Surface((1920, 1080)))
        finally:
            _ldw_scr.style.render_text = _lm_real
assert _lm_seen and not any("open fix 30" in _t or "Not on the wire" in _t
                            for _t in _lm_seen), "a placeholder is drawn"
for _lm_fn in ("ldrright.py", "ldrdraw.py", "screen.py", "ldrwire.py",
               "ldrpopup.py"):
    _lm_src = open(os.path.join(_ldc_root, "screens", "leaders", _lm_fn),
                   encoding="utf-8").read()
    assert "PLACEHOLDER" not in _lm_src and "NOT APPLIED" not in _lm_src, \
        _lm_fn
assert "NOT APPLIED" not in open(os.path.join(_ldc_root, "core", "game_state.py"),
                                 encoding="utf-8").read().split(
                                     "officer_screen: Optional")[0][-600:]
# The black mini-map: 006f renders every screen over two backgrounds and
# no longer excludes this one's galaxy box — a dark flat box there fails
# that check (run once, not twice).
_lm_gl = open(os.path.join(_ldc_root, "tools", "smoke_suite",
                           "006f_core_panel_glass_and_its_slider.py"),
              encoding="utf-8").read()
assert 'stage == "leaders"' not in _lm_gl, "006f excludes Leaders again"
ok("nothing on the Leaders screen names open fix 30 any more, the "
   "placeholder is gone from the code, and no dark flat box is left on it")
