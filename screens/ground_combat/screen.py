"""The ground combat (open fix 91's id 69) — work order 232 C.

The original's `COLGCBT::Colony_Combat_Screen_` (colgcbt.cpp:165-273), after
an invasion: the colony's ground with both sides' troops fighting over it,
the attack and the defense summaries above, the title line saying who
attacks and, at the end, who won. Read in
`dev:doc/briefs/232-invasion-reading.md` §4.

**IT CLAIMS ID 69 ONLY WITH TPOP KIND 11** (open fix 91): every unit, beam
and explosion is the frame the engine drew last, and both boxes are the
engine's numbers and lines — HD computes no motion and no result. Without
the block the id is no screen's, and the F12 notice stands as before
(decision 76). The invasion's outcome is decided before the screen opens
(`invasion::Invade_`, invasion.cpp:858-891); the screen replays it.

**WHAT IT SENDS**, as the original's loop answers it (:232-262): a click
anywhere is the full-screen field [0] — the first, while both sides fight,
makes the fight fast (`_display_fast`, every round at once); one after the
end leaves the screen; ESC is the screen's own hotkey field [1] by the key
rule every screen shares (`core.keyfwd`). Nothing else is sent.

The title on the shell's plate; the two boxes and the field are the shell's
panels (`gcgeom`). Right click: help 541 over the attack box, 542 over the
defense box, 540 everywhere else (`_colony_ground_combat_screen_help`,
colgcbt.cpp:5-9).
"""
import logging

from core.estrings import EStrings
from core.screen_base import ScreenBase

from . import gcdraw, gcgeom as geom

log = logging.getLogger("ground_combat")

GAME_SCREEN_ID = 69
#: The full-screen field `Add_Global_Fields_` adds first (colgcbt.cpp:451-
#: 456): a hidden field over (0, 0)..(0x27F, 0x1DF).
TYPE_HIDDEN = 7
WHOLE = (0, 0, 0x27F, 0x1DF)


def popup_of(state):
    """TPOP kind 11, or None."""
    tp = getattr(state, "turn_popup", None)
    return tp if tp is not None and tp.get("kind") == "ground_combat" \
        else None


class GroundCombatScreen(ScreenBase):
    SCREEN_NAME = "ground_combat"
    GAME_SCREEN_ID = GAME_SCREEN_ID
    USE_FRAME = False
    #: The player watches a battle without input: no idle rate here
    #: (`framerate.loop_cap`, work order 263).
    FULL_RATE = True
    SHELL_WORN = True

    def __init__(self, app):
        super().__init__(app)
        from core.hud import shell
        self.shell = shell.Shell(title=self._title, row=False)
        self._state = None
        self._popup = None
        lang = (getattr(app, "settings", None) or {}).get("language", "en")
        self.estrings = EStrings(lang)

    # ── The dispatcher's questions ────────────────────────────────────

    def claims(self, game_state):
        return popup_of(game_state) is not None

    # ── Per frame ─────────────────────────────────────────────────────

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        got = popup_of(game_state)
        if got is not None:
            self._popup = got

    def _title(self):
        return (self._popup or {}).get("title") or ""

    def render_content(self, surface):
        if self._popup is not None and self._state is not None:
            gcdraw.draw(surface, self, self._popup, self._state)

    # ── Input ─────────────────────────────────────────────────────────

    def whole_field(self):
        """The live full-screen field (decided from the list of now)."""
        return next((f for f in (getattr(self.app.client.state, "fields",
                                         None) or [])
                     if f.field_type == TYPE_HIDDEN and
                     (f.x, f.y, f.x_end, f.y_end) == WHOLE), None)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        f = self.whole_field()
        if f is not None and self.app.connected:
            log.info("ground combat: a click -> field %d", f.index)
            self.app.client.activate_field(f.index)
        return None

    def help_extra_rect(self, spec):
        """The help regions are the original's (`geom.HELP`): 541 and 542
        stand over the two boxes, which are HD's panels."""
        hid = spec.get("help_id")
        if hid == 541:
            return self.box_screen_rect(geom.BAND[0])
        if hid == 542:
            return self.box_screen_rect(geom.BAND[1])
        if hid == 540:
            from core.hud import shell
            return shell.content(self.app.layout)
        return None
