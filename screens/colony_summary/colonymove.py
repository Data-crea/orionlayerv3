"""The original's pop-movement rules, mirrored — `colmove.cpp`.

Decision 33 lets HD test a rule the game already owns, so a refusal
can be shown instead of a silence. It says "where the rule is one
comparison", and this is four rules plus a pick-up refusal, so the
question of whether it still holds is answered explicitly:

**IT HOLDS, because all five decide from fields we have.** Every
input is `s_colony.pop[]`, `n_pops` or `max_farms`, all in the
verified spec (`core/structs/colony.py`), and each is named with its
verification state on the function that reads it. Nothing here needs
state the snapshot does not carry. The fifth drop rule — a click on
another colony being a transport with an ETA dialog — is NOT mirrored
and NOT offered: it lives in `Send_Cluster_`'s long branch
(colmove.cpp:180-500), it opens a dialog, and a dialog is its own
chain under decision 21.

**THE DROP IS DIVISIBLE, AND THAT DECIDES THE SHAPE OF THIS MODULE.**
`Send_Cluster_` walks the cluster one pop at a time and `return`s the
moment `Give_Colonist_New_Job_` refuses (colmove.cpp:168-173),
leaving the pops it already moved in their new job and the rest
unassigned with the cluster still held. So a mirror that answers
yes/no is the wrong instrument: it would say "this works" and then
seven of twelve would move. `plan_drop` answers **how many land and
where it stops**, which is decision 33's own failure mode one level
finer.

It has to be a simulation and not a formula, because the caps move
underneath: `Give_Colonist_New_Job_` recomputes `Sum_Colonists_` on
every call, and `Sum_Colonists_` counts only pops carrying
`POP_MASK_ASSIGNED` — which each successful move sets. The eleventh
farmer can be refused where the tenth was not.

**THE CONDITIONS ARE TRANSCRIBED AS WRITTEN, not as understood.**
`state == 3 or state == 6` is here with its `== 6`, even though
`Pop_To_Pop_State_` (colony.cpp:1240) cannot return 6 and there is no
other definition in that tree. Writing the condition down costs one
`or`; being right about an unreachable branch is the kind of claim
that has failed repeatedly in this project, and it does not have to
be made. The same goes for `max_farms > sum`, which is kept as the
comparison the source writes even though the field holds only 0 or
255 — see `_can_take_job`.

**FOR PHASE 4, NOTED NOW SO IT IS NOT REDISCOVERED:** the preview
does not show WHETHER a column accepts, it shows HOW MANY it takes.
`plan_drop` is already the right shape for that — `landed`,
`carried`, `reason`, `stopped_at` — and `layout.json`'s `move` block
holds the wording, whose `partial` line is about counts for the same
reason this module is.

Masks and accessors come from `core/structs/colony.py`, which is
their one home. This module adds no mask of its own.
"""
from core.structs import colony as colony_struct

#: `Pop_To_Pop_State_` (colony.cpp:1240) returns exactly these three:
#: 3 for a low nibble of 9, 4 for 8, and 2 for everything else.
POP_STATE_NORMAL = 2
POP_STATE_NATIVE = 3
POP_STATE_ANDROID = 4

#: `Sum_Colonists_ >= 42` (colmove.cpp:540). The same 42 as
#: `colonyrows.POP_LIMIT_CAP`, reached from the other side — that
#: constant carries the three sources and this is a fourth site for
#: the same ceiling, so it is named here rather than re-derived.
JOB_LIMIT = 42

#: ECON order, orion2_consts.h:119-123. Imported rather than
#: re-declared: `colonyrows` is where these live.
ECON_FOOD = 0
ECON_INDUSTRY = 1
ECON_RESEARCH = 2

