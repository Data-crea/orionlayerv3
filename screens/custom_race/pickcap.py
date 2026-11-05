"""Custom Race — the cap on negative picks.

The original lets a race take back at most 10 picks by negative choices
(`negative_picks`, the sum of the costs below zero of every chosen primary
option, the government and every special). A choice that would pass the cap
is not set and a warning box answers (KENTEXT 0x4A). Without this HD set the
pick locally, sent it, and the engine refused it with a framebuffer box the
HD screen cannot see — the same reason Accept is refused here (`popup.py`).

TRANSCRIPTION `negative_limit`: -10, `raceopt_config.cpp:8`
(`pick_rules.negative_limit`); the warning is KENTEXT 0x4A (`racesel.cpp:568`,
`:598`, `:626`).

TRANSCRIPTION `cap_rules`, `racesel.cpp:561-567` (a primary group) and
`:593-597` (the government): a choice other than the one already set is
refused when its cost plus the negative picks of the CURRENT state is under
the limit. The current state still counts the choice it would replace — the
original does not subtract it, and neither does this.

TRANSCRIPTION `cap_rules_special`, `racesel.cpp:625-626`: a special that is
switched on is refused when the negative picks, with it counted, are under
the limit; the Rich/Poor Home World partner is cleared only afterwards
(`:637-651`), so it still counts here too. Switching one off, and clicking
the choice that is already set, are never refused.

DEVIATION `partner_kept`: original = after a refused special the
partner (Rich/Poor, Low-G/High-G, Lithovore/Cybernetic, Repulsive/
Charismatic, Uncreative/Creative) is cleared anyway, because the clearing
chain (`racesel.cpp:637-651`) follows the refusal in the same branch; HD = a
refused choice changes nothing. HD does not send the refused click, so the
engine keeps the partner on; clearing it here alone would make the screen
and the engine disagree.

Costs are the screen's `picks` values, the engine's cost with its sign: a
positive cost spends picks, a negative one gives them.
"""

NEGATIVE_LIMIT = -10


def negative_picks(costs):
    """The sum of the costs below zero (`Calculate_Picks`,
    raceopt.cpp:649-675)."""
    return sum(cost for cost in costs if cost < 0)


def refuses_choice(cost, negative_now):
    """A primary option or a government that is not the one set."""
    return cost + negative_now < NEGATIVE_LIMIT


def refuses_special(cost, negative_now):
    """A special that is switched on: its own cost counts only below
    zero, as `Calculate_Picks` adds it."""
    return negative_now + min(cost, 0) < NEGATIVE_LIMIT
