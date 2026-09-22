# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 032_colony_summary_a_click_on_the_centre_of.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - a click on the centre of a figure's visible area picks up that figure — 1 to 20 figures in every
#   - the planet discs are the climate enum's, px square, on the true pixel grid and masked by a circl
#   - every row's disc is the one its climate selects, clear of the name's ink, and planet_info's line
#   - the output icons are px as output.icon_size declares, both morale masks on one footprint, blank 
#   - every planet_output row wears the icon its id or morale sign selects, no taller than its row, on
#   - the output icons are marked DEVIATION and the separators HD EXTENSION in colonyoutput, colonyout
#   - the list palette is Data's table in the default skin (seven keys to the hex), nav_background and
#   - the list stripes A/B by list index (holds under a one-row scroll) and fills the scanned colony's


# ── A CLICK ON A FIGURE AS SEEN PICKS UP THAT FIGURE ────────
#
# Reported 16 September 2026: "with stacked figures you have to
# click LEFT of the figure you want to move". Draw and hit test
# were never two copies — both read `row_boxes` — but the hit
# test answered the slot the sprite is BLITTED at (`rect.x` to
# `rect.x + cell_w`), and the figure is SEEN elsewhere: its ink
# starts a master column or more into the 28 px canvas, runs past
# the slot into the next one, and shows through the next figure's
# transparent columns. Measured on the extracted figures before
# the fix: 165 of 210 figure centres at 1920x1080 picked up a
# neighbour or nothing. `colonytrack.pick_zones` is the one home
# now, and this asserts its rule, not its arithmetic.
#
# READ OFF THE RENDER. Every figure is drawn through the real
# screen, each in its own colour (only the sprite lookup is
# wrapped, the blit and its geometry are the screen's), and the
# centre of the pixels that are still ITS colour on screen is
# clicked. Every count from 1 to 20, in each of the three job
# columns, at three resolutions.
#
# SYNTHETIC FIGURES, shaped like the game's: the extracted ones
# are not committed (decision 50), and a check that needs them
# answers differently in a clone. The silhouette is narrow at the
# head and legs and wide at the arms and starts one column into
# the canvas, which is what makes a neighbour's transparent
# columns show the figure behind. The extracted set is measured
# the same way when it is on this disk (a report, not the check).
from screens.colony_summary import colonyfigures as _pz_fig
from screens.colony_summary import colonylist as _pz_cl
from screens.colony_summary import colonytrack as _pz_ct
import numpy as _pz_np
_pz_src = open(os.path.join(_proj, "screens", "colony_summary",
                            "colonytrack.py"), encoding="utf-8").read()
assert ("THE COVERING FIGURE KEEPS THE OVERLAP, AS IN THE ORIGINAL"
        in _pz_src and "that is a DEVIATION" in _pz_src
        and "coldraw.cpp:362-366" in _pz_src), (
    "colonytrack.pick_zones lost its marking: the covering figure's "
    "rule is the original's (coldraw.cpp:362-366), measured on the "
    "ink instead of the canvas, and that is a DEVIATION")
_pz_mv = open(os.path.join(_proj, "screens", "colony_summary",
                           "colonymoveui.py"), encoding="utf-8").read()
assert "cell_at_x(area, cfg, scale, row, x, figures)" in _pz_mv, (
    "the pick-up no longer passes the figure set the row is drawn "
    "with; without it a click answers the blit slot, not the figure")

def _pz_master():
    _m = pygame.Surface((28, 28), pygame.SRCALPHA)
    _m.fill((0, 0, 0, 0))
    _ink = (200, 200, 200, 255)
    for _r in ((8, 1, 6, 7), (4, 8, 13, 11), (1, 9, 3, 7),
               (17, 9, 3, 7), (5, 19, 4, 8), (11, 19, 4, 8)):
        _m.fill(_ink, _r)
    return _m

def _pz_colour(_job, _index):
    return (30 + _index * 11, 40 + _job * 70, 250)

def _pz_measure(_W, _H, _set_for):
    """[(count, job, index, visible centre, answer)] for every
        figure that is not what a click on it picks up."""
    _real = _pz_cl._figure_for_cell

    def _tagged(_figs, _cells, _job, _index):
        _s = _real(_figs, _cells, _job, _index)
        if _s is None:
            return None
        _t = _s.copy()
        _t.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
        _t.fill((*_pz_colour(_job, _index), 255),
                special_flags=pygame.BLEND_RGBA_MULT)
        return _t

    _rows_all = [(_n, _j) for _n in range(1, 21) for _j in range(3)]
    _bad, _seen = [], 0
    _pz_cl._figure_for_cell = _tagged
    try:
        for _b in range(0, len(_rows_all), 10):
            _batch = _rows_all[_b:_b + 10]
            _app, _scr = _plv.build_screen(_W, _H)
            _app.dispatcher.switch_to("colony_summary")
            _scr.enter(None)
            _scr.update(_plv._Snapshot([
                dict(star=f"P{_n}x{_j}", numeral=0, climate=5, size=4,
                     pops=_n, jobs=tuple(_n if _k == _j else 0
                                         for _k in range(3)),
                     max_farms=255, production=(1, 1, 1, 1), why="pick")
                for _n, _j in _batch]))
            _area, _cfg, _scale, _ = _scr._list_view()
            _figs = _set_for(_scr, _area, _cfg)
            if _figs is None:
                return None, 0
            _surf = pygame.Surface((_W, _H))
            _surf.fill((0, 0, 0))
            _scr.render(_surf)
            _px = pygame.surfarray.array3d(_surf).transpose(1, 0, 2)
            _bands = _pz_ct.row_bands(_area, _cfg, _scale,
                                      len(_scr._rows))
            for (_top, _bh), _row in zip(_bands, _scr._rows):
                _count = sum(len(_c) for _c in _row["cells"])
                _band = _px[_top:_top + _bh]
                for _job, _index, _rect in _pz_ct.row_boxes(
                        _area, _cfg, _scale, _row, (_top, _bh)).cells:
                    _xs = _pz_np.where(_pz_np.all(
                        _band == _pz_np.array(_pz_colour(_job, _index)),
                        axis=2))[1]
                    assert len(_xs), (
                        f"{_W}x{_H}: figure {_index} of {_count} in job "
                        f"{_job} is not visible at all")
                    _cx = int(round(float(_xs.mean())))
                    _seen += 1
                    _got = _pz_cl.cell_at_x(_area, _cfg, _scale, _row,
                                            _cx, _figs)
                    if _got != (_job, _index):
                        _bad.append((_count, _job, _index, _cx, _got))
            _pz_counts = sorted({sum(len(_c) for _c in _r["cells"])
                                 for _r in _scr._rows})
            assert _pz_counts == sorted({_n for _n, _j in _batch}), (
                f"the screen built rows of {_pz_counts} figures, the "
                f"check asked for {sorted({_n for _n, _j in _batch})}")
    finally:
        _pz_cl._figure_for_cell = _real
    return _bad, _seen

