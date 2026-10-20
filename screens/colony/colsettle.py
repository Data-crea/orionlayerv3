"""Colonists carried to another colony at the star — work order 233, open
fix 92 (`MSG_SETTLE_POPS`).

THE ORIGINAL: with colonists in hand (`_field_mode` 1), a click on a planet
of the system display sends them to that planet's colony,
`COLMOVE::Send_Cluster_(planet.colony_index, -1)` (colony.cpp:1796-1800).
For each pop in hand `SETTLER::Pop_Tries_To_Settle_` decides
(settler.cpp:234-306) and `Settle_Pop_` moves it (:308-343): the pop keeps
its job, joins the end of the other colony's array as `Add_Settler_To_
Colony_` builds it (:16-63), and the last pop of the source takes its place.
A refusal answers with a text box naming every reason (colmove.cpp:385-470)
and the rest stays in hand; a move that needs an ETA or finds no room first
asks (:200-260).

HD (TRANSCRIPTION `settle`): the drop on a planet of the system display is
ONE command naming the colony, the target and the pops that settle; the
engine runs the same two functions and settles all of them or none (open
fix 92; fundament 52's DEVIATION, for its reason).

TRANSCRIPTION `settle_count` (work order 315, Data: "why can I not move
population to another planet?"): `Send_Cluster_` asks for EACH pop in hand
in turn (colmove.cpp:177-197, :475) and moves every one it may, then stops
at the first it may not; the rest stay in hand (`Reset_Field_Mode_` only
when no unassigned pop is left, colmove.cpp:528-531), and the box names the
reason with the number already sent ("Settlers Failed.", E 0xFD / 0x241 and
E 0x80, colmove.cpp:316, :366-372, :404, :454-460). Until work order 315
`plan` refused the whole hand when it did not fit at once — and a click on
any figure but a row's last takes every identical colonist after it
(`Get_Cluster_`), so a drop on a smaller colony at the star moved nothing
("Declined because the planet is at its population limit", seen live on
Data's game of 19 October: 15 workers in hand, room for 1). `plan` now
counts the pops the original moves without a question — the source keeps
its last pop (settler.cpp:269-272), the target takes them while it has room
(:296-297, `Room_For_Another_`) — sends those, and leaves the rest in hand
with the original's sentence.
DEVIATION `settle_without_fix103` (work order 316): this module is the
move on an engine with open fix 92 ALONE. There the original's question at
the first pop without room (E 0x205 / 0x203, `Do_Confirmation_Box_`,
colmove.cpp:204-266) is answered NO, always — fix 92 refuses a pop without
room, so a YES has no command — and the refusal and the part sent are said
on the screen's message line, not in the "Settlers Failed." box (E 0x1D6,
colmove.cpp:366-372, :454-460); no "Settlers Depart" box follows (E
0x1D5/0x1D1, :482-522); only colonies at the colony's own star, the system
display's, are reached, and no TRANSPORT button is drawn. On an engine with
open fix 103 (STLR on the wire) the colony screen takes `colxfer` /
`colxferflow` instead: the original's walk to any colony, its questions
and its boxes (`coltransfer`).

Before sending, HD mirrors the
refusals it can read on the wire (decision 33), each with the game's own
sentence — `plan` returns them; what HD cannot read (a space anomaly or the
plague at the source, room for another race than the owner's, settlers in
transit to the planet) the engine still refuses, and the screen then says
so with the game's own fallback sentence (E 0xE4). So `plan` is a FILTER,
not a guarantee (P627): its name for success is `may_settle`.

"""
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct
from screens.colony_summary import colonyrows

#: The game's own sentences (ESTRINGS), Send_Cluster_'s lines (colmove.cpp:
#: 152-155, :385-470).
E_NOT_A_COLONY = 0x210
E_NOT_YOURS = 0x211
E_BLOCKADED = 0x207
E_OUTPOST = 0x1FD
E_LAST_POP = 0x241
E_CONQUERED = 0x20E
E_NO_ROOM = 0xFD
E_FAILED = 0xE4

