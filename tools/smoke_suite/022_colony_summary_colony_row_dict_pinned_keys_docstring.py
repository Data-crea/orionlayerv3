# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 022_colony_summary_colony_row_dict_pinned_keys_docstring.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 3 check(s) it holds:
#   - colony row dict pinned ( keys, docstring and AST agree)
#   - colonyrows imports no pygame at import time ( modules on the graph, function-level imports exclu
#   - population figures: names, step is a swap (28x2/3/4), mod master and per-step files with the ord


# ── THE ROW DICT IS THE INTERFACE, AND IT IS PINNED ──
#
# `build_rows` hands the two renderers plain dicts and its
# docstring lists the keys. The list was PROSE until 7 September
# 2026 — the docstring claimed a check held it and no such check
# existed, which is how `producing_id` and `producing_state`
# could have been added without the fake rows in this file
# following. Read off the source with AST rather than by running
# `build_rows`, which needs a colony blob.
import ast as _ast
_cr_src = open(os.path.join(_proj, "screens", "colony_summary",
                            "colonyrows.py"), encoding="utf-8").read()
_fn = next(n for n in _ast.walk(_ast.parse(_cr_src))
           if isinstance(n, _ast.FunctionDef) and n.name == "build_rows")
_dicts = [n for n in _ast.walk(_fn) if isinstance(n, _ast.Dict)
          and len(n.keys) > 8]
assert len(_dicts) == 1, (
    f"{len(_dicts)} candidate row dicts in build_rows — the pin "
    f"below cannot tell which is the interface any more")
_row_keys = {k.value for k in _dicts[0].keys
             if isinstance(k, _ast.Constant)}
_row_expected = {
    "index", "name", "climate", "pops", "jobs", "cells", "held",
    "no_farming", "max_pop", "producing", "producing_id",
    "producing_state", "producing_turns", "can_buy", "production",
    "drawn_production", "shortage", "size", "gravity", "mineral",
    "growth", "morale", "morale_applies",
    # decision 56: which mask the output panel's morale row wears,
    # decided in colonyrows and handed to the renderer.
    "morale_icon",
}
assert _row_keys == _row_expected, (
    f"the row dict's keys changed. Added: "
    f"{sorted(_row_keys - _row_expected)}; removed: "
    f"{sorted(_row_expected - _row_keys)}. Both renderers and "
    f"every fake row in this file read this set — update them in "
    f"the same commit, which is what this pin is for")
for _doc_key in ("producing_id", "producing_state"):
    assert _doc_key in _fn.body[0].value.value, (
        f"build_rows' docstring no longer lists {_doc_key!r}; the "
        f"docstring IS the interface document for these dicts")
ok(f"colony row dict pinned ({len(_row_expected)} keys, docstring "
   f"and AST agree)")

