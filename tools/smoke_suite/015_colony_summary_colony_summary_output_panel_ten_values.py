# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 015_colony_summary_colony_summary_output_panel_ten_values.py.
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
#   - colony summary output_panel (ten values drawn, BC deviation marked, empty selection draws nothin
#   - colony summary production net (four branches, the (int8_t) cast, the shortage and both of its re


# ── output_panel: eleven values, and the selection that feeds it ──
# The panel is a TRANSCRIPTION of the original's bottom-left scan
# box (colsum.cpp:1155, fundament 43 withdrawn), so what is
# asserted is which values it shows, that they are VISIBLE and not
# merely computed, and that an absence stays an absence.
from screens.colony_summary import colonyoutput as _co
_out_cfg = _sjson.load(open(os.path.join(
    SCREENS_DIR, "colony_summary", "layout.json"),
    encoding="utf-8"))
_words = _out_cfg["words"]
_ocfg = _out_cfg["output"]
_climates = _out_cfg["list"]["climates"]

# THE WORD LISTS, and their provenance. The words are ours: the
# original reads them from the player's estrings.lbx at runtime
# (estrings.cpp, Load_E_Strings_), so there is nothing to
# transcribe and the note has to say so or the list reads as one.
for _cite in ("estrings.cpp:155-169", "estrings.cpp:204-213",
              "estrings.lbx", "decision 15", "list.climates"):
    assert _cite in _words["_note"], (
        f"words._note no longer carries {_cite!r} — these are our "
        f"own English words, not the game's, and the note is the "
        f"only thing that says so")
assert len(_words["sizes"]) == 5 and len(_words["gravities"]) == 3, (
    f"the size and gravity lists are {len(_words['sizes'])} and "
    f"{len(_words['gravities'])}; the enums are 5 and 3 "
    f"(orion2_consts.h:392-397, :377-380) and the index IS the "
    f"enum value")
assert len(_words["minerals"]) == 5, _words["minerals"]
# ONE HOME for each list. Asserting the rule, not the instance: a
# climate word appearing in both blocks is the screen-ID-map
# failure, and it would agree with itself on the day it was made.
assert "climates" not in _words, (
    "the climate words have been copied into the words block; "
    "they live in list.climates with their own provenance note, "
    "and a second copy that agrees today is what drifts tomorrow")
for _w in ("sizes", "gravities", "minerals"):
    assert _w not in _out_cfg["list"], (
        f"{_w} now exists in the list block as well as in words")

# THE TEN VALUES, for one fake colony. Chosen so every one of
# them is distinguishable from every other in the output: a check
# that asserts "0" appears ten times asserts nothing.
# `production` and `drawn_production` are DIFFERENT here on
# purpose: the panel draws the net the original computes
# (coldraw.cpp:73-94) and the sort keys read the stored value, so
# a fake that made them equal would let the panel read either one
# and still pass.
_fake = {"index": 3, "name": "Probe I", "climate": 9, "pops": 17,
         "jobs": [5, 6, 6], "no_farming": False, "max_pop": 31,
         "producing": "", "producing_turns": 0, "can_buy": False,
         "production": [90, 91, 92, 93],
         "drawn_production": [11, 22, 33, 44],
         "shortage": [0, 0, 0, 0], "size": 3, "gravity": 2,
         "mineral": 4, "growth": -42, "morale": -7,
         "morale_applies": True}
_shown = _co.visible_rows(_fake, _ocfg, _words, _climates)
assert len(_shown) == 11, (
    f"the panel has {len(_shown)} rows; it draws the seven "
    f"E_Strings_(74) values in six, the four ECON values, and "
    f"morale")
assert len(_shown) == len(_ocfg["rows"]), (_shown, _ocfg["rows"])
_text = " ".join(f"{e.label}={e.value}" for e in _shown)
for _value in ("Large", "Gaia", "Heavy", "Ultra Rich", "17", "31",
               "-42k", "11", "22", "33", "44"):
    assert _value in _text, (
        f"the panel does not show {_value!r} — it is one of the "
        f"eleven the original's scan box carries. Got: {_text}")
assert "-7" in _text, "morale is not shown"
# And it is the NET that reaches the panel, not the record.
for _stored in ("90", "91", "92", "93"):
    assert _stored not in _text, (
        f"the panel drew the STORED production {_stored} — it must "
        f"draw colonyrows.drawn_production, which is what "
        f"COLDRAW::Draw_Colony_Prod_Both_ computes before it draws "
        f"anything (coldraw.cpp:73-94)")
# GROWTH: signed, and the k is a UNIT — MOO2 counts population in
# thousands and the original's scan box printed "+63k". The sign
# comes from colonyempire.format_value, which is the one home for
# that rule; the unit is wording and lives in the template.
_growth_shown = [e.value for e in _shown if e.label.lower() == "growth"]
assert _growth_shown == ["-42k"], (
    f"growth shows {_growth_shown!r}; it is a net flow, so it "
    f"carries its sign, and thousands, so it carries its k")
