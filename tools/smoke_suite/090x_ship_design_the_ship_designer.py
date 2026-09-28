# smoke-suite area: ship_design
#
# Part of the OrionLayer smoke suite — 090x_ship_design_the_ship_designer.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 7 check(s) it holds:
#   - open fixes 44 and 45's blocks, as a scratch engine wrote them, parse whole; a tail cut short leaves both None; the offered modifications are the recorded ones; no text of the game's in the cut
#   - screen 3 is claimed only with open fix 44's DSGN: without it the game's picture, as before; the page READY on its own list, a box over it modal, a picker over it PICKER; ids 3 and 54-56 literal, table agrees
#   - the designer sends each control's own field, a hull by an injected click, and refuses a hidden hull, a hidden plus, and Build without its button
#   - the designer draws at 1920, 2576 and 3840 from the recorded page, its text scaled once, and every mark it carries is named in its module and the status document
#   - the designer's loaders: stand-ins read, the extracted art absent answers None with a reason, the art extractor's groups are the source's load order
#   - every way into and out of the designer and its pickers is in the replayed set at 1920 and 2576, each reaching its screen
#   - the name is typed in HD: nothing goes out until Enter, then an injected click on the name field, Backspaces enough to clear it, the keys and Enter, one per tick; ESC sends nothing; the page never asks for the game's picture meanwhile, and the live name entry replays with 0 native frames


# ── THE SHIP DESIGNER (work order 185, part 7) ──────────────────
import json as _sd_json
import types as _sd_ns
import hud_evidence as _sd_he
from core import designblocks as _sd_blocks
from core import game_state as _sd_gsm
from screens.ship_design import sdgeom as _sd_geom
from screens.ship_design import sdwire as _sd_wire

_sd_root = os.path.dirname(SCREENS_DIR)
with open(os.path.join(_sd_root, "tools", "fixtures",
                       "design_blocks_185.json"), encoding="utf-8") as _sd_fh:
    _sd_fix = {s["name"]: s for s in _sd_json.load(_sd_fh)["stops"]}

# 1. THE WIRE FORMAT, AS AN ENGINE WROTE IT (a scratch build with open fixes
# 44 and 45, never applied). Whole, or not at all.
for _sd_name, _sd_stop in _sd_fix.items():
    _sd_tail = bytes.fromhex(_sd_stop["tail"])
    _sd_gs = _sd_gsm.GameState()
    assert _sd_blocks.parse(_sd_gs, _sd_tail, 0) == len(_sd_tail), _sd_name
    assert _sd_gs.ship_design is not None, _sd_name
    assert (_sd_gs.design_box is not None) == (_sd_stop["screen"] != 3), \
        (_sd_name, _sd_stop["screen"])
    _sd_short = _sd_gsm.GameState()
    _sd_blocks.parse(_sd_short, _sd_tail[:-3], 0)
    # A cut DSBX leaves DSBX None; a cut DSGN (no DSBX behind it) DSGN.
    assert (_sd_short.design_box if _sd_stop["screen"] != 3
            else _sd_short.ship_design) is None, _sd_name
_sd_w = _sd_he.design_state("weapon").design_box
assert _sd_w["kind"] == "weapon" and _sd_w["mods_offered"] == [10, 11, 12], \
    _sd_w["mods_offered"]
assert [r["text"] for r in _sd_w["rows"]] == ["", "8", "3-12", "1-4"], \
    "the weapon picker's damage strings as the engine formatted them"
_sd_d = _sd_he.design_state("designer").ship_design
assert (_sd_d["printed_cost"], _sd_d["printed_space_available"],
        _sd_d["hull_space"]) == (82, 47, 60), _sd_d
# No text of the game's in the committed cut (tools/design_fixture.neutral).
assert _sd_d["name"] == "Design 1" and all(
    w["mods_text"] in ("", f"Mods {k}")
    for k, w in enumerate(_sd_d["weapons"])), "a text the game wrote"
ok(f"open fixes 44 and 45's blocks, as a scratch engine wrote them, parse "
   f"whole; a tail cut short leaves both None; the offered modifications "
   f"are the recorded ones; no text of the game's in the cut "
   f"({len(_sd_fix)} stops)")

