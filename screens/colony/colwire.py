"""The colony screen's state off the wire — read, validated, or refused.

**WHICH COLONY IS NOT GUESSED** (work order 180 B3, the order's own words:
"HD must not guess the colony"). `COLONY::Colony_Screen_` derives it from
`MOX::_screen_data` and `COLONY::_orbit_temp` (colony_main.cpp:249-255),
and none of it was on the wire. Open fix 35's "COLS" block carries the
pair AND the handle; this module uses the colony only when the two AGREE,
because the first tick at screen 1 carries the previous colony's handle
(`Screen_Control_` ticks before it dispatches, mox2.cpp:40-41). Without
the block `claims()` is False and the dispatcher never gives the id to
this screen — the game's picture, exactly as before (the safety net).

The states, and what the screen does in each:

    READY     the block agrees and the list is the screen's own: HD draws
    WAITING   the pair and the handle disagree (the first tick) — the
              hand-over gate holds the last HD frame (180 A2)
    GAME_BOX  the list is not the screen's own: a text box, a
              confirmation, the transport or troop popup — a modal HD has
              no view for; the net shows it (`handover_is_modal`)

**AND ONLY WITH ALL FOUR OF ITS BLOCKS** — COLS (35), placement CBLD (36),
the status word's CEVT (37), the product's cost and turns CPRD (38), which
the engine writes together on screen 1. Work order 181 applied the series
and `tools/version_check.py` requires it, so an engine that sends COLS
without the other three is not one this tree runs against; it gets the
game's picture (the safety net), never a colony screen with a hole where a
value would be. Until 181 each absent block was an HD STATE drawn as
nothing; with the claim asking for all four there is no such state left.
A CPRD that names another product than the colony's first queue item is
read in the same snapshot as the record and cannot disagree with it; if it
ever does, the screen WAITS rather than draw a bar for the wrong item.
"""
from core.structs import colony as colony_struct
from core.structs import leader as leader_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

from . import colgeom as geom

READY, WAITING, GAME_BOX = "READY", "WAITING", "GAME_BOX"


#: The blocks the engine writes on screen 1 (open fixes 35-38).
BLOCKS = ("colony_screen", "colony_placement", "colony_events",
          "colony_product")


def claims(state):
    """The dispatcher's question: may this screen take id 1 at all?"""
    return (getattr(state, "current_screen", None) == geom.GAME_SCREEN_ID
            and all(getattr(state, k, None) is not None for k in BLOCKS))


def live_field(fields, ident):
    """The live field for a `colgeom` identity `(type, x, y)`, or None.
    `type` None matches any (BUY is type 0 buyable, 7 not)."""
    ftype, x, y = ident
    return next((f for f in (fields or [])
                 if (f.x, f.y) == (x, y)
                 and (ftype is None or f.field_type == ftype)), None)


def hotkey_field(fields, key, ftype=None):
    return next((f for f in (fields or [])
                 if f.hotkey == ord(key) and f.index != 0
                 and (ftype is None or f.field_type == ftype)), None)


