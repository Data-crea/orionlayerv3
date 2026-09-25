"""GAME menu — the HD overlay for `LOADSAVE::_Game_Popup_` (SCREEN_GAME, 8).

The tree Stop 1 read (doc/game_menu_reading.md): the menu, Settings,
Load, Save, the NEW/QUIT confirmation and the slot warning. Decision 59:
one OVERLAY claims screen id 8, so the dispatcher opens it over the
galaxy map and the native popup never shows; which dialog is up is read
off the field list (`nodes.classify`) because the game does not say.

Input is ACTIVATE_FIELD on the field the builder gave that hotkey, looked
up in the list AT THE MOMENT of the click (decision 20) — never an index
remembered from an earlier list. A send closes the gate until the list
changes or the game has had its ticks to answer (`can_send`), so a
double click cannot land its second half in the next dialog: the menu's
SETTINGS is index 5, and index 5 of the Settings list is a checkbox.

What HD does NOT do, each marked here, in layout.json, in the status
document and in the smoke test:

- OMISSION — the game-type icon on every slot row. (The Music and Sound
  Fx bars were one until work order 124 C; they are `gmsliders`.)
- UNVERIFIED, NOT TRANSCRIBED — a right click inside the Save dialog
  outside every help region (`layout.json` `unverified_right_click`).
- DEVIATION — an empty save slot starts the name edit empty, where the
  original pre-fills "... empty slot ..." (`gmsave.SaveEditor.start`,
  `layout.json` `save_empty_slot_deviation`).

QUIT -> YES disarms the client's watchdog BEFORE the YES goes out, and
the app ends with the game (decision 62).
"""
import logging

import pygame

from core import hestrings
from core.hestrings import printf
from core.screen_base import ScreenBase
from core.structs import settings as settings_spec
from core.wire_protocol import EFFECT_PAIRS
from screens.game_menu import gmdraw, gmframe, gmorion, gmsliders, nodes
from screens.game_menu.gmsave import SaveEditor

log = logging.getLogger("game_menu")

#: A load is silence until the engine is back in an input loop
#: (fundament section 3); the watchdog is held this long for it.
LOAD_HOLD_S = 120.0


