#!/usr/bin/env python3
"""Load a saved game through the GAME menu, and prove which one arrived.

    python tools/gameload.py slots         # the ten slots, three sources, loads nothing
    python tools/gameload.py load 4        # load SAVE4.GAM, counter-checked

The standing live protocol says scratch saves SAVE4/SAVE5 only,
RELOADED, never continued (work order 126, rule 8). Until now nothing in
the tree assembled that chain: `screens/game_menu/nodes.py` classifies
the dialog and names the slot rows, and `tools/game_menu_hd.py` clicks
the tenth row through the HD overlay to demonstrate the GAME menu — a
demonstration of one slot, not a driver a live acceptance can steer.

WHAT EVERY STEP IS CHECKED AGAINST — the list read AT THAT MOMENT, never
an earlier reading. The dialog is identified by `nodes.classify`, which
tests SHAPE and not index; the field is found in that same list by
hotkey and type; and the send goes through `tools/livesend.py`, which
re-resolves index, type and native rect against the list the client
holds when the byte goes out, and refuses otherwise (work order 129 A).
A refusal raises.

WHICH SAVE ARRIVED — three sources written by three different things,
and the snapshot as the fourth:

  the file      `SAVE<n>.GAM`: bytes 4..40 are the description and the
                int32 at 0x29 the stardate (filedef.cpp:223-224), read
                here off the disk before anything is sent
  the dialog    that slot's record in MSG_SAVE_SLOTS, which the engine
                formats from the same bytes with `Get_Star_Date_Strings_`
                (doc/ext_save_slots.patch, open fix 14)
  the row       `nodes.slot_rows` sorts the ten type-7 rows top to
                bottom AND row i must sit at the native rectangle
                `Add_Game_Popup_Fields_` builds it at (loadsave.cpp:263)
  the snapshot  after the load, `stardate` and `num_players` off the
                wire — the counter-check, and the only one of the four
                that is about the GAME rather than about a file

The first three are agreement about WHICH ROW; only the fourth says the
game actually loaded it. A driver that stopped at the third would report
a clean load of a slot the engine had refused.

**SAVE8 IS NEVER LOADED.** It is the reference fixture
(`tools/fixtures.py`, `FIXTURE_FILES["reference"]`) — read, never
played. The refusal is the first statement of `load_slot`, before a
field is read, so no caller can reach the send by getting the chain
right; and a smoke check holds it there.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import livesend  # noqa: E402
from screens.game_menu import nodes  # noqa: E402

# `livedrive` — the client, the loop, the evidence — is imported where
# it is used and not here, because it pulls in pygame, the palette and
# `main.App`. The half of this driver that DECIDES anything (the slot
# arithmetic, the three-source agreement, the SAVE8 refusal) is pure,
# and a rule that can only be checked against a running game is a rule
# that gets checked once. `screens/game_menu/nodes.py` is built that
# way for the same reason, and its docstring says so.

#: orion2_consts.h:468. The whole GAME tree reports this one id.
SCREEN_GAME = 8
SCREEN_GALAXY_MAP = 0

#: The GAME button: `MAINSCR::Add_Map_Fields_`, mainscr.cpp:1389 —
#: type 0, hotkey 'G'. Found by those, never by the index 6 it happens
#: to carry on the galaxy map (decision 20: a field NUMBER means
#: something else in every other list).
GAME_HOTKEY = ord("G")

#: The reference save. `fixtures.FIXTURE_FILES["reference"]` is this
#: slot's bytes, and every acceptance that names the reference fixture
#: is measured against them.
REFERENCE_SLOT = 8

#: savegame.h:6-7, read by `Is_Valid_Game_Type_` (loadsave.cpp:953).
VALID_MAGIC = (0xE0, 0xE1)

#: filedef.cpp:227 forces slot 10's description, whatever the file
#: holds — so the file and the dialog disagree there BY DESIGN and the
#: comparison must know it rather than report a fault.
WIRE_FORCED_DESCRIPTION = {10: "(Auto Save)"}


def row_rect(i):
    """Where `Add_Game_Popup_Fields_` case 2 builds slot row `i`.

    `saved_game_fields[i] = Add_Hidden_Field_(173, 49 + 31*i, 370,
    73 + 31*i, ...)`, loadsave.cpp:263. This is the SECOND source for
    "this row is slot i" — the first is its place in the list sorted
    top to bottom, and a row that satisfies only one of them is a row
    this driver will not activate.
    """
    return (173, 49 + 31 * i, 370, 73 + 31 * i)


def _plain(text):
    """A description without the active slot's colour codes.

    `Embed_Special_Color_Codes_` wraps the ACTIVE slot's description in
    `\\x03 ... \\x01` (loadsave.cpp:1655-1667) and
    `Remove_Embedded_Special_Codes_` takes them off again (:1672-1680).
    `wire_protocol.parse_save_slots` already does that for the wire
    side; the FILE carries them too — SAVE1.GAM on this machine holds
    `\\x03Darlok's colony destroyed` — so both sides are normalised
    here before they are compared, or the agreement test would fail on
    whichever slot was active when the file was written.
    """
    if text.startswith("\x03"):
        text = text[1:].split("\x01", 1)[0]
    return text


def file_header(slot):
    """{description, stardate} from SAVE<slot>.GAM, or None.

    None is a STATE, not an error: an empty slot is a file that is not
    there or whose magic number is not a game, and the Load dialog
    shows the warning for it (loadsave.cpp:376-379).
    """
    from livedrive import GAME_DIR
    path = os.path.join(GAME_DIR, f"SAVE{slot}.GAM")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        head = fh.read(0x2E)
    if len(head) < 0x2E or struct.unpack_from("<I", head, 0)[0] \
            not in VALID_MAGIC:
        return None
    return {"description": _plain(head[4:41].split(b"\0", 1)[0]
                                  .decode("latin-1")),
            "stardate": struct.unpack_from("<i", head, 0x29)[0],
            "path": path}


def stardate_str(value):
    """The engine's own printing of a stardate: `Get_Star_Date_Strings_`
    prints `value / 10` and `value % 10` (loadsave.cpp:645-718), which is
    what `GameState.stardate_str` does for the snapshot."""
    return f"{value // 10}.{value % 10}"


def wire_slot(run, slot):
    """That slot's MSG_SAVE_SLOTS record, or None where none arrived.

    Absence is a state: without `doc/ext_save_slots.patch` the message
    never comes and the dialog has slot numbers only (an HD STATE,
    decision 60). This driver still loads — the file and the row still
    agree — and says the source was missing.
    """
    slots = getattr(run.state, "save_slots", None) or {}
    records = slots.get("slots") or []
    return records[slot - 1] if len(records) >= slot else None


def fingerprint(state):
    """What the SNAPSHOT says about which game is loaded.

    Stardate and player count are the two the counter-check names; the
    star and colony counts come along because `fixtures.FIXTURES`
    identifies a save by all four and a run that prints two of them
    cannot be matched against that table afterwards.
    """
    return {"stardate": getattr(state, "stardate", 0),
            "players": getattr(state, "num_players", 0),
            "stars": getattr(state, "num_stars", 0),
            "colonies": getattr(state, "num_colonies", 0)}


def open_menu(run):
    """The galaxy map's GAME button, to the menu's eleven fields."""
    if nodes.classify(run.state.fields) == nodes.MENU:
        return True
    field = next((f for f in (run.state.fields or [])
                  if f.hotkey == GAME_HOTKEY
                  and f.field_type == nodes.TYPE_BUTTON
                  and 0 < f.x < 5000), None)
    if field is None:
        raise livesend.WrongDialog(
            f"no GAME button (type {nodes.TYPE_BUTTON}, hotkey 'G') in "
            f"the list on the wire — nothing sent")
    livesend.activate(run.app.client, field.index, screen=SCREEN_GALAXY_MAP,
                      shape=livesend.on_galaxy_map,
                      field_type=nodes.TYPE_BUTTON,
                      rect=(field.x, field.y, field.x_end, field.y_end),
                      label="GAME")
    return run.wait_for(lambda st: nodes.classify(st.fields) == nodes.MENU,
                        seconds=60, label="the GAME menu")


def open_load(run):
    """LOAD in the menu, to the Load dialog's sixteen fields."""
    button = nodes.hotkey_field(run.state.fields, "L", nodes.TYPE_BUTTON)
    if button is None:
        raise livesend.WrongDialog(
            "no LOAD button in the menu's list — nothing sent")
    livesend.activate(run.app.client, button.index, screen=SCREEN_GAME,
                      shape=livesend.in_game_menu(nodes.MENU),
                      field_type=nodes.TYPE_BUTTON,
                      rect=(button.x, button.y, button.x_end, button.y_end),
                      label="LOAD")
    return run.wait_for(lambda st: nodes.classify(st.fields) == nodes.LOAD,
                        seconds=60, label="the Load dialog")


