"""The single-colony screen (wire id 1) — work order 180 B.

The original's `COLONY::Colony_Screen_` (colony_main.cpp:238-378) in the
HUD style. Inventory: `dev:doc/briefs/180-colony-inventory.md`.

**IT CLAIMS ITS ID ONLY WHEN THE GAME SAYS WHICH COLONY IT SHOWS**
(`claims`: open fix 35's "COLS" block with 36-38's, all APPLIED by work
order 181). Without them the dispatcher does not give id 1 to this screen,
and the game's own picture stands, exactly as before — "HD must not guess
the colony". With them, the first tick at id 1 still
carries the previous colony's handle, so the screen WAITS until the
star/orbit pair and the handle agree, and the hand-over gate (180 A2)
holds the last HD frame meanwhile.

**WHAT IT SENDS** — nothing the player did not choose (decision 65), each
field found in the list on the wire when the byte goes out (decision 20),
and every one through `core.colony_guard`, which refuses CRUNCH, TOGGLE
and the full-screen field [0] (work order 126's safety rule):

    ESC / RETURN      the ESC field [2], the RETURN button as fallback
    < / >             [6] / [7], the original's own keys (index +1 / -1)
    L / LEADERS       [17]      A  the autobuild field [18]
    B / BUY           [3]       CHANGE — the FIELD [4], never the key: a C
                                 reaches [5] (recalculate) first
                                 (fields.cpp:2608-2613) — DEVIATION
                                 `change_by_field` from decision 39's
                                 key-first order, for that reason
    a production row, morale   [13]..[16], [12] — the game's text box
    a planet of the system     its `_sys_disp_planet_fields` entry
    a pop move        one MSG_SET_JOBS (decision 52), picked locally and
                      sent on the drop (decision 47), the Colonies
                      screen's rules and sender unchanged
    to another colony one MSG_SETTLE_POPS: the colonists in hand dropped
                      on a planet of the system display, or on a row of
                      the transport popup the TRANSPORT button opens
                      (TRANSCRIPTION `transport_button`,
                      `transport_popup`, DEVIATION `transport_popup_hud`,
                      OMISSION `transport_plague_red`, HD EXTENSION
                      `transport_escape`, `transport_row_hover`;
                      `coltransfer`, `colxport`) — on an engine with open
                      fix 103 the original's `Send_Cluster_` to any colony:
                      its questions before the command, its "Settlers
                      Failed." and "Settlers Depart" after it, in HD's box
                      (TRANSCRIPTION `transfer_walk`, `transfer_boxes`,
                      DEVIATION `config_bound_send`; `colxfer`,
                      `colxferflow`; work order 316); on one
                      with open fix 92 alone a colony at the star, as many
                      as move without a question (TRANSCRIPTION
                      `settle_count`, DEVIATION `settle_without_fix103`)

THE COLONISTS IN HAND RIDE ON THE POINTER (work order 233, Data: "a figure
that is clicked is bound to the mouse and travels with the cursor; a click
into another field drops it there — as in the original"), TRANSCRIPTION
`carry`: the click on a figure takes it and every identical colonist after
it in the colony's array (`Pickup_Colonists_` -> `COLMOVE::Get_Cluster_`,
colony.cpp:1508-1517, :1621-1626; colmove.cpp:60-100) — so the count is
the clicked figure and the same kind right of it in the row; they leave
their row (`0x200`, coldraw.cpp:336) and hang on the pointer as
`COLMOVE::Draw_Cluster_` draws them, last, over everything
(colony_main.cpp:178-182; colmove.cpp:24-55). HD holds them itself
(decision 47; `core.carry`, the Races screen's spies' gesture) and sends
the drop as one command; from the drop on the rows show what the command
expects until the wire has it (SET DOWN IS SET DOWN, work order 228 C).
DEVIATION `carry_production`: the original recalculates the colony at the
pick-up (colony.cpp:1625), so its production rows count without the
colonists in hand; HD's show the colony as the wire has it until the drop.

TRANSCRIPTION `put_back` — how the original ends a carry: a drop on the
colonists' own row re-flags them (`Send_Cluster_` with their own job,
colmove.cpp:182-183), and leaving the screen — RETURN, ESC, LEADERS,
CHANGE, < / > — puts them back (`Reset_Field_Mode_` -> `Clear_Cluster_`,
colony.cpp:1108-1123, colony_main.cpp:357, colony.cpp:1561). Nothing was
sent for either, so nothing is. Every other click does what it does and
the colonists stay in hand (`Check_Job_Fields_` keeps `_field_mode` 1,
colony.cpp:1524-1532), a refused drop too (its box, then the cluster still
held, colmove.cpp:168-173); a right click is help where the original has
help and nothing elsewhere (F913). The galaxy-map inset is unreachable in
this engine and not built (OMISSION `galaxy_inset`).

A right click on a row of the building list asks the game for that
building's description (TRANSCRIPTION `building_info`, `colright`, work
order 200); a left click starts the game's own demolish of it through open
fix 111 (TRANSCRIPTION `building_demolish`, `coldemolish`, work order 325;
UNVERIFIED `building_demolish_live`). OMISSION `building_actions`: on an
engine without fix 111 a left click on a row sends nothing, because the
game's handler reads the real pointer's polygon and an activated field
lands wherever that pointer is (`coldemolish.offered` is the gate).
Everything else is not sent: recalculation ([5] is a cheat with
`_cheats`), and any key not listed.
"""
import logging

