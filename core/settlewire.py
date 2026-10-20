"""The last settlement's outcome on the wire — open fix 103, "STLR" (work order 316).

    "STLR"  (`doc/ext_settle_anywhere.patch`): written after MREL's place,
            only on SCREEN_COLONY and SCREEN_COLONY_SUMMARY. A version byte
            (1), uint16 sequence (0 before the first long-form
            MSG_SETTLE_POPS), int16 source and destination colony, uint8
            listed, uint8 settled, uint8 stop, uint8 job refusal, uint8
            extra notice, then the fifteen bytes of
            `s_settler_settle_result` in its own order for the last pop
            asked about.

WHY: the original answers a settlement with a text box — "Settlers Failed."
with one line per reason of the pop it stopped on, then "Settlers Depart"
with the number sent and the ETA (`Send_Cluster_`, colmove.cpp:366-372,
:454-460, :482-522) — and a command may not open a box (fundament 52), so
the engine reports what it did and HD draws the boxes
(`screens/colony/colxferflow.py`). The sequence is what a client waits on:
a long-form command is reported even when its list is refused (stop 4),
so a wait never has to guess from the colonies' records alone.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none, and HD offers only open fix 92's move to a colony at
the same star from the colony screen.
"""
import struct as _st

HEAD = "<BHhhBBBBB"
#: `s_settler_settle_result` (orion2.h), member for member — the bytes
#: STLR sends, in this order.
RESULT_FIELDS = (
    "can_settle", "dest_owner_mismatch", "source_blockaded",
    "source_space_anomaly", "dest_is_outpost", "only_one_pop_left",
    "insufficient_freighters", "max_settlers_in_transit", "source_plague",
    "no_room_at_destination", "field10_0xa", "dest_blockaded",
    "dest_space_anomaly", "eta_turns", "selected_pop_flag_0x400")
SIZE = _st.calcsize(HEAD) + len(RESULT_FIELDS)

#: Why a long-form settlement stopped (`SETTLE_STOP_*`, ext_api.cpp).
STOP_NONE, STOP_REFUSED, STOP_DECLINED, STOP_JOB, STOP_LIST = range(5)
#: Which of `Give_Colonist_New_Job_`'s rules stopped it.
JOB_NATIVE, JOB_ANDROID, JOB_FULL = 1, 2, 3
#: The answers byte of the long form.
YES_PAST_LIMIT, YES_ETA = 1, 2
#: The job byte of the long form that keeps each colonist's job.
KEEP_JOB = -1


def parse(gs, data, pos):
    """Read STLR at `pos` into `gs.settle_outcome` (None when absent or
    short, else a dict). Returns the new position."""
    gs.settle_outcome = None
    if data[pos:pos + 4] != b"STLR" or pos + 4 + SIZE > len(data):
        return pos
    (version, seq, source, dest, listed, settled, stop, job_refusal,
     extra) = _st.unpack_from(HEAD, data, pos + 4)
    if version != 1:
        return pos
    at = pos + 4 + _st.calcsize(HEAD)
    result = dict(zip(RESULT_FIELDS, data[at:at + len(RESULT_FIELDS)]))
    gs.settle_outcome = {
        "seq": seq, "source": source, "dest": dest, "listed": listed,
        "settled": settled, "stop": stop, "job_refusal": job_refusal,
        "extra_notice": bool(extra), "result": result}
    return pos + 4 + SIZE


def build(seq=0, source=-1, dest=-1, listed=0, settled=0, stop=STOP_LIST,
          job_refusal=0, extra=0, **result):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"STLR" + _st.pack(HEAD, 1, seq, source, dest, listed, settled,
                              stop, job_refusal, 1 if extra else 0) + \
        bytes(int(result.get(k, 0)) & 0xFF for k in RESULT_FIELDS)


def available(state):
    """Does the engine carry open fix 103 — the long form and its
    outcome? (The block comes on the two colony screens only.)"""
    return getattr(state, "settle_outcome", None) is not None
