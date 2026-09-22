# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 082_fleets_the_fleets_ship_panel_is_sized.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - the Fleets ship panel is sized by its box: ship_panel_text in both resolution sets, inside its h
#   - the Fleets ship panel is laid out as the original lays it out: six tab stops re-derived from the


# ── THE SHIP PANEL'S WORDS COME OUT OF boxes.json ──────────────
#
# Work order 151 B. The panel used to size itself from
# `int(content_rect.height * 0.055)` with a floor of 10 px — a
# constant in the renderer, and a floor that fired at 1080p and
# nowhere else, so the text was 22 % larger against its window
# there than at 1440p. It also wrapped nothing and stopped
# mid-list when it ran out of room. All three are what this holds.
from screens.fleets import fltpanel as _fp
from core import textfit as _tf
import importlib.util as _fp_u
_fp_spec = _fp_u.spec_from_file_location(
    "_panel_preview", os.path.join(os.path.dirname(SCREENS_DIR),
                                   "tools", "colony_list_preview.py"))
_prev = _fp_u.module_from_spec(_fp_spec)
_fp_spec.loader.exec_module(_prev)

_fp_BOX = _fp.PANEL_TEXT_BOX
_fp_short = [("", "I.S.S. Vengeance"), ("Location", "Sol"),
             ("Shields", "Class III Shield")]
_fp_huge = _fp_short + [("", f"{_n} Phasor Cannon (Forward)")
                        for _n in range(8, 0, -1)] \
    + [("", f"Special Device Number {_i}") for _i in range(1, 40)]

# 1. THE BOX IS THERE, IN EVERY RESOLUTION SET, AND IS NOT A
#    CUTOUT. A cutout is locked in the F5 editor and its rect is
#    the artwork's; this one has to be free, or none of the rest
#    of this is editable.
_fp_boxfile = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "boxes.json"), encoding="utf-8"))
for _fp_res, _fp_list in _fp_boxfile.items():
    _fp_b = next((b for b in _fp_list if b["name"] == _fp_BOX), None)
    assert _fp_b is not None, (
        f"{_fp_res}: no {_fp_BOX} box — the ship panel's words "
        f"would fall back to a renderer constant")
    assert "rect" in _fp_b, f"{_fp_res}: {_fp_BOX} carries no rect"
    _fp_st = _fp_b.get("style") or {}
    assert "font_size" in _fp_st, (
        f"{_fp_res}: {_fp_BOX} has no font_size; the size would come "
        f"from fltpanel.PANEL_FALLBACK_FONT, which is a fallback and "
        f"not a layout (decision 14)")
    assert _fp_BOX not in _fhB.RULE_NAMES["fleets"], (
        f"{_fp_BOX} became a cutout name; the editor locks cutouts "
        f"and the point of this box is that F5 can move it")
# and it sits inside the hole it belongs to, at both resolutions
for _fp_res, _fp_list in _fp_boxfile.items():
    _fp_by = {b["name"]: b["rect"] for b in _fp_list if "rect" in b}
    _px, _py, _pw, _ph = _fp_by["ship_panel"]
    _tx, _ty, _tw, _th = _fp_by[_fp_BOX]
    assert (_tx >= _px and _ty >= _py and _tx + _tw <= _px + _pw
            and _ty + _th <= _py + _ph), (
        f"{_fp_res}: {_fp_BOX} {_fp_by[_fp_BOX]} leaves ship_panel "
        f"{_fp_by['ship_panel']} — the words would be drawn on the "
        f"frame, which covers them because it renders last")

