# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006h_core_hud_button_glyphs.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 179, part 6: the button icons 169 listed as missing (P11),
# as glyphs drawn from our own coordinates (assets/shared/hud/glyphs.json,
# tools/hud_glyphs.py) — never a MOO2 picture — built beside the cut
# pieces, so they load, tint and are replaced from the mod folder the same
# way; and the one drawing rule: the word stays whole, the icon is drawn
# only where both fit.
#
# The 2 check(s) it holds:
#   - button glyphs: every P11 button named, every glyph used, drawn from coordinates, derived, moddable, tinted
#   - button glyphs: the word stays whole — an icon only where both fit; the screens draw theirs


import json as _bg_json
import shutil as _bg_sh
import tempfile as _bg_tmp

import hud_glyphs as _bg_hg
from core import usermod as _bg_um
from core.hud import art as _bg_art
from core.hud import blocks as _bg_blk
from core.hud import glyphs as _bg_gl
from core.hud import icons as _bg_ic
from core.hud import tint as _bg_tint

_BG_ROOT = os.path.dirname(SCREENS_DIR)
with open(os.path.join(_BG_ROOT, "assets", "shared", "hud", "glyphs.json"),
          encoding="utf-8") as _fh:
    _bg_data = _bg_json.load(_fh)

# 1 — THE DATA: 169's P11 table, every screen of it; each button names a
#     glyph that exists, each glyph is used, each primitive is one the
#     drawer knows, inside its square.
_BG_SCREENS = {"main_menu", "new_game", "custom_race", "empire_identity",
               "select_race", "colony_summary", "planets", "fleets",
               "leaders", "game_menu", "research", "galaxy_map"}
assert {k.split("/")[0] for k in _bg_gl.BUTTONS} == _BG_SCREENS, \
    sorted({k.split("/")[0] for k in _bg_gl.BUTTONS} ^ _BG_SCREENS)
assert set(_bg_gl.BUTTONS.values()) <= set(_bg_gl.GLYPHS), \
    sorted(set(_bg_gl.BUTTONS.values()) - set(_bg_gl.GLYPHS))
assert set(_bg_gl.GLYPHS) <= set(_bg_gl.BUTTONS.values()), \
    f"glyphs no button uses: {sorted(set(_bg_gl.GLYPHS) - set(_bg_gl.BUTTONS.values()))}"
for _bg_n, _bg_prims in _bg_data["glyphs"].items():
    for _bg_p in _bg_prims:
        assert _bg_p[0] in ("line", "poly", "circle", "disc", "arc"), \
            (_bg_n, _bg_p[0])
        _bg_xy = (_bg_p[1] if _bg_p[0] in ("line", "poly")
                  else [_bg_p[1:3]])
        assert all(0 <= _v <= 1 for _pt in _bg_xy for _v in _pt), \
            (_bg_n, _bg_p)
# 2 — DRAWN FROM COORDINATES, DERIVED: two builds are byte-identical, and
#     a glyph is ONE colour — `chosen.glyph.colour` — with its shape in
#     the alpha: nothing in it can have come from a picture.
_bg_style = _bg_json.load(open(os.path.join(
    _BG_ROOT, "assets", "shared", "hud", "style.json")))["chosen"]["glyph"]
_bg_dirs = [_bg_tmp.mkdtemp(prefix="glyphs_") for _ in range(2)]
try:
    _bg_names = [_bg_hg.write(_d) for _d in _bg_dirs][0]
    assert _bg_names == sorted("icon_" + _g for _g in _bg_gl.GLYPHS)
    for _bg_f in _bg_names:
        _bg_a, _bg_b = (open(os.path.join(_d, _bg_f + ".png"), "rb").read()
                        for _d in _bg_dirs)
        assert _bg_a == _bg_b, f"{_bg_f} is not the same twice"
        _bg_img = pygame.image.load(os.path.join(_bg_dirs[0], _bg_f + ".png"))
        assert _bg_img.get_size() == (_bg_style["height"],) * 2
        _bg_px = pygame.surfarray.pixels3d(_bg_img)
        _bg_al = pygame.surfarray.pixels_alpha(_bg_img)
        _bg_on = _bg_px[_bg_al > 0]
        assert len(_bg_on) > 200 and (_bg_on == _bg_style["colour"]).all(), \
            f"{_bg_f} holds a colour that is not the glyph colour"
        del _bg_px, _bg_al
