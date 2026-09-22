# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 059_core_ship_weapons_end_at_the_first.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 19 check(s) it holds:
#   - ship weapons end at the first empty slot, as the fleet screen's list does (flt2.cpp:693-701); a 
#   - ship spec: design block and weapon records verified, inside 129 bytes without overlaps, the dama
#   - monster hull table == initship.cpp, techdata.cpp and orion2_consts.h (tools/monster_hull_check.p
#   - 
#   - monster panel: drawn for the guarded row with the switch on, the picture window unchanged with i
#   - monster values markings: HD EXTENSION in the module and layout.json, DEVIATION at the sprite cho
#   - ship part names and MAINTEXT descriptions: first strings from the game's counts, the 600-byte re
#   - help popup (auto-size, scroll, draws)
#   - help: missing file and missing id say different things
#   - help file path: loader, extractor and setup agree (3 languages)
#   - no smoke check reaches a derived loader by accident: constructions, every one through the stand-
#   - one construction site each for HStrings and HelpText in the running tree, by ast: core/hestrings
#   - the derived stand-ins are current byte for byte ( files), each carries the FORMAT_VERSION its lo
#   - every extractor is on setup.py's registry or excepted with a tracked output ( extractors, regist
#   - core/lbx.py (container, both frame formats agreeing, 6-bit palette, index 0 transparent, unpalet
#   - tools/make_nebula_icons.py reads FONTS.LBX entries as (flag, R, G, B), pinned with a non-zero fl
#   - help format codes decoded (columns, breaks, no control chars)
#   - help table columns scale with the panel, not with pixels
#   - help: a stale help file is refused, not rendered


# WEAPON SLOTS END AT THE FIRST EMPTY ONE (work order 128 E),
# transcribed from the fleet screen's list (flt2.cpp:693-701), which
# stops for good at `type < 0 || count < 1`. A constructed ship with a
# gap: the weapon after the gap is not listed; a used type with count 0
# ends the list as well; a contiguous design lists every slot.
from core.structs import ship as _ws
import struct as _ws_struct

def _ws_ship(slots):
    raw = bytearray(_ws.SIZE)
    for _i in range(_ws.WEAPON_SLOTS):
        _t, _c = slots[_i] if _i < len(slots) else (-1, 0)
        _ws_struct.pack_into("<hbb", raw, _ws.WEAPONS_OFFSET
                             + _i * _ws.WEAPON_SIZE, _t, _c, _c)
    return _ws.parse(bytes(raw))
assert [(_w.type, _w.count) for _w in _ws.weapons(
    _ws_ship([(5, 2), (-1, 0), (7, 1)]))] == [(5, 2)]
assert [(_w.type, _w.count) for _w in _ws.weapons(
    _ws_ship([(5, 2), (6, 0), (7, 1)]))] == [(5, 2)]
assert [(_w.type, _w.count) for _w in _ws.weapons(
    _ws_ship([(-1, 3), (7, 1)]))] == []
assert [(_w.type, _w.count) for _w in _ws.weapons(
    _ws_ship([(5, 2), (6, 4), (7, 1)]))] == [(5, 2), (6, 4), (7, 1)]
assert "flt2.cpp:693-701" in _ws.weapons.__doc__
ok("ship weapons end at the first empty slot, as the fleet screen's list "
   "does (flt2.cpp:693-701); a weapon after a gap is not listed")

# ── 8. THE MONSTER VALUES IN THE PICTURE WINDOW — fundament 64 ────
from core import maintext as _mmt
from core import monsterhull as _mh
from core import shipparts as _msp
from core import usersettings as _mus
from core import zoomtables as _mzt
from core.layout import Layout as _MLayout
from core.structs import ship as _msh
from screens.planets import monsterpanel as _mp
import fixtures as _mfx
import maintext_extract as _mme
import monster_hull_check as _mhc
import techname_extract as _mte
import tempfile as _mtmp

# 8a. THE SPEC. The design block and the weapon records are verified
#     (header compile plus the live probe, ship.py's docstring), lie
#     inside the 129 bytes without overlapping, and the damage fields
#     are NOT declared: a monster's zeros confirm no offset.
assert _msh.SPEC.verified and _msh.WEAPON_SPEC.verified
_m_spans = sorted((_o, _o + _Spec.kind_width(_k), _n)
                  for _n, _o, _k in _msh.SPEC.fields)
for (_a0, _a1, _an), (_b0, _b1, _bn) in zip(_m_spans, _m_spans[1:]):
    assert _a1 <= _b0, f"s_ship_data spec: {_an} overlaps {_bn}"
assert _m_spans[-1][1] <= _msh.SIZE
_mo = {_n: _o for _n, _o, _k in _msh.SPEC.fields}
assert _msh.WEAPONS_OFFSET + _msh.WEAPON_SLOTS * _msh.WEAPON_SIZE == \
    _mo["picture_num"], "the eight weapon records must end at picture_num"
assert sum(_Spec.kind_width(_k) for _n, _o, _k in
           _msh.WEAPON_SPEC.fields) == _msh.WEAPON_SIZE
assert not set(_mo) & {"armor_damage", "structural_damage",
                       "shield_damage_percent", "drive_damage_percent",
                       "computer_damage"}, (
    "a damage field was declared; it stays UNVERIFIED and unread")
ok("ship spec: design block and weapon records verified, inside 129 "
   "bytes without overlaps, the damage fields undeclared")

# 8b. THE HULL TABLE IS HELD TO THE SOURCE by the checker.
_m_tree = _mhc.find_tree(["smoke"])
if _m_tree is not None:
    _m_diff = _mhc.compare(_mhc.read_source(_m_tree))
    assert _m_diff == [], f"core/monsterhull.py disagrees: {_m_diff}"
else:
    report("monster hull table NOT checked against initship.cpp — no "
           "orion2re tree on this disk")
assert (_mh._cdiv(-3000, 100), _mh._cdiv(-7, 2), _mh._cdiv(7, 2)) == \
    (-30, -3, 3), "C division truncates toward zero"
ok("monster hull table == initship.cpp, techdata.cpp and "
   "orion2_consts.h (tools/monster_hull_check.py)")

