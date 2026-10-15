"""The galactic council (open fix 96's id 70) — work order 270.

The original's `council::Main_Council_Screen` (council.cpp:101-146): the
high council convenes, names the two nominees with the most votes, the
members vote one after the other (`Council_Votes`, :345-399), the player
votes from a list — a nominee, or abstain (`Council_Player_Vote`,
:213-281) — the result is announced (`Council_Finished_Voting`, :567-596)
and, when someone is elected, the player accepts or refuses the ruling
(`Council_Accept_Ruling`, :598-675). Between the steps the game waits for
a click anywhere (`Control_Main_Council_Screen`, :72-99: one hidden field
over the screen).

**IT CLAIMS ID 70 ONLY WITH TPOP KIND 12** (open fix 96): every number and
line is the game's as it stands; HD decides nothing. Without the block the
council runs under the processing id 12 and the F12 notice stands as before
(decision 76).

**WHAT IT SENDS**: a click while the game waits for one is the full-screen
field; a click on a list item is that item's field (the list's type-10
fields under its title's, top to bottom, as `Get_List_Field_` adds them,
fields.cpp:1561-1620). Nothing else. The original's council has no help
list (`Deactivate_Help_List_`, :102): HD shows none.
"""
import logging

from core.screen_base import ScreenBase

from . import cldraw, clgeom as geom

log = logging.getLogger("council")

GAME_SCREEN_ID = 70
TYPE_HIDDEN, TYPE_LIST = 7, 10
WHOLE = (0, 0, 639, 479)


def popup_of(state):
    """TPOP kind 12's council, or None."""
    tp = getattr(state, "turn_popup", None)
    if tp is None or tp.get("kind") != "council":
        return None
    return tp.get("council")


class CouncilScreen(ScreenBase):
    SCREEN_NAME = "council"
    #: Its picture moves only with input, the game and the window: a frame
    #: that would draw it again is not drawn (work order 273, `core/drawgate`).
    STILL = True
    GAME_SCREEN_ID = GAME_SCREEN_ID
    USE_FRAME = False
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        from core.hud import shell
        self.shell = shell.Shell(title=lambda: "GALACTIC COUNCIL", row=False)
        self._state = None
        self._council = None
        self.menu_rects = []

    def claims(self, game_state):
        return popup_of(game_state) is not None

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        got = popup_of(game_state)
        if got is not None:
            self._council = got

    def render_content(self, surface):
        if self._council is not None and self._state is not None:
            cldraw.draw(surface, self, self._council, self._state)

    # ── Input ─────────────────────────────────────────────────────────

    def _fields(self):
        return getattr(self.app.client.state, "fields", None) or []

    def whole_field(self):
        """The full-screen field the game waits on (from the list of now)."""
        return next((f for f in self._fields()
                     if f.field_type == TYPE_HIDDEN and
                     (f.x, f.y, f.x_end, f.y_end) == WHOLE), None)

    def item_field(self, index):
        """List item `index`'s field: the type-10 fields top to bottom,
        the title's first when there is one more than the items."""
        menu = (self._council or {}).get("menu") or {}
        n = len(menu.get("items") or [])
        lists = sorted((f for f in self._fields()
                        if f.field_type == TYPE_LIST), key=lambda f: f.y)
        if len(lists) == n + 1:
            lists = lists[1:]
        return lists[index] if 0 <= index < len(lists) and \
            len(lists) == n else None

    def handle_click(self, screen_x, screen_y):
        if not self.app.connected or self._council is None:
            return None
        if (self._council.get("menu") or {}).get("items"):
            hit = next((i for r, i in self.menu_rects
                        if r.collidepoint(screen_x, screen_y)), None)
            f = self.item_field(hit) if hit is not None else None
            if f is not None:
                log.info("council: item %d -> field %d", hit, f.index)
                self.app.client.activate_field(f.index)
            return None
        f = self.whole_field()
        if f is not None:
            log.info("council: a click -> field %d", f.index)
            self.app.client.activate_field(f.index)
        return None
