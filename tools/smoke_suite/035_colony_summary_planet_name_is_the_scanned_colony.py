# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 035_colony_summary_planet_name_is_the_scanned_colony.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - planet_name is the scanned colony's name in header_text, marked HD EXTENSION, and planet_paragra
#   - the figure fills the band or keeps the step's own canvas (four sizes, the snap measured; at the 


# ── THE NAME HEADING, AND font_scale APPLIED ONCE ─────────────
# planet_name is a text box whose runtime text is the scanned
# colony's name in header_text, marked HD EXTENSION; and
# planet_paragraph's font_scale multiplies the reference size
# before the window scale — at 2560x1440 the paragraph's first line
# renders at font_size(value_font * font_scale), not at a size
# scaled twice.
from core import palette as _nh_pal
for _nh_W, _nh_H in ((1920, 1080), (2560, 1440)):
    _nh_app, _nh_scr = _plv.build_screen(_nh_W, _nh_H)
    _nh_app.dispatcher.switch_to("colony_summary")
    _nh_scr.enter(None)
    _nh_scr.update(_plv._Snapshot(_plv.COLONIES))
    _nh_s = pygame.Surface((_nh_W, _nh_H))
    _nh_scr.render(_nh_s)
    _nh_box = next(_b for _b in _nh_scr.boxes if _b.name == "planet_name")
    _nh_row = _nh_scr.selected_row()
    assert _nh_box.text == _nh_row["name"] and tuple(
        _nh_box.text_color) == _nh_pal.require("colony_summary",
                                               "header_text"), (
        f"{_nh_W}x{_nh_H}: planet_name reads {_nh_box.text!r} in "
        f"{_nh_box.text_color}")
    _nh_tb = next(_b for _b in _nh_scr.boxes
                  if _b.name == "planet_paragraph")
    _nh_fs = float(_nh_tb.style.get("font_scale", 1.0))
    _nh_px = _nh_scr.layout.font_size(
        int(round(_ocfg.get("value_font", 20) * _nh_fs)))
    _nh_big = pygame.Rect(0, 0, 3000, 3000)
    _nh_out = pygame.Surface((3000, 3000))
    _nh_out.fill((0, 0, 0))
    _co.render_info(_nh_out, _nh_row, _nh_big, _ocfg, _words,
                    _climates, _nh_scr.layout, _nh_scr.style,
                    text_box=_nh_tb)
    _nh_first = _nh_tb.text.split("\n")[0]
    _nh_want = _nh_scr.style.render_text(_nh_first, _nh_px,
                                         (255, 255, 255)).get_width()
    _nh_ink = pygame.surfarray.array3d(_nh_out).sum(axis=2) > 0
    _nh_line = _nh_ink[:, :_nh_scr.style.render_text(
        "Hg", _nh_px, (255, 255, 255)).get_height()]
    _nh_xs = _np.nonzero(_nh_line.any(axis=1))[0]
    assert len(_nh_xs) and abs(int(_nh_xs.max()) + 1 - _nh_want) <= 3, (
        f"{_nh_W}x{_nh_H}: the paragraph's first line is "
        f"{int(_nh_xs.max()) + 1 if len(_nh_xs) else 0} px wide and "
        f"font_size(value_font x font_scale {_nh_fs}) = {_nh_px} px "
        f"renders it {_nh_want} — scaled more or less than once")
_nh_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonyoutput.py"), encoding="utf-8").read()
assert "THE NAME HEADING — HD EXTENSION" in _nh_src and \
    "HD EXTENSION" in _b3_ref["_brief_97_note"], (
    "the name heading lost its HD EXTENSION marking in colonyoutput "
    "or layout_reference.json")
ok("planet_name is the scanned colony's name in header_text, marked "
   "HD EXTENSION, and planet_paragraph's font_scale is applied once "
   "(1920x1080 and 2560x1440)")