# 8c. A GUARDED SYSTEM GIVES EXACTLY WHAT THE TEMPLATE AND THE TABLE
#     SAY. Expectations typed from SHIP_CONFIG (ship_config.cpp:51-139,
#     the count is SHIP_WEAPON's last argument) and Get_Ship_Structure_
#     / Get_Design_Structure_ / Get_Ship_Armor_Hits_ — never from the
#     module under test.
_m_expect = {
    9: (None, 4, 3, 800, 800, [(11, 2), (4, 10), (20, 1), (20, 1),
                                (13, 2)], [1, 3, 5, 13, 18, 19, 21, 25]),
    10: ("start", 2, 0, 400, 0, [(45, 1)], [39]),
    11: ("start", 2, 0, 500, 0, [(42, 1), (25, 5)], []),
    12: ("start", 2, 0, 500, 0, [(41, 8), (40, 1)], []),
    13: ("start", 2, 0, 300, 0, [(44, 1)], [19]),
    14: ("start", 2, 0, 500, 0, [(43, 3)], [10]),
}
_m_cfg = _pl_lay["monster_values"]
_m_words = _plw.Words(_PlE(), _PlH({157: "Weapons:", 158: "Specials:",
                                    159: "None"}))

class _MParts:
    def name(self, _table, _i):
        return f"{_table}{int(_i)}"

def _m_check(_ship, _parts=None):
    _stage, _size, _shield, _st, _ar, _wp, _spc = _m_expect[_ship.owner]
    _v = _mp.values(_pl_view, _ship, _m_words, _parts or _MParts(),
                    _m_cfg)
    assert _mh.stage(_ship) == _stage, (_ship.owner, _mh.stage(_ship))
    _want = {
        "monster_type": _plw.race_name(_pl_view, _ship.owner, _m_words),
        "monster_stage": _m_cfg["stage"][_stage] if _stage else "",
        "monster_size": f"hulls{_size}",
        "monster_structure": _m_cfg["structure"] % _st,
        "monster_armour": _m_cfg["armour"] % _ar,
        "monster_shield": f"shields{_shield}",
        "monster_weapons": ["Weapons:"] + [f"weapons{_t}"
                                           for _t, _n in _wp],
        "monster_weapon_counts": [""] + [_m_cfg["count"] % _n
                                         for _t, _n in _wp],
        "monster_specials": ["Specials:"] + (
            [f"specials{_i}" for _i in _spc] or ["None"]),
    }
    assert _v == _want, (_ship.owner, _v, _want)
    return _v

def _m_pack(_owner, _location, _size, _weapons, _flags=(0,) * 5):
    _b = bytearray(_msh.SIZE)
    _b[_mo["size"]] = _size
    _b[_mo["special_device_flags"]:_mo["special_device_flags"] + 5] = \
        bytes(_flags)
    for _slot, (_t, _n) in enumerate(_weapons):
        _pl_struct.pack_into("<hbbbHb", _b, _msh.WEAPONS_OFFSET
                             + _slot * _msh.WEAPON_SIZE, _t, _n, _n,
                             15, 0, 0)
    _b[_mo["previous_owner"]] = _owner
    _pl_struct.pack_into("<bbh", _b, _mo["owner"], _owner, 0, _location)
    return bytes(_b)

_m_hydra = _m_pack(14, 4, 2, [(43, 3)], (0, 0x04, 0, 0, 0))
_m_check(_msh.parse(_m_hydra))
_m_recs, _m_why = _mfx.fixture_ships("reference")
if _m_recs is None:
    report(f"monster values NOT checked on the reference save — {_m_why}")
else:
    _m_all = _msh.parse_all(_m_recs)
    _m_mon = [_s for _s in _m_all
              if _msh.is_monster(_s.owner) and _s.status == 0]
    assert sorted({int(_s.owner) for _s in _m_mon}) == [9, 10, 11, 12, 14]

    class _MView:
        ships = _m_all
    for _s in _m_mon:
        _m_check(_s)
        _g = _mp.guard(_MView, _s.location)
        assert _g is not None and _g.index <= _s.index
with _mtmp.TemporaryDirectory() as _m_d:
    _m_none = _msp.ShipPartNames("en", root=_m_d)
    assert _m_none.state == "missing"
    _m_v = _mp.values(_pl_view, _msh.parse(_m_hydra), _m_words, _m_none,
                      _m_cfg)
    assert _m_v["monster_weapons"][1] == _m_cfg["unnamed"] % 43, _m_v
ok("monster values: a guarded system gives exactly the template's size, "
   "shield, weapons and specials and the hull table's structure and "
   "armour" + ("" if _m_recs is None else
               f" — all {len(_m_mon)} monsters of the reference save") +
   "; no names file shows numbers")

# 8d. ON SCREEN: drawn for the scanned guarded row while the switch is
#     on; with it off the picture window is pixel for pixel the one a
#     row without a monster draws; nothing on the wire; sprites from
#     the masters at the DERIVED size, none for the amoeba, and the 4K
#     box inside the export so the panel only scales down.
class _MSnap(_PlSnap):
    def __init__(self):
        super().__init__()
        self.ships_raw = [_m_hydra] + list(self.ships_raw[1:])

