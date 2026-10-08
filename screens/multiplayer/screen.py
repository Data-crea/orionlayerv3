"""Multiplayer (wire ids 15, 16, 17, 21, 22, 37, 41) — work order 188, Part 7.

What orion2re offers behind the main menu's MULTIPLAYER is read in
`dev:doc/multiplayer_reading.md`: a setup (15) with three types — NETWORK (LAN,
orion2re's own router on port 47800), ONLINE (a direct endpoint; the
original's MODEM, whose art the engine still shows) and HOTSEAT (one engine,
players taking turns) — START NEW GAME, LOAD GAME, JOIN GAME, COMM INFO
(the Online endpoint) and CANCEL; then, per type, the hotseat setup (16) and
player switch (17), hosting (21) and joining (22) a network game with its
waiting steps, loading a multiplayer game (41), and between network turns
(37). Nothing multiplayer-specific was on the wire; the setup reads its
state off its own field list (`mpsetup`), every other step needs open fix
51's "MPLY" block (`mpwire`) and is claimed only with it.

**WHAT IT SENDS**: each button's own field, found in the live list by its
hotkey (`mpsetup.BUTTONS`), activated; the Online endpoint typed in HD and
sent the save dialog's way (an injected click on the input, Backspaces as
long as the engine's text, the keys one per tick, Enter).

Marks (`layout.json`): DEVIATION `hud_panels` (HUD panels and the universal
background instead of MULTIGM.LBX's pictures), DEVIATION `online_word` (the
radio the original's art calls MODEM and the dialog MODEM CONNECT are named
by what orion2re does with them: ONLINE, its endpoint).
"""
import logging

import pygame

from core.hud import blocks as hud
from core.hud import shell
from core.hud import text as hudtext
from core.injection import InjectionChain, name_keys, paced_keys
from core.screen_base import ScreenBase
from core.widgets.text_input import TextInput

from . import mpsetup

log = logging.getLogger("multiplayer")

REF_BUTTON = (330, 60)
REF_GAP = 18


