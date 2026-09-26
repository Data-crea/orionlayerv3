# smoke-suite area: planets
#
# Part of the OrionLayer smoke suite — 058_planets_planets_frame_five_cutouts_boxes_json.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - planets frame: five cutouts == boxes.json at both resolutions, every content box inside a cutout
#   - planets row set: type before colony_index, own colonies and outposts out, visited or omniscient,
#   - planets order: three keys descending, ties keep their order, a rebuild re-sorts only when the co
#   - planets words: ESTRINGS/HESTRNGS indices, special line and its pending monster branch, owner and
#   - planets wire: 32 routes here, entry imposes the sort by click, RETURN by the esc field's id, sor
#   - planets help: 15 entries in evanhelp.cpp's order, no screen-wide fallback, every region answers 
#   - planets markings: the panel shows only disc/name/special, the wheel and fills are marked HD EXTE
#   - planets: the hovered row is the drawn row on all pixel lines at four sizes, and a band's edge li


# ── THE PLANETS SCREEN — brief 101 ───────────────────────────
# SCREEN_PLANET_SUMMARY (32), built from Data's frame3 and mockup3.
# Seven checks: the frame's cutouts, the row set, the order, the
# words, the wire, the help table and the markings. The records are
# packed at the verified spec offsets, and the string tables are
# stubs, so nothing here needs the user's install.
import struct as _pl_struct
import tempfile as _pl_tmp
import frame_holes as _pl_fh
from core import hestrings as _pl_hs
from core import listgrid as _pl_lg
from core.game_state import FieldInfo as _PlField
from core.structs import colony as _pl_cspec
from core.structs import planet as _pl_pspec
from core.structs import player as _pl_plspec
from core.structs import ship as _pl_shspec
from core.structs import star as _pl_sspec
from screens.planets import planetdraw as _pld
from screens.planets import planetrows as _plr
from screens.planets import planetwords as _plw
from screens.planets.screen import PlanetsScreen as _PlScreen

# 1. THE FRAME'S FIVE CUTOUTS ARE boxes.json's, and every hand-placed
#    box sits inside one of them (the rule, not the coordinates).
_pl_png = res.screen_file("planets", "assets", "frame.png")
_pl_iw, _pl_ih, _pl_holes = _pl_fh.find_holes(_pl_png)
_pl_named = _pl_fh.name_holes(_pl_holes, "planets", (_pl_iw, _pl_ih))
assert set(_pl_named) == _pl_fh.RULE_NAMES["planets"], sorted(_pl_named)
_pl_boxdoc = _hjson.load(open(os.path.join(
    SCREENS_DIR, "planets", "boxes.json"), encoding="utf-8"))
assert set(_pl_boxdoc) == {"1920x1080", "2560x1440"}, sorted(_pl_boxdoc)
for _pl_res, _pl_list in _pl_boxdoc.items():
    _pl_by = {_b["name"]: _b for _b in _pl_list}
    for _pl_n, _pl_r in _pl_named.items():
        _pl_want = _pl_fh.to_ref(_pl_r, _pl_iw, _pl_ih)
        assert all(abs(_a - _w) <= 2 for _a, _w in zip(
            _pl_by[_pl_n]["rect"], _pl_want)), (
            f"planets {_pl_res}: {_pl_n} is {_pl_by[_pl_n]['rect']}, "
            f"the frame's hole is {_pl_want}")
    # NO nav_* BOX, AND THAT IS LEGAL: only the galaxy map carries the
    # navigation row; nothing in ScreenBase or the smoke nav checks
    # may require one on this screen.
    assert not any(_n.startswith("nav_") for _n in _pl_by), _pl_res
    _pl_cuts = [pygame.Rect(_pl_by[_n]["rect"]) for _n in _pl_named]
    for _b in _pl_list:
        # help_popup is drawn OVER the frame (render_help is last),
        # like on every other help screen; it needs no hole.
        if _b["name"] in _pl_named or "rect" not in _b \
                or _b["name"] == "help_popup":
            continue
        assert any(_c.contains(pygame.Rect(_b["rect"]))
                   for _c in _pl_cuts), (
            f"planets {_pl_res}: {_b['name']} {_b['rect']} is not "
            f"inside any of the frame's five cutouts — the frame "
            f"would cover it")
