"""The battle's sounds, played by HD — work order 212 C (open fix 79).

The hidden engine played every battle sound itself, at its own time, before
HD's picture of it (work order 210: 0.25 s ahead for a beam, the whole 2.5 s
of the Stellar Converter). With open fix 79 the engine plays none while HD
draws the battle: every `ERICNET::Mox_Play_Sound_` arrives as a CMEV event
(`sound`: the SOUND.LBX entry and a handle of the engine's own), and every
`Fadeout_Sound_`, `Loop_Sound_` and `Pitch_Bend_Sound_` of such a handle as
another (`sound_change`), each with the 55 ms ticks the engine waited since
the event before it. `cbplay` starts each at that point of its own animation
of that event; this module plays them — one program, one clock.

TRANSCRIPTION `sound_player`, what the engine's own player does
(sound.cpp):
  start      `Play_Sound_` (:1290-1341) on the first free channel of 16
             (`Find_Free_Channel_`, :1261-1277; none free: no sound), at the
             master volume (`Play_Sound_File_`, :1229), which is the game's
             Sound Fx level (`Set_Sound_Max_Volume_(_settings.sound_fx_level)`,
             harold.cpp:364, loadsave.cpp:1725) — gain = volume / 100
             (`Set_SDL_Stream_Gain_`, :132-138)
  fade       `Fadeout_Sound_(h, step)` stores the step (:1029-1035); every
             `Sound_Update_` (:322-346, from `Mox_Update_` once a frame)
             lowers the volume by it while the result stays in 1..100, else
             the sound stops. HD steps once every 55 ms tick — the frame of
             the animations it fades at (HD STATE `fade_tick`: the engine's
             idle battle updates twice a tick, its animations once)
  loop       `Loop_Sound_(h, n)` (:1037-1044): n < 0 for ever
  pitch      `Pitch_Bend_Sound_(h, p)` (:793-816): frequency = rate x ratio
             + p, at least 1 — HD resamples the sound by the new ratio
  handle -1  every sound (`Fadeout_Sound_(-1, 30)`, combinit.cpp:1168)

The sounds are read from the player's own SOUND.LBX, extracted raw beside
the battle's artwork (`tools/combat_art_extract.py`, decisions 38, 40, 42 —
never committed); without them the battle is silent and says so once in
the log.
"""
import io
import logging

log = logging.getLogger("combat")

TICK = 0.055                 # s: `Release_Time_(1)`, timer.cpp:14-24
CHANNELS = 16                # SOUND_CHANNEL_COUNT, sound.cpp
FADE, LOOP, PITCH = 1, 2, 3  # CEV_SOUND_CHANGE's change (open fix 79)
SOUND_LBX = "sound"
KINDS = ("sound", "sound_change")


class PygameBackend:
    """pygame's mixer, opened on first use. Every call is safe when there is
    no sound device: the battle is then silent, once logged."""

    def __init__(self):
        self.ok = None

    def _ready(self):
        if self.ok is None:
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.set_num_channels(CHANNELS)
                self.ok = True
            except Exception as exc:          # no device, no SDL audio
                log.warning("combat: no sound device (%s); the battle is "
                            "silent", exc)
                self.ok = False
        return self.ok

    def load(self, blob):
        if not self._ready():
            return None
        import pygame
        try:
            return pygame.mixer.Sound(file=io.BytesIO(blob))
        except (pygame.error, ValueError) as exc:
            log.warning("combat: a sound did not load (%s)", exc)
            return None

    def pitched(self, sound, ratio):
        """The sound played `ratio` times as fast — resampled, linear."""
        import numpy as np
        import pygame
        a = pygame.sndarray.array(sound)
        n = max(1, int(len(a) / ratio))
        at = np.arange(n) * ratio
        i = np.minimum(at.astype(np.int64), len(a) - 1)
        j = np.minimum(i + 1, len(a) - 1)
        w = (at - i)[:, None] if a.ndim > 1 else (at - i)
        out = a[i] * (1 - w) + a[j] * w
        return pygame.sndarray.make_sound(np.ascontiguousarray(
            out.astype(a.dtype)))

    def play(self, sound, loops):
        if not self._ready():
            return None
        import pygame
        ch = pygame.mixer.find_channel(False)
        if ch is not None:
            ch.play(sound, loops=loops)
        return ch

    def replay(self, channel, sound, loops):
        channel.play(sound, loops=loops)

    def volume(self, channel, v):
        channel.set_volume(max(0.0, min(1.0, v / 100.0)))

    def stop(self, channel):
        channel.stop()

    def busy(self, channel):
        return channel.get_busy()


