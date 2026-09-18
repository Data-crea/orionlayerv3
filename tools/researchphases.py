#!/usr/bin/env python3
"""The research dialogs' own live phases: the chain, the room, the choice.

Split out of `tools/research_hd.py` when it passed the 300-line
guideline (decision 6). The generic machinery — the client, the loop,
the evidence, the send counter, the save rule — is `tools/livedrive.py`;
what is here knows about SELECT NEW RESEARCH and nothing else.

EVERY SEND GOES THROUGH `tools/livesend.py`, so it is refused unless the
list on the wire is the one the step was measured against (work order
129 A: a live driver is a client).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import livesend  # noqa: E402
from core import researchlist  # noqa: E402
from livedrive import fb_digest  # noqa: E402

#: wire ids from open fix 24.
SCREEN_SCIENCE_ROOM = 52
SCREEN_SELECT = 53

#: The science room's own list: the dummy, one whole-screen hidden
#: field and an ESC hotkey at (5000, 5000) (science.cpp:169-171). Three
#: fields, and that IS the shape — doc/newtech_reading.md.
SCIENCE_ROOM_FIELDS = 3

#: The race to play, as `Race_Selection_Screen_` numbers them: the
#: fourteen radios are `field_ids[i] = first + i` at
#: `((i/7)*126 + 351, (i%7)*48 + 90)` (racesel.cpp:203-208), and the
#: handler COMPARES THE ID (:249), so ACTIVATE_FIELD reaches them —
#: which an injected click does not reliably, because a radio is
#: resolved through the pointer (open fix 4, still open).
RACE_PSILONS = 9        # right column, third row — the research race

#: The colony build prompt's RETURN, in the original's own pixels
#: (bottom right of SCREEN_COLONY). Used only to get past the
#: turn-start prompt on the way to a research dialog.
COLONY_RETURN = (610, 470)

def offered_entries(run):
    """The HD screen's own reconstructed entries, or []."""
    screen = run.app.dispatcher.screens.get("research_select")
    if screen is None:
        return []
    return [e for e in getattr(screen, "_entries", []) if e.offered]


