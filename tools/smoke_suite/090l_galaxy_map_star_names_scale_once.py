# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 090l_galaxy_map_star_names_scale_once.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/, in file-name order and in ONE
# namespace. Do not import this file; it is not a module.
#
# Work order 179, part 5: at 2160p the star names were twice their size —
# `box_font_scale` (x win_h/1080) fed into `Layout.font_size` (x the window
# scale again), 4x the 1080p size where 2x is proportional. The rule held
# here is the property, measured on the real screen: every text size the
# map asks for at 3840x2160 is twice its size at 1920x1080.
#
# The 1 check(s) it holds:
#   - galaxy map: star names (and the hover name) scale once with the window — 2160p twice 1080p


import hud_evidence as _sn_he


def _sn_sizes(w, h):
    app = _sn_he.make_app(w, h)
    _sn_he.stage(app, "galaxy_map")
    scr = app.dispatcher.active
    seen = []
    real = scr.style.render_text

    def rec(text, size, colour, *a, **k):
        seen.append(size)
        return real(text, size, colour, *a, **k)
    scr.style.render_text = rec
    try:
        scr.render(pygame.Surface((w, h)))
    finally:
        scr.style.render_text = real
    return sorted(seen)


_sn_1080 = _sn_sizes(1920, 1080)
_sn_2160 = _sn_sizes(3840, 2160)
# Forty named stars in the fixture: the count says how much was seen.
assert len(_sn_1080) >= 40 and len(_sn_1080) == len(_sn_2160), \
    (len(_sn_1080), len(_sn_2160))
for _a, _b in zip(_sn_1080, _sn_2160):
    assert abs(_b - 2 * _a) <= 1, (
        f"a star name of {_a} px at 1080p is {_b} px at 2160p — the window "
        f"scale is applied twice (box_font_scale into Layout.font_size)")
_sn_src = open(os.path.join(SCREENS_DIR, "galaxy_map", "screen.py"),
               encoding="utf-8").read()
assert 'self.box_font_scale("map_area")' not in _sn_src, \
    "the hover name squares the resolution factor again"
ok(f"galaxy map: {len(_sn_1080)} star names measured — every one at 2160p "
   f"is twice its 1080p size (scaled once, by Layout.font_size); the hover "
   f"name the same way")
