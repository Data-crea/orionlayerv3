#!/usr/bin/env python3
"""How long a drop takes, and which side of the wire owns it.

    python tools/colony_drop_timing.py --expect reference --drops 10

**THIS MEASURES THE CLICK CHAIN, WHICH THE HD SCREEN NO LONGER
USES — 10 September 2026.** Fundament 52 replaced it with one
`MSG_SET_JOBS` command; `colonysend` sends that and steers no
window. The chain still exists in the ENGINE, and this tool drives
it directly through injected clicks (via `colony_move_hd`), so it
still runs and still measures what it always did. What it no longer
measures is what OrionLayer does. Kept, because it is what produced
the before-value the command is judged against — the ten-drop table
in `v3_projektstatus.md` — and a measurement tool whose output is
still cited is not dead code. The step names below are the ENGINE's
path, not HD's.

**MEASURE BEFORE OPTIMISING.** Data sees a delay on the drop and none
on the pick. That asymmetry is predicted by the design and says
nothing about its size: the first click is LOCAL and sends nothing
(decision 47), so the whole wire sequence — re-sort, establish the
game's list window, pick up, drop — happens at the second click. What
this tool answers is how much of that is OrionLayer waiting and how
much is the game working, because the two have completely different
fixes and only one of them is ours.

WHAT IS TIMED, per drop:

  click        the player's second click reaches `MoveController`
  RESORT       `activate_field` for the sort key, and its wait
  ESTABLISH    the `_first` walk — `activate_field` per step
  PICK         `INJECT_CLICK` on the icon, and its wait
  DROP         `INJECT_CLICK` on the column, and its wait
  done         the screen sees the new split

Each step's wait is `colonysend.Wait`, which is a PREDICATE plus a
floor of `wire_protocol.EFFECT_PAIRS` state and visual messages. The
floor is ours and the predicate is the game's, so the two are
reported separately: a step that spent its whole time on the floor is
an OrionLayer cost, and one that sat past the floor waiting for its
predicate was waiting for the game.

**THE SNAPSHOT CADENCE IS THE UNIT EVERYTHING ELSE IS IN.**
`ext::Tick()` runs from `fields::Get_Input_()`, so a snapshot arrives
once per game input frame and nothing can be observed faster than
that. It is measured here rather than assumed, because every "HD
share" below is really "how many cadences did our own floor cost".

THE GAME'S OWN FLOOR, for comparison: `Get_Input_()` consumes ONE
input per frame, and a pick and a drop are DOWN+UP each
(`INJECT_CLICK` needs both; DOWN alone hangs the game), so four game
frames is the minimum before `Send_Cluster_` has even been reached —
plus the empire-wide food redistribution it always ends in
(`Pass_Out_Imports_`, fundament section 3).

Every drop is a REAL move and is followed by a move back, with the
colony records checked against the `.GAM` at the end — see
`colony_roundtrip`.
"""
import argparse
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screens.colony_summary import colonypick, colonysend  # noqa: E402

import colony_move_hd as base  # noqa: E402
from colony_roundtrip import bytes_of  # noqa: E402
from fixtures import verify_colonies  # noqa: E402


STATE_NAMES = {}


def name_of(st):
    if not STATE_NAMES:
        for attr in dir(colonysend):
            val = getattr(colonysend, attr)
            if attr.isupper() and isinstance(val, int):
                STATE_NAMES[val] = attr
    return STATE_NAMES.get(st, str(st))


class Trace:
    """Timestamps for one drop, and the traffic that arrived."""

    def __init__(self, client):
        self.client = client
        self.marks = []
        self.t0 = time.monotonic()
        self.s0 = dict(client.stats)

    def mark(self, label):
        self.marks.append((label, time.monotonic() - self.t0,
                           dict(self.client.stats)))

    def rows(self):
        """Time SPENT IN each state, not time until it was entered.

        **THE FIRST VERSION OF THIS LABELLED THE OTHER ONE, and the
        table read plausibly either way** — corrected 9 September
        2026 when RESORT appeared to complete in 27 ms against a
        53.6 ms snapshot cadence and a two-message floor, which is
        impossible and was the tell. A mark is taken when a state is
        ENTERED, so the interval that follows a mark belongs to the
        state the mark names; attaching it to the mark itself
        attributes every step's cost to the step after it. Nothing
        about the numbers looked wrong — they summed to the total and
        every one of them was a real interval.
        """
        out = []
        for i, (label, t, s) in enumerate(self.marks):
            if i + 1 < len(self.marks):
                nt, ns = self.marks[i + 1][1], self.marks[i + 1][2]
            else:
                nt, ns = t, s
            out.append({
                "label": label,
                "at": t,
                "step": nt - t,
                "states": ns["state"] - s["state"],
                "visuals": ns["visual"] - s["visual"],
            })
        return out