#: Why a move was refused. OUR OWN strings live in layout.json under
#: `move` (decision 15) — these are ids, not wording. The original's
#: ESTRINGs are its own and are not ours to reproduce: we refuse
#: BEFORE injecting, so the text a player reads is a thing this
#: project chose and has to own.
REFUSE_NATIVE_JOB = "native_job"
REFUSE_ANDROID = "android"
REFUSE_JOB_FULL = "job_full"
REFUSE_NO_FARMING = "no_farming"
REFUSE_NATIVE_PICKUP = "native_pickup"


def pop_state(word):
    """`COLONY::Pop_To_Pop_State_` (colony.cpp:1240).

    Reads the low nibble, which is a PLAYER INDEX and not a race —
    see `core/structs/colony.py`, which refuses to call it one and
    now carries the evidence. **9 = native is VERIFIED** as of
    5 September 2026, by data, picture and the game's own label
    together. **8 = android still has no witness**, because no save
    this project holds contains one.
    """
    nibble = colony_struct.pop_player_index(word)
    if nibble == 9:
        return POP_STATE_NATIVE
    if nibble == 8:
        return POP_STATE_ANDROID
    return POP_STATE_NORMAL


def sum_colonists(pops, n_pops, job):
    """`COLONY::Sum_Colonists_(colony, job, -1, -1, 0, -1)`
    (colony.cpp:2112), which is the only form `colmove` calls.

    With state, race and conquered all -1 every pop matches those
    three, so what is left is: same job, and ASSIGNED. The assigned
    test is the one that matters here — a cluster in hand has that
    bit cleared, so the pops being carried do not count against the
    column they are heading for.
    """
    total = 0
    for i in range(min(n_pops, len(pops))):
        word = pops[i]
        if colony_struct.pop_prof(word) != job:
            continue
        if colony_struct.pop_is_assigned(word):
            total += 1
    return total


def _can_take_job(pops, n_pops, max_farms, index, new_job,
                  inter_colony_transfer=False):
    """`COLMOVE::Give_Colonist_New_Job_` (colmove.cpp:518-558).

    Returns `(True, None)` or `(False, reason)`. The four rules, in
    the source's own order, each with the fields it decides from and
    what those fields rest on under decision 23:

    1. **Natives take neither research nor industry**
       (colmove.cpp:524-529). Decides from the pop word's low nibble
       via `pop_state`. The nibble is VERIFIED live for 0..7 as a
       player index, and **9 meaning native is VERIFIED too** as of
       5 September 2026 — data, picture and the game's own label,
       see `core/structs/colony.py`.

       The condition is written `state == 3 or state == 6` because
       that is what the source writes. `Pop_To_Pop_State_` cannot
       return 6, so the second arm is unreachable in orion2re as it
       stands — and it is here anyway, because transcribing a
       condition costs nothing and being right about dead code is a
       claim nobody has to make.

       The ESTRING this refusal carries says natives may farm *or
       mine*, while the code refuses `ECON_RESEARCH` and
       `ECON_INDUSTRY` and leaves only `ECON_FOOD`. That
       disagreement is a QUESTION for the maintainer
       (`doc/orion2re_open_fixes.md` item 8), not something to
       resolve here: the code is what runs, so the code is what is
       mirrored, and which side is wrong is not ours to decide.

    2. **Androids keep the job they have** (colmove.cpp:531-537).
       Same nibble, value 8, and this one is **still UNVERIFIED**:
       no save this project holds contains an android, so the rule
       is mirrored from the source alone. Note it
       compares against the pop's CURRENT profession, so an android
       dropped back on its own column is allowed — that path does
       not even reach here, see `plan_drop`.

    3. **At most 42 in a job** (colmove.cpp:539-543). Decides from
       every pop's profession and assigned bit. `POP_MASK_PROF` is
       the one mask of the five with a second source; the assigned
       bit is header-only.

    4. **A farmer needs `max_farms > sum`** (colmove.cpp:546-554).
       The comparison is transcribed as written. What the field
       actually holds is 0 or 255 and nothing between —
       `Colony_Calculation_` writes -1 into a `uint8_t` when the
       planet can farm and 0 when it cannot (colcalc.cpp:691-695) —
       so in practice this rule is binary: a planet that cannot farm
       refuses its FIRST farmer, and a planet that can never refuses
       one here, because rule 3 caps the column first. `max_farms` is
       VERIFIED 7/7 against the original's own "No Farming" marks.
       The name is wrong for what it holds; `core/structs/colony.py`
       says so at length.

    `inter_colony_transfer` is always False from this screen — it is
    the transport case's flag, and the transport case is not offered.
    It is carried so the transcription is complete and so the
    parameter cannot be quietly dropped as unused.
    """
    state = pop_state(pops[index])

    # Rule 1 — as written, `== 6` included.
    if (state == POP_STATE_NATIVE or state == 6) and new_job in (
            ECON_RESEARCH, ECON_INDUSTRY):
        return False, REFUSE_NATIVE_JOB

    # Rule 2
    if state == POP_STATE_ANDROID:
        if colony_struct.pop_prof(pops[index]) != new_job:
            return False, REFUSE_ANDROID

    # Rule 3
    if sum_colonists(pops, n_pops, new_job) >= JOB_LIMIT:
        return False, REFUSE_JOB_FULL

    # Rule 4 — the source recomputes the sum here rather than reusing
    # the one above, and so does this.
    if (inter_colony_transfer
            or max_farms > sum_colonists(pops, n_pops, new_job)
            or new_job != ECON_FOOD):
        return True, None
    return False, REFUSE_NO_FARMING


