# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 084_fleets_a_fleets_map_click_resolves_to.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 5 check(s) it holds:
#   - a Fleets map click resolves to the star's OWN field or sends nothing: the offset is derived from
#   - the Fleets ship panel never drops a line in silence: short lists whole, the 8-weapon 39-special 
#   - RETURN's box is its own field and not help 374, the two empty areas say so in a text box and are
#   - a field the Fleets screen did not build hands back to the original: the eleven control origins, 
#   - the Fleets screen waits instead of flashing the original: the map's own recorded lists are WAITI


# 3. NOTHING IS DROPPED WITHOUT SAYING SO. The original clips at
#    its drawing window and says nothing (Set_Window_(15, 282, 320,
#    465), flt1.cpp:402); HD wraps, shrinks, and when it still does
#    not fit replaces its last line with `words.panel_more`. A
#    weapon quietly missing from a ship's list is the one outcome
#    this screen may not have.
_fp_words = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "layout.json"),
    encoding="utf-8"))["words"]
# ── ITEM 8: A STAR IS MATCHED TO ITS FIELD, OR NOTHING IS SENT ─
#
# Work order 152. The move is `ACTIVATE_FIELD` on the star's own
# hidden field, so the whole question is whether HD's drawn stars
# and the game's star fields are the same list. `fltmove.match`
# answers with a bijection or with {}, and {} means send nothing.
from screens.fleets import fltmove as _mv

class _MvF:
    def __init__(self, i, x, y):
        self.index = i
        self.x, self.y = x, y
        self.x_end = x + _flw.STAR_FIELD_SIZE[0]
        self.y_end = y + _flw.STAR_FIELD_SIZE[1]
        self.field_type = _flw.TYPE_HIDDEN
        self.hotkey = 0