_pos = _co.visible_rows(dict(_fake, growth=7), _ocfg, _words, _climates)
assert [e.value for e in _pos if e.label.lower() == "growth"] == ["+7k"], (
    "a positive growth has no explicit plus — the original prints "
    "one, for the same reason the sidebar's Income and Food do")
assert "k" in _ocfg["_growth_note"] and "thousand" in \
    _ocfg["_growth_note"], (
    "output._growth_note no longer says the k is a unit rather "
    "than a decoration, which is the whole of why it is there")

# ── THE SCAN BOX IS TWO BOXES, AND THEY SPLIT BY COLUMN ──
# `Draw_Colony_Scan_Info_` fills the description paragraph at
# native (13, 354, 80, 88) and the production rows from native
# x 106 (colsum.cpp:1171-1176, :1206). The `column` field in
# layout.json already said which row belongs to which half; since
# 8 September 2026 the two halves go into the two holes the frame
# gives them instead of both into the right one.
_left = _co.visible_rows(_fake, _ocfg, _words, _climates, only={0})
_right = _co.visible_rows(_fake, _ocfg, _words, _climates, only={1})
assert len(_left) + len(_right) == len(_shown), (
    f"{len(_left)} + {len(_right)} rows against {len(_shown)} — "
    f"the split must partition the panel, not sample it")
assert {e.label.lower() for e in _left} == {
    "size", "climate", "gravity", "minerals", "population",
    "growth"}, [e.label for e in _left]
assert {e.label.lower() for e in _right} == {
    "food", "industry", "research", "bc", "morale"}, \
    [e.label for e in _right]
# ── THE DESCRIPTION PANEL DRAWS THE PARAGRAPH, AND ONLY IT ──
# `output.info_style` chose between the paragraph and the
# label-and-value table so the two pictures could be compared
# beside the native. They were; Data took the paragraph; Stage 5
# removed the key (brief 87, brief 81's "if the paragraph stays
# the only user"). This asserted that BOTH variants drew
# something, which with one variant left is a tautology — so it
# asserts what is actually true now: the panel draws the
# paragraph whatever the config says, and a stray `info_style`
# cannot bring the branch back by being present.
_info_box = pygame.Rect(0, 0, 324, 224)
_iink = []
for _stray in ({}, {"info_style": "rows"}):
    _isurf = pygame.Surface((324, 224))
    _isurf.fill((0, 0, 0))
    _co.render_info(_isurf, _fake, _info_box,
                    dict(_ocfg, **_stray), _words,
                    _climates, app.layout, app.style)
    _iarr = pygame.surfarray.array3d(_isurf)
    assert _iarr.any(), "the description panel drew nothing at all"
    _iink.append(_iarr.tobytes())
assert _iink[0] == _iink[1], (
    "a stray output.info_style changed what the description panel "
    "drew — the switch is gone and the key must be inert")
# THE PARAGRAPH IS FIVE LINES, NOT SIX ROWS: size and climate
# share one and growth carries no label, which is what
# E_Strings_(74) does.
_para = _co.fill_template(_ocfg["info_paragraph"],
                          _co.row_values(_fake, _words, _climates))
assert len(_para.split("\n")) == 5, _para
assert _para.split("\n")[0] == "Large Gaia", _para
assert "{" not in _para, (
    "a placeholder survived substitution in the paragraph; "
    "fill_template replaces and never formats (decision 37)")
# AND THE WORD-LIST RULE HOLDS FROM THIS SIDE TOO: the nouns are
# in the FORMAT, never in the lists — which is exactly what
# "%sravity" and "Mineral %s" do in the original.
for _noun in ("Gravity", "Mineral", "Population"):
    assert _noun in _ocfg["info_paragraph"], (
        f"the paragraph does not supply {_noun!r}; the word lists "
        f"hold the bare quality and the format the noun "
        f"(words._note)")
    for _lst in ("sizes", "gravities", "minerals"):
        assert not any(_noun.lower() in str(_w).lower()
                       for _w in _words.get(_lst, ())), (
            f"words.{_lst} carries {_noun!r} — it would render "
            f"twice in the paragraph and twice in the table")
# THE WHOLE BOX REDDENS ON NEGATIVE GROWTH, because the format
# opens the attribute before the first word and closes it after
# the last (colsum.cpp:1186-1206). The value alone would be the
# obvious-looking reading and is not what the arguments say.
_red = pygame.Surface((324, 224))
_red.fill((0, 0, 0))
_co.render_info(_red, _fake, _info_box, _ocfg, _words, _climates,
                app.layout, app.style)
_blk = pygame.Surface((324, 224))
_blk.fill((0, 0, 0))
_co.render_info(_blk, dict(_fake, growth=7), _info_box, _ocfg,
                _words, _climates, app.layout, app.style)
def _count(_surface, _rgb):
    _a = pygame.surfarray.array3d(_surface)
    return sum(1 for x in range(324) for y in range(224)
               if tuple(_a[x, y]) == tuple(_rgb[:3]))

