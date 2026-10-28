"""The engine facts behind the colony numbers, shared across screens.

Moved here from `screens/colony_summary/colonyrows.py` by work order 338,
byte for byte: the Colony screen, the Planets list, the galaxy map's
system window, Leaders, Fleets and Audience all read these (the maximum
population, the planet's name, the net production the original draws, the
morale mark, the inset's star positions) and each used to import them from
the Colony Summary screen's row builder. They are not that screen's
behaviour but the original's arithmetic, so they live in `core/` and the
row builder (`colonyrows.build_rows`) imports them like everybody else.

No pygame, no pixels; the source reference of every value stays with its
code, and the screen-specific evidence (what the colony LIST draws and
omits) stays in `colonyrows`' own docstring.
"""
from core import zoomtables
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from core.structs import star as star_struct

ROMAN = ("I", "II", "III", "IV", "V")

#: orion2_consts.h:119-123. `s_colony.production[4]` is indexed by
#: these, and the four sort keys that read it use them.
ECON_FOOD, ECON_INDUSTRY, ECON_RESEARCH, ECON_BC = 0, 1, 2, 3

#: colcalc.cpp:57, _size_climate_max_pop_lookup, indexed by climate.
CLIMATE_FACTOR = (25, 25, 25, 25, 25, 25, 40, 60, 80, 100)
#: mox.cpp:796, _planet_max_population, indexed by PLANET_SIZE. This
#: is the BASE of a computation and never an answer on its own — see
#: the fundament, section 3.
SIZE_BASE = (5, 10, 15, 20, 25)

#: orion2_consts.h:949. The government sits in the trait array like a
#: racial pick, at index 0.
TRAIT_CURRENT_GOVERNMENT = 0

#: orion2_consts.h:199-200. At or above this the original draws NO
#: morale marks at all — Draw_Info_Morale_Both_ zeroes its own count
#: rather than drawing an empty row, and 7 (Galactic Unification) is
#: above it, which is why the test is >= and not ==.
GOVERNMENT_UNIFICATION = 6

TRAIT_AQUATIC = 12            # orion2_consts.h:961
TRAIT_SUBTERRANEAN = 13       # orion2_consts.h:962
TRAIT_ENVIRONMENT_IMMUNE = 23  # orion2_consts.h:972
BUILDING_BIOSPHERES = 15      # orion2_consts.h:28
POP_BONUS_BIOSPHERES = 2      # colcalc_config.cpp:40
#: The engine's hard population ceiling, and therefore the length of
#: the track every row is drawn on. Three sources, one number: a
#: colonist lives in `s_colony.pop[42]` (orion2.h:497), so no colony
#: holds more; `COLCALC::Planet_Max_Population_For_Player_` ends
#: `if (pop_limit > 42) pop_limit = 42;` (colcalc.cpp:930), so no
#: computed maximum passes it; and `COLMOVE::Give_Colonist_New_Job_`
#: caps ONE job at the same number (`Sum_Colonists_ >= 42`,
#: colmove.cpp:518) — which is why a single zone may legitimately
#: span the whole track, and why it cannot be drawn shorter.
#:
#: This is the only copy in the tree. `max_population()` clamps with
#: it and `colonylist.render()` measures the square with it, so the
#: two can never disagree about how long a full bar is.
#:
#: It is also why the square is a fixed unit. The unit used to be
#: derived from the widest `max_pop` in the list being drawn, which
#: made the ruler move with the empire: one new Gaia colony, or a
#: finished Biosphere, lengthened the longest bar and shrank every
#: square on the screen, so a square counted last turn was not the
#: square counted this turn — and nothing about the picture said the
#: scale had changed. A ceiling the engine enforces cannot do that.
POP_LIMIT_CAP = 42

CLIMATE_TUNDRA, CLIMATE_OCEAN, CLIMATE_SWAMP = 4, 5, 6
CLIMATE_TERRAN, CLIMATE_GAIA = 8, 9