if slow("figure_pick"):
    with _tf.TemporaryDirectory() as _pz_dir:
        os.makedirs(os.path.join(_pz_dir, _pz_fig.FIGURE_DIR))
        _pz_m = _pz_master()
        for _name in _pz_fig.all_names():
            pygame.image.save(_pz_m, os.path.join(
                _pz_dir, _pz_fig.FIGURE_DIR, _name))

        def _pz_synthetic(_scr, _area, _cfg):
            # Seated in the app's own cache, so the RENDER draws it.
            _size = _pz_ct.figure_size(_area, _cfg)
            _set = _pz_fig.FigureSet(_scr.app.res, _size, root=_pz_dir)
            assert _set.state == "ok", _set.state
            _scr.app.figure_sets = collections.OrderedDict({_size: _set})
            return _set

        _pz_total = 0
        for _W, _H in ((1920, 1080), (2560, 1440), (3840, 2160)):
            _bad, _seen = _pz_measure(_W, _H, _pz_synthetic)
            assert _seen == 3 * sum(range(1, 21)), (_W, _H, _seen)
            assert not _bad, (
                f"{_W}x{_H}: {len(_bad)} of {_seen} figures are not what a "
                f"click on the centre of their visible area picks up — "
                f"(count, job, index, x, picked) {_bad[:6]}")
            _pz_total += _seen
    for _W, _H in ((1920, 1080), (2560, 1440), (3840, 2160)):
        _bad, _seen = _pz_measure(
            _W, _H, lambda _s, _a, _c: (
                lambda _f: _f if _f is not None and _f.state == "ok"
                else None)(_pz_fig.set_for(_s, _a, _c)))
        if _bad is None:
            report("figure pick: the extracted figure set is not on this "
                   "disk, only the synthetic silhouette is measured")
            break
        report(f"figure pick with the extracted figures at {_W}x{_H}: "
               f"{_seen - len(_bad)} of {_seen} hit"
               + (f", misses {_bad[:4]}" if _bad else ""))
        assert not _bad, (_W, _H, _bad[:6])
    ok(f"a click on the centre of a figure's visible area picks up that "
       f"figure — 1 to 20 figures in every job column, three resolutions, "
       f"{_pz_total} figures read off the render")

# ── DATA'S PLANET DISCS: THE ASSETS ─────────────────────────
#
# Ten sprites, one per `PLANET_CLIMATE` (orion2_consts.h:362-374),
# cut from Data's sheet by `tools/planet_extract.py`. Committed
# artwork, like `assets/frame.png` — so what this holds is that
# they are what the loader expects and that they are at their TRUE
# size, which is the one thing an extraction can quietly get
# wrong: a sprite saved at 4x with 4x4 blocks looks identical on
# screen and is four times the file, four times the scaling work
# and a lie about what the art is.
from screens.colony_summary import colonyplanets as _pl
from PIL import Image as _pl_Image
_pl_dir = os.path.join(SCREENS_DIR, "colony_summary",
                       _pl.PLANET_DIR)
assert len(_pl.NAMES) == 10, _pl.NAMES
# THE NAMES ARE THE ENUM'S, IN ITS ORDER — the ids are what
# `colonyrows` puts in every row, so a shuffled table would draw
# a Gaia for a Toxic world with nothing to report it.
assert _pl.NAMES == ("toxic", "radiated", "barren", "desert",
                     "tundra", "ocean", "swamp", "arid", "terran",
                     "gaia"), _pl.NAMES
assert _pl.name_for(8) == "terran" and _pl.name_for(0) == "toxic"
assert _pl.name_for(10) is None and _pl.name_for(None) is None, (
    "a climate this build does not know has to draw NO disc "
    "rather than the nearest one")
