# 149 — One frame and box system for all screens: catalogue and options

**Work Order 149 — One frame and box system for all screens.**
Parts A and B. **This is the stop.** Part C, the guide, waits for
Data's decision.

Inputs: the extraction from work order 148 (19 139 PNGs under
`evidence/work_order_148/`), the report from 147
(`doc/v3_original_gui_construction.md`), and OrionLayer's own art.
Contact sheets are in `evidence/work_order_149/` and are not in the
repo.

---

# Part A — Catalogue

## The headline, because it changes what Part B can even propose

**The original has no box kit to copy.** Six classes were looked for.
Three of them — grouping panel, picture frame, list area — have **no
standalone art at all**: they are painted into each screen's own
640x480 background, which 147 established and 148's files confirm.
Of the three that do have art, two are screen-local and one is shared:

| class | standalone art? | pieces | reused across screens? |
|---|---|---|---|
| 1 screen frame | yes, one per screen | ~14 backgrounds | **never** |
| 2 grouping panel | **no** | 0 | — painted into the background |
| 3 picture frame | **no** | 0 | — painted into the background |
| 4 list area | **no** | 0 | — painted into the background |
| 5 popup / dialog | yes | 5 pieces | **yes — the only shared box art** |
| 6 button | yes | 478 pieces | **effectively never** |

So there is nothing in the original to derive a reusable kit *from*.
Whatever Part B proposes, **Data has to author it**; the original can
be a reference for look, not a source of parts.

### Do buttons belong in this catalogue?

**Yes, and they are the strongest case in it.** A button in the
original is not a picture with a hit area beside it: `Add_Button_Field_`
sets `x_end = x + Get_Width_(pic) - 1`, stores the picture *in the field
record*, and `Draw_Visible_Fields_` draws it and prints its label centred
in that same rect (147). Art, geometry, label and hit test are one
object — which is exactly what a box skin is. They are in scope.

Icons and pictures are out of scope per the order and were not counted.

## Counts — exact, no threshold involved

From the animation headers of every extracted entry, so these need no
sweep:

* **1 059** full-screen-sized pieces, but most are animation frames
  (the colony terrain has 73, race portraits hundreds). **Distinct
  screen backgrounds: 14.**
* **891** panel-sized pieces, overwhelmingly in `council/` and
  `race_diplomacy/`, which are portrait and animation art, not boxes.
* **478** button-sized pieces (40..200 wide, 14..40 tall).

**Button sizes do not repeat between screens.** The most common exact
size, 110x26, occurs in **one** screen folder. Of the ten commonest
sizes, **eight appear in exactly one folder** and two (74x27, 107x14)
in two. Contact sheet `CLASS_button.png` shows why: grey bevels on
Fleets and Design, green LED lettering on the main menu, blue plaques
on Officers and Planet Summary. They are not variants of one button —
they are different buttons.

## Border thickness — and why most of it is UNCONFIRMED

**The numbers below are marked unconfirmed, and the reason is the
finding.** Five methods were tried; all five are recorded in
`evidence/work_order_149/measure.py` with why each failed:

1. *Walk inward until the pixel matches the modal interior colour* —
   unstable: the wells are textured, so the match depth varies.
2. *Largest dark connected region as the well* — ambiguous: a dialog
   has a content well **and** button wells.
3. *Widest gap in the luma histogram* — picks the wrong gap. On
   CONFIRM the chassis has a wider internal gap (26→37) than the one
   that actually separates well from chassis (18→26).
4. *Otsu* — lands at 46..87 where the boundary is near 20, because the
   chassis dominates the histogram.
5. *Rim at each edge's midpoint, swept over luma percentiles* — gives
   a value for some pieces and none for others.

They fail for one reason, and it is the reason Part B matters:
**this art has no single border thickness to find.** The pieces are
illustrated chassis with irregular outlines, internal shading, lugs
and often more than one well. A number would be false precision.

What *is* stable, by method 5 swept over luma percentiles (15, 20, 25,
30) of each piece's own opaque luma:

| piece | size | L, R, T, B | sweep |
|---|---|---|---|
| FLEET.LBX 17 (selection box) | 59x58 | 2, 1, 2, 2 | stable |
| GAME.LBX 0 (load/save popup) | 279x378 | 40–52, 40–53, 150–162, 100–113 | **UNCONFIRMED** |
| CONFIRM.LBX 0 | 313x227 | — | **UNCONFIRMED**, no rim at some thresholds |
| WARNING.LBX 0 | 331x191 | — | **UNCONFIRMED** |

One number is trustworthy and the rest are not. That is the honest
state of the measurement, and it is why the guide in Part C will have
to *specify* thicknesses rather than transcribe them.

## OrionLayer's own art — exact, and this is where the drift is

A 9-slice's border thickness **is** its corner tile size, so these need
no threshold at all:

| skin | corners | border L/T/R/B | centre |
|---|---|---|---|
| `inner_panel` | 24x24, all four | 24 / 24 / 24 / 24 | alpha 0..0, **transparent** |
| `frame` (shared ring) | TL/TR 368x122, BL/BR 368x169 | 368 / 122 / 368 / 169 | alpha 0..1 |
| `thin_border` | — code-drawn, `draw_thin_border` | 1 px rounded outline | none |
| `text` | — draws only the string | — | none |

**The drift, in one line: five screen frames, five different source
sizes.**

