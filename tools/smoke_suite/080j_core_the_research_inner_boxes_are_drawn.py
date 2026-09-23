# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080j_core_the_research_inner_boxes_are_drawn.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (104 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 166 part C,
# the eight inner boxes.
#
# The 2 check(s) it holds:
#   - neither research screen wears frame ARTWORK any more: no box
#     names a skin, and the drawing goes through one helper
#   - the eight boxes are drawn at the game's own block rectangles,
#     all eight, offered or not
from core import researchpanel as _ib_panel

# ── NO ARTWORK LEFT ON EITHER SCREEN ──
#
# The eight entry boxes wore `inner_panel`, a nine-sliced IMAGE out of
# the skin, and Data's verdict on the live panel was that it does not
# fit them. A box with NO SKIN draws nothing of its own, which is what
# lets the drawing live with the rest of the panel's drawing.
for _ib_screen in ("research_select", "research_change"):
    _ib_boxes = _sjson.load(open(os.path.join(
        SCREENS_DIR, _ib_screen, "boxes.json"), encoding="utf-8"))
    for _ib_res, _ib_list in _ib_boxes.items():
        for _ib_b in _ib_list:
            _ib_skin = (_ib_b.get("style") or {}).get("skin")
            assert _ib_skin != "inner_panel", (
                f"{_ib_screen}/{_ib_res}: {_ib_b['name']} wears the "
                f"inner_panel ARTWORK again")
            if _ib_b["name"].startswith("entry_"):
                assert not _ib_b.get("style"), (
                    f"{_ib_screen}: {_ib_b['name']} grew a style; the "
                    f"entry boxes are drawn in code")
    # …and the screen says so where a reader meets it.
    _ib_layout = _sjson.load(open(os.path.join(
        SCREENS_DIR, _ib_screen, "layout.json"), encoding="utf-8"))
    assert "entry_boxes_note" in _ib_layout, _ib_screen

# ONE HELPER, not a second copy. The list popup drew its window with
# two hand-written `draw.rect` calls and two colours of its own; the
# entry boxes would have made that a third.
_ib_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "core",
                               "researchtechlist.py"),
                  encoding="utf-8").read()
assert "draw_box(" in _ib_src, (
    "the list popup no longer draws its window through the shared "
    "helper")
assert "pygame.draw.rect(surface, col(\"list_fill\"" not in _ib_src
# And the two colours are the PLANETS screen's own, read from the
# section that owns them rather than copied into this screen's.
from screens.planets import planetdraw as _ib_plan
assert tuple(_ib_panel.BOX_FILL)[:3] == tuple(_ib_plan.PANEL_BG)[:3], (
    _ib_panel.BOX_FILL, _ib_plan.PANEL_BG)
assert tuple(_ib_panel.BOX_OUTLINE)[:3] == tuple(_ib_plan.OUTLINE)[:3], (
    _ib_panel.BOX_OUTLINE, _ib_plan.OUTLINE)
ok("neither research screen wears frame ARTWORK any more: no box names "
   "a skin, and the drawing goes through one helper")

# ── AND ALL EIGHT ARE DRAWN, AT THE GAME'S OWN RECTANGLES ──
#
# `Init_Entry_Data_` adds a block field for every category and the
# original draws an empty panel for one with nothing to offer
# (tech.cpp:225-231), so a box is drawn for all eight — and at the same
# rectangle the reconstruction is validated against, which is what
# `Entry.block_rect` being one function buys (decision 5).
_ib_entries = _rl.reconstruct(_dx_tf, _dx_ta, select_mode=False)
assert len(_ib_entries) == 8
_ib_offered = [_e for _e in _ib_entries if _e.offered]
assert 0 < len(_ib_offered) < 8, (
    f"{len(_ib_offered)} of 8 offered — this fixture cannot tell "
    f"'all eight' from 'the offered ones'")
_ib_blocks = {_k: _r for _k, _t, _r in
              _rl.expected_fields(_ib_entries, select_mode=False)
              if _k.startswith("block ")}
for _ib_e in _ib_entries:
    assert _ib_e.block_rect() == _ib_blocks[f"block {_ib_e.index}"], \
        _ib_e.index

_ib_surf = pygame.Surface((1920, 1080))
_ib_surf.fill((0, 0, 0))
_ib_panel.draw(_ib_surf, _dx_scr.layout, _dx_scr.style, _ib_entries,
               None, {"cost": lambda e: None}, _dx_scr._names,
               _dx_scr._wording)
_ib_drawn = 0
for _ib_e in _ib_entries:
    _bx, _by, _bw, _bh = _dx_geo.window_rect(_ib_e.block_rect(),
                                             _dx_scr.layout)
    # The fill is inside; the outline is on the edge. Both are asked
    # for, so a box that drew only one of them fails.
    assert _ib_surf.get_at((_bx + _bw // 2, _by + _bh // 2))[:3] == \
        tuple(_ib_panel.BOX_FILL)[:3], _ib_e.index
    _ib_edge = [_ib_surf.get_at((_x, _by + _bh // 2))[:3]
                for _x in range(_bx, _bx + 3)]
    assert any(_p != (0, 0, 0) and _p != tuple(_ib_panel.BOX_FILL)[:3]
               for _p in _ib_edge), (
        f"entry {_ib_e.index} has a fill and no outline")
    _ib_drawn += 1
assert _ib_drawn == 8, _ib_drawn
ok("the eight boxes are drawn at the game's own block rectangles, all "
   "eight, offered or not")
