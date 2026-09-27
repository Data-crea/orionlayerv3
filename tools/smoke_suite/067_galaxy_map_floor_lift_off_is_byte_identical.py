# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 067_galaxy_map_floor_lift_off_is_byte_identical.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 4 check(s) it holds:
#   - floor lift: off is byte-identical on the graphic and on the map_background fill; light and haze 
#   - floor lift: exactly one application point in _render_map, after both floor paths and before the 
#   - floor lift once per picture (184): the lifted copy is blit + apply byte for byte, made once per picture and step, rebuilt for a new step or a new picture, never for off
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
# SINCE WORK ORDER 170 the floor is drawn over the whole window by ONE
# function, `floorlift.render_floor`, which `_render_map` calls first:
# the application point moved there with it, and is held there.
_fl_src_txt = open(os.path.join(SCREENS_DIR, "galaxy_map", "screen.py"),
                   encoding="utf-8").read()
_fl_mod_txt = open(os.path.join(SCREENS_DIR, "galaxy_map", "floorlift.py"),
                   encoding="utf-8").read()
assert "floorlift.apply(" not in _fl_src_txt, \
    "the floor lift is applied at more than one point"
_fl_body = _fl_mod_txt.split("def render_floor(", 1)[1]
# SINCE WORK ORDER 184 the picture path blits a lifted COPY (`_lifted`,
# made once per picture and step) and the fill path lifts in place: two
# call sites of the one function `apply`, one per floor path, both before
# the star field — and `apply` itself is still the only thing that adds.
_fl_lb = _fl_mod_txt.split("def _lifted(", 1)[1].split("\ndef ", 1)[0]
assert _fl_body.count("apply(") == 1 and _fl_lb.count("apply(") == 1, \
    "the floor lift is applied at more than one point per floor path"
assert _fl_mod_txt.count("special_flags=pygame.BLEND_RGB_ADD") == 1, \
    "a second adding place"
assert "OLED floor lift (HD EXTENSION" in _fl_body, \
    "the call site lost its HD EXTENSION marking"
_fl_at = _fl_body.index("apply(")
_fl_star = _fl_body.index("_starfield.render(")
assert _fl_body.index("_lifted(scaled") < _fl_star
assert _fl_body.index("surface.fill(MAP_BG") < _fl_at < _fl_star
_fl_rm = _fl_src_txt.split("def _render_map(", 1)[1].split("\n    def ", 1)[0]
assert "self._render_floor(" in _fl_rm.split("set_clip", 1)[0], \
    "_render_map no longer draws the floor first"
ok("floor lift: exactly one application point, in the floor that "
   "_render_map draws first, after both floor paths and before the star "
   "field")

# 14. THE LIFT ONCE PER PICTURE, NOT ONCE PER FRAME (work order 184).
#     The additive fill of the whole window was most of a map frame (33,
#     59, 130 ms at 1920, 2576, 3840) — and of the research panel's first
#     frame, which is drawn over the map. The picture is lifted once, as
#     a copy, and blitted; it is opaque, so that is the old blit + add
#     byte for byte. Held: the equality, one copy per picture and step,
#     a rebuild for a new step and for a new picture of the SAME size
#     (the entry holds the picture, never its size or id), and nothing
#     for off.
class _FlScr:
    pass


def _fl_screen(step, pic):
    _s = _FlScr()
    _s.app = _FlApp(step)
    _s.app.win_w, _s.app.win_h = pic.get_size()
    _s._map_bg_scaled = pic
    return _s


def _fl_draw(step, pic):
    _out = pygame.Surface(pic.get_size())
    _out.fill((1, 2, 3))
    _fl.render_floor(_fl_screen(step, pic), _out)
    return pygame.image.tobytes(_out, "RGB")


_fl_pic = pygame.transform.smoothscale(_fl_floor, (96, 54))
assert _fl_pic.get_flags() & pygame.SRCALPHA == 0 and \
    _fl_pic.get_colorkey() is None, "the floor picture is not opaque"
_fl_calls = []
_fl_real_apply = _fl.apply


def _fl_counted(*a):
    _fl_calls.append(a[1])
    return _fl_real_apply(*a)


_fl.apply = _fl_counted
try:
    for _fl_step in ("light", "haze"):
        _fl._LAST[0] = None
        _fl_want = pygame.Surface(_fl_pic.get_size())
        _fl_want.blit(_fl_pic, (0, 0))
        _fl_real_apply(_fl_want, _fl_want.get_rect(), _FlApp(_fl_step))
        del _fl_calls[:]
        assert _fl_draw(_fl_step, _fl_pic) == pygame.image.tobytes(
            _fl_want, "RGB"), f"{_fl_step}: the lifted copy is not blit + add"
        assert len(_fl_calls) == 1, _fl_calls
        _fl_first = _fl._LAST[0][2]
        assert _fl_draw(_fl_step, _fl_pic) == pygame.image.tobytes(
            _fl_want, "RGB") and len(_fl_calls) == 1 and \
            _fl._LAST[0][2] is _fl_first, "the lift was redone for a frame"
    # a new step: rebuilt, and right
    _fl_draw("light", _fl_pic)
    assert _fl._LAST[0][1] == tuple(_fl.LIFT["light"][:3])
    # a new picture of the same size: rebuilt, never mistaken for the old
    _fl_other = _fl_pic.copy()
    _fl_other.fill((40, 0, 0), (0, 0, 20, 20))
    _fl_n = len(_fl_calls)
    _fl_got = _fl_draw("light", _fl_other)
    assert len(_fl_calls) == _fl_n + 1 and _fl._LAST[0][0] is _fl_other
    _fl_want = _fl_other.copy()
    _fl_real_apply(_fl_want, _fl_want.get_rect(), _FlApp("light"))
    assert _fl_got == pygame.image.tobytes(_fl_want, "RGB")
    # off: the plain picture, no copy made
    _fl_n, _fl_last = len(_fl_calls), _fl._LAST[0]
    assert _fl_draw("off", _fl_pic) == pygame.image.tobytes(_fl_pic, "RGB")
    assert len(_fl_calls) == _fl_n and _fl._LAST[0] is _fl_last
finally:
    _fl.apply = _fl_real_apply
    _fl._LAST[0] = None
ok("floor lift once per picture: the lifted copy is blit + apply byte for "
   "byte, made once per picture and step, rebuilt for a new step or a new "
   "picture, never for off")

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
