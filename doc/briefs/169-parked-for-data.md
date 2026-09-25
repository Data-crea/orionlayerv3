# Work order 169 — parked for Data

Every choice this unattended run made that is Data's to confirm, with the
default taken so the run could continue. Nothing here blocks what was
built; each item says what changes if Data decides otherwise.

---

## P0 — "Clone per CLAUDE.md (full tree)"

**Default taken:** worked in the full working tree at
`/home/data/orionlayerv3`, as 167 did. CLAUDE.md names no separate clone
step; the fresh-clone run at the end is the clone check.

## P1 — The live part: the engine did not come up

The display was reachable (`display OK: x11`, with the three variables
CLAUDE.md names) and port 17362 was free. A session-launched orion2re
stopped after `mox2: data space allocated`, as CLAUDE.md records — but
this time `ps -o stat,%cpu,wchan` read `SNl 0.3 drm_syncobj_array_wait_timeout`,
a wait in the GRAPHICS driver, not the `S` at `rt_sigsuspend` 139 E/140 A
measured. It stayed there for 40 s. The order says not to wait, so the
engine was stopped, **no save was loaded, nothing was sent**, and SAVE1-11
hashed identical before and after (`SAVE10.GAM` matches none of the three
fixtures, before and after alike — this run did not touch it).

