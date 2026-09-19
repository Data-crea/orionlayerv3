Build the new galaxy frame (work order 133), with the holes cut from
geometry instead of a threshold:

1. Alpha: for each of the ten holes, take the edges you measured on
   the drawing (half-way luminance crossing, sub-pixel) and cut the
   hole as that shape with a 1 px anti-aliased edge. Everything else
   stays fully opaque. No threshold keying anywhere. Master at its own
   generation size (1707x921), no resampling; RGB under alpha 0 set to
   black.
2. Verify: frame_holes.find_holes on the result gives the full name
   set, the six nav holes have equal height and top edge (spread
   ≤ 1 px), and every hole edge is within 1 px of the measured
   drawing edge.
3. Replace screens/galaxy_map/assets/frame.png, run
   tools/frame_holes.py --write, report kept non-cutout boxes.
4. Move sb_research_text and sb_research_icon inside the new sidebar
   opening at every resolution; check nav labels and TURN sit fully
   inside their holes.
5. Same provenance and marking as the previous ChatGPT frame; keep the
   cutting script with the source if v2's keying script was kept.
6. Headless renders at all resolutions into the 133 evidence folder,
   smoke green, one commit. No push.
