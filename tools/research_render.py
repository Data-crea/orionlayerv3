#!/usr/bin/env python3
"""The research panel rendered offline from a recorded snapshot — work order 184.

    python tools/research_render.py FIXTURE_DIR OUT_DIR [--sizes 1920x1080,...]
                                   [--sequence] [--profile]

Work order 184 part 2 may change how the research screen PREPARES its
frame, never what the frame IS: "renders at 1920, 2576 and 3840 must be
pixel-identical before and after." This is the instrument for that claim.

WHAT IT DOES. The real `main.App`, headless and NOT connected to an
engine; the client's state is filled from the raw payloads
`tools/research_timing.py` recorded on the live wire (`state.bin`,
`fields.bin`, `visual.bin` of the settled change-mode panel — the
player's data, so the fixture lives in the evidence folder, never in the
tree). Then the app's own `_update` / `_render` run until the research
screen is `READY` and a few frames more, and the window surface is saved
as a PNG with the sha256 of its pixels.

THE CLOCK IS FROZEN, because the galaxy map under the panel animates —
the black hole turns on `time.time()`, destination lines move on
`pygame.time.get_ticks()`, the home ping on `time.monotonic()`. Frozen,
two runs of the same tree give the same bytes, and a difference between
two trees is a difference in what they draw.

`--sequence` renders the path a cache has to survive, and each step is
its own PNG: enter at the size, leave to the map, enter again (the second
entry, which a cache serves), then resize to each other size and back.
Every render of one size must equal every other render of that size.

`--profile` prints the ten most expensive calls of the FIRST ready frame
and how many HUD shapes it built (`core.hud.raster.shape`).
"""
import cProfile
import hashlib
import json
import os
import pstats
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vdisplay  # noqa: E402
vdisplay.headless_clients()

# THE FROZEN CLOCK, before anything that reads it is imported.
_T = 1_000_000.0
time.time = lambda: _T
time.monotonic = lambda: _T
import pygame  # noqa: E402
pygame.time.get_ticks = lambda: 0

import main as main_module  # noqa: E402
from core import game_state  # noqa: E402
from core.hud import raster  # noqa: E402

SIZES = ((1920, 1080), (2576, 1432), (3840, 2160))
#: Frames of the list-less first snapshot before the list comes.
WAIT_FRAMES = 3


def _never_connect(app):
    """NO ENGINE, EVER. `main.App.__init__` connects to whatever listens
    on the port — found the hard way on 27 September 2026, when this
    harness's first run attached to the engine a live run had left up and
    drew ITS snapshots instead of the fixture's. A render harness is not a
    client (one client at a time, work order 126)."""
    app.connected = False


main_module.App._connect = _never_connect


class Harness:
    def __init__(self, fixture):
        self.app = main_module.App()
        assert not self.app.client.connected, "the harness connected"
        self.app.connected = True          # the client itself stays closed
        self.fixture = fixture
        self.map_fixture = os.path.join(os.path.dirname(fixture),
                                        "fixture_map")
        self.shapes = 0
        real = raster.shape

        def counted(*a, **k):
            self.shapes += 1
            return real(*a, **k)
        raster.shape = counted

    def load(self, folder):
        def read(name):
            with open(os.path.join(folder, name), "rb") as fh:
                return fh.read()
        st = game_state.parse_state(read("state.bin"))
        st.fields = game_state.parse_fields(read("fields.bin"))
        st.framebuffer, st.palette = game_state.parse_visual(read("visual.bin"))
        st.save_slots = None
        self.app.client.state = st

    def frame(self):
        self.app._update()
        self.app._render()

    def research(self):
        return self.app.dispatcher.screens["research_change"]

    def enter(self, profile=None):
        """Feed the 36 snapshot until the panel is READY and drawn.

        The frame reported is THE ONE ON WHICH THE PANEL FIRST DRAWS —
        the dispatcher opens the overlay and the screen validates in that
        same frame's `_update`, so a test made before the frame would
        report the frame after it (the first version did, and measured a
        warm frame as the first)."""
        # THE WAIT FIRST, as the wire has it: the first snapshot at 36
        # carries no fields (the list `Clear_Fields_` left), the list
        # comes ~550 ms later (`core/researchprepare.py`). A few frames of
        # the empty list, then the fixture's own.
        self.load(self.fixture)
        fields = self.app.client.state.fields
        self.app.client.state.fields = []
        waited = self.shapes
        wait_t = time.perf_counter()
        for _ in range(WAIT_FRAMES):
            self.frame()
        wait_ms = round((time.perf_counter() - wait_t) * 1000, 1)
        waited = self.shapes - waited
        self.app.client.state.fields = fields
        before = self.shapes
        for _ in range(200):
            scr = self.research()
            was_ready = (self.app.dispatcher.overlay is scr
                         and scr.state == scr.READY_STATE)
            prof = cProfile.Profile() if profile is not None else None
            built = self.shapes
            t = time.perf_counter()
            if prof is not None:
                prof.enable()
            self.frame()
            if prof is not None:
                prof.disable()
            dt = time.perf_counter() - t
            ready = (self.app.dispatcher.overlay is scr
                     and scr.state == scr.READY_STATE)
            if ready:
                if prof is not None:
                    profile.append(prof)
                return {"first_ready_frame_ms": round(dt * 1000, 1),
                        "shapes_built": self.shapes - built,
                        "was_ready": was_ready,
                        "wait_frames_ms": wait_ms,
                        "shapes_built_waiting": waited}
        raise SystemExit("the research screen never became READY")

    def leave(self):
        self.load(self.map_fixture)
        for _ in range(5):
            self.frame()

    def resize(self, w, h):
        self.app._apply_resolution(w, h)

    def shot(self, out, name):
        for _ in range(3):
            self.frame()
        surf = self.app.surface
        digest = hashlib.sha256(
            pygame.image.tobytes(surf, "RGB")).hexdigest()
        path = os.path.join(out, f"{name}.png")
        pygame.image.save(surf, path)
        return {"png": path, "sha256": digest,
                "size": list(surf.get_size())}


