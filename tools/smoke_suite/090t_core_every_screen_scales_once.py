# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 090t_core_every_screen_scales_once.py.
# `tools/smoke_test.py` executes this file, and every other module in
# tools/smoke_suite/, in file-name order and in ONE namespace. Do not
# import this file; it is not a module.
#
# The 1 check(s) it holds:
#   - every screen the tree can stage scales its text once: no font at 3840 over twice its 1920 size, by call site


# ── THE WINDOW'S FACTOR, APPLIED ONCE — EVERY SCREEN (work order 182) ──
#
# 179 found the factor applied twice on the star names and Select Race and
# checked those two (090l, 090m); Custom Race and Empire Identity had the
# same fault for three more work orders. This check is not per screen: it
# renders EVERY screen of the registry `hud_evidence` can stage from the
# tree alone (and the popups it can open) at 1920x1080 and 3840x2160,
# records every font size each render asks for by the calling line, and
# refuses a line whose largest size at 3840 is more than twice its largest
# at 1920 — scaled once is 2x, twice is 4x, and the way it was written
# does not matter. WHY RENDERING AND NOT A STATIC RULE: the fault is
# arithmetic that travels — `win_h / 1080` into an `fs` handed to another
# module's `L.font_size(int(14 * fs))` — and a pattern either misses the
# hop or forbids the legitimate direct sizing (`box_font_scale` IS right
# for a caller that sizes in device pixels). The render sees the result.
# Both windows load the SAME box section, so Data's per-resolution F5
# `font_scale` cannot pass for a code fault or hide one. Screens the tree
# cannot stage with text (they need a game) are named, not skipped
# silently; the colony screen, the build popup and the Leaders screen are
# measured by their own groups from their fixtures (090p, 090q, 090c).
import hud_evidence as _so_he

_so_app = _so_he.make_app(1920, 1080)
_so_targets = sorted(_so_app.dispatcher.screens) + ["help_popup",
                                                    "custom_race_message",
                                                    "f12_notice"]


def _so_sites(name, w, h):
    app = _so_he.make_app(w, h)
    if name == "f12_notice":
        # Work order 188: the F12 notice (Stage 1) is the App's panel, not
        # a screen's — drawn over the held galaxy map, as the App does.
        from core import f12notice as _so_fn
        _so_he.stage(app, "galaxy_map")
        d = app.dispatcher

        def draw():
            surf = pygame.Surface((w, h))
            d.active.render(surf)
            _so_fn.Notice().render(surf, d.active.style, {},
                                   "NEXT_TURN (12)")
        return _so_he.font_sites(d.active.style, draw)
    _so_he.stage(app, name)
    d = app.dispatcher

    def draw():
        surf = pygame.Surface((w, h))
        d.active.render(surf)
        if d.overlay_name:
            d.screens[d.overlay_name].render(surf)
    return _so_he.font_sites(d.active.style, draw)


_so_undo = _so_he.same_boxes()
_so_bad, _so_measured, _so_blank = {}, {}, []
try:
    for _so_n in _so_targets:
        _so_a = _so_sites(_so_n, 1920, 1080)
        _so_b = _so_sites(_so_n, 3840, 2160)
        if not _so_a:
            _so_blank.append(_so_n)
            continue
        _so_measured[_so_n] = len(_so_a)
        _so_over = _so_he.scaled_twice(_so_a, _so_b)
        if _so_over:
            _so_bad[_so_n] = _so_over
finally:
    _so_undo()
assert not _so_bad, ("text scaled twice (largest size at 1920 -> at 3840, "
                     f"by call site): {_so_bad}")
# The force of the check is what it saw (fundament, "a green run in a null
# state"): at least these screens with text, and the blank ones by name.
assert {"custom_race", "empire_identity", "select_race", "galaxy_map",
        "colony_summary", "new_game", "main_menu",
        "f12_notice"} <= set(_so_measured), \
    _so_measured
assert set(_so_blank) <= {"colony", "build_queue", "leaders"}, _so_blank
ok(f"every screen the tree can stage scales its text once: "
   f"{sum(_so_measured.values())} call sites on {len(_so_measured)} screens "
   f"and popups, none at 3840 over twice its 1920 size "
   f"(no text offline, measured by their groups: {', '.join(_so_blank)})")
