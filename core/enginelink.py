"""A lost engine — work order 322 C.

Until 322 a connection that closed was reopened once; if that failed the
client stayed disconnected for good, while `main.App` still counted itself
connected and drew the last state as if the game stood behind it. And a
watchdog reconnected after ten seconds of SILENCE, which is how a busy game
looks (P811). Now:

  * **silence is not death** (`core/game_client.py`, STALE_TIMEOUT): only a
    close or a reset is a loss — every way the engine drops a client closes
    its socket (ext_server.cpp:460-471), and the kernel closes a dead
    process's — so a game generating a galaxy or processing a turn is
    waited for, however long, and is never reconnected under;
  * **the App follows the client**: when the client reports a loss
    (`GameClient.lost`), or the App counts itself connected while a client
    that knows of losses is not, `App.connected` goes False; it comes back
    True only when a retry has connected AND the first snapshot of the new
    connection has arrived — until then the panel stays and nothing is sent
    on a snapshot of the old connection. A stand-in client in a check,
    which knows nothing of losses, is never disconnected by this;
  * **a press that was down when the link went is spoilt** (the pointer
    gates), and its release still passes, so a drag ends cancelled, never
    half-done;
  * **a loss is retried**, one connect every `RETRY_EVERY` seconds (wall
    clock: there are no snapshots to count while there is no connection —
    decision 21 counts snapshots where they exist). Each reconnect drops
    its field list (P811, `GameClient._reconnect`);
  * **and said**: the last HD frame, dimmed, with a panel — "The connection
    to the game was lost", that OrionLayer keeps trying, and how to end. No
    input reaches the screen under it (the window's own keys do);
  * **an engine that is gone is said, not retried forever**: `play.py`
    passes the PID of the engine it started (`ENV_PID`) and its log
    (`ENV_LOG`); when that process has ended, or is a zombie waiting for
    play.py to reap it, the panel says the game has ended, where its log
    is, and to start again — and the retries stop. Read off `/proc` only
    (check 006e: OrionLayer signals no process); where there is no `/proc`
    the process cannot be asked and the loss is retried, as for an engine
    somebody started by hand. `/proc` is asked once per retry tick, and
    GONE is final;
  * **play.py's engine not reached at the start is a loss too**: with
    `ENV_PID` set the first connect's failure is not the standalone start
    but the panel and the retries.

HD EXTENSION `engine_lost`: the original is the engine — it has no
connection to lose and no second program to tell the player about it. The
words are OrionLayer's own, in the HD string file
`assets/shared/fallback/labels.json` beside the F12 notice's (decision 15),
which a mod replaces, and translated through `core/lang` like them.

UNVERIFIED `engine_lost_live` (Data's decision of 20 October 2026: no live
runs): a live run would kill the engine under `python play.py` (the panel
"The game has ended", the log's path) and restart one by hand under
`python main.py` (the panel gone, the screen following the game).
"""
import logging
import os
import time

log = logging.getLogger("orionlayer")

#: What play.py passes OrionLayer about the engine it started.
ENV_PID = "ORIONLAYER_ENGINE_PID"
ENV_LOG = "ORIONLAYER_ENGINE_LOG"
#: Seconds between two connects after a loss.
RETRY_EVERY = 2.0

#: The link's states besides None (connected, or never connected).
LOST, GONE = "lost", "gone"

#: The panel's words; the HD string file wins, as for the F12 notice.
DEFAULTS = {
    "lost_title": "The connection to the game was lost",
    "lost_what": "OrionLayer tries to reach the game again every few "
                 "seconds and carries on as soon as it answers.",
    "lost_action": "Close the window to end OrionLayer",
    "gone_title": "The game has ended",
    "gone_what": "orion2re is no longer running, so OrionLayer stops "
                 "trying.",
    "gone_log": "The game's log is",
    "gone_action": "Close OrionLayer and start it again: python play.py",
}


