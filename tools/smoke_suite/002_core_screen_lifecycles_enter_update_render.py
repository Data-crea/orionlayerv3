# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 002_core_screen_lifecycles_enter_update_render.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - screen lifecycles (enter/update/render/click/resize)


# ── Screen lifecycles ──
surf = pygame.Surface((1920, 1080))
for name in sorted(d.screens):
    d.switch_to(name)
    s = d.active
    s.update(None)
    s.render(surf)
    s.handle_click(960, 540)
    s.handle_mouse_motion(960, 540)
    s.on_resize()
ok("screen lifecycles (enter/update/render/click/resize)")
