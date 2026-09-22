# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 031_core_figures_sit_on_the_plate_s.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (92 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - figures sit on the plate's inner floor, row and held alike (four resolutions, every band, measur


# ── The pop move: nothing reaches the game until both clicks ──
# Section 3 of this phase, and the whole of why the first click is
# local: there is no cancel that stays on this screen, so a
# preview that created the game's own cluster would strand a
# player who changed their mind (colsum.cpp:804 and :938 are both
# leave-the-screen paths). The claim is about the WIRE and is
# asserted on the wire — "the screen looks the same afterwards"
# would also be true of a screen that sent a click and redrew the
# old picture.
from screens.colony_summary import colonypick as _cp
from screens.colony_summary import colonysend as _cse
from screens.colony_summary import colonymoveui as _cmu
from screens.colony_summary import colonytrack as _ct
from screens.colony_summary import colonypopup as _cpop
from core import textfit as _textfit
from core import wire_protocol as _wire

class _MoveCap(_CapAll):
    def __init__(self):
        super().__init__()
        self.stats = {"state": 0, "visual": 0}

_mv_cap = _MoveCap()
_mv_client, _mv_conn = app.client, app.connected
app.client, app.connected = _mv_cap, True
_scr_op._sort_key = "name"
_scr_op.update(_sel_snap)
_mv_rows = _scr_op._rows
_mv_area, _mv_cfg, _mv_scale, _mv_n = _scr_op._list_view()
_mv_track = _cl.track_metrics(_mv_area, _mv_cfg, _mv_scale)
_mv_bands = _cl.row_bands(_mv_area, _mv_cfg, _mv_scale, _mv_n)

def _square_xy(row_index, job, index=0):
    """The centre of one CELL, from the row's own geometry.

        Since 6 September a slot index is not a cell index — the job
        markers sit between the groups — so this asks `row_boxes`
        rather than multiplying a pitch, which is the same reason
        `drop_targets` exists.
        """
    _top, _h = _mv_bands[row_index]
    for _j, _i, _r in _cl.row_boxes(_mv_area, _mv_cfg, _mv_scale,
                                    _mv_rows[row_index]).cells:
        if (_j, _i) == (job, index):
            return _r.x + _r.width // 2, _top + _h // 2
    raise AssertionError(f"row {row_index} has no cell {index} of "
                         f"job {job}")

def _band_xy(row_index, job):
    _top, _h = _mv_bands[row_index]
    for _j, _r in _cl.drop_targets(_mv_area, _mv_cfg, _mv_scale,
                                   _mv_rows[row_index]):
        if _j == job and _r.width:
            return _r.x + _r.width // 2, _top + _h // 2
    raise AssertionError(f"no drop target for job {job}")

# A row with pops in at least two jobs, so a move has somewhere
# to go and the fixture is not the thing being tested.
_mv_row = next(i for i, r in enumerate(_mv_rows)
               if sum(1 for c in r["jobs"] if c) >= 2)
_mv_job = next(j for j, c in enumerate(_mv_rows[_mv_row]["jobs"]) if c)
_mv_slot = 0    # the first cell of that job
_mv_target = next(j for j in range(3) if j != _mv_job)

# FIRST CLICK: a selection, and NOTHING on the wire.
_scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
assert _scr_op._move.pick is not None, (
    "a click on a filled square did not pick anything up")
assert _mv_cap.calls == [] and _mv_cap.keys == [] \
    and _mv_cap.fields == [], (
    f"the FIRST click reached the game: clicks {_mv_cap.calls}, "
    f"keys {_mv_cap.keys}, fields {_mv_cap.fields}. It must not: "
    f"Get_Cluster_ unassigns the pops there and then, and the "
    f"only ways out of a held cluster are dropping it or leaving "
    f"the screen")

# THE RIGHT BUTTON IS HELP, EVEN WITH A PICK HELD — brief 98,
# Data's decision (a). The original's help list ends with a
# screen-wide entry, so a right click never reaches Cancel; the HD
# right-click discard could not fire and is gone. A right click over
# the held pop opens help, keeps the pick and sends nothing; the
# next right click closes the popup. The discard that survives is
# the left click off the rows, below.
_scr_op.handle_right_button(True, *_square_xy(_mv_row, _mv_job, _mv_slot))
assert _scr_op._move.pick is not None and _scr_op.help.visible, (
    "a right click with a pick held did not open help, or discarded "
    "the pick — the right button is context help only")
_scr_op.handle_right_button(True, *_square_xy(_mv_row, _mv_job, _mv_slot))
assert not _scr_op.help.visible, "a second right click did not close help"
assert _mv_cap.calls == [] and _mv_cap.keys == [] \
    and _mv_cap.fields == [], "the help path reached the game"
_scr_op.handle_click(_mv_area.x + 2, _mv_area.bottom - 2)
assert _scr_op._move.pick is None, (
    "a left click off the rows did not discard the selection")
# And so does a left click that lands on neither icon nor band.
_scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
assert _scr_op._move.pick is not None
_scr_op.handle_click(_mv_area.x + 2, _mv_area.bottom - 2)
assert _scr_op._move.pick is None, (
    "a click off the rows did not discard the selection")
assert _mv_cap.calls == [] and _mv_cap.fields == []

# EVERY REFUSAL SENDS NOTHING AND SAYS WHY, and the wording comes
# out of layout.json (decision 15). Driven through the controller
# rather than the rules, because the claim is about the seam.
_mv_words = _scr_op._data["move"]
_mv_pops, _mv_np, _mv_mf = _cp.pops_of(_sel_snap,
                                       _mv_rows[_mv_row]["index"])

def _refusal(pops, n_pops, max_farms, job, slot, target,
             sort_key="name"):
    _c = _cmu.MoveController()
    _pick = _cp.pick_at(pops, n_pops, job, slot,
                        _mv_rows[_mv_row]["index"], _mv_row,
                        sort_key)
    if isinstance(_pick, _cp.Refusal):
        return _pick
    _c.pick = _pick
    return _cp.plan_move(_pick, pops, n_pops, max_farms,
                         _mv_rows[_mv_row]["index"], target)

