Work order <n> — Leaders screen in HD (complete, original assets, no frame)

Number: take the next free work-order number from the tree and rename this file accordingly before filing it under doc/briefs/. Decisions are never renumbered.

Mode

Unattended single run. No reporting stops. Questions and open choices go to doc/briefs/<n>-parked-for-data.md (with your chosen default, so the run can continue), progress to doc/briefs/<n>-progress.md. Data corrects afterwards in follow-up orders — completeness beats polish in this run.

Start
Clone per CLAUDE.md (full tree — this run touches artwork). Read the doc/v3_fundament.md index, all principles- parts, and the parts the task needs.
Check the tree for anything Leaders-related that already exists (screens, extractors, smoke checks, briefs, open fixes) before adding anything.
Goal

The Leaders screen as a complete HD screen in OrionLayer, built like the other finished screens: everything the original screen shows and everything the player can do on it, including the dialogs and popups reachable from it.

Inventory the original screen from the orion2re source first: screen ID(s), fields, views/tabs, dialogs, which data the screen reads, which actions it triggers. Write the inventory into the progress file before building.
"Complete" means the inventory, not a guess. Anything in the inventory you do not build goes into the parked file with the reason.
Assets
Original MOO2 graphics only (portraits, icons, buttons, backgrounds as the original uses them), extracted from the game data. Reuse existing extractors where they fit; a new extractor needs a regenerator and a check like the existing ones. No AI artwork in this order.
Sizing from source tables or screen geometry, never from asset pixel dimensions.
Frame

No outer frame in this order — frames come later over the finished structure. Inner layout (boxes, dividers, text areas) as far as needed to make the screen readable and usable; how you draw it is your choice, park it for confirmation. Text must fit its boxes cleanly. No flash of the original screen on open.

orion2re

If data or actions the screen needs are not on the wire, follow the patch rule: entry in doc/orion2re_open_fixes.md, patch file under doc/, reported before applied. In this unattended run that means: write the entry and the patch file, park the go/no-go for Data, and build everything that does not depend on it (with a clear placeholder where it does). orion2re never goes online.

Deviations

Every deviation from the original is marked (HD EXTENSION / DEVIATION) in module, status document and smoke test, with the reason. Nothing silent.

Tests
New smoke-suite group for the screen under tools/smoke_suite/, against real state, not hand-built mocks. Two sources for every hand-copied value.
Live test per the protocol in CLAUDE.md: one client only, scratch on SAVE4/SAVE5 (never SAVE8), hash saves before and after, name slot per live step. Hiring/dismissing changes state — scratch slots only. If no scratch save offers leaders to hire, park it and say which state would be needed.
Side-by-side screenshots HD vs. native for each view and dialog under ~/orionlayer-fixtures/evidence/work_order_<n>/, listed in the progress file as questions to check, not as findings.
Done when
Inventory, build, markers, smoke group, evidence all in place.
Gate green (full suite), commits local. No push — Data decides after fresh-clone verification.
Progress file ends with: what was built, what was parked and why, what Data should look at first.