# ── `colonyrows` IMPORTS NO pygame, AND NOW SOMETHING CHECKS ──
#
# Two files say so and neither could enforce it: `colonyrows`'
# own docstring ("this module imports no pygame and knows
# nothing about pixels"), and `colonyfigures`' header, which
# promises in as many words that "a smoke check walks the import
# graph, because the property had been prose for as long as it
# had been true". It had been prose for exactly that long. Two
# documents asserting a behaviour is not the behaviour —
# decision 51's shape, and the third time this file has met it.
#
# WHY THE GRAPH AND NOT THE FILE. A grep of `colonyrows.py` is
# already green and always would be; the way this property dies
# is TRANSITIVE, through `from . import colonyfigures` at
# colonyrows.py:119. colonyfigures imports pygame INSIDE
# `_load` (colonyfigures.py:256) precisely so it does not reach
# back — move that one line to the top of the file and nothing
# in the tree would have said a word.
#
# MODULE LEVEL ONLY, and that is the whole distinction: an
# import inside a function does not run when the module is
# imported, so it cannot make the importer need pygame. Walking
# `ast.walk` instead of `tree.body` would flag colonyfigures'
# deliberate arrangement as the fault it was built to avoid.
def _import_graph(_start):
    """Project-local modules reachable from `_start` AT IMPORT
        TIME, and every module-level pygame import found on the way.

        Resolves `from core import prodname` — where the name is a
        SUBMODULE and not an attribute — by enqueuing both `core`
        and `core.prodname`; a walk that took only the package would
        stop at `core/__init__.py` and report three clean modules.
        """
    def _path(_m):
        _b = os.path.join(_proj, *_m.split("."))
        for _c in (_b + ".py", os.path.join(_b, "__init__.py")):
            if os.path.exists(_c):
                return _c
        return None

    _seen, _found, _queue = {}, [], [_start]
    while _queue:
        _m = _queue.pop()
        _p = _path(_m)
        if _p is None or _p in _seen:
            continue
        _seen[_p] = _m
        _parts = _m.split(".")
        for _st in _ast.parse(
                open(_p, encoding="utf-8").read()).body:
            if isinstance(_st, _ast.Import):
                _tg = [(_a.name, ()) for _a in _st.names]
            elif isinstance(_st, _ast.ImportFrom):
                _base = _st.module or ""
                if _st.level:          # `from . import x`
                    _up = _parts[:len(_parts) - _st.level]
                    _base = ".".join(
                        _up + ([_base] if _base else []))
                _tg = [(_base, tuple(_a.name for _a in _st.names))]
            else:
                continue
            for _name, _subs in _tg:
                if _name.split(".")[0] == "pygame":
                    _found.append((_m, _st.lineno, _name))
                    continue
                for _cand in (_name,) + tuple(
                        f"{_name}.{_s}" for _s in _subs):
                    if _path(_cand):
                        _queue.append(_cand)
    return _seen, _found

_cr_mod = "screens.colony_summary.colonyrows"
_cr_seen, _cr_pygame = _import_graph(_cr_mod)
assert not _cr_pygame, (
    "the colony row data path reaches pygame at import time: " +
    "; ".join(f"{_m} line {_ln} imports {_n}"
              for _m, _ln, _n in _cr_pygame) +
    ". colonyrows hands the renderer plain dicts and knows "
    "nothing about pixels — that seam is what keeps both halves "
    "under the 300-line guideline (decision 6) and what stops "
    "the renderer reaching back into a struct. If the import is "
    "wanted, move it inside the function that needs a surface, "
    "the way colonyfigures._load does")
# THE WALK HAS TEETH, shown against a module that really does
# import pygame at the top. A graph walk that silently resolved
# nothing would pass the assertion above for the wrong reason,
# and this is the cheapest way to tell the two apart — no
# synthetic file, no temp dir, just a second module in the same
# folder whose answer is known.
_cl_seen, _cl_pygame = _import_graph(
    "screens.colony_summary.colonylist")
assert any(_m == "screens.colony_summary.colonylist"
           for _m, _ln, _n in _cl_pygame), (
    "the import-graph walk did not find pygame in colonylist.py, "
    "which imports it at module level. The walk resolves "
    "nothing, so the colonyrows assertion above is green for no "
    "reason")
# AND IT REACHES PAST THE FIRST HOP. colonyfigures is the module
# the transitive fault would come through, so its presence in
# the reached set is asserted by name rather than by a count
# that any refactor would move.
_cr_files = set(_cr_seen.values())
for _want in (_cr_mod, "screens.colony_summary.colonyfigures",
              "core.prodname", "core.structs.colony"):
    assert _want in _cr_files, (
        f"the walk did not reach {_want}, which colonyrows "
        f"imports. An unreached module is an unchecked one")
ok(f"colonyrows imports no pygame at import time "
   f"({len(_cr_seen)} modules on the graph, function-level "
   f"imports excluded, walk shown to find colonylist's)")

# ── THE POPULATION FIGURES (decision 50) ──
#
# The colony screens draw the player's own RACEICON sprites at an
# integer step. Seven things are asserted here and each is a way
# this has already gone wrong somewhere in this project: a scale
# pretending to be a step, two homes for one number, a hit test
# that follows the ink instead of the slot, and a fallback that
# stops being exercised and rots.
from screens.colony_summary import colonyfigures as _fig
import tempfile as _tf

