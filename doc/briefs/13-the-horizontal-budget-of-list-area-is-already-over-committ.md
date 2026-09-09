The horizontal budget of list_area is already over-committed for what
is still to come. Measure and decide it as one thing, before the
building column is built.

Reservations today: name_width 330, tail_width 150, pad_x 22x2, from
1408. That leaves unit 19. Adding a building column of ~190 would
leave unit 14, which is below anything legible.

Two candidates for recovering width, both to be judged on rendered
output rather than argued:

1. Move the "No Farming" label out of the horizontal tail and into the
   vertical space that is already free: row_height 62 against
   bar_height 34 leaves 28px unused per row. tail_width then goes to
   0 and 150px returns to the track. The label was moved once already
   after the worker squares painted over it, so re-check that the new
   position survives a full track.

2. Narrow name_width. Measure the widest rendered name plus the
   climate/pop line through Style.render_text rather than guessing -
   the value must hold for the longest colony name the game can
   produce, not for the preview's four rows.

Report the resulting unit for: today, with the label moved, with a
narrower name column, and with a 190px building column added to each.
That table is the decision, and it should live in layout.json's notes
so the next session cannot spend the width by accident.