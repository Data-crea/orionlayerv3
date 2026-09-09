cd ~/orionlayerv3

Option 2, split into two numbers.

1. Name column: drawn width = name_width*scale + slack, where
   slack is what list_area has left after building, pad and the
   42-slot track. The TEXT CLIP stays at name_width*scale --
   the ellipsis threshold must be 244 reference px at every
   resolution, not 244..288. Slack becomes gutter between the
   name and the bar, never text budget.
   Nothing written back to layout.json.

2. Revert name_width 236 -> 240? No. Keep 236, but its meaning
   changes: it is now the text budget, not the column width.
   Say so in _name_width_note, and say that the drawn column is
   wider by a per-resolution remainder.

3. Assertions. The current budget check is scale-blind by
   construction -- 1920, 1080 and 1.0 are literals. Replace it:
   - iterate the 12 window sizes from your report, not the two
     boxes.json keys; the fallback chain is what most of them
     go through
   - assert at each: building_right + pad_x == list_area.right
   - assert at each: ellipsis threshold in reference px is the
     same value at every resolution
   Drop the column-sum identity. After 1 it is true by
   construction and cannot fail.

4. Verify both new assertions bite: break the gutter by 1 px and
   break the clip by tying it to the drawn width, and show each
   failing.

5. Then A-F from the sidebar block.

Commit 1-4 including docs, separately from the sidebar work.