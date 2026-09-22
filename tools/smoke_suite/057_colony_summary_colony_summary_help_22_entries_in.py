# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 057_colony_summary_colony_summary_help_22_entries_in.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - colony summary help: 22 entries in erichelp.cpp's order with the fallback last, heading plates a


# Auto-sizing is an HD EXTENSION (the original draws a fixed box
# and wraps into it at a fixed 339 px). What has to hold is that
# the extension does not lose text: a body too tall for the panel
# becomes scrollable rather than clipped, and a short one does
# not scroll. Assert the invariant, not the pixel height.
# ── THE COLONY SUMMARY'S HELP — brief 98 ─────────────────────
# Transcribed from ERICHELP::_colony_summary_screen_help_list. The
# ORDER is asserted against the C++ table itself when the orion2re
# tree is on this disk (the `_source` the file names), because the
# walk stops at the first hit and a reordered table shadows
# entries with nothing on screen to show it; without the tree the
# run says so. Then, drawn through the SHARED walk and popup: a
# heading plate answers its column's entry, the surface picture and
# the name heading answer what the original's rectangles give them,
# the fallback is last, and a long entry scrolls at four sizes.
import re as _ch_re
_ch_doc = _hjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "help.json"), encoding="utf-8"))
_ch_regs = _ch_doc["regions"]
assert _ch_regs[-1].get("screen") and not any(
    _r.get("screen") for _r in _ch_regs[:-1]), (
    "the screen-wide fallback is not last in colony_summary/help.json")
_ch_file, _ch_line = _ch_doc["_source"].split(":")
_ch_cpp = os.path.expanduser(os.path.join(
    "~", "orion2re", "src", "game", _ch_file))
if os.path.exists(_ch_cpp):
    _ch_src = open(_ch_cpp, encoding="utf-8", errors="replace").read()
    _ch_tab = _ch_src.split("\n")[int(_ch_line) - 1:]
    _ch_body = "\n".join(_ch_tab)
    _ch_body = _ch_body[:_ch_body.index("};")]
    assert "_colony_summary_screen_help_list" in _ch_tab[0], (
        f"{_ch_doc['_source']} is not the colony summary's help table")
    _ch_rows = [tuple(int(_v) for _v in _m) for _m in _ch_re.findall(
        r"\{(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\}", _ch_body)]
    _ch_mine = [(_r["help_id"], *_r["native"]) for _r in _ch_regs]
    assert _ch_rows == _ch_mine, (
        f"colony_summary/help.json is not {_ch_doc['_source']} in "
        f"order: source {_ch_rows}, file {_ch_mine}")
else:
    report(f"colony help order NOT checked against the C++ table — "
           f"{_ch_cpp} is not on this disk")
for _ch_W, _ch_H in ((1280, 720), (1920, 1080), (2560, 1440),
                     (3840, 2160)):
    _ch_app, _ch_scr = _pv.build_screen(_ch_W, _ch_H)
    _ch_app.dispatcher.switch_to("colony_summary")
    _ch_scr.enter(None)
    _ch_scr.update(_pv._Snapshot(_pv.COLONIES))
    assert len(_ch_scr._help_regions) == len(_ch_regs)

    def _ch_hit(_pt):
        _ch_scr.help.close()
        assert _ch_scr.handle_right_button(True, *_pt) is True, (
            f"{_ch_W}x{_ch_H}: a right click at {_pt} opened nothing — "
            f"the screen-wide entry should catch every point")
        return _ch_scr.help.help_id

    _ch_area, _ch_cfg, _ch_sc, _ = _ch_scr._list_view()
    _ch_plates = dict(_chdr0.plate_rects(
        _ch_scr.layout.rect(_ch_scr.box_rect("header")),
        _ctk.columns(_ch_area, _ch_cfg), _ch_scr.layout.scale))
    for _ch_key, _ch_id in (("name", 515), ("farmers", 516),
                            ("workers", 517), ("scientists", 518),
                            ("building", 519)):
        assert _ch_hit(_ch_plates[_ch_key].center) == _ch_id, (
            f"{_ch_W}x{_ch_H}: the {_ch_key} heading plate does not "
            f"answer help {_ch_id} — the column region must include "
            f"its heading, as the original's rectangle does")
    for _ch_box, _ch_id in (("planet_name", 523), ("planet_output", 524),
                            ("planet_surface", 513),
                            ("empire_stats", 526), ("return", 500),
                            ("sort_bc", 533)):
        _ch_c = pygame.Rect(*_ch_scr.layout.rect(
            _ch_scr.box_rect(_ch_box))).center
        assert _ch_hit(_ch_c) == _ch_id, (
            f"{_ch_W}x{_ch_H}: a right click on {_ch_box} opened "
            f"{_ch_scr.help.help_id}, the original's table gives {_ch_id}")
    _ch_up, _ch_down = _lp_scroll.arrows(_ch_area, _ch_cfg, _ch_sc)
    assert _ch_hit(_ch_up.center) == 514 and \
        _ch_hit(_ch_down.center) == 522 and \
        _ch_hit(_lp_scroll.track(_ch_area, _ch_cfg, _ch_sc).center) == 521
    # A LONG ENTRY SCROLLS in the shared popup at this size.
    _ch_scr.help.open(516, "Long", "\n".join(
        f"Line {_i} of a long help entry that has to keep going."
        for _i in range(80)))
    _ch_s = pygame.Surface((_ch_W, _ch_H))
    _ch_scr.render(_ch_s)
    assert _ch_scr.help._max_scroll > 0, (
        f"{_ch_W}x{_ch_H}: a long entry does not scroll in the "
        f"colony screen's popup")
    _ch_before = _ch_scr.help._scroll
    assert _ch_scr.handle_mousewheel(-1, 10, 10) is True and \
        _ch_scr.help._scroll > _ch_before, (
        f"{_ch_W}x{_ch_H}: the wheel did not scroll the open popup")
    # AND A LEFT CLICK CLOSES IT WITHOUT REACHING THE SCREEN.
    _ch_scr.handle_click(*_ch_up.center)
    assert not _ch_scr.help.visible, (
        f"{_ch_W}x{_ch_H}: a left click did not close the popup")
ok("colony summary help: 22 entries in erichelp.cpp's order with the "
   "fallback last, heading plates answer their column, the bottom "
   "row answers by box, and a long entry scrolls at four sizes")
