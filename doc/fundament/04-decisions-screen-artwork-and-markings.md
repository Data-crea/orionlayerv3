# The fundament, part 4 of 9 — Screen artwork and markings

One screen, one frame image: the per-screen artwork decisions, the display settings, and the marking vocabulary.

**Decisions in this part:** 55, 56, 58, 61, 63, 64, 65, 66, 67, 68, 69, 71.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
**55. The colony screen wears ONE FIXED IMAGE, and its rectangles
are measured off it.** 12 September 2026, Data's decision after seeing
all three paths rendered. **This supersedes decision 49 for this
screen** — there are no derived plates here any more, and nothing is
generated on this screen at all.

**SUPERSEDED IN APPEARANCE — 25 September 2026, decision 71.** The image
is no longer drawn. The rectangles stay where they were measured off it,
and each window is a HUD panel now.

**What 49 said and why it stops applying.** Decision 49 made the
colony frame a DERIVED file: `layout_reference.json` rendered to a
mask, the mask nine-sliced out of the galaxy map's master into a
plate, the plate cut, and `boxes.json` measured back out of the
plate's own holes. The licence for calling that derived was a
byte-for-byte rebuild, and it held. What it could not do was BE the
picture Data wanted: the rim was the master's lit edge with flat
corner tiles, so c5977cf's "the sort bar's rim cannot be rounded"
was a verdict about the machinery and not about the drawing, and the
rails only covered gaps `frame_master.struts` could see as
rectangles between facing windows.

**What replaces it.** `screens/colony_summary/assets/frame.png`,
authored artwork, committed, scaled to the reference area and
blitted. Every rectangle in `layout_reference.json` is one of its
holes. `tools/boxes_from_reference.py` writes `boxes.json` from that
file plus `BLEED` and `colonyplates.reseat` rebuilds the same rects
at every load, so the written file is a cache and never the
authority — which is the fault this project walked into on the day
it became possible, a reference edited without running the tool
leaving yesterday's fills behind today's frame.

**DECISION 3 IS NOT WEAKENED, IT IS SHORTER.** Its guarantee was
that the holes, the mask and the boxes all say one thing. The mask is
gone because the artwork is no longer generated FROM the rectangles —
it was drawn first and they were measured off it — so the chain is two
links. What holds them together is stronger than what it replaces:
every rectangle must match a transparent hole by OVERLAP, the match
must be a clean bijection, and every window must sit inside its own
hole at all three shipped resolutions, measured against the alpha. The
ring — one rectangle standing for the whole artwork — is gone with the
master it was measured off; "a hole is not a hole in the edge of the
screen" is now asserted per hole, which also catches a window inside
the metal but over the WRONG hole, which the ring never could.

**THE ORDER OF WORK REVERSES, and that is the real change.** It was:
type a rectangle, regenerate the plate, look. It is now: draw the
frame, and move the rectangles to its holes. `tools/frame_holes.py`
prints what a new frame's holes would be called and which of them
nothing claims; the geometry follows the picture instead of the
picture following the geometry.

**WHAT IT COSTS, ON RECORD.** The colony screen no longer wears the
same border as the galaxy map, and nothing checks that it does. The
list is shorter than the Stage-A3 cutout, so 2560x1440 draws its
figures at sprite step 2 where it drew them at 3. One hole — the
pre-Stage-4 title cartouche — is claimed by nothing and shows the
background. All three are measured, all three are in
`v3_projektstatus.md`, and none of them was discovered afterwards.

**FOUR PARKED ITEMS CLOSE AS SUPERSEDED**, not as done:

| item | why it is closed |
|---|---|
| corner tiles | `frame_master.bevel_source` and the four flat tiles are deleted. There is no nine-slice to give a corner to. |
| per-hole bevel | wanted so the sort bar's rim could be rounded without rounding every window; the rim is the artwork's now and each hole already has its own. |
| master >= 3840 | the master was needed because the plate was assembled from it and upscaled; nothing is assembled. The colony frame is 1672x941 and is scaled like any other image. |
| Brief 87 Part 3b | "should the F5 editor edit holes — drag a cutout, write `layout_reference.json`, rebuild the plate". There is no plate to rebuild. The question that is left is whether the editor may write the reference at all, which is a different question and is not parked here. |