# the shape the live run measured: a majority offset of (-6, -6)
# with a one-pixel scatter, inside a 54-star inset
# Spaced the way a real inset is: the star pitch has to exceed the
# offset, or a star's nearest field is its NEIGHBOUR's. On SAVE4's
# 54 stars over a 305x182 box the pitch is ~30 px against an offset
# of 12, which is the margin this rule lives on.
_mv_drawn = [(40 + 30 * (i % 8), 60 + 25 * (i // 8)) for i in range(20)]
_mv_fields = []
for _mv_i, (_mx, _my) in enumerate(_mv_drawn):
    _mv_dx = -6 - (1 if _mv_i % 7 == 0 else 0)
    _mv_dy = -6 - (1 if _mv_i % 5 == 0 else 0)
    _mv_fields.append(_MvF(_mv_i + 1, _mx + _mv_dx, _my + _mv_dy))
_mv_got = _mv.match(_mv_drawn, _mv_fields)
assert len(_mv_got) == len(_mv_drawn), (
    "the star/field match refused a list that differs from the "
    "majority offset by the one pixel the live run measured")
assert len({id(v) for v in _mv_got.values()}) == len(_mv_got), (
    "two stars were matched to one field")
# and it REFUSES rather than guessing
assert _mv.match(_mv_drawn, _mv_fields[:-1]) == {}, (
    "a short field list was matched anyway; a missing star field "
    "means the two lists are not the same list")
_mv_far = list(_mv_fields)
_mv_far[3] = _MvF(4, _mv_far[3].x + 40, _mv_far[3].y)
assert _mv.match(_mv_drawn, _mv_far) == {}, (
    "a star 40 px from its field was matched; outside SLACK the "
    "mapping is not established and nothing may be sent")
assert _mv.SLACK < 12, "SLACK is wide enough for two stars to collide"

ok(f"a Fleets map click resolves to the star's OWN field or sends "
   f"nothing: the offset is derived from the data, the one-pixel "
   f"scatter is allowed, and a short or shifted list refuses")

# ── ITEM 7: THE PANEL IS THE ORIGINAL'S CONTENT, IN ITS WORDS ──
#
# Work order 152. Every string here comes from the player's own
# tables or from a literal in the engine; nothing is HD's English.
from core import kentext as _kt
from screens.fleets import fltrows as _fr

# 1. ALL FIVE ARCS, and the order the original tests them in.
#    0x0F has four bits set and the original answers FORWARD for it,
#    so the order is the answer and not a tidy-up.
assert set(_kt.ARC_MESSAGES) == {0x01, 0x02, 0x04, 0x08}, (
    "the arc message table is not the four Weapon_Arc_String_ asks "
    "KEN for (design.cpp)")
assert _kt.ARC_ORDER == (0x01, 0x02, 0x04, 0x08, 0x10)
assert _kt.ARC_360 == "360", (
    "0x10's word is a LITERAL in Weapon_Arc_String_, not a table "
    "entry — it must not become an extraction")
#    BOTH STATES, EVERY TIME. This used to run whichever branch
#    the machine happened to be in — present here, absent in a
#    clone — so neither was ever exercised on both. The stand-in
#    gives the present one and a directory with nothing in it
#    gives the other.
_kt_words = derived(_kt.ArcWords)
for _kt_bit in _kt.ARC_ORDER:
    assert _kt_words.arc(_kt_bit), (
        f"arc 0x{_kt_bit:02X} has no word; item 7 ships only "
        f"when all five come from source")
assert _kt_words.arc(0x0F) == _kt_words.arc(0x01), (
    "ALL_SECTORS did not answer with the FORWARD word; the bits "
    "are tested in order and the first hit returns")
import tempfile as _kt_tf          # `_tf` is core.textfit by here
with _kt_tf.TemporaryDirectory() as _kt_empty:
    _kt_gone = _kt.ArcWords("en", root=_kt_empty)
    assert not _kt_gone.available
    assert "kentext_extract" in _kt_gone.absent, _kt_gone.absent
    assert _kt_gone.arc(0x01) is None, (
        "with no file an arc answered with a word anyway")

# 2. THE PANEL CARRIES THE ORIGINAL'S OWN SPLIT, and the column
#    positions are the original's: weapons at 0x17, specials at
#    0xBC, inside a window from x 15 that is 305 wide.
assert abs(_fp.SPECIALS_SPLIT - (0xBC - 15) / 305.0) < 1e-9, (
    "the specials column moved off the x the original prints it at")
_fr_p = _fr.Panel(["a"], ["w"], ["s"], "W", "S")
assert _fr_p.flat() == ["a", "W", "w", "S", "s"]

# 3. THE CREW FIELDS ARE IN THE VERIFIED SPEC, or the crew line is
#    reading an offset nobody confirmed.
from core.structs import ship as _sp_ship
_sp_names = {f[0] for f in _sp_ship.SPEC.fields} \
    if hasattr(_sp_ship.SPEC, "fields") else set()
for _sp_n in ("crew_quality", "crew_experience"):
    assert _sp_n in str(_sp_ship.SPEC.__dict__) or _sp_n in _sp_names \
        or hasattr(_sp_ship.SPEC, _sp_n) or _sp_n in io.open(
            os.path.join(os.path.dirname(SCREENS_DIR), "core",
                         "structs", "ship.py"),
            encoding="utf-8").read(), (
        f"{_sp_n} left core/structs/ship.py while the panel prints it")

# 4. THE TWO OMISSIONS SAY SO (decision 61).
_fr_marks = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "layout.json"),
    encoding="utf-8"))["marks"]
for _fr_key in ("omission_panel_plural", "omission_panel_damaged_red"):
    assert "OMISSION" in _fr_marks.get(_fr_key, ""), (
        f"layout.json no longer marks {_fr_key}")

assert "{n}" in _fp_words["panel_more"], (
    "words.panel_more carries no {n}; the marker would not say how "
    "much is missing, which is the whole of it")
# AND IT SAYS NOTHING ELSE. Data, 20 September 2026: the marker is
# on the PLAYER's screen and the editor is not the player's
# business. What a developer needs goes to the log, from
# `fltpanel._log_overflow`.
for _fp_word in ("F5", "font_size", "boxes.json", "editor"):
    assert _fp_word.lower() not in _fp_words["panel_more"].lower(), (
        f"words.panel_more says {_fp_word!r}; that is a developer's "
        f"instruction on a player's screen. It belongs in the log")
assert "log.info" in io.open(os.path.join(
    SCREENS_DIR, "fleets", "fltpanel.py"), encoding="utf-8").read(), (
    "fltpanel no longer logs the overflow; the player's marker is "
    "deliberately short, so the log is the only place that says "
    "WHICH box was too small")

