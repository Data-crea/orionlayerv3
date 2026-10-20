"""The ship detail view outside a battle in HD — work order 317 (open fix 106).

`CMBTDRW1::Detailed_View_Ship` (cmbtdrw1.cpp:227-338; line numbers of the
branch `orionlayer` with open fix 106) opens over the galaxy map (a right
click on an own ship in the fleet box, mainscr.cpp:3631-3644), the Fleets
screen (a right click on an own big icon, flt1.cpp:625-636) and the
Leaders screen (the same, officer.cpp:1171-1177), and draws ONE ship
with `Combat_Draw_View_Ship` — the function the battle's scan draws too.
So HD draws it with the battle's scan, never a second copy (P824): `cbscan`
says what it shows from SHPV's record (`core/shipviewwire.py`) and the
snapshot's ship, leader and player records, `cbscanview` draws it over the
held frame of the screen that opened it, dimmed (the troop popup's way,
`core.overlays.HELD_KINDS`: the caller's own page cannot be drawn again
under id 81, its list is the view's).

  TRANSCRIPTION `ship_view`     the record the view draws, the battle's
                                scan's contents (TRANSCRIPTION
                                `scan_contents`) and its HD additions
                                (`scan_detailed`, `scan_officer`,
                                `scan_identity`, `scan_hull_cards`) as the
                                battle shows them; no battle turn
                                (INVENTION `scan_turn` needs a battle)
  TRANSCRIPTION `ship_view_close`  any click closes it (cmbtdrw1.cpp:304,
                                :314-322): HD activates the view's exit field
                                (SHPV names it, the list must agree); while
                                the name is edited the click goes as the
                                original's own click on the exit field,
                                which stores the typed name first
                                (fields.cpp:1304-1321) — an activation would
                                return before it (fields.cpp:191-201)
  TRANSCRIPTION `ship_view_name_edit`  the name is the view's continuous
                                input field (cmbtdrw1.cpp:300, 15
                                characters): a click on HD's name is an
                                injected click at the field's centre, which
                                opens it (fields.cpp:1288-1302, F904); the
                                keys go to it by the one rule every screen
                                shares (`core/keyfwd.py`, open fix 88's
                                TXTF says it is edited): printable but '_',
                                Backspace, Enter stores, ESC restores; the
                                name shown is TXTF's typed text while
                                edited, else SHPV's buffer; the view stores
                                it into the ship when it closes
                                (cmbtdrw1.cpp:327-332)
  TRANSCRIPTION `ship_view_right`  a right click closes nothing: the
                                original's answers -n for the field under
                                it, never the exit field, and the loop goes
                                on (fields.cpp:1333-1337, cmbtdrw1.cpp:
                                314-322); the caller has deactivated its
                                help list (mainscr.cpp:3639)
  HD EXTENSION `ship_view_esc`  ESC with the name not edited closes the
                                view, as HD's battle scan does (`cbpopups`);
                                the original's ESC answers -1 or nothing
                                (fields.cpp:961-966) and its view stays
  DEVIATION `ship_view_subject`  original = the view's subject decides
                                lines (cmbtdrw1.cpp:3268-3282, :3635,
                                :3752-3765): a non-combat ship (1) shows no
                                drive and no subsystem hits, a ship under
                                strategic combat (2) no armour total and no
                                subsystem hits, and a combat ship (0)
                                prints its shield maximum anew from
                                `TECHDATA::Shield_Strength` and the
                                multi-phase bonus; HD = the battle scan's one
                                view for every subject (work order 298),
                                the record's values — so with a damaged
                                shield generator HD's maximum is the
                                record's `shield_arc_max`, scaled by the
                                generator's hits (combinit.cpp:386-387),
                                lower than the original's
  DEVIATION `scan_card_click`   the battle's: a click on a row whose card is
                                up keeps the view
  HD STATE `ship_view_breakdown`  the values stand without the battle's
                                cards (HD EXTENSION `scan_breakdown`, a
                                round's sum, cbscanparts, combinit.cpp:
                                1053-1061): outside a battle the engine adds
                                `Get_Ship_Combat_Bonuses` (initship.cpp),
                                whose parts are not on the wire and against
                                which no card is checked; the original has
                                no card at all
  HD EXTENSION `ship_view_name_hint`  the whole name line is the name
                                field's hit area, marked by the HUD's
                                separator under it (`cbscanview`); the
                                original shows nothing until the field is
                                clicked
  HD STATE `ship_view_bare`     without the fix, see below
  UNVERIFIED `ship_view_live`   built against the engine's patch and stand-in
                                bytes only: no live run (Data stopped live
                                runs, work order 317); a live run has to
                                show the three openings, SHPV equal to the
                                engine's own view under F12, the close, the
                                stored name, the F12 notice without the fix

Without the fix the engine's view runs under its caller's id and HD cannot
draw it: the screen's F12 notice names it (`shipviewwire.bare_reason`,
`ScreenBase.no_view_reason`).
"""
import logging
import types

from core import keyfwd, mouse, msgbox, rightinfo, shipviewwire, textfields
from core import turnpopup

log = logging.getLogger("orionlayer")


def shown_name(view, state):
    """TXTF's typed text while the name is edited, else SHPV's buffer."""
    f = shipviewwire.name_field(state, view)
    entry = (getattr(state, "text_fields", None) or {}).get(
        f.index) if f is not None else None
    if entry is not None and entry["editing"]:
        return textfields.typed_text(entry), True
    return view["name"], False


