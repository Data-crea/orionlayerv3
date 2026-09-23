# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080k_core_the_research_text_fits_its_box.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (105 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 166 part D,
# text that fits.
#
# The 2 check(s) it holds:
#   - every name and row label lies inside its own box with the
#     margin, at four resolutions, with the longest real names
#   - the hover band covers its row and stays inside the box, and the
#     header words stay above it
from core.helppopup import FALLBACK_BOX as _HelpFallbackBox
from core import researchpanel as _tf_panel

# ── THE LONGEST REAL NAMES, PER BOX ──
#
# Not a made-up string: the longest FIELD name each of the eight
# categories can offer, out of the player's own TECHNAME tables, with
# every one of that field's applications available so the box is as
# full as the game can make it. A check that measures the short names
# measures the case that was never in doubt.
_tf_names = derived(_dx_tn.TechNames)
_tf_tf = [0] * _rl_res.FIELD_COUNT
_tf_slots = _rl.field_applications()
_tf_picked = []
for _tf_i, _tf_group in enumerate(_rl.ENTRY_TO_GROUP):
    _tf_chain, _tf_f = [], _rl.FIRST_FIELD_IN_GROUP[_tf_group]
    while _tf_f:
        _tf_chain.append(_tf_f)
        _tf_f = _rl.NEXT_FIELD[_tf_f]
    _tf_best = max(_tf_chain,
                   key=lambda f: len(_tf_names.field_name(f) or ""))
    _tf_tf[_tf_best] = _rl.FIELD_STATUS_OFFERABLE
    _tf_picked.append(_tf_best)
_tf_ta = [0] * player_mod.TECH_APPLICATIONS_COUNT
for _tf_f in _tf_picked:
    for _tf_a in _tf_slots.get(_tf_f, ()):
        _tf_ta[_tf_a] = _rl.APP_STATUS_AVAILABLE
_tf_entries = _rl.reconstruct(_tf_tf, _tf_ta, select_mode=False)
assert all(_e.offered for _e in _tf_entries), \
    [(_e.index, _e.field) for _e in _tf_entries]
assert all(_tf_names.field_name(_e.field) for _e in _tf_entries)


class _TfLong:
    """The stand-in's names, made as long as this screen can meet.

    The committed stand-in is clone-safe and its names are short, so on
    their own they measure the case that was never in doubt. The real
    tables are the player's and a check may not read them (the
    fundament, "A CHECK THAT READS THE PLAYER'S OWN FILES PASSES ON THE
    MACHINE THAT WROTE THEM"). So the worst case is MADE: a name longer
    than any technology has, which is what the shrink rule
    (`researchpanel._fit`, the DEVIATION `research_select` marks) has
    to keep inside the box. Both passes run.
    """

    state = "ok"

    def __init__(self, inner):
        self.inner = inner

    def field_name(self, field):
        got = self.inner.field_name(field)
        return f"{got} Hyper-Advanced Xenometallurgy" if got else got

    def application_name(self, app, hyper_count=None):
        got = self.inner.application_name(app, hyper_count)
        return f"{got} Phase-Shifted Displacement Array" if got else got


_tf_words = {"placeholder": None, "cost": lambda e: "8888 RP"}


def _tf_render(lay, entries, hover=None, text=True, names=None):
    """The panel at one size, with the text or without it.

    The DIFFERENCE of the two is exactly what the text drew — which is
    a measurement of the drawing rather than a second computation of
    where the drawing should have gone (decision 5's "a tool is a
    reader too").
    """
    _s = pygame.Surface((lay.window_w, lay.window_h))
    _s.fill((0, 0, 0))
    _tf_panel.draw(_s, lay, _dx_scr.style, entries, hover,
                   _tf_words if text else {},
                   (names or _tf_names) if text else None,
                   _dx_scr._wording if text else None)
    return _s


