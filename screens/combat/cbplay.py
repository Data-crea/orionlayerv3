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
  beam_shot  the original's bolt (`cbbeam`, work order 199 C2): the muzzle
             burst, the bolt frame by frame for `_max_frames` frames,
             stopped at the shield when it holds, the hit flash, and the
             damage past the shields as a rising number; at a missile or a
             fighter group when the engine says so. OMISSION
             `shield_flare`: the shield's own flare is not drawn
  missile_*  launches appear with the state after them; a hit shows its
             damage; a missile gone leaves
  destroy    CMBTSFX 3 / 4 / 5 by size at the unit's centre, the unit
             hidden from half-way (cmbtspec.cpp:1193-1276)
  retreat    CMBTSFX 42 beside the unit, which then leaves
             (cmbtdrw1.cpp:2376-2496)
  special,   the original's frames (`cbsfx`, work order 199 C2): the
  bomb,      stasis field, tractor beam, gyro, plasma web, black hole,
  blast_hit, stellar converter, a bomb's flight and impact, a blast round
  web_damage its source, the web on a unit
  others     their word over the unit, briefly (capture, raid, a reflection,
             a special without its own frames here) — DEVIATION
             `event_marks`
"""
import copy
import time

from . import cbbeam, cbdraw, cbsfx, cbshot

CELL = cbdraw.CELL
MOVE_S = 0.15
FRAME_S = 0.055
NUMBER_S = 9 * FRAME_S
BOLT_S = 6 * FRAME_S
#: The beams the colour table does not carry (beams.cpp:1124-1192):
#: weapon id (orion2_consts.h:993-1035) -> (BEAMS.LBX 0's palette fragment,
#: the bolt's length, its step a frame) — the spatial compressor, the
#: mauler, the dragon and plasma breaths, weapon 46.
FRAGMENT = {13: (2, 40, 55), 27: (5, 20, 40), 40: (5, 20, 40),
            43: (5, 20, 40), 46: (6, 40, 50)}
DEATH_SFX = {0: 3, 1: 4, 2: 4, 3: 5, 4: 5, 5: 5}
RETREAT_SFX = 42


class Player:
    def __init__(self):
        self._art = None                 # the artwork, from the first draw
        self._palettes = {}              # beam colours -> one palette dict
        self.reset()

    def reset(self):
        self._last = None
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
            self._last = ev

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
        if k in ("special", "bomb", "blast_hit", "web_damage"):
            p = cbsfx.plan(ev, self._unit, self._art, self._last)
            if p is not None:
                ev["_sfx"] = p
                u = self._unit(ev.get("unit", ev.get("target", -1)))
                hit = ev.get("past_shields") or ev.get("hits")
                if u is not None and hit:
                    self._marks.append((str(hit), *cbdraw.centre(u),
                                        now + p["frames"] * FRAME_S,
                                        (0xff, 0xcc, 0x40)))
                return p["frames"] * FRAME_S
        if k == "beam_shot":
            u = None if ev.get("at_missile") else \
                self._unit(ev.get("target", -1))
            dur = BOLT_S
            b = self._beam(ev)
            if b is not None:
                dur = (b["frames"] + 2) * FRAME_S
            if u is not None and ev["past_shields"]:
                self._marks.append((str(ev["past_shields"]),
                                    *cbdraw.centre(u), now + dur,
                                    (0xff, 0xcc, 0x40)))
            return dur
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
                 "reflect", "special"):
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
        if ev["kind"] == "beam_shot":
            return self._target_point(ev)
        u = self._unit(ev.get("target", ev.get("unit", -1)))
        return cbdraw.centre(u) if u is not None and \
            ev["kind"] != "rotate" else None

    def _beam(self, ev):
        """The shot as `cbbeam` draws it: its record, end points (world
        px), frames, where it stops — or None without both units."""
        src = self._unit(ev.get("source", -1))
        at = self._target_point(ev)
        if src is None or at is None:
            return None
        dst = None if ev.get("at_missile") else self._unit(ev["target"])
        slot = ev.get("slot", 0)
        weapons = src.get("weapons") or []
        specials = weapons[slot]["specials"] if 0 <= slot < len(weapons) \
            else 0
        f = cbbeam.fx(ev.get("weapon", 0), specials)
        cols = None
        if f is None:                   # not a "Steve stuff" weapon
            cols, length, step = FRAGMENT.get(ev.get("weapon"), (5, 20, 40))
            f = dict(cbbeam.fx(3), style=0, length=length, step=step)
        a = tuple(int(v) for v in cbdraw.centre(src))
        b = tuple(int(v) for v in at)
        n, _step = cbbeam.max_frames(a, b, f)
        holds = dst is not None and ev.get("result", 0) & 1 and \
            not ev.get("result", 0) & 2
        size = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}.get(
            int(dst["size_class"]), 1) if dst is not None else 0
        return {"fx": f, "fragment": cols, "src": a, "dst": b, "frames": n,
                "stop": size if holds else None}

    def _target_point(self, ev):
        """Where a shot goes (world px): the target unit's centre — or, when
        the engine says `at_missile` (beams at ordnance, cmbtfire.cpp:1363),
        the missile or fighter group whose INDEX `target` is."""
        if ev.get("at_missile"):
            m = next((m for m in (self.ordnance or {}).get("missiles", [])
                      if m.get("index") == ev.get("target")), None)
            return (m["x"], m["y"]) if m is not None else None
        u = self._unit(ev.get("target", -1))
        return cbdraw.centre(u) if u is not None else None

    def _draw_beam(self, surface, cam, art, ev, b, t, cache):
        cbshot.draw(surface, cam, art, ev, b, t, cache, self._palettes)

    # ── drawing ────────────────────────────────────────────────────
    def draw(self, surface, cam, art, style, scale, cache):
        now = time.monotonic()
        self._art = art
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
        elif "_sfx" in ev:
            p = ev["_sfx"]
            if p["frames"]:
                p["draw"](surface, cam, cache,
                          min(p["frames"] - 1, int(t * p["frames"])))
        elif k == "beam_shot":
            b = self._beam(ev)
            if b is not None:
                self._draw_beam(surface, cam, art, ev, b, t, cache)
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
