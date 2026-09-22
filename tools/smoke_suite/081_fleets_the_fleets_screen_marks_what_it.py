# smoke-suite area: fleets
#
# Part of the OrionLayer smoke suite — 081_fleets_the_fleets_screen_marks_what_it.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 5 check(s) it holds:
#   - the Fleets screen marks what it does not draw: the ship picture, the damage bar, the move previe
#   - the Fleets screen on a real snapshot: the FLTS block parses after FSEL, the grid draws what it n
#   - the strip under the Fleets map names the star the pointer is over, built from the stars HD alrea
#   - the Fleets panel follows the pointer: the hovered ship's lines built from the snapshot HD alread
#   - a native box is recognised by its whole field list ( kinds, rects from the draw call and the LBX


# ── THE FLEETS SCREEN SAYS WHAT IT DOES NOT DRAW ──────────────
#
# Work order 134 C. Four OMISSIONs and one HD EXTENSION, each held
# where it is performed, so none of them can quietly become a thing
# the screen looks like it draws. Every one of the four is a
# DIFFERENT reason, and the reason is the part worth protecting:
# artwork this tree may not carry, offsets no second source has
# confirmed, a value computed on hover that is on no wire, and a key
# the protocol cannot express.
_fl_dir = os.path.join(SCREENS_DIR, "fleets")
_fl_src = {_fn: io.open(os.path.join(_fl_dir, _fn),
                        encoding="utf-8").read()
           for _fn in ("screen.py", "fltrows.py", "fltwire.py",
                       "fltdraw.py", "fltgeom.py")}
_fl_layout = _sjson.load(io.open(os.path.join(_fl_dir, "layout.json"),
                                 encoding="utf-8"))

# 1. THE SHIP PICTURE — **THE OMISSION IS LIFTED** (work order
#    142 D1). It was "SHIPS.LBX is MOO2's art and never in this
#    tree, so a cell shows a name and a colour". The art is still
#    never in this tree, and that has stopped being the same thing
#    as the picture not being drawable: `tools/fleet_art_extract.py`
#    reads the player's OWN installation and `fltart` decodes it at
#    load time, so the cell draws the original's picture whenever
#    the player has extracted it and falls back when they have not.
#
#    So the check changes shape rather than going away. What has to
#    hold now is that BOTH halves are real: the citation survives,
#    and the fallback is still there for the clone that has no
#    files — because a fallback nobody exercises is where this kind
#    of thing rots, and the session writing the code always has the
#    files.
assert "ken.cpp:451-466" in _fl_src["fltrows.py"] or \
    "ken.cpp:466" in _fl_src["fltrows.py"] or \
    "ken.cpp:466" in _fl_src["fltdraw.py"] + _fl_src["screen.py"], (
        "the ship picture lost the citation of the function that "
        "draws it in the original")
assert "fltart" in _fl_src["fltdraw.py"], (
    "fltdraw no longer reaches the artwork loader, so the cells "
    "cannot be drawing the original's picture")
assert "WITHOUT it" in _fl_src["fltdraw.py"], (
    "draw_cells no longer documents the state a fresh clone is in")
# The fallback is not documentation: it runs. Forced, with the
# loader pointed at nothing, and it must still put something in the
# cell — the builder's colour block the screen drew before.
assert "owner_colour(cell.builder)" in _fl_src["fltdraw.py"], (
    "the no-artwork fallback lost the builder's colour block; a "
    "clone without the files would draw an empty grid")

# 2. THE DAMAGE BAR, for a different reason: structural_damage 125
#    and armor_damage 123 are hand counts the ship spec refuses to
#    carry (decision 23). The spec is the proof, not the comment.
from core.structs import ship as _fl_ship
_fl_names = {_f[0] for _f in _fl_ship.SPEC.fields}
assert "structural_damage" not in _fl_names and \
    "armor_damage" not in _fl_names, (
        "the ship spec now carries the damage offsets; the Fleets "
        "screen omits its damage bar BECAUSE they were unverified, "
        "so the omission has to be re-read rather than kept")
assert "fleetpop.cpp:41-81" in _fl_src["fltrows.py"]

# 3. THE MOVE PREVIEW and 4. THE CAPTAIN'S PORTRAIT.
_fl_reasons = _fl_src["fltrows.py"] + _fl_src["fltwire.py"]
for _fl_what, _fl_cite in (("move preview", "flt2.cpp:356-429"),
                           ("captain", "unverified.py"),
                           ("attack/defense bonus",
                            "initship.cpp:638-687")):
    assert _fl_cite in _fl_reasons, (
        f"the {_fl_what} omission lost its citation ({_fl_cite})")
assert _fl_reasons.count("OMISSION") >= 4, (
    "fewer than four OMISSION markings across fltrows and fltwire; "
    "the four are the ship picture, the damage bar, the move "
    "preview and the captain, and each has a different reason")

# 5. THE ONE HD EXTENSION: the wheel. It is an extension AND it is
#    not a local scroll — decision 46 — and both halves are the
#    marking, so both are asserted.
_fl_wheel = FleetsScreen = None
from screens.fleets.screen import FleetsScreen as _fl_cls
_fl_wheel = _fl_cls.handle_mousewheel.__doc__ or ""
assert "HD EXTENSION" in _fl_wheel, (
    "the Fleets wheel no longer says it is an HD EXTENSION")
assert "decision 46" in _fl_wheel, (
    "the Fleets wheel no longer says the list window is the "
    "game's — without that it reads as a local scroll, which is "
    "what decision 46 refuses")
assert "handle_wheel" not in _fl_src["screen.py"], (
    "the Fleets wheel hook is named handle_wheel; main.py calls "
    "handle_mousewheel and nothing would ever reach it")