# 2. THE SIZE IS THE BOX'S, AND SCALED EXACTLY ONCE.
#    `font_size * font_scale`, through `Layout.font_size` and no
#    second window factor. The fault this replaces is in the
#    fundament under "Scaling twice looks correct at the resolution
#    you tested" and in `ScreenBase.box_font_scale_stored`: taking
#    the window factor on both sides gives 4.0 at 2160p against an
#    intended 2.0.
_fp_seen = {}
for _fp_w, _fp_h in ((1920, 1080), (2560, 1440), (3440, 1440),
                     (3840, 2160)):
    _fp_app, _ = _prev.build_screen(_fp_w, _fp_h)
    _fp_app.dispatcher.switch_to("fleets")
    _fp_scr = _fp_app.dispatcher.screens["fleets"]
    _fp_st = _fp_scr.box_style(_fp_BOX)
    _fp_ref = (float(_fp_st["font_size"])
               * float(_fp_st.get("font_scale", 1.0)))
    _fp_px = _fp.panel_font_px(_fp_scr)
    assert _fp_px == _fp_scr.layout.font_size(
        max(1, int(round(_fp_ref)))), (
        f"{_fp_w}x{_fp_h}: panel_font_px is {_fp_px}, the box asks "
        f"for {_fp_ref} reference px")
    _fp_seen[(_fp_w, _fp_h)] = (_fp_px, _fp_scr, _fp_ref)
# the same share of the window at every one of the four, to within
# what `Layout.font_size`'s int() can cost — never a resolution
# where a floor or a squared factor changes the proportion
_fp_share = {k: v[0] / k[1] for k, v in _fp_seen.items()}
_fp_lo, _fp_hi = min(_fp_share.values()), max(_fp_share.values())
assert _fp_hi / _fp_lo <= 1.06, (
    "the panel's font is a different share of the window at "
    f"different resolutions: {_fp_share}. Anything above the "
    "truncation Layout.font_size costs means a per-resolution "
    "number has crept back in")
# and the box actually decides it: double the stored size, get
# double the pixels.
#
# **THE EXPECTED VALUE CARRIES `font_scale` TOO**, and until
# 20 September 2026 it did not — it compared against
# `layout.font_size(font_size * 2)` with the scale left out, which
# is only right while the scale is 1.0. It was 1.0 everywhere, so
# the check was green and wrong at the same time; the first F5
# session that set `ship_panel_text` to 1.5 turned it red and the
# message blamed the product. `panel_font_px` is
# `font_size * font_scale` through `Layout.font_size`, so the
# expectation has to be the same product.
_fp_px0, _fp_scr0, _ = _fp_seen[(1920, 1080)]
_fp_style = _fp_scr0.box_style(_fp_BOX)
_fp_keep = _fp_style.get("font_size")
_fp_sc = float(_fp_style.get("font_scale", 1.0))
try:
    _fp_style["font_size"] = _fp_keep * 2
    _fp_want = _fp_scr0.layout.font_size(
        max(1, int(round(_fp_keep * 2 * _fp_sc))))
    assert _fp.panel_font_px(_fp_scr0) == _fp_want != _fp_px0, (
        f"changing the box's font_size did not change the panel — "
        f"the size is still coming from somewhere else "
        f"(got {_fp.panel_font_px(_fp_scr0)}, expected {_fp_want}, "
        f"was {_fp_px0}, font_scale {_fp_sc})")
finally:
    _fp_style["font_size"] = _fp_keep

ok("the Fleets ship panel is sized by its box: ship_panel_text in "
   "both resolution sets, inside its hole and not a cutout, "
   "font_size x font_scale scaled once, the same share of the "
   "window at all four resolutions")

