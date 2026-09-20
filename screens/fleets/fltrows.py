"""The grid's cells and the ship panel's lines, from the wire.

What reaches here has already been validated by `fltwire.View`: this
module turns ship indices into things to draw and nothing else. It makes
no decision about whether the screen may draw at all.

**THE CELLS CARRY THE SHIP'S OWN PICTURE — THE OMISSION IS LIFTED**
(work order 142 D1). It used to read "SHIPS.LBX is MOO2's artwork,
which is never in this tree, so a cell shows a name and a colour".
The artwork is still never in this tree and never will be (decisions
40 and 42); what changed is that this stopped being the same statement
as "HD cannot draw it". `tools/fleet_art_extract.py` reads the
player's OWN installation and `screens/fleets/fltart.py` decodes it at
load time (decision 38), so the cell draws
`SHIPS.LBX ship_type + colour * 50` — `KEN::Do_Get_Ship_Picture_Seg`,
ken.cpp:451-466 — whenever the player has extracted it.

WITHOUT those files, which is the state of every fresh clone, the cell
falls back to the NAME and the builder's colour exactly as before, and
the screen says how to get them. That fallback is not documentation:
the smoke test forces both states.

**THE DAMAGE BAR IS AN OMISSION FOR A DIFFERENT REASON.**
`FLEETPOP::Draw_Damage_Bars_` (fleetpop.cpp:41-81) reads
`structural_damage` and `armor_damage`, which `core/structs/ship.py`
does NOT carry: they are hand-counted offsets 125 and 123 that no second
source has confirmed (decision 23), and the reading marks them
UNVERIFIED. A bar drawn from an unverified offset is a bar that can be
wrong without looking wrong. The bar's own geometry is unsettled too —
`Draw_Fltscrn_Big_Ship_Icons_` passes width 1 on this screen
(flt1.cpp:56-59, :110), which `Draw_Damage_Bars_` turns into an
effective width of -3.

**THE ATTACK AND DEFENSE BONUSES ARE AN OMISSION** because
`INITSHIP::Get_Ship_Combat_Bonuses_` (initship.cpp:638-687) needs
officer skills from `s_leader_data` (unverified), the crew fields at
113-116 (unverified), `strategic_combat_flag` (not in
`core/structs/settings.py`), tech applications and
`_td_combat_speed_bonus` — five inputs, three of them unverified and one
undecoded.

What IS here is what the verified spec carries: the name, the location,
the shield, the weapon list and the specials.
"""
from core import hestrings
from core.structs import player as player_struct
from core.structs import ship as ship_struct
from core.structs import star as star_struct

#: `Do_Get_Ship_Picture_Seg`'s set for an owner that is not a player
#: (ken.cpp:459-462, MAX_PLAYERS is 8 at consts.h:7).
MONSTER_SET = 8


class Cell:
    """One big-icon cell: what the grid draws in slot `slot`."""

    def __init__(self, slot, ship_idx, selected, view, sprite_set=None,
                 ramp=None):
        self.slot = slot
        self.ship_idx = ship_idx
        self.selected = selected
        self.view = view                      # parsed s_ship_data, or None
        self.name = getattr(view, "name", "") if view else ""
        # THE COLOUR IS THE BUILDER'S, NOT THE OWNER'S. The original
        # picks the picture by `previous_owner` (ken.cpp:451-466), which
        # is who BUILT the hull — a captured ship keeps the colours it
        # was built in. Transcribed, including for a cell that has no
        # picture to show: the marker beside the name follows the same
        # rule, so a captured ship reads the same way it does in the
        # original.
        self.builder = (getattr(view, "previous_owner", None)
                        if view else None)
        self.owner = getattr(view, "owner", None) if view else None
        # WHICH PICTURE, AND WHICH COLOURS — two different owners, and
        # they were read as one until work order 142 D1. `picture_num`
        # (offset 92) picks the hull; `sprite_set` is the BUILDER's
        # colour and selects the artwork set (ken.cpp:453, :466);
        # `ramp` is the CURRENT owner's colour and selects the palette
        # the screen installs over 192..239 (flt1.cpp:561). A captured
        # ship therefore keeps its old hull in its new colours.
        self.picture = getattr(view, "picture_num", None) if view else None
        self.sprite_set = sprite_set
        self.ramp = ramp


