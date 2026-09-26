# smoke-suite area: select_race
#
# Part of the OrionLayer smoke suite — 090m_select_race_text_scales_once.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 179, part 5: Select Race's text overlapped at 2160p — the
# race name over its subtitle, the government row cut off — because every
# size went through `Layout.font_size` with `box_font_scale` (already x
# win_h/1080) inside it: 4x the 1080p size where 2x is proportional.
#
# The 1 check(s) it holds:
#   - Select Race: every text size at 2160p is twice its 1080p size (scaled once)


import hud_evidence as _sr_he


def _sr_sizes(w, h):
    app = _sr_he.make_app(w, h)
    _sr_he.stage(app, "select_race")
    scr = app.dispatcher.active
    seen = []
    real = (scr.style.get_font, scr.style.get_prop_font)

    here = os.path.join(SCREENS_DIR, "select_race")

    def rec(fn):
        # The screen's OWN text (screen.py, renderer.py, info_panel.py);
        # the shared HUD frame — title plate, BACK — sizes itself by its
        # own rule and is measured with the HUD blocks, not here.
        def inner(size, *a, **k):
            if os.path.dirname(os.path.abspath(
                    sys._getframe(1).f_code.co_filename)) == here:
                seen.append(size)
            return fn(size, *a, **k)
        return inner
    scr.style.get_font, scr.style.get_prop_font = rec(real[0]), rec(real[1])
    try:
        scr.render(pygame.Surface((w, h)))
    finally:
        scr.style.get_font, scr.style.get_prop_font = real
    return sorted(seen)


_sr_1080 = _sr_sizes(1920, 1080)
_sr_2160 = _sr_sizes(3840, 2160)
assert len(_sr_1080) >= 6 and len(_sr_1080) == len(_sr_2160), \
    (len(_sr_1080), len(_sr_2160))
for _a, _b in zip(_sr_1080, _sr_2160):
    # `Layout.font_size` has a floor of 8: a 1080p size AT the floor may
    # stand for a smaller one, so it only bounds the 2160p size.
    assert _b <= 2 * _a + 1 and (_a == 8 or abs(_b - 2 * _a) <= 1), (
        f"a Select Race text of {_a} px at 1080p is {_b} px at 2160p — the "
        f"window scale is applied twice")
assert "self.box_font_scale(" not in open(os.path.join(
    SCREENS_DIR, "select_race", "screen.py"), encoding="utf-8").read()
ok(f"Select Race: {len(_sr_1080)} text sizes measured — each at 2160p is "
   f"twice its 1080p size (scaled once), so nothing overlaps that did not "
   f"at 1080p")