class MultiplayerScreen(ScreenBase):
    SCREEN_NAME = "multiplayer"
    GAME_SCREEN_ID = 15
    EXTRA_SCREEN_IDS = (16, 17, 21, 22, 37, 41)
    USE_FRAME = False
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._data = {}
        self._rects = {}
        self._endpoint = None        # HD's text field in COMM INFO
        self._chain = None
        # THE SHELL on the setup (work order 225): its title on the plate,
        # its panel in the content rectangle, CANCEL the closing action.
        # COMM INFO and the steps after the setup are dialogs (the turn
        # popups' panel) and keep their geometry.
        self.shell = shell.Shell(
            title=lambda: self.words("setup_title"), row=True,
            buttons=[("cancel", lambda: self.words("cancel"), "action")],
            visible=lambda key: self._setup_up(),
            enabled=lambda key: self._setup_field(key) is not None)

    def _setup_up(self):
        st = self._state
        return getattr(st, "current_screen", None) == 15 and \
            mpsetup.classify(getattr(st, "fields", None)) == mpsetup.SETUP

    def _setup_field(self, key):
        return mpsetup.buttons(getattr(self._state, "fields", None)).get(key)

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/multiplayer/layout.json", {}) or {}
        self._endpoint = None
        self._chain = None

    # ── the dispatcher's questions ─────────────────────────────────────
    def claims(self, game_state):
        sid = getattr(game_state, "current_screen", None)
        from . import mpwire
        if mpwire.claims(game_state):
            return True        # MPLY: a step is up, whatever the id says
        if sid == 15:
            return mpsetup.classify(getattr(game_state, "fields", None)) \
                is not None
        from . import mpwire
        return mpwire.claims(game_state)

    def wants_original(self):
        return False

    def update(self, game_state=None):
        if game_state is not None:
            self._state = game_state
        if self._chain is not None:
            self._chain.update(game_state)
            if self._chain.done or self._chain.failed:
                self._chain = None

    def words(self, key):
        return (self._data.get("words") or {}).get(key) or key.upper()

    # ── drawing ────────────────────────────────────────────────────────
    def render(self, surface):
        self._render_background(surface)
        self._rects = {}
        self._slanted = set()      # keys hit as their parallelogram
        st = self._state
        fields = getattr(st, "fields", None)
        sid = getattr(st, "current_screen", None)
        if sid == 15 and mpsetup.classify(fields) == mpsetup.SETUP:
            self._draw_setup(surface, fields)
            self.render_shell(surface)
        elif sid == 15 and mpsetup.classify(fields) == mpsetup.COMM:
            self._draw_comm(surface, fields)
        else:
            from . import mpdraw
            self._rects = mpdraw.draw_step(surface, self, st) or {}

    def _button(self, surface, key, rect, field, lit=False, kind="action"):
        s = self.layout.scale
        # THE CHOSEN TYPE IS THE BUTTON'S "active" STATE (work order 208
        # B1, Data's decision 3: one "on" marking everywhere, decision 71's
        # vocabulary) — it was a lit panel behind the button.
        state = ("disabled" if field is None else
                 "active" if lit else "normal")
        if kind == "toggle":
            # A TYPE is a toggle inside the panel: rectangular, "selected"
            # while chosen (work order 225, decisions 88 and 92).
            hud.small_button(surface, rect, s, state, self.words(key),
                             style_renderer=self.style)
        elif kind == "slant":
            # An action of the screen: slanted (decision 87).
            hud.slant_button(surface, rect, s, state, self.words(key),
                             style_renderer=self.style)
        else:
            hud.action_button(surface, rect, s, state, self.words(key),
                              style_renderer=self.style)
        if field is not None:
            self._rects[key] = (rect, field)
            if kind == "slant":
                self._slanted.add(key)

    def _panel(self, surface, title, w_ref, h_ref):
        win_w, win_h = surface.get_size()
        s = win_h / 1080
        top = hud.title_plate(surface, win_w // 2, int(40 * s), s,
                              title, self.style).bottom
        panel = pygame.Rect(0, 0, int(w_ref * s), int(h_ref * s))
        panel.midtop = (win_w // 2, top + int(40 * s))
        hud.panel(surface, panel, s)
        return panel, s

    def _draw_setup(self, surface, fields):
        """The setup in the shell (work order 225): one panel (the
        `setup_panel` box) in the content rectangle, the three types on the
        left as toggles, the four actions on the right, each column centred
        in its half of the panel; CANCEL is the shell's closing action."""
        L = self.ref_layout
        s = L.scale
        panel = self.box_screen_rect("setup_panel") or shell.panels(L, True)
        hud.panel(surface, panel, s)
        btns = mpsetup.buttons(fields)
        chosen = mpsetup.selected(fields)
        bw, bh = int(REF_BUTTON[0] * s), int(REF_BUTTON[1] * s)
        gap = int(REF_GAP * s)
        halves = shell.split(shell.inner(panel, L), L, [1.0, 1.0])
        y = panel.y + int(50 * s)
        for half, keys, kind in ((halves[0], ("network", "online", "hotseat"),
                                  "toggle"),
                                 (halves[1], ("start", "load", "join",
                                              "comm"), "slant")):
            x = half.centerx - bw // 2
            for i, key in enumerate(keys):
                r = pygame.Rect(x, y + i * (bh + gap), bw, bh)
                self._button(surface, key, r, btns.get(key),
                             lit=key == chosen, kind=kind)

    def _draw_comm(self, surface, fields):
        panel, s = self._panel(surface, self.words("comm_title"), 900, 330)
        inp, cancel, accept = mpsetup.comm_fields(fields)
        from . import mpwire
        engine_text = mpwire.endpoint(self._state)
        label = self.style.render_text(self.words("endpoint"),
                                       max(10, int(28 * s)),
                                       hudtext.colour("label")[:3])
        surface.blit(label, (panel.x + int(50 * s), panel.y + int(50 * s)))
        box = pygame.Rect(panel.x + int(50 * s), panel.y + int(100 * s),
                          panel.w - int(100 * s), int(64 * s))
        hud.panel(surface, box, s, lit=self._endpoint is not None,
                  dense=True)
        text = self._endpoint.value if self._endpoint is not None else \
            (engine_text or "")
        t = self.style.render_text(text, max(10, int(30 * s)),
                                   hudtext.colour("value")[:3])
        surface.blit(t, (box.x + int(16 * s),
                         box.centery - t.get_height() // 2))
        if inp is not None:
            self._rects["endpoint"] = (box, inp)
        bw, bh = int(REF_BUTTON[0] * s * 0.8), int(REF_BUTTON[1] * s)
        for key, f, cx in (("cancel", cancel, panel.x + panel.w // 4),
                           ("accept", accept, panel.x + 3 * panel.w // 4)):
            r = pygame.Rect(0, 0, bw, bh)
            r.midbottom = (cx, panel.bottom - int(30 * s))
            self._button(surface, key, r, f)

    # ── input ──────────────────────────────────────────────────────────
    def _send(self, field, why):
        if field is not None and self.app.connected and self._chain is None:
            log.info("multiplayer: %s -> field %d", why, field.index)
            self.app.client.activate_field(field.index)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        if self.shell_click(screen_x, screen_y) == "cancel":
            self._endpoint = None
            self._send(self._setup_field("cancel"), "cancel")
            return None
        for key, (rect, field) in list(self._rects.items()):
            hit = (hud.slant_hit(rect, screen_x, screen_y)
                   if key in getattr(self, "_slanted", ()) else
                   rect.collidepoint(screen_x, screen_y))
            if hit:
                if key == "endpoint":
                    self._open_endpoint()
                elif key == "chat":
                    self._open_chat(field)
                elif key == "accept" and self._endpoint is not None:
                    self._commit_endpoint(then=field)
                else:
                    if key == "cancel":
                        self._endpoint = None
                    self._send(field, key)
                return None
        return None

    def _open_endpoint(self):
        from . import mpwire
        engine_text = mpwire.endpoint(self._state) or ""
        limit = mpwire.endpoint_max(self._state) or 30
        self._endpoint = TextInput(
            value=engine_text[:limit], max_len=limit,
            allowed=lambda c: 0x20 < ord(c) < 0x7F and c != "_",
            on_submit=lambda v: self._commit_endpoint(),
            on_cancel=self._cancel_endpoint)

    def _open_chat(self, field):
        """The chat line typed in HD, sent on Enter the save dialog's way:
        a click on the engine's chat input, the keys, Enter (the input was
        empty — `Chat_Box_Input_Loop_` clears it after each send). At most
        59 characters: the engine's chat buffer is 60 bytes although its
        input allows 80 (open fix 51's reading, finding 1)."""
        index = field.index

        def send(value):
            self._endpoint = None
            keys = name_keys(value.strip(), clear=0)

            def is_turn(fields):
                return any(getattr(f, "index", 0) == index
                           for f in fields or [])

            def run(client, fields):
                f = next(f for f in fields if f.index == index)
                x, y = (f.x + f.x_end) // 2, (f.y + f.y_end) // 2
                return paced_keys(lambda c: c.inject_click(x, y), keys)
            if self.app.connected and value.strip():
                self._chain = InjectionChain(self.app.client, [
                    ("chat", is_turn, run, 10.0)])
        self._endpoint = TextInput(value="", max_len=59,
                                   on_submit=send,
                                   on_cancel=self._cancel_endpoint)

    def _cancel_endpoint(self):
        self._endpoint = None

    def _commit_endpoint(self, then=None):
        """The typed endpoint, the save dialog's way: an injected click on
        the engine's input, as many Backspaces as the engine's text has,
        the keys one per tick, Enter — then ACCEPT's field if given."""
        from . import mpwire
        value = self._endpoint.value.strip()
        old = mpwire.endpoint(self._state)
        clear = len(old) if old is not None else 30
        keys = name_keys(value, clear=clear)
        self._endpoint = None

        def is_dialog(fields):
            return mpsetup.classify(fields) == mpsetup.COMM

        accept_index = then.index if then is not None else None

        def run(client, fields):
            inp = mpsetup.comm_fields(fields)[0]
            x, y = (inp.x + inp.x_end) // 2, (inp.y + inp.y_end) // 2
            log.info("multiplayer: endpoint %r — click (%d, %d), %d keys%s",
                     value, x, y, len(keys),
                     ", then ACCEPT" if accept_index else "")
            sends = paced_keys(lambda c: c.inject_click(x, y), keys)
            if accept_index is not None:
                # ONE paced list: ACCEPT's activation a tick after Enter —
                # a second chain step would wait for a list change the
                # dialog never makes (its fields stay the same)
                sends.append(lambda c: c.activate_field(accept_index))
            return sends
        if self.app.connected:
            self._chain = InjectionChain(self.app.client, [
                ("endpoint", is_dialog, run, 10.0)])

    def handle_key_event(self, event):
        if self._endpoint is not None:
            return self._endpoint.handle_key_event(event)
        if event.key == pygame.K_ESCAPE:
            f = next((f for k, (r, f) in self._rects.items()
                      if k == "cancel"), None)
            self._send(f, "ESC")
        return True