# 1. THE NAME TABLE IS THE ONE HOME. 54 figures — 13 races x
# three jobs, 13 portraits, native and android — and the count is
# computed from the key tuples, so adding a race moves it.
_fig_names = _fig.all_names()
assert len(_fig_names) == len(_fig.RACE_KEYS) * 4 + 2 == 54, \
    len(_fig_names)
assert len(set(_fig_names)) == len(_fig_names), "duplicate figure name"
assert _fig.RACE_KEYS[5] == "human" and _fig.ROLE_KEYS == (
    "farmer", "worker", "scientist"), (
        "the race or role keys moved. They are enum STOCK_RACE "
        "(orion2_consts.h:444-457) and ECON_FOOD/INDUSTRY/RESEARCH "
        "(:119-121) — the SOURCE's identifiers, never "
        "MOX::_race_names[], which is localised and would make a "
        "mod stop working on a translated install")

# 2. THE STEP IS A SWAP, NOT A SCALE (decision 28). Sizes exactly
# 28 x step, and the step comes from ONE function — the same one
# colonytrack lays the cell pitch with, because a track at 3x
# holding sprites at 2x is a picture nothing would report.
# THE MOD LADDER STARTS AT 2 and the DRAWING ladder at 1: `@1x`
# would be a second name for the 28 px master, and decision 50 is
# one PNG with one documented name.
assert _fig.STEPS == (2, 3, 4), _fig.STEPS
assert _zt.FIGURE_STEPS == (1, 2, 3, 4), _zt.FIGURE_STEPS
# THE STEP IS DERIVED FROM THE BAND, at four windows including one
# BELOW the reference resolution, where the master's own size is
# the only step that fits — 1280x720 gives a 42 px band and even a
# 2x figure needs 57. That window used to fall to 1920x1080's
# entry through `box.closest_resolution`, which is how a table
# keyed on three resolutions answered for a fourth.
_fs_la = colony_rects()["list_area"]
_fs_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"]
# THE RULE, NOT THE LADDER — 12 September 2026. This listed the
# step it expected per window, and the list's HEIGHT decides that:
# the static frame's list hole is 615 ref px where the Stage-A3
# cutout was 649, and 1440p falls from 3 to 2 because its band is
# 82 device px and step 3 needs 85. The ladder was the instance.
# What is asserted is the rule the ladder came out of — the step
# is the largest whose `28*step + 1` fits the band, floored at the
# master's own size — and it is asserted at four windows including
# one BELOW the reference resolution, where 1 is the only step
# that fits. That window used to fall to 1920x1080's entry through
# `box.closest_resolution`, which is how a table keyed on three
# resolutions answered for a fourth.
_steps = {}
for _fw, _fh in ((1280, 720), (1920, 1080), (2560, 1440),
                 (3840, 2160)):
    _fa = pygame.Rect(*Layout(_fw, _fh).rect(_fs_la))
    _got = _fig.figure_step(_fa, _fs_cfg)
    _band = _ctk.band_height(_fa, _fs_cfg)
    _need2 = _ctk.FIGURE_TOP_NATIVE + 28 - _ctk.INK_BOTTOM_MIN
    _want = max([_s for _s in _zt.FIGURE_STEPS
                 if _need2 * _s <= _band] or [min(_zt.FIGURE_STEPS)])
    assert _got == _want, (
        f"figure_step at {_fw}x{_fh} is {_got} and a band of "
        f"{_band} px holds {_want} at {_need2} master rows per "
        f"step — the derivation and its own rule have parted")
    assert _need2 * _got <= _band or _got == min(_zt.FIGURE_STEPS), (
        f"figure_step at {_fw}x{_fh} returns {_got}, whose "
        f"{_need2}*{_got} = {_need2 * _got} does not fit the "
        f"{_band} px band: the figure would start above the cell "
        f"plate's own top line")
    _steps[f"{_fw}x{_fh}"] = _got
report(f"figure steps from the list's height: {_steps}")
for _st in _fig.STEPS:
    assert _fig.step_size(_st) == 28 * _st, _fig.step_size(_st)
    assert _fig.step_name("human_farmer.png", _st) == \
        f"human_farmer@{_st}x.png"
