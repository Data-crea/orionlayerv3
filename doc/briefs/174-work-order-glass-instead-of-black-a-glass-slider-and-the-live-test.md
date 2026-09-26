Work order <n> — Glass instead of black on every screen, a glass slider, and the long-overdue live test

Number: next free work-order number from the tree; rename before filing under doc/briefs/.

Mode

Unattended single run, no reporting stops. Choices, findings and questions go to doc/briefs/<n>-parked-for-data.md with the default taken, progress to doc/briefs/<n>-progress.md. Builds on 169–173 (decisions 71, 72). Three parts, in this order: A (start hang), B (glass and slider), C (live test of everything since 167, including B).

Start

Clone per CLAUDE.md. Read the fundament index, the principles- parts, part 04 with decisions 71 and 72, the live-test protocol in CLAUDE.md, and the progress/parked files of 167–173 — especially every "live test parked" entry, 169's note on the hang, and 170/171's tint and contrast rules.

Precondition

Data closes his own engine and client before this run. Check that no engine or client is running and port 17362 is free. If an engine Data started is still running: do not connect to it and do not kill it — record it, do A as far as possible without starting an engine, do B fully offline, and park C.

A. The orion2re start hang

Three times the engine Claude Code started hung after data space allocated (the last time in a graphics call), while Data's own start works.

Start the engine as the live-test protocol says. If it runs cleanly, note it and continue. If it hangs:

Find where it waits (backtrace, strace, the graphics call from 169) — evidence, not guesses.
Compare with how Data starts it (his documented start command and environment): working directory, arguments, environment (DISPLAY/Wayland, SDL video/audio driver, locale), parent process, timing. Change one thing at a time until it starts; say which change did it.
Never wait more than a few minutes on a hung start; kill only processes you started, by PID.
Cause on the OrionLayer side (start script, tool, environment): fix it, add a check. Cause in orion2re: patch rule — entry in doc/orion2re_open_fixes.md, patch file, reported, not applied.
Record the finding in the fundament next to the live-test protocol.
B. Glass instead of black, everywhere

What Data sees: on almost every screen, boxes have a pure black fill. Next to the colourful universal background they look like holes (worst with a neutral frame tone, where the fill becomes near-black). Data's mockup of the look he wants, the right-hand box of Select Race: ~/Downloads/ChatGPT_Image_Sep_26__2026__06_07_07_AM.png — a dark gradient through which the background's nebula shows, dimmed; text clearly readable. Reference for the look only; nothing is cut from it (1683 px, painted blue).

B1. Inventory first. List every box with a black or near-black fill on every HD screen and popup: HUD panels, inner panels, list and table areas, popup bodies, text areas, anything else. Put the list in the progress file. Exclude only areas that are fully covered by a picture, portrait or map — the glass goes under pictures, never over them.

B2. Glass fill as the one fill for all of them, in the panel block in core/hud/, so no screen draws its own:

The background behind the box shows through, dimmed (softened if it helps — your choice, park it), under a vertical gradient.
The gradient's hue follows the frame colour through the existing tint rule: navy under blue, dark violet under violet, anthracite under grey/silver, near-black under black.
Measure opacity and gradient from the mockup (box region against the background beside it) and write them with their source into style.json, overridable by a mod's partial style.json.
A denser variant (one named style value) for boxes whose content must dominate — portrait grids, dense tables. Which boxes use it: your choice, park the list.
Inner corner lines as in the mockup: optional part of the block, off by default unless it looks right across screens; park it with renders.
Built at target resolution, cached per window size, tint, background and slider value — no blur every frame.

B3. Glass slider in the game settings. In GAME → SETTINGS, next to the frame colour rows, a slider "Panel glass" (name your choice) from more see-through to more solid/darker. HD EXTENSION.

One global value for all screens; stored through user_settings.json like the colour; applies immediately; Reset returns to the measured value from the mockup; a mod may set the default.
The slider can never make text unreadable: at every position, every text on every glass box stays at or above the contrast floors of 170/171, with the universal background and 173's demo mod background. Where a position would break that for a box, that box's opacity is clamped — say where and at which value.
The dense variant moves with the slider but stays denser.

Rules that hold: pictures, portraits and sprites pixel-identical (172's check passes); the tint never touches the background; no per-screen fills or hacks.

C. Live test of 167–173 and B

Per CLAUDE.md: one client only, scratch saves only (SAVE4/SAVE5, never SAVE8), hash SAVE1–11 before and after, name the slot per step. For every step: expected vs. observed, screenshot HD and, where it applies, native side by side.

Galaxy: GAME plate click opens the menu; every nav button opens its screen and RETURN comes back; star click; fleet click; TURN on a scratch save advances the stardate.
GAME → SETTINGS: hue, saturation, brightness and the new glass slider change the look live; Reset works; settings survive a restart; mod-folder switch works after restart as documented.
New Game: pictures visible for every setting; every setting cycles; each checkbox toggles and shows its state; CANCEL returns.
Select Race / Custom Race: glass boxes, a race click updates the right box, text readable.
Leaders: opens, both tabs, leader click, hire popup opens and cancels; hire itself only if a scratch save offers a leader — otherwise park.
Every other HD screen and popup: open, one representative click, close. Text readable, nothing covered, clicks land on their button.
Window sizes: at least 1920x1080 and Data's 2576x1432.

Fix only regressions in click mapping or layout clearly caused by 169–173 or by B, each with a check and its own commit. Everything else is recorded and parked with evidence.

Tests
Full suite green, fresh clone green. New checks: glass on every box from the inventory, glass follows tint, slider persistence and reset, contrast floors over tints × backgrounds × slider range, pictures untouched.
Evidence under ~/orionlayer-fixtures/evidence/work_order_<n>/: Select Race next to the mockup; every screen at 1080p and 2160p with glass; Select Race and Colony in blue, violet, silver, grey, black; the slider at its two ends and the middle; live files named ..._LIVE_..., one folder per screen.
SAVE1–11 hashes identical before and after, except the named scratch slot; SAVE8 untouched in any case.
Done when

The hang is explained (fixed if on our side); every black box is glass; the slider works within the contrast floors; every live step has a result. The progress file ends with a table — step, result (works / broken / parked), evidence file — plus what was parked and what Data should look at first. Commits local, one per part and per fix. No push.