# A native is refused at the FIRST click, in a different function
# with a different message (colmove.cpp:59-64).
_nat = [_icon_pop(9, 0)] + list(_mv_pops[1:])
assert _refusal(_nat, _mv_np, _mv_mf, 0, 0, 1).reason == \
    _cm.REFUSE_NATIVE_PICKUP
# An android keeps its job (colmove.cpp:531-537).
_and = [_icon_pop(8, 0)] + list(_mv_pops[1:])
assert _refusal(_and, _mv_np, _mv_mf, 0, 0, 1).reason == \
    _cm.REFUSE_ANDROID
# A planet that cannot farm refuses its first farmer.
assert _refusal(list(_mv_pops), _mv_np, 0, 1, 0, 0).reason == \
    _cm.REFUSE_NO_FARMING
# And a sort HD cannot honour refuses the whole thing: the two
# lists are not in the same order, so no row maps to a slot.
assert _refusal(list(_mv_pops), _mv_np, _mv_mf, 0, 0, 1,
                sort_key=next(iter(_cr.SORT_UNAVAILABLE))).reason \
    == _cp.REFUSE_SORT_UNAVAILABLE
for _r in (_cm.REFUSE_NATIVE_PICKUP, _cm.REFUSE_ANDROID,
           _cm.REFUSE_NO_FARMING, _cp.REFUSE_SORT_UNAVAILABLE,
           _cp.REFUSE_NO_ICON, _cp.REFUSE_OTHER_COLONY):
    assert _mv_words.get(_r), f"move.{_r} has no wording"
    assert _cp.message(_mv_words, _cp.Refusal(_r)) == _mv_words[_r]
# A PARTIAL carries both halves: the rule that stopped it AND the
# count, because "this job is full" alone reads as "nothing fits"
# when two of twelve would have moved.
_part = _cp.message(_mv_words, _cp.Refusal(_cm.REFUSE_JOB_FULL,
                                           landed=2, carried=10,
                                           total=12))
assert _mv_words[_cm.REFUSE_JOB_FULL] in _part and "2" in _part \
    and "12" in _part, _part
assert "{" not in _part, (
    "a placeholder survived substitution; `message` replaces and "
    "never formats (decision 37)")

# A REFUSED DROP SENDS NOTHING THROUGH THE SEAM EITHER.
_mv_cap.calls, _mv_cap.keys, _mv_cap.fields = [], [], []
_scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
_scr_op._sort_key = next(iter(_cr.SORT_UNAVAILABLE))
_scr_op.handle_click(*_band_xy(_mv_row, _mv_target))
_scr_op._sort_key = "name"
assert _mv_cap.calls == [] and _mv_cap.fields == [], (
    "a refused drop reached the game")
_scr_op._move.cancel("test")

# NOTHING IN colonypick CAN SEND. The rule is structural, so the
# check is too: a client would have to arrive through an import.
_cp_src = open(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "screens", "colony_summary", "colonypick.py")).read()
for _forbidden in ("inject_click", "activate_field", "inject_key",
                   "game_client"):
    assert _forbidden not in _cp_src, (
        f"colonypick mentions {_forbidden}; the module that "
        f"DECIDES must not be able to send, which is what makes "
        f"'a preview does not inject' a property of the import "
        f"graph rather than a promise")

# THE MARKINGS, in every home they claim. A marking two documents
# assert and nobody checks is an intention (the help panel's).
assert "HD EXTENSION" in (_cmu.MoveController.cancel.__doc__ or "")
assert "HD EXTENSION" in (_cp.__doc__ or "")
assert "HD EXTENSION" in _mv_words.get("_hd_extension_cancel", "")
from core import zoomtables as _zt
# ── THE DROP TARGET STOPPED BEING AN EXTENSION ──
# `_hd_extension_bands` is gone: the target is the original's own
# per-row job field, added unconditionally in mode 1
# (coldraw.cpp:409), so an empty column is a target there too.
# What is left is the HEIGHT, and that is a DEVIATION with three
# homes. Retargeted in the same commit that took the words out.
assert "_hd_extension_bands" not in _mv_words, (
    "move._hd_extension_bands is back. The drop target is a "
    "transcription — coldraw.cpp:409 adds the field whether or "
    "not the column drew an icon — and calling it an extension "
    "was the marking this commit withdrew")
_dtn = _mv_words.get("_drop_target_note", "")
assert "DEVIATION" in _dtn and "coldraw.cpp:409" in _dtn, (
    "move._drop_target_note must carry the DEVIATION and name "
    "the call the target is transcribed from")
assert "colsum.cpp:909" in _dtn, (
    "the fourth target — a drop on the colony name, which is "
    "Send_Cluster_(colony, -1) — is not named in the note")
assert "DEVIATION IN HEIGHT" in (_ct._column_boxes.__doc__ or ""), (
    "colonytrack._column_boxes no longer carries the drop rect's "
    "height deviation")
# ── AND THE TWO ROW MARKS ARE GONE, WITH THEIR MARKINGS ──
# The pick outline and the drop-band frame. The original marks
# neither: its only drawing outside fields and paragraphs on this
# screen is the scroll thumb (colsum.cpp:759-765).
for _dead in ("draw_pick", "draw_drop_bands"):
    assert not hasattr(_cl, _dead), (
        f"colonylist.{_dead} is back — the original marks neither "
        f"the picked cells nor the row they came from")
for _dead in ("PICK_COLOR", "BAND_COLOR", "MARKER_BG",
              "MARKER_EDGE", "MARKER_TEXT"):
    assert not hasattr(_cl, _dead), (
        f"colonylist.{_dead} survived its drawing — a palette key "
        f"nothing reads is a marking that has stopped marking")
assert "markers" not in _ct.RowBoxes._fields, (
    "RowBoxes carries a markers field again; the F/W/S squares "
    "were removed with their marking on 8 September 2026")