# ONE HOME, still: colonyfigures delegates to colonytrack rather
# than answering separately. Two places computing one step is how
# the pitch and the sprite drift apart by a growing amount with
# nothing on either side reporting it.
_cf_src = open(os.path.join(_proj, "screens", "colony_summary",
                            "colonyfigures.py"), encoding="utf-8").read()
assert "colonytrack.figure_step(area, cfg)" in _cf_src, (
    "colonyfigures no longer delegates the step to colonytrack")

# 3. WHICH SPRITE A POP GETS — `Colony_Pop_Anim_` transcribed
# (colony.cpp:1268-1283), including the ORDER. The conquered test
# is FIRST, so a conquered native draws a portrait and not the
# native sprite; swapping the two reads as a simplification and
# changes the picture.
_races = {0: 5, 1: 10}          # player 0 human, player 1 sakkra
assert _fig.figure_for(0, 5, _races) == "human_farmer.png"
assert _fig.figure_for((2 << 7) | 0, 5, _races) == \
    "human_scientist.png"
assert _fig.figure_for(9, 5, _races) == "native.png"
assert _fig.figure_for(8, 5, _races) == "android.png"
assert _fig.figure_for(0x400 | 1, 5, _races) == "sakkra_portrait.png", (
    "a conquered pop no longer draws ITS OWN race's portrait. "
    "Colony_Pop_Anim_ reads _player[Get_Effective_Pop_Player_(..)]"
    ".race, and the effective player is the pop word's own nibble "
    "— not the colony owner's")
assert _fig.figure_for(0x400 | 9, 5, _races) == "human_portrait.png", (
    "a CONQUERED NATIVE no longer draws a portrait. The 0x400 "
    "test comes before the state dispatch in Colony_Pop_Anim_ "
    "(colony.cpp:1277-1282); reordering them is a one-line "
    "simplification that changes what is on screen")
assert _fig.figure_for(3, 5, {}) is None, (
    "an unknown race no longer answers None. Guessing a race "
    "draws the wrong species, which looks like data and is not")

# 4. AN ABSENT SET IS A STATE, AND THE COLOURED CELLS ARE ITS
# PICTURE. Pointed at an empty root, the loader reports "missing"
# and holds nothing; the renderer takes None and draws the cells
# it has always drawn. **This is why the cell renderer is not on
# Stage 5's deletion list** — it is what an install without the
# extraction sees, not a leftover.
with _tf.TemporaryDirectory() as _empty:
    _none = _fig.FigureSet(app.res, _fig.step_size(2), root=_empty)
    assert _none.state == "missing" and not _none.figures, _none.state
    assert _none.get("human_farmer.png") is None
_cell_surf = pygame.Surface((1920, 1080))
_cell_surf.fill((0, 0, 0))
# The row is BUILT here rather than borrowed from `_rows`, whose
# job split comes from the fixture and could stop having a farmer
# in it without this check saying anything useful.
_cell_row = dict(_rows[1])
_cell_row["jobs"] = [2, 1, 0]
_cell_row["pops"] = 3
_cell_row["cells"] = ((_crw.Cell("", None), _crw.Cell("", None)),
                      (_crw.Cell("", None),), ())
_cl.render(_cell_surf, [_cell_row], _area,
           _column_cfg(_cfg, app.layout, _area), app.layout,
           app.style, 0, 0, None)
_cell_px = pygame.surfarray.array3d(_cell_surf)
assert any(tuple(_cell_px[x, y]) == tuple(_cl.ZONE_COLORS[0][:3])
           for x in range(_area.x, _area.right)
           for y in range(_area.y, _area.bottom)), (
    "with no figure set the farmer cells are not drawn in their "
    "own colour. The coloured cell IS the absent-set state and a "
    "screen that draws neither is the worst of the three")