# NO DEAD FONT KEY ON THIS SCREEN. `Box.render` sizes a `text` box
# from `font_size` alone and never reads `font_scale`
# (core/box.py:101), so a `font_scale` on one is a number that
# looks like a setting and is not. `inset_hint` and `status_hint`
# carried 0.8 and had always rendered at 16. The unification —
# making `Box.render` compose the two — is parked in
# `v3_projektstatus.md` under "What is missing"; until it happens
# this keeps the Fleets screen from growing the key back.
for _fp_res, _fp_list in _fp_boxfile.items():
    for _fp_b in _fp_list:
        _fp_bs = _fp_b.get("style") or {}
        if _fp_bs.get("skin") != "text" or "font_scale" not in _fp_bs:
            continue
        raise AssertionError(
            f"{_fp_res}: box {_fp_b['name']} is a `text` box with "
            f"font_scale {_fp_bs['font_scale']}, which core/box.py "
            f"never reads — it renders at font_size "
            f"{_fp_bs.get('font_size', 16)} whatever that number "
            f"says. Set font_size, or read font_scale the way "
            f"fltpanel does")
for _fp_w, _fp_h in ((1920, 1080), (2560, 1440), (3440, 1440),
                     (3840, 2160)):
    _, _fp_scr, _ = _fp_seen[(_fp_w, _fp_h)]
    _fp_rect = _fp.panel_text_rect(_fp_scr)
    # a list that fits: every line is there and nothing is marked
    _fp_lines, _fp_size, _fp_drop = _fp.panel_block(
        _fp_scr, _fp_short, _fp_words, _fp_rect)
    assert _fp_drop == 0 and len(_fp_lines) == len(_fp_short), (
        f"{_fp_w}x{_fp_h}: three short lines came out as "
        f"{len(_fp_lines)} with {_fp_drop} dropped")
    assert _tf.block_height(_fp_lines) <= _fp_rect.height
    # the worst the struct allows: 8 weapons and 39 specials
    _fp_lines, _fp_size, _fp_drop = _fp.panel_block(
        _fp_scr, _fp_huge, _fp_words, _fp_rect)
    assert _tf.block_height(_fp_lines) <= _fp_rect.height, (
        f"{_fp_w}x{_fp_h}: the panel drew past its box — that is "
        f"the silent clip this replaces")
    assert _fp_drop > 0, f"{_fp_w}x{_fp_h}: 50 lines fitted?"
    assert _fp_size >= _fp_scr.layout.font_size(_fp.PANEL_MIN_FONT), (
        f"{_fp_w}x{_fp_h}: the panel shrank past PANEL_MIN_FONT "
        f"({_fp_size}); below it the words stop being words and "
        f"dropping lines is the better trade")
    _fp_marker = _fp_scr.style.render_text(
        _fp_words["panel_more"].replace("{n}", str(_fp_drop)),
        _fp_size, _fp.col("label_dim"))
    assert _fp_lines[-1].get_size() == _fp_marker.get_size(), (
        f"{_fp_w}x{_fp_h}: the last line is not the marker, so "
        f"{_fp_drop} lines went missing without a word")
# the marker is marked, where decision 61 says
_fp_marks = _sjson.load(io.open(os.path.join(
    SCREENS_DIR, "fleets", "layout.json"),
    encoding="utf-8"))["marks"]
assert "HD EXTENSION" in _fp_marks.get(
    "deviation_panel_overflow", ""), (
    "layout.json no longer marks the panel's overflow behaviour an "
    "HD EXTENSION; the original clips silently and HD does not")
# and the wrap is textfit's, not a fourth private copy
_fp_src = io.open(os.path.join(SCREENS_DIR, "fleets",
                               "fltpanel.py"), encoding="utf-8").read()
assert "textfit.squeeze_block" in _fp_src, (
    "fltpanel no longer goes through core/textfit — decision 30's "
    "rule that wrapping is measured BY RENDERING lives there, in "
    "one place, and this was the module that made it three")
assert ".split()" not in _fp_src, (
    "fltpanel looks like it wraps on its own again")

ok("the Fleets ship panel never drops a line in silence: short "
   "lists whole, the 8-weapon 39-special worst case wrapped and "
   "shrunk to PANEL_MIN_FONT, the remainder counted in "
   "words.panel_more, inside the box at all four resolutions, "
   "marked HD EXTENSION")