def pops_identical(pops, a, b):
    """`COLMOVE::Pops_Identical_` (colmove.cpp:106-126).

    Three tests, all transcribed: the profession bits must match, the
    pop states must match, and the low nibble plus the conquered bit
    must match. The second is implied by the third — `pop_state` is a
    function of the nibble — and both are here because the source has
    both.
    """
    p1, p2 = pops[a], pops[b]
    if (p1 ^ p2) & colony_struct.POP_MASK_PROF:
        return False
    if pop_state(p2) != pop_state(p1):
        return False
    if (p2 ^ p1) & (colony_struct.POP_MASK_PLAYER_INDEX
                    | colony_struct.POP_MASK_CONQUERED):
        return False
    return True


class Cluster:
    """What a first click would pick up, or why it would not.

    `indices` are the pops `Get_Cluster_` would unassign — every pop
    identical to the one clicked, from it to the END of the array
    (colmove.cpp:66-71). Not the contiguous run under the cursor: a
    group split by a different pop still comes along in full, which
    is why the size cannot be read off the icons.
    """

    __slots__ = ("indices", "refused")

    def __init__(self, indices=(), refused=None):
        self.indices = tuple(indices)
        self.refused = refused

    def __repr__(self):
        return (f"Cluster({len(self.indices)} pops, "
                f"refused={self.refused!r})")


def plan_pickup(pops, n_pops, start):
    """`COLMOVE::Get_Cluster_` (colmove.cpp:56-76), without taking it.

    **The refusal at the FIRST click.** A native is rejected outright
    — `pop[start] & 0x0F == 9` (colmove.cpp:59) — and no cluster is
    formed. That is a fifth refusal on top of the four drop rules,
    in a different function, with a different message, and the
    fundament missed it until 4 September 2026.
    """
    if not (0 <= start < min(n_pops, len(pops))):
        return Cluster((), None)
    if colony_struct.pop_player_index(pops[start]) == 9:
        return Cluster((), REFUSE_NATIVE_PICKUP)
    return Cluster(
        [i for i in range(start, min(n_pops, len(pops)))
         if pops_identical(pops, start, i)], None)


