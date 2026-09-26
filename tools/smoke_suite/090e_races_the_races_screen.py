# smoke-suite area: races
#
# Part of the OrionLayer smoke suite — 090e_races_the_races_screen.py.
# Executed in the suite's one namespace, after 090a-090d (whose `_lm_pack`
# record packer and `_ldw_f` field builder it uses). Work order 175 C: the
# Races screen (SCREEN_RACE, 6).
#
# The 5 check(s) it holds:
#   - the geometry is racescrn.cpp's (tables, slider remap, relation words,
#     icon spacing, the two field shapes 8 + 5n and 7 + n), the player
#     fields sit where the headers put them, and every save on this disk
#     keeps the game's invariants at those offsets (tools/races_check.py)
#   - the lists and the states: active and shown players (eliminated,
#     omniscient), MAIN and WHO read off the list, a native box, WAITING
#     then DIALOG — only DIALOG hands over — and a slot says the treaty
#     paragraph, the relation word, IGNORED, the spies and the bonuses
#   - what is sent: every button to its own field in MAIN, a race or the
#     catcher in WHO, ESC; nothing for a mission, nothing from a dialog
#   - the mission buttons' fields are RACES.LBX's own sizes for EVERY slot
#     (each slot has its own pictures, heights 13 or 14 — work order 176's
#     live run found 175's one-slot table wrong)
#   - it draws at three sizes and 2576x1432 with the art absent and
#     present, its markings each have a home in the code, screen 6 routes
#     here, its extractor writes into an ignored folder, and the loader
#     says absent and stale
import json as _rc_json
import struct as _rc_st
import tempfile as _rc_tmp

from core.structs import player as _rc_player
from screens.races import racesart as _rc_art
from screens.races import racesgeom as _rc_g
from screens.races import racesrows as _rc_rows
from screens.races import raceswire as _rc_w


def _rc_player_raw(name, race, colour, contact=(), eliminated=0, **kw):
    _b = _lm_pack(_rc_player.SPEC, _rc_player.SIZE, name=name, race=race,
                  color=colour, eliminated=eliminated, **kw)
    for _p in contact:
        _b[_rc_player.CONTACT_OFFSET + _p] = 1
    return bytes(_b)


def _rc_state(players, me=0, fields=None, leaders=None):
    from core import game_state as _gsm
    _gs = _gsm.GameState()
    _gs.current_screen, _gs.player_num = 6, me
    _gs.num_players = len(players)
    _gs.player_raw = list(players) + [bytes(_rc_player.SIZE)] * (
        8 - len(players))
    _gs.leaders_raw = leaders or []
    _gs.fields = fields or []
    return _gs


def _rc_fields(shape):
    _out = []
    for _r, _t, _hk in shape:
        _out.append(_ldw_f(len(_out) + 1, _r, _t, _hk))
    return _out


# Player 0 (us) has met 1 and 2; 3 is eliminated, 4 unmet.
_rc_rel = [0, 40, -60, 0, 0, 0, 0, 0]
_rc_players = [
    _rc_player_raw("Us", 0, 0, contact=(1, 2), relations=_rc_rel,
                   treaty=[0, 2, 5, 0, 0, 0, 0, 0],
                   trade_treaty=[0, 1, 0, 0, 0, 0, 0, 0],
                   current_trade_agreement_level=[0, 12, 0, 0, 0, 0, 0, 0],
                   tribute_treaty=[0, 0, 1, 0, 0, 0, 0, 0],
                   spies=[3, 5 | (1 << 6), 0, 0, 0, 0, 0, 0],
                   ignoring=1 << 2),
    _rc_player_raw("Ally", 3, 2, contact=(0,), treaty=[2, 0, 0, 0, 0, 0,
                                                        0, 0]),
    _rc_player_raw("Foe", 5, 4, contact=(0,), treaty=[5, 0, 0, 0, 0, 0, 0,
                                                       0]),
    _rc_player_raw("Gone", 7, 6, eliminated=1),
    _rc_player_raw("Far", 9, 7)]

# ── 1. GEOMETRY, SHAPES, OFFSETS ─────────────────────────────
assert _rc_g.slider_y(0, -100) == 49 + 74 - 6 and \
    _rc_g.slider_y(0, 100) == 49 + 0 - 6, "the slider remap (:304-312)"
assert _rc_g.relation_word_id(-100) == 0x21 and \
    _rc_g.relation_word_id(100) == 0x21 + 16 and \
    _rc_g.relation_word_id(0) == 0x21 + 8
assert _rc_g.icon_spacing(1, _rc_g.SPY_GROUP[0]) == 28 and \
    _rc_g.icon_spacing(63, _rc_g.SPY_GROUP[0]) == (187 - 28) // 62
