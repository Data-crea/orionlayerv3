Work order — Colony list: after the geometry round

Read doc/v3_fundament.md before touching anything. The two geometry commits stay as they are; this goes on top. One stop before code for Part A; the rest follows once A's cause is named. Nothing pushed. Report with diff summary and check count.

Evidence from Data, 8 September evening, four screenshots in ~/orionlayer-fixtures/evidence/ as after_geometry_<W>x<H>.png: 1920×1080 correct except Parts C and D; the other three wrong in the ways below. Identify each window size from the image dimensions and Data's config before anything else — the stored keys are not the sizes she runs.

Data's acceptance of the pick: figure leaves the cell and follows the pointer as the original. Not to be touched.

Part A — one coordinate frame (stop and report first)

What the pictures show, as questions, not findings:

At the 1440p-class window the NAME text is clipped on the left and the header/cell columns do not scale with the window — the header NAME box sits at roughly the same device x as at 1080p.
At the ultrawide window the frame is letterboxed and the columns are placed from the window's left edge, outside the frame.
At the third window the panels are drawn far larger than the window.

Question: which transform places the six column boxes, and which places list_area? Decision 2 (cover-scale for background-aligned screens) and decision 1 (reference space, per-resolution lists, fallback by area) both apply here; name the function each rect goes through and where the two paths diverge. Then say the fix in one sentence before writing it. The expected shape: every rect on this screen derives from the list_area cutout through the same transform the frame uses, and the columns are expressed relative to that cutout, not to the window.

A check that renders headless at every stored key AND at Data's three sizes and asserts: the six columns tile list_area exactly, every column lies inside it, the name-block rect lies inside the NAME cell. Assert the rule, not the sizes — a fourth window size next month must fail the same way.

Stop and report Part A before code.

Part B — the scroll column is not "the remainder"

col_scroll takes whatever the window leaves, and the arrows are sized from it. Its width is a transcription: the original's scroll bar geometry in colsum.cpp (Add_Fields_..., the scroll field rect). Give the box that width in reference space; the arrows size from the row band, never from the column width; a check bounds the arrow inside one band. If the window is wider than the six columns after Part A, say where the residue goes and mark it.

Part C — plates on the empty rows

The report said plates on every band including empty rows; the 1080p picture shows seven plated rows and bare space below. Find which is true and fix the false one. The original's bitmap plates all ten. A check counts plate rects == row_count × 6 regardless of colony count.

Part D — "1 moved" goes

The move message evicts the transcribed description panel. The original shows nothing on a move — the row itself is the feedback. Remove the message and the move wording that carries it, or, if Data's earlier acceptance item (RETURN guidance for the held-cluster edge case) needs a line, give that one its own place with a marker at the three homes and never in the description panel. Description stays visible through a pick and a drop.

Part E — drop anywhere in the cell

Data's requirement: where in the cell the figure is dropped must not matter. Verify, do not assume. The drop is a native click injected at a point HD chooses (colonysend); the original's field is the whole cell (Add_Scroll_Field_, coldraw.cpp:409). Sweep: drop at the four corners, the centre, over an existing figure, and on the 1-px plate line, for an empty column and a populated one, on the reference save — Data loads slot 8 first, the tool asserts the save. Same struct diff for every point, one line each. If any point differs, name the rule that refused it (the five in Send_Cluster_) before changing anything.

Part F — the drop delay: measure before optimising

Data sees a delay only on the drop, not on the pick. Log per drop with timestamps: HD click → injection sent → snapshot that shows the new split. Break down what is HD (watchdog, poll interval, snapshot cadence) and what is the game (Get_Input_ takes one input per frame; a pick and a drop are DOWN+UP each, so at least four game frames plus whatever the cluster send costs). Report the numbers on ten drops.

Only after that: if the HD side owns most of it, fix that. If the game owns it, the honest options are (a) accept and record, (b) draw the moved figure in its new cell immediately and reconcile on the snapshot — an HD EXTENSION that must revert visibly if the game refuses (decision 33: nothing may look moved that the game did not move). Propose, do not build, (b).

Small
The hover tooltip ("Workers: 0") in the 1080p picture — is it marked as an HD extension at the three homes? One line.
Acceptance
Headless render at all stored keys and Data's three sizes: the rule check from Part A green.
Screenshots at Data's three sizes beside the original, as questions: do the columns sit inside the frame; do names fit; are the arrows one band tall; are ten rows plated.
Drop sweep on the reference save: identical diff at every point.
Delay numbers on ten drops, HD share and game share stated.
Description panel visible through pick and drop.
Smoke test green; count reported. Nothing pushed.