Two things from the render review:

1. The per-row detail line is an invention and needs its own marker.
   The original prints climate and n/max only for the selected colony,
   into the bottom-left detail box at native (13, 354, 80, 88), via
   COLSUM::Draw_Colony_Scan_Info_ (colsum.cpp:1155) with
   ESTRINGS::E_Strings_(74). The rows carry name and nothing else.
   Showing it on every row is an HD extension of the same family as
   the allocation bar - it makes comparable what the original could
   only show one at a time. Mark it where the bar is marked, and have
   the smoke test assert the marker, so it cannot silently vanish.

   Note while you are there: colony->climate is what the original reads
   too, so that choice is now source-backed, not reasoned. Worth
   recording.

2. Check where the ten climate ESTR ids came from. The original does
   not look up ten strings - it indexes MOX::_planet_climate_string
   with climate_idx. If those ids are a second, independently written
   copy of the same table, that is the screen-ID-map failure again.
   Either confirm the provenance or key off the table index.

Then measure the building column for real: the widest producing string
the game can emit, through Style.render_text at the row's font size,
plus the buy button - not 13.3% of 640 scaled up. The original's 85px
held a five-pixel bitmap font; Aldrich at HD size is a different
object, and this is the nebula-size trap in a new costume.