for _gone in ("growth", "beyond"):
    assert _gone not in _ct.RowBoxes._fields, (
        f"RowBoxes carries a {_gone} field again. It held part of "
        f"the HD allocation bar, an INVENTION that 514ebb2 "
        f"replaced with six column boxes on 8 September 2026, and "
        f"both fields were empty from that day until work order "
        f"157 removed them. A per-row capacity display is an open "
        f"question for Data and would be a MARKED HD EXTENSION "
        f"built against the columns — not these fields returning; "
        f"see colonytrack._column_boxes")
assert "name" in _ct.RowBoxes._fields, (
    "RowBoxes lost the name rect, which is the fourth drop "
    "target (colsum.cpp:909)")
# ── THE HELD CLUSTER, AND THE STEP IT IS OFFSET BY ──
assert "colmove.cpp" in (_cl.draw_held_cluster.__doc__ or ""), (
    "draw_held_cluster does not name Draw_Cluster_, which is the "
    "whole of what it transcribes")
_zt_src = open(os.path.join(_proj, "core", "zoomtables.py"),
               encoding="utf-8").read()
_zt_note = _zt_src[:_zt_src.index("CLUSTER_FIGURE_OFFSET = ")]
_zt_note = _zt_note[_zt_note.rindex("FIGURE_STEPS = "):]
assert "DEVIATION" in _zt_note and "colmove.cpp:23" in _zt_note, (
    "CLUSTER_FIGURE_OFFSET's note must carry the DEVIATION that "
    "multiplying by the sprite step is, and name the source line")
assert (_zt.CLUSTER_FIGURE_OFFSET == (5, -10)
        and _zt.CLUSTER_FIGURE_PITCH == 20), (
    f"the cluster offsets are {_zt.CLUSTER_FIGURE_OFFSET} / "
    f"{_zt.CLUSTER_FIGURE_PITCH}; colmove.cpp:23-28 says "
    f"(5, -10) and 20")
assert "HD EXTENSION" in (_cl._cell_mark.__doc__ or "")
assert "IT DOES NOT APPEAR WHILE A SELECTION IS HELD" in (
    _cpop.__doc__ or "")
for _cite in ("colsum.cpp:804", "colsum.cpp:938"):
    assert _cite in _mv_words["_hd_extension_cancel"], (
        f"the cancel marking no longer names {_cite} — the "
        f"reason it is allowed is that the original's only exits "
        f"from a held cluster are those two, and a marking that "
        f"does not say what the original does instead is a label")
# AND THE STATUS DOCUMENT, which both notes name as a home. A
# marking two documents claim exists is not a marking — that is
# the help panel's lesson, and it cost a day and a half of a
# tree actively defending the wrong label.
_mv_status = open(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "v3_projektstatus.md")).read()
for _mark in ("HD EXTENSION — the cancel",
              "HD EXTENSION — a drop target per job",
              "HD EXTENSION — a click on the held pop's own group",
              "HD EXTENSION — three job markers, always",
              "HD EXTENSION — an identity letter in the cell",
              "HD EXTENSION — a hover popup below the row",
              "DEVIATION — a partial move is refused"):
    assert _mark in _mv_status, (
        f"v3_projektstatus.md does not carry {_mark!r}, which "
        f"layout.json's move notes name as one of its homes")
# ── AND THE SOURCE IS A HOME TOO, NOT ONLY A CITED ONE ──────
# This loop read the status document and `layout.json` and
# stopped there, so a marking that BOTH of them said lived in a
# module could be missing from that module indefinitely — which
# is exactly what had happened to the hover popup:
# `_hd_extension_popup` said "In colonypopup, here, in
# v3_projektstatus.md and in a check", the status entry said "In
# colonypopup, layout.json under _hd_extension_popup, and a
# check", and `colonypopup.py` described the behaviour at length
# without ever naming it. Two documents asserting a marking is
# not a marking (fundament, Evidence) — and a check that reads
# only the documents defends the sentence rather than the file.
for _mod, _why in (("colonypopup.py", "the hover popup"),
                   ("colonymoveui.py", "the stranded notice"),
                   ("colonypick.py", "the cancel")):
    _mod_src = open(os.path.join(SCREENS_DIR, "colony_summary", _mod),
                    encoding="utf-8").read()
    assert "HD EXTENSION" in _mod_src, (
        f"{_mod} carries no HD EXTENSION marking, and it is named "
        f"as a home for {_why} by layout.json and by "
        f"v3_projektstatus.md. A module that two documents say is "
        f"marked and is not is the fault this check exists for")
# ── WHY EVERY MOVE RE-SORTS, AND WHY IT IS NOT SKIPPED ──────
# The step costs 54 ms of a 758 ms drop (measured 9 September
# 2026) and the obvious saving is "skip it when the game already
# holds the key". It cannot be taken, because nothing on the wire
# says the game does: neither `SerializeState` nor
# `SerializeFields` carries `_g_sort_index` or any field's value.
# A reason that lives only in a commit message is one the next
# reader re-litigates, so the module carries it and this holds
# the module to it — including the two line ranges, because
# "not on the wire" without a place it was looked for is an
# assumption wearing a finding's clothes.
# RETARGETED 10 September 2026: the sort STEP went with the click
# chain (fundament 52) and the FINDING did not. It is about the
# API, not about that chain, so it lives with decision 46's other
# not-on-the-wire state in `colonyselect` — and this holds it
# there, including the two line ranges, because "not on the wire"
# without a place it was looked for is an assumption wearing a
# finding's clothes.
_cs_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonyselect.py"), encoding="utf-8").read()
for _cite in ("ext_api.cpp:49-136", "ext_api.cpp:185-200",
              "decision 46", "_g_sort_index"):
    assert _cite in _cs_src, (
        f"colonyselect no longer says where the game's sort state "
        f"was looked for ({_cite}) — an unreadable state is not a "
        f"state to assume, and the next reader will assume it")

assert "DEVIATION" in _mv_words.get("_partial_note", ""), (
    "refusing a partial move is a deviation from the original, "
    "which performs it and then opens a blocking box "
    "(colmove.cpp:168-173, textbox.cpp:149)")