# The inventory's 8 + 5n and 7 + n count the engine's slot 0 too.
for _rc_n in range(8):
    assert len(_rc_g.main_shape(_rc_n)) + 1 == (3 if _rc_n == 0 else
                                                8 + 5 * _rc_n)
    assert len(_rc_g.who_shape(_rc_n)) + 1 == 7 + _rc_n
assert _rc_g.button_rect("exit") == (535, 433, 607, 450)
_rc_off = {_n: _o for _n, _o, _k in _rc_player.SPEC.fields}
assert (_rc_off["relations"], _rc_off["treaty"], _rc_off["spies"],
        _rc_off["ignoring"], _rc_off["tribute_treaty"]) == (1660, 1676, 3772,
                                                            3781, 1700)
_rc_rc = _ld_tool("races_check")
_rc_seen = 0
for _rc_path in sorted(glob.glob(os.path.expanduser(
        "~/orionlayer-fixtures/*.GAM"))):
    _rc_hero = _ld_tool("leader_check").herodata()
    _rc_got = _rc_rc.players_of(open(_rc_path, "rb").read(), _rc_hero)
    if _rc_got is None:
        continue
    _rc_seen += 1
    assert _rc_rc.check(*_rc_got) == [], (_rc_path, _rc_rc.check(*_rc_got))
ok(f"the Races geometry is racescrn.cpp's, the two field shapes are 8 + 5n "
   f"and 7 + n, the player fields sit at the headers' offsets, and "
   f"{_rc_seen} fixture save(s) keep the game's invariants there")

# ── 2. LISTS, STATES, WORDS ──────────────────────────────────
_rc_s = _rc_state(_rc_players)
_rc_ps = _rc_w.players_of(_rc_s)
assert _rc_w.active_players(_rc_ps, 0, 5) == [1, 2]
assert _rc_w.shown_players(_rc_ps, 0, 5) == [1, 2, 3], \
    "the eliminated race is shown after the active ones (bill.cpp:312-338)"
_rc_omni = list(_rc_players)
_rc_ob = bytearray(_rc_omni[0])
_rc_ob[_rc_player.TRAITS_OFFSET + 27] = 1              # TRAIT_OMNISCIENCE
_rc_omni[0] = bytes(_rc_ob)
if _rc_player.has_omniscience(_rc_player.parse(_rc_omni[0])):
    assert _rc_w.shown_players(_rc_w.players_of(_rc_state(_rc_omni)), 0,
                               5) == [1, 2, 3, 4]
for _rc_shape, _rc_want in ((_rc_g.main_shape(2), _rc_w.MAIN),
                            (_rc_g.who_shape(2), _rc_w.WHO)):
    _rc_v = _rc_w.View(_rc_state(_rc_players,
                                 fields=_rc_fields(_rc_shape)))
    assert _rc_v.state == _rc_want and _rc_v.draws, (_rc_v.state,
                                                     _rc_v.reason)
    assert set(_rc_v.buttons) == set(_rc_g.BUTTONS)
_rc_v = _rc_w.View(_rc_state(_rc_players, fields=_rc_fields(
    _rc_g.main_shape(3))))
assert _rc_v.state == _rc_w.WAITING, "a list for another race count"
_rc_v = _rc_w.View(_rc_state(_rc_players, fields=_rc_fields(
    _rc_g.main_shape(3))), waited=_rc_w.WAIT_BOUND)
assert _rc_v.state == _rc_w.DIALOG and not _rc_v.draws and _rc_v.reason
_rc_box = [_ldw_f(1, (235, 302, 286, 323), 7, ord("Y")),
           _ldw_f(2, (345, 302, 396, 323), 7, ord("N"))]
assert _rc_w.View(_rc_state(_rc_players, fields=_rc_box)).state == \
    _rc_w.IN_BOX
_LcW = type("_LcW", (), {"billtext": lambda self, i: {
    0x3A: "TRADE: ", 0x3C: "GETS é%", 0x3B: "PAYS é%",
    0x21 + 11: "WARM", 0x21 + 3: "COLD", 0x32: "(IGN)"}.get(i),
    "estring": lambda self, i: {0x275: "none", 0x277: "pact",
                                0x27A: "fight"}.get(i), "me": 0})()
_rc_v = _rc_w.View(_rc_state(_rc_players, fields=_rc_fields(
    _rc_g.main_shape(2))))
