# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080i_core_the_research_frame_is_cut_and.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (103 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 166 part B,
# the research panel's outer frame.
#
# The 3 check(s) it holds:
#   - the research frame is DERIVED: the cut rebuilds byte for byte
#     from the committed Fleets artwork
#   - its corner lamps scale with the window and are never stretched
#   - the title survives a resize, which is where it was being lost
import importlib.util as _fr_ilu

from core import researchframe as _fr

_fr_tool_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tools", "make_research_frame.py")
_fr_spec = _fr_ilu.spec_from_file_location("_mkframe", _fr_tool_path)
_fr_tool = _fr_ilu.module_from_spec(_fr_spec)
_fr_spec.loader.exec_module(_fr_tool)

# ── DERIVED MEANS A REBUILD REPRODUCES IT ──
#
# Decision 49's surviving half, and the licence for the word: the input
# is committed (`screens/fleets/assets/frame.png`), the output is not,
# the cut is a PLAIN CROP, and this rebuilds it and compares rather
# than trusting that the tool exists (decision 40's own lesson).
assert _fr_tool.CUT == (205, 189, 1537, 950), _fr_tool.CUT
assert _fr_tool.CORNER == _fr.CORNER == 140
assert _fr_tool.RAIL == _fr.RAIL == 23
_fr_shipped = os.path.join(os.path.dirname(SCREENS_DIR),
                           *_fr_tool.OUTPUT.split(os.sep))
if not os.path.exists(_fr_shipped):
    # ABSENCE IS REPORTED, never skipped (decision 42's pattern): a
    # clone that has not run setup still counts this check and is told
    # the command.
    report("research frame NOT rebuilt — no assets/shared/frames/"
           "research_panel.png; run `python tools/setup.py`")
else:
    import tempfile as _fr_tmp
    with _fr_tmp.TemporaryDirectory() as _fr_dir:
        os.makedirs(os.path.join(_fr_dir, "screens", "fleets", "assets"))
        os.symlink(os.path.join(os.path.dirname(SCREENS_DIR),
                                *_fr_tool.SOURCE.split(os.sep)),
                   os.path.join(_fr_dir, *_fr_tool.SOURCE.split(os.sep)))
        _fr_built = _fr_tool.build(_fr_dir)
        assert io.open(_fr_built, "rb").read() == \
            io.open(_fr_shipped, "rb").read(), (
                "the research frame on disk is not what the tool "
                "produces from the committed artwork")
    ok("the research frame is DERIVED: the cut rebuilds byte for byte "
       "from the committed Fleets artwork")

# ── THE LAMPS SCALE, THEY DO NOT STRETCH ──
#
# `core/nineslice.NineSlice` keeps corners at the source's pixel size
# and `core/frame.FrameRenderer` scales them per axis, which stretches
# them when the target's aspect differs from the source's — and this
# panel is square where the cut is 1.62:1. `researchframe` scales the
# SOURCE once by one factor and slices the result, so a lamp keeps its
# shape. Measured, not looked at: the lamp's bounding box aspect at
# four resolutions against the source's own.
_fr_frame = _fr.ResearchFrame(_rs_app.res)
if not _fr_frame.available:
    report("research frame not loaded — the lamp measurement needs "
           "assets/shared/frames/research_panel.png")
