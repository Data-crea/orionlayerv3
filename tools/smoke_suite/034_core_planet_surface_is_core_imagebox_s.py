# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 034_core_planet_surface_is_core_imagebox_s.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - planet_surface is core/imagebox's cover-fill of the scanned colony's tile with the box's own fad


# ── THE SURFACE PICTURE IS A BOX, AND ITS FADE A BOX PROPERTY ──
# Rendered at 1920x1080: the picture box's pixels are exactly what
# core/imagebox draws from the scanned colony's tile with THE BOX'S
# style onto the panel base; its outermost column is the panel base
# itself (the fade reveals what is under the box and types no
# colour); and zeroing `fade_left` in the box's style changes that
# column — so the softness comes from boxes.json and nowhere else.
from core import imagebox as _ib
_ib_boxes = _b3_json.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "boxes.json"), encoding="utf-8"))
for _ib_res, _ib_list in _ib_boxes.items():
    _ib_b = next((_b for _b in _ib_list
                  if _b["name"] == "planet_surface"), None)
    assert _ib_b is not None, f"{_ib_res}: no planet_surface box"
    _ib_st = _ib_b.get("style", {})
    assert _ib_st.get("skin") == "image" and \
        _ib_st.get("fade_left", 0) > 0 and \
        _ib_st.get("fade_right", 0) > 0, (
        f"{_ib_res}: planet_surface's style {_ib_st} does not carry "
        f"both fades as box properties")
_ib_app, _ib_scr = _plv.build_screen(1920, 1080)
_ib_app.dispatcher.switch_to("colony_summary")
_ib_scr.enter(None)
_ib_scr.update(_plv._Snapshot(_plv.COLONIES))
_ib_box = next(_b for _b in _ib_scr.boxes if _b.name == "planet_surface")
_ib_rect = pygame.Rect(*_ib_scr.layout.rect(_ib_box.ref_rect))
_ib_row = _ib_scr.selected_row()
_ib_tile = _sf.set_for(_ib_scr).get(_ib_row["climate"])
assert _ib_tile is not None, "the scanned colony's climate has no tile"

def _ib_frame():
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _ib_scr._surface_cache = {}
    _ib_scr.render(_s)
    return _np.array(pygame.surfarray.array3d(
        _s.subsurface(_ib_rect))).transpose(1, 0, 2)

_ib_got = _ib_frame()
_ib_exp_s = pygame.Surface((1920, 1080))
_ib_exp_s.fill(tuple(_cs_mod.PANEL_BG[:3]))
# ONTO THE SAME PANEL THE SCREEN DRAWS (decision 71, work order 169): the
# window is a HUD panel, whose soft inner band shows through the
# picture's partial alpha along its top and bottom; the reference is
# drawn over that panel, so what is compared is still only imagebox.
from core.hud import blocks as _ib_hud
_ib_hud.panel(_ib_exp_s, pygame.Rect(*_ib_scr.layout.rect(
    _ib_scr.box_rect("colony_panel"))), _ib_scr.layout.scale)
_ib.render_image_box(_ib_exp_s, _ib_scr.layout, _ib_tile,
                     _ib_box.ref_rect, _ib_box.style, {})
_ib_exp = _np.array(pygame.surfarray.array3d(
    _ib_exp_s.subsurface(_ib_rect))).transpose(1, 0, 2)
_ib_band = slice(8, _ib_rect.h - 8)
_ib_cols = slice(40, _ib_rect.w - 40)
assert (_ib_got[_ib_band, _ib_cols] == _ib_exp[_ib_band, _ib_cols]).all(), (
    "planet_surface on the screen is not core/imagebox's drawing of "
    "the scanned colony's tile with the box's own style")
# What is UNDER the box is the HUD panel (decision 71), so the fully
# faded column must be that panel's own pixels, row for row.
_ib_under = pygame.Surface((1920, 1080))
_ib_under.fill(tuple(_cs_mod.PANEL_BG[:3]))
_ib_hud.panel(_ib_under, pygame.Rect(*_ib_scr.layout.rect(
    _ib_scr.box_rect("colony_panel"))), _ib_scr.layout.scale)
_ib_under_a = _np.array(pygame.surfarray.array3d(
    _ib_under.subsurface(_ib_rect))).transpose(1, 0, 2)
assert (_ib_got[_ib_band, 0] == _ib_under_a[_ib_band, 0]).all(), (
    f"the picture's outer column is {_ib_got[_ib_band, 0][0]} and not "
    f"the panel base — the fade is not revealing what is under the box")
_ib_saved = dict(_ib_box.style)
try:
    _ib_box.style["fade_left"] = 0.0
    _ib_flat = _ib_frame()
finally:
    _ib_box.style.clear()
    _ib_box.style.update(_ib_saved)
assert (_ib_flat[_ib_band, 0] != _ib_got[_ib_band, 0]).any(), (
    "zeroing fade_left in the box's style changed nothing — the fade "
    "is not a box property")
ok("planet_surface is core/imagebox's cover-fill of the scanned "
   "colony's tile with the box's own fades, fading into the panel "
   "base, and the softness is boxes.json's (both lists)")
