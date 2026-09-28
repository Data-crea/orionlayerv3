# Work order — overnight run: original never shown, HD for all remaining paths, turn-change messages, travel line on hover, Multiplayer and Hall of Fame

**Number: next free work-order number in the tree** (the last one Data knows of is 187). Use it everywhere this order says `<n>`.

## Data's standing rule

**The player never sees any part of the original picture unless he presses F12.** No hand-over to the original for input, no native frame in transitions, no original screen as a fallback. Where HD cannot yet do something, it is parked for Data, never shown as original.

## How this run works

- **One unattended run, no pauses, no questions.** If a part is blocked, park it with the default you took and continue with the next part. Anything that needs Data goes into `<n>-parked-for-data.md`; keep `<n>-progress.md` current after every part, so the run can be picked up at any part boundary. Both files go where the tree currently keeps briefs (the repo or the local dev folder, whichever the cleanup decided). Never put your own material in `~/Downloads/`.
- **One commit per part.** Engine fixes: one commit per fix (see below).
- **Start:** read the index `doc/v3_fundament.md`, then the parts the task needs, always all `principles-` parts; then `187-progress.md`, `187-parked-for-data.md` and `187-original-visibility.md`.
- **Baseline Data expects:** `main` = `origin/main` = `b576bc7`, suite 409 green; orion2re `orionlayer-local` = `230a0638`, fixes 34–41 and 43–47 applied, Fix 42 OPEN. If the tree says otherwise, record the actual state and work from it.
- **Division of labour:** you own every detail. This order names what Data wants and what counts as done.
- **Part order is priority order.** If the run cannot finish everything, the earlier parts matter more.

## New permissions for this run (Data, 28 Sep)

- **Starting and closing the game:** you may start and close engines and clients as you need, including ones already running. Run `tools/liveguard.py` before closing anything you did not start, and back up the protected files first, as in 187.
- **Saving:** you may save into any slot **except the reference save (SAVE8)**. SAVE8 is never written. Check against the ways-of-working document which save is the reference; if it names a different slot, that slot is protected instead and you record it. Before you overwrite any other slot, copy it into the evidence folder so Data can restore it.
- **Live tests** still run on Xvfb; the real desktop only with `--real-desktop REASON`.
- **Colony screen:** never trigger CRUNCH, TOGGLE or field [0].
- **Diplomacy:** never confirm Declare War or any proposal that changes relations; answer with Cancel.

## Engine fixes: approved in advance for this run

Data wants this in one piece. Any orion2re change that a part of this order needs — Fix 29 and any new fix — is **approved in advance**, on these conditions:

- Entry in `doc/orion2re_open_fixes.md` and patch file first; full proof on the current tip of `orionlayer-local` (applies cleanly without offset, compiles, counter-test with a misspelled constant fails). No proof, no apply: park it.
- Then the full ritual: one-line comment `OrionLayer, open fix N.` at every changed place; one commit per fix, never pushed; entry set to APPLIED with diff, both hashes, revert path and side effects; `tools/version_check.py`, README, `setup.py` and fundament part 09 updated; a new bundle after each fix; doc and commit byte-identical.
- The fix must be needed by a part of this order. Nothing else.
- **Fix 42 is not approved** and stays OPEN.
- Rebuilding the engine binary `play.py` starts is allowed under the permissions above.

## Rules that apply to every part

- Every new HD screen or box goes through the handover gate `core/handover.py` and is covered by the flash check and by the double-scaling check 090t. Style as all current screens: HUD style, glass fill with the transparency setting, universal background with mod override, global frame colour. Original graphics are adopted where the original has them. Visible game text comes from the extracted strings.
- **No silent deviation:** every difference from the original gets its marker (HD EXTENSION / DEVIATION) in module, status document and smoke test, with the reason.
- **Committed fixtures:** every game-written text replaced by a stand-in before the first commit.
- **Evidence** under `~/orionlayer-fixtures/evidence/work_order_<n>/`.
- References to earlier briefs, entries or decisions name the number AND the first line.

---

## Part 1 — Stage 1: the original is never shown

Implement the proposal from `187-original-visibility.md` for **all 6 paths**. Wherever the original picture would become visible without F12, HD keeps its last frame and shows the notice "F12 to answer" (HD EXTENSION; text in the HD string file so it can be translated). F12 then shows the original as it does today and returns to HD.

- One check that fails if any of the 6 paths shows a native frame without F12.
- Extend the flash check so it counts "native frame without F12" as a failure everywhere, not only on the recorded transitions.

Commit: the change and its checks.

## Part 2 — Small items from 187

- **Audience menu header:** the original draws it in the colour of the menu items; HD does the same.
- **Name entry in the Ship Designer:** instead of a fixed 15 Backspaces, delete as many characters as the current name has (from the wire since Fix 44). Live: a short name and one at the field's maximum length, both replaced cleanly.