_rc_sl = _rc_rows.slots(_rc_v, _LcW)
assert [s.player for s in _rc_sl] == [1, 2, 3]
assert _rc_sl[0].lines == ["PACT", "TRADE: 12BC"], _rc_sl[0].lines
assert _rc_sl[1].lines == ["FIGHT", "PAYS 5%"], _rc_sl[1].lines
assert _rc_sl[0].relation_word == "WARM" and _rc_sl[1].relation_word == "COLD"
assert _rc_sl[1].ignored and not _rc_sl[0].ignored
assert (_rc_sl[0].spies, _rc_sl[0].mission) == (5, 1)
assert _rc_sl[2].eliminated and _rc_sl[2].lines == []
assert _rc_rows.agents(_rc_v) == 3
assert _rc_rows.spy_bonuses(_rc_v, []) == (0, 0)
ok("the Races lists (active, shown with the eliminated and the omniscient's), "
   "MAIN and WHO off the list, a box, WAITING then DIALOG — the only "
   "hand-over — and each slot's treaty lines, relation word, IGNORED, spies "
   "and the agents")

# ── 3. WHAT IS SENT ───────────────────────────────────────────
_ldw_app.dispatcher.switch_to("races")
_rc_scr = _ldw_app.dispatcher.screens["races"]


def _rc_click(native):
    from core import researchnative as _n
    _ldw_sent.clear()
    _p = _n.window_point(native, _rc_scr.layout)
    _rc_scr.handle_click(_p[0] + 1, _p[1] + 1)
    return list(_ldw_sent)


