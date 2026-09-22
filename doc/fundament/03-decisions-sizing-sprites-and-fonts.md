# The fundament, part 3 of 9 — Sizing, sprites and fonts

Sizes, sprite steps, tints, rotation and fonts — and the two entries about who owns a rule that the artwork decisions rest on.

**Decisions in this part:** 26, 27, 28, 29, 30, 32, 49, 53, 54.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
### Sizing and artwork

**26. All sizing comes from `core/zoomtables.py`.** Icon dimensions,
font scales and zoom levels are transcriptions of orion2re's own
tables. Changing a number there is a deliberate deviation and must be
marked as such — as must a whole *function* the original has no
counterpart for. `hd_zoom_level` exists only because the decoupled HD
viewport produces scales between the rungs the game can stand on, and
its docstring says HD EXTENSION, NOT TRANSCRIBED in as many words. It
is built to agree with the transcription on every rung, so the
deviation is confined to values the original cannot produce.

**Including sizes an asset appears to carry.** Nebula footprints were
derived from the HD master's pixel width divided by the export scale
— correct exactly as long as every master stayed at that scale, and
wrong by 3.3x to 4.1x, differently per type, the day new artwork was
drawn at its own working resolution. Artwork carries a shape, never a
size; `NEBULA_DIM` carries the size.

**27. Derived tables say so in the table.** `SHIP_ICON_DIM` and
`MONSTER_ICON_DIM_ZOOM0` are *not* transcriptions — those sizes live
in BUFFER0.LBX and are only read back at runtime. The evidence is
written out in `doc/ship_icon_measurement.md` and the comment says
DERIVED. A number nobody can trace becomes a number nobody dares
change.

**28. Sprites are swapped by step, not scaled.** orion2re ships six
pre-rendered sprites per star class and indexes them with
`zoom_level + star.size` on one axis; four per ship colour indexed by
zoom. HD artwork follows the same structure, so a single step can be
replaced by hand without touching code.

**ONE EXCEPTION, AND IT IS MARKED — 12 September 2026, Data's
decision.** The colony list's population figures are drawn at a
FRACTIONAL size where the band is far from a multiple of the step:
the step is the largest integer that fits, and at 2560x1440 and
3440x1371 the band is 77 and 73 px against a 56 px figure, so a
quarter of every row was empty. The size is the band less the plate's
own line, taken only when that buys at least a quarter of a master row
(`colonytrack.figure_size`, `FIGURE_SIZE_SNAP`), and it is nearest
neighbour — so every colour is still exactly the game's and what
breaks is the pixel GRID, invisible at 1:1 and visible in a 3x zoom.
Below that threshold the integer step stands and the sprite is bit for
bit what this decision always drew, which is the case at 1920x1080 and
3840x2160 and is asserted rather than assumed.

**The half of this decision that did NOT move is the one the modder
sees.** A step is still an integer, `@2x.png`/`@3x.png`/`@4x.png` is
still the contract (decision 50), a wrong-sized file is still refused,
and a fractional size is reached BY SCALING THE STEP BELOW IT — so a
hand-drawn `@2x` is what gets stretched rather than being passed over
in favour of the master it was drawn to replace. The alternative that
keeps the grid even, an integer step up and a smoothscale down, blends
the colours and was rejected on the side-by-side.

**29. Player colours are tinted at runtime, never baked.** One
greyscale sprite, eight tints — mirroring what the original does with
palette-swapped LBX entries. Exports are forced to true luma so
resampling ringing cannot leave a coloured pixel to survive the
multiply.

**32. Runtime rotation needs a fiducial on the axis, and artwork
built for it.** The black hole is one drawing turned at runtime rather
than a frame sequence, for the same reason as 29: one master, many
states. That only works if the artwork is a square whose content fits
its inscribed circle and whose event horizon sits on the centre —
otherwise the sprite orbits instead of turning, or loses a corner.
`tools/make_black_hole_master.py` enforces all three and refuses to
write a master that fails; the smoke test re-checks them against the
shipped asset. Rotate with `rotozoom`, never `rotate`: the latter does
not filter, and centre by surface size with `round`, never `//`.

**49. The colony frame plates are DERIVED, and both halves of that
word are part of the decision.** `tools/frame_build.py` nine-slices
`screens/galaxy_map/assets/frame.png` into three plates
(1920x1080, 2560x1440, 3840x2160) under
`screens/colony_summary/assets/frames/`. They are not committed. Both
inputs are — the master and `layout_reference.json` — so a rebuild
reproduces all three byte for byte, and a smoke check asserts exactly
that rather than trusting the tool's existence (decision 40, whose
`stars/` lesson was this mistake in the other direction).

