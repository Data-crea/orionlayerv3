"""Playing the battle's events before showing their result — work order 197 C.

DATA'S CONDITION (30 September 2026): the engine may run ahead of HD, but HD
shows no result and takes no input before the animation that belongs to it.
Open fix 56 gives every event, numbered, and every snapshot's state is the
battle AFTER its events; so each snapshot's events are queued with that
state, HD shows the battle as the events it has already played left it, and
adopts the engine's state only when the queue is empty (`busy` holds the
screen's input meanwhile).

THE PACE is the original's, TRANSCRIPTION `pace`
(`dev:doc/combat_drawing_reading.md` §8): a move
is 10 frames a cell with no timer (HD: 0.15 s a cell), a turn one facing per
55 ms frame, an effect one frame per 55 ms (`Release_Time_(1)`), damage
numbers 9 frames.

WHAT EACH EVENT DOES here:
  move       the unit glides from its cell to the new one (a teleport jumps)
  rotate     the unit turns one facing per frame to the new facing
  beam_shot  a bolt from the shooter to the target in the weapon's two
             colours (`Set_Beam_Colors_`, beams.cpp:1848-2062) and the damage
             past the shields as a rising number — DEVIATION
             `beam_simplified`: a straight two-colour bolt, not the
             original's jittered bolt code (193's option (a), Data's
             decision taken by work order 197)
  special    the same bolt in the special's colour
  missile_*  launches appear with the state after them; a hit shows its
             damage; a missile gone leaves
  destroy    CMBTSFX 3 / 4 / 5 by size at the unit's centre, the unit
             hidden from half-way (cmbtspec.cpp:1193-1276)
  retreat    CMBTSFX 42 beside the unit, which then leaves
             (cmbtdrw1.cpp:2376-2496)
  others     their number over the unit, briefly (capture, raid, blast,
             web damage) — DEVIATION `event_marks`
"""
import copy
import time

import pygame

from . import cbdraw

CELL = cbdraw.CELL
MOVE_S = 0.15
FRAME_S = 0.055
NUMBER_S = 9 * FRAME_S
BOLT_S = 6 * FRAME_S
#: (c1, c2) per weapon id — `Set_Beam_Colors_`' table (beams.cpp:1848-2062).
BEAM_COLOURS = {
    1: ((0x59, 0x6b, 0xc3), (0xda, 0xfc, 0xff)),
    2: ((0x59, 0x67, 0x6c), (0xb2, 0xc8, 0xc8)),
    3: ((0xc8, 0x14, 0x20), (0xff, 0x50, 0x0a)),
    4: ((0x5e, 0x70, 0xcd), (0xba, 0xdd, 0xff)),
    5: ((0xd2, 0x46, 0x00), (0xff, 0xa2, 0x00)),
    6: ((0x94, 0x9b, 0x49), (0xfe, 0xfe, 0x94)),
    7: ((0x44, 0x98, 0x8f), (0x93, 0xff, 0xff)),
    8: ((0x92, 0x53, 0xba), (0xff, 0xb8, 0xff)),
    9: ((0xa9, 0x2b, 0x00), (0xff, 0xa6, 0x60)),
    41: ((0xa9, 0x2b, 0x00), (0xff, 0xa6, 0x60)),
    10: ((0x6b, 0xa2, 0x16), (0xf2, 0xff, 0x35)),
    11: ((0xc9, 0x53, 0xc4), (0xff, 0xb8, 0xff)),
    42: ((0xc9, 0x53, 0xc4), (0xff, 0xb8, 0xff)),
    12: ((0xd2, 0x53, 0x00), (0xff, 0xff, 0x52)),
}
OTHER_BEAM = ((0x70, 0x90, 0xff), (0xe0, 0xf0, 0xff))
DEATH_SFX = {0: 3, 1: 4, 2: 4, 3: 5, 4: 5, 5: 5}
RETREAT_SFX = 42