_warm = _count(_red, _co.SHORTAGE_COLOR)
_cool = _count(_blk, _co.VALUE_COLOR)
assert _warm > 50 and _count(_red, _co.VALUE_COLOR) == 0, (
    f"negative growth inked {_warm} px of the warn colour and "
    f"{_count(_red, _co.VALUE_COLOR)} of the value colour; the "
    f"sign string opens the attribute before the FIRST word and "
    f"the reset comes after the last, so the whole paragraph "
    f"reddens rather than the number")
assert _cool > 50 and _count(_blk, _co.SHORTAGE_COLOR) == 0, (
    f"positive growth inked {_count(_blk, _co.SHORTAGE_COLOR)} px "
    f"of the warn colour — nothing should redden at all")

# ── A VALUE CARRIES NO PREFIX; THE LABEL CARRIES IT ──
# A rule, not three decisions. The original's box is one run-on
# paragraph and this panel is a table, so a word that reads
# correctly there reads twice here: MINERALS Mineral Rich, GRAVITY
# Normal Gravity. The source draws the line more finely than "our
# list is wrong" — colland.cpp:60-62 puts the mineral value into
# its own format string, so "Mineral" belongs to the FORMAT and
# the table holds "Rich"; colland.cpp:65 prints the gravity entry
# with no format at all, so "Normal Gravity" really is in the
# table. Both lists carry the bare quality either way.
for _cite in ("colland.cpp:60-62", "colland.cpp:65",
              "THE LABEL CARRIES IT"):
    assert _cite in _words["_note"], (
        f"words._note no longer carries {_cite!r} — the rule is "
        f"what keeps this from being re-decided one list at a time")
for _list_name, _label in (("gravities", "Gravity"),
                           ("minerals", "Minerals")):
    _label_words = set(_label.lower().rstrip("s").split())
    for _w in _words[_list_name]:
        assert not (set(_w.lower().split()) & _label_words), (
            f"{_list_name} carries {_w!r}, which repeats its own "
            f"label: the panel would draw '{_label.upper()} {_w}'")
# ALL FOUR PRODUCTION VALUES. BC was left out for a day on the
# reading that the panel showed "food, industry and research";
# the original draws four. ECON_COUNT is 4 (orion2_consts.h:123)
# and the GEOMETRY says so without the constant: y_pos starts at
# 349 and steps 18 (colsum.cpp:1170-1173) — 349, 367, 385, 403 —
# with morale one step further on at 421 (colsum.cpp:1176), which
# leaves room for four rows above it and not three.
_prod_rows = [_r for _r in _ocfg["rows"]
              if _r["value"] in ("{food}", "{industry}",
                                 "{research}", "{bc}")]
assert len(_prod_rows) == 4, (
    f"the panel draws {len(_prod_rows)} production rows; the "
    f"original draws ECON_COUNT of them and ECON_COUNT is 4")
assert all(_r["column"] == _prod_rows[0]["column"]
           for _r in _prod_rows), (
    "the four production values are split across columns; the "
    "original draws them as one column at native x 106")
for _cite in ("colsum.cpp:1170-1173", "colsum.cpp:1176"):
    assert _cite in _ocfg["_deviation_note"], (
        f"output._deviation_note no longer cites {_cite!r} — the "
        f"geometry is what settled the fourth row independently "
        f"of ECON_COUNT")
# WHAT IS STILL NOT DRAWN has to keep naming itself. After the
# net and the shortage landed, two of the original's four groups
# per row remain: imports[t] (coldraw.cpp:46) and the secondary
# group — imports[ECON_INDUSTRY] on food, pollution on industry
# (coldraw.cpp:51-58). Both are REACHABLE, so the note must not
# read as a data limitation, and an omission nobody wrote down is
# indistinguishable from one nobody saw.
# AND HOW TO READ A NATIVE SCREENSHOT OF ONE. The groups are
# separated by an empty SLOT (a bare drawn_count++ at
# coldraw.cpp:150, budgeted at :100), and a negative-imports group
# is drawn with the NET's own sprites (coldraw.cpp:154 against
# :118) — so two groups look like one long run. That is exactly
# how Wolf II's BC row was read as 18 when it was 10 plus 8, and
# the note is the only place that mistake is written down.
for _cite in ("coldraw.cpp:73-94", "coldraw.cpp:46",
              "coldraw.cpp:51-58", "pollution", "REACHABLE",
              "coldraw.cpp:150", "empty slot", "10 plus 8"):
    assert _cite in _ocfg["_deviation_note"], (
        f"output._deviation_note no longer carries {_cite!r} — it "
        f"is the record of which of the original's four groups "
        f"this panel still does not draw, and why that is a "
        f"layout question and not a missing offset")

# MORALE UNDER UNIFICATION: the label stays, the value goes. The
# original zeroes its own sprite count (Draw_Info_Morale_Both_),
# so drawing a 0 would claim neutral morale where the original is
# claiming that morale does not apply.
_unified = dict(_fake, morale_applies=False)
_mor = [(e.label, e.value) for e
        in _co.visible_rows(_unified, _ocfg, _words, _climates)
        if e.label.lower() == "morale"]
