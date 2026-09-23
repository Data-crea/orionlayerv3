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
# The 4 check(s) it holds:
#   - every name and row label lies inside its own box with the
#     margin, at four resolutions, with the longest real names
#   - the hover band covers its row and stays inside the box, and the
#     header words stay above it
#   - no hover band cuts the field heading, on the panel or in the
#     list popup (Data's Nachtrag to 166, rule 1)
#   - the boxes and the button keep their distance from each other
#     (Data's Nachtrag to 166, rules 2 and 3)
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
# edge of its box and did not line up with it. Its x span is the ROW
# rectangle's, which is transcribed and 3 px wider than the game's own
# block field — so what had to move was the BOX, and this is what says
# it did.
#
# `band_rect`, NOT `row_rect`: since the Nachtrag to 166 the drawn band
# and the click area are two rectangles, and this measures the one that
# is drawn. Check 3 below holds the other half — that the click area is
# still the transcribed one and the band stays off the field heading.
_tf_lay = Layout(1920, 1080)
_tf_band_seen = 0
for _tf_e in _tf_entries:
    _bx, _by, _bw, _bh = _dx_geo.window_rect(
        _tf_e.panel_box(_tf_panel.BOX_MARGIN), _tf_lay)
    _tf_box = pygame.Rect(_bx, _by, _bw, _bh)
    for _tf_row in range(len(_tf_e.apps)):
        _rx, _ry, _rw, _rh = _dx_geo.window_rect(
            _tf_e.band_rect(_tf_row), _tf_lay)
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
_rx, _ry, _rw, _rh = _dx_geo.window_rect(_tf_e0.band_rect(0), _tf_lay)
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

# ── 3. NO HOVER BAND CUTS THE FIELD HEADING ──
#
# Data's Nachtrag to 166, rule 1, and its reading instruction: look up
# what the ORIGINAL marks there first. `Draw_Little_Arrow_`
# (tech.cpp:740-775) draws its arrowhead at `app_label_y[i] + 5`, in
# `label_x - 9 .. label_x - 2`, and its stem rises only to
# `app_label_y[0] - 3` — three pixels above the FIRST application's
# label, nineteen below the field's own name. The original's mark never
# touches the heading, so neither may HD's band.
#
# The CLICK area is a different rectangle and stays transcribed: row 0
# runs from `y1[0]` = 0, i.e. it takes in the field-name line, because
# `Add_Fields_To_List_Page_` (list.cpp:94-116) puts the field there and
# the original accepts a click on it.
#
# This is a MEASUREMENT, not a second computation of the geometry: the
# headings are rendered alone — a names stand-in whose application names
# are empty — against a render with no names at all, and the difference
# is exactly the ink of the eight field names. No band may contain one
# of those pixels.


class _TfHeads:
    """Field names only: the application names come back empty."""

    state = "ok"

    def __init__(self, inner):
        self.inner = inner

    def field_name(self, field):
        return self.inner.field_name(field)

    def application_name(self, app, hyper_count=None):
        return ""


class _TfMute(_TfHeads):
    """Neither. The difference to `_TfHeads` is the headings' ink."""

    def field_name(self, field):
        return ""


def _tf_ink_points(a, b, step=1):
    """Every point where the two surfaces differ, as a set."""
    out = set()
    for y in range(0, a.get_height(), step):
        for x in range(0, a.get_width(), step):
            if a.get_at((x, y))[:3] != b.get_at((x, y))[:3]:
                out.add((x, y))
    return out


_tf_lay = Layout(1920, 1080)
_tf_heads = _tf_render(_tf_lay, _tf_entries, names=_TfHeads(_tf_names))
_tf_mute = _tf_render(_tf_lay, _tf_entries, names=_TfMute(_tf_names))
_tf_head_ink = _tf_ink_points(_tf_heads, _tf_mute)
assert len(_tf_head_ink) > 400, len(_tf_head_ink)
_tf_cut = 0
for _tf_e in _tf_entries:
    for _tf_row in range(len(_tf_e.apps)):
        _rx, _ry, _rw, _rh = _dx_geo.window_rect(
            _tf_e.band_rect(_tf_row), _tf_lay)
        _tf_band = pygame.Rect(_rx, _ry, _rw, _rh)
        _tf_cut += sum(1 for _p in _tf_head_ink if _tf_band.collidepoint(_p))
