"""TOOL — what every presented frame came from. Work order 180, part A1.

**This is a TOOL and not a feature.** Data saw the game's own picture,
with a sentence on the left, flash up before an HD screen appeared. Work
order 166 A measured that once, for one screen, with a pixel comparison
inside one tool. This records the same question for EVERY frame the
window presents, on every screen, so a walk through all transitions can
count what the player saw rather than argue about it.

WHAT IS RECORDED, one entry per `pygame.display.flip()`:

    t        `time.monotonic()` when the frame was presented
    screen   the game's `current_screen` in the snapshot that frame used
    fields   how many fields that snapshot's list held
    source   "hd"   an HD screen drew it (`dispatcher.render`)
             "net"  the game's own picture (`original_view.render`)
             "fill" neither — the plain background fill
    kind     for "net", WHICH way in (see `main.App._showing_original`):
             "no_screen" decision 22's id HD has no screen for,
             "hand_over" a screen that knows the id said
             `wants_original()`, "f12" the player's own render mode
    hd       the HD screen on top (overlay first), or "" for none
    reason   the hand-over's sentence, or ""

The source is the BRANCH `App._render` took, which is the code that put
the pixels there. It is still a flag in the sense work order 129 warned
about, so `tools/flash_walk.py` also compares pixels inside the picture
area against the product's own rendering of the game's picture, the
166 A method, and reports where the two disagree.

OFF UNLESS ASKED, the `core/debuginput` rule and for its reason: an
environment variable is gone when the shell is, a setting can be saved
by accident. `ORIONLAYER_FRAME_TRACE` present turns it on; a value other
than `1` is also a file the entries are appended to as JSON lines. When
it is absent `open()` returns None and `App._render` pays one `is None`
test per frame — nothing is built, nothing is formatted.

AND IT SAYS SO, one line at startup, like the debug input channel.
"""
import collections
import json
import logging
import os
import time

log = logging.getLogger("frametrace")

#: The one switch — see the module docstring for why not a setting.
ENV = "ORIONLAYER_FRAME_TRACE"

HD, NET, FILL = "hd", "net", "fill"
SOURCES = (HD, NET, FILL)
#: The three ways into the game's picture (`App._showing_original`).
NO_SCREEN, HAND_OVER, F12 = "no_screen", "hand_over", "f12"

#: Entries kept in memory. A walk reads them back through the App; at
#: the ~60 frames a second the loop runs, this is over half an hour.
KEEP = 120_000


class FrameTrace:
    def __init__(self, path=None, keep=KEEP):
        self.frames = collections.deque(maxlen=keep)
        self.path = path
        self._fh = open(path, "a", encoding="utf-8") if path else None

    @classmethod
    def open(cls, environ=None):
        """A trace when the switch is set, else None (the normal case)."""
        env = os.environ if environ is None else environ
        if ENV not in env:
            return None
        value = env.get(ENV, "")
        path = value if value not in ("", "1") else None
        trace = cls(path)
        log.info("TOOL: frame trace ON (%s)",
                 path or "in memory only")
        return trace

    def record(self, *, screen, fields, source, kind="", hd="", reason=""):
        entry = {"t": time.monotonic(), "screen": screen, "fields": fields,
                 "source": source, "kind": kind, "hd": hd,
                 "reason": reason or ""}
        self.frames.append(entry)
        if self._fh is not None:
            self._fh.write(json.dumps(entry) + "\n")
        return entry

    def mark(self):
        """An index to read from later: `since(mark)`."""
        return len(self.frames)

    def since(self, mark):
        return list(self.frames)[mark:]

    def close(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def record_app_frame(app, shown):
    """One entry for the frame `App._render` is about to present.

    `shown` is the value `_render` itself branches on, so the entry names
    the code that draws the pixels: the game's picture, an HD screen, or
    the plain fill when neither is up.
    """
    state = app.client.state if app.connected else None
    dispatcher = app.dispatcher
    top = dispatcher.top
    if shown:
        source = NET
    elif dispatcher.active:
        source = HD
    else:
        source = FILL
    name = ((dispatcher.overlay_name or dispatcher.active_name)
            if top is not None else "")
    return app._frame_trace.record(
        screen=getattr(state, "current_screen", None),
        fields=len(getattr(state, "fields", None) or []),
        source=source, kind=app._net_kind if shown else "",
        hd=name, reason=app._fallback_note or "")


def summarise(frames, target=None):
    """A transition's frames as the numbers the walk reports.

    A transition starts on the OLD screen, which is HD too, so "the
    first HD frame" is the first frame the TARGET screen drew (`hd ==
    target`); with no target, any HD frame. `native_before_hd` counts the
    "net" frames presented before it and `native_seconds` how long they
    stood — from the first of them to the frame that replaced the last.
    `native_total` counts every "net" frame of the stretch, before or
    after, so a flash AFTER the screen appeared is not lost either.
    """
    def is_target(f):
        return f["source"] == HD and (target is None or f["hd"] == target)
    first_hd = next((i for i, f in enumerate(frames) if is_target(f)), None)
    head = frames if first_hd is None else frames[:first_hd]
    native = [i for i, f in enumerate(head) if f["source"] == NET]
    seconds = 0.0
    if native:
        end = native[-1] + 1
        t_end = frames[end]["t"] if end < len(frames) else frames[-1]["t"]
        seconds = t_end - frames[native[0]]["t"]
    return {
        "frames": len(frames),
        "first_hd_frame": first_hd,
        "native_before_hd": len(native),
        "native_seconds": round(seconds, 3),
        "native_total": sum(1 for f in frames if f["source"] == NET),
        "kinds": sorted({f["kind"] for f in frames if f["source"] == NET}),
        "reasons": sorted({f["reason"] for f in frames
                           if f["source"] == NET and f["reason"]}),
        "screens": sorted({f["screen"] for f in frames
                           if f["screen"] is not None}),
    }
