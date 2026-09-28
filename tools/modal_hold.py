#!/usr/bin/env python3
"""How long HD holds before a modal box, and where the time goes — work order 186, part 4.

    python tools/modal_hold.py designer [--repeat N]   # the Ship Designer's shield warning (id 3)
    python tools/modal_hold.py colony_base            # SAVE4's TURN: the colony-base choice (id 0)
    python tools/modal_hold.py combat                 # SAVE5's TURN: the combat choice (id 12)

MEASUREMENT ONLY. Nothing in the product is changed or patched; the tool
drives the running App through its window (every input a posted pygame
event, as a player's) and records, per modal:

    input      the HD input's own time (`core.inputlog`)
    engine     every STATE snapshot's arrival, with its screen and live
               field list (a wrapper around the client's message handler)
               — the first one carrying the box's list is when the engine
               had built it; the gap before it is the engine's silence
    gate       every presented frame (`core.frametrace`): `hold` frames are
               the hand-over gate holding HD's last frame, the first `net`
               frame is the box's picture shown — with the snapshot count
               each frame was presented at
    pacing     the gaps between snapshots while the box stands

Each run writes `modal_hold.json` into its evidence folder
(`ORIONLAYER_EVIDENCE_FOLDER`, default `work_order_186`). The caller starts
the engine with `tools/engine_start.py --guard` and verifies the guard
after; the TURN scenarios rewrite SAVE10 (the autosave) and are answered
with NOTHING — the engine is stopped with the box still up.
"""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
os.environ.setdefault("ORIONLAYER_INPUT_LOG", "1")
os.environ.setdefault("ORIONLAYER_EVIDENCE_FOLDER", "work_order_186")

import vdisplay  # noqa: E402
vdisplay.headless_clients()

import pygame  # noqa: E402

import flash_walk  # noqa: E402
import livesend  # noqa: E402
from core.wire_protocol import MSG_FIELDS, MSG_STATE  # noqa: E402

RECORD_S = 9.0


def live_sig(fields):
    """A list's shape: every live field's type and rect, in order."""
    return tuple((f.field_type, f.x, f.y, f.x_end, f.y_end)
                 for f in (fields or []) if getattr(f, "index", 0) != 0)


class Wire:
    """Every STATE snapshot as it arrives: time, screen, live list — and
    every FIELD_LIST (`lists`), which the engine sends on its own when the
    list changes and which can arrive before the next STATE."""

    def __init__(self, app):
        self.app, self.rows, self.lists = app, [], []
        real = app.client._handle_message

        def spy(kind, flags, payload):
            out = real(kind, flags, payload)
            if kind == MSG_FIELDS:
                self.lists.append({"t": time.monotonic(),
                                   "snap": app.client.stats.get("state"),
                                   "sig": live_sig(app.client.state.fields)})
            if kind == MSG_STATE:
                st = app.client.state
                self.rows.append({"t": time.monotonic(),
                                  "snap": app.client.stats.get("state"),
                                  "screen": st.current_screen,
                                  "sig": live_sig(st.fields)})
            return out
        app.client._handle_message = spy


def timeline(t0, wire, frames, before_sig, until):
    """The numbers of one modal, from the input at `t0`."""
    snaps = [r for r in wire.rows if t0 <= r["t"] <= until]
    lists = [r for r in wire.lists if t0 <= r["t"] <= until]
    new_list = next((r for r in lists if r["sig"] != before_sig), None)
    box = next((r for r in snaps if r["sig"] and r["sig"] != before_sig), None)
    fr = [f for f in frames if t0 <= f["t"] <= until]
    hold0 = next((f for f in fr if f["source"] == "hold"), None)
    net0 = next((f for f in fr if f["source"] == "net"), None)
    out = {"snapshots_recorded": len(snaps),
           "first_after_input": [(round(r["t"] - t0, 3), r["screen"], len(r["sig"]),
                                  r["sig"] == before_sig) for r in snaps[:5]]}
    if box is None:
        out["box"] = "no new list within the recording"
        return out
    pre = [r["t"] for r in snaps if r["t"] <= box["t"]]
    gaps_before = [b - a for a, b in zip([t0] + pre[:-1], pre)]
    during = [r["t"] for r in snaps if r["t"] >= box["t"] and r["sig"] == box["sig"]]
    gaps = [b - a for a, b in zip(during, during[1:])]
    if new_list is not None:
        out["engine_box_list_s"] = round(new_list["t"] - t0, 3)
        out["box_list_fields"] = len(new_list["sig"])
    out.update({
        "box_screen": box["screen"], "box_fields": len(box["sig"]),
        "engine_first_box_snapshot_s": round(box["t"] - t0, 3),
        "longest_silence_before_box_s": round(max(gaps_before), 3) if gaps_before else None,
        "snapshots_before_box": len(pre) - 1,
        "box_pacing_median_ms": round(1000 * statistics.median(gaps), 1) if gaps else None,
        "box_snapshots_per_s": round(1 / statistics.median(gaps), 2) if gaps else None,
    })
    if hold0:
        out["gate_hold_starts_s"] = round(hold0["t"] - t0, 3)
        out["gate_hold_kind"] = hold0["kind"]
        out["hold_first_snap"] = hold0["snap"]
    if net0:
        out["first_native_frame_s"] = round(net0["t"] - t0, 3)
        out["net_kind"] = net0["kind"]
        out["net_snap"] = net0["snap"]
        if hold0:
            out["held_snapshots"] = net0["snap"] - hold0["snap"]
            out["held_s"] = round(net0["t"] - hold0["t"], 3)
        out["box_snapshots_until_shown"] = net0["snap"] - box["snap"]
    return out


