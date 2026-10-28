"""Read the mod folder again without the player starting the program by
hand — HD EXTENSION `mod_reload`, work order 337 (original: none).

**A RESTART IN PLACE, NOT A LIVE RELOAD.** More than thirty modules and
every screen keep what they loaded (scaled pictures, cut sprites, boxes);
a reload that clears them one by one shows a stale picture the day one is
forgotten. The one reload that cannot is a fresh process: the same
program, the same arguments, the same environment, the same process id —
`os.execv` — so the engine that `play.py` started keeps running and the new
client connects to it as any start does. What the person sees is the window
closing and opening again, on the screen the game is on.

**WHAT IS LOST.** Unsaved layout changes of the editor (Save first), the
window size chosen with F7 and anything else a start does not read from the
settings files. The engine is not touched.

UNVERIFIED live (no live runs, Data 20 October 2026): the check holds the
arguments and the order of the steps, not a real exec. On Windows `execv`
starts the new process and ends this one, which does the same for a player.
"""
import logging
import os
import sys

log = logging.getLogger("modreload")


def command():
    """The program as it was started: interpreter, then its arguments."""
    return [sys.executable] + list(sys.argv)


def restart(app, execv=os.execv, quit_=None):
    """Leave the engine link and the window cleanly, then start this program
    again over the process. `execv` and `quit_` are parameters so the suite can
    watch the calls instead of making them (a real `pygame.quit` would end
    the display for every later check); `execv` returns only as a stand-in."""
    argv = command()
    log.info("mod folder: restarting in place (%s)", " ".join(argv))
    client = getattr(app, "client", None)
    if client is not None:
        try:
            client.disconnect()
        except Exception as err:    # a link already gone must not stop it
            log.warning("mod folder: disconnect before restart: %s", err)
    try:
        if quit_ is None:
            import pygame
            quit_ = pygame.quit
        quit_()
    except Exception as err:
        log.warning("mod folder: pygame.quit before restart: %s", err)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (OSError, ValueError):
            pass
    execv(argv[0], argv)