# ── THE PANEL IS LAID OUT THE WAY THE ORIGINAL LAYS IT OUT ─────
#
# Work order 154, formatting only. Every number below is a native
# x or a line rule from `Print_Scanned_Ship_Data_`
# (flt2.cpp:524-747) and every one of them was ALSO read off a
# native screenshot of the same panel, the ship "Rafale"
# (evidence/work_order_152/panel/001_20_panel_native.png). Two
# sources, which is what this tree asks for before a value is
# trusted.
#
# **NOTHING HERE MAY NEED THE EXTRACTED NAMES.** The wording comes
# out of the player's own HESTRNGS and TECHNAME.LBX, which a fresh
# clone does not have — and the first version of this check
# assumed they were there, passed on the machine that wrote it and
# failed in a clone. So the LAYOUT is measured against a panel
# built here out of literals, and the two states of the wording
# are both exercised: with the catalogues and without.
from screens.fleets import fltrows as _pl
from core.structs import star as _pl_star_spec
from core.structs import ship as _pl_ship_spec
#  NOT ALIASED. A loader class imported under another name is a
#  construction the piece-3 check cannot see; it refuses the
#  aliasing import for exactly that reason.
from core.shipparts import ShipPartNames
from core.hestrings import HStrings
import struct as _pl_s
import types as _pl_types
#    THE STAND-INS, not the player's catalogues: this very block
#    is the fourth occurrence of the clone-only fault and the
#    reason `derived` exists.
_pl_parts = derived(ShipPartNames)
_pl_str = derived(HStrings)
_pl_words = True
_pl_layout = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "layout.json"), encoding="utf-8"))

# 1. THE TAB STOPS ARE THE ORIGINAL'S OWN x VALUES over its own
#    window. `Set_Window_(15, 282, 320, 465)` is the origin and
#    the width, so a stop is (native x - 15) / 305.
for _pl_name, _pl_frac, _pl_native in (
        ("COL_LABEL", _fp.COL_LABEL, 0x12),
        ("COL_ENTRY", _fp.COL_ENTRY, 0x17),
        ("COL_RIGHT_LABEL", _fp.COL_RIGHT_LABEL, 0xAD),
        ("COL_RIGHT_ENTRY", _fp.COL_RIGHT_ENTRY, 0xBC),
        ("COL_OCV_VALUE_END", _fp.COL_OCV_VALUE_END, 0x85),
        ("COL_DCV_VALUE", _fp.COL_DCV_VALUE, 0x73 + 0xAD)):
    assert abs(_pl_frac - (_pl_native - 15) / 305.0) < 1e-9, (
        f"{_pl_name} is {_pl_frac}, and the original prints there "
        f"at native x {_pl_native} in a window at 15 of width 305")
assert _fp.SPECIALS_SPLIT == _fp.COL_RIGHT_ENTRY, (
    "SPECIALS_SPLIT stopped being the specials column's own stop; "
    "one number with two homes is decision 5's failure")
#    the entries are INDENTED under their headings, both columns
assert _fp.COL_ENTRY > _fp.COL_LABEL, "the weapons are not indented"
assert _fp.COL_RIGHT_ENTRY > _fp.COL_RIGHT_LABEL, (
    "the specials are not indented under their heading")

# 2. THE HEAD IS FOUR SLOTS AND AN EMPTY ONE IS A BLANK LINE.
#    The original has a fifth, Beam OCV / Beam DCV, between the
#    shield and the destination. HD does not draw it at all —
#    neither number is computable and Data refused empty labels on
#    20 September 2026 — so the grid is deliberately one line
#    shorter and `omission_panel_beam_bonuses` says so.
assert _pl.Panel.HEAD_SLOTS == (
    "name", "crew", "shield", "destination")

class _PlShip:
    """One ship's bytes, only what the panel reads."""

    def __init__(self, loc=0, shield=0, crew=(0, 15), ship_type=0):
        b = bytearray(_pl_ship_spec.SIZE)
        b[0:6] = b"Rafale"
        b[17] = ship_type
        b[18] = shield
        b[99] = 1
        b[101:103] = _pl_s.pack("<h", loc)
        b[113], b[114] = crew
        for i, (t, n) in enumerate(((14, 1), (21, 3))):
            o = (_pl_ship_spec.WEAPONS_OFFSET
                 + i * _pl_ship_spec.WEAPON_SIZE)
            b[o:o + 8] = _pl_s.pack("<hbbbHb", t, n, n, 0x10, 0, 0)
        self.raw = bytes(b)

