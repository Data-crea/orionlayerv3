"""s_player — VERIFIED spec (3854 bytes), partial.

Only the fields the HD screens actually read. The record is large
and mostly diplomacy/tech state; adding a field is cheap, so this
grows on demand rather than mapping all ~130 members up front.

Offsets are not hand-counted. They come from compiling orion2re's
own `src/game/orion2.h` with the `#pragma pack(push, 1)` the header
itself sets, then reading offsetof() for each member. sizeof came
out at exactly 3854, matching PLAYER_SIZE / the 0xF0E in sizes.h —
if any offset had drifted, the size would not land on the assert.

Sidebar semantics, from mainscr_main.cpp's sidebar drawing:
  treasury line     bc, then surplus_bc as a signed second line
  command points    "(command_points - command_points_used)
                     (command_points)"
  food              surplus_food, signed
  freighters        "surplus_freighters (n_freighters)"
  research          research_breakthrough != 0 -> "breakthrough",
                    else current_research_field == 0 -> "none"

`contact` is an 8-byte array indexed by player; non-zero means the
local player has met that empire. Star names in Get_Star_Name_ use
it to decide whether an owned system shows its owner's colour.
"""
import struct as _struct

from core.structs import Spec

SIZE = 0xF0E   # 3854

MAX_PLAYERS = 8

SPEC = Spec("s_player", SIZE, [
    ("picture",                 0, "i8"),
    ("name",                    1, "str20"),
    ("race_name",              21, "str15"),
    ("eliminated",             36, "u8"),
    ("race",                   37, "u8"),
    ("color",                  38, "u8"),
    ("personality",            39, "u8"),
    ("home_planet_id",         41, "i16"),
    ("research_breakthrough",  48, "i8"),
    ("tax_rate",               49, "u8"),
    ("bc",                     50, "i32"),
    ("n_freighters",           54, "i16"),
    ("surplus_freighters",     56, "i16"),
    ("command_points",         58, "i16"),
    ("command_points_used",    60, "i16"),
    ("total_pop",             266, "i16"),
    ("food_produced",         268, "i16"),
    ("industry_produced",     270, "i16"),
    ("research_produced",     272, "i16"),
    ("bc_produced",           274, "i16"),
    ("surplus_food",          276, "i16"),
    ("surplus_bc",            278, "i16"),
    ("research_accumulated",  591, "i32"),
    ("current_research_field", 901, "i8"),
    ("total_research",       1613, "i16"),
    ("total_ships",          1615, "i16"),
    ("total_colonies",       1649, "i16"),
], verified=True)

CONTACT_OFFSET = 1512      # sbyte contact[MAX_PLAYERS]
TRAITS_OFFSET = 2308       # int8_t traits[TRAIT_COUNT]
#: uint8_t tech_applications[TECH_APP_COUNT]; TECH_APP_COUNT is 212
#: (orion2_consts.h:1388, orion2re 1.60). Not a spec field — the
#: table is not decoded yet — but the offset is wanted as an ANCHOR:
#: a live read that gets race, traits and this right and the sidebar
#: scalars wrong is telling you about the scalars, not the record.
#: Advanced City Planning lives in this table; see
#: colonyrows.max_population, which does NOT apply it.
TECH_APPLICATIONS_OFFSET = 379
TRAIT_COUNT = 31
TRAIT_OMNISCIENCE = 27     # TRAIT enum, orion2_consts.h


#: What KIND of number each sidebar scalar is. They are not one
#: kind, and the difference decides what a reader may do with them:
#:
#:   stock      a balance that persists between turns. Differencing
#:              two turns gives a flow.
#:   net flow   already a per-turn difference, signed, and the sign
#:              is meaningful — the original prints these with %+d.
#:   gross      a per-turn amount with nothing subtracted. NOT
#:              comparable with a net flow, and adding it to one is
#:              the mistake this table exists to prevent.
#:   count      a cardinality. Never negative in normal play, and a
#:              negative one is a bug or a misread offset.
#:
#: Ordered as COLSUM::Draw_Empire_Info_ prints them (colsum.cpp:418,
#: orion2re 1.60), which is also the order in the colony summary's
#: layout.json. `tools/struct_probe.py players --sidebar` reads the
#: six from SPEC above and annotates them with this.
SIDEBAR_KINDS = {
    "bc":                 ("stock",
                           "treasury carried between turns"),
    "surplus_bc":         ("net flow",
                           "income minus maintenance, per turn"),
    "total_pop":          ("count", "colonists across the empire"),
    "surplus_freighters": ("count",
                           "freighters free, not a per-turn change "
                           "— the name says surplus, the number is "
                           "a cardinality"),
    "surplus_food":       ("net flow",
                           "produced minus eaten, per turn"),
    "research_produced":  ("gross",
                           "RP generated this turn, nothing "
                           "subtracted — not a net of anything"),
}

#: Already-trusted offsets, carried by `--sidebar` as controls.
#: `race` and `traits` are the two with a live corroboration on
#: record (see the docstring); `tech_applications` rides along
#: because a wrong record shows up there first — it is the largest
#: member and the furthest from the scalars.
SIDEBAR_ANCHORS = ("race", "traits", "tech_applications")


def contacts(view):
    """Per-player contact flags; contacts(v)[n] is truthy when the
    local player has met player n."""
    return list(_struct.unpack_from(
        f"<{MAX_PLAYERS}b", view.raw, CONTACT_OFFSET))


def traits(view):
    """The 31 racial trait values (signed)."""
    return list(_struct.unpack_from(
        f"<{TRAIT_COUNT}b", view.raw, TRAITS_OFFSET))


def has_omniscience(view):
    """Galactic lore via the racial pick.

    NOT the whole story: HAROLD::Player_Is_Omniscient_ also returns
    true when any hired leader carries the Galactic Lore skill, which
    lives in the leader records. Treat a False here as "no lore from
    traits", not as "no lore".
    """
    return traits(view)[TRAIT_OMNISCIENCE] != 0


def command_point_surplus(view):
    return view.command_points - view.command_points_used


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
