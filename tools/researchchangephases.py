#!/usr/bin/env python3
"""Change mode's own live phases: entering it, committing, leaving it.

Split out of `tools/research_change_hd.py` when that passed the
300-line guideline (decision 6), at the seam `tools/research_hd.py` and
`tools/researchphases.py` already use: the COMMANDS are there, what
knows about SCREEN_TECH_CHANGE is here, and the generic machinery — the
client, the loop, the evidence, the save rule — is `tools/livedrive.py`.

EVERY SEND GOES THROUGH `tools/livesend.py`, so it is refused unless the
list on the wire is the one the step was measured against (work order
129 A: a live driver is a client).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import livesend  # noqa: E402
from core import researchlist, researchnative  # noqa: E402
from screens.galaxy_map import mapboxes  # noqa: E402

#: SCREEN_TECH_CHANGE, the engine's own (orion2_consts.h; the reading's
#: §4). Unlike select mode's 53 there is nothing synthetic about it.
SCREEN_CHANGE = 36
SCREEN_MAP = 0

#: The scratch slots of the standing protocol (work order 126, rule 8).
#: `tools/gameload.py` refuses SAVE8 on its own; this is the positive
#: half, and a smoke check holds the two together.
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