def player_climate(climate, traits):
    """COLCALC::Calc_Player_Climate_ (colcalc.cpp). Aquatic only."""
    if traits and traits[TRAIT_AQUATIC]:
        if climate in (CLIMATE_TUNDRA, CLIMATE_SWAMP):
            return CLIMATE_TERRAN
        if climate in (CLIMATE_OCEAN, CLIMATE_TERRAN):
            return CLIMATE_GAIA
    return climate


#: Advanced City Planning (work order 322 A2/A10): `TECH_APP_ADVANCED_
#: CITY_PLANNING` 3 (orion2_consts.h, v2 :702) researched (status 3,
#: orion2_consts.h:1324) adds 5 — 1.60's literal (colcalc.cpp:928, :1022)
#: and v2's default, which v2 reads from its config (DEVIATION
#: `city_planning_config`, colcalc_config.cpp:79-82).
TECH_APP_ADVANCED_CITY_PLANNING = 3
TECH_RESEARCH_STATUS_RESEARCHED = 3
CITY_PLANNING_BONUS = 5


def city_planning(player):
    """Has this parsed player record researched Advanced City Planning?
    False for no record, or one whose layout has no `tech_applications`."""
    apps = getattr(player, "tech_applications", None) if player else None
    return bool(apps) and len(apps) > TECH_APP_ADVANCED_CITY_PLANNING and \
        apps[TECH_APP_ADVANCED_CITY_PLANNING] == \
        TECH_RESEARCH_STATUS_RESEARCHED


def max_population(colony, planet, traits, city_planning=False):
    """The maximum the original prints, for the colony's OWNER.

    `COLCALC::Colony_Race_Pop_Limit_` (colcalc.cpp:1012-1033, v2
    :1103-1125) over `Size_And_Climate_Race_Pop_Limit_` and
    `Size_And_Climate_Max_Population_` (colcalc.cpp:1271).

    Two details that are easy to get wrong and were both read out of
    the source rather than assumed. The climate is the COLONY's
    (offset 226), not the planet's: `Colony_Calculation_` rewrites it
    when a shield turns a Radiated world Barren (colcalc.cpp:682).
    And `SIZE_BASE[size]` is only the base — the climate factor and
    the immunity bonus scale it, which is the difference between 10
    and the 5 the game prints for a Small Ocean planet.

    ADVANCED CITY PLANNING is applied since work order 322: the caller
    passes `city_planning(owner record)` — the colony OWNER's research
    (colcalc.cpp:1021-1023), the local player's for an unsettled planet
    (:927-929) — and its +5 goes on before the biospheres, the cap last.
    DEVIATION `city_planning_config`: v2's config may name another bonus
    (see `CITY_PLANNING_BONUS`).

    ONE DEVIATION remains: the original returns the best limit over the
    RACES PRESENT in the colony; this returns the limit for the owner's
    race. The two agree for a single-race colony. The walk needs the pop
    nibble, which is now confirmed for 0..7 — what it does not have is
    the 8 and 9 sentinels, and a walk that mis-resolves androids and
    natives would pick the wrong race for exactly the colonies the walk
    exists for. It makes the bar too SHORT rather than too long, which
    shows as a bar that cannot hold its own squares — visible, not silent.
    """
    climate = player_climate(colony.climate, traits)
    immune = bool(traits[TRAIT_ENVIRONMENT_IMMUNE]) if traits else False
    factor = min(100, (25 if immune else 0) + CLIMATE_FACTOR[climate])
    size = max(0, min(len(SIZE_BASE) - 1, planet.size))
    limit = (factor * SIZE_BASE[size] + 50) // 100
    if traits and traits[TRAIT_SUBTERRANEAN]:
        limit += 2 * size + 2          # COLCALC::Double_Add_Two_
    if city_planning:
        limit += CITY_PLANNING_BONUS
    if colony.buildings[BUILDING_BIOSPHERES]:
        limit += POP_BONUS_BIOSPHERES
    return min(limit, POP_LIMIT_CAP)


