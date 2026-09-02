"""UNVERIFIED starting-point specs — DO NOT use in production paths.

Specs live here until their offsets are confirmed. Confirmation
means one of:
  - numeric agreement with live data via tools/struct_probe.py, or
  - orion2re's own header compiled with its `#pragma pack(1)` and
    the resulting sizeof matching the assert in sizes.h.

Once confirmed, a spec moves into its own module with
verified=True and the evidence written into the docstring.

Already promoted out of this file:
  s_nebula      -> core/structs/nebula.py   (26 Aug 2026)
  s_planet_data -> core/structs/planet.py   (26 Aug 2026)
  s_player      -> core/structs/player.py   (26 Aug 2026, partial)
  s_colony      -> core/structs/colony.py   (31 Aug 2026; byte
                   layout verified against the colony summary of an
                   85-turn savegame, the pop[] bit masks promoted
                   with it but NOT all verified — only MASK_PROF is)

The old s_planet_data guess that used to sit here had `star_index`
at offset 0 and an invented `position` at 2. Both were wrong: the
real first member is `colony_index`. Kept as a note because it is
exactly the kind of plausible-looking guess this file exists to
quarantine.

Still needed, still unverified:
  s_leader_data (59 B)  — officers screen

And one that is NOT a starting point but a RE-OPENING: `s_player`
was promoted on one source, and `PLAYER_SIDEBAR` below carries the
six scalars the colony-summary sidebar reads back to header-only
status until a live read agrees with the original's own screen. See
the block comment on that spec — it is a probe, not a second home
for offsets that live in `player.py`.
"""
from core.structs import Spec

# s_leader_data: 59 bytes. Same situation.
LEADER = Spec("s_leader_data", 59, [], verified=False,
              note="confirm name string offset first, it is the "
                   "cheapest ground truth")


# ── s_player, the six the colony-summary sidebar reads ────────────
#
# s_player is ALREADY a verified spec in core/structs/player.py, and
# these six offsets are in it. This is not a second home for them and
# must never become one: it is a PROBE spec, and it exists because
# "verified" was claimed on one source.
#
# player.py's own docstring says where its offsets come from — the
# header compiled with its `#pragma pack(1)`, sizeof landing on the
# 0xf0e in sizes.h. That was reproduced on 2 September 2026 and every
# number below is exact. But it is ONE source, and it is the source
# that cannot be wrong in the way that matters: a header describes the
# struct the ENGINE was compiled from, and what OrionLayer parses is
# what came over the wire. Those agree until the day they do not, and
# a size assert cannot tell a stock from a flow or catch two adjacent
# int16s in the wrong order.
#
# So the six get read off a live game beside what the screen shows —
# `tools/struct_probe.py players --sidebar` — and this spec is what
# that mode decodes against. The three ANCHORS are here as controls,
# not as data: `race`, `traits` and `tech_applications` are already
# trusted, so a live read that gets those right and the six wrong is
# telling you about the six, while one that gets the anchors wrong is
# telling you the record is not what you think it is.
#
# THE HAZARD, and it is why this is not a formality: `surplus_food`
# (276) and `surplus_bc` (278) are two bytes apart, both int16, both
# net flows, both printed with an explicit sign. Swapped, every value
# on screen stays plausible — a food surplus and a BC surplus are the
# same order of magnitude in most empires. No assert catches that.
# Only reading them beside the original's own sidebar does.
#
# The smoke test holds every offset here against player.py, so the
# duplication cannot drift while it lasts.

#: What KIND of number each field is. They are not one kind, and the
#: difference decides what a reader may do with them:
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
PLAYER_KINDS = {
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

#: The three already-trusted offsets, carried as controls. Values are
#: asserted against player.py by the smoke test rather than being a
#: second opinion about where they live.
PLAYER_ANCHORS = ("race", "traits", "tech_applications")

PLAYER_SIDEBAR = Spec("s_player", 0xF0E, [
    # ── controls: already verified, here to validate a live read ──
    ("race",                   37, "u8"),
    # ── the six, header source only until struct_probe agrees ──
    ("bc",                     50, "i32"),
    ("surplus_freighters",     56, "i16"),
    ("total_pop",             266, "i16"),
    ("research_produced",     272, "i16"),
    ("surplus_food",          276, "i16"),
    ("surplus_bc",            278, "i16"),
    # ── controls, continued ──
    ("tech_applications",     379, "u8[212]"),
    ("traits",               2308, "i8[31]"),
], verified=False,
    note="six sidebar scalars, header source only; race/traits/"
         "tech_applications are verified controls. Promote by "
         "running tools/struct_probe.py players --sidebar against a "
         "live game and agreeing with the original's own sidebar.")