_tf_seen = 0
for _tf_w, _tf_h in ((1920, 1080), (2560, 1440), (3440, 1440),
                     (3840, 2160)):
  for _tf_src in (_tf_names, _TfLong(_tf_names)):
    _tf_lay = Layout(_tf_w, _tf_h)
    _tf_with = _tf_render(_tf_lay, _tf_entries, names=_tf_src)
    _tf_without = _tf_render(_tf_lay, _tf_entries, text=False)
    # Every entry's own inner rect: the drawn box, pulled in by the
    # margin the box was grown by.
    _tf_inner, _tf_header = [], []
    for _tf_e in _tf_entries:
        _bx, _by, _bw, _bh = _dx_geo.window_rect(
            _tf_e.panel_box(_tf_panel.BOX_MARGIN), _tf_lay)
        _tf_m = max(1, int(_tf_panel.BOX_MARGIN * _tf_lay.scale * 0.5))
        _tf_inner.append(pygame.Rect(_bx + _tf_m, _by + _tf_m,
                                     _bw - 2 * _tf_m, _bh - 2 * _tf_m))
        # The category label and the cost are drawn ABOVE the box, on
        # the strip the original paints its header plate into. They are
        # not in a box HD draws, so the rule for them is that they stay
        # OFF the box: above its top edge.
        _tf_header.append(pygame.Rect(_bx - 4 * _tf_m, 0,
                                      _bw + 8 * _tf_m, _by))
    _tf_ink = _tf_out = 0
    for _tf_y in range(0, _tf_h, 2):
        for _tf_x in range(0, _tf_w, 2):
            if _tf_with.get_at((_tf_x, _tf_y))[:3] == \
                    _tf_without.get_at((_tf_x, _tf_y))[:3]:
                continue
            _tf_ink += 1
            if not any(_r.collidepoint(_tf_x, _tf_y)
                       for _r in _tf_inner + _tf_header):
                _tf_out += 1
    assert _tf_ink > 200, (_tf_w, _tf_h, _tf_ink)
    assert _tf_out == 0, (
        f"{_tf_w}x{_tf_h}, {'long' if _tf_src is not _tf_names else 'real'}"
        f" names: {_tf_out} of {_tf_ink} text pixels lie outside every "
        f"box's inner rect and every header strip — a name is on its "
        f"box's edge or over it")
    _tf_seen += 1
assert _tf_seen == 8, _tf_seen
ok("every name and row label lies inside its own box with the margin, "
   "at four resolutions, with the longest real names")

# ── THE HOVER BAND COVERS ITS ROW AND STAYS INSIDE ──
#
# Data's fourth point: on the live panel the band ran past the right
# edge of its box and did not line up with it. It is the ROW rectangle,
# which is transcribed and 3 px wider than the game's own block field —
# so what had to move was the BOX, and this is what says it did.
_tf_lay = Layout(1920, 1080)
_tf_band_seen = 0
for _tf_e in _tf_entries:
    _bx, _by, _bw, _bh = _dx_geo.window_rect(
        _tf_e.panel_box(_tf_panel.BOX_MARGIN), _tf_lay)
    _tf_box = pygame.Rect(_bx, _by, _bw, _bh)
    for _tf_row in range(len(_tf_e.apps)):
        _rx, _ry, _rw, _rh = _dx_geo.window_rect(
            _tf_e.row_rect(_tf_row), _tf_lay)
        _tf_band = pygame.Rect(_rx, _ry, _rw, _rh)
        assert _tf_box.contains(_tf_band), (
            f"entry {_tf_e.index} row {_tf_row}: the band {_tf_band} "
            f"is not inside its box {_tf_box}")
        # …and it is INSIDE by the margin, not merely touching.
        assert _tf_band.left - _tf_box.left >= 2, (_tf_e.index, _tf_row)
        assert _tf_box.right - _tf_band.right >= 2, (_tf_e.index, _tf_row)
        _tf_band_seen += 1