class _PlStar:
    def __init__(self, name, visited):
        b = bytearray(_pl_star_spec.SIZE)
        b[0:len(name)] = name.encode("latin-1")
        b[171] = visited
        self.raw = bytes(b)

def _pl_state(loc, visited=0x01, n_stars=3):
    _g = _pl_types.SimpleNamespace()
    _g.ships_raw = [_PlShip(loc=loc).raw]
    _g.stars = _pl_star_spec.parse_all(
        [_PlStar(f"Star {i}", visited).raw for i in range(n_stars)])
    _g.player_raw = []
    _g.player_num = 0
    return _g

#    BOTH STATES OF THE WORDING, so neither can rot: the panel is
#    built once with the player's catalogues and once with none,
#    and the SLOTS have to behave the same either way.
for _pl_have, _pl_s_arg in ((_pl_words, _pl_str), (False, None)):
    _pl_p = _pl.panel_lines(0, _pl_state(0), _pl_parts, _pl_s_arg, None)
    assert len(_pl_p.head) == 4, _pl_p.head
    assert _pl_p.head[0] == "Rafale"
    assert not any(isinstance(_h, tuple) for _h in _pl_p.head), (
        "a head slot is still a two-label line; the Beam OCV/DCV "
        "line was dropped and nothing else in this panel has two")
    assert _pl_p.head[3] is None, (
        f"a parked ship got a destination line {_pl_p.head[4]!r}; the "
        f"original prints that line only for location >= 10000 "
        f"(flt2.cpp:644) and the native screenshot shows it blank")
    #  IN TRANSIT to a visited star: the slot is filled
    _pl_m = _pl.panel_lines(0, _pl_state(10000 + 1), _pl_parts,
                            _pl_s_arg, None)
    assert _pl_m.head[3], "a ship in transit got no destination line"
    assert "Star 1" in _pl_m.head[3], _pl_m.head[3]
    #  IN TRANSIT to a star nobody has explored: the NAME must not
    #  leak, with or without the wording to replace it with
    _pl_u = _pl.panel_lines(0, _pl_state(10000 + 1, visited=0x00),
                            _pl_parts, _pl_s_arg, None)
    assert not _pl_u.head[3] or "Star 1" not in _pl_u.head[3], (
        f"the destination named an unexplored star "
        f"({_pl_u.head[3]!r}); the original prints H 0x9C there "
        f"(flt2.cpp:661-666)")
    if _pl_have:
        assert _pl_u.head[3] == _pl_str.message(0x9C), _pl_u.head[3]
        _pl_a = _pl.panel_lines(0, _pl_state(10000 + 3), _pl_parts,
                                _pl_str, None)
        assert _pl_a.head[3] == _pl_str.message(0x68), _pl_a.head[3]
        #  and the two labels the line WOULD have used are not on
        #  screen anywhere, which is the whole of Data's decision
        for _pl_lbl in (_pl_str.message(0x99), _pl_str.message(0x9A)):
            assert _pl_lbl not in _pl_p.flat(), (
                f"{_pl_lbl!r} is still drawn; the Beam OCV/DCV line "
                f"was dropped because a label with nothing after it "
                f"is not wanted on the player's screen")
    else:
        #  WITHOUT the catalogues every wording slot is blank and
        #  none of them is invented
        assert _pl_u.head[3] is None, (
            f"with no HESTRNGS the unexplored destination became "
            f"{_pl_u.head[3]!r}; it has no wording to use and must "
            f"say nothing rather than fall back to the name")
    #  and `flat()` never carries a blank
    assert all(_pl_p.flat()), _pl_p.flat()

# 3. THE LINE GRID, MEASURED BY RECORDING WHAT IS DRAWN — against
#    a panel built out of LITERALS, so a clone with no extracted
#    names measures exactly what this machine measures.
class _PlRec:
    def __init__(self):
        self.at = []

    def blit(self, surf, pos):
        self.at.append((pos[0], pos[1], surf.get_width()))