app.client, app.connected = _mv_client, _mv_conn
_scr_op.update(_sel_snap)
# ── The drop target IS the group, and the outline IS the target ─
# Until 5 September 2026 the targets were three equal thirds of
# the whole 42-slot track. Every job was reachable — but only at
# a place where nothing stood: a colony of 13 pops has all its
# cells inside the first third, so a click on a WORKER cell named
# food while empty track two thirds along named research and
# worked. The picture and the hit test agreed with each other and
# neither agreed with the squares, which is decision 5's failure
# exactly. Measured then: every non-food group of every row in
# the reference save named food.
_dt_rows = [
    # the case that was reported, and the two the fixtures added
    {"name": "Draconis V", "pops": 9, "jobs": [4, 4, 1],
     "no_farming": False, "climate": 8, "max_pop": 14,
     "producing": "", "producing_turns": 0, "can_buy": False},
    {"name": "Urna I", "pops": 4, "jobs": [4, 0, 0],
     "no_farming": False, "climate": 5, "max_pop": 4,
     "producing": "", "producing_turns": 0, "can_buy": False},
    {"name": "Neptunus I", "pops": 2, "jobs": [0, 0, 2],
     "no_farming": True, "climate": 2, "max_pop": 3,
     "producing": "", "producing_turns": 0, "can_buy": False},
    # an empty MIDDLE group, which no fixture happens to hold
    {"name": "inner", "pops": 13, "jobs": [12, 0, 1],
     "no_farming": False, "climate": 8, "max_pop": 22,
     "producing": "", "producing_turns": 0, "can_buy": False},
    # and a job nobody holds at all
    {"name": "single", "pops": 1, "jobs": [1, 0, 0],
     "no_farming": False, "climate": 8, "max_pop": 4,
     "producing": "", "producing_turns": 0, "can_buy": False},
]
_dt_track = _cl.track_metrics(_mv_area, _mv_cfg, _mv_scale)
for _r in _dt_rows:
    _regs = _cl.row_regions(_r)
    _targets = _cl.drop_targets(_mv_area, _mv_cfg, _mv_scale, _r)
    assert [j for j, _ in _targets] == [0, 1, 2], _targets
    _boxes = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _r)
    # 1. EVERY CELL NAMES ITS OWN JOB. The one that was broken.
    for _zone, _k, _cell in _boxes.cells:
        _cx = _cell.x + _cell.width // 2
        _got = _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r, _cx)
        assert _got == _zone, (
            f"{_r['name']}: cell {_k} of job {_zone} names "
            f"{_got}. A click on a cell must name that cell's "
            f"job — looks right, clicks wrong is the whole "
            f"fault this replaced")
    # 1b. THE COLONY NAME NAMES NO JOB, and answers the fourth
    #     target instead — `Send_Cluster_(colony, -1)`,
    #     colsum.cpp:909, which is "put them back".
    _nrect = _ct.name_rect(_mv_area, _mv_cfg, _mv_scale, _r)
    if _nrect is not None and _nrect.width:
        _nmid = _nrect.x + _nrect.width // 2
        assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                             _nmid) is None, (
            f"{_r['name']}: the name column names a job")
        assert _ct.on_name(_mv_area, _mv_cfg, _mv_scale, _r, _nmid), (
            f"{_r['name']}: on_name does not recognise the middle "
            f"of the name column")
    # 1c. EACH GROUP SITS IN ITS OWN COLUMN, and every cell of it
    #     inside that column. This replaced "the run is flush" at
    #     Stage 4: a flush run was the property of ONE track, and
    #     the row is five columns now — a marker that started
    #     where the previous group ended would put the workers
    #     under the FARMERS heading the moment a colony had
    #     eleven farmers. The failure shape is the one this whole
    #     block exists for, so the property moved with the
    #     geometry rather than being dropped.
    _colmap = _ct.columns(_mv_area, _mv_cfg)
    assert _colmap, (
        "the screen's list cfg has no column table, so this whole "
        "block would be testing the single-track fallback that "
        "nothing ships — colonyheader.install_columns")
    for _zone, _key in enumerate(_ct.JOB_KEYS):
        _cx, _cw = _colmap[_key]
        _own = [c for j, _k, c in _boxes.cells if j == _zone]
        # THE FIRST CELL IS ONE PIXEL INSIDE THE COLUMN, which
        # is the plate's own line and is transcribed: the
        # original's icons start at `left_x` 101/236/378 and its
        # drawn boxes at 100/235/377. It used to be one marker's
        # width in; the markers went on 8 September 2026.
        if _own:
            assert _own[0].x == _cx + _ctk.PLATE_LINE, (
                f"{_r['name']}: the first cell of job {_zone} is "
                f"at {_own[0].x}, its column starts at {_cx} and "
                f"the plate's line takes one px")
        for _c in _own:
            assert _cx <= _c.x and _c.right <= _cx + _cw, (
                f"{_r['name']}: a cell of job {_zone} "
                f"({_c.x}..{_c.right}) leaves its column "
                f"({_cx}..{_cx + _cw}) — a cell under the wrong "
                f"heading is the failure this block exists for")
    # AND NO GROWTH BOXES. This asserted `not _boxes.growth`
    # per fixture until 21 September 2026 (work order 157);
    # the FIELD is gone now and the claim moved up to
    # RowBoxes._fields, which is strictly stronger — it says
    # the field cannot come back at all, where this said only
    # that it was empty for the rows this block happens to
    # build. `_column_boxes` carries the reasoning.
    # 2. EVERY JOB HAS A TARGET, INCLUDING AN EMPTY ONE — and
    #    since 8 September that is a TRANSCRIPTION rather than a
    #    thing the markers bought: mode 1 adds the field after a
    #    walk that may have drawn nothing (coldraw.cpp:409), so
    #    the original accepts a drop on an empty column too.
    for _job, _rect in _targets:
        assert _rect.width >= 1, (
            f"{_r['name']}: job {_job} has no target at all; an "
            f"empty job is the one a player most wants to start")
        assert (_rect.x, _rect.width) == _colmap[_ct.JOB_KEYS[_job]], (
            f"{_r['name']}: job {_job}'s target is "
            f"{(_rect.x, _rect.width)} and its column is "
            f"{_colmap[_ct.JOB_KEYS[_job]]} — the target is the "
            f"whole cell, which is what coldraw.cpp:409 adds")
        _mid = _rect.x + _rect.width // 2
        assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                             _mid) == _job
    # 3. THE THREE TARGETS DO NOT OVERLAP, in ECON order.
    _xs = [(r.x, r.x + r.width) for _j, r in _targets]
    for _a, _b in zip(_xs, _xs[1:]):
        assert _a[1] <= _b[0], (
            f"{_r['name']}: targets overlap, {_xs}")
    # 4. NO JOB IS EVER EMPTY, and it cannot be: the target IS
    #    the column box, so a job with no pops is as wide as one
    #    that is full.
    for _job, _rect in _targets:
        assert _rect.width == _colmap[_ct.JOB_KEYS[_job]][1], (
            f"{_r['name']}: job {_job}'s target is {_rect.width} "
            f"and its column is "
            f"{_colmap[_ct.JOB_KEYS[_job]][1]}")
    # 5. OUTSIDE EVERY TARGET IS None, and None is a state.
    # 5b. OUTSIDE THE THREE JOB COLUMNS IS None, and None is a
    #     state — it discards a held selection rather than
    #     dropping it. The bounds are the columns' own now, not
    #     the single track's.
    _lo = min(_colmap[_k2][0] for _k2 in _ct.JOB_KEYS)
    _hi = max(_colmap[_k2][0] + _colmap[_k2][1]
              for _k2 in _ct.JOB_KEYS)
    assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                         _lo - 5) is None
    assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                         _hi + 5) is None
