#!/usr/bin/env python3
"""Drop a cluster at every point of a cell and prove the point does
not matter.

Data's requirement, 9 September 2026: *where in the cell the figure is
dropped must not matter.* This VERIFIES it rather than assuming it.

    python tools/colony_drop_sweep.py --expect reference
    python tools/colony_drop_sweep.py --expect reference --probe

**WHY IT CAN BE ASSUMED AND IS NOT.** The original's drop target is a
FIELD, added unconditionally per row and per job: mode 1 of
`COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_` ends in
`fields::Add_Scroll_Field_(left_x, top_y, left_x, right_x + 8, left_x,
right_x, right_x - left_x + 8, 30, …)` (coldraw.cpp:409), so native x
101..234 / 236..376 / 378..510 accept a drop whether or not the column
holds an icon, and `COLSUM::Evaluate_Colony_Pop_Input_` turns a hit on
one into `Send_Cluster_(colony, job)` (colsum.cpp:869). Nothing in
that chain reads WHERE inside the field the click landed.

Nothing — except that the PICK-UP does. `Get_Selected_Pop_`
(colsum.cpp:1006) passes mode 3, whose test reads `*scroll_value_ptr`
(coldraw.cpp:361), which `fields::Find_Bar_Position_` writes out of
`mouse::Pointer_X_() + _pointer_offset` (fields.cpp:1702-1743). So one
half of this gesture is exquisitely sensitive to a pixel and the other
is not, and the only difference between them is which mode the field
was added in. That asymmetry is exactly the kind of thing a document
gets right and a binary gets wrong, and it is why this sweeps.

**EVERY PROBE IS A REAL MOVE, AND THIS TOOL WRITES TO THE PLAYER'S
LOADED GAME.** There is no dry run: a drop is an injected click and
the game acts on it. Each point is therefore followed by a move back,
and the array is checked against the bytes it had before — and the
FIRST round trip that does not restore is the last thing the tool
does. That rule was learned by breaking it: on 9 September 2026
`--scan` walked thirty configurations without stopping, several of
them inexact, and left the reference fixture with a pop permanently
moved on Blucher II. The `.GAM` on disk is never touched, so the fix
is always "reload the slot" — but nothing said so and nothing stopped.

**THE RESTORE IS THE HARD PART, AND IT IS ASSERTED, NOT HOPED.** Two
drops are only comparable if they start from the same bytes, so every
point is followed by a move back and the array is checked against the
bytes it had before. `Get_Cluster_` takes every identical pop from the
clicked one to the END of the array (colmove.cpp), so moving pop i out
and a DIFFERENT identical pop j back leaves the array with i and j
swapped — every count on screen correct and the bytes different. The
`--probe` mode does one round trip and reports whether the restore is
byte-exact on this save before any sweep is run; the sweep re-checks
it after every point and stops on the first failure rather than
reporting diffs that are not comparable.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from screens.colony_summary import (colonyicons, colonylist,  # noqa: E402
                                    colonypick)
import colony_move_hd as base  # noqa: E402
from colony_roundtrip import (bytes_of, cell_and_figure,  # noqa: E402
                              colony_diff, diff_signature,
                              restore_returns, _round_trip_for)


#: The points swept inside one drop cell, in the order they are run.
#: Four corners, the centre, an existing figure, and the plate's own
#: 1 px line — Data's list, plus the two the corners do not cover.
#:
#: A corner is the INCLUSIVE pixel: `rect.right` and `rect.bottom` are
#: one past the last pixel of the rect, and a click there lands in the
#: NEIGHBOUR — which is a real difference and not the one being
#: measured.
def sweep_points(rect, figure_rect):
    points = [
        ("centre", (rect.centerx, rect.centery)),
        ("top-left", (rect.left, rect.top)),
        ("top-right", (rect.right - 1, rect.top)),
        ("bottom-left", (rect.left, rect.bottom - 1)),
        ("bottom-right", (rect.right - 1, rect.bottom - 1)),
        # ON the plate's drawn outline. `StyleRenderer.draw_plate`
        # draws width 1 at every resolution, so this is the line
        # itself and not a pixel near it.
        ("plate line", (rect.centerx, rect.top)),
    ]
    if figure_rect is not None:
        points.append(
            ("over a figure", (figure_rect.centerx, figure_rect.centery)))
    return points


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--expect", default="reference")
    ap.add_argument("--row-name", default=None)
    ap.add_argument("--job", type=int, default=None)
    ap.add_argument("--target", type=int, default=None,
                    help="which column to drop into, so one run "
                         "proves a POPULATED column and another "
                         "an EMPTY one rather than whichever the "
                         "save happened to offer")
    ap.add_argument("--scan", action="store_true",
                    help="try a round trip for every (row, source, "
                         "target) the save offers and report which of "
                         "them restore byte-exactly, so a POPULATED "
                         "target can be swept from a state the sweep "
                         "can return to")
    ap.add_argument("--probe", action="store_true",
                    help="one round trip only, to establish whether "
                         "the restore is byte-exact on this save "
                         "before any sweep is trusted")
    args = ap.parse_args()

    from main import App
    app = App()
    if not app.connected:
        print("no game on the extension port")
        return 1
    counter = base.Counter(app.client)
    if not base.wait_for(app, lambda: (
            app.dispatcher.active is not None
            and getattr(app.dispatcher.active, "SCREEN_NAME", "")
            == "colony_summary"
            and app.dispatcher.active._rows), 15.0, "the colony summary"):
        print("the game is not on the colony summary")
        return 1
    screen = app.dispatcher.active
    if not base.identify(app.client.state, args.expect):
        return 1
    # THE SAVE IS STILL THE SAVE — see `fixtures.verify_colonies`.
    # This tool is the reason that check exists: it is the one that
    # drifted the fixture, and it is the one that must refuse to
    # start from a drifted one. All eleven of the player's colonies
    # and the forty-four it does not own, against the `.GAM`.
    if not base.verify_colonies(
            app.client.state, args.expect,
            {r["index"]: r["name"] for r in screen._rows}):
        return 1

    target = base.choose(screen, app.client.state, args.job, args.row_name)
    if target is None:
        print("no row this save can prove a move on")
        return 1
    row_index, cell, job, target_job, pick, plan, max_farms = target
    if args.target is not None:
        target_job = args.target
    row = screen._rows[row_index]
    colony = row["index"]
    print(f"sweeping row {row_index} {row['name']!r} jobs={row['jobs']}, "
          f"cell {cell} of column {job} -> column {target_job}")
    print(f"  cluster {pick.size}, plan {plan}")

    def bytes_now():
        return bytes_of(app)

    def round_trip(point, label):
        return _round_trip_for(app, screen, row_index, job, cell,
                               target_job, colony, point, label)

    # ── SCAN: which configurations can a sweep return from? ─────
    if args.scan:
        print("\nrow / source -> target : target icons, restore exact")
        for ri, r in enumerate(screen._rows):
            loaded = colonypick.pops_of(app.client.state, r["index"])
            if loaded is None:
                continue
            pops, n_pops, max_farms = loaded
            for sj in range(3):
                icons = colonyicons.icon_pops(pops, n_pops, sj)
                if not icons:
                    continue
                sc = len(icons) - 1
                pk = colonypick.pick_at(pops, n_pops, sj, sc,
                                        r["index"], ri, screen._sort_key)
                if isinstance(pk, colonypick.Refusal):
                    continue
                for tj in range(3):
                    if tj == sj:
                        continue
                    pl = colonypick.plan_move(pk, pops, n_pops, max_farms,
                                              r["index"], tj)
                    if isinstance(pl, colonypick.Refusal):
                        continue
                    held = len(r["cells"][tj])
                    rect_t, _f = cell_and_figure(screen, ri, tj)
                    if rect_t is None:
                        continue
                    # bind the module-level closure to THIS candidate
                    # PREDICTED, NOT PROBED — see `restore_returns`.
                    # This loop used to make a real move per row to
                    # find out, and the ones that could not return
                    # left the fixture drifted. It now answers from
                    # the pop array and moves nothing at all.
                    exact, nt = restore_returns(pops, n_pops, sj, sc, tj)
                    print(f"  {ri:2d} {r['name']:<14s} {sj} -> {tj} : "
                          f"{held} icons, may-return={exact}"
                          + ("" if exact else f"  ({nt})"))
        print("\n  nothing was moved: every line above is PREDICTED "
              "from the pop array. `may-return=False` is certain; "
              "`True` means no reason was found in pop[], and the "
              "recalculated fields are not modelled — 17 of 19 agreed "
              "with a probing run, both misses in the unsafe "
              "direction.")
        return 0

    # ── PROBE: is the restore byte-exact on this save at all? ────
    rect, fig = cell_and_figure(screen, row_index, target_job)
    if rect is None:
        print("the target column has no drop rect at this resolution")
        return 1
    _loaded = colonypick.pops_of(app.client.state, colony)
    _ok, _why = restore_returns(_loaded[0], _loaded[1], job, cell,
                               target_job)
    if not _ok:
        print(f"\ncolumn {target_job} cannot be swept from a state "
              f"this tool can return to: {_why}")
        print("  Nothing was moved. `--scan` lists the configurations "
              "that can.")
        return 1
    start = bytes_now()
    sig0, restored, note = round_trip((rect.centerx, rect.centery),
                                      "probe")
    if sig0 is None:
        print(f"the probe drop failed: {note}")
        return 1
    if restored is None:
        print(f"the probe restore failed: {note}")
        return 1
    exact = restored == start
    print(f"\nprobe round trip: restore is byte-exact = {exact}")
    if not exact:
        moved = colony_diff(start, restored)
        print(f"  colonies still differing after the round trip: "
              f"{[i for i, _ in moved]}")
        print("  A SWEEP CANNOT BE RUN FROM HERE. Two drops are only")
        print("  comparable from the same bytes, and this save does not")
        print("  return to them: `Get_Cluster_` takes every identical")
        print("  pop from the clicked one to the END of the array, so")
        print("  the pop that comes back is not always the one that")
        print("  went. Reported rather than worked around.")
        return 1
    if args.probe:
        print("  probe only; re-run without --probe for the sweep")
        return 0

    # ── THE SWEEP ────────────────────────────────────────────────
    _held = len(screen._rows[row_index]["cells"][target_job])
    _kind = "POPULATED" if _held else "EMPTY"
    print(f"\nsweeping {len(sweep_points(rect, fig))} points of the "
          f"{_kind} column {target_job} ({_held} icons)")
    results = []
    for name, point in sweep_points(rect, fig):
        start = bytes_now()
        sig, restored, note = round_trip(point, name)
        if sig is None:
            print(f"  {name:14s} at {point}  FAILED: {note}")
            return 1
        if restored != start:
            print(f"  {name:14s} at {point}  RESTORE NOT EXACT: {note}")
            return 1
        results.append((name, point, sig))
        print(f"  {name:14s} at {str(point):16s} "
              f"colony {colony} bytes changed at {list(sig[0])}, "
              f"recalculated elsewhere: {list(sig[1])}")

    # An EMPTY column too: the original's field is added after a walk
    # that may have drawn nothing (coldraw.cpp:409), so an empty
    # column takes a drop and this is where that is proven.
    empty_job = next((j for j in range(3)
                      if j not in (job, target_job)), None)
    empty_results = []
    if empty_job is not None:
        erect, _ = cell_and_figure(screen, row_index, empty_job)
        _l2 = colonypick.pops_of(app.client.state, colony)
        _ok2, _why2 = restore_returns(_l2[0], _l2[1], job, cell, empty_job)
        if erect is not None and not _ok2:
            print(f"\ncolumn {empty_job} SKIPPED, nothing moved: {_why2}")
            print("  The second half of the sweep is a gap in the "
                  "evidence and not a pass. Run it on a row where the "
                  "round trip returns — `--scan` lists them.")
            erect = None
        if erect is not None:
            _h2 = len(screen._rows[row_index]["cells"][empty_job])
            print(f"\nsweeping the {'POPULATED' if _h2 else 'EMPTY'} "
                  f"column {empty_job} ({_h2} icons)")
            _erect, _efig = cell_and_figure(screen, row_index, empty_job)
            for name, point in sweep_points(erect, _efig):
                start = bytes_now()
                sig, restored, note = round_trip(point, name)
                if sig is None:
                    print(f"  {name:14s} FAILED: {note}")
                    return 1
                if restored != start:
                    print(f"  {name:14s} RESTORE NOT EXACT")
                    return 1
                empty_results.append((name, point, sig))
                print(f"  {name:14s} at {str(point):16s} "
                      f"colony {colony} bytes changed at {list(sig[0])}, "
                      f"recalculated elsewhere: {list(sig[1])}")
    else:
        print("\nonly two job columns were reachable on this row — the "
              "second half of the sweep did not run, which is a gap in "
              "the evidence and not a pass")

    # ── THE VERDICT ──────────────────────────────────────────────
    bad = 0
    for label, group in (("populated", results), ("empty", empty_results)):
        if not group:
            continue
        first_sig = group[0][2]
        for name, point, sig in group[1:]:
            if sig != first_sig:
                bad += 1
                print(f"\nDIFFERENT at {label} {name} {point}:")
                print(f"  wanted {first_sig[0]} / {first_sig[1]}")
                print(f"  got    {sig[0]} / {sig[1]}")
    if bad:
        print(f"\n{bad} point(s) differ. The five rules in "
              f"`Give_Colonist_New_Job_` (colmove.cpp:518-558) and the "
              f"pick-up's native refusal (colmove.cpp:59-64) are what "
              f"to check before changing anything.")
        return 1
    print(f"\nIDENTICAL at every point: {len(results)} populated"
          + (f", {len(empty_results)} empty" if empty_results else "")
          + f". {counter}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
