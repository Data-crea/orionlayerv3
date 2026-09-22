# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 070_core_game_menu_all_six_nodes_render.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - GAME menu: all six nodes render; no slot message -> no invented label, MSG_SAVE_SLOTS -> the eng


# 4. EVERY NODE RENDERS. With MSG_SAVE_SLOTS (open fix 14, applied
#    16 September 2026) the rows are the engine's strings verbatim;
#    without it — the one tick before the message — a row draws no
#    invented label, and "Slot N" may not come back.
_gm_live = bytes([1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0,
                  1, 50, 1, 49, 7]) + bytes(_gm_set.SIZE - 22)
_gm_gs.settings_raw = _gm_live
_gm_scr.enter(_gm_gs)
_gm_said = []
_gm_real_rt = app.style.render_text
app.style.render_text = lambda t, *a, **k: (_gm_said.append(t),
                                           _gm_real_rt(t, *a, **k))[1]
try:
    for _n in ("menu", "settings", "load", "save", "confirm",
               "warning"):
        _gm_gs.fields = _gm_fields(_gm_fix[_n])
        _gm_scr.update(_gm_gs)
        _gm_scr.render(surf)
    assert not any(str(_s).startswith("Slot ") for _s in _gm_said), \
        "a slot row drew an invented 'Slot N' label"
    # UNDER A CONFIRMATION the menu stays drawn, as the original keeps
    # the popup behind Confirmation_Box_ (work order 124 D): its buttons
    # come from the menu's last list, not the confirmation's.
    _gm_gs.fields = _gm_fields(_gm_fix["menu"])
    _gm_scr.update(_gm_gs)
    _gm_gs.fields = _gm_fields(_gm_fix["confirm"])
    _gm_scr.update(_gm_gs)
    _gm_said.clear()
    _gm_scr.render(surf)
    for _gm_w in ("save", "load", "settings", "return"):
        assert _gmd_word(_gm_scr, _gm_w) in _gm_said, (
            f"menu button {_gm_w} missing under the confirmation")
    _gm_said.clear()
    _gm_rec = bytes([0, 0]) + b"\x03Test Save\x01".ljust(37, b"\0") + \
        b"Stardate:3500.0".ljust(25, b"\0") + \
        b"31, 126 13:52".ljust(25, b"\0")
    _gm_gs.save_slots = _gm_wp.parse_save_slots(bytes([2, 10]) +
                                               _gm_rec * 10)
    _gm_gs.fields = _gm_fields(_gm_fix["load"])
    _gm_scr.update(_gm_gs)
    _gm_scr.render(surf)
    assert "Test Save" in _gm_said and "31, 126 13:52" in _gm_said, \
        "slot strings were not drawn as the engine formatted them"
    assert _gm_gs.save_slots["slots"][0]["active_marked"]
finally:
    app.style.render_text = _gm_real_rt
_gm_gs.save_slots = None
ok("GAME menu: all six nodes render; no slot message -> no invented "
   "label, MSG_SAVE_SLOTS -> the engine's strings verbatim, colour codes cut")