def colony_morale(colony, traits):
    """(value, applies) — COLDRAW::Draw_Info_Morale_Both_, transcribed.

    The engine never prints this number: it draws `abs(morale / 2)`
    sprites, at most 20, in one of two artworks by sign. The HALVING
    is the transcription and so is the sign, and `int(a / 2)` is C
    truncation toward zero — `//` rounds a negative morale away from
    zero and would draw one mark too many on exactly the colonies
    where it matters. Turning the count into a printed number is a
    DEVIATION and is marked in `layout.json` under
    `output._deviation_note`.

    `applies` is False under Unification and Galactic Unification,
    where the original sets its count to 0 and therefore draws
    nothing. That is not the same as a morale of zero, and the panel
    draws nothing for it rather than a 0.
    """
    if traits and traits[TRAIT_CURRENT_GOVERNMENT] >= GOVERNMENT_UNIFICATION:
        return 0, False
    return int(colony.morale / 2), True


def morale_icon(value):
    """Which mask the output panel's MORALE row wears — decision 56.

    Data's rule of 13 September 2026, and it is NOT the original's.
    `Draw_Info_Morale_Both_` picks its artwork by the sign of the
    halved value too (coldraw.cpp:220), but draws NOTHING at zero,
    because there it is a counter and zero copies of anything is
    nothing. Here the icon is a row LABEL, so a row that prints has
    one: negative is the low mask, everything else — zero included —
    is the normal one. Under Unification the value is 0 and the row
    still prints its label, so it wears the normal mask; the icon
    follows the row.

    Decided here and handed to the panel, the same seam as the net
    and the shortage: `colonyoutput` does not read the record.
    """
    return "morale_low" if value < 0 else "morale_normal"


def planet_name(colony, planets, stars, first=None):
    """'Sol III' — HAROLD::Planet_Number_ counts occupied slots. `first`:
    the word that replaces "I" (`star_planet_name`)."""
    if not 0 <= colony.planet < len(planets):
        return "?"
    planet = planet_struct.parse(planets[colony.planet])
    if not 0 <= planet.star_index < len(stars):
        return "?"
    return star_planet_name(stars[planet.star_index], colony.planet, first)


def star_planet_name(star, planet_index, first=None):
    """`HACCESS::Do_Get_Planet_Name_` (haccess.cpp:208): "%s %s", the
    star's name and the numeral of the planet's place among the
    system's OCCUPIED slots. One home since brief 101 — the Planets
    list names its rows through it too. `first` is the localised name of
    the first planet: `Get_Planet_Name_` (haccess.cpp:236-239) writes
    H_Message 0xA0 ("Prime" in the English game) where the numeral is
    "I"; the lists use `Get_Planet_Name_No_Prime_` and pass None."""
    number = 0
    for slot in star_struct.planet_indices(star):
        if slot == planet_index:
            break
        if slot > -1:
            number += 1
    numeral = ROMAN[number] if number < len(ROMAN) else str(number + 1)
    if first and numeral == "I":
        numeral = first
    return f"{star.name} {numeral}"



#: MAX_PLAYERS, consts.h:7. The bound `Draw_Galaxy_Map_Box_` tests
#: `owner` against before treating a star as unowned.
MAX_PLAYERS = 8

#: The galaxy inset's own box, native, as `COLSUM::Draw_Galaxy_Map_`
#: passes it: MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d,
#: 0x80, 0x5b, 0, 0, 0, 0, 3, 0) at colsum.cpp:415 — x 380, y 349,
#: width 128, height 91, view_mode 3. Second source for the same
#: four: Colsum_Connect_Galaxy_Map_Stars_ (colsum.cpp:734-735).
INSET_NATIVE = (380, 349, 128, 91)

#: The two constants the original divides by, movebox.cpp:19-20.
#:
#: They are not arbitrary, and the number in them has ONE meaning
#: here: 506000 is the map viewport's own width — 506 native px,
#: `MAINSCR::Draw_Influence_Overlay_`'s `map_width` (mainscr.cpp:163)
#: and `Maximum_Galaxy_Display_Scale_`'s divisor (mapgen.cpp:68) —
#: times 1000, and 400000 is its height the same way. **This is the
#: viewport's REACH per scale unit, not a scale recovered from a
#: width**; the ratio 50.6 that used to be cited here was the
#: retired estimate's constant and pointing at it made one number
#: carry two meanings. The division below therefore reduces to
#: `star.x / MAP_MAX_X * width`, i.e. the whole galaxy across the
#: box. Transcribed as the integer arithmetic the original writes,
#: NOT as that algebraic form: three of the four divisions truncate
#: and the simplified version lands a pixel out.
INSET_SCALE_X = 506000
INSET_SCALE_Y = 400000


