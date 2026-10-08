#!/usr/bin/env python3
"""The patches stacked on orion2re's `ext_api.cpp`, and taking them off a copy
— work order 186, moved out of `tools/version_check.py`.

A check that proves an EARLIER applied fix comes back off (`patch -R
--dry-run`, which is what "applied" means for fixes 30 and 32) has to take
every later fix that sits on that fix's context off a scratch copy first,
last one first, as the stack was applied. Until work order 186 that was the
colony series (open fixes 35-40, work order 181); since then the Ship
Designer's and the audience's fixes (44, 45, 47) and fix 43 sit on top of
it. This module holds the order and does the taking off; `version_check`
re-exports both names, which is where the checks import them from.

Nothing here reads or writes `~/orion2re`: the caller hands a copy.
"""
import os
import subprocess

#: Open fixes 35-40 in the order they are stacked on `ext_api.cpp` (work
#: order 181). Each appends its block after the one before, so they sit
#: on the trailing context of every earlier block in `SerializeState` —
#: a check that proves an earlier patch comes back off (`patch -R`) has to
#: take these off a copy first, last one first, as the stack was applied.
COLONY_SERIES = (
    "doc/ext_colony_screen_colony.patch",
    "doc/ext_colony_building_placement.patch",
    "doc/ext_colony_status_word.patch",
    "doc/ext_colony_product_cost.patch",
    "doc/ext_build_popup_queue.patch",
    "doc/ext_build_popup_lists.patch",
)


#: The fixes applied AFTER the colony series that change `ext_api.cpp`
#: around its blocks, in the order work order 186 applied them: 44 and 45
#: append after fix 40's block, 47 puts DIPL between INFS and COLS (fix
#: 35's context), 43 changes ProcessInput and the flag — and then the
#: fixes of work order 188, in the order applied (48 after 45's block). So they come off
#: a copy first, last one first — only their `ext_api.cpp` part, since the
#: copy holds that file alone. (Fix 46 does not touch `ext_api.cpp`; fix
#: 41's one line there sits far from every block and is left.)
STACKED_AFTER_COLONY = (
    "doc/ext_ship_designer_state.patch",
    "doc/ext_ship_designer_boxes.patch",
    "doc/ext_audience_screen.patch",
    "doc/ext_audience_state.patch",
    "doc/ext_engine_window_on_request.patch",
    # work order 188: 48 appends FMOV after 45's DSBX block, last
    "doc/ext_fleet_move_verdict.patch",
    # 29 appends MSGB after 48's FMOV
    "doc/ext_message_box_text.patch",
    # 49 appends TPOP after 29's MSGB
    "doc/ext_turn_popups.patch",
    # 50 appends HOFM after 49's TPOP
    "doc/ext_hall_of_fame.patch",
    # 51 appends MPLY after 50's HOFM
    "doc/ext_multiplayer_state.patch",
    # work order 194: 61 adds a case to ProcessInput (the right click)
    "doc/ext_inject_right_click.patch",
    # 52 adds the battle's gate after 50's g_hof_live
    "doc/ext_combat_screen_id.patch",
    # 53 appends CMBT after 51's MPLY, LAST
    "doc/ext_combat_state.patch",
    # 55 appends CMSL after 53's CMBT
    "doc/ext_combat_ordnance.patch",
    # 57 amends 52's CombatGuard and appends CRES after 55's CMSL
    "doc/ext_combat_result.patch",
    # 54 appends CTGT after 57's CRES
    "doc/ext_combat_targets.patch",
    # 59 appends FBSC after 54's CTGT
    "doc/ext_fleet_box_scroll.patch",
    # 56 adds the event ring at the file's head and appends CMEV after 59's FBSC
    "doc/ext_combat_events.patch",
    # 58 adds the command beside 56's ring and in ProcessInput
    "doc/ext_combat_commands.patch",
    # work order 197: 62 checks the pending activation in ProcessInput and Tick
    "doc/ext_activate_checked.patch",
    # work order 197: 65 keeps the view round 58's commands (Take_Combat_Command)
    "doc/ext_combat_command_view.patch",
    # work order 197: 64 adds MSG_SET_SPIES beside 58's command (ProcessInput)
    "doc/ext_set_spies.patch",
    # work order 199: 66 appends CPOP after 56's CMEV, LAST
    "doc/ext_combat_popup.patch",
    # work order 199: 67 extends 29's MSGB (version 2)
    "doc/ext_msgbox_items.patch",
    # work order 200: 68 appends COPT after 66's CPOP
    "doc/ext_combat_options.patch",
    # work order 200: 69 appends HLPL after 68's COPT
    "doc/ext_help_list.patch",
    # work order 212: 79 records the battle's sounds beside 56's
    # Combat_Event and after 52's gate
    "doc/ext_combat_sound.patch",
    # work order 212: 71 marks the input poll in Tick and adds its wait test
    # after 79's tick counter
    "doc/ext_combat_waits.patch",
    # work order 212: 71 amended clears the poll mark in 79's Combat_Event
    # after a taken command
    "doc/ext_combat_waits_command.patch",
    # work order 213: 82 adds Combat_Note after 71 amended's Combat_Event,
    # LAST (83 does not touch ext_api.cpp)
    "doc/ext_combat_beam_aim.patch",
    # work order 223: 84 compares the field list's bytes in Tick, LAST
    "doc/ext_field_list_content.patch",
)


def _api_part(root, patch):
    """The `src/ext/ext_api.cpp` section of a patch file, or None."""
    with open(os.path.join(root, patch), encoding="utf-8") as f:
        text = f.read()
    head = "diff --git a/src/ext/ext_api.cpp b/src/ext/ext_api.cpp\n"
    if head not in text:
        return None
    part = text[text.index(head):]
    end = part.find("\ndiff --git", 1)
    return part if end < 0 else part[:end + 1]


def _table(patch):
    """The version_check table that lists `patch` (imported late: that
    module imports this one)."""
    import sys
    vc = sys.modules.get("version_check") or sys.modules.get("tools.version_check")
    if vc is None:
        import version_check as vc
    return vc.LOCAL_PATCHES if patch in vc.LOCAL_PATCHES else vc.REPORTED_PATCHES


def take_off_colony_series(workdir, root):
    """Reverse every applied fix of COLONY_SERIES in `workdir` (a copy
    holding `src/ext/ext_api.cpp`), last first — after the `ext_api.cpp`
    parts of STACKED_AFTER_COLONY, which sit on its context (work order
    186). Returns the list of (patch, returncode, output); a patch whose
    marker the copy does not carry is skipped, so a tree without the
    series passes through."""
    api = os.path.join(workdir, "src", "ext", "ext_api.cpp")
    done = []
    for patch in reversed(STACKED_AFTER_COLONY):
        table = _table(patch)
        part = _api_part(root, patch)
        with open(api, "r", errors="replace") as f:
            if part is None or table[patch][1] not in f.read():
                continue
        run = subprocess.run(["patch", "-R", "-p1"], input=part,
                             cwd=workdir, capture_output=True, text=True)
        done.append((patch, run.returncode, run.stdout + run.stderr))
        if run.returncode != 0:
            return done
    for patch in reversed(COLONY_SERIES):
        table = _table(patch)
        marker = table[patch][1]
        with open(api, "r", errors="replace") as f:
            if marker not in f.read():
                continue
        run = subprocess.run(
            ["patch", "-R", "-p1", "-i", os.path.join(root, patch)],
            cwd=workdir, capture_output=True, text=True)
        done.append((patch, run.returncode, run.stdout + run.stderr))
        if run.returncode != 0:
            break
    return done