_m_app, _ = _pv.build_screen(1920, 1080)
_m_rec = _PlRec()
_m_app.client = _m_rec
with _mtmp.TemporaryDirectory() as _m_d:
    _m_app.user_settings = _mus.UserSettings(
        path=os.path.join(_m_d, "user_settings.json"))
    _m_app.dispatcher.switch_to("planets")
    _m_scr = _m_app.dispatcher.active
    _m_scr.update(_MSnap())
    _m_rec.log.clear()
    _m_rows = {_r["star"]: _r for _r in _m_scr._list.rows}
    _m_said = []
    _m_rt = _m_app.style.render_text
    _m_app.style.render_text = lambda _t, *_a, **_k: (
        _m_said.append(_t), _m_rt(_t, *_a, **_k))[1]
    _m_pp = _pld.window(_m_scr, "picture_panel")

    def _m_frame(_star):
        _m_scr._selected = _m_rows[_star]["index"]
        _m_said.clear()
        _s = pygame.Surface((1920, 1080))
        _m_scr.render(_s)
        return pygame.image.tostring(_s.subsurface(_m_pp), "RGB")

    try:
        _m_on = _m_frame(4)
        assert _m_cfg["structure"] % 500 in _m_said and \
            _m_cfg["armour"] % 0 in _m_said, _m_said
        assert _mp.render(_m_scr, pygame.Surface((1920, 1080)),
                          _m_rows[4]) is True
        _m_empty = _m_frame(0)
        assert _m_on != _m_empty, "the panel drew nothing for the Hydra"
        _m_app.user_settings.set("monster_values", "off")
        assert _m_frame(4) == _m_empty, (
            "with the switch off the picture window must be the one a "
            "row without a monster draws")
        assert _m_cfg["structure"] % 500 not in _m_said
        assert _mp.render(_m_scr, pygame.Surface((1920, 1080)),
                          _m_rows[4]) is False
    finally:
        _m_app.style.render_text = _m_rt
    assert _m_rec.log == [], f"the monster panel sent {_m_rec.log}"
    for _owner, _kind in sorted(_mp.galaxy_ships.MONSTER_KINDS.items()):
        if not _msh.is_monster(_owner):
            continue
        _path = _mp.sprite_path(_m_scr, _owner)
        if _kind == "amoeba":
            assert _path is None, "the amoeba has no master and no sprite"
            continue
        assert _path, f"no panel sprite for {_kind}"
        _img = pygame.image.load(_path)
        assert max(_img.get_size()) == _mzt.MONSTER_PANEL_SPRITE_PX, (
            _kind, _img.get_size())
_m_4k = _MLayout(3840, 2160).scale
for _m_res, _m_list in _pl_boxdoc.items():
    _m_by = {_b["name"]: _b for _b in _m_list}
    assert set(_mp.BOXES) <= set(_m_by), (_m_res, set(_mp.BOXES) - set(_m_by))
    assert not {"monster_picture", "monster_race"} & set(_m_by)
    _m_sb = _m_by[_mp.SPRITE_BOX]["rect"]
    assert max(_m_sb[2], _m_sb[3]) * _m_4k <= _mzt.MONSTER_PANEL_SPRITE_PX, (
        f"{_m_res}: the sprite box {_m_sb} is larger at 4K than the "
        f"{_mzt.MONSTER_PANEL_SPRITE_PX} px export — re-derive the export")
ok("monster panel: drawn for the guarded row with the switch on, the "
   "picture window unchanged with it off, no wire traffic, sprites at "
   "the derived size from the masters and none for the amoeba, the 4K "
   "box inside the export")

# 8e. THE MARKINGS, THE SWITCH'S DEFAULT, AND THE FUNDAMENT ENTRY.
assert (_mp.__doc__ or "").lstrip().startswith(
    "The monster guarding a system") and "HD EXTENSION" in _mp.__doc__
assert "DEVIATION" in (_mp.sprite_path.__doc__ or "")
assert _m_cfg["_hd_extension"].startswith("HD EXTENSION")
assert _m_cfg["_deviation_sprite"].startswith("DEVIATION")
assert _mus.DEFAULTS["monster_values"] == "on"
_m_fund = read_doc(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                "v3_fundament.md"))
assert "**64. " in _m_fund and "star index % 5" in _m_fund, (
    "fundament 64 does not carry the entry or the sprite deviation")
ok("monster values markings: HD EXTENSION in the module and layout.json, "
   "DEVIATION at the sprite choice, switch default on, fundament 64")

# 8f. THE NAMES AND THE DESCRIPTIONS, both decision 38's pattern.
assert (_msp.SPECIAL_FIRST_STRING, _msp.ARMOR_FIRST_STRING,
        _msp.SHIELD_FIRST_STRING, _msp.WEAPON_FIRST_STRING,
        _msp.HULL_FIRST_STRING) == (344, 384, 391, 397, 542)
_m_rec600 = _pl_struct.pack("<HH", 1, _mmt.RECORD_SIZE) + \
    b"Space \x82\x00junk".ljust(_mmt.RECORD_SIZE, b"\x00")
assert _mme.parse_entry(_m_rec600) == "Space é"
assert _mme.parse_entry(_pl_struct.pack("<HH", 1, 0x57B) + bytes(0x57B)) \
    is None
with _mtmp.TemporaryDirectory() as _m_d:
    for _m_loader, _m_rel, _m_ok in (
            (_msp.ShipPartNames, _msp.name_file("en"),
             {_k: {"0": "x"} for _k in _msp.TABLES}),
            (_mmt.MainText, _mmt.text_file("en"),
             {"entries": {"0": "No Special"}})):
        assert _m_loader("en", root=_m_d).state == "missing"
        _m_p = os.path.join(_m_d, *_m_rel.split("/"))
        os.makedirs(os.path.dirname(_m_p), exist_ok=True)
        for _m_body, _m_state in (({"format": 0}, "stale"),
                                  (dict(_m_ok, format=1), "ok")):
            with open(_m_p, "w", encoding="utf-8") as _fh:
                _hjson.dump(_m_body, _fh)
            assert _m_loader("en", root=_m_d).state == _m_state, (
                _m_loader, _m_body)
# AGAINST THE PLAYER'S OWN FILES when they are on this disk: the first
# string of every table is its "No ..." entry, and entry 0 of MAINTEXT
# is "No Special" — the sums are right or the words say so.
from core import lbx as _mlbx
_m_tn = os.path.expanduser("~/Master of Orion 2/TECHNAME.LBX")
if os.path.exists(_m_tn):
    _m_str = [_mte.decode(_x) for _x in _mte.split_block(
        _mlbx.read_entry(_m_tn, 0))]
    assert [_m_str[_i] for _i in (344, 384, 391, 397, 542)] == [
        "No Special", "No Armor", "No Shield", "No Weapons", "Frigate"], \
        [_m_str[_i] for _i in (344, 384, 391, 397, 542)]
else:
    report(f"ship part indices NOT checked against a TECHNAME.LBX — "
           f"{_m_tn} is not on this disk")