else:
    def _fr_lamp(surf, x0, y0, w, h):
        """The orange lamp's bounding box inside a corner region."""
        xs, ys = [], []
        # The frame's rect can start off-screen: the panel's own top is
        # 4 native px down and the rail is thicker than that at every
        # resolution, so `around()` puts the frame's top edge above the
        # window. Clamped rather than assumed inside.
        for _y in range(max(0, y0), min(y0 + h, surf.get_height())):
            for _x in range(max(0, x0), min(x0 + w, surf.get_width())):
                _p = surf.get_at((_x, _y))
                if _p[3] > 40 and _p[0] > 110 and _p[0] - _p[2] > 50:
                    xs.append(_x)
                    ys.append(_y)
        return (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1) if xs else None

    _fr_src_lamp = _fr_lamp(_fr_frame.image, 0, 0, 200, 200)
    assert _fr_src_lamp, "no lamp in the cut's top-left corner"
    _fr_src_aspect = _fr_src_lamp[0] / _fr_src_lamp[1]
    _fr_seen = 0
    for _fr_w, _fr_h in ((1920, 1080), (2560, 1440), (3440, 1440),
                         (3840, 2160)):
        _fr_lay = Layout(_fr_w, _fr_h)
        _fr_box = _dx_geo.window_rect(_dx_scr.geom.panel_rect, _fr_lay)
        _fr_surf = pygame.Surface((_fr_w, _fr_h), pygame.SRCALPHA)
        _fr_rect = _fr_frame.render(_fr_surf, _fr_box, _fr_lay.scale)
        assert _fr_rect is not None
        _fr_scale = _fr.REFERENCE_SCALE * _fr_lay.scale
        _fr_corner = _fr_frame.corner(_fr_scale)
        _fr_got = _fr_lamp(_fr_surf, _fr_rect.x, _fr_rect.y,
                           _fr_corner, _fr_corner)
        assert _fr_got, (_fr_w, _fr_h, "no lamp in the drawn corner")
        _fr_aspect = _fr_got[0] / _fr_got[1]
        assert abs(_fr_aspect - _fr_src_aspect) < 0.06, (
            f"{_fr_w}x{_fr_h}: the lamp is {_fr_got}, aspect "
            f"{_fr_aspect:.3f} against the cut's {_fr_src_aspect:.3f} "
            f"— the corner is being stretched")
        # …and it SCALES: the drawn lamp is the source's times the
        # window factor, or the corner is simply being clipped.
        assert abs(_fr_got[0] - _fr_src_lamp[0] * _fr_scale) <= 4, (
            _fr_w, _fr_got, _fr_src_lamp, _fr_scale)
        _fr_seen += 1
    assert _fr_seen == 4, _fr_seen
    ok("its corner lamps scale with the window and are never stretched")

# ── AND THE TITLE SURVIVES A RESIZE ──
#
# `ScreenBase.on_resize` -> `_reload_boxes` REPLACES every box object,
# so the label `enter` wrote onto the title box was written onto an
# object the screen no longer had: the panel lost its headline at every
# resolution the player did not enter at. Found in a live 4K capture,
# and an offline check could not have found it while it CONSTRUCTED a
# screen at each size — the colony column's own blind spot. So this
# check goes the way the fault went: enter at one size, then resize.
_fr_scr = _rs_d.screens["research_change"]
_fr_state = _RsGameState()
_fr_state.current_screen = 36
_fr_state.fields = _rl_list(_dx_entries, select_mode=False)
_fr_state.player_raw = list(_dx_state.player_raw)
_fr_state.player_num = 0
_rs_client.state = _fr_state
_fr_scr.enter(_fr_state)


def _fr_title_label():
    return [b.style.get("label") for b in _fr_scr.boxes
            if b.name == "title"]


assert _fr_title_label() == ["CHANGE CURRENT RESEARCH"], _fr_title_label()
_fr_was = (_rs_app.win_w, _rs_app.win_h, _rs_app.layout)
for _fr_w, _fr_h in ((3840, 2160), (2560, 1440), (1920, 1080)):
    _rs_app.win_w, _rs_app.win_h = _fr_w, _fr_h
    _rs_app.layout = Layout(_fr_w, _fr_h)
    _fr_scr.on_resize()
    assert _fr_title_label() == ["CHANGE CURRENT RESEARCH"], (
        f"{_fr_w}x{_fr_h}: the title lost its word to the resize — "
        f"_reload_boxes replaced the box it was written on")
    # …and it still DRAWS. A label nobody renders is the same silence.
    _fr_box_surf = pygame.Surface((_fr_w, _fr_h))
    _fr_box_surf.fill((0, 0, 0))
    for _fr_b in _fr_scr.boxes:
        if _fr_b.name == "title":
            _fr_b.render(_fr_box_surf, _rs_app.layout, _rs_app.style)
    _fr_ink = sum(1 for _y in range(0, _fr_h, 3)
                  for _x in range(0, _fr_w, 3)
                  if _fr_box_surf.get_at((_x, _y))[:3] != (0, 0, 0))
    assert _fr_ink > 50, (_fr_w, _fr_h, _fr_ink)
_rs_app.win_w, _rs_app.win_h, _rs_app.layout = _fr_was
_fr_scr.on_resize()
ok("the title survives a resize, which is where it was being lost")
