Brief — Colony frame: strut bevel, preview, provenance

Follows d188908. Three stages, two reporting stops. Nothing deleted, boxes.json untouched, frame_holes.py --write not run — both wait for the commit that makes the new modules default.

Stage A — bevel from the master

Goal. Every cut window in the built colony frame gets the master's own light edge, so struts read as structure the way the master's do. No invented pixels: every pixel around a hole comes from galaxy_map/frame.png.

Method. Per-hole 9-slice. Sample the master's window edge — the bevel strip around one of its own holes — as four edge pieces and four corner pieces. For each cut window in the colony plate, lay the corners once (scaled once with the plate, like the ring corners) and stretch the edges along their length only, exactly as the plate's nine-cut already does for the ring. Same code path where possible; if a second implementation is needed, say why — the third copy is the signal to extract, and this would be the second.

Which edge to sample is found, not named, same rule as the strut patch: the master hole whose bevel is stable across all four sides (measure the strip's luminance profile per side; pick the hole where the four profiles agree best). Report which hole was chosen and the profiles.

Where the bevel is too wide for the gap. Two adjacent windows in the lower band may sit closer than two bevel widths. Report each gap against the bevel width; do not narrow the bevel to fit — if it does not fit, that is a layout number to change in layout_reference.json, and it goes to the stop.

Acceptance.

frame_cut window check still passes: every window fully transparent at all three resolutions.
Ring equality check unchanged and green.
New check: for each hole, the four bevel strips are present (measured as a luminance ridge along each edge, not as "ink drawn").
Masks, plate and holes regenerate byte-identical from layout_reference.json + master.

Reporting stop A. Comparison image at 1080p, at 2×: built plate / current colony frame / native screen. Plus the bevel-fit table. Stop before anything else.

Stage B — preview switch

Only after Data has seen the Stage A image and says go.

Goal. See the built plate in the running game without touching boxes.json or the screen's box list.

Method. A flag (--frame-preview <path> or an env var, your call, but one mechanism) that makes the colony screen blit the built plate instead of the shipped frame.png and nothing else. Boxes, hit-tests, panels stay exactly as today — content will sit wrong under the new holes, and that is expected: this previews the frame, not the layout. Say so in the log line when the flag is active, every session, so a screenshot with it on can never be mistaken for the real state.

Acceptance. Flag off → byte-identical rendering to today (assert in the smoke test with the flag forced both ways). Flag on → the plate is drawn, the log says PREVIEW.

Stage C — provenance and status

Derived or asset. The built plate is reproducible from two inputs: the family master (committed) and the mask (generated from layout_reference.json). Under Decision 40 that makes it derived: generated, never committed. Today colony_summary/assets/frame.png is a committed asset. Propose one of:

the three variants are gitignored, the smoke test builds them, and a fresh clone works because both inputs are in the tree; or
they are committed as assets, with frame_build.py as the regenerator and a check that the committed file equals the regenerated one — the frame_holes.py pattern.

Say which and why; do not do both. This is a decision for Data, so it goes to the stop with your recommendation, not as a fait accompli.

Status document. Dated entries: 1440p and 2160p are upscaled interim variants of a 2322 px family master; the fix is a family master ≥ 3840 wide, listed under horizon, not under colony-screen debt. boxes.json still carries 451×203 and the old holes — the existing dated entry stays until the swap commit.

Fundament. Not in this brief — the sentence about ring-from-artwork, windows-from-layout, boundary-measured goes into the follow-up commit with the two paragraphs already queued (palette lesson, percentage-is-the-transcription).

Reporting stop C. Commits listed, checks count, the derived-vs-asset recommendation, and the exact list of what still waits for the swap commit.

Not in scope
No image-model polish. If Stage A's bevel is not enough, that is a separate decision with the Stage A image in hand.
No boxes.json swap, no frame_holes.py --write, no deletion of old presentation modules.
No Stage 3 work (sprites-assets stop, squish transcription, loader chain). Those start after the frame is accepted.