ok("planets frame: five cutouts == boxes.json at both resolutions, "
   "every content box inside a cutout, no nav_* box and none needed")

# The synthetic galaxy. Stars: Alpha (visited, natives), Beta (NOT
# visited), Gamma (visited, gold), Hole (black hole), Delta (visited,
# space monster). Planets: 0 free Gaia, 1 OUR colony, 2 an enemy
# OUTPOST, 3 an enemy colony, 4 unvisited, 5 heavy-G/poor/hostile
# artifacts world in the monster system, 6 an EMPTY SLOT (type 0 —
# the trap), 7 a second free Gaia.
def _pl_pack(_spec, **_values):
    _off = {_n: (_o, _k) for _n, _o, _k in _spec.SPEC.fields}
    _buf = bytearray(_spec.SIZE)
    for _name, _value in _values.items():
        _o, _k = _off[_name]
        if _k.startswith("str"):
            _buf[_o:_o + len(_value)] = _value.encode("latin-1")
        else:
            _pl_struct.pack_into({"i8": "<b", "u8": "<B", "i16": "<h",
                                  "i32": "<i"}[_k], _buf, _o, _value)
    return _buf

def _pl_star(_name, _x, _slots, _visited=1, _special=0, _spectral=1):
    # y is half of x so every star stays inside the 1012 x 800 map
    # the inset is scaled to — a star past MAP_MAX_Y draws below it.
    _buf = _pl_pack(_pl_sspec, name=_name, x=_x, y=_x // 2, owner=-1,
                    spectral_class=_spectral, system_special=_special,
                    visited=_visited)
    _pl_struct.pack_into("<5h", _buf, _pl_sspec.PLANET_INDEX_OFFSET,
                         *(list(_slots) + [-1] * (5 - len(_slots))))
    return bytes(_buf)

def _pl_planet(_ci, _si, _type, _size, _grav, _clim, _min, _food,
               _special=0):
    return bytes(_pl_pack(
        _pl_pspec, colony_index=_ci, star_index=_si, planet_type=_type,
        size=_size, gravity_class=_grav, climate=_clim,
        mineral_class=_min, food_per_farmer=_food,
        planet_special=_special))

def _pl_player(_race, _colour, _omniscient=False):
    _buf = _pl_pack(_pl_plspec, race_name=_race, color=_colour)
    if _omniscient:
        _buf[_pl_plspec.TRAITS_OFFSET + _pl_plspec.TRAIT_OMNISCIENCE] = 1
    return bytes(_buf)

class _PlSnap:
    def __init__(self, _fields=(), _omniscient=False):
        self.player_num = 0
        self.current_screen = 32
        self.map_max_x, self.map_max_y = 1012, 800
        self.stars = _pl_sspec.parse_all([
            _pl_star("Alpha", 100, [0, 1, 2, 3], _special=6),
            _pl_star("Beta", 300, [4], _visited=0),
            _pl_star("Gamma", 500, [6, 7], _special=4),
            _pl_star("Hole", 700, [], _spectral=6),
            _pl_star("Delta", 900, [5], _special=9)])
        self.planets_raw = [
            _pl_planet(-1, 0, 3, 3, 1, 9, 3, 3, 6),
            _pl_planet(0, 0, 3, 2, 1, 8, 2, 2),
            _pl_planet(1, 0, 3, 2, 1, 8, 2, 2),
            _pl_planet(2, 0, 3, 2, 1, 8, 4, 2),
            _pl_planet(-1, 1, 3, 3, 1, 9, 3, 3),
            _pl_planet(-1, 4, 3, 1, 2, 3, 1, 0, 10),
            _pl_planet(-1, 2, 0, 0, 0, 0, 0, 0),
            _pl_planet(-1, 2, 3, 4, 1, 9, 3, 3)]
        self.colonies_raw = [
            bytes(_pl_pack(_pl_cspec, owner=0, planet=1, climate=8)),
            bytes(_pl_pack(_pl_cspec, owner=1, planet=2, climate=8,
                           outpost_flag=1)),
            bytes(_pl_pack(_pl_cspec, owner=1, planet=3, climate=8))]
        self.player_raw = [_pl_player("Human", 1, _omniscient),
                           _pl_player("Klackon", 4)]
        self.ships_raw = [
            bytes(_pl_pack(_pl_shspec, owner=14, status=0, location=4)),
            bytes(_pl_pack(_pl_shspec, owner=0, status=0, location=2)),
            # A wreck: status >= 3 gets no stack node (shipstak.cpp:56)
            bytes(_pl_pack(_pl_shspec, owner=1, status=5, location=2))]
        self.fields = list(_fields)