class View:
    def __init__(self, state):
        self.state = WAITING
        self.reason = ""
        self.index = -1
        self.colony = self.planet = self.star = None
        self.system = [None] * star_struct.PLANET_SLOTS
        self._read(state)

    @property
    def draws(self):
        return self.state == READY

    def _read(self, state):
        block = getattr(state, "colony_screen", None)
        if block is None:
            self.reason = ("Which colony the game shows is not on the wire "
                           "(open fix 35).")
            return
        self.block = block
        planets = [planet_struct.parse(r) for r in
                   (getattr(state, "planets_raw", None) or [])]
        at = [p for p in planets if p.star_index == block["star"]
              and p.orbit == block["orbit"]]
        derived = at[0].colony_index if at else -1
        raws = getattr(state, "colonies_raw", None) or []
        if derived < 0 or derived != block["colony"] \
                or not 0 <= derived < len(raws):
            self.reason = (f"The star and orbit name colony {derived}, the "
                           f"screen's handle says {block['colony']} — the "
                           f"first tick at screen 1, not settled yet.")
            return
        ev = getattr(state, "colony_events", None)
        prod = getattr(state, "colony_product", None)
        record = colony_struct.parse(raws[derived])
        if ev is None or ev.get("plague") is None or prod is None \
                or prod["producing"] != record.producing[0]:
            self.reason = ("The status word's or the product's block does "
                           "not describe this colony yet (open fixes 37, "
                           "38).")
            return
        # EVERY BLOCK AGREES: the page is known whether or not a box of the
        # game's covers it — GAME_BOX draws it behind the App's box (work
        # order 196 A), only the list below decides which state this is.
        self.index = derived
        self.colony = record
        self.planet = at[0]
        stars = getattr(state, "stars", None) or []
        self.star = stars[block["star"]] if 0 <= block["star"] < len(stars) \
            else None
        by_index = dict(enumerate(planets))
        if self.star is not None:
            self.system = [by_index.get(i) if i >= 0 else None
                           for i in star_struct.planet_indices(self.star)]
        self.drawing_display = block["drawing_display"]
        self.autobuild_enabled = bool(block["autobuild_enabled"])
        players = getattr(state, "player_raw", None) or []
        owner = self.colony.owner
        self.owner_traits = (player_struct.traits(player_struct.parse(
            players[owner])) if 0 <= owner < len(players) else None)
        # The Colonies screen's own row model for this colony — the icon
        # walk, the figures, the net production — one source for both
        # screens. None for a colony that is not the local player's.
        self.row = next((r for r in colonyrows.build_rows(state)
                         if r["index"] == derived), None)
        if live_field(getattr(state, "fields", None), geom.RETURN) is None:
            self.state = GAME_BOX
            self.reason = ("The game has opened its own box over the colony "
                           "screen; its fields are the only ones on the "
                           "wire until it is answered.")
            return
        self.state = READY

    # ── What the screen draws, each from one source ──────────────────

    def blockaded(self, player_num):
        """The star's bit for the player the screen runs as (:832)."""
        if self.star is None:
            return False
        return bool((self.star.blockaded >> (int(player_num) & 0x1F)) & 1)

    def events(self, state):
        """(plague, pop boom) from open fix 37's CEVT — a READY view has it
        for this colony (`_read`)."""
        ev = state.colony_events
        return ev["plague"], ev["pop_boom"]

    def placement(self, state):
        """Open fix 36's grid and satellites (read, not placed: UNVERIFIED
        `building_placement`, see `coldraw._buildings`)."""
        return state.colony_placement

    def product(self, state):
        """Open fix 38's (cost, turns) for what this colony produces — a
        READY view has CPRD naming the colony's own first item (`_read`)."""
        p = state.colony_product
        return p["cost"], p["turns"]

    def pop_line(self):
        """`Draw_Info_Name_And_Pop_`'s numbers (colony_main.cpp:858-870):
        assigned pops plus the round-off's thousands, the remainder, the
        growth — the three %d of E 424."""
        c = self.colony
        roundoff = sum(c.pop_roundoff[:10])
        growth = sum(c.pop_growth[:10])
        assigned = sum(1 for w in c.pop[:c.n_pops]
                       if colony_struct.pop_is_assigned(w))
        return assigned + roundoff // 1000, roundoff % 1000, growth

    def buildings(self):
        """The building ids this colony has (`buildings[]`, @310)."""
        return [i for i, n in enumerate(self.colony.buildings) if n]

    def units(self):
        """`military[2]` @304 — the two unit counts the strip draws."""
        return list(self.colony.military[:2])

    def officer(self, state):
        """(name, eta) of the leader the star keeps for the player the
        screen runs as, or None (`Draw_Colony_Info_Officer_`,
        colony.cpp:706-734: `_star[star].officer_index[_PLAYER_NUM]`)."""
        if self.star is None:
            return None
        me = int(getattr(state, "player_num", 0) or 0)
        idx = self.star.officer_index[me] if 0 <= me < 8 else -1
        leaders = getattr(state, "leaders_raw", None) or []
        if idx < 0 or idx >= len(leaders):
            return None
        leader = leader_struct.parse(leaders[idx])
        return leader.name, int(leader.eta)
