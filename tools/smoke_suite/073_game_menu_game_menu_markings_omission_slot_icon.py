# smoke-suite area: game_menu
#
# Part of the OrionLayer smoke suite — 073_game_menu_game_menu_markings_omission_slot_icon.py.
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
#   - GAME menu markings: OMISSION (slot icon), UNVERIFIED (Save right click), DEVIATION (empty slot e
#   - GAME menu popup drawn on the first opening: its rim is on the screen at 1080p and 1440p


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

# 7a. THE POPUP IS ON THE SCREEN, on the FIRST opening. Rewritten by
#     work order 169 (decision 71) from "the metal is on the screen": the
#     frame image is no longer drawn, and the fault this check exists for
#     is unchanged — every other placement check entered the overlay
#     twice, which is what hid a first opening that drew the fill alone
#     (16 September 2026). It takes the real path once — a fresh app, the
#     dispatcher opening the overlay for screen 8 — renders it, and
#     compares the popup's RIM (the band of its edge line, where no
#     content is drawn) with the popup block drawn alone at that rect.
if slow("game_menu_frame_drawn"):
    from screens.game_menu import gmframe as _mt_gmf
    from core.hud import blocks as _mt_hud
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
        _mt_fr, _mt_op = _mt_gmf.rects(_mt_s)
        assert _mt_fr is not None, (
            _W, "the first opening of the GAME menu has no placement")
        _mt_surf = pygame.Surface((_W, _H))
        _mt_surf.fill((255, 0, 255))
        _mt_s.render(_mt_surf)
        _mt_ref = pygame.Surface((_W, _H))
        _mt_ref.fill((255, 0, 255))
        _mt_hud.popup(_mt_ref, _mt_op, _mt_s.layout.scale)
        _mt_rim = np.zeros((_H, _W), bool)
        _mt_e = max(2, int(3 * _mt_s.layout.scale))
        _mt_rim[_mt_op.top:_mt_op.bottom, _mt_op.left:_mt_op.right] = True
        _mt_rim[_mt_op.top + _mt_e:_mt_op.bottom - _mt_e,
                _mt_op.left + _mt_e:_mt_op.right - _mt_e] = False
        _mt_a = pygame.surfarray.array3d(_mt_surf).transpose(1, 0, 2)
        _mt_b = pygame.surfarray.array3d(_mt_ref).transpose(1, 0, 2)
        _mt_n = int(_mt_rim.sum())
        _mt_hit = int((np.abs(_mt_a[_mt_rim].astype(int)
                              - _mt_b[_mt_rim].astype(int)).max(axis=1)
                       <= 4).sum())
        assert _mt_n > 2000 and _mt_hit >= 0.98 * _mt_n, (
            f"GAME menu popup at {_W}x{_H}: {_mt_hit} of {_mt_n} rim "
            f"pixels drawn — the popup is not on the screen")
    ok("GAME menu popup drawn on the first opening: its rim is on the "
       "screen at 1080p and 1440p")
