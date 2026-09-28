# smoke-suite area: audience
#
# Part of the OrionLayer smoke suite — 090z_audience_the_diplomacy_audience.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 6 check(s) it holds:
#   - open fix 47's DIPL block, as a scratch engine wrote it, parses whole — the refusal, the greeting, the menu with its enable flags; a tail cut short, or none, leaves it None; the committed fixture carries no text of the game's
#   - ids 57 and 58 are one screen, claimed only with DIPL: without it the game's picture, as before; a menu, a statement, a refusal read off the list, anything else modal
#   - the audience sends an enabled item's own field, the statement's one field on any click, and refuses a disabled item
#   - the audience draws at 1920, 2576 and 3840 from the recorded menu, its text scaled once, and every mark it carries is named in its module and the status document
#   - the audience's art loader: the player's files absent answer None with a reason; the extractor takes the source's entries (r, 2r+13, 2r+14)
#   - every way into and out of the audience the scratch save offers is in the replayed set, each reaching its screen


# ── THE DIPLOMACY AUDIENCE (work order 185, parts 9-11) ─────────
import json as _au_json
import audience_fixture as _au_fix
from core import diplblocks as _au_blocks
from core import game_state as _au_gsm

with open(_au_fix.OUT, encoding="utf-8") as _au_fh:
    _au_stops = {s["name"]: s for s in _au_json.load(_au_fh)["stops"]}

# 1. THE WIRE FORMAT, AS AN ENGINE WROTE IT (a scratch build with open fixes
# 46 and 47, never applied), texts replaced by stand-ins at the cut.
_au_want = {"refused": ("player", 0, 126, []),
            "greeting": ("player", 1, 128, []),
            "menu": ("player", 1, 128, [False, True, True, True])}
for _au_name, (_au_mode, _au_opt, _au_resp, _au_flags) in _au_want.items():
    _au_tail = bytes.fromhex(_au_stops[_au_name]["tail"])
    _au_gs = _au_gsm.GameState()
    _au_end = _au_blocks.parse(_au_gs, _au_tail, 0)
    _au_a = _au_gs.audience
    assert _au_a is not None and _au_end > 4, _au_name
    assert (_au_a["mode"], _au_a["option"], _au_a["response"]) == \
        (_au_mode, _au_opt, _au_resp), (_au_name, _au_a)
    assert [i["enabled"] for i in _au_a["items"]] == _au_flags, _au_name
    assert _au_a["text"] == f"Reply {_au_resp}", "a text the game wrote"
    assert all(i["text"] == f"Item {k}"
               for k, i in enumerate(_au_a["items"])), _au_name
    assert _au_stops[_au_name]["screen"] == 57
    _au_short = _au_gsm.GameState()
    assert _au_blocks.parse(_au_short, _au_tail[:_au_end - 1], 0) == 0 and \
        _au_short.audience is None, _au_name
# The menu's items are its type-10 fields but the first (the title): the
# list the flags belong to (Get_List_Field_, fields.cpp:1561-1620).
_au_menu = _au_fix.state("menu")
assert len([f for f in _au_menu.fields if f.index and f.field_type == 10]) \
    == len(_au_menu.audience["items"]) + 1
_au_none = _au_gsm.GameState()
assert _au_blocks.parse(_au_none, b"COLS" + bytes(8), 0) == 0 and \
    _au_none.audience is None
assert set(_au_blocks.AUDIENCE_IDS) == {57, 58}
ok("open fix 47's DIPL block, as a scratch engine wrote it, parses whole — "
   "the refusal, the greeting, the menu with its enable flags; a tail cut "
   "short, or none, leaves it None; the committed fixture carries no text of "
   "the game's")

# 2. THE CLAIM, both ways, and the states read off the list.
from screens.audience import augeom as _au_geom, auwire as _au_wire
from core import screen_names as _au_names
_au_app, _ = _pv.build_screen(1920, 1080)
_au_d = _au_app.dispatcher
_au_scr = _au_d.screens["audience"]
assert (_au_scr.GAME_SCREEN_ID, tuple(_au_scr.EXTRA_SCREEN_IDS)) == \
    (_au_geom.GAME_SCREEN_ID, _au_geom.EXTRA_SCREEN_IDS) == (57, (58,))
assert all(_au_d.screen_map.get(i) == "audience" and
           _au_names.SCREENS[i] == ("(synthetic)", "audience")
           for i in (57, 58))
_au_bare = _au_fix.state("menu")
_au_bare.audience = None
assert not _au_scr.claims(_au_bare)
_au_d.update_from_game(_au_bare)
assert _au_d.use_original and _au_d.active_name != "audience", \
    "no DIPL: the game's picture, as before"
_au_v = {n: _au_wire.View(_au_fix.state(n))
         for n in ("refused", "greeting", "menu")}
assert (_au_v["menu"].state, _au_v["greeting"].state,
        _au_v["refused"].state) == (_au_wire.MENU, _au_wire.STATEMENT,
                                    _au_wire.STATEMENT)
assert _au_v["refused"].refused and not _au_v["greeting"].refused
assert len(_au_v["menu"].items()) == 4 and _au_v["menu"].title_field.y < \
    _au_v["menu"].items()[0][1].y
_au_odd = _au_fix.state("menu")
_au_odd.fields = _au_odd.fields[:-1]
assert _au_wire.View(_au_odd).state == _au_wire.GAME_BOX
_au_scr.update(_au_odd)
assert _au_scr.handover_is_modal() and _au_scr.wants_original()
_au_d.update_from_game(_au_fix.state("menu"))
assert _au_d.active_name == "audience"
ok("ids 57 and 58 are one screen, claimed only with DIPL: without it the "
   "game's picture, as before; a menu, a statement, a refusal read off the "
   "list, anything else modal")

