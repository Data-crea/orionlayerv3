#!/usr/bin/env python3
"""Returning to a comparable state, and whether that is possible.

Split out of `colony_drop_sweep.py` on 9 September 2026 at 317 code
lines against the ~300 guideline (decision 6). The seam is real: the
sweep is about WHERE a click lands, and everything here is about the
separate and harder question of how to get back to the bytes you
started from — which earned its own fundament entry the same day and
is what any future tool driving the game will need before it needs a
sweep.

**EVERY PROBE IS A REAL MOVE.** There is no dry run for an injected
click: the game acts on it, and the player's loaded save is what
changes. Two drops are only comparable from the same bytes, so a
measurement here is always move-then-move-back, and the move back has
to be VERIFIED rather than assumed.
"""
import sys

from screens.colony_summary import colonyicons

import colony_move_hd as base


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


def restore_returns(pops, n_pops, source_job, cell, target_job):
    """Could a round trip through `target_job` return byte-exactly?

    **NECESSARY, NOT SUFFICIENT — and it was written believing
    otherwise.** This rules out ONE cause of a non-returning round
    trip, the one that lives in `pop[]`. It does not rule out the
    other, and a True here is "no reason found", never "it will
    return". The byte comparison after the move is still the
    authority; this only keeps the tool from making moves it can
    already know are hopeless.

    Measured against the probing scan's own results on the reference
    fixture, 9 September 2026: **17 of 19 agree, and both
    disagreements are in the dangerous direction** — predicted
    returnable, measured not. Both are scientists -> farmers, both
    completed their moves, and both left bytes changed outside
    `pop[]`. The leading explanation is the one the fundament already
    records in section 3: `Send_Cluster_` always ends in
    `Pass_Out_Imports_`, which rewrites `imports[ECON_FOOD]` on every
    non-outpost colony of the owner and `pop_growth`, `pop_roundoff`
    and `specialty` on every NEEDY one, and a move that changes food
    production and is then undone need not land the distribution
    passes back on the same numbers. **That is an explanation and not
    a measurement** — separating the two costs a run on a drifted
    save, and it has not been made.

    Which is why the sweep still verifies bytes after every point and
    stops on the first that does not return. The worst this function
    can cost is one drifting move, at the sweep's first point, and
    that is the floor for any test of a thing you can only learn by
    doing it.

    The part it DOES settle. The
    restore takes the target column's LAST ICON, and
    `Get_Cluster_` takes every identical pop from the clicked one to
    the END of the array — so it returns exactly the pop that went
    only when that pop is the last of the target column in the icon
    walk's order. The walk's innermost loop IS array order
    (coldraw.cpp:326-337) and every pop in these fixtures is identical
    apart from its job bits, so the test reduces to: is the moved
    pop's array index greater than every index already in the target
    column?

    Where it is not, the pop that comes back is a DIFFERENT one and
    the array ends with the two swapped — every count on screen
    correct and the bytes different, which is this project's worst
    failure shape and the reason the sweep asserts bytes rather than
    counts.
    """
    moving = colonyicons.icon_pops(pops, n_pops, source_job)
    if not 0 <= cell < len(moving):
        return False, "the source cell is not drawn"
    pop = moving[cell]
    already = colonyicons.icon_pops(pops, n_pops, target_job)
    if already and pop < max(already):
        return False, (f"pop {pop} would land in column {target_job} "
                       f"below pop {max(already)}, so the restore "
                       f"would take that one instead")
    return True, ""


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
