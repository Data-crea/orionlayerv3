# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 080c_core_the_research_description_box_is.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (96 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# This one did NOT stand inside main(): it is work order 165 part C,
# the description box, which is one behaviour of BOTH research modes
# and therefore lives in core/researchscreen.py and in this group.
#
# The 2 check(s) it holds:
#   - the research description box opens over a row and nowhere else,
#     with the game's own record and the FULL cost in both modes
#   - the research panel draws under its own help popup, not over it

# ── THE DESCRIPTION BOX (tech.cpp:323-337) ──
#
# A right click that reaches the field system comes back NEGATIVE, and
# `_Tech_Select_` negates it and hands it to `Set_Selected_Entry_`,
# which matches `app_click_field_ids` and nothing else
# (tech.cpp:468-487). So the ROWS answer a right click; an entry block,
# the whole-screen field and the panel's empty space answer nothing.
# And `app_id != 0` guards the call (:337), which is the placeholder
# row — a row that can be committed and has no application to describe.
from core import billtext as _dx_bt, research as _dx_res
from core import researchnative as _dx_geo
from core import researchscreen as _dx_core, technames as _dx_tn
from core.screen_base import ScreenBase as _DxScreenBase
from core.helptext import HelpText


class _DxRes:
    """A resolver that reads the COMMITTED stand-ins first.

    The clone-only fault, again: a check that reads whatever this
    machine has extracted passes here and can fail in a clone. This is
    `083`'s resolver, written out rather than reached for, because that
    module runs after this one and a name is not a dependency worth
    creating between two check files.
    """

    skin = "default"

    def load_json(self, rel, default=None):
        for _base in (DERIVED_ROOT, os.path.dirname(SCREENS_DIR)):
            _p = os.path.join(_base, *rel.split("/"))
            if os.path.exists(_p):
                return __import__("json").load(io.open(_p,
                                                       encoding="utf-8"))
        return default


def _dx_record(tech_fields, tech_apps, accumulated=0, field=0, app=0):
    """A raw `s_player` saying exactly this."""
    _raw = bytearray(player_mod.SPEC.size)
    _off = next(_o for _n, _o, _k in player_mod.SPEC.fields
                if _n == "tech_fields")
    _raw[_off:_off + len(tech_fields)] = bytes(tech_fields)
    _ao = player_mod.TECH_APPLICATIONS_OFFSET
    _raw[_ao:_ao + len(tech_apps)] = bytes(tech_apps)
    _widths = {"i8": 1, "u8": 1, "i16": 2, "u16": 2, "i32": 4,
               "u32": 4}
    for _n, _v in (("research_accumulated", accumulated),
                   ("current_research_field", field),
                   ("current_research_application", app)):
        _o, _k = next((_oo, _kk) for _nn, _oo, _kk in player_mod.SPEC.fields
                      if _nn == _n)
        _w = _widths[_k]
        _raw[_o:_o + _w] = int(_v).to_bytes(_w, "little", signed=False)
    return bytes(_raw)


#: Enough of a game to offer two categories, in CHANGE mode — the mode
#: whose entry cost has an offset, which is what makes "the description
#: shows the FULL cost" a claim with a control.
_DX_ACCUMULATED = 20
_dx_tf = [0] * _rl_res.FIELD_COUNT
for _dx_g in (4, 7):
    _dx_tf[_rl.FIRST_FIELD_IN_GROUP[_dx_g]] = _rl.FIELD_STATUS_OFFERABLE
_dx_ta = [_rl.APP_STATUS_AVAILABLE] * player_mod.TECH_APPLICATIONS_COUNT
_dx_entries = _rl.reconstruct(_dx_tf, _dx_ta, select_mode=False)
_dx_fields = _rl_list(_dx_entries, select_mode=False)
_dx_state = _RsGameState()
_dx_state.current_screen = 36
_dx_state.fields = _dx_fields
_dx_state.player_raw = [_dx_record(_dx_tf, _dx_ta, _DX_ACCUMULATED)]
_dx_state.player_num = 0

_dx_scr = _rs_d.screens["research_change"]
_dx_scr.enter(_dx_state)
# THE STAND-INS, after `enter`, because `enter` builds both loaders
# from the real tree. `derived()` is the one way a check gets a
# derived catalogue; `HelpText` takes a Resources and is on that
# rule's allow-list, so it gets the resolver above instead.
_dx_scr._names = derived(_dx_tn.TechNames)
_dx_scr._wording = derived(_dx_bt.BillText)
_rs_app.helptext = HelpText(_DxRes(), "en")
assert _rs_app.helptext.available, (
    "the help stand-in did not load — run "
    "`python tools/make_derived_fixtures.py`")
_dx_scr.update(_dx_state)
assert _dx_scr.state == _dx_core.READY, (_dx_scr.state, _dx_scr.problems)

