#!/usr/bin/env python3
"""Change the current research live, and read the result off the wire.

    python tools/research_change_hd.py probe 4   # load SAVE4, look, leave unchanged
    python tools/research_change_hd.py run       # part D's last item, three changes

WHAT THIS PROVES, and it is one claim: **open fix 25's commit path
covers CHANGE mode.** `doc/ext_tech_activate.patch` was measured in
select mode (work order 130 B) and covers both by source reading —
`_Tech_Select_(changing_tech)` is one function — and a source reading is
not a measurement. Without the patch a commit reads the game's POINTER
(`Get_Selected_Entry_`, tech.cpp:356) and an activation either commits
whatever the pointer happens to be over or dereferences null
(`doc/tech_change_reading.md` §2, consequence 1 — the SIGSEGV of open
fix 23, seen live in work order 128 C).

So each change is read back off the wire as a PAIR: `s_player`
`current_research_field` @901 and `current_research_application` @902.
The field alone would not settle it — a category offers one field and
several applications, and the pointer explanation dies on the
application, not on the field.

THE SAVES. Every change starts from a FRESHLY LOADED scratch slot
(`tools/gameload.py`), because "three changes" measured by making them
one after another on one loaded game is three changes of which only the
first started from a state anybody can reproduce. SAVE4, SAVE4, SAVE5;
never SAVE8; nothing is ever saved, so SAVE1-9 are identical at the end
and the run says so.

THE CONTROL, and it is the same one work order 130 used: the game's
physical pointer is never moved by this run. Three different rows
committed correctly on three occasions cannot all be a pointer standing
still — and one of the three goes out as a bare ACTIVATE_FIELD with no
click anywhere, which is the patch's own path.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gameload  # noqa: E402
import livesend  # noqa: E402
from core import researchlist, researchpanel  # noqa: E402
from core import researchtechlist  # noqa: E402
from livedrive import Run, SendCounter, close, hashes  # noqa: E402
from researchchangephases import (SCRATCH, SCREEN_CHANGE,  # noqa: E402
                                  commit, describe, enter_change, hd,
                                  leave_change, offered, pair,
                                  plan_changes)


def cmd_probe(run, slot):
    record = gameload.load_slot(run, slot)
    if not record["loaded"]:
        return False, {"load": record}
    if not enter_change(run):
        return False, {"load": record}
    describe(run, f"SAVE{slot}")
    screen = hd(run)
    print(f"  current field {pair(run)[0]}, TRAIT_CREATIVE "
          f"{screen._creative}, every row of it marked: "
          f"{researchpanel.marks_every_row(pair(run)[0], screen._creative)}")
    # THE SIX "EVERYONE GETS EVERYTHING" FIELDS, as this save has them.
    # Work order 131 part C wants the case seen live, and whether it is
    # reachable at all in a scratch save is a fact, not a guess: status
    # 3 is researched (core.research.STATUS_RESEARCHED).
    tech_fields = screen._tech[0]
    print("  the six starting fields: "
          + ", ".join(f"{f}:{tech_fields[f]}"
                      for f in researchlist.ALL_APPLICATIONS_FIELDS))
    before = pair(run)
    run.capture(f"probe_slot_{slot}")
    ok = leave_change(run)
    after = pair(run)
    print(f"  the exit changed nothing: {before} -> {after}: "
          f"{before == after}")
    return bool(ok and before == after), {
        "load": record, "before": list(before), "after": list(after),
        "offered": [[e.index, e.group, e.field, list(e.apps)]
                    for e in offered(run)]}


def cmd_run(run):
    """Part D's last item: three changes, three categories, all read back.

    One of the three goes out as a bare ACTIVATE_FIELD; the other two
    are clicks in OrionLayer's own window. The middle one is the bare
    activation deliberately — first would leave the two HD changes to
    explain a patched engine, last would leave it to explain a warm one.
    """
    plan, changes = None, []
    for i, (slot, how) in enumerate(((SCRATCH[0], "hd"),
                                     (SCRATCH[0], "activate"),
                                     (SCRATCH[1], "hd")), start=1):
        print(f"\n  change {i}: SAVE{slot}, by {how}")
        load = gameload.load_slot(run, slot)
        if not load["loaded"]:
            print("    the load did not land — stopping before anything "
                  "is sent into the research screen")
            return False, {"changes": changes, "load": load}
        if not enter_change(run):
            print("    change mode did not come up drawn by HD")
            return False, {"changes": changes, "load": load}
        describe(run, f"SAVE{slot}")
        here = plan_changes(offered(run), pair(run)[0])
        if plan is None:
            plan = [e.group for e in here]
        # THE CATEGORY IS THE UNIT, not the entry index: a different
        # save can offer a different field in the same category, and
        # "three different categories" is what the order asks for.
        want = plan[i - 1] if i - 1 < len(plan) else None
        entry = next((e for e in offered(run) if e.group == want
                      and not e.placeholder), None)
        if entry is None:
            print(f"    category {want} offers nothing on SAVE{slot} — "
                  f"taking the next free category instead")
            used = {c["category"] for c in changes}
            entry = next((e for e in here if e.group not in used), None)
        if entry is None:
            print("    no unused category is offered here — stopping")
            return False, {"changes": changes}
        changes.append(commit(run, entry, 0, how, f"change{i}_{how}"))
    cats = {c["category"] for c in changes}
    every = all(c["match"] for c in changes)
    bare = [c for c in changes if c["how"] == "activate"]
    print(f"\n  three changes in {len(cats)} categories {sorted(cats)}, "
          f"every one read back off the wire: {every}; "
          f"{len(bare)} of them by bare ACTIVATE_FIELD")
    return bool(every and len(cats) == 3 and bare), {
        "changes": changes, "categories": sorted(cats),
        "all_match": every, "bare_activations": len(bare)}


def cmd_listprobe(run, slot, want_entry=0):
    """Open the GAME's own category list and compare HD's to it.

    The one validation the list popup can have, and it is decision 25's
    own condition: HD reconstructs `Get_Group_List_` and `Init_List_Data_`
    from `s_player` and static tables, so the reconstruction has to be
    checkable against what the engine builds. It is — `_Tech_List_`
    replaces the field list with its own (`Save_Field_Stats_`,
    tech.cpp:889, serialized through the moved pointer,
    ext_api.cpp:245-259), and every row of the visible page is a hidden
    field at exactly the rectangle HD computes.

    HD ITSELF SENDS NOTHING FOR ITS POPUP — this driver does, once, on
    purpose, to get the engine to build the list it is being compared
    against. The popup is display-only, so nothing changes: the pair is
    read before and after.
    """
    record = gameload.load_slot(run, slot)
    if not record["loaded"] or not enter_change(run):
        return False, {"load": record}
    before = pair(run)
    screen = hd(run)
    entry = next((e for e in offered(run) if e.index == want_entry),
                 offered(run)[0])
    items = screen.group_items(entry)
    pages = researchtechlist.paginate(items)
    field = screen.radio_field(entry.index)
    if field is None:
        raise livesend.WrongDialog(
            f"no category button for entry {entry.index} in the live list")
    print(f"    HD reconstructs category {entry.group}: "
          f"{len(items)} fields over {len(pages)} pages — "
          + ", ".join(f"{i.field}:{len(i.apps)}" for i in items))
    panel_shape = len(run.state.fields or [])
    livesend.activate(run.app.client, field.index, screen=SCREEN_CHANGE,
                      field_type=researchlist.TYPE_RADIO,
                      rect=(field.x, field.y, field.x_end, field.y_end),
                      label=f"open the category list of entry {entry.index}")
    opened = run.wait_for(lambda st: len(st.fields or []) != panel_shape,
                          seconds=60, label="the game's own list popup")
    run.pump(20)
    live = list(run.state.fields or [])
    run.capture("list_popup")
    # The popup's own shape: two type-0 page buttons, one type-7 field
    # per visible row, then the two whole-screen fields (tech.cpp:936-969).
    rows_live = [f for f in live
                 if f.field_type == researchlist.TYPE_HIDDEN
                 and (f.x, f.y, f.x_end, f.y_end) != (0, 0, 639, 479)]
    popup = researchtechlist.TechListPopup()
    popup.open(entry, items)
    lx = popup.list_x(screen.geom.origin)
    rows_hd = [item.row_rect(row, lx)
               for item in popup.items()
               for row in range(len(item.apps))]
    got = [(f.x, f.y, f.x_end, f.y_end) for f in rows_live]
    match = got == rows_hd
    print(f"    the game's list has {len(live)} fields, {len(got)} rows; "
          f"HD's first page has {len(rows_hd)}: "
          f"{'MATCH' if match else 'MISMATCH'}")
    if not match:
        for i, (a, b) in enumerate(zip(got, rows_hd)):
            if a != b:
                print(f"      row {i}: game {a}, HD {b}")
                break
        print(f"      game {got[:3]} … HD {rows_hd[:3]} …")
    # CLOSE IT: a positive input on the whole-screen ESC field returns
    # from `_Tech_List_` (tech.cpp:1015-1028).
    close = next((f for f in live
                  if (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)
                  and f.hotkey == 0x1B), None)
    if close is None:
        raise livesend.WrongDialog("no ESC field in the popup's list")
    livesend.activate(run.app.client, close.index, screen=SCREEN_CHANGE,
                      field_type=researchlist.TYPE_HIDDEN,
                      rect=(0, 0, 639, 479), label="close the list")
    back = run.wait_for(lambda st: len(st.fields or []) == panel_shape,
                        seconds=60, label="the panel's list again")
    left = leave_change(run)
    after = pair(run)
    print(f"    the popup changed nothing: {before} -> {after}: "
          f"{before == after}")
    return bool(opened and match and back and left and before == after), {
        "load": record, "category": entry.group, "entry": entry.index,
        "items": [[i.field, list(i.apps), list(i.statuses), i.status]
                  for i in items],
        "pages": len(pages), "rows_hd": rows_hd, "rows_game": got,
        "match": match, "before": list(before), "after": list(after)}


def cmd_resolutions(run, slot):
    """Change mode beside the native frame, at every resolution.

    Part D's fifth item. The window is cycled with the product's OWN
    F9 (`main.App._cycle_resolution`), not by constructing four apps:
    the placement a capture has to line up with is the one the running
    app computes, and a second app would be a second computation of it.

    `Run.capture` writes the HD window and the game's framebuffer from
    ONE frame and records the window's distinct colour count beside
    each — the measurement work order 129 did not make.
    """
    import pygame as _pg
    record = gameload.load_slot(run, slot)
    if not record["loaded"] or not enter_change(run):
        return False, {"load": record}
    before = pair(run)
    shots, seen = [], set()
    for _ in range(len(run.app._resolutions)):
        size = (run.app.win_w, run.app.win_h)
        if size in seen:
            break
        seen.add(size)
        run.pump(12)
        shot = run.capture(f"change_{size[0]}x{size[1]}")
        shots.append({"size": list(size), "hd_png": shot["hd_png"],
                      "native_png": shot["native_png"],
                      "hd_active": shot["hd_active"],
                      "showing_original": shot["showing_original"],
                      "colours": shot["hd_distinct_colours"]})
        _pg.event.post(_pg.event.Event(_pg.KEYDOWN,
                                       {"key": _pg.K_F9, "unicode": "",
                                        "mod": 0}))
        run.pump(10)
    ok = leave_change(run)
    after = pair(run)
    drawn = [s for s in shots if s["hd_active"] == "research_change"
             and not s["showing_original"]]
    print(f"    {len(shots)} resolutions, {len(drawn)} of them drawn by "
          f"HD: " + ", ".join(f"{s['size'][0]}x{s['size'][1]}"
                              f"({s['colours']})" for s in shots))
    print(f"    the run changed nothing: {before} -> {after}: "
          f"{before == after}")
    return bool(ok and len(drawn) == len(shots) and len(shots) >= 4
                and before == after), {
        "load": record, "shots": shots, "before": list(before),
        "after": list(after)}


def main():
    args = sys.argv[1:]
    what = args[0] if args else "run"
    slot = (int(args[1]) if what in ("probe", "listprobe", "resolutions")
            and len(args) > 1 and args[1].isdigit() else None)
    folder = args[-1] if len(args) > 1 and not args[-1].isdigit() \
        else "work_order_165"
    run = Run(f"D_{what}" + (f"_{slot}" if slot else ""), folder=folder)
    saves = hashes()
    counter = SendCounter(run.app.client)
    run.pump(40)
    if what == "probe":
        ok, extra = cmd_probe(run, slot)
    elif what == "run":
        ok, extra = cmd_run(run)
    elif what == "resolutions":
        ok, extra = cmd_resolutions(run, slot or SCRATCH[0])
    elif what == "listprobe":
        ok, extra = cmd_listprobe(
            run, slot or SCRATCH[0],
            int(args[2]) if len(args) > 2 and args[2].isdigit()
            else 0)
    else:
        sys.exit(f"unknown command {what!r}; known: probe, run, listprobe, resolutions")
    run.save_record({**extra, "sends": counter.counts,
                     "sent": [list(x) for x in counter.sent],
                     **close(run, saves)})
    print(f"{what}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
