#!/usr/bin/env python3
"""The Ship Designer and its pickers walked live — work order 185, part 7.

    python tools/design_walk.py W H [--slot N]

ONLY AGAINST AN ENGINE CARRYING OPEN FIXES 44 AND 45 — applied since work
order 186, so the engine `tools/engine_start.py` starts; without them the
designer is the game's picture and there is nothing to walk. Every
transition through the HD window (`colony_accept.Accept`, every frame
traced and pixel-checked, recorded for the flash check's replay fixture,
`tools/flash_fixture.py`):

    colony -> build popup (CHANGE); Design; a design row  -> ship_design
    the computer panel -> design_box (54), ESC back
    the first weapon row -> design_box (55), ESC back
    the first special row -> design_box (56), ESC back
    ship_design -> build popup (ESC = Cancel), the popup's Cancel

and at each stop the snapshot and the list as they came off the wire
(`state.bin`, `fields.bin`), which `tools/design_fixture.py` cuts into the
committed stand-in. Nothing is built or saved: the design row opens the
designer on slot N (default 1), Cancel leaves it unchanged; no TURN, no
SAVE. The shield panel is not walked — with nothing researched it answers
with a warning box (the reading, section 10), not a picker.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import colony_accept  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402

from core.wire_protocol import MSG_FIELDS, MSG_STATE  # noqa: E402

#: The designer's panels and first rows, (type, x, y) — `sdgeom`'s.
PANELS = (("computer", 54, (7, 0x1B5, 0x61)),
          ("weapon", 55, (7, 0x4D, 0xA9)),
          ("special", 56, (7, 0x11, 0x13F)))


class DesignWalk(colony_accept.Accept):

    def __init__(self, size, tag):
        super().__init__(size, tag)
        self.raw = {}
        real = self.app.client._handle_message

        def keep(kind, flags, payload):
            self.raw[kind] = payload
            return real(kind, flags, payload)
        self.app.client._handle_message = keep
        self.stops = []

    def stop(self, label):
        """The snapshot and list now, as they came off the wire."""
        folder = os.path.join(self.run.dir, label)
        os.makedirs(folder, exist_ok=True)
        for kind, name in ((MSG_STATE, "state"), (MSG_FIELDS, "fields")):
            with open(os.path.join(folder, name + ".bin"), "wb") as fh:
                fh.write(self.raw.get(kind, b""))
        st = self.st
        box = st.design_box or {}
        self.stops.append({"label": label, "screen": st.current_screen,
                           "fields": len(st.fields or []),
                           "ship_design": st.ship_design,
                           "design_box": st.design_box})
        print(f"  stop {label}: screen {st.current_screen}, DSGN "
              f"{'yes' if st.ship_design else 'no'}, DSBX "
              f"{box.get('kind')} rows {len(box.get('rows', []))} offered "
              f"{box.get('mods_offered')}")

    def page_ready(self, st):
        v = self.hd("ship_design")._view
        return st.current_screen == 3 and v is not None and \
            v.state == "ok"

    def box_ready(self, sid):
        def ready(st):
            b = self.hd("design_box")._box
            return st.current_screen == sid and b is not None and b.draws
        return ready

    def field(self, ident):
        t, x, y = ident
        return next((f for f in self.st.fields or [] if f.index != 0 and
                     (f.field_type, f.x, f.y) == (t, x, y)), None)

    def into_designer(self, slot):
        from screens.build_queue import bqwire
        popup = self.hd("build_queue")
        f = bqwire.live_field(self.st.fields, bqwire.DESIGN)
        self.click_field(popup, (f.x, f.y, f.x_end, f.y_end))
        self.wait(lambda st: (st.build_queue or {}).get("field_mode") == 1,
                  10)
        self.settle(10)
        others = (self.st.build_lists or {}).get("others", [])
        idx = next(i for i, e in enumerate(others) if e["id"] == -50 - slot)
        row = popup._view.other_rows[idx]
        return self.transition(
            f"build_queue -> ship_design (design slot {slot})",
            "ship_design", lambda: self.click_field(
                popup, (row.x, row.y, row.x_end, row.y_end)),
            self.page_ready)

    def pickers(self):
        page = self.hd("ship_design")
        for label, sid, ident in PANELS:
            f = self.field(ident)
            if f is None:
                print(f"  {label}: no field at {ident} now — not walked")
                continue
            ok = self.transition(
                f"ship_design -> design_box ({label})", "design_box",
                lambda f=f: self.click_field(
                    page, (f.x, f.y, f.x_end, f.y_end)),
                self.box_ready(sid))
            if ok:
                self.stop(label)
            self.transition(f"design_box ({label}) -> ship_design (ESC)",
                            "ship_design",
                            lambda: self.key(pygame.K_ESCAPE),
                            self.page_ready)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    slot = next((int(a.split("=", 1)[1]) for a in argv
                 if a.startswith("--slot=")), 1)
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    saves = hashes()
    w = DesignWalk(size, os.environ.get("FLASH_WALK_TAG", "P7_design"))
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    w.settle(40)
    if w.st.current_screen == 10:
        w.load()
    if not livesend.on_galaxy_map(w.st):
        raise livesend.WrongDialog(f"screen {w.st.current_screen}, not the "
                                   f"galaxy map — nothing sent")
    results = {}
    gm = w.hd("galaxy_map")
    star, view = gm.home_star(), gm._map_view()
    before = len(w.st.fields or [])
    w.click(*view.to_screen(star.x, star.y))
    w.wait(lambda st: len(st.fields or []) != before, 20)
    w.settle(10)
    w.click_rect(w.own_colony_disc())
    results["colony"] = w.wait(w.on_colony, 20)
    w.settle(20)
    w.open_popup("colony -> build_queue (CHANGE)")
    results["designer"] = w.into_designer(slot)
    if results["designer"]:
        w.stop("designer")
        w.pickers()
        w.stop("designer_after")
        from screens.build_queue import bqwire
        w.transition("ship_design -> build_queue (ESC)", "build_queue",
                     lambda: w.key(pygame.K_ESCAPE),
                     lambda st: st.current_screen == 25 and
                     w.hd("build_queue")._view is not None and
                     w.hd("build_queue")._view.draws)
        w.popup_button("build_queue -> colony (Cancel)", bqwire.CANCEL,
                       "colony", w.on_colony)
    w.transition("colony -> galaxy_map (ESC)", "galaxy_map",
                 lambda: w.key(pygame.K_ESCAPE), livesend.on_galaxy_map)
    with open(os.path.join(w.run.dir, "record.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"steps": w.stops}, fh, indent=1, default=str)
    closed = close(w.run, saves)
    w.save({"results": results, **closed})
    bad = [r["transition"] for r in w.rows if r["native_total"]]
    print(f"\n  {len(w.rows)} transitions, {len(bad)} with native frames")
    # Work order 188: a native frame without F12 ANYWHERE in the run —
    # between the recorded transitions too — fails the walk.
    return 1 if bad or closed["native_frames"].get("without_f12") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