class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.shown = None        # the battle as HD shows it
        self.ordnance = None
        self._queue = []         # [event, ...] still to play
        self._after = []         # [(last seq, combat, ordnance)]
        self._anim = None        # (event, start time, duration)
        self._marks = []         # floating numbers: (text, wx, wy, t0, rgb)
        self._next_seq = None
        self._last_queued = None
        self._played = -1

    def busy(self):
        return bool(self._queue) or self._anim is not None

    def feed(self, combat, events, ordnance):
        """One snapshot: its events (new ones only) and the state after.

        Each snapshot's state waits for the last event queued so far —
        its own, or an earlier snapshot's when it brings none — and is
        shown once that event has played."""
        new = [e for e in events
               if self._next_seq is None or e["seq"] >= self._next_seq]
        if new:
            self._next_seq = new[-1]["seq"] + 1
        if self.shown is None:
            self.shown = copy.deepcopy(combat)
            self.ordnance = ordnance
            return
        playable = [e for e in new if e["kind"] != "command"]
        self._queue.extend(playable)
        if playable:
            self._last_queued = playable[-1]["seq"]
        if not self.busy():
            self.shown, self.ordnance = copy.deepcopy(combat), ordnance
            self._after = []
        else:
            self._after.append((self._last_queued, copy.deepcopy(combat),
                                ordnance))

    # ── the clock ──────────────────────────────────────────────────
    def _advance(self, now):
        while True:
            if self._anim is not None:
                ev, t0, dur = self._anim
                if now - t0 < dur:
                    return
                self._finish(ev)
                self._anim = None
                self._played = ev["seq"]
                self._adopt()
            if not self._queue:
                return
            ev = self._queue.pop(0)
            self._anim = (ev, now, self._start(ev, now))

    def _adopt(self):
        """Show the newest state whose events have all been played."""
        done = None
        while self._after and (self._after[0][0] is None or
                               self._after[0][0] <= self._played):
            done = self._after.pop(0)
        if done is not None:
            self.shown, self.ordnance = done[1], done[2]

    def _unit(self, i):
        units = self.shown["units"] if self.shown else []
        return units[i] if 0 <= i < len(units) else None

    def _start(self, ev, now):
        k = ev["kind"]
        if k == "move":
            if ev.get("teleport"):
                return FRAME_S
            cells = max(abs(ev["to_x"] - ev["from_x"]),
                        abs(ev["to_y"] - ev["from_y"]), 1)
            return MOVE_S * cells
        if k == "rotate":
            return FRAME_S * max(1, _turn_steps(ev["from_facing"],
                                                ev["to_facing"]))
        if k in ("beam_shot", "special"):
            u = self._unit(ev.get("target", -1))
            if u is not None and k == "beam_shot" and ev["past_shields"]:
                self._marks.append((str(ev["past_shields"]),
                                    *cbdraw.centre(u), now + BOLT_S,
                                    (0xff, 0xcc, 0x40)))
            return BOLT_S
        if k in ("missile_hit", "fighter_pass"):
            u = self._unit(ev.get("target", -1))
            if u is not None and ev.get("past_shields"):
                self._marks.append((str(ev["past_shields"]),
                                    *cbdraw.centre(u), now,
                                    (0xff, 0xcc, 0x40)))
            return 3 * FRAME_S
        if k == "destroy":
            return 18 * FRAME_S
        if k == "retreat":
            return 12 * FRAME_S
        if k in ("capture", "raid", "blast_hit", "web_damage", "bomb",
                 "reflect"):
            u = self._unit(ev.get("defender", ev.get("target",
                                                     ev.get("unit", -1))))
            if u is not None:
                self._marks.append((k.replace("_", " "), *cbdraw.centre(u),
                                    now, (0xe0, 0xe0, 0xff)))
            return 6 * FRAME_S
        return 0.0

    def _finish(self, ev):
        """The event's lasting effect on the shown battle."""
        k = ev["kind"]
        if k == "move":
            u = self._unit(ev["unit"])
            if u is not None:
                u["x"], u["y"] = ev["to_x"], ev["to_y"]
                u.pop("_off", None)
        elif k == "rotate":
            u = self._unit(ev["unit"])
            if u is not None:
                u["facing_dir"] = ev["to_facing"]
        elif k in ("destroy", "retreat"):
            u = self._unit(ev["unit"])
            if u is not None:
                u["unit_status"] = 5

    def focus(self):
        """The world point the event being played happens at (a move's
        cell, a shot's target), or None."""
        if self._anim is None:
            return None
        ev = self._anim[0]
        if ev["kind"] == "move":
            return ((ev["to_x"] + 0.5) * CELL, (ev["to_y"] + 0.5) * CELL)
        u = self._unit(ev.get("target", ev.get("unit", -1)))
        return cbdraw.centre(u) if u is not None and \
            ev["kind"] != "rotate" else None

    # ── drawing ────────────────────────────────────────────────────
    def draw(self, surface, cam, art, style, scale, cache):
        now = time.monotonic()
        self._advance(now)
        if self._anim is not None:
            ev, t0, dur = self._anim
            t = min(1.0, (now - t0) / dur) if dur else 1.0
            self._draw_event(surface, cam, art, ev, t, cache)
        keep = []
        for text, wx, wy, t0, rgb in self._marks:
            age = now - t0
            if age < 0:
                keep.append((text, wx, wy, t0, rgb))
                continue
            if age > NUMBER_S:
                continue
            keep.append((text, wx, wy, t0, rgb))
            rise = age / FRAME_S          # 1 px a frame, the original's
            x, y = cam.to_window(wx, wy - 8 - rise)
            size = max(10, int(20 * scale))
            img = style.render_text(text, size, rgb)
            surface.blit(img, (x - img.get_width() // 2, y))
        self._marks = keep

    def _draw_event(self, surface, cam, art, ev, t, cache):
        k = ev["kind"]
        if k == "move" and not ev.get("teleport"):
            u = self._unit(ev["unit"])
            if u is not None:
                u["x"], u["y"] = ev["from_x"], ev["from_y"]
                u["_off"] = ((ev["to_x"] - ev["from_x"]) * CELL * t,
                             (ev["to_y"] - ev["from_y"]) * CELL * t)
        elif k == "rotate":
            u = self._unit(ev["unit"])
            if u is not None:
                steps = _turn_steps(ev["from_facing"], ev["to_facing"])
                sign = _turn_sign(ev["from_facing"], ev["to_facing"])
                u["facing_dir"] = (ev["from_facing"] +
                                   sign * int(steps * t)) & 15
        elif k in ("beam_shot", "special"):
            src, dst = self._unit(ev["source"]), self._unit(ev["target"])
            if src is None or dst is None:
                return
            c1, c2 = BEAM_COLOURS.get(ev.get("weapon"), OTHER_BEAM)
            a = cam.to_window(*cbdraw.centre(src))
            b = cam.to_window(*cbdraw.centre(dst))
            head = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            width = max(1, int(3 * cam.scale))
            pygame.draw.line(surface, c1, a, head, width + 2)
            pygame.draw.line(surface, c2, a, head, width)
        elif k in ("destroy", "retreat"):
            u = self._unit(ev["unit"])
            if u is None:
                return
            entry = RETREAT_SFX if k == "retreat" else \
                DEATH_SFX.get(int(u["size_class"]), 4)
            n = max(1, art.frame_count("cmbtsfx", entry))
            pic = art.surface("cmbtsfx", entry, min(n - 1, int(n * t)))
            if pic is not None:
                cx, cy = cbdraw.centre(u)
                img = cbdraw.scaled(pic, cam.scale, cache)
                x, y = cam.to_window(cx, cy)
                surface.blit(img, (x - img.get_width() // 2,
                                   y - img.get_height() // 2))
            if t > 0.5:
                u["unit_status"] = 5


def _turn_steps(a, b):
    d = (int(b) - int(a)) & 15
    return min(d, 16 - d)


def _turn_sign(a, b):
    d = (int(b) - int(a)) & 15
    return 1 if d <= 8 else -1