#: `Room_For_Another_`'s ceiling on every colony (settler.cpp:96-98).
MAX_POPS = 42


class Refusal:
    """Why nothing is sent: the game's sentence for it (an ESTRINGS id)."""

    __slots__ = ("estring",)

    def __init__(self, estring):
        self.estring = estring

    def __repr__(self):
        return f"Refusal(E {self.estring:#x})"


class Expected:
    """What the settlement leaves: per colony, n_pops and the count per
    job — what `on_wire` compares. Not the words: the engine writes the
    target's new pop words itself (`Add_Settler_To_Colony_`), and a drawn
    row that waited for words HD only predicts would wait for nothing."""

    __slots__ = ("colonies", "pops", "sent", "rest", "stopped")

    def __init__(self, colonies, pops, sent=(), rest=(), stopped=None):
        self.colonies = colonies    # {index: (n_pops, (farmers, workers, scientists))}
        self.pops = pops            # {index: (n_pops, words)} — drawn meanwhile
        self.sent = tuple(sent)     # the source's pop indices the command names
        self.rest = tuple(rest)     # still in hand: indices AFTER the settle
        self.stopped = stopped      # the ESTRINGS id of why the rest stays

    def on_wire(self, state):
        raws = getattr(state, "colonies_raw", None) or []
        for index, (n, jobs) in self.colonies.items():
            if not 0 <= index < len(raws):
                return False
            rec = colony_struct.parse(raws[index])
            if rec.n_pops != n or jobs_of(rec.pop, rec.n_pops) != jobs:
                return False
        return True


def jobs_of(pops, n):
    """(farmers, workers, scientists) among the first n pop words."""
    out = [0, 0, 0]
    for p in list(pops)[:n]:
        prof = colony_struct.pop_prof(p)
        if 0 <= prof < 3:
            out[prof] += 1
    return tuple(out)


def target(view, orbit):
    """The colony index on orbit `orbit` of the system display, or a
    Refusal (`Send_Cluster_`'s `colony_idx < 0`: E 0x210, colmove.cpp:
    152-155)."""
    system = getattr(view, "system", None) or []
    planet = system[orbit] if 0 <= orbit < len(system) else None
    if planet is None or planet.colony_index < 0:
        return Refusal(E_NOT_A_COLONY)
    return planet.colony_index


def plan(state, view, pick, dest_index):
    """`Expected` for the pops in hand that settle in colony `dest_index`
    as `Send_Cluster_` moves them — one by one until the first that may
    not (TRANSCRIPTION `settle_count`; `stopped` names why, `rest` what
    stays in hand) — or the `Refusal` when not even the first may (the
    original's checks in `Pop_Tries_To_Settle_`'s order, as far as the
    wire carries them)."""
    raws = getattr(state, "colonies_raw", None) or []
    if not 0 <= dest_index < len(raws):
        return Refusal(E_NOT_A_COLONY)
    source = colony_struct.parse(raws[pick.colony])
    dest = colony_struct.parse(raws[dest_index])
    if dest.owner != source.owner:
        return Refusal(E_NOT_YOURS)
    if view.blockaded(source.owner):
        return Refusal(E_BLOCKADED)
    if dest.outpost_flag != 0:
        return Refusal(E_OUTPOST)
    held = sorted(pick.cluster.indices)
    pops = list(source.pop)
    n = int(source.n_pops)
    # a conquered colonist is its own kind (`Pops_Identical_`), so a hand
    # is all conquered or none: refused at its first pop
    if any(colony_struct.pop_is_conquered(pops[i]) for i in held):
        return Refusal(E_CONQUERED)
    count, stopped = settle_count(len(held), n, dest.n_pops,
                                  _room(state, dest, dest_index))
    if count == 0:
        return Refusal(stopped)
    return _expected(source, pick.colony, dest, dest_index, held, count,
                     stopped)