| screen | frame image | transparent |
|---|---|---|
| colony_summary | 1672x941 | 70.1 % |
| galaxy_map | 1707x921 | 70.3 % |
| fleets | 1445x811 | 45.6 % |
| game_menu | 1108x1419 | 75.7 % |
| planets | 1920x1080 | 75.2 % |

Each is its own image, plain-scaled over the reference area. Nothing
holds them to a common border thickness, corner size or colour ramp —
which is the "consistency depends on luck" Data described. `fleets` is
the odd one at 45.6 % transparent because work order 146 gave it 32
cutout holes; the others have one opening each.

### Where OrionLayer already matches the original's classes

| class | the original | OrionLayer today |
|---|---|---|
| screen frame | baked background per screen | **matches** — one image per screen |
| grouping panel | painted into the background | `thin_border`, code-drawn |
| picture frame | painted into the background | `inner_panel`, 9-slice |
| list area | painted into the background | `thin_border` |
| popup / dialog | shared art, remapped per palette | screen-local art (`game_menu`) |
| button | art in the field record, per screen | `thin_border` + a label, or a hole |

OrionLayer is **more systematic than the original in three classes**
(it has skins where the original has paint) and **less systematic in
one**: the original shares its dialog art across every screen, HD does
not.

---

# Part B — Options

Three systems, each covering the six classes. Trade-offs only; no
recommendation.

## Option 1 — Frame image per screen, one shared box kit inside it

What work order 146 moved Fleets toward, generalised.

* **Built from art:** one PNG per screen carrying the outer ring and
  every cutout hole. Everything *inside* a hole is drawn by a shared
  9-slice kit, one per class.
* **Resolutions:** the frame is stretched over the reference area as
  now, so no per-resolution tuning; the kit's corners blit unchanged
  and its edges scale in one dimension. **Double scaling is avoided**
  the way the fundament requires — anything that must be right at an
  untuned resolution reads the stored scale directly, never a value
  multiplied by the window scale twice.
* **Decision 3** ("Cutout boxes come from the frame; content boxes do
  not") — unchanged and extended to every screen; `frame_holes.py`
  already does it for two.
* **Decision 12** ("Frame variants only — no runtime tile swapping") —
  unchanged.
* **Decision 34** ("Two panel skins, and which one means what") —
  **changes.** The kit needs a name per class, so two skins become four
  or five, and 34's own last sentence bites: every screen that renders
  panel skins selectively must then match on all of them.
* **Decision 37** ("A third box skin, `text`, draws nothing but the
  string") — unchanged.
* **Data draws per screen:** one frame image. **Reusable:** the whole
  box kit.
* **Covers badly:** buttons whose art is the frame's hole — a hole
  cannot show a pressed state, so button states need either a kit
  piece drawn over the hole or a second frame variant.

## Option 2 — One kit for everything, no per-screen frame art

* **Built from art:** no screen images at all. The outer ring is a
  9-slice like any other box, and a screen is a list of boxes in
  `boxes.json`.
* **Resolutions:** every piece scales by the same rule; a screen has no
  intrinsic size, so nothing can be off at an untuned resolution.
* **Decision 3** — **changes fundamentally.** There are no holes, so
  cutout boxes have nothing to come from; `frame_holes.py` and its
  smoke checks retire.
* **Decision 12** — unchanged in letter, hollow in practice: with no
  frame image there are no variants to choose between.
* **Decision 34** — **changes**, as Option 1.
* **Decision 37** — unchanged.
* **Data draws per screen:** *nothing*. He draws the kit once.
  **Reusable:** everything.
* **Covers badly:** the screen frame class. Every HD screen today has
  an ornate ring with corner lights and asymmetric top/bottom
  (368/122/368/169) that a uniform 9-slice cannot reproduce without
  becoming a very large one. It also throws away art Data has already
  accepted by eye.

## Option 3 — Keep frames per screen, add a specification and a checker

The minimal change: no new skin system, but the frames stop being
independent.

* **Built from art:** as today — one image per screen, `inner_panel`
  and `thin_border` inside — but every frame must meet a written
  specification: fixed border thickness per side, fixed corner size,
  a stated colour ramp and light direction, holes on a grid.
* **Resolutions:** unchanged from today.
* **Decisions 3, 12, 34, 37** — **all unchanged.** This is the only
  option that changes no decision.
* **Data draws per screen:** a whole frame, as now, but to a spec.
  **Reusable:** nothing new; the consistency comes from the spec, not
  from shared files.
* **Covers badly:** it does not actually unify anything. Two frames
  drawn to the same spec by an AI will still differ in texture and
  weathering, and the only thing holding them together is a checker
  that has to be written and that can only test what it was told to
  measure. Given Part A found that **border thickness cannot be
  measured reliably even on finished art**, a checker for this option
  would be measuring something the catalogue could not.

## What none of them covers

* **Palette-portable dialogs.** The original draws one dialog over any
  screen by nearest-colour remapping at draw time (147). No option
  above reproduces that; HD would ship a dialog per palette or accept
  one look everywhere.
* **The button-state problem** stated under Option 1, in all three:
  wherever a button's art comes from a hole, pressed and disabled need
  a second source.

## For the decision

Options 1 and 2 both change decision 34 and need a name per class;
Option 3 changes nothing and unifies nothing. Option 2 is the only one
where a new screen costs Data no art, and the only one that discards
the ring he has already accepted. Option 1 keeps the ring and the
cutout rule that two screens already run on.

**Stopping here per the order.** Part C follows the decision.
