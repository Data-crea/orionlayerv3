"""The battle's one playback clock and its speed control (work order 399).

The original's PageUp / PageDown change `animation_speedup` between -3 and
+3 and a readout "Animation speed %+d" shows for 55 ticks of 55 ms.

TRANSCRIPTION `speed_keys` (work order 399): PageUp raises the level,
PageDown lowers it, clamped to -3..+3, and every key push stamps the
readout's time even when the level did not move (`Handle_Animation_Speed_Key`,
timer.cpp:27-39, called from every key push, key.cpp:70); the readout is
visible 55 ticks x 55 ms = 3.025 s after the stamp
(`Animation_Speed_Change_Is_Visible`, timer.cpp:45-51) as the text
"Animation speed %+d", right-aligned at (630, 8) of the 640 x 480 plane in
`combat_green` (`Draw_Animation_Speed`, cmbtdrw1.cpp:45-58; mox.cpp:644).

HD EXTENSION `speed_factor`: the original takes `speedup` ticks off each
WAIT (`Release_Time`, timer.cpp:53-76, the subtraction :61); HD's playback has no waits (the
engine waits for no animation while HD draws, open fix 71; decision 78: one
clock), so the level scales the clock instead: `now()` advances by the real
time x `FACTOR ** level` (1.6 ** level, so +3 plays 4.1 times and -3 0.24
times as fast). It is continuous and monotonic: a level change changes the
slope, never the value. Level 0 is the real time exactly (`now()` returns
the real source's value untouched). The level is kept while the program
runs and is not saved. Everything that is animation time reads `now()`:
the playback and the sounds scheduled on it, the fades, the glow and the
ship frame. What is NOT scaled: input waits and timeouts (`_ready`, the
held input, the OPTIONS/popup/row waits, the readout's own 3.025 s), the
WAV's own length and the planet's global spin clock. SOUNDS, exactly
(`cbsound.Sounds.tick(now)`, given this clock's time): a sound STARTS at
its picture's scaled tick, a FADE steps its volume once per 55 ms of THIS
clock (so at +3 a fading sound ends with its faster picture), and the
sample itself plays out at its real length. The keys are taken in every
state (key.cpp:70 runs for any key) and are never sent to the engine. The
core's own real-time reads the battle calls (glassfx, textsize,
screen_base's button flash, namebox's caret) are HUD chrome, not battle
animation, and stay on the real time.

HD EXTENSION `speed_readout`: the original shows the readout only under
AUTO (cmbtdrw1.cpp:980-983); HD shows it in any mode, as the keys work in
any mode. HD STATE `speed_readout_place`: the plane is the window (the
point scales by the window's width and height over 640 x 480), the font is
HD's, 12 plane rows tall (the original's font 3 height is not measured:
UNVERIFIED), the colour is palette entry 0x89, `combat_green`'s body
(entry 1; entry 0 is its edge, fonts.cpp:62).

This is the one module of the battle allowed to read `time.monotonic()` for
animation time: `CLOCK.real`. The input waits of `screen`, `cbopts`,
`cbpopups` and `cbpanel` read the real time on purpose (check 090zzzzzzzzx).
"""
import time

import pygame

from core.nativeview import NATIVE_H, NATIVE_W

#: the original's range and readout (timer.cpp:9-10, :13)
MIN_LEVEL, MAX_LEVEL = -3, 3
READOUT_S = 55 * 0.055                     # 3.025 s
FACTOR = 1.6
#: the original's key pushes (key.cpp:70) are PageUp / PageDown
STEP_KEYS = {pygame.K_PAGEUP: 1, pygame.K_PAGEDOWN: -1}
#: `combat_green`'s body entry, the readout's point and text row (the plane
#: is `core.nativeview`'s)
GREEN_INDEX = 0x89
RIGHT_AT = (630, 8)
TEXT_ROWS = 12


def _real():
    """The one real-time read of the animation clock; looked up at the call
    so a check can stand in for the module's `time`."""
    return time.monotonic()


class Clock:
    """Virtual playback time over an injectable real-time source."""

    def __init__(self, real=_real):
        self.real = real
        self.level = 0
        self._shift = 0.0              # level 0: virtual = real + shift
        self._base = None              # (real, virtual) at the last change
        self._stamp = None             # real time of the last key push

    def factor(self):
        return FACTOR ** self.level

    def now(self):
        r = self.real()
        if self.level == 0:
            return r + self._shift if self._shift else r
        return self._base[1] + (r - self._base[0]) * self.factor()

    def step(self, d):
        """TRANSCRIPTION `speed_keys`: clamp to -3..+3; the readout's stamp
        is taken on every push, as the original's."""
        v, r = self.now(), self.real()
        self.level = max(MIN_LEVEL, min(MAX_LEVEL, self.level + d))
        self._base = (r, v)
        self._shift = v - r            # the road back to level 0
        self._stamp = r
        return self.level

    def readout_visible(self, real_now=None):
        r = self.real() if real_now is None else real_now
        return self._stamp is not None and \
            0 <= r - self._stamp < READOUT_S

    def text(self):
        return f"Animation speed {self.level:+d}"


CLOCK = Clock()


def now():
    """The battle's animation time."""
    return CLOCK.now()


def handle_key(key):
    """True when `key` is a speed key and was taken (never forwarded)."""
    d = STEP_KEYS.get(key)
    if d is None:
        return False
    CLOCK.step(d)
    return True


def draw_readout(surface, style, art, clock=None):
    """HD EXTENSION `speed_readout`: drawn last of the battle's own parts."""
    clock = clock or CLOCK
    if not clock.readout_visible():
        return
    w, h = surface.get_size()
    colour = art.palette_with().get(GREEN_INDEX, (60, 200, 60))
    img = style.render_text(clock.text(), max(9, round(
        TEXT_ROWS * h / NATIVE_H)), colour)
    surface.blit(img, (round(RIGHT_AT[0] * w / NATIVE_W) - img.get_width(),
                       round(RIGHT_AT[1] * h / NATIVE_H)))
