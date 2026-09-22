# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 071_game_menu_game_menu_the_body_wears_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - GAME menu: the body wears the frame image, every other panel and button is a thin_border box, no
#   - GAME menu frame: opening == the artwork's one hole, loaded through the resource roots, fitted in


# 5. THE SKINS: the body wears the frame image (decision 69) and
#    nothing else does; every other panel and button is a thin_border
#    box, and nothing in the package draws a rectangle itself
#    (decision 34). Rewritten 16 September 2026 when the body's
#    outline was replaced — the rule moved, the check did not go.
_gm_boxes = _gm_json.load(open(os.path.join(
    SCREENS_DIR, "game_menu", "boxes.json")))["1920x1080"]
for _b in _gm_boxes:
    _sk = _b.get("style", {}).get("skin")
    if _b["name"] == "body":
        assert _b["style"].get("frame") is True and _sk != \
            "thin_border", ("body", _b["style"])
        continue
    assert not _b.get("style", {}).get("frame"), _b["name"]
    if _b["name"].endswith("_panel") or \
            _b["name"].split("_")[0] in ("menu", "confirm", "load",
                                        "save") and _sk != "area":
        assert _sk == "thin_border", (_b["name"], _sk)
for _fn in os.listdir(os.path.join(SCREENS_DIR, "game_menu")):
    if _fn.endswith(".py"):
        _src = open(os.path.join(SCREENS_DIR, "game_menu", _fn),
                    encoding="utf-8").read()
        assert "draw.rect(" not in _src, f"{_fn} draws a rectangle"
ok("GAME menu: the body wears the frame image, every other panel and "
   "button is a thin_border box, no pygame.draw.rect in the package")