_m_mtx = _mme.find_lbx(None, "en")
if _m_mtx:
    _m_ent, _m_skip = _mme.extract(_m_mtx)
    assert len(_m_ent) == 14 and _m_ent[0] == "No Special" and \
        _m_skip == 0, (len(_m_ent), _m_ent.get(0), _m_skip)
else:
    report("MAINTEXT.LBX NOT parsed — not in ~/Master of Orion 2")
_m_setup = open(os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                             "setup.py"), encoding="utf-8").read()
assert "maintext_extract.py" in _m_setup and "shipparts_file" in _m_setup
ok("ship part names and MAINTEXT descriptions: first strings from the "
   "game's counts, the 600-byte record parse, missing/stale/ok loaders, "
   "both named in setup.py")

_pop = _HelpPopup()
_box = (430, 200, 1060, 680)
_pop.open(1, "Short", "One line.")
_pop.render(surf, app.layout, app.style, _box, 1.0)
assert _pop._max_scroll == 0, _pop._max_scroll
_pop.open(2, "Long", "\n".join(f"Line {i} of a long help entry "
                               "that has to keep going."
                               for i in range(80)))
_pop.render(surf, app.layout, app.style, _box, 1.0)
assert _pop._max_scroll > 0, "a long entry must scroll"
_before = _pop._scroll
_pop.handle_wheel(-1)
assert _pop._scroll > _before, (_before, _pop._scroll)
_pop.handle_wheel(50)
assert _pop._scroll == 0, _pop._scroll
# It also has to actually draw: an empty panel and a missing one
# look the same on screen.
_blank = pygame.Surface((1920, 1080))
_drawn = pygame.Surface((1920, 1080))
_pop.close()
_pop.render(_drawn, app.layout, app.style, _box, 1.0)
assert (pygame.surfarray.array3d(_blank)
        == pygame.surfarray.array3d(_drawn)).all(), \
    "a closed popup drew something"
_pop.open(3, "Title", "Body.")
_pop.render(_drawn, app.layout, app.style, _box, 1.0)
assert not (pygame.surfarray.array3d(_blank)
            == pygame.surfarray.array3d(_drawn)).all(), \
    "an open popup drew nothing"
ok("help popup (auto-size, scroll, draws)")

# Two different faults produce the same empty box: no help file at
# all, and a file that lacks this one id. Only the first is fixed
# by running the extractor, so they must not share a message.
# Both states are forced rather than read off disk — this test has
# to give the same answer before and after the user extracts.
from core.helptext import HelpText   # not aliased: piece 3's rule
_ht = HelpText(res, "en")
_ht._entries, _ht._available, _ht._stale = {}, False, False
_no_file = _ht.missing_entry(288)
_ht._entries, _ht._available = {1: {"title": "x", "body": "y"}}, True
_no_id = _ht.missing_entry(288)
assert _no_file != _no_id, _no_file
assert "help_extract" in _no_file[1], _no_file[1]
assert "288" in _no_id[1], _no_id[1]
assert "help_extract" not in _no_id[1], _no_id[1]
ok("help: missing file and missing id say different things")

# Three places touch that file: core.helptext builds the path the
# loader reads, help_extract.py writes it, setup.py reports
# whether it is there. They were three independent spellings, and
# setup's was a hardcoded help_en.json — so a non-English install
# was told to run an extractor it had already run correctly, and
# an English file under a German setting was reported ok while
# every popup showed a placeholder. Asserted per language rather
# than for one, because "en" is exactly the value under which the
# bug is invisible.
import importlib.util as _ilu
from core.helptext import help_file as _help_file
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = _ilu.spec_from_file_location(
    "_setup_mod", os.path.join(_root, "tools", "setup.py"))
_setup = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_setup)
for _lang in ("en", "de", "fr"):
    _want = os.path.join(_root, *_help_file(_lang).split("/"))
    _path, _what, _cmd = _setup.from_game({"language": _lang})[0]
    assert _path == _want, (_lang, _path, _want)
    # The command has to be runnable as printed: an install on a
    # non-default language needs --lang, or following the advice
    # writes a file the loader will not read.
    assert _lang == "en" or ("--lang " + _lang) in _cmd, _cmd
    assert "placeholder" in _what, _what
# The extractor writes the file the loader reads.
_espec = _ilu.spec_from_file_location(
    "_extract_mod", os.path.join(_root, "tools", "help_extract.py"))
_extract = _ilu.module_from_spec(_espec)
_espec.loader.exec_module(_extract)
for _lang in ("en", "de"):
    _written = os.path.join(_extract.OUT_DIR,
                            os.path.basename(_help_file(_lang)))
    assert _written == os.path.join(
        _root, *_help_file(_lang).split("/")), _written
ok("help file path: loader, extractor and setup agree (3 languages)")

# ── EVERY EXTRACTOR IS ON THE REGISTRY, OR SAYS WHY NOT ───────
#
# **THE FOURTH TIME A CHECK PASSED HERE AND WENT RED IN A CLONE**
# — 13 September (`d3d0561`), twice in one run (`5402b7d`) and
# 20 September (`58b2808`). `tools/setup.py:from_game()` is the
# one list of files derived from the player's own installation:
# it is what tells a clone which extractor to run, and anything
# else keyed on that list inherits its holes.
#
# It had two, found by writing this check on 20 September 2026:
# `kentext_en.json`, which `ArcWords` reads for the Fleets
# panel's firing arcs, and the Fleets gamedata that `fltart`
# reads for the ship pictures. Neither had ever been reported
# absent, so a clone was never told to run either extractor.
#
# The rule is two-way, like the over-300-lines list: every
# extractor is named by a registry command, or is on the
# exception list AND its output is really tracked — because an
# exception that is wrong puts the hole back.
import subprocess as _reg_sp

#: Extractors whose output is COMMITTED, so a clone already has
#: it and it is not a "derived from the player's install" file.
#: The value is one file the tool writes, and it is checked.
_EXTRACT_COMMITTED = {
    # Data's own sheet, not the player's MOO2: ten planet discs
    # cut out of ~/Downloads/planets.png and committed.
    "planet_extract.py":
        "screens/colony_summary/assets/planets/gaia.png",
}
_reg_cmds = " ".join(_c for _p, _w, _c in _setup.from_game())
_extractors = sorted(
    _f for _f in os.listdir(os.path.join(_root, "tools"))
    if _f.endswith("_extract.py"))
