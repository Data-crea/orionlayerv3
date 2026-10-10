"""One fault in one screen must not end the game — work order 229 B.

Until 229 any exception in a screen's input, update or drawing ended the
client; `play.py` then stopped the engine, and everything the player had
done since the last save was gone (228's review, proposal 1). The guard
catches it per frame, in `main.App.run` only:

  * **the full stack goes to the log, every time** — the player's own log,
    `<user folder>/logs/faults.log` (`core.usermod.user_dir`, per platform;
    never a path of this machine), bounded at `LOG_BYTES` with `LOG_KEEP`
    old files, and one line on the console naming it;
  * **the screen on top is SUSPENDED**: nothing more reaches it — no input,
    no update, no drawing — so a fault that would repeat every frame
    cannot repeat at all. In its place HD draws a notice over the dimmed
    background: what happened, that the game is still running, and the way
    on. It is F12, as for every screen HD cannot draw (Data's rule since
    work order 187: no part of the original without F12): F12 shows the
    game, where the player plays on and can save; F12 again tries the HD
    screen once more. **Why suspend and not retry or skip one frame:** a
    screen whose `render` raised has drawn half a frame and may hold half
    an update; calling it again draws on that, and a fault that repeats
    would repeat sixty times a second. The game moving to another screen
    (`dispatcher.top` changes) also lifts it — a new screen, a new chance;
  * a fault while a screen is already suspended is OrionLayer's own loop
    (the poll, the screen switch, the notice): it is logged with its stack
    once, then counted — one line every `REPEAT_EVERY` seconds while it
    lasts — and the loop goes on at the frame cap, so it neither spins
    nor floods.

**OFF EVERYWHERE ELSE, and that is the point:** `FrameGuard()` starts
disarmed and re-raises; only `App.run` arms it, and no tool or check runs
`App.run`. The suite and the gates go red on an exception exactly as before
(check 090zzv holds it, with a suite run that must fail).
HD EXTENSION `frame_guard`: the original has no second renderer to fail.
`ORIONLAYER_FRAME_GUARD=off` leaves it disarmed for a developer who wants
the old crash.
"""
import logging
import os
import time
import traceback

log = logging.getLogger("orionlayer")

ENV = "ORIONLAYER_FRAME_GUARD"
LOG_NAME = "faults.log"
#: The log's bound: one file of this size, then `LOG_KEEP` older ones.
LOG_BYTES = 1024 * 1024
LOG_KEEP = 2
#: A repeating fault in the loop's own code: one count line this often.
REPEAT_EVERY = 10.0
#: The notice's words; the HD string file (`assets/shared/fallback/
#: labels.json`, decision 15) wins, as for the F12 notice.
DEFAULTS = {
    "fault_title": "Something went wrong in OrionLayer",
    "fault_what": "{screen}: an error in HD's own code. The game itself is "
                  "still running.",
    "fault_log": "The details are in",
    "fault_action": "F12: play on (and save) in the original - "
                    "F12 again: try HD once more",
    "fault_action_alone": "No game is connected: close OrionLayer and "
                          "start it again",
}

def suspended(app):
    """The screen `app`'s guard holds suspended, or None — also for a host
    that borrows the App's methods without being one (a check's stand-in
    App has no guard at all, and nothing is suspended there)."""
    guard = getattr(app, "_guard", None)
    return guard.suspended if guard is not None else None


def blocks(app, event):
    guard = getattr(app, "_guard", None)
    return guard is not None and guard.blocks(app, event)


def log_path():
    from core import usermod
    return os.path.join(usermod.user_dir(), "logs", LOG_NAME)


def _rotate(path):
    """Keep the log bounded: faults.log -> .1 -> .2, the oldest dropped."""
    try:
        if os.path.getsize(path) < LOG_BYTES:
            return
    except OSError:
        return
    for n in range(LOG_KEEP, 0, -1):
        older = f"{path}.{n}"
        newer = f"{path}.{n - 1}" if n > 1 else path
        if os.path.exists(newer):
            os.replace(newer, older)


def write_log(text, path=None):
    """Append `text` to the fault log; returns the path, or None when it
    could not be written (a full disk must not become the next fault)."""
    path = path or log_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _rotate(path)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text)
        return path
    except OSError as err:
        log.error("frame guard: the fault log %s could not be written: %s",
                  path, err)
        return None