def player_colour(game_state, index):
    """`_player[index].color`, or None when there is no such player.

    The indirection the original makes at ken.cpp:459-462 and that
    this screen made nowhere: a player INDEX is not a colour, and the
    two coincide often enough in a fresh game to hide the difference.

    **A DELIBERATE DIVERGENCE, MARKED.** The original tests
    `player_idx < MAX_PLAYERS` on a value it has already sign-extended
    (ken.cpp:453), so `previous_owner` 0xFF reaches `_player[-1]` and
    reads whatever is in front of the table. None comes back here
    instead and the caller falls to the monster set. Reproducing an
    out-of-bounds read is not transcription.
    """
    raws = getattr(game_state, "player_raw", None) or []
    if index is None or not 0 <= int(index) < len(raws):
        return None
    try:
        return int(player_struct.parse(raws[int(index)]).color)
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def cells(fleet_view, game_state):
    """The `Cell` list for the displayed rows, in display order."""
    raws = getattr(game_state, "ships_raw", None) or []
    out = []
    for slot, ship_idx, selected in fleet_view.rows:
        view = None
        if 0 <= ship_idx < len(raws):
            raw = raws[ship_idx]
            if len(raw) >= ship_struct.SIZE:
                view = ship_struct.parse(raw)
        built = player_colour(game_state,
                              getattr(view, "previous_owner", None))
        held = player_colour(game_state, getattr(view, "owner", None))
        out.append(Cell(slot, ship_idx, selected, view,
                        sprite_set=MONSTER_SET if built is None else built,
                        ramp=MONSTER_SET if held is None else held))
    return out


class Panel:
    """The scanned ship's readout, in the original's own three parts.

    `head` is the full-width block, `weapons` and `specials` are the
    two COLUMNS — `Print_Scanned_Ship_Data_` prints the weapons at
    x 0x17 and the specials at x 0xBC, each with its own cursor from a
    shared `base_y` (flt2.cpp:683-740). One column is not a list under
    the other and never was.

    **`head` IS A FIXED NUMBER OF SLOTS, NOT A LIST OF WHAT THERE IS**
    — work order 154. The original advances its y cursor by one line
    per slot whether or not it printed anything in it, so a slot it
    leaves empty is a BLANK LINE and everything below it stays put.
    That is not a detail: it is the empty line between the head and
    the Weapons/Specials headings that Data compared against, and it
    only exists because a parked ship has no destination to print.

    A slot is one of three things:

      `None`              the original printed nothing there
      a string            one label at the left tab stop
      a two-tuple         two labels, at the left and right stops —
                          the "Beam OCV:" / "Beam DCV:" line

    `HEAD_SLOTS` names them in order.
    """

    #: The five, in the order `Print_Scanned_Ship_Data_` prints them.
    HEAD_SLOTS = ("name", "crew", "shield", "bonuses", "destination")

    __slots__ = ("head", "weapons", "specials",
                 "weapons_heading", "specials_heading")

    def __init__(self, head, weapons, specials,
                 weapons_heading="", specials_heading=""):
        self.head = head
        self.weapons = weapons
        self.specials = specials
        self.weapons_heading = weapons_heading
        self.specials_heading = specials_heading

    def __bool__(self):
        # A head of five empty slots is not content. It can happen in a
        # clone with no extracted names at all, and an empty panel must
        # read as empty rather than as five blank lines.
        return bool(any(line for line in self.head)
                    or self.weapons or self.specials)

    def flat(self):
        """Everything as one column, for a caller that cannot do two.

        Blank slots are dropped rather than carried: the fallback is a
        plain list of lines for a renderer that cannot place columns,
        and a blank there would be a gap with no layout behind it.
        """
        out = []
        for line in self.head:
            if not line:
                continue
            if isinstance(line, tuple):
                out.extend(part for part in line if part)
            else:
                out.append(line)
        for heading, column in ((self.weapons_heading, self.weapons),
                                (self.specials_heading, self.specials)):
            if heading:
                out.append(heading)
            out.extend(column)
        return out


#: `Crew_Description_String_` (flt2.cpp:749-773): the crew word by
#: `crew_quality`, from the player's own HESTRNGS.
CREW_MESSAGES = {0: 0x8A, 1: 0x8B, 2: 0x8C, 3: 0x8D}
#: The headings and the empty-column word, same table
#: (flt2.cpp:681-682, :719, :740).
MSG_WEAPONS, MSG_SPECIALS, MSG_NONE = 0x9D, 0x9E, 0x9F
#: The DESTINATION line, and it is a destination and not a location:
#: 0x9B is "Destination, %s", 0x9C "Destination, Unexplored star",
#: 0x68 "Destination: Antares" (flt2.cpp:645-677, strings read out of
#: the player's own HESTRNGS).
MSG_AT_STAR, MSG_UNKNOWN_STAR, MSG_IN_TRANSIT = 0x9B, 0x9C, 0x68