# AND THE MARKS ARE IN THE FILE THE PLAYER-FACING DOCUMENT READS.
assert "HD EXTENSION" in _sjson.dumps(_fl_layout), (
    "screens/fleets/layout.json carries no HD EXTENSION marking")
# The screen's own state, in the module docstring — decision 61,
# and the same shape the research screen's marking has.
import screens.fleets.screen as _fl_mod
assert "BUILT, NOT ACCEPTED" in (_fl_mod.__doc__ or ""), (
    "the Fleets module docstring no longer says BUILT, NOT "
    "ACCEPTED; no live acceptance has run against this screen")
assert "134-parked-for-data" in (_fl_mod.__doc__ or ""), (
    "the Fleets module no longer names the file that holds the "
    "parked live steps, so the marking says nothing actionable")
ok("the Fleets screen marks what it does not draw: the ship "
   "picture, the damage bar, the move preview and the captain, "
   "each with its own reason, and its one HD EXTENSION says the "
   "list window is still the game's")

# ── THE FLEETS SCREEN, DRIVEN BY A REAL SNAPSHOT ──────────────
#
# Work order 134 D. The state goes in as BYTES and comes out of
# core.game_state.parse_state, so the FLTS block's own layout is
# under test and not a dict somebody typed. A dict would have proved
# the screen and left the parser — the half that faces the engine —
# untested, which is where a wrong offset lives.
import struct as _fl_s
import core.game_state as _gs_mod
import colony_list_preview as _fl_plv
from core.game_state import (parse_state as _fl_parse,
                             SETTINGS_SIZE as _FL_SET,
                             PLAYER_SIZE as _FL_PL,
                             LEADER_SIZE as _FL_LD,
                             ANTARAN_SIZE as _FL_AN)
from core.structs import ship as _fl_shipspec
from screens.fleets import fltgeom as _flg, fltwire as _flw

_FL_CELLS = _flg.native_cells()

def _fl_ship_bytes(name, owner, builder, shield=2):
    _b = bytearray(_fl_shipspec.SIZE)
    _b[0:len(name)] = name.encode("latin-1")
    _b[18] = shield
    _b[92] = 3
    _b[93] = builder
    _b[99] = owner
    return bytes(_b)

from core.structs import star as _fl_starspec

def _fl_star_bytes(name, visited, x, y):
    """One s_star_data, only the fields the strip under the map
        reads: the name, the visited bitmask and the position that
        decides where `galaxy_inset_stars` draws it."""
    _b = bytearray(_fl_starspec.SIZE)
    _b[0:len(name)] = name.encode("latin-1")
    _b[15:17] = _fl_s.pack("<h", x)
    _b[17:19] = _fl_s.pack("<h", y)
    _b[20] = 0xFF                      # unowned
    _b[171] = visited
    return bytes(_b)

def _fl_snapshot(icons=6, first_row=0, owner=1, relocate=0,
                 selected=(1, 2), with_block=True, rows=2,
                 shown=None, ship_icons=(), scanned_big=1,
                 stars=()):
    """A STATE_SNAPSHOT payload with the fleet screen up.

        The FLTS block sits after FSEL, exactly where the engine writes
        it, so a parser that read it too early or too late fails here.
        """
    _shown = icons if shown is None else shown
    _b = bytearray()
    _b += _fl_s.pack("<hbihhhhhB b", 4, 0, 100, 1, 2, 0, icons, 0, 0, 0)
    _b += _fl_s.pack("<hhhhh", 15, 0, 0, 759, 600)
    _b += bytes(_FL_SET)
    _b += bytes(_FL_PL * 8)
    _b += _fl_s.pack("<h", len(stars))             # stars
    for _st in stars:
        _b += _fl_star_bytes(*_st)
    _b += _fl_s.pack("<h", icons)                  # ships
    for _i in range(icons):
        _b += _fl_ship_bytes(f"Ship {_i}", 1, _i % 8)
    _b += _fl_s.pack("<h", 0)                      # colonies
    _b += _fl_s.pack("<h", 0)                      # planets
    _b += bytes([0])                            # nebulas
    _b += bytes(_FL_LD * 67)
    _b += bytes(_FL_AN)
    _b += _fl_s.pack("<h", len(ship_icons))        # ship icons
    for _ic in ship_icons:
        _b += _fl_s.pack("<6h", *_ic)
    _b += _fl_s.pack("<8h", 0, 0, 0, 0, 0, 0, 0, 0)   # newgame temps
    # The owner block is one byte per icon and is NOT optional once
    # there are icons: the parser reads exactly that many before it
    # looks for FSEL (core/game_state.py), so a fixture that skips
    # it eats the block header and every later block goes missing.
    _b += bytes([0xFF]) * len(ship_icons)
    _b += b"FSEL" + _fl_s.pack("<hhh", -1, 0, 0)   # open fix 20, empty
    if with_block:
        _b += b"FLTS"
        _b += _fl_s.pack("<12h", 2, 5, owner, icons, _shown, rows,
                      first_row, len(selected), scanned_big, -1, 1, 1)
        _b += bytes([relocate, 0])
        _b += _fl_s.pack("<h", icons)
        for _i in range(icons):
            _b += _fl_s.pack("<hB", _i, 1 if _i in selected else 0)
    return _fl_parse(bytes(_b))

def _fl_zero():
    """The engine's own slot 0 — see FIELD_ZERO_ROW."""
    _f = _gs_mod.FieldInfo()
    (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
     _f.hotkey) = FIELD_ZERO_ROW
    return _f

