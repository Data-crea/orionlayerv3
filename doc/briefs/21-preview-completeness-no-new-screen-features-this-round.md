cd ~/orionlayerv3

Preview completeness. No new screen features this round.

1. tools/colony_list_preview.py currently renders the rows only.
   The sidebar (empire info) and the sort bar are not in it, so
   the two most recent commits have no picture at all. Add both,
   drawn through the same code path the real screen uses -- not a
   reimplementation. If the preview has to fake state to do it,
   fake the state, not the drawing.

2. The sidebar needs values that make its layout falsifiable, not
   plausible ones:
   - a NEGATIVE income, so red-if-negative actually renders
   - a wide value (5+ digits) and a 1-digit value in the same
     column, so right alignment is visible as alignment rather
     than as coincidence
   - Reserve as a stock, Food and Income signed, Research
     unsigned -- the four kinds must be distinguishable in the
     picture

3. Two deviations found in the shipped render, neither marked
   anywhere. Do not change the rendering; mark both:
   - The colony NAME is right aligned. The original draws it
     LEFT: Squeeze_Formatted_Paragraph_Centered_ passes its last
     argument through _Squeeze_Print_Paragraph_ as `justify`, and
     colsum.cpp passes 0 = JUSTIFY_LEFT. "Centered_" is center_y
     only. Re-read this in YOUR 1.60 tree; my line numbers are
     1.31 (colsum.cpp:572, bill.cpp).
   - The per-row second line ("Terran 22/24") has no per-row
     counterpart. Draw_Colony_Scan_Info_ (1.31: colsum.cpp:1119)
     draws size, climate, gravity, mineral class, n_pops, max_pop
     and growth ONCE, for _g_colony_n only, at (13, 354) in the
     bottom-left panel.
   Mark each as HD EXTENSION in the module, in v3_fundament.md,
   and in a smoke assertion, per the marked-inventions rule.
   I want both kept -- this is about the marking, not the pixels.

4. Confirm from source what the row's second line SHOULD contain
   if it stays: the original's panel carries seven values, the HD
   row shows two. State whether the other five are omitted
   deliberately or were never considered, and where they would go
   if the hover band from the design ever lands.

5. Then render the full preview at 1920x1080 and put it next to a
   640x480 original screenshot of the same screen, scaled up, in
   /tmp/colony_list_preview/. Side by side, one image. That
   comparison is the method that found the mislabelled field, the
   misplaced TURN button and the oversized ship icons -- it has
   never once come back empty.

Commit 1-4. Data pushes.