import pygame

from core import carry
from core import colony_guard
from core import mouse as mouse_input
from core.buildnames import BuildingNames
from core.estrings import EStrings
from core import prodname
from core.screen_base import ScreenBase
from screens.colony_summary import (colonylist, colonymove, colonypick,
                                    colonysend)
from core import nativedraw as nd

from . import (colbuildings, colplanettip, coldemolish, coldraw,
               colgeom as geom, colright, colsettle, coltransfer, colwire,
               colwords)

log = logging.getLogger("colony")

KEYS = {pygame.K_ESCAPE: "esc", pygame.K_LESS: "<", pygame.K_GREATER: ">",
        pygame.K_l: "L", pygame.K_a: "A", pygame.K_b: "B"}
#: The keys and buttons that leave the screen: colonists in hand go back
#: (`Reset_Field_Mode_`, TRANSCRIPTION `put_back`).
LEAVES = {"esc", "<", ">", "L", "leaders", "return", "CHANGE"}


class Names:
    """The names the screen draws: planets, stars, buildings, products."""

    def __init__(self, state, buildings, strings):
        # RAW records: `colonyfacts.planet_name` parses them itself.
        self.planets = getattr(state, "planets_raw", None) or []
        self.stars = getattr(state, "stars", None) or []
        self._buildings, self._strings = buildings, strings

    def building(self, bid):
        name, _st = prodname.production_name(bid, self._buildings)
        return name or ""

    def product(self, pid, state):
        ships = prodname.ShipNames(state, getattr(state, "player_num", 0))
        return prodname.production_name(pid, self._buildings, self._strings,
                                        ships)


def _rest_pick(pick, outcome):
    """The colonists still in hand after a part settled
    (TRANSCRIPTION `settle_count`): the same kind from the same row, at
    the indices the settle leaves them, against the source's array as the
    engine will hold it (each word assigned again: the engine never
    unassigned them)."""
    n, words = outcome.pops[pick.colony]
    words = [w | colsettle.colony_struct.POP_MASK_ASSIGNED for w in words]
    rest = tuple(outcome.rest)
    return colonypick.Pick(pick.colony, pick.position, pick.job, pick.slot,
                           rest[0], colonymove.Cluster(rest), words, n,
                           pick.icon_count)