# ── 137 E4/E5/E6: WHERE RETURN'S BOX COMES FROM, THE TWO EMPTY
#    AREAS, AND THE TWO HIGHLIGHTED CELLS ────────────────────────
#
# E4. RETURN's drawn box is its FIELD and nothing else. Help 374 is
# (456, 430)-(628, 456) (evanhelp.cpp:165), a strip reaching left
# across the two filter radios, and decision 38 lets a help
# rectangle decide no box edge. The entry used to take the strip's
# right and bottom — and 556 + 73 - 1 IS 628, so the wrong
# derivation produced the right rectangle. That is why this is a
# check and not a comment.
assert _flg.CONTROLS["btn_return"][1][:2] == (556, 430), (
    "RETURN's box no longer starts at its field's own origin "
    "(flt1.cpp:1201)")
assert _flg.CONTROLS["btn_return"][1][2:] == \
    _flg.CONTROLS["btn_leaders"][1][2:], (
        "RETURN's extent is no longer LEADERS' — the same row, the "
        "same artwork family, and the only size in any source")
_fl_help374 = (456, 430, 628 - 456 + 1, 456 - 430 + 1)
assert not [_n for _n, (_p, _r) in _flg.CONTROLS.items()
            if tuple(_r) == _fl_help374], (
    "a control box equals help 374's strip; a help rectangle is not "
    "an extent (decision 38)")
assert "374" in io.open(os.path.join(SCREENS_DIR, "fleets", "help.json"),
                        encoding="utf-8").read(), (
    "help 374 left help.json; the rectangle is still the original's "
    "and stays where decision 38 puts it")

# E5. The two areas HD leaves empty say so, in a `text` box
# (decision 37) whose words are in `layout.json` (decision 15), and
# both are marked OMISSION beside the four fltwire already carries.
assert set(_flg.HINTS) == {"inset_hint", "status_hint"}, _flg.HINTS
_fl_boxfile_1080 = _sjson.load(io.open(
    os.path.join(_fl_dir, "boxes.json"),
    encoding="utf-8"))["1920x1080"]
for _fl_hint, (_fl_region, _fl_word) in _flg.HINTS.items():
    assert _fl_word in _fl_layout["words"], _fl_word
    _fl_hb = next((_b for _b in _fl_boxfile_1080
                   if _b["name"] == _fl_hint), None)
    assert _fl_hb and _fl_hb["style"].get("skin") == "text", (
        f"{_fl_hint} is not a text box; a panel or a border there "
        f"would be a second outline inside {_fl_region}'s own")
# E5b. EVERY CONTROL THE PLAYER CAN CLICK WEARS A WORD — the rule,
#      not the list. PREV and NEXT were live, clickable and drawn
#      as NOTHING AT ALL for two work orders, because the original
#      draws arrow glyphs there and `draw_labels` only knew the
#      seven that have painted words. A box with a field behind it
#      and no mark on it is a feature a player cannot find.
from screens.fleets import fltdraw as _fd_mod
_fl_clickable = set(_flw.HOTKEYS) & set(_fhB.RULE_NAMES["fleets"])
_fl_worded = {_n for _n, _k in _fd_mod.CONTROL_WORDS}
assert _fl_worded == _fl_clickable, (
    f"these are clickable controls with a hole and no word: "
    f"{sorted(_fl_clickable - _fl_worded)}; and these have a word "
    f"and are not clickable controls: "
    f"{sorted(_fl_worded - _fl_clickable)}")
for _fl_n, _fl_k in _fd_mod.CONTROL_WORDS:
    assert (_fl_layout["words"].get(_fl_k) or "").strip(), (
        f"{_fl_n} maps to words.{_fl_k}, which is missing or empty "
        f"— the box would draw nothing and the control would be "
        f"invisible")

assert {"omission_inset_map", "omission_status_line"} <= \
    set(_fl_layout["marks"]), sorted(_fl_layout["marks"])
for _fl_mark, _fl_cite in (("omission_inset_map", "flt1.cpp:649"),
                           ("omission_status_line", "flt2.cpp:338-522")):
    assert _fl_layout["marks"][_fl_mark].startswith("OMISSION"), _fl_mark
    assert _fl_cite in _fl_layout["marks"][_fl_mark], (
        f"{_fl_mark} no longer cites {_fl_cite}, so it records a "
        f"label rather than what the original does instead")

