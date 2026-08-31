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
TRAIT_COUNT = 31
TRAIT_OMNISCIENCE = 27     # TRAIT enum, orion2_consts.h


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