# 3. WHAT A CLICK SENDS — a fake client records the send path.
import types as _au_ns
from screens.leaders import ldrdraw as _au_nd
_au_log = []
_au_app.client = _au_ns.SimpleNamespace(
    state=_au_fix.state("menu"),
    activate_field=lambda i: _au_log.append(("activate", i)))
_au_app.connected = True
_au_p = _au_d.active
_au_p.update(_au_app.client.state)


def _au_click(x, y):
    _au_log.clear()
    _au_p.handle_click(x, y)
    return list(_au_log)


for _au_item, _au_f in _au_wire.View(_au_app.client.state).items():
    _au_r = _au_nd.rect(_au_p.layout, (_au_f.x, _au_f.y, _au_f.x_end,
                                       _au_f.y_end))
    assert _au_click(_au_r.centerx, _au_r.centery) == (
        [("activate", _au_f.index)] if _au_item["enabled"] else []), \
        _au_item
_au_app.client.state = _au_fix.state("greeting")
_au_p.update(_au_app.client.state)
_au_one = [f for f in _au_app.client.state.fields if f.index][0]
assert _au_click(5, 5) == [("activate", _au_one.index)], \
    "a statement: any click answers it"
_au_src = open(os.path.join(SCREENS_DIR, "audience", "screen.py"),
               encoding="utf-8").read()
assert _au_src.count("activate_field(") == 1 and "inject_" not in _au_src
ok("the audience sends an enabled item's own field, the statement's one "
   "field on any click, and refuses a disabled item")

# 4. IT DRAWS, and its marks are named where the rule says.
_au_fonts = {}
for _au_size in ((1920, 1080), (2576, 1432), (3840, 2160)):
    _au_a, _ = _pv.build_screen(*_au_size)
    _au_gs = _au_fix.state("menu")
    _au_a.dispatcher.update_from_game(_au_gs)
    _au_c = _au_a.dispatcher.active
    _au_c.update(_au_gs)
    assert not _au_c.wants_original(), _au_c.fallback_reason()
    _au_s = pygame.Surface(_au_size)
    _au_fonts[_au_size] = _sd_he.font_sites(_au_c.style,
                                            lambda: _au_c.render(_au_s))
# The words at the size the original's row pitch leaves (part 11 found
# them at 9 native px against the native frame's style 4).
_au_want_px = round(_au_geom.TEXT_PX * _au_nd.native_scale(
    _pv.build_screen(1920, 1080)[1].layout))
assert max(_au_fonts[(1920, 1080)].values()) >= _au_want_px, \
    (_au_fonts[(1920, 1080)], _au_want_px)
assert len(_au_fonts[(1920, 1080)]) >= 2 and not _sd_he.scaled_twice(
    _au_fonts[(1920, 1080)], _au_fonts[(3840, 2160)]), _au_fonts
_au_nmarks = _sd_marks_named("audience", ("audraw.py", "screen.py",
                                          "auwire.py"))
ok(f"the audience draws at 1920, 2576 and 3840 from the recorded menu, its "
   f"text scaled once, and every mark it carries is named in its module "
   f"and the status document ({_au_nmarks} marks)")

# 5. THE ART LOADER, and what the extractor takes (dip_scrn_main.cpp:465-
# 480, :1645-1678: the palette at r, the room at 2r + 13, the ambassador at
# 2r + 14).
from screens.audience import auart as _au_art
import audience_art_extract as _au_ext
_au_empty = _au_art.AudienceArt(os.path.join(os.path.dirname(SCREENS_DIR),
                                             "tools", "fixtures", "none"))
assert not _au_empty.available and "audience_art_extract" in _au_empty.reason
assert _au_empty.picture("rooms", 4) is None
assert [(n, [f(r) for r in (0, 4, 12)]) for n, f in _au_ext.GROUPS] == [
    ("palettes", [0, 4, 12]), ("rooms", [13, 21, 37]),
    ("ambassadors", [14, 22, 38])]
assert _au_ext.FORMAT_VERSION == _au_art.FORMAT_VERSION
ok("the audience's art loader: the player's files absent answer None with a "
   "reason; the extractor takes the source's entries (r, 2r+13, 2r+14)")

# 6. EVERY WAY IN AND OUT the scratch save offers (tools/audience_walk.py
# on a scratch engine with open fixes 46 and 47), each reaching its screen.
# A sequence identical at both window sizes is kept once by the fixture's
# builder, so a way is held at either size.
with open(os.path.join(os.path.dirname(SCREENS_DIR), "tools", "fixtures",
                       "transitions_180.json"), encoding="utf-8") as _au_fh:
    _au_tr = [t for t in _au_json.load(_au_fh)["transitions"]
              if t.get("source", "").startswith("P10_audience_")]
_au_ways = {"races -> audience (race slot 0)": 57,
            "audience -> races (refusal clicked)": 6,
            "races -> audience (race slot 1)": 57,
            "audience -> audience (statement clicked)": 57,
            "audience -> races (Good Bye)": 6}
for _au_way, _au_id in _au_ways.items():
    _au_got = [t for t in _au_tr if t["transition"] == _au_way]
    assert _au_got, f"{_au_way} not recorded"
    assert all(any(_r[1] == _au_id for _r in t["rows"]) for t in _au_got), \
        (_au_way, "never reaches screen", _au_id)
assert {t["source"] for t in _au_tr} == {"P10_audience_1920x1080",
                                         "P10_audience_2576x1432"}
ok(f"every way into and out of the audience the scratch save offers is in "
   f"the replayed set, each reaching its screen ({len(_au_ways)} ways, "
   f"{len(_au_tr)} recorded transitions)")