Commit: both changes and their checks.

## Part 3 — Galaxy map: travel line on hover

Today, with a ship or fleet selected, the dashed travel line appears only after clicking a planet. Data wants:

- The dashed line appears **as soon as the mouse hovers over a star/planet** while a ship or fleet is selected, and disappears when the mouse leaves.
- **Green:** the ship can reach it. **Red:** it cannot.
- Clicking works as today.

First check what the original does on hover and which colours it uses; wherever Data's wish differs from the original, mark it HD EXTENSION with the reason "Data's decision, 28 Sep". Reachability comes from the engine (range/fuel as the engine computes it), never recomputed by HD from guesses; if it is not on the wire, that is an engine fix under the rules above. Hover must stay smooth at 2576: measure frame time with the line active.

Live on Xvfb: one reachable and one unreachable target, hover in and out, then click; screenshots of each state.

Commit: the change, its checks, the frame-time measurement.

## Part 4 — Turn-change messages in HD

At turn change the original shows its own boxes today. Build HD versions of **all** of them.

1. **Inventory first** from the orion2re source and the original: every box and message that can appear at turn change or during the turn's processing — finished building projects, events, notifications, reports and whatever else you find — with the screen id each one has, what it shows, its buttons and where each button leads. Write `doc/brief_turn_messages.md` before building.
2. Build them. Where it fits, use one shared HD message box (the one from Part 5 / Fix 29) and per-type content, rather than one screen per message.
3. **Buttons that jump elsewhere** (for example to a colony): known issue entry 33 — the jump from the Turn Summary lands on the galaxy instead of the colony. If a message button runs into it, you may fix it under the engine-fix rules above; otherwise park it.
4. **Live:** end turns in the scratch saves (under the saving permission above) until as many message types as possible have appeared. Walk each one: in, every button, out; 0 native frames. List the types that never appeared, each with what would trigger it and whether it is checked offline from recorded data.

Commit: inventory/brief, the HD boxes and their checks, the live report.

## Part 5 — Stage 2: HD for each of the 6 paths

Replace the Stage 1 notice with a real HD version for every one of the 6 paths from `187-original-visibility.md` that Part 4 did not already cover. Start with the HD message box on the basis of Fix 29 (proof first, then apply under the rules above), then the rest (for example the colony base choice and the combat choice), each with the data it needs from the wire.

The Stage 1 notice stays only for a path that cannot be finished in this run; each such path is parked with what is missing.

Live: walk each path, 0 native frames, compare with the native frame beside it.

Commit: one commit per path or per group of paths sharing one box.

## Part 6 — Main menu: Hall of Fame

Implement the Hall of Fame completely: every entry, every column, the way in and out, the empty state. If the scratch saves or the game files have no entries, build test entries in a scratch location only (never in the player's real Hall of Fame file; back that file up before any live test) and remove them afterwards. Compare with the native frames.

Commit: the screen, its checks, the comparison.

## Part 7 — Main menu: Multiplayer

Implement the Multiplayer path completely, as far as orion2re supports it: every screen and dialog behind the main-menu button (connection type, setup, lobby, whatever exists), every way in and out.

- First establish from the source what orion2re really offers for multiplayer (which modes work, which are stubs). Build HD for everything the engine offers; what the engine does not offer is recorded, not faked.
- Live as far as it can be done on one machine (hotseat, or two local instances if the engine supports that). Anything that needs a second machine or a network partner is parked with how Data could test it.

Commit: reading report, the screens and their checks, the live report.

## Part 8 — Gates and push

Push only if all four are green: full suite, fresh clone, liveguard, flash check (with the stricter "no native frame without F12" rule from Part 1). No force-push. If a gate stays red, do not push and say why.

## Carried over unchanged (do not act; list them in the parked file with the existing defaults)

- From 185: hull choice only faintly marked; audience header line (text), fade-in and talking animation not drawn.
- Extra slot message after ESC in the load dialog (default: leave it).
- Narrow buttons with the word only.
- Buildings as a list instead of the grid (Fix 36 unused, UNVERIFIED).
- Research query at turn start not measured.

## End of run

The progress file ends with:
- which engine fixes were applied (number, first line, hash after) and which were parked;
- how many of the 6 paths are HD now and which still show the Stage 1 notice;
- the list of turn-change message types: built / seen live / checked offline only / not built;
- the travel-line result with frame time;
- Hall of Fame and Multiplayer: what works, what the engine doesn't offer, what needs Data;
- which save slots were overwritten (with their backups), and confirmation that SAVE8 is untouched;
- a short acceptance checklist for Data (one screen), and what is parked.
