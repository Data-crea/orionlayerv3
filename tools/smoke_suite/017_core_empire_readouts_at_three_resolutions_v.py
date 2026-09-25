# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 017_core_empire_readouts_at_three_resolutions_v.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - empire readouts at three resolutions (value ink inside the box and clear of its label, so a doub


# ── THE MARKER INVENTORY ──────────────────────────────────
#
# The fundament's rule is that a marked invention says so in its
# module, in the status document AND in a check that fails if the
# marking disappears. The third home is the one that rots: a
# check greps a FILE, and a marking that moves to a file no check
# reads goes on being true and stops being watched. Nothing in
# the tree could see that happen.
#
# So this is the inventory. Every file carrying an HD EXTENSION
# or DEVIATION marking must be listed here with one string that
# has to survive in it. A marking added to a new file fails until
# it is declared; a marking deleted from a declared file fails
# too. It does not replace the per-subject checks above — those
# assert what the marking SAYS — it asserts that no marking is
# unwatched.
#
# smoke_test.py itself is excluded and only it: a check that
# quotes the words it looks for would otherwise have to declare
# itself, and the exclusion is by exact path so a marking in any
# other tool is still caught.
_MARKED = {
    # ADDED 25 September 2026, work order 173 / decision 72: the player's
    # mod folder (HD EXTENSION). Its own check is 006d.
    "core/usermod.py": "HD EXTENSION, work order 173, decision 72",
    "tools/mod_template.py": "HD EXTENSION, work order 173, decision 72",
    # ADDED 15 September 2026, brief 110 Part A / decision 65: the
    # guard that sends no unchosen move order (DEVIATION). Its own
    # check is the galaxy_map icon hit test block.
    "screens/galaxy_map/mapclick.py": "DECISION 65",
    # ADDED 15 September 2026, brief 110 Part A step 2: the HD boxes'
    # layout (DEVIATION) and the fields HD leaves alone (OMISSION),
    # and the status line HD prints regardless of the selection
    # (DEVIATION). Their check is the galaxy_map HD boxes block.
    "screens/galaxy_map/boxdraw.py": "OMISSION (decision 61)",
    "screens/galaxy_map/boxmodel.py": "DEVIATION: the original prints",
    # ADDED 15 September 2026, brief 110 Part B (brief 121): every map
    # line antialiased (HD EXTENSION B1), the wave's step and clock
    # (HD EXTENSION B2), three line kinds left out (OMISSION). Their
    # check is the galaxy_map map-lines block.
    "screens/galaxy_map/maplines.py": "HD EXTENSION — B1",
    "screens/galaxy_map/mapeta.py": "DEVIATION — two locks",
    # ADDED 16 September 2026, work order 123: the dialogs scaled into
    # the frame's opening. Their own check is "GAME menu frame".
    "screens/game_menu/gmframe.py": "HD DEVIATION",
    "screens/game_menu/gmdraw.py": "HD DEVIATION",
    "screens/galaxy_map/renderer.py": "HD EXTENSION B1",
    # ADDED 25 September 2026, work order 169 / decision 71: the Fleets
    # control words in the HUD's button colour (DEVIATION). Its own
    # check is "Fleets in the HUD style" in the fleets group.
    "screens/fleets/fltdraw.py": "DEVIATION (decision 71",
    # ADDED 25 September 2026, work order 170: boxes anchored to the
    # window's edges (HD EXTENSION). Its own check is "galaxy map: no
    # star, name, fleet or wormhole pixel under a HUD block" (011a).
    "core/layout.py": "HD EXTENSION, work order 170",
    # ADDED 25 September 2026, work order 170: the HUD frame colour (HD
    # EXTENSION). Its own checks are the two "hud frame colour" ones in
    # 006b.
    "core/hud/tint.py": "HD EXTENSION (work order 170)",
    "core/hud/art.py": "HD EXTENSION, work order",
    "main.py": "The HUD frame colour (HD EXTENSION, work order 170)",
    "core/helppopup.py": "the panel auto-sizes to its text",
    "core/zoomtables.py": "INSET_DOT_DIM",
    "screens/colony_summary/colonybuild.py": "Buy",
    "screens/colony_summary/colonyempire.py": "decision 44",
    "screens/colony_summary/colonyinset.py": "isotropic",
    "screens/colony_summary/colonyheader.py": "PLATE_HEIGHT_REF",
    "screens/colony_summary/colonylist.py": "identity",
    "screens/colony_summary/colonymoveui.py": "discard",
    "screens/colony_summary/colonyoutput.py": "decision 43",
    # ADDED 13 September 2026, brief 92 / decision 56: the output
    # icons (DEVIATION) and the separator's colour (HD EXTENSION).
    # Their own check is the output-panel marking block.
    "screens/colony_summary/colonyoutputicons.py": "decision 56",
    "tools/make_output_icons.py": "decision 56",
    # ADDED 13 September 2026, brief 97 / decision 58: the planet
    # surface loader. Its own check is the surfaces block.
    "screens/colony_summary/colonysurfaces.py": "decision 58",
    "assets/shared/skins/default/colors.json": "output_separator",
    "screens/colony_summary/colonypick.py": "partial",
    # ADDED 9 September 2026, and it is the inventory doing its
    # job in the other direction: the hover popup's marking was
    # named as living here by BOTH `layout.json`'s
    # `_hd_extension_popup` and `v3_projektstatus.md`, and this
    # file carried none — so the module was absent from the
    # inventory because there was nothing to inventory, and the
    # net could not report a hole it had never been shown.
    "screens/colony_summary/colonypopup.py": "hover popup",
    "screens/colony_summary/colonysort.py": "typography",
    "screens/colony_summary/colonyrows.py": "layout.json",
    # RETARGETED 8 September 2026, in the commit that deleted the
    # F/W/S markers. `colonytrack` was cited on "marker" and
    # layout.json on `_hd_extension_markers`; both named the same
    # removed thing. The live marking in that module is now the
    # drop rect's height, and layout.json's is the hover popup.
    "screens/colony_summary/colonytrack.py": "DEVIATION IN HEIGHT",
    "screens/colony_summary/layout.json": "_hd_extension_popup",
    # WAS `figure_scale` — caught by this check on its first run,
    # which was the whole point of it: the figure step's marking
    # went in with Stage 1 and nothing was reading the file it
    # went into. The step is DERIVED from the row band since
    # 8 September 2026 and that key is gone with the table it
    # duplicated; what this file still carries is the inset's own
    # deviation.
    "screens/colony_summary/layout_reference.json": "THE BOX IS 239 x 189",
    "screens/colony_summary/screen.py": "cancel",

    # ADDED 12 September 2026 with decision 54. The namer carries
    # the seven sort slots' DEVIATION because it is where the
    # reversal shows in code that is not the screen's: `sort_bar`
    # became `sort_<key>` and the naming became an overlap match.
    # Its check is the marking block in the colony_summary section,
    # which names all five homes.
    "tools/frame_holes.py": "sort_<key>",

    # ADDED 12 September 2026 with the fractional figure size —
    # the DEVIATION from decision 28. The loader is where the
    # sourcing rule lives (the step BELOW the size, a mod's own
    # file if it ships one), so the marking is on `FigureSet` and
    # its check is the size block below.
    "screens/colony_summary/colonyfigures.py": "decision 28",

    # ADDED 14 September 2026 with fundament 63, the player-colour
    # presets. Their own check is the "player colours" block: it
    # asserts HD EXTENSION in both docstrings.
    "core/palette.py": "fundament 63",
    "core/playercolors.py": "fundament 63",
    "screens/galaxy_map/floorlift.py": "fundament 63",
    "screens/galaxy_map/screen.py": "OLED floor lift",
    "screens/game_menu/gmorion.py": "fundament 63",
    # ADDED 17 September 2026, work order 126 D: the empty save slot's
    # edit. Its own check is the GAME menu markings block (7).
    "screens/game_menu/gmsave.py": "DEVIATION — an EMPTY slot",
    "screens/game_menu/screen.py": "they have no field",
    "screens/game_menu/layout.json": "orionlayer_rows",

    # ADDED 13 September 2026, brief 101: the list code extracted
    # from the colony modules carries the row fills' HD EXTENSION
    # (decision 57). Its own check is the planets list block, which
    # draws both screens' fills through this module.
    "core/listgrid.py": "decision 57",
    # ADDED 13 September 2026, brief 101: the Planets screen. Its
    # own checks are the planets block (markings, the range gap,
    # the panel, the wheel).
    "screens/planets/layout.json": "HD EXTENSION: panel",
    "screens/planets/planetdraw.py": "HD EXTENSION: panel",
    "screens/planets/screen.py": "_hd_extension_wheel",

    # ADDED 14 September 2026 with fundament 64, the monster values
    # in the Planets panel. The panel carries the HD EXTENSION and
    # the sprite choice's DEVIATION, the generator the panel export,
    # the galaxy map the amoeba/antaran stand-in, zoomtables the
    # export size. Their own checks are the monster panel block.
    "screens/planets/monsterpanel.py": "STAR INDEX % 5",
    "tools/make_ship_icons.py": "one source, no second set of artwork",
    "screens/galaxy_map/ships.py": "AMOEBA and the ANTARAN",

    # ADDED 18 September 2026, work order 130 E: the research select
    # screen. Its own check is the markings block at the end of the
    # research section — it holds the four omissions, the one HD
    # extension and the three deviations, each in the module that
    # performs it.
    "screens/research_select/screen.py": "MARKED, and each held by a smoke check",
    "screens/research_select/panel.py": "SQUEEZES, HD SHRINKS",
    "screens/research_select/native.py": "part of the TECHSEL art",
    # CITATION CHANGED 22 September 2026, work order 165 part A. It was
    # `MOX::_settings.language`, for the RP/FP/PR deviation this file
    # carried while that byte had no verified offset. The byte is in
    # the settings spec now and the suffix follows the game, so the
    # deviation went — and what is left in this file is the title,
    # which the original paints into its TECHSEL art rather than
    # printing (an HD EXTENSION, and the reason it is here at all).
    "screens/research_select/layout.json": "TECHSEL",

    # ADDED 22 September 2026, work order 165 part B: the research
    # panel's geometry became one module for both modes, and the ONE
    # chosen rectangle on those screens — the title's strip, which the
    # original paints into its TECHSEL art rather than printing — moved
    # into it with everything else. Its own check is in the research
    # screen's marking block.
    "core/researchnative.py": "HD EXTENSION",

    # …and the drawing with it. The squeeze/shrink DEVIATION is done
    # here for both modes, and so is the INVENTION that fills a hovered
    # row where the original cycles a palette index. Its own check is
    # in the research screen's marking block.
    "core/researchpanel.py": "DEVIATION",

    # ADDED 22 September 2026, work order 165 part B: CHANGE mode, the
    # engine's own screen 36. Its markings are select mode's minus the
    # science room, which is select mode's own strip — and that
    # difference is asserted, in both directions, in the change-mode
    # check.
    "screens/research_change/screen.py": "DEVIATION",
    "screens/research_change/layout.json": "TECHSEL",

    # ADDED 23 September 2026, work order 166 part B: the research
    # panel's outer frame, cut from the Fleets artwork. Its own check
    # is the frame block — the cut rebuilds byte for byte and the
    # corners scale without stretching.
    "core/researchframe.py": "DEVIATION",

    # ADDED 22 September 2026, work order 165 part C: the two popups
    # the research panel shares. `researchpopups.py` carries Q11, the
    # radio index skew HD does not reproduce; `researchtechlist.py`
    # carries the window's own deviation — chosen page-button size,
    # unextracted art — and the hover INVENTION it shares with
    # `researchpanel.py`. Both are asserted in the list-popup block.
    "core/researchpopups.py": "DEVIATION",
    "core/researchtechlist.py": "DEVIATION",

    # ADDED 19 September 2026, work order 134 C: the Fleets screen.
    # Its own check is the fleets markings block below — four
    # OMISSIONs and one HD EXTENSION, each in the module that
    # performs it.
    # fltrows.py and fltwire.py carry the four OMISSIONs and are
    # NOT listed: this inventory nets HD EXTENSION and DEVIATION
    # only. The omissions have their own assertions in the same
    # block, which is what holds them.
    "screens/fleets/screen.py": "HD EXTENSION",
    "screens/fleets/layout.json": "HD EXTENSION",

    # ADDED 19 September 2026, work order 139 D: the sentence a
    # handing-over HD screen leaves on screen. Its own check is the
    # "a fallback says why" block.
    "core/fallbacknote.py": "HD EXTENSION",

    # ADDED 19 September 2026, work order 142 D1: the integer
    # magnification of the game's own sprites, which decision 28
    # cannot cover because SHIPS.LBX holds one size. Its own check
    # is the "the Fleets screen's own artwork" block.
    "screens/fleets/fltart.py": "HD EXTENSION",

    # ADDED 24 September 2026, work order 167: the Leaders screen. Its
    # own checks are the leaders group (tools/smoke_suite/090c): the
    # layout.json marks, each named in the module that performs it —
    # the drawn inner boxes, the HD font, the sprite scale, the button
    # words, HD's own skill help box.
    "screens/leaders/layout.json": "deviation_inner_boxes_drawn",
    "screens/leaders/screen.py": "inner_boxes_drawn",
    "screens/leaders/ldrdraw.py": "sprite_scale",
    "screens/leaders/ldrright.py": "sprite_scale",
    "screens/leaders/ldrdialog.py": "hd_skill_help",
    "screens/leaders/ldrinput.py": "hd_skill_help",

}
_MARKS = ("HD EXTENSION", "DEVIATION")
_SELF = SUITE_FILES
_found = {}
for _dirpath, _dirnames, _filenames in os.walk(_proj):
    _dirnames[:] = [d for d in _dirnames
                    if d not in ("__pycache__", ".git", ".venv", "venv")]
    for _fn in _filenames:
        if not _fn.endswith((".py", ".json")):
            continue
        _full = os.path.join(_dirpath, _fn)
        _rel = os.path.relpath(_full, _proj)
        if _rel in _SELF:
            continue
        try:
            _text = open(_full, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if any(_m in _text for _m in _MARKS):
            _found[_rel.replace(os.sep, "/")] = _text
_undeclared = sorted(set(_found) - set(_MARKED))
_stale = sorted(set(_MARKED) - set(_found))
assert not _undeclared, (
    f"these files carry an HD EXTENSION or DEVIATION marking that "
    f"no check reads: {_undeclared}. Add the marking's own check, "
    f"then list the file in _MARKED — the inventory is the net, "
    f"not the check")
assert not _stale, (
    f"these files are listed as carrying a marking and no longer "
    f"do: {_stale}. Either the marking was removed, in which case "
    f"the status document says so too, or it moved to a file the "
    f"inventory does not know about")
for _rel, _cite in _MARKED.items():
    assert _cite in _found[_rel], (
        f"{_rel} still carries a marking but no longer says "
        f"{_cite!r} — the marking survived and its subject did not")
# ── THE HEADER WINDOW IS OURS, AND SO IS THE OUTLINE COLOUR ──
# Both markings, all three homes, and the numbers the first one
# rests on. The plate height is the interesting one: it is a
# TRANSCRIBED number that does NOT fit, so the check pins the
# measurement and the window it fails to fit rather than the
# compromise, which is the only way the gap stays visible.
from screens.colony_summary import colonyheader as _chdr
assert _chdr.PLATE_HEIGHT_REF == 66, _chdr.PLATE_HEIGHT_REF
assert _chdr.DIVIDER_REF == 6, _chdr.DIVIDER_REF
_hbox = d.screens["colony_summary"].box_rect("header")
assert _hbox and _hbox[3] < _chdr.PLATE_HEIGHT_REF, (
    f"the header window is {_hbox[3]} ref px and the original's "
    f"plate measures {_chdr.PLATE_HEIGHT_REF} — if the window has "
    f"grown to fit, the deviation is over and the note that "
    f"records it has to go with it")
_hcfg = d.screens["colony_summary"]._data.get("header", {})
for _cite in ("DEVIATION", "44", "60", "96", "66 reference px",
              "panel.thin_border", "recess"):
    assert _cite in _hcfg.get("_deviation_window", ""), (
        f"header._deviation_window no longer carries {_cite!r}")
# THE PLATES TILE THE HEADER EXACTLY, and each heads its own
# column: a heading that is not as wide as the column under it is
# a second copy of the layout (decision 5).
_cs4 = d.screens["colony_summary"]
_cs4_area = pygame.Rect(*_cs4.layout.rect(_cs4.box_rect("list_area")))
_chdr.sync_columns(_cs4)
_cols = _ctk.columns(_cs4_area, _cs4._data.get("list", {}))
assert set(_cols) == {"name", "farmers", "workers", "scientists",
                      "building", "scroll"}, sorted(_cols)
# ── THE DEVIATION TABLE, PER COLUMN ─────────────────────────
# Decision 36's shape: the columns are editable now, so the
# transcription needs a checker rather than a reminder. What the
# original STATES is a RATIO — `COLSUM::Get_Selected_Pop_`
# (colsum.cpp:1006-1024) gives drawn spans 135 : 142 : 134 with
# WORKERS the widest — and not a width, because HD's columns are
# 2.53x their native ones by Data's Stage 1 decision. So the three
# job columns are held to the ratio, and every column's deviation
# is REPORTED into the status; red only where one is unmarked.
_nat = _zt2.NATIVE_JOB_COLUMNS
_nat_sum = sum(_nat.values())
_job_sum = sum(_cols[_k][1] for _k in _nat)
_dev = {}
for _k, _n in _nat.items():
    _want = _job_sum * _n / _nat_sum
    _dev[_k] = (_cols[_k][1] - _want) / _want
for _k, _v in _dev.items():
    assert abs(_v) < 0.01, (
        f"the {_k} column is {_v*100:+.1f} % off the transcribed "
        f"ratio {_nat['farmers']}:{_nat['workers']}:"
        f"{_nat['scientists']} (colsum.cpp:1006-1024). A column may "
        f"be dragged, and a drag past one per cent is a deviation "
        f"that has to be marked before it is kept")
# AND THE THREE THAT ARE NOT TRANSCRIBED AT ALL must each be
# named where the deviation is recorded. `col_name` and
# `col_building` carry reasons already; `col_scroll` has no
# native counterpart to be a share of.
_dev_note = _cs4._data.get("list", {}).get("_deviation_note", "")
assert "DEVIATION" in _dev_note or "deviat" in _dev_note.lower(), (
    "list._deviation_note does not record what deviates")
for _k in ("col_name", "col_building"):
    assert _k in _dev_note, (
        f"{_k} deviates from a proportional share and "
        f"list._deviation_note does not name it")
_status_txt = open(os.path.join(_proj, "v3_projektstatus.md"),
                   encoding="utf-8").read()
assert "135 : 142 : 134" in _status_txt or "135:142:134" in _status_txt, (
    "the status document does not carry the transcribed column "
    "ratio, which is where the deviation table is reported")
# ── AND THE TABLE IS HELD TO boxes.json ─────────────────────
# Every width in that table is a number somebody typed into a
# document, and it went stale within the hour on 9 September
# 2026: `col_building` and `col_scroll` changed in the commit
# that transcribed the scroll column, and the table still said
# 315 and 35 with the scroll row still claiming "no native
# counterpart" for a column that had just acquired a source.
#
# A hand-copied number without a checker is this project's oldest
# recurring fault (decision 36's rule, the engine version, the
# check count in two documents). The table is the third instrument
# against it. Asserted per ROW rather than as a blob, so the
# failure names the column that drifted.
_dev_rows = dict(re.findall(
    r"^\|\s*`(col_\w+)`\s*\|\s*(\d+)\s*\|", _status_txt, re.M))
_dev_boxes = {_n: _r[2] for _n, _r in colony_rects().items()
              if _n.startswith("col_")}
assert set(_dev_rows) == set(_dev_boxes), (
    f"the deviation table lists {sorted(_dev_rows)} and boxes.json "
    f"has {sorted(_dev_boxes)} — every column is reported or the "
    f"table is not the report it says it is")
for _dc, _dw in sorted(_dev_boxes.items()):
    assert int(_dev_rows[_dc]) == _dw, (
        f"v3_projektstatus.md's deviation table says {_dc} is "
        f"{_dev_rows[_dc]} reference px and boxes.json says {_dw}. "
        f"The table is a hand-copied number and this is its "
        f"checker; update it in the commit that moves the box")
# ── ONE RECT SOURCE: the heading reads the column ───────────
_hpx = pygame.Rect(*_cs4.layout.rect(_hbox))
_plates = dict(_chdr.plate_rects(_hpx, _cols, _cs4.layout.scale))
assert set(_plates) == set(_cols), sorted(_plates)
for _k, (_cx, _cw) in _cols.items():
    _pr = _plates[_k]
    assert _cx <= _pr.left and _pr.right <= _cx + _cw, (
        f"the {_k} plate ({_pr.left}..{_pr.right}) is not inside "
        f"its column ({_cx}..{_cx + _cw}) — the heading and the "
        f"cells must read one rect (decision 5)")
_hdr_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                             "colonyheader.py"), encoding="utf-8").read()
assert "border_radius" not in _hdr_src, (
    "colonyheader draws its own rounded rect again; the plate is "
    "StyleRenderer.draw_plate's (decision 51)")