def attach(walk):
    """Give a walk (the flash walk's App, load and helpers) the recorder."""
    walk.wire = Wire(walk.app)

    def record(t0, before_sig, seconds=RECORD_S):
        end = t0 + seconds
        while time.monotonic() < end:
            walk.frame()
        return timeline(t0, walk.wire, list(walk.app._frame_trace.frames),
                        before_sig, end)
    walk.record = record
    return walk


def designer(w, repeat):
    from screens.ship_design import sdgeom as G
    from screens.build_queue import bqwire
    results = []
    gm = w.hd("galaxy_map")
    star, view = gm.home_star(), gm._map_view()
    before = len(w.st.fields or [])
    w.click(*view.to_screen(star.x, star.y))
    w.wait(lambda st: len(st.fields or []) != before, 20)
    w.settle(10)
    w.click_rect(w.own_colony_disc())
    assert w.wait(w.on_colony, 20)
    w.settle(20)
    assert w.open_popup("colony -> build_queue (CHANGE)")
    assert w.into_designer(1)
    for i in range(repeat):
        w.settle(30)
        f = w.field(G.SHIELD)
        assert f is not None and w.page_ready(w.st), "not on the designer's page — nothing sent"
        sig = live_sig(w.st.fields)
        t0 = time.monotonic()
        w.click_field(w.hd("ship_design"), (f.x, f.y, f.x_end, f.y_end))
        res = w.record(t0, sig)
        res["run"] = i + 1
        results.append(res)
        print(f"  designer run {i + 1}: {res}")
        full = next((x for x in w.st.fields or [] if (x.x, x.y, x.x_end, x.y_end) == (0, 0, 639, 479)), None)
        if full is not None and w.app._showing_original():
            w.click(960, 540)            # the box's full-screen field, through the picture
        assert w.wait(w.page_ready, 10), "the box did not close"
    c = w.field(G.CANCEL)
    w.transition("ship_design -> build_queue (Cancel)", "build_queue",
                 lambda: w.click_field(w.hd("ship_design"), (c.x, c.y, c.x_end, c.y_end)),
                 lambda st: st.current_screen == 25)
    w.popup_button("build_queue -> colony (Cancel)", bqwire.CANCEL, "colony", w.on_colony)
    w.transition("colony -> galaxy_map (ESC)", "galaxy_map",
                 lambda: w.key(pygame.K_ESCAPE), livesend.on_galaxy_map)
    return results


def turn(p, slot):
    flash_walk.SLOT = slot
    assert p.st.current_screen == 10, "not at the main menu — nothing sent"
    assert p.load(), "the load did not arrive"
    p.settle(30)
    assert livesend.on_galaxy_map(p.st), p.st.current_screen
    gm = p.hd("galaxy_map")
    sig = live_sig(p.st.fields)
    t0 = time.monotonic()
    p.click_rect(gm.nav_rect("turn"))
    res = p.record(t0, sig, seconds=12.0)
    print(f"  SAVE{slot} TURN: {res}")
    return [res]


def main(argv):
    from livedrive import close, hashes
    which = argv[0] if argv else "designer"
    repeat = next((int(a.split("=", 1)[1]) for a in argv if a.startswith("--repeat=")), 3)
    saves = hashes()
    if which == "designer":
        import design_walk
        p = attach(design_walk.DesignWalk((1920, 1080), f"P4_modal_{which}"))
    else:
        p = attach(flash_walk.Walk((1920, 1080), f"P4_modal_{which}"))
    p.run.wait_for(lambda st: st.current_screen >= 0, seconds=30, label="first")
    p.settle(40)
    if which == "designer":
        if p.st.current_screen == 10:
            p.load()
        results = designer(p, repeat)
    elif which == "colony_base":
        results = turn(p, 4)
    elif which == "combat":
        results = turn(p, 5)
    else:
        raise SystemExit(f"unknown scenario {which}")
    with open(os.path.join(p.run.dir, "modal_hold.json"), "w", encoding="utf-8") as fh:
        json.dump({"scenario": which, "results": results,
                   "wire": p.wire.rows, "lists": p.wire.lists}, fh, default=str)
    p.save({"notes": f"modal_hold {which}", **close(p.run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
