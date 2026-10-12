"""HD's own keys — the one table (work order 231 D, Data's decision 4).

The App answers these before any screen (`main.App._handle_events`); every
other key goes to the screen and, where the screen does not answer it, to the
game by `core/keyfwd.py`'s rule.

Data's decision 4 of 10 October 2026: F5 and F9 are the original's again (the
previous own star; the distance between stars), so HD's layout editor and
window size moved to keys the original answers on NO screen and HD did not
use — F3 and F7 (`Check_Function_Keys_` has no case for -1003 or -1007,
mainscr.cpp:3047-3153, and no other screen tests them; the table per screen
is `dev:doc/briefs/230-keys.md`). Which of the two is which is HD's choice,
parked for Data (231 P1): F7 sits beside F8 (the screenshot), the other key
of the window, and F3 is left for the editor, a modder's tool.

With Alt held none of them is HD's: Alt+F3, Alt+F5, Alt+F7, Alt+F8 and Alt+F9
are the original's game options and autosave on the galaxy map
(mainscr.cpp:3237-3302, mainscr_main.cpp:617-626), which until work order 231
never reached the game because the App took the bare key first.
"""
import pygame

#: (key, what it does) — the names a player reads come from here.
EDITOR = pygame.K_F3
WINDOW_SIZE = pygame.K_F7
SCREENSHOT = pygame.K_F8
FULLSCREEN = pygame.K_F11
ORIGINAL = pygame.K_F12

OWN = {
    EDITOR: "the layout editor",
    WINDOW_SIZE: "the window size",
    SCREENSHOT: "a screenshot",
    FULLSCREEN: "full screen",
    ORIGINAL: "the original's picture",
}


def name(key):
    """"F3" for pygame.K_F3."""
    return pygame.key.name(key).upper()


def own(event):
    """The HD key this KEYDOWN is, or None — never with Alt held."""
    if getattr(event, "mod", 0) & pygame.KMOD_ALT:
        return None
    key = getattr(event, "key", None)
    return key if key in OWN else None