class GameMenuScreen(ScreenBase):
    SCREEN_NAME = "game_menu"
    GAME_SCREEN_ID = 8        # SCREEN_GAME, orion2_consts.h:468
    IS_OVERLAY = True
    #: The screen the popup belongs over. SCREEN_GAME is entered from one
    #: place only, the galaxy map's GAME button (mainscr_main.cpp:609-613,
    #: `_return_screen = SCREEN_MAIN`), and the original draws it over the
    #: map. A client that connects while the menu is already up has never
    #: been on the map, so the dispatcher enters this screen first instead
    #: of opening the overlay over whatever was active (the main-menu
    #: backdrop, found in work order 125, fixed in 126 D).
    OVERLAY_PARENT = "galaxy_map"
    #: No dimming: a palette-indexed engine cannot darken what is under
    #: a popup, and the original draws its popup over the map as it is.
    OVERLAY_DIM = 0

    #: Each dialog's buttons: the HD box and the hotkey of the field it
    #: activates — the builders' own letters (loadsave.cpp:188-198,
    #: :220, :266, :282, :284; gendraw.cpp:172-173).
    BUTTONS = {
        nodes.MENU: [("menu_save", "S"), ("menu_load", "L"),
                     ("menu_new", "N"), ("menu_quit", "Q"),
                     ("menu_settings", "O"), ("menu_return", nodes.ESC)],
        nodes.SETTINGS: [("settings_accept", "A")],
        nodes.LOAD: [("load_load", "L"), ("load_cancel", "C")],
        nodes.SAVE: [("save_save", "S"), ("save_cancel", "C")],
        nodes.CONFIRM: [("confirm_yes", "Y"), ("confirm_no", "N")],
    }

    def __init__(self, app):
        super().__init__(app)
        self.words = {}
        self.node = None
        self.under = None       # the dialog a confirmation/warning covers
        self.state = None
        self.flags = None       # the thirteen checkbox states, held locally
        self.pending = None     # "new" / "quit": which confirmation is up
        self.last_slot = None   # the Load row HD sent, for the warning
        self.hstrings = None
        self._sent = None
        self.save = SaveEditor(self)
        self.menu_keys = set()  # the menu's buttons, as its last list had them
        self.slider_drag = None  # gmsliders: a press on a bar, not sent yet
        self.slider_sent = {}

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        # THE WORDS FIRST: `super().enter` reloads the boxes, and seating them
        # (`gmframe.seat`) reads `frame` out of layout.json. Loaded after, the
        # FIRST entry found no frame, left the menu unplaced and drew the fill
        # without the artwork; only a second entry showed it (found live,
        # 16 September 2026, after work order 125).
        self.words = self.app.res.load_json(
            "screens/game_menu/layout.json", {}) or {}
        super().enter(game_state)
        # ONE CONSTRUCTION SITE (D17, work order 159). These four lines
        # WERE the right shape and are now the shared one: `for_app`
        # holds exactly them, so the galaxy map and Planets get this
        # instance rather than building their own.
        self.hstrings = hestrings.for_app(self.app)
        self.node = self.under = self.pending = self.last_slot = None
        self.menu_keys = set()
        self._sent = None
        self.flags = self._initial_flags(game_state)
        self.save.reset()

    def exit(self):
        # Every way out of the popup, ESC from Settings included, keeps
        # the OrionLayer rows' values; the save writes nothing twice.
        gmorion.save(self)
        self.save.reset()
        super().exit()

    def _reload_boxes(self):
        """The file's boxes, then seated into the galaxy map's opening
        (`gmframe.seat`, work order 125)."""
        super()._reload_boxes()
        gmframe.seat(self)

    def _load_background(self):
        """An overlay draws no background: the map stays underneath."""

    @staticmethod
    def _initial_flags(game_state):
        raw = getattr(game_state, "settings_raw", b"") or b""
        if len(raw) < settings_spec.SIZE:
            return None
        return settings_spec.option_flags(
            raw, getattr(game_state, "game_type", 0))

    def update(self, game_state=None):
        if game_state is None:
            return
        self.state = game_state
        if self.flags is None:
            self.flags = self._initial_flags(game_state)
        node = nodes.classify(game_state.fields)
        if node == nodes.MENU:
            self.menu_keys = {key for _, key in self.BUTTONS[nodes.MENU]
                              if self.present(nodes.MENU, key)}
        if node != self.node:
            if node in (nodes.MENU, nodes.SETTINGS, nodes.LOAD, nodes.SAVE):
                self.under = node
            if node == nodes.MENU:
                self.pending = None
            if node != nodes.SAVE:
                self.save.reset_edit()
            log.info("game menu: %s -> %s", self.node, node)
            self.node = node
        self.save.update(game_state)
        gmsliders.advance(self, game_state)

    def render(self, surface):
        gmdraw.render(self, surface)
        self.render_help(surface)

    # ── Sending ───────────────────────────────────────────

    def fields(self):
        return self.state.fields if self.state is not None else []

    def _ticks(self):
        stats = getattr(self.app.client, "stats", None)
        return stats["state"] if stats else None

    def can_send(self):
        """Closed after a send until the list changes, or until the game
        has had EFFECT_PAIRS + 1 snapshots to change it and did not (a
        toggle, or a SAVE with no slot to save). A count of ticks, never
        a clock (decision 21)."""
        if self._sent is None:
            return True
        sig, mark = self._sent
        ticks = self._ticks()
        if (nodes.signature(self.fields()) != sig or ticks is None
                or ticks >= mark + EFFECT_PAIRS + 1):
            self._sent = None
            return True
        return False

    def send(self, field):
        if field is None or not self.app.connected or not self.can_send():
            return False
        self._sent = (nodes.signature(self.fields()), self._ticks() or 0)
        self.app.client.activate_field(field.index)
        return True

    def present(self, node, key):
        ftype = nodes.TYPE_HIDDEN if node == nodes.CONFIRM else nodes.TYPE_BUTTON
        return nodes.hotkey_field(self.fields(), key, ftype) is not None

    def press(self, key):
        """One of the dialog's own letters, clicked or typed."""
        node = self.node
        ftype = nodes.TYPE_HIDDEN if node == nodes.CONFIRM else nodes.TYPE_BUTTON
        field = nodes.hotkey_field(self.fields(), key, ftype)
        if field is None or not self.can_send():
            return
        if node == nodes.CONFIRM and key == "Y" and self.pending == "quit":
            # Before YES, never after: the game saves SAVE10.GAM and
            # exits (loadsave.cpp:1261-1273), and a watchdog still armed
            # would read that silence as a dead link and reconnect.
            self.app.client.expect_shutdown()
        if node == nodes.MENU and key in ("N", "Q"):
            self.pending = "new" if key == "N" else "quit"
        if node == nodes.LOAD and key == "L":
            self.app.client.hold_watchdog(LOAD_HOLD_S)
        if node == nodes.SETTINGS and key == "A":
            gmorion.save(self)
        self.send(field)

    def confirm_text(self):
        hid = self.words.get("confirm", {}).get(self.pending)
        if hid is None:
            return self.words.get("words", {}).get("confirm_unknown", "")
        return gmdraw.game_string(self, hid)

    def warning_text(self):
        slots = gmdraw.slots_for(self, nodes.LOAD)
        if self.last_slot is None:
            return self.words.get("words", {}).get("warning_unknown", "")
        if slots:
            hid = self.words.get("warning", {}).get(
                str(slots[self.last_slot]["status"]))
            if hid is not None:
                return printf(gmdraw.game_string(self, hid),
                              self.last_slot + 1)
        return self.words.get("words", {}).get(
            "warning_unknown", "").replace("{n}", str(self.last_slot + 1))

    # ── Input ─────────────────────────────────────────────

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y) or self.node is None:
            return None
        # THE PRESSED STATE FIRST, before anything decides whether to send:
        # it shows the click landed, not that the game took it (decision 33).
        for name, _ in self.BUTTONS.get(self.node, []):
            if gmdraw.hit(self, name, screen_x, screen_y):
                self.pressed.press(name, gmdraw.box(self, name).screen_rect)
        if self.node in (nodes.LOAD, nodes.SAVE):
            i = gmdraw.row_at(self, "slot_list", nodes.SLOTS,
                              screen_x, screen_y)
            if i is not None:
                self.pressed.press(f"slot_{i}", gmdraw.bands(
                    gmdraw.box(self, "slot_list").screen_rect, nodes.SLOTS)[i])
        if self.save.handle_click(screen_x, screen_y):
            return None
        if gmsliders.press(self, screen_x, screen_y):
            return None
        for name, key in self.BUTTONS.get(self.node, []):
            if gmdraw.hit(self, name, screen_x, screen_y):
                self.press(key)
                return None
        if self.node == nodes.SETTINGS:
            # THE ORIONLAYER ROWS FIRST, and they never reach `send`:
            # they have no field (HD EXTENSION, fundament 63).
            if gmorion.handle_click(self, screen_x, screen_y):
                return None
            i = gmdraw.row_at(self, "settings_rows", nodes.OPTIONS,
                              screen_x, screen_y)
            labels = nodes.option_toggles(self.fields())
            if i is not None and labels and self.send(labels[i]) \
                    and self.flags is not None:
                self.flags[i] ^= 1
        elif self.node == nodes.LOAD:
            i = gmdraw.row_at(self, "slot_list", nodes.SLOTS,
                              screen_x, screen_y)
            rows = nodes.slot_rows(self.fields())
            if i is not None and rows and self.can_send():
                # A slot row loads AT ONCE (loadsave.cpp:332-375).
                self.last_slot = i
                self.app.client.hold_watchdog(LOAD_HOLD_S)
                self.send(rows[i])
        elif self.node == nodes.WARNING:
            self.send(nodes.esc_field(self.fields()))
        return None

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        gmsliders.motion(self, screen_x, screen_y)

    def handle_left_release(self, screen_x, screen_y):
        super().handle_left_release(screen_x, screen_y)
        gmsliders.release(self, screen_x, screen_y)

    def handle_key_event(self, event):
        if self.save.handle_key_event(event):
            return
        if self.help_consumes_key(event.key) or self.node is None:
            return
        if event.key == pygame.K_ESCAPE:
            if self.node == nodes.CONFIRM:
                return          # the loop wants YES or NO (gendraw.cpp:212)
            if self.node == nodes.MENU:
                self.press(nodes.ESC)       # RETURN, the first ESC field
            else:
                self.send(nodes.esc_field(self.fields()))
            return
        ch = (getattr(event, "unicode", "") or "").upper()
        if any(key == ch for _, key in self.BUTTONS.get(self.node, [])):
            self.press(ch)

    def handle_key(self, key):
        """Nothing is forwarded raw: only the dialog's letters mean
        anything to the popup, and they go through `press`."""
        self.help_consumes_key(key)

    # ── Help ──────────────────────────────────────────────

    def help_region_rect(self, spec):
        """Only the current dialog's table (help.json `node`)."""
        if spec.get("node") != self.node:
            return None
        return super().help_region_rect(spec)

    def help_extra_rect(self, spec):
        return gmdraw.help_rect(self, spec)