# 2. THE ROW SET — the source's tests in the source's order.
_pl_view = _plr.View(_PlSnap())

def _pl_ids(_filters=None, _view=None):
    return [_r["index"] for _r in _plr.build_rows(_view or _pl_view,
                                                 _filters or {})]

assert _pl_ids() == [0, 3, 5, 7], _pl_ids()
assert _pl_ids({"gravity": True}) == [0, 3, 7], _pl_ids({"gravity": True})
assert _pl_ids({"enemy": True}) == [7], _pl_ids({"enemy": True})
assert _pl_ids({"hostile": True}) == [0, 3, 7]
assert _pl_ids({"minerals": True}) == [0, 3, 7]
assert _pl_ids(_view=_plr.View(_PlSnap(_omniscient=True))) == \
    [0, 3, 4, 5, 7], "omniscience does not reveal the unvisited planet"
# THE RANGE GAP, and the check that keeps it honest in both
# directions: the toggle changes nothing EXACTLY while it is marked.
_pl_range_inert = _pl_ids({"range": True}) == _pl_ids()
assert _pl_range_inert == ("range" in _plr.FILTER_GAPS), (
    "the Planets In Range filter and its MARKED GAP disagree: either "
    "the filter was built and FILTER_GAPS (and layout.json "
    "restrictions._gap_range, and the status document) still say it "
    "is missing, or the marking was removed while the list still "
    "ignores the toggle")
assert set(_plr.FILTER_GAPS) <= set(_plr.FILTERS)
_pl_T = [0] * _pl_plspec.TRAIT_COUNT
_pl_low, _pl_heavy = list(_pl_T), list(_pl_T)
_pl_low[_plr.TRAIT_LOW_G_WORLD] = 1
_pl_heavy[_plr.TRAIT_HEAVY_G_WORLD] = 1
assert [_plr.productivity_penalty(_pl_T, _g) for _g in (0, 1, 2)] == \
    [25, 0, 50]
assert [_plr.productivity_penalty(_pl_low, _g) for _g in (0, 1, 2)] == \
    [0, 25, 50]
assert [_plr.productivity_penalty(_pl_heavy, _g) for _g in (0, 1, 2)] \
    == [25, 0, 0]
_pl_rows = {_r["index"]: _r for _r in _plr.build_rows(_pl_view, {})}
assert {_i: _r["max_pop"] for _i, _r in _pl_rows.items()} == \
    {0: 20, 3: 12, 5: 3, 7: 25}, _pl_rows
assert _plr.monster_owner(_pl_view, 4) == 14
assert _plr.monster_owner(_pl_view, 2) is None
ok("planets row set: type before colony_index, own colonies and "
   "outposts out, visited or omniscient, four filters by the source, "
   "the range toggle inert exactly while marked, penalty table, max pop")

# 3. THE ORDER: descending, STABLE, and the rebuild-on-count rule.
assert _plr.SORT_VALUES == {_b["key"]: _b["value"] for _b in _hjson.load(
    open(os.path.join(SCREENS_DIR, "planets", "layout.json"),
         encoding="utf-8"))["sort"]["buttons"]}
_pl_list = _plr.PlanetList("size")

def _pl_order():
    return [_r["index"] for _r in _pl_list.rows]