# ── THE FIGURE'S SIZE IS NOT ALWAYS AN INTEGER STEP ─────────
#
# **DEVIATION FROM DECISION 28 — 12 September 2026, Data's
# decision after the A/B/C crops.** The step is still the integer
# the mod contract is written in; the SIZE is the band less the
# plate's line, taken only when that buys at least a quarter of a
# master row. Asserted here as the RULE, at every shipped size,
# with the two properties that make it safe: the size fills the
# band, or it is exactly the step's own canvas.
_fs_dev = (_sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"].get("_figure_size_deviation", ""))
assert "DEVIATION" in _fs_dev and "decision 28" in _fs_dev, (
    "layout.json list._figure_size_deviation no longer marks the "
    "fractional size against the decision it deviates from")
# EACH HOME IS READ WHERE THE MARKING MEANS SOMETHING (work order 128
# F). This loop used to ask for "decision 28" and "DEVIATION" anywhere
# in each whole file, and the fundament passed on words from other
# entries while decision 28's own exception paragraph carried neither
# (found by 127's Stop 1). Now: the fundament's entry 28 itself, the
# docstring of the function that computes the size, the loader's
# constructor, and the status document's own paragraph for the change.
import inspect as _fs_insp
from screens.colony_summary import colonyfigures as _fs_cf
from screens.colony_summary import colonytrack as _fs_track
_fs_norm = lambda _t: " ".join(_t.split())  # noqa: E731
_fs_fund = read_doc(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                 "v3_fundament.md"))
_fs_entry = _fs_fund[_fs_fund.index("**28. Sprites are swapped by step"):]
_fs_entry = _fs_norm(_fs_entry[:_fs_entry.index("**29.")])
assert ("ONE EXCEPTION, AND IT IS MARKED" in _fs_entry
        and "colonytrack.figure_size" in _fs_entry), (
    "fundament decision 28 no longer states its marked exception, the "
    "fractional figure size")
assert "DEVIATION from decision 28" in _fs_norm(
    _fs_track.figure_size.__doc__ or ""), (
    "colonytrack.figure_size no longer marks itself as the DEVIATION "
    "from decision 28")
assert "DEVIATION from decision 28" in _fs_norm(
    _fs_insp.getsource(_fs_cf.FigureSet.__init__)), (
    "colonyfigures.FigureSet no longer names the DEVIATION from "
    "decision 28 it is keyed for")
