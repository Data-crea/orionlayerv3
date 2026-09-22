# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 004_core_screen_ids_claimed_each_by_one.py.
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
#   - screen ids: claimed, each by one screen, synthetic ones above the engine's last SCREEN value (),
#   - editor select + resize + glow + overlay


# ── Screen ids: one screen per id, and synthetic ids outside the
#    engine's own range (work order 128 B, open fix 22) ──
# Select Race claimed 6 because our own patch borrowed SCREEN_RACE,
# and 6 is the Races screen: HD drew race selection over diplomacy.
# The rule, read off every screen module in the tree and in mods, and
# held against core/screen_names.py (the one home of the table):
# no two screens claim one id; an id the engine's enum has is <= its
# last value; a synthetic id lies above it; the table names the
# screen that claims the id.
import ast as _sid_ast
from core import screen_names as _sid_names
_sid_claims = {}
_sid_root = os.path.dirname(SCREENS_DIR)
for _sid_path in sorted(glob.glob(os.path.join(SCREENS_DIR, "*", "screen.py"))
                        + glob.glob(os.path.join(_sid_root, "mods", "*",
                                                 "screens", "*", "screen.py"))):
    for _sid_node in _sid_ast.walk(_sid_ast.parse(open(_sid_path).read())):
        if (isinstance(_sid_node, _sid_ast.Assign)
                and any(getattr(_t, "id", None) == "GAME_SCREEN_ID"
                        for _t in _sid_node.targets)
                and isinstance(_sid_node.value, _sid_ast.Constant)
                and isinstance(_sid_node.value.value, int)):
            _sid_claims.setdefault(_sid_node.value.value, []).append(
                os.path.basename(os.path.dirname(_sid_path)))
assert len(_sid_claims) >= 8, _sid_claims
_sid_dupes = {k: v for k, v in _sid_claims.items() if len(v) > 1}
assert not _sid_dupes, f"one screen id claimed twice: {_sid_dupes}"
for _sid, (_sid_engine, _sid_hd) in _sid_names.SCREENS.items():
    if _sid_engine == "(synthetic)":
        assert _sid > _sid_names.ENGINE_SCREEN_MAX, (
            f"synthetic screen id {_sid} lies inside the engine's range "
            f"(0..{_sid_names.ENGINE_SCREEN_MAX})")
    else:
        assert _sid <= _sid_names.ENGINE_SCREEN_MAX, (_sid, _sid_engine)
for _sid, _sid_who in _sid_claims.items():
    assert _sid in _sid_names.SCREENS, f"screen id {_sid} ({_sid_who}) not in the table"
    assert _sid_names.SCREENS[_sid][1] == _sid_who[0], (
        f"core/screen_names.py names {_sid_names.SCREENS[_sid][1]!r} for "
        f"id {_sid}, the tree's screen is {_sid_who[0]!r}")
ok(f"screen ids: {len(_sid_claims)} claimed, each by one screen, synthetic "
   f"ones above the engine's last SCREEN value "
   f"({_sid_names.ENGINE_SCREEN_MAX}), table agrees")

# ── Editor ──
app.editor = Editor(app)
d.switch_to("main_menu")
ed = app.editor
ed.toggle()
ed.render(surf)
ed.handle_event(pygame.event.Event(
    pygame.MOUSEBUTTONDOWN, button=1, pos=(960, 540)))
scr = d.active
if scr.boxes:
    box = scr.boxes[0]
    cx, cy = box.screen_rect.center
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy)))
    assert ed.selected is box
    # Resize-handle drag (bottom-right corner)
    r = box.screen_rect
    old = tuple(box.ref_rect)
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONUP, button=1, pos=(cx, cy)))
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(r.right, r.bottom)))
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEMOTION, pos=(r.right + 15, r.bottom + 10)))
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONUP, button=1,
        pos=(r.right + 15, r.bottom + 10)))
    assert tuple(box.ref_rect) != old, "resize had no effect"
    # Glow + rotate + nudge path
    ed.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_g, mod=0))
    ed.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_r, mod=0))
    ed.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_LEFT, mod=0))
ed.render(surf)
ed.toggle()
ok("editor select + resize + glow + overlay")