**SUPERSEDED FOR THE COLONY SCREEN — 12 September 2026, decision 55.**
There are no derived plates on that screen any more: it wears one
fixed image and its rectangles are measured off it. Everything below
is the record of what was built and why it was right at the time; the
machinery it describes is deleted. This entry still stands for
anything else that becomes a derived file — the byte-for-byte rebuild
IS the licence, and that part did not change.

**Committing them was the alternative and it was rejected on
history, not on taste.** As an asset the plates would render in a
clone that had not run `tools/setup.py`, which is the whole of what
that option buys, and the preview is off by default so nearly nobody
would collect it. The cost is permanent: git stores images as whole
blobs rather than diffs, the three plates are 3.6 MB, and the master
is *expected* to be replaced by a >=3840 family master. Every future
revision would leave another full copy in the history forever, to
save 1.7 s that `setup.py` already spends. Derived changes ONE
committed file when the master changes; asset changes four.

The measurements the decision was taken on: the plates rebuild in
1.66 s for all three, the smoke suite **already builds them in
memory** on every run, so the byte-for-byte check costs **0.28 s** on
a 27 s suite — the licence for the word "derived" is close to free
here, which is not true everywhere and is why it is worth writing
down that it was checked.

**Two conditions are part of the decision, not follow-up work.**
`frame_build.py` is a step in `tools/setup.py`, because a derived
file with no step in the setup run is one a clone can never get —
which is what the tree actually had for a day, gitignored as
"generated" with nothing that generated it. And the check **reports
absence rather than skipping**: no plates means it names the command
and still counts, so "the check count must not go down" stays a rule
anybody can follow (decision 42's pattern, second use).

**Amended 7 September 2026, Stage 4: `frame_preview` ships ON and
its name is backwards.** This entry was written while the flag was a
preview and flag-off was the shipped screen, byte-identical to what
the tree had always drawn. That is no longer what off means.
`boxes.json` is generated from the plate's own holes now, so the
plate IS the colony screen's frame; turning the flag off draws the
SUPERSEDED artwork over boxes it does not fit, and the class A
checker measures that as 5822 glyph pixels under opaque frame alpha
at 1080p and 31654 at 2160p. The old frame and the flag are kept
together for one stage so the two pictures can be compared, and
**Stage 5 deletes both in the same commit.** Until then the
byte-identity that is still asserted is the SUPERSEDED surface's, not
the shipped one's — a check that the fallback stays honest while it
exists, which is a different claim from the one this paragraph
originally made.

**30. Blocked font glyphs are detected, never listed in code.**
`Style.blocked_glyphs()` finds the characters a font maps onto one
shared bitmap and substitutes the proportional font for exactly
those. Hardcoding the DEMO list would mean a licensed font keeps
splitting strings forever. Any text that can contain game or user data
goes through `Style.render_text`, not `get_font(...).render`.

Consequence for anything that *measures* text: measure by rendering.
`render_text` can mix two fonts inside one string, so a single font's
`.size()` is not the width that will be drawn. The message popup's
word wrap does exactly that and caches the result per
(text, pixel size, width).

**53. A layout rule we CHOSE is Data's to change; a rule TRANSCRIBED
from the original stays a check.** 11 September 2026, when the colony
screen's top and bottom band were freed so a new frame could be
drawn. The suite had grown to hold both kinds at the same strength,
and that is what made the artwork unmovable: a picture could not be
redrawn without breaking assertions that were never about MOO2 at
all.

The test is the SOURCE REFERENCE, not the feeling. A transcription in
this project carries `file.cpp:line`; an invention or a deviation
carries its label. A rule with neither is ours, and ours means Data's.

**THE PRINCIPLE STANDS; ITS EXAMPLES ARE GONE — 12 September 2026,
decision 55.** Both tables below name `_gaps_note`, `_ring_source`,
`frame_mask` and `tools/colony_frame_check.py`, and all four were
deleted with the plate machinery. Nothing about the RULE changed —
a rule we chose is Data's, a rule transcribed from MOO2 stays a check
— and the four dropped enforcements stayed dropped. What replaced the
last line of the second table is stronger and is in 55: every window
must sit inside its OWN hole of the artwork, measured against the
alpha at three resolutions, which also catches a window inside the
metal but over the wrong hole.

**Chosen — dropped as checks, still reported every run:**

| rule | where its origin is written |
|---|---|
| lower band flush with `list_area`, left and right | `_lower_band_note`: our own eye; MOO2 has no band of four panels |
| the band's three gaps equal | `_lower_band_note`: "THE MASTER'S OWN SLOT DIVIDER" — our artwork |
| every gap equal to its role's strut | `_gaps_note`: our master's struts, and it records that the original's own gaps are ~3 and ~12 ref px, so the rule is WIDER than what it deviates from |
| `ring` pinned to `galaxy_map/assets/frame.png`, and the built plate's ring pinned to that table | `_ring_source`: measured there "because that is what this screen has to sit beside" |

**Transcribed — still checks:**

| rule | source |
|---|---|
| every hole inside the ring | not a preference: a hole outside the metal is a hole in the edge of the screen. The DERIVED form stays asserted — the built metal reaches exactly as far as the rectangles put it — and only the pin to the typed table went |
| `galaxy_inset` aspect | movebox.cpp:20-21; the coverage is 128*(506000//128) by 91*(400000//91) and the galaxy size cancels |
| inset minimum height | `colonyinset.map_rect` fits 128:91 isotropically; below `w*91/128` the height binds and the map gets panel either side |
| figure column >= 4 unsquashed figures, all three resolutions | the original's widest column — industry, reach 122 at pitch 30, colsum.cpp:1006-1024 for the bounds |
| list height -> `figure_step` | band >= `28*step + 1`, measured off the 54 figure masters' own ink |
| hole alpha exactly rectangular; hole rect == `frame_mask` rect | decision 3's chain, and a soft rim would make a hole's size depend on where the threshold sits |

**A DROPPED CHECK BECOMES A REPORT, NEVER A SILENCE.** `smoke_test.report()`
prints the measured value with no pass/fail and does not touch `PASS`,
so a band that drifts is still visible in the output and the count the
two documents are held to stays honest. And an enforcement that leaves
the suite has to arrive somewhere: `tools/colony_frame_check.py` holds
the surviving rules against a PNG, which is where they can actually
meet Data's file. The suite cannot do that job and should not try —
*"Data's artwork is not in the tree and never will be"*, and a check
that needed it would fail for anyone who cloned the repository.

**WHAT THIS ENTRY DOES NOT LICENCE.** Dropping a check because it is
inconvenient. The four above were each traced to a sentence already in
the tree saying where the number came from. Two further rules turned up
in the same session that block the same work and were NOT dropped,
because their origin is not marked either way and deciding that is not
a session's call — they are named in the status document under the same
date, which is the shape a rule of unknown parentage gets: written
down, not resolved in passing.

**54. The artwork may take a division back off the code, and a
reversed decision is written down as a reversal.** 12 September 2026,
when the seven sort keys became seven boxes again. This is the DEVIATION
this entry exists to record, and what it deviates from is decision 53's
own principle applied one level up: Stage A3 read the original
correctly and drew the wrong conclusion for OUR frame.

**What Stage A3 decided, on 7 September 2026, and why it was right
about the original.** MOO2 draws its seven sort keys inside one
recessed blue strip, native y 446..469, with the words laid along it —
`Add_Multi_Button_Field_(x, 446, …)` seven times at colsum.cpp:267-273.
So the plate cut ONE `sort_bar` hole and `colonysort.layout`
distributed the keys along it: *"the division lives here rather than in
the artwork"*. Nothing about that reading of the source has changed and
nothing in it was wrong.

**Why it is reversed.** The reading answered a question about MOO2 and
was applied as an answer about our frame. Data's artwork cuts a slot
per key, and where a hole is, is not ours to decide — it is decision
3's whole chain (`layout_reference.json` → mask → plate → `boxes.json`)
and decision 53's "a rule we chose is Data's". A screen with seven
holes and a module that divides one bar would have had the division in
two places and neither would have owned it.

**What it costs, stated rather than discovered later.** The even gaps
`colonysort` computed are gone, and they were the one thing in that
module marked as a READING rather than a transcription — so what left
is what was already labelled as ours. The `native_click` points, the
hotkeys, the highlight at word width plus pad, the PRODUCING dimming
and the typography deviation are all unchanged: they are transcriptions
or marked deviations, and none of them was about where a button sits.

**And the naming stopped being an index, which is the part that
generalises.** Two holes in a row can be named left to right; eight
hand-placed ones cannot, because the failure is silent — two slots
exchanged in GIMP give a frame where PRODUCING sorts by science and
every other thing on the screen is still correct. This project already
paid for that once (`frame_holes` had the last two bottom panels the
wrong way round for a fortnight, `layout.json`, `panels._note`). So
`frame_holes` matches a hole to a `layout_reference.json` rectangle by
OVERLAP, rejects a match that is not a clean bijection, and says which
way it went. **The rule: a plate whose holes are placed by hand is
named by geometry, never by order.** The row SHAPE stays a check — it
is what still catches a RETURN that has drifted into the band.

**Two things the artwork could not have and the tree decided.** The
seven initial rects are measured off the superseded 14-hole colony
frame, because the galaxy master's bottom edge carries SIX slots — its
nav row — and there was no seventh to read; and where a slot met
something fixed, the slot gave way, never the fixed thing. `sort_bc`
ran 121 ref px into RETURN and is 57 px wide instead of 195; the row
ran 4 px past the ring and lost 4 px of height. Both are in
`_sort_slots_note` with their arithmetic. **Shrink the slot, not the
thing that is checked** — RETURN's position and "every hole inside the
ring" are both on decision 53's transcribed side.

