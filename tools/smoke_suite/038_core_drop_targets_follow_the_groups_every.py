# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 038_core_drop_targets_follow_the_groups_every.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 5 check(s) it holds:
#   - drop targets follow the groups (every cell names its own job, every job has a target, the outlin
#   - pop move: the first click and every refusal send NOTHING, the cancel is marked in four homes
#   - held cluster on the pointer (+5/-10 and 20 apart at the sprite step, swapped never scaled, nothi
#   - a drop is resolved by column and never by slot (the icon search is fatal while a cluster is held
#   - pop move message fits spare_panel (wrapped and shrunk, no glyph under the frame's rim, nothing d


ok("drop targets follow the groups (every cell names its own job, "
   "every job has a target, the outline is the target)")

ok("pop move: the first click and every refusal send NOTHING, "
   "the cancel is marked in four homes")

import tempfile as _tf
from screens.colony_summary import colonyfigures as _fig
# ── THE HELD CLUSTER HANGS ON THE POINTER, AT THE SPRITE STEP ──
# `COLMOVE::Draw_Cluster_` (colmove.cpp:7-37) draws each held pop
# at x + 5 + 20*k, y - 10, native, beside a 28 px sprite. HD
# multiplies all three by `FIGURE_STEP`, which is the DEVIATION
# marked in zoomtables — so what has to hold is that the figure
# is the STEP's own size (a swap, decision 28, never a scale) and
# that the offsets moved with it.
#
# The figures are built here rather than read from the tree: they
# are derived from the player's own RACEICON.LBX and are not
# committed (decision 50), so a check that needed them would
# answer differently for a clone that had not run the extractor.
with _tf.TemporaryDirectory() as _hcdir:
    _hcd = os.path.join(_hcdir, _fig.FIGURE_DIR)
    os.makedirs(_hcd)
    _hcm = pygame.Surface((28, 28), pygame.SRCALPHA)
    _hcm.fill((255, 0, 0, 255))
    pygame.image.save(_hcm, os.path.join(_hcd, "human_farmer.png"))
    from core.resources import Resources as _HcRes
    _hcres = _HcRes()
    _hcres.mod_dirs = [_hcdir]
    # THE STEP IS WHATEVER THE LIST'S HEIGHT YIELDS, asked for
    # rather than declared — 12 September 2026. This listed 2/3/4,
    # which is the ladder the Stage-A3 list produced; the static
    # frame's list is 34 ref px shorter and 1440p yields 2. What
    # this block is about is the HELD CLUSTER being drawn at the
    # step the row uses, and that is true at any step.
    for _sw, _sh in ((1920, 1080), (2560, 1440), (3840, 2160)):
        _sa = pygame.Rect(*Layout(_sw, _sh).rect(_fs_la))
        _sc = Layout(_sw, _sh).scale
        _step = _cfig.figure_step(_sa, _fs_cfg)
        assert _step in _fig.STEPS, (
            f"figure_step at {_sw}x{_sh} is {_step}, which is not "
            f"a step the figure masters ship at ({_fig.STEPS})")
        _hcset = _cfig.FigureSet(_hcres, _cfig.step_size(_step))
        _hcsurf = pygame.Surface((600, 400), pygame.SRCALPHA)
        _hcsurf.fill((0, 0, 0, 255))
        _hccells = tuple(_crw.Cell("", "human_farmer.png")
                         for _ in range(3))
        _cl.draw_held_cluster(_hcsurf, (200, 200), _hcset, _hccells,
                              _step)
        _hca = pygame.surfarray.array3d(_hcsurf)
        _hit = [(x, y) for x in range(600) for y in range(400)
                if tuple(_hca[x, y]) == (255, 0, 0)]
        assert _hit, f"step {_step}: the held cluster drew nothing"
        _hx = sorted({x for x, _y in _hit})
        _hy = sorted({y for _x, y in _hit})
        _ox, _oy = _zt.CLUSTER_FIGURE_OFFSET
        assert _hx[0] == 200 + _ox * _step, (
            f"step {_step}: the first figure starts at x={_hx[0]}, "
            f"the pointer + 5*step is {200 + _ox * _step}")
        assert _hy[0] == 200 + _oy * _step, (
            f"step {_step}: the figures start at y={_hy[0]}, the "
            f"pointer - 10*step is {200 + _oy * _step}")
        # SWAP, NEVER SCALE: the drawn figure is exactly the
        # step's size, so a fractional resize would show here as
        # a width that is not 28 * step.
        assert _hy[-1] - _hy[0] + 1 == 28 * _step, (
            f"step {_step}: the held figure is "
            f"{_hy[-1] - _hy[0] + 1} px tall, not {28 * _step} — "
            f"a sprite is swapped by step and never scaled "
            f"(decision 28)")
        # AND THE PITCH IS 20 * step, not the icon spacing and
        # not the squished column pitch.
        _pitch = _zt.CLUSTER_FIGURE_PITCH * _step
        assert _hx[-1] - _hx[0] + 1 == 28 * _step + 2 * _pitch, (
            f"step {_step}: three held figures span "
            f"{_hx[-1] - _hx[0] + 1} px; 20*step between them "
            f"makes {28 * _step + 2 * _pitch}")
    # AND NOTHING WITHOUT FIGURES. The coloured cell is the row's
    # absent-set picture; a coloured square on the POINTER would
    # be a shape the original never has.
    _hcsurf = pygame.Surface((600, 400), pygame.SRCALPHA)
    _hcsurf.fill((0, 0, 0, 255))
    _cl.draw_held_cluster(_hcsurf, (200, 200), None,
                          (_crw.Cell("", "human_farmer.png"),), 2)
    assert not pygame.surfarray.array3d(_hcsurf).any(), (
        "the held cluster drew something with no figure set")
