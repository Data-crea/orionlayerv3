Work order <n> — Which outer frame becomes the one shared outer ring

Number: take the next free work-order number from the tree and rename this file accordingly before filing it under doc/briefs/.

Mode

Analysis only. No frame, screen, layout or check is changed. The result is a report and evidence; Data decides. Single run, questions go into the report, not into stops.

Background

Data wants ONE outer frame for all full-screen views, so every screen looks the same at the edge and that sameness can be checked (decision 55 records that today nothing checks it). Before he builds it, he needs to know which of the existing frames is the best base, above all in terms of sharpness.

Material
The frame images in the tree: every screens/*/assets/frame.png (and any other outer-frame image you find). List each with path, pixel size, origin as far as the tree says (authored, derived, AI-generated) and which decisions govern it (55, 69, 70, 12 and whatever else applies).
Data's screenshots under /home/data/Bilder/Bildschirmfotos/. List what is there and which screen and resolution each shows. They are renders, already scaled — use them for how the frame LOOKS in use, not as the source for sharpness.
Questions to answer

A. Sharpness (the main question).

Native size of each frame against the 1920x1080 reference and the 3840x2160 canvas of decision 70: the scale factor at 1080p, 1440p and 2160p. Which frames are upscaled at 2160p and by how much.
Measured sharpness of the RING only (holes and interior struts masked out), on the source image and on renders at 1080p, 1440p and 2160p. Use a metric you can name and repeat (e.g. Laplacian variance, edge width across a few chosen metal edges); same regions on every frame. State the method so it can be rerun.
Visible artefacts: blur, halos, JPEG-like blocks, AI smearing in the rivets, lights and corner ornaments. Crops at 1:1 and 200 %.

B. Suitability as a shared ring.

Ring thickness on each side, in reference px, and how much content area it leaves.
Symmetry and consistency: are the four corners, the lights and the edges the same, so the ring can be used for every screen? Anything screen-specific baked into the ring (title plate, button rail, struts running into it) that would have to be removed.
The inner edge: clean, straight alpha edge a hole can be measured off, or soft/irregular.
Whether the ring can be cut out of the image cleanly, and what would have to be repainted.

C. Recommendation.

Ranking of the candidates with the numbers behind it.
For the best one: what Data would have to do to turn it into the shared ring (re-export at 3840x2160 from a sharper source, repaint corners, remove the title plate into a variant, etc.). If none is sharp enough at 2160p, say so plainly and what the source would need to be.
Output
Report: doc/briefs/<n>-frame-evaluation.md — tables for A and B, recommendation C, method section.
Evidence: ~/orionlayer-fixtures/evidence/work_order_<n>/ — ring crops side by side per frame at the same spots, renders per resolution. Listed in the report as things for Data to look at, not as findings.
Measurement script, if you write one, under tools/ with a line in the report on how to rerun it. No smoke check in this order.
Commit the report and the script locally. No push.
