"""TOOL — where the time goes when the research screen opens. Work order 184.

**This is a TOOL and not a feature.** Data finds that opening the research
screen takes noticeably long. Work order 184 measures first and optimises
second, and this is the measuring half: for every entry into a research
screen it records the path from the player's input to the first HD frame
of that screen, split into the order's five phases.

THE FIVE PHASES, as timestamps on one entry (all `time.perf_counter()`):

    t0  the frame that handled the player's input began (`_handle_events`)
    t1  the input's message left for the engine (`_send_message` returned)
    t2  the first snapshot whose screen is the research screen's id was
        parsed (`_handle_message`, inside `client.poll`)
    t3  the frame on which the screen first said `READY` polled — i.e. the
        snapshot carrying the field list it validates against was parsed
    t4  that frame's `pygame.display.flip()` returned, with the panel drawn

    (a) t1 - t0   the input to the wire
    (b) t2 - t1   the engine switching screens, up to its first snapshot
                  with the research id (includes the wait for the MAP's own
                  next input loop, which is where the engine reads input)
    (c) t3 - t2   the wait for the data the panel needs: the snapshots the
                  screen spent `WAITING` (work order 166 A) for the game's
                  field list; the count and the snapshot rate are recorded
    (d) the HD side's own preparation: every call into the research
        screen's `enter` / `update` / `render` / `on_resize` during
        the entry, timed separately, first entry and later ones apart —
        and `d_ready`, t3 to the start of the frame's render, which is the
        part of it that stands between the data and the picture
    (e) the drawing of the first frame: the whole `_render` of the frame at
        t3, flip included

(a)+(b)+(c)+d_ready+(e) = t4 - t0: the phases are consecutive by
construction. The research screen's `enter` runs inside (c) — the
dispatcher opens the overlay on the first snapshot at its id, while the
list is still missing — so it is reported in (d) and NOT added again.

WHAT IT CANNOT SEE, said so the numbers are not read as more than they
are: the time a click waits in SDL's queue before the frame that handles
it (at most one frame, 1/60 s in `main.App.run`), and the time a snapshot
waits in the socket before the next `poll` (the same bound). pygame 2
carries no event timestamp and the socket none either.

THE ENGINE'S OWN PICTURE, for the floor (order part 1.4): every visual
message's arrival time and a digest of its framebuffer are kept for the
entry, so a tool can say at which snapshot the engine's native panel was
complete on the wire — the earliest any client could show it.

OFF UNLESS ASKED, the `core/frametrace` rule and for its reason.
`ORIONLAYER_ENTRY_TIMING` present turns it on (`1` keeps the entries in
memory, any other value is a JSON-lines file they are appended to);
`ORIONLAYER_ENTRY_PROFILE=<dir>` also runs `cProfile` around phase (d) and
writes one profile for the first entry and one for all later ones. Unset,
`open` returns None, nothing is wrapped, and `main.App` pays nothing at
all: the hooks are installed by WRAPPING the app's own methods on the
instance, so no line of the product's loop tests for this tool.
"""
import cProfile
import hashlib
import json
import logging
import os
import pstats
import time

from core.wire_protocol import MSG_FIELDS, MSG_STATE, MSG_VISUAL

log = logging.getLogger("entrytiming")

#: The switches — see the module docstring for why not a setting.
ENV = "ORIONLAYER_ENTRY_TIMING"
PROFILE_ENV = "ORIONLAYER_ENTRY_PROFILE"

#: The screens an entry is measured into, by HD name, and the wire id
#: each one claims. Read off the registered screens at install time, so
#: this names the two research modes and not their numbers.
TARGETS = ("research_change", "research_select")

#: The research screen's own methods that make up phase (d).
PREP_METHODS = ("enter", "update", "render", "on_resize")

#: How many snapshots after t2 an entry may stand without its screen
#: becoming READY before it is recorded as not reached. A bound, not a
#: timer (decision 21): the entry ends when the screen is drawn.
GIVE_UP_SNAPSHOTS = 200


def _now():
    return time.perf_counter()


