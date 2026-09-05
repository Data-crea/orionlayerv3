"""Injection chain — drive orion2re through a sequence of original
dialogs while an HD screen stays on top.

Used by Empire Identity: after Custom Race the game shows three
dialogs in a row (Enter Ruler Name, Select Banner Color, Enter Home
Star Name). The HD screen collects all three answers at once; on
Accept the chain feeds them to the game one dialog at a time.

Steps are detected by the SHAPE of the field list, not by field IDs,
so no per-dialog dump is needed:
  name dialog    exactly one type=11 (string input) field
  banner dialog  >= 8 type=1 (radio) fields

Ordering rule: everything a step sends goes into orion2re's SDL
event queue in one burst (keys, clicks, Enter) — that keeps the
order. ACTIVATE_FIELD is NOT used inside a step: g_pending_field is
consumed by Get_Input_() before queued SDL events, so it would fire
before the typed text arrives.

After a step fires, the next step is only evaluated once the field
list has CHANGED (the two name dialogs look identical) and a short
settle time has passed.

**That shape is also what makes this chain immune to the pre-effect
snapshot, and it was immune before anybody knew to ask** — audited
5 September 2026. Twice over: `ext_api.cpp` sends a FIELD_LIST only
when the field count or the screen changed, which cannot happen
before the game has acted, and the comparison is against the
SIGNATURE this chain fired on, so an unchanged list does not advance
it. A loop that waited for "a fresh message" instead would be
answered by the message serialized in the very tick that consumed its
send. See "A fresh message is not a fresh world" in the fundament;
the settle here is a floor under that comparison, not the thing that
ends the wait.

The three dialogs are NOT evenly spaced. Ruler name and banner sit
next to each other inside `Race_Selection_Screen_`, but the home star
name is asked after race selection has returned and the game has
generated the galaxy — seconds of complete silence, because
`ext::Tick()` only runs from `fields::Get_Input_()` and mapgen has no
input loop. Hence the per-step timeout, and hence the chain holding
the client's stale-connection watchdog open while it waits: a
reconnect in that gap throws away the FIELD_LIST the last step is
waiting for, and `ext_api.cpp` will not send another one until the
field count or the screen changes again.

Known limitation (to verify live): INJECT_KEY pushes a bare keysym
without modifiers. Whether upper-case letters survive depends on
orion2re's key → ASCII path; if names arrive lower-case, INJECT_KEY
needs a modifier field on the C++ side.
"""
import logging
import time
import pygame

log = logging.getLogger("injection")

TYPE_BUTTON = 0
TYPE_RADIO = 1
TYPE_STRING = 11

SETTLE_S = 0.35        # wait after a step before looking for the next
STEP_TIMEOUT_S = 4.0   # default: give up on a step that never appears
CLEAR_KEYS = 24        # backspaces sent to empty a name field

# A step may carry its own timeout as a fourth element, because the
# gaps between dialogs are not the same length. The home star name is
# not asked by racesel.cpp at all — it comes after the game has left
# race selection and GENERATED THE GALAXY, and nothing publishes
# state during that. The wait is a mapgen, not a redraw.
LONG_STEP_TIMEOUT_S = 90.0

# While a chain is live the connection is held open regardless of
# silence: a reconnect in the middle of a chain loses the FIELD_LIST
# the next step is waiting for, and the chain can never recover.
WATCHDOG_MARGIN_S = 5.0

# How often a waiting step reports what is arriving on the socket.
HEARTBEAT_S = 2.0


def _signature(fields):
    return tuple((f.index, f.x, f.y, f.x_end, f.y_end, f.field_type)
                 for f in fields)


# ── Detectors ────────────────────────────────────────────

def is_name_dialog(fields):
    return sum(1 for f in fields if f.field_type == TYPE_STRING) == 1