def leave_dialog(run):
    """CANCEL back to the menu, then RETURN to the galaxy map.

    CANCEL is hotkey 'C' (loadsave.cpp:382-387); RETURN is the FIRST
    ESC field of the menu, which is why `nodes.esc_field` walks the
    list the way `Interpret_Keyboard_Input_` does.
    """
    cancel = nodes.hotkey_field(run.state.fields, "C", nodes.TYPE_BUTTON)
    if cancel is None:
        raise livesend.WrongDialog("no CANCEL in the Load dialog")
    livesend.activate(run.app.client, cancel.index, screen=SCREEN_GAME,
                      shape=livesend.in_game_menu(nodes.LOAD),
                      field_type=nodes.TYPE_BUTTON,
                      rect=(cancel.x, cancel.y, cancel.x_end, cancel.y_end),
                      label="CANCEL")
    run.wait_for(lambda st: nodes.classify(st.fields) == nodes.MENU,
                 seconds=60, label="the menu again")
    back = nodes.esc_field(run.state.fields)
    livesend.activate(run.app.client, back.index, screen=SCREEN_GAME,
                      shape=livesend.in_game_menu(nodes.MENU),
                      rect=(back.x, back.y, back.x_end, back.y_end),
                      label="RETURN")
    return run.wait_for(livesend.on_galaxy_map, seconds=60,
                        label="the galaxy map's own field list")