assert _mor and _mor[0][1] == _ocfg["hidden_value"], (
    f"under Unification the morale row shows {_mor!r}; it must "
    f"show hidden_value, and a 0 is not the same statement")

# AN INDEX OUTSIDE ITS ENUM IS VISIBLE, not clamped. A clamp
# would draw "Huge" for a 9 and look exactly like data.
_bad = _co.row_values(dict(_fake, size=99), _words, _climates)
assert _bad["size"] == "?", _bad["size"]

# Substitution is a REPLACE, never str.format (decision 37): a
# stray brace must not raise inside the render path.
assert _co.fill_template("{size} }{ {nope}", {"size": "Large"}) == \
    "Large }{ {nope}", _co.fill_template("{size} }{ {nope}",
                                         {"size": "Large"})

# ── The panel DRAWS them, and draws nothing when empty ──
# A green table says the data is right; only ink says it is
# visible. Both directions, because the empty case is the one
# that would silently become a column of zeroes.
d.switch_to("colony_summary")
_scr_op = d.active
_op_box = _scr_op.box_rect("planet_output")
assert _op_box, "planet_output has no box"
_oa = pygame.Rect(*app.layout.rect(_op_box))
_osurf = pygame.Surface((_oa.right + 8, _oa.bottom + 8))
_osurf.fill((0, 0, 0))
_co.render(_osurf, _fake, _oa, _ocfg, _words, _climates,
           app.layout, app.style)
_ink = pygame.surfarray.array3d(_osurf.subsurface(_oa)).sum()
assert _ink > 0, "the panel drew nothing for a selected colony"
_osurf.fill((0, 0, 0))
_co.render(_osurf, None, _oa, _ocfg, _words, _climates,
           app.layout, app.style)
assert pygame.surfarray.array3d(_osurf.subsurface(_oa)).sum() == 0, (
    "the panel put ink on the screen with nothing selected. The "
    "original's box is guarded by _g_colony_n != -1 "
    "(colsum.cpp:1165) and a zero is a value where it has an "
    "absence")
assert _ocfg["empty"] == "", (
    "output.empty is no longer empty — that is allowed, but the "
    "check above then has to change with it rather than fail")

# THE COLUMNS MUST NOT RUN TOGETHER, and the failure that
# actually happened was NOT an overlap. The first render had
# column_gap 12, every number in it was correct, no two glyphs
# touched — and 'Huge GROWTH' and 'Ultra Poor RESEARCH' read as
# single phrases, because the left column's right-aligned value
# ended twelve pixels before the right column's left-aligned
# label began. So there are two assertions and they catch
# different things:
#
#   the GUTTER must be at least one em of the value font. Two
#   runs of type separated by less than the height of the type
#   read as one run with a word space in it. That is the rule the
#   34 was measured against, stated as a rule so it survives a
#   font change rather than pinning the number that came out of
#   one look.
#
#   the widest LABEL plus the widest VALUE must still fit the
#   column minus that gutter, which is the different failure of a
#   long word eating the gap it was given.
#
# Both at every shipped resolution, and both measured by
# RENDERING (decision 30) because render_text can mix two fonts
# inside one string and a single font's .size() is not the width
# that gets drawn.
assert _ocfg["column_gap"] >= _ocfg["value_font"], (
    f"column_gap {_ocfg['column_gap']} is under one em of the "
    f"{_ocfg['value_font']} px value font, so the left column's "
    f"value and the right column's label read as one phrase. "
    f"That is how the first render of this panel looked, with "
    f"every value in it correct.")
# PER ROW, against the values THAT ROW can actually show. Pairing
# the widest label in the panel with the widest value in the
# panel asserts a collision that cannot happen — POPULATION never
# prints "Ultra Poor" — and it failed at 1280x720 on exactly that
# imaginary pair. The real tightest is MINERALS against
# "Ultra Poor".
_POP_CAP = _cl.POP_LIMIT_CAP
_WORDS_FOR = {"{size}": _words["sizes"], "{climate}": list(_climates),
              "{gravity}": _words["gravities"],
              "{mineral}": _words["minerals"]}
