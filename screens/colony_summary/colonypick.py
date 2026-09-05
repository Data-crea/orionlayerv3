"""The HD-side pop selection: what is picked up, and what a drop would do.

**NOTHING IN THIS MODULE CAN SEND ANYTHING.** It imports the rules
(`colonymove`), the icon list (`colonyicons`) and the struct
accessors, and no client, no injection and no screen. That is the
decision this file exists to make structural rather than remembered,
and a smoke check asserts the import list stays that way.

**THE HD SELECTION IS NOT THE GAME'S CLUSTER, AND THAT IS WHY IT MAY
BE DISCARDED FOR FREE.** The original is click-click
(colsum.cpp:851-870): the first click on an icon calls
`COLMOVE::Get_Cluster_`, which unassigns the pops there and then, and
the second calls `Send_Cluster_`. A cluster in hand has exactly two
ways out — drop it, or leave the screen — because both
`Clear_Cluster_` call sites on this screen are leave-the-screen paths
(colsum.cpp:804 and :938). An HD preview that created a real cluster
would therefore strand a player who changed their mind, on a screen
whose own Cancel does not exist.

So the first click is LOCAL. It picks a pop, computes what the game
WOULD take, and draws it. Nothing is injected until the second click
names a target and every rule has passed — and then BOTH clicks go
out, back to back, which is what `colonysend` does.

**THE CANCEL IS AN HD EXTENSION, AND THIS IS THE SENTENCE IT RESTS
ON.** Right-click, or a left click on neither an icon nor a column,
discards the selection. MOO2 has no such thing: there is no cancel
that stays on this screen at all. It is not offered because it is
kinder — it is offered because *our* selection is not the game's
cluster, so discarding it costs nothing and changes nothing on the
other side of the wire. The moment a preview does inject, this
paragraph stops being true and the extension has to go. Marked here,
in `layout.json` under `move`, in `v3_projektstatus.md`, and in a
smoke check that fails if any of the three markings disappears.

**THE THREE REFUSALS THAT ARE NOT `colonymove`'S.** That module
mirrors the engine's five rules. Three more are ours, and each one
is about the CLICK FRAME rather than about a pop:

  `sort_unavailable`  HD's row order is not the game's, so no row
                      maps to a slot. Only `producing` is in
                      `colonyrows.SORT_UNAVAILABLE` today.
  `no_icon`           the square clicked has no icon behind it. The
                      HD row draws one square per pop of a job;
                      the original draws one per ASSIGNED pop
                      (coldraw.cpp:336), so the lists differ exactly
                      while a cluster is held.
  `other_colony`      the drop landed on a different row. That is
                      the original's inter-colony transport, whose
                      long branch opens an ETA dialog
                      (colmove.cpp:180-500) — a dialog is its own
                      chain under decision 21 and is not offered.

A partial move is refused too, and it does NOT get an id of its own:
the refusal carries the engine's own reason — the rule that stopped
the walk — plus the count that says how far it would have got. A
generic "this would not finish" would drop the one piece of
information the player needs to pick a different column.

**A PARTIAL MOVE IS REFUSED, AND THAT IS A DEVIATION.** The original
performs it: `Send_Cluster_` walks the cluster one pop at a time and
returns the moment `Give_Colonist_New_Job_` says no
(colmove.cpp:168-173), leaving the moved ones moved, the rest
unassigned and the cluster still held. What the fundament did not
record until 5 September 2026 is what the refusal itself does:
`Give_Colonist_New_Job_` answers every one of its four refusals with
`GENDRAW::Help_` (colmove.cpp:526, :534, :541, :555), and that is
`TEXTBOX::Do_Text_Box_` — a BLOCKING message box, `do { … } while
(fields::Get_Input_() == 0)` (textbox.cpp:149). So a refused drop
does not merely leave a partial: it parks the game in a modal the HD
screen does not draw, over a colony summary the player can no longer
reach, with a cluster still in hand.

Refusing before sending is therefore not politeness, it is the only
state this screen can guarantee it can leave. `plan_drop` already
answers "how many land and where it stops", so the test is one field:
a plan with a `reason` is not sent, whatever its `landed` is. The
cost is real and is named rather than hidden — a player who wants to
move two of twelve into a column with room for two cannot, where the
original would let them and then show a box. That is the DEVIATION,
and it ends the day something can dismiss the box (the box adds a
hidden field over the whole screen, textbox.cpp:246, so one injected
click would do it — unverified, and it is not built on a guess).
"""
from core.structs import colony as colony_struct
from . import colonyicons
from . import colonymove
from . import colonyrows

#: Refusals that are about the click frame rather than about a pop.
#: `colonymove`'s five keep their own ids; these three are ours and
#: the wording for all eight is `layout.json`'s `move` block
#: (decision 15).
REFUSE_SORT_UNAVAILABLE = "sort_unavailable"
REFUSE_NO_ICON = "no_icon"
REFUSE_OTHER_COLONY = "other_colony"