finally:
    for _d in _bg_dirs:
        _bg_sh.rmtree(_d, ignore_errors=True)
# 3 — MODDABLE AND TINTED like the nav glyphs: a piece art loads, a name
#     the mod folder's hud/ accepts (a typo still refused), turned by the
#     frame colour.
for _bg_g in _bg_gl.GLYPHS:
    assert "icon_" + _bg_g in _bg_art.PIECES
    assert "icon_" + _bg_g in _bg_tint.FOLLOWS
assert _bg_um.tree_path("hud/icon_back.png") == \
    "assets/shared/hud/cut/icon_back.png"
assert _bg_um._known("hud/icon_back.png", "assets/shared/hud/cut/icon_back.png",
                     _BG_ROOT)
assert not _bg_um._known("hud/icon_nope.png",
                         "assets/shared/hud/cut/icon_nope.png", _BG_ROOT)
ok(f"button glyphs: {len(_bg_gl.BUTTONS)} buttons of 169's P11 table on "
   f"{len(_BG_SCREENS)} screens, {len(_bg_gl.GLYPHS)} glyphs, each used; "
   f"drawn from coordinates in one colour, derived byte for byte, a mod "
   f"piece, turned by the frame colour")


# 4 — THE WORD STAYS WHOLE. An icon beside a word only where both fit; a
#     narrow button shows its word alone. Then the screens: what they
#     really DRAW (icons.RECORD), not what they ask for.
if _bg_art.available("icon_back"):
    _bg_s = pygame.Surface((400, 100), pygame.SRCALPHA)
    _bg_ic.RECORD = []
    try:
        _bg_cx = _bg_ic.icon_beside(_bg_s, (0, 0, 400, 50), "back", 100)
        assert _bg_cx > 200 and _bg_ic.RECORD == ["back"], \
            (_bg_cx, _bg_ic.RECORD)
        _bg_ic.RECORD = []
        _bg_cx = _bg_ic.icon_beside(_bg_s, (0, 0, 120, 50), "back", 100)
        assert _bg_cx == 60 and _bg_ic.RECORD == [], "a word was crowded"
        _bg_ic.RECORD = []
        _bg_blk.slant_button(_bg_s, (0, 0, 160, 40), 1.0, "normal",
                             "A VERY LONG WORD", icon="back",
                             style_renderer=app.style)
        assert _bg_ic.RECORD == [], "the block drew an icon over a word"
        _bg_blk.slant_button(_bg_s, (0, 0, 380, 40), 1.0, "normal", "OK",
                             icon="back", style_renderer=app.style)
        assert _bg_ic.RECORD == ["back"], _bg_ic.RECORD
        import hud_evidence as _bg_he
        _bg_shown = {}
        for _bg_scr in ("planets", "main_menu", "new_game", "select_race",
                        "fleets", "game_menu_confirm"):
            _bg_ic.RECORD = []
            _bg_he.render(_bg_scr, 1920, 1080)
            _bg_shown[_bg_scr] = set(_bg_ic.RECORD) & set(_bg_gl.GLYPHS)
        _BG_MUST = {"planets": {"shield", "gravity", "leaf", "range", "flag",
                                "outpost", "back"},
                    "main_menu": {"play", "load", "new", "players", "power"},
                    "new_game": {"check", "close"},
                    "select_race": {"back"},
                    "fleets": {"all", "relocate", "trash", "back"},
                    "game_menu_confirm": {"check", "close"}}
        for _bg_scr, _bg_want in _BG_MUST.items():
            assert _bg_want <= _bg_shown[_bg_scr], (
                _bg_scr, sorted(_bg_want - _bg_shown[_bg_scr]))
    finally:
        _bg_ic.RECORD = None
    ok("button glyphs: an icon only where it and the whole word fit (both "
       "drawing paths); Planets, the main menu, New Game, Select Race, "
       "Fleets and the GAME menu's confirmation draw theirs at 1920x1080")
else:
    report("button glyphs NOT built here — python tools/setup.py; the rule "
           "was not drawn")
    ok("button glyphs: drawing rule reported (pieces not built)")
