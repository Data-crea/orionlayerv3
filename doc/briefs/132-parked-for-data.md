# Work order 132 — parked for Data

Everything here is either Data's to decide or a question the measurements
raised and did not answer. The assignment itself, with its numbers, is
`doc/briefs/132-frame-assignment.md`; the side-by-side renders are
`~/orionlayer-fixtures/evidence/work_order_132/`.

## 1. Three of four assets are unused. Is that the right outcome?

**What:** only `frame_plain.png` was assigned (to Select Race).
`frame_map_sidebar.png` (8 openings), `frame_map_4panels_7buttons.png`
(5 openings + 7 opaque plates) and `panel.png` (opening aspect 3.71) fit
no screen this project has, by opening count and aspect. The reasons are
in the assignment document and they are counts, not taste.

**Why yours:** they were made for screens that do not exist in that
shape. Either the assets get redrawn to the screens' real needs, or a
screen's panel count changes to suit an asset — and changing a screen's
content to fit a picture is a decision, not a build step. Work order 132
does not authorise it and this run did not do it.

**The nearest misses, if you want to close the gap from the asset side:**

- `frame_map_sidebar.png` is one opening-split away from Planets. Planets
  needs list + side panel + **three** bottom panels; the asset has list +
  side column + **three** bottom fields + **three** stacked rows. Merge
  the three stacked rows into one and it is Planets' shape exactly.
- `frame_map_4panels_7buttons.png` is the galaxy map's shape except that
  it has no side column and its seven buttons are painted rather than
  cut. Cut the buttons and add a sidebar opening and it becomes a
  candidate.

**Answer:** redraw the assets / change a screen's panel count / leave
them unused.

## 2. The seven button plates are opaque. Should `frame_holes` learn to see plates?

**What:** they are `rgba(20, 31, 37, 255)`, alpha 255.
`tools/frame_holes.py` reads alpha < 16 and finds five holes in that
file, none of them a button. So decision 3 cannot derive `nav_*` from
them.

**Why yours:** teaching the regenerator a second rule — "an opaque teal
region is also a cutout" — would be a new mechanism beside decision 3's,
keyed on a COLOUR rather than on transparency. It is fragile (the same
teal is the title plate and the corner plates) and it would make the
artwork's palette load-bearing. This run did not invent it.

**Answer:** cut the buttons as holes in the artwork (preferred, no new
rule) / teach `frame_holes` a colour rule / leave it.

## 3. The openings are irregular. Straighten them, or transcribe them?

**What:** fields that look identical are not. Measured at 1920x1080,
where image px equal reference px:

| asset | group | spread |
|---|---|---|
| `frame_map_sidebar` | three bottom fields | width **237 px** (322 / 396 / 559) |
| `frame_map_sidebar` | three stacked rows | height **11 px** (55 / 49 / 44) |
| `frame_map_4panels` | four bottom fields | width **21 px** (385..406) |
| `frame_map_4panels` | seven button plates | width **20 px**, gaps 40..43 |

Doubled at 3840x2160.

**Why yours:** because of decision 3 these would become box coordinates
on any screen that derived cutouts from them, and the order is explicit
that they must not be fixed in the artwork by me and never compensated
in code. `frame_plain.png`, the one asset in use, has a single opening
and no siblings to be inconsistent with — its own asymmetry is 2 px
horizontally (L92 / R94) and 6 px vertically (T81 / B87), which nothing
depends on.

**Answer:** straighten them in the source before any of these is used
for a cutout screen / accept them as transcription and let the boxes be
irregular.

## 4. The three large frames are stored already resampled. Re-export at native size?

**What:** Chat says they were generated at about 1670–1683 px wide and
scaled to 1920x1080. I could not confirm or refute that from the files —
the directional-sharpness measurement puts them inside the range the
committed frames already show, and `colony_summary`'s committed frame
has the same ratio while being stored at its native 1672x941.

**What IS certain:** every committed frame is stored at the size it was
generated and scaled by the code at load. These three are stored at
1920x1080, so whatever resampling happened is baked in and the renderer
no longer chooses the filter or the target.

**Why yours:** it is an asset-pipeline decision and it is cheap to
reverse now and expensive later. Note it does NOT make the Select Race
assignment wrong: the frame it replaces is a 1672x941 source, so the new
one is the sharper of the two at every resolution either way.

**Answer:** re-export the three at their native size / keep them as they
are.

## 5. `panel.png` would need decision 34's skins to change. Not done.

**What:** its opening is aspect 3.710. The popups it was meant for are
`help_popup` (1.35), `system_box` (1.09), `fleet_box` (0.86) and the GAME
menu body (0.739). Plain-scaling distorts by 2.7x or more; nine-slicing
would stretch the brackets at the middle of each edge, which is what
decision 12 and the brackets themselves rule out.

**Why yours:** using it means changing what `inner_panel` and
`thin_border` mean (decision 34), which work order 132 says to park
rather than do.

**Answer:** redraw it at a popup's aspect / give it a 9-slice that
leaves the brackets alone / leave it unused.

## 6. Empire Identity misses by 3 px. Nudge one box, or leave it?

**What:** `busy_panel` sits 3 reference px above `frame_plain.png`'s
opening. Every other box on that screen is inside. Moving one hand-placed
box by 3 px would make it a second clean assignment and would give the
uniform look one more screen.

**Why yours:** it is a content move on a screen whose layout is yours,
and 3 px is exactly the size of change that gets made quietly and then
cannot be explained later. Custom Race and Main Menu are NOT near misses
— 6 and 7 boxes out, by up to 66 px — so this is the only one.

**Answer:** nudge `busy_panel` and assign the frame there too / leave
Empire Identity on the 9-slice.

---

**Closing state, 18 September 2026: six items.** One screen built and
committed (Select Race), nothing pushed, no orion2re change, no change
to `core/zoomtables.py`, decision 34 untouched, and no new decision
filed in the fundament — nothing was decided or reversed that is not
already covered by decisions 3, 12, 34, 55 and 69.