from screens.colony_summary import colonyicons as _ci
from screens.colony_summary import colonymove as _cmv2
from screens.colony_summary import colonyfigures as _cfig
from core.structs import colony as _cspec
# 6. A HELD CLUSTER LEAVES THE ROW, AND THE PITCH FOLLOWS IT —
#    which is what replaced the two marks on 8 September 2026.
#    The original does not outline the picked cells and does not
#    frame the row; it clears `0x200` (colmove.cpp:70) and the
#    icon walk stops emitting them (coldraw.cpp:336), so the row
#    is shorter and the squish is recomputed over what is left by
#    the SAME pre-pass that serves the draw and both hit tests
#    (coldraw.cpp:301 -> :419).
#
#    Asserted on the render, not on the code: the cells are
#    recovered from their own ink before and after, and the
#    surviving pitch is compared against `column_pitch` at the
#    SHORTENED count. A second arithmetic anywhere on this path
#    would show up here as a pitch that did not move.
_hc_pops = [((1 & 3) << 7) | _cspec.POP_MASK_ASSIGNED
            for _ in range(6)]
_hc_row = {"name": "held", "pops": 6, "jobs": [0, 6, 0],
           "no_farming": False, "climate": 8, "max_pop": 10,
           "producing": "", "producing_turns": 0, "can_buy": False,
           "cells": ((), tuple(range(6)), ())}
_hc_full = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _hc_row)
_hc_kept = dict(_hc_row, cells=((), tuple(range(4)), ()))
_hc_short = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _hc_kept)
assert len([c for j, _k, c in _hc_full.cells if j == 1]) == 6
_hc_cells = [c for j, _k, c in _hc_short.cells if j == 1]
assert len(_hc_cells) == 4, (
    "holding two of six pops did not shorten the row — the cells "
    "are built from the icon list and the icon list is built from "
    "the assigned bit")
# The pitch is the shortened one, and it comes from the one home.
_hc_step = _cfig.figure_step(_mv_area, _mv_cfg)
_hc_want = min(_ci.column_pitch(1, 4), _ci.ICON_SPACING) * _hc_step
assert abs((_hc_cells[1].x - _hc_cells[0].x) - int(_hc_want)) <= 1, (
    f"the shortened row draws a pitch of "
    f"{_hc_cells[1].x - _hc_cells[0].x}; colonyicons.column_pitch "
    f"at 4 icons times the sprite step is {int(_hc_want)} — a "
    f"second pitch computation has entered the pick path")
# AND `build_rows` IS WHAT SHORTENS IT, by clearing the bit the
# original clears. Not a count subtracted somewhere.
_hc_held = _cmv2.held_pops(_hc_pops, (4, 5))
assert len(_ci.icon_pops(_hc_held, 6, 1)) == 4, _hc_held
assert all(not (_hc_held[i] & _cspec.POP_MASK_ASSIGNED)
           for i in (4, 5)), _hc_held
assert all(_hc_held[i] & _cspec.POP_MASK_ASSIGNED
           for i in range(4)), _hc_held
assert _hc_pops[4] & _cspec.POP_MASK_ASSIGNED, (
    "held_pops wrote into the array it was given; the snapshot's "
    "own words must survive it (decision 47)")
# NO `count - n` ANYWHERE ON THE PATH. The rule, not the
# instance: the shortening is one cleared bit, so no module on
# this path may subtract a held size from a count.
for _mod in ("colonytrack.py", "colonylist.py", "colonyrows.py",
             "colonyicons.py"):
    _msrc = open(os.path.join(_proj, "screens", "colony_summary",
                              _mod), encoding="utf-8").read()
    for _bad in ("- len(held", "- len(self.cluster",
                 "- pick.size", "- self.pick.size"):
        assert _bad not in _msrc, (
            f"{_mod} subtracts a held count ({_bad!r}). The held "
            f"pops leave the row by losing 0x200, which is what "
            f"the original does and what keeps one list serving "
            f"the draw, the pitch and both hit tests")