_dx_offered = [_e for _e in _dx_scr._entries if _e.offered]
assert _dx_offered, "the fixture offers nothing to right-click"
_dx_entry = _dx_offered[0]
_dx_x, _dx_y, _dx_w, _dx_h = _dx_geo.window_rect(_dx_entry.row_rect(0),
                                              _dx_scr.layout)
_dx_cx, _dx_cy = _dx_x + _dx_w // 2, _dx_y + _dx_h // 2
assert _dx_scr.row_at(_dx_cx, _dx_cy) == (_dx_entry.index, 0)

# 1. OVER A ROW: the description opens, keyed by the APPLICATION id,
#    and it carries the record's own title.
_dx_scr.help.close()
assert _dx_scr.handle_right_button(True, _dx_cx, _dx_cy) is True
assert _dx_scr.help.visible
assert _dx_scr.help.help_id == _dx_entry.apps[0], (
    _dx_scr.help.help_id, _dx_entry.apps[0])

# 2. THE COST IS THE FULL ONE, and the entry beside it is not. The
#    entry subtracts `research_accumulated` in change mode
#    (tech.cpp:203); `New_Get_Tech_Cost_` subtracts nothing (:802).
#    The original's design — doc/tech_change_reading.md §3 — so the
#    two numbers have to DIFFER here or this check is measuring one
#    number twice.
_dx_full = _dx_res.cost(_dx_entry.field)
assert _dx_scr.cost_offset() == _DX_ACCUMULATED, _dx_scr.cost_offset()
assert _dx_full > _DX_ACCUMULATED > 0, (_dx_full, _DX_ACCUMULATED)
_dx_body = " ".join(_l.plain() for _l in _dx_scr.help._lines)
_dx_label = _dx_scr._wording.message(_dx_bt.MSG_RESEARCH_COST)
assert f"{_dx_label}{_dx_full}" in _dx_body, (_dx_label, _dx_full,
                                              _dx_body[-120:])
assert _dx_scr.cost_text(_dx_entry) == \
    f"{_dx_full - _DX_ACCUMULATED}{_dx_scr._cost_suffix}", \
    _dx_scr.cost_text(_dx_entry)
assert f"{_dx_full - _DX_ACCUMULATED}{_dx_scr._cost_suffix}" \
    not in _dx_body, (
        "the description is showing the REMAINING cost; the original "
        "shows the full one there and the remaining one on the entry")

# 3. AND NOWHERE ELSE. A point inside the panel that is not a row
#    opens nothing — `Set_Selected_Entry_` matches row fields only.
#    Two points, so a single lucky gap is not the whole claim: just
#    above the first row, and the panel's own top-left corner.
_dx_scr.help.close()
for _dx_px, _dx_py in ((_dx_cx, _dx_y - 4),
                       _dx_geo.window_point((_dx_scr.geom.origin + 6, 8),
                                         _dx_scr.layout)):
    if _dx_scr.row_at(_dx_px, _dx_py) is not None:
        continue                      # a row after all; not this claim
    assert _dx_scr.open_description_at(_dx_px, _dx_py) is False, \
        (_dx_px, _dx_py)
    assert not _dx_scr.help.visible

# 4. THE PLACEHOLDER ROW has app id 0 and describes nothing (:337).
_dx_ph_tf = [0] * _rl_res.FIELD_COUNT
_dx_ph_tf[_rl.FIRST_FIELD_IN_GROUP[4]] = _rl.FIELD_STATUS_OFFERABLE
_dx_ph = _rl.reconstruct(_dx_ph_tf,
                         [0] * player_mod.TECH_APPLICATIONS_COUNT,
                         select_mode=False)
_dx_ph_entry = next(_e for _e in _dx_ph if _e.offered)
assert _dx_ph_entry.placeholder and _dx_ph_entry.apps == (0,), \
    (_dx_ph_entry.placeholder, _dx_ph_entry.apps)
_dx_scr._entries = _dx_ph
_dx_ph_x, _dx_ph_y, _dx_ph_w, _dx_ph_h = _dx_geo.window_rect(
    _dx_ph_entry.row_rect(0), _dx_scr.layout)
