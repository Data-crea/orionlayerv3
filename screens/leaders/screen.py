"""Leaders — orion2re SCREEN_OFFICERS (29), `OFFICER::Officers_Screen_`
(officer.cpp:856-1195). Work order 167.

HD STATE: **BUILT, NOT ACCEPTED.** The live part of work order 167 is
parked in `doc/briefs/167-parked-for-data.md` (item L) with its exact
steps. Decision 61, and a smoke check fails if this sentence leaves this
docstring.

Entered from the galaxy map's and the Fleets screen's LEADERS buttons
and from the colony screen. Two views — Colony Leaders and Ship
Officers — four rows of leaders, HIRE / POOL / DISMISS / RETURN, PREV /
NEXT, the view box and the galaxy box; the inventory is
`doc/briefs/167-progress.md` Part A.

**NO OUTER FRAME** (the work order): OFFICER.LBX 0, the full-screen art
the original paints its rails and panels into, is not drawn. What stands
in its place are the inner boxes, drawn in code (DEVIATION
`inner_boxes_drawn`, `ldrdraw`), and everything the original draws ON
that art at its own native rectangle — `ldrgeom` holds every one with
its source line.

THE MODULES, one topic each:

  ldrgeom    the native geometry, sourced
  ldrwire    what one snapshot lets HD believe and send (the six states)
  ldrrows    what a row says: name, cost, status, skills
  ldrpopup   the hire popup: recognised, and its leader identified
  ldrdraw    the left half, the buttons, the strips
  ldrright   the view box and the galaxy box
  ldrdialog  the popup and the skill help box
  ldrinput   what a click, a right click, the pointer and a key do
  ldrart     the original's artwork, extracted by the player

**WHAT HD MAY SEND** is `ldrwire.View.sendable`'s answer and nothing
else, and without open fix 30 (`doc/ext_officer_screen_state.patch`,
NOT APPLIED) it is short on purpose: the two tabs, HIRE, CANCEL,
RETURN, a click on a leader FOR HIRE, the popup's two answers and a
native box's own buttons — each one's effect is visible on the wire
afterwards. POOL, DISMISS, PREV / NEXT, assigning a leader and the
galaxy box's clicks need the block; without it they are drawn and
answer nothing (HD STATE).
"""
import logging

from core import estrings, hestrings, skildesc
from core.screen_base import ScreenBase
from core.structs import player as player_struct

from . import ldrart, ldrdialog, ldrdraw, ldrgeom, ldrinput, ldrright
from . import ldrrows, ldrwire

log = logging.getLogger("leaders")