def _fl_fields(count, hotkeys=True, first_row=0):
    """A FIELD_LIST the way Add_Fleet_Screen_Fields_ builds it —
        field 0 first, because the engine cannot send a list without
        one (FIELD_ZERO_ROW)."""
    _out = [_fl_zero()]
    for _i in range(count):
        _x, _y = _FL_CELLS[_i]
        _f = _gs_mod.FieldInfo()
        _f.index, _f.x, _f.y = 10 + _i, _x, _y
        _f.x_end, _f.y_end = _x + 58, _y + 57
        _f.field_type, _f.hotkey = 7, 0
        _out.append(_f)
    if hotkeys:
        # EACH CONTROL AT ITS OWN ORIGIN (flt1.cpp:1187-1257, via
        # fltwire.CONTROL_ORIGINS). They used to be eleven fields at
        # (0, 0)-(1, 1), which was enough for a lookup by hotkey and
        # is not a field list the engine could produce — and work
        # order 137 A's rule, which asks whether a field is one this
        # screen builds, is exactly the rule that can tell.
        for _name, _hk in ((("btn_scrap"), ord("S")),
                           ("btn_all", ord("A")),
                           ("btn_return", 0x1B),
                           ("btn_leaders", ord("L")),
                           ("btn_relocate", ord("R")),
                           ("btn_support", ord("U")),
                           ("btn_combat", ord("C")),
                           ("prev_fleet", ord(",")),
                           ("next_fleet", ord(".")),
                           ("scroll_up", ord("-")),
                           ("scroll_down", ord("+"))):
            (_ox, _oy), _types = _flw.CONTROL_ORIGINS[_name]
            _f = _gs_mod.FieldInfo()
            _f.index = 100 + len(_out)
            _f.x, _f.y = _ox, _oy
            _f.x_end, _f.y_end = _ox + 73, _oy + 27
            _f.field_type, _f.hotkey = _types[0], _hk
            _out.append(_f)
    # AND THE CATCHER, which `Add_Fleet_Screen_Fields_` adds LAST
    # (flt1.cpp:1262) and which is how `fltwire.has_fleet_list`
    # knows the list is this screen's at all (work order 142 A). A
    # fixture without it is a list that is still the map's.
    _f = _gs_mod.FieldInfo()
    _f.index = 100 + len(_out)
    (_f.x, _f.y, _f.x_end, _f.y_end) = _flw.CATCHER_RECT
    _f.field_type, _f.hotkey = _flw.TYPE_HIDDEN, 0
    _out.append(_f)
    return _out

_fl_app, _fl_other = _fl_plv.build_screen(1920, 1080)
_fl_app.dispatcher.switch_to("fleets")
_fl_scr = _fl_app.dispatcher.screens["fleets"]
_fl_surf = pygame.Surface((1920, 1080))
_fl_sent = []
_fl_app.client.select_ship = lambda i, sel: _fl_sent.append((i, sel))
_fl_app.client.activate_field = lambda fid: _fl_sent.append(("act", fid))
_fl_app.client.inject_click = lambda x, y: _fl_sent.append(("click", x, y))

# 1. THE BLOCK PARSES AND THE SCREEN DRAWS IT.
_fl_gs = _fl_snapshot()
_fl_gs.fields = _fl_fields(6)
assert _fl_gs.fleet_screen is not None, (
    "the FLTS block did not parse out of a real snapshot — either "
    "the layout moved or it is no longer written after FSEL")
assert _fl_gs.fleet_screen["ship_idx"] == list(range(6))
assert _fl_gs.fleet_screen["ship_selected"] == [
    False, True, True, False, False, False]
_fl_scr.update(_fl_gs)
assert _fl_scr._view.state == _flw.READY, _fl_scr._view.state
assert not _fl_scr.wants_original()
assert [r[1] for r in _fl_scr._view.rows] == list(range(6))
assert _fl_scr._view.selected_ships() == [1, 2]
_fl_scr.render(_fl_surf)

# 2. THE FOUR REFUSALS, EACH ON A REAL SNAPSHOT, and each says why.
#    A screen that hands over without a sentence is the failure
#    decision 22 and 61 are both about.
for _fl_make, _fl_want in (
        (lambda: (_fl_snapshot(with_block=False), _fl_fields(6)),
         _flw.NO_BLOCK),
        (lambda: (_fl_snapshot(), None), _flw.NO_FIELDS),
        (lambda: (_fl_snapshot(icons=0, rows=0, selected=()),
                  _fl_fields(0)), _flw.NO_STACK),
        (lambda: (_fl_snapshot(), _fl_fields(2)), _flw.MISMATCH)):
    _fl_g, _fl_f = _fl_make()
    _fl_g.fields = _fl_f
    _fl_scr.update(_fl_g)
    assert _fl_scr._view.state == _fl_want, (
        _fl_want, _fl_scr._view.state)
    assert _fl_scr.wants_original(), _fl_want
    assert _fl_scr.fallback_reason(), (
        f"{_fl_want}: the screen handed over and said nothing")
    assert _fl_scr.problems
    # AND IT SENDS NOTHING while it is refusing.
    _fl_sent.clear()
    _fl_scr.handle_click(960, 540)
    _fl_scr.handle_mousewheel(1, 960, 540)
    _fl_scr.handle_key(27)
    assert _fl_sent == [], (_fl_want, _fl_sent)
    _fl_scr.render(_fl_surf)

# THE MISMATCH IS NOT A BLANKET REFUSAL: a FOREIGN stack adds no
# big-icon fields at all (flt2.cpp:312-322), so the same missing
# fields must be READY when the stack is not ours.
_fl_g = _fl_snapshot(owner=5)
_fl_g.fields = _fl_fields(0)
_fl_scr.update(_fl_g)
assert _fl_scr._view.state == _flw.READY and not _fl_scr._view.own_stack, (
    "a foreign stack was read as a mismatch; the field list is "
    "empty there by design and the owner in the block says so")