def galaxy_inset_stars(game_state, box=INSET_NATIVE, black_hole=9):
    """Every star as (native_x, native_y, colour_index).

    Transcribed from `MOVEBOX::Draw_Galaxy_Map_Box_` (movebox.cpp:4)
    under view_mode 3, which is the mode `COLSUM::Draw_Galaxy_Map_`
    asks for. Native pixels, because that is the space the original's
    arithmetic is in; scaling to the panel is the renderer's job.

    THE POSITION (movebox.cpp:62-64), with x_start 380, y_start 349
    and both map offsets 0:

        scale_x = 506000 / width          (movebox.cpp:19)
        sx = x_start + ((star.x * 1000 / max_map_scale) * 10) / scale_x

    and the same for y over 400000 / height. `max_map_scale` is not on
    the wire and is recovered from MAP_MAX_X **and MAP_MAX_Y** by
    `zoomtables.max_map_scale` — one home for that, already used by
    the galaxy map. Both extents go in: the recovery transcribes
    `MAPGEN::Maximum_Galaxy_Display_Scale_`, whose two ceilings are
    per axis, and every dot here divides by its answer.

    **VERIFIED AGAINST THE ORIGINAL'S OWN FRAMEBUFFER**, 4 September
    2026: all 99 stars of the reference save land within 2 px of ink
    in the native frame the Extension API reports, at stardate 3502.
    That is the transform checked against the thing it is a transform
    of, rather than against a screenshot measured by eye.

    THE COLOUR INDEX (movebox.cpp:67-79), which selects a sprite from
    `MOX::_colony_galaxy_star_seg[10]` — gstar.lbx entries 23..32,
    loaded by `COLONY::Load_Galaxy_Map_Anims_` (colony.cpp:329-338):

        black hole                      -> 9 on this screen
        unowned, and visited or -1/-2   -> 8
        unowned otherwise               -> 0
        owned                           -> _player[owner].color

    The black-hole line is `_using_colony_screen_palette ? 9 : 10`
    (movebox.cpp:70), so the index DEPENDS ON THE CALLING SCREEN and is
    the `black_hole` parameter. This screen sets that flag and gets 9.
    The Fleets screen clears it (flt1.cpp:522) and gets 10, which is a
    real eleventh sprite there: `_fleet_galaxy_star_seg` is declared
    `[11]` (mox.h:110) and `FLT1::Load_Galaxy_Stars_` fills all eleven
    from FLEET.LBX 34..44 (flt1.cpp:1441-1444).

    **THAT CORRECTS A NOTE THIS DOCSTRING USED TO CARRY**, which said
    10 "would be off the end of a ten-entry array". It is off the end
    of the COLONY screen's ten-entry `_colony_galaxy_star_seg`, and the
    colony screen never asks for it; the fleet screen's array is one
    longer and 10 is its black hole. The difference was invisible while
    both indices drew the same flat dot, and stops being invisible the
    moment the sprites are the original's.

    **TWO THINGS ABOUT INDEX 0 WORTH KNOWING BEFORE READING A
    SCREENSHOT.** It is both "unowned and unvisited" AND player colour
    0, so those two draw the same sprite in the original. And the
    unvisited branch is nearly unreachable: it needs an unowned star
    whose `owner` is neither -1 nor -2, and all 52 unowned stars in
    the reference save carry -1. Every index 0 in that save is a
    colour-0 player's star, not a dark one.
    """
    stars = getattr(game_state, "stars", None) or []
    if not stars:
        return []
    raws = getattr(game_state, "player_raw", None) or []
    players = [player_struct.parse(r) for r in raws
               if len(r) >= player_struct.SIZE]
    local = getattr(game_state, "player_num", 0)
    scale = zoomtables.max_map_scale(
        getattr(game_state, "map_max_x", 0),
        getattr(game_state, "map_max_y", 0))
    if not scale:
        return []
    # `box` is the native box the caller's original draws into; the
    # Planets screen passes its own (443, 17, 180, 116), plntsum.cpp:1351
    # (brief 101) — same function, a parameter rather than a copy.
    _x, _y, width, height = box
    div_x = INSET_SCALE_X // width
    div_y = INSET_SCALE_Y // height
    out = []
    for star in stars:
        sx = ((int(star.x) * 1000 // scale) * 10) // div_x
        sy = ((int(star.y) * 1000 // scale) * 10) // div_y
        out.append((sx, sy,
                    _inset_color_index(star, players, local, black_hole)))
    return out


def _inset_color_index(star, players, local, black_hole=9):
    """movebox.cpp:67-79, in order."""
    if star_struct.is_black_hole(star):
        return black_hole
    owner = int(star.owner)
    if owner < 0 or owner >= MAX_PLAYERS:
        if star_struct.visited_by(star, local) or owner in (-1, -2):
            return 8
        return 0
    return players[owner].color if owner < len(players) else 0


def galaxy_inset_label(game_state, colony_index):
    """The star name the original prints under the inset, or "".

    TRANSCRIBED. `Draw_Scan_Info_` (colsum.cpp:80) prints
    `_star[_galaxy_map_scanned_star]` centred at native (444, 431)
    — colsum.cpp:86 — which is the inset box's own horizontal centre
    (380 + 64) near its bottom edge.

    `_galaxy_map_scanned_star` follows the SELECTED colony: it is set
    from that colony's planet's star on entry (colsum.cpp:141) and
    again whenever a row is scanned (colsum.cpp:1001). The original
    also sets it by hovering a star IN the inset — those stars are
    fields, `_galaxy_map_star_field[]` (colsum.cpp:69-75) — and that
    path is NOT DRAWN here; see `colonyinset`.

    So on this screen the label names the selected colony's star,
    which is the same selection `colonyselect` already holds.
    """
    stars = getattr(game_state, "stars", None) or []
    idx = scanned_star(game_state, colony_index)
    return stars[idx].name if idx is not None else ""


def scanned_star(game_state, colony_index):
    """`_galaxy_map_scanned_star` for the selected colony — its planet's
    star (colsum.cpp:141, :1001) — or None. The label names it and the
    inset marks it (work order 196 C2)."""
    if colony_index is None:
        return None
    colonies = getattr(game_state, "colonies_raw", None) or []
    planets = getattr(game_state, "planets_raw", None) or []
    stars = getattr(game_state, "stars", None) or []
    if not (0 <= colony_index < len(colonies)):
        return None
    colony = colony_struct.parse(colonies[colony_index])
    if not (0 <= colony.planet < len(planets)):
        return None
    idx = int(planet_struct.parse(planets[colony.planet]).star_index)
    return idx if 0 <= idx < len(stars) else None


def _low_byte_signed(value):
    """`(int8_t)` of an int16, as C does it — the LOW BYTE, signed.

    Its own function so the cast is a named thing that a check can
    aim at, rather than an `& 0xff` buried in an expression that the
    next reader tidies into a plain comparison. It exists because
    `COLDRAW::Draw_Colony_Prod_Both_` sign-tests `imports[t]` twice
    and casts only once — coldraw.cpp:73 against :152. See
    `drawn_production`.
    """
    byte = value & 0xFF
    return byte - 256 if byte > 127 else byte


def drawn_production(col, econ):
    """What the original DRAWS on one production row, not what it
    stores.

    **`production[t]` is not the number on screen.**
    `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36) computes a net
    before it draws anything, in four branches (coldraw.cpp:73-94),
    and only one of the four is `production[t]` itself. Transcribed,
    all four:

      imports[t] byte-negative:
        A  t == ECON_INDUSTRY -> max(0, production - maintenance[t])
        B  otherwise          -> production - abs(imports[t])
      otherwise:
        C  maintenance[ECON_INDUSTRY] == 0 or t != ECON_INDUSTRY
                              -> production[t]
        D  otherwise          -> max(0, production - maintenance[t])

    A to D are the order the C++ writes them in and are the names
    anything referring to a branch uses — here, in the smoke test and
    in the status document.

    **A AND D ARE THE SAME EXPRESSION, AND NO SAVEGAME CAN SEPARATE
    THEM.** Not "unwitnessed" — indistinguishable, which is a
    stronger and less hopeful statement and is true by inspection
    rather than by evidence. Both are guarded by
    `prod_type == ECON_INDUSTRY`, so the industry row is the only row
    either can run on, and both compute
    `max(0, production - maintenance[prod_type])` — character for
    character the same three lines, coldraw.cpp:75-78 against :89-92.
    Only the `(int8_t)` cast decides which one is entered, and the
    cast cannot change the number that comes out. An experiment that
    cannot come out two ways is not an experiment waiting for data.

    **AND C COLLAPSES INTO THEM ON THAT ROW TOO**, which needs one
    fact from outside this file. `COLCALC::Pre_Import_Computing_`
    (colcalc.cpp:487) ends with, unconditionally for every colony it
    is called on,

        imports[ECON_INDUSTRY] = min((uint8)maintenance[ECON_INDUSTRY],
                                     production[ECON_INDUSTRY])

    (colcalc.cpp:507-511), and that is the ONLY write to
    `imports[ECON_INDUSTRY]` anywhere in the engine — verified by
    grepping every assignment to `imports[`, which finds ECON_FOOD in
    colcalc_main.cpp at :222, :229, :335 and :1408, ECON_BC at
    colcalc.cpp:1265, ECON_INDUSTRY only here, and ECON_RESEARCH
    never. So on the industry row:

        maintenance == 0 -> imports == 0 -> byte non-negative -> C,
                            which returns production, and that IS
                            max(0, production - 0)
        maintenance != 0 -> A or D depending on the cast, and both
                            return max(0, production - maintenance)

    All four paths therefore compute
    `max(0, production[INDUSTRY] - maintenance[INDUSTRY])`.

    **THE ASSUMPTION IS `production[ECON_INDUSTRY] >= 0`, and it is
    load-bearing.** With a negative production the collapse fails at
    the top line: `min(0, production)` is then the negative
    production rather than 0, and depending on its low byte the row
    reaches either A — which clamps to 0 — or C, which returns the
    negative value. Nothing in this file enforces it and nothing in
    the engine was found clamping it; the tax step that rewrites
    production after the imports assignment
    (`Colony_Industry_To_Tax_`, colcalc.cpp:1111, reached from
    colcalc.cpp:514) cannot make a non-negative production negative,
    because it only runs when production already exceeds
    maintenance.

    **WHAT A SAVE COULD STILL SETTLE: D AGAINST C.** That is a real
    distinction — `production` against `max(0, production -
    maintenance)` — and it is the one the reference save cannot make
    for the rows this screen draws.

    **THE LIVE EVIDENCE**, 4 September 2026, reference save. Eleven
    colonies belong to the local player and are the ones drawn; the
    snapshot carries 55 records in all, and reading the other 44 is
    what the second block below rests on.

      B  production - abs(imports)     NINE of the eleven, through a
                                       negative imports[BC]. Wolf
                                       II's BC reads 18 stored
                                       against 10 drawn.
      C  production[t]                 every other drawn row.
      A  and D                         NOT REACHED on any drawn row:
                                       imports[ECON_INDUSTRY] and
                                       maintenance[ECON_INDUSTRY] are
                                       both 0 on all eleven. Nor
                                       would reaching them show
                                       anything, per the two blocks
                                       above.

    Across all 55 records, `maintenance[ECON_INDUSTRY]` runs 0..7 and
    `imports[ECON_INDUSTRY]` runs 0..7 — never negative, never
    exceeding maintenance, which is `min(maintenance, production)`
    behaving exactly as colcalc.cpp:507-511 says. So D IS reached in
    this save, on other players' colonies; it is only unreachable
    from what this screen draws.

    **A IS COVERED BY THE TRANSCRIPTION AND NOT BY A TEST**, and that
    is stated rather than papered over. Deleting branch A and letting
    the industry row fall through to D leaves the suite GREEN, tried
    on 4 September 2026 — which is not a hole in the check but the
    same fact as the first block, arriving from the direction of the
    tests. The suite asserts the VALUE the industry row produces, and
    that value is right whichever of the two computes it. What it
    cannot assert is which one ran, and no test can, so none pretends
    to.

    Stated per branch rather than left to "the function is
    transcribed", which is the same distinction `core/structs/
    player.py` makes per FIELD: one flag covering a whole spec
    implies evidence it does not have. This is that question a level
    down — not which field, but which branch.

    Note which `maintenance` each branch reads: the CONDITION on D
    tests `maintenance[ECON_INDUSTRY]` and the SUBTRACTION uses
    `maintenance[prod_type]` (coldraw.cpp:85, :89).
    On the industry row — the only row that reaches it — those are
    the same slot, so nothing depends on it today; it is transcribed
    as written because the next person to read the C++ will see two
    different indices and wonder whether this file noticed.

    **THE `(int8_t)` CAST IS THE ORIGINAL'S AND IS DELIBERATE.**
    coldraw.cpp:73 tests `(int8_t)colony->imports[prod_type] < 0` —
    the LOW BYTE of an int16 — while the same function tests
    `colony->imports[prod_type] < 0` with no cast at coldraw.cpp:152,
    where it decides whether to draw the shortage. Two sign tests on
    one field, disagreeing for every value whose low byte and whole
    differ in sign: 256 is positive as a word and 0 as a byte, 384 is
    positive as a word and -128 as a byte. It changes nothing at
    realistic import values, which is exactly why nobody would ever
    notice it, and it is NOT normalised here. Filed as a QUESTION in
    dev:doc/orion2re_open_fixes.md item 7 — does the original binary sign
    -test the byte or the word? — because it is not our tree and the
    answer decides which of the two is the transcription.

    `maintenance` (offset 239, u8[4]) and `imports` (243, i16[4]) are
    both in the verified spec, so decision 23 is satisfied and this
    needed no new offset work.
    """
    production = col.production[econ]
    imports = col.imports[econ]
    maintenance = col.maintenance[econ]
    # The cast, as written. int16 -> signed low byte.
    if _low_byte_signed(imports) < 0:
        if econ == ECON_INDUSTRY:
            return max(0, production - maintenance)
        return production - abs(imports)
    if col.maintenance[ECON_INDUSTRY] == 0 or econ != ECON_INDUSTRY:
        return production
    return max(0, production - maintenance)


def production_shortage(col, econ):
    """How much this row is short, or 0 — and 0 whenever the original
    would not draw it at all.

    THE ARITHMETIC (coldraw.cpp:61-64):
        shortage = maintenance[t] - imports[t] - production[t]
    clamped to 0 at anything below 1. Drawn with
    `COLONY::Short_Anims_` (coldraw.cpp:170-177), which is the import
    sprite outlined in palette colour 0xED (colony.cpp:2192-2199).

    **THE REFUSAL IS PART OF THE TRANSCRIPTION, and it is why this
    returns 0 rather than the raw difference.** Those `Short_Anims_`
    loops sit in the ELSE of `if (imports[t] < 0 || t ==
    ECON_INDUSTRY)` (coldraw.cpp:152), so the shortage is drawn only
    when imports are non-negative AND the row is not industry. A
    shortage computed and shown on the industry row would be an
    invention wearing a citation — the number exists in the C++ and
    is never drawn there. Decision 33: mirror the refusal, do not
    just copy the sum.

    Note the sign test at :152 has NO `(int8_t)` cast, and the one
    that picks the net at :73 does. See `drawn_production`.

    REFERENCE CASE, measured 4 September 2026: Wolf II, 13 pops,
    production[FOOD] 12, imports[FOOD] 0, maintenance[FOOD] 13 — so
    13 - 0 - 12 = 1, and the original draws exactly one red marker on
    that row.
    """
    if econ == ECON_INDUSTRY or col.imports[econ] < 0:
        return 0
    return max(0, col.maintenance[econ] - col.imports[econ]
               - col.production[econ])
