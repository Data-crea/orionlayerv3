"""Which snapshot's icons and scale the galaxy map may believe.

One job: `ScreenStateGate`, the single point where a game snapshot becomes
the map's state, with the fields it gates (`GATED_FIELDS`) and what they
hold before a screen-0 snapshot has arrived (`BLANK_FIELDS`). Split out of
ships.py (decision 6); it needs nothing from the icon drawing.
"""

#: SCREEN_MAIN — the only screen whose snapshot describes the galaxy
#: map. The same number as GalaxyMapScreen.GAME_SCREEN_ID.
MAP_SCREEN_ID = 0

#: THE SNAPSHOT FIELDS ANOTHER SCREEN REWRITES WHILE IT IS UP, each with
#: the line that writes it. ONE list: a field is added here and nowhere
#: else, and the smoke test iterates this dict rather than naming a
#: field of its own.
#:
#: Both entries belong to the Fleets screen AND to the Officers screen,
#: which is why the rule is "screen 0 only" and not "not screen 4":
#: `Set_Fltscrn_Small_Ship_Icon_XYs_` is called from flt1.cpp:531 and
#: :711 and from officer.cpp:905, and both screens save the map scale on
#: entry and put it back on exit. A list of guilty screens would have
#: missed screen 29 on the day it was written.
GATED_FIELDS = {
    "ship_icons": (
        "FLT::Set_Fltscrn_Small_Ship_Icon_XYs_ overwrites x/y with "
        "FLEET-INSET coordinates (flt.cpp:54-55) and "
        "FLT2::Add_Fltscrn_Small_Icon_Fields_ overwrites stack_id with "
        "the id of the hidden field it adds for that icon "
        "(flt2.cpp:34). Serialized at ext_api.cpp:165-167; only "
        "MAINSCR::Main_Screen_ puts them back "
        "(mainscr_main.cpp:314-315)."),
    "map_scale": (
        "FLT::Set_Fltscrn_Small_Ship_Icon_XYs_ sets _cur_map_scale = "
        "_max_map_scale so the inset covers the whole galaxy "
        "(flt.cpp:14). FLT1::Fleet_Screen_ saves it on entry and "
        "restores it on exit (flt1.cpp:487, :835), and "
        "OFFICER::Officer_Screen_ does the same (officer.cpp:857, "
        ":1191). Serialized at ext_api.cpp:111."),
}

#: What a gated field holds before any screen-0 snapshot has arrived:
#: `core.game_state.GameState`'s own starting values. An empty map is a
#: state every renderer here already handles; another screen's map is
#: not. Copied per gate, never shared.
BLANK_FIELDS = {"ship_icons": [], "map_scale": 0}

#: NOT GATED, and each for a reason that had to be read rather than
#: assumed:
#:   map_x / map_y  `MOX::_cur_map_x/_cur_map_y` are written only by
#:                  savegame.cpp:1514-1515, mainscr.cpp and
#:                  mainscr_main.cpp — nothing under flt*.cpp or
#:                  officer.cpp touches them, so the map ORIGIN is
#:                  already the map's.
#:   fleet_selection FSEL's stack is `_fleet_box_ship_stack`, written
#:                  once on EXIT (flt1.cpp:827) and never during the
#:                  screen, and `_ship_node[].selected` is not touched
#:                  either: the Fleets screen keeps its own selection in
#:                  `_fltscrn_big_icon[].selected` (flt1.cpp:429) and
#:                  open fix 28 writes that array, not the node table.
#:   ships / stars / colonies  SCRAP, a move order and a relocation are
#:                  real changes to the game and MUST reach the map.
#:                  A screen's own display state is what is gated here,
#:                  never a thing the player did.


class _GatedSnapshot:
    """A snapshot whose gated fields are the map's; everything else is
    the game's, live.

    Same shape as `viewctl._ViewProxy` and for the same reason: a few
    attributes are ours and the rest must fall through. A COPY of the
    state would have been simpler and is wrong — `core/game_client.py`
    sets `fields`, `framebuffer` and `save_slots` onto the snapshot
    object after `parse_state` built it, and a copy would freeze the
    field list, which is the thing that decides what may be sent
    (decision 59, work order 128 C).
    """

    def __init__(self, state, held):
        self._state = state
        self.__dict__.update(held)

    def __getattr__(self, name):
        return getattr(self._state, name)


class ScreenStateGate:
    """State a screen rewrites for itself is that screen's, not the
    map's: every field of `GATED_FIELDS` is adopted from screen 0 and
    from nowhere else.

    Nothing about the records says which space they are in. They parse,
    they are in range, and a map drawn from them puts every stack at an
    inset position at a scale meant for a 305x182 box — with every
    other number on screen still correct, which is this project's worst
    failure shape (decision 35). Mixing HALF of them is the same fault
    one layer down: work order 135 gated the icons and left the scale,
    so the map held screen-0 icons against a screen-4 scale, which is
    two reference frames in one picture.

    THE GATE IS HERE, at the one point where a snapshot becomes the
    map's state, and not at each reader: `render_fleets`, `maplines`,
    `mapeta`, `mapinput`/`mapclick`, `boxmodel.remember` and the two
    map views all read the screen's `_state` and therefore all get the
    same answer. Work orders 135 B and 136 B; the hazard is question 15
    of `dev:doc/fleet_screen_reading.md`.

    **`viewctl.park_game` is deliberately NOT behind it.** Parking
    drives the GAME's own zoom and stops on an absolute target read off
    the snapshot, so a frozen scale would be a target it can never
    reach. It is handed the raw snapshot in `GalaxyMapScreen.update`
    and it already refuses unless the game reports screen 0 with this
    screen's field list; a smoke check holds both halves.

    On screen 0 the snapshot is handed back untouched, so the normal
    case costs one comparison and no wrapper.
    """

    def __init__(self):
        self.held = dict(BLANK_FIELDS)

    def reset(self):
        """Forget what was held — a fresh entry to the screen has
        nothing, and an empty map is honest where a stale one is not."""
        self.held = dict(BLANK_FIELDS)

    def state(self, game_state):
        """The snapshot as the galaxy map may read it."""
        if getattr(game_state, "current_screen",
                   MAP_SCREEN_ID) != MAP_SCREEN_ID:
            return _GatedSnapshot(game_state, self.held)
        for _name in GATED_FIELDS:
            _value = getattr(game_state, _name, None)
            self.held[_name] = (BLANK_FIELDS[_name] if _value is None
                                else _value)
        return game_state
