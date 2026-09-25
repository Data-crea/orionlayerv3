Work order <n> — The frame colour must never touch pictures

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Choices go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. Builds on 169–171 (decision 71).

Start

Clone per CLAUDE.md. Read the fundament index, all principles- parts, part 04 with decision 71, and the progress and parked files of 169–171.

What Data saw

Screenshot of the New Game screen at 2576x1432 with a grey/silver frame tone: the five picture boxes (Difficulty, Galaxy Size, Galaxy Age, Players, Tech Level) are completely black where the pictures for the chosen setting belong. Also visible:

The NEW GAME title plate shows a blotchy light smear behind the word — the plate's centre glow looks dirty when tinted to grey.
The three checkboxes (Tactical Combat, Random Events, Antarans Attack) are all empty. Unknown whether they are all off in that state or the check mark is no longer drawn.
1. Find the cause first

Two candidates; establish which, with evidence, before changing anything:

The tint recolours the pictures (e.g. their colours fall in the 170–250° accent range and get darkened), or
The pictures were already lost in 169 when the pre-game screens were rebuilt, independent of the tint.

Render the New Game screen at the default blue and at grey/black and compare the picture boxes with the source images. Write the finding into the progress file. If they were lost in 169, check every other screen rebuilt in 169 for the same loss.

2. Fix: recolour by component, never by colour

The tint applies only to named HUD building blocks (panels, edges, glow, separators, buttons, title plate, scrollbar, TURN and the other blocks in core/hud/) and to text marked as accent labels. Everything else is untouched by construction — pictures, original sprites, portraits, planet and surface images, star and player colours, icons with their own colours — whatever their hue. If the current rule selects pixels by hue anywhere, replace that with the component rule. Restore the pictures where they are missing.

3. Title plate glow in neutral tones

Make the plate look clean in silver, grey, dark grey and black: the centre glow must not turn into a smear. Your choice how (tint the glow separately, fade it with saturation, or a code-drawn glow) — park it with renders.

4. Checkboxes

Find out whether the New Game checkboxes draw their checked state. If not, restore it in the new style (a HUD block, following the tint). Check every other checkbox or toggle in the HD screens the same way.

Tests
Full suite green, fresh clone green.
New check: for every screen and popup, every picture/sprite/portrait region is pixel-identical to its source rendering across a set of tints (default blue, silver, grey, dark grey, black, one saturated colour). No check is deleted for failing.
New check: checkboxes draw both states.
Renders under ~/orionlayer-fixtures/evidence/work_order_<n>/: New Game in blue, silver, grey, black before and after; the title plate in each neutral tone; any other screen where pictures were missing. Listed as things for Data to look at.
Live test only if orion2re starts cleanly; do not connect to an engine Data started. If blocked, run offline and park it.
Done when

Cause documented, pictures back on every screen under every tint, plate clean in neutral tones, checkboxes show their state, checks in. Progress file ends with what was built, what was parked, and what Data should look at first. Commits local. No push.
