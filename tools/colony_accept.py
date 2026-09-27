#!/usr/bin/env python3
"""The colony screen and the build popup accepted live — work order 181.

    python tools/colony_accept.py W H [--orders]

Open fixes 35-40 are applied (work order 181), so on `orionlayer-local`
both screens claim their ids by themselves. This walks every way into and
out of screen 1 and screen 25 that a scratch save offers WITHOUT a turn,
through the HD window (`colony_live.Live`, every frame traced and
pixel-checked, every transition recorded for 180 A2's replay fixture):

    galaxy map   the home star -> the system window -> the colony's planet
                 (mainscr.cpp:563-577, `Do_Colony_Screen_`), ESC back
    Colonies     a row's name (colsum.cpp:945, through `livesend`: the HD
                 Colonies screen offers no such click), ESC back
    < and >      the colony screen's own keys, twice each way
    Leaders      L to screen 29 (colony_main.cpp:1043-1048), ESC back
    the popup    CHANGE (the field), Cancel and OK back; and from the
                 Colonies screen's producing column (colsum.cpp:922-943)

At EVERY frame HD draws the colony screen, the colony it draws must be the
one the engine's handle names (the screen the game draws is the handle's,
colony_main.cpp) — counted, and any disagreement is printed.

THE ORDERS, only with `--orders`, on the loaded scratch slot, never saved:
the pop move there and back (`Live.pop_move`), and in the popup a building
selected (in the queue under edit on the wire while `producing[]` is still
as before — open fix 39), a ship selected, Cancel (`producing[]` as
before); then one building added and confirmed with OK (on the wire, and
in the game's own popup reopened), and taken back the same way (the row
toggles, colbldg.cpp:1654-1672) and confirmed — `producing[]` as before,
and the colony record compared field by field.

Not walked, each for its reason: the Info screen's Turn Summary jump (open
fix 33 — the engine goes to the map; info.cpp unchanged since 176
measured it), the turn-start reports, the turn summary and a colony
landing (only after TURN, which writes SAVE10), A (autobuild) and B (buy)
(orders), Design and Refit from the popup (screen 3, no HD screen).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import colony_live  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402

from core import colony_guard  # noqa: E402
from core.structs import colony as colony_struct  # noqa: E402

NAME_FIELD = colony_live.NAME_FIELD
PROD_FIELD = lambda i: (512, 35 + 31 * i, 597, 65 + 31 * i)  # noqa: E731


class Accept(colony_live.Live):
    def __init__(self, size, tag):
        super().__init__(size, tag)
        self.agree = {"frames": 0, "wrong": []}
        self.patched_engine = True
        self.notes = {}

    def frame(self):
        super().frame()
        d = self.app.dispatcher
        top = d.overlay_name or d.active_name
        if top != "colony" or d.use_original:
            return
        view = getattr(d.active, "_view", None)
        block = getattr(self.st, "colony_screen", None)
        if view is None or not view.draws or block is None:
            return
        self.agree["frames"] += 1
        if view.index != block["colony"]:
            self.agree["wrong"].append((self.trace.frames[-1]["snap"],
                                        view.index, block["colony"]))

    def index(self):
        v = getattr(self.hd("colony"), "_view", None)
        return v.index if v is not None and v.draws else -1

    def on_colony(self, st):
        return st.current_screen == 1 and self.index() >= 0

    # ── the ways in ──────────────────────────────────────────────────
    def from_map(self):
        from screens.galaxy_map import boxdraw
        gm = self.hd("galaxy_map")
        star, view = gm.home_star(), gm._map_view()
        x, y = view.to_screen(star.x, star.y)
        before = len(self.st.fields or [])
        self.transition("galaxy_map -> system window", "galaxy_map",
                        lambda: self.click(x, y),
                        lambda st: len(st.fields or []) != before)
        disc = self.own_colony_disc()
        if disc is None:
            print("  from the map: no own colony's disc in the window")
            return False
        ok = self.transition("galaxy_map -> colony (system window)",
                             "colony", lambda: self.click_rect(disc),
                             self.on_colony)
        self.notes["map_colony"] = self.index()
        self.run.capture("P3_colony_from_map")
        self.transition("colony -> galaxy_map (ESC)", "galaxy_map",
                        lambda: self.key(pygame.K_ESCAPE),
                        livesend.on_galaxy_map)
        self._home()
        return ok

    def own_colony_disc(self):
        """The HD system window's disc of a colony of the local player's
        (not an outpost: `Do_Colony_Screen_` answers those with a box)."""
        from screens.galaxy_map import boxdraw
        gm = self.hd("galaxy_map")
        me = int(getattr(self.st, "player_num", 0) or 0)
        raws = self.st.colonies_raw or []
        disc = None
        for _names, _box, model in boxdraw.drawable(gm):
            for p in model.get("planets", []):
                col = p.get("colony", -1)
                c = colony_struct.parse(raws[col]) \
                    if 0 <= col < len(raws) else None
                if c is not None and c.owner == me and not c.outpost_flag:
                    disc = next((r for r, f in getattr(gm, "_box_hits", [])
                                 if f == p["field"]), None)
        return disc

    def switch(self, key, label):
        before = self.index()
        ok = self.transition(f"colony -> colony ({label})", "colony",
                             lambda: self.key(key),
                             lambda st: self.on_colony(st) and
                             self.index() != before)
        print(f"  {label}: colony {before} -> {self.index()}")
        self.run.capture(f"P3_switch_{label}")
        return ok

    def leaders_and_back(self):
        ok = self.transition("colony -> leaders (L)", "leaders",
                             lambda: self.key(pygame.K_l),
                             self.run.on_screen(29))
        back = self.transition("leaders -> colony (ESC)", "colony",
                               lambda: self.key(pygame.K_ESCAPE),
                               self.on_colony)
        return ok and back

    def open_popup(self, name):
        scr = self.hd("colony")
        change = next((f for f in self.st.fields or []
                       if (f.field_type, f.x, f.y) == (0, 519, 123)), None)
        return self.transition(name, "build_queue", lambda: self.click_field(
            scr, (change.x, change.y, change.x_end, change.y_end)),
            lambda st: st.current_screen == 25 and
            self.hd("build_queue")._view is not None and
            self.hd("build_queue")._view.draws)

    def popup_button(self, name, ident, target, ready):
        from screens.build_queue import bqwire
        f = bqwire.live_field(self.st.fields, ident)
        return self.transition(name, target, lambda: self.click_field(
            self.hd("build_queue"), (f.x, f.y, f.x_end, f.y_end)), ready)

    def from_summary_producing(self, row):
        f = next((f for f in (self.st.fields or []) if f.field_type == 7
                  and (f.x, f.y, f.x_end, f.y_end) == PROD_FIELD(row)), None)
        if f is None:
            return False

        def send():
            colony_guard.check(f, self.st.current_screen)
            livesend.activate(self.app.client, f.index,
                              shape=livesend.on_colony_summary,
                              field_type=7, rect=(f.x, f.y, f.x_end, f.y_end),
                              label=f"producing row {row}")
        from screens.build_queue import bqwire
        ok = self.transition(f"colony_summary -> build_queue (producing, "
                             f"row {row})", "build_queue", send,
                             lambda st: st.current_screen == 25)
        self.run.capture("P3_popup_from_summary")
        self.popup_button("build_queue -> colony_summary (Cancel)",
                          bqwire.CANCEL, "colony_summary",
                          livesend.on_colony_summary)
        return ok

    # ── the popup, against the game's own ────────────────────────────
    def popup_record(self, tag):
        from screens.build_queue.screen import Names
        scr = self.hd("build_queue")
        v = scr._view
        names = Names(self.st, scr._buildings, scr._strings)
        rec = {k: [dict(e, name=names.product(e["id"], self.st)[0])
                   for e in getattr(v, k)] for k in ("buildings", "others")}
        rec.update(queue=[dict(e, name=names.product(e["id"], self.st)[0])
                          for e in v.queue_numbers if e["id"] != -1],
                   items=list(v.items), auto_building=v.auto_building,
                   autobuild_enabled=self.st.colony_screen[
                       "autobuild_enabled"], field_mode=v.field_mode,
                   rows=[len(v.building_rows), len(v.other_rows)])
        self.notes[tag] = rec
        self.run.capture(tag)
        return rec

    def popup_orders(self, idx, before):
        from screens.build_queue import bqwire
        out = {}
        rec = self.popup_record("P3_popup_lists")
        v = self.hd("build_queue")._view
        pick = next((e["id"] for e in rec["buildings"]
                     if e["id"] > 0 and e["id"] not in v.items), None)
        row = lambda pid: next(f for e, f in zip(  # noqa: E731
            self.hd("build_queue")._view.buildings,
            self.hd("build_queue")._view.building_rows) if e["id"] == pid)
        f = row(pick)
        self.click_field(self.hd("build_queue"), (f.x, f.y, f.x_end, f.y_end))
        shown = self.wait(lambda st: pick in st.build_queue["items"], 10)
        self.settle(20)
        wire = list(self.colony_record(idx).producing)
        out["under_edit"] = {"building": pick, "in_bldq": shown,
                             "producing_unchanged": wire == before,
                             "hd_items": list(self.hd("build_queue")
                                              ._view.items)}
        self.run.capture("P3_queue_under_edit")
        v = self.hd("build_queue")._view
        ship = next(((e, f) for e, f in zip(v.others, v.other_rows)
                     if e["id"] != bqwire.SEPARATOR and e["cost"] >= 0), None)
        items = list(v.items)
        self.click_field(self.hd("build_queue"),
                         (ship[1].x, ship[1].y, ship[1].x_end, ship[1].y_end))
        out["ship"] = (ship[0]["id"], self.wait(
            lambda st: st.build_queue["items"] != items, 10))
        self.settle(20)
        self.run.capture("P3_ship_selected")
        self.popup_button("build_queue -> colony (Cancel)", bqwire.CANCEL,
                          "colony", self.on_colony)
        out["cancel_restores"] = list(self.colony_record(idx).producing) \
            == before
        # One real order: add the building, OK, see it, take it back, OK.
        raw0 = self.st.colonies_raw[idx]
        self.open_popup("colony -> build_queue (CHANGE, add)")
        f = row(pick)
        self.click_field(self.hd("build_queue"), (f.x, f.y, f.x_end, f.y_end))
        self.wait(lambda st: pick in st.build_queue["items"], 10)
        self.popup_button("build_queue -> colony (OK)", bqwire.OK, "colony",
                          self.on_colony)
        after = list(self.colony_record(idx).producing)
        slot = before.index(-1) if -1 in before else None
        want = list(before)
        if slot is not None:
            want[slot] = pick
        out["ok_added"] = {"producing": after, "expected": want,
                           "ok": after == want}
        self.run.capture("P3_after_ok")
        self.open_popup("colony -> build_queue (CHANGE, check)")
        self.popup_record("P3_popup_after_ok")
        f = row(pick)
        self.click_field(self.hd("build_queue"), (f.x, f.y, f.x_end, f.y_end))
        self.wait(lambda st: pick not in st.build_queue["items"], 10)
        self.popup_button("build_queue -> colony (OK, taken back)", bqwire.OK,
                          "colony", self.on_colony)
        out["taken_back"] = list(self.colony_record(idx).producing) == before
        raw1 = self.st.colonies_raw[idx]
        a, b = colony_struct.parse(raw0), colony_struct.parse(raw1)
        out["record_fields_changed"] = sorted(
            k for k in a._values if a._values[k] != b._values.get(k))
        out["record_identical"] = bytes(raw0) == bytes(raw1)
        self.run.capture("P3_after_taken_back")
        print(f"  popup orders: {json.dumps(out)}")
        return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    saves = hashes()
    w = Accept(size, os.environ.get("FLASH_WALK_TAG", "P3_accept"))
    w.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                   label="the first snapshot")
    w.settle(40)
    if w.st.current_screen == 10:
        w.load()
    if not livesend.on_galaxy_map(w.st):
        raise livesend.WrongDialog(f"screen {w.st.current_screen}, not the "
                                   f"galaxy map — nothing sent")
    results = {"from_map": w.from_map()}
    gm = w.hd("galaxy_map")
    w.transition("galaxy_map -> colony_summary", "colony_summary",
                 lambda: w.click_rect(gm.nav_rect("colonies")),
                 livesend.on_colony_summary)
    results["from_summary"] = w.enter_colony(0)
    w.settle(10)
    idx = w.index()
    results["summary_colony"] = idx
    for key, label in ((pygame.K_GREATER, ">"), (pygame.K_LESS, "<"),
                       (pygame.K_LESS, "<"), (pygame.K_GREATER, ">")):
        results[f"switch {label} {len(results)}"] = w.switch(key, label)
    results["back_on"] = w.index() == idx
    results["leaders"] = w.leaders_and_back()
    before = list(w.colony_record(w.index()).producing)
    if "--orders" in argv:
        results["pop_move"] = w.pop_move()
    w.open_popup("colony -> build_queue (CHANGE)")
    if "--orders" in argv:
        results["popup"] = w.popup_orders(w.index(), before)
    else:
        from screens.build_queue import bqwire
        w.popup_record("P3_popup_lists")
        w.popup_button("build_queue -> colony (Cancel)", bqwire.CANCEL,
                       "colony", w.on_colony)
    w.transition("colony -> colony_summary (ESC)", "colony_summary",
                 lambda: w.key(pygame.K_ESCAPE), livesend.on_colony_summary)
    results["from_producing"] = w.from_summary_producing(1)
    w.transition("colony_summary -> galaxy_map (ESC)", "galaxy_map",
                 lambda: w.key(pygame.K_ESCAPE), livesend.on_galaxy_map)
    results["agreement"] = {"frames": w.agree["frames"],
                            "wrong": w.agree["wrong"][:20]}
    print(f"  agreement: {w.agree['frames']} colony frames, "
          f"{len(w.agree['wrong'])} disagreeing")
    w.save({"results": results, "notes": w.notes, **close(w.run, saves)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
