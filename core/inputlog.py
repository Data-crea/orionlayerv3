"""Every click and key the HD client receives, and what became of it —
work order 182, part 3. A TOOL, off in normal play.

Work order 181 lost one Cancel click in the build popup at 3840, in a
frame where the engine had sent an empty field list, and could not say
why: nothing recorded what the client did with an input. This does, for
every left click and key press `main.App` receives:

    t, screen    monotonic time and the game's screen id at that moment
    fields       the live field list's length at that moment
    top          the HD screen on top, and its view's state if it has one
    outcome      "sent" — a message went to the engine while the input was
                 handled (the message ids are listed) — or "dropped"
    reason       why it was dropped: "editor" (F5 editor), "hold" (the
                 hand-over gate of 180 A2 holds the frame), "net" (the
                 game's picture is up and nothing was forwarded), "app key"
                 (F5, F8, F9, F11, F12), "not connected", or "screen sent
                 nothing" — the screen took it and chose to send nothing
                 (no field under the cursor, a separator, a WAITING view,
                 an empty field list: `fields` and `view` say which)

Switched on like the frame trace: `ORIONLAYER_INPUT_LOG` set (`1` keeps
it in memory, any other value is a JSON-lines file). Unset, `open`
returns None and `main.App` never calls in — it costs nothing.
"""
import json
import logging
import os
import time

import pygame

log = logging.getLogger("inputlog")

ENV = "ORIONLAYER_INPUT_LOG"
APP_KEYS = (pygame.K_F5, pygame.K_F8, pygame.K_F9, pygame.K_F11, pygame.K_F12)


class InputLog:
    def __init__(self, client, path=None):
        self.entries = []
        self.path = path
        self._fh = open(path, "a", encoding="utf-8") if path else None
        self._sent = []
        self._pending = None
        real = client._send_message

        def counted(msg_type, payload):
            self._sent.append(msg_type)
            return real(msg_type, payload)
        client._send_message = counted

    @classmethod
    def open(cls, client, environ=None):
        env = os.environ if environ is None else environ
        if ENV not in env:
            return None
        value = env.get(ENV, "")
        path = value if value not in ("", "1") else None
        log.info("TOOL: input log ON (%s)", path or "in memory only")
        return cls(client, path)

    def begin(self, app, event):
        """Before `main.App` handles a left click or a key press."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            what = {"kind": "click", "pos": list(event.pos)}
        elif event.type == pygame.KEYDOWN:
            what = {"kind": "key", "key": int(event.key)}
        else:
            self._pending = None
            return
        state = getattr(app.client, "state", None)
        d = app.dispatcher
        top = d.overlay_name or d.active_name or ""
        view = getattr(getattr(d, "top", None), "_view", None)
        self._pending = dict(
            what, t=round(time.monotonic(), 4),
            screen=getattr(state, "current_screen", None),
            fields=len(getattr(state, "fields", None) or []),
            top=top, view=getattr(view, "state", None),
            editor=bool(app.editor.active),
            hold=bool(app._handover.holding),
            net=bool(app._showing_original()),
            connected=bool(app.connected), sent_before=len(self._sent))

    def end(self):
        """After it was handled: the outcome, and the reason for a drop."""
        p, self._pending = self._pending, None
        if p is None:
            return None
        sent = self._sent[p.pop("sent_before"):]
        if sent:
            outcome, reason = "sent", ""
        elif p["kind"] == "key" and p["key"] in APP_KEYS:
            outcome, reason = "dropped", "app key"
        elif p["editor"]:
            outcome, reason = "dropped", "editor"
        elif not p["connected"]:
            outcome, reason = "dropped", "not connected"
        elif p["net"]:
            outcome, reason = "dropped", "net"
        elif p["hold"]:
            outcome, reason = "dropped", "hold"
        else:
            outcome, reason = "dropped", "screen sent nothing"
        entry = dict(p, outcome=outcome, reason=reason, messages=sent)
        self.entries.append(entry)
        if self._fh is not None:
            self._fh.write(json.dumps(entry) + "\n")
            self._fh.flush()
        return entry

    def close(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None