assert _tf_cut == 0, (
    f"{_tf_cut} of {len(_tf_head_ink)} pixels of the field headings lie "
    f"inside a hover band — the band is on the heading, and "
    f"Draw_Little_Arrow_ puts the original's mark on the application's "
    f"label line (tech.cpp:740-775)")
# …AND THE CLICK AREA IS STILL THE TRANSCRIBED ONE. The band may not be
# bought by narrowing what the player can hit: row 0 stays 34 px tall.
for _tf_e in _tf_entries:
    _tf_r0 = _tf_e.row_rect(0)
    assert _tf_r0[3] - _tf_r0[1] == _rl.ROW_Y2[0] - _rl.ROW_Y1[0] == 33, \
        _tf_r0
    assert _tf_r0[1] == _tf_e.y + _rl.ROW_Y_BASE, _tf_r0
    _tf_b0 = _tf_e.band_rect(0)
    assert _tf_b0[1] > _tf_r0[1], (_tf_b0, _tf_r0)
    assert _tf_b0[3] == _tf_r0[3], (_tf_b0, _tf_r0)
# Every band is the SAME height, which is what "bei allen Zeilen gleich
# hoch" asks for, and it is the height rows 1..3 already had.
_tf_hs = {_tf_e.band_rect(_r)[3] - _tf_e.band_rect(_r)[1]
          for _tf_e in _tf_entries for _r in range(len(_tf_e.apps))}
assert _tf_hs == {_rl.BAND_H - 1}, _tf_hs
assert _rl.BAND_H == _rl.ROW_Y2[1] - _rl.ROW_Y1[1] + 1 == 15, _rl.BAND_H

# THE SAME IN THE LIST POPUP, measured the same way. Its rows come from
# the same table (list.cpp:94-116) and its field name is printed at the
# item's own y, so it had the same fault and takes the same split.
_tf_lpop = _tl.TechListPopup()
_tf_lpop.open(type("E", (), {"index": 0, "group": 4})(), _tl_items)
_tf_lorigin = _dx_geo.Geometry("change").origin


def _tf_popup_render(names):
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _tl.draw(_s, _tf_lay, _dx_scr.style, _tf_lpop, _tf_lorigin, names, None)
    return _s


_tf_lheads = _tf_ink_points(_tf_popup_render(_TfHeads(_tf_names)),
                            _tf_popup_render(_TfMute(_tf_names)))
assert len(_tf_lheads) > 400, len(_tf_lheads)
_tf_lx = _tf_lpop.list_x(_tf_lorigin)
_tf_lcut = _tf_lrows = 0
for _tf_item in _tf_lpop.items():
    for _tf_row in range(len(_tf_item.apps)):
        _rx, _ry, _rw, _rh = _dx_geo.window_rect(
            _tf_item.band_rect(_tf_row, _tf_lx), _tf_lay)
        _tf_lband = pygame.Rect(_rx, _ry, _rw, _rh)
        _tf_lcut += sum(1 for _p in _tf_lheads
                        if _tf_lband.collidepoint(_p))
        # The click area stays the transcribed row here too.
        assert _tf_item.row_rect(_tf_row, _tf_lx)[3] == \
            _tf_item.band_rect(_tf_row, _tf_lx)[3]
        _tf_lrows += 1
assert _tf_lrows >= 4, _tf_lrows
assert _tf_lcut == 0, (
    f"list popup: {_tf_lcut} of {len(_tf_lheads)} pixels of the field "
    f"headings lie inside a hover band")
_tf_lpop.close()
ok("no hover band cuts the field heading, on the panel or in the list "
   "popup, and the click area stays the transcribed row")