# RE-POINTED 13 September 2026, brief 97: this measured a TWO-column
# table of all eleven rows in `planet_output`, which has not been
# drawn since the paragraph moved to `planet_info` — the box draws
# the five column-1 rows in ONE column, each label shifted right by
# its icon and `icon_gap` (decision 56). What is asserted is that
# geometry, in the part of `colony_panel` the rows now sit in.
from screens.colony_summary import colonyoutputicons as _cg_oi
for _W, _H in _SIZES:
    _lay = Layout(_W, _H)
    _r = pygame.Rect(*_lay.rect(_op_box))
    _cols = 1
    _pad = int(_ocfg["pad_x"] * _lay.scale)
    _cw = (_r.w - 2 * _pad) // _cols
    _cgap = int(_ocfg["column_gap"] * _lay.scale)
    _icon_room = (_cg_oi.icon_px(_ocfg, _lay.scale)
                  + int(_ocfg.get("icon_gap", 0) * _lay.scale))
    # One em of the LABEL font, scaled like everything else.
    _em = _lay.font_size(_ocfg["label_font"])
    for _row_spec in [_s for _s in _ocfg["rows"] if _s["column"] == 1]:
        _cands = _WORDS_FOR.get(_row_spec["value"])
        if _cands is None:
            # Numeric. The widest a value can get: growth sums ten
            # int16 (colsum.cpp:1179-1182), the others are one,
            # and population is the engine's cap over itself.
            _cands = ([f"{_POP_CAP}/{_POP_CAP}"]
                      if "/" in _row_spec["value"]
                      else ["-327680" if _row_spec["id"] == "growth"
                            else "-32768"])
        _lw = app.style.render_text(
            _row_spec["label"].upper(),
            _lay.font_size(_ocfg["label_font"]),
            (255, 255, 255)).get_width() + _icon_room
        # THE SHORTAGE MARKER AND A WIDE VALUE CANNOT CO-OCCUR,
        # and that is structural rather than lucky. A shortage is
        # drawn only when imports >= 0 and the row is not
        # industry (coldraw.cpp:152) — which is exactly the
        # branch where the net IS production[t] (coldraw.cpp:86)
        # — and it is positive only when
        # production < maintenance - imports <= maintenance,
        # a u8[4] at offset 239. So a row that shows a marker has
        # a value in 0..254 and a marker in 1..255; a row with a
        # wide value has no marker at all. Pairing the widest of
        # each would assert a case the engine cannot produce, and
        # it fails at 1366x768 — which is how this coupling was
        # found rather than assumed.
        #
        # The one assumption, stated because it is the one that
        # could break: production is never negative.
        _pairs = [(_c, "") for _c in _cands]
        if _row_spec["id"] in ("food", "research", "bc"):
            _pairs.append(
                ("254",
                 _ocfg["shortage_value"].replace("{shortage}", "255")))
        for _cand, _short in _pairs:
            _vw = app.style.render_text(
                _cand, _lay.font_size(_ocfg["value_font"]),
                (255, 255, 255)).get_width()
            if _short:
                _vw += app.style.render_text(
                    _short, _lay.font_size(_ocfg["label_font"]),
                    (255, 255, 255)).get_width() + int(
                        _ocfg["shortage_gap"] * _lay.scale)
            assert _lw + _vw <= _cw - _cgap - _em, (
                f"{_W}x{_H}: {_row_spec['label']!r} ({_lw} px) and "
                f"{_cand + _short!r} ({_vw} px) need {_lw + _vw} px in a "
                f"column of {_cw - _cgap}, leaving less than one "
                f"em of the label font between them — they read "
                f"as one phrase before they touch, which is what "
                f"column_gap 34 was measured to prevent")

# ── The selection: row 0 on entry, and it keeps its COLONY ──
# colsum.cpp:139 sets _g_colony_n = _list_col[0] in the screen's
# setup, and _list_col is filled from the SORTED list
# (colsum.cpp:348-351). The sort handler (colsum.cpp:830-837)
# never touches _g_colony_n, so the selection follows its colony
# into the new order rather than staying on row 0.
_sel_snap = _pv._Snapshot(_pv.COLONIES)
_scr_op._sort_key = "name"
_scr_op.update(_sel_snap)
assert _scr_op.selected_position() == 0, (
    f"entry selection is row {_scr_op.selected_position()}, not "
    f"row 0 of the sorted list (colsum.cpp:139)")
_first_name = _scr_op.selected_row()["name"]
_first_index = _scr_op._selected
# A key that reorders the list, so "row 0" and "the same colony"
# are different answers and the check can tell them apart.
_scr_op._sort_key = "population"
_scr_op._rebuild_rows()
_moved = _scr_op.selected_position()
assert _scr_op._selected == _first_index, (
    f"the sort reseated the selection from colony {_first_index} "
    f"to {_scr_op._selected}; the original keeps the colony and "
    f"lets its ROW move (colsum.cpp:830-837 touches nothing)")
assert _scr_op.selected_row()["name"] == _first_name, "colony changed"
assert _moved != 0, (
    f"{_first_name!r} is still at row 0 after re-sorting, so this "
    f"check cannot tell 'keeps the colony' from 'keeps the row' — "
    f"pick a sort key that actually moves it")
# And the panel follows the selection rather than the row index.
assert _co.visible_rows(_scr_op.selected_row(), _ocfg, _words,
                        _climates), "the panel lost its row"
# An empty snapshot selects nothing at all — not row 0 of nothing.
_scr_op.update(_pv._Snapshot([]))
assert _scr_op._selected is None and _scr_op.selected_row() is None, (
    f"an empty colony list still has a selection "
    f"({_scr_op._selected!r})")
_scr_op.update(_sel_snap)

# The hit-test and the drawing share one geometry (decision 5):
# every drawn band's midpoint must resolve back to its own row.
_la = pygame.Rect(*app.layout.rect(_scr_op.box_rect("list_area")))
_lcfg = dict(_out_cfg["list"])
# The column table, as the screen's own cfg carries it — see the
# overflow fixture above for why a fixture without it tests the
# path the screen does not take.
_lcfg = _column_cfg(_lcfg, app.layout)
_bands = _cl.row_bands(_la, _lcfg, app.layout.scale,
                       len(_scr_op._rows))