assert _pl_list.refresh(_pl_view, {}) is True
assert _pl_order() == [7, 0, 3, 5], _pl_order()
_pl_list.sort("climate")
assert _pl_order() == [7, 0, 3, 5], (
    f"{_pl_order()}: 7 and 0 tie on climate and must keep the order "
    f"they had — the HD sort is stable (brief 101)")
_pl_list.sort("minerals")
assert _pl_order() == [3, 7, 0, 5], _pl_order()
assert _pl_list.refresh(_pl_view, {"range": True}) is False
assert _pl_order() == [3, 7, 0, 5], "an unchanged count re-sorted"
assert _pl_list.refresh(_pl_view, {"hostile": True}) is True
assert _pl_order() == [3, 0, 7], _pl_order()
assert _pl_list.first_row_of_star(2) == 2
assert _pl_list.first_row_of_star(3) == -1
ok("planets order: three keys descending, ties keep their order, a "
   "rebuild re-sorts only when the count changes (plntsum.cpp:1044)")

# 4. THE WORDS, through stub tables: every index is visible as E<hex>.
class _PlE:
    def string(self, _i):
        return f"E{_i:X}"

class _PlH:
    def __init__(self, _table):
        self._t = _table

    def message(self, _i):
        return self._t.get(_i)

_pl_H = {0x142: "-%d%% prod", 0x143: "%d max pop",
         0x152: "%d prod/worker", 325: "Black Hole", 148: "unexplored"}
_pl_words = _plw.Words(_PlE(), _PlH(_pl_H))
_pl_c0 = _plw.cells(_pl_view, _pl_rows[0], _pl_words)
assert _pl_c0["planet"] == {"special": "E2BF", "special_pending": False,
                            "name": "Alpha I", "owner": ""}, _pl_c0
assert (_pl_c0["climate"], _pl_c0["gravity"], _pl_c0["minerals"],
        _pl_c0["size"]) == (("E12F", "1.5 Food"), ("E2B0", None),
                            ("E1C2", "5 prod/worker"),
                            ("E168", "20 max pop")), _pl_c0
_pl_c3 = _plw.cells(_pl_view, _pl_rows[3], _pl_words)
assert _pl_c3["planet"]["name"] == "Alpha IV"
assert _pl_c3["planet"]["owner"] == "(Klackon)"
assert _pl_c3["planet"]["special"] == ""
_pl_c5 = _plw.cells(_pl_view, _pl_rows[5], _pl_words)
assert _pl_c5["planet"]["special_pending"] is True and \
    _pl_c5["planet"]["owner"] == "(E144)", _pl_c5
assert _pl_c5["gravity"] == ("E2B1", "-50% prod"), _pl_c5["gravity"]
assert _plw.cells(_pl_view, _pl_rows[7], _pl_words)["planet"][
    "name"] == "Gamma II", "the numeral counts OCCUPIED slots"
assert _plw.food_text(4) == "2" and _plw.food_text(-1) == "32767.5"
assert _plw.cells(_pl_view, _pl_rows[0], _plw.Words(_PlE(), _PlH({})))[
    "size"] == ("E168", "20"), "no HESTRNGS must still show the value"
assert _plw.status_line(_pl_view, None, _pl_words) is None
assert _plw.status_line(_pl_view, 1003, _pl_words) == ("Black Hole", "red")
assert _plw.status_line(_pl_view, 1001, _pl_words) == \
    ("unexplored", "neutral")
assert _plw.status_line(_pl_view, 1000, _pl_words) == ("Alpha", "neutral")
assert _plw.race_name(_pl_view, 8, _pl_words) == "E292"
assert _plw.race_name(_pl_view, 9, _pl_words) == "E293"
with _pl_tmp.TemporaryDirectory() as _pl_d:
    assert _pl_hs.HStrings("en", root=_pl_d).state == "missing"
    _pl_p = os.path.join(_pl_d, *_pl_hs.string_file("en").split("/"))
    os.makedirs(os.path.dirname(_pl_p))
    for _pl_body, _pl_state in (
            ({"format": 0, "strings": []}, "stale"),
            ({"format": _pl_hs.FORMAT_VERSION, "strings": ["x"] * 10},
             "missing"),
            ({"format": _pl_hs.FORMAT_VERSION, "strings": [
                str(_i) for _i in range(_pl_hs.HSTRINGS_COUNT)]}, "ok")):
        with open(_pl_p, "w", encoding="utf-8") as _fh:
            _hjson.dump(_pl_body, _fh)
        _pl_h = _pl_hs.HStrings("en", root=_pl_d)
        assert _pl_h.state == _pl_state, (_pl_body["format"], _pl_h.state)
    assert _pl_h.message(0x143) == str(0x143)
