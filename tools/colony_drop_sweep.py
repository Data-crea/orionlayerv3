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


def colony_diff(before, after):
    """[(index, [byte offsets])] for every colony record that moved."""
    out = []
    for i, (b, a) in enumerate(zip(before, after)):
        if b != a:
            out.append((i, [k for k in range(min(len(b), len(a)))
                            if b[k] != a[k]]))
    return out


def diff_signature(before, after, colony):
    """A one-line, comparable description of what a drop did.

    Deliberately NOT the raw bytes: `COLCALC::Pass_Out_Imports_`
    rewrites `imports[ECON_FOOD]` on every non-outpost colony of the
    owner and `Post_Import_Computing_` rewrites three more fields on
    every NEEDY one (fundament, section 3), so "exactly one colony
    changed" is not a property of a pop move and a byte-equality test
    would fail on a correct one. What has to be identical between two
    drops is the MOVED COLONY's own record and the SET of other
    colonies the recalculation touched.
    """
    changed = colony_diff(before, after)
    others = sorted(i for i, _ in changed if i != colony)
    mine = next((offs for i, offs in changed if i == colony), [])
    return (tuple(mine), tuple(others),
            bytes(after[colony]) if colony < len(after) else b"")


def drop_at(app, screen, row_index, job, cell, target_job, point,
            counter, label):
    """One pick and one drop at `point`. (ok, note)."""
    xy = base.square_xy(screen, row_index, job, cell)
    if xy is None:
        return False, "the row is not drawn"
    base.click_at(app, *xy)
    if screen._move.pick is None:
        return False, f"no selection ({screen._move.message!r})"
    base.click_at(app, *point)
    if not base.wait_for(app, lambda: not screen._move.busy, 20.0, label):
        return False, "the send never finished"
    if screen._move.pick is not None:
        return False, "the selection is still held"
    return True, screen._move.message or ""


def cell_and_figure(screen, row_index, target_job):
    """(drop rect, an existing figure's rect or None) for one column."""
    area, cfg, scale, n_rows = screen._list_view()
    first = screen._first
    bands = colonylist.row_bands(area, cfg, scale, n_rows - first)
    band = row_index - first
    if not 0 <= band < len(bands):
        return None, None
    top, row_h = bands[band]
    row = screen._rows[row_index]
    rect = None
    for tj, r in colonylist.drop_targets(area, cfg, scale, row):
        if tj == target_job and r.width:
            rect = pygame.Rect(r.x, top, r.width, row_h)
    fig = None
    for cj, _ci, r in colonylist.row_boxes(area, cfg, scale, row).cells:
        if cj == target_job:
            fig = pygame.Rect(r.x, top, r.width, row_h)
            break
    return rect, fig


def bytes_of(app):
    return [bytes(b) for b in app.client.state.colonies_raw]


def _round_trip_for(app, screen, row_index, job, cell, target_job,
                    colony, point, label):
    """Move at `point`, move it back, return (signature, restored, note).

    `restored` is None when the round trip could not be completed, and
    the caller must treat "not byte-exact" and "did not complete" the
    same way: neither leaves a state two drops can be compared from.

    **THE RESTORE IS NOT ALWAYS POSSIBLE, AND THAT IS A PROPERTY OF
    THE SAVE.** `Get_Cluster_` takes every identical pop from the
    clicked one to the END of the array, so taking the target column's
    LAST icon takes exactly one pop only when that pop is the last
    identical one in the array. Move a pop into a column that already
    holds one with a higher array index and the pop that comes back is
    the OTHER one — the array ends with the two swapped, every count
    on screen still correct and the bytes different. That is the
    fundament's worst failure shape, and here it is a measurement
    rather than a bug: `--scan` reports which configurations return
    exactly, and the sweep refuses the ones that do not.
    """
    before = bytes_of(app)
    ok, note = drop_at(app, screen, row_index, job, cell, target_job,
                       point, None, label)
    if not ok:
        return None, None, note
    after = bytes_of(app)
    sig = diff_signature(before, after, colony)
    row_now = next((r for r in screen._rows if r["index"] == colony), None)
    if row_now is None:
        return sig, None, "the row left the list"
    back_cell = len(row_now["cells"][target_job]) - 1
    if back_cell < 0:
        return sig, None, "the target column drew no icon to take back"
    bxy = base.square_xy(screen, row_index, target_job, back_cell)
    rect, _fig = cell_and_figure(screen, row_index, job)
    if bxy is None or rect is None:
        return sig, None, "the row is not drawn for the restore"
    base.click_at(app, *bxy)
    if screen._move.pick is None:
        return sig, None, f"restore pick refused ({screen._move.message!r})"
    base.click_at(app, rect.centerx, rect.centery)
    if not base.wait_for(app, lambda: not screen._move.busy, 20.0,
                         "restore"):
        return sig, None, "the restore never finished"
    return sig, bytes_of(app), note


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
                    globals()["_scan_ctx"] = (ri, sj, sc, tj, r["index"])
                    st0 = bytes_now()
                    sg, rs, nt = _round_trip_for(
                        app, screen, ri, sj, sc, tj, r["index"],
                        (rect_t.centerx, rect_t.centery), "scan")
                    exact = rs is not None and rs == st0
                    print(f"  {ri:2d} {r['name']:<14s} {sj} -> {tj} : "
                          f"{held} icons, exact={exact}"
                          + ("" if exact else f"  ({nt})"))
                    if not exact:
                        # ── STOP. EVERY PROBE IS A REAL MOVE. ──────
                        # This loop used to carry on, and each
                        # inexact round trip left the save further
                        # from where it started: run on the reference
                        # fixture on 9 September 2026 it walked
                        # thirty configurations, and Blucher II ended
                        # with one pop permanently in scientists that
                        # had begun in farmers. The scan is a
                        # DIAGNOSTIC and it writes to the player's
                        # loaded game — so the first configuration it
                        # cannot return from is the last one it may
                        # try. What it reports is still useful: the
                        # rows above it are the ones a sweep can run
                        # on.
                        print()
                        print("  STOPPED. A round trip that does not")
                        print("  restore has CHANGED THE LOADED GAME,")
                        print("  and every further probe would change")
                        print("  it again. Reload the save before any")
                        print("  acceptance run.")
                        return 1
        print("\n  every configuration above restored exactly; the "
              "save is as it was loaded")
        return 0

    # ── PROBE: is the restore byte-exact on this save at all? ────
    rect, fig = cell_and_figure(screen, row_index, target_job)
    if rect is None:
        print("the target column has no drop rect at this resolution")
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
