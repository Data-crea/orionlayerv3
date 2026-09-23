#!/usr/bin/env python3
"""Driving orion2re live through OrionLayer's own front door.

The machinery every live acceptance needs, split out of
`tools/research_hd.py` when that grew past the 300-line guideline
(decision 6) — and split at a seam rather than to satisfy a number:
what is here knows nothing about research. The next screen's driver
gets it for free.

ONE CLIENT (work order 126, rule 8). A `Run` IS the client: the real
`main.App`, headless, real pygame events. Nothing here starts a second
one, and a caller that wants to check for somebody else's must do it
before it constructs a `Run`.

WHAT IT PROVIDES

    Run            the app, the loop, `wait_for` on a SHAPE and never a
                   timer (decision 21), and `capture` — the native
                   framebuffer AND the HD window from ONE frame, plus a
                   record line for each
    SendCounter    wraps the client's three send paths and counts them
                   while the real method still runs, so a claim about
                   the WIRE is a number and not an argument
    fb_digest      "did the picture move", for a dialog that answers an
                   input without changing its field list
    hashes/close   the save-file rule: SAVE1-9 identical over the run,
                   SAVE10 logged, SAVE11 logged and identical

WHY `capture` COUNTS COLOURS. Work order 129 reported that the two
turn-start dialogs showed "the original picture" in OrionLayer's
window. Its own screenshots were a single colour and its record carried
`use_original: true` — the dispatcher's FLAG, read as the observation.
Every capture here records how many distinct colours the window holds,
so "the window is blank" cannot be written down as "the window shows
the picture".

Evidence goes OUTSIDE the tree, to `~/orionlayer-fixtures/evidence/`:
pictures of the player's game are the player's data (decision 42).
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import toolenv  # noqa: E402
toolenv.init_palette()

import main as main_module  # noqa: E402
from core.structs import player as player_spec  # noqa: E402

GAME_DIR = os.path.expanduser("~/Master of Orion 2")
EVIDENCE = os.path.expanduser("~/orionlayer-fixtures/evidence")


def hashes():
    """{name: sha256} for SAVE1..SAVE11, absent ones omitted."""
    out = {}
    for n in range(1, 12):
        path = os.path.join(GAME_DIR, f"SAVE{n}.GAM")
        if os.path.exists(path):
            with open(path, "rb") as fh:
                out[f"SAVE{n}.GAM"] = hashlib.sha256(fh.read()).hexdigest()
    return out


class SendCounter:
    """Counts the client's three send paths; the real method still runs.

    Not a mock (`colony_move_hd.Counter`'s rule): what it buys is a
    claim about THE WIRE rather than about the picture. Used here to
    settle whether a commit that nobody asked for came from this
    driver — the answer has to be a number, not an argument.

    **IT PUTS THE CLIENT BACK, and that is not tidiness.** Every
    counter WRAPS the client's three methods, so a second one wraps the
    first and a send after that increments BOTH: a counter meant to
    measure one step keeps counting every step after it. Read live on
    23 September 2026 — a record said `activate_field: 3` for a step
    whose own printed line said 0, because the dict it stored was the
    LIVE one and two later steps had gone through the same wrapper. The
    number that was true when it was printed was false when it was
    written down.

    So `release()` restores the client's own methods, `__exit__` calls
    it, and `snapshot()` returns a COPY. A step measures itself with

        with SendCounter(client) as counter:
            ...
        counts, sent = counter.snapshot()
    """

    def __init__(self, client):
        self.client = client
        self.counts = {"activate_field": 0, "inject_click": 0,
                       "inject_key": 0}
        self.sent = []
        self._real = {}
        for name in self.counts:
            self._real[name] = getattr(client, name)
            setattr(client, name, self._wrap(name, self._real[name]))

    def _wrap(self, name, real):
        def counted(*args, **kwargs):
            self.counts[name] += 1
            self.sent.append((name, args))
            return real(*args, **kwargs)
        return counted

    def release(self):
        """Put the client's own methods back. Idempotent."""
        for name, real in self._real.items():
            setattr(self.client, name, real)
        self._real = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()
        return False

    def snapshot(self):
        """`(counts, sent)`, COPIED — the numbers as they are NOW."""
        return dict(self.counts), [(n, tuple(a)) for n, a in self.sent]

    def total(self):
        return sum(self.counts.values())

    def __repr__(self):
        return ", ".join(f"{k}={v}" for k, v in sorted(self.counts.items()))


class Run:
    """One live acceptance, with its own evidence folder and record."""

    def __init__(self, name, folder="."):
        # `folder` is the work order's own directory under EVIDENCE, so
        # this module names no work order and the next one needs no
        # edit here.
        self.dir = os.path.join(EVIDENCE, folder, name)
        os.makedirs(self.dir, exist_ok=True)
        self.log = []
        self.step = 0
        self.app = main_module.App()
        if not self.app.connected:
            sys.exit("no orion2re on the wire — nothing to drive")

    # ── the loop ──────────────────────────────────────────

    def pump(self, frames=1):
        for _ in range(frames):
            self.app._handle_events()
            self.app._update()
            self.app._render()
            time.sleep(0.02)

    @property
    def state(self):
        return self.app.client.state

    def shape(self):
        st = self.state
        return (st.current_screen, len(st.fields or []))

    def wait_for(self, ready, seconds=90.0, label=""):
        """Pump until `ready(state)`. Event-driven, never timed
        (decision 21) — the deadline is a give-up, not a schedule."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.pump()
            if ready(self.state):
                return True
        print(f"  ! timed out waiting for {label}")
        return False

    def on_screen(self, screen_id, fields=None):
        def ready(st):
            if st.current_screen != screen_id:
                return False
            return fields is None or len(st.fields or []) == fields
        return ready

    # ── evidence ──────────────────────────────────────────

    def player(self):
        """The local player's parsed record, or None."""
        st = self.state
        raws = getattr(st, "player_raw", None) or []
        me = getattr(st, "player_num", 0) or 0
        if not 0 <= me < len(raws):
            return None
        return player_spec.SPEC.parse(raws[me])

    def capture(self, name):
        """Native framebuffer AND the HD window, from ONE moment.

        Both halves come from the same frame or the pair is a
        comparison of two different games (colony_move_hd's rule).
        """
        self.step += 1
        st = self.state
        tag = f"{self.step:03d}_{name}"
        native = os.path.join(self.dir, f"{tag}_native.png")
        hd = os.path.join(self.dir, f"{tag}_hd.png")
        if st.framebuffer and st.palette:
            surf = pygame.Surface((640, 480), depth=8)
            surf.set_palette([(r, g, b) for r, g, b in st.palette])
            surf.get_buffer().write(bytes(st.framebuffer[:640 * 480]))
            pygame.image.save(surf, native)
        pygame.image.save(self.app.surface, hd)
        plr = self.player()
        entry = {
            "step": self.step,
            "name": name,
            "screen": st.current_screen,
            "fields": len(st.fields or []),
            # THE SCREEN THAT IS ACTUALLY DRAWING ON TOP, which is not
            # `active_name` once a screen is an OVERLAY: the GAME menu
            # and, since work order 165 part F, change mode both leave
            # `active_name` saying "galaxy_map" while they are the
            # picture. Work order 131 part D asks this record to name
            # the HD screen that was drawing, and `active_name` stopped
            # being that answer.
            "hd_active": (self.app.dispatcher.overlay_name
                          or self.app.dispatcher.active_name),
            "hd_parent": self.app.dispatcher.active_name,
            "use_original": self.app.dispatcher.use_original,
            "showing_original": self.app._showing_original(),
            "stardate": getattr(st, "stardate", 0),
            "research_field": int(plr.current_research_field) if plr else None,
            "research_app": (int(plr.raw[902]) if plr and len(plr.raw) > 902
                             else None),
            "breakthrough": int(plr.research_breakthrough) if plr else None,
            "hd_png": os.path.basename(hd),
            "native_png": os.path.basename(native),
            "hd_distinct_colours": self.hd_colours(),
        }
        self.log.append(entry)
        print(f"  [{self.step:03d}] {name}: screen={entry['screen']} "
              f"fields={entry['fields']} hd={entry['hd_active'] or '-'} "
              f"orig={entry['showing_original']} "
              f"field={entry['research_field']} "
              f"colours={entry['hd_distinct_colours']}")
        return entry

    def hd_colours(self):
        """How many distinct colours the HD window holds.

        THE MEASUREMENT WORK ORDER 129 DID NOT MAKE. Its report said
        the fallback showed the original picture; its own screenshots
        were a single colour, 100% (6, 8, 16), and nobody looked. One
        number here makes "the window is blank" impossible to write
        down as "the window shows the picture".
        """
        surf = self.app.surface
        w, h = surf.get_size()
        seen = set()
        for y in range(0, h, 17):
            for x in range(0, w, 23):
                seen.add(surf.get_at((x, y))[:3])
                if len(seen) > 64:
                    return ">64"
        return len(seen)

    def save_record(self, extra=None):
        path = os.path.join(self.dir, "record.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"log": self.log, **(extra or {})}, fh, indent=1)
        print(f"  record: {path}")

    # ── input ─────────────────────────────────────────────

    def hd_click(self, x, y, button=1):
        """A real pygame click into OrionLayer's own window.

        The front door: `App._handle_click` decides what it means —
        the HD screen's row, or the fallback's forwarding.

        The queue is DRAINED first. A click posted while one screen is
        up and consumed after the game has moved to the next one is the
        shape of work order 128's crash, one level out, and this driver
        must not be the thing that produces it.
        """
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": button}))
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": button}))
        self.pump(3)
        pygame.event.clear()

    def hd_motion(self, x, y):
        """The pointer MOVED to a window point — a hover, not a click.

        The same front door as `hd_click`: `App` routes MOUSEMOTION to
        `dispatcher.route_motion`, which is what sets a screen's hover.
        `rel` and `buttons` are carried because the letterbox branch
        rebuilds the event out of them (main.py:192-195) and a motion
        without them raises there rather than arriving.

        NOTHING IS SENT BY A HOVER, in either mode: the research
        screen's `handle_mouse_motion` only assigns `_hover`. The
        driver still counts sends around it, because "it sends nothing"
        is a measurement and not an expectation.
        """
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEMOTION, {"pos": (x, y), "rel": (0, 0),
                                 "buttons": (0, 0, 0)}))
        self.pump(3)
        pygame.event.clear()