_pl_seen = []
for _pl_name in _pl.NAMES:
    _pl_path = os.path.join(_pl_dir, f"{_pl_name}.png")
    assert os.path.exists(_pl_path), (
        f"{_pl_path} is missing — run "
        f"`python tools/planet_extract.py`")
    _pl_img = _pl_Image.open(_pl_path).convert("RGBA")
    assert _pl_img.size == (_pl.MASTER_SIZE, _pl.MASTER_SIZE), (
        f"{_pl_name}.png is {_pl_img.size} and the loader refuses "
        f"anything but {_pl.MASTER_SIZE} square")
    _pl_a = _np.array(_pl_img)
    # ON THE TRUE GRID: there is no block size b >= 2 for which
    # every b x b cell is one colour. That is exactly "no block
    # larger than 1 px in the saved file".
    for _pl_b in (2, 3, 4):
        _pl_n = _pl.MASTER_SIZE // _pl_b * _pl_b
        _pl_q = _pl_a[:_pl_n, :_pl_n].reshape(
            _pl_n // _pl_b, _pl_b, _pl_n // _pl_b, _pl_b, 4)
        _pl_flat = (_pl_q.min(axis=(1, 3)) == _pl_q.max(axis=(1, 3))
                    ).all()
        assert not _pl_flat, (
            f"{_pl_name}.png is uniform in every {_pl_b}x{_pl_b} "
            f"block — it was saved at {_pl_b}x and is not at its "
            f"true size")
    # AND IT IS A DISC: opaque in the middle, gone at the corners,
    # and the dark limb is still there — the alpha is a circle and
    # never a luma key, which is what would eat a Barren world's
    # night side.
    assert _pl_a[_pl.MASTER_SIZE // 2, _pl.MASTER_SIZE // 2, 3] == 255
    assert _pl_a[0, 0, 3] == 0 and _pl_a[-1, -1, 3] == 0, (
        f"{_pl_name}.png has opaque corners — the mask is not a "
        f"circle")
    _pl_mid = _pl_a[_pl.MASTER_SIZE // 2]
    _pl_dark = int((_pl_mid[:, 3] == 255).sum())
    _pl_seen.append((_pl_name, _pl_dark,
                     int(_pl_a[:, :, 3].max())))
report("planet discs: " + ", ".join(
    f"{_n} {_w}px wide" for _n, _w, _ in _pl_seen))
ok(f"the {len(_pl.NAMES)} planet discs are the climate enum's, "
   f"{_pl.MASTER_SIZE} px square, on the true pixel grid and "
   f"masked by a circle")

# ── AND WHAT IS DRAWN WITH THEM ─────────────────────────────
#
# Three properties, all measured out of the render: the disc on a
# row is the one its own text names, it does not touch the name's
# ink, and the five lines in `planet_info` stay inside their box
# beside the big one. The first is the whole point of the mapping
# being one field read twice, and it is the one a shuffled table
# or an off-by-one climate id would break silently.
_pl_climates = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["list"].get("climates", ())
for _pl_W, _pl_H in ((1920, 1080), (2560, 1440), (3440, 1371),
                     (3840, 2160)):
    _pl_app, _pl_scr = _plv.build_screen(_pl_W, _pl_H)
    _pl_app.dispatcher.switch_to("colony_summary")
    _pl_scr.enter(None)
    _pl_scr.update(_plv._Snapshot(_plv.COLONIES))
    _pl_surf = pygame.Surface((_pl_W, _pl_H))
    _pl_surf.fill((0, 0, 0))
    _pl_scr.render(_pl_surf)
    _pl_area, _pl_cfg, _pl_scale, _pl_n = _pl_scr._list_view()
    _pl_size = _pl.icon_size(_pl_area, _pl_cfg)
    _pl_set = _pl.set_for(_pl_scr, _pl_size)
    assert _pl_set is not None and _pl_set.state == "ok", (
        f"{_pl_W}x{_pl_H}: the planet set is {_pl_set and _pl_set.state}")
    _pl_cols = _ctk.columns(_pl_area, _pl_cfg)
    _pl_nx, _pl_nw = _pl_cols["name"]
    _pl_bands = _ctk.row_bands(_pl_area, _pl_cfg, _pl_scale, _pl_n)
    _pl_inset = int(_pl_scr._frame_inset()
                    * (_pl_scr.layout.font_size(
                        _pl_cfg.get("name_font", 21)) / 21.0))
    _pl_rows = 0
    for _pl_i, (_pl_top, _pl_bh) in enumerate(_pl_bands):
        if _pl_i >= len(_pl_scr._rows):
            continue
        _pl_row = _pl_scr._rows[_pl_i]
        _pl_want = _pl_set.get(_pl_row.get("climate"))
        assert _pl_want is not None, (
            f"row {_pl_i} has climate {_pl_row.get('climate')!r} "
            f"and no disc — every colony the game reports has a "
            f"climate in the enum")
        _pl_x = _pl_nx + _pl_inset
        _pl_y = _pl_top + (_pl_bh - _pl_want.get_height()) // 2
        # THE PIXELS, against the sprite the row's OWN climate
        # selects. Comparing the drawn region to the expected
        # sprite is what ties the picture to the text: the text
        # comes from the same `climate` through `list.climates`.
        _pl_got = _np.array(pygame.surfarray.array3d(
            _pl_surf.subsurface(pygame.Rect(
                _pl_x, _pl_y, _pl_want.get_width(),
                _pl_want.get_height())))).transpose(1, 0, 2)
        _pl_ref = _np.array(pygame.surfarray.array3d(
            _pl_want)).transpose(1, 0, 2)
        _pl_alpha = _np.array(pygame.surfarray.array_alpha(
            _pl_want)).transpose(1, 0)
        _pl_solid = _pl_alpha == 255
        assert _pl_solid.sum() > 100, "the disc has no opaque body"
        assert (_pl_got[_pl_solid] == _pl_ref[_pl_solid]).all(), (
            f"{_pl_W}x{_pl_H} row {_pl_i} ({_pl_row['name']}, "
            f"climate {_pl_row.get('climate')}): the disc drawn at "
            f"{(_pl_x, _pl_y)} is not the sprite that climate "
            f"selects")
        # AND IT DOES NOT TOUCH THE NAME. The ink of the name and
        # of the "Terran 13/22" line under it starts past the
        # disc's right edge plus the gap that is in layout.json.
        _pl_strip = _pl_surf.subsurface(pygame.Rect(
            _pl_nx, _pl_top, _pl_nw, _pl_bh))
        _pl_lit = _np.array(pygame.surfarray.array3d(
            _pl_strip)).transpose(1, 0, 2).sum(axis=2) > 260
        _pl_lit[:, :_pl_want.get_width() + _pl_inset] = False
        _pl_xs = _np.where(_pl_lit.any(axis=0))[0]
        if len(_pl_xs):
            assert _pl_nx + int(_pl_xs.min()) >= _pl_x + \
                _pl_want.get_width(), (
                f"{_pl_W}x{_pl_H} row {_pl_i}: the name's ink "
                f"starts at {_pl_nx + int(_pl_xs.min())} and the "
                f"disc ends at {_pl_x + _pl_want.get_width()}")
        _pl_rows += 1
    assert _pl_rows >= 5, f"{_pl_W}x{_pl_H}: {_pl_rows} rows measured"
    # ── AND THE PANEL'S FIVE LINES STAY IN THEIR BOX ────────
    _pl_box = pygame.Rect(*_pl_scr.layout.rect(
        _pl_scr.box_rect("planet_info")))
    _pl_pad = int(_sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["output"].get("pad_x", 18)
        * _pl_scr.layout.scale)
    # INSIDE THE BLEED AND THE RIM. The box is the hole grown by
    # `colonyplates.BLEED` and the frame's own lit metal sits on
    # that edge — at 1920x1080 it reads as ink from x 450 to 460
    # of 461 and says nothing about the text. The screen's own
    # `frame_inset` is the number for how far that reaches (see
    # `layout.json._frame_inset_note`), which is what the panels
    # keep their text clear of in the first place.
    _pl_rim = max(4, int(_pl_scr._frame_inset() * _pl_scr.layout.scale))
    _pl_pan = _np.array(pygame.surfarray.array3d(
        _pl_surf.subsurface(_pl_box.inflate(-2 * _pl_rim,
                                            -2 * _pl_rim)))
    ).transpose(1, 0, 2)
    _pl_ink = _pl_pan.sum(axis=2) > 260
    _pl_ys, _pl_xs = _np.where(_pl_ink)
    assert len(_pl_ys), f"{_pl_W}x{_pl_H}: planet_info drew nothing"
    # The right-hand padding is EMPTY: the five lines wrap inside
    # the room the disc leaves them, and a line that did not would
    # put ink in the strip the panel keeps clear.
    _pl_edge = _pl_pan.shape[1] - (_pl_pad - _pl_rim)
    assert not _pl_ink[:, max(0, _pl_edge):].any(), (
        f"{_pl_W}x{_pl_H}: planet_info has ink in the "
        f"{_pl_pad} px the panel keeps clear on the right — a "
        f"line is wider than the room the disc leaves it")
    assert int(_pl_ys.max()) < _pl_pan.shape[0], (
        f"{_pl_W}x{_pl_H}: planet_info's content reaches "
        f"{int(_pl_ys.max())} of {_pl_pan.shape[0]} px of height")
ok("every row's disc is the one its climate selects, clear of the "
   "name's ink, and planet_info's lines stay beside the big one "
   "(four sizes, measured out of the render)")

# ── THE OUTPUT PANEL'S ICONS AND SEPARATORS — decision 56 ─────
#
# Three checks. The ASSETS: six derived files at the one size the
# table declares, both morale masks on one footprint, no colour
# hiding under a transparent pixel, and regenerating them
# reproduces them byte for byte — decision 40's licence to call
# them derived and keep them out of the repository. The DRAWING,
# asserted as a rule at every resolution boxes.json declares
# planet_output for: every row wears the icon its id or its morale
# sign selects, no icon is taller than its row, there is one line
# between each pair of rows and none anywhere else, and an empty
# selection draws none of it. The MARKING: DEVIATION for the icons
# and HD EXTENSION for the line, at every home, so neither can
# quietly turn into "how the panel looks".
import importlib.util as _oi_ilu
import subprocess as _oi_sp
import tempfile as _oi_tf
from screens.colony_summary import colonyoutputicons as _oi
from screens.colony_summary import colonyrows as _oi_cr
_oi_root = os.path.dirname(SCREENS_DIR)
_oi_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))["output"]
_oi_master = _oi.master_size(_oi_cfg)
assert _oi_master > 0, (
    "layout.json output.icon_size is gone or not a positive int — "
    "the tool and the loader both read it")
_oi_dir = os.path.join(SCREENS_DIR, "colony_summary", _oi.ICON_DIR)
_oi_tool = os.path.join(_oi_root, "tools", "make_output_icons.py")
_oi_fit = {}
for _oi_name in _oi.NAMES:
    _oi_path = os.path.join(_oi_dir, f"{_oi_name}.png")
    assert os.path.exists(_oi_path), (
        f"{_oi_path} is missing — run `python tools/setup.py`, which "
        f"runs tools/make_output_icons.py")
    _oi_a = _np.array(_pl_Image.open(_oi_path).convert("RGBA"))
    assert _oi_a.shape[:2] == (_oi_master, _oi_master), (
        f"{_oi_name}.png is {_oi_a.shape[1]}x{_oi_a.shape[0]} and "
        f"output.icon_size declares {_oi_master}; the loader refuses it")
    assert not _oi_a[_oi_a[:, :, 3] == 0, :3].any(), (
        f"{_oi_name}.png keeps colour under transparent pixels — "
        f"BLEND_RGB_ADD ignores alpha and would show it (fundament "
        f"section 4)")
    _oi_ys, _oi_xs = _np.nonzero(_oi_a[:, :, 3] > 0)
    assert len(_oi_ys), f"{_oi_name}.png is empty"
    _oi_fit[_oi_name] = (int(_oi_xs.max() - _oi_xs.min() + 1),
                         int(_oi_ys.max() - _oi_ys.min() + 1))
    assert max(_oi_fit[_oi_name]) == _oi_master, (
        f"{_oi_name}.png's content is {_oi_fit[_oi_name]} and does "
        f"not fill the {_oi_master} px footprint on its long edge")
# ONE FOOTPRINT FOR THE TWO STATES: the same canvas and the same
# long edge, so a morale change neither moves nor resizes the icon.
assert max(_oi_fit["morale_normal"]) == max(_oi_fit["morale_low"]), (
    f"the morale masks fill {_oi_fit['morale_normal']} and "
    f"{_oi_fit['morale_low']} — a state change would resize the icon")
_oi_tool_src = open(_oi_tool, encoding="utf-8").read()
for _oi_word in ("AI-GENERATED", "ChatGPT", "LICENCE", "decision 40",
                 "Lanczos", "PREMULTIPLIED"):
    assert _oi_word in _oi_tool_src, (
        f"tools/make_output_icons.py no longer says {_oi_word!r} — "
        f"where the sources came from and how they were resampled "
        f"is written there and nowhere else")
if _oi_ilu.find_spec("scipy") is None:
    report("output icons: the byte-for-byte rebuild was NOT checked — "
           "tools/make_output_icons.py needs scipy and it is not "
           "installed. The files above are unverified as derived.")
else:
    with _oi_tf.TemporaryDirectory() as _oi_tmp:
        _oi_run = _oi_sp.run([sys.executable, _oi_tool, "--out", _oi_tmp],
                             capture_output=True, text=True)
        assert _oi_run.returncode == 0, (
            f"make_output_icons.py failed: {_oi_run.stderr[-400:]}")
        for _oi_name in _oi.NAMES:
            with open(os.path.join(_oi_dir, f"{_oi_name}.png"),
                      "rb") as _oi_fh:
                _oi_have = _oi_fh.read()
            with open(os.path.join(_oi_tmp, f"{_oi_name}.png"),
                      "rb") as _oi_fh:
                _oi_again = _oi_fh.read()
            assert _oi_have == _oi_again, (
                f"{_oi_name}.png does not regenerate byte for byte — "
                f"it is not derived until it does (decision 40)")
report("output icons: " + ", ".join(
    f"{_n} {_w}x{_h}" for _n, (_w, _h) in _oi_fit.items()))
ok(f"the {len(_oi.NAMES)} output icons are {_oi_master} px as "
   f"output.icon_size declares, both morale masks on one footprint, "
   f"blank under transparency, and rebuilt byte for byte from "
   f"assets/_src/output/")

# ── …AND WHAT IS DRAWN WITH THEM, AT EVERY DECLARED SIZE ──────
assert _oi_cr.morale_icon(-1) == "morale_low"
assert _oi_cr.morale_icon(0) == "morale_normal", (
    "a halved morale of 0 wears the normal mask — as a label it has "
    "no zero, decision 56 (the original draws nothing there because "
    "it counts)")
assert _oi_cr.morale_icon(7) == "morale_normal"
_oi_boxes = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "boxes.json"), encoding="utf-8"))
_oi_res = sorted(
    _k for _k, _v in _oi_boxes.items() if isinstance(_v, list)
    and any(isinstance(_b, dict) and _b.get("name") == "planet_output"
            for _b in _v))
