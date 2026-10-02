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

from core import handover, msgbox, rightinfo, turnpopup

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
                                 self.box, backdrop=self.box_backdrop)
            drew = True
        elif self.popup is not None:
            self.popup_view.render(surface, app.style, self.popup_labels,
                                   self.popup, app.client.state,
                                   backdrop=self.backdrop, app=app)
            drew = True
        if self.box is None:
            self.box_view.reset()
        if self.popup is None:
            self.popup_view.reset()
            self.popup_view.sent = None
        host = self.help_host()
        if host is not None and host.help.visible:
            if self.popup is None:
                host.help.close()     # its popup has gone
            else:
                host.render_help(surface)
        return drew

    def help_host(self):
        """The screen whose help popup a popup's right click opens (the
        galaxy map's: one help popup, its look and texts)."""
        return self.app.dispatcher.screens.get("galaxy_map")

    def box_backdrop(self, surface):
        """A box over a turn popup stands over the popup, as the original
        draws it (a planet's colony info over the discovery, a skill's help
        over a leader offer — work order 200 B); otherwise `backdrop`."""
        popup = handover.popup_under_box(self.app)
        if popup is None:
            return self.backdrop(surface)
        self.popup_view.render(surface, self.app.style, self.popup_labels,
                               popup, self.app.client.state,
                               backdrop=self.backdrop, app=self.app)
        return True

    def backdrop(self, surface):
        """THE SCREEN THAT IS OPEN, drawn behind the box or popup — True if
        it drew, False to leave the held frame (work order 196 A).

        Data saw every turn-time popup and the boxes after it on a black
        screen: the popups asked for the galaxy map, which the dispatcher
        had EXITED for the turn (its boxes dropped, so it drew only its
        floor and title), and a box stood on whatever frame was held — that
        black base, or the frame before a screen that had just come up (the
        new colony's, behind "just colonized"). The original draws each box
        over the screen it opened on; the report phase's popups over the
        map (mainscr2.cpp, `Reports_Screen_`). So:

          an HD overlay is up (the GAME menu)   the held frame: the popup's
                                                own picture under its
                                                confirmation (gmdraw)
          an HD screen claims the game's id     that screen's page
          none does, in a game                  the galaxy map, as it last
                                                drew it
          none does, before a game              the held frame
        """
        d = self.app.dispatcher
        if d.overlay is not None:
            return False
        top = d.active
        # a screen whose data is there and whose list a box replaced
        # (`modal_is_box`) has a page to stand behind it; one that cannot
        # vouch for its data has none
        if top is None or not top.draws_this_frame() or (
                top.wants_original() and not top.modal_is_box()):
            top = d.screens.get("galaxy_map")
            if top is None or not same_game(getattr(top, "_state", None),
                                            self.app.client.state):
                return False
        surface.fill((4, 6, 14))
        top.render_backdrop(surface)
        return True

    # ── input ─────────────────────────────────────────────────────────
    def right(self, down, x, y):
        """A right click on what is up (work order 200 B): a text or message
        box closes, as any input closes it (textbox.cpp:148-152,
        gendraw.cpp:147-154; a confirmation reads only its two buttons,
        :215-223); a popup answers as `turnpopup.View.right_at` says."""
        if not down or not self.active:
            return
        host = self.help_host()
        if host is not None and host.help.visible:
            host.help.close()
            return
        fields = self.app.client.state.fields
        if self.box is not None:
            if self.box["kind"] != "confirmation":
                self.answer_box(dict(msgbox.answers(self.box, fields))
                                .get("close"))
        elif self.popup is not None:
            got = self.popup_view.right_at(x, y)
            if got is None:
                return
            if host is None:
                return
            if got[0] == "help":
                rightinfo.opener(host)(got[1])
            elif got[0] == "field":
                rightinfo.send(self.app, got[1], f"{self.popup['kind']} item",
                               rightinfo.opener(host))

    def click(self, x, y):
        host = self.help_host()
        if host is not None and host.help.visible:
            host.help.close()         # the help over a popup takes the click
            return
        fields = self.app.client.state.fields
        if self.box is not None:
            self.answer_box(self.box_view.answer_at(self.box, fields, x, y))
        elif self.popup is not None:
            self.answer_popup(self.popup_view.action_at(x, y))

    def key(self, event):
        host = self.help_host()
        if host is not None and host.help.visible:
            host.help.close()
            return
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


def same_game(map_state, state):
    """True when the galaxy map's last snapshot is of the game running now:
    the same galaxy and player, at most one turn behind (the report phase
    runs after the stardate moved). A finished game's map must not stand
    behind a box before the next game (work order 196 A)."""
    if map_state is None or state is None:
        return False
    return (getattr(map_state, "num_stars", -1) == getattr(state, "num_stars", -2)
            and getattr(map_state, "player_num", -1) == getattr(state, "player_num", -2)
            and 0 <= getattr(state, "stardate", 0) - getattr(map_state, "stardate", 0) <= 1)