assert _pl_hs.printf("-%d%% prod", 25) == "-25% prod"
assert "hestrings_extract.py" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "setup.py"),
    encoding="utf-8").read()
ok("planets words: ESTRINGS/HESTRNGS indices, special line and its "
   "pending monster branch, owner and monster race, food, the bare "
   "value without HESTRNGS, status line, hestrings missing/stale/ok")

# 5. THE WIRE, recorded: what each control sends, and what sends
#    nothing. The fields carry the esc button and the "C" send field.
class _PlRec:
    class state:
        fields = []

    def __init__(self):
        self.log = []

    def activate_field(self, _fid):
        self.log.append(("act", _fid))

    def inject_click(self, _x, _y):
        self.log.append(("click", _x, _y))

    def inject_key(self, _k):
        self.log.append(("key", _k))

# FIELD 0 FIRST — the engine cannot send a list without one
# (FIELD_ZERO_ROW). Its hotkey is 0, which is what a lookup by
# hotkey has to survive: `_send_available` asks "is there a field
# with this key", and a slot 0 carrying a stale key would answer
# for a button the screen does not have.
_pl_fields = [_PlField(index=0, hotkey=0),
              _PlField(index=42, hotkey=27),
              _PlField(index=43, hotkey=ord("C"))]
for _pl_W, _pl_H2 in ((1920, 1080), (2560, 1440)):
    _pl_app, _ = _pv.build_screen(_pl_W, _pl_H2)
    _pl_rec = _PlRec()
    _pl_app.client = _pl_rec
    _pl_app.dispatcher.update_from_game(_PlSnap(_pl_fields))
    assert _pl_app.dispatcher.active_name == "planets", (
        "current_screen 32 does not route to the planets screen")
    _pl_scr = _pl_app.dispatcher.active
    assert isinstance(_pl_scr, _PlScreen)
    assert _pl_rec.log == [("click", 470, 212)], (
        f"entering did not impose the climate sort: {_pl_rec.log}")

    def _pl_c(_name):
        return pygame.Rect(*_pl_scr.layout.rect(
            _pl_scr.box_rect(_name))).center

    _pl_rec.log.clear()
    _pl_scr.handle_click(*_pl_c("return"))
    assert _pl_rec.log == [("act", 42)], _pl_rec.log
    _pl_rec.log.clear()
    assert _pl_scr._send_available("C") and \
        not _pl_scr._send_available("O")
    _pl_scr.handle_click(*_pl_c("send_colony"))
    assert _pl_rec.log == [], f"a send button sent {_pl_rec.log}"
    _pl_scr.handle_click(*_pl_c("sort_minerals"))
    assert _pl_rec.log == [("click", 533, 212)], _pl_rec.log
    assert [_r["index"] for _r in _pl_scr._list.rows] == [3, 0, 7, 5]
    _pl_rec.log.clear()
    _pl_scr.handle_click(*_pl_c("restrict_enemy"))
    assert _pl_rec.log == [("key", ord("1"))], _pl_rec.log
    assert [_r["index"] for _r in _pl_scr._list.rows] == [7]
    _pl_scr.handle_click(*_pl_c("restrict_enemy"))
    _pl_rec.log.clear()
    _pl_scr.handle_click(*_pl_c("restrict_range"))
    assert _pl_rec.log == [("key", ord("5"))], _pl_rec.log
    assert len(_pl_scr._list.rows) == 4
    # Hover selects and scans; leaving the rows keeps the scan.
    _pl_rows_rect = _pld.window(_pl_scr, "rows")
    _pl_scr.handle_mouse_motion(_pl_rows_rect.x + 10,
                                _pl_rows_rect.y + 5)
    _pl_first = _pl_scr._list.rows[0]
    assert _pl_scr._selected == _pl_first["index"] and \
        _pl_scr._scanned == _pl_first["star"] + 1000
    _pl_scr.handle_mouse_motion(1, 1)
    assert _pl_scr._hover is None and \
        _pl_scr._scanned == _pl_first["star"] + 1000
    # The wheel and the star click move the HD window and send nothing.
    _pl_scr._list.rows = _pl_scr._list.rows * 3
    _pl_rec.log.clear()
    assert _pl_scr.handle_mousewheel(-1, *_pl_rows_rect.center) is True
    assert _pl_scr._first == 1 and _pl_rec.log == []
    _pl_stars = _pl_scr._inset_stars()
    assert len(_pl_stars) == 5, _pl_stars
    _pl_inset = _pld.window(_pl_scr, "galaxy_inset")
    _pl_pts = _pld.colonyinset.star_points(
        _pl_stars, _pld.colonyinset.map_rect(_pl_inset, (180, 116)),
        (180, 116))
    _pl_scr.handle_click(*_pl_pts[4][:2])
    assert _pl_scr._first == _pl_scr._list.first_row_of_star(4) and \
        _pl_rec.log == [], (_pl_scr._first, _pl_rec.log)
    _pl_scr.update(_PlSnap(_pl_fields))
    _pl_scr.render(pygame.Surface((_pl_W, _pl_H2)))