def _banner_tiles(fields):
    """The 8 banner tiles of the Flag Screen. Detected by SHAPE, not
    type: live the tiles do NOT come through as type=1 radio buttons
    (they are plain/hidden fields), so we look for >= 8 non-string
    fields sharing the same size, laid out in 2 rows."""
    cand = [f for f in fields if f.field_type != TYPE_STRING
            and f.x_end > f.x and f.y_end > f.y]
    by_size = {}
    for f in cand:
        by_size.setdefault((f.x_end - f.x, f.y_end - f.y), []).append(f)
    best = max(by_size.values(), key=len, default=[])
    if len(best) < 8:
        return []
    return sorted(best, key=lambda f: (f.y, f.x))


def is_banner_dialog(fields):
    return len(_banner_tiles(fields)) >= 8


def describe(fields):
    return " ".join(f"{f.index}:t{f.field_type}@{f.x},{f.y}-{f.x_end},{f.y_end}"
                    for f in fields)


# ── Actions ──────────────────────────────────────────────

def type_name(client, text):
    """Clear the focused string field and type `text`, then Enter.
    All keys go into one SDL burst so the order is preserved."""
    for _ in range(CLEAR_KEYS):
        client.inject_key(pygame.K_BACKSPACE)
    for ch in text:
        code = ord(ch)
        if 32 <= code < 127:
            client.inject_key(code)
    client.inject_key(pygame.K_RETURN)


def click_banner(client, fields, color, order):
    """Click the radio tile for `color`; tiles are sorted by row/col
    and mapped onto `order` (the MOO2 colour sequence)."""
    tiles = _banner_tiles(fields)[:len(order)]
    idx = order.index(color) if color in order else 0
    if idx >= len(tiles):
        log.warning("Banner tile %d missing (%d tiles)", idx, len(tiles))
        return False
    f = tiles[idx]
    # ACTIVATE_FIELD instead of INJECT_CLICK: the click path maps
    # 640x480 coords as window coords (orion2re ext bug) and this
    # step sends no keys, so g_pending_field ordering is no issue.
    log.info("Banner tile %d -> field %d", idx, f.index)
    client.activate_field(f.index)
    return True


# ── Runner ───────────────────────────────────────────────

