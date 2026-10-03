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
  retreat    CMBTSFX 42 beside the unit, which then leaves
             (cmbtdrw1.cpp:2376-2496)
  special,   the original's frames (`cbsfx`, work order 199 C2): the
  bomb,      stasis field, tractor beam, gyro, plasma web, black hole,
  blast_hit, stellar converter, a bomb's flight and impact, a blast round
  web_damage its source, the web on a unit
  reflect    the beam sent back and the reflection field's flare
             (`cbreflect`, work order 200)
  others     their word over the unit, briefly (capture, raid, a special
             without its own frames here) — DEVIATION `event_marks`
"""
import copy
import random
import time

from . import (cbbeam, cbblast, cbcloak, cbdraw, cbflare, cbreflect, cbsfx,
               cbshot)

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
        self.fast = False                # the game's FAST ANIMATIONS (COPT)
        self.colours, self.planet = {}, None   # for a flared target's picture
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
        self._carry = None       # a volley's flare, handed to its next shot
        self._lightning_frame = 0   # CMBTSFX 0's own frame (work order 210)
        self.last_beam = None    # the shot a reflection sends back

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
        new = [e for e in events
               if self._next_seq is None or e["seq"] >= self._next_seq]
        if new:
            self._next_seq = new[-1]["seq"] + 1
        if self.shown is None:
            if combat is not None:
                self.shown, self.ordnance = copy.deepcopy(combat), ordnance
            return
        playable = self._with_lightning(
            [e for e in new if e["kind"] != "command"])
        self._queue.extend(playable)
        if playable:
            self._last_queued = playable[-1]["seq"]
        if combat is not None and not self.busy():
            self.shown, self.ordnance = copy.deepcopy(combat), ordnance
            self._after = []
        elif combat is not None:
            self._after.append((self._last_queued, copy.deepcopy(combat),
                                ordnance))

    def _with_lightning(self, events):
        """HD STATE `lightning_inferred` (work order 210 C3): a Lightning
        Field fires wherever ordnance reaches a unit carrying a working one
        (cmbtmis.cpp:312-333) and no event says so (proposed open fix 76);
        HD puts the field's frames before each missile hit or fighter pass
        at such a unit, as the original draws them before the hit."""
        out = []
        for e in events:
            if e["kind"] in ("missile_hit", "fighter_pass") and \
                    not e.get("anti_missile") and \
                    _has_lightning(self._unit(e.get("target", -1))):
                out.append({"kind": "lightning", "seq": e["seq"] - 0.5,
                            "unit": e["target"], "serial": e.get("serial")})
            out.append(e)
        return out

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

    @property
    def reflection_frames(self):
        return self._art.frame_count("beams", 0x59) if self._art else 4

    def unit(self, i):
        return self._unit(i)

    def _unit(self, i):
        units = self.shown["units"] if self.shown else []
        return units[i] if 0 <= i < len(units) else None

    def _start(self, ev, now):
        k = ev["kind"]
        ev["_step"] = 2 if self.fast else 1
        if k == "move":
            if ev.get("teleport"):
                # `Draw_Teleporting_Ship_`: ten frames, five under FAST
                # (`cbcloak.vanish`, work order 210 C4)
                ev["_noise"] = random.randrange(0, 256, 2)
                return FRAME_S * (10 // ev["_step"])
            cells = max(abs(ev["to_x"] - ev["from_x"]),
                        abs(ev["to_y"] - ev["from_y"]), 1)
            return MOVE_S * cells / (6 if self.fast else 1)
        if k == "rotate":
            return FRAME_S * max(1, _turn_steps(ev["from_facing"],
                                                ev["to_facing"]))
        if k in ("special", "bomb", "blast_hit", "web_damage"):
            w = int(ev.get("weapon", 0))
            # a spherical blast is drawn on the special that fires it, every
            # time (work order 210 C3, `cbblast`)
            p = cbblast.plan(self, ev.get("source", -1), cbblast.AREA[w],
                             self._art) if k == "special" and \
                w in cbblast.AREA else None
            if p is None and k == "special" and w == cbsfx.ANTI_MISSILE:
                p = self._anti_missile(ev)
            if p is None:
                p = cbsfx.plan(ev, self._unit, self._art, self._last)
            if p is not None:
                ev["_sfx"] = p
                u = self._unit(ev.get("unit", ev.get("target", -1)))
                hit = ev.get("past_shields") or ev.get("hits")
                ticks = -(-p["frames"] // p.get("step", ev["_step"]))
                if u is not None and hit and not ev.get("at_missile"):
                    self._marks.append((str(hit), *cbdraw.centre(u),
                                        now + ticks * FRAME_S,
                                        (0xff, 0xcc, 0x40)))
                if ev.get("_destroyed"):
                    # the missiles destroyed, over the missile as the blast
                    # starts (`Add_Damage_Indicator_For_Missile_`,
                    # cmbtspec.cpp:772)
                    self._marks.append((str(ev["_destroyed"]), *ev["_at"],
                                        now + p["fly"] * FRAME_S,
                                        (0xff, 0xcc, 0x40)))
                return ticks * FRAME_S
        if k == "beam_shot":
            u = None if ev.get("at_missile") else \
                self._unit(ev.get("target", -1))
            dur = BOLT_S
            b = ev["_beam"] = self._beam(ev)
            if b is not None:
                nxt = self._queue[0] if self._queue else None
                volley = nxt is not None and nxt["kind"] == "beam_shot" and \
                    not nxt.get("at_missile") and all(
                        nxt.get(f) == ev.get(f) for f in ("source", "target"))
                self.last_beam = ev
                self._carry = cbshot.plan(ev, b, cbshot.flared(self, ev, u),
                                          self.fast, self._carry, volley)
                dur = len(b["ticks"]) * FRAME_S
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
            u = self._unit(ev.get("unit", -1))
            state = int(ev.get("death_state", 1))
            if u is not None and state in (2, 3, 4) and \
                    int(ev.get("previous_owner", 0)) < 10:
                # a ship dying in a blast (work order 210 C4, `cbblast`)
                p = cbblast.plan(self, ev["unit"], state, self._art)
                if p is not None:
                    ev["_sfx"] = p
                    return -(-p["frames"] // ev["_step"]) * FRAME_S
            if u is None:
                return 18 * FRAME_S / ev["_step"]
            ev["_death"] = cbblast.death_plan(u, self._art)
            return -(-ev["_death"][1] // ev["_step"]) * FRAME_S
        if k == "retreat":
            return 12 * FRAME_S / (3 if self.fast else 1)
        if k == "reflect":
            b = ev["_beam"] = cbreflect.plan(self, ev)
            u = self._unit(ev.get("shooter", -1))
            if b is not None:
                if u is not None and ev.get("past_shields"):
                    self._marks.append((str(ev["past_shields"]),
                                        *cbdraw.centre(u), now + len(
                                            b["ticks"]) * FRAME_S / 2,
                                        (0xff, 0xcc, 0x40)))
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

    def _anti_missile(self, ev):
        """The anti-missile rocket's plan (`cbsfx.anti_missile`), or None.
        HD STATE `anti_missile_count`: the engine does not say how many it
        destroyed (proposed open fix 75); HD reads it as the missile's
        quantity now less its quantity in the next state queued, or the
        whole stack when a `missile_gone` for it is queued."""
        src = self._unit(ev.get("source", -1))
        m = self._missile(ev.get("target", -1), self.ordnance)
        if src is None or m is None or not ev.get("at_missile", 1):
            return None
        later = next((o for seq, _c, o in self._after
                      if seq is None or seq >= ev["seq"]), None)
        after = self._missile(ev["target"], later)
        gone = any(e["kind"] == "missile_gone" and e.get("missile") ==
                   ev["target"] for e in self._queue)
        destroyed = m.get("quantity", 0) if gone else max(
            0, m.get("quantity", 0) - (after or {}).get("quantity",
                                                       m.get("quantity", 0)))
        ev["_destroyed"], ev["_at"] = destroyed, (m["x"], m["y"])
        return cbsfx.anti_missile(cbdraw.centre(src), (m["x"], m["y"]),
                                  destroyed, self._art, self.fast)

    @staticmethod
    def _missile(index, ordnance):
        return next((m for m in (ordnance or {}).get("missiles", [])
                     if m.get("index") == index), None)

    def _finish(self, ev):
        """The event's lasting effect on the shown battle."""
        k = ev["kind"]
        done = ev.get("_sfx", {}).get("finish") if isinstance(
            ev.get("_sfx"), dict) else None
        if done is not None:
            done()
        if k == "move":
            u = self._unit(ev["unit"])
            if u is not None:
                u["x"], u["y"] = ev["to_x"], ev["to_y"]
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
        total = self._art.frame_count("beams", 67) if self._art else 0
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
                "stop": size if holds else None, "specials": specials,
                "total": total or 10}

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
                steps = _turn_steps(ev["from_facing"], ev["to_facing"])
                sign = _turn_sign(ev["from_facing"], ev["to_facing"])
                u["facing_dir"] = (ev["from_facing"] +
                                   sign * int(steps * t)) & 15
        elif "_sfx" in ev:
            p = ev["_sfx"]
            if p["frames"]:
                n = p.get("step", ev.get("_step", 1))
                p["draw"](surface, cam, cache, min(
                    p["frames"] - 1, n * int(t * -(-p["frames"] // n))))
        elif k in ("beam_shot", "missile_hit", "reflect"):
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
            frame = min(n - 1, int(n * t))
            if frame >= n // 2:
                u["unit_status"] = 5
            pic = art.surface("cmbtsfx", entry, frame)
            if pic is not None:
                cx, cy = cbdraw.centre(u)
                surface.blit(cbdraw.scaled(pic, cam.scale, cache),
                             cam.to_window(cx + ox, cy + oy))
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


#: The Lightning Field's special bit (`SPECIAL_LIGHTNING_FIELD`).
LIGHTNING_FIELD = 19


def _has_lightning(u):
    """`Does_Combat_Ship_Have_Special_(u, SPECIAL_LIGHTNING_FIELD)`: the
    bit set and not damaged."""
    from . import cbpanel
    if u is None:
        return False
    have = cbpanel.special_bits(u.get("special_device_flags") or [0] * 5)
    hurt = cbpanel.special_bits(u.get("special_device_damage_flags") or
                                [0] * 5)
    return LIGHTNING_FIELD in have and LIGHTNING_FIELD not in hurt


def _turn_steps(a, b):
    d = (int(b) - int(a)) & 15
    return min(d, 16 - d)


def _turn_sign(a, b):
    d = (int(b) - int(a)) & 15
    return 1 if d <= 8 else -1