# 2. THE CLAIM, both ways, and the page's states.
from screens.ship_design import screen as _sd_scr_mod
_sd_app, _ = _pv.build_screen(1920, 1080)
_sd_disp = _sd_app.dispatcher
_sd_page = _sd_disp.screens["ship_design"]
_sd_none = _sd_gsm.GameState()
_sd_none.current_screen = 3
assert not _sd_page.claims(_sd_none), "no DSGN: id 3 is the game's picture"
_sd_disp.update_from_game(_sd_none)
assert _sd_disp.use_original and _sd_disp.active_name != "ship_design"
_sd_gs = _sd_he.design_state("designer")
assert _sd_page.claims(_sd_gs)
assert _sd_wire.View(_sd_gs).state == _sd_wire.READY
_sd_box = _sd_he.design_state("designer")
_sd_box.fields = [_sd_gsm.FieldInfo(index=1, field_type=7, x=0, y=0,
                                    x_end=639, y_end=479)]
assert _sd_wire.View(_sd_box).state == _sd_wire.GAME_BOX
_sd_page.update(_sd_box)
assert _sd_page.handover_is_modal() and _sd_page.wants_original()
_sd_pk = _sd_he.design_state("weapon")
_sd_v = _sd_wire.View(_sd_pk, _sd_gs.fields)
assert _sd_v.state == _sd_wire.PICKER and _sd_v.draws and \
    _sd_v.fields is _sd_gs.fields, "under a picker: the page's own last list"
from core import screen_names as _sd_names
import ast as _sd_ast
_sd_src = open(_sd_scr_mod.__file__, encoding="utf-8").read()
assert "    GAME_SCREEN_ID = 3\n" in _sd_src and _sd_geom.GAME_SCREEN_ID == 3
assert _sd_names.SCREENS[3][1] == "ship_design"
assert all(_sd_names.SCREENS[i] == ("(synthetic)", "design_box")
           for i in (54, 55, 56)) and \
    set(_sd_geom.PICKER_IDS) == set(_sd_blocks.BOX_IDS) == {54, 55, 56}
ok("screen 3 is claimed only with open fix 44's DSGN: without it the game's "
   "picture, as before; the page READY on its own list, a box over it modal, "
   "a picker over it PICKER; ids 3 and 54-56 literal, table agrees")

# 3. WHAT A CLICK SENDS — a fake client records the send paths.
_sd_log = []
_sd_app.client = _sd_ns.SimpleNamespace(
    state=_sd_he.design_state("designer"),
    activate_field=lambda i: _sd_log.append(("activate", i)),
    inject_click=lambda x, y: _sd_log.append(("click", x, y)),
    inject_key=lambda k: _sd_log.append(("key", k)))
_sd_app.connected = True
_sd_disp.update_from_game(_sd_app.client.state)
_sd_p = _sd_disp.active
assert _sd_disp.active_name == "ship_design"
from screens.ship_design.screen import Names as _sd_Names
from core.hestrings import HStrings
_sd_app.hstrings = derived(HStrings)
_sd_p._names = _sd_Names(_sd_app, "en", root=DERIVED_ROOT)
_sd_p.update(_sd_app.client.state)
from screens.leaders import ldrdraw as _sd_nd


def _sd_click(f):
    r = _sd_nd.rect(_sd_p.layout, (f.x, f.y, f.x_end, f.y_end))
    _sd_log.clear()
    _sd_p.handle_click(r.centerx, r.centery)
    return list(_sd_log)


_sd_live = _sd_app.client.state.fields
for _sd_ident in (_sd_geom.CANCEL, _sd_geom.CLEAR, _sd_geom.BUILD,
                  _sd_geom.SHIELD, _sd_geom.COMPUTER):
    _sd_f = _sd_wire.live_field(_sd_live, _sd_ident)
    assert _sd_f is not None and _sd_click(_sd_f) == \
        [("activate", _sd_f.index)], _sd_ident
_sd_hulls = [_sd_wire.at_origin(_sd_live, _sd_geom.HULL_X[0], y1)
             for y1, _y2 in _sd_geom.HULL_ROWS]