def settle_count(held, n_source, n_dest, room):
    """(how many of `held` pops `Send_Cluster_` settles before it stops,
    the ESTRINGS id it stops on or None) — per pop, in
    `Pop_Tries_To_Settle_`'s order: `only_one_pop_left` while the source
    has one pop (settler.cpp:269-272), then `no_room_at_destination`
    (:296-297) once the target holds its limit (`room`, None where HD
    cannot read it) or `Room_For_Another_`'s 42 (settler.cpp:94-99)."""
    limit = MAX_POPS if room is None else min(room, MAX_POPS)
    for moved in range(held):
        if n_source - moved <= 1:
            return moved, E_LAST_POP
        if n_dest + moved >= limit:
            return moved, E_NO_ROOM
    return held, None


def _room(state, dest, dest_index):
    """The target's population limit for its owner's race — the number the
    system display prints after the slash (`colonyrows.max_population`) —
    or None where HD cannot read it."""
    planets = getattr(state, "planets_raw", None) or []
    if not 0 <= dest.planet < len(planets):
        return None
    players = getattr(state, "player_raw", None) or []
    owner = (player_struct.parse(players[dest.owner])
             if 0 <= dest.owner < len(players) else None)
    traits = player_struct.traits(owner) if owner is not None else None
    return colonyrows.max_population(
        dest, planet_struct.parse(planets[dest.planet]), traits)


def _expected(source, source_index, dest, dest_index, held, count=None,
              stopped=None):
    """The two arrays after `Settle_Pop_` has run once per pop that
    settles (`count`, all in hand by default), in `Send_Cluster_`'s order:
    the first unassigned pop each time (colmove.cpp:160, :475), moved by
    `Settle_Pop_` — appended to the target with its job
    (`Add_Settler_To_Colony_`, settler.cpp:46-57) and replaced in the
    source by the source's last pop (:337-342). The farmer-to-scientist
    turn where the target's farms are full (:21-43) is mirrored; whatever
    the engine writes beyond it, `on_wire` does not compare. `sent` is
    which of the source's pops those were (the indices of the pick), `rest`
    where the ones still in hand stand afterwards."""
    src = list(source.pop)[:source.n_pops]
    dst = list(dest.pop)[:dest.n_pops]
    ids = list(range(len(src)))       # which pick index each slot holds
    for i in held:
        src[i] &= ~colony_struct.POP_MASK_ASSIGNED
    count = len(held) if count is None else count
    sent = []
    unassigned = lambda: next((i for i, p in enumerate(src)
                               if not colony_struct.pop_is_assigned(p)), None)
    i = unassigned()
    while i is not None and len(sent) < count:
        word = src[i]
        race = colony_struct.pop_player_index(word)
        prof = colony_struct.pop_prof(word)
        farmers = [k for k, p in enumerate(dst)
                   if colony_struct.pop_prof(p) == 0]
        if prof == 0 and len(farmers) >= dest.max_farms:
            if race < 8:
                prof = 2
            else:
                target_farmer = next(
                    (k for k in farmers
                     if colony_struct.pop_player_index(dst[k]) < 8), None)
                if target_farmer is not None:
                    dst[target_farmer] = _with_prof(dst[target_farmer], 2)
        # `Set_Original_Owner` keeps three bits (pop.h:35-37)
        new = race | ((race & 7) << 4) | (prof << 7) | \
            colony_struct.POP_MASK_ASSIGNED
        dst.append(new)
        sent.append(ids[i])
        src[i], ids[i] = src[-1], ids[-1]
        src.pop()
        ids.pop()
        i = unassigned()
    rest = [k for k, p in enumerate(src)
            if not colony_struct.pop_is_assigned(p)]
    return Expected(
        {source_index: (len(src), jobs_of(src, len(src))),
         dest_index: (len(dst), jobs_of(dst, len(dst)))},
        {source_index: (len(src), src), dest_index: (len(dst), dst)},
        sent, rest, stopped)


def _with_prof(word, prof):
    return (word & ~colony_struct.POP_MASK_PROF) | (prof << 7)
