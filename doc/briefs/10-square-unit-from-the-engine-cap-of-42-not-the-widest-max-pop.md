Read doc/v3_fundament.md and CLAUDE.md first.

In screens/colony_summary/colonylist.py, the square unit is derived
from the widest max_pop present in the current colony list. Change it
to derive from the engine cap of 42 instead, so the unit never changes
as the empire grows.

Source: s_colony.pop[42] in orion2.h, and
COLCALC::Planet_Max_Population_For_Player_ ends with
"if (pop_limit > 42) pop_limit = 42;". The same 42 is the per-job cap
in COLMOVE::Give_Colonist_New_Job_ (Sum_Colonists_ >= 42), so a single
zone may legitimately span the whole track.

The track then has three regions per row, and each needs its own
visual state:
  1. filled     - one square per assigned pop, in zone colour
  2. free       - from n_pops to max_pop: dashed outline, no fill
  3. unreachable - from max_pop to 42: no square, only a faint
                   baseline. This region is reachable later via
                   Advanced City Planning (+5), Biospheres (+2),
                   Subterranean and terraforming, so it is not padding.

Put the 42 in one named constant with the source in the comment.
Do not add a second copy anywhere. Run python tools/smoke_test.py.