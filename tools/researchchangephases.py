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
        lambda st: (run.app.dispatcher.overlay_name == "research_change"
                    and run.app.dispatcher.active_name == "galaxy_map"
                    and hd(run).state == "ok" and offered(run)),
        seconds=90, label="change mode, drawn by HD over the map")


def offered(run):
    """The entries change mode is offering, off the HD screen itself."""
    return [e for e in getattr(hd(run), "_entries", []) if e.offered]


def panel_ready(run):
    """Wait until change mode is DRAWN by HD and its exit is on the wire.

    The first snapshot at 36 carries the one-field list `Clear_Fields_`
    leaves behind (mainscr_main.cpp:699), so a caller that acts on the
    screen id alone acts on a list that has nothing in it — which is
    how this driver once asked to leave before there was an exit button
    to activate.
    """
    return run.wait_for(
        lambda st: (run.app.dispatcher.overlay_name == "research_change"
                    and hd(run).exit_field() is not None),
        seconds=90, label="change mode's panel and its exit button")


def ensure_on_map(run):
    """Leave change mode if the game is sitting in it. Re-runnability.

    A driver that can only start from the map is a driver that has to
    be rescued by hand the first time a step aborts half way.
    """
    run.pump(20)
    if run.state.current_screen != SCREEN_CHANGE:
        return True
    print("    the game is on 36 already — leaving it first")
    panel_ready(run)
    return leave_change(run)


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


def map_behind(run):
    """Is the HD galaxy map visible behind the panel? A PIXEL answer.

    Two frames of the SAME app state, one with the overlay and one
    without. In the two side bands — native x 0..80 and 557..639, the
    strips the original leaves as map (`Draw_Mini_Main_Screen_`,
    mainscr_main.cpp:700-703) and this screen filled with a cockpit
    texture until work order 165 part F — the panel draws nothing, so
    the two frames must be IDENTICAL there. Inside the panel they must
    differ, or the equality is about a frame that drew no panel at all.

    Returns (behind, sampled, changed, panel_diff, map_only_surface).
    """
    import pygame
    disp = run.app.dispatcher
    screen = hd(run)

    def frame(with_overlay):
        kept = disp.overlay
        if not with_overlay:
            disp.overlay = None
        surf = pygame.Surface((run.app.win_w, run.app.win_h))
        surf.fill((0, 0, 0))
        disp.render(surf)
        disp.overlay = kept
        return surf

    with_panel, without = frame(True), frame(False)
    seen = changed = 0
    for band in ("left_band", "right_band"):
        bx, by, bw, bh = researchnative.window_rect(
            screen.geom.bands[band], screen.layout)
        for y in range(by, by + bh, 2):
            for x in range(bx, bx + bw, 2):
                seen += 1
                if with_panel.get_at((x, y))[:3] != \
                        without.get_at((x, y))[:3]:
                    changed += 1
    px, py, pw, ph = researchnative.window_rect(screen.geom.panel_rect,
                                                screen.layout)
    panel_diff = sum(
        1 for y in range(py, py + ph, 3) for x in range(px, px + pw, 3)
        if with_panel.get_at((x, y))[:3] != without.get_at((x, y))[:3])
    return (changed == 0 and panel_diff > 500, seen, changed,
            panel_diff, without)


def _send_counter(run):
    """`SendCounter` for this run's client.

    Imported here and not at module level: this module is loaded by a
    smoke check WITHOUT pygame, and `livedrive` pulls in pygame, the
    palette and `main.App`.
    """
    from livedrive import SendCounter
    return SendCounter(run.app.client)


