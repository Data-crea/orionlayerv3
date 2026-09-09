_Squeeze_Print_Paragraph_ (bill.cpp) settles the building column: the
width is hard and the text bends. It wraps into the width, then shrinks
space width, then leading, then one font style down. It never
truncates. So 85 of 640 IS a width reservation, and 190 of 1408 is the
correct transcription of it. What was measured - widest string, one
line, full font - is a requirement the original never imposes.

Build the column at 190, two lines, small font: name on the first,
"- 8t" plus the buy button on the second. Row height 62 against bar
height 34 is the same vertical reserve that freed tail_width, and the
original does exactly this in its own (13, 354, 80, 88) box.

Transcribe the behaviour, not the three steps: wrap, then reduce size
until it fits, never truncate. The space-glyph narrowing is a bitmap
font trick with no Aldrich equivalent.

Then re-open name_width. It was rejected at 230 because the name
overprinted the track - under left alignment. Right alignment sends
overflow left into pad_x instead, so the render that refused it no
longer applies. Measure 240 against the realistic range (the running
galaxy's widest is 124px) and keep the 336 structural maximum as the
ellipsis case, not the reservation.

Report the unit for each combination and render it.