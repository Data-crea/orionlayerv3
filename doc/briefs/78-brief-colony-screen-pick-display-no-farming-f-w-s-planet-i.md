Brief — Colony screen: pick display, No Farming, F/W/S, planet_info

Read doc/v3_fundament.md before touching anything. Fundament and CLAUDE.md stay in sync. Two reporting stops before code; Stop 0 is a question, not a task.

Reference save: ab70cc9ad5442335 (stardate 3502.4). Every tool that produces evidence identifies the save first.

Evidence for this round: Data's two screenshots of 7 September, 22:27 — overlay and original of the same screen. They live in ~/orionlayer-fixtures/evidence/ as pick_round_overlay.png and pick_round_original.png; copy them there before Stop 0.

Decisions set by Data (8 September)
Pick: the clicked figure leaves the grid. The row draws without it while it hangs on the cursor. Observed at the original; Stop 1 confirms it from source, it does not replace it.
No Farming: as in the original — centred in the column, not under a button.
F/W/S buttons: removed.
planet_info: the empty left panel takes the planet description (the six rows now on the left of the planet_output table: size, climate, gravity, minerals, population, growth). planet_output keeps the production rows. Whether the description renders as sentences like the original or as label/value is decided by Data from the screenshot beside native — put both up if cheap.
SORT label: not this round.
Yellow cell frame and blue row frame: the original shows neither during a pick. They fall unless Stop 1 finds a row marking in the original.
Stop 0 — same game state?

Between the two screenshots Draconis III moves from all-farmers (overlay) to all-workers (original), and Horus IV differs too, while Reserve, Population and Research agree. Either Data moved population between the shots, or the overlay assigns a column wrongly.

Answer from the struct, not from the pictures: load the reference save, read the pop record of Draconis III through core/structs, and state what the overlay renders for that row from the same snapshot. One line each. If they disagree, that is the first task and everything below waits.

Stop 1 — source (report, no code)

Function and line in coldraw.cpp / colmove.cpp for each:

Cluster pick: one figure or the whole slot? What decides it.
Row during pick: which function draws the row with count − n, and does the squish pitch come from the same geometry as at rest? If it is a second computation, name it — that is a Fundament-5 case before anything is transcribed.
slot_at during pick: does the hit test count the shortened row or the full one? This decides where a drop into the same row lands.
Cursor figure: offset from the cursor tip as a number, with source. The screenshot shows the figure over the cursor, not beside it.
Drop target: with F/W/S gone, what does the original accept as a drop into an empty column — the cell rect, the row, something else? Name the rect the original tests.
Row selection: does the original mark the selected row at all? If yes, how and where; if no, say so and the blue frame falls.
No Farming: position and font size in the original, with source, so the placement is a transcription and not a layout choice.
Side question (Fundament 25, cheap): does the building cost table live in an LBX like techname, and is production accumulation on the wire in the colony struct? Yes/no each. This decides whether the - 1t suffix is an extraction or a request to Joes. No work on it this round.

Stop and report. Data decides the row frame and the drop rect from the report.

Stop 2 — implementation and acceptance
Cursor figure drawn at the sprite step of the current resolution; swap, never scale. A check reads the step from the files, as the row check does.
The row draws with count − n from the same geometry function that serves render and hit test. No second pitch.
slot_at behaves during a pick as Stop 1 found, and a check fails if a pick leaves it counting the resting row.
Live PICK/DROP proof against the reference save, including a drop into an empty column and a drop back into the source row. The tool names the save.
F/W/S removed. Their click targets are re-established by construction on the rect Stop 1 named — not by keeping invisible buttons. Any HD EXTENSION marker they carried is retargeted in the same commit (the marker checks).
Yellow cell frame deleted, blue row frame per Data's decision after Stop 1; markers retargeted in the same commit.
No Farming centred in the column, size from Stop 1, DEVIATION marked only if the HD column width forces one.
planet_info: description on the left, production on the right, words from the estrings word list per the word-list rule (label carries the prefix, the value does not). _geometry_note in layout.json updated if a box moves.
Screenshots beside native at 1920×1080, 2560×1440, 3840×2160, as questions: does the figure sit relative to the cursor tip as in the original; does the shortened row squish as the original does; does No Farming sit where the original puts it; does the left panel read like the original's.
Smoke test green; report the check count.
Not this round

SORT label; the round detail button per row (record as deliberate omission at the three homes); - 1t suffix beyond the Stop-1 question; the 68 double-scaling boxes on four other screens — enter them as known-wrong in v3_projektstatus.md today.