_fs_status = _fs_norm(open(os.path.join(
    os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
    encoding="utf-8").read())
_fs_para = _fs_status[_fs_status.index("**die Figur füllt die Zeile"):]
_fs_para = _fs_para[:_fs_para.index("This session (")]
assert "DEVIATION from decision 28" in _fs_para, (
    "the status document's paragraph for the fractional figure size "
    "no longer marks it as the DEVIATION from decision 28")

_fs_seen = []
for _fs_spec in ("1920x1080", "2560x1440", "3440x1371", "3840x2160"):
    _fs_W, _fs_H = (int(v) for v in _fs_spec.split("x"))
    _fs_lay = Layout(_fs_W, _fs_H)
    _fs_boxes = {b.name: b for b in _seated(
        os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
        _fs_W, _fs_H)}
    _fs_area = pygame.Rect(*_fs_lay.rect(
        _fs_boxes["list_area"].ref_rect))
    _fs_cfg = _column_cfg(dict(_sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["list"]), _fs_lay)
    _fs_band = _ctk.band_height(_fs_area, _fs_cfg)
    _fs_step = _ctk.figure_step(_fs_area, _fs_cfg)
    _fs_size = _ctk.figure_size(_fs_area, _fs_cfg)
    _fs_plain = _ctk.MASTER_ROWS * _fs_step
    _fs_short = _fs_band - _fs_size
    # THE RULE, BOTH BRANCHES. Filling the band to within the
    # plate's line is the goal; keeping the step's own canvas is
    # what happens when the fractional size would buy less than
    # `FIGURE_SIZE_SNAP`, and then the shortfall is that snap and
    # no more. A size that is neither is a rule nobody wrote.
    if _fs_size == _fs_plain:
        assert _fs_band - _fs_plain - _ctk.PLATE_LINE < \
            _ctk.FIGURE_SIZE_SNAP, (
            f"{_fs_spec}: the figure keeps the step's {_fs_plain} "
            f"px canvas in a {_fs_band} px band — that is "
            f"{_fs_band - _fs_plain} px of empty row, over the "
            f"{_ctk.FIGURE_SIZE_SNAP} px the snap allows")
    else:
        assert _fs_size == _fs_band - _ctk.PLATE_LINE, (
            f"{_fs_spec}: the figure is {_fs_size} px in a "
            f"{_fs_band} px band — a derived size fills the band "
            f"but for the plate's own line")
        assert _fs_size - _fs_plain >= _ctk.FIGURE_SIZE_SNAP, (
            f"{_fs_spec}: the pixel grid was given up for "
            f"{_fs_size - _fs_plain} px, under the snap of "
            f"{_ctk.FIGURE_SIZE_SNAP}")
    # AND THE SOURCE IS THE STEP BELOW IT, which is the mod
    # contract's half of the deviation.
    assert _fs_size // _ctk.MASTER_ROWS == _fs_step, (
        f"{_fs_spec}: a {_fs_size} px figure would be sourced "
        f"from step {_fs_size // _ctk.MASTER_ROWS} and the "
        f"step is {_fs_step} — the @Nx file a mod ships for this "
        f"window would stop being the one that is used")
    _fs_seen.append(f"{_fs_spec} band {_fs_band} step {_fs_step} "
                    f"-> {_fs_size} px"
                    + ("" if _fs_size != _fs_plain else " (snap)"))
report("figure size: " + ", ".join(_fs_seen))

# ── AND WHERE THE STEP WAS INTEGER, NOTHING CHANGED ─────────
# Data's condition on the whole deviation. Two properties, both
# measured: the set is not resampled at all, so the sprites are
# the pixels decision 28 always drew, and the cell pitch is the
# integer one — the pitch is the scale times the original's own
# squish step, and at an integer scale that is the old arithmetic
# exactly.
from screens.colony_summary import colonyfigures as _fs_fig
for _fs_spec in ("1920x1080", "3840x2160"):
    _fs_W, _fs_H = (int(v) for v in _fs_spec.split("x"))
    _fs_app, _fs_scr = _plv.build_screen(_fs_W, _fs_H)
    _fs_app.dispatcher.switch_to("colony_summary")
    _fs_scr.enter(None)
    _fs_scr.update(_plv._Snapshot(_plv.COLONIES))
    _fs_a, _fs_c, _fs_sc, _fs_n = _fs_scr._list_view()
    _fs_set = _fs_fig.set_for(_fs_scr, _fs_a, _fs_c)
    _fs_step = _ctk.figure_step(_fs_a, _fs_c)
    assert _fs_set.size == _ctk.MASTER_ROWS * _fs_step, (
        f"{_fs_spec}: the set is {_fs_set.size} px and the step's "
        f"canvas is {_ctk.MASTER_ROWS * _fs_step}")
    assert not _fs_set.resampled, (
        f"{_fs_spec}: the figure set was RESAMPLED at a window "
        f"where the step is exact — decision 28's own sizes have "
        f"to come through untouched")
    assert _ctk.figure_scale(_fs_a, _fs_c) == float(_fs_step), (
        f"{_fs_spec}: the scale is "
        f"{_ctk.figure_scale(_fs_a, _fs_c)} and the step "
        f"{_fs_step} — every pitch on this screen is that number "
        f"times a native constant")
ok("the figure fills the band or keeps the step's own canvas "
   "(four sizes, the snap measured; at the two exact ones nothing "
   "is resampled and every pitch is the integer's)")