class LeadersScreen(ScreenBase):
    SCREEN_NAME = "leaders"
    GAME_SCREEN_ID = ldrgeom.GAME_SCREEN_ID   # 29, orion2_consts.h:484
    USE_FRAME = False

    def __init__(self, app):
        super().__init__(app)
        self._state = None
        self._view = None
        self._waited = 0
        self._last_view = None
        self._rows = []
        self._hover = None          # leader id under the pointer
        self._skill_help = None     # (title, body) of HD's help box
        self._data = {}
        self._shown = ({}, False, None)   # buttons, hire mode, mode
        self._words = None
        self._skills = None
        self._art = ldrart.load()

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/leaders/layout.json", {}) or {}
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._words = ldrrows.Words(estrings.EStrings(language),
                                    hestrings.for_app(self.app), language)
        self._skills = skildesc.for_app(self.app)
        self._waited, self._hover, self._skill_help = 0, None, None
        self._last_view = None
        self._shown = ({}, False, None)
        self._help_doc = self.app.res.load_json(
            "screens/leaders/help.json", {}) or {}
        self.update(game_state)

    def update(self, game_state=None):
        if game_state is None:
            return
        self._state = game_state
        own = ldrwire.is_officer_list(getattr(game_state, "fields", None))
        self._waited = 0 if own else self._waited + 1
        self._view = ldrwire.View(game_state, self._waited,
                                  self._warlord_of, self._last_view)
        if self._view.view_known:
            self._last_view = self._view.view
        if self._view.state == ldrwire.READY:
            # What the buttons looked like the last time the list was
            # this screen's. A box or the popup REPLACES the list, and
            # the original keeps drawing the screen under it unchanged
            # (the auto function, mainpups.cpp:829-837), so HD draws the
            # buttons it last read rather than none.
            self._shown = (dict(self._view.buttons), self._view.hire_mode,
                           self._view.mode)
        self._rows = (ldrrows.build(self._view, game_state, self._words,
                                    self._warlord_of)
                      if self._view.draws and self._words else [])

    def _warlord_of(self, player):
        """`_player[player].traits[TRAIT_WARLORD]` (officer.cpp:93)."""
        raws = getattr(self._state, "player_raw", None) or []
        if not 0 <= int(player) < len(raws):
            return False
        traits = player_struct.traits(player_struct.parse(raws[player]))
        return bool(traits[30]) if len(traits) > 30 else False

    def wants_original(self):
        """Hand over only for the two refusals (decision 22). WAITING
        keeps HD's own picture up — the no-glimpse rule of work order
        166 A — and a native box or the popup is drawn over it."""
        return self._view is not None and not self._view.draws

    def fallback_reason(self):
        return self._view.reason if self._view else ""

    @property
    def problems(self):
        return [self._view.reason] if self.wants_original() else []

    # ── Drawing ───────────────────────────────────────────

    def render(self, surface):
        self._render_background(surface)
        art, view = self._art, self._view
        ldrdraw.draw_frame_boxes(surface, self,
                                 art is not None and art.available)
        if view is not None and view.draws:
            ldrright.draw_view_box(surface, self, view, self._state, art)
        ldrright.draw_galaxy_box(surface, self, self._state, art)
        ldrdraw.draw_rows(surface, self, self._rows, art, self._lit())
        self._draw_buttons(surface)
        self._draw_strips(surface)
        if view is not None and view.state == ldrwire.POPUP:
            ldrdialog.draw_popup(surface, self, view, self._popup_words(),
                                 art, self._state)
        if view is not None and view.state == ldrwire.IN_BOX:
            from screens.fleets import fltbox
            fltbox.draw(surface, self, self._state)
        if self._skill_help is not None:
            ldrdialog.draw_skill_help(surface, self, *self._skill_help, art)
        self.render_help(surface)

    def _lit(self):
        """The leaders drawn in the selected colours: the one under the
        pointer (`_officer_scanned`, officer.cpp:1397) and, with the
        block, the selected one (:3608-3622)."""
        lit = set()
        if self._hover is not None:
            lit.add(self._hover)
        block = self._view.block if self._view else None
        if block is not None:
            for key in ("selected", "scanned"):
                if int(block.get(key, -1)) >= 0:
                    lit.add(int(block[key]))
        return lit

    def _draw_buttons(self, surface):
        """In the order `Draw_Officer_Screen_` draws them (officer.cpp:
        778-839), which is what lets hire mode's panel cover POOL and
        DISMISS as it does in the original."""
        view, art = self._view, self._art
        if view is None:
            return
        live, hire_mode, mode = self._shown
        colony = view.view == ldrgeom.VIEW_COLONY
        for name, mode_on in (("dismiss", 2), ("pool", 1)):
            if name in live:
                ldrdraw.draw_button(surface, self, art, name,
                                    frame=1 if mode == mode_on else 0)
            else:
                ldrdraw.draw_button(surface, self, art, name, dull=True)
        if "hire" in live:
            ldrdraw.draw_button(surface, self, art, "hire")
        elif not view.for_hire_here():
            ldrdraw.draw_button(surface, self, art, "hire", dull=True)
        if hire_mode:
            self._draw_hire_panel(surface)
        if "cancel" in live:
            ldrdraw.draw_button(surface, self, art, "cancel")
        for name in ("return", "prev", "next"):
            ldrdraw.draw_button(surface, self, art, name)
        if not colony:
            ldrdraw.draw_button(surface, self, art, "scroll_up")
            ldrdraw.draw_button(surface, self, art, "scroll_down")
        ldrdraw.draw_button(surface, self, art, "tab_colony",
                            frame=1 if colony else 0,
                            at=ldrgeom.TAB_DRAW["tab_colony"])
        ldrdraw.draw_button(surface, self, art, "tab_ship",
                            frame=0 if colony else 1,
                            at=ldrgeom.TAB_DRAW["tab_ship"])

    def _draw_hire_panel(self, surface):
        """OFFICER.LBX 17 at (300, 441) and the cost of the leader under
        the pointer — "%d bcs and %d bc/turn" or "%d bcs, no
        maintenance" (officer.cpp:796-808)."""
        art = self._art
        x, y = ldrgeom.HIRE_PANEL_AT
        w, h = ldrgeom.HIRE_PANEL_SIZE
        r = ldrdraw.rect(self.layout, (x, y, x + w - 1, y + h - 1))
        sprite = art.sprite("hire_panel") if art and art.available else None
        if sprite is not None:
            surface.blit(ldrdraw.stretched(sprite, r), r.topleft)
        else:
            ldrdraw.draw_box(surface, self, (x, y, x + w - 1, y + h - 1))
        if self._hover is None or self._view is None:
            return
        from core import leaderskills as ls
        view = self._view
        cost = ls.hire_cost(view.leaders, self._hover, view.player,
                            self._warlord_of)
        upkeep = ls.maintenance(view.leaders, self._hover, view.player,
                                self._warlord_of)
        template = self._words.hstring(0x129 if upkeep == 0 else 0x121)
        if not template:
            return
        text = hestrings.printf(template, cost) if upkeep == 0 else \
            hestrings.printf(template, cost, upkeep)
        tx, ty = ldrgeom.HIRE_COST_AT
        at = ldrdraw.point(self.layout, tx, ty)
        fit_w = ldrdraw.rect(self.layout,
                             (tx, ty, tx + ldrgeom.HIRE_COST_FIT_W - 1, ty)).w
        ldrdraw.blit_text(surface, self.style, text, at[0], at[1], fit_w,
                          ldrdraw.font_px(self.layout, "cost"),
                          ldrdraw.text_colour(art, "normal"))

    def _draw_strips(self, surface):
        """The strip under the view box (officer.cpp:810-826, :695-727)
        — only where the wire names its subject (open fix 30)."""
        view, state = self._view, self._state
        if view is None or view.block is None or state is None:
            return
        text = ""
        if view.view == ldrgeom.VIEW_COLONY:
            text = self._star_strip(int(view.block.get("star_displayed", -1)))
        ldrdraw.draw_strip(surface, self, ldrgeom.VIEW_STRIP, text, self._art)

    def _star_strip(self, star):
        """The star's name, or "%s (%s)" with its leader, or HESTR
        0x92/0x93 with the ETA (officer.cpp:810-826)."""
        stars = getattr(self._state, "stars", None) or []
        if not 0 <= star < len(stars):
            return ""
        name = stars[star].name
        slots = list(getattr(stars[star], "officer_index", []) or [])
        me = self._view.player
        leader = slots[me] if 0 <= me < len(slots) else -1
        if leader < 0 or leader >= len(self._view.leaders):
            return name
        rec = self._view.leaders[leader]
        if int(rec.eta) < 1:
            return f"{name} ({rec.name})"
        template = self._words.hstring(0x92 if int(rec.eta) == 1 else 0x93)
        return hestrings.printf(template, name, rec.name, int(rec.eta)) \
            if template else name

    def _popup_words(self):
        """What `ldrdialog.draw_popup` needs to name a leader."""
        from core import leaderskills as ls

        def parts(rec, idx):
            level = ls.shown_level(rec, idx, self._warlord_of)
            title = self._words.estring(ls.level_name_estring(rec, level))
            return level, title, ldrrows.the_word(self._words, idx)
        return {"words": self._words, "name_parts": parts}

    # ── Input — `ldrinput` holds the rules; these only route ──

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        return ldrinput.click(self, screen_x, screen_y)

    def handle_right_button(self, down, screen_x, screen_y):
        return ldrinput.right_button(self, down, screen_x, screen_y)

    def open_help_at(self, screen_x, screen_y):
        return ldrinput.open_help(self, screen_x, screen_y)

    def handle_mouse_motion(self, screen_x, screen_y):
        ldrinput.hover(self, screen_x, screen_y)
        return super().handle_mouse_motion(screen_x, screen_y)

    def handle_key(self, key):
        if self.help_consumes_key(key):
            return
        ldrinput.key(self, key)
