"""The research panel's behaviour, for both of its modes.

`TECH::_Tech_Select_(changing_tech)` (tech.cpp:111-395) is ONE function
in the original, entered two ways:

    select (0)  at turn start when a project completes, wire id 53
                (synthetic, open fix 24). No way out but a commit.
    change (1)  from the galaxy map's research window, wire id 36 —
                the engine's own SCREEN_TECH_CHANGE. Leaves unchanged
                through its exit button.

So this is one class with two configurations, which is what work order
165 asks for and what the redundancy audit's lesson asks for. The
geometry is `core.researchnative.Geometry`, the drawing is
`core.researchpanel`, and both take the mode the same way.

WHAT DRIVES THE GAME FROM HERE, and how (decision 20):

    a row      ACTIVATE_FIELD on the row's field, looked up in the
               CURRENT field list BY SHAPE (`researchlist.row_field`
               -> `core.livefields.live_field`), never by a remembered
               index. Open fix 25 is what makes that mean the row:
               without it the game commits whatever its own pointer
               rests on, or dereferences null (open fix 23).
    the exit   change mode only: ACTIVATE_FIELD on the exit button,
               found the same way. It leaves with nothing changed
               (tech.cpp:347-353).

Nothing else sends anything.

THE SCREEN REFUSES BEFORE IT SENDS (decision 33), and it refuses to
DRAW before that. Every entry runs
`researchlist.validate_against_fields`: the reconstruction must agree
with the game's own field list — one hidden row per offered
application, in order, one radio per non-empty category. If it does
not, or the extracted names are absent, the screen does not draw a list
it cannot vouch for: it hands over to the fallback view, which since
work order 130 A shows the game's own picture and forwards clicks, and
it logs why.
"""
import logging

import pygame

from core import billtext, research, researchlist, researchnative
from core import researchpanel, researchtechlist, technames
from core.researchpopups import ResearchPopupsMixin
from core.screen_base import ScreenBase
from core.structs import player as player_spec
from core.structs import settings as settings_spec

log = logging.getLogger("research")

#: THE COST SUFFIX IS THE GAME'S, indexed by `MOX::_settings.language`
#: (tech.cpp:631-639). A language the original has no case for falls to
#: " RP", which is what its own `else` does. Transcribed here rather
#: than put in a screen's `layout.json`, because it is the original's
#: wording and not OrionLayer's — decision 15 is about the words a
#: renderer must not own, and these are words the GAME owns.
COST_SUFFIX = {0: " RP", 1: " FP", 3: " RP", 4: " PR"}


def cost_suffix(language):
    """The unit the original prints after a research cost."""
    return COST_SUFFIX.get(language, " RP")


#: Why the screen is on the fallback, in the order they are tested.
READY = "ok"
NO_PLAYER = "no_player"
NAMES_MISSING = "names_missing"
WORDING_MISSING = "wording_missing"
UNVALIDATED = "unvalidated"