# 5. A WRONG SIZE IS REFUSED, NOT FITTED — master and step file
# alike, one log line each, and the search moves on to the next
# root so the base figure is what gets drawn.
with _tf.TemporaryDirectory() as _bad:
    _bd = os.path.join(_bad, _fig.FIGURE_DIR)
    os.makedirs(_bd)
    pygame.image.save(pygame.Surface((32, 32), pygame.SRCALPHA),
                      os.path.join(_bd, "human_farmer.png"))
    pygame.image.save(pygame.Surface((99, 99), pygame.SRCALPHA),
                      os.path.join(_bd, "human_worker@2x.png"))
    _bad_set = _fig.FigureSet(app.res, _fig.step_size(2), root=_bad)
    assert len(_bad_set.refused) == 2, _bad_set.refused
    assert _bad_set.state == "missing", (
        "a directory of refused files is not a figure set. "
        "Refusing a file and then reporting the set as usable is "
        "the failure this state exists to name")

# 6. THE ONE-FILE MOD, both conventions, and the ORDER between
# them. A mod that ships ONLY a master must beat the base
# project's step files — which is what `Resources.roots()` is
# for, and what two `resolve` calls would get backwards.
_figs_present = os.path.isdir(os.path.join(_proj, _fig.FIGURE_DIR))
if _figs_present:
    with _tf.TemporaryDirectory() as _mod:
        _md = os.path.join(_mod, _fig.FIGURE_DIR)
        os.makedirs(_md)
        _m = pygame.Surface((28, 28), pygame.SRCALPHA)
        _m.fill((255, 0, 0, 255))
        pygame.image.save(_m, os.path.join(_md, "human_farmer.png"))
        _s3 = pygame.Surface((84, 84), pygame.SRCALPHA)
        _s3.fill((0, 255, 0, 255))
        pygame.image.save(_s3, os.path.join(_md, "human_worker@3x.png"))
        from core.resources import Resources as _Res
        _modres = _Res()
        _modres.mod_dirs = [_mod]
        _set3 = _fig.FigureSet(_modres, _fig.step_size(3))
        assert _set3.state == "ok" and len(_set3.figures) == 54, (
            f"a two-file mod broke the other 52 figures "
            f"({_set3.state}, {len(_set3.figures)})")
        _got = _set3.get("human_farmer.png")
        assert _got.get_size() == (84, 84), _got.get_size()
        assert _got.get_at((42, 42))[:3] == (255, 0, 0), (
            "the mod's MASTER did not win at step 3. A mod that "
            "ships one 28x28 file must beat the base project's "
            "own step files, or a one-file mod is not one file")
        _gotw = _set3.get("human_worker@3x.png".replace("@3x", ""))
        assert _gotw.get_at((42, 42))[:3] == (0, 255, 0), (
            "the mod's explicit @3x file did not win. An author "
            "who draws HD artwork for one resolution supplies one "
            "file and must not have to redraw the other two")
        # AND THE STEP FILE IS PER STEP: at 2x the same mod falls
        # back to the base worker, because it shipped no @2x.
        _set2 = _fig.FigureSet(_modres, _fig.step_size(2))
        _gotw2 = _set2.get("human_worker.png")
        assert _gotw2.get_size() == (56, 56)
        assert _gotw2.get_at((28, 28))[:3] != (0, 255, 0), (
            "the @3x file leaked into step 2. Each step is "
            "replaceable ALONE")

# 7. THE OVERLAP DRAWS LEFT TO RIGHT. `pop_draw_index++` is at
# coldraw.cpp:377, AFTER the draw at :349, so the walk paints
# ascending and each figure covers its left neighbour's right
# edge. At a squished pitch ours must do the same, or the overlap
# is a mirror image of the original's at the same squish.
class _StubSet:
    """Two solid colours, so an overlap is readable in one pixel."""

    def __init__(self, size):
        self._s = {}
        for _n, _c in (("human_farmer.png", (255, 0, 0)),
                       ("native.png", (0, 0, 255))):
            _surf2 = pygame.Surface((size, size))
            _surf2.fill(_c)
            self._s[_n] = _surf2

    def get(self, name):
        return self._s.get(name)