def editing(state, view):
    """True while the engine edits the view's name (TXTF)."""
    return shown_name(view, state)[1]


class _Host:
    """What `cbscansources.Sources` reads off the battle screen — the
    tables, the art and the colours — for a view no battle hosts. The art
    is the battle screen's own when there is one (its detail and livery)."""

    def __init__(self, app):
        from core.kentext import ArcWords
        from core.shipparts import ShipPartNames
        self.app = app
        self._language = (getattr(app, "settings", {}) or {}).get(
            "language", "en")
        self._names = ShipPartNames(self._language)
        self._ken = ArcWords(self._language)
        battle = getattr(getattr(app, "dispatcher", None), "screens",
                         {}).get("combat")
        art = getattr(battle, "_art", None)
        if art is None:
            from screens.combat import cbart
            art = cbart.CombatArt()
        self._art = art
        self._play = types.SimpleNamespace(colours={})


def model(view, state, words):
    """`cbscan.build` for SHPV's record and the snapshot."""
    from screens.combat import cbscan
    unit = dict(view["unit"])
    unit["_index"] = None            # no battle: never the planet, unit 0
    # the record's own ship_idx is the view's (combinit.cpp:259)
    unit["ship_idx"] = view["ship_idx"]
    m, _players = cbscan.build_unit(unit, state, words)
    name, edited = shown_name(view, state)
    m.name = name + ("_" if edited else "")
    m.cards = None                   # HD STATE `ship_view_breakdown`
    # HD EXTENSION `ship_view_name_hint`: only an editable name is marked
    m.name_editable = int(view["name_field"]) >= 0
    return m


class View:
    def __init__(self):
        from screens.combat import cbscanview
        self.scan = cbscanview.View()
        self.base = None
        self._host = None
        self._sources = None
        #: (ship, snapshot) of the close sent: one per view, again after
        #: `turnpopup.RESEND_AFTER` unchanged snapshots
        self.sent = None

    def reset(self):
        self.base = None
        self.sent = None

    def sources(self, app):
        language = (getattr(app, "settings", {}) or {}).get("language", "en")
        if self._host is None or self._host._language != language:
            from screens.combat import cbscansources
            self._host = _Host(app)
            self._sources = cbscansources.Sources(self._host)
        return self._sources

    def render(self, surface, style, scale, view, state, app):
        """The scan of SHPV's ship over the held frame, dimmed."""
        self.base = msgbox.dimmed_base(surface, self.base, msgbox.DIM_ALPHA)
        surface.blit(self.base, (0, 0))
        src = self.sources(app)
        if self._host is not None:
            from screens.combat import cbdraw
            self._host._play.colours = cbdraw.player_colours(state)
        m = model(view, state, src.words())
        self.scan.draw(surface, style, scale, m, None,
                       src.pictures(view["unit"]), pointer=mouse.pos())

    # ── input ─────────────────────────────────────────────────────
    def action_at(self, x, y, view, state):
        """What a click at (x, y) sends: ("click", (nx, ny)) — an injected
        click at a native point —, ("activate", field), or None."""
        if self.scan.card_at(x, y):
            return None                     # DEVIATION `scan_card_click`
        name = self.scan.rects.get("name")
        if name is not None and name.collidepoint(x, y):
            f = shipviewwire.name_field(state, view)
            if f is None or editing(state, view):
                return None                 # the guard field's answer: none
            return ("click", ((f.x + f.x_end) // 2, (f.y + f.y_end) // 2))
        return self.close_action(view, state)

    @staticmethod
    def close_action(view, state):
        f = shipviewwire.exit_field(state, view)
        if f is None:
            return None
        if editing(state, view):
            return ("click", rightinfo.point_for(
                f, getattr(state, "fields", None) or []))
        return ("activate", f)

    @staticmethod
    def key_action(event, view, state):
        """("key", code) into the edited name, the close on ESC, or None."""
        import pygame
        fields = getattr(state, "fields", None) or []
        if editing(state, view):
            how, value, _why = keyfwd.decide("ship_view", fields, state, event)
            return ("key", value) if how == "key" else None
        if event.key == pygame.K_ESCAPE:
            return View.close_action(view, state)   # HD EXTENSION `ship_view_esc`
        return None

    def send(self, app, view, action):
        """Send `action`; a close goes once per view (`sent`)."""
        if action is None or not getattr(app, "connected", False):
            return False
        how, what = action
        if how == "key":
            app.client.inject_key(what)
            return True
        closing = how == "activate" or what != self._name_point(app, view)
        if closing:
            snap = app.client.stats.get("state", 0)
            key = view["ship_idx"]
            if self.sent is not None and self.sent[0] == key and \
                    snap - self.sent[1] < turnpopup.RESEND_AFTER:
                return False
            self.sent = (key, snap)
        if how == "activate":
            log.info("ship view: close, field %d", what.index)
            app.client.activate_field(what.index)
        else:
            log.info("ship view: click (%d, %d)", *what)
            app.client.inject_click(*what)
        return True

    @staticmethod
    def _name_point(app, view):
        f = shipviewwire.name_field(app.client.state, view)
        return None if f is None else ((f.x + f.x_end) // 2,
                                       (f.y + f.y_end) // 2)