def fb_digest(run):
    """A digest of the game's own framebuffer, for "did anything change".

    The science room answers a click by advancing ONE discovery: the
    screen id and the field count stay exactly as they were, and only
    the picture moves (science.cpp:169-171 — the list is the dummy, one
    whole-screen field and an ESC hotkey, whatever is being shown). A
    change test on the field list alone reports "nothing happened" for
    an input that plainly did something, which is the mistake work
    order 129 made one level up.
    """
    st = run.state
    if not st.framebuffer:
        return None
    return hashlib.sha256(bytes(st.framebuffer[:640 * 480])).hexdigest()


def close(run, before):
    after = hashes()
    scratch = [f"SAVE{n}.GAM" for n in range(1, 10)]
    changed = [k for k in scratch
               if before.get(k) != after.get(k)]
    print("\nSAVE1-9 identical:" if not changed else
          f"\n!! SAVE1-9 CHANGED: {changed}")
    for k in ("SAVE10.GAM", "SAVE11.GAM"):
        same = before.get(k) == after.get(k)
        print(f"  {k}: {'unchanged' if same else 'REWRITTEN'} "
              f"({'logged only' if k == 'SAVE10.GAM' else 'must stay same'})")
    return {"saves_before": before, "saves_after": after,
            "scratch_changed": changed}