class Sounds:
    """The battle's sounds on HD's clock: `at(when, event)` schedules a
    `sound` or `sound_change` event, `tick(now)` plays what is due and steps
    the fades; `level` is the game's Sound Fx level (0..100)."""

    def __init__(self, blob=None, backend=None):
        self._blob = blob                  # (lbx, entry) -> bytes or None
        self.backend = backend or PygameBackend()
        self.level = 100
        self._due = []                     # [(when, order, event)]
        self._order = 0
        self._live = {}                    # handle -> dict
        self._loaded = {}                  # (entry, pitch) -> sound or None
        self._missing = False
        self.played = []                   # (when, entry, handle): the record

    def set_level(self, level):
        level = max(0, min(100, int(level)))
        if level != self.level:
            # `Set_Master_Volume_` (sound.cpp:1115-1131): every channel to it
            for s in self._live.values():
                s["volume"] = level
                self.backend.volume(s["channel"], level)
        self.level = level

    def at(self, when, ev):
        self._due.append((when, self._order, ev))
        self._order += 1
        self._due.sort(key=lambda d: (d[0], d[1]))

    def reset(self):
        for s in list(self._live.values()):
            self.backend.stop(s["channel"])
        self._live, self._due = {}, []

    def busy(self):
        return bool(self._due) or any(self.backend.busy(s["channel"])
                                      for s in self._live.values())

    def tick(self, now):
        while self._due and self._due[0][0] <= now:
            when, _o, ev = self._due.pop(0)
            if ev["kind"] == "sound":
                self._start(when, ev)
            else:
                self._change(when, ev)
        for h, s in list(self._live.items()):
            if not self.backend.busy(s["channel"]):
                del self._live[h]
                continue
            while s["fade"] and now >= s["next"]:
                v = s["volume"] - s["fade"]
                if not 1 <= v <= 100:            # `Sound_Update_`, :333-344
                    self.backend.stop(s["channel"])
                    del self._live[h]
                    break
                s["volume"], s["next"] = v, s["next"] + TICK
                self.backend.volume(s["channel"], v)

    def _start(self, when, ev):
        handle, entry = ev.get("handle"), int(ev.get("sound", 0))
        loops, pitch = 0, 0
        # what the engine does to the handle in the same instant — a loop
        # or a pitch bend right after `Mox_Play_Sound_` — is applied before
        # the sound starts, not by starting it twice
        keep = []
        for d in self._due:
            c = d[2]
            if d[0] <= when and c["kind"] == "sound_change" and \
                    c.get("handle") == handle and c.get("change") in (LOOP,
                                                                       PITCH):
                if c["change"] == LOOP:
                    loops = -1 if c["value"] < 0 else int(c["value"])
                else:
                    pitch += int(c["value"])
            else:
                keep.append(d)
        self._due = keep
        old = self._live.pop(handle, None)
        if old is not None:
            self.backend.stop(old["channel"])
        snd = self._sound(entry, pitch)
        if snd is None:
            return
        ch = self.backend.play(snd, loops)
        if ch is None:                           # no free channel: none
            return
        self.backend.volume(ch, self.level)
        self._live[handle] = {"channel": ch, "volume": self.level,
                              "fade": 0, "next": when, "entry": entry}
        self.played.append((when, entry, handle))

    def _change(self, when, ev):
        handle, kind = ev.get("handle"), ev.get("change")
        targets = list(self._live.values()) if handle == -1 else \
            [self._live[handle]] if handle in self._live else []
        for s in targets:
            if kind == FADE:
                s["fade"], s["next"] = int(ev.get("value", 0)), when
            elif kind in (LOOP, PITCH):
                # later than the start (the engine does both at once, and
                # `_start` takes them there): the sound again from its start
                pitch = int(ev.get("value", 0)) if kind == PITCH else 0
                loops = (-1 if ev["value"] < 0 else int(ev["value"])) \
                    if kind == LOOP else 0
                snd = self._sound(s["entry"], pitch)
                if snd is not None:
                    self.backend.replay(s["channel"], snd, loops)

    def _sound(self, entry, pitch):
        key = (entry, pitch)
        if key in self._loaded:
            return self._loaded[key]
        blob = self._blob(SOUND_LBX, entry) if self._blob else None
        if not blob:
            if not self._missing:
                self._missing = True
                log.warning("combat: SOUND.LBX is not extracted; the battle "
                            "is silent. Run: python "
                            "tools/combat_art_extract.py")
            self._loaded[key] = None
            return None
        snd = self.backend.load(blob)
        if snd is not None and pitch:
            rate = _wav_rate(blob) or 22050
            ratio = max(1.0, rate + pitch) / rate
            snd = self.backend.pitched(snd, ratio)
        self._loaded[key] = snd
        return snd


def _wav_rate(blob):
    """The WAV's own sample rate (the `fmt ` chunk), or None."""
    if len(blob) < 28 or blob[:4] != b"RIFF":
        return None
    return int.from_bytes(blob[24:28], "little")


def offset(ev, sound, dur):
    """When a sound recorded after `ev` starts in HD's playback of `ev`, in
    seconds from its start: the engine's ticks since `ev` (open fix 79), no
    later than HD's animation ends. A loop without a wait says nothing in
    ticks, so an effect with one names the time of each of its sound items
    in its plan (`sound_times`, in the engine's order — the plasma web's
    travel and impact, the gyro's spin); and a move's loop has no wait
    (cmbtmov1.cpp:309-317; HD glides 0.15 s a cell, decision H of work
    order 202), nor has a teleport's: what is faded after either is faded
    at its end."""
    if ev is not None:
        k = ev.get("_sound_k", 0)
        ev["_sound_k"] = k + 1
        times = (ev.get("_sfx") or {}).get("sound_times") \
            if isinstance(ev.get("_sfx"), dict) else None
        if times and k < len(times):
            return max(0.0, min(dur, times[k]))
        if ev.get("kind") == "move" and sound["kind"] == "sound_change" \
                and sound.get("change") == FADE:
            # a teleport's loop has no wait either (cmbtmov1.cpp:856-891)
            return dur
    return max(0.0, min(dur, int(sound.get("ticks", 0)) * TICK))
