Work order (next free number) — New frame set of 18 Sep: assign and integrate

Read doc/v3_fundament.md first, as always. Check the next free work-order and decision numbers before filing anything.

Goal

Data wants a graphically uniform frame look across the HD screens. Chat has produced four frame images from ChatGPT renders and given them real alpha.

Data has delegated the assignment to you: you check yourself which frame belongs to which screen, and you build it. There is no reporting stop. Nothing is pushed, so Data's check is the diff review plus the side-by-side images before the push. Anything where no asset fits cleanly, or two readings are equally good, goes to doc/briefs/<n>-parked-for-data.md instead of being decided by taste.

Inputs

The files are in ~/Downloads/. Copy them first to ~/orionlayer-fixtures/incoming/frames_18sep/ and work from that copy only. Check that the copies are byte-identical to the originals (sha256).

File    Chat's description (re-measure, do not trust)
frame_map_sidebar.png    1920x1080, large left opening, right column, three bottom fields, three stacked rows bottom right
frame_map_4panels_7buttons.png    1920x1080, one large opening, four bottom fields, seven dark button plates, dark title plate top centre
frame_plain.png    1920x1080, one opening, dark title plate top, two dark plates bottom left/right
panel.png    native size, horizontal panel with mid-edge brackets, intended for popups/smaller boxes
key_frames.py    the script Chat used to turn a painted checkerboard into alpha

What Chat knows about them. These are properties to verify, not findings:

The three large frames were generated at about 1670–1683 px wide and not exactly 16:9. Chat scaled them to 1920x1080, which stretches them by about 1–2 %. At 2160p they will be soft.
The openings are hand-drawn, not constructed. Stroke widths and gaps vary by several pixels between fields that look the same. Because of decision 3, these irregularities would become box coordinates.
The seven button plates and the title plates are opaque dark areas, not holes. frame_holes.py will not see them.
panel.png has brackets at the middle of each edge. Stretching it as a 9-slice would distort them (decision 12).
Part A — read, measure, assign (before any change to the tree)
Inventory. For every screen and overlay, record how it is framed today: frame image with cutouts, plain-scaled frame image (as in decision 69), inner_panel / thin_border, or nothing. Include the screens that have no frame yet, such as research_select.
Measure the new assets. For each one, list its openings and plates at every supported resolution, using the scaling mode the candidate screen would apply. Report the irregularities in numbers.
Assignment. Build a table of asset → screen(s) or "no fit", each with a reason. Write it to doc/briefs/<n>-frame-assignment.md. Compare against the boxes each screen actually needs: count, aspect ratio, and the cutout names from decision 3. Two questions to answer explicitly, not to assume:
Can frame_map_sidebar.png replace the galaxy map's current frame, given how the nav_* boxes are derived today?
Can the seven plates of frame_map_4panels_7buttons.png carry the seven nav buttons, given that they are not holes? Assignment rules: fit by opening count, aspect ratio and the boxes the screen needs, never by looks alone. A screen that already has a frame is only switched if the new one fits at least as well; otherwise park it. An asset that fits nowhere stays unused and is reported as such.
Consequences. For each assignment, state what changes in boxes.json, which F5-placed boxes would end up outside an opening, and what the smoke assertion "cutouts agree with frame" would say.
Side by side. Render each assignment headless to PNG, next to the current HD screen and a native screenshot of the same screen. Put the images under ~/orionlayer-fixtures/evidence/work_order_<n>/.
Provenance. Decide where the frame sources and key_frames.py belong in the tree, following how the earlier ChatGPT frames were handled. Give them the same marking as HD artwork.
Part B — build the assignment
Build one screen per commit (one package per screen).
Regenerate cutouts with tools/frame_holes.py --write. Report the count of non-cutout boxes it kept.
Do not fix irregular openings in the artwork yourself, and never compensate in code. Report them with numbers and park the question of whether to straighten them.
Run the smoke test after every step. The pre-commit hook must pass.
No push, no orion2re change, no change to core/zoomtables.py.
Leave the panel-skin meanings of decision 34 unchanged. If panel.png would require changing them, park it.
Final report: assignment table, commits, smoke count before and after, evidence path, parked items.
Record the result in the status document, and in the fundament only if a decision was actually made or reversed.
