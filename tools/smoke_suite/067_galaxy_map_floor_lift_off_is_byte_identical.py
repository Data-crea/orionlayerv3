# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 067_galaxy_map_floor_lift_off_is_byte_identical.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - floor lift: off is byte-identical on the graphic and on the map_background fill; light and haze 
#   - floor lift: exactly one application point in _render_map, after both floor paths and before the 
#   - GAME menu: the six measured field lists classify as their own node, field 0 ignored, multiplayer


# ── Map floor lift (fundament 63, an HD EXTENSION) ──
from screens.galaxy_map import floorlift as _fl

class _FlApp:
    def __init__(self, step):
        self.user_settings = _us.UserSettings({"floor_lift": step})

# 12. OFF IS INVISIBLE, AND THE LIFT IS EXACTLY THE LIFT, on both floor
#     paths: the graphic and the map_background fill.
assert "HD EXTENSION" in (_fl.__doc__ or ""), "floorlift lost its marking"
_fl_png = os.path.join(SCREENS_DIR, "galaxy_map", "assets",
                       "map_background.png")
_fl_floor = pygame.image.load(_fl_png).convert()
_fl_fill = pygame.Surface((64, 32))
from screens.galaxy_map.screen import MAP_BG as _fl_bg
_fl_fill.fill(_fl_bg[:3])
for _fl_src in (_fl_floor, _fl_fill):
    _fl_rect = _fl_src.get_rect()
    _fl_ref = pygame.image.tobytes(_fl_src, "RGB")
    _fl_off = _fl_src.copy()
    assert _fl.apply(_fl_off, _fl_rect, _FlApp("off")) == (0, 0, 0)
    assert pygame.image.tobytes(_fl_off, "RGB") == _fl_ref, \
        "floor lift OFF changed the floor"
    assert _fl.apply(_fl_src.copy(), _fl_rect, object()) == (0, 0, 0)
    for _fl_step in ("light", "haze"):
        _fl_lift = tuple(_fl.LIFT[_fl_step][:3])
        _fl_out = _fl_src.copy()
        _fl.apply(_fl_out, _fl_rect, _FlApp(_fl_step))
        _fl_want = _fl_src.copy()
        _fl_want.fill(_fl_lift)
        _fl_want.blit(_fl_src, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        assert pygame.image.tobytes(_fl_out, "RGB") == \
            pygame.image.tobytes(_fl_want, "RGB"), (
            f"floor lift {_fl_step}: the additive fill differs from fill "
            f"plus additive blit")
_fl_px = _fl_fill.copy()
_fl.apply(_fl_px, _fl_px.get_rect(), _FlApp("light"))
assert tuple(_fl_px.get_at((0, 0)))[:3] == tuple(
    min(255, a + b) for a, b in zip(_fl_bg[:3], _fl.LIFT["light"]))
ok("floor lift: off is byte-identical on the graphic and on the "
   "map_background fill; light and haze equal fill + additive blit")

# 13. ONE APPLICATION POINT, after both floor paths and before the
#     star field — so nothing else on the map is lifted.
_fl_src_txt = open(os.path.join(SCREENS_DIR, "galaxy_map", "screen.py"),
                   encoding="utf-8").read()
assert _fl_src_txt.count("floorlift.apply(") == 1, \
    "the floor lift is applied at more than one point"
assert "OLED floor lift: HD EXTENSION" in _fl_src_txt, \
    "the call site lost its HD EXTENSION marking"
_fl_body = _fl_src_txt.split("def _render_map(", 1)[1].split("\n    def ", 1)[0]
_fl_at = _fl_body.index("floorlift.apply(")
assert _fl_body.index("surface.blit(self._map_bg_scaled") < _fl_at
assert _fl_body.index("surface.fill(MAP_BG") < _fl_at
assert _fl_at < _fl_body.index("self._starfield.render(")
ok("floor lift: exactly one application point in _render_map, after both "
   "floor paths and before the star field")

# ── GAME menu overlay (work order Stop 2, 14 September 2026) ──
import json as _gm_json
from core.game_state import FieldInfo as _GmField, GameState as _GmState
from core import game_client as _gm_gc, injection as _gm_inj
from core import wire_protocol as _gm_wp
from core.structs import settings as _gm_set
from screens.game_menu import gmdraw as _gm_draw, nodes as _gm_nodes

def _gmd_word(_scr, _k):
    return _gm_draw.word(_scr, "menu", _k)

_gm_fix = _gm_json.load(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "game_menu_fields.json")))

def _gm_fields(rows):
    out = []
    for _r in rows:
        _f = _GmField()
        (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
         _f.hotkey) = _r
        out.append(_f)
    return out

# 1. EVERY MEASURED LIST IS ITS OWN NODE, field 0 never counted, a
#    multiplayer menu (no LOAD, no NEW) still a menu, the galaxy
#    map's list none of them.
for _gm_node in ("menu", "settings", "load", "save", "confirm",
                 "warning"):
    assert _gm_nodes.classify(_gm_fields(_gm_fix[_gm_node])) == \
        _gm_node, _gm_node
assert _gm_nodes.classify(_gm_fields(_gm_fix["galaxy_map"])) is None
_gm_mp = [r for r in _gm_fix["menu"] if r[6] not in (ord("L"), ord("N"))]
assert _gm_nodes.classify(_gm_fields(_gm_mp)) == "menu"
_gm_z = [[0, 999, 999, 999, 999, 0, ord("S")]] + _gm_fix["warning"][1:]
assert _gm_nodes.classify(_gm_fields(_gm_z)) == "warning", \
    "field 0 decided a classification"
ok("GAME menu: the six measured field lists classify as their own "
   "node, field 0 ignored, multiplayer menu kept, galaxy list none")