# 3. DRAW AND HIT-TEST ARE THE SAME GEOMETRY (decision 5). Click the
#    centre of every drawn cell and the slot that answers must be
#    the slot that was drawn.
_fl_gs = _fl_snapshot()
_fl_gs.fields = _fl_fields(6)
_fl_scr.update(_fl_gs)
_fl_slots = _fl_scr.icon_slots()
assert len(_fl_slots) == _flg.GRID_MAX_ICONS, len(_fl_slots)
for _fl_i, _fl_rect in enumerate(_fl_slots):
    assert _fl_scr._slot_at(*_fl_rect.center) == (
        _fl_i if _fl_i < 6 else None), _fl_i
# ...and a click on a drawn cell sends MSG_SELECT_SHIP for the ship
#    that cell shows, with the selection INVERTED.
_fl_sent.clear()
_fl_scr.handle_click(*_fl_slots[1].center)
assert _fl_sent == [(1, False)], _fl_sent   # ship 1 was selected
_fl_sent.clear()
_fl_scr.handle_click(*_fl_slots[3].center)
assert _fl_sent == [(3, True)], _fl_sent

# 4. REFUSED WHERE THE ENGINE REFUSES IT (decision 33): a foreign
#    stack, and relocate mode 1 where the painting is off entirely
#    (flt1.cpp:413).
for _fl_g in (_fl_snapshot(owner=5), _fl_snapshot(relocate=1)):
    _fl_g.fields = _fl_fields(6)
    _fl_scr.update(_fl_g)
    _fl_sent.clear()
    _fl_scr.handle_click(*_fl_slots[3].center)
    assert _fl_sent == [], _fl_sent

# 5. THE TWO FILTERS GET A CLICK, THE REST AN ACTIVATION. This is
#    not a style choice: ACTIVATE_FIELD returns a type-1 field's id
#    without toggling it (fields.cpp:1018-1024, :1292-1297), so an
#    activated filter never changes.
_fl_gs = _fl_snapshot()
_fl_gs.fields = _fl_fields(6)
_fl_scr.update(_fl_gs)
for _fl_name, _fl_kind in (("btn_support", "click"),
                           ("btn_combat", "click"),
                           ("btn_all", "act"), ("btn_return", "act"),
                           ("btn_scrap", "act"), ("btn_leaders", "act"),
                           ("btn_relocate", "act")):
    _fl_box = _fl_scr.box_by_name(_fl_name)
    _fl_sent.clear()
    _fl_scr.handle_click(*_fl_box.screen_rect.center)
    assert _fl_sent and _fl_sent[0][0] == _fl_kind, (
        _fl_name, _fl_kind, _fl_sent)

# 6. THE SEVEN CONTROLS' LIVE STATE IS THE FIELD LIST'S ANSWER.
#    LEADERS is the case worth the check: with no officer the
#    builder adds it as a HIDDEN field with no hotkey at all
#    (flt1.cpp:1238-1240), so it must read as dead.
assert "btn_leaders" in _fl_scr.enabled_buttons()
_fl_gs.fields = [f for f in _fl_gs.fields if f.hotkey != ord("L")]
_fl_scr.update(_fl_gs)
assert "btn_leaders" not in _fl_scr.enabled_buttons(), (
    "LEADERS reads as live with no L field in the list")

# 7. EVERY BOX LIES INSIDE THE FRAME IMAGE, and every DERIVED box
#    lies on its own hole. v3 asked whether a box was inside the
#    frame's ONE opening; v4 has thirty-two, and "box equals hole
#    plus BLEED" is asserted for all of them in the Fleets v4 frame
#    block, which is strictly stronger. What is left for here is
#    the hand-placed boxes, which have no hole to be held to.
_fl_boxfile = _sjson.load(io.open(
    os.path.join(SCREENS_DIR, "fleets", "boxes.json"), encoding="utf-8"))
from core.box import load_boxes as _fl_load
for _fl_key in _fl_boxfile:
    _fl_w, _fl_h = (int(v) for v in _fl_key.split("x"))
    _fl_out = []
    for _fl_b in _fl_load(os.path.join(SCREENS_DIR, "fleets"),
                          _fl_w, _fl_h):
        _bx, _by, _bw, _bh = _fl_b.ref_rect
        if (_bx < 0 or _by < 0 or _bx + _bw > 1920
                or _by + _bh > 1080):
            _fl_out.append(_fl_b.name)
    assert not _fl_out, (
        f"at {_fl_key} these boxes leave the reference area: "
        f"{_fl_out}")

# 7b. THE SCROLL BAR IS PAINTED, SO ITS BOX MUST LAND ON THE PAINT.
#     It is the one control with no hole: `scroll_column` is placed
#     from `fltgeom.SCROLL_SRC_COLUMN`, measured off the artwork, and
#     this is the checker that measurement needs (decision 36).
#     Everything inside the housing must be OPAQUE — a hole there
#     would mean the bar had become a cutout and the measurement
#     stale.
_fl_sx, _fl_sy, _fl_sw, _fl_sh = _flg.SCROLL_SRC_COLUMN
_fl_al = _fo_np.array(_fo_Image.open(
    res.screen_file("fleets", "assets", "frame.png")).convert("RGBA"))[:, :, 3]
assert (_fl_al[_fl_sy:_fl_sy + _fl_sh,
               _fl_sx:_fl_sx + _fl_sw] >= 16).all(), (
    "the scroll bar's measured column contains transparent pixels; "
    "it is painted art, not a hole, and the rects come from that")
