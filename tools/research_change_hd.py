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
from core import researchlist, researchnative  # noqa: E402
from core import researchtechlist  # noqa: E402
from livedrive import Run, SendCounter, close, hashes  # noqa: E402
from screens.galaxy_map import mapboxes  # noqa: E402

#: SCREEN_TECH_CHANGE, the engine's own (orion2_consts.h; the reading's
#: §4). Unlike select mode's 53 there is nothing synthetic about it.
SCREEN_CHANGE = 36
SCREEN_MAP = 0

#: The scratch slots of the standing protocol (work order 126, rule 8).
#: `gameload` refuses SAVE8 on its own; this is the positive half.
SCRATCH = (4, 5)


def hd(run):
    return run.app.dispatcher.screens["research_change"]


def pair(run):
    """`(current_research_field, current_research_application)`, now.

    Both off `s_player`, both promoted to their second source by work
    order 165 part A — and @902 is `u8`, because application ids run
    past 127 and the header's `int8_t` made 196 read as -60.
    """
    plr = run.player()
    if plr is None:
        return (None, None)
    return (int(plr.current_research_field),
            int(plr.current_research_application))


def enter_change(run):
    """The galaxy map's research window, to screen 36 drawn by HD.

    The field is found in the LIVE list by type and rect through the
    PRODUCT's own spec (`screens/galaxy_map/layout.json`
    `research_window_field`), never by a remembered index: the
    turn-start research prompt also reports screen 0 and its fields are
    choice rows (decision 20).
    """
    spec = run.app.dispatcher.screens["galaxy_map"]._data.get(
        "research_window_field")
    field = mapboxes.live_field(getattr(run.state, "fields", None), spec)
    if field is None:
        raise livesend.WrongDialog(
            "no research window in the list on the wire — this is not the "
            "galaxy map's own list, whatever the game reports")
    livesend.activate(run.app.client, field.index, screen=SCREEN_MAP,
                      shape=livesend.on_galaxy_map,
                      field_type=spec["field_type"], rect=spec["rect"],
                      label="research window")
    if not run.wait_for(lambda st: st.current_screen == SCREEN_CHANGE,
                        seconds=90, label="screen 36"):
        return False
    return run.wait_for(
        lambda st: (run.app.dispatcher.active_name == "research_change"
                    and hd(run).state == "ok" and offered(run)),
        seconds=90, label="change mode, drawn by HD")


def offered(run):
    """The entries change mode is offering, off the HD screen itself."""
    return [e for e in getattr(hd(run), "_entries", []) if e.offered]


def leave_change(run):
    """The exit button: the one branch of the loop that does not commit.

    `input == accept_btn_id`, tech.cpp:347-353. Found in the live list
    by the screen's own `exit_field`, which keys on the origin and on
    being the list's one BUTTON field — the rect is art-derived and
    `doc/tech_change_reading.md` §2 has its end as read off the wire.
    """
    field = hd(run).exit_field()
    if field is None:
        raise livesend.WrongDialog(
            "no exit button in the list on the wire — nothing sent")
    livesend.activate(run.app.client, field.index, screen=SCREEN_CHANGE,
                      field_type=researchlist.TYPE_BUTTON,
                      rect=(field.x, field.y, field.x_end, field.y_end),
                      label="exit")
    return run.wait_for(livesend.on_galaxy_map, seconds=90,
                        label="the galaxy map after the exit")


