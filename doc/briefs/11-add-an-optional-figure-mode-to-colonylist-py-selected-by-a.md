Add an optional figure mode to colonylist.py, selected by a key in
layout.json (default off). Same geometry function as the square mode -
the unit, the zone boundaries and the free-slot region must come from
one shared computation, or the comparison compares two layouts instead
of two renderings.

In figure mode a sprite is drawn per filled slot instead of a square,
and the zone colour becomes a 3px rule under the figures rather than a
background fill.

Sprite sizing rule - normalise on HEIGHT, never on width:

  common_height = min over the set of (max_sprite_width * h_i / w_i)

  where max_sprite_width is the step minus the gap. The widest sprite
  in the set therefore sets the height for all of them, and every
  other sprite follows from its own aspect ratio.

  Normalising on width makes the narrowest figure the tallest, and
  makes the whole set resize whenever one new sprite with a different
  tool pose is added.

Measured at a 966px track: step 23, max sprite width 21, common height
26, resulting widths 15 (farmer) / 20 (worker) / 18 (scientist).

Add a guard that fails loudly if the source crops of one set differ in
height by more than 2px. A set whose crops do not share a baseline is
not a set, and the symptom looks like an art style problem rather than
a measurement error.