# ── 4. THE BOXES AND THE BUTTON KEEP THEIR DISTANCE ──
#
# Data's Nachtrag to 166, rules 2 and 3: the left and right columns may
# not touch, there has to be a VISIBLE gap, and CANCEL may not touch the
# bottom row of boxes. Asserted as ONE rule over every pair rather than
# as the two instances, because the pair rule is what a later margin
# change runs into.
#
# 3 native pixels is the floor: at 1920x1080 the scale is 3, so it is
# 9 window pixels, and the smallest window this screen supports still
# draws it. `BOX_MARGIN = 4` leaves 1 and fails here, which is the
# Nachtrag's own case.
_TF_CLEAR = 3
_tf_pairs = 0
for _tf_sel in (True, False):
    _tf_boxes = [(_e.index, _e.panel_box(_tf_panel.BOX_MARGIN))
                 for _e in _rl.reconstruct(_tf_tf, _tf_ta,
                                           select_mode=_tf_sel)]
    _tf_things = list(_tf_boxes)
    if not _tf_sel:
        # CANCEL sits where the GEOMETRY puts it, and the geometry's
        # origin is the source's (`s + 189, 452`, tech.cpp:198-200).
        # Taking it from there rather than from the literal above is
        # what makes this rule notice a moved button and not only a
        # moved box; the SIZE stays the wire's, because
        # `Add_Button_Field_` reads it off the art (fields.cpp:366-367).
        _tf_ox, _tf_oy = _dx_geo.Geometry("change").exit_button_origin
        assert (_tf_ox, _tf_oy) == _tf_exit[:2], (_tf_ox, _tf_oy, _tf_exit)
        _tf_things.append(("CANCEL", (_tf_ox, _tf_oy,
                                      _tf_ox + _tf_exit[2] - _tf_exit[0],
                                      _tf_oy + _tf_exit[3] - _tf_exit[1])))
    for _tf_i, (_tf_an, _tf_a) in enumerate(_tf_things):
        for _tf_bn, _tf_b in _tf_things[_tf_i + 1:]:
            _tf_gap = max(_tf_b[0] - _tf_a[2], _tf_a[0] - _tf_b[2],
                          _tf_b[1] - _tf_a[3], _tf_a[1] - _tf_b[3])
            assert _tf_gap >= _TF_CLEAR, (
                f"{'select' if _tf_sel else 'change'} mode: {_tf_an} "
                f"{_tf_a} and {_tf_bn} {_tf_b} are {_tf_gap} native px "
                f"apart — under {_TF_CLEAR} that is not a visible gap, "
                f"and at 0 or less they touch")
            _tf_pairs += 1
assert _tf_pairs == 2 * 28 + 8, _tf_pairs
# The gap is bought out of the MARGIN and NOT by moving a box off its
# rows: every box still sits on its own four row rectangles, and all
# eight are the same size — a box nudged sideways to make room would
# pass the pair rule above and put its text over the edge, which is
# check 1's business. This is what ties the two together.
_tf_sizes = set()
for _tf_e in _tf_entries:
    _tf_box = _tf_e.panel_box(_tf_panel.BOX_MARGIN)
    _tf_sizes.add((_tf_box[2] - _tf_box[0], _tf_box[3] - _tf_box[1]))
    _tf_rows = [_tf_e.row_rect(_r) for _r in range(len(_tf_e.apps))]
    assert _tf_rows, _tf_e.index
    assert _tf_box[0] == min(_r[0] for _r in _tf_rows) - _tf_panel.BOX_MARGIN
    assert _tf_box[2] == max(_r[2] for _r in _tf_rows) + _tf_panel.BOX_MARGIN
    assert _tf_box[1] == min(_r[1] for _r in _tf_rows) - _tf_panel.BOX_MARGIN
    # The BOTTOM is the four-row block's, not the last row's: an entry
    # that offers two applications wears the same box as one that offers
    # four, because `Init_Entry_Data_` gives every category the same
    # block field whatever it has to show (tech.cpp:225-231).
    assert _tf_box[3] >= max(_r[3] for _r in _tf_rows) + _tf_panel.BOX_MARGIN
assert len(_tf_sizes) == 1, _tf_sizes
ok("the boxes and the button keep their distance: no two of the eight "
   "and no box and CANCEL come within 3 native px, in both modes")
