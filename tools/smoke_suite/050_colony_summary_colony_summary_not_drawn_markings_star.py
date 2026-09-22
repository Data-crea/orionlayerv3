# smoke-suite area: colony_summary
#
# Part of the OrionLayer smoke suite — 050_colony_summary_colony_summary_not_drawn_markings_star.py.
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
#   - colony summary NOT DRAWN markings (star blockade reachable, colony event not on the wire, both s


# ── The colony row's two marked deviations ──
# Neither changes a pixel; both exist so the next reader takes
# them as choices rather than as fidelity.
#
#   the NAME is right-aligned  — the original left-aligns it,
#       Squeeze_Formatted_Paragraph_Centered_ (colsum.cpp:582)
#       passing 0 = JUSTIFY_LEFT through bill.cpp:210, with
#       "Centered_" meaning center_y ONLY (bill.cpp:205)
#   the DETAIL LINE is per row — the original draws it once for
#       the selected colony (colsum.cpp:1155)
_cl_src2 = open(os.path.join(SCREENS_DIR, "colony_summary",
                             "colonylist.py"), encoding="utf-8").read()
_fund_src = read_doc(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                  "v3_fundament.md"))
# THE FIRST IS RETIRED — 8 September 2026. The name is
# left-aligned now, which is what the original does; the column
# became a box, the widest producible name fits it, and the trade
# that bought right alignment is over. The READING stays cited on
# both sides, because that is the expensive half: `Centered_` is
# about the vertical axis and a reader who trusts the name of the
# function will file the alignment as transcribed without opening
# bill.cpp.
for _cite in ("colsum.cpp:582", "bill.cpp:210", "JUSTIFY_LEFT"):
    assert _cite in _cl_src2, (
        f"colonylist.py no longer cites {_cite} — the name's "
        f"alignment is a transcription now and the evidence that "
        f"it is one has to travel with it")
    assert _cite in _fund_src, (
        f"the fundament no longer cites {_cite} for the name's "
        f"alignment")
assert "RETIRED" in _fund_src or "retired" in _fund_src, (
    "decision 45 no longer says the right-aligned name was "
    "retired — a marking that disappears without a sentence is "
    "indistinguishable from one nobody noticed")
assert "**45." in _fund_src, (
    "the fundament no longer carries the colony row's two "
    "deviations as a decision")
# The detail line's omission is deliberate and says what it omits.
assert "colsum.cpp:1196" in _cl_src2, (
    "colonylist.py no longer names where the original's seven "
    "values come from, so 'a SUBSET' is a claim without a source")

# ── Two states the original's row carries and ours does not ──
# Neither is a task and neither is on the open-fixes list; they
# are marked because an omission nobody wrote down cannot be told
# apart from one nobody noticed, and both were found by reading
# Draw_Colony_Summary_For_Colony_ for something else.
#
# The check has the same shape as the marking check the fundament
# asks for: refuse a marking that does not say what the ORIGINAL
# does, so the note records a reason rather than carrying a label.
_cr_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                            "colonyrows.py"), encoding="utf-8").read()
assert "NOT DRAWN" in _cr_src, (
    "colonyrows.py no longer carries a NOT DRAWN section — the "
    "star blockade and the colony event are two states of the "
    "original's row string that the HD row does not draw")
for _cite in ("colsum.cpp:557-569", "colsum.cpp:562", "blockaded"):
    assert _cite in _cr_src, (
        f"the blockade marking no longer cites {_cite!r}, so it "
        f"names a state without naming where the original draws it")
for _cite in ("colsum.cpp:553", "events.cpp:635",
              "Colony_Has_Event_"):
    assert _cite in _cr_src, (
        f"the colony-event marking no longer cites {_cite!r}")
# The two are NOT the same kind of absence and the note must keep
# them apart: blockaded is a verified field on the wire, events
# are not on the wire at all. Collapsing them into one line is
# how the reachable one would stop looking buildable.
assert "ext_api.cpp:53-136" in _cr_src, (
    "the colony-event marking no longer names where the snapshot "
    "is written, which is the only evidence that _event_data is "
    "absent from it rather than merely unread")
from core.structs import star as _star_spec
assert any(_f[0] == "blockaded" for _f in _star_spec.SPEC.fields), (
    "s_star_data.blockaded is gone from the verified spec, so the "
    "blockade marking claims a field that no longer exists")
assert _star_spec.SPEC.verified, "star spec is no longer verified"
# And events really are absent from the snapshot: assert it
# against GameState rather than against the note, so the day Joes
# serializes them this fails and the marking gets revisited.
from core.game_state import GameState as _GS
# `ng_random_events` is the New Game screen's own toggle
# (ext_api.cpp:135) and is deliberately not what this looks for:
# what the marking claims absent is the EVENTS::_event_data[]
# array, which would arrive as a record array like every other
# one — a `*_raw` member, or a parsed list beside `stars`.
_gs_attrs = [_a2 for _a2 in dir(_GS()) if not _a2.startswith("_")]
_ev = [_a2 for _a2 in _gs_attrs
       if "event" in _a2.lower() and not _a2.startswith("ng_")]
assert not _ev, (
    f"GameState grew an events member {_ev} — the colony-event "
    f"marking says the snapshot carries none, and that is now "
    f"wrong. Re-read colsum.cpp:553 and decide whether the row "
    f"can draw it before deleting the marking.")
ok("colony summary NOT DRAWN markings (star blockade reachable, "
   "colony event not on the wire, both sourced)")
