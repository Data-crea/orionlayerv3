#!/usr/bin/env python3
"""Inputs under repetition, with the click log on — work order 182, part 3.

    python tools/stress_inputs.py W H [--popup N] [--colony N] [--fleets N]

Work order 181 lost one Cancel click in the build popup at 3840 and could
not say why. This repeats the three gestures the order names on the
virtual display, with `core/inputlog` recording every click and key the
HD client receives and whether it reached the engine:

    popup   the colony screen's CHANGE (HD click) -> the build popup,
            then its Cancel (HD click) -> the colony screen      (200)
    colony  the galaxy map's home star -> the system window -> the
            colony's planet (HD clicks), `<`, `>`, ESC -> the map (100)
    fleets  the galaxy map's FLEETS button -> the Fleets screen, ESC
            -> the map                                           (100)

After every cycle it checks the screen it had to reach. A transition that
does not settle is a LOST INPUT, and its entry in the log names the cause.
Nothing is ordered: Cancel scraps nothing it did not make, the other
steps are navigation. SAVE4 is loaded (scratch); nothing is saved.

Output: `stress.json` (per cycle and per lost input) and `inputs.jsonl`
(the whole log) in the evidence folder.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Work order 182: SDL's dummy drivers FORCED, never a window or a sound in
# the user's session.
import vdisplay  # noqa: E402
vdisplay.headless_clients()

import pygame  # noqa: E402

import colony_accept  # noqa: E402
import flash_walk  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402

#: A stress cycle waits for fewer frames than an acceptance walk: it asks
#: whether the screen was reached, not how it looked for half a second.
SETTLE_FRAMES = 6


class Stress(colony_accept.Accept):
    def __init__(self, size, tag):
        super().__init__(size, tag)
        self.cycles = []
        self.inlog = self.app._input_log
        assert self.inlog is not None, "the input log is off"
        self._real_capture = self.run.capture
        self.run.capture = lambda name: None      # pictures only on a loss

    def step(self, kind, n, name, target, action, ready):
        mark = len(self.inlog.entries)
        ok = self.transition(name, target, action, ready)
        inputs = self.inlog.entries[mark:]
        rec = {"kind": kind, "cycle": n, "step": name, "reached": ok,
               "inputs": inputs}
        if not ok:
            rec["picture"] = self._real_capture(
                f"LOST_{kind}_{n}_{name}".replace(" ", "_"))["hd_png"]
            print(f"  LOST {kind} {n}: {name} — inputs "
                  f"{[(i['outcome'], i['reason'], i['fields']) for i in inputs]}")
        self.cycles.append(rec)
        return ok

    def popup(self, n):
        from screens.build_queue import bqwire
        scr = self.hd("colony")
        change = next((f for f in self.st.fields or []
                       if (f.field_type, f.x, f.y) == (0, 519, 123)), None)
        if change is None:
            return self.step("popup", n, "no CHANGE field", "colony",
                             lambda: None, lambda st: False)
        ok = self.step("popup", n, "colony -> build_queue", "build_queue",
                       lambda: self.click_field(scr, (change.x, change.y,
                                                      change.x_end,
                                                      change.y_end)),
                       lambda st: st.current_screen == 25 and
                       self.hd("build_queue")._view is not None and
                       self.hd("build_queue")._view.draws)
        f = bqwire.live_field(self.st.fields, bqwire.CANCEL)
        if f is None:
            return self.recover("colony")
        ok &= self.step("popup", n, "build_queue -> colony (Cancel)",
                        "colony", lambda: self.click_field(
                            self.hd("build_queue"),
                            (f.x, f.y, f.x_end, f.y_end)), self.on_colony)
        return ok or self.recover("colony")

    def colony(self, n):
        from screens.galaxy_map import boxdraw
        gm = self.hd("galaxy_map")
        open_box = any(m.get("kind") == "system"
                       for _n, _b, m in boxdraw.drawable(gm))
        if not open_box:
            star, view = gm.home_star(), gm._map_view()
            x, y = view.to_screen(star.x, star.y)
            self.step("colony", n, "galaxy_map -> system window",
                      "galaxy_map", lambda: self.click(x, y),
                      lambda st: any(m.get("kind") == "system" for _n, _b, m
                                     in boxdraw.drawable(gm)))
        disc = self.own_colony_disc()
        ok = disc is not None and self.step(
            "colony", n, "system window -> colony", "colony",
            lambda: self.click_rect(disc), self.on_colony)
        for key, label in ((pygame.K_LESS, "<"), (pygame.K_GREATER, ">")):
            if ok:
                before = self.index()
                ok &= self.step("colony", n, f"colony -> colony ({label})",
                                "colony", lambda k=key: self.key(k),
                                lambda st, b=before: self.on_colony(st) and
                                self.index() != b)
        ok &= self.step("colony", n, "colony -> galaxy_map (ESC)",
                        "galaxy_map", lambda: self.key(pygame.K_ESCAPE),
                        livesend.on_galaxy_map)
        return ok or self.recover("galaxy_map")

    def fleets(self, n):
        gm = self.hd("galaxy_map")
        ok = self.step("fleets", n, "galaxy_map -> fleets", "fleets",
                       lambda: self.click_rect(gm.nav_rect("fleets")),
                       self.run.on_screen(4))
        ok &= self.step("fleets", n, "fleets -> galaxy_map", "galaxy_map",
                        lambda: self.key(pygame.K_ESCAPE),
                        livesend.on_galaxy_map)
        return ok or self.recover("galaxy_map")

    def recover(self, where):
        """Back on a known screen after a loss, by the same gestures."""
        for _ in range(3):
            if where == "colony" and self.on_colony(self.st):
                return False
            if where == "galaxy_map" and livesend.on_galaxy_map(self.st):
                return False
            self.key(pygame.K_ESCAPE)
            self.settle(40)
        return False


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    count = lambda k, d: next((int(a.split("=")[1]) for a in argv  # noqa
                               if a.startswith(f"--{k}=")), d)
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    os.environ.setdefault("ORIONLAYER_INPUT_LOG", "1")
    flash_walk.SETTLED = SETTLE_FRAMES
    saves = hashes()
    w = Stress(size, os.environ.get("FLASH_WALK_TAG", "P3_stress"))
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    w.settle(40)
    if w.st.current_screen == 10:
        w.load()
    start = time.monotonic()
    for n in range(count("fleets", 100)):
        w.fleets(n)
    for n in range(count("colony", 100)):
        w.colony(n)
    gm = w.hd("galaxy_map")
    w.transition("galaxy_map -> colony_summary", "colony_summary",
                 lambda: w.click_rect(gm.nav_rect("colonies")),
                 livesend.on_colony_summary)
    w.enter_colony(0)
    w.settle(10)
    for n in range(count("popup", 200)):
        w.popup(n)
    summary = {}
    for kind in ("popup", "colony", "fleets"):
        steps = [c for c in w.cycles if c["kind"] == kind]
        lost = [c for c in steps if not c["reached"]]
        summary[kind] = {"cycles": len({c["cycle"] for c in steps}),
                         "steps": len(steps), "lost": len(lost)}
    drops = [e for e in w.inlog.entries if e["outcome"] == "dropped"]
    report = {"size": list(size), "seconds": round(time.monotonic() - start),
              "summary": summary, "inputs": len(w.inlog.entries),
              "dropped": drops,
              "lost": [c for c in w.cycles if not c["reached"]]}
    with open(os.path.join(w.run.dir, "stress.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(w.run.dir, "inputs.jsonl"), "w") as fh:
        for e in w.inlog.entries:
            fh.write(json.dumps(e) + "\n")
    print(f"STRESS {size[0]}x{size[1]}: {json.dumps(summary)}; "
          f"{len(w.inlog.entries)} inputs, {len(drops)} dropped "
          f"({sorted({d['reason'] for d in drops})}); "
          f"{report['seconds']} s")
    w.save({"summary": summary, **close(w.run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