class Pick:
    """A pop selected in HD, and what the game would take with it.

    `slot` is the icon's position in the original's own column
    (`colonyicons.icon_pops`), which is what a click has to aim at;
    `pop` is its index in `pop[]`, which is what the rules read. They
    are different numbers and both are needed, because the column is
    not the array in order.

    `pops` is the array the pick was computed against, kept so a
    later drop can notice the colony changed underneath it. A
    selection that survives a snapshot it no longer describes is the
    quiet way to move the wrong pops.
    """

    __slots__ = ("colony", "position", "job", "slot", "pop", "cluster",
                 "pops", "n_pops", "icon_count")

    def __init__(self, colony, position, job, slot, pop, cluster,
                 pops, n_pops, icon_count):
        self.colony = colony
        self.position = position
        self.job = job
        self.slot = slot
        self.pop = pop
        self.cluster = cluster
        self.pops = tuple(pops)
        self.n_pops = n_pops
        self.icon_count = icon_count

    @property
    def size(self):
        return len(self.cluster.indices)

    def slots(self):
        """The icon slots this pick would take, for the drawing.

        A cluster is every identical pop from the clicked one to the
        END of the array (colmove.cpp:66-71), and identical pops
        share the state, the conquered bit and the low nibble — which
        is exactly what the icon walk groups by — so they are a RUN
        of icons starting at `slot`. Computed rather than assumed:
        the run is read back out of the icon list, so a pop that is
        somehow not drawn simply does not light up.
        """
        icons = colonyicons.icon_pops(self.pops, self.n_pops, self.job)
        return tuple(i for i, pop in enumerate(icons)
                     if pop in self.cluster.indices)

    def stale(self, pops, n_pops):
        """Has the colony changed since the pick was taken?"""
        return (tuple(pops[:n_pops]) != self.pops[:self.n_pops]
                or n_pops != self.n_pops)

    def __repr__(self):
        return (f"Pick(colony={self.colony}, job={self.job}, "
                f"slot={self.slot}, pop={self.pop}, size={self.size})")


class Refusal:
    """Why nothing was sent, and how many would have moved.

    `landed` is carried even on a refusal because the partial case
    has to be able to say "two of twelve" — the count is the reason
    the wording is about counts (`layout.json._count_note`).
    """

    __slots__ = ("reason", "landed", "carried", "total")

    def __init__(self, reason, landed=0, carried=0, total=0):
        self.reason = reason
        self.landed = landed
        self.carried = carried
        self.total = total

    def __repr__(self):
        return (f"Refusal({self.reason!r}, landed={self.landed}, "
                f"carried={self.carried}, total={self.total})")


def sort_binds(sort_key):
    """Can an HD row position be mapped to a game slot at all?

    Only while both lists are sorted the same way (decision 46, and
    `colonyselect.GameWindow`'s last paragraph). A key HD cannot
    honour leaves the game sorted by it and HD sorted by nothing of
    the kind, and every row would then name the wrong colony with
    every value on screen still correct.
    """
    return sort_key not in colonyrows.SORT_UNAVAILABLE


def pick_at(pops, n_pops, job, slot, colony, position, sort_key):
    """A `Pick` for icon `slot` of a column, or a `Refusal`.

    The pick-up refusal is `colonymove`'s: a native is rejected by
    `Get_Cluster_` before a cluster exists (colmove.cpp:59-64), with
    its own message. Ours are the two above it — a row order that
    does not bind, and a square with no icon behind it.
    """
    if not sort_binds(sort_key):
        return Refusal(REFUSE_SORT_UNAVAILABLE)
    pop = colonyicons.slot_pop(pops, n_pops, job, slot)
    if pop is None:
        return Refusal(REFUSE_NO_ICON)
    cluster = colonymove.plan_pickup(pops, n_pops, pop)
    if cluster.refused:
        return Refusal(cluster.refused)
    icons = colonyicons.icon_pops(pops, n_pops, job)
    return Pick(colony, position, job, slot, pop, cluster, pops, n_pops,
                len(icons))


def plan_move(pick, pops, n_pops, max_farms, colony, target_job):
    """The `DropPlan` for a drop, or a `Refusal`.

    Everything is checked against the pops handed in, not against the
    ones the pick was taken with: a snapshot arrives every frame and
    the colony may have changed. A stale pick is refused rather than
    re-based, because re-basing silently would move a cluster the
    player never saw.
    """
    if colony != pick.colony:
        return Refusal(REFUSE_OTHER_COLONY)
    if pick.stale(pops, n_pops):
        return Refusal(REFUSE_NO_ICON)
    plan = colonymove.plan_drop(pops, n_pops, max_farms, pick.cluster,
                                target_job)
    if plan.reason is not None:
        return Refusal(plan.reason, plan.landed, plan.carried, pick.size)
    return plan


def message(words, outcome, total=0):
    """The sentence to draw, from `layout.json`'s `move` block.

    Substitution is `replace` and never `str.format` (decision 37):
    a brace in a translated string must not be able to raise inside
    a render path.

    A refusal that would still have moved somebody gets both halves —
    the rule that stopped it, and the count — because "this job is
    full" alone reads as "nothing fits" when two of twelve would
    have.
    """
    def fill(template, **values):
        text = str(template or "")
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        return text

    if isinstance(outcome, Refusal):
        text = fill(words.get(outcome.reason, outcome.reason))
        if outcome.landed:
            text += " — " + fill(words.get("partial", ""),
                                 landed=outcome.landed,
                                 carried=outcome.carried,
                                 total=outcome.total)
        return text
    landed = getattr(outcome, "landed", 0)
    return fill(words.get("complete", ""), landed=landed,
                carried=getattr(outcome, "carried", 0), total=total or landed)


def column_of(pops, n_pops, job):
    """How many icons a column draws — the count the geometry needs.

    One line, and it is here rather than at the call sites because
    the number is `colonyicons`' and the temptation is `row["jobs"]`,
    which counts pops rather than icons.
    """
    return len(colonyicons.icon_pops(pops, n_pops, job))


def pops_of(state, colony_index):
    """(pops, n_pops, max_farms) for one colony of a snapshot, or None.

    A short or absent colony record is a state that reaches a render
    path (see `colonyrows.build_rows`), so it is answered rather than
    raised.
    """
    raws = getattr(state, "colonies_raw", None) or []
    if not 0 <= colony_index < len(raws):
        return None
    raw = raws[colony_index]
    if len(raw) < colony_struct.SIZE:
        return None
    col = colony_struct.parse(raw)
    return list(col.pop), col.n_pops, col.max_farms