def slot_row(run, slot):
    """The Load dialog's row for SAVE<slot>.GAM, off the list read now.

    Both sources must agree — see `row_rect`.
    """
    rows = nodes.slot_rows(run.state.fields)
    if len(rows) != nodes.SLOTS:
        raise livesend.WrongDialog(
            f"the live Load dialog has {len(rows)} slot rows, not "
            f"{nodes.SLOTS} — nothing sent")
    row = rows[slot - 1]
    got, want = (row.x, row.y, row.x_end, row.y_end), row_rect(slot - 1)
    if got != want:
        raise livesend.WrongDialog(
            f"row {slot} of the live list is at {got}; loadsave.cpp:263 "
            f"builds slot {slot} at {want} — the two sources disagree "
            f"about which row this is, nothing sent")
    return row


def slot_table(run):
    """Every slot as the file and the dialog see it, for the record."""
    out = []
    for slot in range(1, nodes.SLOTS + 1):
        disk, wire = file_header(slot), wire_slot(run, slot)
        entry = {"slot": slot, "file": disk, "wire": wire,
                 "agrees": agreement(slot, disk, wire)}
        out.append(entry)
    return out


def agreement(slot, disk, wire):
    """How the file and the dialog compare for one slot, as a word.

    "no wire" is not a failure (see `wire_slot`); "empty" is the engine's
    own reading of an absent or invalid file.
    """
    if disk is None:
        return "empty"
    if wire is None:
        return "no wire"
    want_desc = WIRE_FORCED_DESCRIPTION.get(slot, disk["description"])
    if _plain(wire["description"]) != want_desc:
        return (f"MISMATCH, description: file {disk['description']!r}, "
                f"dialog {wire['description']!r}")
    if wire["stardate"].strip() and stardate_str(disk["stardate"]) \
            not in wire["stardate"]:
        return (f"MISMATCH, stardate: file "
                f"{stardate_str(disk['stardate'])}, dialog "
                f"{wire['stardate']!r}")
    return "agrees"