class FrameGuard:
    """Per-frame exception guard for one App."""

    def __init__(self, armed=False, path=None):
        self.armed = armed
        self.path = path
        #: The screen object suspended, and its name, or None.
        self.suspended = None
        self.suspended_name = ""
        #: Faults caught (all), and suspensions begun.
        self.faults = 0
        self.suspensions = 0
        self._went_original = False
        self._repeat = None          # (signature, count, last line time)
        self._notice = None

    @classmethod
    def for_app(cls):
        """Armed unless ORIONLAYER_FRAME_GUARD=off — `App.run` only."""
        return cls(armed=os.environ.get(ENV, "").lower() not in
                   ("off", "0", "no"))

    # -- the frame ----------------------------------------------------
    def frame(self, app):
        """One frame of `app`: events, update, render — guarded if armed."""
        if not self.armed:
            app._handle_events()
            app._update()
            app._render()
            return
        try:
            app._handle_events()
            app._update()
            self._lift_if_moved_on(app)
            app._render()
            self._repeat_end()
        except Exception as exc:  # noqa: BLE001 — the guard's whole job
            self._fault(app, exc)

    def blocks(self, app, event):
        """True for an event that must not reach a suspended screen: all
        but the window's own and the App's function keys (F8, F9, F11,
        F12) — and none at all on F12, where input is the game's."""
        if self.suspended is None or app.render_mode == "original":
            return False
        import pygame
        if event.type in (pygame.QUIT, pygame.VIDEORESIZE):
            return False
        return not (event.type == pygame.KEYDOWN and event.key in (
            pygame.K_F8, pygame.K_F9, pygame.K_F11, pygame.K_F12))

    def _lift_if_moved_on(self, app):
        if self.suspended is None:
            return
        if app.render_mode == "original":
            self._went_original = True
            return
        if self._went_original or app.dispatcher.top is not self.suspended:
            why = ("back from F12" if self._went_original
                   else "the game moved to another screen")
            log.info("frame guard: %s resumed (%s)", self.suspended_name, why)
            self.suspended, self.suspended_name = None, ""
            self._went_original = False
            self._notice = None

    # -- a fault ------------------------------------------------------
    def _fault(self, app, exc):
        self.faults += 1
        stack = traceback.format_exception(type(exc), exc, exc.__traceback__)
        sig = (type(exc).__name__, tuple(
            (f.filename, f.lineno) for f in
            traceback.extract_tb(exc.__traceback__)[-3:]))
        top = app.dispatcher.top
        name = ((app.dispatcher.overlay_name or app.dispatcher.active_name)
                if top is not None else "") or "-"
        if self.suspended is None and top is not None:
            self.suspended, self.suspended_name = top, name
            self.suspensions += 1
            self._went_original = False
            self._notice = None
            app._surface_hd = False
            self._record(stack, f"in the screen {name!r}; the screen is "
                         f"suspended (F12, or the game moving on, resumes "
                         f"it)", exc)
            return
        # The loop's own code, or a fault with no screen to suspend:
        # the stack once, then a count while the same fault repeats.
        if self._repeat is not None and self._repeat[0] == sig:
            count, last = self._repeat[1] + 1, self._repeat[2]
            now = time.monotonic()
            if now - last >= REPEAT_EVERY:
                log.error("frame guard: the same fault again, %d times so "
                          "far (stack in %s)", count, self.path or log_path())
                last = now
            self._repeat = (sig, count, last)
            return
        self._repeat_end()
        self._repeat = (sig, 1, time.monotonic())
        self._record(stack, f"in OrionLayer's own loop (screen {name!r}"
                     f"{', suspended' if self.suspended is not None else ''})"
                     f"; it is counted while it repeats", exc)

    def _repeat_end(self):
        if self._repeat is not None and self._repeat[1] > 1:
            line = (f"{time.strftime('%Y-%m-%d %H:%M:%S')} the fault above "
                    f"repeated {self._repeat[1]} times in a row\n")
            write_log(line, self.path)
        self._repeat = None

    def _record(self, stack, where, exc):
        from core.config import build_line
        head = (f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} fault "
                f"{self.faults} {where}\n=== build: {build_line()}\n")
        written = write_log(head + "".join(stack), self.path)
        log.error("frame guard: %s: %s %s — full stack in %s",
                  type(exc).__name__, exc, where, written or "(no log)")

    # -- the notice ---------------------------------------------------
    def words(self, app):
        labels = getattr(app, "_note_labels", None) or {}
        get = lambda k: labels.get(k) or DEFAULTS[k]  # noqa: E731
        from core import lang
        # translated as a template, before its blanks are filled — the
        # filled line is no key of the language file
        what = (lang.tr(get("fault_what")).replace(
            "{screen}", self.suspended_name) + " " +
            lang.tr(get("fault_log")) + " " + (self.path or log_path()))
        action = get("fault_action" if app.connected
                     else "fault_action_alone")
        return get("fault_title"), what, action

    def render(self, app):
        """The notice over the dimmed universal background — never the
        half-drawn frame the fault left."""
        from core import backgrounds, f12notice
        if self._notice is None:
            self._notice = f12notice.Notice()
            backgrounds.draw(app.surface, "universal")
        elif self._notice._base is not None and \
                self._notice._base.get_size() != app.surface.get_size():
            self._notice = f12notice.Notice()
            backgrounds.draw(app.surface, "universal")
        title, what, action = self.words(app)
        self._notice.render(app.surface, app.style, app._note_labels, what,
                            title=title, action=action)
        app._surface_hd = False