**AND THE CHECK COUNT WENT DOWN, which it may do in this shape only.**
Seven checks were deleted because their SUBJECT was deleted — the
frame cut, the validator, the built ring and bevel, the byte-for-byte
plates, the preview switch, the strut rails, and the plateless
renderer's own two. Each one's replacement is named in the status
document. A check may not be deleted because it is inconvenient, and
it may not be deleted because it is failing; it may be deleted when
the thing it measures no longer exists, and then the commit says so
and the two count documents move with it.

**69. The GAME menu wears ONE FIXED FRAME IMAGE, plain-scaled, and its
place is the original's place in the map window.** 16 September 2026,
work order 122 Run 1b (`doc/briefs/122-*`). Numbered 69 after checking
at the commit that carries it: the highest entry was 68, and nothing in
the tree used 69.

**SUPERSEDED IN APPEARANCE — 25 September 2026, decision 71.** The body
is the HUD popup block; the frame image is not drawn. Where the popup
sits is decided below and is unchanged by 71.

**What it supersedes, and only there.** The overlay drew its popup body
as a `thin_border` box (decision 34). `screens/game_menu/assets/frame.png`
replaces THAT outline on this screen and nothing else: the buttons, the
slot list, the settings rows and the confirmation and warning panels
keep their skins, and decision 34 stands everywhere else. It is decision
55's shape, not a new one — authored artwork, committed, loaded through
the resource roots (decision 16) and scaled as one image: no 9-slice, no
master, no plate. The body box keeps its style name for what it is
(`"frame": true`) and `screens/game_menu/gmframe.py` is the one place
that draws it.

**The opening is measured, not typed, and the frame goes round the
content.** `layout.json` `frame.opening` is the image's one transparent
hole as `tools/frame_holes.find_holes` reads it, and a smoke check holds
the two equal. The image is scaled with ONE factor so that opening covers
the body box plus a 2 ref px bleed, centred on it; the body box is still
the original's rectangle, so the content decides where the frame sits
and never the reverse. The opening's aspect is the body's to three
decimals (0.737 against 0.739), which is why this works without a
second placement rule.

**The octagon is transparent, so the menu fills its own ground.** The
opaque-fill rule from "A trick that works on one screen is not a rule"
applies verbatim: the fill is the shared cockpit texture over the
opening's bounding box, opaque, and nothing is dimmed, because a
palette-indexed engine cannot dim what is under a popup. The chamfers
are metal and cover the fill's corners. The check samples the drawn
frame inside the opening.

**Where it sits is TRANSCRIBED, and it is not the centre of the map.**
`LOADSAVE::Add_Game_Popup_Fields_` (loadsave.cpp:176-293) gives all
four in-game dialogs one fixed top-left, `_popup_base_x = 0x90`,
`_popup_base_y = 0x19`, and `_Draw_Main_Game_Popup_` draws GAME.LBX
picture 0 there (:1356); pictures 0, 8, 11 and 14 are 279x378 in the LBX
headers. The popup's centre is therefore native (283.5, 214): 51.68 %
across and 48.0 % down the map window (22,22)-(527,421), and nowhere near
the 640x480 window's centre. The brief expected "the centre of the map
area"; the source puts it near that and not on it, and the PROPORTION is
what is transcribed, against the galaxy map's own `map_area` box. Every
box of the overlay moved as one group, and a smoke check fails if the
body's centre leaves that proportion by more than a reference pixel.