# ── THE EMPIRE READOUTS SURVIVE AN UNTUNED RESOLUTION ──
#
# Rendered at all three and read back as INK, because the fault
# this replaces was invisible to any check that derived the
# expected size from the renderer's own expression. `colonyempire`
# took `box_font_scale`, which multiplies by `win_h / 1080`, and
# then went through `Layout.font_size`, which multiplies by the
# window scale again: 1.0 at 1080p, 1.78 at 1440p and **4.0 at
# 2160p against an intended 2.0**. The colony summary carries no
# tuned `font_scale` on any box, so nothing cancelled it and the
# six values came out at twice their size at 4K and collided with
# their labels. Same family as the help popup's, which
# `screenhelp` had already solved privately — see
# `ScreenBase.box_font_scale_stored`.
#
# Two properties, and the second is the one that fails on a double
# scale: the value's ink stays inside the box, and it stays clear
# of its own label.
from screens.colony_summary import colonyempire as _emp_chk
_emp_seen = 0
for _W, _H in (("1920", 1080), ("2560", 1440), ("3840", 2160)):
    _W = int(_W)
    _ea, _es = _pv.build_screen(_W, _H)
    _ea.dispatcher.switch_to("colony_summary")
    _esc = _ea.dispatcher.active
    _esc.enter(None)
    _esc.update(_pv._Snapshot(_pv.COLONIES))
    _ebox = _esc.box_rect("empire_stats")
    assert _ebox, "no empire_stats box"
    _er = pygame.Rect(*_ea.layout.rect(_ebox))
    _esurf = pygame.Surface((_W, _H))
    _esurf.fill((0, 0, 0))
    _esc.render(_esurf)
    _epx = pygame.surfarray.array3d(
        _esurf.subsurface(_er)).transpose(1, 0, 2).astype(int)
    _lab_rgb = _np.array(_emp_chk.LABEL_COLOR[:3], dtype=int)
    _val_rgb = _np.array(_emp_chk.VALUE_COLOR[:3], dtype=int)
    # A TIGHT match on the glyph CORE. The two colours are only
    # 248 apart summed — (140,155,190) against (220,228,245) — so
    # a loose threshold makes each mask catch the other's
    # antialiasing and the separation test compares noise.
    _is_lab = (_np.abs(_epx - _lab_rgb).sum(axis=2) < 12)
    _is_val = (_np.abs(_epx - _val_rgb).sum(axis=2) < 12)
    assert _is_lab.any() and _is_val.any(), (
        f"{_W}x{_H}: the empire panel drew no labels or no values, "
        f"so this check asserts nothing")
    # INSIDE THE BOX: no ink on the outermost column or row, which
    # is what a value too big to fit produces first.
    for _side, _band in (("left", _is_val[:, :1]),
                         ("right", _is_val[:, -1:]),
                         ("top", _is_val[:1, :]),
                         ("bottom", _is_val[-1:, :])):
        assert not _band.any(), (
            f"{_W}x{_H}: value ink touches the {_side} edge of "
            f"empire_stats — it is too large for its box")
    # CLEAR OF THE LABEL: on every row that carries both, the
    # rightmost label pixel is left of the leftmost value pixel.
    _rows_both = [_y for _y in range(_er.h)
                  if _is_lab[_y].any() and _is_val[_y].any()]
    assert len(_rows_both) >= 6, (
        f"{_W}x{_H}: only {len(_rows_both)} rows carry both a "
        f"label and a value; the panel has six")
    for _y in _rows_both:
        _lx = int(_np.where(_is_lab[_y])[0].max())
        _vx = int(_np.where(_is_val[_y])[0].min())
        assert _lx < _vx, (
            f"{_W}x{_H}: on row y={_y} the label reaches x={_lx} "
            f"and the value starts at x={_vx} — they collide, "
            f"which is what a doubled font scale does first")
    _emp_seen += 1
assert _emp_seen == 3
ok("empire readouts at three resolutions (value ink inside the box "
   "and clear of its label, so a doubled font scale fails here)")