# E6. TWO HIGHLIGHTED CELLS ARE THE ORIGINAL'S OWN STATE, not a
# fault: FLT1::Set_Fltscrn_Big_Icons_ (flt1.cpp:1610-1616) is the
# ALL button and sets `selected = 1` on every icon, and
# Update_Selection_Flags_ (:1069-1093) counts them — SCRAP exists
# only while the count is above zero (:1185). What the panel shows
# is a DIFFERENT variable: the SCANNED ship, never the selection.
# **THIS CHECK IS ABOUT THE WIRE'S `scanned_big`, so it clears
# HD's own hover first.** Since work order 153 B there are two
# sources and `fltscan.resolve` prefers HD's pointer; a check
# that did not say which one it was driving would answer
# whichever an EARLIER check happened to leave set, which is what
# it did the moment work order 155's block started hovering. A
# check states its own precondition.
_fl_scr._scan.clear()
_fl_multi = _fl_snapshot(selected=(1, 2), scanned_big=0)
_fl_multi.fields = _fl_fields(6)
_fl_scr.update(_fl_multi)
assert _fl_scr._view.state == _flw.READY, _fl_scr._view.state
assert [_c.selected for _c in _fl_scr._cells] == \
    [False, True, True, False, False, False], (
        "the grid does not draw two selected cells; multi-select is "
        "the original's own state")
assert _fl_scr._view.selected_ships() == [1, 2]
# `_panel` is a `fltrows.Panel` since work order 152 item 7 — the
# original prints its weapons and specials in two COLUMNS, so the
# content carries the split. Compared through `flat()`, which is
# the same three parts in one list.
_fl_panel_0 = list(_fl_scr._panel.flat())
_fl_scr._scan.clear()
_fl_one = _fl_snapshot(selected=(1, 2), scanned_big=3)
_fl_one.fields = _fl_fields(6)
_fl_scr.update(_fl_one)
assert list(_fl_scr._panel.flat()) != _fl_panel_0 and _fl_scr._panel, (
    "the ship panel did not follow the SCANNED ship; it must not "
    "follow the selection, which can be several ships at once")
ok("RETURN's box is its own field and not help 374, the two empty "
   "areas say so in a text box and are marked OMISSION with the line "
   "the original draws there, and two selected cells are the "
   "original's own state while the panel follows the SCANNED ship")

# ── A FIELD THIS SCREEN DID NOT BUILD HANDS BACK TO THE ORIGINAL ──
#
# Work order 137 A, from the state 136 D found by reading: SCRAP's
# confirmation box (FLT1::Scrap_Ships_ flt1.cpp:1512 ->
# HAROLD::User_Box_ mode 1 -> GENDRAW::Confirmation_Box_) adds two
# hidden fields at native (0xEB, 0x12E)-(0x11E, 0x143) and
# (0x159, 0x12E)-(0x18C, 0x143) (gendraw.cpp:172-173) and CLEARS
# NOTHING. The screen id stays 4, ext_api.cpp:265 keeps writing the
# FLTS block, every field this screen built is still at its own
# rect — so the validation that only asks "is each cell's field
# there" said READY over a game waiting in a modal loop.
#
# THE RULE, NOT THE BOX. `fltwire.foreign_fields` knows what
# `Add_Fleet_Screen_Fields_` builds, read out of the builders
# (flt1.cpp:1177-1263), and ANY field outside that set hands back.
# So the check feeds the two real fields AND a stranger at four
# other places, and it feeds a list built from the tables themselves
# so that a rule which called one of our own fields foreign fails
# here rather than in front of Data.
_ff_icons = [(137, 0, 5, 0, 60, 80), (138, 1, 6, 2, 90, 95)]

def _ff_field(rect, ftype, hotkey=0, index=0):
    _f = _gs_mod.FieldInfo()
    _f.index = index
    _f.x, _f.y, _f.x_end, _f.y_end = rect
    _f.field_type, _f.hotkey = ftype, hotkey
    return _f

def _ff_ours(n_cells=6):
    """A list holding one of EVERY field the builder can add, and
        the engine's own slot 0 in front of them (FIELD_ZERO_ROW)."""
    _out = [_fl_zero()]
    for _i in range(n_cells):
        _x, _y = _FL_CELLS[_i]
        _out.append(_ff_field((_x, _y, _x + 58, _y + 57),
                              _flw.TYPE_HIDDEN, 0, 10 + _i))
    for (_ox, _oy), _types in _flw.CONTROL_ORIGINS.values():
        # The extent comes from FLEET.LBX at runtime, so any is fine
        # and the rule must not depend on it.
        _out.append(_ff_field((_ox, _oy, _ox + 73, _oy + 27),
                              _types[0], 0, 50 + len(_out)))
    for _r, _types in _flw.EXACT_FIELDS.items():
        _out.append(_ff_field(_r, _types[0], 0, 90 + len(_out)))
    for _ic in _ff_icons:                      # small ship icons
        _out.append(_ff_field((_ic[4], _ic[5], _ic[4] + 9, _ic[5] + 9),
                              _flw.TYPE_HIDDEN, 0x29, 120 + len(_out)))
    for _sx, _sy in ((40, 70), (300, 220)):    # inset star fields
        _out.append(_ff_field((_sx - 3, _sy - 3, _sx + 8, _sy + 9),
                              _flw.TYPE_HIDDEN, 0x29, 150 + len(_out)))
    return _out