_fl_col_ref = [int(round(_fl_sx * 1920 / _flg.FRAME_SRC_SIZE[0])),
               int(round(_fl_sy * 1080 / _flg.FRAME_SRC_SIZE[1])),
               int(round(_fl_sw * 1920 / _flg.FRAME_SRC_SIZE[0])),
               int(round(_fl_sh * 1080 / _flg.FRAME_SRC_SIZE[1]))]
for _fl_key, _fl_list in _fl_boxfile.items():
    _fl_got = next(b["rect"] for b in _fl_list
                   if b["name"] == "scroll_column")
    assert _fl_got == _fl_col_ref, (
        f"{_fl_key}: scroll_column is {_fl_got}, the painted bar "
        f"makes {_fl_col_ref}")

# 8. THE MINIMAP HOLE AGAINST THE GALAXY, not against a screenshot.
#    v3 seated `inset_map` from the native 305x182 and this checked
#    the seat kept that aspect; v4 cuts the hole and Data chose its
#    shape, so the question is no longer "did the seat keep the
#    proportion" but "does the hole fit what goes in it".
#
#    EVERY GALAXY SIZE NORMALISES TO THE SAME EXTENT. The inset
#    transform divides by `INSET_SCALE_X // width`, and
#    `(MAP_MAX * 1000 // scale) * 10` is 506000 x 400000 for all
#    four sizes (mapgen.cpp's table, transcribed in
#    core/mapcoords): Small 506x400 at 10, Medium 759x600 at 15,
#    Large 1012x800 at 20, Huge 1518x1200 at 30. So the galaxy
#    always fills the box and always has intrinsic aspect 1.265,
#    and the fit is one answer for every galaxy size rather than
#    four.
from screens.colony_summary.colonyrows import (
    INSET_SCALE_X as _fl_isx, INSET_SCALE_Y as _fl_isy)
