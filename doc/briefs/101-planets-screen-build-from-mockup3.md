Brief 101 — Planets screen: build from mockup3, wire into the game

Date: 13 September 2026. Author: chat-Claude, on Data's instruction. Files in ~/Downloads/: frame3.png (1920x1080 RGBA, five transparent holes), mockup3.png. Copy both into the repo beside this brief and report sha256 for each. frame3.png becomes the screen's frame asset.

Before starting: git status -sb — if the tree is ahead, stop and ask Data to push first. Read doc/v3_fundament.md; next free decision number is 59 — verify.

Goal

MOO2's Planets screen (the list reached from the main screen's PLANETS button: every known planet, sort priority, display restrictions, Send Colony Ship / Send Outpost Ship / Return) as an HD screen, auto discovered, playable end to end in the running game.

mockup3.png is the look. The original is the data and the behaviour. Where the two disagree, the original wins unless this brief says otherwise — same call Data made on Colony Summary (brief 97).

Data gives you free hand on module layout, widget choice, box names, JSON structure and the order of work inside a stop. The constraints below are the ones the fundament already imposes; nothing here is new process.

Reuse, do not rebuild
Planet discs: the climate-resolved disc from Colony Summary, through core/resources.py. Same for the surface art if you use it.
Galaxy inset: Colony Summary's galaxy_inset — same renderer, same marker semantics. If it needs a parameter it does not have yet, add the parameter, do not copy the module.
List: the Colony Summary row palette and row states (row_a, row_b, row_selected, HD EXTENSION marked) and its column-box approach (column boxes F5-editable, everything else derived at runtime, never serialized). If the list code is not shareable as it stands, extracting it is in scope — this is the second screen that needs it, and the third copy rule says the extraction may wait, but a copy-and-diverge is the failure the fundament describes under "A name table copied into three files".
Panel skins: thin_border for grouping, text for bare labels, nothing drawn by hand (decision 34, 37).
Right-click help: the shared walk and popup (core/screenhelp.py, core/helppopup.py), regions transcribed from the original's help list into screens/<name>/help.json, bound by box name (decision 38, brief 98 pattern).
The frame

frame3.png has five holes and no nav row. Run tools/frame_holes.py --write and let it name them; the regenerator keeps non-cutout boxes. Two things to establish in Stop 1, not to assume:

The original Planets screen has no main-screen button bar, so a frame without nav_* holes is correct. Check that ScreenBase.handle_click (decision 13) and the smoke test tolerate a screen with zero nav_* boxes; if either does not, that fix is part of this brief.
The right column is one hole from top to the bottom strut. The mockup splits it into galaxy inset, system readout, SORT PRIORITY and DISPLAY RESTRICTIONS — those are content boxes with thin_border inside the cutout, like the sb_* readouts. The bottom-right hole holds the three buttons; buttons over a hole need a fill (cockpit panel or skin), they must not float on black.
What the mockup shows that the game does not have

The monster panel in the mockup carries "Heads 6 / Combat Strength / Special / Tactics" and a prose description. Do not reproduce that. Show only what the game provides for a guarded system — the monster's identity and whatever the original Planets screen or snapshot exposes about it. Hand-written flavour text is an unmarked invention. If Data wants such a panel later, it is a separate decision with a marked HD EXTENSION and a data source.

Same rule for the colour coding of rows (green / yellow / red for "good / marginal / hostile"): transcribe the original's colouring if it has one; if the original does not colour rows, the mockup's scheme is an HD EXTENSION and must be marked as one and keyed in colors.json, not painted in code.

No HD monster artwork exists in the tree. The picture box in the middle bottom hole is an image box resolved through core/resources.py that draws nothing and logs the missing set when no asset is present — same behaviour as the surface tiles on a fresh clone. Artwork later is a file swap.

Stops

Stop 1 — read, no code. Report:

Which orion2re files draw the Planets screen and handle its input; its screen ID; its field list (IDs, types) for the sort buttons, the restriction toggles, the three action buttons, the list and its scroll; which of those take ACTIVATE_FIELD and which are type 1 radios that need INJECT_CLICK (decision 20).
What the list shows per row in the original and where each value comes from — which of them the snapshot already carries and which would need a struct spec (decision 23, two sources) or a patch. Name anything you would have to reconstruct (decision 25).
The original's sort semantics and each display restriction's exact predicate, with the source line as reference, since the HD list may have to filter client-side.
What Send Colony Ship / Send Outpost Ship do when no suitable ship exists — whether that is a case for refuse-before-send (decision 33: one comparison, silent failure) or not.
The help list for the screen: how many entries, which have an HD counterpart.
The two frame checks above.
Anything in the mockup that the original cannot produce and that is not already listed here.

Stop and wait for Data's decisions. Any item where the answer changes the design goes into the report as a question with the options, not as a choice you made.

Stop 2 — build. After Data's answers. Screen folder, boxes.json for the resolutions the other screens define, help.json, colors.json entries, transitions in both directions (main screen → Planets, RETURN → main screen), input through field IDs, smoke test extended: frame holes agree with boxes.json, nav_* absence is legal, every HD EXTENSION named in the brief has a test that fails if it silently disappears. Tree may be red between steps; the closing stop must be green under SDL_VIDEODRIVER=dummy.

Stop 3 — live. Reference save ab70cc9ad5442335 (slot 8, Greywind). Name slot and fixture per step; check SAVE10.GAM against the secured fixture before and after. Open Planets from the main screen, sort by each priority, toggle each restriction, select a row, Return. Put an HD screenshot beside the native one for the same state and list what differs — as questions for Data, not findings. Right-click every help region once.

Acceptance
Playable round trip main screen → Planets → Return without the framebuffer fallback showing.
Every value on screen traceable to the snapshot, a verified struct spec, or a marked HD EXTENSION; nothing hand-typed from the mockup.
Sort and restriction results identical to the original on the reference save for at least one non-trivial combination, shown side by side.
Smoke test green; decisions filed under the next free number, if any are needed; status document updated; brief closed with a note on what was deferred.
Nothing pushed. Before asking "push?", name the one check that would break a fresh clone.
