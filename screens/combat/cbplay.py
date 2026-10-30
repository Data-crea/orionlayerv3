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
numbers 9 frames. With the game's FAST ANIMATIONS on (open fix 68's COPT,
work order 200) every effect takes the step the original takes under
`_speedx2_flag`: a move 12 px a frame instead of 2 (cmbtmov1.cpp:309-317),
a beam's bolt two frames at a time (`cbshot`), the specials' and a
destroyed unit's frames every second one (cmbtspec.cpp:99, 1226 and the
other sites), a retreat every third (cmbtdrw1.cpp:2462); a turn is not
faster (`Rotate_Ship_` has no such step).

WHAT EACH EVENT DOES here:
  move       the unit glides from its cell to the new one (a teleport jumps)
  rotate     the unit turns one facing per frame to the new facing
  beam_shot  the original's bolt (`cbbeam`, work order 199 C2): the muzzle
             burst, the bolt frame by frame for `_max_frames` frames,
             stopped at the shield when it holds, the hit flash, the
             shield's flare (`cbflare`, work order 200), and the damage
             past the shields as a rising number; at a missile or a
             fighter group when the engine says so
  missile_*  launches appear with the state after them; a hit shows its
             damage; a missile gone leaves
  destroy    CMBTSFX 3 / 4 / 5 by size at the unit's centre, the unit
             hidden from half-way (cmbtspec.cpp:1193-1276)
  retreat    the warp effect beside the unit, which slides into it
             (`cbretreat`)
  special,   the original's frames (`cbsfx`, work order 199 C2): the
  bomb,      stasis field, tractor beam, gyro, plasma web, black hole,
  blast_hit, stellar converter, a bomb's flight and impact, a blast round
  web_damage its source, the web on a unit
  reflect    the beam sent back and the reflection field's flare
             (`cbreflect`, work order 200), after its shot's slot
  others     their word over the unit, briefly (capture, raid, a special
             without its own frames here) — DEVIATION `event_marks`