_ov = pygame.Surface((1920, 1080))
_ov.fill((0, 0, 0))
_ovrow = dict(_rows[1])
_ovrow["jobs"] = [8, 0, 0]
_ovrow["pops"] = 8
_ovrow["cells"] = ((_crw.Cell("", "human_farmer.png"),
                    _crw.Cell("native", "native.png")) * 4, (), ())
_cl.render(_ov, [_ovrow], _area, _cfg, app.layout, app.style, 0, 0,
           _StubSet(_fig.step_size(2)))
_ovpx = pygame.surfarray.array3d(_ov)
_red = [x for x in range(_area.x, _area.right)
        for y in [_area.y + 30]
        if tuple(_ovpx[x, y]) == (255, 0, 0)]
_blue = [x for x in range(_area.x, _area.right)
         for y in [_area.y + 30]
         if tuple(_ovpx[x, y]) == (0, 0, 255)]
if _red and _blue:
    assert max(_blue) > max(_red), (
        "the last figure drawn is not the rightmost on the "
        "surface. coldraw.cpp:349 draws and :377 increments, so "
        "the walk is ascending and a later figure covers an "
        "earlier one's right edge")

# 8. THE CLICK IS UNMOVED, AND IT FOLLOWS THE SLOT AND NOT THE
# INK. `case 4` (coldraw.cpp:367) takes the FIRST slot whose
# right edge is at or past the pointer — the LEFTMOST slot, which
# at an overlap is the figure that is partly underneath. The
# original's own click and ink disagree there; transcribing it is
# right and "the click should follow the visible figure" is the
# invention.
from screens.colony_summary import colonyicons as _ci
_cnt = 8
_pitch = _ci.column_pitch(0, _cnt)
assert _pitch < _ci.ICON_SPACING, (
    f"eight farmers no longer squish (pitch {_pitch}); the "
    f"overlap case this asserts does not arise")
_edge0 = _ci.slot_right_edge(0, 0, _cnt)
assert _ci.slot_at(0, _edge0, _cnt) == 0 and \
    _ci.slot_at(0, _edge0 + 1, _cnt) == 1, (
        "slot_at no longer answers by slot boundary. A click one "
        "px past slot 0's right edge belongs to slot 1 even where "
        "slot 0's sprite is still drawn over it")
# 9. THE CLIP IS LOSSLESS, MEASURED ACROSS THE WHOLE SET. A
# stepped figure is taller than its row at 2560x1440 — 84 px
# against 77 — and the row clip has to take that out of empty
# canvas. Every master must therefore carry enough transparent
# rows BELOW its ink, which is why the figure is top-aligned:
# what the clip removes is the bottom of the canvas, never a head.
#
# THE RESERVE ROWS are those transparent rows, and the rule is
# one line: at every step, the overhang must fit in them.
#
# UNTIL 10 SEPTEMBER 2026 THIS WHOLE BLOCK SAT UNDER
# `if _figs_present:` AND THE ok() LINE BELOW CLAIMED "row clip
# loses no ink" EITHER WAY. The figures are extracted from the
# player's own RACEICON.LBX and are not committed (decision 40,
# decision 50), so on a fresh clone — which is every CI machine
# and every new contributor — the measurement did not happen and
# the report said it had. A check that reports a pass it did not
# perform is worse than no check: it is the state decision 51
# calls three documents asserting a behaviour, with nobody left
# to consult. Two things change. The rule is now a function, so
# it can be run against masters that are NOT on this disk; and
# it is run against a synthetic set every time, so the arithmetic
# is exercised on a machine with no figures at all.
def _reserve_rows(_dirpath, _names):
    """Fewest transparent rows below the ink, over `_names`.

        Loaded through `pygame.image.load` and measured with
        `get_bounding_rect`, which is the same pair the drawing path
        uses — a measurement off the file's declared height would
        not see ink that reaches the last row.
        """
    _worst = 28
    for _n in _names:
        _im = pygame.image.load(
            os.path.join(_dirpath, _n)).convert_alpha()
        assert _im.get_size() == (28, 28), (
            f"{_n} is {_im.get_size()} — every RACEICON job "
            f"sprite and both shared sprites are 28x28, measured "
            f"across all 171 entries")
        _worst = min(_worst, 28 - _im.get_bounding_rect().bottom)
    return _worst

