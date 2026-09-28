"""What the App draws OVER the held frame: the HD message box and the
turn-time popups — work order 188 (open fixes 29 and 49).

**ONE HOME, OUT OF `main.py`** (decision 6, "split rather than add"): the
App asks `update()` once per frame — `core.handover.overlay_for` is the rule
— and while something is up the frame is HELD (no picture, no screen input)
and this draws it and routes clicks and keys to it. The box's drawing and
answers are `core/msgbox.py`'s, the popups' `core/turnpopup.py`'s; this
module holds what they share: which one is up, the once-only answer, the
galaxy map behind a popup.
"""
import logging

from core import handover, msgbox, turnpopup

log = logging.getLogger("orionlayer")


class Overlays:
    def __init__(self, app):
        self.app = app
        #: The box / popup that is up this frame, or None.
        self.box = None
        self.popup = None
        self.box_view = msgbox.View()
        self.popup_view = turnpopup.View()
        #: The last box answered: a second click before it has gone would
        #: land in whatever comes after it (decision 65's reasoning).
        self.box_sent = None
        self.box_labels = app.res.load_json(
            "assets/shared/msgbox/labels.json", {}) or {}
        self.popup_labels = app.res.load_json(
            "assets/shared/turnpopup/labels.json", {}) or {}

    # ── which one is up ───────────────────────────────────────────────
    def update(self):
        """Ask the rule; True while a box or a popup is up."""
        over = handover.overlay_for(self.app)
        self.box = over[1] if over and over[0] == "box" else None
        self.popup = over[1] if over and over[0] == "popup" else None
        if self.box is None:
            self.box_sent = None
        if self.popup is None:
            self.popup_view.sent = None
        return over is not None

    @property
    def active(self):
        return self.box is not None or self.popup is not None

    # ── drawing ───────────────────────────────────────────────────────
    def render(self, surface):
        """Draw what is up over the held surface; True if it drew."""
        app = self.app
        drew = False
        if self.box is not None:
            self.box_view.render(surface, app.style, self.box_labels,
                                 self.box)
            drew = True
        elif self.popup is not None:
            self.popup_view.render(surface, app.style, self.popup_labels,
                                   self.popup, app.client.state,
                                   backdrop=self._map_backdrop, app=app)
            drew = True
        if self.box is None:
            self.box_view.reset()
        if self.popup is None:
            self.popup_view.reset()
            self.popup_view.sent = None
        return drew

    def _map_backdrop(self, surface):
        """The galaxy map as its screen last drew it, behind a turn popup
        (the report phase runs over the map in the original)."""
        gm = self.app.dispatcher.screens.get("galaxy_map")
        if gm is not None and getattr(gm, "_state", None) is not None:
            surface.fill((4, 6, 14))
            gm.render(surface)

    # ── input ─────────────────────────────────────────────────────────
    def click(self, x, y):
        fields = self.app.client.state.fields
        if self.box is not None:
            self.answer_box(self.box_view.answer_at(self.box, fields, x, y))
        elif self.popup is not None:
            self.answer_popup(self.popup_view.action_at(x, y))

    def key(self, event):
        fields = self.app.client.state.fields
        if self.box is not None:
            self.answer_box(msgbox.View.answer_key(self.box, fields, event))
        elif self.popup is not None:
            self.answer_popup(turnpopup.key_action(self.popup_view,
                                                   self.popup, event))

    def answer_box(self, field):
        """The box's answer: its own field, activated — once per box."""
        box, app = self.box, self.app
        if box is None or field is None or not app.connected:
            return
        key = (box["kind"], box["title"], box["text"], box["field_a"])
        if key == self.box_sent:
            return
        self.box_sent = key
        log.info("message box: %s answered with field %d", box["kind"],
                 field.index)
        app.client.activate_field(field.index)

    def answer_popup(self, action):
        """A popup's answer through its own field: activated, or an injected
        click at the field's centre where the original reads the pointer —
        once per state of the popup (`turnpopup.state_key`), again after
        `turnpopup.RESEND_AFTER` unchanged snapshots."""
        app = self.app
        if self.popup is None or action is None or not app.connected:
            return
        key = turnpopup.state_key(self.popup)
        snap = app.client.stats.get("state", 0)
        sent = self.popup_view.sent
        if sent is not None and sent[0] == key and \
                snap - sent[1] < turnpopup.RESEND_AFTER:
            return
        self.popup_view.sent = (key, snap)
        how, field = action
        log.info("turn popup: %s -> %s field %d", self.popup["kind"], how,
                 field.index)
        if how == "click":
            app.client.inject_click((field.x + field.x_end) // 2,
                                    (field.y + field.y_end) // 2)
        else:
            app.client.activate_field(field.index)