assert _dx_scr.open_description_at(_dx_ph_x + _dx_ph_w // 2,
                                   _dx_ph_y + _dx_ph_h // 2) is False
assert not _dx_scr.help.visible
_dx_scr._entries = _dx_entries
ok("the research description box opens over a row and nowhere else, "
   "with the game's own record and the FULL cost in both modes")

# ── THE POPUP IS DRAWN LAST, AND IT WAS NOT ──
#
# `ScreenBase.render` ends with `render_help`; these two screens drew
# their entries AFTER calling it, so a popup opened on them was painted
# and then covered by the panel's own text. Found while building the
# description box, which is that same popup. The fix is the
# `render_content` hook, and this is the proof it works: render once
# without the popup, once with it, and require that pixels THE PANEL
# ITSELF DREW inside the popup have changed. If the panel were still
# last, every one of them would be identical.
assert _dx_core.ResearchPanelScreen.render is _DxScreenBase.render, (
    "the research screens override render() again — the panel has to "
    "go in render_content or it is drawn over the help popup")
assert _dx_core.ResearchPanelScreen.render_content is not \
    _DxScreenBase.render_content

_dx_scr.update(_dx_state)


def _dx_render(with_panel, with_popup):
    """One frame, with or without the panel and with or without the popup."""
    _dx_scr.help.close()
    if with_popup:
        _dx_scr.help.open(255, "Change Current Research", "Help 255 body")
    _kept = _dx_scr._entries
    if not with_panel:
        _dx_scr._entries = []
    _surf = pygame.Surface((1920, 1080))
    _surf.fill((0, 0, 0))
    _dx_scr.render(_surf)
    _dx_scr._entries = _kept
    _dx_scr.help.close()
    return _surf


# THREE FRAMES, because two are not enough to tell the orders apart.
# The panel's text is blitted with alpha, so it looks DIFFERENT over
# the popup's fill than over black whichever order they go in — a test
# that only asked "did these pixels change" passed with the order
# swapped, and was replaced by this one.
#
#   A  the panel alone      C  the popup alone      B  both
#
# Where A and C both drew, B has to be C. If the panel went last, B
# would be the panel blended over the popup and would not be.
# A FOURTH frame is the baseline: the background and the boxes are
# drawn in every one of them, so "non-black" would select the whole
# window. What each of the two DREW is what it changed against this.
_dx_base = _dx_render(False, False)
_dx_a = _dx_render(True, False)
_dx_c = _dx_render(False, True)
_dx_b = _dx_render(True, True)
# The popup's own footprint first, so the pixel-by-pixel pass below
# runs over a panel-sized box and not over two million pixels: the
# panel's TEXT is sparse, and a coarse grid over the whole window
# finds too few overlapping pixels to be a claim.
_dx_box = None
for _dx_sy in range(0, 1080, 3):
    for _dx_sx in range(0, 1920, 3):
        if _dx_c.get_at((_dx_sx, _dx_sy))[:3] == \
                _dx_base.get_at((_dx_sx, _dx_sy))[:3]:
            continue
        _dx_box = ((_dx_sx, _dx_sy, _dx_sx, _dx_sy) if _dx_box is None
                   else (min(_dx_box[0], _dx_sx), min(_dx_box[1], _dx_sy),
                         max(_dx_box[2], _dx_sx), max(_dx_box[3], _dx_sy)))
assert _dx_box is not None, "the help popup drew nothing at all"
# THE POPUP'S OPAQUE BODY, NOT ITS GLOW (work order 169, decision 71):
# the HUD popup block's outer glow is translucent by design and blends
# with whatever is under it, panel included, so the footprint is shrunk
# by the glow's pad (`core.hud.raster.shape`: ceil(2.2 x glow) + 2) and
# three px of sampling grid. What is claimed — the popup is drawn LAST —
# is about the body, and the body is opaque.
from core.hud import style as _dx_hs
_dx_pad = int(math.ceil(_dx_hs.get().get("panel.glow_width")
                        * app.layout.scale * 2.2)) + 2 + 3
_dx_box = (_dx_box[0] + _dx_pad, _dx_box[1] + _dx_pad,
           _dx_box[2] - _dx_pad, _dx_box[3] - _dx_pad)
_dx_both = _dx_wrong = 0
for _dx_sy in range(_dx_box[1], _dx_box[3] + 1):
    for _dx_sx in range(_dx_box[0], _dx_box[2] + 1):
        _dx_p0 = _dx_base.get_at((_dx_sx, _dx_sy))[:3]
        _dx_pa = _dx_a.get_at((_dx_sx, _dx_sy))[:3]
        _dx_pc = _dx_c.get_at((_dx_sx, _dx_sy))[:3]
        if _dx_pa == _dx_p0 or _dx_pc == _dx_p0:
            continue
        _dx_both += 1
        if _dx_b.get_at((_dx_sx, _dx_sy))[:3] != _dx_pc:
            _dx_wrong += 1
assert _dx_both > 50, (
    f"only {_dx_both} sampled pixels have both the panel and the popup "
    f"on them — this fixture cannot tell the two orders apart")
assert _dx_wrong == 0, (
    f"{_dx_wrong} of {_dx_both} pixels where the panel and the popup "
    f"overlap are not the popup's — it is being painted UNDER the "
    f"panel again")
ok("the research panel draws under its own help popup, not over it")