**Parked:** the live check that the HUD's clicks reach the right native
fields on a running game. What was checked offline instead: every button
still activates the same field id through the same code path
(`mapinput`, `colonysort.button_at`, `ScreenBase._frame_button_hit`), and
the shapes drawn and hit agree on every pixel (006a). **Suggested run**,
with the engine started from Data's desktop: `python tools/leaders_hd.py
run 5` and `python tools/research_hd.py` as written by their orders, plus a
click on each galaxy nav button and TURN from the HUD.

## P2 — Aldrich stays the face

The mockups use a squared geometric sans. The tree holds two faces:
Aldrich (the display font since 31 August) and pygame's freesansbold.
Aldrich is the closer. **Default:** Aldrich for every HUD word
(`chosen.font`). A licensed face closer to the mockups (e.g. Rajdhani,
Exo 2, both OFL) would be one file under `assets/shared/fonts/` and one
line in style.json — decision 41's licence rule applies.

## P3 — The colony mockup is not in the tree

`colony_screen.png` is 21 MB (6700x3756). The galaxy HUD (7.3 MB) and the
galaxy mockup (2 MB) are committed; the colony mockup is not. Its table
values are in style.json's `measured.mockup_colony` with the file's
sha256; `tools/hud_measure.py --colony <png>` re-measures them, and the
suite REPORTS the block rather than checking it. **If Data wants it
committed**, it goes to `doc/briefs/169-mockup-colony.png` with a README
link, and the report becomes a check.

## P4 — Hover, active, disabled are chosen, not measured

The HUD shows every button in ONE state. **Defaults** (`chosen.button`):
hover = the TURN button's lit edge + the panel's inner-glow fill; active
= the colony mockup's selected-row fill + the lit edge; disabled = the
normal button at 45 %. **One label colour in every state** — the state is
the block's, never the word's (Data's rule for the colony sort keys of
12 September, made general).

## P5 — The title plate is a cut piece, not code

No code version was built: the plate's glossy centre, its bevel and
the two orange lamps are painted light, which the blocks' flat fill,
edge and glow cannot reproduce, so it was judged from the artwork alone.
If Data wants it in code, that is one block and a comparison render. **Default:** the plate and its wings are cut from the HUD
(`tools/hud_cut.py`), drawn at the HUD's own proportion (4780 HUD px wide
= 1369 reference px), the word in code. Panels, buttons, the action
button, separators, tables and popups are all code — none fell short
enough to cut.

## P6 — The background slot is `screens/<name>/assets/background.png`

The slot ScreenBase already had, resolved through the resource roots.
What changed is the fallback: the shared cockpit texture is no longer
drawn; a screen without a picture draws the placeholder
(`chosen.background_placeholder`, (3, 7, 16)). **Main Menu keeps its
own picture** (the title art is a background, not a frame). **New Game's
picture is NOT drawn** although it sits in the slot: it was a cutout
frame around the five setting pictures; it is still loaded, because its
cover-scale maps the slots. When Data's backgrounds arrive, each is one
file at that path — New Game's needs its slot geometry moved into
`layout.json` first (its `_hd_to_screen` reads the old picture's size).

## P7 — The galaxy map's floor now runs to the screen's corner

`map_area` is `[0, 0, 1611, 947]`: from the top-left corner to the HUD's
panel and nav row (`tools/hud_boxes.py`, `MAP_GAP` 6 ref px, chosen). The
title plate hangs over the floor, as in the mockup. The GAME menu now
seats in the map's free area below the title plate (it was fitted to the
old cutout's height). **If Data wants the floor full-screen** under the
panel and nav row too, that is `MAP_GAP` and one box; stars under the
panel would then be unclickable there (the panel swallows clicks).

## P8 — DEVIATIONS this order added, each marked in its module

| where | what | why |
|---|---|---|
| colony `colonysort.render` | sort-key words in the HUD button colour, not the original's grey (196,196,196) | one colour for every HUD button word |
| fleets `fltdraw.draw_labels` | control words in the HUD button colour, not the skin's green | the same |
| leaders `ldrdraw.draw_button`, `ldrdialog.draw_popup` | OFFICER.LBX button art and popup picture not drawn; HUD blocks with words | every screen in the HUD style; portraits, skill icons and the map box keep the original's art |
| galaxy map | nav row at the bottom, GAME in the title plate (carried over, now written in `screen.py`) | the HUD's layout |
| colony list | stripes, scanned row and outlines in the HUD table's colours (decision 57's keys stay in the skin, unread) | one table look on every screen |

**Question for Data:** is the Leaders button art (167's "original
assets only") meant to give way to the HUD, as done, or to stay as the
original's pictures inside the new style?

## P9 — Star names at 2160p are about twice the mockup's size

Seen on `galaxy_map_beside_mockup_offline.png`. The map's name size is
`layout.font_size(16 * box_font_scale("map_area") * zoom)` — the
"scaling twice" of the fundament (window scale taken twice). It is older
than this order and was left alone here, because it changes the map, not
the HUD. **Recommended:** `box_font_scale_stored`, as the sidebar now
uses.

## P10 — The old frame images and their code stay

As the order says. Not drawn by anything: the five `screens/*/assets/
frame.png`, the skin 9-slice frame and its `select_race` variant,
`core/frame.py`, `core/researchframe.py` and `tools/make_research_frame.py`
(still a setup step), `ScreenBase._load_frame/_scale_frame`, the metal
picks bar of Custom Race, New Game's toggle knobs. The frame checks that
measure image against boxes (class B, planets' five cutouts, the Fleets
v4 holes, decision 70's canvases) still pass, because neither the images
nor those boxes moved — they measure a relationship nobody sees any more.
**A later order** removes images, code and those checks together.

## P11 — Missing icons (for Data to generate)

The HUD has twelve icons: the five info-panel pictures, the six nav
glyphs and the TURN triangle. Every other button draws its word alone.
Size = the HUD's own proportion, **icon height 0.6 x button height**
(measured: 130 of 216 HUD px), in REFERENCE px at 1920x1080; a master at
4x that (for 2160p with room) is the safe export.

| screen | button | button h (ref) | icon h (ref) |
|---|---|---|---|
| colony summary | NAME, POPULATION, FOOD, INDUSTRY, SCIENCE, PRODUCING, BC, RETURN | ~52 | ~31 |
| planets | sort CLIMATE, MINERALS, SIZE | 42 | 25 |
| planets | NO ENEMY PRESENCE, NORMAL GRAVITY, NON-HOSTILE ENVIRONMENT, MINERAL ABUNDANCE, PLANETS IN RANGE | 56 | 34 |
| planets | SEND COLONY SHIP, SEND OUTPOST SHIP, RETURN | 46-50 | 28-30 |
| fleets | ALL, RELOCATE, SCRAP, LEADERS, SUPPORT, COMBAT, RETURN | 66 | 40 |
| fleets | PREV, NEXT (fleet) | 60 | 36 |
| leaders | COLONY LEADERS, SHIP OFFICERS (tabs) | 52 | 31 |
| leaders | HIRE, POOL, DISMISS, CANCEL, RETURN | 61-65 | 37-39 |
| leaders | PREV, NEXT, scroll up, scroll down | 43-47 | 26-28 |
| GAME menu | SAVE GAME, LOAD GAME, NEW GAME, QUIT GAME, SETTINGS, RETURN | 58-61 (seated x0.87) | 35-37 |
| GAME menu | LOAD, SAVE, CANCEL, ACCEPT, YES, NO | 42-47 | 25-28 |
| main menu | CONTINUE, LOAD GAME, NEW GAME, MULTIPLAYER, HALL OF FAME, QUIT | 50 | 30 |
| new game / custom race / empire identity | CANCEL / CLEAR, ACCEPT | 45 | 27 |
| research | EXIT | the wire's rect, ~40 | 24 |
| galaxy map | the system window's CLOSE | 38 | 23 |

The blocks already place an icon left of the word (`slant_button`,
`action_button`); a new icon needs its name added to
`core/hud/art.ICONS` and a source — either a new HUD sheet cut by
`tools/hud_cut.py`, or one file per icon under `assets/shared/hud/cut/`
through the resource roots.

## P12 — Two screens' colours moved to the HUD, their skin keys unread

`colony_summary.panel_background`, `row_a/row_b/row_selected`,
`plate_outline`, `header_background`, `header_text`, and the planets /
research box fill are read from the HUD style now; the keys stay in
`colors.json`. Deleting them is a later cleanup.