class ResearchPanelScreen(ResearchPopupsMixin, ScreenBase):
    """The research panel, in whichever of its two modes the subclass picks.

    `TECH::_Tech_Select_(changing_tech)` is ONE function in the
    original and this is one class: the differences are the four
    attributes below plus what `core.researchnative.Geometry` derives
    from the mode. A subclass sets them and adds nothing else.
    """

    USE_FRAME = False

    #: The "can draw" state, as a class attribute so
    #: `core/researchpopups.py` can test it without importing this
    #: module back — which would be a cycle — and without a second
    #: copy of the word.
    READY_STATE = READY

    #: "select" or "change" — everything else follows from it.
    MODE = "select"
    #: Where the screen's own wording lives.
    LAYOUT_PATH = ""
    #: Whether leaving is possible at all. Select mode has no ESC field
    #: and cancel is disabled (tech.cpp:131, fields.cpp:983-988), so the
    #: original ignores every key and so does this class; change mode
    #: leaves through its exit button, whose hotkey IS ESC
    #: (tech.cpp:198-200, fields.cpp:2608-2613).
    HAS_EXIT = False

    def __init__(self, app):
        super().__init__(app)
        self._data = {}
        self._entries = []
        self._hover = None       # (entry index, row) or None
        self._state = READY
        self._problems = []
        self._names = None
        self._wording = None
        self._sent = False       # one commit per visit (decision 21)
        self._cost_suffix = COST_SUFFIX[0]
        self._left = False       # change mode: the exit has been sent
        #: The category list popup, `TECH::_Tech_List_`. HD draws it
        #: and sends NOTHING for it: it is display-only in the original
        #: (`doc/tech_change_reading.md` §2), so the game stays in
        #: `_Tech_Select_`'s own loop with the panel's field list —
        #: which is also what keeps `validate_against_fields` passing
        #: while the popup is up.
        self._techlist = researchtechlist.TechListPopup()
        #: The two arrays the popup rebuilds its own list from, kept
        #: from the frame that parsed them rather than re-parsed: the
        #: popup opens on a click and the wire is what it opened over.
        self._tech = ([], [])
        #: `(current_research_field, current_research_application)` and
        #: `research_accumulated`, off the wire, refreshed by
        #: `_player_record` on every frame that has a record. Select
        #: mode never reads them — see `current_pair` and `cost_offset`.
        self._current = (0, 0)
        self._accumulated = 0
        #: TRAIT_CREATIVE off the wire. It decides whether the current
        #: field's rows are ALL marked (`researchpanel.marks_every_row`).
        self._creative = False
        self.geom = researchnative.Geometry(self.MODE)
        self._box_native = self.geom.box_native()

    # ── The three questions the two modes answer differently ──

    @property
    def select_mode(self):
        return self.MODE == "select"

    def current_pair(self):
        """What the original's SECOND colour marks (tech.cpp:686-696).

        Change mode marks the field being researched and its chosen
        application. Select mode has neither: `Tech_Select_` zeroes
        `current_research_field` before the list is built
        (tech.cpp:104-105), so it passes zeros and every row is drawn
        in the first colour.
        """
        return (0, 0) if self.select_mode else self._current

    def cost_offset(self):
        """What the entry cost has subtracted from it (tech.cpp:203, :221).

        Change mode passes `research_accumulated`, so an entry shows
        what is LEFT; select mode passes 0 and shows the full cost. The
        description box shows the full cost in BOTH modes, which is the
        original's design and not a bug —
        `doc/tech_change_reading.md` §3.
        """
        return 0 if self.select_mode else self._accumulated

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(self.LAYOUT_PATH, {}) or {}
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._names = technames.TechNames(language)
        self._wording = billtext.BillText(language)
        self._hover = None
        self._sent = False
        self._left = False
        self._techlist.close()
        # The title's WORDS come from layout.json and not from
        # boxes.json, so the wording has one home (decision 15) and the
        # F5 editor cannot end up owning a sentence.
        for box in self.boxes:
            if box.name == "title":
                box.style["label"] = self._data.get("title", "")
        unseated = researchnative.seat(self.boxes, self.layout,
                                       self._box_native)
        assert not unseated, (
            f"{unseated} are in boxes.json and not in the geometry's "
            f"own box table for mode {self.MODE!r}. "
            f"A box this screen cannot seat draws at the origin and reads "
            f"as a layout bug rather than a missing entry")
        self.update(game_state)

    def on_resize(self):
        super().on_resize()
        researchnative.seat(self.boxes, self.layout, self._box_native)

    def _render_background(self, surface):
        """Under an OVERLAY: the parent screen, and the panel's own fill.

        Change mode is a panel over the HD galaxy map — the GAME menu's
        pattern (decision 69) — and it is what the original does:
        `Draw_Mini_Main_Screen_` paints the map before the screen is
        switched (mainscr_main.cpp:700-703, `Tech_Change_`
        tech.cpp:1159-1161). A full-window background here would paint
        the map out, which is what this screen did until work order 165
        part F.

        **AND THE PANEL'S OWN AREA IS FILLED, WHICH IS THE SOURCE'S OWN
        LINE.** `Fill_(_g_scrn_x + 4, _g_scrn_y + 4, _g_scrn_x + 0x1D7,
        _g_scrn_y + 0x1D8, 0)` — palette index 0 — runs before the
        panel art is drawn over it (tech.cpp:290-291). The first build
        of this overlay left it out, and the galaxy map shone THROUGH
        the rows: clean in the side bands, unreadable where the text
        is. Found by LOOKING at the live capture, which is the only
        thing that would have.

        Select mode is a screen of its own — the original fills the
        same rectangle there (:300) and puts the science-room animation
        beside it rather than the map — so it keeps the shared texture,
        which covers that rectangle already.
        """
        if not self.IS_OVERLAY:
            super()._render_background(surface)
            return
        surface.fill(
            researchpanel.col("panel_fill", (0, 0, 0)),
            pygame.Rect(*researchnative.window_rect(self.geom.panel_rect,
                                                    self.layout)))

    def update(self, game_state=None):
        """Rebuild the list from the state, and decide whether to draw it.

        The reconstruction is redone rather than remembered: the field
        list is the signal (decision 21), and a list built from an
        earlier frame is exactly the remembered index this screen must
        not have.
        """
        previous = self._state
        self._cost_suffix = self._suffix_for(game_state)
        self._entries, self._state, self._problems = self._rebuild(game_state)
        if self._state != READY:
            self._hover = None
        if self._state != previous and self._state != READY:
            # Logged ONCE per change, not per frame: this runs at 60 Hz
            # and a reason repeated 3600 times a minute is a reason
            # nobody reads.
            log.warning("research %s hands over to the original "
                        "picture (%s): %s", self.MODE, self._state,
                        "; ".join(self._problems[:4]) or "no detail")

    def _suffix_for(self, game_state):
        """The cost unit for the language the game is running in.

        Absent settings are not an error state: the wire carries the
        block on every snapshot, and before the first one there is
        nothing to draw anyway. The fallback is the original's own
        `else`, not a guess of ours.
        """
        raw = getattr(game_state, "settings_raw", b"") or b""
        if len(raw) <= settings_spec.LANGUAGE_OFFSET:
            return COST_SUFFIX[0]
        return cost_suffix(raw[settings_spec.LANGUAGE_OFFSET])

    def _rebuild(self, game_state):
        """(entries, state, problems) for this frame's game state."""
        if self._names is not None and self._names.state != "ok":
            return [], NAMES_MISSING, [f"research names: "
                                       f"{self._names.state}"]
        if self._wording is not None and self._wording.state != "ok":
            return [], WORDING_MISSING, [f"panel wording: "
                                         f"{self._wording.state}"]
        record = self._player_record(game_state)
        if record is None:
            return [], NO_PLAYER, ["no player record on the wire"]
        tech_fields, tech_applications = record
        # `current_field=0` IN BOTH MODES, and the docstring of
        # `offered_field` says why: the game has zeroed it before the
        # list is built in select mode and zeroes it around the call in
        # change mode, so the current field IS offered in change mode
        # without anything here asking for it.
        entries = researchlist.reconstruct(
            tech_fields, tech_applications, current_field=0,
            select_mode=self.select_mode)
        problems = researchlist.validate_against_fields(
            entries, getattr(game_state, "fields", None),
            select_mode=self.select_mode)
        if problems:
            return entries, UNVALIDATED, problems
        return entries, READY, []

    def _player_record(self, game_state):
        """(tech_fields, tech_applications) off the wire, or None.

        THE LOCAL PLAYER IS `player_raw[player_num]`, which is how every
        other screen reads it (colonyrows, boxmodel, planetrows). The
        first version of this method asked for a `players` attribute
        that `core/game_state.py` has never had, and it was a headless
        check with a hand-made state object that let it through — the
        fake carried the name the code expected, so both were wrong
        together. Found by driving it live, which is the only thing
        that would have.

        BOTH are verified spec fields since work order 165 part A.
        `tech_applications` was quarantined in
        `core/structs/unverified.py` with one of decision 23's two
        sources until 22 September 2026; its second source is written
        out in `core/structs/player.py` beside the field.

        The validation against the game's own field list did NOT retire
        with the promotion, and the spec comment says why: the second
        source settles where the bytes are and that they are research
        statuses, not that status 1 means "this row appears on the
        game's own screen". `researchlist.validate_against_fields` is
        what tests that, on every entry, and the screen still hands
        over when it disagrees.
        """
        if game_state is None:
            return None
        raws = getattr(game_state, "player_raw", None) or []
        me = getattr(game_state, "player_num", 0) or 0
        if not 0 <= me < len(raws):
            return None
        raw = raws[me]
        if raw is None or len(raw) < player_spec.SPEC.size:
            return None
        try:
            view = player_spec.SPEC.parse(raw)
            self._current = (view.current_research_field,
                             view.current_research_application)
            self._accumulated = view.research_accumulated
            self._creative = player_spec.traits(
                view)[player_spec.TRAIT_CREATIVE] == 1
            self._tech = (list(view.tech_fields),
                          list(view.tech_applications))
            return self._tech
        except (AttributeError, IndexError, ValueError, TypeError):
            return None

    # ── Rendering ─────────────────────────────────────────

    def render_content(self, surface):
        """The eight entries, over the boxes and UNDER the help popup.

        `ScreenBase.render` ends with `render_help`, so a screen that
        drew after calling it painted over its own popup — which these
        two screens did until work order 165 part C, and which nobody
        saw because the only popup they had was right-click help on a
        strip the panel does not cover at every resolution.
        """
        if self._state != READY:
            return
        words = {
            # The placeholder row's label is the game's own message 62,
            # "Pure research" — a row that exists and CAN be picked
            # (tech.cpp:624-636), not an error line.
            "placeholder": self._wording.message(
                billtext.MSG_NO_APPLICATION) if self._wording else None,
            # A callable, because the cost is per entry and the entries
            # change every frame. `panel` asks for the one it is drawing
            # rather than being handed a table it could index wrongly.
            "cost": self.cost_text,
        }
        # SELECT MODE PASSES ZEROS for the current field and
        # application on purpose — `Tech_Select_` has zeroed the field
        # before this list exists (tech.cpp:104-105), so the original's
        # second colour has nothing to mark here. Change mode is what
        # gives it something.
        researchpanel.draw(surface, self.layout, self.style,
                           self._entries, self._hover, words, self._names,
                           self._wording, current=self.current_pair(),
                           creative=self._creative)
        # AND THE LIST POPUP OVER IT. The original saves the panel's
        # fields and draws the window on top (`Save_Field_Stats_`,
        # tech.cpp:889); here it is one more layer, still under the
        # help popup, which `ScreenBase.render` draws last.
        researchtechlist.draw(surface, self.layout, self.style,
                              self._techlist, self.geom.origin,
                              self._names, self._wording)

    def cost_text(self, entry):
        """The "N RP" string for one entry, as the original builds it.

        The number comes from `core.research` — one home for the table
        (work order 129 C) — and the suffix from the GAME'S OWN
        language byte since work order 165 part A: `tech.cpp:631-639`
        picks "%i RP", "%i FP" (language 1) or "%i PR" (language 4)
        from `MOX::_settings.language`, and that byte is in the
        settings spec now. It was printed as " RP" always, and marked
        as a deviation for it, for as long as the offset was missing.

        SELECT mode subtracts NOTHING: `_Tech_Select_(0)` passes a
        research_cost_offset of 0 (tech.cpp:221), where change mode
        passes `research_accumulated` (:203) — so change mode shows
        what is LEFT and select mode the full cost, and neither is an
        omission. The original clamps at 0 (:590-607) and so does this.
        """
        if not entry.offered:
            return None
        cost = research.cost(entry.field) - self.cost_offset()
        return f"{max(0, cost)}{self._cost_suffix}"

    # ── Input ─────────────────────────────────────────────

    def native_point(self, screen_x, screen_y):
        """The 640x480 pixel a window point is, or None outside the view.

        One conversion for the rows, the category buttons and the list
        popup — the product's own placement, never arithmetic of a
        caller's (decision 5).
        """
        return researchnative.from_hd_point(
            self.layout.to_ref(screen_x, screen_y), self.layout)

    def row_at(self, screen_x, screen_y):
        """(entry index, row) under a WINDOW point, or None.

        Window -> reference -> native, then tested against
        `Entry.row_rect`. One rectangle, and the hit test reads the
        same one the drawing does (decision 5).
        """
        if self._state != READY:
            return None
        point = self.native_point(screen_x, screen_y)
        if point is None:
            return None
        nx, ny = point
        for entry in self._entries:
            for row in range(len(entry.apps)):
                x1, y1, x2, y2 = entry.row_rect(row)
                if x1 <= nx <= x2 and y1 <= ny <= y2:
                    return (entry.index, row)
        return None

    def handle_mouse_motion(self, screen_x, screen_y):
        super().handle_mouse_motion(screen_x, screen_y)
        if self._techlist.visible:
            self._hover = None
            point = self.native_point(screen_x, screen_y)
            hit = (self._techlist.at(self.geom.origin, *point)
                   if point else None)
            self._techlist.hover = (hit[1], hit[2]) if hit and \
                hit[0] == "row" else None
            return
        self._hover = self.row_at(screen_x, screen_y)

    def handle_click(self, screen_x, screen_y):
        """A row commits that row. Anything else sends nothing.

        Decision 33: an input the game would refuse is refused here,
        before it goes out — and on this screen a wrong one is worse
        than refused, it is open fix 23's crash on a tree without open
        fix 25.
        """
        if self.help_consumes_click(screen_x, screen_y):
            return
        if self._techlist.visible:
            self.list_click(screen_x, screen_y)
            return
        if self.open_list_at(screen_x, screen_y):
            return
        hit = self.row_at(screen_x, screen_y)
        if hit is None:
            return
        if self._sent:
            # One commit per visit. The game leaves 53 on its own and
            # the dispatcher follows (decision 21, decision 22); a
            # second activation would land in whatever list replaced
            # this one.
            return
        entry = self._entries[hit[0]]
        if entry.placeholder:
            # "Pure research": the row exists and its app id is 0. The
            # original DOES let it be picked — it is how a field is
            # spent on points alone — and it is sent like any other row,
            # because the field it commits is the entry's.
            pass
        field = researchlist.row_field(
            getattr(self.app.client.state, "fields", None)
            if self.app.connected else None, entry, hit[1])
        if field is None:
            log.warning("research row %s.%s is not in the field list this "
                        "frame — nothing sent", hit[0], hit[1])
            return
        if not self.app.connected:
            return
        self._sent = True
        log.info("research: entry %s row %s -> ACTIVATE_FIELD %s "
                 "(field %s)", hit[0], hit[1], field.index, entry.field)
        self.app.client.activate_field(field.index)

    def handle_key(self, key):
        """ESC leaves in change mode, and nothing does in select mode.

        `ScreenBase.handle_key` forwards every key to the game. In
        SELECT mode that would be a key into a dialog whose cancel is
        disabled (tech.cpp:131) and which has no ESC field at all
        (tech.cpp:207) — the original ignores it and so does this.

        In CHANGE mode the exit button IS the ESC field
        (tech.cpp:198-200; `Interpret_Keyboard_Input_`,
        fields.cpp:2608-2613), so ESC and a click on the button are the
        same act and go out the same way: an activation of that field,
        found in the live list. Nothing else is forwarded, because
        nothing else does anything in the original's loop
        (tech.cpp:311-393).
        """
        import pygame
        if key != pygame.K_ESCAPE:
            return
        if self._techlist.visible:
            # The popup's whole-screen field carries the ESC hotkey
            # (tech.cpp:968), and `match_val == hidden_field_1` closes
            # the list and returns to the panel — it does not leave the
            # screen. So ESC under an open list never reaches the exit
            # button, in either mode.
            self._techlist.close()
            return
        if not self.HAS_EXIT:
            return
        self._leave()

    def _leave(self):
        """Send change mode's exit. It leaves with NOTHING changed.

        `input == accept_btn_id` is the one branch of the loop that
        does not commit (tech.cpp:347-353): it returns and the fields
        the player was looking at are untouched. The button's rect is
        not in the source — `Add_Button_Field_` takes it from the art
        (fields.cpp:366-367) and `doc/tech_change_reading.md` §2 has
        the end as NOT SETTLED — so it is found in the LIVE list by
        shape, never by a remembered index, exactly as a row is.
        """
        if self._left or self._sent or not self.app.connected:
            return
        field = self.exit_field()
        if field is None:
            log.warning("research %s: no exit button in the field list "
                        "this frame — nothing sent", self.MODE)
            return
        self._left = True
        log.info("research %s: exit -> ACTIVATE_FIELD %s",
                 self.MODE, field.index)
        self.app.client.activate_field(field.index)

    def exit_field(self):
        """The exit button in the live list, or None (change mode only).

        Its ORIGIN is the source's (`s + 189, 452`, tech.cpp:198-200)
        and its size is not, so the match is on the origin and on being
        the list's one BUTTON field with an ESC hotkey — which is what
        the original itself keys on.
        """
        if not self.HAS_EXIT or not self.app.connected:
            return None
        want = self.geom.exit_button_origin
        for f in (getattr(self.app.client.state, "fields", None) or []):
            if (getattr(f, "field_type", None) == researchlist.TYPE_BUTTON
                    and (f.x, f.y) == want):
                return f
        return None

    def handle_right_button(self, down, screen_x, screen_y):
        """Help outside the panel; the DESCRIPTION over a row inside it.

        The original's own order, and it is the order of two different
        mechanisms rather than a preference: a right button first walks
        the screen's help list (`Check_Help_List_`, fields.cpp:2916) and
        a hit swallows the click; only a right click that reaches the
        FIELD system comes back negative, and `_Tech_Select_` negates it
        and resolves it through `Set_Selected_Entry_` (tech.cpp:323-337).

        `Set_Selected_Entry_` matches `app_click_field_ids` and nothing
        else (tech.cpp:468-487), so it is the ROWS that answer a right
        click. An entry BLOCK, the whole-screen field and the panel's
        empty space match nothing and open nothing — which is why this
        returns False for them rather than finding something near by.
        """
        if not down:
            return super().handle_right_button(down, screen_x, screen_y)
        if self.help.visible:
            self.help.close()
            return True
        if self._techlist.visible:
            # While the list is up the panel is behind it and the help
            # list has been replaced by the popup's own
            # (`Tech_Change_List_*_Help_`, tech.cpp:915-931), whose
            # rectangles lie outside the window. A right click on a ROW
            # opens that application's description (:1003-1011);
            # anywhere else only redraws (:993-998).
            return self.list_describe(screen_x, screen_y)
        if self.open_help_at(screen_x, screen_y):
            return True
        return self.open_description_at(screen_x, screen_y)

    # ── What the screen says when it cannot draw ──────────

    @property
    def state(self):
        return self._state

    @property
    def problems(self):
        return list(self._problems)

    def fallback_reason(self):
        """The sentence for the state the screen is in, or None."""
        if self._state == READY:
            return None
        return (self._data.get("fallback", {}) or {}).get(self._state)

    def wants_original(self):
        """The fallback IS this screen's answer when it cannot vouch.

        Work order 130 C: "the screen does not draw a list it cannot
        vouch for: it hands over to the fallback view (now clickable,
        part A) and logs why." This is that hand-over, and it is what
        this order has instead of a reporting stop.
        """
        return self._state != READY

    def keep_lock(self, screen_id):
        return None