def _rc_mid(r):
    return ((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)


_rc_s = _rc_state(_rc_players, fields=_rc_fields(_rc_g.main_shape(2)))
_rc_scr.update(_rc_s)
for _rc_name in _rc_g.BUTTONS:
    _rc_r = _rc_g.button_rect(_rc_name)
    assert _rc_click(_rc_mid(_rc_r)) == [
        ("act", _ldw_index(_rc_s.fields, _rc_r))], _rc_name
assert _rc_click(_rc_mid(_rc_g.mission_rect(0, 1))) == [], \
    "a mission went out"
assert _rc_click(_rc_mid(_rc_g.spy_field(0))) == [], "a spy strip went out"
_ldw_sent.clear()
_rc_scr.handle_key(27)
assert _ldw_sent == [("act", _ldw_index(_rc_s.fields,
                                         _rc_g.button_rect("exit")))]
_rc_s = _rc_state(_rc_players, fields=_rc_fields(_rc_g.who_shape(2)))
_rc_scr.update(_rc_s)
assert _rc_click(_rc_mid(_rc_g.who_field(1))) == [
    ("act", _ldw_index(_rc_s.fields, _rc_g.who_field(1)))]
assert _rc_click((620, 300)) == [
    ("act", _ldw_index(_rc_s.fields, _rc_g.CATCHER))], "WHO's cancel"
_rc_scr.update(_rc_state(_rc_players, fields=_rc_fields(
    _rc_g.main_shape(3))))
_rc_scr._waited = _rc_w.WAIT_BOUND
_rc_scr.update(_rc_state(_rc_players, fields=_rc_fields(
    _rc_g.main_shape(3))))
assert _rc_scr.wants_original() and _rc_click(_rc_mid(
    _rc_g.button_rect("exit"))) == []
# The declare-war box (work order 176: 175 never drew it and the screen
# crashed on it live): drawn through fltbox, NO goes to its own field.
_rc_scr._waited = 0
_rc_s = _rc_state(_rc_players, fields=_rc_box)
_rc_scr.update(_rc_s)
assert _rc_scr._view.in_box and not _rc_scr.wants_original()
_rc_scr.render(pygame.Surface((1920, 1080)))
from screens.fleets import fltbox as _rc_fb
_rc_btn = {k: r for k, _f, r in _rc_fb.button_rects(_rc_scr)}
assert set(_rc_btn) == {"yes", "no"}, _rc_btn
_ldw_sent.clear()
_rc_scr.handle_click(*_rc_btn["no"].center)
assert _ldw_sent == [("act", 2)], _ldw_sent
ok("the Races screen sends every button to its own field in MAIN, a race or "
   "the catcher in WHO, ESC to RETURN, the declare-war box's answer to its "
   "field — and no mission, no spy strip, nothing from a dialog")

# ── 3b. THE MISSION BUTTONS, EVERY SLOT (work order 176) ─────────────
# 175 measured slot 0's pictures and used them for all seven; live, slot
# 1's SABOTAGE is 13 high, not 14, the main list was not recognised and
# the screen handed over. The table now holds each slot's own sizes; where
# the player's RACES.LBX is on this disk it is the second source.
assert len(_rc_g.MISSION_H) == _rc_g.SLOTS
assert _rc_g.mission_rect(1, 1) == (196, 233, 267, 245), \
    "slot 1's SABOTAGE as the live list reported it on 26 September 2026"
_rc_fa = _ld_tool("fleet_art_extract")
_rc_lbx_path = _rc_fa.find_lbx(None, "RACES.LBX")
if _rc_lbx_path:
    from core import lbx as _rc_lbx
    _rc_e = _rc_lbx.read_entries(_rc_lbx_path)
    for _i in range(_rc_g.SLOTS):
        for _k, _base in enumerate((10, 17, 24)):
            _h = _rc_lbx.parse_header(_rc_e[_base + _i], "RACES.LBX")
            _r = _rc_g.mission_rect(_i, _k)
            assert (_r[2] - _r[0] + 1, _r[3] - _r[1] + 1) == (
                _h.width, _h.height), (_i, _k, _r, _h.width, _h.height)
else:
    report("the mission buttons NOT checked against RACES.LBX — not on "
           "this disk")
ok("the Races mission buttons' fields are each slot's own picture sizes "
   "(RACES.LBX 10+i, 17+i, 24+i), checked against the file where it is "
   "on disk")

# ── 4. DRAWING, MARKINGS, ROUTING, EXTRACTION ───────────────
import pygame as _rc_pg
_rc_dir = os.path.join(_ldc_root, "screens", "races")
_rc_arts = [_rc_art.RacesArt(os.path.join(_ldc_root, "nowhere"))]
if _rc_art.load().available:
    _rc_arts.append(_rc_art.load())
_rc_s = _rc_state(_rc_players, fields=_rc_fields(_rc_g.main_shape(2)))
for _rc_size in ((1920, 1080), (2560, 1440), (3840, 2160), (2576, 1432)):
    _rc_app, _ = _ldw_plv.build_screen(*_rc_size)
    _rc_app.dispatcher.switch_to("races")
    _rc_x = _rc_app.dispatcher.screens["races"]
    for _rc_a in _rc_arts:
        _rc_x._art = _rc_a
        _rc_x.update(_rc_s)
        _rc_x._hover = _rc_mid(_rc_g.bar_field(0))
        _rc_x.render(_rc_pg.Surface(_rc_size))
assert "races_art_extract" in _rc_arts[0].reason
_rc_layout = _rc_json.load(open(os.path.join(_rc_dir, "layout.json"),
                                encoding="utf-8"))
_rc_src = "".join(open(os.path.join(_rc_dir, _f), encoding="utf-8").read()
                  for _f in os.listdir(_rc_dir) if _f.endswith(".py"))
for _rc_key in _rc_layout["marks"]:
    if _rc_key == "hd_state":
        continue
    _rc_word = _rc_key.split("_", 1)[1]
    for _rc_pre in ("extension_", "state_"):
        if _rc_word.startswith(_rc_pre):
            _rc_word = _rc_word[len(_rc_pre):]
    assert _rc_word in _rc_src, f"{_rc_key}: no module names {_rc_word!r}"
assert "BUILT, NOT ACCEPTED" in _rc_layout["marks"]["hd_state"]
assert "BUILT, NOT ACCEPTED" in open(os.path.join(_rc_dir, "screen.py"),
                                     encoding="utf-8").read().split('"""')[1]
from core.screen_names import SCREENS as _rc_names
assert _rc_names[6] == ("RACE", "races")
assert _ldw_app.dispatcher.screen_map.get(6) == "races"
_rc_ign = _ldc_sp.run(["git", "-C", _ldc_root, "check-ignore", "--no-index",
                       "screens/races/assets/gamedata/"],
                      capture_output=True, text=True)
assert _rc_ign.stdout.strip(), "git does not ignore the Races artwork"
_rc_tool = _ld_tool("races_art_extract")
assert os.path.commonpath([_ldc_root, _rc_tool.DEFAULT_OUT]) == _ldc_root
with _rc_tmp.TemporaryDirectory() as _rc_t:
    with open(os.path.join(_rc_t, "manifest.json"), "w") as _fh:
        _fh.write('{"format": %d}' % (_rc_art.FORMAT_VERSION + 1))
    _rc_old = _rc_art.RacesArt(_rc_t)
    assert not _rc_old.available and _rc_old.portrait(0) is None and \
        str(_rc_art.FORMAT_VERSION) in _rc_old.reason
ok("the Races screen draws at 1080p, 1440p, 2160p and 2576x1432 with the art "
   "absent and present, every marking has a home in its code, screen 6 "
   "routes here, the extractor writes into an ignored folder and the loader "
   "says absent and stale")