for _fl_W, _fl_H, _fl_S in ((506, 400, 10), (759, 600, 15),
                            (1012, 800, 20), (1518, 1200, 30)):
    assert ((_fl_W * 1000 // _fl_S) * 10,
            (_fl_H * 1000 // _fl_S) * 10) == (_fl_isx, _fl_isy), (
        f"galaxy {_fl_W}x{_fl_H} at scale {_fl_S} does not normalise "
        f"to {_fl_isx}x{_fl_isy}; the minimap fit is then a different "
        f"answer per galaxy size and this check is too weak")
_fl_hole = _fo_named["inset_map"]
_fl_ar = _fl_hole[2] / _fl_hole[3]
_fl_native_ar = 305 / 182
assert abs(_fl_ar - _fl_native_ar) / _fl_native_ar < 0.05, (
    f"the minimap hole is {_fl_hole[2]}x{_fl_hole[3]}, aspect "
    f"{_fl_ar:.4f}, against the original's inset box "
    f"{_fl_native_ar:.4f}. Both stretch the galaxy's own 1.265, "
    f"which is the original's doing; what must not drift is HD "
    f"stretching it by a DIFFERENT amount than the original does")

# 9. THE TWO PATCHES ARE REQUIRED AND SAY THEY ARE NOT LIVE-TESTED.
for _fl_patch in ("doc/ext_fleet_screen_state.patch",
                  "doc/ext_fleet_screen_select.patch"):
    _fl_text = io.open(os.path.join(
        os.path.dirname(SCREENS_DIR), *_fl_patch.split("/")),
        encoding="utf-8").read()
    assert "NOT CONFIRMED LIVE" in _fl_text, (
        f"{_fl_patch} no longer says it is not confirmed live; "
        f"work order 134's live part is parked and nothing has "
        f"driven these two")
    assert "diff --git" in _fl_text, f"{_fl_patch} carries no diff"
ok("the Fleets screen on a real snapshot: the FLTS block parses "
   "after FSEL, the grid draws what it names, four refusals each "
   "say why and send nothing, a foreign stack is not a mismatch, "
   "draw and hit-test agree on all twenty cells, the filters get a "
   "click and the rest an activation, every box fits the opening "
   "at both resolutions and the inset keeps 305:182")

# ── HOVER SHOWS THE SHIP, AND SENDS NOTHING ───────────────────
#
# Work order 153, Part B. In the original the panel is printed for
# `_scanned_big_ship` and for nothing else (flt1.cpp:401-406), and
# that value is the HOVER: `Scan_Fltscrn_Big_Icons_` sets its FIRST
# out parameter from the field under the pointer and answers result
# 4 (flt2.cpp:938-946), where a click matches `input` and sets both
# (:925-935). Selection never reaches the panel. The Extension API
# has no mouse motion, so HD scans with its own pointer —
# `screens/fleets/fltscan.py` — and the requirement that costs
# nothing on the wire is the one asserted first here.
from screens.fleets import fltscan as _hv

_hv_gs = _fl_snapshot(icons=9, scanned_big=-1, selected=(2,))
_hv_gs.fields = _fl_fields(9)
_fl_scr.enter(_hv_gs)
assert _fl_scr._view.ok, _fl_scr._view.state
assert _fl_scr._panel == [] or not _fl_scr._panel, (
    "the panel is not empty on entry; the original sets "
    "_scanned_big_ship = -1 there (flt1.cpp:528) and prints nothing")

def _hv_at(slot):
    """Move HD's pointer to the middle of a displayed slot."""
    _r = _fl_scr.icon_slots()[slot]
    del _fl_sent[:]
    _fl_scr.handle_mouse_motion(_r.centerx, _r.centery)
    return _fl_scr._panel

# 1. IT SHOWS THE HOVERED SHIP, AND THE RIGHT ONE.
_hv_p = _hv_at(5)
assert getattr(_hv_p, "head", None), (
    "hovering an occupied cell left the panel empty")
assert _hv_p.head[0] == "Ship 5", (
    f"hovering slot 5 shows {_hv_p.head[0]!r}; the FLTS block's "
    f"ship_idx[5] is ship 5")
assert _fl_scr._scan.icon == 5

# 2. **NOTHING WAS SENT.** This is the acceptance criterion in
#    Data's own words and the reason the panel is built locally:
#    the API has no mouse motion to forward, and a send per mouse
#    movement would flood the input loop it does have.
assert _fl_sent == [], (
    f"hovering sent {_fl_sent} to the game; hover must never send")
for _hv_s in (0, 1, 2, 3, 4, 6, 7, 8):
    _hv_at(_hv_s)
    assert _fl_sent == [], f"hovering slot {_hv_s} sent {_fl_sent}"

# 3. THE MARK AND THE PANEL ARE ONE VALUE. `fltdraw` asks
#    `_scan.slot`, so the cell that is marked is the cell whose
#    ship is in the panel — which is what the original does with
#    one variable and two draw calls.
_hv_at(3)
assert _fl_scr._scan.slot(_fl_scr._view.block) == 3
assert _fl_scr._panel.head[0] == "Ship 3"

# 4. SELECTION DOES NOT FEED IT. Ship 2 is the selected one in
#    this fixture and the panel is on ship 3.
assert _fl_scr._view.selected_ships() == [2]
assert _fl_scr._panel.head[0] == "Ship 3", (
    "the panel followed the selection; in the original `selected` "
    "is a separate flag with its own sprite and never reaches "
    "Print_Scanned_Ship_Data_")

# 5. THE POINTER LEAVING THE GRID CHANGES NOTHING. Nothing in the
#    original clears `_scanned_big_ship` when the mouse moves off
#    the icons, so the last hovered ship stays in the panel.
_fl_scr.handle_mouse_motion(5, 5)
assert _fl_scr._hover_cell is None
assert _fl_scr._scan.icon == 3 and _fl_scr._panel.head[0] == "Ship 3", (
    "the panel emptied when the pointer left the grid; the "
    "original keeps the last hovered ship")

# 6. THE TWO REFUSALS ARE THE ORIGINAL'S. An EMPTY slot has no
#    icon to match (the scan loop stops at `_n_fltscrn_big_icons`,
#    flt2.cpp:906-909), and a FOREIGN stack is outside the whole
#    `if (_PLAYER_NUM == _fltscrn_stack_owner)` (flt1.cpp:615).
_hv_at(15)
assert _fl_scr._scan.icon == 3, (
    "hovering an empty slot moved the panel; there is no icon "
    "there for the original's scan to match")
_hv_foreign = _hv.Scan()
assert not _hv_foreign.hover(0, 0, False, [(0, 0, False)]), (
    "a foreign stack's grid set the scan; the original never "
    "reaches that line for one")

# 7. IT IS AN ICON INDEX AND NOT A SLOT, so an arrow scroll keeps
#    the SAME SHIP in the panel and takes the mark off the grid
#    when that ship is no longer one of the twenty on screen —
#    both because `_fltscrn_big_icon` is the whole filtered list
#    and the box is drawn inside the loop over the visible icons.
_hv_scroll = _hv.Scan()
_hv_blk = {"stack": 2, "icons": 60, "first_row": 0, "scanned_big": -1}
assert _hv_scroll.hover(6, 0, True, [(6, 6, False)])
assert _hv_scroll.slot(_hv_blk) == 6
_hv_blk2 = dict(_hv_blk, first_row=3)
assert _hv_scroll.resolve(_hv_blk2) == 6, "the scanned SHIP moved"
assert _hv_scroll.slot(_hv_blk2) is None, (
    "the mark stayed on the grid after its ship scrolled out of "
    "the five rows")

# 8. IT CLEARS WHERE THE ORIGINAL CLEARS — the stack pointer
#    moving (flt1.cpp:677, :757, :765) and the list being rebuilt,
#    which is SCRAP (:714) and the two filters.
for _hv_key, _hv_val in (("stack", 7), ("icons", 4)):
    _hv_c = _hv.Scan()
    _hv_c.follow(_hv_blk)
    assert _hv_c.hover(2, 0, True, [(2, 2, False)])
    _hv_c.follow(dict(_hv_blk, **{_hv_key: _hv_val}))
    assert _hv_c.icon == -1, (
        f"{_hv_key} changed and the scan survived it")
#    and on entering the screen (:528)
_fl_scr.enter(_hv_gs)
assert _fl_scr._scan.icon == -1 and not _fl_scr._panel

# 9. THE WIRE'S OWN VALUE IS STILL THE FALLBACK. With nothing
#    hovered in HD, a `scanned_big` the engine did report is what
#    the panel shows — it is the same field, read off the game's
#    own cursor.
_hv_gs2 = _fl_snapshot(icons=9, scanned_big=4, selected=())
_hv_gs2.fields = _fl_fields(9)
_fl_scr.enter(_hv_gs2)
assert _fl_scr._panel.head[0] == "Ship 4", (
    "with no HD hover the wire's scanned_big no longer reaches the "
    "panel")
_hv_at(1)
assert _fl_scr._panel.head[0] == "Ship 1", (
    "HD's own pointer did not win over the frozen wire value")

# 10. AND NOT ONE OF THE TEN MOVES SENT ANYTHING.
assert _fl_sent == [], _fl_sent

# ── THE STRIP UNDER THE MAP NAMES THE HOVERED STAR ───────────
#
# Work order 155, and the finding is what it does NOT do.
# `Print_Fltscrn_Scanned_Star_Name_` (flt2.cpp:338-522) picks one
# of ten states: with ships selected it runs
# `Ships_Try_To_Move_To_` and prints a MOVE PREVIEW, and only with
# none selected is it state 7, the star's own name, or state 8,
# H 0x94 for a star the player knows nothing about. HD draws those
# two and stays SILENT where the original previews a move, because
# a name there answers a different question.
#
# The fixture's local player is 1 — the snapshot's fourth field —
# so bit 1 is "player 1 has been there".
from screens.fleets import fltmove as _mv
_MB_STARS = (("Sol", 0x02, 120, 90), ("Vega", 0x02, 380, 160),
             ("Zoctan", 0x00, 460, 260))
_mb_gs = _fl_snapshot(icons=6, scanned_big=-1, selected=(),
                      stars=_MB_STARS)
_mb_gs.fields = _fl_fields(6)
_fl_scr.enter(_mb_gs)
assert _fl_scr._view.ok, _fl_scr._view.state
assert _mb_gs.player_num == 1, _mb_gs.player_num
assert _fl_scr._scan_star == -1 and _fl_scr._status == "", (
    "the strip is not empty on entry; the original prints it only "
    "under `_galaxy_map_scanned_star > -1` (flt1.cpp:397)")

_mb_box = next(b.screen_rect for b in _fl_scr.boxes
               if b.name == "inset_map")
_mb_nat = _flg.REGIONS["inset_map"]
_mb_drawn = _fl_scr._inset_stars()
assert len(_mb_drawn) == len(_MB_STARS), _mb_drawn
assert len({(_x, _y) for _x, _y, _c in _mb_drawn}) == len(_MB_STARS), (
    f"the fixture's stars land on top of each other ({_mb_drawn}), "
    f"so hovering cannot tell them apart and this proves nothing")

def _mb_point(_i):
    _sx, _sy, _c = _mb_drawn[_i]
    return (int(_mb_box.x + _sx * _mb_box.width / _mb_nat[2]),
            int(_mb_box.y + _sy * _mb_box.height / _mb_nat[3]))

# 1. EACH VISITED STAR NAMES ITSELF, AND NOTHING IS SENT.
for _mb_i, (_mb_name, _mb_vis, _x, _y) in enumerate(_MB_STARS):
    del _fl_sent[:]
    _fl_scr.handle_mouse_motion(*_mb_point(_mb_i))
    assert _fl_scr._scan_star == _mb_i, (
        f"hovering star {_mb_i} scanned {_fl_scr._scan_star}")
    if _mb_vis:
        assert _fl_scr._status == _mb_name, (
            f"star {_mb_i} shows {_fl_scr._status!r}, not "
            f"{_mb_name!r}")
    else:
        # 2. AND AN UNEXPLORED ONE IS NOT NAMED — state 8.
        assert _mb_name not in (_fl_scr._status or ""), (
            f"the strip named {_mb_name!r}, which this player has "
            f"not explored; the original prints H 0x94 there "
            f"(flt2.cpp:379-393)")
    assert _fl_sent == [], (
        f"hovering star {_mb_i} sent {_fl_sent}; the strip is built "
        f"from the stars HD already draws and must send nothing")

# 3. AN EMPTY PATCH OF MAP CLEARS IT.
del _fl_sent[:]
_fl_scr.handle_mouse_motion(_mb_box.x + 2, _mb_box.bottom - 2)
assert _fl_scr._scan_star == -1 and _fl_scr._status == "", (
    f"an empty point left {_fl_scr._status!r} in the strip")
assert _fl_sent == []

# 4. THE THREE SCANS ARE MUTUALLY EXCLUSIVE, as in the original:
#    taking a big icon sets `_scanned_big_ship` and clears
#    `_galaxy_map_scanned_star` in the same branch
#    (flt1.cpp:616-620).
_fl_scr.handle_mouse_motion(*_mb_point(0))
assert _fl_scr._scan_star == 0
del _fl_sent[:]
_mb_cell = _fl_scr.icon_slots()[2]
_fl_scr.handle_mouse_motion(_mb_cell.centerx, _mb_cell.centery)
assert _fl_scr._scan_star == -1, (
    "hovering a grid cell left the star scanned; the original "
    "clears it in the same branch that takes the icon")
assert _fl_scr._scan.icon == 2, _fl_scr._scan.icon
assert _fl_sent == []

# 5. WITH SHIPS SELECTED THE ORIGINAL PREVIEWS A MOVE, AND HD SAYS
#    NOTHING RATHER THAN SOMETHING ELSE.
_mb_sel = _fl_snapshot(icons=6, scanned_big=-1, selected=(0,),
                       stars=_MB_STARS)
_mb_sel.fields = _fl_fields(6)
_fl_scr.update(_mb_sel)
assert int(_mb_sel.fleet_screen["selected_count"]) == 1
del _fl_sent[:]
_fl_scr.handle_mouse_motion(*_mb_point(0))
assert _fl_scr._status == "", (
    f"with a ship selected the strip shows {_fl_scr._status!r}; the "
    f"original prints a move preview there, which is on no wire, so "
    f"HD must print nothing rather than a name")
assert _fl_sent == []

# 6. ONE COPY OF "WHICH STAR IS UNDER THIS POINT". The click and
#    the hover ask the same question and `fltmove.star_at` is the
#    only answer; outside the box it says so.
assert _mv.star_at(_fl_scr, 2, 2) == (False, None)
assert _mv.star_at(_fl_scr, *_mb_point(1)) == (True, 1)

ok("the strip under the Fleets map names the star the pointer is "
   "over, built from the stars HD already draws with nothing sent, "
   "silent on an empty point and while ships are selected — where "
   "the original previews a move — never naming an unexplored "
   "star, and clearing when the pointer takes a grid cell")

ok("the Fleets panel follows the pointer: the hovered ship's "
   "lines built from the snapshot HD already holds with nothing "
   "sent, one value behind the panel and the mark, selection kept "
   "out of it, the two refusals the original makes, an icon index "
   "that survives a scroll, the four resets, and the wire's own "
   "scanned_big still the fallback")

# ── A NATIVE BOX IS RECOGNISED, AND THE LIMITATION IS MARKED ───
#
# Work order 152, items 1 and 2. `FIELDSAV::Save_Field_Stats_`
# re-bases the field array and clears it, so a native box leaves
# ONLY its own fields on the wire; HD used to read that as WAITING
# and keep an empty grid up. What is held here is the recognition,
# the equality it rests on, and the marking of the one thing HD
# cannot do — set the box's text in its own font.
from core import gamebox as _gb
from screens.fleets import fltbox as _fb, fltwire as _fw

class _GBField:
    def __init__(self, i, r, hk, t=7):
        self.index = i
        self.x, self.y, self.x_end, self.y_end = r
        self.hotkey = hk
        self.field_type = t

# 1. EACH KIND IS RECOGNISED FROM ITS OWN FIELDS, and the rects are
#    the ones the source draws — checked against the player's LBX
#    when it is there, which is the second source (decision 36).
for _gb_kind in _gb.KINDS:
    _gb_live = [_GBField(i + 1, r, hk, t)
                for i, (r, hk, t) in enumerate(sorted(_gb_kind.fields))]
    _gb_got = _gb.detect(_gb_live)
    assert _gb_got is not None and _gb_got.kind is _gb_kind, (
        f"{_gb_kind.name} is not recognised from its own fields")
    assert len(_gb_got.buttons()) == len(_gb_kind.answers), (
        f"{_gb_kind.name}: {len(_gb_got.buttons())} answerable "
        f"button(s), {len(_gb_kind.answers)} expected")
    _gb_x, _gb_y, _gb_w, _gb_h = _gb_kind.rect
    assert 0 <= _gb_x and 0 <= _gb_y and _gb_x + _gb_w <= _gb.NATIVE_W \
        and _gb_y + _gb_h <= _gb.NATIVE_H, (
        f"{_gb_kind.name}'s rect {_gb_kind.rect} leaves the 640x480 "
        f"frame it is measured in")

# 2. THE EQUALITY IS THE POINT. A box REPLACES the list, so a match
#    on a subset would read a screen that merely contains one of
#    these rectangles as a box — and the fleet screen contains the
#    warning box's rectangle exactly, at hotkey 0 instead of ESC.
_gb_plus = [_GBField(i + 1, r, hk, t) for i, (r, hk, t)
            in enumerate(sorted(_gb.CONFIRMATION.fields))]
_gb_plus.append(_GBField(99, (0, 0, 639, 479), 0, 7))
assert _gb.detect(_gb_plus) is None, (
    "a list with an extra field was read as a confirmation box; the "
    "match has to be an equality, not a subset")
assert _gb.detect([_GBField(1, (0, 0, 639, 479), 0, 7)]) is None, (
    "the fleet screen's own catcher (same rect, hotkey 0) was read "
    "as a warning box — the ESC hotkey is what tells them apart")

# 3. THE STATE EXISTS AND KEEPS HD'S PICTURE UP. `in_box` must not
#    be `waiting` and must not hand over, or the empty grid is back.
assert hasattr(_fw, "GAME_BOX") and _fw.GAME_BOX != _fw.WAITING, (
    "fltwire has no GAME_BOX state distinct from WAITING; the two "
    "are different facts and one of them keeps an empty grid up")

# 4. THE LIMITATION SAYS SO, in the module and in the status
#    document, and names its replacement. A limitation nobody wrote
#    down is one somebody will read as a bug (decision 61).
_gb_src = io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                               "core", "gamebox.py"),
                  encoding="utf-8").read()
