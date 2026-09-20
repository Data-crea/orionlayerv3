# 149 — parked for Data

## 1. The work order is unnumbered, again

Same as 148: it says *"put it in the title above, and rename this file
to match"*, and it reached me as a paste, so there is no file here to
rename. The number is 149 and it is in the catalogue's title.

148's parked file raised this; if work orders should go back to being
filed under `doc/briefs/<n>-work-order-*.md` the way 142 and earlier
were, say so once and it applies from then on.

## 2. Border thickness could not be measured reliably, and that is load-bearing

Part A marks most of the original's border thicknesses UNCONFIRMED
after five methods. This is not a gap to be closed by more effort:
the pieces are illustrated chassis with irregular outlines, internal
shading and often more than one well, so there is no single thickness
to find.

**It matters for the decision.** Option 3 in Part B is "write a
specification and a checker". A checker of the kind
`tools/make_black_hole_master.py` represents can only test what can be
measured — and border thickness on finished art of this sort is
exactly what could not be. If you pick Option 3, the checker will be
able to test canvas size, transparency, hole positions and palette,
but **not** "is the border 12 px on every side", which is the property
the option exists to enforce.

## 3. What I did not do, and would need a word on

**Per-class measurements of the baked panels.** Classes 2, 3 and 4
(grouping panel, picture frame, list area) have no standalone art, so
measuring them means measuring regions *inside* the 640x480
backgrounds — picking where each panel is, by hand, on fourteen
screens. That is a real piece of work and it is interpretation:
deciding where a painted panel "starts" is the same judgement the
order forbids when it says not to cut frames out of backgrounds. I
counted them as classes and left them unmeasured rather than invent
boundaries.

If you want those numbers, the honest way is to name the panels you
care about on two or three screens and have them measured against a
stated edge rule — a smaller, answerable question.

## 4. Two things in Part B that are judgements, not findings

**a. "Effectively never reused" for buttons.** The measurement is that
eight of the ten commonest button sizes occur in one screen folder and
two occur in two. Same *size* is weaker evidence than same *art* — two
screens could share a size by coincidence. I did not compare button
pixels across screens for actual duplicates. If that distinction
matters to the decision it is a cheap check.

**b. The dialog class being "the only shared box art".** That comes
from 147's reading of `GENDRAW`/`User_Box_` callers, not from
comparing the files. GSTAR.LBX and RACEICON.LBX are also shared, but
they are icons and pictures, which this order puts out of scope.

## 5. Option 2 discards accepted art

Worth stating plainly before a decision: Option 2 — one kit,
no per-screen frames — would retire the five frame images now in the
tree, including the ring you accepted by eye. Nothing about the
catalogue says that is wrong, and it is the only option where a new
screen costs no art at all. But it is the one choice here that throws
away work rather than adding to it, and that seemed worth naming
rather than leaving inside a trade-off table.
