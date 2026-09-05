"""Move one pop on the colony summary, and prove where it landed.

    python tools/colony_move_probe.py              # dry run, default
    python tools/colony_move_probe.py --commit     # actually click

**The failure mode this is built against is invisible.** A click that
lands on the wrong row leaves every number on both screens correct
and only the destination wrong, so looking at the screen cannot
settle it. What settles it is a prediction made before the click and
a byte-for-byte diff after: `colonymove.plan_drop` computes the
resulting pop words, and the whole colony array is compared against
them afterwards.

**THE SEQUENCE, and the order is not negotiable** (decision 46):

  1. push a known sort key, so HD's row order and the game's list
     order are the same one — `Switched_cmp_` has no toggle
     (colsum.cpp:378-401), so re-sorting by the key the game already
     holds is idempotent;
  2. establish `_first`, ONE activation at a time, reading it back
     off the scroll thumb after each — `ext::g_pending_field` is a
     single slot, so a batch would leave only the last;
  3. check the rules;
  4. pick up;
  5. **verify the pick-up before dropping** — see below;
  6. drop.

**EVERY ONE OF THOSE STEPS WAITS FOR ITS EFFECT, NEVER FOR A
MESSAGE** — see `after_send`, which is where the reason is written
down. The short form: `ext::Tick()` consumes injected input before it
serializes anything, so the first snapshot after a send is the world
from before the game acted, and a wait that accepts it reports a step
that worked as a step that did not. That is exactly how this tool
stopped on its first two runs.

**THE INTERLOCK, which is what makes step 4 safe to attempt at all.**
A mis-landed pick-up is not harmless: it takes a cluster we did not
choose, and there is no cancel that stays on the screen. Two things
can put the click somewhere other than where it was aimed, and both
are `doc/orion2re_open_fixes.md` item 3: the coordinates were mapped
as WINDOW coordinates, and the injected POINTER did not survive to
the moment the field was pushed. Both halves are patched in the
binary this tool is run against — which is a claim about a build, not
about the source, so it is verified here rather than assumed.

So the pick-up is verified against its prediction before anything
else happens. `Get_Cluster_` clears bit 0x200 on exactly the pops it
takes (colmove.cpp:70), and that is on the wire — so the snapshot
after the click says precisely which cluster is held. If it is not
the predicted one, the tool drops it back onto the column it came
from and stops. That is an exact undo rather than a guess:
`Send_Cluster_` with a requested job equal to the pop's current job
takes the re-flag path at colmove.cpp:165, sets 0x200 back and
consults no rule, which is bit-for-bit what `Get_Cluster_` undid.

**The first target is the LAST icon in a column**, which needs no
squish arithmetic: the walk matches the first icon whose right edge
is at or past the value, with `*last_slot_idx_ptr == pop_draw_index`
as the fallback (coldraw.cpp:361), so a click past every icon
selects the last one. It also moves the fewest pops — `Get_Cluster_`
takes the identical run from there to the end of the array, which for
the last icon of its kind is one.

CORRECTED 5 September 2026: that walk is MODE 3 and its input is the
SCROLL FIELD's value, not `mouse::Pointer_X_()` directly.
`Get_Selected_Pop_` (colsum.cpp:1006) passes mode 3, whose test
reads `*scroll_value_ptr` (coldraw.cpp:361); the value is written by
`Find_Bar_Position_` (fields.cpp:1702-1743) out of
`mouse::Pointer_X_() + _pointer_offset` when the field is pushed
down, and the scroll field's range is built so that the value IS the
pointer x, clamped to the column (`Add_Scroll_Field_(left_x, top_y,
left_x, right_x + 8, left_x, right_x, right_x - left_x + 8, 30, …)`,
coldraw.cpp:409). Same conclusion — the pointer decides the icon —
through one more link than the fundament recorded, and the extra link
is not decoration: the value SURVIVES between clicks, and
`_pointer_offset` (the cursor picture's frame, mouse.cpp:115) is
added to it. Neither is something to reason about here; the interlock
below measures the result instead.

Nothing here is a retry. A step that does not land is reported and
the tool stops.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from core.game_client import GameClient  # noqa: E402
from core.wire_protocol import EFFECT_PAIRS  # noqa: E402
from core.structs import colony as colony_struct  # noqa: E402
from screens.colony_summary import colonyfirst as cfirst  # noqa: E402
from screens.colony_summary import colonymove as cmove  # noqa: E402
from screens.colony_summary import colonyrows as crows  # noqa: E402
from screens.colony_summary.colonyselect import GameWindow  # noqa: E402

#: The three job columns, native. `Add_Fields_Pop_For_`
#: (colsum.cpp:312-346) passes these as (left_x, right_x) per job,
#: and the row's top is `slot * 31 + 34`.
COLUMNS = ((101, 226), (236, 368), (378, 502))
ROW_PITCH, ROW_TOP = 31, 34

#: How far inside the column's right edge to click. Any pointer past
#: the last icon selects it (coldraw.cpp:369); 4 keeps us off the
#: boundary without needing to know the squish.
RIGHT_MARGIN = 4

SORT_KEY, SORT_HOTKEY = "name", ord("n")


def snapshot(client, tries=60):
    """A fresh snapshot AND a freshly DRAWN frame, or None.

    Both counters, not just the state one. `_first` is read off the
    scroll thumb, which lives in the framebuffer, so accepting a new
    STATE message with the previous VISUAL frame reads the window
    where it was before the step.

    **This is the wait for a READING, never for an EFFECT** — see
    `after_send`, which is the one to use after anything is injected.
    """
    seen_state = client.stats.get("state", 0)
    seen_visual = client.stats.get("visual", 0)
    for _ in range(tries):
        client.poll()
        if (client.stats.get("state", 0) > seen_state
                and client.stats.get("visual", 0) > seen_visual
                and client.state.framebuffer is not None):
            return client.state
        time.sleep(0.05)
    return None


def after_send(client, ready, tries=60):
    """Poll until `ready(state)`, having first let the pre-effect
    snapshot go by. Returns the state, or None on a timeout.

    **THE FIRST SNAPSHOT AFTER A SEND IS PRE-EFFECT BY CONSTRUCTION,
    and no counter can fix that** — measured 5 September 2026.
    `ext::Tick()` calls `ProcessInput()` FIRST and serializes the
    state and the frame AFTER it (ext_api.cpp:341-386), so the very
    tick that consumes an injected command also ships the world from
    before the game acted on it. The effect appears on the SECOND
    state/visual pair, never the first: one increment of the game's
    list window, logged per arriving pair, read `_first` 0 at pair 1
    and 1 at pair 2.

    That is why waiting for "a fresh snapshot" was not enough even
    after it was fixed to wait for a fresh FRAME. Both counters moved,
    and both moved one tick too early. So this waits for the EFFECT
    the caller names, with a floor of two pairs so a predicate that
    is already true cannot be satisfied by the pre-effect frame.

    **THE FLOOR IS A COUNT AND DECISION 21 REFUSES COUNTED WAITS, so
    it has to say why it is not one.** It is not a settling time:
    what ends this loop is `ready`. The number and the whole argument
    live in `core.wire_protocol.EFFECT_PAIRS`, because the gap is a
    property of the API's tick ordering and not of this tool — and
    the smoke test pins both sides of it.

    Nothing here retries a send. A step that does not land inside
    `tries` is reported by its caller, which stops.
    """
    seen_state = client.stats.get("state", 0)
    seen_visual = client.stats.get("visual", 0)
    for _ in range(tries):
        client.poll()
        if (client.stats.get("state", 0) >= seen_state + EFFECT_PAIRS
                and client.stats.get("visual", 0) >= seen_visual + EFFECT_PAIRS
                and client.state.framebuffer is not None
                and ready(client.state)):
            return client.state
        time.sleep(0.05)
    return None


def local_colonies(state):
    """(count, [(index, colony)]) — the pair N_Colonies_ counts on."""
    out = []
    for i, raw in enumerate(state.colonies_raw):
        if len(raw) < colony_struct.SIZE:
            continue
        col = colony_struct.parse(raw)
        if col.owner == state.player_num and col.outpost_flag == 0:
            out.append((i, col))
    return len(out), out


def read_first(state, n):
    """`_first` off the scroll thumb of this snapshot's frame.

    The row shaping is `colonyfirst.rows`, not a numpy reshape of its
    own: this tool had the only copy and the screen needs the same
    one, and a second shaping of the same buffer is a second thing to
    get wrong by a stride.
    """
    return cfirst.read_first(cfirst.rows(state.framebuffer), n)


def first_reaches(n, want):
    """Predicate for `after_send`: the game's window is AT `want`.

    Below ten colonies the bar is not drawn at all (colsum.cpp:751)
    and `Update_First_` has already forced `_first = 0`
    (colsum.cpp:194-197), so `NOT_DRAWN` is the honest reading and
    the only reachable target is 0. That case is spelled out rather
    than folded into the comparison, because a reader that treated
    `NOT_DRAWN` as 0 would be unable to tell an idle channel from a
    real answer.
    """
    def ready(state):
        value = read_first(state, n)
        if n < GameWindow.SLOTS:
            return value is cfirst.NOT_DRAWN and want == 0
        return value == want
    return ready


def pops_of(state, colony_index):
    return list(colony_struct.parse(state.colonies_raw[colony_index]).pop)


def choose_target(state, rows):
    """A row where a wrong window would look DIFFERENT, or None.

    The point of the diff is that an off-by-one `_first` changes
    another colony. If the neighbours have the same pop composition
    that is invisible, so a target whose neighbours match is refused
    rather than used — the null-state lesson one domain over.
    """
    def shape(row):
        return tuple(row["jobs"])

    for pos, row in enumerate(rows):
        near = [rows[p] for p in (pos - 1, pos + 1)
                if 0 <= p < len(rows)]
        if not near or any(shape(o) == shape(row) for o in near):
            continue
        for job, count in enumerate(row["jobs"]):
            if count >= 1:
                return pos, row, job
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", action="store_true",
                    help="send the clicks; without it nothing is sent "
                         "beyond the sort key and the window steps")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    args = ap.parse_args()

    pygame.init()
    pygame.display.set_mode((32, 32))
    client = GameClient()
    if not client.connect(host=args.host, port=args.port):
        print("no game on the extension port")
        return 1
    state = snapshot(client, 200)
    if state is None:
        print("no snapshot")
        return 1
    if state.current_screen != 20:
        print(f"the game is on screen {state.current_screen}, not the "
              f"colony summary (20). Put it there and re-run — this "
              f"tool does not navigate.")
        return 1

    n, colonies = local_colonies(state)
    print(f"colony summary is up: {n} colonies of the local player")
    first = read_first(state, n)
    print(f"_first read off the scroll thumb: {first!r}")
    if first is cfirst.NOT_DRAWN and n >= GameWindow.SLOTS:
        print("  the bar should be drawn at this count and is not — "
              "stopping rather than guessing")
        return 1

    # 1. One sort order for both sides.
    # A sort is not only an order: the handler sets `_first = 0`
    # (colsum.cpp:830-837), so the window going home IS the effect
    # this key can be waited on for. Where it was already 0 the wait
    # falls through on the pre-effect floor alone, which is why the
    # steps below still establish rather than assume.
    client.inject_key(SORT_HOTKEY)
    settled = after_send(client, first_reaches(n, 0))
    if settled is None:
        print(f"  the sort key did not put the window at 0 "
              f"(_first reads {read_first(client.state, n)!r}) — stopping")
        return 1
    state = settled
    rows = crows.build_rows(state, SORT_KEY)
    print(f"sorted by {SORT_KEY!r}: {len(rows)} rows")

    pick = choose_target(state, rows)
    if pick is None:
        print("no row whose neighbours differ in pop composition — a "
              "wrong window would look identical here, so there is "
              "nothing this save can prove. Stopping.")
        return 1
    position, row, job = pick
    print(f"target: row {position} {row['name']!r} jobs={row['jobs']} "
          f"column {job}")

    plan, slot = GameWindow.slot_for(n, position)
    if plan.refused:
        print(f"window refuses that row: {plan.refused}")
        return 1
    print(f"window plan: {plan}  -> slot {slot}")

    # 2. Establish, one at a time, confirming each.
    steps = ([("down", plan.down)] if plan.down else []) + \
            ([("up", plan.up)] if plan.up else [])
    for direction, count in steps:
        for i in range(count):
            before = read_first(state, n)
            if not isinstance(before, int):
                print(f"  the thumb reads {before!r} — stopping")
                return 1
            # The EFFECT this step must have, named before it is sent.
            # Decrement clamps at 0 (colsum.cpp:211-214), so a step at
            # the top legitimately moves nothing; increment always
            # moves, because the plan never asks for one past `n - 10`.
            want = max(0, before - 1) if direction == "down" else before + 1
            client.activate_field(_scroll_field(state, direction))
            settled = after_send(client, first_reaches(n, want))
            if settled is None:
                print(f"  {direction} {i + 1}/{count}: _first stayed "
                      f"{read_first(client.state, n)!r}, wanted {want} — "
                      f"reporting and stopping rather than retrying")
                return 1
            state = settled
            print(f"  {direction} {i + 1}/{count}: _first {before!r} "
                  f"-> {want}")
    final = read_first(state, n)
    if final != plan.first:
        print(f"established _first = {final!r}, wanted {plan.first} — "
              f"stopping")
        return 1
    print(f"_first established at {final} and confirmed on the thumb")

    # 3. The rules, before anything is sent.
    colony_index = row["index"]
    pops = pops_of(state, colony_index)
    col = colony_struct.parse(state.colonies_raw[colony_index])
    icon_indices = [i for i in range(col.n_pops)
                    if colony_struct.pop_prof(pops[i]) == job
                    and colony_struct.pop_is_assigned(pops[i])]
    if not icon_indices:
        print("no assigned pop in that column")
        return 1
    start = icon_indices[-1]
    cluster = cmove.plan_pickup(pops, col.n_pops, start)
    print(f"pick-up predicts: {cluster} from pop {start}")
    if cluster.refused:
        print(f"  the game would refuse the pick-up: {cluster.refused}")
        return 1
    target_job = next(j for j in (1, 2, 0) if j != job)
    drop = cmove.plan_drop(pops, col.n_pops, col.max_farms, cluster,
                           target_job)
    print(f"drop onto column {target_job} predicts: {drop}")

    before_raw = list(state.colonies_raw)
    pick_field = _job_field(state, slot, job)
    drop_field = _job_field(state, slot, target_job)
    print(f"pick-up field {pick_field}, drop field {drop_field}")

    if not args.commit:
        print("\ndry run — nothing was clicked. Re-run with --commit.")
        return 0

    # 4. PICK UP. Click the column's right edge: a pointer past every
    # icon selects the LAST one (coldraw.cpp:369), so this needs no
    # squish arithmetic.
    px, py = pick_field
    print(f"\nclick 1 (pick up) at native ({px}, {py})")
    client.inject_click(px, py)
    # THE EFFECT, not the send: `Get_Cluster_` clears bit 0x200 on
    # the pops it takes (colmove.cpp:70), so a cluster in hand is
    # visible on the wire. Waiting for ANY cluster rather than for
    # the predicted one keeps the two failures apart — nothing was
    # picked up, and the wrong thing was.
    settled = after_send(client, lambda st: _held_cluster(st) is not None)
    if settled is None:
        print("  no cluster appeared in the snapshot. The click "
              "reached no icon: Get_Selected_Pop_ resolves one from "
              "the scroll field's value, which Find_Bar_Position_ "
              "writes from mouse::Pointer_X_() (fields.cpp:1702, "
              "reached through Draw_Field_ at fields.cpp:2837), so a "
              "pointer that does not survive to the field push "
              "selects nothing. Stopping.")
        return 1
    state = settled

    # 5. THE INTERLOCK. Get_Cluster_ clears bit 0x200 on exactly the
    # pops it took (colmove.cpp:70) and that is on the wire, so the
    # snapshot says which cluster is actually held. Verify it before
    # anything else moves.
    held = _held_cluster(state)
    want = (colony_index, tuple(cluster.indices))
    if held != want:
        print(f"  PICK-UP DID NOT MATCH THE PREDICTION")
        print(f"    predicted: colony {want[0]} pops {list(want[1])}")
        print(f"    actually held: "
              + (f"colony {held[0]} pops {list(held[1])}" if held
                 else "nothing"))
        print("  The click did not land where it was aimed — most "
              "likely INJECT_CLICK's window mapping, open fix 3.")
        if held:
            print("  A CLUSTER IS HELD. Leaving the colony summary "
                  "clears it exactly: Get_Cluster_ only cleared bit "
                  "0x200 and Clear_Cluster_ sets it back, job bits "
                  "untouched (colmove.cpp:39-53).")
        print("  Not retrying and not clicking again with geometry "
              "that has just been shown wrong. Stopping.")
        return 1
    print(f"  held cluster matches the prediction: colony "
          f"{held[0]} pops {list(held[1])}")

    # 6. DROP.
    dx, dy = drop_field
    print(f"click 2 (drop on column {target_job}) at native ({dx}, {dy})")
    predicted = cmove.predict_pops(pops, col.n_pops, col.max_farms,
                                   cluster, target_job)
    client.inject_click(dx, dy)
    # The effect this one must have is the whole point of the tool,
    # so it is what is waited on. A drop that lands DIFFERENTLY never
    # satisfies it — hence the fall-through, which takes whatever the
    # game did produce and lets the diff below say what it was. A
    # timeout here is not a failure by itself.
    settled = after_send(client, lambda st: _pops_are(st, colony_index,
                                                      col.n_pops, predicted))
    if settled is None:
        print("  the predicted array did not appear inside the wait — "
              "diffing what the game actually holds")
        state = snapshot(client) or state
    else:
        state = settled

    # 7. THE DIFF. Predicted after-state against the whole array.
    changed = [i for i, raw in enumerate(state.colonies_raw)
               if i < len(before_raw) and raw != before_raw[i]]
    # Bound to names: an index alone is not a claim anybody can check,
    # and "the wrong colony moved" is the failure this diff exists for.
    named = {r["index"]: r["name"] for r in rows}
    print("\ncolonies whose bytes changed: "
          + (", ".join(f"{i} = {named.get(i, chr(40) + 'not the ' 'player' + chr(41))}"
                       for i in changed) or "none"))
    ok = True
    if changed != [colony_index]:
        print(f"  EXPECTED EXACTLY [{colony_index}] — a different "
              f"colony changing is the invisible failure this whole "
              f"sequence is built against")
        ok = False
    after = pops_of(state, colony_index) if colony_index < len(
        state.colonies_raw) else []
    for i in range(col.n_pops):
        if after[i] != predicted[i]:
            print(f"  pop {i}: got 0x{after[i]:x}, predicted "
                  f"0x{predicted[i]:x}")
            ok = False
    print("  every pop word matches the prediction" if ok
          else "  MISMATCH")
    return 0 if ok else 1


def _job_field(state, slot, job):
    """(x, y) to click for one row's job column, from the FIELD LIST.

    The game reports the rect, so nothing here guesses geometry. The
    x is the field's right edge less a margin: a pointer past every
    icon selects the last one (coldraw.cpp:369).
    """
    left = COLUMNS[job][0]
    top = slot * ROW_PITCH + ROW_TOP
    for f in getattr(state, "fields", None) or []:
        if abs(f.x - left) <= 2 and abs(f.y - top) <= 2:
            return (f.x_end - RIGHT_MARGIN, (f.y + f.y_end) // 2)
    raise SystemExit(f"no job field at native ({left}, {top}) for "
                     f"slot {slot} column {job}")


def _held_cluster(state):
    """(colony index, pops) currently unassigned, or None.

    `Get_Cluster_` clears POP_MASK_ASSIGNED on exactly the pops it
    takes, so a held cluster is visible on the wire.
    """
    for i, raw in enumerate(state.colonies_raw):
        if len(raw) < colony_struct.SIZE:
            continue
        col = colony_struct.parse(raw)
        loose = tuple(p for p in range(col.n_pops)
                      if not colony_struct.pop_is_assigned(col.pop[p]))
        if loose:
            return (i, loose)
    return None


def _pops_are(state, colony_index, n_pops, predicted):
    """Does the colony's pop array match `predicted`, word for word?

    The predicate `after_send` waits on for the drop. Word for word
    and not a summary: `plan_drop` answers a count, and two different
    moves can land the same count in the same column.
    """
    if colony_index >= len(state.colonies_raw):
        return False
    pops = pops_of(state, colony_index)
    return all(pops[i] == predicted[i] for i in range(n_pops))


def _scroll_field(state, direction):
    """The up/down button's field id, found by its own geometry.

    `_x_fields[1]` is at native (619, 15) and `_x_fields[2]` at
    (619, 316) (colsum.cpp:263-264). Matching on the reported rect
    rather than on an index, because an index is a field dump's word
    for it and those have been wrong before.
    """
    want_y = 15 if direction == "down" else 316
    # `down` means _first decreases: the TOP button is Decrement_First_
    best = None
    for f in getattr(state, "fields", None) or []:
        x, y = getattr(f, "x", None), getattr(f, "y", None)
        if x is None or y is None:
            continue
        if abs(x - 619) <= 6 and abs(y - want_y) <= 6:
            best = f.index
    if best is None:
        raise SystemExit(f"no scroll field near (619, {want_y}) in the "
                         f"field list")
    return best


if __name__ == "__main__":
    sys.exit(main())
