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
#: 35's context), 43 changes ProcessInput and the flag. So they come off
#: a copy first, last one first — only their `ext_api.cpp` part, since the
#: copy holds that file alone. (Fix 46 does not touch `ext_api.cpp`; fix
#: 41's one line there sits far from every block and is left.)
STACKED_AFTER_COLONY = (
    "doc/ext_ship_designer_state.patch",
    "doc/ext_ship_designer_boxes.patch",
    "doc/ext_audience_screen.patch",
    "doc/ext_audience_state.patch",
    "doc/ext_engine_window_on_request.patch",
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