def row_pixel(run, entry, row):
    """The WINDOW pixel at the visible centre of one HD row."""
    from screens.research_select import native as rsnative
    screen = run.app.dispatcher.screens["research_select"]
    x, y, w, h = rsnative.window_rect(entry.row_rect(row), screen.layout)
    return (x + w // 2, y + h // 2)


def read_field(run):
    """`current_research_field` off the wire, now."""
    plr = run.player()
    return int(plr.current_research_field) if plr else None


def fallback_click(run, native_x, native_y, tag):
    """Click a NATIVE point through OrionLayer's own window.

    The point is converted with the product's OWN placement
    (`OriginalView.placement`), never with arithmetic of this tool's
    — decision 5 covers tools, and a driver that computes the mapping
    itself proves the mapping against a copy of itself.

    This is part A's claim in one function: with no HD screen for the
    id, the window shows the game's picture and a click in it reaches
    the game. Before work order 130 A the window was a flat colour and
    the click went nowhere.
    """
    view = run.app.original_view
    dst_x, dst_y, _w, _h, scale = view.placement(run.app.win_w,
                                                 run.app.win_h)
    px = int(dst_x + (native_x + 0.5) * scale)
    py = int(dst_y + (native_y + 0.5) * scale)
    back = view.screen_to_640(px, py, run.app.win_w, run.app.win_h)
    print(f"    window ({px}, {py}) -> native {back} "
          f"(wanted {native_x}, {native_y})")
    before = run.capture(f"{tag}_before")
    run.hd_click(px, py)
    return before, (px, py), back


def end_turn(run, label="turn"):
    """Press TURN and wait for whatever the game does next.

    Either a turn-start dialog (52 or 53) or the map again at a new
    stardate. The wait is on the SHAPE, and the TURN field is found by
    its own hotkey 'T' (84) in the list read now, never by an index.
    """
    st = run.state
    before_date = getattr(st, "stardate", 0)
    turn = next((f for f in (st.fields or [])
                 if f.hotkey == 84 and 0 < f.x < 5000), None)
    if turn is None:
        raise livesend.WrongDialog(
            f"{label}: no TURN field in this list — nothing sent")
    livesend.activate(run.app.client, turn.index, screen=0,
                      shape=livesend.on_galaxy_map, label=label)
    run.wait_for(lambda s: s.current_screen in (SCREEN_SCIENCE_ROOM,
                                                SCREEN_SELECT)
                 or getattr(s, "stardate", 0) > before_date,
                 seconds=120, label="the next turn or a dialog")
    run.pump(20)
    return run.state.current_screen


def walk_room(run, tag, limit=12):
    """Click the science room out through OrionLayer's window."""
    clicks = []
    for i in range(limit):
        if run.state.current_screen != SCREEN_SCIENCE_ROOM:
            break
        digest = fb_digest(run)
        before_screen = run.state.current_screen
        _b, window_pt, back = fallback_click(run, 320, 240, f"{tag}_room{i + 1}")
        run.wait_for(lambda s, d=digest, sc=before_screen:
                     fb_digest(run) != d or s.current_screen != sc,
                     seconds=45, label="the room to answer")
        run.pump(12)
        clicks.append({"click": i + 1, "window_point": window_pt,
                       "mapped_back": back,
                       "screen_after": run.state.current_screen})
        if run.state.current_screen != SCREEN_SCIENCE_ROOM:
            break
    return clicks


def choose(run, want_entry, how, tag):
    """One research choice, and what the wire says afterwards.

    `how` is "hd" — a real click on the HD row, the whole gesture
    inside OrionLayer's window (part F) — or "activate", a bare
    ACTIVATE_FIELD on the row's field resolved by shape (part B).

    Returns the record entry, including the field the game ended up
    with. The CLAIM is that it equals the row's own field, and the
    control is that the game's pointer never moves in this run: three
    different rows chosen on three occasions cannot all match a pointer
    that stands still.
    """
    # ACT FIRST, WRITE THE PICTURES AFTERWARDS. Measured in this run:
    # the select list commits a row BY ITSELF about a second and a half
    # after the science room hands over, with nothing sent (the report
    # has the send-counted measurement). Saving two 1920x1080 PNGs
    # before the click lost the occasion — the wire had a field by the
    # time the click went out. The frame is COPIED here, in memory, and
    # written after the choice, so the evidence is still of the moment
    # before it.
    screen_obj = run.app.dispatcher.screens["research_select"]
    run.wait_for(lambda st: (st.current_screen == SCREEN_SELECT
                             and run.app.dispatcher.active_name
                             == "research_select"
                             and screen_obj.state == "ok"
                             and offered_entries(run)),
                 seconds=120, label="the select list, drawn by HD")
    held = (run.app.surface.copy(),
            bytes(run.state.framebuffer[:640 * 480])
            if run.state.framebuffer else None,
            list(run.state.palette or []))
    screen = screen_obj
    entries = offered_entries(run)
    if not entries:
        raise livesend.WrongDialog(
            f"{tag}: the HD screen offers no rows (state={screen.state}, "
            f"{screen.problems[:2]}) — nothing sent")
    entry = next((e for e in entries if e.index == want_entry), entries[0])
    row = 0
    field_before = read_field(run)
    if field_before not in (0, None):
        raise livesend.WrongDialog(
            f"{tag}: the wire already reports research field "
            f"{field_before} while the select list is up — "
            f"`Tech_Select_` zeroes it (tech.cpp:104-105), so something "
            f"has committed already and this occasion would prove "
            f"nothing")

    if how == "hd":
        px, py = row_pixel(run, entry, row)
        print(f"    HD click at {px},{py} — entry {entry.index} "
              f"(category {entry.group}), field {entry.field}, row {row}")
        run.hd_click(px, py)
    else:
        live = researchlist.row_field(run.state.fields, entry, row)
        if live is None:
            raise livesend.WrongDialog(
                f"{tag}: row {entry.index}.{row} is not in the live list")
        print(f"    ACTIVATE_FIELD {live.index} — entry {entry.index} "
              f"(category {entry.group}), field {entry.field}, row {row}")
        livesend.activate(run.app.client, live.index,
                          screen=SCREEN_SELECT, field_type=7,
                          rect=(live.x, live.y, live.x_end, live.y_end),
                          label=f"{tag} row")

    run.wait_for(lambda st: st.current_screen != SCREEN_SELECT,
                 seconds=120, label="the game leaving 53")
    run.pump(40)
    # Now write the frame that was held from before the click.
    run.step += 1
    tag_b = f"{run.step:03d}_{tag}_select_list"
    pygame.image.save(held[0], os.path.join(run.dir, f"{tag_b}_hd.png"))
    if held[1]:
        surf = pygame.Surface((640, 480), depth=8)
        surf.set_palette([(r, g, b) for r, g, b in held[2]])
        surf.get_buffer().write(held[1])
        pygame.image.save(surf, os.path.join(run.dir, f"{tag_b}_native.png"))
    before = {"hd_png": f"{tag_b}_hd.png"}
    after = run.capture(f"{tag}_after")
    got = read_field(run)
    ok = (got == entry.field)
    print(f"    -> wire says field {got}, the row's field is "
          f"{entry.field}: {'MATCH' if ok else 'MISMATCH'} "
          f"(was {field_before})")
    after.update({"chose_entry": entry.index, "chose_category": entry.group,
                  "chose_field": entry.field, "chose_row": row,
                  "how": how, "field_before": field_before,
                  "field_after": got, "match": ok,
                  "hd_before": before["hd_png"]})
    return after


def new_game(run):
    """From wherever the game is, to a galaxy map on turn one.

    Every step waits for the SHAPE it expects and sends only into that
    shape (decision 21). Nothing here is timed.
    """
    order = []

    def at(screen, fields=None):
        return run.wait_for(run.on_screen(screen, fields), seconds=60,
                            label=f"screen {screen}")

    run.pump(40)
    if run.state.current_screen != 10:
        sys.exit(f"the game is on screen {run.state.current_screen}, not the "
                 f"main menu — this phase starts from a fresh game")
    run.capture("main_menu")

    # NEW GAME is the third row, hotkey 'N' (78).
    field = next(f for f in run.state.fields if f.hotkey == 78 and f.x < 5000)
    livesend.activate(run.app.client, field.index, screen=10,
                      label="NEW GAME")
    order.append(("NEW GAME", field.index))
    at(13)
    # The settings screen only reports its own list once the count
    # changes: the menu's is 8 fields and so is the first snapshot here
    # (open fix 2). Wait for the 17-field list, not for the screen.
    run.wait_for(lambda st: len(st.fields or []) == 17, seconds=60,
                 label="the new game settings list")
    run.capture("new_game")

    # ACCEPT is the type 0 button on the right of the two.
    buttons = sorted((f for f in run.state.fields if f.field_type == 0
                      and f.index > 0), key=lambda f: f.x)
    livesend.activate(run.app.client, buttons[-1].index, screen=13,
                      field_type=0, label="ACCEPT settings")
    order.append(("ACCEPT settings", buttons[-1].index))
    at(51, 16)
    run.capture("select_race")

    radios = sorted((f for f in run.state.fields if f.field_type == 1),
                    key=lambda f: f.index)
    race = radios[RACE_PSILONS]
    livesend.activate(run.app.client, race.index, screen=51,
                      field_type=1, label="pick race")
    order.append(("pick race", race.index))

    # NAMING POPUP, then the FLAG SCREEN, then the map. Both are called
    # from inside Race_Selection_Screen_ (racesel.cpp:268-283), so the
    # wire still says 51 throughout and the SHAPE is the only signal
    # (decision 21). The naming popup is three fields — the dummy, an
    # OK button and a type 11 text entry (racesel.cpp Naming_Popup_);
    # the flag screen is its own small list. Both are accepted with
    # their default, because this run is about research and not about
    # what the empire is called.
    def popup_ok(st):
        fs = st.fields or []
        return (len(fs) == 3
                and any(f.field_type == 11 for f in fs)
                and any(f.field_type == 7 and f.x < 5000 for f in fs))

    run.wait_for(popup_ok, seconds=60, label="the naming popup")
    run.capture("name_popup")
    ok_field = next(f for f in run.state.fields
                    if f.field_type == 7 and f.x < 5000)
    livesend.activate(run.app.client, ok_field.index, screen=51,
                      shape=popup_ok, label="accept the default name")
    order.append(("accept name", ok_field.index))

    # The flag screen: wait for a list that is neither the popup's nor
    # the fourteen radios, then take its first real button.
    run.wait_for(lambda st: not popup_ok(st), seconds=60,
                 label="leaving the naming popup")
    run.pump(30)
    run.capture("flag_screen")
    if run.state.current_screen == 51:
        buttons = [f for f in (run.state.fields or [])
                   if f.field_type in (0, 7) and 0 < f.x < 5000]
        if buttons:
            livesend.activate(run.app.client, buttons[-1].index, screen=51,
                              label="accept the flag")
            order.append(("accept flag", buttons[-1].index))

    run.wait_for(lambda st: st.current_screen != 51, seconds=90,
                 label="leaving race selection")
    run.capture("after_race")

    # THE HOMEWORLD NAMING POPUP comes last, already on screen 0 — a
    # text entry and an OK, the same shape as the emperor's. Accept the
    # default and wait for the galaxy map's OWN list (its grid field),
    # which `livesend.on_galaxy_map` is the one test for.
    def naming(st):
        fs = st.fields or []
        return (any(f.field_type == 11 for f in fs)
                and any(f.field_type in (0, 7) and 0 < f.x < 5000
                        for f in fs)
                and len(fs) <= 4)

    for _ in range(4):
        if not run.wait_for(lambda st: naming(st) or
                            livesend.on_galaxy_map(st),
                            seconds=60, label="a popup or the map"):
            break
        if livesend.on_galaxy_map(run.state):
            break
        run.capture("naming_popup")
        button = next(f for f in run.state.fields
                      if f.field_type in (0, 7) and 0 < f.x < 5000)
        livesend.activate(run.app.client, button.index,
                          screen=run.state.current_screen, shape=naming,
                          label="accept the default name")
        order.append(("accept name", button.index))
        run.wait_for(lambda st: not naming(st), seconds=60,
                     label="leaving the popup")

    run.wait_for(livesend.on_galaxy_map, seconds=90,
                 label="the galaxy map's own field list")
    run.capture("galaxy_map")
    return order


def advance(run, limit=40):
    """End turns until a research dialog, handling what comes between.

    Everything it clicks that is NOT the map goes through the FALLBACK
    — which is the point: every one of those clicks is part A's claim
    again, on a screen HD has no version of.
    """
    for step in range(limit):
        st = run.state
        screen = st.current_screen
        if screen in (SCREEN_SCIENCE_ROOM, SCREEN_SELECT):
            print(f"  reached screen {screen} after {step} steps")
            return screen
        if livesend.on_galaxy_map(st):
            end_turn(run, label=f"turn {step + 1}")
            continue
        if not run.app._showing_original():
            # A POPUP OVER THE MAP. Screen 0 with a list that is not the
            # map's own: a leader offer, a warning, an event. HD has no
            # screen for these and does not fall back either, because
            # the SCREEN ID has not changed — decision 22 covers an
            # unknown id, not an unknown list on a known one. Declined
            # here by its own hotkey so the run can go on; that HD
            # draws the map over them is a finding for the report, not
            # something this order changes.
            buttons = [f for f in (st.fields or [])
                       if f.field_type == 0 and 0 < f.x < 5000]
            decline = next((f for f in buttons if f.hotkey in (82, 78, 27)),
                            None)
            if decline is None:
                # A DIALOG WITH NO BUTTON AT ALL — the GNN broadcast is
                # the dummy plus one whole-screen hidden field, and any
                # input closes it. Same family as the leader offer: a
                # list of its own on screen 0, which HD covers with the
                # galaxy map because the ID has not changed.
                whole = [f for f in (st.fields or [])
                         if f.field_type == 7
                         and (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)]
                if whole and len(st.fields or []) <= 3:
                    decline = whole[0]
                # A DIPLOMACY AUDIENCE: type 10 text options stacked in
                # the top left, the question first and the answers under
                # it. The lowest one is the refusal ("Reject"), and this
                # run refuses everything — a gift accepted would change
                # the game under the measurement.
                options = sorted((f for f in (st.fields or [])
                                  if f.field_type == 10), key=lambda f: f.y)
                if decline is None and len(options) >= 2:
                    decline = options[-1]
            if decline is not None:
                print(f"    popup on screen 0 ({len(st.fields or [])} "
                      f"fields): declining with field {decline.index} "
                      f"(hotkey {decline.hotkey})")
                run.capture(f"popup{step + 1}")
                # SOME OF THESE HAVE PAGES. The GNN broadcast keeps one
                # whole-screen field and advances its TEXT per input, so
                # a wait on the field list reports "nothing happened"
                # for an input that plainly did something — the same
                # trap as the science room, one screen along. Keep
                # sending while the picture moves and the list does not.
                before = run.shape()
                for _page in range(12):
                    digest = fb_digest(run)
                    livesend.activate(run.app.client, decline.index,
                                      screen=0, label="decline a popup")
                    run.wait_for(lambda s, b=before, d=digest:
                                 (s.current_screen,
                                  len(s.fields or [])) != b
                                 or fb_digest(run) != d,
                                 seconds=45, label="the popup to answer")
                    run.pump(10)
                    if run.shape() != before:
                        break
                continue
            run.pump(30)
            continue
        # A fallback screen. The colony prompt has its RETURN; anything
        # else takes a click in the middle, which is what dismisses the
        # turn summary.
        nx, ny = COLONY_RETURN if screen == 1 else (320, 240)
        before = run.shape()
        fallback_click(run, nx, ny, f"advance{step + 1}_s{screen}")
        run.wait_for(lambda s, b=before: (s.current_screen,
                                          len(s.fields or [])) != b,
                     seconds=45, label="the fallback click to land")
        run.pump(15)
    print(f"  no research dialog in {limit} steps")
    return run.state.current_screen