#: GENDRAW::Confirmation_Box_'s two, exactly as it adds them.
_FF_CONFIRM = [_ff_field((0xEB, 0x12E, 0x11E, 0x143),
                         _flw.TYPE_HIDDEN, 0x29, 300),
               _ff_field((0x159, 0x12E, 0x18C, 0x143),
                         _flw.TYPE_HIDDEN, 0x29, 301)]

# FIELD 0 IS IN EVERY FIXTURE, AND THAT IS THE POINT OF THIS BLOCK.
# The RECORDED lists carry it because they were captured live; the
# HAND-BUILT ones did not, and that is where 137 A's fault hid for
# two days. Both halves are asserted, so a re-recording that drops
# it and a new builder that forgets it both fail here.
for _ff_rec in ("galaxy_box_fields.json", "game_menu_fields.json"):
    _ff_j = _sjson.load(io.open(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools", _ff_rec),
        encoding="utf-8"))
    for _ff_k, _ff_v in _ff_j.items():
        _ff_rows = _ff_v.get("fields") if isinstance(_ff_v, dict) else _ff_v
        if not isinstance(_ff_rows, list) or not _ff_rows \
                or not isinstance(_ff_rows[0], list):
            continue
        assert _ff_rows[0][0] == 0, (
            f"{_ff_rec}[{_ff_k}] does not start with field 0; a "
            f"recorded list that lost it is no longer what the "
            f"engine sends (fields.cpp:207, ext_api.cpp:326)")
assert _fl_fields(6)[0].index == 0 and _ff_ours()[0].index == 0, (
    "a hand-built Fleets field list has no field 0")
assert FIELD_ZERO_ROW[0] == 0 and FIELD_ZERO_ROW[1:5] != (0, 0, 0, 0), (
    "FIELD_ZERO_ROW must be index 0 with junk geometry: zeros are "
    "falsy and a rule that survives them has not met the slot")

_ff_gs = _fl_snapshot(ship_icons=_ff_icons)
assert _ff_gs.fleet_screen is not None, (
    "the fixture's FLTS block did not parse with ship icons present "
    "— the owner block sits between them and FSEL")

# 1. EVERY FIELD THE BUILDER MAKES IS ONE OF OURS.
_ff_gs.fields = _ff_ours()
assert _flw.foreign_fields(_ff_gs.fields, _FL_CELLS, _ff_gs.ship_icons) == [], (
    "fltwire calls one of Add_Fleet_Screen_Fields_'s own fields "
    "foreign: "
    f"{[(f.x, f.y, f.x_end, f.y_end) for f in _flw.foreign_fields(_ff_gs.fields, _FL_CELLS, _ff_gs.ship_icons)]}")
_fl_scr.update(_ff_gs)
assert _fl_scr._view.state == _flw.READY, _fl_scr._view.state

# 2. THE CONFIRMATION BOX HANDS BACK, and says which fields.
_ff_gs.fields = _ff_ours() + _FF_CONFIRM
_fl_scr.update(_ff_gs)
assert _fl_scr._view.state == _flw.FOREIGN_FIELDS, _fl_scr._view.state
assert _fl_scr.wants_original()
for _r in ((0xEB, 0x12E, 0x11E, 0x143), (0x159, 0x12E, 0x18C, 0x143)):
    assert str(_r) in _fl_scr.fallback_reason(), (
        f"the reason does not name {_r}: {_fl_scr.fallback_reason()}")