**What it costs, on record.** Menu, Settings, Load and Save lie inside
the octagon at 1080p, 1440p and 2160p, measured on the drawn pixels.
The confirmation and the slot warning do NOT, and that is the original's
geometry and not ours: CONFIRM.LBX is 313 and WARNING.LBX 331 native px
wide against the popup's 279, so they overhang its right edge there too.
At 1080p they reach 106 and 137 ref px past the opening, over the metal.
Nothing was shrunk; the suite reports the numbers every run, and whether
those two panels move, shrink or stay is Data's decision. **Amended by work
order 123: Data decided they are scaled into the opening — one factor per
box, the popup's width over the box's, rects and fonts alike, centred on the
popup — an HD DEVIATION, and every dialog is now held to the octagon.**

**AMENDED BY WORK ORDER 125, 16 September 2026 — the position is no longer
the original's.** The anchor above transcribed a FRAMELESS popup's place,
and with a frame it put metal across the GAME field and the nav bar. Data's
decision: the frame is fitted to the galaxy map's own opening — the height
of `map_area` as `boxes.json` holds it, aspect kept, centred — and every box
of the overlay is seated into the frame's opening by one move and one
factor (0.8666 with today's cutout), fonts included. An HD DEVIATION,
marked in `gmframe.py` and held by a smoke check that fails the moment the
frame reaches outside the cutout. The file keeps the unscaled geometry; an
editor save writes back through the inverse. At 1080p the
frame's top rim also started about one reference pixel above the window —
corrected by work order 123: the scale factor takes the width term, the
opening came out a few pixels taller than the body needs and half of that
went above it; the slack now goes below the body.

**71. The cockpit frames give way to ONE FRAMELESS STYLE, drawn in code,
on every screen.** 25 September 2026, Data's decision, recorded by work
order 169 (`doc/briefs/169-*`). Numbered 71 after checking at the commit
that carries it: the highest entry was 70, and nothing in the tree, the
status document or the briefs used 71.

**What replaces the frames.** No screen wears a metal frame image any
more. What every screen draws instead is one style: a background image
behind everything, panels with a thin glowing edge, slanted buttons with
a glowing underline, a title plate, and a large action button. The look
is Data's, from `assets/shared/hud/galaxy_hud.png` — an AI-generated HUD
for the galaxy map with its text removed, 6704x3756, committed as
authored artwork like the frames before it (decision 58's pattern) — and
from two mockups that are a reference for the look and nothing else: no
geometry, text or data comes from them.

**Why.** None of the frames is sharp at 2160p (work order 168: the only
one that is not upscaled there carries the texture of the 1672 px draft
it was upscaled from). A style made mostly of shapes drawn in code at
the target resolution is sharp at every resolution, and uniform BY
CONSTRUCTION: one function draws every panel, so two screens cannot
wear two versions of it. Decision 55's "nothing checks that the colony
screen wears the galaxy map's border" is closed the same way.

**How it is held together.**
- **One style file, measured.** `assets/shared/hud/style.json` carries
  every colour, width, softness and proportion the blocks use, each
  with where it was measured. `tools/hud_measure.py` measures them off
  the HUD image and the smoke test holds the file to the tool, so a
  hand-edited value is a value that fails.
- **One set of blocks.** `core/hud/` draws them — panel, slanted button
  in four states, title plate, action button, small button, table
  header, row, selected row and scrollbar, popup body, separator — at
  the window's own pixel size, cached per size and state. A screen
  calls a block and never draws its own variant; the box skins of
  decision 34 and the plate of decision 51 are routed through the same
  blocks.
- **Cut pieces only where code falls short**, and each is named:
  `tools/hud_cut.py` cuts the icons and the title plate out of the HUD
  image. They are DERIVED — generated by `tools/setup.py`, ignored by
  git, rebuilt byte for byte by the suite (decision 40). A screen that
  needs an icon the HUD does not have draws a text-only button until
  Data supplies one.
- **All text is drawn in code**, never baked into an image.
- **One background slot per screen**, resolved through the resource
  roots (decision 16); until Data delivers the pictures, a plain dark
  placeholder. The galaxy map's own floor is untouched: the HUD sits on
  top of it.

**What it supersedes, checked rather than assumed** — each entry carries
a pointer back here:

| decision | what stops applying |
|---|---|
| 3 | the galaxy map's boxes are no longer cut from `frame.png`'s holes; they are measured off the HUD image |
| 12 | no frame variant is drawn; the 9-slice skin frames of the pre-game screens give way to the title plate and the buttons |
| 13 | the frame's two buttons are HUD buttons now; their clicks are still handled in `ScreenBase.handle_click`, by the same function that places them |
| 34 | `inner_panel` and `thin_border` both draw the HUD panel |
| 55 | the colony screen draws no frame image; its rectangles stay where they were measured and are panels now |
| 69 | the GAME menu's body is the popup block, not a frame image |
| 70 | no frame image is drawn, so none is authored at the canvas; the HUD image is a source of cut pieces, not a frame |

The rest of those decisions stands where it is not about a frame image:
decision 5 (one function for drawing and hitting), 53 (who owns a rule),
61 (the marking vocabulary), and every transcription.

**The old frame images and their code are NOT deleted** in the order that
records this. They stay in the tree, loaded by nothing a screen draws,
until a later order removes them.

**What it costs, on record: the original's cockpit look.** MOO2's screens
are framed in metal, and every frame this project drew was a version of
that. The HUD is not: it is a modern game's frameless look over the
original's content. Where a button or box now sits somewhere the
original did not put it, the click still reaches the original's field
— the click follows the box — and the position is marked DEVIATION in
the module, the status document and a smoke check.

**56. An icon beside a label is a LABEL, and its size is ours.**
13 September 2026, Data's decisions on brief 92 Run 1. The colony
output panel's five rows wear an icon at the left — food, industry,
research, BC and a morale mask — and a line between consecutive rows.

**The icons are a DEVIATION, not a transcription and not an
invention.** Their shapes are the original's own (COLONY2.LBX units
0-3 and the morale masks 0x10 / 0x11), but the original only COUNTS
with them — `Draw_Colony_Prod_Both_` and `Draw_Info_Morale_Both_`
draw N copies for N — and no routine on either colony screen draws one
singly beside a word. So an icon beside a label continues the panel's
label-and-number deviation. INVENTION stays reserved for what the
original has nothing like at all, such as the bars the mockup also
drew and nobody built.

**A label has no zero.** The original picks its morale artwork by the
sign of the halved value and draws nothing at zero. As a label the
rule becomes: negative is the low mask, everything else — zero
included — the normal one, and the icon follows the ROW, so it prints
whenever the morale label does, Unification included.

**The separator is an HD EXTENSION.** The original draws no line in
that box, in code or in the background art.

**The size is ours, so it lives beside the thing it was measured
from.** `core/zoomtables` is for transcriptions (decision 26). A size
we chose goes in `layout.json` next to a note that names its source —
here `output.icon_size` 31, chosen from the row's own height at
1920x1080 (32) so that resolution draws the master 1:1 — and
the tool and the loader both read that one number. The art supplies a
shape; the table supplies the size.

**58. The planet surface picture is an HD EXTENSION, and the artwork is
AI-generated.** 13 September 2026, brief 97. The original shows no
landscape on the Colonies screen — `Draw_Colony_Scan_Info_` draws
production and morale sprites and one paragraph — so the picture of the
scanned colony's world in `colony_panel` is ours, and is marked in the
module that draws it, here, in the status document and in a smoke
check. Data made the sheet with ChatGPT; no copyright is claimed, and
LICENSE's scope lists it.

**One picture per climate, found the way the disc is found.** The
climate id picks the tile and the name is `colonyplanets.NAMES`'s, the
enum's own order (orion2_consts.h:362-373), resolved through the
resource roots so a mod replaces the directory (decisions 16, 17). A
box that shows one says where and how big and never which file.

**Derived, unscaled, and absent is a state.** `tools/make_surface_tiles.py`
cuts each tile at sheet resolution from edges measured on all ten cards
(a plain crop, so a rebuild is byte-identical); `tools/setup.py` runs
it and git ignores the output (decision 40). The box scales the tile
once where it is drawn. A clone that has not run setup has no tiles,
and the loader says so and draws no picture — decision 38's rule.

**Where it is drawn, and how it softens — brief 97, Stop 3.** The
picture is `planet_surface`, a part of `colony_panel`, drawn by
`core/imagebox.py`: the image-box code that was Empire Identity's own
moved into core when a second screen needed it, and gained
`fade_right` beside `fade_left`. Both fades are box properties in
`boxes.json` and multiply the picture's ALPHA, so a soft edge shows the
panel base under the box and no colour is typed for it. In the same
stop the scan box's paragraph gained a name heading above it,
`planet_name`, also an HD EXTENSION — the original's box prints no name
— while the paragraph itself stays the transcription; and the
paragraph box's `font_scale` multiplies the reference size before the
window scale, once ("Scaling twice").

**63. The player's display settings: an OLED floor lift and player-colour
presets, both HD EXTENSIONS, in one user file.** 14 September 2026,
Data's decisions on the brief "OLED floor lift and colour-blind
palettes". MOO2 has no adjustable floor and assigns its eight player
colours fixed; neither is something the original can do, and both are
properties of the player's display and eyes, not of the game.

**One home for the values, and it is not `settings.json`.**
`core/usersettings.py` reads and writes `user_settings.json`: ignored by
git, never shipped, never on the editor's save path (decision 19). An
absent file is the defaults, silently; an unreadable one is one error
line, the defaults, and the file moved aside on the next save; a key
this build does not know is written back. The Game Settings dialog's
two OrionLayer rows are the only UI; they have no field, their clicks
send nothing, and the thirteen engine rows keep their own state source.

**The floor lift is live and has one application point.** A constant
added to the floor after it is drawn (`screens/galaxy_map/floorlift.py`),
whichever floor path ran, before anything else on the map. Step `off`
is no lift at all and renders byte for byte what the map always drew;
`light` and `haze` are MEASURED against the real floor graphic — its
median (1, 2, 5) and 90th percentile (4, 10, 20) — not against black,
because the floor already averages (1.7, 3.7, 7.9).

**A preset swaps all four colour tables or none.** `owner_*`, `ship_*`,
`owner_hover_*` and the banner cloth tints: one empire, one colour
everywhere. Moving `ship_*` and the banner literals into the palette
came first, each checked byte for byte. The preset is read ONCE, by
`palette.init(preset=)`, which `main.App` calls after loading the user
file and every other caller calls without — tools and the smoke test
never see the player's choice. Changing it needs a restart, and the
dialog says so only while the saved preset differs from the active one.

**THE RULE THAT FILLS A PRESET IS OURS, AND IS MARKED DEVIATION.** The
gate before the tables measured whether the original's tables follow
from `owner_*`: they do not (ship lift k per channel -0.22..1.00,
hover k 0.27..1.00, the banner add constant for seven colours and not
for orange). So a preset the game never had is filled by an invented
rule, written next to its values: owner = base; ship and hover = base
lifted toward white by one measured k each; banner multiply = base, add
none. `k_ship` 0.07 is the smallest lift that keeps every preset ship at
least as bright as the darkest ORIGINAL ship at every zoom step;
`k_hover` 0.45 matches the original's mean hover-to-owner luminance
ratio. The smoke test holds both criteria, so a changed base colour
cannot quietly break them.

**Okabe–Ito, with black replaced by white.** Eight colours documented
for deuteranopia and protanopia; black is invisible on the floor and
the original has a white player. Mapped over the original's banner
order, each colour to its nearest relative, the last two by distance.
Its smallest pairwise distance after a deuteranopia simulation
(Viénot 1999) is dE 17.2; the original's is 3.8, which is the reason
the preset exists — so the threshold is held by the colour-blind
presets and the original is reported. Known limit, not solved: a white
base cannot get lighter, so the white player has no visible hover mark
in the Planets list.

**64. A space monster's values in the Planets panel: all of it an HD
EXTENSION except the type, and the reason is levelling.** 14 September
2026, Data's decisions on brief 107 (`doc/briefs/107-*`, `108-*`, `109-*`).
Numbered 64 after checking: the highest entry in this file was 63, and
nothing in the tree, the status document or the briefs used 64.

**The original shows the type and nothing else.** Outside combat MOO2
names the monster — "(Amoeba)" under the planet in the Planets list, the
"guarded by" prompts — and that is all. The fleet screen's scan, which
prints weapons, shield and specials, never runs for a monster: its big
icons are scanned only for the player's own stack
(`Scan_Fltscrn_Big_Icons_`, flt1.cpp:614). The monster system popup is
unreachable in a running game. So stage, size, structure, armour, shield,
weapons and specials are ALL the extension, not only the hull points —
the brief had expected the fleet screen to make half of it a
transcription, and the source said otherwise.

**Why it is here anyway.** The values are fixed per type, compiled
templates (`SHIP_CONFIG`, ship_config.cpp:86-139), and have been public
for years. Showing them removes a disadvantage a newcomer has and a
veteran never had. It is not a spoiler, because a spoiler is information
one could not have had. Numbers, not judgements: no rating, no warning
colour, no difficulty word — a rating would be a second invention. A
switch in the Game Settings OrionLayer rows turns it off, and it is ON by
default, the one default in `core/usersettings.py` that is not the
original's look.

**What is read, and why each is trusted.**
- The design block of `s_ship_data` and the weapon records, verified by
  decision 23's two sources: the header compiled with 48 static_asserts
  (and a deliberately wrong one that failed), and a live probe of five
  monster records matching their templates field for field
  (`core/structs/ship.py`).
- **The damage fields are neither declared nor read.** Monsters are
  repaired in full every turn, so every value the probe could see was
  zero, and a zero confirms no offset. The panel shows maxima, which
  outside combat are the true values. The two owner-8 "Viper VII"
  records with non-zero structural damage on the `natives` fixture are
  a lead for later, not evidence now.
- Hull points: TACTICAL only, structure and armour as two lines, because
  combat takes armour first and a sum would hide that. The five monsters
  read "Armour 0", which is what `ARMOR_NO_ARMOR` gives. The table in
  `core/monsterhull.py` is a copy of `Get_Ship_Structure_` and the hull
  and armour tables, and a copy is only legitimate with a checker:
  `tools/monster_hull_check.py` reads initship.cpp, techdata.cpp and
  orion2_consts.h and the smoke test runs it. The strategic numbers
  (`AIPOWER::Max_Ship_Hits_`) are AI heuristics and are not shown.
- Names from the player's TECHNAME.LBX, decision 38's pattern, in a
  second file beside the building names (`core/shipparts.py`). Data
  asked for weapons, shields and armour; the specials and the hull
  classes are read too, from the same walk, because the panel names both
  and has no other source for either. Specials are shown for all forty
  bits: the fleet screen's own loop stops at 39 (flt2.cpp:727), which
  would hide the Amoeba's only special, Regeneration, bit 39.

**DEVIATION: the sprite is the monster's TYPE.** The original's own
monster picture, in the unreachable popup, is chosen by star index % 5
(`RUSS::Star_To_Monster_`, mainpups.cpp:1082), so a star can show a
creature that is not the one guarding it. HD shows the creature that is
there, from the galaxy map's own master — a larger export out of the same
`make_ship_icons.py` pipeline, 314 px on its long edge, DERIVED for the
4K box so the panel only scales down, with the number and its source in
`core/zoomtables.py`. One source, no second set of artwork.

**Empty in the panel, a stand-in on the map — two different answers on
purpose.** No master exists for the Amoeba (nor for the Antaran, which
is not a monster). In the panel an empty sprite box is an understandable
state and an invented picture would be a deviation, so it stays empty.
On the map a monster that vanished would be a gap against the original,
which draws it, so the grey player-ship stand-in stays — marked
DEVIATION at `_resolve_sprite`, named in the status document's known
gaps, and held by a smoke check to exactly {amoeba, antaran}.

**65. HD sends no move order the player has not chosen.** 15 September
2026, Data's decision A4 on brief 110 (`doc/briefs/110-*`, `111-*`,
`112-*`). Numbered 65 after checking at the commit that carries it: the
highest entry was 64, and nothing in the tree used 65.

