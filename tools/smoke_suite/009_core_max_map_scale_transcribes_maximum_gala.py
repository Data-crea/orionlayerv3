# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 009_core_max_map_scale_transcribes_maximum_gala.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - max_map_scale transcribes Maximum_Galaxy_Display_Scale_ (73..1023: /951 differ from the retired 


# ── Zoom tables (transcribed from orion2re) ──
from core import zoomtables as zt
# HAROLD::Map_Scale_To_Zoom_Level_
assert [zt.zoom_level(s) for s in (10, 15, 20, 30)] == [0, 1, 2, 3]
# max_zoom_count clamps: a small galaxy never leaves zoom 0
assert zt.zoom_level(30, 0) == 0
# MOX::_star_fields_dim indexed by (zoom + star.size)
assert [zt.star_dimension(sz, 0) for sz in range(3)] == [33, 29, 25]
assert [zt.star_dimension(sz, 3) for sz in range(3)] == [23, 21, 17]
# Draw_Black_Holes_ zoom_dist[] — ignores star.size, 1 and 2 equal
assert [zt.black_hole_dimension(z) for z in range(4)] == [39, 33, 33, 24]
# Star_Scale_Percent_: only shrinks past 72 stars AND scale > 30
assert zt.star_scale_percent(36, 10) == 100
assert zt.star_scale_percent(100, 30) == 100
assert zt.star_scale_percent(100, 40) == 75
# Scale_Star_Dimension_ never goes below 3 px
assert zt.scale_star_dimension(4, 10) == 3
# Animation and names switch off on an extended max view
assert zt.black_hole_animates(36, 10) is True
assert zt.black_hole_animates(100, 40) is False
assert zt.names_suppressed(100, 40, 40) is True
assert zt.names_suppressed(36, 10, 10) is False
# Orbit stack spacing = 11 - zoom
assert [zt.orbit_stack_step(z) for z in range(4)] == [11, 10, 9, 8]
# Ship icon footprint: 13x10 at zoom 0, one px narrower/shorter per
# step. The height must stay BELOW the stack step or four fleets at
# one star would touch — that relation is the reason for the table.
assert [zt.ship_icon_dimension(z) for z in range(4)] == \
    [(11, 10), (10, 9), (9, 8), (8, 7)]
for z in range(4):
    assert zt.ship_icon_dimension(z)[1] < zt.orbit_stack_step(z), z
# Out-of-range zoom clamps instead of raising.
assert zt.ship_icon_dimension(9) == zt.ship_icon_dimension(3)
assert zt.ship_icon_dimension(-1) == zt.ship_icon_dimension(0)
# Monsters have their own per-type footprints, same shrink.
assert zt.monster_icon_dimension("guardian", 0) == (12, 11)
assert zt.monster_icon_dimension("guardian", 3) == (9, 8)
# No monster may tower over the ship: the guardian was 17x16 here
# for a day because a measurement picked up background stars, and
# it read on screen as half again too big. Nothing in the original
# is more than ~1.4x the player ship in either axis.
sw, sh = zt.ship_icon_dimension(0)
for kind in ("guardian", "crystal", "dragon", "hydra", "eel",
             "amoeba", "antaran"):
    mw, mh = zt.monster_icon_dimension(kind, 0)
    assert mw <= sw * 1.4 and mh <= sh * 1.4, (kind, mw, mh)
