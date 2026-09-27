#!/usr/bin/env python3
"""Clicks into the gap: is an input lost while the engine's delay runs?

    python tools/gap_clicks.py TAG [--screens research,colony,popup]
                              [--reps N] [--offsets 0,50,...]

Work order 185, part 1. Open fix 42 (`doc/ext_input_delay_tick.patch`,
entry 42) lets the engine send a screen during its input delay, so the HD
screen appears while `fields::Get_Input_()` still returns 0 for the delay's
passes. The question the entry has to answer before Data can approve it:
**can the player's click land in that gap, and is it lost?**

THE METHOD. One trial = open the screen the player's way, take the moment
its FIRST HD frame was presented (flipped) as t0 (the frame trace: source hd, the
target screen on top, and the screen's own "can draw" state), then post the
player's input into the HD window at t0 + offset — a pygame event through
the product's front door, so HD decides what it sends — and read the wire
back for `OBSERVE` seconds:

    research  change mode's exit button (HD click) -> ACTIVATE_FIELD; the
              delay is 5 passes (tech.cpp `Set_Input_Delay_(5)`)
              taken = the wire leaves 36 for the map; lost = still 36
    colony    ESC on the colony screen -> ACTIVATE_FIELD on its ESC field
              (never CRUNCH, TOGGLE or field [0]); delay 3 passes
              (colony_main.cpp) — taken = the map; lost = still 1
    research_key / research_click   the same gap through SDL's queues:
              INJECT_KEY ESC and INJECT_CLICK on the exit button, what
              HD's safety net forwards for a screen it does not draw
    popup     the build popup's Auto Build radio (HD click) -> INJECT_CLICK,
              the SDL mouse path; delay 3 passes (colbldg.cpp) — read off
              the wire's `build_queue.auto_building` (open fix 39), every
              value it takes: flipped once = taken, never = lost, flipped
              and back = TAKEN TWICE

Every trial also records what HD did with the input (`core/inputlog`:
sent, or dropped and why), when the effect reached the wire (so a click
taken late shows WHEN the engine began to accept), and any screen the game
passed through that the effect does not explain.

The same tool runs on the patched scratch engine and on the unpatched one;
the caller starts each with `tools/engine_start.py [--engine ...]` and runs
liveguard around it. SAVE4 is loaded (scratch); nothing is saved. The
Auto Build flag a trial flips is flipped back before the next one, and the
popup is left with Cancel.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
os.environ.setdefault("ORIONLAYER_INPUT_LOG", "1")
os.environ.setdefault("ORIONLAYER_EVIDENCE_FOLDER", "work_order_185")

import vdisplay  # noqa: E402
vdisplay.headless_clients()

import pygame  # noqa: E402

import colony_accept  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402

from core import frametrace, researchnative  # noqa: E402
from core.config import TARGET_FPS  # noqa: E402

OFFSETS = (0, 25, 50, 75, 100, 150, 200, 300, 400, 500, 600, 800, 1000)
#: Seconds the wire is read after the input: longer than any delay (the
#: research panel's is 5 x 110 ms) plus the transition.
OBSERVE = 2.5
SCREENS = ("research", "research_key", "research_click", "colony",
           "popup")


class Gap(colony_accept.Accept):
    def __init__(self, tag):
        super().__init__((1920, 1080), tag)
        self.inlog = self.app._input_log
        assert self.inlog is not None, "the input log is off"
        self.measuring = False
        self.trials = []

    # ── the loop: the product's own while measuring ──────────────
    def frame(self):
        if not self.measuring:
            return super().frame()
        app = self.app
        app._handle_events()
        app._update()
        app._render()
        app.clock.tick(TARGET_FPS)

    def top(self):
        d = self.app.dispatcher
        return d.overlay_name or d.active_name

    def first_hd(self, target, ready, timeout=20.0):
        """Pump until the target's first HD frame; its presentation time."""
        mark = self.trace.mark()
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            self.frame()
            last = self.trace.frames[-1]
            if last["source"] == frametrace.HD and last["hd"] == target \
                    and ready():
                # PRESENTED, not recorded: the trace stamps a frame before
                # it is drawn, and a cold first frame takes ~0.3 s to draw.
                return time.monotonic(), len(self.trace.frames) - mark
        return None, None

    def wait_until(self, t_mono):
        while time.monotonic() < t_mono:
            self.frame()

    def observe(self, probe):
        """Every (t, screen, probe value) for OBSERVE seconds."""
        seen = []
        end = time.monotonic() + OBSERVE
        while time.monotonic() < end:
            self.frame()
            seen.append((time.monotonic(), self.st.current_screen, probe()))
        return seen

    # ── the three screens ────────────────────────────────────────
    def research_trial(self, offset):
        gm = self.hd("galaxy_map")
        scr = self.hd("research_change")
        x, y, w, h = gm.layout.rect(gm.box_rect("sb_research_text"))
        self.click(x + w // 2, y + h // 2)
        t0, frames = self.first_hd(
            "research_change",
            lambda: scr.state == "ok" and scr.exit_rect() is not None)
        if t0 is None:
            return {"error": "the research panel was not drawn"}
        ex = researchnative.window_rect(scr.exit_rect(), scr.layout)
        self.wait_until(t0 + offset / 1000)
        mark = len(self.inlog.entries)
        t_in = time.monotonic()
        self.click(ex[0] + ex[2] // 2, ex[1] + ex[3] // 2)
        seen = self.observe(lambda: None)
        left = next((t for t, s, _v in seen if s == 0), None)
        rec = {"t_input_after_hd": round(1000 * (t_in - t0), 1),
               "hd_input": self.inlog.entries[mark:mark + 2],
               "outcome": "taken" if left is not None else "lost",
               "effect_ms": round(1000 * (left - t_in), 1)
               if left is not None else None,
               "screens": sorted({s for _t, s, _v in seen})}
        if left is None:
            self._home()
        self.wait(lambda st: livesend.on_galaxy_map(st)
                  and self.app.dispatcher.overlay is None, 20)
        self.settle(30)
        return rec

    def research_raw_trial(self, offset, how):
        """The SDL paths inside the research gap: `INJECT_KEY` ESC (the
        exit's hotkey, tech.cpp) or `INJECT_CLICK` on the exit button —
        what HD's safety net sends for a screen it does not draw
        (`original_view.forward_click` / `forward_key`). Decided from the
        list read at that moment: the exit button must be in it."""
        gm = self.hd("galaxy_map")
        scr = self.hd("research_change")
        x, y, w, h = gm.layout.rect(gm.box_rect("sb_research_text"))
        self.click(x + w // 2, y + h // 2)
        t0, frames = self.first_hd(
            "research_change",
            lambda: scr.state == "ok" and scr.exit_rect() is not None)
        if t0 is None:
            return {"error": "the research panel was not drawn"}
        self.wait_until(t0 + offset / 1000)
        f = scr.exit_field()
        if f is None:
            return {"error": "no exit button in the list at the moment of "
                             "sending — nothing sent"}
        t_in = time.monotonic()
        if how == "key":
            self.app.client.inject_key(pygame.K_ESCAPE)
        else:
            self.app.client.inject_click((f.x + f.x_end) // 2,
                                         (f.y + f.y_end) // 2)
        seen = self.observe(lambda: None)
        left = next((t for t, s, _v in seen if s == 0), None)
        rec = {"t_input_after_hd": round(1000 * (t_in - t0), 1),
               "hd_input": [{"outcome": "sent", "reason": f"tool {how}"}],
               "outcome": "taken" if left is not None else "lost",
               "effect_ms": round(1000 * (left - t_in), 1)
               if left is not None else None,
               "screens": sorted({s for _t, s, _v in seen})}
        if left is None:
            self._home()
        self.wait(lambda st: livesend.on_galaxy_map(st)
                  and self.app.dispatcher.overlay is None, 20)
        self.settle(30)
        return rec

    def research_key_trial(self, offset):
        return self.research_raw_trial(offset, "key")

    def research_click_trial(self, offset):
        return self.research_raw_trial(offset, "click")

    def colony_trial(self, offset):
        gm = self.hd("galaxy_map")
        star, view = gm.home_star(), gm._map_view()
        before = len(self.st.fields or [])
        self.click(*view.to_screen(star.x, star.y))
        self.wait(lambda st: len(st.fields or []) != before, 20)
        self.settle(10)
        disc = self.own_colony_disc()
        if disc is None:
            return {"error": "no own colony's disc in the system window"}
        self.click_rect(disc)
        t0, frames = self.first_hd("colony", lambda: self.index() >= 0)
        if t0 is None:
            return {"error": "the colony screen was not drawn"}
        self.wait_until(t0 + offset / 1000)
        mark = len(self.inlog.entries)
        t_in = time.monotonic()
        self.key(pygame.K_ESCAPE)
        seen = self.observe(lambda: None)
        left = next((t for t, s, _v in seen if s == 0), None)
        rec = {"t_input_after_hd": round(1000 * (t_in - t0), 1),
               "hd_input": self.inlog.entries[mark:mark + 2],
               "outcome": "taken" if left is not None else "lost",
               "effect_ms": round(1000 * (left - t_in), 1)
               if left is not None else None,
               "screens": sorted({s for _t, s, _v in seen})}
        if left is None:
            self._home()
        self.wait(livesend.on_galaxy_map, 20)
        self.settle(30)
        return rec

    def auto(self):
        q = getattr(self.st, "build_queue", None)
        return None if not q else q.get("auto_building")

    def popup_trial(self, offset):
        from screens.build_queue import bqwire
        scr = self.hd("colony")
        change = next((f for f in self.st.fields or []
                       if (f.field_type, f.x, f.y) == (0, 519, 123)), None)
        if change is None:
            return {"error": "no CHANGE field on the colony screen"}
        self.click_field(scr, (change.x, change.y, change.x_end,
                               change.y_end))
        bq = self.hd("build_queue")
        t0, frames = self.first_hd(
            "build_queue", lambda: bq._view is not None and bq._view.draws)
        if t0 is None:
            return {"error": "the build popup was not drawn"}
        radio = bqwire.live_field(self.st.fields, bqwire.AUTO_BUILD)
        if radio is None:
            return {"error": "no Auto Build field in the popup's list"}
        start = self.auto()
        from screens.leaders import ldrdraw as _nd   # the popup's own mapping (screen.py)
        r = _nd.rect(bq.layout, (radio.x, radio.y, radio.x_end, radio.y_end))
        self.wait_until(t0 + offset / 1000)
        mark = len(self.inlog.entries)
        t_in = time.monotonic()
        self.click(*r.center)
        seen = self.observe(self.auto)
        values = [v for _t, s, v in seen if s == 25 and v is not None]
        flips = sum(1 for a, b in zip([start] + values, values) if a != b)
        first = next((t for t, s, v in seen if s == 25 and v is not None
                      and v != start), None)
        outcome = {0: "lost", 1: "taken"}.get(flips, "taken twice"
                                                if flips == 2 else
                                                f"flipped {flips}x")
        rec = {"t_input_after_hd": round(1000 * (t_in - t0), 1),
               "hd_input": self.inlog.entries[mark:mark + 2],
               "outcome": outcome, "auto_before": start,
               "auto_after": values[-1] if values else None,
               "effect_ms": round(1000 * (first - t_in), 1)
               if first is not None else None,
               "screens": sorted({s for _t, s, _v in seen})}
        # PUT IT BACK: one more HD click on the radio until the flag is the
        # one the trial found, then Cancel back to the colony screen.
        for _ in range(3):
            if self.auto() == start or self.st.current_screen != 25:
                break
            self.click(*r.center)
            self.wait(lambda st, s=start: self.auto() == s, 5)
            self.settle(10)
        rec["restored"] = self.auto() == start
        cancel = bqwire.live_field(self.st.fields, bqwire.CANCEL)
        if cancel is not None and self.st.current_screen == 25:
            self.click_field(bq, (cancel.x, cancel.y, cancel.x_end,
                                  cancel.y_end))
        self.wait(self.on_colony, 20)
        self.settle(30)
        return rec

    def to_colony(self):
        """Onto the colony screen from the map, for the popup trials."""
        gm = self.hd("galaxy_map")
        star, view = gm.home_star(), gm._map_view()
        before = len(self.st.fields or [])
        self.click(*view.to_screen(star.x, star.y))
        self.wait(lambda st: len(st.fields or []) != before, 20)
        self.settle(10)
        self.click_rect(self.own_colony_disc())
        return self.wait(self.on_colony, 20) and (self.settle(30) or True)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    tag = args[0] if args else "gap"
    opt = lambda k, d: next((a.split("=", 1)[1] for a in argv  # noqa: E731
                             if a.startswith(f"--{k}=")), d)
    screens = opt("screens", ",".join(SCREENS)).split(",")
    reps = int(opt("reps", 2))
    offsets = [int(v) for v in opt("offsets", ",".join(map(str, OFFSETS)))
               .split(",")]
    saves = hashes()
    g = Gap(tag)
    g.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    g.settle(40)
    if g.st.current_screen == 10:
        if not g.load():
            return 1
    g._home()
    g.measuring = True
    for name in screens:
        if name == "popup" and not g.to_colony():
            print("  popup: could not reach the colony screen")
            continue
        for rep in range(reps):
            for off in offsets:
                rec = getattr(g, f"{name}_trial")(off)
                rec.update({"screen": name, "offset_ms": off, "rep": rep})
                g.trials.append(rec)
                hd = [(e.get("outcome"), e.get("reason")) for e in
                      rec.get("hd_input", [])]
                print(f"  {name:8s} +{off:4d} ms (at {rec.get('t_input_after_hd')}"
                      f"): {rec.get('outcome', rec.get('error'))}"
                      f"  effect {rec.get('effect_ms')} ms  HD {hd}"
                      f"  screens {rec.get('screens')}")
        if name == "popup":
            g.measuring = False
            g._home()
            g.measuring = True
    summary = {}
    for t in g.trials:
        key = f"{t['screen']}"
        s = summary.setdefault(key, {})
        s[t.get("outcome", "error")] = s.get(t.get("outcome", "error"), 0) + 1
    path = os.path.join(g.run.dir, "gap.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"tag": tag, "trials": g.trials, "summary": summary,
                   **close(g.run, saves)}, fh, indent=1)
    print(f"\nGAP {tag}: {json.dumps(summary)}\n  record: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