#: The two combat-bonus labels, "Beam OCV:" and "Beam DCV:"
#: (flt2.cpp:606, :613 / :629).
MSG_BEAM_OCV, MSG_BEAM_DCV = 0x99, 0x9A


def panel_lines(ship_idx, game_state, parts, strings=None, arcs=None):
    """The ship panel's content, as a `Panel`.

    `FLT2::Print_Scanned_Ship_Data_` (flt2.cpp:524-747) in the order it
    prints. `strings` is a `core.hestrings.HStrings` and `arcs` a
    `core.kentext.ArcWords`; both may be absent, and what depends on
    them is then left out rather than invented (decision 22).

    **WHAT IS STILL OMITTED, and why** — both marked in `layout.json`:

    * **Beam OCV and Beam DCV.** `Get_Ship_Combat_Bonuses_`
      (initship.cpp:638-687) needs officer skills, the crew record,
      traits, the strategic-combat flag and the tech applications;
      three of those are UNVERIFIED offsets and one is undecoded.
    * **The RED for a damaged special.** The original colours a special
      with `FLT2::_red_colors` when its bit is set in
      `special_device_damage_flags` (flt2.cpp:724-731). That field is
      at @118 by the header route and **is not verified**: the obvious
      live check — a damaged device must be a fitted one — held on all
      60 ships of the acceptance save and proved nothing, because not
      one of them had any damage.
    """
    raws = getattr(game_state, "ships_raw", None) or []
    if not (0 <= ship_idx < len(raws)):
        return Panel([], [], [])
    raw = raws[ship_idx]
    if len(raw) < ship_struct.SIZE:
        return Panel([], [], [])
    view = ship_struct.parse(raw)

    def message(index):
        return strings.message(index) if strings is not None else None

    # FIVE SLOTS, ALWAYS — see `Panel`. An empty one is a blank line
    # in the original too, and everything below it keeps its place.
    head = [view.name, None, None, None, None]

    # THE CREW LINE. crew_quality @113 and crew_experience @114 are
    # VERIFIED by the header route (orion2.h:2847-2868, the same struct
    # run the spec is already verified through at @109) and by a live
    # reading over 60 ships, where the experience bands per quality do
    # not overlap and rise — which is what MOO2 deriving the word from
    # the points predicts and what two unrelated bytes cannot produce.
    word = message(CREW_MESSAGES.get(int(view.crew_quality), -1))
    if word:
        head[1] = f"{word} ({int(view.crew_experience)} EP)"

    # The original always has a shield name — `_shields[0].name` is
    # "No Shield" and the native screenshot shows it. HD has one only
    # when the player has extracted the catalogue; without it the slot
    # stays blank rather than closing up (decision 22).
    head[2] = (parts.name("shields", view.shield_type) if parts else None)

    # **THE BEAM OCV / DCV LINE, LABELS ONLY — see `layout.json`'s
    # `omission_panel_beam_bonuses`.** The line is the original's and
    # is printed for every combat ship; the two NUMBERS are not
    # reachable (`INITSHIP::Get_Ship_Combat_Bonuses_` walks the leader
    # records) and are not invented. The labels hold the line so the
    # gap is on screen instead of silent, which is the same argument
    # as `deviation_panel_overflow`.
    ocv, dcv = message(MSG_BEAM_OCV), message(MSG_BEAM_DCV)
    if ocv or dcv:
        head[3] = (ocv or "", dcv or "")

    head[4] = _destination(view, game_state, strings)

    # "n Name (arc)" per weapon. THE LIST STOPS AT THE FIRST EMPTY SLOT
    # on this screen — `no_weapons` breaks the loop (flt2.cpp:696-701)
    # — which is NOT what `ship.weapons()` does elsewhere.
    weapons = []
    for slot in ship_struct.weapons(view):
        count = int(getattr(slot, "count", 0) or 0)
        if count <= 0:
            break
        label = (parts.name("weapons", slot.type) if parts else None) \
            or f"#{slot.type}"
        # **OMISSION — THE PLURAL.** The original prints
        # `TECHDATA::_weapons[t].name_plural` whenever the count is not
        # one (flt2.cpp:706-711). `tools/techname_extract.py` takes the
        # `name` field and not the plural one, so the catalogue in this
        # tree has no plural to print; the singular stands rather than
        # an invented "s", which is not the original's word either and
        # would be wrong for the first irregular one. Marked in
        # `layout.json`; lifting it is a change to the extractor and its
        # format version, which is its own piece of work.
        arc = arcs.arc(getattr(slot, "firing_arc", 0)) if arcs else None
        weapons.append(f"{count} {label} ({arc})" if arc
                       else f"{count} {label}")

    specials = []
    for bit in ship_struct.special_bits(view):
        label = parts.name("specials", bit) if parts else None
        if label:
            specials.append(label)

    none_word = message(MSG_NONE)
    if not weapons and none_word:
        weapons = [none_word]
    if not specials and none_word:
        specials = [none_word]
    return Panel(head, weapons, specials,
                 message(MSG_WEAPONS) or "", message(MSG_SPECIALS) or "")