assert len(_extractors) >= 10, _extractors
_reg_unlisted = [_t for _t in _extractors
                 if _t not in _EXTRACT_COMMITTED
                 and _t not in _reg_cmds]
assert not _reg_unlisted, (
    f"{_reg_unlisted} write files nobody registers: they are in "
    f"neither tools/setup.py's from_game() nor the committed-output "
    f"exception list. A clone is never told to run them, setup.py "
    f"never reports their files absent, and any check keyed on that "
    f"list has a hole exactly their size")
for _t, _out in sorted(_EXTRACT_COMMITTED.items()):
    assert _t in _extractors, (
        f"{_t} is on the committed-output list and is not an "
        f"extractor any more")
    assert _t not in _reg_cmds, (
        f"{_t} is BOTH registered in from_game() and excepted as "
        f"committed; one of the two is wrong")
    _reg_r = _reg_sp.run(["git", "ls-files", "--error-unmatch", _out],
                         cwd=_root, capture_output=True, text=True)
    assert _reg_r.returncode == 0, (
        f"{_t} is excepted because its output is committed, and "
        f"{_out} is not tracked. The exception is wrong and the "
        f"file belongs in from_game()")
#    and the registry's own paths are distinct — a copy-paste that
#    registers one file twice hides the other one
_reg_paths = [_p for _p, _w, _c in _setup.from_game()]
assert len(set(_reg_paths)) == len(_reg_paths), (
    f"from_game() registers a path twice: "
    f"{sorted(_p for _p in _reg_paths if _reg_paths.count(_p) > 1)}")

# ── THE STAND-INS ARE CURRENT, AND EVERY SITE USES THEM ──────
#
# Piece 2 of the clone-only fault. The stand-ins are what a check
# gets instead of the player's extraction; they are generated
# from the loaders' OWN constants and carry the same
# `FORMAT_VERSION` the loader refuses on, so a format bump that
# forgets them fails here rather than in a clone six commits
# later.
import importlib.util as _sf_ilu2
_sf_spec2 = _sf_ilu2.spec_from_file_location(
    "_derived_fixtures", os.path.join(_root, "tools",
                                      "make_derived_fixtures.py"))
_sfx = _sf_ilu2.module_from_spec(_sf_spec2)
_sf_spec2.loader.exec_module(_sfx)

#  1. WHAT IS ON DISK IS WHAT THE GENERATOR MAKES — byte for byte,
#     which is the same licence decision 40 gives derived artwork.
_sfx_stale = []
for _sfx_rel, _sfx_doc in sorted(_sfx.files().items()):
    _sfx_path = os.path.join(_sfx.DERIVED_ROOT, *_sfx_rel.split("/"))
    _sfx_want = _sjson.dumps(_sfx_doc, indent=2) + "\n"
    if not os.path.exists(_sfx_path):
        _sfx_stale.append((_sfx_rel, "missing"))
    elif io.open(_sfx_path, encoding="utf-8").read() != _sfx_want:
        _sfx_stale.append((_sfx_rel, "stale"))
assert not _sfx_stale, (
    "the committed stand-ins are out of date: "
    + "; ".join(f"{_f}: {_w}" for _f, _w in _sfx_stale)
    + ". Run `python tools/make_derived_fixtures.py`")
assert len(_sfx.files()) >= 8, sorted(_sfx.files())

#  2. AND EACH CARRIES THE FORMAT THE LOADER DEMANDS. The version
#     is read off the loader module, so bumping one without
#     regenerating is caught at the bump.
from core import billtext as _sfx_bt, buildnames as _sfx_bn
from core import estrings as _sfx_es, hestrings as _sfx_hs
from core import kentext as _sfx_kt, maintext as _sfx_mt
from core import shipparts as _sfx_sp, technames as _sfx_tn
for _sfx_mod in (_sfx_bt, _sfx_bn, _sfx_es, _sfx_hs, _sfx_kt,
                 _sfx_mt, _sfx_sp, _sfx_tn):
    _sfx_file = next(getattr(_sfx_mod, _n)("en")
                     for _n in ("string_file", "name_file",
                                "message_file", "text_file")
                     if hasattr(_sfx_mod, _n))
    _sfx_doc = _sjson.load(io.open(os.path.join(
        _sfx.DERIVED_ROOT, *_sfx_file.split("/")), encoding="utf-8"))
    assert _sfx_doc.get("format") == _sfx_mod.FORMAT_VERSION, (
        f"{_sfx_file} carries format {_sfx_doc.get('format')} and "
        f"{_sfx_mod.__name__}.FORMAT_VERSION is "
        f"{_sfx_mod.FORMAT_VERSION} — regenerate the stand-ins "
        f"with the bump, not after it")
    assert "STAND-IN" in (_sfx_doc.get("_comment") or ""), (
        f"{_sfx_file} lost the note saying it is not an extraction")

#  3. AND EVERY ONE OF THEM LOADS through the loader's own path,
#     which is the point of keeping the directory layout.
for _sfx_loader in (_sfx_bt.BillText, _sfx_bn.BuildingNames,
                    _sfx_es.EStrings, _sfx_hs.HStrings,
                    _sfx_kt.ArcWords, _sfx_mt.MainText,
                    _sfx_sp.ShipPartNames, _sfx_tn.TechNames):
    derived(_sfx_loader)

#  4. THE ALLOW-LIST: which checks may still read the PLAYER's
#     own extraction, and why. Each of these is ABOUT the
#     extraction — it pins a real string so a walk that slipped by
#     one index fails — and each is guarded by a `state` test, so
#     a clone skips it instead of failing.
_REAL_DERIVED_OK = {
    "BuildingNames": "pins 'Automated Factory' at id 7, which is "
                     "what catches a TECHNAME walk off by one",
    "EStrings": "pins three anchors from Option_String_'s switch, "
                "which is what catches the 4-byte header slip",
    "HelpText": "the help-file path check IS about the loader, "
                "the extractor and setup.py agreeing",
}
assert set(_REAL_DERIVED_OK) == {"BuildingNames", "EStrings",
                                 "HelpText"}, sorted(_REAL_DERIVED_OK)