_pl_lit = _pl.Panel(
    ["Rafale", "Green Crew (15 EP)", "No Shield", None],
    ["1 Nuclear Missile (360)", "3 Nuclear Bomb (360)"], ["None"],
    "Weapons:", "Specials:")
_pl_app, _ = _prev.build_screen(2560, 1440)
_pl_app.dispatcher.switch_to("fleets")
_pl_scr = _pl_app.dispatcher.screens["fleets"]
_pl_rect = _fp.panel_text_rect(_pl_scr)
_pl_rec = _PlRec()
assert _fp.draw_columns(_pl_rec, _pl_scr, _pl_lit, _pl_rect), (
    "the panel did not fit at 1440p for the ship the native "
    "screenshot shows")
_pl_stops = _fp._stops(_pl_rect)
_pl_ys = sorted({y for _x, y, _w in _pl_rec.at})
_pl_pitch = _pl_ys[1] - _pl_ys[0]
_pl_rows = {y: sorted(x for x, yy, _w in _pl_rec.at if yy == y)
            for y in _pl_ys}
_pl_first = _pl_ys[0]
#    the head's three filled slots, each on its own line and each
#    at the LEFT stop
for _pl_i in range(3):
    assert _pl_rows.get(_pl_first + _pl_i * _pl_pitch) == [
        _pl_stops["label"]], (
        f"head slot {_pl_i} is at "
        f"{_pl_rows.get(_pl_first + _pl_i * _pl_pitch)}, its stop "
        f"is {_pl_stops['label']}")
#    then a GAP of one blank line — the empty destination slot —
#    before the headings
_pl_headings = _pl_first + 4 * _pl_pitch
assert _pl_headings in _pl_rows, (
    "the Weapons/Specials headings are not one blank line below "
    "the head; the destination slot did not hold its place")
assert _pl_first + 3 * _pl_pitch not in _pl_rows, (
    "something was drawn in the blank destination slot")
#    the headings at the LABEL stops, the entries INDENTED
assert _pl_rows[_pl_headings] == [_pl_stops["label"],
                                  _pl_stops["right_label"]]
_pl_entries = _pl_rows[_pl_headings + _pl_pitch]
assert _pl_entries and _pl_entries[0] == _pl_stops["entry"], (
    f"the weapon entries start at {_pl_entries[0]} and their stop "
    f"is {_pl_stops['entry']}")
assert _pl_stops["right_entry"] in _pl_entries, (
    "the special entries are not at their own indented stop")
assert _pl_stops["entry"] > _pl_stops["label"]
assert _pl_stops["right_entry"] > _pl_stops["right_label"]

# 4. THE FOUR MARKS THIS ORDER ADDED SAY WHAT THE ORIGINAL DOES.
for _pl_mark, _pl_cite in (
        ("omission_panel_beam_bonuses", "initship.cpp:638-687"),
        ("deviation_panel_one_font", "flt2.cpp:578"),
        ("deviation_panel_destination_info", "flt2.cpp:657-662"),
        # WORK ORDER 159 CLOSED `omission_panel_support_ship_help`
        # and these two replace it: the mode is built, so what is
        # left to mark is the colour that is NOT transcribed and
        # the wording a clone with no extraction sees.
        ("deviation_panel_paragraph_colour", "flt2.cpp:566-571"),
        ("fallback_panel_help_missing", "labels.json")):
    assert _pl_mark in _pl_layout["marks"], _pl_mark
    assert _pl_cite in _pl_layout["marks"][_pl_mark], (
        f"{_pl_mark} no longer cites {_pl_cite}; a marking without "
        f"the line it describes is a label")

ok("the Fleets ship panel is laid out as the original lays it "
   "out: six tab stops re-derived from the native x values, four "
   "head slots with the destination slot blank for a parked ship, "
   "no Beam OCV/DCV labels anywhere, entries indented under both "
   "headings, the unexplored destination no longer naming the "
   "star with OR without the catalogues, and five markings citing "
   "what the original does instead")
