#!/usr/bin/env python3
"""Every transition into and out of every HD screen, frame by frame.

    python tools/flash_walk.py [W H] [--pregame-only | --ingame-only]

Work order 180, part A1 (and A2's live verification, the same walk run
again). Data saw the game's own picture, with a sentence on the left,
flash up before an HD screen appeared. This walks every screen the
registry names — `dispatcher.screen_map`, read from the running App and
never from a list here — in both directions, and counts the native
frames each transition presented before the target's first HD frame.

TWO VERDICTS PER FRAME, and they are reported side by side:

  the trace   `core.frametrace` — the branch `App._render` took (hd,
              net, fill), recorded by the product itself
  the pixels  the window compared, inside the 4:3 picture area, against
              the product's own rendering of the game's picture — work
              order 166 A's method (`entry_glimpse.shows_picture`),
              because a flag reported as an observation was wrong once

THE FRONT DOOR. Every entry is what a player does in the HD window: a
click on the HD button (nav bar, title plate, research window, frame
button, race cell) or a key into the HD window, posted as a pygame event
and handled by the product. Exits are ESC into the HD window, which the
screens forward to the game as the original's own way back. The one
exception is loading the scratch slot, which goes through `livesend`
against the list read at that moment, as `tools/gameload.py` does.

Nothing is saved: no TURN, no SAVE. The Load dialog loads SAVE4
(scratch); liveguard is run by the caller before and after.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
import livesend  # noqa: E402
from livedrive import Run, close, hashes  # noqa: E402
from entry_glimpse import probe_points, shows_picture  # noqa: E402

from core import frametrace  # noqa: E402
from screens.game_menu import nodes  # noqa: E402

#: The evidence folder: the work order running the tool (180 wrote it;
#: 181 runs it again), `ORIONLAYER_EVIDENCE_FOLDER` to name it.
FOLDER = os.environ.get("ORIONLAYER_EVIDENCE_FOLDER", "work_order_180")
SLOT = 4
#: Consecutive frames of the target's own HD picture that end a watch.
SETTLED = 30
TIMEOUT = 30.0


class Walk:
    def __init__(self, size, tag):
        self.size = tuple(size)
        self.run = Run(f"{tag}_{size[0]}x{size[1]}", folder=FOLDER)
        app = self.run.app
        if self.size != (app.win_w, app.win_h):
            app._apply_resolution(*self.size)
        self.trace = app._frame_trace
        assert self.trace is not None, "frame trace is off"
        self.points = probe_points(app)
        self.rows = []
        self.pixels = []           # one verdict per traced frame
        self._flash_saved = True   # armed per transition
        self._current = ""

    # ── the loop ──────────────────────────────────────────
    @property
    def app(self):
        return self.run.app

    @property
    def st(self):
        return self.run.state

    def frame(self):
        app = self.app
        app._handle_events()
        app._update()
        app._render()
        native = shows_picture(app, self.points)
        self.pixels.append(native)
        last = self.trace.frames[-1] if self.trace.frames else None
        if (native or (last and last["source"] == frametrace.NET)) \
                and not self._flash_saved:
            # THE FLASH ITSELF, once per transition: the window as it
            # was presented and the game's framebuffer of the same frame.
            self._flash_saved = True
            self.run.capture(f"FLASH_{self._current}")
        time.sleep(0.015)

    def hd(self, name):
        return self.app.dispatcher.screens.get(name)

    def top_name(self):
        d = self.app.dispatcher
        return d.overlay_name or d.active_name

    # ── inputs, all through the HD window ────────────────
    def click(self, x, y):
        pygame.event.clear()
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            pygame.event.post(pygame.event.Event(
                kind, {"pos": (int(x), int(y)), "button": 1}))

    def click_rect(self, rect):
        x, y, w, h = rect
        self.click(x + w // 2, y + h // 2)

    def key(self, keycode):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {
            "key": keycode, "mod": 0, "scancode": 0,
            "unicode": chr(keycode) if keycode < 128 else ""}))

    # ── one transition ────────────────────────────────────
    def transition(self, name, target, action, ready=None):
        """Do `action`, watch until `target` has drawn SETTLED frames in
        a row (and `ready(state)` holds, if given), or TIMEOUT."""
        mark = self.trace.mark()
        pix0 = len(self.pixels)
        self._current = name.replace(" ", "").replace(">", "")
        self._flash_saved = False
        start = time.monotonic()
        action()
        streak, settled = 0, False
        while time.monotonic() - start < TIMEOUT:
            self.frame()
            last = self.trace.frames[-1]
            ok = (last["source"] == frametrace.HD and last["hd"] == target
                  and (ready is None or ready(self.st)))
            streak = streak + 1 if ok else 0
            if streak >= SETTLED:
                settled = True
                break
        frames = self.trace.since(mark)
        pix = self.pixels[pix0:pix0 + len(frames)]
        for f, p in zip(frames, pix):
            f["pixels_native"] = bool(p)
        summary = frametrace.summarise(frames, target)
        first = summary["first_hd_frame"]
        head = frames if first is None else frames[:first]
        summary["pixel_native_before_hd"] = sum(
            1 for f in head if f["pixels_native"])
        summary["pixel_native_total"] = sum(
            1 for f in frames if f["pixels_native"])
        summary["disagree"] = sum(
            1 for f in frames
            if f["pixels_native"] != (f["source"] == frametrace.NET))
        row = {"transition": name, "target": target, "settled": settled,
               "seconds": round(time.monotonic() - start, 2),
               "size": list(self.size), **summary, "trace": frames}
        self.rows.append(row)
        flag = "" if summary["native_total"] == 0 else "  <-- NATIVE"
        print(f"  {name:38s} settled={settled!s:5s} "
              f"native-before-HD {summary['native_before_hd']:3d} "
              f"({summary['native_seconds']:.3f} s) "
              f"total {summary['native_total']:3d} "
              f"pixels {summary['pixel_native_before_hd']:3d}/"
              f"{summary['pixel_native_total']:3d}"
              f" held {summary['held']:3d}"
              f"{' kinds=' + ','.join(summary['kinds']) if summary['kinds'] else ''}"
              f"{flag}")
        if summary["native_total"]:
            for r in summary["reasons"]:
                print(f"      reason: {r}")
        self._flash_saved = True
        if settled:
            self.run.capture(f"{name}_settled")
        return settled

    def settle(self, frames=20):
        for _ in range(frames):
            self.frame()

    # ── the two legs ──────────────────────────────────────
    def pregame(self):
        """Main menu, New Game, Select Race, Empire Identity, Custom Race
        — `tools/flash_legs.pregame`."""
        import flash_legs
        flash_legs.pregame(self)

    def load(self):
        """Main menu -> Load dialog (the GAME menu overlay) -> SAVE4."""
        # The menu's OWN list first: during its opening animation the hand-
        # over gate holds the frame and takes no input (180 A2), so an L
        # pressed then is dropped, as a player's would be.
        mm = self.app.dispatcher.screens.get("main_menu")
        self.run.wait_for(lambda st: st.current_screen != 10 or
                          nodes.classify(st.fields) == nodes.LOAD or
                          mm._own_list(st.fields or []), seconds=30,
                          label="the main menu's own list")
        self.settle(10)
        if nodes.classify(self.st.fields) != nodes.LOAD:
            self.transition("main_menu -> load dialog", "game_menu",
                            lambda: self.key(pygame.K_l),
                            lambda st: nodes.classify(st.fields) == nodes.LOAD)
        # The main menu runs the dialog at another base than the GAME
        # popup (+36, +26 against loadsave.cpp:263's, measured here), so
        # `gameload.slot_row`'s rectangle test refuses it. The row is the
        # fourth of `slot_rows` (top to bottom) AND the dialog's own slot
        # record must agree with the file on disk — the same two sources
        # about WHICH save, without the in-game rectangle.
        rows = nodes.slot_rows(self.st.fields)
        verdict = gameload.agreement(SLOT, gameload.file_header(SLOT),
                                     gameload.wire_slot(self.run, SLOT))
        if len(rows) != nodes.SLOTS or verdict != "agrees":
            raise livesend.WrongDialog(
                f"{len(rows)} slot rows, slot {SLOT} {verdict} — nothing sent")
        row = rows[SLOT - 1]
        print(f"  slot {SLOT}: row field {row.index}, {verdict}")

        def send():
            livesend.activate(self.app.client, row.index,
                              shape=livesend.in_game_menu(nodes.LOAD),
                              field_type=nodes.TYPE_HIDDEN,
                              rect=(row.x, row.y, row.x_end, row.y_end),
                              label=f"load slot {SLOT}")
        ok = self.transition(f"load dialog -> galaxy_map (SAVE{SLOT})",
                             "galaxy_map", send, livesend.on_galaxy_map)
        return ok and self.st.current_screen == 0

    def ingame(self):
        # A walk that clicks the map's buttons anywhere else clicks some
        # other screen's controls: refuse unless the map's list is up.
        if not livesend.on_galaxy_map(self.st):
            raise livesend.WrongDialog(
                f"in-game leg: the game reports screen "
                f"{self.st.current_screen} without the galaxy map's list "
                f"— nothing clicked")
        gm = self.hd("galaxy_map")
        back = livesend.on_galaxy_map
        registry = self.app.dispatcher.screen_map
        for spec in gm._data.get("buttons", []):
            key = spec["key"]
            if key == "turn":
                continue            # TURN writes SAVE10 — never pressed
            target = registry.get(self._nav_screen_id(key))
            if target is None:
                print(f"  {key}: no HD screen registered — skipped")
                continue
            if not self.transition(f"galaxy_map -> {target}", target,
                                   lambda k=key: self.click_rect(
                                       gm.nav_rect(k))):
                self._home()
                continue
            self.transition(f"{target} -> galaxy_map", "galaxy_map",
                            lambda: self.key(pygame.K_ESCAPE), back)
            self._home()
        self.transition("galaxy_map -> game_menu", "game_menu",
                        lambda: self.click_rect(gm.title_rect()),
                        lambda st: nodes.classify(st.fields) == nodes.MENU)
        self.transition("game_menu -> galaxy_map", "galaxy_map",
                        lambda: self.key(pygame.K_ESCAPE), back)
        self._home()
        box = next(b for b in (gm.box_rect("sb_research_text"),
                               gm.box_rect("sb_research_icon")) if b)
        self.transition("galaxy_map -> research_change", "research_change",
                        lambda: self.click_rect(gm.layout.rect(box)),
                        self.run.on_screen(36))
        self.transition("research_change -> galaxy_map", "galaxy_map",
                        lambda: self.key(pygame.K_ESCAPE), back)
        self._home()

    def boxes(self):
        """The galaxy map's own boxes: the system window on the home star
        (a click on an owned star with no fleet box open is no order,
        decision 65), then ESC closes it (decision 66's CLOSE field)."""
        gm = self.hd("galaxy_map")
        star, view = gm.home_star(), gm._map_view()
        if star is None or view is None:
            print("  boxes: no home star or view — skipped")
            return
        x, y = view.to_screen(star.x, star.y)
        before = len(self.st.fields or [])
        self.transition("galaxy_map -> system window", "galaxy_map",
                        lambda: self.click(x, y),
                        lambda st: len(st.fields or []) != before)
        self.transition("system window -> galaxy_map", "galaxy_map",
                        lambda: self.key(pygame.K_ESCAPE),
                        lambda st: len(st.fields or []) == before)
        self._home()

    #: The engine's screen for each nav button (mainscr_main.cpp's
    #: handlers; the ids are `core/screen_names.py`'s).
    NAV_SCREENS = {"colonies": 20, "planets": 32, "fleets": 4,
                   "leaders": 29, "races": 6, "info": 9}

    def _nav_screen_id(self, key):
        return self.NAV_SCREENS.get(key)

    def _home(self):
        """Back on the galaxy map's own list, whatever happened."""
        if livesend.on_galaxy_map(self.st):
            self.settle(10)
            return
        esc = next((f for f in (self.st.fields or [])
                    if f.index != 0 and f.hotkey == 0x1B), None)
        if esc is not None:
            print(f"  (home: ESC field {esc.index} on screen "
                  f"{self.st.current_screen})")
            self.app.client.activate_field(esc.index)
        self.run.wait_for(livesend.on_galaxy_map, seconds=20,
                          label="the galaxy map")
        self.settle(10)

    def save(self, extra):
        rows = [{k: v for k, v in r.items() if k != "trace"}
                for r in self.rows]
        path = os.path.join(self.run.dir, "transitions.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"size": list(self.size), "rows": rows, **extra},
                      fh, indent=1)
        with open(os.path.join(self.run.dir, "trace.jsonl"), "w",
                  encoding="utf-8") as fh:
            for r in self.rows:
                for f in r["trace"]:
                    fh.write(json.dumps({"transition": r["transition"],
                                         **f}) + "\n")
        self.run.save_record(extra)
        print(f"  table: {path}")


def main(argv):
    # The trace is opened by `App.__init__`, i.e. inside `Run`, so it has
    # to be switched on before the Walk builds one — not at import.
    os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1])) if len(args) >= 2 else (1920, 1080)
    tag = os.environ.get("FLASH_WALK_TAG", "A1_walk")
    saves = hashes()
    walk = Walk(size, tag)
    # The first snapshot, before anything is decided from the screen id:
    # -1 until HELLO_REPLY and the first state arrive.
    walk.run.wait_for(lambda st: st.current_screen >= 0, seconds=30,
                      label="the first snapshot")
    if "--ingame-only" not in argv:
        walk.pregame()
    if "--pregame-only" not in argv:
        if walk.st.current_screen == 10 and not walk.load():
            print("!! the load did not arrive — in-game leg skipped")
        else:
            repeat = next((int(a.split("=", 1)[1]) for a in argv
                           if a.startswith("--repeat=")), 1)
            for _ in range(repeat):
                walk.ingame()
                walk.boxes()
    closed = close(walk.run, saves)
    walk.save({"registry": {str(k): v for k, v in
                            walk.app.dispatcher.screen_map.items()},
               **closed})
    bad = [r["transition"] for r in walk.rows if r["native_total"]]
    print(f"\n  {len(walk.rows)} transitions, {len(bad)} with native frames")
    # Work order 188: a native frame without F12 ANYWHERE in the run —
    # between the recorded transitions too — fails the walk.
    return 1 if bad or closed["native_frames"].get("without_f12") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
