Brief 97 ("Colony Summary: the new frame with three bottom windows, the
planet surface art cut from Data's sheet, and the bottom row rearranged as
in 97-mockup.png"), Data's decisions on the Stop 1 report:

1. Names: planet_info / colony_panel / galaxy_inset; planet_output,
   planet_surface, empire_stats as parts of colony_panel.
2. Shortage figure stays as it is (transcribed).
3. Paragraph: keep the original's format and whole-paragraph red. Add
   only a name heading as a text box above it — HD EXTENSION, marked.
   No separate climate line.
4. Fade: both sides; move image-box drawing into core; scale the tiles
   up, Data judges at the Stop 2 screenshot.
5. planet_paragraph honours font_scale — scaled once, not twice (the
   double-scale lesson in v3_fundament).

Execute Stop 2 and stop for Data's look at the tiles beside the sheet.

---

The reported sha256 of toxic and barren share their last 56 hex digits.
Recompute both from the files with sha256sum and paste the tool output
verbatim; if the files really collide, stop.

---

Tiles approved. Execute Stop 3 of brief 97: regenerate cutouts with
--write, the three parts inside colony_panel, the name heading as a text
box in planet_info, retire the four-hole and cartouche remnants in
frame_holes.py, fix boxes.json's missing final newline. Smoke test
green, screenshots at 1080p and 1440p beside 97-mockup.png and the last
native screenshot, then report with the one check that would break a
fresh clone. No push.