assert _bands, "no row bands for a non-empty list"
for _i, (_top, _h) in enumerate(_bands):
    assert _cl.row_at(_la, _lcfg, app.layout.scale,
                      len(_scr_op._rows),
                      (_la.x + 4, _top + _h // 2)) == _i, _i
# Hovering row 1 selects the colony IN row 1, and clicking it
# changes nothing — the original would leave for SCREEN_COLONY
# (colsum.cpp:912-920) and there is no HD screen to leave to.
_t1, _h1 = _bands[1]
_scr_op.handle_mouse_motion(_la.x + 4, _t1 + _h1 // 2)
assert _scr_op._selected == _scr_op._rows[1]["index"], (
    "hovering a row did not select its colony "
    "(colsum.cpp:880-890 assigns _g_colony_n on the SCANNED "
    "field, not the clicked one)")
_before = _scr_op._selected
_cap2 = _Cap()
_cl_save, _conn_save = app.client, app.connected
app.client, app.connected = _cap2, True
_scr_op.handle_click(_la.x + 4, _t1 + _h1 // 2)
app.client, app.connected = _cl_save, _conn_save
assert _scr_op._selected == _before, "a row click moved the selection"
assert _cap2.calls == [] and _cap2.keys == [], (
    f"a row click sent {_cap2.calls}/{_cap2.keys} to the game. It "
    f"is inert on purpose: the original leaves for SCREEN_COLONY "
    f"and no HD screen exists to leave to")
# Leaving the list keeps the last colony — the assignment in
# colsum.cpp:880-890 has no else branch.
_scr_op.handle_mouse_motion(_la.x - 40, _la.y - 40)
assert _scr_op._selected == _before, (
    "the selection cleared when the pointer left the list; the "
    "original's _g_colony_n keeps whatever it last held")
ok("colony summary output_panel (ten values drawn, BC deviation "
   "marked, empty selection draws nothing, columns clear at 12 "
   "resolutions, hover selects and the sort keeps the colony)")

# ── The NET the original draws, and the shortage beside it ──
# COLDRAW::Draw_Colony_Prod_Both_ (coldraw.cpp:36) computes what
# it draws BEFORE it draws anything. Until 4 September 2026 this
# panel printed colony->production[t], which is only one of the
# four branches at coldraw.cpp:73-94 — so the number a player
# read was wrong whenever a colony had maintenance or imports,
# and it looked exactly as plausible as the right one.
import types as _types
from screens.colony_summary import colonyrows as _crw

def _col(prod, maint, imps, poll=0):
    return _types.SimpleNamespace(production=list(prod),
                                  maintenance=list(maint),
                                  imports=list(imps),
                                  pollution=poll)

# ALL FOUR BRANCHES, with values chosen so each gives a DIFFERENT
# answer from the others. A case where every branch returns
# production[t] would pass against any three of the four.
#
# A to D are `colonyrows.drawn_production.__doc__`'s names for
# them, which is also where the record of WHICH of the four has
# ever been seen on a live save lives — B and C have, A and D
# have not, and the assertions below are all A and D have.
#   A  byte(imports) < 0, t == INDUSTRY  -> max(0, prod - maint[t])
#   B  byte(imports) < 0, t != INDUSTRY  -> prod - abs(imports)
#   C  otherwise, maint[INDUSTRY] == 0 or t != INDUSTRY -> prod
#   D  otherwise                          -> max(0, prod - maint[t])
_bA = _col([20, 30, 40, 50], [3, 7, 0, 0], [-5, -2, 0, 0])
# NOT "branch A", and the name is corrected rather than kept.
# A and D are the SAME expression (coldraw.cpp:75-78 against
# :89-92) and both are guarded by prod_type == ECON_INDUSTRY, so
# nothing here or anywhere can tell which one ran — deleting A
# and letting this case fall through to D leaves the suite green,
# tried on 4 September 2026. What this asserts is the VALUE the
# industry row produces with byte-negative imports, which is
# right whichever branch computes it. See
# colonyrows.drawn_production, which records that A is covered by
# the transcription and not by a test.
assert _crw.drawn_production(_bA, _crw.ECON_INDUSTRY) == 23, (
    "the industry row with byte-negative imports must be "
    "production - maintenance (coldraw.cpp:74-78, and :88-92, "
    "which are the same three lines)")
assert _crw.drawn_production(_bA, _crw.ECON_FOOD) == 15, (
    "branch B: a non-industry row with byte-negative imports is "
    "production - abs(imports) (coldraw.cpp:80)")
assert _crw.drawn_production(_bA, _crw.ECON_RESEARCH) == 40, (
    "branch C: non-negative imports on a non-industry row is the "
    "stored production (coldraw.cpp:86)")
_bD = _col([20, 30, 40, 50], [0, 7, 0, 0], [0, 4, 0, 0])
assert _crw.drawn_production(_bD, _crw.ECON_INDUSTRY) == 23, (
    "branch D: industry with non-negative imports and non-zero "
    "maintenance[INDUSTRY] is production - maintenance "
    "(coldraw.cpp:89)")
# …and the SAME row takes branch C when maintenance[INDUSTRY] is
# 0, which is the condition that separates C from D. Without this
# the two are indistinguishable.
assert _crw.drawn_production(
    _col([20, 30, 40, 50], [0, 0, 0, 0], [0, 4, 0, 0]),
    _crw.ECON_INDUSTRY) == 30, (
    "maintenance[INDUSTRY] == 0 must send the industry row to the "
    "plain production branch (coldraw.cpp:85)")
# The clamp is the original's and is on both maintenance branches.
assert _crw.drawn_production(
    _col([3, 3, 0, 0], [10, 10, 0, 0], [-1, -1, 0, 0]),
    _crw.ECON_INDUSTRY) == 0, (
    "production below maintenance must clamp at 0, not go "
    "negative (coldraw.cpp:76)")

# THE INDUSTRY ROW COLLAPSES TO ONE EXPRESSION, and asserting
# that is worth more than pretending to separate A from D. The
# engine writes imports[ECON_INDUSTRY] in exactly one place —
# COLCALC::Pre_Import_Computing_ (colcalc.cpp:487) ends with
# imports = min((uint8)maintenance, production) at :507-511, and
# grepping every assignment to `imports[` finds no other. Feed
# the function inputs that satisfy that invariant, as a real
# snapshot always does, and all four branches agree on
# max(0, production - maintenance).
#
# ASSUMPTION, load-bearing and the same one the docstring names:
# production[ECON_INDUSTRY] >= 0. The sweep only covers that
# case, because below it the collapse genuinely fails.
for _p in (0, 1, 7, 30, 127, 128, 200, 255, 400):
    for _m in (0, 1, 7, 100, 127, 128, 200, 255):
        _imp = min(_m, _p)                    # colcalc.cpp:507-511
        _got = _crw.drawn_production(
            _col([0, _p, 0, 0], [0, _m, 0, 0], [0, _imp, 0, 0]),
            _crw.ECON_INDUSTRY)
        assert _got == max(0, _p - _m), (
            f"industry row with production {_p}, maintenance {_m} "
            f"and the engine's own imports {_imp} drew {_got}, "
            f"not {max(0, _p - _m)}. On engine-consistent input "
            f"all four branches compute that one expression — see "
            f"colonyrows.drawn_production for the derivation")

# THE (int8_t) CAST, AND IT IS DELIBERATE. coldraw.cpp:73 tests
# the LOW BYTE of imports[t]; coldraw.cpp:152, deciding whether
# to draw the shortage, tests the WHOLE int16 with no cast. 384
# is positive as a word and -128 as a byte, so the two disagree —
# and this check is here so the next reader who "tidies" the cast
# into a plain comparison fails instead of silently changing a
# number. Filed as a QUESTION in doc/orion2re_open_fixes.md,
# because which of the two is the transcription is the original
# binary's answer and not ours.
_cast = _col([20, 0, 0, 0], [0, 0, 0, 0], [384, 0, 0, 0])
assert _crw.drawn_production(_cast, _crw.ECON_FOOD) == 20 - 384, (
    "imports 384 has a NEGATIVE low byte, so the net takes the "
    "byte-negative branch (coldraw.cpp:73). Getting 20 here means "
    "the cast was normalised to a plain int16 comparison — do not "
    "fix it, it is transcribed; see colonyrows._low_byte_signed")
assert _crw._low_byte_signed(384) == -128 and \
    _crw._low_byte_signed(256) == 0 and \
    _crw._low_byte_signed(-1) == -1, "the cast is not (int8_t)"

# THE SHORTAGE: maintenance - imports - production, clamped below
# 1 (coldraw.cpp:61-64).
assert _crw.production_shortage(
    _col([12, 0, 0, 0], [13, 0, 0, 0], [0, 0, 0, 0]),
    _crw.ECON_FOOD) == 1, (
    "Wolf II is the reference case: 13 maintenance, 0 imports, 12 "
    "production, and the original draws exactly one red marker")
assert _crw.production_shortage(
    _col([12, 0, 0, 0], [11, 0, 0, 0], [0, 0, 0, 0]),
    _crw.ECON_FOOD) == 0, "a surplus is not a negative shortage"

# THE REFUSALS, which are the part that matters. Those
# Short_Anims_ loops (coldraw.cpp:170-177) sit in the ELSE of
# `if (imports[t] < 0 || t == ECON_INDUSTRY)` (coldraw.cpp:152),
# so the original draws a shortage ONLY for a non-industry row
# with non-negative imports. The arithmetic alone would produce a
# number on the industry row too, and drawing it would be an
# invention wearing a citation — decision 33 says mirror the
# refusal, not just the sum.
_short_ind = _col([2, 2, 0, 0], [9, 9, 0, 0], [0, 0, 0, 0])
assert _crw.production_shortage(_short_ind, _crw.ECON_FOOD) == 7, (
    "the food row of the refusal case must have a shortage, or "
    "the industry half of this check proves nothing")
assert _crw.production_shortage(
    _short_ind, _crw.ECON_INDUSTRY) == 0, (
    "a shortage was computed for the INDUSTRY row; the original "
    "never draws one there (coldraw.cpp:152)")
# NEGATIVE imports, the other refusal. The word is tested here,
# not the byte — the same field, the other comparison.
assert _crw.production_shortage(
    _col([2, 0, 0, 0], [9, 0, 0, 0], [-1, 0, 0, 0]),
    _crw.ECON_FOOD) == 0, (
    "a shortage was computed for a row with negative imports; "
    "that row takes the IF at coldraw.cpp:152 and draws imports "
    "as Prod_Anims_ instead")

# ── The shortage reaches the panel, and only when it should ──
_sh_row = dict(_fake, shortage=[3, 5, 0, 0])
_sh = {e.label.lower(): e.shortage
       for e in _co.visible_rows(_sh_row, _ocfg, _words, _climates)}
assert _sh["food"] == _ocfg["shortage_value"].replace("{shortage}", "3"), (
    f"the food row's shortage element is {_sh['food']!r}; the "
    f"wording is layout.json's shortage_value (decision 15) and "
    f"the substitution is a replace (decision 37)")
assert _sh["industry"], "a non-zero shortage was dropped"
# ZERO DRAWS NOTHING AT ALL, not a 0 and not a dash — the same
# shape as the empty selection. A template that renders "0" must
# not be able to bring the element back, because the decision is
# the number's and is taken before the template.
assert _sh["research"] == "" and _sh["bc"] == "", (
    f"a zero shortage produced {_sh['research']!r}; the original "
    f"draws no sprite, and a 0 is a claim where it has an absence")
assert all(e.shortage == "" for e in _co.visible_rows(
    _fake, _ocfg, _words, _climates)), (
    "a colony with no shortage anywhere still produced elements")
# A non-production row can never take one, whatever it is called.
assert _sh["growth"] == "" and _sh["size"] == "", (
    "a non-production row was given a shortage element")

# AND ON THE SURFACE: the marker is ink, and no shortage is no
# ink. Rendered twice into the same rect and differenced, so this
# asserts the drawing and not the tuple a second time.
_sh_area = pygame.Rect(*app.layout.rect(_scr_op.box_rect("planet_output")))
_sh_surf = pygame.Surface((_sh_area.right + 8, _sh_area.bottom + 8))
_sh_ink = []
for _r in (_fake, _sh_row):
    _sh_surf.fill((0, 0, 0))
    _co.render(_sh_surf, _r, _sh_area, _ocfg, _words, _climates,
               app.layout, app.style)
    _sh_ink.append(int(pygame.surfarray.array3d(
        _sh_surf.subsurface(_sh_area)).sum()))
assert _sh_ink[1] > _sh_ink[0], (
    f"the panel put no more ink on a colony with two shortages "
    f"({_sh_ink[1]}) than on one with none ({_sh_ink[0]})")

# AND THE MARKER FOLLOWS THE VALUE, which is the order the
# original draws its groups in: net, secondary, imports,
# shortage — the shortage is LAST (coldraw.cpp:170-177, after the
# import loops). It was drawn to the LEFT until 4 September 2026.
# Asserted by colour: the marker is the only thing on the panel
# in the warn red, so its columns can be found without knowing
# where the renderer decided to put it.
_sh_surf.fill((0, 0, 0))
_co.render(_sh_surf, dict(_fake, shortage=[3, 0, 0, 0]), _sh_area,
           _ocfg, _words, _climates, app.layout, app.style)
_sh_px = pygame.surfarray.array3d(
    _sh_surf.subsurface(_sh_area)).transpose(1, 0, 2).astype(int)
_red = _np.array(_co.SHORTAGE_COLOR[:3], dtype=int)
_val = _np.array(_co.VALUE_COLOR[:3], dtype=int)
_is_red = (_np.abs(_sh_px - _red).sum(axis=2) < 60)
_is_val = (_np.abs(_sh_px - _val).sum(axis=2) < 60)
_rows_red = _np.where(_is_red.any(axis=1))[0]
assert len(_rows_red), "the shortage marker put no red on the panel"
# The value on the SAME row as the marker.
_band = slice(max(0, _rows_red.min() - 2), _rows_red.max() + 3)
_red_x = _np.where(_is_red[_band].any(axis=0))[0]
_val_x = _np.where(_is_val[_band].any(axis=0))[0]
assert len(_val_x), "no value ink on the shortage row"
assert _red_x.min() > _val_x.max(), (
    f"the shortage marker (x {_red_x.min()}..{_red_x.max()}) is not "
    f"to the right of the value (x {_val_x.min()}..{_val_x.max()}). "
    f"The original draws the shortage as the LAST group in the row "
    f"(coldraw.cpp:170-177); drawing it first inverts the only two "
    f"groups this panel has")
ok("colony summary production net (four branches, the (int8_t) "
   "cast, the shortage and both of its refusals)")