ok("held cluster on the pointer (+5/-10 and 20 apart at the "
   "sprite step, swapped never scaled, nothing without figures)")

# ── A PICK DOES NOT ROUTE THROUGH THE SLOT SEARCH ──
# The original never runs its icon hit test while a cluster is
# held: `Get_Selected_Pop_` is reached only when
# `_cluster_colony_n == -1` (colsum.cpp:862), and with one in hand
# the click goes straight to `Send_Cluster_` (:869) — the FIELD
# decides, not the slot. Asserted by making the search fatal and
# driving a real drop through the screen, because "the code does
# not call it" is what a reader claims and this is what a run
# proves.
_slot_calls = []

def _forbid(name, real):
    def _fn(*a, **kw):
        _slot_calls.append(name)
        return real(*a, **kw)
    return _fn

_sl_saved = (_ci.slot_at, _ci.slot_pop, _cl.cell_at_x)
_ci.slot_at = _forbid("slot_at", _sl_saved[0])
_ci.slot_pop = _forbid("slot_pop", _sl_saved[1])
_cl.cell_at_x = _forbid("cell_at_x", _sl_saved[2])
try:
    _scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
    assert _scr_op._move.pick is not None, (
        "the pick-up did not take; the rest of this check would "
        "be vacuous")
    assert _slot_calls, (
        "the PICK-UP reached no slot search at all — it is "
        "supposed to, and a check that cannot see the call it "
        "forbids proves nothing about the drop")
    _slot_calls.clear()
    _scr_op.handle_click(*_band_xy(_mv_row, _mv_target))
finally:
    _ci.slot_at, _ci.slot_pop, _cl.cell_at_x = _sl_saved
assert not _slot_calls, (
    f"a drop reached the slot search ({sorted(set(_slot_calls))}). "
    f"With a cluster held the original resolves a click by FIELD "
    f"— which job column it landed in — and never by icon "
    f"(colsum.cpp:862-869)")
_scr_op._move.pick = None
_scr_op._move.send = None
_scr_op._rebuild_rows()
ok("a drop is resolved by column and never by slot (the icon "
   "search is fatal while a cluster is held)")

# ── And the sentence has to FIT the panel it is drawn in ──────
# Found by rendering it and looking, which is the only thing that
# could: at one line and 18 px the longest of these messages —
# a rule plus its count — ran past `spare_panel` on both sides
# and lost its first and last characters under the frame's metal.
# Every value was right and the text was drawn, so a check that
# asked "did it draw ink?" would have passed. Decision 44's class
# A rule, met from a new direction.
_fit_msg = _cp.message(_mv_words, _cp.Refusal(_cm.REFUSE_JOB_FULL,
                                              landed=2, carried=10,
                                              total=12))
_fit_box = _scr_op.box_rect("planet_info")
assert _fit_box, "spare_panel is where the move message goes"
_fit_rect = pygame.Rect(*app.layout.rect(_fit_box))
_fit_px = app.layout.font_size(_mv_words.get("font", 18))
_fit_surf = pygame.Surface((_fit_rect.right + 8, _fit_rect.bottom + 8))
_fit_surf.fill((0, 0, 0))
_fit_ctl = _cmu.MoveController()
_fit_ctl.message = _fit_msg
_fit_ctl.draw_message(_fit_surf, _fit_rect, _fit_px, app.style,
                      (255, 255, 255))
_fit_ink = pygame.surfarray.array3d(_fit_surf).sum(axis=2)
_fit_cols = [x for x in range(_fit_surf.get_width())
             if _fit_ink[x].any()]
_fit_rows = [y for y in range(_fit_surf.get_height())
             if _fit_ink[:, y].any()]
assert _fit_cols and _fit_rows, "the message drew nothing at all"
_fit_inset = max(2, _fit_px // 2)
_fit_in = _fit_rect.inflate(-2 * _fit_inset, -2 * _fit_inset)
assert (_fit_in.left <= min(_fit_cols) and max(_fit_cols) <= _fit_in.right
        and _fit_in.top <= min(_fit_rows)
        and max(_fit_rows) <= _fit_in.bottom), (
    f"the move message runs from x {min(_fit_cols)}..{max(_fit_cols)}, "
    f"y {min(_fit_rows)}..{max(_fit_rows)}, outside {_fit_in} — a "
    f"glyph past a cutout's edge is drawn under the frame's rim "
    f"and the panel is a cutout (fundament 44)")
# NOTHING IS TRUNCATED to make it fit: the wrap shrinks the size
# and leaves a too-wide word whole, because losing a character is
# not one of the outcomes.
_fit_lines = _textfit.wrap_text(app.style, _fit_msg, _fit_px,
                                _fit_rect.w - 2 * _fit_inset)
assert " ".join(_fit_lines).split() == _fit_msg.split(), (
    f"the wrap dropped words: {_fit_lines}")
ok("pop move message fits spare_panel (wrapped and shrunk, no "
   "glyph under the frame's rim, nothing dropped)")
