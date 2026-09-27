#!/usr/bin/env python3
"""The colony screen and the build popup, live — work order 180 B2 and C2.

    python tools/colony_live.py W H [--rows N] [--no-orders]

Drives the real App (headless, `tools/flash_walk.Walk`, every frame traced
and pixel-checked) from the galaxy map into the Colonies screen, into N
colonies' screens and each one's build popup and back, recording every
transition for A2's replay fixture. On an engine carrying open fixes
35-40 the HD screens claim ids 1 and 25 and draw; on one without them the
game's own picture stands (the safety net) — the same walk measures both.

THE ORDERS, only with the fixes and only without `--no-orders`, on the
loaded scratch slot and never saved:

    B2  one pop move on the first colony, through the HD job rows (pick a
        worker, drop on scientists), confirmed on the wire, then moved back
        the same way and confirmed restored word for word
    C2  in that colony's popup, through the HD rows: select a building,
        select a ship — each confirmed in the queue on the wire (open fix
        39) and captured beside the game's own picture — then Cancel, and
        the colony's producing[] must be what it was before the popup

Entering a colony uses the Colonies screen's own name field through
`livesend` (the HD Colonies screen offers no such click); everything
inside the colony screen and the popup is HD input.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402
import flash_walk  # noqa: E402

from core import colony_guard  # noqa: E402
from core.structs import colony as colony_struct  # noqa: E402
from screens.colony import coldraw, colgeom  # noqa: E402
from screens.leaders import ldrdraw as nd  # noqa: E402

NAME_FIELD = lambda i: (12, 35 + 31 * i, 101, 65 + 31 * i)  # noqa: E731


class Live(flash_walk.Walk):
    def patched(self):
        return getattr(self.st, "colony_screen", None) is not None

    def colony_record(self, index):
        raws = getattr(self.st, "colonies_raw", None) or []
        return colony_struct.parse(raws[index]) if 0 <= index < len(raws) \
            else None

    def wait(self, pred, seconds=20.0):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.frame()
            if pred(self.st):
                return True
        return False

    def enter_colony(self, row):
        f = next((f for f in (self.st.fields or []) if f.field_type == 7
                  and (f.x, f.y, f.x_end, f.y_end) == NAME_FIELD(row)), None)
        if f is None:
            return False

        def send():
            colony_guard.check(f, self.st.current_screen)
            livesend.activate(self.app.client, f.index,
                              shape=livesend.on_colony_summary,
                              field_type=7,
                              rect=(f.x, f.y, f.x_end, f.y_end),
                              label=f"colony row {row}")
        target = "colony"
        ok = self.transition(f"colony_summary -> colony (row {row})", target,
                             send, lambda st: st.current_screen == 1) \
            if self.claims_colony_soon() else self.native_transition(
                f"colony_summary -> colony (row {row}, net)", send, 1)
        return ok

    def claims_colony_soon(self):
        return self.patched_engine

    def native_transition(self, name, action, screen):
        """A transition INTO an id no HD screen claims: settles when the
        game reports `screen` for 30 frames; native frames are allowed
        there (A2's rule) and counted all the same."""
        mark = self.trace.mark()
        pix0 = len(self.pixels)
        self._current, self._flash_saved = name.replace(" ", ""), False
        action()
        streak = 0
        start = time.monotonic()
        while time.monotonic() - start < flash_walk.TIMEOUT and streak < 30:
            self.frame()
            streak = streak + 1 if self.st.current_screen == screen else 0
        self._flash_saved = True
        frames = self.trace.since(mark)
        for fr, p in zip(frames, self.pixels[pix0:pix0 + len(frames)]):
            fr["pixels_native"] = bool(p)
        from core import frametrace
        s = frametrace.summarise(frames, None)
        s.update(pixel_native_before_hd=0, pixel_native_total=sum(
            1 for fr in frames if fr["pixels_native"]), disagree=0)
        self.rows.append({"transition": name, "target": "", "settled":
                          streak >= 30, "size": list(self.size), **s,
                          "trace": frames})
        print(f"  {name:38s} (no HD screen) native {s['native_total']:3d} "
              f"kinds={','.join(s['kinds'])}")
        self.run.capture(name.replace(" ", "_"))
        return streak >= 30

    def hd(self, name):
        return self.app.dispatcher.screens.get(name)

    def send_field(self, f, label):
        """A field of the live list, through the colony guard and livesend
        (the net's path, where no HD screen draws)."""
        colony_guard.check(f, self.st.current_screen)
        livesend.activate(self.app.client, f.index,
                          screen=self.st.current_screen,
                          field_type=f.field_type,
                          rect=(f.x, f.y, f.x_end, f.y_end), label=label)

    def click_field(self, screen, ident_rect):
        r = nd.rect(screen.layout, ident_rect)
        self.click(r.centerx, r.centery)

    # ── B2: a pop move, and back ─────────────────────────────────────
    def pop_move(self):
        scr = self.hd("colony")
        view = scr._view
        if view is None or not view.draws:
            print("  pop move: the HD colony screen is not drawing")
            return None
        cells = coldraw.job_cells(scr, view)
        workers = [c for c in cells if c[0] == 1]
        if not workers:
            print("  pop move: no worker to move")
            return None
        index = view.index
        before = tuple(self.colony_record(index).pop)
        self.run.capture("B2_before_pop_move")
        _j, _k, rect, _c = workers[-1]
        self.click(rect.centerx, rect.centery)
        self.settle(5)
        sci = nd.rect(scr.layout, colgeom.JOB_ROWS[2])
        self.click(sci.right - 4, sci.centery)
        moved = self.wait(lambda st: tuple(self.colony_record(index).pop)
                          != before, 10)
        self.settle(20)
        self.run.capture("B2_after_pop_move")
        print(f"  pop move: worker -> scientist on the wire: {moved}")
        # And back: the last scientist to the workers.
        view = scr._view
        cells = coldraw.job_cells(scr, view)
        sci_cells = [c for c in cells if c[0] == 2]
        _j, _k, rect, _c = sci_cells[-1]
        self.click(rect.centerx, rect.centery)
        self.settle(5)
        wr = nd.rect(scr.layout, colgeom.JOB_ROWS[1])
        self.click(wr.right - 4, wr.centery)
        back = self.wait(lambda st: tuple(self.colony_record(index).pop)
                         == before, 10)
        self.settle(20)
        self.run.capture("B2_pop_moved_back")
        print(f"  pop move back: restored word for word: {back}")
        return moved and back

    # ── C2: select a building, a ship, cancel ────────────────────────
    def popup_orders(self, index, producing_before):
        from screens.build_queue import bqwire
        scr = self.hd("build_queue")
        v = scr._view
        if v is None or not v.draws:
            print("  popup: the HD build screen is not drawing")
            return None
        items0 = list(v.items)
        out = {"items_before": items0}
        b = next(((e, f) for e, f in zip(v.buildings, v.building_rows)
                  if e["id"] > 0 and e["id"] not in items0), None)
        if b is not None:
            self.click_field(scr, (b[1].x, b[1].y, b[1].x_end, b[1].y_end))
            ok = self.wait(lambda st: b[0]["id"] in
                           (getattr(st, "build_queue", None) or {})
                           .get("items", []), 10)
            self.settle(20)
            self.run.capture("C2_building_selected")
            out["building"] = (b[0]["id"], ok)
            print(f"  select building {b[0]['id']}: in the queue on the "
                  f"wire: {ok}")
        v = scr._view
        s = next(((e, f) for e, f in zip(v.others, v.other_rows)
                  if e["id"] not in (-9,) and e["cost"] >= 0), None)
        if s is not None:
            before = list(v.items)
            self.click_field(scr, (s[1].x, s[1].y, s[1].x_end, s[1].y_end))
            ok = self.wait(lambda st: (getattr(st, "build_queue", None)
                                       or {}).get("items") != before, 10)
            self.settle(20)
            self.run.capture("C2_ship_selected")
            out["ship"] = (s[0]["id"], ok)
            print(f"  select ship/other {s[0]['id']}: the queue moved on "
                  f"the wire: {ok}")
        cancel = bqwire.live_field(self.st.fields, bqwire.CANCEL)
        self.transition("build_queue -> colony (Cancel)", "colony",
                        lambda: self.click_field(scr, (cancel.x, cancel.y,
                                                       cancel.x_end,
                                                       cancel.y_end)),
                        lambda st: st.current_screen == 1)
        after = list(self.colony_record(index).producing)
        out["producing_restored"] = after == producing_before
        print(f"  Cancel: producing[] as before the popup: "
              f"{out['producing_restored']} ({producing_before[:3]} -> "
              f"{after[:3]})")
        self.run.capture("C2_after_cancel")
        return out


def main(argv):
    from screens.build_queue import bqwire
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    rows = next((int(a.split("=")[1]) for a in argv
                 if a.startswith("--rows=")), 2)
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    tag = os.environ.get("FLASH_WALK_TAG", "B_live")
    saves = hashes()
    w = Live(size, tag)
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    w.settle(40)
    if w.st.current_screen == 10:
        w.load()
    # Told, then CHECKED against the wire at the first colony.
    w.patched_engine = "--patched" in argv
    gm = w.hd("galaxy_map")
    if w.st.current_screen == 1:
        # Left on a colony by an earlier run: its own RETURN.
        ret = next((f for f in w.st.fields or []
                    if (f.field_type, f.x, f.y) == (0, 556, 459)), None)
        if ret is not None:
            w.send_field(ret, "RETURN (left by an earlier run)")
            w.wait(livesend.on_colony_summary, 20)
            w.settle(10)
    if not livesend.on_colony_summary(w.st):
        if not livesend.on_galaxy_map(w.st):
            raise livesend.WrongDialog(
                f"neither the galaxy map nor the Colonies screen is up "
                f"(screen {w.st.current_screen}) — nothing sent")
        w.transition("galaxy_map -> colony_summary", "colony_summary",
                     lambda: w.click_rect(gm.nav_rect("colonies")),
                     livesend.on_colony_summary)
    results = {}
    for row in range(rows):
        # Whether THIS engine sends the blocks is read off the wire, not
        # assumed: the first entry is recorded either way.
        if not w.enter_colony(row):
            continue
        w.settle(10)
        if w.patched() != w.patched_engine:
            print(f"!! --patched says {w.patched_engine}, the wire says "
                  f"{w.patched()} — stopping")
            break
        scr = w.hd("colony")
        idx = scr._view.index if w.patched_engine and scr._view else -1
        if row == 0 and w.patched_engine and "--no-orders" not in argv:
            results["pop_move"] = w.pop_move()
        producing = list(w.colony_record(idx).producing) if idx >= 0 else []
        change = next((f for f in w.st.fields or []
                       if (f.field_type, f.x, f.y) == (0, 519, 123)), None)
        if change is not None:
            if w.patched_engine:
                w.transition(f"colony -> build_queue (row {row})",
                             "build_queue", lambda: w.click_field(
                                 scr, (change.x, change.y, change.x_end,
                                       change.y_end)),
                             lambda st: st.current_screen == 25)
                if row == 0 and "--no-orders" not in argv:
                    results["popup"] = w.popup_orders(idx, producing)
                else:
                    c = bqwire.live_field(w.st.fields, bqwire.CANCEL)
                    w.transition(f"build_queue -> colony (row {row})",
                                 "colony", lambda: w.click_field(
                                     w.hd("build_queue"),
                                     (c.x, c.y, c.x_end, c.y_end)),
                                 lambda st: st.current_screen == 1)
            else:
                w.native_transition(f"colony -> popup (row {row}, net)",
                                    lambda: w.send_field(change, "CHANGE"),
                                    25)
                w.key(pygame.K_ESCAPE)
                w.wait(lambda st: st.current_screen == 1, 10)
        ret = next((f for f in w.st.fields or []
                    if (f.field_type, f.x, f.y) == (0, 556, 459)), None)
        if ret is None:
            continue
        if w.patched_engine:
            w.transition(f"colony -> colony_summary (row {row})",
                         "colony_summary", lambda: w.key(pygame.K_ESCAPE),
                         livesend.on_colony_summary)
        else:
            w.transition(f"colony -> colony_summary (row {row}, net)",
                         "colony_summary",
                         lambda: w.send_field(ret, "RETURN"),
                         livesend.on_colony_summary)
    w.save({"results": results, "patched": w.patched_engine,
            **close(w.run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