_gm_layout = _hjson.load(open(os.path.join(
    SCREENS_DIR, "galaxy_map", "layout.json"), encoding="utf-8"))
assert {_b["key"]: _b["field_id"] for _b in _gm_layout["buttons"]}[
    "planets"] == 11, "the galaxy map's Planets button is not field 11"
ok("planets wire: 32 routes here, entry imposes the sort by click, "
   "RETURN by the esc field's id, sorts by click, restrictions by "
   "hotkey, send inert, hover scans, wheel and star click send nothing")

# 6. THE HELP TABLE — evanhelp.cpp:118, fifteen entries, NO fallback.
_pl_help = _hjson.load(open(os.path.join(
    SCREENS_DIR, "planets", "help.json"), encoding="utf-8"))
_pl_regs = _pl_help["regions"]
assert len(_pl_regs) == 15 and not any(_r.get("screen")
                                       for _r in _pl_regs)
_pl_hf, _pl_hl = _pl_help["_source"].split(":")
_pl_cpp = os.path.expanduser(os.path.join("~", "orion2re", "src",
                                          "game", _pl_hf))
if os.path.exists(_pl_cpp):
    _pl_tab = open(_pl_cpp, encoding="utf-8", errors="replace").read(
        ).split("\n")[int(_pl_hl) - 1:]
    _pl_body = "\n".join(_pl_tab)
    _pl_body = _pl_body[:_pl_body.index("};")]
    assert "_plntsum_screen_help_list" in _pl_tab[0], _pl_tab[0]
    _pl_src_rows = [tuple(int(_v) for _v in _m) for _m in _ch_re.findall(
        r"\{(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\}",
        _pl_body)]
    assert _pl_src_rows == [(_r["help_id"], *_r["native"])
                            for _r in _pl_regs], _pl_src_rows
else:
    report(f"planets help order NOT checked against the C++ table — "
           f"{_pl_cpp} is not on this disk")