def one_size(w, h, fixture, out, argv):
    """Everything for ONE size, in a process of its own: the HUD cache
    and the fonts are module-global, so a second size in the same process
    would start warm and report a first entry that is not one."""
    report = {"renders": {}, "steps": []}
    hz = Harness(fixture)
    hz.resize(w, h)
    hz.leave()
    profs = [] if "--profile" in argv else None
    first = hz.enter(profs)
    shot = hz.shot(out, f"research_{w}x{h}_first")
    report["renders"][f"{w}x{h}"] = shot["sha256"]
    step = {"size": [w, h], "step": "first entry", **first, **shot}
    report["steps"].append(step)
    print(f"  {w}x{h} first entry: {first} {shot['sha256'][:16]}")
    if profs:
        stats = pstats.Stats(profs[0])
        rows = sorted(stats.stats.items(), key=lambda kv: kv[1][3],
                      reverse=True)
        step["top_cum"] = [
            {"call": f"{os.path.relpath(f) if os.path.isabs(f) else f}"
                     f":{ln}({fn})", "calls": v[1],
             "own_ms": round(v[2] * 1000, 2),
             "cum_ms": round(v[3] * 1000, 2)}
            for (f, ln, fn), v in rows[:25]]
        step["top_own"] = [
            {"call": f"{os.path.relpath(f) if os.path.isabs(f) else f}"
                     f":{ln}({fn})", "calls": v[1],
             "own_ms": round(v[2] * 1000, 2),
             "cum_ms": round(v[3] * 1000, 2)}
            for (f, ln, fn), v in sorted(stats.stats.items(),
                                         key=lambda kv: kv[1][2],
                                         reverse=True)[:10]]
        for r in step["top_cum"]:
            print(f"      cum {r['cum_ms']:8.2f} own {r['own_ms']:7.2f} "
                  f"x{r['calls']:<5} {r['call']}")
    if "--sequence" in argv:
        hz.leave()
        second = hz.enter()
        shot2 = hz.shot(out, f"research_{w}x{h}_second")
        report["steps"].append({"size": [w, h], "step": "second entry",
                                **second, **shot2})
        print(f"  {w}x{h} second entry: {second} {shot2['sha256'][:16]} "
              f"{'same' if shot2['sha256'] == shot['sha256'] else 'DIFFERENT'}")
        for ow, oh in SIZES:
            if (ow, oh) == (w, h):
                continue
            hz.resize(ow, oh)
            other = hz.enter()
            s_o = hz.shot(out, f"research_{w}x{h}_via_{ow}x{oh}")
            hz.resize(w, h)
            back = hz.enter()
            s_b = hz.shot(out, f"research_{w}x{h}_back_from_{ow}x{oh}")
            report["steps"].append({"size": [ow, oh],
                                    "step": f"resized from {w}x{h}",
                                    **other, **s_o})
            report["steps"].append({"size": [w, h],
                                    "step": f"back from {ow}x{oh}",
                                    **back, **s_b})
            print(f"  {w}x{h} -> {ow}x{oh} -> back: {other} {back} "
                  f"{s_o['sha256'][:12]} "
                  f"{'same' if s_b['sha256'] == shot['sha256'] else 'DIFFERENT'}")
    return report


def main(argv):
    import subprocess
    args = [a for a in argv if not a.startswith("--")]
    fixture, out = args[0], args[1]
    os.makedirs(out, exist_ok=True)
    one = next((a.split("=", 1)[1] for a in argv
                if a.startswith("--one=")), None)
    if one:
        w, h = (int(v) for v in one.split("x"))
        rep = one_size(w, h, fixture, out, argv)
        with open(os.path.join(out, f"renders_{w}x{h}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
        return 0
    sizes = SIZES
    for a in argv:
        if a.startswith("--sizes="):
            sizes = tuple(tuple(int(v) for v in s.split("x"))
                          for s in a.split("=", 1)[1].split(","))
    report = {"fixture": fixture, "renders": {}, "steps": []}
    for w, h in sizes:
        code = subprocess.call([sys.executable, os.path.abspath(__file__),
                                *argv, f"--one={w}x{h}"])
        if code:
            return code
        with open(os.path.join(out, f"renders_{w}x{h}.json"),
                  encoding="utf-8") as fh:
            rep = json.load(fh)
        report["renders"].update(rep["renders"])
        report["steps"] += rep["steps"]
    path = os.path.join(out, "renders.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(f"  renders: {json.dumps(report['renders'])}")
    print(f"  record: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
