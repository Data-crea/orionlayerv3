"""Move a pop by CLICKING THE HD SCREEN, and prove where it landed.

    python tools/colony_move_hd.py                # dry run: pick, render, stop
    python tools/colony_move_hd.py --commit       # click the drop too
    python tools/colony_move_hd.py --cancel       # pick, then discard

**This is the acceptance run for the HD path, and the difference from
`colony_move_probe.py` is the whole point of it.** That tool computes
a native click and injects it. This one posts a real
`MOUSEBUTTONDOWN` into pygame's own queue, at a screen pixel inside
the drawn row, and lets `main.App` route it: `_handle_events` ->
`Dispatcher.route_click` -> `ColonySummaryScreen.handle_click` ->
`colonymoveui` -> `colonysend`. Nothing is called past the front
door. If the HD geometry, the row offset, the icon order or the
window plan is wrong anywhere along that path, this run is where it
shows.

It runs the real `App` against the real game, headless
(`SDL_VIDEODRIVER=dummy`), one frame at a time so the wait for each
effect is the screen's own.

**THE CLICK COUNTER IS THE EVIDENCE FOR THE CANCEL PATH.** Every
send method on the client is wrapped and counted, so `--cancel` can
assert that discarding a selection put NOTHING on the wire — which is
the claim, and not "the screen looks the same afterwards", because a
screen that sent a click and drew the old picture would look the same
too.

**THE PICTURE IS PART OF THE ACCEPTANCE, NOT A BONUS.** A held
selection is rendered to PNG before anything is dropped, because a
green table says the plan is right and only the picture says the
selection is visible — the "No Farming" label was drawn under the
worker squares for a day with every value correct.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from core.structs import colony as colony_struct  # noqa: E402
from screens.colony_summary import colonyicons  # noqa: E402
from screens.colony_summary import colonylist  # noqa: E402
from screens.colony_summary import colonymove  # noqa: E402
from screens.colony_summary import colonypick  # noqa: E402
from screens.colony_summary import colonysend  # noqa: E402
from colony_list_preview import side_by_side  # noqa: E402

SCREEN_COLONY_SUMMARY = 20


def native_png(state, path):
    """The game's own 640x480 frame, from the SAME snapshot, to PNG.

    The comparison this project keeps paying for is the side-by-side
    (fundament, "compare side by side before styling"), and it is only
    a comparison if both halves are one moment: the HD render is made
    from `state` and so is this. Taking the original half later would
    photograph a different game.

    Indexed pixels plus a 256-entry palette, exactly as
    `core.original_view` reads them — the wire carries no RGB.
    """
    fb, pal = state.framebuffer, state.palette
    if not fb or not pal:
        return None
    surf = pygame.Surface((640, 480), depth=8)
    surf.set_palette([(r, g, b) for r, g, b in pal])
    surf.get_buffer().write(bytes(fb[:640 * 480]))
    pygame.image.save(surf, path)
    return path

#: Where the held-selection picture goes. `tools/colony_list_preview`
#: uses /tmp/colony_list_preview for the same reason.
DEFAULT_OUT_DIR = os.path.join("/tmp", "colony_move_hd")


class Counter:
    """Wraps the client's three send paths and counts them.

    Not a mock: the real method still runs. What it buys is a claim
    about the WIRE rather than about the picture.
    """

    def __init__(self, client):
        self.client = client
        self.counts = {"inject_click": 0, "activate_field": 0,
                       "inject_key": 0}
        for name in self.counts:
            setattr(client, name, self._wrap(name, getattr(client, name)))

    def _wrap(self, name, method):
        def wrapped(*args, **kwargs):
            self.counts[name] += 1
            return method(*args, **kwargs)
        return wrapped

    def total(self):
        return sum(self.counts.values())

    def __repr__(self):
        return ", ".join(f"{k}={v}" for k, v in sorted(self.counts.items()))


def pump(app, frames=1):
    """Run the real loop for `frames` frames."""
    for _ in range(frames):
        app._handle_events()
        app._update()
        app._render()
        time.sleep(0.02)


def wait_for(app, ready, seconds=10.0, label=""):
    """Pump until `ready()`, or give up and say so."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        pump(app)
        if ready():
            return True
    print(f"  timed out waiting for {label}")
    return False


def click_at(app, x, y, button=1):
    """Post a real mouse event, the way a mouse would."""
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": button}))
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": button}))
    pump(app, 2)


