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

The old s_planet_data guess that used to sit here had `star_index`
at offset 0 and an invented `position` at 2. Both were wrong: the
real first member is `colony_index`. Kept as a note because it is
exactly the kind of plausible-looking guess this file exists to
quarantine.

Still needed, still unverified:
  s_colony      (361 B) — colony screen (verify field by field,
                          starting with population/owner)
  s_leader_data (59 B)  — officers screen
"""
from core.structs import Spec

# s_colony: 361 bytes. Field ORDER is known from orion2.h but no
# offsets have been checked yet. Deliberately left empty so nothing
# can accidentally depend on a guess.
COLONY = Spec("s_colony", 361, [], verified=False,
              note="map from orion2.h, then confirm owner/population "
                   "against a known colony via struct_probe.py")

# s_leader_data: 59 bytes. Same situation.
LEADER = Spec("s_leader_data", 59, [], verified=False,
              note="confirm name string offset first, it is the "
                   "cheapest ground truth")