# 5b. THE FRAME (decision 69). The opening in layout.json is the
#     artwork's own hole, the image comes through the resource roots,
#     the popup sits where the original's sits IN THE MAP WINDOW, and
#     every dialog's content lies inside the octagon at three
#     resolutions — measured on the drawn pixels against the scaled
#     alpha — ALL SIX, since work order 123: the confirmation and the
#     warning are wider than the popup in the original (CONFIRM.LBX
#     313 px, WARNING.LBX 331, the popup 279) and overhang it there;
#     Data decided they are scaled into the opening (HD DEVIATION,
#     decision 69), so they are held to it like every other dialog.
if slow("game_menu_frame_opening"):
    import frame_holes as _gmf_fh
    from screens.game_menu import gmframe as _gmf
    from screens.galaxy_map import mapboxes as _gmf_mb
    _gmf_lay = _gm_json.load(open(os.path.join(
        SCREENS_DIR, "game_menu", "layout.json")))
    _gmf_png = res.screen_file("game_menu", "assets", "frame.png")
    assert _gmf_png, "screens/game_menu/assets/frame.png is missing"
    _gmf_w, _gmf_h, _gmf_holes = _gmf_fh.find_holes(_gmf_png)
    assert len(_gmf_holes) == 1, _gmf_holes
    assert list(_gmf_holes[0]) == _gmf_lay["frame"]["opening"], (
        _gmf_holes, _gmf_lay["frame"]["opening"])
    assert [_gmf_w, _gmf_h] == _gmf_lay["frame"]["image_size"]
    _gmf_src = open(_gmf.__file__, encoding="utf-8").read()
    assert "asset_path(" in _gmf_src and "os.path" not in _gmf_src, \
        "gmframe must load through the resource roots (decision 16)"
    # THE PLACEMENT (work order 125, HD DEVIATION, superseding 122's share
    # of the map window): the frame fitted to the galaxy map's map_area as
    # boxes.json has it — its height, centred — and every box seated by one
    # move and one factor. The file keeps the design geometry.
    _gmf_body = next(_b["rect"] for _b in _gm_boxes if _b["name"] == "body")
    assert "HD DEVIATION" in _gmf.__doc__ and "map" in _gmf.__doc__
    from core.box import load_boxes as _gmf_lb
    _gmf_nodes = ("menu", "settings", "load", "save", "confirm", "warning")
    _gmf_real = _gmf.draw
    for _W, _H in ((1920, 1080), (2560, 1440), (3840, 2160)):
        _gmf_app, _ = _pv.build_screen(_W, _H)
        _gmf_d = _gmf_app.dispatcher
        _gmf_d.switch_to("galaxy_map")
        _gmf_gs = _GmState()
        _gmf_gs.current_screen = 8
        _gmf_gs.settings_raw = _gm_live
        _gmf_gs.fields = _gm_fields(_gm_fix["menu"])
        _gmf_d.update_from_game(_gmf_gs)
        _gmf_s = _gmf_d.screens["game_menu"]
        _gmf_s.enter(_gmf_gs)
        _gmf_br = _gm_draw.rect(_gmf_s, "body")
        _gmf_fr, _gmf_op = _gmf.rects(_gmf_s, _gmf_br)
        assert _gmf_op.contains(_gmf_br), (_W, _gmf_op, _gmf_br)
        _gmf_img = pygame.transform.smoothscale(
            pygame.image.load(_gmf_png), _gmf_fr.size)
        _gmf_al = np.full((_H, _W), 255, dtype=np.uint8)
        _gmf_fa = pygame.surfarray.array_alpha(_gmf_img).T
        # INSIDE THE MAP CUTOUT (work order 125): the frame's rect within
        # map_area, its height the cutout's, centred on it, and its metal
        # (alpha >= 16) clear of the GAME field above and the nav bar below.
        _gmf_cut = pygame.Rect(*_gmf_s.layout.rect(next(
            _b.ref_rect for _b in _gmf_lb(res.screen_file(
                "galaxy_map", "boxes.json"), _W, _H) if _b.name == "map_area")))
        assert _gmf_cut.inflate(2, 2).contains(_gmf_fr), (
            _W, "the GAME menu frame reaches outside the map cutout",
            _gmf_fr, _gmf_cut)
        assert abs(_gmf_fr.h - _gmf_cut.h) <= 1 and abs(
            _gmf_fr.centerx - _gmf_cut.centerx) <= 1, (_W, _gmf_fr, _gmf_cut)
        _gmf_rows = np.where((_gmf_fa >= 16).any(axis=1))[0]
        assert _gmf_fr.y + _gmf_rows[0] >= _gmf_cut.y and \
            _gmf_fr.y + _gmf_rows[-1] < _gmf_cut.bottom, (_W, _gmf_fr)
        # One factor for every box: the seated body is the file's body times
        # content_scale, and a seated button keeps its offset in proportion.
        _gmf_k = _gmf_s.content_scale
        assert 0.5 < _gmf_k < 1.0, _gmf_k
        _gmf_sb = {_b.name: _b.ref_rect for _b in _gmf_s.boxes}
        _gmf_fb = {_b["name"]: _b["rect"] for _b in _gm_boxes}
        for _bn in ("menu_save", "confirm_panel", "sound_bar"):
            _exp = (_gmf_sb["body"][0] + (_gmf_fb[_bn][0] - _gmf_body[0])
                    * _gmf_k, _gmf_fb[_bn][2] * _gmf_k)
            assert abs(_gmf_sb[_bn][0] - _exp[0]) < 1e-6 and \
                abs(_gmf_sb[_bn][2] - _exp[1]) < 1e-6, (_bn, _gmf_sb[_bn])
            # An editor save writes the file's rect, never the seated one.
            _gmf_bx = next(_b for _b in _gmf_s.boxes if _b.name == _bn)
            assert _gmf_bx.to_dict()["rect"] == _gmf_fb[_bn], _bn
        _gx, _gy = max(0, _gmf_fr.x), max(0, _gmf_fr.y)
        _sx, _sy = _gx - _gmf_fr.x, _gy - _gmf_fr.y
        _ww = min(_W - _gx, _gmf_fa.shape[1] - _sx)
        _hh = min(_H - _gy, _gmf_fa.shape[0] - _sy)
        _gmf_al[_gy:_gy + _hh, _gx:_gx + _ww] = \
            _gmf_fa[_sy:_sy + _hh, _sx:_sx + _ww]
        for _n in _gmf_nodes:
            _gmf_gs.fields = _gm_fields(_gm_fix[_n])
            _gmf_s.update(_gmf_gs)
            _gmf.draw = lambda *_a: True
            try:
                _gmf_surf = pygame.Surface((_W, _H))
                _gmf_surf.fill((255, 0, 255))
                _gmf_s.render(_gmf_surf)
            finally:
                _gmf.draw = _gmf_real
            _px = pygame.surfarray.array3d(_gmf_surf).transpose(1, 0, 2)
            _content = ~((_px[:, :, 0] == 255) & (_px[:, :, 1] == 0)
                         & (_px[:, :, 2] == 255))
            assert _content.sum() > 2000, (_W, _n, "drew nothing")
            _out = _content & (_gmf_al >= 16)
            assert not _out.any(), (
                f"GAME menu {_n} at {_W}x{_H}: {int(_out.sum())} px of "
                f"content outside the frame's opening")
            # THE FILL: the octagon is transparent, so the menu's own
            # ground has to be under it — sampled in the drawn frame, off
            # every box, it must not be the map underneath.
            if _n == "menu":
                _gmf_full = pygame.Surface((_W, _H))
                _gmf_full.fill((255, 0, 255))
                _gmf_s.render(_gmf_full)
                _pt = (_gmf_op.centerx, _gmf_op.y + _gmf_op.h // 2)
                assert _gmf_full.get_at(_pt)[:3] != (255, 0, 255), (
                    _W, "the opening is not filled")
    # THE FIT RULE (work order 123): each box scaled by ONE factor, the
    # body's width over the panel's, so the panel is the body's width and
    # centred on it, and its fonts carry the same factor as its rects.
    _gmf_rects = {_b["name"]: _b for _b in _gm_boxes}
    for _grp in ("confirm", "warning"):
        _gp = _gmf_rects[f"{_grp}_panel"]["rect"]
        assert abs(_gp[2] - _gmf_body[2]) <= 1 and abs(
            (_gp[0] + _gp[2] / 2) - (_gmf_body[0] + _gmf_body[2] / 2)) <= 1, (
            _grp, _gp, _gmf_body)
        # The text box keeps its native proportion to the panel: a text
        # area scaled on its own would change the wrap, not the size.
        _nat = _gmf_lay["native"]
        _np_, _nt = _nat[f"{_grp}_panel"], _nat[f"{_grp}_text"]
        _gt = _gmf_rects[f"{_grp}_text"]["rect"]
        assert abs(_gt[2] / _gp[2] - (_nt[2] - _nt[0]) / (_np_[2] - _np_[0])
                   ) < 0.01, (_grp, _gt, _gp)
    assert "HD DEVIATION" in _gmf.__doc__ and "HD DEVIATION" in \
        _gm_draw.__doc__, "the confirmation fit lost its marking"
    ok("GAME menu frame: opening == the artwork's one hole, loaded through "
       "the resource roots, fitted inside the galaxy map cutout with every "
       "box seated by one factor, all six dialogs inside the octagon and "
       "filled at 1080p/1440p/2160p")
