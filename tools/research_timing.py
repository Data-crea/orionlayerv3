#!/usr/bin/env python3
"""Open the research screen again and again, and time every entry.

    python tools/research_timing.py W H [--entries N] [--icon N]
                                   [--tag NAME] [--profile] [--no-load]

Work order 184, part 1. The real `main.App`, headless (or on the real
desktop with `ORIONLAYER_REAL_DESKTOP`), ONE client, with
`core/entrytiming` switched on: every entry into the research screen is
recorded phase by phase, (a) to (e) — see that module for the phases and
for what it cannot see.

THE FRONT DOOR. Each entry is what a player does: a left click in the HD
window on the galaxy map's research window (`sb_research_text`, or
`sb_research_icon` for `--icon`), posted as a pygame event and handled by
the product (`mapinput.click`). Each exit is ESC into the HD window, which
change mode sends as its exit button (tech.cpp:357, nothing changed). No
row is ever activated — open fix 23 — and nothing is committed.

THE LOOP IS THE PRODUCT'S. A frame is `_handle_events`, `_update`,
`_render` and `app.clock.tick(TARGET_FPS)`, exactly `main.App.run`, so the
frame-alignment the timings contain is the one a player gets. Between
entries the map is left standing `REST` frames, so every entry starts from
the engine's steady map loop and not from the tail of the previous exit.

Also on: the frame trace, so every entry says how many native frames it
presented (the flash rule of 180: none).

SAVE4 is loaded (scratch; `--no-load` when it already is); nothing is
saved. The caller runs `tools/liveguard.py` before and after.
"""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ORIONLAYER_ENTRY_TIMING", "1")
os.environ.setdefault("ORIONLAYER_FRAME_TRACE", "1")
os.environ.setdefault("ORIONLAYER_EVIDENCE_FOLDER", "work_order_184")

import vdisplay  # noqa: E402
vdisplay.headless_clients()

import pygame  # noqa: E402

import flash_walk  # noqa: E402
import gameload  # noqa: E402
import livesend  # noqa: E402
from livedrive import close, hashes  # noqa: E402
from researchchangephases import SCREEN_CHANGE, ensure_on_map  # noqa: E402

from core import frametrace  # noqa: E402
from core.config import TARGET_FPS  # noqa: E402

FOLDER = flash_walk.FOLDER
SLOT = flash_walk.SLOT
#: Frames the map stands between entries (~1 s at 60 fps).
REST = 60
#: Frames the drawn panel stands before ESC, so the exit is not measured
#: as part of the entry and the panel is seen settled.
SHOW = 20
TIMEOUT = 30.0