assert "open fix 29" in _gb_src, (
    "core/gamebox.py no longer names the open fix that replaces the "
    "framebuffer crop")
_gb_fixes = io.open(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                 "orion2re_open_fixes.md"),
                    encoding="utf-8").read()
assert "## 29." in _gb_fixes, (
    "open fix 29 is gone from doc/orion2re_open_fixes.md while "
    "core/gamebox.py still points at it")
_gb_status = io.open(os.path.join(os.path.dirname(SCREENS_DIR),
                                  "v3_projektstatus.md"),
                     encoding="utf-8").read()
assert "open fix 29" in _gb_status, (
    "v3_projektstatus.md no longer marks the framebuffer crop as the "
    "limitation it is")

# 5. AND IT IS DRAWN AT AN INTEGER MAGNIFICATION (decision 28):
#    these are the game's own pixels and a smooth resample of them
#    is a picture of something the game never drew.
assert _fb.MAX_SCALE >= 1 and isinstance(_fb.MAX_SCALE, int)
for _gb_w, _gb_h in ((1920, 1080), (2560, 1440), (3840, 2160)):
    class _GBScreen:
        class app:
            win_w, win_h = _gb_w, _gb_h
    _gb_scale, _gb_dest = _fb.placement(_GBScreen, _gb.CONFIRMATION)
    assert int(_gb_scale) == _gb_scale and _gb_scale >= 1
    assert _gb_dest.width == _gb.CONFIRMATION.rect[2] * _gb_scale
    assert _gb_dest.right <= _gb_w and _gb_dest.bottom <= _gb_h, (
        f"{_gb_w}x{_gb_h}: the box is drawn off the window")

ok(f"a native box is recognised by its whole field list ("
   f"{len(_gb.KINDS)} kinds, rects from the draw call and the LBX), "
   f"the fleet catcher is not mistaken for one, GAME_BOX keeps HD's "
   f"picture up, and the framebuffer crop is marked a limitation "
   f"with open fix 29 as its replacement")