# AND ONE HOME FOR THE PITCH. `squish_step` is
# Calculate_Squish_Step_ transcribed and must exist once.
_sq = []
for _dp, _dn, _fns in os.walk(_proj):
    _dn[:] = [d for d in _dn if d not in ("__pycache__", ".git")]
    for _fn in _fns:
        if not _fn.endswith(".py"):
            continue
        _fp = os.path.join(_dp, _fn)
        # This file is excluded, and only by exact path: it names
        # the function in the assertion below, which would
        # otherwise count as a second home. Same exclusion the
        # marking inventory makes, for the same reason.
        if os.path.relpath(_fp, _proj) in SUITE_FILES:
            continue
        if "def squish_step(" in open(_fp, encoding="utf-8").read():
            _sq.append(_fp)
assert len(_sq) == 1 and _sq[0].endswith("colonyicons.py"), (
    f"Calculate_Squish_Step_ is transcribed in {_sq} — one home, "
    f"or the render and the hit test drift (decision 5)")

# 7. THE CELL UNDER A PIXEL IS THE CELL DRAWN AT THAT PIXEL —
#    for every cell of every row, PICK-UP as well as drop.
#
#    Item 6 above was built for exactly this class of fault and
#    did not catch it, which is worth more than the fault: it
#    inks `draw_drop_bands` only, and only its two outermost
#    columns, so it can say nothing about the pick-up path and
#    nothing about any cell in between. `draw_pick` was never
#    rendered by any check at all. It computed `start + slot *
#    step` from the track origin, while `slot` is an index within
#    ONE JOB's icons — so the outline sat one marker plus every
#    preceding cell to the left of the cell it named. Reported
#    live on Horus IV as "exactly one cell" because food is job 0
#    and its only error is the F marker; industry was off six
#    cells and research ten. Born in 343d9ba, invisible on food
#    until the markers moved the run.
#
#    So this reads the RENDER and not the geometry: the cells are
#    recovered from their own ink, and both hit tests and the
#    pick outline are asserted against THAT. Two functions
#    calling a third is what the broken version could also have
#    claimed.
_pk_surf = pygame.Surface((_mv_area.right + 16, _mv_area.bottom + 16))
_pk_band = _mv_bands[0]
_mv_px = app.layout.font_size(_mv_cfg.get("small_font", 15))

def _ink_runs(_draw, _rgb):
    """The x-runs where `_draw` put `_rgb` down, left to right."""
    _pk_surf.fill((0, 0, 0))
    _draw(_pk_surf)
    _a = pygame.surfarray.array3d(_pk_surf)
    _hit = [_x for _x in range(_pk_surf.get_width())
            if (_a[_x] == list(_rgb[:3])).all(axis=1).any()]
    _runs = []
    for _x in _hit:
        if _runs and _x == _runs[-1][1] + 1:
            _runs[-1] = (_runs[-1][0], _x)
        else:
            _runs.append((_x, _x))
    return _runs

for _r in _dt_rows:
    _drawn = {_j: _ink_runs(
        lambda _s, _row=_r: _cl._render_bar(
            _s, _row, _mv_area, _mv_cfg, _mv_scale, _pk_band,
            _dt_track, _mv_px, app.style, app.layout),
        _cl.ZONE_COLORS[_j]) for _j in range(3)}
    _boxes = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _r, _pk_band)
    for _j in range(3):
        _want = [(_c.x, _c.x + _c.width - 1)
                 for _job, _k, _c in _boxes.cells if _job == _j]
        assert _drawn[_j] == _want, (
            f"{_r['name']}: job {_j} draws its cells at "
            f"{_drawn[_j]}, the geometry says {_want} — the "
            f"picture and the rects disagree")
        for _k, (_x0, _x1) in enumerate(_drawn[_j]):
            # PICK-UP: every pixel of the drawn cell picks up
            # that cell, and nothing else does.
            for _x in (_x0, (_x0 + _x1) // 2, _x1):
                assert _cl.cell_at_x(_mv_area, _mv_cfg, _mv_scale,
                                     _r, _x) == (_j, _k), (
                    f"{_r['name']}: x={_x} is drawn as cell {_k} "
                    f"of job {_j} and picks up "
                    f"{_cl.cell_at_x(_mv_area, _mv_cfg, _mv_scale, _r, _x)}")
                assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale,
                                     _r, _x) == _j, (
                    f"{_r['name']}: x={_x} is drawn as job {_j} "
                    f"and drops into "
                    f"{_cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r, _x)}")
# ── THE HELD CLUSTER SITS ON THE ROW'S OWN FIGURE LINE ──────
#
# Reported as "at 2560x1440 the moved figure hangs in the air over
# the row; at 1920 and 3840 it lands correctly", and it did. The
# cluster hung at `pointer + CLUSTER_FIGURE_OFFSET * step`, which
# is `COLMOVE::Draw_Cluster_` transcribed (colmove.cpp:7-37), and
# that lands on the row's figure line only when the pointer is
# half a sprite below the band top — which is the middle of the
# row in the ORIGINAL, whose band is 30 native px against a 28 px
# sprite, and is not the middle of ours. Measured with the pointer
# at each band's centre: +1 px out at 1080p, +2 at 2160p, +10 at
# 1440p, whose band is 77 against a 56 px sprite because step 3
# does not fit. See `colonytrack.held_figure_y`.
#
# **THE GEOMETRY AND THE INK, because they fail differently.** A
# y that is right and a blit that ignores it look identical in the
# arithmetic and not on screen.
import importlib.util as _hlu
_plv_spec = _hlu.spec_from_file_location(
    "_held_preview", os.path.join(os.path.dirname(SCREENS_DIR),
                                  "tools", "colony_list_preview.py"))