class Timer(flash_walk.Walk):
    """The flash walk's loader (the main menu's Load dialog, SAVE4) and
    its pixel verdict while loading; while MEASURING, the product's own
    loop and nothing else — the per-frame pixel comparison would be time
    the player never spends."""

    def __init__(self, size, tag):
        super().__init__(size, tag)
        self.timing = self.app._entry_timing
        assert self.timing is not None, "entry timing is off"
        self.measuring = False
        # THE RAW PAYLOADS of the last message of each kind, so the
        # settled panel can be replayed offline (`tools/research_render.py`)
        # — the player's data, written to the evidence folder only.
        self.raw = {}
        client = self.app.client
        real = client._handle_message

        from core.wire_protocol import MSG_FIELDS, MSG_VISUAL
        self.list_visual = None
        #: Every visual of the current entry, (perf_counter, framebuffer),
        #: from the click on — for the native floor (order part 1.4).
        self.visual_log = None
        self._armed = False

        def keep(msg_type, flags, payload):
            self.raw[msg_type] = payload
            result = real(msg_type, flags, payload)
            # THE FRAMEBUFFER THAT CAME WITH THE LIST: the engine sends
            # state, fields, visual per `Tick` (ext_api.cpp:1135-1172),
            # so the visual after the first non-empty list of an entry is
            # the native picture of that same snapshot (order part 1.4).
            entry = self.timing._entry
            if msg_type == MSG_FIELDS and entry is not None and \
                    self.list_visual is None and client.state.fields:
                self._armed = True
            elif msg_type == MSG_VISUAL and self._armed:
                self.list_visual, self._armed = payload, False
            if msg_type == MSG_VISUAL and self.visual_log is not None \
                    and len(self.visual_log) < 60:
                self.visual_log.append((time.perf_counter(),
                                        payload[:640 * 480]))
            return result
        client._handle_message = keep
        self.fixture = None

    def save_fixture(self, name):
        from core.wire_protocol import MSG_FIELDS, MSG_STATE, MSG_VISUAL
        folder = os.path.join(self.run.dir, name)
        os.makedirs(folder, exist_ok=True)
        for kind, label in ((MSG_STATE, "state"), (MSG_FIELDS, "fields"),
                            (MSG_VISUAL, "visual")):
            with open(os.path.join(folder, f"{label}.bin"), "wb") as fh:
                fh.write(self.raw.get(kind, b""))
        return folder

    def frame(self):
        if not self.measuring:
            return super().frame()
        app = self.app
        app._handle_events()
        app._update()
        app._render()
        app.clock.tick(TARGET_FPS)

    def frames(self, n):
        for _ in range(n):
            self.frame()

    def wait(self, ready, label):
        start = time.monotonic()
        while time.monotonic() - start < TIMEOUT:
            self.frame()
            if ready():
                return True
        print(f"  ! timed out waiting for {label}")
        return False

    def click_box(self, box_name):
        gm = self.app.dispatcher.screens["galaxy_map"]
        # The map's boxes exist once it is ENTERED; right after a way back
        # (`_home`) the wire may say map a frame before the HD map is.
        self.wait(lambda: gm.box_rect(box_name) is not None,
                  f"the galaxy map's {box_name} box")
        box = gm.box_rect(box_name)
        x, y, w, h = gm.layout.rect(box)
        pygame.event.clear()
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            pygame.event.post(pygame.event.Event(
                kind, {"pos": (x + w // 2, y + h // 2), "button": 1}))

    def key(self, keycode):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {
            "key": keycode, "mod": 0, "scancode": 0,
            "unicode": chr(keycode) if keycode < 128 else ""}))

    def on_map(self):
        d = self.app.dispatcher
        return (livesend.on_galaxy_map(self.run.state)
                and d.overlay is None and d.active_name == "galaxy_map")

    def entry(self, n, box_name):
        """One entry and its exit. Returns the timing record or None."""
        done = len(self.timing.entries)
        self.list_visual, self._armed = None, False
        self.visual_log = []
        mark = self.trace.mark()
        self.click_box(box_name)
        ok = self.wait(lambda: len(self.timing.entries) > done,
                       f"entry {n} to be timed")
        rec = self.timing.entries[done] if ok else None
        self.frames(SHOW)
        if rec is not None and self.fixture is None:
            self.fixture = self.save_fixture("fixture_36")
        if rec is not None and self.list_visual is not None:
            rec["list_vs_settled_px"] = native_difference(
                self.list_visual, self.raw.get(MSG_VISUAL_ID, b""))
        if rec is not None:
            rec["native"] = native_floor(rec, self.visual_log,
                                         self.raw.get(MSG_VISUAL_ID, b""))
        self.visual_log = None
        frames = self.trace.since(mark)
        summary = frametrace.summarise(frames, "research_change")
        if rec is not None:
            rec["box"] = box_name
            rec["native_frames"] = summary["native_total"]
            rec["held_frames"] = summary["held"]
            rec["waiting_frames"] = sum(
                1 for f in frames[:summary["first_hd_frame"] or 0]
                if f["screen"] == SCREEN_CHANGE)
            nat = rec.get("native") or {}
            print(f"  {n:2d} {box_name:16s} "
                  f"{'first' if rec['first_after_start'] else 'later'} "
                  f"total {rec.get('total_ms', 0):7.1f} ms  "
                  f"a {rec.get('a_ms', 0):5.1f} b {rec.get('b_ms', 0):6.1f} "
                  f"c {rec.get('c_ms', 0):6.1f} ({rec.get('snaps_c')} snaps) "
                  f"d {rec['d_ms']:6.1f} d_ready "
                  f"{rec.get('d_ready_ms', 0):5.1f} e {rec.get('e_ms', 0):5.1f}"
                  f"  native {rec['native_frames']} held "
                  f"{rec['held_frames']}  engine's panel on the wire "
                  f"{nat.get('ms_after_click')} ms")
        self.key(pygame.K_ESCAPE)
        self.wait(self.on_map, f"the map after entry {n}")
        self.frames(REST)
        return rec


MSG_VISUAL_ID = 0x12      # core.wire_protocol.MSG_VISUAL


def native_difference(a, b):
    """How many of the 640x480 framebuffer pixels differ between two
    visual payloads (the palette after them is left out), and where:
    `{"pixels": n, "box": [x0, y0, x1, y1] or None}`."""
    n = 640 * 480
    fa, fb = a[:n], b[:n]
    if len(fa) != n or len(fb) != n:
        return None
    diff = [i for i in range(n) if fa[i] != fb[i]]
    if not diff:
        return {"pixels": 0, "box": None}
    xs = [i % 640 for i in diff]
    ys = [i // 640 for i in diff]
    return {"pixels": len(diff), "box": [min(xs), min(ys), max(xs), max(ys)]}


#: A framebuffer within this many pixels of the settled panel IS the
#: panel: the loop redraws its selection box every pass, so a byte-for-
#: byte test would never be met by some entries (Part 1: 16 of 25).
NATIVE_TOLERANCE = 640 * 480 // 100


def native_floor(rec, log, settled):
    """When the engine's own panel was first on the wire, from the click.

    `{"ms_after_t2": ..., "ms_after_click": ..., "diff_px": ...}` for the
    first visual within `NATIVE_TOLERANCE` of the settled one, measured
    against `rec`'s own t2 and (a)+(b); None if none was."""
    import numpy as np
    ref = np.frombuffer(settled[:640 * 480], np.uint8)
    if ref.size != 640 * 480 or not log:
        return None
    for t, fb in log:
        a = np.frombuffer(fb, np.uint8)
        if a.size != ref.size:
            continue
        diff = int((a != ref).sum())
        if diff <= NATIVE_TOLERANCE:
            after_t2 = round((t - rec["t2_abs"]) * 1000, 1)
            return {"ms_after_t2": after_t2,
                    "ms_after_click": round(after_t2 + rec.get("a_ms", 0)
                                            + rec.get("b_ms", 0), 1),
                    "diff_px": diff}
    return None


def stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"n": len(values), "median": round(statistics.median(values), 1),
            "max": round(max(values), 1), "min": round(min(values), 1)}


def report(recs):
    """Median / max per phase, first entry and later ones apart."""
    out = {}
    for label, sel in (("first", [r for r in recs if r["first_after_start"]]),
                       ("later", [r for r in recs
                                  if not r["first_after_start"]])):
        if not sel:
            continue
        row = {k: stats([r.get(k) for r in sel]) for k in
               ("total_ms", "a_ms", "b_ms", "c_ms", "d_ms", "d_ready_ms",
                "e_ms", "snaps_c", "snaps_b", "snap_rate")}
        tot = sum(r["total_ms"] for r in sel if r.get("total_ms"))
        if tot:
            row["share"] = {k: round(100 * sum(r.get(k, 0) for r in sel)
                                     / tot, 1)
                            for k in ("a_ms", "b_ms", "c_ms", "d_ready_ms",
                                      "e_ms")}
        row["native_frames"] = sum(r.get("native_frames", 0) for r in sel)
        out[label] = row
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    size = (int(args[0]), int(args[1]))
    opt = lambda k, d: next((a.split("=", 1)[1] for a in argv  # noqa: E731
                             if a.startswith(f"--{k}=")), d)
    entries, icon = int(opt("entries", 20)), int(opt("icon", 0))
    tag = opt("tag", "P1")
    if "--profile" in argv:
        os.environ["ORIONLAYER_ENTRY_PROFILE"] = os.path.join(
            os.path.expanduser("~/orionlayer-fixtures/evidence"), FOLDER,
            f"{tag}_{size[0]}x{size[1]}", "profile")
    saves = hashes()
    t = Timer(size, tag)
    t.run.pump(30)
    if "--no-load" not in argv:
        if t.run.state.current_screen == 10:
            if not t.load():            # from the main menu (flash walk)
                return 1
        else:
            ensure_on_map(t.run)
            if not gameload.load_slot(t.run, SLOT)["loaded"]:
                return 1
    ensure_on_map(t.run)
    if not livesend.on_galaxy_map(t.run.state):
        t._home()            # the flash walk's way back: the list's ESC field
    t.measuring = True
    t.wait(t.on_map, "the galaxy map")
    t.frames(REST)
    t.save_fixture("fixture_map")
    print(f"  {size[0]}x{size[1]}: {entries} entries by the research "
          f"window's text, {icon} by its icon")
    recs = []
    for i in range(1, entries + 1):
        recs.append(t.entry(i, "sb_research_text"))
    for i in range(1, icon + 1):
        recs.append(t.entry(entries + i, "sb_research_icon"))
    good = [r for r in recs if r and r.get("reached")]
    text = [r for r in good if r["box"] == "sb_research_text"]
    summary = {"text": report(text),
               "icon": report([r for r in good
                               if r["box"] == "sb_research_icon"]),
               "lost": len(recs) - len(good)}
    profiles = t.timing.dump_profiles()
    path = os.path.join(t.run.dir, "timing.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"size": list(size), "entries": recs, "summary": summary,
                   "profiles": profiles, **close(t.run, saves)}, fh,
                  indent=1)
    print(f"\nSUMMARY {size[0]}x{size[1]}: {json.dumps(summary)}")
    for key, p in profiles.items():
        print(f"  profile {key}: {p['path']}")
        for r in p["top_cum"]:
            print(f"    cum {r['cum_ms']:8.2f} own {r['own_ms']:7.2f} "
                  f"x{r['calls']:<6} {r['call']}")
    print(f"  record: {path}")
    return 0 if not summary["lost"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
