"""Research Select — orion2re SELECT NEW RESEARCH, wire id 53.

`TECH::_Tech_Select_(0)` (tech.cpp:111-395), reached at turn start when
a project completes: `Display_Report_Aux_` -> `Has_Research_Breakthrough_`
or `Set_Initial_Tech_` -> `TECH::Tech_Select_` (report.cpp:474, :513).
The game reports SCREEN_MAIN throughout (mainscr2.cpp:119) and open
fix 24 gives it the synthetic **53** on the wire instead.

Built by work order 130 E. STRUCTURE ONLY — frame and artwork come
later (Data, 17 September: "Rahmen und Visuelles kommen später
darüber").

WHAT DRIVES THE GAME FROM HERE, and how (decision 20):

    a row      ACTIVATE_FIELD on the row's field, looked up in the
               CURRENT field list BY SHAPE (`researchlist.row_field`
               -> `core.livefields.live_field`), never by a remembered
               index. Open fix 25 is what makes that mean the row:
               without it the game commits whatever its own pointer
               rests on, or dereferences null (open fix 23).

Nothing else sends anything. There is no exit: select mode has no ESC
field and cancel is disabled (tech.cpp:131, fields.cpp:983-988), so the
original ignores ESC and so does this screen — `handle_key` is
overridden to send NOTHING, because `ScreenBase` would otherwise
forward every key press to a dialog that has no way out but a commit.

THE SCREEN REFUSES BEFORE IT SENDS (decision 33), and it refuses to
DRAW before that. Every entry runs
`researchlist.validate_against_fields`: the reconstruction must agree
with the game's own field list — one hidden row per offered
application, in order, one radio per non-empty category. If it does
not, or the extracted names are absent, the screen does not draw a list
it cannot vouch for: it hands over to the fallback view, which since
work order 130 A shows the game's own picture and forwards clicks, and
it logs why. That is what this order has instead of a reporting stop.

NOT ACCEPTED YET, and the reason is not ours: OPEN FIX 26.
`SELECT NEW RESEARCH` commits a row BY ITSELF, about a second and a half
after the science room hands over to it — measured 18 September 2026
with a send counter proving the client sent nothing. Data's counter-test
of 19 September (same binary, no client connected, the completion dialog
clicked away with the real mouse) shows the list WAITS, so open fix 25
is not the cause; the injected dismissal of that dialog and a connected
client as such are both still suspect and not separated. OPEN, deferred
by Data.

**THE PLAYER'S WAY ROUND IT, while open fix 26 is open: click the
completion dialog away in the orion2re window with the real mouse. The
research selection then waits, and this screen can be used for the
choice.**

That sentence is here, in `doc/orion2re_open_fixes.md` and in
`v3_projektstatus.md`, and a smoke check fails if it leaves any of them
while open fix 26 still says OPEN. The rest of what this screen still
owes — the third live choice, two resolutions, the work order 128 crash
case, the promotion of `tech_applications` out of `unverified.py`, and
the six always-open fields and uncreative races never compared against
the original — is the status document's list.

MARKED, and each held by a smoke check so the marking cannot quietly
disappear (decision 61):

  OMISSION      the science room animation on the left strip
                (`SR_R%x_SC.LBX`, tech.cpp:245-273) — artwork, not
                extracted
  OMISSION      the category list popup (`_Tech_List_`, tech.cpp:781+),
                which is display-only and out of scope for this build
  OMISSION      the description box a right click inside the panel
                opens (tech.cpp:323-337, `Draw_Application_Description_`)
                — so a right click inside the panel does NOTHING here
                rather than something else
  OMISSION      the little arrow and the cycling selection box
                (`Draw_Little_Arrow_`, tech.cpp:740)
  HD EXTENSION  the title: the original's headline is part of the
                TECHSEL art and is not a string tech.cpp prints
  DEVIATION     the category label is printed as text where the
                original paints it into the panel art; the word itself
                is the game's own (billtext 64 + group)
  DEVIATION     a name too wide is SHRUNK, where `Squeeze_Print_`
                compresses the glyphs (panel.py)
"""
import logging

from core import billtext, research, researchlist, technames
from core.screen_base import ScreenBase
from core.structs import player as player_spec
from core.structs import settings as settings_spec

from . import native, panel

log = logging.getLogger("research_select")