_sd_multi = [f for f in _sd_hulls if f and f.field_type == 3]
_sd_hidden = [f for f in _sd_hulls if f and f.field_type == 7]
assert _sd_multi and _sd_click(_sd_multi[0]) == [
    ("click", (_sd_multi[0].x + _sd_multi[0].x_end) // 2,
     (_sd_multi[0].y + _sd_multi[0].y_end) // 2)], "a hull is a click"
assert not _sd_hidden or _sd_click(_sd_hidden[0]) == [], \
    "a hull the list offers only hidden is refused"
for _sd_key, _sd_ident in ((pygame.K_ESCAPE, _sd_geom.CANCEL),
                           (pygame.K_l, _sd_geom.CLEAR),
                           (pygame.K_b, _sd_geom.BUILD)):
    _sd_log.clear()
    _sd_p.handle_key(_sd_key)
    assert _sd_log == [("activate", _sd_wire.live_field(
        _sd_live, _sd_ident).index)], _sd_key
# Build gone from the list (the design does not fit): refused.
_sd_nobuild = _sd_he.design_state("designer")
_sd_bf = _sd_wire.live_field(_sd_nobuild.fields, _sd_geom.BUILD)
_sd_nobuild.fields = [f for f in _sd_nobuild.fields if f is not _sd_bf]
_sd_app.client.state = _sd_nobuild
_sd_p.update(_sd_nobuild)
assert _sd_click(_sd_bf) == [], "Build without its button is refused"
# A plus / minus the list holds only hidden is refused.
_sd_hid = _sd_he.design_state("designer")
_sd_plus = next(f for f in _sd_hid.fields if (f.x, f.y) == (
    _sd_geom.PLUS_X, _sd_geom.WEAPON_ROW_Y0))
_sd_plus.field_type = 7
_sd_app.client.state = _sd_hid
_sd_p.update(_sd_hid)
assert _sd_click(_sd_plus) == [], "a hidden plus is refused"
_sd_ssrc = open(os.path.join(_sd_root, "screens", "ship_design", "screen.py"),
                encoding="utf-8").read()
assert _sd_ssrc.count("activate_field(") == 1 and \
    _sd_ssrc.count("inject_click(") == 1
ok("the designer sends each control's own field, a hull by an injected "
   "click, and refuses a hidden hull, a hidden plus, and Build without its "
   "button")

# 4. IT DRAWS, and its marks are named where the rule says.
_sd_fonts, _sd_inked = {}, []
for _sd_size in ((1920, 1080), (2576, 1432), (3840, 2160)):
    _sd_a, _ = _pv.build_screen(*_sd_size)
    _sd_st = _sd_he.design_state("designer")
    _sd_a.dispatcher.update_from_game(_sd_st)
    _sd_c = _sd_a.dispatcher.active
    _sd_a.hstrings = derived(HStrings)
    _sd_c._names = _sd_Names(_sd_a, "en", root=DERIVED_ROOT)
    _sd_c.update(_sd_st)
    assert not _sd_c.wants_original(), _sd_c.fallback_reason()
    _sd_surf = pygame.Surface(_sd_size)
    _sd_fonts[_sd_size] = _sd_he.font_sites(
        _sd_c.style, lambda: _sd_c.render(_sd_surf))
    _sd_r = _sd_nd.rect(_sd_c.layout, (0x14, 0x19, 0x98, 0x28))
    _sd_inked.append(len({_sd_surf.get_at((x, _sd_r.centery))[:3]
                          for x in range(_sd_r.x, _sd_r.right, 2)}))
assert min(_sd_inked) > 3, ("the design's name is not drawn", _sd_inked)
assert len(_sd_fonts[(1920, 1080)]) >= 3 and not _sd_he.scaled_twice(
    _sd_fonts[(1920, 1080)], _sd_fonts[(3840, 2160)]), _sd_fonts
_sd_status = open(os.path.join(_sd_root, "v3_projektstatus.md"),
                  encoding="utf-8").read()


def _sd_marks_named(folder, files):
    with open(os.path.join(SCREENS_DIR, folder, "layout.json"),
              encoding="utf-8") as fh:
        marks = _sd_json.load(fh)["marks"]
    text = "".join(open(os.path.join(SCREENS_DIR, folder, f),
                        encoding="utf-8").read() for f in files)
    for key in marks:
        name = key.split("_", 2)[2] if key.startswith("hd_") else \
            key.split("_", 1)[1]
        assert f"`{name}`" in text, f"{folder} {key}: not in the module"
        assert f"`{name}`" in _sd_status, f"{folder} {key}: not in the status doc"
    return len(marks)


_sd_nmarks = _sd_marks_named("ship_design",
                             ("sddraw.py", "screen.py", "sdwire.py"))
# Open fixes 44 and 45 are APPLIED (work order 186) and the data path was
# seen live on that engine: the build requires them, the page carries no
# UNVERIFIED `fix44` any more, and the name is an OMISSION with the reason
# the data does not cover it (the text being typed is on no block) — what
# keys do there was measured in 186 part 3, so it is no longer UNVERIFIED.
import version_check as _sd_vc
with open(os.path.join(SCREENS_DIR, "ship_design", "layout.json"),
          encoding="utf-8") as _sd_fh:
    _sd_mk = _sd_json.load(_sd_fh)["marks"]
assert "doc/ext_ship_designer_state.patch" in _sd_vc.LOCAL_PATCHES
assert "unverified_fix44" not in _sd_mk, "fix 44 is applied: its mark goes"
assert "deviation_name_field" in _sd_mk and not {
    "unverified_name_entry", "omission_name_entry"} & set(_sd_mk), _sd_mk
ok(f"the designer draws at 1920, 2576 and 3840 from the recorded page, its "
   f"text scaled once, and every mark it carries is named in its module and "
   f"the status document ({_sd_nmarks} marks)")

# 5. THE LOADERS: the committed stand-ins read; the player's art absent is
# a stated absence, never an exception; the extractor's groups are the
# source's load order (design_main.cpp:522-561, idx counting on from 12).
from core import shipparts as _sd_parts, techdesc as _sd_desc
from screens.ship_design import sdart as _sd_art
_sd_app.hstrings = derived(HStrings)
_sd_n = _sd_Names(_sd_app, "en", root=DERIVED_ROOT)
assert _sd_n.state == "ok", _sd_n.state
assert derived(_sd_parts.ShipPartNames).has_design_names()
assert derived(_sd_desc.TechDesc).special(2) == "Description 2"
_sd_empty = _sd_art.DesignArt(os.path.join(_sd_root, "tools", "fixtures",
                                           "no_such_folder"))
assert not _sd_empty.available and "design_art_extract" in _sd_empty.reason
assert _sd_empty.arc(0) is None and _sd_empty.label("filter", 0, 1) is None \
    and _sd_empty.ship(0, 0) is None
import design_art_extract as _sd_dae
_sd_order = ["dark_build", "plus", "minus", "up", "down", "dull_plus",
             "dull_minus", "dull_up", "dull_down", "scroll_bar", "filter",
             "filter", "filter", "filter", "cancel", "accept", "top", "mid",
             "bottom", "selected", "rack"] + ["arc"] * 5 + ["arc_word"] * 5 \
    + ["rack_word"] * 5
_sd_at = {name: 12 + _sd_order.index(kind) for name, kind in (
    ("filters", "filter"), ("arcs", "arc"), ("arc_words", "arc_word"),
    ("rack_words", "rack_word"))}
assert {g[0]: g[1] for g in _sd_dae.GROUPS} == _sd_at, _sd_dae.GROUPS
assert _sd_dae.FORMAT_VERSION == _sd_art.FORMAT_VERSION
ok("the designer's loaders: stand-ins read, the extracted art absent answers "
   "None with a reason, the art extractor's groups are the source's load "
   "order")

# 6. EVERY WAY INTO AND OUT OF THE DESIGNER AND ITS PICKERS is in the set
# 090o replays (`tools/design_walk.py` on a scratch engine with open fixes
# 44 and 45), at both window sizes, each reaching the screen it names.
with open(os.path.join(_sd_root, "tools", "fixtures", "transitions_180.json"),
          encoding="utf-8") as _sd_fh:
    _sd_tr = _sd_json.load(_sd_fh)["transitions"]
_sd_ways = {"build_queue -> ship_design (design slot 1)": 3,
            "ship_design -> design_box (computer)": 54,
            "design_box (computer) -> ship_design (ESC)": 3,
            "ship_design -> design_box (weapon)": 55,
            "design_box (weapon) -> ship_design (ESC)": 3,
            "ship_design -> design_box (special)": 56,
            "design_box (special) -> ship_design (ESC)": 3,
            "ship_design -> build_queue (ESC)": 25}
_sd_count = 0
for _sd_size in ("1920x1080", "2576x1432"):
    _sd_got = {t["transition"]: t for t in _sd_tr
               if t.get("source") == f"P7_design_{_sd_size}"}
    for _sd_way, _sd_id in _sd_ways.items():
        assert _sd_way in _sd_got, f"{_sd_way} at {_sd_size} not recorded"
        assert any(_r[1] == _sd_id for _r in _sd_got[_sd_way]["rows"]), \
            (_sd_way, _sd_size, "never reaches screen", _sd_id)
        _sd_count += 1
ok(f"every way into and out of the designer and its pickers is in the "
   f"replayed set at 1920 and 2576, each reaching its screen "
   f"({_sd_count} recorded transitions)")



# 7. THE NAME, IN HD (work order 187, part 2). Data's rule: nothing of the
#    original's picture outside F12 — so the name is typed in HD's own field
#    and sent on Enter the save dialog's way (`sdname.py`): an injected
#    click opens the original's field (an activation does not, 186), 15
#    Backspaces clear it (one takes one letter in this field, 187), the keys, Enter. One
#    send per tick (the double has no counters: one per update).
import pygame as _sn_pg
from screens.ship_design import sdname as _sn
_sn_ev = lambda k, u="": _sn_pg.event.Event(_sn_pg.KEYDOWN, key=k, mod=0,
                                            unicode=u, scancode=0)
_sn_live = _sd_app.client.state.fields
_sn_f = _sd_wire.live_field(_sn_live, _sd_geom.NAME)
assert _sn_f is not None and (_sn_f.x, _sn_f.y, _sn_f.x_end, _sn_f.y_end) == \
    _sd_geom.NAME_RECT, "the name field is where sdgeom says"
_sn_r = _sd_nd.rect(_sd_p.layout, _sd_geom.NAME_RECT)
_sd_p.name_edit = _sn.NameEditor(_sd_p)
_sd_log.clear()
_sd_p.handle_click(_sn_r.centerx, _sn_r.centery)
assert _sd_p.name_edit.editing and _sd_log == [], _sd_log
_sn_before = _sd_p.name_edit.input.value
for _sn_k, _sn_u in ((_sn_pg.K_BACKSPACE, ""), (ord("x"), "X"),
                     (ord("_"), "_"), (ord("b"), "B")):
    _sd_p.handle_key_event(_sn_ev(_sn_k, _sn_u))
assert _sd_p.name_edit.input.value == _sn_before[:-1] + "XB", \
    "Backspace edits, '_' is refused, letters append"
assert _sd_log == [], "nothing goes out before Enter"
assert not _sd_p.wants_original(), "the page keeps HD's picture"
# ESC cancels in HD: nothing sent, the field closes
_sd_p.handle_key_event(_sn_ev(_sn_pg.K_ESCAPE))
assert _sd_p.name_edit.input is None and _sd_log == []
# a 15th character is refused
_sd_p.handle_click(_sn_r.centerx, _sn_r.centery)
for _sn_c in "ABCDEFGHIJKLMNOPQ":
    _sd_p.handle_key_event(_sn_ev(ord(_sn_c.lower()), _sn_c))
assert len(_sd_p.name_edit.input.value) <= _sn.NAME_MAX == 14
_sd_p.name_edit.input.value = "Ab"
_sd_p.handle_key_event(_sn_ev(_sn_pg.K_RETURN, "\r"))
assert _sd_p.name_edit.busy and not _sd_p.wants_original()
for _ in range(40):
    _sd_p.name_edit.update(_sd_app.client.state)
_sn_cx, _sn_cy = (_sn_f.x + _sn_f.x_end) // 2, (_sn_f.y + _sn_f.y_end) // 2
assert _sd_log == [("click", _sn_cx, _sn_cy)] + \
    [("key", _sn_pg.K_BACKSPACE)] * _sn.CLEAR_KEYS + \
    [("key", ord("A")), ("key", ord("b")), ("key", _sn_pg.K_RETURN)], _sd_log
assert _sn.CLEAR_KEYS >= _sn.NAME_MAX + 1, "enough Backspaces for any name" 
assert not _sd_p.name_edit.busy
# while the keys went out, a click on the page sent nothing else
assert "activate" not in {e[0] for e in _sd_log}
_sd_p.name_edit = _sn.NameEditor(_sd_p)
# AND LIVE, 0 NATIVE FRAMES: the name entry walked on the applied engine
# (work order 187 part 2: "Rafale" -> "Hawke", Backspace, Enter; then ESC)
# is in the replayed set, which 090o runs through the gate — no native frame.
with open(os.path.join(_sd_root, "tools", "fixtures", "transitions_180.json"),
          encoding="utf-8") as _sn_fh:
    _sn_tr = {t["transition"]: t for t in _sd_json.load(_sn_fh)["transitions"]}
for _sn_k in ("ship_design -> ship_design (name entry: Enter)",
              "ship_design -> ship_design (name entry: ESC)"):
    assert _sn_k in _sn_tr and all(not r[4] for r in _sn_tr[_sn_k]["rows"]), (
        f"{_sn_k}: not in the replayed set, or a row asks for the picture")
ok("the name is typed in HD: nothing goes out until Enter, then an injected "
   "click on the name field, Backspaces enough to clear it, the keys and "
   "Enter, one per tick; "
   "ESC sends nothing; the page never asks for the game's picture meanwhile, "
   "and the live name entry replays with 0 native frames")
