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

Every other block — placement (36), the status word (37), the product's
cost and turns (38) — is optional ON TOP of 35 and read only for a READY
colony; each absent one is an HD STATE where the value would be, never an
invented one.
"""
from core.structs import colony as colony_struct
from core.structs import leader as leader_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct
from screens.colony_summary import colonyrows

from . import colgeom as geom

READY, WAITING, GAME_BOX = "READY", "WAITING", "GAME_BOX"


def claims(state):
    """The dispatcher's question: may this screen take id 1 at all?"""
    return (getattr(state, "current_screen", None) == geom.GAME_SCREEN_ID
            and getattr(state, "colony_screen", None) is not None)


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
        if live_field(getattr(state, "fields", None), geom.RETURN) is None:
            self.state = GAME_BOX
            self.reason = ("The game has opened its own box over the colony "
                           "screen; its fields are the only ones on the "
                           "wire until it is answered.")
            return
        self.state = READY
        self.index = derived
        self.colony = colony_struct.parse(raws[derived])
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

    # ── What the screen draws, each from one source ──────────────────

    def blockaded(self, player_num):
        """The star's bit for the player the screen runs as (:832)."""
        if self.star is None:
            return False
        return bool((self.star.blockaded >> (int(player_num) & 0x1F)) & 1)

    def events(self, state):
        """(plague, pop boom) from open fix 37, or None — HD STATE."""
        ev = getattr(state, "colony_events", None)
        if ev is None or ev.get("plague") is None:
            return None
        return ev["plague"], ev["pop_boom"]

    def placement(self, state):
        """Open fix 36's grid and satellites, or None — HD STATE."""
        return getattr(state, "colony_placement", None)

    def product(self, state):
        """Open fix 38's (cost, turns) for WHAT THIS COLONY PRODUCES, or
        None. The block names its product; one that disagrees with the
        colony record is stale and not used."""
        p = getattr(state, "colony_product", None)
        if p is None or self.colony is None or p["cost"] < 0 \
                or p["producing"] != self.colony.producing[0]:
            return None
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
