# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 071_game_menu_game_menu_the_body_wears_the.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - GAME menu: the body and both dialogs wear the HUD popup, the buttons are HUD small buttons, no
#   - GAME menu popup: seated in the galaxy map's free area below the title plate with every box by one


# 5. THE SKINS — REPLACED BY WORK ORDER 169 (decision 71). This was "the
#    body wears the frame image, every other panel and button is a
#    thin_border box": the frame image is no longer drawn, and its
#    successor is asserted here. The body (`"frame": true`) and every
#    DIALOG panel (`"backdrop": true` — the confirmation, the slot
#    warning) wear the HUD popup block; every button is the HUD small
#    button; and nothing in the package draws a rectangle itself
#    (decision 34, unchanged).
_gm_boxes = _gm_json.load(open(os.path.join(
    SCREENS_DIR, "game_menu", "boxes.json")))["1920x1080"]
_gm_dialogs = {_b["name"] for _b in _gm_boxes
               if _b.get("style", {}).get("frame")
               or _b.get("style", {}).get("backdrop")}
assert _gm_dialogs == {"body", "confirm_panel", "warning_panel"}, \
    _gm_dialogs
from core.hud import blocks as _gm_hud
_gm_popups, _gm_smalls = [], []
_gm_real_pop, _gm_real_small = _gm_hud.popup, _gm_hud.small_button
_gm_hud.popup = lambda _s, _r, *_a, **_k: _gm_popups.append(tuple(_r))
_gm_hud.small_button = lambda _s, _r, *_a, **_k: _gm_smalls.append(
    tuple(_r))
try:
    for _n in ("menu", "confirm", "warning"):
        _gm_gs.fields = _gm_fields(_gm_fix[_n])
        _gm_scr.update(_gm_gs)
        _gm_scr.render(surf)
finally:
    _gm_hud.popup, _gm_hud.small_button = _gm_real_pop, _gm_real_small
for _n in ("body", "confirm_panel", "warning_panel"):
    _r = _gm_draw.box(_gm_scr, _n)
    assert _r is not None and _r.screen_rect is not None, _n
for _n in ("menu_save", "menu_return", "confirm_yes", "confirm_no"):
    _b = _gm_draw.box(_gm_scr, _n)
    assert tuple(_b.screen_rect) in _gm_smalls, (
        f"{_n} is not drawn as the HUD small button")
assert len(_gm_popups) >= 3, _gm_popups
for _fn in os.listdir(os.path.join(SCREENS_DIR, "game_menu")):
    if _fn.endswith(".py"):
        _src = open(os.path.join(SCREENS_DIR, "game_menu", _fn),
                    encoding="utf-8").read()
        assert "draw.rect(" not in _src, f"{_fn} draws a rectangle"
ok("GAME menu: the body and both dialogs wear the HUD popup, the buttons "
   "are HUD small buttons, no pygame.draw.rect in the package")

# 5b. THE POPUP'S PLACE — REPLACED BY WORK ORDER 169 (decision 71). This
#     was "GAME menu frame: opening == the artwork's one hole ... inside
#     the octagon": the frame image is no longer drawn, so its hole is
#     not what content has to fit. What stays asserted, rewritten for the
#     popup block: the popup sits in the galaxy map's FREE AREA (the map
#     cutout less the HUD title plate) and fills it as far as the body's
#     aspect allows, every box is seated by one move and one factor, the
#     file keeps the design geometry, and every dialog's content lies
#     inside the seated body at 1080p/1440p/2160p — ALL SIX, the
#     confirmation and the warning included (HD DEVIATION, work order 123).
if slow("game_menu_frame_opening"):
    from screens.game_menu import gmframe as _gmf
    _gmf_lay = _gm_json.load(open(os.path.join(
        SCREENS_DIR, "game_menu", "layout.json")))
    _gmf_body = next(_b["rect"] for _b in _gm_boxes if _b["name"] == "body")
    assert "HD DEVIATION" in _gmf.__doc__ and "map" in _gmf.__doc__
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
        # IN THE FREE AREA, and as large as the aspect allows there.
        _gmf_area = pygame.Rect(*_gmf_s.layout.rect(_gmf.free_area(_gmf_s)))
        assert _gmf_area.contains(_gmf_op), (_W, _gmf_op, _gmf_area)
        _gmf_m = _gmf.MARGIN * _gmf_s.layout.scale
        assert (abs(_gmf_op.h - (_gmf_area.h - 2 * _gmf_m)) <= 2
                or abs(_gmf_op.w - (_gmf_area.w - 2 * _gmf_m)) <= 2), (
            _W, "the popup does not fill the free area", _gmf_op, _gmf_area)
        # One factor for every box: the seated body is the file's body times
        # content_scale, and a seated button keeps its offset in proportion.
        _gmf_k = _gmf_s.content_scale
        assert 0.5 < _gmf_k < 1.2, _gmf_k
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
        from core.hud import blocks as _gmf_hud
        _gmf_real_pop = _gmf_hud.popup
        for _n in _gmf_nodes:
            _gmf_gs.fields = _gm_fields(_gm_fix[_n])
            _gmf_s.update(_gmf_gs)
            # The popup blocks themselves are left out: their GLOW is
            # meant to reach past the rect, and what must stay inside is
            # the content drawn on them.
            _gmf.draw = lambda *_a: True
            _gmf_hud.popup = lambda *_a, **_k: None
            try:
                _gmf_surf = pygame.Surface((_W, _H))
                _gmf_surf.fill((255, 0, 255))
                _gmf_s.render(_gmf_surf)
            finally:
                _gmf.draw = _gmf_real
                _gmf_hud.popup = _gmf_real_pop
            _px = pygame.surfarray.array3d(_gmf_surf).transpose(1, 0, 2)
            _content = ~((_px[:, :, 0] == 255) & (_px[:, :, 1] == 0)
                         & (_px[:, :, 2] == 255))
            assert _content.sum() > 2000, (_W, _n, "drew nothing")
            _inside = np.zeros_like(_content)
            _inside[_gmf_op.top:_gmf_op.bottom,
                    _gmf_op.left:_gmf_op.right] = True
            _out = _content & ~_inside
            assert not _out.any(), (
                f"GAME menu {_n} at {_W}x{_H}: {int(_out.sum())} px of "
                f"content outside the popup body")
            # THE FILL: the popup is opaque — sampled in the drawn popup,
            # off every box, it must not be the map underneath.
            if _n == "menu":
                _gmf_full = pygame.Surface((_W, _H))
                _gmf_full.fill((255, 0, 255))
                _gmf_s.render(_gmf_full)
                _pt = (_gmf_op.centerx, _gmf_op.y + _gmf_op.h // 2)
                assert _gmf_full.get_at(_pt)[:3] != (255, 0, 255), (
                    _W, "the popup is not filled")
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
    ok("GAME menu popup: seated in the galaxy map's free area below the "
       "title plate with every box by one factor, all six dialogs inside "
       "the popup body and filled at 1080p/1440p/2160p")