assert _oi_res, "no resolution in boxes.json declares planet_output"
_oi_ids = [_s["id"] for _s in _oi_cfg["rows"] if _s["column"] == 1]
assert _oi_cfg.get("separator_thickness", 0) > 0, (
    "output.separator_thickness is 0 — the separator is switched "
    "off. That is its undo, and it is made on purpose together with "
    "this check, never on its own")
for _oi_spec in _oi_res:
    _oi_W, _oi_H = (int(_v) for _v in _oi_spec.split("x"))
    _oi_app, _oi_scr = _plv.build_screen(_oi_W, _oi_H)
    _oi_app.dispatcher.switch_to("colony_summary")
    _oi_scr.enter(None)
    _oi_area = pygame.Rect(*_oi_scr.layout.rect(
        _oi_scr.box_rect("planet_output")))
    _oi_set = _oi.set_for(_oi_scr, _oi_cfg)
    assert _oi_set is not None and _oi_set.state == "ok", (
        f"{_oi_spec}: the output icon set is "
        f"{_oi_set and _oi_set.state}")
    _oi_s = _oi_scr.layout.scale
    _oi_pad_x = int(_oi_cfg["pad_x"] * _oi_s)
    _oi_pad_y = int(_oi_cfg["pad_y"] * _oi_s)
    _oi_gap = int(_oi_cfg["row_gap"] * _oi_s)
    _oi_n = len(_oi_ids)
    _oi_row_h = (_oi_area.h - 2 * _oi_pad_y
                 - _oi_gap * (_oi_n - 1)) // _oi_n
    _oi_left = _oi_area.x + _oi_pad_x
    _oi_right = (_oi_left + (_oi_area.w - 2 * _oi_pad_x)
                 - int(_oi_cfg["column_gap"] * _oi_s))
    _oi_sep = max(1, int(round(_oi_cfg["separator_thickness"] * _oi_s)))
    _oi_ins = int(_oi_cfg.get("separator_inset", 0) * _oi_s)
    assert _oi_set.size <= _oi_row_h, (
        f"{_oi_spec}: the icon is {_oi_set.size} px in a row of "
        f"{_oi_row_h}")
    for _oi_morale in (_fake["morale"], 0):
        _oi_row = dict(_fake, morale=_oi_morale,
                       morale_icon=_oi_cr.morale_icon(_oi_morale))
        _oi_surf = pygame.Surface((_oi_area.right + 8,
                                   _oi_area.bottom + 8))
        _oi_surf.fill((0, 0, 0))
        _co.render(_oi_surf, _oi_row, _oi_area, _oi_cfg, _words,
                   _climates, _oi_scr.layout, _oi_scr.style,
                   only={1}, icons=_oi_set)
        _oi_px = _np.array(pygame.surfarray.array3d(
            _oi_surf)).transpose(1, 0, 2)
        # EVERY ROW'S ICON IS THE ONE ITS ID — or, for morale, its
        # sign — selects, compared pixel for pixel on the opaque
        # body.
        for _oi_i, _oi_id in enumerate(_oi_ids):
            _oi_want = (_oi_row["morale_icon"] if _oi_id == "morale"
                        else _co.ICON_BY_ID[_oi_id])
            _oi_spr = _oi_set.get(_oi_want)
            _oi_top = (_oi_area.y + _oi_pad_y
                       + _oi_i * (_oi_row_h + _oi_gap))
            _oi_y = _oi_top + max(0, (_oi_row_h
                                      - _oi_spr.get_height()) // 2)
            _oi_got = _oi_px[_oi_y:_oi_y + _oi_spr.get_height(),
                             _oi_left:_oi_left + _oi_spr.get_width()]
            _oi_ref = _np.array(pygame.surfarray.array3d(
                _oi_spr)).transpose(1, 0, 2)
            _oi_solid = _np.array(pygame.surfarray.array_alpha(
                _oi_spr)).transpose(1, 0) == 255
            assert _oi_solid.sum() > 0 and (
                _oi_got[_oi_solid] == _oi_ref[_oi_solid]).all(), (
                f"{_oi_spec} row {_oi_id} (morale {_oi_morale}): the "
                f"icon drawn is not {_oi_want}")
        # ONE LINE BETWEEN EACH PAIR OF ROWS, NONE ANYWHERE ELSE: the
        # set of pixel rows fully in the separator colour across the
        # content span is exactly the expected set.
        _oi_span = _oi_px[:, _oi_left + _oi_ins:_oi_right - _oi_ins]
        _oi_lines = set(int(_y) for _y in _np.nonzero(
            (_oi_span == _np.array(_co.SEPARATOR_COLOR[:3])
             ).all(axis=(1, 2)))[0])
        _oi_expect = set()
        for _oi_i in range(1, _oi_n):
            _oi_top = (_oi_area.y + _oi_pad_y
                       + _oi_i * (_oi_row_h + _oi_gap))
            _oi_y0 = _oi_top - _oi_gap + max(0, (_oi_gap - _oi_sep) // 2)
            _oi_expect.update(range(_oi_y0, _oi_y0 + _oi_sep))
        assert _oi_lines == _oi_expect, (
            f"{_oi_spec}: separator rows {sorted(_oi_lines)} where "
            f"{_oi_n - 1} lines of {_oi_sep} px belong at "
            f"{sorted(_oi_expect)} — one between each pair of rows, "
            f"none above the first or under the last")
    # UNIFICATION: the value is hidden and the label prints, so the
    # icon prints too.
    _oi_uni = _co.visible_rows(
        dict(_fake, morale=0, morale_applies=False,
             morale_icon=_oi_cr.morale_icon(0)),
        _oi_cfg, _words, _climates, only={1})
    assert _oi_uni[-1].icon == "morale_normal" and \
        _oi_uni[-1].value == _oi_cfg.get("hidden_value", ""), (
        f"under Unification the morale row is {_oi_uni[-1]} — the "
        f"icon follows the row, which prints")
    # AND NOTHING ON AN EMPTY SELECTION — no icon, no line.
    _oi_surf.fill((0, 0, 0))
    _co.render(_oi_surf, None, _oi_area, _oi_cfg, _words, _climates,
               _oi_scr.layout, _oi_scr.style, only={1}, icons=_oi_set)
    assert pygame.surfarray.array3d(_oi_surf).sum() == 0, (
        f"{_oi_spec}: the panel drew icons or separators with "
        f"nothing selected")
ok(f"every planet_output row wears the icon its id or morale sign "
   f"selects, no taller than its row, one separator between each "
   f"pair of rows and none outside them, nothing when empty "
   f"({', '.join(_oi_res)})")

# ── …AND BOTH ARE MARKED WHERE A READER WOULD LOOK ────────────
_oi_homes = {
    "colonyoutput.py": (os.path.join(SCREENS_DIR, "colony_summary",
                                     "colonyoutput.py"),
                        ("HD EXTENSION", "decision 56")),
    "colonyoutputicons.py": (os.path.join(
        SCREENS_DIR, "colony_summary", "colonyoutputicons.py"),
        ("DEVIATION", "decision 56")),
    "colonyrows.py": (os.path.join(SCREENS_DIR, "colony_summary",
                                   "colonyrows.py"),
                      ("def morale_icon", "decision 56")),
    "doc/v3_fundament.md": (os.path.join(_oi_root, "doc",
                                         "v3_fundament.md"),
                            ("**56.", "HD EXTENSION", "DEVIATION")),
    "v3_projektstatus.md": (os.path.join(_oi_root,
                                         "v3_projektstatus.md"),
                            ("decision 56", "HD EXTENSION")),
}
for _oi_home, (_oi_path, _oi_words) in _oi_homes.items():
    _oi_text = read_doc(_oi_path)
    for _oi_word in _oi_words:
        assert _oi_word in _oi_text, (
            f"{_oi_home} no longer carries {_oi_word!r} — the output "
            f"icons are a DEVIATION and the separators an HD "
            f"EXTENSION, and the marking lives at every home")
assert _oi_cfg["_separator_note"].startswith("HD EXTENSION"), (
    "output._separator_note no longer opens with its marking")
assert "DEVIATION, decision 56" in _oi_cfg["_deviation_note"], (
    "output._deviation_note no longer lists the icons")
assert "An asset is not a measurement" in _oi_cfg["_icon_size_note"], (
    "output._icon_size_note no longer says where 31 came from")
_oi_colors = _sjson.load(open(os.path.join(
    _oi_root, "assets", "shared", "skins", "default", "colors.json"),
    encoding="utf-8"))["colony_summary"]
assert "output_separator" in _oi_colors and \
    "HD EXTENSION" in _oi_colors.get("_output_separator_note", ""), (
    "the skin no longer declares the separator's colour and marking")
ok("the output icons are marked DEVIATION and the separators HD "
   "EXTENSION in colonyoutput, colonyoutputicons, colonyrows, "
   "layout.json, colors.json, the fundament and the status document")

# ── THE LIST PALETTE — decision 57, briefs 95 and 96 ──────────
#
# Data's table (doc/briefs/95-palette.png) is the SOURCE, so the
# skin is held to its hex values; the row fills are an HD
# EXTENSION and the marking is asserted at every home; the table's
# hover colour has no key on purpose; and — the rule, not the
# instance — no module of this screen types a colour for a row
# background or a plate outline.
import ast as _lp_ast
from core import palette as _lp_pal
from screens.colony_summary import colonylist as _lp_cl
from screens.colony_summary import colonytrack as _lp_ct
_lp_root = os.path.dirname(SCREENS_DIR)
_lp_skin = _sjson.load(open(os.path.join(
    _lp_root, "assets", "shared", "skins", "default", "colors.json"),
    encoding="utf-8"))["colony_summary"]
_lp_hex = {"panel_background": "080E17", "row_a": "0A121E",
           "row_b": "111E2E", "plate_outline": "29394C",
           "row_selected": "182B72", "header_background": "09111D",
           "header_text": "79A8E8"}
for _lp_k, _lp_h in _lp_hex.items():
    _lp_want = tuple(int(_lp_h[_i:_i + 2], 16) for _i in (0, 2, 4))
    assert tuple(_lp_skin.get(_lp_k, ())) == _lp_want, (
        f"colors.json colony_summary.{_lp_k} is "
        f"{_lp_skin.get(_lp_k)} and Data's table says #{_lp_h} "
        f"{_lp_want}")
    assert _lp_pal.require("colony_summary", _lp_k) == _lp_want
assert "nav_background" not in _lp_skin, (
    "colony_summary.nav_background is back — nothing on this screen "
    "reads it (the galaxy map's own key is live and separate)")
assert "row_hover" not in _lp_skin, (
    "a row_hover key appeared. Decision 57: the row under the "
    "pointer IS the scanned colony (colsum.cpp:880-890), so a hover "
    "fill could never be seen under the selected one")
assert _lp_skin["_row_fill_note"].startswith("HD EXTENSION") and \
    "colsum.cpp:880-890" in _lp_skin["_row_fill_note"], (
    "colors.json _row_fill_note no longer opens with its marking or "
    "no longer says why there is no hover key")
for _lp_home, _lp_path, _lp_words in (
        ("colonylist.py", os.path.join(SCREENS_DIR, "colony_summary",
                                       "colonylist.py"),
         ("HD EXTENSION, decision 57", "row_selected")),
        ("doc/v3_fundament.md", os.path.join(_lp_root, "doc",
                                             "v3_fundament.md"),
         ("**57.", "HD EXTENSION")),
        ("v3_projektstatus.md", os.path.join(_lp_root,
                                             "v3_projektstatus.md"),
         ("decision 57", "HD EXTENSION"))):
    _lp_text = read_doc(_lp_path)
    for _lp_w in _lp_words:
        assert _lp_w in _lp_text, (
            f"{_lp_home} no longer carries {_lp_w!r} — the row fills "
            f"are an HD EXTENSION and the marking lives at every home")
_lp_forbidden = set(_lp_hex) - {"panel_background"} | {"galaxy_inset_fill"}
_lp_dir = os.path.join(SCREENS_DIR, "colony_summary")
for _lp_fn in sorted(os.listdir(_lp_dir)):
    if not _lp_fn.endswith(".py"):
        continue
    _lp_src = open(os.path.join(_lp_dir, _lp_fn), encoding="utf-8").read()
    assert "nav_background" not in _lp_src, (
        f"{_lp_fn} reads nav_background, which this screen dropped")
    for _lp_n in _lp_ast.walk(_lp_ast.parse(_lp_src)):
        if not isinstance(_lp_n, _lp_ast.Call):
            continue
        _lp_f = _lp_n.func
        _lp_name = (_lp_f.attr if isinstance(_lp_f, _lp_ast.Attribute)
                    else getattr(_lp_f, "id", None))
        _lp_a = _lp_n.args
        # A CODE DEFAULT FOR ONE OF THESE KEYS is a second home for
        # the colour — decision 14.
        if (_lp_name == "col" and len(_lp_a) >= 2
                and isinstance(_lp_a[1], _lp_ast.Constant)
                and _lp_a[1].value in _lp_forbidden):
            raise AssertionError(
                f"{_lp_fn}:{_lp_n.lineno} reads {_lp_a[1].value!r} "
                f"through palette.col with a code default — use "
                f"palette.require (decision 14)")

        def _lp_literal(_node):
            return (isinstance(_node, (_lp_ast.Tuple, _lp_ast.List))
                    and len(_node.elts) in (3, 4)
                    and all(isinstance(_e, _lp_ast.Constant)
                            and isinstance(_e.value, int)
                            for _e in _node.elts))
        # A LITERAL COLOUR FOR A PLATE OUTLINE, anywhere on the screen.
        if _lp_name == "draw_plate" and len(_lp_a) >= 4 \
                and _lp_literal(_lp_a[3]):
            raise AssertionError(
                f"{_lp_fn}:{_lp_n.lineno} draws a plate in a literal "
                f"colour — the outline is the skin's plate_outline")
        # A LITERAL COLOUR FOR A ROW BACKGROUND: the list's own fills.
        if _lp_fn == "colonylist.py" and (
                (_lp_name == "fill" and _lp_a and _lp_literal(_lp_a[0]))
                or (_lp_name == "rect" and len(_lp_a) >= 2
                    and _lp_literal(_lp_a[1]))):
            raise AssertionError(
                f"colonylist.py:{_lp_n.lineno} fills in a literal "
                f"colour — a row background is the skin's")
ok("the list palette is Data's table in the default skin (seven "
   "keys to the hex), nav_background and row_hover absent, the row "
   "fills marked HD EXTENSION at every home, and no row-background or "
   "plate-outline colour typed anywhere in screens/colony_summary/")

# ── …AND THE STRIPE IS THE LIST'S, THE FILL IS THE SCANNED ROW'S ──
# Rendered, twice: from the top and scrolled by one. Every band's
# background (the MODE over the band, which the fill dominates) is
# row_selected where the band's colony is the scanned one and
# otherwise A or B by LIST index — so scrolling by one swaps the
# colours on screen and keeps each colony's own.
from screens.colony_summary import colonyfigures as _lp_fig
from screens.colony_summary import colonyscroll as _lp_scroll
_lp_app, _lp_scr = _plv.build_screen(1920, 1080)
_lp_app.dispatcher.switch_to("colony_summary")
_lp_scr.enter(None)
_lp_scr.update(_plv._Snapshot(_plv.COLONIES))
_lp_area, _lp_cfg, _lp_scale, _lp_n = _lp_scr._list_view()
_lp_rows = _lp_scr._rows
assert len(_lp_rows) >= 3, "the synthetic empire has too few rows"
_lp_scanned = _lp_rows[2]["index"]
_lp_cols = [(_x, _w) for _k, (_x, _w)
            in _lp_ct.columns(_lp_area, _lp_cfg).items()
            if _k != _lp_scroll.COLUMN]
_lp_x0 = min(_x for _x, _w in _lp_cols)
_lp_x1 = max(_x + _w for _x, _w in _lp_cols)
for _lp_first in (0, 1):
    _lp_s = pygame.Surface((1920, 1080))
    _lp_s.fill((255, 0, 255))
    _lp_cl.render(_lp_s, _lp_rows, _lp_area, _lp_cfg, _lp_scr.layout,
                  _lp_scr.style, _lp_first, _lp_scr._frame_inset(),
                  _lp_fig.set_for(_lp_scr, _lp_area, _lp_cfg),
                  _lp_scanned, None)
    _lp_px = _np.array(pygame.surfarray.array3d(_lp_s)).transpose(1, 0, 2)
    for _lp_b, (_lp_by, _lp_bh) in enumerate(
            _lp_ct.all_bands(_lp_area, _lp_cfg)):
        _lp_li = _lp_first + _lp_b
        _lp_sel = (_lp_li < len(_lp_rows)
                   and _lp_rows[_lp_li]["index"] == _lp_scanned)
        _lp_exp = (_lp_cl.ROW_SELECTED if _lp_sel else
                   (_lp_cl.ROW_A if _lp_li % 2 == 0 else _lp_cl.ROW_B))
        _lp_band = _lp_px[_lp_by + 2:_lp_by + _lp_bh - 2,
                          _lp_x0 + 2:_lp_x1 - 2].reshape(-1, 3)
        _lp_c, _lp_cnt = _np.unique(_lp_band, axis=0, return_counts=True)
        _lp_got = tuple(int(_v) for _v in _lp_c[int(_np.argmax(_lp_cnt))])
        assert _lp_got == tuple(_lp_exp[:3]), (
            f"first={_lp_first} band {_lp_b} (list index {_lp_li}"
            f"{', scanned' if _lp_sel else ''}) is mostly {_lp_got}; "
            f"expected {tuple(_lp_exp[:3])}")
ok("the list stripes A/B by list index (holds under a one-row "
   "scroll) and fills the scanned colony's band row_selected, "
   "measured as the mode of every rendered band")
