"""What the colony screen SAYS — every string by the id the source uses.

TRANSCRIBED from `Draw_Info_Name_And_Pop_` (colony_main.cpp:806-873),
`Planet_Summary_String_` (colsysdi.cpp:89-179), `Draw_Info_Build_`
(:955-976) and `Draw_Turn_Count_` (colony.cpp:980-994). The words are the
player's own ESTRINGS.LBX through `core.estrings` (decision 38): absent,
a word is None and nothing is drawn in its place. The one literal is
orion2re's, not the LBX's: `"Auto Build Queue %d"` (colony_main.cpp:966),
the label of an autobuild preset, which the original game never had.

NOTE THE TWO WORD TABLES. The system display uses its OWN short words for
size, gravity and mineral class (colsysdi.cpp:103-118: "T", "S", "LG",
"U-Poor" …), not `MOX::_planet_size_string` and its neighbours — only the
climate comes from the shared table (colsysdi.cpp:165). So `SYS_SIZE` and
friends here are not `screens/planets/planetwords`' tables, and must not
be merged with them.
"""
from core.structs import player as player_struct
from screens.colony_summary import colonyrows
from screens.planets import planetwords

E_EMPTY = 0x00C
E_TITLE, E_ANNIHILATING = 97, 181                   # orion2_str.h:96, :174
#: `Colony_Type_` (colony.cpp:1148-1167): -1 empty, 0 agricultural,
#: 1 industrial, 2 and anything else research.
SPECIALTY = {-1: E_EMPTY, 0: 600, 1: 601, 2: 602}
E_BLOCKADED, E_PLAGUE, E_POP_BOOM = 202, 415, 426
E_POP = 424                                         # "Pop %d,%03d k (%+dk)"
E_TURNS = 32                                        # "%d turn(s)"
E_AUTOBUILD = 0x0BD
PRESET_LABEL = "Auto Build Queue %d"                # colony_main.cpp:966

#: colsysdi.cpp:103-118, indexed by PLANET_SIZE / _GRAVITY / MINERAL.
SYS_SIZE = (0x1F6, 0x25C, 0x25D, 0x25E, 0x25F)
SYS_GRAVITY = (0x169, E_EMPTY, 0x25B)
SYS_MINERAL = (0x222, 0x1A7, E_EMPTY, 0x1C2, 0x223)
SYS_GAS_GIANT, SYS_ASTEROIDS, SYS_ONE = 0x132, 0x0BA, 0x046
SYS_FREE, SYS_OWNED, SYS_POP = 0x02C, 0x029, 0x008
PLANET_TYPE_ASTEROID, PLANET_TYPE_GAS_GIANT = 1, 2  # orion2_consts.h:402-404

#: The autobuild encoding (build_queue.h:54-76).
AUTOBUILD_DISABLED, AUTOBUILD_LEGACY, AUTOBUILD_CUSTOM_BASE = 0, 1, 2
PRESET_COUNT = 11


def _fmt(template, *values):
    if template is None:
        return None
    try:
        return template % values
    except (TypeError, ValueError):
        return None


def _pick(table, value):
    return table[value] if 0 <= value < len(table) else None


class Words:
    def __init__(self, estrings):
        self.strings = estrings

    def e(self, index):
        return self.strings.string(index) if self.strings is not None \
            else None

    # ── The title line ───────────────────────────────────────────────

    def title(self, view, planet_name):
        c = view.colony
        if c.occupation_policy == 0:
            return _fmt(self.e(E_ANNIHILATING), planet_name)
        kind = self.e(SPECIALTY.get(c.specialty, 602))
        return _fmt(self.e(E_TITLE), kind if kind is not None else "",
                    planet_name)

    def status(self, view, player_num, state):
        """The status word, "" for none, or None where the answer needs
        open fix 37 and it is absent (HD STATE — nothing drawn)."""
        if view.blockaded(player_num):
            return self.e(E_BLOCKADED)
        events = view.events(state)
        if events is None:
            return None
        plague, boom = events
        if plague:
            return self.e(E_PLAGUE)
        if boom:
            return self.e(E_POP_BOOM)
        return ""

    def pop(self, view):
        return _fmt(self.e(E_POP), *view.pop_line())

    # ── The system display (colsysdi.cpp:141-179) ─────────────────────

    def summary(self, planet, state):
        if planet is None:
            return None
        if planet.planet_type == PLANET_TYPE_GAS_GIANT:
            return _fmt(self.e(SYS_ONE), self.e(SYS_GAS_GIANT))
        if planet.planet_type == PLANET_TYPE_ASTEROID:
            return _fmt(self.e(SYS_ONE), self.e(SYS_ASTEROIDS))
        grav = self.e(_pick(SYS_GRAVITY, planet.gravity_class))
        mineral = self.e(_pick(SYS_MINERAL, planet.mineral_class))
        colonies = getattr(state, "colonies_raw", None) or []
        if planet.colony_index < 0 or planet.colony_index >= len(colonies):
            climate = self.e(_pick(planetwords.CLIMATE_WORDS, planet.climate))
            return _fmt(self.e(SYS_FREE),
                        self.e(_pick(SYS_SIZE, planet.size)), climate,
                        grav, mineral, self.e(E_EMPTY))
        from core.structs import colony as colony_struct
        col = colony_struct.parse(colonies[planet.colony_index])
        players = getattr(state, "player_raw", None) or []
        owner = (player_struct.parse(players[col.owner])
                 if 0 <= col.owner < len(players) else None)
        traits = player_struct.traits(owner) if owner is not None else None
        pops = _fmt(self.e(SYS_POP), col.n_pops,
                    colonyrows.max_population(col, planet, traits))
        return _fmt(self.e(SYS_OWNED),
                    owner.race_name if owner is not None else "",
                    grav, mineral, pops)

    # ── The production window ────────────────────────────────────────

    def turns(self, n):
        return _fmt(self.e(E_TURNS), n)

    def autobuild(self, view):
        """The label over the production window, or "" for none
        (colony_main.cpp:961-974 over build_queue.h:66-81)."""
        value = int(view.colony.auto_building)
        enabled = view.autobuild_enabled
        preset = (value - AUTOBUILD_CUSTOM_BASE
                  if enabled and AUTOBUILD_CUSTOM_BASE <= value
                  < AUTOBUILD_CUSTOM_BASE + PRESET_COUNT else -1)
        legacy = (value != AUTOBUILD_DISABLED if not enabled
                  else value == AUTOBUILD_LEGACY)
        if preset >= 0:
            return PRESET_LABEL % preset
        return (self.e(E_AUTOBUILD) or "") if legacy else ""
