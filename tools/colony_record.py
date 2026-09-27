#!/usr/bin/env python3
"""Record the colony screen (1) and the build popup (25) off the wire.

    python tools/colony_record.py [slot] [colonies]

Work order 180, parts B and C. Drives the game from the Colonies screen
into several colonies' screens and their build popups and keeps, at each
stop, the raw STATE payload, the field list and the game's own picture.
Run against a SCRATCH build that carries open fixes 35-40 (never applied
to orionlayer-local), it is what the colony and build screens' fixtures
are cut from: the patched wire format as the engine wrote it. Run against
the real engine it records the same stops without the blocks, which is
the safety net's own evidence.

WHAT IT MAY SEND, and nothing else — each field found in the list read at
that moment, by type, hotkey and native rectangle (decision 20, and
`tools/livesend.py`'s rule):

    Colonies (20)  a row's name field (12, 35+31i)-(101, 65+31i)
                   (colsum.cpp:283-291), which opens screen 1
    colony (1)     `<` (the next colony), CHANGE (type 0 at 519,123),
                   RETURN (type 0 at 556,459)
    popup (25)     Cancel (type 0 at 493,447) — scraps nothing it did not
                   make (colbldg.cpp:1540-1576), and this run makes nothing
    a text box     one SPACE key, while the list is not the screen's own

and it REFUSES, whatever it is asked: a type-8 field, a hotkey spelling
CRUNCH or TOGGLE, and any full-screen field (0,0)-(639,479) while the
game reports screen 1 or 25 — the safety rule of work order 126 and 180
B. The refusal is `colony_guard.check`, the same function the HD screen
sends through.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
import livesend  # noqa: E402
from livedrive import Run, close, hashes  # noqa: E402

from core import colony_guard  # noqa: E402

#: The evidence folder: the work order running the tool (180 wrote it;
#: 181 runs it again), `ORIONLAYER_EVIDENCE_FOLDER` to name it.
FOLDER = os.environ.get("ORIONLAYER_EVIDENCE_FOLDER", "work_order_180")
NAME_FIELD = lambda i: (12, 35 + 31 * i, 101, 65 + 31 * i)  # noqa: E731
CHANGE = (0, 519, 123)
RETURN = (0, 556, 459)
POPUP_CANCEL = (0, 493, 447)


class Recorder:
    def __init__(self, tag):
        self.run = Run(tag, folder=FOLDER)
        self.stops = []
        self.last_state = b""
        client = self.run.app.client
        real = client._handle_message

        def keep(msg_type, flags, payload):
            from core.wire_protocol import MSG_STATE
            if msg_type == MSG_STATE:
                self.last_state = bytes(payload)
            return real(msg_type, flags, payload)
        client._handle_message = keep

    @property
    def st(self):
        return self.run.state

    def field(self, ftype, x, y):
        return next((f for f in (self.st.fields or [])
                     if f.field_type == ftype and (f.x, f.y) == (x, y)), None)

    def send(self, f, label):
        colony_guard.check(f, self.st.current_screen)
        livesend.activate(self.run.app.client, f.index,
                          screen=self.st.current_screen,
                          field_type=f.field_type,
                          rect=(f.x, f.y, f.x_end, f.y_end), label=label)

    def own_list(self, screen):
        want = RETURN if screen == 1 else POPUP_CANCEL
        return self.field(*want) is not None

    def settle(self, screen):
        """Wait for the screen's OWN list; answer an entry text box with
        one space key (never a field) and wait again."""
        for _ in range(4):
            ok = self.run.wait_for(
                lambda st: st.current_screen == screen and
                self.own_list(screen), seconds=8, label=f"screen {screen}")
            if ok:
                self.run.pump(20)
                return True
            if self.st.current_screen == screen and not self.own_list(screen):
                self.stop(f"modal_on_{screen}")
                livesend.key(self.run.app.client, pygame.K_SPACE,
                             screen=screen,
                             shape=lambda st: not self.own_list(screen),
                             label="answer the text box")
        return False

    def stop(self, name):
        entry = self.run.capture(name)
        base = os.path.join(self.run.dir, f"{entry['step']:03d}_{name}")
        with open(base + "_state.bin", "wb") as fh:
            fh.write(self.last_state)
        with open(base + "_fields.json", "w", encoding="utf-8") as fh:
            json.dump([[f.index, f.x, f.y, f.x_end, f.y_end, f.field_type,
                        f.hotkey] for f in (self.st.fields or [])], fh)
        st = self.st
        entry["blocks"] = {k: getattr(st, k, None) for k in (
            "colony_screen", "colony_placement", "colony_events",
            "colony_product", "build_queue", "build_lists")}
        self.stops.append(entry)
        print(f"      blocks: " + ", ".join(
            k for k, v in entry["blocks"].items() if v is not None))
        return entry

    def colony(self, row):
        """Colonies row -> screen 1 -> `<` -> CHANGE -> Cancel -> RETURN."""
        name = next((f for f in (self.st.fields or [])
                     if f.field_type == 7 and
                     (f.x, f.y, f.x_end, f.y_end) == NAME_FIELD(row)), None)
        if name is None:
            print(f"  row {row}: no name field — skipped")
            return
        self.send(name, f"colony row {row}")
        if not self.settle(1):
            return
        self.stop(f"colony_row{row}")
        nxt = next((f for f in (self.st.fields or [])
                    if f.hotkey == ord("<") and f.field_type == 7), None)
        if nxt is not None:
            self.send(nxt, "next colony <")
            self.run.pump(30)
            if self.settle(1):
                self.stop(f"colony_row{row}_next")
        change = self.field(*CHANGE)
        if change is not None:
            self.send(change, "CHANGE")
            if self.settle(25):
                self.stop(f"popup_row{row}")
                self.send(self.field(*POPUP_CANCEL), "popup Cancel")
                self.settle(1)
        ret = self.field(*RETURN)
        if ret is not None:
            self.send(ret, "RETURN")
            self.run.wait_for(livesend.on_colony_summary, seconds=20,
                              label="the Colonies screen")
            self.run.pump(20)


def main(argv):
    slot = int(argv[0]) if argv else 4
    rows = int(argv[1]) if len(argv) > 1 else 3
    rec = Recorder(os.environ.get("COLONY_RECORD_TAG", "B_record"))
    saves = hashes()
    rec.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                     label="the first snapshot")
    rec.run.pump(40)
    if rec.st.current_screen == 10:
        gameload_main_menu(rec, slot)
    gm = rec.run.app.dispatcher.screens["galaxy_map"]
    if not livesend.on_galaxy_map(rec.st):
        raise livesend.WrongDialog("not on the galaxy map — nothing sent")
    col = next(s for s in gm._data["buttons"] if s["key"] == "colonies")
    livesend.activate(rec.run.app.client, col["field_id"], screen=0,
                      shape=livesend.on_galaxy_map, label="COLONIES")
    rec.run.wait_for(livesend.on_colony_summary, seconds=20,
                     label="the Colonies screen")
    rec.run.pump(20)
    rec.stop("colonies")
    for row in range(rows):
        rec.colony(row)
    rec.run.save_record({"stops": rec.stops, **close(rec.run, saves)})
    return 0


def gameload_main_menu(rec, slot):
    """From the main menu: L, then the slot's row — the rows in top-to-
    bottom order and the dialog's own record agreeing with the file."""
    from screens.game_menu import nodes
    livesend.key(rec.run.app.client, pygame.K_l, screen=10,
                 label="LOAD GAME")
    rec.run.wait_for(lambda st: nodes.classify(st.fields) == nodes.LOAD,
                     seconds=30, label="the Load dialog")
    rows = nodes.slot_rows(rec.st.fields)
    verdict = gameload.agreement(slot, gameload.file_header(slot),
                                 gameload.wire_slot(rec.run, slot))
    if len(rows) != nodes.SLOTS or verdict != "agrees":
        raise livesend.WrongDialog(f"slot {slot}: {verdict} — nothing sent")
    row = rows[slot - 1]
    livesend.activate(rec.run.app.client, row.index,
                      shape=livesend.in_game_menu(nodes.LOAD),
                      field_type=nodes.TYPE_HIDDEN,
                      rect=(row.x, row.y, row.x_end, row.y_end),
                      label=f"load slot {slot}")
    rec.run.wait_for(livesend.on_galaxy_map, seconds=240,
                     label="the galaxy map after the load")
    rec.run.pump(40)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
