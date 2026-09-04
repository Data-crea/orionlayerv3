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

**THE INTERLOCK, which is what makes step 4 safe to attempt at all.**
`INJECT_CLICK` coordinates are mapped as WINDOW coordinates
(`doc/orion2re_open_fixes.md` item 3), so they are only reliable at a
640x480 window, and this tool cannot ask the game how big its window
is. A mis-landed pick-up is not harmless: it takes a cluster we did
not choose, and there is no cancel that stays on the screen.

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
squish arithmetic: the hit test walks the icons and matches the first
whose right edge is at or past the pointer, with `*last_slot_idx_ptr
== pop_draw_index` as the fallback (coldraw.cpp:369), so a pointer
past every icon selects the last one. It also moves the fewest pops —
`Get_Cluster_` takes the identical run from there to the end of the
array, which for the last icon of its kind is one.

Nothing here is a retry. A step that does not land is reported and
the tool stops.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import numpy as np  # noqa: E402

from core.game_client import GameClient  # noqa: E402
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


def settle(client, tries=60):
    """A fresh snapshot AND a freshly DRAWN frame, or None.

    Both counters, not just the state one. `_first` is read off the
    scroll thumb, which lives in the framebuffer, so accepting a new
    STATE message with the previous VISUAL frame reads the window
    where it was before the step. That is not hypothetical: the first
    run of this sequence reported "_first 1 -> 1, stopping" for a
    decrement that had in fact worked, because the frame had not been
    redrawn yet.
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


def framebuffer_rows(state):
    return np.frombuffer(state.framebuffer,
                         dtype=np.uint8)[:640 * 480].reshape(480, 640)


def read_first(state, n):
    return cfirst.read_first(framebuffer_rows(state), n)


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
    state = settle(client, 200)
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
    client.inject_key(SORT_HOTKEY)
    state = settle(client) or state
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
            client.activate_field(_scroll_field(state, direction))
            state = settle(client) or state
            after = read_first(state, n)
            print(f"  {direction} {i + 1}/{count}: _first {before!r} "
                  f"-> {after!r}")
            if not isinstance(after, int):
                print("  the thumb stopped reading — stopping")
                return 1
            if direction == "up" and after == before:
                print("  the window did not move; reporting and "
                      "stopping rather than retrying")
                return 1
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
    state = settle(client) or state

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
    client.inject_click(dx, dy)
    state = settle(client) or state

    # 7. THE DIFF. Predicted after-state against the whole array.
    changed = [i for i, raw in enumerate(state.colonies_raw)
               if i < len(before_raw) and raw != before_raw[i]]
    print(f"\ncolonies whose bytes changed: {changed}")
    ok = True
    if changed != [colony_index]:
        print(f"  EXPECTED EXACTLY [{colony_index}] — a different "
              f"colony changing is the invisible failure this whole "
              f"sequence is built against")
        ok = False
    after = pops_of(state, colony_index) if colony_index < len(
        state.colonies_raw) else []
    predicted = cmove.predict_pops(pops, col.n_pops, col.max_farms,
                                   cluster, target_job)
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