_plv = _hlu.module_from_spec(_plv_spec)
_plv_spec.loader.exec_module(_plv)
from core import zoomtables as _hzt
_hf_seen = []
for _hspec2 in ("1920x1080", "2560x1440", "3440x1371", "3840x2160"):
    _hw2, _hh2 = (int(v) for v in _hspec2.split("x"))
    _hlay2 = Layout(_hw2, _hh2)
    _hboxes = {b.name: b for b in _seated(
        os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
        _hw2, _hh2)}
    _harea = pygame.Rect(*_hlay2.rect(_hboxes["list_area"].ref_rect))
    _hcfg = dict(_sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["list"])
    from screens.colony_summary import colonyheader as _hchdr
    _hcfg[_ctk.COLUMNS_KEY] = [(n[4:], _hboxes[n]) for n in
                               _hchdr.COLUMN_BOXES]
    _hcfg[_ctk.COLUMNS_SPAN_KEY] = (
        _hboxes["list_area"].ref_rect[0],
        _hboxes["list_area"].ref_rect[2])
    _hstep = _ctk.figure_step(_harea, _hcfg)
    # A SPRITE'S OWN INK ROW, because that is what the anchor
    # takes: the commonest master inks to row 23 of 28, so at
    # this step its last inked row is `24 * step - 1`.
    _hink = 24 * _hstep - 1
    _hband = _ctk.band_height(_harea, _hcfg)
    _hbands = _ctk.row_bands(_harea, _hcfg, _hlay2.scale, 10)
    assert _hbands, _hspec2
    for _bi, (_btop, _bh) in enumerate(_hbands[:3]):
        _want_y = _ctk.figure_origin_y(_btop, _bh, _hink)
        # EVERY y INSIDE THE BAND, not just its centre: the
        # pointer is wherever the hand is, and the whole point is
        # that the cluster no longer depends on where in the row
        # it happens to be.
        for _py in (_btop, _btop + _bh // 2, _btop + _bh - 1):
            _got = _ctk.held_figure_y(
                _harea, _hcfg, _hlay2.scale, 10,
                (_harea.x + 10, _py), _hstep, _hink)
            assert _got == _want_y, (
                f"{_hspec2} band {_bi}: a pointer at y {_py} hangs "
                f"the cluster at {_got} and that row's figures are "
                f"at {_want_y} — band {_bh}, step {_hstep}")
    # AND OUTSIDE THE LIST THE TRANSCRIPTION IS UNTOUCHED. That is
    # most of the screen, and it is the only place the original's
    # own picture can be compared at all.
    _out = _harea.bottom + 40
    assert _ctk.held_figure_y(
        _harea, _hcfg, _hlay2.scale, 10, (_harea.x + 10, _out),
        _hstep, _hink) == _out + _hzt.CLUSTER_FIGURE_OFFSET[1] * _hstep, (
        f"{_hspec2}: outside the list the cluster no longer hangs "
        f"at the transcribed offset (colmove.cpp:7-37)")
    # ── AND THE SPRITE SITS ON THE BAND'S FLOOR, EVERY ROW ──
    #
    # **THE ANCHOR MOVED FROM THE TOP TO THE BOTTOM — 12
    # September 2026, Data's decision, and it is a DEVIATION.**
    # The original anchors at the top, three native px under its
    # band's own first row; its band is 31 rows against a 28 row
    # sprite. Ours is `list_area` divided by ten, so the slack is
    # 2 px at 1920x1080 and 17 at 3440x1371 — and all of it used
    # to sit UNDER the figures, which is the float. The rule is
    # `colonytrack.figure_origin_y` and this is every band of it,
    # not the first three: a rule that held for row 0 and not for
    # row 9 is what a per-row assertion catches.
    for _bi, (_btop, _bh) in enumerate(_hbands):
        _floor = _btop + _bh - 1 - _ctk.PLATE_LINE
        # Both ink rows the set actually holds: 23 of 28 for 51
        # masters and 24 for the three Bulrathi. Both must land on
        # the SAME floor — that is what anchoring by ink buys and
        # what a canvas anchor cannot give.
        for _ink in (24 * _hstep - 1, 25 * _hstep - 1):
            _fb = _ctk.figure_origin_y(_btop, _bh, _ink) + _ink
            assert _fb == _floor, (
                f"{_hspec2} band {_bi}: a sprite inking to row "
                f"{_ink} ends at {_fb} and the plate's inner "
                f"floor is {_floor}")
            assert _ctk.figure_origin_y(_btop, _bh, _ink) >= _btop, (
                f"{_hspec2} band {_bi}: a sprite inking to row "
                f"{_ink} at step {_hstep} does not fit a {_bh} px "
                f"band — figure_step chose a step it cannot hold")
    _hf_seen.append((_hspec2, _hband, _hstep))
# ── AND THE PIXELS AGREE WITH THE ARITHMETIC ────────────────
# A held figure and a row figure of the same master must ink on
# the same top row. **TWO SIZES SINCE 12 September 2026** — the
# one the arithmetic was wrong at, and 3440x1371, which is what a
# single 3440x1440 display actually GRANTS for the two largest F9
# options (`App._set_mode` measured it), and where the float was
# reported a second time. The arithmetic above covers four sizes;
# the blit is measured at the two whose band leaves the sprite the
# most slack, because a y that is right and a blit that ignores it
# look identical in the arithmetic and not on screen.
def _held_ink_at(_W, _H):
    """Every figure's LOWEST INKED PIXEL, out of the render.

        **THE ARITHMETIC CANNOT ANSWER THIS ONE.** The anchor was
        moved to the band's floor on 12 September 2026 and the
        figures still floated at every size, because the canvas is
        not the figure: a master inks to row 23 of 28 (24 for the
        three Bulrathi) and the transparent tail — 8 device px at
        step 2, 16 at step 4 — sat under every sprite. Every
        arithmetic assertion was green while it did. So this reads
        the pixels: for every band that has figures, the lowest lit
        row inside each job column must be the plate's INNER FLOOR,
        exactly, and the held cluster's must be the same row.
        """
    _hd_app, _hd_screen = _plv.build_screen(_W, _H)
    _hd_app.dispatcher.switch_to("colony_summary")
    _hd_screen.enter(None)
    _hd_screen.update(_plv._Snapshot(_plv.COLONIES))
    _hd_area, _hd_cfg, _hd_scale, _hd_n = _hd_screen._list_view()
    _hd_step = _ctk.figure_step(_hd_area, _hd_cfg)
    from screens.colony_summary import colonyfigures as _hcfig
    _hd_set = _hcfig.set_for(_hd_screen, _hd_area, _hd_cfg)
    if _hd_set is None or _hd_set.state != "ok" or not _hd_screen._rows:
        report(f"figure floors at {_W}x{_H}: the figure set is not "
               f"extracted on this disk, so only the arithmetic "
               f"above is measured")
        return
    _hd_bands = _ctk.row_bands(_hd_area, _hd_cfg, _hd_scale, 10)
    _hd_cols = _ctk.columns(_hd_area, _hd_cfg)
    _hd_jobs = [_hd_cols[_k] for _k in ("farmers", "workers",
                                        "scientists")]
    import core.mouse as _hd_m

    def _render(_ptr):
        _hd_saved = _hd_m.pos
        _hd_m.pos = lambda: _ptr
        try:
            _s2 = pygame.Surface((_W, _H))
            _s2.fill((0, 0, 0))
            _hd_screen.render(_s2)
        finally:
            _hd_m.pos = _hd_saved
        # ABOVE THE PLATE, NOT ABOVE BLACK. The cell plate's own
        # line is `panel.thin_border`, (55, 65, 85), which sums to
        # 205 and runs along every band's edge — a threshold that
        # caught it would measure the plate and call it a figure.
        # The masters are the game's own palette and are brighter.
        return pygame.surfarray.array3d(_s2).transpose(
            1, 0, 2).sum(axis=2) > 260

    # ── THE ROWS, with nothing in hand ──────────────────────
    #
    # PER CELL, AND ONLY WHERE A FIGURE IS DRAWN. A column is not
    # the unit: the farmers column of a `max_farms == 0` colony
    # carries "No Farming" and nothing else, and its text ends 23
    # px above the floor perfectly correctly. `row_boxes` gives
    # the same cell rects the renderer blits into, and the row's
    # own cells say which of them have a sprite.
    _hd_lit = _render((0, 0))
    _hd_seen = 0
    for _bi, (_btop, _bh) in enumerate(_hd_bands):
        if _bi >= len(_hd_screen._rows):
            continue
        _row = _hd_screen._rows[_bi]
        _boxes = _ctk.row_boxes(_hd_area, _hd_cfg, _hd_scale, _row,
                                (_btop, _bh))
        _floor = _btop + _bh - 1 - _ctk.PLATE_LINE
        _cells = _row.get("cells") or ()
        for _job, _ix, _crect in _boxes.cells:
            if _job >= len(_cells) or _ix >= len(_cells[_job]):
                continue
            _fname = _cells[_job][_ix].figure
            if _fname is None or _hd_set.get(_fname) is None:
                continue
            _ys = np.where(_hd_lit[_btop:_btop + _bh,
                                   _crect.x:_crect.x + _crect.w]
                           .any(axis=1))[0]
            if not len(_ys):
                continue
            _hd_seen += 1
            assert _btop + int(_ys.max()) == _floor, (
                f"{_W}x{_H} band {_bi}, cell at x {_crect.x} "
                f"({_fname}): its lowest inked pixel is at "
                f"{_btop + int(_ys.max())} and the plate's inner "
                f"floor is {_floor} — "
                f"{_floor - _btop - int(_ys.max())} px of empty "
                f"band under the figure, which is the float")
    assert _hd_seen >= 20, (
        f"{_W}x{_H}: only {_hd_seen} figure cell(s) were measured "
        f"— a green run over an empty list asserts nothing")

    # ── AND THE CLUSTER IN HAND, on the same floor ──────────
    from screens.colony_summary import colonypick as _hd_cp
    _hd_loaded = _hd_cp.pops_of(_plv._Snapshot(_plv.COLONIES),
                                _hd_screen._rows[3]["index"])
    _hd_pick = _hd_cp.pick_at(_hd_loaded[0], _hd_loaded[1], 0, 2,
                              _hd_screen._rows[3]["index"], 3, "name")
    assert not isinstance(_hd_pick, _hd_cp.Refusal), _hd_pick
    _hd_screen._move.pick = _hd_pick
    _hd_screen._rebuild_rows()
    _hd_top, _hd_bh = _hd_bands[1]
    _hd_ptr = (_hd_cols["farmers"][0] + 40, _hd_top + _hd_bh // 2)
    _hd_lit = _render(_hd_ptr)
    _floor = _hd_top + _hd_bh - 1 - _ctk.PLATE_LINE
    # To the RIGHT of the pointer, which is where `Draw_Cluster_`
    # puts it (+5 per step); the row's own figures start at the
    # column's left edge.
    _held = _hd_lit[_hd_top:_hd_top + _hd_bh,
                    _hd_ptr[0] + 4:_hd_ptr[0] + 4 + 28 * _hd_step]
    _ys = np.where(_held.any(axis=1))[0]
    assert len(_ys), f"{_W}x{_H}: no held figure ink beside the pointer"
    assert _hd_top + int(_ys.max()) == _floor, (
        f"{_W}x{_H}: the held cluster's lowest inked pixel is at "
        f"{_hd_top + int(_ys.max())} and the row's is {_floor} — "
        f"a figure in hand and a figure in a row are on different "
        f"lines")
    _hd_screen._move.pick = None
    _hd_screen._rebuild_rows()
    report(f"figure floors at {_W}x{_H}: {_hd_seen} cells and the "
           f"held cluster, all on the plate's inner floor "
           f"(band {_hd_bh}, step {_hd_step})")

for _hd_W, _hd_H in ((1920, 1080), (2560, 1440), (3440, 1371),
                     (3840, 2160)):
    _held_ink_at(_hd_W, _hd_H)
report("held cluster: " + ", ".join(
    f"{_s} band {_b} step {_st}" for _s, _b, _st in _hf_seen))
ok("figures sit on the plate's inner floor, row and held alike "
   "(four resolutions, every band, measured out of the render; "
   "outside the list the transcribed pointer offset is untouched)")