for _pl_W, _pl_H2 in ((1280, 720), (1920, 1080), (2560, 1440),
                      (3840, 2160)):
    _pl_app, _ = _pv.build_screen(_pl_W, _pl_H2)
    _pl_app.dispatcher.switch_to("planets")
    _pl_scr = _pl_app.dispatcher.active
    _pl_scr.update(_PlSnap())
    for _r in _pl_regs:
        _pl_scr.help.close()
        _pl_pt = pygame.Rect(*_pl_scr.layout.rect(
            _pl_scr.box_rect(_r["box"]))).center
        assert _pl_scr.handle_right_button(True, *_pl_pt) is True and \
            _pl_scr.help.help_id == _r["help_id"], (
            f"{_pl_W}x{_pl_H2}: a right click on {_r['box']} opened "
            f"{_pl_scr.help.help_id}, evanhelp.cpp:118 gives "
            f"{_r['help_id']}")
    _pl_scr.help.close()
    assert _pl_scr.handle_right_button(True, 1, 1) is False, (
        "the planets table has no screen-wide entry, so a right click "
        "on the frame's corner must open nothing")
    # AND AN OPEN POPUP RENDERS. Found live in Stop 3: help_popup had
    # no rect, and the first right click that opened an entry crashed
    # render_help — every region above "answered" without ever being
    # drawn.
    _pl_scr.handle_right_button(True, *pygame.Rect(*_pl_scr.layout.rect(
        _pl_scr.box_rect("rows"))).center)
    assert _pl_scr.help.visible
    _pl_scr.render(pygame.Surface((_pl_W, _pl_H2)))
    assert _pl_scr.box_rect("help_popup") == (420, 170, 1080, 745) or \
        list(_pl_scr.box_rect("help_popup")) == [420, 170, 1080, 745]
    _pl_scr.help.close()
ok("planets help: 15 entries in evanhelp.cpp's order, no screen-wide "
   "fallback, every region answers on its own box at four sizes")

# 7. THE MARKINGS, each with the behaviour it describes.
_pl_lay = _hjson.load(open(os.path.join(
    SCREENS_DIR, "planets", "layout.json"), encoding="utf-8"))
assert _pl_lay["panel"]["_hd_extension_panel"].startswith(
    "HD EXTENSION: panel")
assert "HD EXTENSION: panel" in (_pld.render_planet_panel.__doc__ or "")
assert {_b["name"] for _b in _pl_boxdoc["1920x1080"]
        if _b["name"].startswith("planet_")} == {
    "planet_panel", "planet_disc", "planet_name", "planet_special"}, (
    "the bottom-left window shows only what the row already has — a "
    "new planet_* box is a new value, and Data's decision was none")
assert "HD EXTENSION" in _pl_lay["list"]["_hd_extension_wheel"]
assert "_hd_extension_wheel" in (_PlScreen.handle_mousewheel.__doc__
                                 or "")