def square_xy(screen, row_index, job, index):
    """The screen pixel of one CELL of one row — the renderer's own.

    **It asks `row_boxes` and multiplies no pitch.** It used to
    compute `track_x + slot * step` from a slot the caller had
    already flattened with `sum(row["jobs"][:job]) + slot`, which is
    a second copy of the layout in a tool whose whole job is to prove
    the layout. The markers of 6 September moved every cell right and
    this arithmetic did not move with them, so the acceptance run
    would have aimed one cell short of its own target — the same
    fault, in the tool built to catch it. Decision 5 covers tools
    too.
    """
    area, cfg, scale, n_rows = screen._list_view()
    first = screen._first
    bands = colonylist.row_bands(area, cfg, scale, n_rows - first)
    band = row_index - first
    if not 0 <= band < len(bands):
        return None
    top, row_h = bands[band]
    for cell_job, cell_index, rect in colonylist.row_boxes(
            area, cfg, scale, screen._rows[row_index]).cells:
        if (cell_job, cell_index) == (job, index):
            return rect.x + rect.width // 2, top + row_h // 2
    return None


def band_xy(screen, row_index, job):
    """The screen pixel of one drop target of one row.

    From `drop_targets`, which is the same function the outline is
    drawn with — so this tool aims where a player would, and cannot
    pass a run that a player could not reproduce.
    """
    area, cfg, scale, n_rows = screen._list_view()
    first = screen._first
    bands = colonylist.row_bands(area, cfg, scale, n_rows - first)
    band = row_index - first
    if not 0 <= band < len(bands):
        return None
    top, row_h = bands[band]
    for target_job, rect in colonylist.drop_targets(
            area, cfg, scale, screen._rows[row_index]):
        if target_job == job and rect.width:
            return rect.x + rect.width // 2, top + row_h // 2
    return None


#: The acceptance fixtures, by what a SNAPSHOT can see of them —
#: `v3_projektstatus.md`, "Acceptance fixtures — the two savegames".
#: Stardate alone is not enough: 3502.4 and 3502.5 are one tick apart
#: and any game reaches them.
FIXTURES = {
    "reference": {"stardate": 35024, "stars": 99, "colonies": 55},
    "natives": {"stardate": 35025, "stars": 71, "colonies": 36},
}


def identify(state, expect):
    """True when the game is on the fixture this run claims.

    **ADDED 7 September 2026, AFTER THIS TOOL PRODUCED THREE CLEAN
    ACCEPTANCE RUNS AGAINST THE WRONG GAME.** Every line of them was
    true — the clicks landed, the pop words matched their predictions,
    no other colony changed — and none of it was evidence about the
    reference save, because the game had a different one loaded and
    nothing in the run said so. The status document already required
    that "anything below that reads a save reads it by its fixture
    name"; this tool did not, and a report is only as good as the
    thing it was measured on.

    Reported, never guessed: an unknown state names what it saw.
    """
    if expect == "any":
        print("fixture check skipped (--expect any)")
        return True
    want = FIXTURES.get(expect)
    got = {"stardate": state.stardate,
           "stars": len(getattr(state, "stars", None) or []),
           "colonies": state.num_colonies}
    if want is None:
        print(f"unknown fixture {expect!r}; known: {sorted(FIXTURES)}")
        return False
    if got == want:
        print(f"fixture: {expect} ({got['stars']} stars, stardate "
              f"{got['stardate'] / 10:.1f}) — the run is about this save")
        return True
    named = [n for n, f in FIXTURES.items() if f == got]
    print(f"WRONG SAVE. This run claims {expect} {want}, the game has "
          f"{got}" + (f" — which is the {named[0]} fixture" if named
                      else " — which is no acceptance fixture at all"))
    print("  Load the right slot and re-run. A green table measured on "
          "the wrong game is worse than no table.")
    return False