class InjectionChain:
    """steps: list of (name, detect(fields) -> bool,
                       run(client, fields) -> None
                       [, timeout_seconds])

    An empty field list is treated as NO INFORMATION, never as a
    change and never as a detection: after a reconnect the client
    clears the list rather than keep a stale one, and the game
    publishes nothing at all while it is busy. Only the step timeout
    runs during such a gap.
    """

    def __init__(self, client, steps):
        self.client = client
        self.steps = [self._normalise(s) for s in steps]
        self.pos = 0
        self.failed = False
        self.failed_step = ""
        self._fired_at = 0.0
        self._fired_sig = None
        self._started = time.monotonic()
        self._beat_at = self._started
        self._beat_stats = None
        self._chain_started = self._started
        self._setup_logged = False

    @staticmethod
    def _normalise(step):
        name, detect, run = step[0], step[1], step[2]
        timeout = step[3] if len(step) > 3 else STEP_TIMEOUT_S
        return (name, detect, run, timeout)

    @property
    def done(self):
        return self.pos >= len(self.steps)

    @property
    def current(self):
        return self.steps[self.pos][0] if not self.done else ""

    @property
    def step_number(self):
        """1-based index of the step being waited for."""
        return min(self.pos + 1, len(self.steps))

    @property
    def step_count(self):
        return len(self.steps)

    @property
    def waited(self):
        """Seconds spent on the current wait — either since the last
        step fired, or since the field list last changed. Worth
        showing: the gap before the home star name is a mapgen, and a
        number is the difference between "slow" and "hung"."""
        ref = self._fired_at if self._fired_sig is not None else self._started
        return max(0.0, time.monotonic() - ref)

    def _log_setup(self, game_state):
        """One line at the start with the New Game settings.

        A chain that takes 3 s on one run and 24 s on the next is
        useless to diagnose unless the log says what the two runs
        differed in. Galaxy size and opponent count are the obvious
        candidates and were not being recorded, so two runs could not
        be compared at all.
        """
        if self._setup_logged:
            return
        self._setup_logged = True
        get = lambda n: getattr(game_state, n, None)
        if get("ng_galaxy_size") is None:
            return
        conns = None
        try:
            from core.game_client import count_connections
            conns = count_connections(getattr(self.client, "port", 17362))
        except Exception:
            pass
        log.info("setup: galaxy_size=%s age=%s opponents=%s (players=%s) "
                 "difficulty=%s tech=%s stars=%s ext_connections=%s",
                 get("ng_galaxy_size"), get("ng_galaxy_age"),
                 get("ng_opponents"),
                 (get("ng_opponents") or 0) + 2,
                 get("ng_difficulty"), get("ng_tech_level"),
                 get("num_stars"), conns)

    def _snapshot_stats(self):
        s = getattr(self.client, "stats", None)
        return dict(s) if s else None

    def _heartbeat(self, now, name, waited, fields):
        """One line every HEARTBEAT_S while a step waits.

        The point is the traffic, not the elapsed time. A wait with
        snapshots pouring in means the game is running its input loop
        and the chain is the thing that is slow; a wait with nothing
        arriving means the game is busy and the chain is doing its
        job. The two are indistinguishable on screen.
        """
        if now - self._beat_at < HEARTBEAT_S:
            return
        stats = self._snapshot_stats()
        delta = ""
        if stats and self._beat_stats:
            secs = max(0.001, now - self._beat_at)
            d = {k: stats[k] - self._beat_stats.get(k, 0) for k in stats}
            delta = (f" | {d['state'] / secs:.1f} state/s"
                     f"  {d['fields']} field lists"
                     f"  {d['visual'] / secs:.1f} visual/s"
                     f"  {d['bytes'] / secs / 1024:.0f} KB/s")
        self._beat_at = now
        self._beat_stats = stats
        log.info("waiting for '%s' %.1fs (%d fields)%s",
                 name, waited, len(fields), delta)

    def update(self, game_state):
        """Call every frame while the chain is active."""
        if self.done or self.failed or game_state is None:
            return
        name, detect, run, timeout = self.steps[self.pos]

        # Keep the connection alive for as long as this step may wait.
        hold = getattr(self.client, "hold_watchdog", None)
        if hold is not None:
            hold(timeout + WATCHDOG_MARGIN_S)

        self._log_setup(game_state)
        fields = game_state.fields or []
        now = time.monotonic()
        self._heartbeat(now, name, self.waited, fields)

        if self._fired_sig is not None:
            # Waiting for the game to move on to the next dialog.
            if now - self._fired_at < SETTLE_S:
                return
            if not fields or _signature(fields) == self._fired_sig:
                if now - self._fired_at > timeout:
                    self._fail("Chain stuck after '%s' — waited %.1fs "
                               "for '%s' (%d fields)",
                               self.steps[self.pos - 1][0],
                               now - self._fired_at, name, len(fields))
                return
            log.info("Fields changed after '%s' (%.1fs): %s",
                     self.steps[self.pos - 1][0], now - self._fired_at,
                     describe(fields))
            self._fired_sig = None
            self._started = now

        if fields and detect(fields):
            log.info("Chain step '%s' (%d fields, %.1fs after the "
                     "previous list)", name, len(fields),
                     now - self._started)
            run(self.client, fields)
            self._fired_at = now
            self._fired_sig = _signature(fields)
            self.pos += 1
            if self.done:
                log.info("Chain complete in %.1fs",
                         now - self._chain_started)
        elif now - self._started > timeout:
            self._fail("Chain step '%s' never appeared after %.1fs; "
                       "fields: %s", name, now - self._started,
                       describe(fields))

    def _fail(self, msg, *args):
        log.error(msg, *args)
        self.failed_step = self.current
        self.failed = True
