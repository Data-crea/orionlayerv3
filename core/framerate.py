"""The frame rate the player chose — work order 212 B, decision 79.

HD EXTENSION `frame_rate`: MOO2 has no such setting.

Game Settings' OrionLayer rows offer 30, 60, 120, the monitor's refresh rate
(the default) and unlimited; `main.App.run` caps its loop at `cap()`. Nothing
in OrionLayer may run faster or slower with it (decision 78, one clock): the
battle's animations and sounds are timed by elapsed time (`screens/combat/
cbplay.py`, `cbsound.py`), and the waits that give up on a missing list
count snapshots, not frames (`core/researchscreen.py`, Leaders, Races,
Info). MOO2 has no such setting: it ran at the DOS timer's 18.2 Hz
(`timer::Release_Time_`, timer.cpp:14-24).

The monitor's rate is asked of SDL itself (`SDL_GetCurrentDisplayMode` for
the display the window is on), because pygame 2.6 has no call for it; when
SDL cannot say, 60 Hz is used and logged once.
"""
import ctypes
import ctypes.util
import logging
import os

log = logging.getLogger("framerate")

STEPS = ("30", "60", "120", "monitor", "unlimited")
DEFAULT = "monitor"
FALLBACK_HZ = 60

_said = False


def cap(choice, hz=None):
    """The frames a second `clock.tick` is given for a choice: 0 for
    unlimited (pygame's "no cap"), the monitor's rate for "monitor"."""
    choice = choice if choice in STEPS else DEFAULT
    if choice == "unlimited":
        return 0
    if choice == "monitor":
        return hz if hz is not None else monitor_hz()
    return int(choice)


class _Mode(ctypes.Structure):
    _fields_ = [("format", ctypes.c_uint32), ("w", ctypes.c_int),
                ("h", ctypes.c_int), ("refresh_rate", ctypes.c_int),
                ("driverdata", ctypes.c_void_p)]


def _sdl():
    """The libSDL2 pygame runs on — the one already in this process, so the
    display it reports is the one pygame opened."""
    try:
        with open("/proc/self/maps", encoding="utf-8") as fh:
            for line in fh:
                path = line.split()[-1]
                if os.path.basename(path).startswith("libSDL2-2.0.so"):
                    return ctypes.CDLL(path)
    except OSError:
        pass
    import pygame
    for name in ("SDL2.dll", "libSDL2-2.0.0.dylib"):
        path = os.path.join(os.path.dirname(pygame.__file__), name)
        if os.path.exists(path):
            return ctypes.CDLL(path)
    found = ctypes.util.find_library("SDL2")
    return ctypes.CDLL(found) if found else None


def monitor_hz():
    """The refresh rate of the display the window is on, or 60."""
    global _said
    hz = None
    try:
        from pygame._sdl2 import video
        index = video.Window.from_display_module().display_index
        lib = _sdl()
        mode = _Mode()
        if lib is not None and lib.SDL_GetCurrentDisplayMode(
                int(index), ctypes.byref(mode)) == 0 and mode.refresh_rate > 0:
            hz = int(mode.refresh_rate)
    except Exception as exc:              # no window yet, no SDL, no display
        if not _said:
            log.info("frame rate: the monitor's rate is unknown (%s)", exc)
    if hz is None:
        if not _said:
            log.info("frame rate: the monitor does not say its rate; %d Hz",
                     FALLBACK_HZ)
        _said = True
        return FALLBACK_HZ
    return hz