def load_slot(run, slot):
    """Load SAVE<slot>.GAM through the GAME menu. Returns the record.

    The whole chain, each step against the list read at that moment,
    and the counter-check at the end.
    """
    if slot == REFERENCE_SLOT:
        raise ValueError(
            f"SAVE{REFERENCE_SLOT}.GAM is the reference fixture and is "
            f"read, never played (work order 126, rule 8) — nothing sent")
    if not 1 <= slot <= nodes.SLOTS:
        raise ValueError(f"slot {slot} is not one of 1..{nodes.SLOTS}")
    disk = file_header(slot)
    if disk is None:
        raise ValueError(
            f"SAVE{slot}.GAM is not a valid saved game on disk — the "
            f"dialog would answer with its warning box, nothing sent")
    before = fingerprint(run.state)
    if not open_menu(run):
        raise livesend.WrongDialog("the GAME menu did not come up")
    if not open_load(run):
        raise livesend.WrongDialog("the Load dialog did not come up")
    table = slot_table(run)
    wire = wire_slot(run, slot)
    verdict = agreement(slot, disk, wire)
    if verdict.startswith("MISMATCH"):
        raise livesend.WrongDialog(
            f"slot {slot}: {verdict} — the file and the dialog are not "
            f"talking about the same save, nothing sent")
    row = slot_row(run, slot)
    print(f"  slot {slot}: file {disk['description']!r} stardate "
          f"{stardate_str(disk['stardate'])}; dialog "
          f"{(wire or {}).get('description')!r} "
          f"{(wire or {}).get('stardate')!r}; row {row.index} at "
          f"{(row.x, row.y, row.x_end, row.y_end)} — {verdict}")
    livesend.activate(run.app.client, row.index, screen=SCREEN_GAME,
                      shape=livesend.in_game_menu(nodes.LOAD),
                      field_type=nodes.TYPE_HIDDEN,
                      rect=(row.x, row.y, row.x_end, row.y_end),
                      label=f"load slot {slot}")
    # A slot row loads THAT slot at once — there is no select-then-LOAD
    # step (loadsave.cpp:332-375). Success lands on SCREEN_REPORTS
    # through a period of silence inside `FILEDEF::Load_Game_`, and
    # `Reports_Screen_` writes SCREEN_MAIN before any report runs
    # (mainscr2.cpp:119), so the wait is on the MAP'S OWN LIST and not
    # on a screen number: screen 0 arrives before the map does.
    arrived = run.wait_for(livesend.on_galaxy_map, seconds=240,
                           label="the galaxy map after the load")
    after = fingerprint(run.state)
    record = {"slot": slot, "file": disk, "wire": wire,
              "agreement": verdict, "row_field": row.index,
              "row_rect": [row.x, row.y, row.x_end, row.y_end],
              "before": before, "after": after, "arrived": arrived,
              "slots": table}
    record["loaded"] = check_loaded(record)
    return record


def check_loaded(record):
    """THE COUNTER-CHECK: does the snapshot show the save we asked for.

    The stardate is the one value the file and the snapshot both carry,
    so it is the test. The player count comes with it because a stardate
    is not unique — two saves of the same turn of two different games
    share one — and because it is the second number the snapshot header
    carries independently of the settings block (work order 165 part A).
    """
    disk, before, after = record["file"], record["before"], record["after"]
    same_date = after["stardate"] == disk["stardate"]
    moved = after != before
    print(f"  snapshot after the load: stardate "
          f"{stardate_str(after['stardate'])}, {after['players']} players, "
          f"{after['stars']} stars, {after['colonies']} colony records")
    print(f"    the file says stardate {stardate_str(disk['stardate'])}: "
          f"{'MATCH' if same_date else 'MISMATCH'}")
    if not moved:
        print("    and the fingerprint is UNCHANGED from before the load — "
              "either the slot held this very game or nothing loaded")
    return bool(same_date and record["arrived"])


def _cmd_slots(run):
    if not open_menu(run) or not open_load(run):
        return False
    for entry in slot_table(run):
        disk, wire = entry["file"], entry["wire"]
        print(f"  {entry['slot']:>2}  file "
              + (f"{disk['description']!r:<32} "
                 f"{stardate_str(disk['stardate']):>7}" if disk
                 else f"{'—':<32} {'—':>7}")
              + "   dialog "
              + (f"{wire['description']!r:<32} {wire['stardate']!r}"
                 if wire else "—")
              + f"   {entry['agrees']}")
    row = slot_row(run, 1)
    print(f"  the ten rows carry fields "
          f"{[f.index for f in nodes.slot_rows(run.state.fields)]}, "
          f"row 1 at {(row.x, row.y, row.x_end, row.y_end)}")
    print(f"  SAVE{REFERENCE_SLOT}.GAM is the reference fixture and this "
          f"driver refuses it")
    return leave_dialog(run)


def main():
    args = sys.argv[1:]
    what, rest, slot = (args[0] if args else "slots"), args[1:], None
    if what == "load":
        if not rest:
            sys.exit("load needs a slot: `load <slot> [evidence-folder]`")
        slot, rest = int(rest[0]), rest[1:]
    folder = rest[0] if rest else "gameload"
    from livedrive import Run, SendCounter, close, hashes
    run = Run(what if slot is None else f"{what}{slot}", folder=folder)
    saves = hashes()
    counter = SendCounter(run.app.client)
    run.pump(40)
    if what == "slots":
        ok = _cmd_slots(run)
        run.capture("slots")
    elif what == "load":
        record = load_slot(run, slot)
        ok = record["loaded"]
        run.capture(f"loaded_slot_{slot}")
        run.save_record({**record, "sends": counter.counts,
                         **close(run, saves)})
        print(f"load {slot}: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    else:
        sys.exit(f"unknown command {what!r}; known: slots, load")
    run.save_record({"sends": counter.counts, **close(run, saves)})
    print(f"{what}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