def esc_leave(run):
    """Leave change mode by pressing ESC. What the wire saw.

    The counterpart of `exit_click`, measured the same way, because
    "ESC and a click on the button are the same act" is a claim about
    what goes out and a claim like that is a number or it is an
    argument. ESC resolves to the FIRST ESC field of the list
    (`Interpret_Keyboard_Input_`, fields.cpp:2608-2613), which in
    change mode is the exit button (tech.cpp:208-210).
    """
    import pygame
    screen = hd(run)
    field = screen.exit_field()
    with _send_counter(run) as counter:
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": "\x1b",
                             "mod": 0}))
        run.pump(4)
        left = run.wait_for(livesend.on_galaxy_map, seconds=90,
                            label="the galaxy map after ESC")
        run.pump(20)
    counts, sent = counter.snapshot()
    closed = (run.app.dispatcher.overlay is None
              and run.app.dispatcher.active_name == "galaxy_map")
    print(f"    ESC: sent {[list(x) for x in sent]} — the exit "
          f"field is {field.index if field else None}")
    return {"field": field.index if field else None, "left": left,
            "closed": closed, "sends": counts,
            "sent": [list(x) for x in sent]}


def one_activation_of(record):
    """True when this record is exactly one ACTIVATE_FIELD on its field."""
    return (record["sends"] == {"activate_field": 1, "inject_click": 0,
                                "inject_key": 0}
            and [(n, tuple(a)) for n, a in record["sent"]]
            == [("activate_field", (record["field"],))])


def exit_click(run):
    """Leave change mode by CLICKING the exit button. What the wire saw.

    The rectangle is the one the live list reports — the source has the
    origin only, because `Add_Button_Field_` takes the rest from the
    art (tech.cpp:208-210, fields.cpp:366-367) — and the click is a
    real pygame click in OrionLayer's own window, through the front
    door. Returns the record for it.
    """
    screen = hd(run)
    rect = screen.exit_rect()
    if rect is None:
        raise livesend.WrongDialog(
            "no exit button at its own origin in the list on the wire")
    field = screen.exit_field()
    x, y, w, h = researchnative.window_rect(rect, screen.layout)
    point = (x + w // 2, y + h // 2)
    on_it = screen.exit_at(*point)
    print(f"    the wire puts the exit button at {rect} (field "
          f"{field.index}); HD's own hit test says {on_it} at window "
          f"{point}")
    with _send_counter(run) as counter:
        run.hd_click(*point)
        left = run.wait_for(livesend.on_galaxy_map, seconds=90,
                            label="the galaxy map after the exit click")
        run.pump(20)
    counts, sent = counter.snapshot()
    closed = (run.app.dispatcher.overlay is None
              and run.app.dispatcher.active_name == "galaxy_map")
    return {"rect": list(rect), "field": field.index, "on_it": on_it,
            "window_point": list(point), "left": left, "closed": closed,
            "sends": counts, "sent": [list(x) for x in sent]}


def compare_list_popup(run, entry, items, screen):
    """Open the GAME's own category list and compare HD's page to it.

    The one validation this popup can have, and decision 25's own
    condition: HD reconstructs `Get_Group_List_` and `Init_List_Data_`
    from `s_player` and static tables, so the reconstruction has to be
    checkable against what the engine builds. It is — `_Tech_List_`
    replaces the field list with its own (`Save_Field_Stats_`,
    tech.cpp:889, serialized through the moved pointer,
    ext_api.cpp:245-259) and every row of the visible page is a hidden
    field at exactly the rectangle HD computes.

    HD ITSELF SENDS NOTHING for its popup; this sends the category
    button ONCE, on purpose, to make the engine build the list being
    compared against. The popup is display-only, so nothing changes.
    """
    from core import researchtechlist
    field = screen.radio_field(entry.index)
    if field is None:
        raise livesend.WrongDialog(
            f"no category button for entry {entry.index} in the live list")
    panel_shape = len(run.state.fields or [])
    livesend.activate(run.app.client, field.index, screen=SCREEN_CHANGE,
                      field_type=researchlist.TYPE_RADIO,
                      rect=(field.x, field.y, field.x_end, field.y_end),
                      label=f"open the category list of entry {entry.index}")
    opened = run.wait_for(lambda st: len(st.fields or []) != panel_shape,
                          seconds=60, label="the game's own list popup")
    run.pump(20)
    live = list(run.state.fields or [])
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
    return {"opened": opened, "live": live, "rows_game": got,
            "rows_hd": rows_hd, "match": match,
            "panel_shape": panel_shape}