assert _fl_scr.problems
# AND NOTHING GOES OUT while it is handing back — the game is in
# Confirmation_Box_'s own input loop (gendraw.cpp:205-212), which
# takes only its two fields, so an HD send is swallowed and the
# player sees a screen that did not react.
_fl_sent.clear()
_fl_scr.handle_click(*_fl_slots[1].center)
_fl_scr.handle_click(*_fl_scr.box_by_name("btn_scrap").screen_rect.center)
_fl_scr.handle_mousewheel(1, 960, 540)
_fl_scr.handle_key(27)
assert _fl_sent == [], _fl_sent
_fl_scr.render(_fl_surf)

# 3. AND IT COMES BACK WITHOUT A RESTART. The View is rebuilt from
#    the snapshot every update, so the box closing is the whole of
#    the recovery — no flag to reset, nothing to time out.
_ff_gs.fields = _ff_ours()
_fl_scr.update(_ff_gs)
assert _fl_scr._view.state == _flw.READY, _fl_scr._view.state
assert not _fl_scr.wants_original()
_fl_sent.clear()
_fl_scr.handle_click(*_fl_slots[1].center)
assert _fl_sent == [(1, False)], _fl_sent

# 4. A STRANGER ANYWHERE ELSE DOES THE SAME. Five places, each one
#    a near-miss of a rule rather than a random rectangle: a button
#    one pixel off its origin, a cell-sized field outside the grid,
#    a star-sized field outside the inset, an icon-sized field at no
#    icon's corner, and a second full-screen catcher.
for _ff_what, _ff_f in (
        ("a button one px off its origin",
         _ff_field((550, 380, 621, 407), _flw.TYPE_BUTTON, ord("S"), 400)),
        ("a cell-sized field outside the grid",
         _ff_field((100, 100, 158, 157), _flw.TYPE_HIDDEN, 0x29, 401)),
        ("a star-sized field outside the inset",
         _ff_field((400, 400, 411, 412), _flw.TYPE_HIDDEN, 0x29, 402)),
        ("an icon-sized field at no icon's corner",
         _ff_field((61, 80, 70, 89), _flw.TYPE_HIDDEN, 0x29, 403)),
        ("a second full-screen catcher",
         _ff_field((0, 0, 639, 478), _flw.TYPE_HIDDEN, 0, 404))):
    _ff_gs.fields = _ff_ours() + [_ff_f]
    _fl_scr.update(_ff_gs)
    assert _fl_scr._view.state == _flw.FOREIGN_FIELDS, (
        f"{_ff_what} was accepted as one of this screen's own")
    assert _fl_scr.wants_original() and _fl_scr.fallback_reason()

# 5. THE SET IS PINNED TO THE BUILDER, because a rule that reads a
#    table cannot notice a row taken OUT of the table. Eleven
#    controls, three exact rects: Add_Fleet_Screen_Fields_ adds
#    SCRAP, ALL, RETURN, the two scroll arrows, PREV, NEXT,
#    RELOCATE, LEADERS and the two filter radios, plus the debug
#    field, the screen-filling catcher and the big-icon scroll bar.
assert set(_flw.CONTROL_ORIGINS) == {
    "btn_scrap", "btn_all", "btn_return", "scroll_up", "scroll_down",
    "prev_fleet", "next_fleet", "btn_relocate", "btn_leaders",
    "btn_support", "btn_combat"}, sorted(_flw.CONTROL_ORIGINS)
assert set(_flw.EXACT_FIELDS) == {(0, 0, 639, 479), (0, 470, 10, 479),
                                  (605, 86, 619, 320)}, _flw.EXACT_FIELDS
# LEADERS is the one control that legitimately carries two types —
# a button with an officer, a hidden field without (flt1.cpp:1234,
# :1240) — and it is why a control is not identified by type alone.
assert _flw.CONTROL_ORIGINS["btn_leaders"][1] == (
    _flw.TYPE_BUTTON, _flw.TYPE_HIDDEN)

ok("a field the Fleets screen did not build hands back to the "
   "original: the eleven control origins, the three exact rects, "
   "the grid cells, the ship icons and the inset star fields are "
   "its own, SCRAP's two confirmation fields and five near-misses "
   "are not, nothing is sent while it hands back, and it returns "
   "to READY when they go")