# ── NO CHECK REACHES A DERIVED LOADER BY ACCIDENT ────────────
#
# Piece 3 of the clone-only fault, and the part that makes the
# rule enforceable instead of remembered. Every construction of a
# derived-data loader in this file has to be one of three things:
#
#   * `derived(Loader)`          — the committed stand-in;
#   * an explicit `root=`        — a scratch directory, which is
#                                  how a FORCED-ABSENT case is
#                                  written, or the stand-in root;
#   * a language that cannot exist ("zz") — the other way to force
#                                  absence;
#
# and anything else must be named in `_REAL_DERIVED_OK` with the
# reason it needs the player's own extraction.
#
# **READ WITH `ast`, NOT WITH A GREP.** A call can span lines and
# the first version of this rule was a line scan that could not
# see one. The alias is the other half: `Loader(...)` under
# another name is a construction no scan can attribute, so an
# aliasing import of one of these classes is refused outright.
import ast as _dl_ast

_DERIVED_LOADERS = {
    "BillText", "BuildingNames", "EStrings", "HStrings",
    "ArcWords", "MainText", "ShipPartNames", "TechNames",
    "HelpText",
}
#: A language the player cannot have extracted, which is how a
#: check forces the absent state without a temporary directory.
_DL_IMPOSSIBLE = {"zz"}

_dl_src = suite_source()
_dl_tree = _dl_ast.parse(_dl_src)

_dl_aliased = []
for _dl_node in _dl_ast.walk(_dl_tree):
    if isinstance(_dl_node, (_dl_ast.Import, _dl_ast.ImportFrom)):
        for _dl_a in _dl_node.names:
            if _dl_a.name in _DERIVED_LOADERS and _dl_a.asname:
                _dl_aliased.append(
                    f"line {_dl_node.lineno}: {_dl_a.name} as "
                    f"{_dl_a.asname}")
assert not _dl_aliased, (
    "a derived loader is imported under another name, which hides "
    "every construction of it from this check: "
    + "; ".join(_dl_aliased)
    + ". Import it under its own name and pass the class to "
      "`derived()`")

def _dl_name(_fn):
    """The class a Call is calling, if it is one of ours."""
    if isinstance(_fn, _dl_ast.Attribute):
        return _fn.attr
    if isinstance(_fn, _dl_ast.Name):
        return _fn.id
    return None

_dl_bad = []
_dl_seen = 0
for _dl_node in _dl_ast.walk(_dl_tree):
    if not isinstance(_dl_node, _dl_ast.Call):
        continue
    _dl_cls = _dl_name(_dl_node.func)
    if _dl_cls not in _DERIVED_LOADERS:
        continue
    _dl_seen += 1
    if _dl_cls in _REAL_DERIVED_OK:
        continue
    if any(_kw.arg == "root" for _kw in _dl_node.keywords):
        continue
    if any(isinstance(_a, _dl_ast.Constant)
           and _a.value in _DL_IMPOSSIBLE for _a in _dl_node.args):
        continue
    _dl_bad.append(f"line {_dl_node.lineno}: {_dl_cls}(...)")
assert not _dl_bad, (
    "these read whatever this machine has extracted, so they pass "
    "here and can fail in a clone: " + "; ".join(_dl_bad)
    + ". Use `derived(Loader)` for content, an explicit `root=` or "
      "the language 'zz' to force absence, or add the class to "
      "_REAL_DERIVED_OK with the reason it needs the real files")
assert _dl_seen >= 10, (
    f"only {_dl_seen} loader constructions found; the scan has "
    f"stopped seeing them and would pass on anything")

ok(f"no smoke check reaches a derived loader by accident: "
   f"{_dl_seen} constructions, every one through the stand-in, an "
   f"explicit root, an impossible language or the "
   f"{len(_REAL_DERIVED_OK)}-entry allow-list, and no loader "
   f"imported under another name")

# ── ONE CONSTRUCTION SITE, IN THE RUNNING TREE ───────────────
#
# D17, closed by work order 159. `HStrings` was built at FOUR
# sites with three lifetimes — galaxy_map/boxdraw per screen,
# game_menu/screen per app, planets/planetwords fresh on every
# Planets enter, fleets/screen per screen — so one session could
# read HESTRNGS.LBX into four objects and look its language up two
# different ways, one of which raised where the others defaulted.
# Data's decision: one instance, owned by the App, built on first
# use, through `hestrings.for_app`.
#
# **AND `HelpText` IS HELD THE SAME WAY, WHICH IT WAS NOT.**
# `screenhelp.helptext`'s docstring has claimed "exactly one
# construction site" since it was written and NOTHING CHECKED IT —
# work order 159 went looking for that check to copy its shape and
# there was none. A property asserted only in prose is the fault
# this project keeps paying for, so both are held here.
_oc_want = {"HStrings": "core/hestrings.py",
            "HelpText": "core/screenhelp.py"}
_oc_roots = [os.path.dirname(SCREENS_DIR)]
_oc_found = {_k: [] for _k in _oc_want}
for _oc_top in ("core", "screens"):
    for _oc_dp, _oc_dn, _oc_fn in os.walk(
            os.path.join(_oc_roots[0], _oc_top)):
        if "__pycache__" in _oc_dp:
            continue
        for _oc_f in sorted(_oc_fn):
            if not _oc_f.endswith(".py"):
                continue
            _oc_path = os.path.join(_oc_dp, _oc_f)
            _oc_rel = os.path.relpath(_oc_path, _oc_roots[0]).replace(
                os.sep, "/")
            _oc_tree = _dl_ast.parse(
                io.open(_oc_path, encoding="utf-8").read())
            for _oc_n in _dl_ast.walk(_oc_tree):
                if not isinstance(_oc_n, _dl_ast.Call):
                    continue
                _oc_c = _dl_name(_oc_n.func)
                if _oc_c in _oc_found:
                    _oc_found[_oc_c].append(f"{_oc_rel}:{_oc_n.lineno}")
