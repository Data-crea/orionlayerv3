#!/usr/bin/env python3
"""Drive the research dialogs live, and prove where the choice landed.

    python tools/research_hd.py run        # the whole acceptance
    python tools/research_hd.py where      # say what is on screen, send nothing

Work order 130's live acceptance, parts A, B and F. The real `main.App`,
headless, ONE client, real pygame events through the front door — the
shape `tools/game_menu_hd.py` and `tools/colony_move_hd.py` established.
Every send that is not an HD click goes through `tools/livesend.py`, so
it is refused unless the list on the wire is the one the step was
measured against (work order 129 A).

WHAT IT PROVES, and each is a different claim:

  A  On wire id 52, the science room, a click in OrionLayer's WINDOW
     moves the game on — without F12. Before work order 130 A the
     window was a flat (6, 8, 16) and the click went nowhere.
  B  An ACTIVATE_FIELD on a research row sets the player's research to
     THAT row's field, read back off the wire. Three different rows on
     three occasions. Plus the case that crashed in 128: an activation
     where nothing is selectable.
  F  Three turn-start selections made entirely inside OrionLayer's
     window by clicking an HD row, in three different categories.

THE SAVE-FILE RULE (work order 126, rule 8) runs around the whole run:
SAVE1-SAVE9 hashed before and after and identical; SAVE10 is the
autosave and is logged, never compared; SAVE11 logged the same way. No
action in any save dialog, and no QUIT -> YES.

Evidence goes OUTSIDE the tree, to
`~/orionlayer-fixtures/evidence/work_order_130/` — pictures of the
player's game are the player's data (decision 42).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import toolenv  # noqa: E402
toolenv.init_palette()

import livesend  # noqa: E402
from core import researchlist  # noqa: E402
from livedrive import (Run, SendCounter, close, fb_digest,  # noqa: E402
                       hashes)
from researchphases import (SCREEN_SCIENCE_ROOM, SCREEN_SELECT,  # noqa: E402
                            advance, choose, fallback_click, new_game,
                            offered_entries, read_field, row_pixel,
                            walk_room)

def cmd_where():
    """Say what is on screen and send nothing."""
    run = Run("where")
    run.pump(40)
    run.wait_for(lambda st: (st.fields or []), seconds=10, label="a field list")
    entry = run.capture("where")
    st = run.state
    print(f"\n  screen {st.current_screen} -> "
          f"{run.app.dispatcher.screen_name_for(st.current_screen)}")
    for f in (st.fields or [])[:24]:
        print(f"    {f.index:>3} t={f.field_type:<3} "
              f"({f.x},{f.y})-({f.x_end},{f.y_end}) hk={f.hotkey}")
    plr = run.player()
    if plr is not None:
        print(f"  research field={plr.current_research_field} "
              f"accumulated={plr.research_accumulated} "
              f"produced={plr.research_produced} "
              f"breakthrough={plr.research_breakthrough}")
    run.save_record()
    return entry


def cmd_step():
    """Walk the chain by hand: `step c:538,208 a:15 w:60`.

    An exploratory mode, for learning a screen chain that is not yet a
    named phase. Every send still goes through livesend, so it refuses
    on a list it cannot identify.
    """
    run = Run("step")
    run.pump(40)
    run.capture("start")
    for arg in sys.argv[2:]:
        kind, _, val = arg.partition(":")
        before = run.shape()
        if kind == "c":
            x, y = (int(v) for v in val.split(","))
            livesend.click(run.app.client, x, y,
                           screen=run.state.current_screen,
                           label=f"step {arg}")
        elif kind == "a":
            livesend.activate(run.app.client, int(val),
                              screen=run.state.current_screen,
                              label=f"step {arg}")
        elif kind == "k":
            livesend.key(run.app.client, int(val),
                         screen=run.state.current_screen,
                         label=f"step {arg}")
        elif kind == "w":
            run.pump(int(val))
            run.capture(f"wait{val}")
            continue
        run.wait_for(lambda st, b=before: (st.current_screen,
                                           len(st.fields or [])) != b,
                     seconds=30, label=f"a change after {arg}")
        run.pump(20)
        run.capture(arg.replace(":", "_").replace(",", "_"))
    st = run.state
    for f in (st.fields or [])[:24]:
        print(f"    {f.index:>3} t={f.field_type:<3} "
              f"({f.x},{f.y})-({f.x_end},{f.y_end}) hk={f.hotkey}")
    run.save_record()
    return True


def cmd_fbclick():
    """`fbclick <nx> <ny> <tag>` — one click through the fallback."""
    nx, ny = int(sys.argv[2]), int(sys.argv[3])
    tag = sys.argv[4] if len(sys.argv) > 4 else "fbclick"
    run = Run(tag)
    saves = hashes()
    run.pump(40)
    st = run.state
    if not run.app._showing_original():
        sys.exit(f"the window is NOT showing the game's picture "
                 f"(screen {st.current_screen}, hd="
                 f"{run.app.dispatcher.active_name}) — nothing sent")
    before_shape = run.shape()
    before, window_pt, back = fallback_click(run, nx, ny, tag)
    moved = run.wait_for(lambda s: (s.current_screen,
                                    len(s.fields or [])) != before_shape,
                         seconds=60, label="the game moving on")
    run.pump(25)
    after = run.capture(f"{tag}_after")
    print(f"    the game moved on: {moved} "
          f"({before['screen']}/{before['fields']} -> "
          f"{after['screen']}/{after['fields']})")
    run.save_record({"native_point": [nx, ny], "window_point": window_pt,
                     "mapped_back": back, "moved": moved,
                     "hd_colours_before": before["hd_distinct_colours"],
                     "showing_original": before["showing_original"],
                     **close(run, saves)})
    return True


def cmd_advance():
    run = Run("advance")
    saves = hashes()
    run.pump(40)
    screen = advance(run)
    run.capture("stopped")
    run.save_record({"stopped_on": screen, **close(run, saves)})
    return True


def cmd_room():
    """`room` — walk the science room out by clicking OrionLayer's window.

    PART A, on wire id 52. Every click is a real pygame click in the HD
    window with no F12; the point is converted by the product's own
    placement. The room advances one discovery per input and then
    leaves for the select list, so the test is "the picture moved", and
    the acceptance is that it eventually leaves 52 without a single
    click going anywhere but OrionLayer's window.
    """
    run = Run("A_step")
    saves = hashes()
    counter = SendCounter(run.app.client)
    run.pump(40)
    if run.state.current_screen != SCREEN_SCIENCE_ROOM:
        sys.exit(f"the game is on screen {run.state.current_screen}, "
                 f"not the science room ({SCREEN_SCIENCE_ROOM})")
    clicks = []
    for i in range(12):
        if run.state.current_screen != SCREEN_SCIENCE_ROOM:
            break
        if not run.app._showing_original():
            sys.exit("the window is not showing the game's picture on 52")
        before_digest = fb_digest(run)
        before_screen = run.state.current_screen
        _b, window_pt, back = fallback_click(run, 320, 240, f"A{i + 1}")
        run.wait_for(lambda s: fb_digest(run) != before_digest
                     or s.current_screen != before_screen,
                     seconds=45, label="the room to answer")
        run.pump(20)
        after = run.capture(f"A{i + 1}_after")
        clicks.append({"click": i + 1, "window_point": window_pt,
                       "mapped_back": back,
                       "picture_moved": fb_digest(run) != before_digest,
                       "screen_after": after["screen"],
                       "showing_original": after["showing_original"],
                       "hd_colours": after["hd_distinct_colours"]})
        print(f"    click {i + 1}: picture moved="
              f"{clicks[-1]['picture_moved']} screen={after['screen']}")
        if after["screen"] != SCREEN_SCIENCE_ROOM:
            break
    left = run.state.current_screen != SCREEN_SCIENCE_ROOM
    print(f"  left the science room by clicking OrionLayer's window: {left} "
          f"(now screen {run.state.current_screen}) after {len(clicks)} clicks")

    # AND THEN WATCH, SENDING NOTHING. Twice in this run the select list
    # that replaces the room had committed a research field by the time
    # the next process looked, with nothing sent into it. Either this
    # driver is sending something it does not know about, or an input
    # survives the hand-over from the room to the list. The counter
    # settles which: it wraps the client's three send paths and the
    # real method still runs, so a send cannot happen unseen.
    sends_at_handover = counter.total()
    print(f"  the driver sent {sends_at_handover} inputs in total to walk "
          f"the room out ({len(clicks)} clicks): {counter.sent}")
    watch = []
    for i in range(12):
        run.pump(25)
        watch.append({"frame_batch": i + 1,
                      "screen": run.state.current_screen,
                      "research_field": read_field(run),
                      "sends_total": counter.total()})
        if read_field(run):
            print(f"    field became {read_field(run)} with the driver's "
                  f"send count still at {counter.total()} "
                  f"(it was {sends_at_handover} when the room handed over) "
                  f"— screen {run.state.current_screen}")
            break
    run.capture("after_watch")
    print(f"  watch: {counter.total() - sends_at_handover} sends from the "
          f"driver after the hand-over, field ends at {read_field(run)}, "
          f"screen {run.state.current_screen}")
    run.save_record({"clicks": clicks, "left_the_room": left,
                     "ended_on": run.state.current_screen,
                     "watch": watch,
                     "driver_sends_total": counter.counts,
                     "driver_sends_at_handover": sends_at_handover,
                     "driver_sent": [list(x) for x in counter.sent],
                     **close(run, saves)})
    return True


def cmd_roomchoose():
    """`roomchoose <entry> [hd|activate] <tag>` — the room, then the choice.

    ONE PROCESS, because the select list does not wait: measured in this
    run, it commits a row by itself about a second and a half after the
    science room hands over, with nothing sent (see the report). Walking
    the room in one process and choosing in the next lost the occasion
    three times. This does both without letting go.
    """
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    how = sys.argv[3] if len(sys.argv) > 3 else "hd"
    tag = sys.argv[4] if len(sys.argv) > 4 else f"RC{want}"
    run = Run(tag)
    saves = hashes()
    run.pump(30)
    clicks = []
    if run.state.current_screen == SCREEN_SCIENCE_ROOM:
        clicks = walk_room(run, tag)
        print(f"    room walked out in {len(clicks)} clicks -> screen "
              f"{run.state.current_screen}")
    entry = choose(run, want, how, tag)
    run.save_record({"room_clicks": clicks, "occasion": entry,
                     **close(run, saves)})
    return True


def cmd_crash():
    """`crash` — the case that killed the engine in work order 128.

    An ACTIVATE_FIELD into the select list where NOTHING is selectable:
    the entry BLOCK of a category that offers nothing. Before open fix
    25 the commit branch took `Get_Selected_Entry_`, which returns
    nullptr when no entry is selected, and dereferenced it
    (tech.cpp:376) — SIGSEGV, open fix 23. The patch resolves a block
    field to that entry's last visible row, and an EMPTY category has
    none, so it must select nothing and the null guard must hold.

    The acceptance is: the engine is still alive afterwards, and the
    research field is unchanged.
    """
    run = Run("B_crash")
    saves = hashes()
    run.pump(30)
    if run.state.current_screen != SCREEN_SELECT:
        sys.exit(f"the game is on screen {run.state.current_screen}, not "
                 f"the select list")
    screen = run.app.dispatcher.screens["research_select"]
    if screen.state != "ok":
        sys.exit(f"the HD screen cannot vouch for the list "
                 f"({screen.state}) — this test needs its entries")
    empty = [e for e in screen._entries if not e.offered]
    if not empty:
        sys.exit("every category offers something in this list — the "
                 "empty-block case is not reachable here")
    from screens.research_select import native as rsnative
    entry = empty[0]
    block = rsnative.BOX_NATIVE[f"entry_{entry.index}"]
    field = livesend.field_at(run.state, block[0] + 4, block[1] + 4)
    before = run.capture("crash_before")
    field_before = read_field(run)
    print(f"    empty category {entry.group} (panel entry {entry.index}), "
          f"its block field is {field.index if field else None}")
    if field is None:
        sys.exit("no field under the empty entry's block — nothing sent")
    livesend.activate(run.app.client, field.index, screen=SCREEN_SELECT,
                      field_type=7, label="activate an empty entry block")
    run.pump(60)
    alive = run.app.client.state is not None and run.app.connected
    after = run.capture("crash_after")
    same = read_field(run) == field_before
    print(f"    engine alive after the activation: {alive}; "
          f"research field {field_before} -> {read_field(run)} "
          f"({'unchanged' if same else 'CHANGED'}); "
          f"screen {before['screen']} -> {after['screen']}")
    run.save_record({"empty_entry": entry.index, "group": entry.group,
                     "block_field": field.index, "alive": alive,
                     "field_before": field_before,
                     "field_after": read_field(run), "unchanged": same,
                     **close(run, saves)})
    return True


def cmd_newgame():
    run = Run("newgame")
    before = hashes()
    order = new_game(run)
    run.pump(60)
    run.capture("settled")
    st = run.state
    for f in (st.fields or [])[:24]:
        print(f"    {f.index:>3} t={f.field_type:<3} "
              f"({f.x},{f.y})-({f.x_end},{f.y_end}) hk={f.hotkey}")
    run.save_record({"order": order, **close(run, before)})
    return True


def cmd_choose():
    """`choose <entry> <hd|activate> <tag>` — one occasion, live."""
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    how = sys.argv[3] if len(sys.argv) > 3 else "hd"
    tag = sys.argv[4] if len(sys.argv) > 4 else f"{how}_{want}"
    run = Run(tag)
    before = hashes()
    run.pump(40)
    entry = choose(run, want, how, tag)
    run.save_record({"occasion": entry, **close(run, before)})
    return True


def cmd_turns():
    """`turns <n>` — end n turns, stopping at any turn-start dialog."""
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    run = Run("turns")
    before = hashes()
    run.pump(40)
    for i in range(n):
        if not livesend.on_galaxy_map(run.state):
            print(f"  not on the map (screen "
                  f"{run.state.current_screen}) — stopping")
            break
        screen = end_turn(run, label=f"turn {i + 1}")
        run.capture(f"turn{i + 1}")
        if screen in (SCREEN_SCIENCE_ROOM, SCREEN_SELECT):
            print(f"  turn-start dialog: screen {screen} — stopping")
            break
    run.save_record(close(run, before))
    return True


COMMANDS = {"where": cmd_where, "step": cmd_step,
            "newgame": cmd_newgame, "choose": cmd_choose,
            "turns": cmd_turns,
            "fbclick": cmd_fbclick,
            "advance": cmd_advance,
            "room": cmd_room,
            "roomchoose": cmd_roomchoose,
            "crash": cmd_crash}


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "where"
    if what not in COMMANDS:
        sys.exit(f"unknown command {what!r}; known: {sorted(COMMANDS)}")
    return COMMANDS[what]() and 0


if __name__ == "__main__":
    sys.exit(main() or 0)
