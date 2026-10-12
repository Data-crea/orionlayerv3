"""
Screen dispatcher.

Manages active screens and switches between them based on
orion2re's current_screen value. Unknown screen IDs fall
back to the original framebuffer view.

The game-ID -> screen mapping is built at registration time
from each screen class's GAME_SCREEN_ID attribute. Screens
(including screens added by mods) declare their own ID; there
is no central list to maintain.
"""
import logging

import pygame

from core.screen_names import SCREENS as _SCREEN_NAMES

log = logging.getLogger("dispatcher")

# Display names for orion2re screen IDs (status bar only —
# has no effect on routing). Falls back to the ENGINE_NAME (e.g.
# "GAME", "EXIT") for IDs with no OrionLayer screen of their own,
# so the status bar always shows something instead of the bare id.
# Single source: core/screen_names.py.
GAME_SCREEN_NAMES = {
    sid: (orionlayer_name or engine_name.lower())
    for sid, (engine_name, orionlayer_name) in _SCREEN_NAMES.items()
}


class Dispatcher:
    """Manages screen transitions."""

    def __init__(self):
        self.screens = {}       # name -> ScreenBase instance
        self.screen_map = {}    # game screen_id -> name (from GAME_SCREEN_ID)
        # game screen_id -> [names] that SHARE it (`SHARES_GAME_SCREEN_ID`)
        self.shared_map = {}
        self.active = None      # active screen (ScreenBase)
        self.active_name = ""   # name of the active screen
        self.use_original = False  # True when no HD screen available
        self._locked_screen = ""   # sub-screen lock (prevents auto-switch)
        self._locked_game_ids = set()  # game screen_id when lock was set
        self.overlay = None        # overlay screen shown above active
        self.overlay_name = ""

    def register(self, name, screen):
        """Register a screen. GAME_SCREEN_ID wires auto-switching."""
        self.screens[name] = screen
        game_id = getattr(screen, "GAME_SCREEN_ID", None)
        if game_id is not None:
            self.screen_map[game_id] = name
            # `EXTRA_SCREEN_IDS`: more ids the same screen answers — the
            # Ship Designer's three pickers are one box drawn three ways
            # (work order 185, open fix 45's 54 / 55 / 56).
            for extra in getattr(screen, "EXTRA_SCREEN_IDS", ()):
                self.screen_map[extra] = name
        # `SHARES_GAME_SCREEN_ID` (work order 223): a screen the game shows
        # under ANOTHER screen's id — the race report under Races' 6, the
        # refit lists under the build popup's 25. It has no id of its own,
        # and it is asked first: it takes the snapshot only when its own
        # `claims` recognises its list, else the id's owner is asked.
        shared = getattr(screen, "SHARES_GAME_SCREEN_ID", None)
        if shared is not None:
            self.shared_map.setdefault(shared, []).append(name)

    def screen_name_for(self, game_screen_id):
        """Display name for a game screen ID (status bar)."""
        return self.screen_map.get(
            game_screen_id,
            GAME_SCREEN_NAMES.get(game_screen_id, f"#{game_screen_id}"))

    def switch_to(self, name, game_state=None, lock_ids=None):
        """Switch to the named screen.

        If the screen has no GAME_SCREEN_ID (a sub-screen), set a lock
        so update_from_game won't override it until the game's screen
        ID actually changes. `lock_ids` (iterable of game screen IDs)
        widens the lock: the sub-screen stays while orion2re reports
        ANY of these IDs — needed when the game hops between IDs
        underneath one HD screen (Custom Race Accept: 50 -> 6).
        """
        target = self.screens.get(name)
        if target and getattr(target, "IS_OVERLAY", False):
            # An overlay that names the screen it belongs over gets that
            # screen underneath, whatever was active before — the GAME menu
            # reached by connecting while it is already open would otherwise
            # sit on the main menu's backdrop (work order 126 D).
            parent = getattr(target, "OVERLAY_PARENT", None)
            if (parent and parent != self.active_name
                    and parent in self.screens):
                self.switch_to(parent, game_state)
            self.open_overlay(name, game_state)
            return
        self.close_overlay()

        if name == self.active_name:
            return

        if self.active:
            self.active.exit()

        screen = target
        if screen:
            # WORK ORDER 139 B. Until now a screen switch left no trace
            # at all, so a log could not say whether HD had followed the
            # game at all — work order 138 had to infer it from which
            # screen sent the NEXT click. One line, here, where the
            # switch happens, with the game's own id beside the names.
            log.info("screen: %s -> %s (game screen %s)",
                     self.active_name or "-", name,
                     getattr(game_state, "current_screen", "?"))
            self.active = screen
            self.active_name = name
            self.use_original = False
            screen.enter(game_state)

            # Check if this is a sub-screen (no GAME_SCREEN_ID). A screen
            # that SHARES an id is no sub-screen: its `claims` decides on
            # every snapshot, and a lock would keep it after its list is
            # gone (work order 223 — the report stayed over Races).
            is_mapped = name in self.screen_map.values() or \
                getattr(screen, "SHARES_GAME_SCREEN_ID", None) is not None
            if is_mapped:
                self._locked_screen = ""
                self._locked_game_ids = set()
            else:
                self._locked_screen = name
                ids = set(lock_ids) if lock_ids else set()
                if game_state:
                    ids.add(game_state.current_screen)
                self._locked_game_ids = ids


    # ── Overlay layer ────────────────────────────────────

    def open_overlay(self, name, game_state=None):
        """Open an overlay screen above the active screen.

        The parent stays active and keeps rendering underneath.
        Only one overlay at a time; opening another replaces it.
        """
        if name == self.overlay_name:
            return
        self.close_overlay()
        screen = self.screens.get(name)
        if screen:
            self.overlay = screen
            self.overlay_name = name
            screen.enter(game_state)

    def close_overlay(self):
        """Close the overlay, if any. Parent screen is untouched."""
        if self.overlay:
            self.overlay.exit()
        self.overlay = None
        self.overlay_name = ""

    @property
    def top(self):
        """Topmost screen receiving input (overlay before parent)."""
        return self.overlay or self.active

    # ── Rendering / input routing ────────────────────────

    def render(self, surface):
        """Render active screen, dim layer, then overlay."""
        if self.active:
            self.active.render(surface)
        if self.overlay:
            dim = getattr(self.overlay, "OVERLAY_DIM", 120)
            if dim > 0:
                shade = pygame.Surface(surface.get_size(),
                                       pygame.SRCALPHA)
                shade.fill((0, 0, 0, dim))
                surface.blit(shade, (0, 0))
            self.overlay.render(surface)

    def update_screens(self, game_state=None):
        """Per-frame update for parent AND overlay."""
        if self.active:
            self.active.update(game_state)
        if self.overlay:
            self.overlay.update(game_state)

    def route_click(self, x, y):
        if self.top:
            self.top.handle_click(x, y)

    def route_motion(self, x, y):
        if self.top:
            self.top.handle_mouse_motion(x, y)

    def route_key_event(self, event):
        """Full KEYDOWN event (unicode included) to the top screen."""
        if self.top:
            self.top.handle_key_event(event)

    def update_from_game(self, game_state):
        """Switch screen based on orion2re's current_screen.

        If a sub-screen lock is active and the game's screen ID
        hasn't changed, keep the locked screen visible.
        """
        screen_id = game_state.current_screen

        # A SCREEN STILL PLAYING WHAT BELONGS TO IT keeps the window (work
        # order 202 D, `ScreenBase.finishing`): the battle's last events
        # come with the first snapshot after it, and Data's condition of
        # 30 September 2026 is that HD shows nothing after them before
        # they are played.
        finishing = getattr(self.active, "finishing", None)
        if finishing is not None and not self.overlay and \
                finishing(game_state):
            return True

        # Overlay bound to a game screen ID: close it when the
        # game leaves that ID; ignore the parent re-report.
        if self.overlay:
            overlay_id = getattr(self.overlay, "GAME_SCREEN_ID", None)
            if overlay_id is not None:
                # `ALSO_OVER_IDS`: a screen the overlay may also stand over
                # — the GAME menu's Load dialog is run by the main menu too
                # (work order 177), under SCREEN_MAIN_MENU; the parent
                # screen decides when it closes there.
                if screen_id == overlay_id or screen_id in getattr(
                        self.overlay, "ALSO_OVER_IDS", ()) or \
                        screen_id in getattr(self.overlay,
                                             "EXTRA_SCREEN_IDS", ()):
                    return True
                self.close_overlay()
            # Manually opened overlay (no ID): parent logic decides.

        # MPLY (below) also ends a sub-screen's lock: Empire Identity, the
        # race pick's sub-screen, is locked on the 51 that race selection
        # leaves behind (work order 188, seen live in the hotseat setup).
        if getattr(game_state, "multiplayer", None) is not None and \
                "multiplayer" in self.screens and self._locked_screen:
            self._locked_screen = ""
            self._locked_game_ids = set()
        # Sub-screen lock: stay on locked screen until game changes
        if self._locked_screen and self._locked_screen != self.active_name:
            self._locked_screen = ""      # stale lock (screen left)
            self._locked_game_ids = set()
        if self._locked_screen:
            locked = self.screens.get(self._locked_screen)
            keep = getattr(locked, "keep_lock", None)
            verdict = keep(screen_id) if keep is not None else None
            if verdict is True:
                return True   # screen insists (e.g. running chain)
            if verdict is None and screen_id in self._locked_game_ids:
                return True   # keep locked screen
            # Game screen changed — release lock
            self._locked_screen = ""
            self._locked_game_ids = set()

        # A BLOCK THAT NAMES ITS SCREEN (work order 188): open fix 51's
        # MPLY is on the wire exactly while a multiplayer step is up (its
        # guards clear it for every race pick), whatever id the engine still
        # reports — race selection leaves its 51 behind when it returns into
        # the hotseat setup (open fix 22 restores the caller's id on ESC
        # only), seen live. So the multiplayer screen takes it.
        if getattr(game_state, "multiplayer", None) is not None and \
                "multiplayer" in self.screens:
            name = "multiplayer"
        else:
            name = next((n for n in self.shared_map.get(screen_id, ())
                         if self.screens[n].claims(game_state)),
                        self.screen_map.get(screen_id))

        # A screen may decline its id for a snapshot it cannot draw at all
        # (`ScreenBase.claims`, work order 180 B): then the id is unclaimed.
        if name and name in self.screens \
                and self.screens[name].claims(game_state):
            self.switch_to(name, game_state)
            self.use_original = False
            return True

        # No HD screen for this ID -> original framebuffer
        self.close_overlay()
        if self.active and not self.use_original:
            self.active.exit()
            self.active = None
            self.active_name = ""
        self.use_original = True
        return False

    def on_resize(self):
        """Forward resize to active screen and overlay."""
        if self.active:
            self.active.on_resize()
        if self.overlay:
            self.overlay.on_resize()