assert _tf_band_seen >= 8, _tf_band_seen
# AND IT IS DRAWN THERE: the hovered row's fill must appear inside the
# band and nowhere else in the box.
_tf_e0 = _tf_entries[0]
_tf_hov = _tf_render(_tf_lay, _tf_entries, hover=(_tf_e0.index, 0))
_tf_flat = _tf_render(_tf_lay, _tf_entries)
_rx, _ry, _rw, _rh = _dx_geo.window_rect(_tf_e0.row_rect(0), _tf_lay)
_tf_band = pygame.Rect(_rx, _ry, _rw, _rh)
_tf_moved = _tf_spill = 0
for _tf_y in range(0, 1080, 2):
    for _tf_x in range(0, 1920, 2):
        if _tf_hov.get_at((_tf_x, _tf_y))[:3] == \
                _tf_flat.get_at((_tf_x, _tf_y))[:3]:
            continue
        _tf_moved += 1
        if not _tf_band.collidepoint(_tf_x, _tf_y):
            _tf_spill += 1
assert _tf_moved > 100, _tf_moved
assert _tf_spill == 0, (
    f"{_tf_spill} of {_tf_moved} pixels the hover changed lie outside "
    f"the row it is for")
# ── CANCEL, AND THE DESCRIPTION BOX ──
#
# The order lists every string on these screens, and two of them are
# not on the panel: the exit button's label and the description box's
# text.
_tf_exit = (269, 452, 360, 470)          # what the wire reports
_tf_btn = pygame.Surface((1920, 1080))
_tf_btn.fill((255, 0, 255))
_tf_rect = _tf_panel.draw_exit(_tf_btn, _tf_lay, _dx_scr.style,
                               _tf_exit, "CANCEL")
_tf_bare = pygame.Surface((1920, 1080))
_tf_bare.fill((255, 0, 255))
_tf_panel.draw_exit(_tf_bare, _tf_lay, _dx_scr.style, _tf_exit, None)
_tf_label_out = _tf_label_ink = 0
_tf_pad = max(2, int(_tf_rect.height * 0.12))
_tf_inner_btn = _tf_rect.inflate(-2 * _tf_pad, -2 * _tf_pad)
for _tf_y in range(0, 1080):
    for _tf_x in range(0, 1920):
        if _tf_btn.get_at((_tf_x, _tf_y))[:3] == \
                _tf_bare.get_at((_tf_x, _tf_y))[:3]:
            continue
        _tf_label_ink += 1
        if not _tf_inner_btn.collidepoint(_tf_x, _tf_y):
            _tf_label_out += 1
assert _tf_label_ink > 50, _tf_label_ink
assert _tf_label_out == 0, (
    f"{_tf_label_out} of {_tf_label_ink} pixels of CANCEL lie outside "
    f"the button the wire reported, less its own padding")

# The description box is the shared help panel, which wraps and scrolls
# — its marked HD EXTENSION. What this asserts is that it keeps to its
# box: open the longest description this fixture can make and require
# every pixel it draws to be inside the popup's own rect.
_dx_scr.app.helptext = HelpText(_DxRes(), "en")
_dx_scr.help.close()
_dx_scr.help.open(25, "A Very Long Technology Name Indeed",
                  ("Ion Drive " * 60) + "\rResearch cost: 900 RP")
_tf_pop_box = _dx_scr.box_rect(_dx_scr.HELP_BOX) or _HelpFallbackBox
_tf_pop_rect = pygame.Rect(*_dx_scr.layout.rect(_tf_pop_box))
_tf_pop = pygame.Surface((1920, 1080))
_tf_pop.fill((255, 0, 255))
_dx_scr.render_help(_tf_pop)
_tf_pop_ink = _tf_pop_out = 0
for _tf_y in range(0, 1080, 2):
    for _tf_x in range(0, 1920, 2):
        if _tf_pop.get_at((_tf_x, _tf_y))[:3] == (255, 0, 255):
            continue
        _tf_pop_ink += 1
        if not _tf_pop_rect.collidepoint(_tf_x, _tf_y):
            _tf_pop_out += 1
assert _tf_pop_ink > 200, _tf_pop_ink
assert _tf_pop_out == 0, (
    f"{_tf_pop_out} of {_tf_pop_ink} pixels of the description box lie "
    f"outside its own panel")
_dx_scr.help.close()
ok("the hover band covers its row and stays inside the box, the header "
   "words stay above it, and CANCEL and the description keep to theirs")