for _oc_cls, _oc_home in sorted(_oc_want.items()):
    assert len(_oc_found[_oc_cls]) == 1, (
        f"{_oc_cls} is constructed at {len(_oc_found[_oc_cls])} sites "
        f"in the running tree: {_oc_found[_oc_cls]}. One instance per "
        f"App, built on first use — {_oc_home} owns it, and a second "
        f"site is a second read of the player's file and a second "
        f"answer to the same lookup")
    assert _oc_found[_oc_cls][0].startswith(_oc_home), (
        f"{_oc_cls}'s one construction moved to "
        f"{_oc_found[_oc_cls][0]}; it belongs in {_oc_home}")
ok("one construction site each for HStrings and HelpText in the "
   "running tree, by ast: core/hestrings.for_app and "
   "core/screenhelp.helptext own them, and a fifth HStrings or a "
   "second HelpText fails here (D17)")

ok(f"the derived stand-ins are current byte for byte "
   f"({len(_sfx.files())} files), each carries the FORMAT_VERSION "
   f"its loader demands, each loads through the loader's own "
   f"path, and {len(_REAL_DERIVED_OK)} checks are allowed the "
   f"player's own extraction with a reason")

ok(f"every extractor is on setup.py's registry or excepted with a "
   f"tracked output ({len(_extractors)} extractors, "
   f"{len(_reg_paths)} registered paths, "
   f"{len(_EXTRACT_COMMITTED)} exception)")

# ── core/lbx.py: the container all three extractors read ──
#
# Asserted against a container built HERE, byte by byte, and not
# against the user's own MOO2 files: those are not in the tree,
# a test that needs them fails for the person who followed the
# instructions (that is the help-file lesson, one domain over),
# and a decoder checked against real data alone cannot say which
# of its two frame formats it got right.
from core import lbx as _lbx
import tempfile as _tf

def _make_lbx(_entries):
    """A container per vfs_lbx.cpp, from a list of blobs."""
    _head = struct.pack("<HHI", len(_entries), _lbx.LBX_MAGIC, 0)
    _pos = 8 + 4 * _lbx.LBX_OFFSET_COUNT
    _offs, _body = [], b""
    for _b in _entries:
        _offs.append(_pos + len(_body))
        _body += _b
    _offs.append(_pos + len(_body))
    _offs += [_offs[-1]] * (_lbx.LBX_OFFSET_COUNT - len(_offs))
    return _head + struct.pack(f"<{_lbx.LBX_OFFSET_COUNT}I",
                               *_offs) + _body

def _anim(_w, _h, _frames, _flags, _payload, _palette=b""):
    _n = len(_frames)
    _hdr = struct.pack("<hhhhbbBB", _w, _h, 0, _n, 0, 0, 0, _flags)
    _base = 12 + 4 * (_n + 1) + len(_palette)
    _offs, _acc = [], b""
    for _f in _frames:
        _offs.append(_base + len(_acc))
        _acc += _f
    _offs.append(_base + len(_acc))
    return (_hdr + struct.pack(f"<{_n + 1}I", *_offs)
            + _palette + _acc + _payload)

# A 2x2 BITMAP frame: index 0 is transparent, 1 is in the
# palette, 200 is not and must come back as grey 200.
# s_palette_entry is {changed, r, g, b} — THE FLAG FIRST
# (orion2.h:2131-2136). The flag byte here is 1 and not 0 on
# purpose: a decoder that read r,g,b,changed would return
# (4, 252, 128) for index 1 and pass every other assertion below.
# That reading is what shipped in nebula_extract.py and was
# inherited by core/lbx.py, and it survived because STARBG.LBX
# has no palettes at all — the function had never run on data.
_pal = struct.pack("<hh", 0, 2) + bytes([0, 0, 0, 0, 1, 63, 32, 16])
_bmp = _anim(2, 2, [bytes([0, 1, 200, 1])],
             _lbx.DRAW_MODE_BITMAP | _lbx.FLAG_HAS_PALETTE, b"", _pal)
# The same picture as a PACKED frame (Draw_Animated_Sprite_):
# row 0 skips 1 then writes 1 literal, row 1 writes 2 literals.
# The odd-length run is deliberate: the stream pads to an even
# offset after every literal run, and a decoder that forgets the
# pad reads the next run header one byte late and still produces
# a picture — a wrong one.
_packed = _anim(2, 2, [struct.pack("<HH", 0, 0)          # unk, start_y
                       + struct.pack("<hh", 1, 1) + bytes([1])
                       + b"\x00"                         # the pad
                       + struct.pack("<hh", 0, 1)        # next row
                       + struct.pack("<hh", 2, 0) + bytes([200, 1])
                       + struct.pack("<hh", 0, 1)],      # end
                _lbx.DRAW_MODE_ANIMATED, b"")