"""
import copy
import random
import time

from . import (cbbeam, cbcloak, cbdraw, cbflare, cbflight, cblightning,
               cbnumbers, cbpace, cbqueue, cbreflect, cbretreat, cbsfx,
               cbshot, cbsound, cbstart)

CELL = cbdraw.CELL
MOVE_S = cbpace.MOVE_S
UNTIMED_S = cbpace.UNTIMED_S
FRAME_S = cbpace.FRAME_S
NUMBER_S = cbpace.NUMBER_S
BOLT_S = cbpace.BOLT_S
FRAGMENT = cbpace.FRAGMENT
DEATH_SFX = cbpace.DEATH_SFX
sfx_times = cbpace.sfx_times
sfx_frame = cbpace.sfx_frame


class Player:
    def __init__(self):
        self._art = None                 # the artwork, from the first draw
        self.fast = False                # the game's FAST ANIMATIONS (COPT)
        self.colours, self.planet = {}, None   # for a flared target's picture
        self._palettes = {}              # beam colours -> one palette dict
        self.sounds = cbsound.Sounds()   # the battle's sounds (open fix 79)
        self.reset()

    def reset(self):
        self._last = None
        self.shown = None        # the battle as HD shows it
        self.ordnance = None
        self._queue = []         # [event, ...] still to play
        self._after = []         # [(last seq, combat, ordnance)]
        self._anim = None        # (event, start time, duration)
        self._marks = []         # floating words: (text, wx, wy, t0, rgb)
        self._numbers, self._num_cache = [], {}   # `cbnumbers` (265)
        self._next_seq = None
        self._last_queued = None
        self._played = -1
        self._lightning_frame = 0   # CMBTSFX 0's own frame (work order 210)
        self.last_beam = None    # the shot a reflection sends back
        self._fed = None         # the last snapshot's battle fed
        self._fed_ordnance = None   # and its ordnance (`_with_flight`)
        self._aims_seen = False     # the engine sends open fix 82's aims
        self._head = None           # the last batch's last event (305)
        self.sounds.reset()

    def busy(self):
        return bool(self._queue) or self._anim is not None

    def feed(self, combat, events, ordnance):
        """One snapshot: its events (new ones only) and the state after.

        Each snapshot's state waits for the last event queued so far —
        its own, or an earlier snapshot's when it brings none — and is
        shown once that event has played.

        `combat` None: the battle has ended and these are its LAST events
        (they arrive with the first snapshot after it, open fix 56) —
        queued like any others, with no state after them: what they leave
        is the last picture (work order 202 D)."""
        if combat is not None and events and self._next_seq is not None \
                and events[-1] is not self._head and \
                events[-1]["seq"] < self._next_seq:
            # HD STATE `engine_restart`: the engine numbers its events once,
            # from 1 (open fix 56) — a new batch wholly below the last one
            # is a new engine's: started afresh, not filtered away
            self.reset()
        self._head = events[-1] if events else self._head
        new = [e for e in events
               if self._next_seq is None or e["seq"] >= self._next_seq]
        if new:
            self._next_seq = new[-1]["seq"] + 1
        if any(e["kind"] == "beam_aim" for e in new):
            self._aims_seen = True
        fresh = combat is not None and combat is not self._fed
        if fresh:
            self._fed = combat
        if self.shown is None:
            if combat is not None:
                self.shown, self.ordnance = copy.deepcopy(combat), ordnance
                self._fed_ordnance = ordnance
            return
        playable = self._with_lightning(
            [e for e in new if e["kind"] != "command"], combat)
        if (combat or self._fed or {}).get("super_fast"):
            for e in playable:      # TRANSCRIPTION `super_fast` (`_advance`)
                e["_super_fast"] = True
        if fresh:
            playable = self._with_flight(playable, ordnance)
            self._fed_ordnance = ordnance
        self._queue.extend(playable)
        if playable:
            self._last_queued = playable[-1]["seq"]
        # a snapshot is copied once, when it comes (work order 305): the
        # screen feeds the same one every frame
        if fresh and not self.busy():
            self.shown, self.ordnance = copy.deepcopy(combat), ordnance
            self._after = []
        elif fresh:
            self._after.append((self._last_queued, copy.deepcopy(combat),
                                ordnance))

    def _with_flight(self, events, ordnance):
        """TRANSCRIPTION `flight` and `launch_flight` (`cbflight.place`,
        work order 212 E): this snapshot's flights among its events."""
        return cbflight.place(events, self._fed_ordnance, ordnance,
                              self._unit, self.fast,
                              max(self._last_queued or 0, self._played))

    def _with_lightning(self, events, combat=None):
        """HD STATE `lightning_inferred` (work orders 210 C3, 305): no
        event names the Lightning Field (proposed open fix 76); HD puts its
        frames where the original draws them, before the point defence of
        each missile hit or fighter pass at a unit carrying a working one,
        and before a stack the field emptied ends (`cblightning`)."""
        return cblightning.place(
            events, self._unit, cblightning.targets_of(self._fed_ordnance),
            [c["units"] for c in (self.shown, combat) if c])

    # ── the clock ──────────────────────────────────────────────────
    def tick(self, now=None):
        """Advance the playback and its sounds to `now`. Called from the
        screen's `update` as well as from `draw`, so the battle's own clock
        runs while the player looks at the original (F12) and nothing waits
        for a frame to be drawn (decision 78: one clock)."""
        now = time.monotonic() if now is None else now
        self._advance(now)
        self.sounds.tick(now)
        if self._anim is not None and self._anim[0]["kind"] == "flight":
            ev, t0, dur = self._anim
            f = ev["_flight"]
            self.ordnance = cbflight.at(f, ev["_base"], int(
                (now - t0) / UNTIMED_S))

    def _advance(self, now):
        while True:
            if self._anim is not None:
                ev, t0, dur = self._anim
                self._attach(ev, t0, dur, now)
                if now - t0 < dur:
                    return
                self._finish(ev)
                self._anim = None
                self._played = max(ev["seq"], ev.get("_tail", ev["seq"]))
                self._adopt()
            if not self._queue:
                return
            cbqueue.lead_reflects(self._queue)
            if self._queue[0]["kind"] == "beam_shot" and \
                    not self._aims_ready(now):
                return
            ev = self._queue.pop(0)
            if ev["kind"] in cbsound.KINDS or ev["kind"] == cbqueue.CHARGE:
                # a sound with no animation of HD's before it — a field's
                # click, an engine noise that starts before its move is
                # recorded (cmbtmov1.cpp) — or a charge (open fix 94): now
                if ev["kind"] == cbqueue.CHARGE:
                    self._charge(ev)
                else:
                    self.sounds.at(now, ev)
                self._played = max(self._played, ev["seq"])
                self._adopt()
                continue
            n, m = len(self._numbers), len(self._marks)
            dur = self._start(ev, now)
            if ev.get("_super_fast"):
                # TRANSCRIPTION `super_fast`: under Z (CMBT's flag, set by
                # its key and cleared with AUTO, v2 combat1.cpp:624-633,
                # :693-695) the original draws no move, turn, shot, effect,
                # death or retreat (each behind `super_fast_flag == 0`, v2
                # cmbtmov1.cpp:320, :412; cmbtfire.cpp:402, :1565;
                # cmbtspec.cpp:1741; combat1.cpp:2103): played, not shown
                del self._numbers[n:], self._marks[m:]
                dur = 0.0
            self._anim = (ev, now, dur)
            self._last = ev

    def _attach(self, ev, t0, dur, now=None):
        """The sounds the engine recorded after `ev` and before its next
        event: started at their ticks into HD's animation of `ev`
        (`cbsound.offset`), whether they came with it or with a snapshot
        sent during its animation (the shield flare polls, beams.cpp:705)."""
        if ev.get("_charges") and (time.monotonic() if now is None else
                                   now) - t0 >= ev["_sfx"]["_number_at"]:
            for c in ev.pop("_charges"):    # the converter's, its frames done
                self._charge(c)
        while self._queue and (self._queue[0]["kind"] in cbsound.KINDS or
                               self._queue[0]["kind"] in cbqueue.INSTANT):
            # an event with nothing to draw (a missile gone, merged or
            # launched, recorded between a hit and its sound, cmbtmis.cpp)
            # does not take the sounds after it away from the picture
            s = self._queue.pop(0)
            if s["kind"] in cbsound.KINDS:
                self.sounds.at(t0 + cbsound.offset(ev, s, dur), s)
            ev["_tail"] = s["seq"]

    def _adopt(self):
        """Show the newest state whose events have all been played."""
        done = None
        while self._after and (self._after[0][0] is None or
                               self._after[0][0] <= self._played):
            done = self._after.pop(0)
        if done is not None:
            self.shown, self.ordnance = done[1], done[2]

    @property
    def reflection_frames(self):
        return self._art.frame_count("beams", 0x59) if self._art else 4

    def unit(self, i):
        return self._unit(i)

    def _charge(self, ev):
        """The Energy Absorber's charge on the shown unit (open fix 94)."""
        u = self._unit(ev.get("unit", -1))
        if u is not None:
            u["reflected_damage_pool"] = ev.get("pool", 0)

    def _unit(self, i):
        units = self.shown["units"] if self.shown else []
        return units[i] if 0 <= i < len(units) else None

    def _start(self, ev, now):
        k = ev["kind"]
        ev["_step"] = 2 if self.fast else 1
        if k == "move":
            if ev.get("teleport"):
                # `Draw_Teleporting_Ship_`: ten frames, five under FAST
                # (`cbcloak.vanish`, work order 210 C4), its loop without a
                # wait (DEVIATION `untimed_pace`, decision 80)
                ev["_noise"] = random.randrange(0, 256, 2)
                return UNTIMED_S * (10 // ev["_step"])
            ev["_to_px"] = cbqueue.death_on_move(self._queue, ev, CELL)
            end = _move_end(ev)
            cells = max(abs(end[0] - ev["from_x"] * CELL),
                        abs(end[1] - ev["from_y"] * CELL), CELL) / CELL
            return MOVE_S * cells / (6 if self.fast else 1)
        if k == "rotate":
            return FRAME_S * max(1, _turn(ev)[0])
        if k in ("special", "bomb", "blast_hit", "web_damage"):
            length = cbstart.effect(self, ev, now, k)
            if length is not None:
                return length
        if k == "beam_shot":
            return cbstart.beam_shot(self, ev, now)
        if k == "flight":
            ev["_base"] = copy.deepcopy(self.ordnance)
            return ev["_flight"]["frames"] * UNTIMED_S
        if k == "fighter_pass" and self._queue and \
                self._queue[0]["kind"] == "fighter_beam" and \
                self._queue[0].get("missile") == ev.get("missile"):
            # its beams and its number are the beam event's (open fix 77)
            self._queue[0]["_pass"] = ev
            return 0.0
        if k == "fighter_beam":
            p = ev["_beams"] = cbflight.beams_plan(ev)
            pas = ev.get("_pass") or {}
            u = self._unit(pas.get("target", -1)) \
                if not pas.get("at_missile") else None
            if u is not None:
                self._number(u, pas.get("past_shields"), pas.get("absorbed"),
                             now + p["frames"] * FRAME_S)
            # the numbers are waited for only when the pass did damage
            # (`Add_Damage_Indicator_For_Ship_` queues no zero, cmbtmis.cpp:
            # 946-967; measured: 3 ticks for a pass that hit nothing)
            if not (pas.get("past_shields") or pas.get("absorbed")):
                p["numbers"] = 0
            return (p["frames"] + p["numbers"]) * FRAME_S
        if k in ("missile_hit", "fighter_pass"):
            u = self._unit(ev.get("target", -1))
            if u is not None:
                self._number(u, ev.get("past_shields"), ev.get("absorbed"),
                             now)
            if k == "missile_hit" and u is not None and ev.get("target") and \
                    ev.get("absorbed", 0) > 0 and not ev.get("anti_missile"):
                m = next((m for m in (self.ordnance or {}).get("missiles", [])
                          if m.get("index") == ev.get("missile")), None)
                at = cbdraw.centre(u)
                b = ev["_beam"] = cbshot.plan_once(
                    u, cbflare.SHIP_SIZE.get(int(u["size_class"]), 1), at,
                    (m["x"], m["y"]) if m else at)
                return len(b["ticks"]) * FRAME_S
            return 3 * FRAME_S
        if k == "lightning":
            # TRANSCRIPTION `lightning` (`Lightning_Field_`,
            # cmbtspec.cpp:216-271): CMBTSFX 0 at the unit's centre less 36,
            # 15 ticks, its frames running on from the last field's
            # (`animate::Draw_` advances the picture's own frame)
            ev["_from"] = self._lightning_frame
            self._lightning_frame += 15
            return 15 * FRAME_S
        if k == "destroy":
            return cbstart.destroy(self, ev)
        if k == "retreat":
            u = self._unit(ev.get("unit", -1))
            p = ev["_retreat"] = None if int(ev.get("status", 0) or 0) or \
                u is None or self.shown is None else cbretreat.plan(
                    u, u["owner"] == self.shown.get("attacker"), self._art,
                    self.colours, self.fast)
            return cbretreat.length(p) * FRAME_S
        if k == "reflect":
            b = ev["_beam"] = cbreflect.plan(self, ev)
            u = self._unit(ev.get("shooter", -1))
            if b is not None:
                if u is not None:
                    self._number(u, ev.get("past_shields"),
                                 ev.get("absorbed"),
                                 now + len(b["ticks"]) * FRAME_S / 2)
                return len(b["ticks"]) * FRAME_S
        if k in ("capture", "raid", "blast_hit", "web_damage", "bomb",
                 "special"):
            u = None if ev.get("at_missile") else self._unit(ev.get(
                "defender", ev.get("target", ev.get("unit", -1))))
            if u is not None:
                self._marks.append((k.replace("_", " "), *cbdraw.centre(u),
                                    now, (0xe0, 0xe0, 0xff)))
            return 6 * FRAME_S
        return 0.0

    def _finish(self, ev):
        """The event's lasting effect on the shown battle."""
        k = ev["kind"]
        for c in ev.pop("_charges", ()):    # never lost (work order 260)
            self._charge(c)
        if k == "flight":
            self.ordnance = cbflight.at(ev["_flight"], ev["_base"],
                                        ev["_flight"]["frames"])
        done = ev.get("_sfx", {}).get("finish") if isinstance(
            ev.get("_sfx"), dict) else None
        if done is not None:
            done()
        if k == "move":
            u = self._unit(ev["unit"])
            if u is not None:
                # TRANSCRIPTION `move_until_death`: where it died
                end = ev.get("_to_px")
                u["x"], u["y"] = (end[0] / CELL, end[1] / CELL) if end else \
                    (ev["to_x"], ev["to_y"])
                u.pop("_off", None)
                u.pop("_hidden", None)
        elif k == "rotate":
            u = self._unit(ev["unit"])
            if u is not None:
                u["facing_dir"] = ev["to_facing"]
        elif k in ("destroy", "retreat"):
            u = self._unit(ev["unit"])
            if u is not None:
                u["unit_status"] = 5
                u.pop("_hidden", None)
        elif k == "special":
            # what a special leaves on its target, held from the moment its
            # frames end until the state after it is shown (work order 210
            # C2): the field each writes (cmbtfire.cpp:1907-1910, 1976-1977;
            # cmbtspec.cpp:681, :1162)
            src, dst = self._unit(ev.get("source", -1)), \
                self._unit(ev.get("target", -1))
            w = int(ev.get("weapon", 0))
            if dst is None or src is None or ev.get("at_missile"):
                return
            if w == cbsfx.STASIS:
                dst["stasis_source_idx"] = ev["source"]
            elif w == cbsfx.BLACK_HOLE:
                dst["black_hole_flag"] = 1
                dst["black_hole_source_idx"] = ev["source"]
            elif w == cbsfx.TRACTOR:
                src["special_cooldown"] = ev["target"]
            elif w in cbsfx.WEBS and not dst.get("plasma_web_damage"):
                dst["plasma_web_damage"] = 1

    def dont_draw(self):
        """The unit the event being played draws itself — a move, a turn,
        a teleport — or None. The original keeps that unit out of the
        field it redraws (`_dont_draw_ship`, set by `Rotate_Ship_` and the
        move, cmbtmov1.cpp:84-85, :321; the teleport, :836), and with it
        the acting unit's cursor (cmbtdrw1.cpp:815): work order 222,
        TRANSCRIPTION `cursor_hidden`."""
        if self._anim is None:
            return None
        ev = self._anim[0]
        return ev.get("unit") if ev["kind"] in ("move", "rotate",
                                                "retreat") else None

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

    def _beam(self, ev, aim=None):
        """The shot as `cbbeam` draws it: its record, end points (world
        px), frames, where it stops — or None without both units. With the
        entry's `beam_aim` (open fix 82) its end points are the original's
        own: the entry's last fire point and the target point with the miss
        offset (beams.cpp:1381-1459), so its frame count is too (the count
        halves its step past six frames, :2287-2301, and a few pixels
        decide it); without one, the units' centres."""
        src = self._unit(ev.get("source", -1))
        at = self._target_point(ev)
        if src is None or at is None:
            return None
        dst = None if ev.get("at_missile") else self._unit(ev["target"])
        slot = ev.get("slot", 0)
        weapons = src.get("weapons") or []
        specials = weapons[slot]["specials"] if 0 <= slot < len(weapons) \
            else int(ev.get("specials", 0) or 0)
        f = cbbeam.fx(ev.get("weapon", 0), specials)
        total = self._art.frame_count("beams", 67) if self._art else 0
        cols = None
        if f is None:                   # not a "Steve stuff" weapon
            cols, length, step = FRAGMENT.get(ev.get("weapon"), (5, 20, 40))
            f = dict(cbbeam.fx(3), style=0, length=length, step=step)
        if aim is not None:
            a = (int(aim["from_x"]), int(aim["from_y"]))
            b = (int(aim["to_x"]), int(aim["to_y"]))
        else:
            a = tuple(int(v) for v in cbdraw.centre(src))
            b = tuple(int(v) for v in at)
        n, _step = cbbeam.max_frames(a, b, f)
        holds = dst is not None and ev.get("result", 0) & 1 and \
            not ev.get("result", 0) & 2
        size = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3}.get(
            int(dst["size_class"]), 1) if dst is not None else 0
        w = int(ev.get("weapon", 0) or 0)
        # every shooter but a fighter (`attacker_size_class` -1, beams.cpp:
        # 1243), and a fighter's beams are not shots here (`cbflight`)
        multi = w in cbshot.MULTI_BEAM
        return {"fx": f, "fragment": cols, "src": a, "dst": b, "frames": n,
                "stop": size if holds else None, "specials": specials,
                "total": total or 10, "multi": 3 if multi else 1,
                "variant": cbshot.MULTI_BEAM.get(w, 0) if multi else 0,
                "ball": multi and cbshot.MULTI_BEAM[w] == 0}

    def _aims_ready(self, now):
        return cbqueue.aims_ready(self._queue, self._aims_seen, now)

    def _take_spin(self, ev):
        cbqueue.take_spin(self._queue, ev)

    def _take_aims(self, ev):
        return ev.pop("_aims") if "_aims" in ev else \
            cbqueue.take_aims(self._queue, ev)

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
        cbshot.draw(surface, cam, art, ev, cbshot.ramps(self, b), t, cache,
                    self._palettes,
                    cbshot.look(self, ev, art) if b.get("flare") else None)

    # ── drawing ────────────────────────────────────────────────────
    def draw(self, surface, cam, art, style, scale, cache):
        now = time.monotonic()
        self._art = art
        self.tick(now)
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
        self._numbers = cbnumbers.draw(
            surface, cam, style, self._numbers, now, FRAME_S,
            art.palette_with() if art is not None else None, self._num_cache)

    def _number(self, u, total, hull, t0, side=1):
        """Queue a hit's two damage numbers (`cbnumbers`, work order 265)."""
        m = cbnumbers.mark(cbdraw.centre(u), u["size_class"], total, hull,
                           t0, side)
        if m is not None:
            self._numbers.append(m)

    def _draw_event(self, surface, cam, art, ev, t, cache):
        k = ev["kind"]
        if k == "move" and not ev.get("teleport"):
            u = self._unit(ev["unit"])
            if u is not None:
                u["x"], u["y"] = ev["from_x"], ev["from_y"]
                end = _move_end(ev)
                u["_off"] = ((end[0] - ev["from_x"] * CELL) * t,
                             (end[1] - ev["from_y"] * CELL) * t)
        elif k == "move":
            # TRANSCRIPTION `teleport` (`cbcloak`): out where it was, in
            # where it goes, in the same frames
            u = self._unit(ev["unit"])
            if u is None:
                return
            u["_hidden"] = True
            step = ev.get("_step", 1)
            k_ = min(10 // step - 1, int(t * (10 // step)))
            out_pct, in_pct = 10 * step * k_, 100 - 10 * step * k_
            for (cx, cy), pct in (((ev["from_x"], ev["from_y"]), out_pct),
                                  ((ev["to_x"], ev["to_y"]), in_pct)):
                pic = cbcloak.vanished(art, self.colours, u, pct,
                                       ev.get("_noise", 0))
                if pic is not None:
                    at = cbdraw.sprite_origin(dict(u, x=cx, y=cy))
                    surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                                 cam.to_window(*at))
        elif k == "rotate":
            u = self._unit(ev["unit"])
            if u is not None:
                steps, sign = _turn(ev)
                u["facing_dir"] = (ev["from_facing"] +
                                   sign * int(steps * t)) & 15
        elif "_sfx" in ev:
            p = ev["_sfx"]
            frame = sfx_frame(p, t)
            if frame is not None:
                p["draw"](surface, cam, cache, frame)
        elif k == "fighter_beam" and "_beams" in ev:
            p = ev["_beams"]
            frame = int(t * (p["frames"] + p["numbers"]))
            if frame < p["frames"]:
                cbflight.draw_beams(surface, cam, art, ev, p, frame, cache,
                                    self._palettes)
        elif k == "beam_shot" and "_firing" in ev:
            f = ev["_firing"]
            cbshot.ramps(self, f["b"])
            cbshot.draw_firing(surface, cam, art, f, t, cache, self._palettes,
                               cbshot.look(self, ev, art)
                               if "flare_size" in f["b"] else None)
        elif k in ("missile_hit", "reflect"):
            b = ev.get("_beam")
            if b is not None:
                self._draw_beam(surface, cam, art, ev, b, t, cache)
        elif k == "lightning":
            u = self._unit(ev["unit"])
            n = max(1, art.frame_count("cmbtsfx", 0))
            pic = art.surface("cmbtsfx", 0, (ev["_from"] + min(14, int(
                15 * t))) % n)
            if u is not None and pic is not None:
                cx, cy = cbdraw.centre(u)
                surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                             cam.to_window(cx - 36, cy - 36))
        elif k == "destroy" and "_death" in ev:
            # TRANSCRIPTION `death_picture` (`cbblast`): frames 0..n-1 at
            # the centre plus the size's offset, the unit gone from n / 2
            u = self._unit(ev["unit"])
            if u is None:
                return
            entry, n, (ox, oy) = ev["_death"]
            frame = sfx_frame(ev["_dp"], t)
            if frame is None:
                return
            if frame >= n // 2:
                u["unit_status"] = 5
            pic = art.surface("cmbtsfx", entry, frame)
            if pic is not None:
                cx, cy = cbdraw.centre(u)
                surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                             cam.to_window(cx + ox, cy + oy))
        elif k == "retreat":
            u = self._unit(ev["unit"])
            if u is not None and ev.get("_retreat"):
                u["_hidden"] = True       # `Draw_Retreating_Ship` draws it
                cbretreat.draw(surface, cam, art, self.colours, u,
                               ev["_retreat"], t, cache, cbdraw.glow_frame(
                                   u, ev["unit"], int(time.monotonic() /
                                                      FRAME_S)))
        elif k == "destroy":
            u = self._unit(ev["unit"])
            if u is None:
                return
            entry = DEATH_SFX.get(int(u["size_class"]), 4)
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


def _move_end(ev):
    """Where a move's glide ends (world px): its cell, or where the unit
    died on the way (`cbqueue.death_on_move`)."""
    return ev.get("_to_px") or (ev["to_x"] * CELL, ev["to_y"] * CELL)


def _turn_steps(a, b):
    d = (int(b) - int(a)) & 15
    return min(d, 16 - d)


def _turn(ev):
    """(facings, direction) of a turn. TRANSCRIPTION `turn_step`
    (`Rotate_Ship`, cmbtmov1.cpp:77-82; v2 :74-79): the direction is the
    event's own step (CEV_ROTATE, v2 cmbtmov1.cpp:85), else the original's
    from diff = current - target: below 0, -1 past -8 and +1 else; from 0
    up, +1 past 8 and -1 else — so a half turn (diff +-8) goes against the
    diff's sign; one facing a frame until it faces the target."""
    a, b = int(ev["from_facing"]), int(ev["to_facing"])
    step = int(ev.get("step", 0) or 0)
    if step not in (1, -1):
        diff = a - b
        step = (-1 if abs(diff) > 8 else 1) if diff < 0 else \
            (1 if diff > 8 else -1)
    return ((b - a) * step) & 15, step
