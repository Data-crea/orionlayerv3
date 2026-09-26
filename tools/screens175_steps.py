"""The steps of `tools/screens175_live.py` — imported only once the port is
known to be ours, because importing it builds the real App and connects.

Every step: what the original does (EXPECTED, with its source line), what
the wire says afterwards (OBSERVED), native and HD from one snapshot.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
import livesend  # noqa: E402
from leaders_live import side_by_side  # noqa: E402
from livedrive import Run, SendCounter, close, hashes  # noqa: E402

from core import researchnative as nat  # noqa: E402
from core.structs import leader as leader_struct  # noqa: E402

FOLDER = "work_order_176"


class Live:
    def __init__(self, screen, slot, size):
        self.run = Run(screen, folder=FOLDER)
        self.size, self.slot = size, slot
        if tuple(size) != (1920, 1080):
            self.run.app._apply_resolution(*size)
        self.saves = hashes()
        self.counter = SendCounter(self.run.app.client)
        self.steps = []
        self.run.pump(40)

    # ── plumbing ──────────────────────────────────────────
    @property
    def st(self):
        return self.run.state

    def hd(self, name):
        return self.run.app.dispatcher.screens.get(name)

    def cap(self, name):
        entry = self.run.capture(f"LIVE_{self.size[0]}x{self.size[1]}_{name}")
        entry["side"] = side_by_side(self.run, entry)
        return entry["side"] or entry["hd_png"]

    def step(self, name, expected, observed, ok, capture=True):
        pic = self.cap(name) if capture else None
        self.steps.append({"step": name, "expected": expected,
                           "observed": observed, "ok": bool(ok),
                           "evidence": pic})
        print(f"  {'OK ' if ok else 'BAD'} {name}: {observed}")
        return ok

    def wait(self, pred, seconds=20, label=""):
        return self.run.wait_for(lambda st: _safe(pred), seconds, label)

    def click_native(self, screen, native_rect, button=1, frames=20):
        r = nat.window_rect(native_rect, screen.layout)
        self.run.hd_click(r[0] + r[2] // 2, r[1] + r[3] // 2, button=button)
        self.run.pump(frames)

    def key(self, keycode, frames=20):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {
            "key": keycode, "mod": 0, "unicode": chr(keycode)
            if keycode < 128 else "", "scancode": 0}))
        self.run.pump(frames)

    def load(self):
        # Left on another screen by an earlier run: its own ESC, to the map.
        for _ in range(4):
            if self.st.current_screen in (0, 10) and (
                    self.st.current_screen == 10 or
                    livesend.on_galaxy_map(self.st)):
                break
            from core import gamebox
            box = gamebox.detect(self.st.fields)
            if box is not None:
                # A box left open by an earlier run: NO, or its dismissal.
                answers = dict(box.buttons())
                f = answers.get("no") or answers.get("dismiss")
                self.run.app.client.activate_field(f.index)
                self.run.pump(30)
                continue
            self.run.app.client.inject_key(27)
            self.run.wait_for(livesend.on_galaxy_map, seconds=15,
                              label="the map (ESC)")
        if self.st.current_screen == 10:
            return self._load_from_main_menu()
        out = gameload.load_slot(self.run, self.slot)
        self.step("load", f"SAVE{self.slot} loaded through the game's own "
                  f"Load dialog", f"loaded={out.get('loaded')} "
                  f"{gameload.fingerprint(self.st)}", out.get("loaded"),
                  capture=False)
        return out.get("loaded")

    def _load_from_main_menu(self):
        """The main menu's LOAD (a hidden field, hotkey 'L', mainmenu.cpp:
        132), then the slot's row in the CENTRED Load dialog: 197 x 24
        rows, ten, top to bottom (loadsave.cpp:224-229, :263). Checked
        against the file's own header after the load."""
        disk = gameload.file_header(self.slot)
        f = next((f for f in self.st.fields or [] if f.index and
                  f.hotkey == ord("L") and (f.x, f.y) == (0x19F, 0xC3)), None)
        if f is None or disk is None:
            self.step("load", "the main menu's LOAD", "no LOAD field or no "
                      "valid save", False, capture=False)
            return False
        self.run.app.client.activate_field(f.index)

        def rows():
            return sorted((r for r in self.st.fields or [] if r.index and
                           r.x_end - r.x == 0xe2 - 0x1d and
                           r.y_end - r.y == 0x18), key=lambda r: r.y)
        self.run.wait_for(lambda st: len(rows()) == 10, seconds=30,
                          label="the Load dialog")
        rs = rows()
        if len(rs) != 10:
            self.step("load", "the Load dialog's ten rows", f"{len(rs)} rows",
                      False, capture=False)
            return False
        self.cap("main_menu_load_dialog")
        self.run.app.client.activate_field(rs[self.slot - 1].index)
        arrived = self.run.wait_for(livesend.on_galaxy_map, seconds=240,
                                    label="the galaxy map after the load")
        self.run.pump(30)
        ok = arrived and int(self.st.stardate) == int(disk["stardate"])
        self.step("load", f"SAVE{self.slot} loaded from the main menu's Load "
                  f"dialog (row {self.slot})", f"map {arrived}, stardate "
                  f"{self.st.stardate} (file {disk['stardate']}) "
                  f"{disk['description']!r}", ok, capture=False)
        return ok

    def open_nav(self, key, screen_id, hd_name, ready=lambda: True):
        gm = self.hd("galaxy_map")
        rect = pygame.Rect(*gm.layout.rect(gm.box_rect(key)))
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                             {"pos": rect.center, "button": 1}))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                             {"pos": rect.center, "button": 1}))
        ok = self.run.wait_for(
            lambda st: st.current_screen == screen_id and
            self.run.app.dispatcher.active_name == hd_name and _safe(ready),
            seconds=40, label=hd_name)
        return ok

    def back_to_map(self):
        return self.run.wait_for(livesend.on_galaxy_map, seconds=40,
                                 label="the galaxy map")

    def leaders(self):
        raws = getattr(self.st, "leaders_raw", None) or []
        return leader_struct.parse_all(raws) if len(raws) == 67 else []

    def finish(self, extra=None):
        counts, sent = self.counter.snapshot()
        self.counter.release()
        rec = {"slot": self.slot, "size": list(self.size),
               "steps": self.steps, "sends": counts,
               "sent": [list(x) for x in sent], **(extra or {})}
        self.run.save_record({**rec, **close(self.run, self.saves)})
        # One record per run, beside the pictures (the size, the slot, the
        # mod folder in its name): record.json alone is the last run's.
        tag = (getattr(self, "phase_tag", "") +
               f"slot{self.slot}_{self.size[0]}x{self.size[1]}" +
               ("_mod" if os.environ.get("ORIONLAYER_USER_DIR") else ""))
        os.replace(os.path.join(self.run.dir, "record.json"),
                   os.path.join(self.run.dir, f"record_{tag}.json"))
        bad = [s["step"] for s in self.steps if not s["ok"]]
        print(f"  {len(self.steps) - len(bad)} of {len(self.steps)} steps OK"
              + (f"; NOT: {bad}" if bad else ""))
        return 0 if not bad else 1


def _safe(pred):
    try:
        return bool(pred())
    except Exception:
        return False


from screens175_leaders import leaders_phase, hire_phase  # noqa: E402
from screens175_others import races_phase, info_phase, fleets_phase  # noqa: E402

PHASES = {"leaders": leaders_phase, "hire": hire_phase, "races": races_phase,
          "info": info_phase, "fleets": fleets_phase}
