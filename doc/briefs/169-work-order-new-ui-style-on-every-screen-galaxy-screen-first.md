Work order <n> — New UI style on every screen, galaxy screen first

Number: take the next free work-order number from the tree and rename this file accordingly before filing it under doc/briefs/.

Mode

Unattended single run. No reporting stops. Choices and questions go to doc/briefs/<n>-parked-for-data.md with the default you took, progress to doc/briefs/<n>-progress.md. Data corrects afterwards in follow-up orders — coverage of all screens and a harmonious whole beat polish on any one of them.

Start

Clone per CLAUDE.md (full tree). Read the doc/v3_fundament.md index, all principles- parts, and at least parts 01, 03 and 04 (frames, sizing, artwork, markings). Read doc/briefs/168-frame-evaluation.md.

Data's decision (25 September 2026) — record it first

The metal cockpit frames are replaced on every screen by a frameless style: background image, panels with a thin glowing edge, slanted buttons with a glowing underline, a title plate, a large action button. The look is defined by Data's material below. Reason: none of the frames is sharp at 2160p (168), and a style made mostly of code-drawn shapes is sharp at every resolution and uniform by construction.

Write this as a new decision in the fundament (next free number), in the part it belongs to, with what it supersedes (55, 69, 70 and whatever else hangs on per-screen frame images — check, do not assume) and what it costs: the original's cockpit look. The old frame images and their code are NOT deleted in this order; the new style becomes what every screen draws.

Material (in ~/Downloads/)
galaxy_hud_notext(1).png — 6704x3756 RGBA, Data's AI-generated HUD for the galaxy screen, text already removed: title plate, right info panel with five icons, six slanted nav buttons with icons, TURN button. Real alpha. Effective detail about half its size (measured). The source for cut pieces and for measured style values.
galaxy_screen.png, colony_screen.png — mockups of the finished look. Reference for how it should LOOK; no geometry, text or data comes from them.

Put the HUD image into the tree as authored artwork (like frame.png, decision 58's pattern for AI artwork), and a cutter tool that derives the pieces from it. LICENSE: AI-generated, no copyright claimed — and fix the wrong frame provenance 168 found in the same commit.

What to build

1. Style values, measured. From the HUD image and the mockups: panel fill, edge colour and width, glow colour and softness, separator lines, corner shape, button fill, active/hover glow, title and label colours, text sizes relative to box height. One file every screen reads. Each value names where it was measured.

2. One shared set of building blocks, drawn in code at the target resolution and cached per resolution and state: panel, slanted button (normal, hover, active, disabled), title plate with its text in code, large action button, small button inside panels, table header / row / selected row / scrollbar, popup/dialog body, separator. Cut pieces from the HUD are used where code cannot match them (icons, and the title plate or panels if the code version falls clearly short — say which and why). No screen draws its own variant of a block.

3. Text. All text in code, never baked. Pick the closest font in the tree to the mockups' font; park the choice.

4. Screens. Galaxy screen first, then every other screen with an HD version — make the list from the tree and put it in the progress file. Commit per screen. Leaders included, in its current state (open fix 30 still parked). The GAME menu and every popup and dialog get the popup block.

5. Backgrounds. Data delivers them later. Each screen gets one background slot resolved through the resource roots; until then a plain dark placeholder. The galaxy map's own floor stays what it is — the HUD sits on top of it.

6. Icons. Use the HUD's icons where they fit. A screen that needs icons the HUD does not have gets text-only buttons for now, and the parked file lists every missing icon (screen, button, size) so Data can generate them.

Rules that do not change
Clicks still reach the right native fields. Where a button or box sits somewhere other than the original's place, the click mapping follows it and the position is marked DEVIATION.
Every extension, deviation and omission marked in module, status document and smoke check (decision 61's vocabulary).
Checks whose subject no longer exists (frame holes, rings) may be deleted, and the commit says so and names the replacement; no check is deleted for failing. New checks for the blocks and the style file.
Sizes from source tables or measured values, never from asset pixel size.
Tests
Full suite green, fresh clone green.
Renders of every screen at 1080p, 1440p and 2160p, and galaxy and colony side by side with the mockups, under ~/orionlayer-fixtures/evidence/work_order_<n>/, listed in the progress file as things for Data to look at.
Live test per CLAUDE.md, one client, scratch saves only. If the connection is taken, do not wait — run everything offline and park the live part.
Done when

All screens draw the new style, the decision is recorded, the progress file ends with what was built, what was parked, the missing-icon list, and what Data should look at first. Commits local. No push.