# An unknown type must not render at a nonsense size.
assert zt.monster_icon_dimension("nessie", 1) == zt.ship_icon_dimension(1)
# _max_map_scale / _max_zoom_count are not serialized by the ext
# API; both must be recoverable from MAP_MAX (mapgen.cpp).
#
# ── THE REFERENCE IS WRITTEN OUT HERE, NOT IMPORTED ──
# A verifier that shares its generation function is blind, so
# this walks the OTHER way round: from the star count through
# MAPGEN::Maximum_Galaxy_Grid_Y_/X_ (mapgen.cpp:49-59) to the
# extent, where zoomtables starts from the extent that arrives on
# the wire. Even the ceiling is spelled differently — `-(-a//b)`
# here against `(a + b - 1) // b` there — so one mistyped idiom
# cannot satisfy both.
def _mgds(star_count):
    """(MAP_MAX_X, MAP_MAX_Y, _max_map_scale) for a Maximum galaxy."""
    gy = 8
    while ((gy * 5 + 3) // 4) * gy < star_count:
        gy += 1
    gx = (gy * 5 + 3) // 4
    cell = (50 * 30) // 10                     # mapgen.cpp:65
    w, h = gx * cell, gy * cell                # mapgen.cpp:1114-1115
    return w, h, max(-(-w * 10 // 506), -(-h * 10 // 400))

def _retired(map_max_x):
    """What stood here until 7 September 2026: round(x / 50.6)."""
    return int(round(map_max_x / 50.6))

# FIXED POINT 1 — the four stock sizes' literals (mapgen.cpp:
# 1078-1110). The switch assigns these outright and never calls
# the function; that ONE expression reproduces all four is what
# lets a single recovery cover five galaxy sizes.
for mx, my, exp_scale, exp_zoom in ((506, 400, 10, 0),
                                    (759, 600, 15, 1),
                                    (1012, 800, 20, 2),
                                    (1518, 1200, 30, 3)):
    assert zt.max_map_scale(mx, my) == exp_scale, (mx, my)
    assert zt.max_zoom_count(mx, my) == exp_zoom, (mx, my)
    assert zt.maximum_galaxy_display_scale(mx, my) == exp_scale, \
        f"the Maximum-size function must reproduce the stock literal " \
        f"{exp_scale} for MAP_MAX {mx}x{my}"

# FIXED POINT 2 — the live probe, 7 September 2026. A generated
# 155-star Maximum galaxy, driven to its own zoom-out limit with
# field 9, reported map_scale 45 where the retired estimate said
# 44 (tools/zoom_check.py: "MEASURED 45 > DERIVED 44"). That run
# is the second source this transcription was accepted on.
assert _mgds(155)[:2] == (2250, 1800), _mgds(155)
assert zt.max_map_scale(2250, 1800) == 45, "live probe 2026-09-07, 155 stars"
assert _retired(2250) == 44, "the estimate this replaced"

# FIXED POINT 3 — the reference save, where the two AGREE. This
# is why the save could not settle the question by itself.
assert _mgds(99)[:2] == (1800, 1350), _mgds(99)
assert zt.max_map_scale(1800, 1350) == 36 == _retired(1800)

# AND NO STOCK WIDTH IS A GRID PRODUCT. The two arms of the
# switch are told apart by MAP_MAX_X alone, so they must not
# overlap: if any of 506/759/1012/1518 were a whole number of
# 150-unit cells, a Maximum galaxy of exactly that width would be
# routed to the literal arm and answered with a stock scale
# instead of its own ceiling.
for _sw in zt.STOCK_MAX_MAP_SCALE:
    assert _sw % zt.MAXIMUM_GALAXY_CELL != 0, (
        f"MAP_MAX_X {_sw} is both a stock literal and {_sw // 150} "
        f"cells of {zt.MAXIMUM_GALAXY_CELL} — a Maximum galaxy that "
        f"wide would take the stock arm and be given "
        f"{zt.STOCK_MAX_MAP_SCALE[_sw]} instead of its own ceiling")

# FIXED POINT 4 — THE Y TERM IS LOAD BEARING. At 35 x 28 cells
# the height ceiling is the larger one, so a recovery that
# ceilings x alone is still one short. This is the half of the
# defect that a MAP_MAX_X-only reading could never have caught.
assert zt.max_map_scale(5250, 4200) == 105, (
    "THE Y TERM HAS BEEN DROPPED. MAP_MAX 5250 x 4200 (35 x 28 cells) "
    "is one of the four widths where ceil(MAP_MAX_Y*10/400) is the "
    "LARGER ceiling: 105 against x's 104. A recovery that reads "
    "MAP_MAX_X alone is still one short here even after it stops "
    "rounding, and the map draws a zoom-out limit one step tighter "
    "than the game's with every number on screen still correct.")
assert -(-5250 * 10 // 506) == 104, "the x ceiling alone"

# THE WHOLE RANGE, against the independent reference.
_differ, _widths, _below = 0, set(), 0
for _n in range(73, 1024):
    _w, _h, _want = _mgds(_n)
    assert zt.max_map_scale(_w, _h) == _want, (_n, _w, _h)
    _old = _retired(_w)
    if _old != _want:
        _differ += 1
        _widths.add(_w)
    if _want < _old:
        _below += 1
# Reported at Stop 1 and reproduced here. If these move, that is
# a finding about the arithmetic, not a test to loosen.
assert _differ == 688, f"{_differ} of 951 differ, expected 688"
assert len(_widths) == 15, sorted(_widths)
assert _below == 0, \
    f"the transcription is BELOW the old estimate at {_below} counts; " \
    f"it must never be — the estimate rounds down from a ceiling"
# NO CALL SITE MAY PASS MAP_MAX_X ALONE. Both extents are on the
# wire and both are required, so a one-argument call is a
# TypeError — but only on the path that runs, and the galaxy
# sizes where the y ceiling wins are exactly the ones no fixture
# reaches. This reads the SOURCE instead, so a forgotten y in a
# branch nobody exercises fails here rather than on somebody's
# Maximum galaxy. It is also what keeps the default from coming
# back: the default existed once, was justified only by a test
# written for it, and had no caller in the tree.
_need_two = ("max_map_scale", "max_zoom_count")
_root = os.path.dirname(SCREENS_DIR)
_thin = []
_scanned = 0
for _dir, _subs, _files in os.walk(_root):
    _subs[:] = [_s2 for _s2 in _subs
                if _s2 not in ("__pycache__", ".git", "assets")]
    for _f in _files:
        if not _f.endswith(".py"):
            continue
        _path = os.path.join(_dir, _f)
        _tree = ast.parse(open(_path, encoding="utf-8").read())
        _scanned += 1
        for _node in ast.walk(_tree):
            if not isinstance(_node, ast.Call):
                continue
            _fn = _node.func
            _name = (_fn.attr if isinstance(_fn, ast.Attribute)
                     else _fn.id if isinstance(_fn, ast.Name) else None)
            if _name not in _need_two:
                continue
            # `f(*pair)` passes both; ast cannot count through it.
            if any(isinstance(_a, ast.Starred) for _a in _node.args):
                continue
            if len(_node.args) + len(_node.keywords) < 2:
                _thin.append(f"{os.path.relpath(_path, _root)}:"
                             f"{_node.lineno} {_name}()")
assert _scanned > 40, f"only {_scanned} python files scanned"
assert not _thin, (
    "these call MAP_MAX recovery with one argument, which means "
    "MAP_MAX_Y is being dropped — the half of the retired estimate "
    f"that no stock-size fixture can catch: {_thin}")
ok("max_map_scale transcribes Maximum_Galaxy_Display_Scale_ "
   f"(73..1023: {_differ}/951 differ from the retired estimate, "
   f"never below; 5 galaxy sizes; both extents required at "
   f"{_scanned} source files)")