class DropPlan:
    """How much of a cluster lands, and where it stops.

    NOT a boolean, and that is the point — see the module docstring.
    `landed` is how many pops would end up assigned, `carried` how
    many would still be in hand, and `reason` why it stopped, or None
    if it did not.

    `stopped_at` is the pop index the refusal happened on. It is the
    first pop that did NOT move, so a preview can name it.
    """

    __slots__ = ("landed", "carried", "reason", "stopped_at")

    def __init__(self, landed, carried, reason=None, stopped_at=None):
        self.landed = landed
        self.carried = carried
        self.reason = reason
        self.stopped_at = stopped_at

    @property
    def complete(self):
        return self.reason is None

    def __repr__(self):
        return (f"DropPlan(landed={self.landed}, carried={self.carried}"
                f", reason={self.reason!r}, at={self.stopped_at})")


def predict_pops(pops, n_pops, max_farms, cluster, requested_job):
    """The pop array `plan_drop` would leave behind.

    Same walk, returning the state rather than the count — so a
    caller can diff a real snapshot against it word for word instead
    of against a summary. That is what turns "the click landed
    somewhere" into a checkable claim.
    """
    work = list(pops)
    held = set(cluster.indices if isinstance(cluster, Cluster) else cluster)
    for i in held:
        if 0 <= i < len(work):
            work[i] &= ~colony_struct.POP_MASK_ASSIGNED
    while True:
        index = next((i for i in range(min(n_pops, len(work)))
                      if not colony_struct.pop_is_assigned(work[i])), None)
        if index is None:
            return work
        if (requested_job == -1
                or colony_struct.pop_prof(work[index]) == requested_job):
            work[index] |= colony_struct.POP_MASK_ASSIGNED
            continue
        ok, _reason = _can_take_job(work, n_pops, max_farms, index,
                                    requested_job)
        if not ok:
            return work
        work[index] = ((work[index] & ~colony_struct.POP_MASK_PROF)
                       | (requested_job << 7)
                       | colony_struct.POP_MASK_ASSIGNED)


def plan_drop(pops, n_pops, max_farms, cluster, requested_job):
    """`COLMOVE::Send_Cluster_`'s same-colony branch, simulated.

    colmove.cpp:160-176 and the loop's advance at :458. Each pass
    takes the FIRST pop still lacking the assigned bit, which is why
    this walks in array order and why the caps tighten as it goes.

    Two paths per pop, and only one of them consults the rules:

      the pop is already in the requested job (or `requested_job` is
      -1) -> it is simply re-flagged assigned (colmove.cpp:165). No
      rule is checked, so an android returning to its own column
      lands even though rule 2 would refuse it.

      otherwise -> `Give_Colonist_New_Job_`, and a refusal ENDS THE
      WHOLE DROP (colmove.cpp:168-173). The pops already moved keep
      their new job; this one and every later one stay in hand.

    Works on a COPY. Nothing here mutates the caller's snapshot — a
    plan that changed the state it was planning against would be
    useful exactly once.
    """
    work = list(pops)
    held = set(cluster.indices if isinstance(cluster, Cluster) else cluster)
    for i in held:
        if 0 <= i < len(work):
            work[i] &= ~colony_struct.POP_MASK_ASSIGNED
    landed = 0
    while True:
        index = next((i for i in range(min(n_pops, len(work)))
                      if not colony_struct.pop_is_assigned(work[i])), None)
        if index is None:
            break
        if (requested_job == -1
                or colony_struct.pop_prof(work[index]) == requested_job):
            work[index] |= colony_struct.POP_MASK_ASSIGNED
            landed += 1
            continue
        ok, reason = _can_take_job(work, n_pops, max_farms, index,
                                   requested_job)
        if not ok:
            return DropPlan(landed, len(held) - landed, reason, index)
        work[index] = ((work[index] & ~colony_struct.POP_MASK_PROF)
                       | (requested_job << 7)
                       | colony_struct.POP_MASK_ASSIGNED)
        landed += 1
    return DropPlan(landed, len(held) - landed)