def process_state(pid, proc="/proc"):
    """`(alive, start)` of process `pid` from `proc`: alive True or False,
    and its start time (stat field 22, to tell a reused PID) — or
    `(None, None)` where the process cannot be asked (no `/proc`). A zombie
    is not alive: the engine is play.py's child, and play.py reaps it only
    after OrionLayer has ended."""
    if not pid or not os.path.isdir(proc):
        return None, None
    try:
        with open(os.path.join(proc, str(pid), "stat")) as handle:
            text = handle.read()
    except FileNotFoundError:
        return False, None
    except OSError:
        return None, None
    rest = text.rsplit(")", 1)[-1].split()
    if len(rest) < 20:
        return None, None
    return rest[0] not in ("Z", "X", "x"), rest[19]


class Link:
    """The App's view of its engine: connected, lost or gone."""

    def __init__(self, pid=None, engine_log=None, proc="/proc",
                 clock=time.monotonic):
        self.pid = pid
        self.engine_log = engine_log
        self.proc = proc
        self.clock = clock
        self.state = None
        self.retries = 0
        self._next = 0.0
        self._start = None
        self._started = False       # the start's failed connect looked at
        self._await = None          # the STATE count a reconnect waits past
        self._reconnected = 0       # the client's reconnects already taken
        self._notice = None
        if pid:
            self._start = process_state(pid, proc)[1]

    @classmethod
    def from_env(cls, environ=None):
        env = os.environ if environ is None else environ
        try:
            pid = int(env.get(ENV_PID, "") or 0) or None
        except ValueError:
            pid = None
        return cls(pid=pid, engine_log=env.get(ENV_LOG) or None)

    @property
    def down(self):
        return self.state is not None

    def engine_gone(self):
        """True when play.py's engine has ended; False when it runs or no
        engine was named, or it cannot be asked."""
        if not self.pid:
            return False
        alive, start = process_state(self.pid, self.proc)
        if alive is None:
            return False
        if not alive:
            return True
        return self._start is not None and start != self._start

    # -- the frame ----------------------------------------------------
    def follow(self, app):
        """Poll, retry, end — once a frame from `main.App._update`. Returns
        `app.connected` as it now stands."""
        client = app.client
        knows = hasattr(client, "lost")
        if knows and not self._started:
            self._started = True
            self._reconnected = getattr(client, "reconnected", 0)
            if self.pid and not app.connected and client.lost is None:
                # play.py's engine, not reached at the start (WO 322 C13)
                client.lost = "no connection at the start"
        if app.connected or (self.state == LOST and client.connected):
            client.poll()
        if getattr(client, "game_ended", False):
            # QUIT -> YES in the GAME menu: the player asked the game to
            # end, the client stood its watchdog down before sending YES,
            # and OrionLayer ends with it (decision 62). No reconnect, no
            # "game ended" screen.
            from core import lastword
            log.info("orion2re ended at the player's request; "
                     "OrionLayer exits with it")
            lastword.ended("the game ended at the player's request")
            app.running = False
            app.connected = False
            return False
        if not knows or self.state == GONE:
            return app.connected
        again = getattr(client, "reconnected", 0)
        if again != self._reconnected:
            # THE CLIENT RECONNECTED ITSELF within the poll (a close, then
            # a connect that worked): `connected` never went False, so the
            # branch below would not see a loss and the App would keep
            # acting on the old connection's snapshot, its pointer gates
            # unspoilt. It is a loss all the same; the way back is the
            # documented one — the new connection's first snapshot.
            self._reconnected = again
            if app.connected and client.connected:
                self._went_down(app, client, "reconnected at once")
        if not client.connected:
            if app.connected or self.state is None:
                if client.lost is None and not app.connected:
                    return False            # the standalone start
                # a loss: said by the client, or a client found closed
                client.lost = client.lost or "the connection closed"
                self._went_down(app, client)
            elif self.clock() >= self._next:
                self._next = self.clock() + RETRY_EVERY
                if self.engine_gone():
                    self._gone()
                else:
                    self.retries += 1
                    if client.retry():
                        self._await = client.stats.get("state", 0)
            return app.connected
        if self.state == LOST:
            if self._await is None:
                self._await = client.stats.get("state", 0)
            elif client.stats.get("state", 0) > self._await:
                # the first snapshot of the new connection: the world now
                log.info("orion2re reached again after %d retries",
                         self.retries)
                self.state, self.retries, self._notice = None, 0, None
                self._await = None
                app.connected = True
        return app.connected

    def _went_down(self, app, client, why=None):
        app.connected = False
        self._notice, self._await = None, None
        # a press that was down is spoilt: its release cancels (C5)
        for name in ("_pointer_gate", "_right_gate"):
            gate = getattr(app, name, None)
            if gate is not None:
                gate.watch(False)
        if self.engine_gone():
            self._gone()
            return
        self.state = LOST
        self._next = self.clock() + RETRY_EVERY
        log.warning("the connection to orion2re was lost (%s); retrying "
                    "every %.0f s", why or client.lost, RETRY_EVERY)

    def _gone(self):
        self.state, self._notice = GONE, None
        log.warning("orion2re (PID %s) has ended; not reconnecting%s",
                    self.pid, f" — its log is {self.engine_log}"
                    if self.engine_log else "")

    def blocks(self, event, app=None):
        """True for an event that must not reach the screen under the
        panel: all but the window's own (close, resize), the release of a
        button whose press was down when the link went (its gate is spoilt,
        so it ends the gesture cancelled, not half-done) and the App's
        window keys — F12 is blocked, there is no game to show."""
        if self.state is None:
            return False
        import pygame
        if event.type in (pygame.QUIT, pygame.VIDEORESIZE, pygame.KEYUP):
            return False
        if event.type == pygame.MOUSEBUTTONUP:
            gate = getattr(app, {1: "_pointer_gate", 3: "_right_gate"}.get(
                getattr(event, "button", 0), ""), None)
            return not (gate is not None and gate.armed)
        from core import hdkeys
        return not (event.type == pygame.KEYDOWN and hdkeys.own(event) in (
            hdkeys.WINDOW_SIZE, hdkeys.SCREENSHOT, hdkeys.FULLSCREEN))

    # -- the panel ----------------------------------------------------
    def words(self, labels):
        """`(title, what, action)` in the session's language."""
        labels = labels or {}
        get = lambda k: labels.get(k) or DEFAULTS[k]  # noqa: E731
        from core import lang
        if self.state == GONE:
            what = lang.tr(get("gone_what"))
            if self.engine_log:
                what += " " + lang.tr(get("gone_log")) + " " + \
                    self.engine_log
            return get("gone_title"), what, get("gone_action")
        return get("lost_title"), get("lost_what"), get("lost_action")

    def render(self, app):
        """The panel over the last HD frame, dimmed; over the universal
        background once the window has another size than that frame."""
        from core import backgrounds, f12notice
        size = app.surface.get_size()
        if self._notice is None or self._notice.size not in (None, size):
            if self._notice is not None:
                backgrounds.draw(app.surface, "universal")
            self._notice = f12notice.Notice()
        title, what, action = self.words(getattr(app, "_note_labels", None))
        rect = self._notice.render(app.surface, app.style,
                                   getattr(app, "_note_labels", None), what,
                                   title=title, action=action)
        app._surface_hd = False
        return rect


def link(app):
    """The App's link; a host that has none — a tool's or a check's
    stand-in borrowing `main.App`'s methods — gets a fresh one each time,
    never a shared one that could carry one host's loss to the next."""
    found = getattr(app, "_link", None)
    return found if found is not None else Link()


def follow(app):
    return link(app).follow(app)


def down(app):
    return link(app).down


def blocks(app, event):
    return link(app).blocks(event, app)


def render(app):
    return link(app).render(app)
