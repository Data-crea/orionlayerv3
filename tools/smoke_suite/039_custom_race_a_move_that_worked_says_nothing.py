# smoke-suite area: custom_race
#
# Part of the OrionLayer smoke suite — 039_custom_race_a_move_that_worked_says_nothing.py.
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
#   - a move that worked says nothing; the description survives a pick and a drop, and the stranded no


# ── A MOVE THAT WORKED SAYS NOTHING ─────────────────────────
#
# The original marks nothing on this screen. The only Fill_/Line_
# calls in colsum.cpp are the scroll thumb (:759-765) — no frame
# round a picked cell, none round the row it came from, and no
# notice after a drop. What it does instead is redraw the row:
# the pops left one column and are in another, and that IS the
# feedback. HD draws the same row from the same array.
#
# "{landed} moved" was drawn into `planet_info`, which is the
# LEFT HALF OF THE ORIGINAL'S OWN SCAN BOX — the description
# paragraph at native (13, 354, 80, 88),
# `Draw_Colony_Scan_Info_`, colsum.cpp:1155 — so every successful
# move evicted a transcription to report a thing already on
# screen. Data's two 1440p screenshots of 8 September 2026 are
# the pair: one with the paragraph, one with "1 moved" in its
# place.
assert "complete" not in _mv_words, (
    "layout.json move.complete is back — a success has no "
    "sentence, the row is the feedback")
class _Landed:
    landed, carried = 1, 0
assert _cp.message(_mv_words, _Landed(), 1) == "", (
    "a successful move still produces a sentence")
# A REFUSAL STILL SPEAKS — decision 33, and not an exception to
# the above: HD refuses before injecting so the player reads a
# reason instead of the silence the framebuffer would answer
# with, and the original's own answer is a BLOCKING text box
# (textbox.cpp:149). Transient, so `_render_info` takes the panel
# back on the next frame.
assert _cp.message(_mv_words, _cp.Refusal(_cm.REFUSE_JOB_FULL)), (
    "a refusal lost its sentence — decision 33 is what lets HD "
    "refuse before sending at all")

# ── THE DESCRIPTION SURVIVES A PICK AND A DROP ──────────────
# Asserted on the PIXELS of the panel, not on the message string:
# the fault was that something else was drawn there, and only the
# picture can say what a panel holds (the fundament's "a table
# says the data is right; only the picture says it is visible").
_pi_box = _scr_op.box_rect("planet_info")
_pi_rect = pygame.Rect(*app.layout.rect(_pi_box))

def _panel_ink():
    _s = pygame.Surface((1920, 1080))
    _s.fill((0, 0, 0))
    _scr_op.render(_s)
    _a = pygame.surfarray.array3d(
        _s.subsurface(_pi_rect)).sum(axis=2)
    return int((_a > 40).sum())

_scr_op._move.pick = None
_scr_op._move.message = ""
_scr_op._move.notice = ""
_scr_op._rebuild_rows()
_pi_idle = _panel_ink()
assert _pi_idle > 0, (
    "the description panel is empty before a move even starts")
# WITH A PICK HELD.
_pi_loaded = _cp.pops_of(_sel_snap, _scr_op._rows[0]["index"])
_pi_pick = _cp.pick_at(_pi_loaded[0], _pi_loaded[1], 0, 0,
                       _scr_op._rows[0]["index"], 0, "name")
if not isinstance(_pi_pick, _cp.Refusal):
    _scr_op._move.pick = _pi_pick
    _scr_op._rebuild_rows()
    assert _panel_ink() > 0, (
        "the description panel went blank while a cluster was "
        "held — a pick may not evict a transcription")
    _scr_op._move.pick = None
    _scr_op._rebuild_rows()
# AND AFTER A DROP THAT LANDED. `advance` is the path that used
# to set the sentence; it must leave the panel alone.
_pi_ctl = _scr_op._move
_pi_ctl.message = "leftover"
_pi_ctl.notice = ""
class _FakeSend:
    def __init__(self, st):
        self.state, self.reason = st, None
    def update(self, _state):
        pass
    finished = True
    @property
    def holding(self):
        return self.state == _cse.HOLDING
_pi_ctl.send = _FakeSend(_cse.DONE)
_pi_ctl.advance(_sel_snap, _mv_words)
assert _pi_ctl.message == "", (
    f"a completed move left {_pi_ctl.message!r} in the panel")
assert _pi_ctl.notice == "", "a completed move raised the notice"
assert _panel_ink() == _pi_idle, (
    "the description panel differs after a completed move")

# ── THE STRANDED NOTICE IS NEVER IN THAT PANEL ──────────────
# It is the one line that is neither a refusal nor a result, and
# it stands until the player presses RETURN — so unlike a refusal
# it would evict the paragraph for an unbounded time. Its own
# strip, over the top band of the list.
_pi_ctl.message = ""
_pi_ctl.send = _FakeSend(_cse.HOLDING)
_pi_ctl.advance(_sel_snap, _mv_words)
assert _pi_ctl.notice == _mv_words["stranded"], (
    f"a held cluster set notice={_pi_ctl.notice!r}")
assert _pi_ctl.message == "", (
    "the stranded line went into `message`, which is the "
    "description panel's guest slot")
_st_area = _scr_op._list_view()[0]
_st_surf = pygame.Surface((1920, 1080))
_st_surf.fill((0, 0, 0))
_pi_ctl.draw_notice(_st_surf, _st_area,
                    _scr_op._data.get("list", {}),
                    app.layout.font_size(_mv_words.get("font", 18)),
                    app.style, (255, 255, 255), (8, 11, 20))
_st_ink = pygame.surfarray.array3d(_st_surf).sum(axis=2)
_st_rows = [y for y in range(1080) if (_st_ink[:, y] > 40).any()]
_st_band = _ctk.band_height(_st_area, _scr_op._data.get("list", {}))
assert _st_rows, "the stranded notice drew nothing"
assert _st_area.y <= min(_st_rows) and \
    max(_st_rows) <= _st_area.y + _st_band, (
    f"the notice runs y {min(_st_rows)}..{max(_st_rows)}, outside "
    f"the top band {_st_area.y}..{_st_area.y + _st_band}")
assert not _pi_rect.collidepoint(_st_area.centerx, min(_st_rows)), (
    "the stranded notice reaches into planet_info")
# MARKED AT THE THREE HOMES, because an extension nobody can find
# is an extension that quietly becomes a transcription.
assert "HD EXTENSION" in _mv_words.get("_hd_extension_notice", ""), (
    "layout.json move._hd_extension_notice does not mark it")
_mu_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonymoveui.py"), encoding="utf-8").read()
assert "HD EXTENSION" in _mu_src.split("self.notice")[0][-900:], (
    "colonymoveui does not mark the notice where it is declared")
assert "_hd_extension_notice" in _status_txt or \
    "stranded notice" in _status_txt, (
    "v3_projektstatus.md does not carry the stranded notice's "
    "marking")
_pi_ctl.message = ""
_pi_ctl.notice = ""
_pi_ctl.send = None
_pi_ctl.pick = None
_scr_op._rebuild_rows()
ok("a move that worked says nothing; the description survives a "
   "pick and a drop, and the stranded notice has its own strip "
   "(marked at three homes)")