def choose(screen, state, only_job=None):
    """(row_index, slot, job, target_job) for a move worth making.

    `only_job` restricts the SOURCE column, so the acceptance can
    prove one pick and one drop per column instead of whichever the
    save happened to offer first.

    Three conditions, and every one of them is about what the run can
    PROVE rather than about what would be convenient:

      the neighbours' pop composition must differ, so an off-by-one
      window would change a different colony and the diff would see
      it;

      the plan must COMPLETE, because a partial is refused before it
      is sent (`layout.json._partial_note`) and would prove nothing
      about the wire;

      the source square must be the LAST icon of its group, so the
      cluster is one pop and the run moves as little as possible.
    """
    rows = screen._rows

    def shape(row):
        return tuple(row["jobs"])

    for row_index, row in enumerate(rows):
        near = [rows[p] for p in (row_index - 1, row_index + 1)
                if 0 <= p < len(rows)]
        if not near or any(shape(o) == shape(row) for o in near):
            continue
        loaded = colonypick.pops_of(state, row["index"])
        if loaded is None:
            continue
        pops, n_pops, max_farms = loaded
        for job in range(3):
            if only_job is not None and job != only_job:
                continue
            icons = colonyicons.icon_pops(pops, n_pops, job)
            if not icons:
                continue
            slot = len(icons) - 1
            pick = colonypick.pick_at(pops, n_pops, job, slot,
                                      row["index"], row_index,
                                      screen._sort_key)
            if isinstance(pick, colonypick.Refusal):
                continue
            for target in range(3):
                if target == job:
                    continue
                plan = colonypick.plan_move(pick, pops, n_pops, max_farms,
                                            row["index"], target)
                if isinstance(plan, colonypick.Refusal):
                    continue
                return (row_index, slot, job, target,
                        pick, plan, max_farms)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", action="store_true",
                    help="click the second time as well")
    ap.add_argument("--cancel", action="store_true",
                    help="pick up, then right-click to discard")
    # OUTSIDE THE TREE by default, like `colony_list_preview`'s
    # `/tmp/colony_list_preview`. A diagnostic that writes a PNG into
    # the repository root is one `git add .` away from committing a
    # generated file (decision 40), and the two tools that once
    # defaulted to a relative path put their output wherever the
    # shell happened to be — both faults are in the fundament.
    ap.add_argument("--expect", default="reference",
                    help="which acceptance fixture the game must be "
                         "on: reference, natives, or 'any' to skip the "
                         "identification")
    ap.add_argument("--job", type=int, default=None,
                    help="restrict the SOURCE column (0 food, 1 "
                         "industry, 2 research), so one run proves one "
                         "column rather than whichever the save offers")
    ap.add_argument("--png", default=os.path.join(
        DEFAULT_OUT_DIR, "colony_move_hd.png"))
    args = ap.parse_args()

    from main import App
    app = App()
    if not app.connected:
        print("no game on the extension port")
        return 1
    counter = Counter(app.client)

    if not wait_for(app, lambda: (
            app.dispatcher.active is not None
            and getattr(app.dispatcher.active, "SCREEN_NAME", "")
            == "colony_summary"
            and app.dispatcher.active._rows), 15.0, "the colony summary"):
        state = app.client.state
        print(f"  the game is on screen {state.current_screen}, not "
              f"{SCREEN_COLONY_SUMMARY}. Put it there and re-run.")
        return 1
    screen = app.dispatcher.active
    state = app.client.state
    rows = screen._rows
    if not identify(state, args.expect):
        return 1
    print(f"colony summary is up: {len(rows)} rows, sorted by "
          f"{screen._sort_key!r}")
    print(f"sends so far (entry sort key): {counter}")

    target = choose(screen, state, args.job)
    if target is None:
        print("no row this save can prove a move on — a neighbour with "
              "the same pop composition, or no plan that completes. "
              "Stopping.")
        return 1
    (row_index, cell, job, target_job, pick, plan,
     max_farms) = target
    row = rows[row_index]
    print(f"target: row {row_index} {row['name']!r} jobs={row['jobs']}, "
          f"cell {cell} of column {job} -> column {target_job}")
    print(f"  pick predicts {pick}, drop predicts {plan}")

    before = list(state.colonies_raw)
    sends_before = counter.total()

    xy = square_xy(screen, row_index, job, cell)
    if xy is None:
        print("the row is not drawn at this resolution")
        return 1
    print(f"click 1 at screen {xy}")
    click_at(app, *xy)
    if screen._move.pick is None:
        print(f"  no selection was made ({screen._move.message!r})")
        return 1
    print(f"  held locally: {screen._move.pick}, slots "
          f"{screen._move.pick.slots()}")
    # THE OUTLINE IS READ BACK OFF THE FRAME, not off the geometry.
    # A pick that names the right pop while the mark sits on the
    # neighbouring cell is what shipped on 6 September, and every
    # value in this run was correct while it did.
    _area, _cfg, _scale, _n = screen._list_view()
    _cells = {(j, i): r for j, i, r in colonylist.row_boxes(
        _area, _cfg, _scale, row).cells}
    _want = sorted(_cells[(job, i)].x for i in screen._move.pick.slots()
                   if (job, i) in _cells)
    _arr = pygame.surfarray.array3d(app.surface)
    _rgb = list(colonylist.PICK_COLOR[:3])
    _got = sorted({x for x in range(app.surface.get_width())
                   if (_arr[x] == _rgb).all(axis=1).any()})
    _left = [x for x in _got if x - 1 not in _got]
    print(f"  outline inked at x {_left}, the cells are at {_want}")
    if _left != _want:
        print("  THE MARK IS NOT ON THE CELL IT NAMES")
        return 1
    print("  the outline sits on the cells the pick names")
    if counter.total() != sends_before:
        print(f"  THE FIRST CLICK SENT SOMETHING: {counter}")
        return 1
    print("  the first click sent nothing, which is the whole design")

    os.makedirs(os.path.dirname(args.png) or ".", exist_ok=True)
    pygame.image.save(app.surface, args.png)
    print(f"  rendered with the selection held -> {args.png}")
    # THE ORIGINAL HALF, from the same snapshot (see `native_png`).
    native = os.path.join(os.path.dirname(args.png), "native.png")
    if native_png(app.client.state, native):
        pair_path = os.path.join(os.path.dirname(args.png), "side_by_side.png")
        pygame.image.save(
            side_by_side(app.surface, native), pair_path)
        print(f"  the original at the same moment -> {native}")
        print(f"  side by side                    -> {pair_path}")
    else:
        print("  NO NATIVE HALF: the snapshot carried no framebuffer, so "
              "this is not a comparison")

    if args.cancel:
        click_at(app, xy[0], xy[1], button=3)
        held = screen._move.pick is None
        print(f"right click: selection discarded = {held}, {counter}")
        ok = held and counter.total() == sends_before
        print("  the cancel path sent nothing" if ok
              else "  THE CANCEL PATH SENT SOMETHING")
        return 0 if ok else 1

    if not args.commit:
        print("\ndry run — the drop was not clicked. Re-run with --commit.")
        return 0

    xy2 = band_xy(screen, row_index, target_job)
    print(f"click 2 at screen {xy2} (drop band {target_job})")
    click_at(app, *xy2)
    if screen._move.send is None and screen._move.pick is not None:
        print(f"  the drop was refused: {screen._move.message!r}")
        return 1
    if not wait_for(app, lambda: screen._move.send is None, 20.0,
                    "the move to finish"):
        return 1
    print(f"  finished: {screen._move.message!r}")
    print(f"  sends: {counter}")

    state = app.client.state
    # Predicted from the array the PICK was taken against, which is
    # the state the player saw and the plan was made in. Re-deriving
    # it from the snapshot that came back would be checking the move
    # against itself.
    predicted = colonymove.predict_pops(list(pick.pops), pick.n_pops,
                                        max_farms, pick.cluster,
                                        target_job)
    changed = [i for i, raw in enumerate(state.colonies_raw)
               if i < len(before) and raw != before[i]]
    # THE INDEX IS BOUND TO A NAME, because an index alone is not a
    # claim anybody can check: `[10]` says nothing about whether the
    # right colony moved, and the whole point of diffing every record
    # is that the wrong one is the failure being looked for.
    named = {r["index"]: r["name"] for r in rows}
    print("colonies whose bytes changed: "
          + (", ".join(f"{i} = {named.get(i, '(not the player\'s)')}"
                       for i in changed) or "none"))
    ok = changed == [row["index"]]
    if not ok:
        print(f"  EXPECTED EXACTLY [{row['index']}] — another colony "
              f"changing is the invisible failure this run is built "
              f"against")
    after = colony_struct.parse(state.colonies_raw[row["index"]])
    for i in range(pick.n_pops):
        if after.pop[i] != predicted[i]:
            print(f"  pop {i}: got 0x{after.pop[i]:x}, predicted "
                  f"0x{predicted[i]:x}")
            ok = False
    print("  every pop word matches the prediction" if ok else "  MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