**It is the other side of decision 33.** 33 refuses input the game would
refuse; this refuses input the game would ACCEPT as an order nobody gave.
Opening the fleet box of a stack you own selects its ships by itself
(`fleetpop.cpp:683-686`, when `auto_select_ships` is on), and while that
box is open the game tests stars BEFORE ships (`mainscr_main.cpp:427-431`),
so the next click it resolves to a star is `Ships_Try_To_Move_To_` and
`Apply_Player_Movement_Order_` (`:480-535`). HD does not draw that box
yet, so no such click can have been chosen.

So while the FIELD_LIST shows the fleet box (`mapboxes.py`),
`mapclick.plan` refuses every map click whose NATIVE point
`Check_Stars_XY_` would resolve to a star — with the game's radius, not
HD's, because a click on empty space or on an icon beside a star is the
same order as a click on the star itself. A black hole is exempt: the
original never orders a move there (`:481`). Marked DEVIATION in the
module, since the original moves the fleet, and held by a smoke check.

**What it costs, on record:** until HD draws the fleet box and a target
is chosen in it, a fleet cannot be moved from the HD map at all. That is
the order Data set (A1): the icon hit test first, the box next. The guard
lifts for an explicit choice made in the HD box and for nothing else.

**AMENDED 15 September 2026, brief 117 (Data's path 1), in the commit
that builds it — and one choice inside it is still Data's.** The guard
steps aside while HD draws the fleet box with its selection READ OFF THE
WIRE (open fix 20's FSEL block, `boxdraw.orders_ok`): the cells then show
blue exactly the ships a star click moves, so the click is made in sight
of what it orders. That is variant (a) of brief 115's question — the
original's own gesture. Variant (b), a click that only marks the target
and a button that sends it, was not decided; it would be a DEVIATION
where (a) transcribes. No engine carries open fix 20 today, so on every
tree as it stands the guard holds exactly as before.

**PREMISE MEASURED, 15 September 2026 (briefs 119 and 120).** Until then
"a star click with the fleet box open is a move order" was read from the
source (`mainscr_main.cpp:427-431`, `:480-535`), never seen. Data's hand
test in brief 119 moved the ships: the premise is live-confirmed, and the
guard guards against a real order. Open fixes 20 (revision 2) and 21 are
applied, so the amendment is in force on the tree: the guard was checked
live on SAVE5 in both directions without sending an order (brief 120) — a
box HD opened and draws lets the star click through (planned, not sent),
a box opened behind HD's back refuses it, nothing sent, nothing changed.
Two things came with it. A star click sent as an order keeps the fleet
box's identity (`boxmodel.remember(order=True)`): the game keeps the box
open, and HD had renamed it a system window and stopped drawing it. And
the probe's own star clicks in run 119 moved nothing — once out of range
(no message by design, `Ships_Try_To_Move_To_`), once to Sol, in range,
with the original showing "4 turns to Sol": not separated from the
injection path, recorded as a gap in `v3_projektstatus.md`. **RESOLVED
(brief 121):** Data's hand test in the HD window alone moved the ships out
of their orbit slot as the original does — HD's target click flies, and
the failure of run 119 lay in the probe (its target star), not in the HD
path.

**68. Every line on the HD map follows one rule: antialiased, marked,
through one routine.** 15 September 2026, Data's decision B1 on brief 110
(`doc/briefs/111-*`), in brief 121's commit that draws the first line the
rule was made for. Numbered 68 at that commit: the highest entry was 67,
and nothing in the tree used 68.

MOO2 is palette-indexed and cannot antialias; `line::Line_` and
`line::Multi_Colored_Line_` plot hard one-pixel lines. HD's wormhole link
was antialiased and alpha-blended long before anyone asked, unmarked, and
the smoke test defended it — decision 43's shape, a check guarding a choice
nobody had recorded. Stop 1 of brief 110 found it; Data chose softness for
ALL lines instead of hardness for all, on one condition: it is one rule, not
a property of whichever line happened to be written first.

So `screens/galaxy_map/maplines.stroke` is the only place a map line is
drawn (marked HD EXTENSION B1 there), the wormhole layer calls it, and the
smoke test fails if `aaline` or `pygame.draw.line` appears in any other
galaxy map module. A new line kind — the order preview, relocation lines —
goes through `stroke`, or it is a second rule. What a line transcribes
(colour table, wave, endpoints) stays the original's; only the edge is HD's.

**67. The ship node table comes off the wire; nothing rebuilds it.**
15 September 2026, brief 119. Numbered 67 at the commit that carries it:
the highest entry was 66, and nothing in the tree used 67.

For a month OrionLayer rebuilt `MOX::_ship_node[]` from `_ship[]`: node n
was the n-th ship with status below 3, transcribed from
`SHIPSTAK::Find_Ship_Stacks_`, with a docstring that said `ship_idx` "is
written nowhere else in the source". It is:
`SHIPSTAK::Sort_Ships_In_Stack_` (shipstak.cpp:261-278) runs right after,
qsorts each stack's ships by type and writes `ship_idx` back along the
chain — node places stay, ships move — and qsort is not stable, so no
transcription can reproduce it for two equal ships. The owners came out
right anyway, because every ship of a stack has one owner, and a
validation against `star_idx` cannot see a move INSIDE a stack. The fleet
box's per-ship selection could: live (brief 118) HD's click on ship 13
flipped the engine's node 11 and the original's third cell.

So: open fix 20 revision 2 sends `ship_idx` per node and the fleet box's
chain, `ships.wire_nodes` is the only table, and owners, icon anchors and
the fleet box read it. Without the block there is no table — owners fall
back to the per-star guess and HD draws no fleet box; nothing is
reconstructed. The smoke test fails if `build_node_map`, `stack_of` or
`selection_of` come back. "Written nowhere else" is a claim about a grep,
and it needs the grep's output.

**66. No positional right click while a box is open; a box closes
through its own CLOSE field.** 15 September 2026, Data's decision A5 on
brief 110. Numbered 66 after checking at the commit that carries it.

CANCEL_FIELD does not click where the pointer is. The Extension API
pushes the right button at the field's CENTRE (`ext_api.cpp:427-455`),
for the map grid native (274, 221). An open box can cover that point —
the system window at its default position does, measured live in brief
110 Stop 1 — and the lowest-indexed field under a point wins
(`fields.cpp:1264-1283`), so the right click goes to the box, and over a
planet it opens `Potential_Colony_Info_Popup_`, a modal. HD therefore
sends no CANCEL_FIELD while `mapboxes` reports a box; the pan still
starts. A box is closed through its ESC-hotkey CLOSE field, looked up in
the live list — which HD can offer only once it draws the boxes.

**61. An OMISSION is marked like an extension, and so is a state HD
cannot fill.** 14 September 2026, the GAME menu. HD EXTENSION and
DEVIATION say what HD does that the original does not; nothing said
what the original does that HD leaves out, and a thing left out is the
easiest to stop seeing. Three labels now, each in the module, in the
status document and in a smoke check: **OMISSION** — the original has
it and HD does not draw it (the volume sliders, which an activation
cannot set — built after all by work order 124 C, through an injected click; the slot game-type icon, whose artwork is not extracted);
**HD STATE** — HD draws something in place of a value the wire does not
carry yet (slot rows showed "Slot N" until open fix 14 was applied on
16 September 2026); **UNVERIFIED** — a
source reading Data required to be confirmed live before it is
transcribed, and that could not be run (the Save dialog's right click
outside a help region). An UNVERIFIED behaviour is not built at all:
HD does nothing there rather than guess.