def row_window_point(run, entry, row):
    """The WINDOW pixel at the centre of one HD row.

    `core.researchnative.window_rect` is the product's own placement —
    a tool that computed the mapping itself would prove the mapping
    against a copy of itself (decision 5).
    """
    x, y, w, h = researchnative.window_rect(entry.row_rect(row),
                                            hd(run).layout)
    return (x + w // 2, y + h // 2)


def commit(run, entry, row, how, tag):
    """One change, and what the wire says afterwards.

    `how` is "hd" — a real click in OrionLayer's window, the whole
    gesture inside it — or "activate", a bare ACTIVATE_FIELD on the
    row's field resolved out of the live list, which is open fix 25's
    own path and the one this order is here to measure.
    """
    before = pair(run)
    screen = hd(run)
    shot = run.capture(f"{tag}_panel")
    app_id = entry.apps[row]
    if how == "hd":
        px, py = row_window_point(run, entry, row)
        # THE PRODUCT'S OWN HIT TEST, asserted before the click: if
        # `row_at` does not resolve this pixel to this row, the click
        # would commit a different row and the run would report the
        # wrong claim as proved.
        hit = screen.row_at(px, py)
        if hit != (entry.index, row):
            raise livesend.WrongDialog(
                f"{tag}: the window point {px},{py} resolves to {hit}, "
                f"not to entry {entry.index} row {row} — nothing sent")
        print(f"    HD click at {px},{py} — entry {entry.index} "
              f"(category {entry.group}), field {entry.field}, app {app_id}")
        run.hd_click(px, py)
    else:
        live = researchlist.row_field(run.state.fields, entry, row)
        if live is None:
            raise livesend.WrongDialog(
                f"{tag}: row {entry.index}.{row} is not in the live list")
        print(f"    ACTIVATE_FIELD {live.index} — entry {entry.index} "
              f"(category {entry.group}), field {entry.field}, app {app_id}")
        livesend.activate(run.app.client, live.index, screen=SCREEN_CHANGE,
                          field_type=researchlist.TYPE_HIDDEN,
                          rect=(live.x, live.y, live.x_end, live.y_end),
                          label=f"{tag} row")
    left = run.wait_for(lambda st: st.current_screen != SCREEN_CHANGE,
                        seconds=120, label="the game leaving 36")
    run.wait_for(livesend.on_galaxy_map, seconds=120,
                 label="the galaxy map after the commit")
    after = run.capture(f"{tag}_after")
    got = pair(run)
    want = (entry.field, app_id)
    match = got == want
    print(f"    -> the wire says field {got[0]} application {got[1]}; the "
          f"row is field {want[0]} application {want[1]}: "
          f"{'MATCH' if match else 'MISMATCH'} (was {before})")
    return {"tag": tag, "how": how, "entry": entry.index,
            "category": entry.group, "row": row,
            "row_field": entry.field, "row_application": app_id,
            "before": list(before), "after": list(got),
            "match": match, "left_36": left,
            "panel_png": shot["hd_png"], "after_png": after["hd_png"]}


def plan_changes(entries, current_field, want=3):
    """`want` offered entries in DIFFERENT categories, not the current one.

    Three rules, and each of them is a way the acceptance could pass
    while proving nothing:

      * the CURRENT field is offered in change mode — the game zeroes
        `current_research_field` around the call (tech.cpp:201, :204) —
        and committing it would read back as a match without anything
        having changed;
      * a placeholder row is billtext message 62, app id 0, a row that
        exists and cannot be chosen (`researchlist.Entry.placeholder`);
      * two entries of the same CATEGORY would be two changes, not two
        categories, and the order asks for three categories.

    Fewer than `want` is returned rather than a repeat: a short plan is
    a result the caller reports, a repeated category is one it would
    not notice.
    """
    chosen, seen = [], set()
    for entry in entries:
        if not entry.offered or entry.placeholder:
            continue
        if entry.group in seen or entry.field == current_field:
            continue
        seen.add(entry.group)
        chosen.append(entry)
        if len(chosen) == want:
            break
    return chosen


def describe(run, label):
    print(f"  {label}: change mode offers "
          + ", ".join(f"entry {e.index}/cat {e.group}: field {e.field} "
                      f"apps {list(e.apps)}" for e in offered(run)))


def cmd_probe(run, slot):
    record = gameload.load_slot(run, slot)
    if not record["loaded"]:
        return False, {"load": record}
    if not enter_change(run):
        return False, {"load": record}
    describe(run, f"SAVE{slot}")
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


def main():
    args = sys.argv[1:]
    what = args[0] if args else "run"
    slot = (int(args[1]) if what in ("probe", "listprobe")
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
    elif what == "listprobe":
        ok, extra = cmd_listprobe(
            run, slot or SCRATCH[0],
            int(args[2]) if len(args) > 2 and args[2].isdigit()
            else 0)
    else:
        sys.exit(f"unknown command {what!r}; known: probe, run, listprobe")
    run.save_record({**extra, "sends": counter.counts,
                     "sent": [list(x) for x in counter.sent],
                     **close(run, saves)})
    print(f"{what}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