class EntryTiming:
    def __init__(self, app, path=None, profile_dir=None):
        self.app = app
        self.entries = []
        self.path = path
        self._fh = open(path, "a", encoding="utf-8") if path else None
        self.profile_dir = profile_dir
        self._profiles = {}            # "first" / "later" -> cProfile
        self._entered = set()          # targets entered since start
        self._entry = None             # the entry being measured
        self._pending = None           # a send not yet followed by a switch
        self._events_t0 = None         # this frame's _handle_events start
        self._in_events = False
        self._frame_poll_t = None      # this frame's _update start
        self._depth = 0                # nesting of wrapped prep calls
        self._ids = {}                 # wire id -> target name
        self.snapshots = 0             # state messages seen, ever

    # ── switching on ──────────────────────────────────────

    @classmethod
    def open(cls, app, environ=None):
        """A timer installed on `app` when the switch is set, else None."""
        env = os.environ if environ is None else environ
        if ENV not in env:
            return None
        value = env.get(ENV, "")
        path = value if value not in ("", "1") else None
        timing = cls(app, path, env.get(PROFILE_ENV) or None)
        timing.install()
        log.info("TOOL: research entry timing ON (%s%s)",
                 path or "in memory only",
                 f", cProfile to {timing.profile_dir}"
                 if timing.profile_dir else "")
        return timing

    def install(self):
        app = self.app
        self._wrap(app, "_handle_events", self._around_events)
        self._wrap(app, "_update", self._around_update)
        self._wrap(app, "_render", self._around_render)
        self._wrap(app.client, "_send_message", self._around_send)
        self._wrap(app.client, "_handle_message", self._around_message)
        for name in TARGETS:
            screen = app.dispatcher.screens.get(name)
            if screen is None:
                continue
            sid = getattr(screen, "GAME_SCREEN_ID", None)
            if sid is not None:
                self._ids[sid] = name
            for method in PREP_METHODS:
                if hasattr(screen, method):
                    self._wrap_prep(screen, name, method)

    @staticmethod
    def _wrap(obj, name, around):
        real = getattr(obj, name)

        def wrapped(*args, **kwargs):
            return around(real, *args, **kwargs)
        setattr(obj, name, wrapped)

    def _wrap_prep(self, screen, target, method):
        real = getattr(screen, method)

        def wrapped(*args, **kwargs):
            return self._prep(target, method, real, *args, **kwargs)
        setattr(screen, method, wrapped)

    # ── the hooks ─────────────────────────────────────────

    def _around_events(self, real):
        self._events_t0 = _now()
        self._in_events = True
        try:
            return real()
        finally:
            self._in_events = False

    def _around_send(self, real, msg_type, payload=b""):
        result = real(msg_type, payload)
        if self._entry is None:
            t1 = _now()
            self._pending = {
                "t0": self._events_t0 if self._in_events else t1,
                "t1": t1, "msg": msg_type,
                "from": self._top_name(),
                "snap": self.snapshots,
                "by_input": self._in_events,
            }
        return result

    def _around_message(self, real, msg_type, flags, payload):
        result = real(msg_type, flags, payload)
        t = _now()
        state = self.app.client.state
        e = self._entry
        if msg_type == MSG_STATE:
            self.snapshots += 1
            sid = getattr(state, "current_screen", None)
            if e is None and sid in self._ids:
                self._start(sid, t)
            elif e is not None and not e.get("done"):
                e["snaps"].append((t, sid))
                if sid != e["screen"]:
                    self._finish(reached=False, why=f"left for {sid}")
        elif e is not None and not e.get("done"):
            if msg_type == MSG_FIELDS:
                e["fields"].append(
                    (t, len(getattr(state, "fields", None) or [])))
            elif msg_type == MSG_VISUAL:
                fb = getattr(state, "framebuffer", None) or b""
                e["visuals"].append(
                    (t, hashlib.blake2b(bytes(fb), digest_size=8)
                     .hexdigest()))
        return result

    def _around_update(self, real):
        self._frame_poll_t = _now()
        result = real()
        e = self._entry
        if e is not None and not e.get("done") and "t3" not in e:
            screen = self.app.dispatcher.screens.get(e["target"])
            if getattr(screen, "state", None) == getattr(
                    screen, "READY_STATE", "ok"):
                # THE LIST THAT MADE IT VALID is the last one parsed
                # before this frame's update; its arrival is t3 when the
                # frame parsed it, which is this frame's poll.
                last = e["fields"][-1][0] if e["fields"] else None
                e["t3"] = last if last is not None else self._frame_poll_t
                e["t3_poll"] = self._frame_poll_t
                e["t3_update_end"] = _now()
                e["snaps_c"] = sum(1 for t, _s in e["snaps"]
                                   if t <= e["t3"])
            elif len(e["snaps"]) > GIVE_UP_SNAPSHOTS:
                self._finish(reached=False, why="never READY")
        return result

    def _around_render(self, real):
        e = self._entry
        armed = e is not None and "t3" in e and not e.get("done")
        r0 = _now()
        result = real()
        if armed:
            r1 = _now()
            app = self.app
            gate = getattr(app, "_handover", None)
            drew = (self._top_name() == e["target"]
                    and not (gate is not None and gate.holding)
                    and getattr(app, "_surface_hd", False))
            if drew:
                e["t4"], e["render_start"] = r1, r0
                self._finish(reached=True)
        return result

    def _prep(self, target, method, real, *args, **kwargs):
        e = self._entry
        measuring = (e is not None and not e.get("done")
                     and e["target"] == target and self._depth == 0)
        if not measuring:
            self._depth += 1
            try:
                return real(*args, **kwargs)
            finally:
                self._depth -= 1
        prof = self._profile_for(e) if self.profile_dir else None
        self._depth += 1
        t = _now()
        if prof is not None:
            prof.enable()
        try:
            return real(*args, **kwargs)
        finally:
            if prof is not None:
                prof.disable()
            dt = _now() - t
            self._depth -= 1
            e["prep"].setdefault(method, []).append(round(dt * 1000, 3))

    # ── an entry ──────────────────────────────────────────

    def _start(self, sid, t2):
        target = self._ids[sid]
        pending = self._pending
        self._pending = None
        self._entry = {
            "target": target, "screen": sid,
            "first_after_start": target not in self._entered,
            "t2": t2, "snaps": [(t2, sid)], "fields": [], "visuals": [],
            "prep": {}, "send": pending,
            "snaps_b": (self.snapshots - 1 - pending["snap"])
            if pending else None,
            "size": [self.app.win_w, self.app.win_h],
        }
        self._entered.add(target)

    def _finish(self, reached, why=""):
        e = self._entry
        e["done"] = True
        self._entry = None
        rec = self.summary(e, reached, why)
        self.entries.append(rec)
        if self._fh is not None:
            self._fh.write(json.dumps(rec) + "\n")
            self._fh.flush()
        log.info("entry timing: %s %s %s", rec["target"],
                 "first" if rec["first_after_start"] else "later",
                 json.dumps({k: rec[k] for k in
                             ("total_ms", "a_ms", "b_ms", "c_ms", "d_ms",
                              "d_ready_ms", "e_ms", "snaps_c")
                             if k in rec}))

    @staticmethod
    def summary(e, reached, why=""):
        """One entry as milliseconds per phase, plus what they rest on."""
        ms = lambda a, b: round((b - a) * 1000, 2)  # noqa: E731
        send = e["send"]
        rec = {"target": e["target"], "screen": e["screen"],
               "first_after_start": e["first_after_start"],
               "reached": reached, "why": why, "size": e["size"],
               "by_input": bool(send and send["by_input"]),
               "from": send["from"] if send else None,
               "snaps_b": e["snaps_b"], "prep": e["prep"],
               "d_ms": round(sum(sum(v) for v in e["prep"].values()), 2)}
        t2 = e["t2"]
        if send:
            rec["a_ms"] = ms(send["t0"], send["t1"])
            rec["b_ms"] = ms(send["t1"], t2)
        if "t3" in e:
            rec["c_ms"] = ms(t2, e["t3"])
            rec["snaps_c"] = e["snaps_c"]
            span = e["t3"] - t2
            rec["snap_rate"] = (round((e["snaps_c"] - 1) / span, 2)
                                if span > 0 and e["snaps_c"] > 1 else None)
        if reached:
            rec["d_ready_ms"] = ms(e["t3"], e["render_start"])
            rec["e_ms"] = ms(e["render_start"], e["t4"])
            rec["total_ms"] = ms(send["t0"] if send else t2, e["t4"])
        rec["fields"] = [(ms(t2, t), n) for t, n in e["fields"]]
        rec["visuals"] = [(ms(t2, t), h) for t, h in e["visuals"]]
        rec["snaps"] = [(ms(t2, t), s) for t, s in e["snaps"]]
        return rec

    # ── helpers ───────────────────────────────────────────

    def _top_name(self):
        d = self.app.dispatcher
        return (d.overlay_name or d.active_name) if d.top is not None else ""

    def _profile_for(self, e):
        key = "first" if e["first_after_start"] else "later"
        prof = self._profiles.get(key)
        if prof is None:
            prof = self._profiles[key] = cProfile.Profile()
        return prof

    def dump_profiles(self, top=10):
        """Write each profile and return its `top` calls by own time."""
        out = {}
        if not self.profile_dir:
            return out
        os.makedirs(self.profile_dir, exist_ok=True)
        for key, prof in self._profiles.items():
            path = os.path.join(self.profile_dir, f"research_{key}.prof")
            prof.dump_stats(path)
            stats = pstats.Stats(prof)
            rows = []
            for (file, line, func), (cc, nc, tt, ct, _callers) in \
                    stats.stats.items():
                rows.append({"call": f"{os.path.relpath(file) if os.path.isabs(file) else file}:{line}({func})",
                             "calls": nc, "own_ms": round(tt * 1000, 3),
                             "cum_ms": round(ct * 1000, 3)})
            rows.sort(key=lambda r: r["own_ms"], reverse=True)
            out[key] = {"path": path, "top_own": rows[:top],
                        "top_cum": sorted(rows, key=lambda r: r["cum_ms"],
                                          reverse=True)[:top]}
        return out

    def close(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None
