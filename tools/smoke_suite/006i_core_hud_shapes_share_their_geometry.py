# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 006i_core_hud_shapes_share_their_geometry.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 1 check(s) it holds:
#   - HUD shapes share their geometry: one outline's masks and bands are
#     built once, a memoised shape is byte for byte a cold one, the arrays
#     are read-only, the widths are in the key, the memo is bounded by bytes


# ── ONE GEOMETRY, MANY PANELS (work order 184) ──────────────────
#
# The research panel's first frame built 19 HUD shapes out of 4 outlines —
# eight entry panels of one size at eight positions, eight box panels of
# another, the frame twice — and every one of them recomputed the same
# coverage masks and blurred bands, which are most of a shape's cost:
# 0.5 s of the first entry at 1920, 2.2 s at 3840. `raster._geometry` keeps
# them per outline and `shape` composes each panel's own colours and glass
# over them. The rule held here is the one that makes that a free change:
# A SHAPE FROM THE MEMO IS BYTE FOR BYTE THE SHAPE FROM A COLD MEMO — for a
# filled glass panel and for an outline, with both bands — and the counts
# say the second panel of an outline built nothing. The research renders at
# 1920, 2576 and 3840 (`tools/research_render.py`) were identical before and
# after; this is the rule those renders were a sample of.
import numpy as _sg_np
from core.hud import raster as _sg_r


def _sg_shape(glass, fill_alpha=1.0, edge_w=2.3):
    return _sg_r.shape(
        lambda w, h: _sg_r.chamfered(w, h, 9.0), 180, 90,
        fill=(10, 20, 30), edge=(90, 120, 160), edge_w=edge_w,
        glow=(40, 80, 120), glow_w=3.2, inner=(20, 30, 50), inner_w=14.3,
        fill_alpha=fill_alpha, ss=3, glass=glass)


def _sg_bytes(built):
    return pygame.image.tobytes(built[0], "RGBA"), built[1]


_sg_g1 = _sg_np.full((90, 180, 3), 30.0, _sg_np.float32)
_sg_g2 = _sg_np.linspace(0, 200, 90 * 180 * 3, dtype=_sg_np.float32) \
    .reshape(90, 180, 3)
_sg_cold = []
for _sg_args in ((_sg_g1,), (_sg_g2,), (None, 0.0)):
    _sg_r.clear_geometry()
    _sg_cold.append(_sg_bytes(_sg_shape(*_sg_args)))
assert _sg_cold[0] != _sg_cold[1], "two glasses drew the same panel"
_sg_r.clear_geometry()
_sg_warm = [_sg_bytes(_sg_shape(*_a))
            for _a in ((_sg_g1,), (_sg_g2,), (None, 0.0))]
assert _sg_r.geometry_stats == {"built": 1, "reused": 2}, (
    f"three panels of one outline built {_sg_r.geometry_stats['built']} "
    f"geometries — the memo is not shared")
assert _sg_warm == _sg_cold, (
    "a shape from the memo differs from the same shape built cold — the "
    "memo changes pixels")
# READ-ONLY, so a caller cannot change every later panel of the outline.
_sg_geo = next(iter(_sg_r._GEOMETRY.values()))
for _sg_a in _sg_geo:
    assert _sg_a is not None and not _sg_a.flags.writeable
try:
    _sg_geo[0][0, 0] = 0.5
    raise AssertionError("a memoised mask accepted a write")
except ValueError:
    pass
# THE WIDTHS ARE IN THE KEY: another edge width is another geometry.
_sg_shape(_sg_g1, edge_w=4.0)
assert _sg_r.geometry_stats["built"] == 2, _sg_r.geometry_stats
# BOUNDED BY BYTES: an outline larger than the bound is used, not kept.
_sg_max = _sg_r.GEOMETRY_MAX_BYTES
try:
    _sg_r.clear_geometry()
    _sg_r.GEOMETRY_MAX_BYTES = 1000
    assert _sg_bytes(_sg_shape(_sg_g1)) == _sg_cold[0]
    assert not _sg_r._GEOMETRY and _sg_r._GEOMETRY_BYTES[0] == 0
finally:
    _sg_r.GEOMETRY_MAX_BYTES = _sg_max
    _sg_r.clear_geometry()
ok("HUD shapes share their geometry: one outline's masks and bands are "
   "built once, a memoised shape is byte for byte a cold one, the arrays "
   "are read-only, the widths are in the key, the memo is bounded by bytes")