#: Every name this module marks, and what kind of marking it is. The
#: smoke test reads THIS, so a marking cannot be removed from the
#: docstring and left in the code or the other way round.
MARKED = {
    "science_room_animation": "OMISSION",
    "category_list_popup": "OMISSION",
    "description_box": "OMISSION",
    "little_arrow": "OMISSION",
    "title": "HD EXTENSION",
    "category_label_as_text": "DEVIATION",
    "shrink_instead_of_squeeze": "DEVIATION",
}

#: THE COST SUFFIX IS THE GAME'S, indexed by `MOX::_settings.language`
#: (tech.cpp:631-639). A language the original has no case for falls to
#: " RP", which is what its own `else` does. Transcribed here rather
#: than put in `layout.json`, because it is the original's wording and
#: not OrionLayer's — decision 15 is about the words a renderer must
#: not own, and these are words the GAME owns.
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


class ResearchSelectScreen(ScreenBase):
    SCREEN_NAME = "research_select"
    GAME_SCREEN_ID = 53         # synthetic, open fix 24, wire only
    USE_FRAME = False

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

    # ── Lifecycle ─────────────────────────────────────────

    def enter(self, game_state=None):
        super().enter(game_state)
        self._data = self.app.res.load_json(
            "screens/research_select/layout.json", {}) or {}
        language = (getattr(self.app, "settings", {}) or {}).get(
            "language", "en")
        self._names = technames.TechNames(language)
        self._wording = billtext.BillText(language)
        self._hover = None
        self._sent = False
        # The title's WORDS come from layout.json and not from
        # boxes.json, so the wording has one home (decision 15) and the
        # F5 editor cannot end up owning a sentence.
        for box in self.boxes:
            if box.name == "title":
                box.style["label"] = self._data.get("title", "")
        unseated = native.seat(self.boxes, self.layout,
                               native.BOX_NATIVE)
        assert not unseated, (
            f"{unseated} are in boxes.json and not in native.BOX_NATIVE. "
            f"A box this screen cannot seat draws at the origin and reads "
            f"as a layout bug rather than a missing entry")
        self.update(game_state)

    def on_resize(self):
        super().on_resize()
        native.seat(self.boxes, self.layout, native.BOX_NATIVE)

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
            log.warning("research select hands over to the original "
                        "picture (%s): %s", self._state,
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
        entries = researchlist.reconstruct(
            tech_fields, tech_applications, current_field=0,
            select_mode=True)
        problems = researchlist.validate_against_fields(
            entries, getattr(game_state, "fields", None), select_mode=True)
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
            return list(view.tech_fields), list(view.tech_applications)
        except (AttributeError, IndexError, ValueError, TypeError):
            return None

    # ── Rendering ─────────────────────────────────────────

    def render(self, surface):
        super().render(surface)
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
        panel.draw(surface, self.layout, self.style, self._entries,
                   self._hover, words, self._names, self._wording)

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
        passes `research_accumulated`. So this is the FULL cost, and
        that is not an omission.
        """
        if not entry.offered:
            return None
        return f"{research.cost(entry.field)}{self._cost_suffix}"

    # ── Input ─────────────────────────────────────────────

    def row_at(self, screen_x, screen_y):
        """(entry index, row) under a WINDOW point, or None.

        Window -> reference -> native, then tested against
        `Entry.row_rect`. One rectangle, and the hit test reads the
        same one the drawing does (decision 5).
        """
        if self._state != READY:
            return None
        point = native.from_hd_point(
            self.layout.to_ref(screen_x, screen_y), self.layout)
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
        """Nothing. Select mode has no way out but a commit.

        `ScreenBase.handle_key` forwards every key to the game. Here
        that would be a key into a dialog whose cancel is disabled
        (tech.cpp:131) and whose only ESC field does not exist in this
        mode — so the original ignores it, and so does this.
        """
        return

    def handle_right_button(self, down, screen_x, screen_y):
        """Help outside the panel; NOTHING inside it.

        Inside the panel the original opens the description box for the
        choice under the pointer (tech.cpp:323-337). That box is not
        built, and decision 61 is explicit that a behaviour HD cannot
        reproduce is not approximated: HD does nothing there rather
        than guess. Outside, help id 254 works as on every screen.
        """
        return super().handle_right_button(down, screen_x, screen_y)

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
