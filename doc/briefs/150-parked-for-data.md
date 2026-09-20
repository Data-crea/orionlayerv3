# 150 — parked for Data

## 1. The work order is unnumbered — third time

Same as 148 and 149: *"rename this file to match"*, and it arrives as
a paste, so there is no file here to rename. The number is 150.

148's and 149's parked files both raised it. One instruction — either
"file every work order under `doc/briefs/<n>-work-order-*.md`" or
"don't, the number in the brief is enough" — settles it permanently.

## 2. 155 field calls could not be resolved, and that limits the exact half

Of 279 `Add_*_Field_` calls across the eighteen screens, **124 gave an
exact rect and 155 did not.** They are listed per screen with their
call site and reason, but it means the solid-line half of several
wireframes is thin: Ship Design drew 10 of 42, Officers 2 of 17,
Info Library 0 of 13.

The reason is not laziness in the parser — it is that the original
computes most of its rects at run time, in loops over rows and
columns. Getting them would mean **executing** the layout rather than
reading it: either instrumenting a build of orion2re to dump the field
array per screen, or reading the live field list over the Extension
API, which OrionLayer already receives.

**The second is cheap and would make every screen's exact half
complete.** It needs one live run per screen with the port free. Say
the word and it is a small order.

## 3. The traced half is interpretation, and two screens got nothing

`galaxy_map` and `tactical_combat` traced **zero** dark wells at every
percentile in the sweep. That is the right answer rather than a
failure: the galaxy map's content sits on a starfield and the combat
screen's on a tactical grid, neither of which is a well. But it does
mean those two wireframes are the thinnest in the set, and for the
galaxy map what carries the layout is the single transparent cutout
plus its 18 exact fields.

If you want those two fuller, the honest route is the live field list
above, not a looser trace threshold.

## 4. Class assignment is mine, by size, and is the weakest thing here

Each box is coloured by class, and the class is decided by a size rule
I wrote: 600x440 or larger is a screen frame, 150x120 or larger is a
grouping panel, 150 wide and short is a list area, buttons are anything
added by `Add_Button_Field_`. Everything else is "field (unclassed)".

That rule is not from the catalogue and not from the source — it is a
convenience so the drawings have colour. The **geometry** in every
table is sourced and traceable; the **class** on that row is my guess
from its dimensions. Where a class matters to the kit decision, read
the size, not the colour.

The 20 Fleets grid cells are the clearest example: they come out
"field (unclassed)" at 56x54, when they are plainly a list area's
cells.

## 5. One thing I did not do

The order says labels must stay readable and "where boxes are too
small, number them and put the details in the table". I numbered
**everything** — F1, F2, … for exact and T1/C1, … for traced — rather
than labelling large boxes by name and only numbering small ones. It
is consistent and the tables carry the detail, but it means you cannot
read a box's name off the picture for the original's screens. The HD
wireframes do carry real box names, because `boxes.json` has them.

If names on the original's wireframes would help, the field calls have
no names to give — only the hotkey and the call site — so it would be
the call site, e.g. `flt1.cpp:1187`, drawn in the box.