def cadence(app, seconds=3.0):
    """Seconds between STATE_SNAPSHOTs, measured, not assumed."""
    stamps = []
    start = time.monotonic()
    last = app.client.stats["state"]
    while time.monotonic() - start < seconds:
        base.pump(app, 1)
        now = app.client.stats["state"]
        if now != last:
            stamps.append(time.monotonic())
            last = now
    if len(stamps) < 3:
        return None, len(stamps)
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    return statistics.median(gaps), len(stamps)


def one_drop(app, screen, row_index, job, cell, target_job):
    """Pick, drop, and time every state the send passes through."""
    tr = Trace(app.client)
    xy = base.square_xy(screen, row_index, job, cell)
    if xy is None:
        return None, "the row is not drawn"
    tr.mark("pick click (local)")
    base.click_at(app, *xy)
    if screen._move.pick is None:
        return None, f"no selection ({screen._move.message!r})"
    tr.mark("held")

    area, cfg, scale, _n = screen._list_view()
    rect = None
    from screens.colony_summary import colonylist
    top, row_h = colonylist.row_bands(
        area, cfg, scale, _n - screen._first)[row_index - screen._first]
    for tj, r in colonylist.drop_targets(area, cfg, scale,
                                         screen._rows[row_index]):
        if tj == target_job and r.width:
            rect = (r.centerx, top + row_h // 2)
    if rect is None:
        return None, "no drop rect"

    tr.mark("drop click")
    base.click_at(app, *rect)
    seen = None
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        base.pump(app, 1)
        send = screen._move.send
        cur = name_of(send.state) if send is not None else "finished"
        if cur != seen:
            tr.mark(cur)
            seen = cur
        if send is None:
            break
    return tr, screen._move.message or ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--expect", default="reference")
    ap.add_argument("--drops", type=int, default=10)
    ap.add_argument("--row-name", default="Blucher II")
    args = ap.parse_args()

    from main import App
    app = App()
    if not app.connected:
        print("no game on the extension port")
        return 1
    if not base.wait_for(app, lambda: (
            app.dispatcher.active is not None
            and getattr(app.dispatcher.active, "SCREEN_NAME", "")
            == "colony_summary"
            and app.dispatcher.active._rows), 15.0, "the colony summary"):
        print("the game is not on the colony summary")
        return 1
    screen = app.dispatcher.active
    if not base.identify(app.client.state, args.expect):
        return 1
    if not verify_colonies(app.client.state, args.expect,
                           {r["index"]: r["name"] for r in screen._rows}):
        return 1

    gap, n = cadence(app)
    if gap is None:
        print(f"only {n} snapshots in 3 s — the game is not talking, so "
              f"nothing below would be a measurement")
        return 1
    print(f"\nsnapshot cadence: {gap * 1000:.0f} ms median over {n} "
          f"snapshots ({1 / gap:.1f}/s)")
    print(f"  `ext::Tick()` runs from `Get_Input_()`, so this IS the "
          f"game's input frame; nothing can be observed faster")
    print(f"  our own floor per waiting step is "
          f"{colonysend.EFFECT_PAIRS} state + "
          f"{colonysend.EFFECT_PAIRS} visual messages = "
          f"{colonysend.EFFECT_PAIRS * gap * 1000:.0f} ms at this cadence")

    target = base.choose(screen, app.client.state, None, args.row_name)
    if target is None:
        print("no row this save can prove a move on")
        return 1
    row_index, cell, job, target_job, _pick, _plan, _mf = target
    print(f"\nten drops on row {row_index} "
          f"{screen._rows[row_index]['name']!r}, column {job} <-> "
          f"{target_job}, alternating so the array returns")

    start_bytes = bytes_of(app)
    traces = []
    src, dst = job, target_job
    for i in range(args.drops):
        loaded = colonypick.pops_of(app.client.state,
                                    screen._rows[row_index]["index"])
        icons = __import__("screens.colony_summary.colonyicons",
                           fromlist=["x"]).icon_pops(loaded[0], loaded[1],
                                                     src)
        if not icons:
            print(f"  drop {i + 1}: column {src} is empty, stopping")
            break
        tr, note = one_drop(app, screen, row_index, src,
                            len(icons) - 1, dst)
        if tr is None:
            print(f"  drop {i + 1} failed: {note}")
            return 1
        total = tr.marks[-1][1]
        traces.append((i + 1, src, dst, total, tr))
        print(f"  drop {i + 1:2d}  {src} -> {dst}  {total * 1000:7.0f} ms")
        src, dst = dst, src

    if not traces:
        return 1

    print("\nwhere the time goes, median over "
          f"{len(traces)} drops (ms):")
    per_label = {}
    for _i, _s, _d, _t, tr in traces:
        for r in tr.rows():
            per_label.setdefault(r["label"], []).append(
                (r["step"], r["states"], r["visuals"]))
    order = [lbl for _i, _s, _d, _t, tr in traces[:1]
             for lbl in (r["label"] for r in tr.rows())]
    print(f"  {'step':<22s} {'ms':>7s} {'states':>7s} {'visuals':>8s}"
          f"  {'floor?':>7s}")
    for lbl in order:
        vals = per_label.get(lbl, [])
        if not vals:
            continue
        ms = statistics.median(v[0] for v in vals) * 1000
        st = statistics.median(v[1] for v in vals)
        vi = statistics.median(v[2] for v in vals)
        floor = ("yes" if st <= colonysend.EFFECT_PAIRS
                 and vi <= colonysend.EFFECT_PAIRS else "past it")
        print(f"  {lbl:<22s} {ms:7.0f} {st:7.0f} {vi:8.0f}  {floor:>7s}")

    totals = [t for _i, _s, _d, t, _tr in traces]
    print(f"\ntotal per drop: median {statistics.median(totals) * 1000:.0f} "
          f"ms, min {min(totals) * 1000:.0f}, max {max(totals) * 1000:.0f}")

    # ── THE TWO SHARES ───────────────────────────────────────────
    waiting = []
    for _i, _s, _d, _t, tr in traces:
        rows = tr.rows()
        w = sum(r["step"] for r in rows
                if r["states"] <= colonysend.EFFECT_PAIRS
                and r["visuals"] <= colonysend.EFFECT_PAIRS
                and r["label"] not in ("pick click (local)", "held"))
        waiting.append(w)
    med_total = statistics.median(totals)
    med_floor = statistics.median(waiting)
    print(f"\nHD share (steps that ended ON our own "
          f"{colonysend.EFFECT_PAIRS}-message floor, i.e. the game had "
          f"already answered): {med_floor * 1000:.0f} ms of "
          f"{med_total * 1000:.0f} = {med_floor / med_total * 100:.0f} %")
    print(f"GAME share (steps that ran PAST the floor waiting for their "
          f"predicate): {(med_total - med_floor) * 1000:.0f} ms = "
          f"{(1 - med_floor / med_total) * 100:.0f} %")
    print(f"\nthe game's own floor, for scale: a pick and a drop are "
          f"DOWN+UP each and `Get_Input_()` takes one input per frame, "
          f"so 4 frames = {4 * gap * 1000:.0f} ms before "
          f"`Send_Cluster_` is reached at all")

    end_bytes = bytes_of(app)
    same = end_bytes == start_bytes
    print(f"\nthe array returned to where it started: {same}")
    verify_colonies(app.client.state, args.expect,
                    {r["index"]: r["name"] for r in screen._rows})
    return 0


if __name__ == "__main__":
    sys.exit(main())
