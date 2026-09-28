"""The diplomacy audience (wire ids 57, 58) — work order 185, part 10.

The original's `DIP_SCRN::Diplomacy_Screen_` (the player's, from the
Races screen: 57) and `Npc_Diplomacy_Screen_` (an AI's — at turn start or
on a sneak attack: 58), one screen for both; the reading is
`doc/audience_reading.md`, the brief `doc/brief_audience.md`.

**IT CLAIMS THE IDS ONLY WITH OPEN FIX 47's "DIPL" BLOCK ON THE WIRE**
(`auwire.claims`), and the ids themselves exist only with open fix 46.
Both are applied since work order 186 (orion2re `8aea1a25`, `ba9b6bc6`)
and the player's audience (57) was walked live on that engine; on an
engine without them the audience runs under its caller's id and stays the
game's picture, as before.

**WHAT IT SENDS** — ACTIVATE_FIELD, the field found in the list on the
wire when the byte goes out (decision 20), nothing the player did not
choose (decision 65):

    a menu item          its field: the list's type-10 fields in y order,
                         the title first (the list returns the chosen
                         field, fields.cpp:1640-1688 — measured live in
                         part 9: Good Bye by activation left the audience)
    a statement          its one full-screen field, on any click

Refused before it goes out (decision 33): a disabled item — the list
ignores it (fields.cpp:1647-1649). No keys are sent: the list's fields
carry no hotkey. A right click opens nothing (OMISSION `audience_help`:
the audience's help ids are not built).
"""
import logging

from core.screen_base import ScreenBase
from screens.leaders import ldrdraw as nd

from . import audraw, auwire

log = logging.getLogger("audience")


class AudienceScreen(ScreenBase):
    SCREEN_NAME = "audience"
    # Literal, as every screen's is (the id check reads them off the
    # source); `augeom` names the same, and the smoke group holds the two.
    GAME_SCREEN_ID = 57
    EXTRA_SCREEN_IDS = (58,)
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None

    # ── The dispatcher's and the gate's questions ────────────────────

    def claims(self, game_state):
        return auwire.claims(game_state)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def handover_is_modal(self):
        return self._view is not None and \
            self._view.state == auwire.GAME_BOX

    def fallback_reason(self):
        if self._view is not None and not self._view.draws:
            return self._view.reason
        return ""

    # ── Per frame ─────────────────────────────────────────────────────

    def update(self, game_state=None):
        if game_state is not None and game_state is not self._state:
            self._state = game_state
            self._view = auwire.View(game_state)

    def hovered(self, rect):
        from core import mouse as mouse_input
        return rect.collidepoint(*mouse_input.pos())

    def render(self, surface):
        self._render_background(surface)
        if self._view is not None and self._view.draws:
            audraw.draw(surface, self, self._view)

    # ── Sending ──────────────────────────────────────────────────────

    def send(self, field, label):
        if field is None or not self.app.connected:
            return False
        log.info("audience: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        state = getattr(self.app.client, "state", None)
        live = auwire.View(state) if state is not None else None
        if live is None or not live.draws:
            return None
        if live.state == auwire.STATEMENT:
            self.send(live.fields[0], "statement")
            return None
        for item, f in live.items():
            if nd.rect(self.layout, (f.x, f.y, f.x_end, f.y_end)) \
                    .collidepoint(screen_x, screen_y):
                if item["enabled"]:
                    self.send(f, f"item {item['text'].strip()!r}")
                return None           # a disabled item: refused
        return None
