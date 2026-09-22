# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 073_game_menu_game_menu_markings_omission_slot_icon.py.
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
#   - GAME menu markings: OMISSION (slot icon), UNVERIFIED (Save right click), DEVIATION (empty slot e
#   - GAME menu frame drawn on the first opening: the metal's opaque pixels are on the screen at 1080p


# 7. THE MARKINGS cannot silently disappear: module, layout.json and
#    the status document, for each omission and the HD state.
_gm_doc = _gm_scr.__class__.__module__
_gm_mod = sys.modules[_gm_doc].__doc__
_gm_lay = _gm_json.load(open(os.path.join(
    SCREENS_DIR, "game_menu", "layout.json")))
_gm_status = open(os.path.join(os.path.dirname(SCREENS_DIR),
                               "v3_projektstatus.md"),
                  encoding="utf-8").read()
for _mark in ("OMISSION", "UNVERIFIED"):
    assert _mark in _gm_mod, f"screen.py lost its {_mark} marking"
# The slot-name HD STATE ended with open fix 14 (16 September 2026):
# its marking, its label and its word are gone, and must stay gone.
assert "slot rows show their number" not in _gm_mod
assert "hd_state_slot" not in _gm_lay["words"] and \
    "slot" not in _gm_lay["words"]
assert "omission_sliders" not in _gm_lay, "the slider omission is back"
assert _gm_lay["slot_rows"]["omission_icon"].startswith("OMISSION")
assert _gm_lay["unverified_right_click"].startswith("UNVERIFIED")
# The empty slot's edit (work order 126 D): a deliberate DEVIATION, in
# the module where the edit starts, the screen's list, layout.json and
# the status document.
from screens.game_menu import gmsave as _gm_sv
import inspect as _gm_insp
assert "DEVIATION — an EMPTY slot starts the edit EMPTY" in \
    _gm_insp.getsource(_gm_sv.SaveEditor.start)
assert "DEVIATION — an empty save slot" in _gm_mod
assert _gm_lay["save_empty_slot_deviation"].startswith("DEVIATION")
assert "DEVIATION — the empty save slot's name edit starts empty" in \
    _gm_status, "status document lost the empty-slot DEVIATION"
for _mark in ("OMISSION — the slot game-type icon",
              "UNVERIFIED — the Save dialog's right click"):
    assert _mark in _gm_status, f"status document lost: {_mark}"
ok("GAME menu markings: OMISSION (slot icon), UNVERIFIED (Save right "
   "click), DEVIATION (empty slot edit) in module, layout, status; the "
   "slot-name HD STATE gone")

# 7a. THE METAL IS ON THE SCREEN, on the FIRST opening. Every other
#     frame check measures geometry, and every one of them entered the
#     overlay twice — which is exactly what hid the missing artwork:
#     `enter` seated the boxes before it had read layout.json, so the
#     first opening drew the fill alone (16 September 2026). This one
#     takes the real path once — a fresh app, the dispatcher opening the
#     overlay for screen 8 — renders it, and compares the drawn pixels
#     with the scaled frame image wherever that image is fully opaque.
if slow("game_menu_frame_drawn"):
    from screens.game_menu import gmframe as _mt_gmf
    for _W, _H in ((1920, 1080), (2560, 1440)):
        _mt_app, _ = _pv.build_screen(_W, _H)
        _mt_d = _mt_app.dispatcher
        _mt_d.switch_to("galaxy_map")
        _mt_gs = _GmState()
        _mt_gs.current_screen = 8
        _mt_gs.settings_raw = _gm_live
        _mt_gs.fields = _gm_fields(_gm_fix["menu"])
        _mt_d.update_from_game(_mt_gs)
        _mt_s = _mt_d.overlay
        assert _mt_d.overlay_name == "game_menu" and _mt_s is not None
        _mt_s.update(_mt_gs)
        _mt_fr, _ = _mt_gmf.rects(_mt_s)
        assert _mt_fr is not None, (
            _W, "the first opening of the GAME menu has no frame placement")
        _mt_surf = pygame.Surface((_W, _H))
        _mt_surf.fill((255, 0, 255))
        _mt_s.render(_mt_surf)
        _mt_img = pygame.transform.smoothscale(pygame.image.load(
            res.screen_file("game_menu", "assets", "frame.png")),
            _mt_fr.size)
        _mt_a = pygame.surfarray.array_alpha(_mt_img).T
        _mt_rgb = pygame.surfarray.array3d(_mt_img).transpose(1, 0, 2)
        # `smoothscale` tops out a hair below 255 (253 measured), so "fully
        # opaque" is >= 250 and the colour may carry that sliver of ground.
        _mt_ys, _mt_xs = np.where(_mt_a >= 250)
        _mt_ys, _mt_xs = _mt_ys + _mt_fr.y, _mt_xs + _mt_fr.x
        _mt_in = (_mt_ys >= 0) & (_mt_ys < _H) & (_mt_xs >= 0) & (_mt_xs < _W)
        _mt_draw = pygame.surfarray.array3d(_mt_surf).transpose(1, 0, 2)[
            _mt_ys[_mt_in], _mt_xs[_mt_in]].astype(int)
        _mt_want = _mt_rgb[_mt_ys[_mt_in] - _mt_fr.y,
                           _mt_xs[_mt_in] - _mt_fr.x].astype(int)
        _mt_hit = int((np.abs(_mt_draw - _mt_want).max(axis=1) <= 4).sum())
        _mt_n = int(_mt_in.sum())
        assert _mt_n > 50000 and _mt_hit >= 0.98 * _mt_n, (
            f"GAME menu frame at {_W}x{_H}: {_mt_hit} of {_mt_n} opaque "
            f"frame pixels drawn — the artwork is not on the screen")
    ok("GAME menu frame drawn on the first opening: the metal's opaque "
       "pixels are on the screen at 1080p and 1440p")