assert "MARKED GAP" in _pl_lay["restrictions"]["_gap_range"]
assert "Planets In Range is a marked gap" in open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read()
assert "HD EXTENSION" in _pl_lay["list"]["_hd_extension_fills"]
# THE FILLS ARE listgrid's, measured in a rendered frame: the hovered
# row wears row_selected and the next one row_b.
_pl_app, _ = _pv.build_screen(1920, 1080)
_pl_app.dispatcher.switch_to("planets")
_pl_scr = _pl_app.dispatcher.active
_pl_scr.update(_PlSnap())
_pl_rr = _pld.window(_pl_scr, "rows")
_pl_scr.handle_mouse_motion(_pl_rr.x + 10, _pl_rr.y + 5)
_pl_surf = pygame.Surface((1920, 1080))
_pl_scr.render(_pl_surf)
_pl_cols = _pld.columns(_pl_scr, _pl_scr._data["list"])
_pl_bands = _pl_lg.all_bands(_pl_rr, 8)
_pl_a, _pl_b, _pl_sel = _pl_lg.row_palette()[:3]
for _pl_band, _pl_want in ((0, _pl_sel), (1, _pl_b)):
    _pl_pt = (_pl_cols["climate"][0] + 4,
              _pl_bands[_pl_band][0] + _pl_bands[_pl_band][1] // 2)
    _pl_px = tuple(_pl_surf.get_at(_pl_pt))[:3]
    # Glass since work order 174: listgrid's fill AT THAT PLACE.
    _pl_exp = _pl_lg.fill_colour_at((1920, 1080), _pl_cols, (),
                                    _pl_bands[_pl_band], _pl_want,
                                    _pl_band == 0, _pl_pt)
    assert _pl_px == _pl_exp, (
        f"band {_pl_band} is {_pl_px}, listgrid's fill there is {_pl_exp}")
ok("planets markings: the panel shows only disc/name/special, the "
   "wheel and fills are marked HD EXTENSION and drawn, the range gap "
   "is marked in layout.json and the status document")

# THE HOVERED ROW IS THE DRAWN ROW, on every pixel line (work order 128
# D, decision 5). Hover divided the window proportionally while the rows
# were drawn as h // n with the remainder on the last band, and the two
# named different rows on single lines. Two claims, because one shared
# function guarantees agreement and not correctness:
#   1. at every device row y of the list, the hovered row is the row
#      whose band `row_bands` draws at y — no render needed, so EVERY
#      line is swept;
#   2. against what is visible: at the first and last line of every
#      drawn band (where the two arithmetics disagreed), a rendered frame
#      shows `row_selected` at that y — the hover lit the row the pixel
#      is in.
_hv_lines = 0
for _hv_W, _hv_H in ((1366, 768), (1920, 1080), (2560, 1440), (3840, 2160)):
    _hv_app, _ = _pv.build_screen(_hv_W, _hv_H)
    _hv_app.dispatcher.switch_to("planets")
    _hv_scr = _hv_app.dispatcher.active
    _hv_scr.update(_PlSnap())
    _hv_area = _pld.window(_hv_scr, "rows")
    _hv_bands = _pld.row_bands(_hv_scr)
    _hv_n = len(_hv_scr._list.rows)
    assert _hv_n >= 3 and len(_hv_bands) == _hv_scr.visible, (_hv_n, _hv_bands)
    for _hv_y in range(_hv_area.top, _hv_area.bottom):
        _hv_scr.handle_mouse_motion(_hv_area.x + 10, _hv_y)
        _hv_drawn = next((_i for _i, (_t, _h) in enumerate(_hv_bands)
                          if _t <= _hv_y < _t + _h), None)
        _hv_want = (_hv_scr._first + _hv_drawn
                    if _hv_drawn is not None
                    and _hv_scr._first + _hv_drawn < _hv_n else None)
        assert _hv_scr._hover == _hv_want, (
            f"{_hv_W}x{_hv_H} y={_hv_y}: hover {_hv_scr._hover}, the "
            f"row drawn there {_hv_want}")
        _hv_lines += 1
    _hv_surf = pygame.Surface((_hv_W, _hv_H))
    _hv_cols = _pld.columns(_hv_scr, _hv_scr._data["list"])
    _hv_sel = tuple(_pl_lg.row_palette()[2])[:3]
    for _hv_i, (_hv_t, _hv_h) in enumerate(_hv_bands[:_hv_n]):
        for _hv_y in (_hv_t, _hv_t + _hv_h - 1):
            _hv_scr.handle_mouse_motion(_hv_area.x + 10, _hv_y)
            _hv_scr.render(_hv_surf)
            # One px into the cell: the band's edge line is the cell
            # plate's own line everywhere but its CUT CORNER, where the
            # fill shows. It was 4 px in while the plate was a rounded
            # rect of radius 6; the HUD outline (decision 71) cuts its
            # corners by ~3 px at 1366x768, so 4 px landed on the line.
            _hv_pt = (_hv_cols["climate"][0] + 1, _hv_y)
            _hv_px = tuple(_hv_surf.get_at(_hv_pt))[:3]
            # Glass since work order 174: the hovered fill AT THAT PLACE.
            _hv_exp = _pl_lg.fill_colour_at((_hv_W, _hv_H), _hv_cols, (),
                                            (_hv_t, _hv_h), _hv_sel, True,
                                            _hv_pt)
            assert _hv_px == _hv_exp, (
                f"{_hv_W}x{_hv_H} y={_hv_y} (band {_hv_i}): the pixel "
                f"shows {_hv_px}, the hovered row's fill there is {_hv_exp}")
ok(f"planets: the hovered row is the drawn row on all {_hv_lines} pixel "
   f"lines at four sizes, and a band's edge lines light that band")
