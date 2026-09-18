Work order 130 — Build the research select screen (wire id 53), with the two things it stands on: clicks through the fallback view, and a row choice that means the row (18 Sep 2026)

Assign the next free number. Data's direction this morning: no long test series, the next screen gets built. This order therefore has NO reporting stop. Where a wrong build would result, it names a fallback instead of a stop. Separate commits, no push.

Rules: the block headed "RULES FOR THE WHOLE RUN — re-read this block at the start of every part" in doc/briefs/126-work-order-unattended-run.md, plus the three additions at the top of work order 129 (bundle after every orion2re commit; counter-tests with cleared bytecode or `python -B`; every reference by number AND first line). Live sends from tools go through tools/livesend.py.

Chat wrote this WITHOUT having read doc/research_screen_stop1.md, doc/newtech_reading.md or doc/briefs/129-parked-for-data.md — 129 was not on GitHub when this was drafted. Those three documents and doc/tech_change_reading.md are the authority on every detail; this order says where and why, not what. Where it contradicts them, they win and the report says so.


DECIDED (Data, 17–18 Sep; chat's recommendations, accepted)

- The fallback view forwards clicks (129 parked point 1).
- A research row is chosen by ACTIVATE_FIELD, made reliable by the small ORION2RE_EXT insertion in the tech selection that marks the activated row as selected before it is evaluated — option (c) under "What a patch would carry — described only" in doc/tech_change_reading.md. It is AUTHORISED here; it is the only orion2re change in this order. Reasons: decision 20 ("Field IDs for input.") reserves INJECT_CLICK for radio buttons and free map clicks; 129 showed live that an activation today commits whatever is under the pointer; and the same spot is the null dereference that crashed the game in 128.
- tech_applications[] gets verified now; hyper_advanced_tech stays quarantined and marked until a late-game save exists.
- First build: select mode only. Not in it: the category popup, change mode (36), the presentation dialog (52), the scientist artwork.


PART A — The fallback view forwards clicks

Decision 22 ("Graceful fallback.") promises the game stays playable on a screen HD does not know. 129 found that the fallback shows the original picture but forwards nothing; only the F12 mode does (main.py, the block 129's report cites). Since 52 and 53 exist, that makes every turn-start research a dead end inside OrionLayer's window.

- The fallback takes the SAME path as F12 — decision 9 ("Original-mode interaction lives in `original_view.py`"). No second click path; if the two differ in anything but how they are entered, say what and why.
- Decision 20's caveat applies: injected coordinates are window coordinates. State which half of the coordinate fix this relies on and that version_check requires it.
- Live: on wire id 52 (the presentation dialog), a click in OrionLayer's window moves the game on. A smoke check for the mapping from HD window pixel to native pixel at all four resolutions, including letterboxing if the view has any.


PART B — orion2re: the activated row is the chosen row

- Read the tech selection's input handling again yourself before touching it; build the insertion as small as the report describes it, guarded by ORION2RE_EXT, behaviour unchanged for mouse input.
- New commit on orionlayer-local, a fresh bundle, a new entry in doc/orion2re_open_fixes.md (next free number — quote its first line wherever you refer to it), the patch file under doc/, the REQUIRED_FIXES entry in tools/version_check.py.
- Live proof, on a new game as in 129 (the dialogs come quickly there): with the game's pointer parked somewhere else, ACTIVATE_FIELD on a row sets the player's current research field to THAT row's field — on three different rows on three occasions, read back from the wire. And the case that crashed in 128 (an activation with nothing selectable under the pointer) now does nothing or chooses the activated row, and does not crash.
- Open Fix 23 ("observation" — the SIGSEGV from 128): update its entry with what this changes.


PART C — The offered rows: verify, reconstruct, validate — or fall back

- tech_applications[] by decision 23's two sources (header compile against the size assert; a live read that agrees with what the screen shows). Until both agree it stays in unverified.py and this part ends in the fallback below.
- Reconstruct the offered rows per category the way doc/research_screen_stop1.md lays out; its finding was that categories and the offered field reconstruct, and the rows did not yet, for two named reasons. Address those two reasons; do not route around them.
- Validation the data provides (decision 25): the reconstruction must agree with the live FIELD_LIST — one hidden row per offered application, in the same order, one radio per non-empty category.
- This validation also runs IN THE PRODUCT, every time the screen is entered. If it fails — count or order disagree, a name is missing, the extractor's file is absent — the screen does not draw a list it cannot vouch for: it hands over to the fallback view (now clickable, part A) and logs why. That is what replaces a reporting stop in this order. If the rows cannot be reconstructed at all, deliver parts A and B, park the finding with exactly what is missing, and describe (not apply) what would have to come over the wire.


PART D — Names, costs and descriptions from the player's own files

Follow the extractor plan in doc/research_screen_stop1.md and the existing extractor pattern (tools/techname_extract.py and its siblings): run from tools/setup.py, output in an ignored folder, bytes handed over untouched with decoding at load time and a format version (decision 38's third bullet is the model), nothing extracted is ever committed, and an absent file is a state the screen explains by falling back, not an error. The cost table from 129 part C (core/research.py) is the source for the RP figures — one home, do not copy it.


PART E — The screen: screens/research_select/, GAME_SCREEN_ID 53

Structure first; frame and artwork come later (Data, 17 Sep: "Rahmen und Visuelles kommen später darüber").

- Layout transcribed from the original's own rectangles into boxes.json, each box carrying its 640x480 source as provenance: the title, eight category panels in two columns, per panel the category label with its cost, the field name, and the application rows. thin_border groups, the text skin labels (decisions 34 and 37). All wording from JSON or from the extracted strings (decision 15). Text that can carry game data goes through Style.render_text (decision 30).
- One function gives a row's rect; drawing, hover and click all call it (decision 5) — and because shared geometry guarantees agreement, not correctness, the check also asserts against the drawn pixels, as 128 part D did for the Planets list.
- Hover highlights the row as the original does. A left click on a row looks the row's field up in the CURRENT field list by shape — never by a remembered index (the rule 128 part C put into mapboxes.live_field; reuse it, third-copy rule) — and sends ACTIVATE_FIELD. Decision 33 ("Refuse input the game would refuse, before sending it."): a click that is not on an offered row sends nothing.
- After the send the screen waits for the game to leave 53, event-driven (decision 21), and HD returns to the galaxy map by itself as 129 saw.
- There is no cancel in select mode; say what the original does with ESC and a right click here, and do the same. If the screen has a help list of its own, transcribe its regions per decision 38; if not, say so.
- Everything the first build leaves out (the category popup, the scientist artwork, the description box if it is not built) is MARKED: in the module, in the status document, and in a check that fails if the marking disappears.


PART F — Checks and live acceptance

- Smoke checks: the layout at four resolutions; the row geometry rule; the refusal cases (click beside a row, field list of the wrong shape, reconstruction disagreeing with the field list → fallback, extractor file absent → fallback); no send while the state reports 52.
- Live, new game, one client: three turn-start selections made entirely inside OrionLayer's window by clicking an HD row — three different categories. Each time the wire afterwards reports the chosen field, the sidebar's research readout (129 part D) shows its turn count, and the game carries on. HD beside the native frame at three resolutions as evidence.
- Status document: the screen count, what works, what is marked missing. doc/briefs: progress file as in 126.


NOT IN THIS ORDER

The presentation dialog (52) as an HD screen — it stays on the now-clickable fallback. Change mode (36). The category popup. Any artwork or frame. A second orion2re change. The colony view, the fleet screen and their patches. The smoke-test split, Stop 2 of 127, moving ids 50/51 to the wire-only path.


REPORT

Deviations first. Then per part: seen live (evidence path), committed (repository and hash), bundle name, smoke count before and after. Which of the twelve questions under "Questions for Data before a build can start" in doc/tech_change_reading.md are now closed. A parked file only if part C ended in its fallback or something is Data's to decide; if it stays empty, say so.