def _destination(view, game_state, strings=None):
    """The destination line, or None for a blank slot.

    **IT IS A DESTINATION AND IS PRINTED ONLY WHILE THE SHIP IS ON ITS
    WAY** — corrected by work order 154, and the correction is the
    condition rather than the wording. The original's test is

        loc >= SHIP_LOCATION_MOVING_OFFSET
            && loc <= _NUM_STARS + SHIP_LOCATION_WORMHOLE_OFFSET

    (flt2.cpp:644, the offsets 10000 and 20000 from consts.h:22-24), so
    a ship PARKED at a star — whose `location` is the bare star index —
    gets no line at all and the slot stays blank. HD printed
    "Destination, Vega" for a ship sitting at Vega and going nowhere:
    work order 152 item 7 established that the line is the original's
    and did not carry its condition across. The blank is visible in
    the native screenshot of the same panel
    (`evidence/work_order_152/panel/001_20_panel_native.png`).

    The three wordings are the original's own (flt2.cpp:661-673):

      * `_NUM_STARS == star_idx` -> H 0x68 "Destination: Antares";
      * the player has no information -> H 0x9C "Destination,
        Unexplored star";
      * otherwise H 0x9B "Destination, %s" with the star's name.

    **AND THE SECOND OF THOSE IS NEW HERE.** HD printed the name
    whatever the player knew, which shows the name of a star they have
    not explored. The original's test is
    `Player_Has_Visited_ || TRAIT_OMNISCIENCE ||
    One_Leader_With_Galactic_Lore_ || Contact_With_One_Colony_`
    (:657-662). HD can read the first two — `star.visited` is a
    bitmask over players and `player.traits` carries the pick — and
    has neither the leader skills nor the diplomatic contact, so it
    can be wrong in ONE direction only: it says "Unexplored star"
    where the original would have named it. Marked in `layout.json`
    as `deviation_panel_destination_info`; saying too little about a
    star is the safe half of that trade and showing its name is not.
    """
    loc = int(view.location)
    stars = getattr(game_state, "stars", None) or []
    if not (ship_struct.LOCATION_MOVING_OFFSET <= loc
            <= len(stars) + ship_struct.LOCATION_WORMHOLE_OFFSET):
        return None
    idx = ship_struct.absolute_location(loc)
    if idx == len(stars):
        return (strings.message(MSG_IN_TRANSIT)
                if strings is not None else None)
    if not (0 <= idx < len(stars)):
        return None
    if not _player_knows_star(game_state, idx):
        return (strings.message(MSG_UNKNOWN_STAR)
                if strings is not None else None)
    name = getattr(stars[idx], "name", "") or ""
    if not name:
        return None
    if strings is not None:
        template = strings.message(MSG_AT_STAR)
        if template:
            return hestrings.printf(template, name)
    return name


def _player_knows_star(game_state, star_idx):
    """The reachable half of the original's own four-way test.

    `star.visited` is a bitmask over players and is read the way
    `colonyrows` reads it; `player.has_omniscience` is the racial
    pick, and its own docstring already says a False there is not
    "no lore". The two routes HD cannot follow are recorded at
    `_destination`.
    """
    stars = getattr(game_state, "stars", None) or []
    me = int(getattr(game_state, "player_num", 0) or 0)
    if star_struct.visited_by(stars[star_idx], me):
        return True
    raws = getattr(game_state, "player_raw", None) or []
    if 0 <= me < len(raws):
        return player_struct.has_omniscience(player_struct.parse(raws[me]))
    return False


def star_name(game_state, star_idx):
    """One star's name, or ""."""
    stars = getattr(game_state, "stars", None) or []
    if not (0 <= star_idx < len(stars)):
        return ""
    return getattr(stars[star_idx], "name", "") or ""


def is_black_hole(game_state, star_idx):
    stars = getattr(game_state, "stars", None) or []
    if not (0 <= star_idx < len(stars)):
        return False
    return star_struct.is_black_hole(stars[star_idx])