# ── THE ORIGINAL DOES NOT FLASH UP WHEN THE SCREEN OPENS ────────
#
# Work order 142 A. `MOX2::Screen_Control_` calls `ext::Tick` at
# the top of its loop (mox2.cpp:40) and dispatches to
# `Fleet_Screen_` after it, so the first snapshot that says screen
# 4 still carries the galaxy map's field list. 139 A made that
# visible and 140 measured it live — 24 strangers, then one — and
# every open showed the game's own picture for about a second.
#
# WAITING is that state. It is recognised by the field
# `Add_Fleet_Screen_Fields_` adds LAST,
# `Add_Hidden_Field_(0, 0, 639, 479, "", 0)` (flt1.cpp:1262): its
# presence means the whole list is built. Checked against RECORDED
# live lists rather than assumed — none of the galaxy map's four in
# `tools/galaxy_box_fields.json` carries a full-screen field, and
# the one list that does is a message box's own catcher with hotkey
# ESC (textbox.cpp:246), which is why the hotkey is part of the
# test.
assert not _flw.has_fleet_list([]), "an empty list is not ours"
_wt_map = _sjson.load(io.open(os.path.join(
    os.path.dirname(SCREENS_DIR), "tools", "galaxy_box_fields.json"),
    encoding="utf-8"))

def _wt_rows(rows):
    # The fixture stores some entries as a bare list of rows and
    # some as {_what, fields}; both are the same recording.
    if isinstance(rows, dict):
        rows = rows["fields"]
    _out = []
    for _r in rows:
        _f = _gs_mod.FieldInfo()
        (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
         _f.hotkey) = _r
        _out.append(_f)
    return _out

for _wt_name in ("closed", "fleet_own", "fleet_monster", "system"):
    assert not _flw.has_fleet_list(_wt_rows(_wt_map[_wt_name])), (
        f"the galaxy map's recorded list '{_wt_name}' reads as the "
        f"Fleets screen's own")
# The message box's catcher carries ESC and must NOT pass either.
assert not _flw.has_fleet_list(_wt_rows(_wt_map["modal"])), (
    "a message box's full-screen catcher (hotkey ESC, "
    "textbox.cpp:246) reads as the Fleets list")
assert _flw.has_fleet_list(_fl_fields(6)), "our own list does not"

# 1. THE MAP'S LIST WITH SCREEN 4 IS **WAITING**, and WAITING keeps
#    HD's own picture up and sends nothing.
_wt_gs = _fl_snapshot(ship_icons=_ff_icons)
_wt_gs.fields = _wt_rows(_wt_map["closed"])
_fl_scr.update(_wt_gs)
assert _fl_scr._view.state == _flw.WAITING, _fl_scr._view.state
assert not _fl_scr.wants_original(), (
    "WAITING handed over; that is the flash 142 A is about")
assert _fl_scr._view.waiting and not _fl_scr._view.ok
assert _fl_scr.fallback_reason(), "WAITING says nothing"
_fl_sent.clear()
_fl_scr.handle_click(*_fl_slots[1].center)
_fl_scr.handle_click(*_fl_scr.box_by_name("btn_all").screen_rect.center)
_fl_scr.handle_mousewheel(1, 960, 540)
_fl_scr.handle_key(27)
assert _fl_sent == [], (
    f"WAITING sent {_fl_sent} into the previous screen's list")
_fl_scr.render(_fl_surf)

# 2. THE LIST ARRIVES -> READY, on the next update and nothing else
#    (decision 21: the state ends on the event, never on a timer).
_wt_gs.fields = _fl_fields(6)
_fl_scr.update(_wt_gs)
assert _fl_scr._view.state == _flw.READY, _fl_scr._view.state
assert not _fl_scr.wants_original()

# 3. AND FOREIGN_FIELDS IS NOW THE REAL BOX CASE ONLY: our list,
#    plus GENDRAW::Confirmation_Box_'s two (gendraw.cpp:172-173).
_wt_gs.fields = _fl_fields(6) + _FF_CONFIRM
_fl_scr.update(_wt_gs)
assert _fl_scr._view.state == _flw.FOREIGN_FIELDS, _fl_scr._view.state
assert _fl_scr.wants_original(), (
    "a native box over the Fleets screen must still hand over")

# 4. EVERY LIST ABOVE CARRIES A FIELD 0, because the engine cannot
#    send one without (141 B). The recorded ones have their own;
#    the built ones get FIELD_ZERO_ROW.
assert _wt_rows(_wt_map["closed"])[0].index == 0
assert _fl_fields(6)[0].index == 0

ok("the Fleets screen waits instead of flashing the original: the "
   "map's own recorded lists are WAITING at screen 4 and send "
   "nothing, the catcher field (flt1.cpp:1262) ends it, and "
   "FOREIGN_FIELDS is left for a real native box")