with _tf.TemporaryDirectory() as _td:
    _lp = os.path.join(_td, "probe.lbx")
    with open(_lp, "wb") as _fh:
        _fh.write(_make_lbx([_bmp, _packed]))
    _ents = _lbx.read_entries(_lp)
    assert len(_ents) == 2, len(_ents)
    assert _lbx.read_entry(_lp, 1) == _ents[1], (
        "read_entry and read_entries disagree about entry 1")
    _h0 = _lbx.parse_header(_ents[0])
    assert (_h0.width, _h0.height, _h0.frame_count) == (2, 2, 1), _h0
    assert _h0.has_palette and _h0.mode == _lbx.DRAW_MODE_BITMAP, _h0
    _p0 = _lbx.decode_frame(_ents[0], _h0)
    assert list(_p0) == [0, 1, 200, 1], list(_p0)
    # BOTH FRAME FORMATS MUST GIVE THE SAME PICTURE. They are two
    # transcriptions of two different functions in draw.cpp, and
    # nothing else in the tree can tell you one of them drifted.
    _h1 = _lbx.parse_header(_ents[1])
    assert _h1.mode == _lbx.DRAW_MODE_ANIMATED and not _h1.has_palette
    assert list(_lbx.decode_frame(_ents[1], _h1)) == list(_p0), (
        f"the RLE decoder gives {list(_lbx.decode_frame(_ents[1], _h1))} "
        f"where the bitmap decoder gives {list(_p0)}")
    # 6-bit VGA components are scaled by 4 and clamped.
    assert _lbx.read_palette(_ents[0], 1) == {0: (0, 0, 0),
                                              1: (252, 128, 64)}, (
        f"the palette byte order moved: "
        f"{_lbx.read_palette(_ents[0], 1)}")
    # Index 0 transparent, a palette index opaque, an index with
    # no entry GREY — never an invented colour (see rgba_bytes).
    _rgba = _lbx.rgba_bytes(_p0, _lbx.read_palette(_ents[0], 1))
    assert _rgba[0:4] == bytes([0, 0, 0, 0]), _rgba[0:4]
    assert _rgba[4:8] == bytes([252, 128, 64, 255]), _rgba[4:8]
    assert _rgba[8:12] == bytes([200, 200, 200, 255]), _rgba[8:12]
    # A FILE THAT IS NOT ONE RAISES, and does not exit: these are
    # library calls now, and a tool that wants to try a second
    # path must be able to catch the first one failing.
    _bad = os.path.join(_td, "bad.lbx")
    with open(_bad, "wb") as _fh:
        _fh.write(b"\x00" * 4096)
    for _call in (lambda: _lbx.read_entries(_bad),
                  lambda: _lbx.read_entry(_bad, 0)):
        try:
            _call()
        except _lbx.LbxError:
            pass
        else:
            raise AssertionError("a file with no LBX magic was accepted")
    assert not isinstance(_lbx.LbxError(), SystemExit)
# A frame past the end is a STATE, not an exception: an LBX holds
# entries of several kinds and a walk over all of them meets data
# that is not a sprite.
assert _lbx.decode_frame(_ents[0], _h0, 5) is None
ok("core/lbx.py (container, both frame formats agreeing, 6-bit "
   "palette, index 0 transparent, unpalettised index stays grey)")

# THE NEBULA TOOL READS FONTS.LBX'S PALETTE ITSELF, and read it one
# byte to the left until 16 September 2026 (work order 122, 2.3) —
# the same fault `core/lbx.read_palette` had and was fixed for on
# 6 September, in a second reader nobody looked at. Pinned the same
# way: entry 1 of a probe container, every entry's flag byte
# NON-ZERO, so the flag read as red cannot pass.
sys.path.insert(0, os.path.join(os.path.dirname(SCREENS_DIR), "tools"))
import make_nebula_icons as _mni
_mni_pal = b"".join(bytes([1 + (_i % 7), _i % 64, (_i * 2) % 64,
                           (_i * 3) % 64]) for _i in range(256))
with _tf.TemporaryDirectory() as _td:
    _lp = os.path.join(_td, "FONTS.LBX")
    with open(_lp, "wb") as _fh:
        _fh.write(_make_lbx([b"\x00" * 16, _mni_pal]))
    _mni_got = _mni.load_game_palette(_lp)
for _i in (0, 1, 2, 63, 200, 255):
    _want = (min((_i % 64) * 4, 255), min(((_i * 2) % 64) * 4, 255),
             min(((_i * 3) % 64) * 4, 255))
    assert tuple(int(_v) for _v in _mni_got[_i]) == _want, (
        f"make_nebula_icons palette entry {_i}: "
        f"{tuple(_mni_got[_i])}, want {_want} — (flag, R, G, B)")
ok("tools/make_nebula_icons.py reads FONTS.LBX entries as (flag, R, G, "
   "B), pinned with a non-zero flag byte")

# MOO2's help bodies are not plain text: they carry FMTPARA
# control codes, and the column positions inside them are what
# makes the Command Points table a table. Printing them raw put
# "\aX3.Frigate\aX97.-1" on screen, watermark glyph and all.
from core import helpformat as _hf

_row = "\aX3.Frigate\aX97.-1 \aX150.Star Base\aX270.+1"
_parsed = _hf.parse(_row)
assert len(_parsed) == 1, _parsed
assert [r.x for r in _parsed[0].runs] == [3, 97, 150, 270], \
    _parsed[0].runs
assert _parsed[0].runs[0].text == "Frigate", _parsed[0].runs[0]
assert _parsed[0].columns
# No control character may survive into anything that gets drawn:
# that is the whole failure, and it is invisible to a test that
# only checks the popup drew ink.
_raw = ("\aF2.Head\r\aX3.a\aX97.b\r\rTail\ftext\aT10,20.\tx\b-")
for _ln in _hf.parse(_raw):
    for _r in _ln.runs:
        assert not any(c < " " for c in _r.text), repr(_r.text)
assert _hf.parse("plain\nlines")[0].plain() == "plain"
# Functions the popup does not honour are reported, not assumed
# away.
assert "F" in _hf.dropped_functions(_raw), _hf.dropped_functions(_raw)
assert "X" not in _hf.dropped_functions(_raw)
ok("help format codes decoded (columns, breaks, no control chars)")

# A column is a fraction of the text width, not a pixel count, so
# the table lines up at every resolution rather than at one.
def _row_x(width):
    pop = _HelpPopup()
    pop.open(9, "T", _row)
    blocks = pop._blocks(app.style, 20, 16, width)
    surf = next(s for s, _ in blocks if s is not None
                and s.get_width() == width)
    ink = _np.nonzero(pygame.surfarray.array_alpha(surf).any(axis=1))[0]
    return ink.min() / width

_narrow, _wide = _row_x(400), _row_x(1200)
assert abs(_narrow - _wide) < 0.02, (_narrow, _wide)
assert abs(_narrow - 3 / _hf.HELP_PARA_W) < 0.02, _narrow
ok("help table columns scale with the panel, not with pixels")

# A file from the older extractor is refused rather than rendered
# subtly wrong: it lost the trailing \t and \f codes to an
# rstrip, which produces a plausible-looking wrong layout.
_ht2 = HelpText(res, "en")
_ht2._entries, _ht2._available, _ht2._stale = {}, False, True
_stale = _ht2.missing_entry(288)
assert "help_extract" in _stale[1] and _stale != _no_file, _stale
ok("help: a stale help file is refused, not rendered")