def _clip_faults(_reserve):
    """Steps at which the overhang does not fit in the reserve.

        58 is the reference band; the three factors are the shipped
        resolutions' scales. Returns (step, overhang, budget) so the
        message can name the numbers rather than the verdict.
        """
    _out = []
    for _st in _fig.STEPS:
        _rowpx = round(58 * (1.0 if _st == 2 else
                             (4 / 3 if _st == 3 else 2.0)))
        _over = max(0, _fig.step_size(_st) - _rowpx)
        if _over > _reserve * _st:
            _out.append((_st, _over, _reserve * _st))
    return _out

# THE RED RUN, AND IT RUNS ON EVERY MACHINE. One synthetic
# master, ink in the LAST reserve row, is what the rule exists
# to refuse; if `_clip_faults` came back empty for it the green
# verdict below would mean nothing. Ink at (0, 27) leaves zero
# reserve rows, so 3x's seven-pixel overhang has nothing to fall
# into — the same seven pixels the real set clears with two to
# spare.
with _tf.TemporaryDirectory() as _inked:
    _bad = pygame.Surface((28, 28), pygame.SRCALPHA)
    _bad.fill((0, 0, 0, 0))
    _bad.fill((255, 0, 0, 255), pygame.Rect(4, 2, 20, 14))
    _bad.set_at((0, 27), (255, 0, 0, 255))      # in the reserve
    pygame.image.save(_bad, os.path.join(_inked, "inked.png"))
    _bad_reserve = _reserve_rows(_inked, ["inked.png"])
    assert _bad_reserve == 0, _bad_reserve
    _bad_faults = _clip_faults(_bad_reserve)
    assert [f[0] for f in _bad_faults] == [3], (
        f"a master with ink in its last row was not refused at "
        f"3x ({_bad_faults}). 3x is the step that overhangs — 84 "
        f"px of figure into a 77 px band — so a rule that passes "
        f"this file passes anything and the green run below "
        f"proves nothing")
    # AND THE PAIRED GREEN: the same synthetic figure with the
    # reserve rows left empty is accepted. Red and green one
    # after the other is what shows the rule discriminates, and
    # not merely that it refuses.
    _ok_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
    _ok_surf.fill((0, 0, 0, 0))
    _ok_surf.fill((255, 0, 0, 255), pygame.Rect(4, 2, 20, 14))
    pygame.image.save(_ok_surf, os.path.join(_inked, "clean.png"))
    _ok_reserve = _reserve_rows(_inked, ["clean.png"])
    assert _ok_reserve == 12 and not _clip_faults(_ok_reserve), (
        f"the clean synthetic master was refused (reserve "
        f"{_ok_reserve}, faults {_clip_faults(_ok_reserve)}) — "
        f"the rule refuses everything and the red run above is "
        f"not evidence")

# THE GREEN RUN AGAINST THE SHIPPED MASTERS, when they are on
# this disk. The absence is reported in the ok() line rather
# than passed over, because "not measured" and "measured and
# clean" are the two states this check must never blur.
if _figs_present:
    _clip_reserve = _reserve_rows(
        os.path.join(_proj, _fig.FIGURE_DIR), _fig_names)
    _clip_bad = _clip_faults(_clip_reserve)
    assert not _clip_bad, (
        "; ".join(f"at step {_s}x a figure overhangs its row by "
                  f"{_o}px and the emptiest master has only "
                  f"{_b}px of transparent canvas below its ink"
                  for _s, _o, _b in _clip_bad) +
        " — the row clip would cut a figure's feet")
    _clip_note = (f"row clip loses no ink over {len(_fig_names)} "
                  f"masters, {_clip_reserve} reserve rows spare")
else:
    _clip_note = ("row clip NOT MEASURED — no figure set on this "
                  "disk, run `python tools/raceicon_extract.py`")
ok(f"population figures: {len(_fig_names)} names, step is a swap "
   f"(28x2/3/4), mod master and per-step files with the order "
   f"per root, absent set draws cells, ink in the reserve rows "
   f"refused at 3x; {_clip_note})")