class ColonyScreen(ScreenBase):
    SCREEN_NAME = "colony"
    #: Its picture moves only with input, the game and the window: a frame
    #: that would draw it again is not drawn (work order 273, `core/drawgate`).
    STILL = True
    GAME_SCREEN_ID = geom.GAME_SCREEN_ID
    USE_FRAME = False
    SHELL_WORN = True
    #: THE SCREEN SHELL (work order 225; rebuilt by work order 231 E, Data's
    #: decision 7): the screen sits in the shell's content rectangle as
    #: Planets and Leaders do — the original's band as four panels across
    #: its width, the surface as the panel under them down to the
    #: rectangle's bottom, LEADERS above RETURN at its lower right, where
    #: the original has them (work order 232, Data's decisions 1 and 2;
    #: decisions 86, 87, 90 — until 232 they stood in a button row). Until
    #: 231 its 640x480 stage
    #: was fitted in proportion into the rectangle's height, so it kept a
    #: width of its own. Every region stands inside its panel's inset (the
    #: shell's); the surface's figures keep the band's sprite step
    #: (`sprites` False).
    REGIONS = (("col_build_buttons", geom.BUILD_BUTTONS, True, False,
                False, "col_build"),) + tuple(
        (name, native, True, False) for name, native in geom.BAND_REGIONS
    ) + ((geom.SURFACE_REGION[0], geom.SURFACE_REGION[1], True, False,
          False),)
    #: The two buttons of the build window are slanted and hit as drawn
    #: (decision 5); LEADERS and RETURN are the shell's (`self.shell`,
    #: placed by `colgeom.buttons`).
    SLANTED = ("CHANGE", "BUY")
    #: The shell's buttons and the original's fields behind them — LEADERS
    #: is the officer's frame where the star has one (`_shell_field`).
    SHELL_FIELDS = {"leaders": geom.LEADERS, "return": geom.RETURN}
    #: Their help (`_colony_screen_help_list`, erichelp.cpp:90-108).
    SHELL_HELP = {499: "leaders", 500: "return"}
    #: The title line's help (the same table): the status word, the title,
    #: "Pop" — answered where HD prints them (`coldraw.title_line_rects`).
    TITLE_LINE_HELP = {484: "status", 485: "title", 486: "pop"}

    def __init__(self, app):
        super().__init__(app)
        from core.hud import shell
        # LEADERS above RETURN on the surface's lower right (Data's
        # decision 1, work order 232), the original's place: no button
        # row, the surface reaches the rectangle's bottom (decision 2).
        self.shell = shell.Shell(
            title=self._shell_title,
            buttons=[(key, (lambda k=key: self._shell_word(k)),
                      (lambda layout, k=key: self._stack_rect(layout, k)))
                     for key in geom.STACK],
            row=False,
            enabled=lambda key: self._shell_field(key) is not None)
        self._state = None
        self._wire = None           # the snapshot's own view
        self._drawn_view = None     # what is drawn: the wire, the carry
        self._drawn_key = None
        self.carry = carry.Carry()  # the colonists in hand (`colonypick.Pick`)
        self.transfer = coltransfer.Transfer()   # open fix 103's moves
        self.send_ = None
        self.message = ""
        lang = (getattr(app, "settings", None) or {}).get("language", "en")
        self._strings = EStrings(lang)
        self._buildings = BuildingNames(lang)
        self._words = colwords.Words(self._strings)
        self._data = self.app.res.load_json("screens/colony/layout.json",
                                            {}) or {}
        self._move_words = (self.app.res.load_json(
            "screens/colony_summary/layout.json", {}) or {}).get("move", {})

    def exit(self):
        """What this visit left must not be the next visit's: a refused
        drop's message stayed drawn, at the hover line, until the first
        click of a later colony, and a hand the game's own screen change
        took us away from stayed full. Only the keys and buttons that
        leave from here put the hand back and cleared the move; the
        game leaving on its own went by neither."""
        self.carry.put_back()     # TRANSCRIPTION `put_back`: nothing was sent
        self.transfer.clear()
        self.message = ""
        # a move left half sent: no snapshot reaches an inactive screen, so
        # its tracker would never finish — and it blocks every click on the
        # next visit until it does — and what it expected would be drawn
        self.send_ = None
        self.carry.sent = None
        super().exit()

    # ── The dispatcher's and the gate's questions ────────────────────

    def claims(self, game_state):
        return colwire.claims(game_state)

    def wants_original(self):
        return self._view is not None and not self._view.draws

    def handover_is_modal(self):
        return self._view is not None and self._view.state == colwire.GAME_BOX

    def modal_is_box(self):
        # GAME_BOX is reached only after every block has been checked: the
        # screen's data is there and a box has replaced its list.
        return self.handover_is_modal()

    def fallback_reason(self):
        return self._view.reason if self._view is not None else ""

    # ── Per frame ─────────────────────────────────────────────────────

    @property
    def pick(self):
        """The colonists in hand — the carry's hand (`colonypick.Pick`)."""
        return self.carry.hand

    @pick.setter
    def pick(self, value):
        self.carry.take(value)

    def update(self, game_state=None):
        if game_state is None:
            return
        fresh = self.new_snapshot(game_state)
        if game_state is not self._state:
            self._state = game_state
            self._wire = colwire.View(game_state)
            if self.pick is not None and (not self._wire.draws or
                                          self._wire.index != self.pick.colony):
                # another colony, or a box: `Set_Colony_Screen_To_New_
                # Colony_` / leaving put the colonists back
                log.info("colony: colonists in hand put back (%s)",
                         "a box" if not self._wire.draws else "another colony")
                self.carry.put_back()
                if self.transfer.popup is not None:
                    self.transfer.popup = None
        if self.send_ is not None:
            self.send_.update(game_state)
            if self.send_.finished:
                if self.send_.state != colonysend.DONE:
                    self.message = self._move_words.get(
                        self.send_.reason, self.send_.reason or "")
                self.send_ = None
        coltransfer.update(self, game_state, fresh)
        outcome = self.carry.settle(
            lambda expected: expected.on_wire(game_state), fresh)
        if outcome == carry.CONFIRMED:
            self._retake_rest(game_state)
        elif outcome == carry.REFUSED:
            if self.carry.put_back():  # nothing went: the rest goes home
                self.message = ""
            if not self.message:
                self.message = self._e(colsettle.E_FAILED)

    @property
    def _view(self):
        """What is drawn and hit: the wire's view, or the carry's (`_drawn`),
        current after every click as after every snapshot."""
        return self._drawn()

    def _drawn(self):
        """The view drawn this frame: the wire's, with the colonists in hand
        out of their row, or — from a drop until the wire has it — what the
        drop expects (`colwire.Shown`). Rebuilt only when one of the three
        changed."""
        wire, hand, sent = self._wire, self.carry.hand, self.carry.sent
        key = (id(self._state), id(hand), id(sent))
        if key == self._drawn_key:
            return self._drawn_view
        self._drawn_key = key
        if wire is None or not wire.draws or (hand is None and sent is None):
            self._drawn_view = wire
            return wire
        state = colwire.Shown(self._state, sent.pops) if sent is not None \
            else self._state
        held = (hand.colony, hand.cluster.indices) if hand is not None \
            else None
        view = colwire.View(state, held)
        self._drawn_view = view if view.draws else wire
        return self._drawn_view

    def _e(self, index):
        return (self._words.e(index) or "").strip()

    def word(self, key):
        return (self._data.get("words") or {}).get(key, key.upper())

    def render(self, surface):
        self._render_background(surface)
        view = self._view
        if view is not None and view.draws:
            names = Names(self._state, self._buildings, self._strings)
            coldraw.draw(surface, self, view, self._state, self._words, names)
            if self.message:
                coldraw.text(surface, self, self.message,
                             *geom.HOVER_CENTRE, 600, "value", "negative",
                             align="center")
        self.render_shell(surface)
        if view is not None and view.draws:
            # HD EXTENSION `planet_hover` (colplanettip.py)
            colplanettip.draw(surface, self, view, self._state, self._words)
            coltransfer.render(self, surface, lambda: self.carry.draw(
                surface, mouse_input.pos(), self._draw_hand))
        self.render_help(surface)

    def _reload_boxes(self):
        """The file's boxes, and the building list's own when the file (a
        mod's, which replaces the base file whole) does not name it."""
        super()._reload_boxes()
        colbuildings.seat_default(self)

    def _draw_hand(self, surface, hand, pointer):
        """The colonists in hand at the pointer: `Draw_Cluster_`'s +5 / -10
        and 20 per figure, native px (colmove.cpp:38-50), at the band's
        scale, in array order — the Colonies screen's drawing
        (`colonylist.draw_held_cluster`), with this screen's figures."""
        row = self._view.row if self._view is not None else None
        figures = getattr(self, "_figures", None)
        if row is None or figures is None or figures.state == "missing":
            return
        colonylist.draw_held_cluster(surface, pointer, figures,
                                     row.get("held") or (),
                                     nd.native_scale(self.layout))

    def render_backdrop(self, surface):
        """The page behind the game's own box (work order 196 A) — "just
        colonized", BUY — which the original draws over this screen: in
        GAME_BOX every block has been checked, only the list is the box's."""
        view = self._view
        if view is None or view.state not in (colwire.READY, colwire.GAME_BOX):
            return
        self._render_background(surface)
        coldraw.draw(surface, self, view, self._state, self._words,
                     Names(self._state, self._buildings, self._strings))
        self.render_shell(surface)

    # ── Sending ──────────────────────────────────────────────────────

    def _live(self):
        return getattr(self.app.client.state, "fields", None) or []

    def send(self, field, label):
        """ACTIVATE_FIELD, through the one guard, into the live list."""
        if field is None or not self.app.connected:
            return False
        state = self.app.client.state
        try:
            colony_guard.check(field, getattr(state, "current_screen", -1))
        except colony_guard.Refused as err:
            log.warning("colony: %s — %s", label, err)
            return False
        log.info("colony: %s -> field %d", label, field.index)
        self.app.client.activate_field(field.index)
        return True

    def _hot(self, key, ftype=None):
        return colwire.hotkey_field(self._live(), key, ftype)

    def _field(self, ident):
        return colwire.live_field(self._live(), ident)

    # ── Input ────────────────────────────────────────────────────────

    def handle_key(self, key):
        if self.help_consumes_key(key) or not (self._view and
                                               self._view.draws):
            return
        if coltransfer.key(self, key, chr(key) if 0 < key < 128 else ""):
            return
        what = KEYS.get(key)
        if what is None:
            # the rest of the original's keys (C, the Alt cheats;
            # colony_main.cpp:980-1031): the one rule every screen shares
            # (work order 230 E)
            super().handle_key(key)
            return
        if what == "esc":
            sent = self.send(colwire.hotkey_field(self._live(), "\x1b")
                             or self._field(geom.RETURN), "RETURN")
        else:
            sent = self.send(self._hot(what), f"key {what}")
        if sent and what in LEAVES:
            self.carry.put_back()     # TRANSCRIPTION `put_back`
            self.transfer.clear()

    def handle_right_button(self, down, mx, my):
        # Colonists in hand stay in hand: the right button is help where the
        # original has help and nothing elsewhere (F913, P818). Then the
        # help regions (until work order 200 this override never let
        # them open), then a building's description (`colright`)
        if ScreenBase.handle_right_button(self, down, mx, my):
            return True
        return down and colright.answer(self, mx, my)

    def handle_click(self, screen_x, screen_y):
        if self.help_consumes_click(screen_x, screen_y):
            return None
        view = self._view
        if view is None or not view.draws or self.send_ is not None \
                or self.carry.sent is not None:
            return None
        if coltransfer.click(self, screen_x, screen_y):
            return None
        self.message = ""
        if self._job_click(screen_x, screen_y):
            return None
        if self.pick is not None and self._settle_click(screen_x, screen_y):
            return None
        # Anything else does what it does; colonists in hand stay in hand
        # unless the click leaves the screen (TRANSCRIPTION `put_back`).
        key = self.shell_click(screen_x, screen_y)
        if key is not None:
            f = self._shell_field(key)
            if f is not None and self.send(f, key.upper()) and key in LEAVES:
                self.carry.put_back()
            return None
        for key, ident in (("CHANGE", geom.CHANGE), ("BUY", geom.BUY)):
            f = self._field(ident)
            if f is not None and nd.field_slant_hit(self.layout, f,
                                                    screen_x, screen_y):
                if self.send(f, key) and key in LEAVES:
                    self.carry.put_back()
                return None
        # a row of the building list: the game's demolish (open fix 111;
        # TRANSCRIPTION `building_demolish`), colonists in hand stay in hand
        if coldemolish.click(self, screen_x, screen_y):
            return None
        for native in list(geom.PROD_ROWS.values()) + [geom.MORALE]:
            if nd.rect(self.layout, native).collidepoint(screen_x, screen_y):
                self.send(self._field((geom.TYPE_HIDDEN,) + native[:2]),
                          "info box")
                return None
        x1, y1, x2, y2 = geom.SYS_DISP
        for f in self._live():
            if f.field_type == geom.TYPE_HIDDEN and x1 <= f.x and \
                    f.x_end <= x2 and y1 <= f.y and f.y_end <= y2 + 8 \
                    and nd.field_hit(self.layout, f, screen_x, screen_y):
                self.send(f, "system display")
                return None
        # the marines and armour at the foot: the game's military field of
        # that kind, which opens its troop popup (colony.cpp:2007-2013;
        # HD's popup on open fix 98, work order 274)
        for kind, rect, native_x in getattr(self, "unit_hits", []):
            if not rect.collidepoint(screen_x, screen_y):
                continue
            # its own field starts at the figures' foot row, never at the
            # top: the full-screen field [0] shares x 0 and y_end 479 and
            # demolishes the building under the real pointer
            # (`core.colony_guard`)
            f = next((f for f in self._live()
                      if f.field_type == geom.TYPE_HIDDEN and
                      f.x == native_x and f.y_end == 479 and
                      f.y >= geom.UNIT_FIELD_TOP), None)
            if f is not None:
                self.send(f, "troops")
            return None
        return None

    def help_extra_rect(self, spec):
        """help.json's regions are the original's native rectangles, and
        the page stands where the original's does. Without this hook they
        resolved to nothing and no right click here ever opened help —
        found by work order 200 B's walk against the original's list."""
        key = self.SHELL_HELP.get(spec.get("help_id"))
        if key is not None:          # a shell button's help is its own rect
            return self.shell.rect(self.ref_layout, key)
        # the title line's three: where its words stand now — the status
        # word and "Pop" beside the plate, the title on it (work order 232)
        line = self.TITLE_LINE_HELP.get(spec.get("help_id"))
        if line is not None:
            from core.hud import shell
            return (shell.title_rects(self.ref_layout)[1] if line == "title"
                    else coldraw.title_line_rects(self)[line == "pop"])
        native = spec.get("native")
        return nd.rect(self.layout, native) if native else None

    def _shell_field(self, key):
        """The live field behind a shell button: LEADERS' button, or — with
        an officer at the star — the hidden field over his frame, which the
        original adds INSTEAD of the button (colony_main.cpp:994-999)."""
        f = self._field(self.SHELL_FIELDS[key])
        if f is None and key == "leaders":
            f = self._field(geom.OFFICER_FIELD)
        return f

    def _shell_word(self, key):
        """A shell button's word; the LEADERS slot carries the officer's
        name or his ETA where the original shows his frame there
        (`coldraw.officer_line`) — DEVIATION `officer_slot`: the original
        shows his portrait in a frame with the name under it."""
        view = self._view
        if key == "leaders" and view is not None and view.draws:
            line = coldraw.officer_line(view, self._state, self._words)
            if line:
                return line
        return self.word(key)

    def _stack_rect(self, layout, key):
        """LEADERS' or RETURN's rect: stacked in the surface panel as its
        box stands (`colgeom.buttons`) — the one rect for drawing and hit."""
        return geom.buttons(layout,
                            self.box_screen_rect(geom.SURFACE_REGION[0]))[key]

    def _shell_title(self):
        view = self._view
        # READY, and GAME_BOX: the page under the game's own box
        # (`render_backdrop`) wears its title too.
        if view is None or view.state not in (colwire.READY,
                                              colwire.GAME_BOX):
            return ""
        names = Names(self._state, self._buildings, self._strings)
        return coldraw.title_words(self, view, self._words, names)

    def _job_click(self, x, y):
        """The pop move: first click picks (locally), second drops (one
        command). The Colonies screen's rules and sender, unchanged."""
        view = self._view
        rows = [(j, nd.rect(self.layout, r)) for j, r in
                enumerate(geom.JOB_CELLS)]       # the drawn cells (226 G)
        job = next((j for j, r in rows if r.collidepoint(x, y)), None)
        if job is None:
            return False
        loaded = colonypick.pops_of(self._state, view.index)
        if loaded is None:
            return True
        pops, n_pops, max_farms = loaded
        if self.pick is None:
            hit = next(((j, k) for j, k, rect, _c in
                        coldraw.job_cells(self, view)
                        if rect.collidepoint(x, y)), None)
            if hit is None:
                return True
            outcome = colonypick.pick_at(pops, n_pops, hit[0], hit[1],
                                         view.index, 0, "name")
            if isinstance(outcome, colonypick.Refusal):
                self.message = colonypick.message(self._move_words, outcome)
            else:
                self.carry.take(outcome)
            return True
        if job == self.pick.job:
            self.carry.put_back()     # its own row: re-flagged, nothing sent
            return True
        outcome = colonypick.plan_move(self.pick, pops, n_pops, max_farms,
                                       view.index, job)
        if isinstance(outcome, colonypick.Refusal):
            # the original's refusal box, and the rest still in hand
            self.message = colonypick.message(self._move_words, outcome)
            return True
        if not self.app.connected:
            return True
        cluster = self.pick.cluster
        predicted = colonymove.predict_pops(pops, n_pops, max_farms,
                                            cluster, job)
        self.send_ = colonysend.Send(self.app.client, colony=view.index,
                                     target_job=job, cluster=cluster,
                                     predicted=predicted)
        self.carry.set_down(colsettle.Expected(
            {view.index: (n_pops, colsettle.jobs_of(predicted, n_pops))},
            {view.index: (n_pops, list(predicted))}))
        return True

    def _settle_click(self, x, y):
        """Colonists in hand dropped on a planet of the system display
        (TRANSCRIPTION `settle`, `colsettle`): another colony of the player
        at the star gets them in one command; a planet that is no colony,
        or a refusal HD can read, keeps them in hand with the game's own
        sentence; their own colony's planet puts them back
        (`Send_Cluster_` re-flags them, colmove.cpp:178-183)."""
        x1, y1, x2, y2 = geom.SYS_DISP
        for f in self._live():
            if not (f.field_type == geom.TYPE_HIDDEN and x1 <= f.x and
                    f.x_end <= x2 and y1 <= f.y and f.y_end <= y2 + 8 and
                    nd.field_hit(self.layout, f, x, y)):
                continue
            orbit = geom.sys_planet_orbit(f)
            if orbit is None:
                return False          # a summary: it does what it does
            pick = self.pick
            dest = colsettle.target(self._wire, orbit)
            if isinstance(dest, colsettle.Refusal):
                self.message = self._e(dest.estring)
                return True
            if dest == pick.colony:
                self.carry.put_back()
                return True
            if coltransfer.available(self):     # open fix 103
                coltransfer.start(self, dest)
                return True
            outcome = colsettle.plan(self._state, self._wire, pick, dest)
            if isinstance(outcome, colsettle.Refusal):
                self.message = self._e(outcome.estring)
                return True
            if not self.app.connected:
                return True
            pops = sorted(outcome.sent)
            log.info("colony: %d of %d colonists %s of colony %d -> colony "
                     "%d", len(pops), pick.size, pops, pick.colony, dest)
            self.app.client.settle_pops(pick.colony, dest, pops)
            self.carry.set_down(outcome)
            if outcome.rest:
                # TRANSCRIPTION `settle_count`: the rest stay in hand, and
                # the original's box names why and how many went
                # (colmove.cpp:366-372, :454-460) — HD's sentence line
                self.carry.take(_rest_pick(pick, outcome))
                self.message = self._settle_stopped(outcome)
            return True
        return False

    def _settle_stopped(self, outcome):
        """The original's "Settlers Failed." lines for a hand that went in
        part: the reason, then E 0x80 with the number sent (colmove.cpp:
        404, :454), on one line; `replace`, never `format`
        (decision 37). DEVIATION `settle_without_fix103`: the original
        shows them in a text box (E 0x1D6, colmove.cpp:366-372,
        :454-460); HD on the screen's message line."""
        sent = self._e(0x80).replace("%d", str(len(outcome.sent)))
        return " ".join(f"{self._e(outcome.stopped)} {sent}".split())

    def _retake_rest(self, state):
        """After the wire confirmed a part settled: the colonists still in
        hand are taken again from the wire's own array, so a later drop
        compares against what the engine holds (`Pick.stale`); if the wire
        does not hold them where the settle left them, they go back."""
        hand = self.pick
        if hand is None:
            return
        raws = getattr(state, "colonies_raw", None) or []
        if not 0 <= hand.colony < len(raws):
            self.carry.put_back()
            return
        from core.structs import colony as colony_struct
        rec = colony_struct.parse(raws[hand.colony])
        words = list(rec.pop)[:rec.n_pops]
        mask = ~colony_struct.POP_MASK_ASSIGNED
        if any(i >= len(words) or (words[i] & mask) != (hand.pops[i] & mask)
               for i in hand.cluster.indices):
            self.carry.put_back()
            return
        self.carry.take(colonypick.Pick(
            hand.colony, hand.position, hand.job, hand.slot, hand.pop,
            hand.cluster, words, rec.n_pops, hand.icon_count))
