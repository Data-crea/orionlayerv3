"""Zoom levels and sprite dimensions, transcribed from orion2re.

THREE INDEPENDENT AXES — do not conflate them:

1. ZOOM LEVEL (0..3), from MOX::_cur_map_scale via
   HAROLD::Map_Scale_To_Zoom_Level_. This is the ONLY thing that
   changes icon and font size. It changes while playing, every
   time the user hits + or -.

2. GALAXY SIZE, from MOX::_max_map_scale (recovered from
   MAP_MAX_X and MAP_MAX_Y — see max_map_scale). It does NOT
   scale anything by itself — it only caps how far out the user
   may zoom, via _max_zoom_count.
   A Huge galaxy zoomed fully IN draws exactly the same 33 px
   star as a Small galaxy, because both sit at scale 10 / zoom 0.
   The only reason a Small galaxy never shows small icons is that
   it cannot zoom out at all (max_zoom_count = 0).

3. STAR COUNT above 72, orion2re's extension beyond the original
   limit. MAP_SCALE::Star_Scale_Percent_ applies an EXTRA shrink
   of 3000/map_scale on top of axis 1, and only when map_scale
   also exceeds 30. In a vanilla game this is always 100 %.

Nothing here is measured or estimated. Sources:
  HAROLD::Map_Scale_To_Zoom_Level_       harold.cpp
  HAROLD::Map_Scale_Star_Size_To_Zoom_Level_
  MOX::_star_fields_dim[6]               harold.cpp (init)
  MAP_SCALE::Star_Scale_Percent_         map_scale.h
  MAP_SCALE::Scale_Star_Dimension_       map_scale.h
  MAINSCR::Draw_Black_Holes_ zoom_dist[] mainscr.cpp
  HAROLD::Zoom_Level_Font_Style_         harold.cpp
  MAPGEN::Set_Galaxy_Size_ switch        mapgen.cpp:1078-1120
  MAPGEN::Maximum_Galaxy_Display_Scale_  mapgen.cpp:64-71
  MAINSCR::Draw_Influence_Overlay_ (the  mainscr.cpp:161-164
    506 x 400 map rectangle)
  MAPGEN::Load_Nebula_Pictures_          mapgen.cpp + STARBG.LBX
                                         (sprite headers, see
                                          NEBULA_DIM)

The original works in native 640x480 pixels. HD rendering wants
fractions of the map width instead, so each table also has a
`*_fraction` helper dividing by MAP_WIDTH.
"""

#: Visible map width in native pixels — 527 - 22, the columns a star
#: can occupy inside the 506-wide rectangle (see GALAXY_VIEWPORT_W,
#: and mapcoords).
MAP_WIDTH = 505

#: Star count above which orion2re switches to extended scaling.
ORIGINAL_MAX_STARS = 72

#: AXIS 2 reference data (mapgen.cpp): per galaxy size, the value
#: _max_map_scale is initialised to and the highest zoom level it
#: permits. This caps the zoom RANGE only — it is deliberately not
#: consulted by any sizing function, because galaxy size does not
#: scale icons. Kept for diagnostics; the recovery itself reads
#: STOCK_MAX_MAP_SCALE, which is keyed by the MAP_MAX_X that arrives
#: on the wire rather than by a name nothing serializes.
GALAXY_MAX_SCALE = {
    "small":  (10, 0),
    "medium": (15, 1),
    "large":  (20, 2),
    "huge":   (30, 3),
}

#: MOX::_star_fields_dim — indexed by (zoom_level + star.size).
#: Six entries cover zoom 0..3 combined with size 0..2.
STAR_FIELDS_DIM = (33, 29, 25, 23, 21, 17)

#: MAINSCR::Draw_Black_Holes_ zoom_dist[4] (mainscr.cpp:706, v2
#: mainscr.cpp:873). NOT THE DRAWN SIZE: `Draw_Scaled_Star_Picture_`
#: takes it only to CENTRE the sprite, top-left = centre - zoom_dist / 2
#: (mainscr.cpp:20-28, :740). Black holes ignore star.size entirely, and
#: zoom 1 and 2 are the same value in the original.
BLACK_HOLE_DIM = (39, 33, 33, 24)

#: The black hole's drawn size: the header of BUFFER0.LBX entry
#: 148 + 6 * 6 + zoom (`Get_Star_Picture_Seg_`, mainscr.cpp:368-387, the
#: black hole skipping `+ size`), 184..187. DERIVED (decision 27: a size
#: read off the LBX is derived, not transcribed), two sources (work order
#: 310): the headers read with core/lbx.py (40 x 40, 34 x 34, 34 x 34,
#: 25 x 25, square) and zoom_dist above, which is the header less one at
#: every zoom — the centring the original wrote for this sprite. The
#: placement by zoom_dist / 2 (`black_hole_origin`) is the transcription,
#: `black_hole_draw` in renderer.render_stars.
BLACK_HOLE_HEADER_DIM = (40, 34, 34, 25)

#: Nebula footprint in native pixels, [type][zoom_level] -> (w, h).
#:
#: Not a source array and not a screenshot measurement: these are the
#: sprite header dimensions of STARBG.LBX entries 6..53, the twelve
#: types x four pre-rendered zoom variants the original swaps between
#: (mapgen.cpp Load_Nebula_Pictures_: entry = type * 4 + zoom + 6).
#: Read back by tools/nebula_extract.py; the reference PNGs and
#: summary.txt under screens/galaxy_map/assets/nebula_ref are the
#: receipt for every number below.
#:
#: Cross-check, second independent source: variant 3 doubles as the
#: gameplay shape, and geo.cpp Point_Is_In_Nebula_N_ maps world
#: coordinates onto its pixel grid through a division by 3. So
#: zoom_3_size * 3 is the nebula's extent in WORLD units, and it
#: agrees with the zoom-0 size here to within 7 % for all twelve
#: types (type 0: 183 vs 185). That is what makes the zoom-0 column
#: the world footprint at map scale 10, where one world unit is one
#: native pixel.
#:
#: The columns are close to Get_Scaled_Value_ (x 10 / map_scale, i.e.
#: 1.0 / 0.667 / 0.5 / 0.333) but not equal to it — per type the
#: measured ratios wander between 0.62 and 0.75 at zoom 1. A formula
#: therefore cannot replace this table, and the artwork's own pixel
#: size must never stand in for it: HD masters are drawn at whatever
#: resolution the artist worked at.
#:
#: NOTE: the renderer does NOT size nebulas from the zoom columns —
#: it uses column 0 as a world footprint and scales it continuously
#: (nebula_native_dimension). The columns 1..3 are kept as the
#: transcription and as the receipt for column 0; the reason the
#: drawn size no longer follows them is written out there.
NEBULA_DIM = (
    ((185, 174), (138, 132), ( 87,  83), ( 61,  56)),   #  0
    ((176, 179), (124, 129), ( 86,  88), ( 48,  51)),   #  1
    ((190, 184), (131, 127), ( 90,  87), ( 66,  67)),   #  2
    ((158, 171), (119, 125), ( 78,  80), ( 57,  56)),   #  3
    ((206, 192), (137, 127), ( 99,  92), ( 65,  60)),   #  4
    ((202, 191), (134, 127), ( 96,  89), ( 67,  63)),   #  5
    ((192, 183), (135, 127), ( 88,  84), ( 60,  55)),   #  6
    ((190, 186), (127, 122), ( 86,  84), ( 64,  64)),   #  7
    ((171, 176), (118, 124), ( 81,  83), ( 53,  55)),   #  8
    ((170, 184), (105, 114), ( 81,  90), ( 61,  58)),   #  9
    ((201, 189), (136, 132), ( 98,  94), ( 63,  61)),   # 10
    ((209, 206), (130, 132), ( 94,  93), ( 64,  64)),   # 11
)

#: TRANSCRIPTION `nebula_zoom3_hold`: the original draws the variant of
#: its zoom level unchanged (Draw_Nebulae_ never scales), so past the
#: scale that variant is drawn for the nebula keeps its size while the
#: map shrinks. On an ordinary map Map_Scale_To_Zoom_Level_ answers 3 for
#: every scale beyond 20 (harold.cpp:1086-1110), so the hold is at 30; on
#: an extended one (over 72 stars) the level comes from
#: Extended_Zoom_Level_For_Scale_ (map_scale.h:25-32): zoom 2 runs up to
#: max_map_scale - 1 and zoom 3 is only the maximum itself.
NEBULA_HOLD_SCALE = 30

#: The scale each zoom level's variant is drawn for on an ordinary map
#: (the vanilla ladder, `scale_rungs`): the zoom-z variant is the
#: footprint x 10 / NEBULA_RUNG_SCALE[z], within the variants' own
#: 12 to 25 % wander (nebula_native_dimension).
NEBULA_RUNG_SCALE = (10, 15, 20, NEBULA_HOLD_SCALE)

#: Number of nebula shapes; savegame.cpp and netmox.cpp both reject a
#: savegame with type outside 0..11, and Draw_Nebulae_ indexes with
#: type % 12.
NEBULA_TYPE_COUNT = len(NEBULA_DIM)

#: Whether an extended galaxy (> 72 stars, map_scale > 30) shrinks
#: nebulas the way it shrinks stars. SETTLED False (work order 310):
#: Draw_Nebulae_ draws `_nebula_pict_seg[type % 12][zoom_level]` with
#: animate::Draw_ and never consults Star_Scale_Percent_ or scales
#: (mainscr.cpp:941-963), like the ship icons.
NEBULA_EXTENDED_SHRINK = False

#: HAROLD::Zoom_Level_Font_Style_ — the original picks a font
#: STYLE, not a pixel size. Mapped here to relative text scale so
#: an HD renderer can pick a proportional size.
FONT_SCALE_BY_ZOOM = (1.00, 0.86, 0.86, 0.72)

#: SHIPS::Get_XYs_For_Orbiting_Ships_ — vertical spacing between
#: stacked orbit slots is (11 - zoom_level) native pixels.
ORBIT_STACK_STEP_BASE = 11

#: Ship icon footprint in native pixels, indexed by zoom level.
#:
#: DERIVED, not transcribed — mark any change as a deviation. Unlike
#: the star table there is no array in the source: the sizes live in
#: BUFFER0.LBX (SHIPS::Get_Ship_Icon_Pict_Seg_ loads entry
#: 205 + colour*4 + (3 - zoom)) and are only read back at runtime into
#: MOX::_ship_icon_width/_height[4] (ships.cpp:328).
#:
#: MEASURED, 29 August, from a native 640x480 screenshot: the central
#: blob of the sprite, threshold-swept and cross-checked against the
#: pixel map, is 11 x 10 px at zoom 0. See
#: dev:doc/ship_icon_measurement.md for the method and why it matters.
#:
#: The per-step shrink is one pixel, from the only hint the source
#: gives: MAINSCR::Do_Fleet_Popup_ passes (13 - zoom, 9 - zoom) to
#: Overlapped_Ship_Icon_Button_ as proximity thresholds. Those numbers
#: are NOT the icon size — threshold_y is smaller than the measured
#: height — but the -1 per zoom step is.
#:
#: The height must stay below the orbit stack step (11 - zoom), or
#: four fleets at one star collide. 10 < 11 at every step.
#:
#: DELIBERATE DEVIATION from the sprite header the game positions with,
#: Data's decision of 15 September 2026 (work order 122, item 2.2): the
#: header table below is SHIP_ICON_HEADER_DIM = ((11, 11), (12, 11), (12, 10), (16, 12)),
#: indexed 3 - zoom, and this one stays as measured because the HD icon's
#: click area at these sizes is live-confirmed. Marked in
#: `screens/galaxy_map/maplines.py`; the smoke test holds this comment to
#: the header table's current values.
SHIP_ICON_DIM = ((11, 10), (10, 9), (9, 8), (8, 7))

#: The header size of BUFFER0.LBX entries 205..208, index = entry - 205:
#: what `SHIPS::Get_Ship_Icon_Dimensions_(index)` returns
#: (`animate::Get_Width_/Get_Height_`, ships.cpp:328-335) and what the
#: game positions with — ALWAYS colour 0's entries, whatever the owner.
#: `Draw_Ship_Destination_Line_` asks for index 3 - zoom (the line starts at
#: the icon corner plus half of it, ships.cpp:535-552);
#: `Get_Ship_Icon_Coords_In_Space_` asks for index zoom (ships.cpp:516-531).
#:
#: MEASURED AT THE SPRITE, brief 121 (the open point of run 114), two
#: sources: the LBX headers read with core/lbx.py, and the live framebuffer
#: on SAVE5 — at zoom 2 entry 218 (colour 3) was drawn at s_ship_icon.x/y
#: pixel for pixel (30/30) with its 12 x 11 header, and the green line began
#: at the corner plus (6, 5); at zoom 0 it began at plus (8, 6), half of
#: index 3's 16 x 12, where index 0's 11 x 11 matched 2 pixels of 74.
#: NOT SHIP_ICON_DIM, which is 9 x 8 at zoom 2: that table sizes the HD
#: icon and is left as it is (dev:doc/ship_icon_measurement.md). DELIBERATE
#: DEVIATION between the two, work order 122 item 2.2: SHIP_ICON_DIM =
#: ((11, 10), (10, 9), (9, 8), (8, 7)); the smoke test holds this comment to
#: its current values.
SHIP_ICON_HEADER_DIM = ((11, 11), (12, 11), (12, 10), (16, 12))

#: The same headers for EVERY player colour: BUFFER0.LBX entry
#: 205 + colour * 4 + index, index = 3 - zoom, [colour][index] =
#: (width, height). `SHIPS::Print_Eta_On_Ship_Icon_` (ships.cpp:482-506)
#: places the "eta N" label with the header of the OWNER's own sprite
#: (`Get_Ship_Icon_Pict_Seg_(player_idx, 0)`, :337-367, colour from
#: `_player[].color`), not colour 0's — so this table, not the one above,
#: is what that label needs. Row 0 IS `SHIP_ICON_HEADER_DIM` (a smoke check
#: holds the two equal). MEASURED, work order 122 item 2.1, 16 September
#: 2026: read from the headers with core/lbx.py, and the label's position
#: confirmed live in the framebuffer for the colours the run could see
#: (dev:v3_projektstatus.md, "the eta digit").
SHIP_ICON_HEADER_DIM_BY_COLOUR = (
    ((11, 11), (12, 11), (12, 10), (16, 12)),
    ((11, 11), (12, 11), (13, 10), (16, 12)),
    ((11, 11), (11, 11), (13, 12), (17, 14)),
    ((11, 11), (12, 11), (13, 12), (17, 14)),
    ((11, 11), (12, 11), (14, 12), (17, 14)),
    ((11, 11), (12, 11), (14, 12), (17, 14)),
    ((11, 11), (12, 11), (14, 12), (17, 14)),
    ((11, 11), (11, 11), (14, 12), (16, 14)),
)

#: The "eta N" label's font style by zoom — `style_toggle <= 1 ? 1 : 0`
#: (ships.cpp:496-497) — and the INK HEIGHT of a digit in each of the two
#: styles, in native pixels: 5 rows in style 0, 7 in style 1. The heights
#: are not in any source: they are glyphs of the player's FONTS.LBX entry
#: 0 (`fonts::Load_Font_File_`, fonts.cpp:887; glyphs as
#: `Print_Character_ASM_` walks them, :46). MEASURED, 16 September 2026,
#: by decoding every digit of both styles, and confirmed against the live
#: framebuffer the same day. HD sizes the label's digits to rows * px.
ETA_FONT_STYLE_BY_ZOOM = (1, 1, 0, 0)
ETA_DIGIT_INK_ROWS = (5, 7)

#: Monster icons, per kind and zoom level — TRANSCRIPTION `monster_icon_dim`
#: of the sprite the original picks; the sizes themselves are DERIVED
#: (decision 27): read back off BUFFER0.LBX, as the game reads them at
#: runtime (work order 310, replacing the zoom-0 screenshot table and its
#: "one pixel less a step"). Which sprite the original draws is
#: `SHIPS::Get_Ship_Icon_Pict_Seg_` (ships.cpp:337-397, v2 the same):
#: owner 8 (Antaran) BUFFER0.LBX 237 + (3 - zoom), backwards like the
#: player; owners 9..14 241 + (owner - 9) * 4 + zoom, forwards.
#:
#: TWO SIZES PER SPRITE, AND THEY ARE NOT THE SAME THING.
#:
#: MONSTER_ICON_HEADER_DIM is the entry's header (w, h): the box the
#: game anchors at s_ship_icon.x/y and whose width
#: `Get_XYs_For_Orbiting_Ships_` halves (ships.cpp:290-291). Read with
#: core/lbx.py off the player's BUFFER0.LBX; the second source is the
#: entries' own frame streams, which decode inside exactly these bounds
#: (core/lbx.decode_packed refuses a run past them).
#:
#: MONSTER_ICON_DIM is (x0, y0, w, h), the box of the pixels the game
#: actually draws (index != 0, all eight frames, composed): the HD
#: icon's size and, from (x0, y0), its place inside the header box. The
#: headers carry up to nine pixels of empty margin — the crystal is
#: 15 x 13 at every zoom and draws 6 x 6 at zoom 3 — and the HD masters
#: are cropped to their content, so a header-sized box would draw the
#: crystal two and a half times the original's. Two sources: the
#: decode of work order 310, and dev:doc/ship_icon_measurement.md's
#: 14 September sweep, whose t0 column (another decoder, through the
#: game's palette) gives the same zoom-0 boxes for all six it measured,
#: while its live framebuffer at zoom 3 matched each monster's entry
#: pixel for pixel.
MONSTER_ICON_HEADER_DIM = {
    "antaran":  ((18, 15), (14, 12), (12, 10), (11, 10)),   # 240..237
    "guardian": ((16, 13), (14, 11), ( 9,  9), ( 7,  7)),   # 241..244
    "amoeba":   ((15, 15), (12, 13), (10, 11), ( 9,  9)),   # 245..248
    "crystal":  ((15, 13), (15, 13), (15, 13), (15, 13)),   # 249..252
    "dragon":   ((15, 15), (12, 14), ( 9,  9), ( 9,  9)),   # 253..256
    "eel":      ((17,  7), (13,  7), (11,  7), ( 8,  6)),   # 257..260
    "hydra":    ((15, 14), (12, 11), ( 8,  9), ( 7,  8)),   # 261..264
}
MONSTER_ICON_DIM = {
    "antaran":  ((2, 2, 13, 11), (2, 2, 10, 8), (2, 2, 7, 6), (3, 3, 5, 4)),
    "guardian": ((2, 1, 13, 11), (2, 1, 11, 9), (0, 1, 8, 7), (1, 1, 5, 5)),
    "amoeba":   ((1, 1, 13, 14), (1, 2, 10, 10), (2, 2, 6, 8), (2, 1, 5, 6)),
    "crystal":  ((0, 1, 15, 12), (2, 2, 12, 10), (4, 4, 8, 6), (5, 3, 6, 6)),
    "dragon":   ((1, 0, 13, 15), (1, 1, 10, 13), (2, 0, 7, 9), (2, 2, 6, 5)),
    "eel":      ((1, 1, 15, 5), (1, 1, 12, 4), (2, 1, 7, 4), (2, 1, 5, 4)),
    "hydra":    ((1, 1, 13, 13), (1, 1, 10, 9), (1, 1, 6, 7), (1, 1, 5, 6)),
}

#: The monster sprite export for the Planets panel, longest edge in px.
#: **HD EXTENSION, DERIVED** — a size for the HD artwork, not a
#: transcription (the original shows no monster outside combat).
#:
#: 314 = the panel's sprite box, 157 reference px on its long edge in
#: screens/planets/boxes.json when this was set, times 2.0, the layout
#: scale at 3840x2160 (core/layout.py, min(w/1920, h/1080)). Designed
#: for the 4K box so the panel only ever scales DOWN. Typed here, not
#: read from the box: a box can be dragged, an export cannot follow it,
#: and the smoke test says so when the box outgrows the export.
MONSTER_PANEL_SPRITE_PX = 314

#: Its file, beside the four map steps in ships/<kind>/ (derived, ignored).
MONSTER_PANEL_SPRITE_FILE = "panel.png"

#: Smallest footprint an icon may shrink to, native pixels.
MIN_ICON_DIM = 4

#: The galaxy viewport the two ceilings below divide by, in native
#: 640x480 pixels. **506 x 400 is the RECTANGLE**, declared under
#: those names by `MAINSCR::Draw_Influence_Overlay_` (mainscr.cpp:
#: 161-164, `map_left = 22, map_top = 22, map_width = 506,
#: map_height = 400`) and confirmed live: the galaxy map's field 23
#: arrives on the wire as (22, 22)-(527, 421), which is 506 columns
#: and 400 rows counted inclusively.
#:
#: `mapcoords.MAP_WIDTH` is 505 and the fundament says 505 x 399, and
#: that is the SAME rectangle counted differently, not a second one:
#: `MAINSCR::Star_On_Screen_` (mainscr.cpp:399-410) admits the near
#: edge (`x > 0x15` passes at 22) and excludes the far one
#: (`x < 0x20f` stops at 526), so a star reaches 505 of the 506
#: columns and 399 of the 400 rows. The rectangle is what the scale
#: has to cover, so the rectangle is what the ceilings divide by.
GALAXY_VIEWPORT_W = 0x1FA        # 506, mapgen.cpp:68
GALAXY_VIEWPORT_H = 0x190        # 400, mapgen.cpp:69

#: The four stock galaxy sizes' MAP_MAX_X -> _max_map_scale, as
#: mapgen.cpp:1078-1110 assigns them: literal constants beside a
#: literal `_MAP_MAX_X`/`_MAP_MAX_Y`, never through the function
#: below. Transcribed as the switch writes them, because that is what
#: the switch is; `maximum_galaxy_display_scale` reproduces all four
#: and a smoke check holds it to them.
STOCK_MAX_MAP_SCALE = {506: 10, 759: 15, 1012: 20, 1518: 30}

#: `raw_cell_size`, mapgen.cpp:65 and :1113 — the same expression in
#: both places: MAXIMUM_GALAXY_CELL_SIZE 50 * MAXIMUM_GALAXY_MAP_SCALE
#: 30 / 10. The Maximum galaxy is a grid of cells this wide.
MAXIMUM_GALAXY_CELL = 150

#: max_map_scale -> max_zoom_count (mapgen.cpp, same switch).
MAX_ZOOM_BY_SCALE = {10: 0, 15: 1, 20: 2, 30: 3}


#: ── THE COLONY SUMMARY'S OWN TWO TABLES ────────────────────
#:
#: Both are **HD EXTENSIONS** and neither is a rung of anything
#: above. They live here because this is where a size a renderer may
#: use is allowed to come from, and because a literal in a draw call
#: is a defect.

#: The population figure's integer step, per resolution.
#: **HD EXTENSION, DERIVED.**
#:
#: A figure is 28 x 28 native px — every people entry of
#: RACEICON.LBX carries that header, and `raceicon_ref/summary.txt`
#: is the receipt. The layout scales are 1, 4/3 and 2
#: (`core/layout.py`, min(w/1920, h/1080)), so a step of 2 at 1080p
#: scales to 2.667 and 4 — and **2.667 is not an integer**. Read the
#: other way round, against the original's own screen, 1920/640 is 3
#: and 1080/480 is **2.25**, 3840/640 is 6 and 2160/480 is **4.5**:
#: the proportional answer is fractional whichever end it is taken
#: from, and in one axis only, which would also make the figure
#: anisotropic.
#:
#: Nearest-neighbour at a fractional step invents pixels the original
#: does not have, and a reference figure may not do that. So the
#: steps are integers and the deviation is in the SIZE rather than in
#: the pixels: 56 / 84 / 112 px against the proportional 63 / 84 /
#: 126. 1440p is exact; 1080p draws 11 % small and 2160p 11 % small.
#:
#: `screens/colony_summary/layout_reference.json` holds the same
#: table as a design input and its list height depends on it — that
#: file is where a change is made, and this is where a renderer reads
#: it.
#: **THE PER-RESOLUTION TABLE IS GONE — 8 September 2026.** It read
#: `{"1920x1080": 2, "2560x1440": 3, "3840x2160": 4}`, and every one
#: of those three was a hand-written answer to a question the LAYOUT
#: can answer: the colony list holds ten rows (the original's own
#: window, colsum.cpp:348), so a row band is the window divided by
#: ten and the step is the largest whose figure fits it. At the list
#: window this project shipped until that day, the derived answer at
#: 2560x1440 was 2 and the table said 3 — the table was declaring a
#: step the band could not hold, and `colonylist._render_bar` clipped
#: the overflow every frame. The window grew 29 ref px and the table
#: went; `colonytrack.figure_step` is the derivation and
#: `screens/colony_summary/layout_reference._list_height_note` is
#: the arithmetic.
#:
#: What stays here is the LADDER — which integer steps exist at all,
#: because that is a property of the sprites and not of a screen.
#:
#: **1 IS ON IT, AND IT IS THE MASTER ITSELF.** A step is an integer
#: nearest-neighbour swap (decision 28) and a master is 28 x 28, so
#: step 1 is the master drawn at its own size — which is the right
#: answer below the reference resolution: at 1280x720 the list band
#: is 42 device px and even a 2x figure needs 57. It was left off
#: while this was a three-entry table keyed by the three resolutions
#: this project ships at, and a window smaller than 1920x1080 had no
#: entry at all. **It is NOT on `colonyfigures.STEPS`**, which is the
#: list of steps a MOD may ship as an explicit `@Nx` file: `@1x`
#: would be a second name for the master, and decision 50's whole
#: point is one PNG with one documented name.
FIGURE_STEPS = (1, 2, 3, 4)

#: The three job columns of the colony list, NATIVE, and what the
#: original states about them is a RATIO. **TRANSCRIBED** from
#: `COLSUM::Get_Selected_Pop_` (colsum.cpp:1006-1024) and
#: `Add_Fields_Pop_For_` (colsum.cpp:311-345), which pass the bounds
#: as literals: `left_x` 101 / 236 / 378 and `right_x` = the next
#: `left_x` - 10. The DRAWN spans are the separators either side —
#: 100 / 235 / 377 / 511, measured on
#: `~/claude/evidence/colony_summary_native_split.png` at
#: 1:1 — giving **135 : 142 : 134, with WORKERS the widest**.
#:
#: **THE RATIO IS THE TRANSCRIPTION AND THE WIDTH IS NOT.** HD's job
#: columns are 2.53x their native ones, which is Data's Stage 1
#: decision to send the extra HD width to the column reservation
#: rather than to figure spacing; the absolute number is therefore
#: ours and only the proportion among the three is the original's. A
#: check measures every column box against this and reports the
#: deviation into `dev:v3_projektstatus.md`, red only where one is
#: unmarked (decision 36's shape: a hand-editable value gets a
#: checker, not a reminder).
NATIVE_JOB_COLUMNS = {"farmers": 135, "workers": 142, "scientists": 134}

#: Where a HELD cluster's figures sit beside the pointer, in NATIVE
#: px, and the pitch between them when more than one is held.
#: **TRANSCRIBED** from `COLMOVE::Draw_Cluster_` (colmove.cpp:7-37),
#: which the colony summary calls last in its own draw with the raw
#: pointer — `COLMOVE::Draw_Cluster_(mouse::Pointer_X_(),
#: mouse::Pointer_Y_())` (colsum.cpp:509-511):
#:
#:     animate::Draw_(x, y, C_Anims_(15))     the pointer picture
#:     current_x = x + 5                      colmove.cpp:23
#:     animate::Draw_(current_x, y - 10, …)   colmove.cpp:27
#:     current_x += 20                        colmove.cpp:28
#:
#: So the first figure sits five px right of and ten px ABOVE the
#: pointer, overlapping it, and further held pops step 20 px — which
#: is neither the icon spacing (30) nor the squished pitch. Only
#: pops whose `0x200` is clear are drawn, so the cluster on the
#: cursor and the icons missing from the row are one fact.
#:
#: **DEVIATION — THEY ARE MULTIPLIED BY `FIGURE_STEP`, AND NOTHING ON
#: THIS SCREEN HAS ONE MAGNIFICATION.** The offsets are native px
#: measured against a 28 px sprite, so the only companion that keeps
#: the picture the original's is the sprite's own integer step
#: (decision 28): at step 3 a figure three times the size sits three
#: times as far out, and the overlap with the pointer is the
#: original's. The layout scale would not do it — 1.333 against a
#: figure at 3 would tuck the figure into the pointer at 1440p and
#: away from it at 1080p.
#:
#: What makes it a DEVIATION rather than plain arithmetic is what
#: the multiplication is NOT consistent with. The colony row's job
#: columns are 342/360/339 reference px against the original's
#: 135/142/134, a scale of 2.53, while the figure steps 2/3/4; the
#: pointer itself is 4.38 % of window height (`core/cursor.py`), a
#: third factor again. Three magnifications live on one screen and
#: this constant picks the sprite's, because the thing it positions
#: is a sprite. Stated here, in `colonylist.draw_held_cluster`, and
#: in `dev:v3_projektstatus.md`.
CLUSTER_FIGURE_OFFSET = (5, -10)
CLUSTER_FIGURE_PITCH = 20

#: The galaxy inset's star dot, per resolution, in device pixels.
#: **HD EXTENSION, DERIVED — and ODD BY REQUIREMENT.**
#:
#: The original's inset star is not on any axis above: `gstar.lbx`
#: entries 23..32 are 3 x 3 with 8 frames whatever the galaxy size
#: and whatever the zoom (`COLONY::Load_Galaxy_Map_Anims_`,
#: colony.cpp:329-339), where `STAR_FIELDS_DIM` and
#: `star_dimension()` answer about the galaxy map's zoom levels.
#: There is no rung to read, so the size is derived.
#:
#: The derivation, in world units, from `dev:doc/colony_inset_geometry.md`
#: Part 3: the original's dot is 3 native px, which is
#: `3 * M * 3953/10000` world units wide and `3 * M * 4395/10000`
#: tall; at the HD inset's scale of `5/M` reference px per world unit
#: that is **5.93 x 6.59 reference px at every galaxy size** — M
#: cancels, which is the same statement as "the original's dot is a
#: fixed 3 px whatever the size". Times the layout scale: 5.93, 7.91,
#: 11.86.
#:
#: **ODD, AND NOT BY TASTE.** The original draws the dot at
#: `(sx - 1, sy - 1)` (movebox.cpp:103) so that the computed pixel IS
#: the centre — a 3 px dot has one. An even size has no centre pixel,
#: so the computed star position could only be placed half a pixel
#: off, and "the star is drawn where the transform says" would stop
#: being checkable. The requirement therefore picks the size, and
#: what is left is which odd number is nearest: 5 over 7 (0.93 against
#: 1.07), 7 over 9 (0.91 against 1.09), 11 over 13 (0.86 against
#: 1.14).
#:
#: The consequence, stated rather than hidden: the dot does NOT scale
#: with the layout. 5 / 7 / 11 is 1.0 / 1.4 / 2.2 where the layout is
#: 1.0 / 1.333 / 2.0, so the dot is up to 10 % large at 2160p
#: relative to 1080p. That is the price of a centre pixel at every
#: resolution, and it is smaller than the half-pixel it buys.
INSET_DOT_DIM = {"1920x1080": 5, "2560x1440": 7, "3840x2160": 11}

#: What INSET_DOT_DIM was rounded FROM, kept beside it so the choice
#: can be re-checked without re-deriving it — the same reason
#: NEBULA_DIM keeps its zoom columns.
INSET_DOT_TARGET = {"1920x1080": 5.93, "2560x1440": 7.91,
                    "3840x2160": 11.86}


def inset_dot_origin(centre, dim):
    """Top-left of a dot of `dim` px whose CENTRE pixel is `centre`.

    `movebox.cpp:103` draws at `(sx - 1, sy - 1)` for a 3 px sprite,
    which is `(dim - 1) // 2`. One function so the renderer and the
    check cannot disagree about where a dot goes — decision 5, in the
    smallest thing it applies to.
    """
    return centre - (int(dim) - 1) // 2


def maximum_galaxy_display_scale(map_max_x, map_max_y):
    """MAPGEN::Maximum_Galaxy_Display_Scale_, mapgen.cpp:64-71.

    The scale at which the whole galaxy fits the map viewport: per
    axis, the smallest scale whose `HAROLD::Get_Scaled_Value_`
    (`v * 10 / scale`, harold.cpp:169) puts the far edge inside the
    506 x 400 rectangle — then the LARGER of the two, because an axis
    that does not fit is an axis the player cannot see.

    **A CEILING, NOT A ROUNDING**, written in the original as the
    integer idiom `(a + b - 1) / b`. That one word is the whole of
    the defect this function replaced: `round(map_max_x / 50.6)`
    agreed on the four stock sizes it was measured from and came out
    exactly one too small — never too large — for 688 of the 951 star
    counts in 73..1023, at 15 distinct map widths.

    The function in orion2re takes no arguments: it derives the
    galaxy's extent from `_maximum_star_count` through
    `Maximum_Galaxy_Grid_X_/Y_` (mapgen.cpp:49-59) times
    `raw_cell_size`. **Those two products are character for character
    what the same branch assigns to `MOX::_MAP_MAX_X` and `_MAP_MAX_Y`
    ten lines later** (mapgen.cpp:1113-1115), and both are on the wire
    (ext_api.cpp:113-114). So the extent is READ rather than rebuilt,
    and no star count enters here.

    Verified two ways before it replaced anything (fundament, "two
    independent sources"): the function above, and a live probe on
    7 September 2026 — a generated 155-star Maximum galaxy, MAP_MAX
    2250 x 1800, whose own zoom-out limit the game reported as
    **45**, where the retired estimate said 44.
    """
    if not map_max_x or not map_max_y or map_max_x <= 0 or map_max_y <= 0:
        return 0
    scale_x = (int(map_max_x) * 10 + GALAXY_VIEWPORT_W - 1) // GALAXY_VIEWPORT_W
    scale_y = (int(map_max_y) * 10 + GALAXY_VIEWPORT_H - 1) // GALAXY_VIEWPORT_H
    return max(scale_x, scale_y)


def max_map_scale(map_max_x, map_max_y):
    """Recover MOX::_max_map_scale, transcribing the mapgen switch.

    `MAPGEN::Set_Galaxy_Size_` (mapgen.cpp:1078-1120) answers this in
    two different ways and so does this function, in the same order:
    the four stock sizes get a literal beside a literal MAP_MAX
    (STOCK_MAX_MAP_SCALE), and GALAXY_SIZE_MAXIMUM gets
    `Maximum_Galaxy_Display_Scale_()`. Nothing is estimated from a
    ratio any more, at either size. Returns 0 for an extent no galaxy
    size produces, which callers read as "unknown" rather than
    substituting a value that would silently change rendering.

    **MAP_MAX_Y HAS NO DEFAULT, DELIBERATELY.** It is on the wire
    beside x (ext_api.cpp:113-114) and every caller in the tree has
    the state object it comes from, so a default would exist only to
    let the next caller forget it — and forgetting it is precisely
    the defect this function replaced: the y ceiling is the larger of
    the two at 4 of the 15 map widths where the retired estimate was
    wrong. A missing argument is a TypeError where it is written; a
    defaulted 0 is a wrong scale, at one galaxy size, on a screen
    where every other number stays correct. A smoke check refuses a
    one-argument call site anywhere in the tree, because a TypeError
    only fires on the path that runs.

    The stock branch keys on MAP_MAX_X alone and that is not an
    exception to the above: 506, 759, 1012 and 1518 each name one arm
    of the switch, and the switch assigns the scale as a literal
    without consulting either extent. Their extents are literals too,
    not grid products — 506 is not a multiple of the 150-unit cell —
    so nothing about a stock size can be re-derived from a grid, and
    an inversion could never have served one.
    """
    if not map_max_x or map_max_x <= 0:
        return 0
    stock = STOCK_MAX_MAP_SCALE.get(int(map_max_x))
    if stock:
        return stock
    return maximum_galaxy_display_scale(map_max_x, map_max_y)


def max_zoom_count(map_max_x, map_max_y):
    """Recover MOX::_max_zoom_count, mapgen.cpp's same switch.

    0/1/2/3 for the four stock sizes; GALAXY_SIZE_MAXIMUM sets 3
    outright (mapgen.cpp:1118), which is what an unknown scale gets
    too — the zoom RANGE is the one thing a Maximum galaxy shares
    with Huge. Both extents required, for max_map_scale's reason.
    """
    scale = max_map_scale(map_max_x, map_max_y)
    return MAX_ZOOM_BY_SCALE.get(scale, 3)


def scale_rungs(max_zoom_count=3, num_stars=0, max_map_scale=None):
    """The map_scale values the game itself can stand on.

    Vanilla ladder 10/15/20/30 up to `max_zoom_count`; the extended
    ladder (over 72 stars) is built by halving max_map_scale, exactly
    as _extended_scale_for_zoom does. Sorted ascending.
    """
    if num_stars > ORIGINAL_MAX_STARS and max_map_scale:
        rungs = sorted({_extended_scale_for_zoom(
            max_map_scale, max_zoom_count, lvl)
            for lvl in range(0, max_zoom_count + 1)})
    else:
        rungs = [10, 15, 20, 30][:max_zoom_count + 1] or [10]
    return rungs


def hd_zoom_level(map_scale, max_zoom_count=3, num_stars=0,
                  max_map_scale=None):
    """Zoom level for a CONTINUOUS scale. HD EXTENSION, NOT TRANSCRIBED.

    The decoupled HD viewport zooms smoothly, so its scale sits
    between the rungs the original can stand on — and the transcribed
    zoom_level() answers "not a rung" with max zoom, which would draw
    the smallest sprites while nearly fully zoomed in. This helper
    snaps the scale to the NEAREST rung (ties toward the zoomed-in
    one) and asks the transcription about that rung, so on-rung
    values, including everything the game itself reports, answer
    exactly as before. The deviation is confined to the in-between
    values the original never produces.
    """
    return zoom_level(hd_rung(map_scale, max_zoom_count, num_stars,
                              max_map_scale),
                      max_zoom_count, num_stars, max_map_scale)


def hd_rung(map_scale, max_zoom_count=3, num_stars=0, max_map_scale=None):
    """The rung hd_zoom_level snaps a continuous scale to — what stands in
    for `MOX::_cur_map_scale` where the original compares the scale itself
    (`Get_Ship_Icon_Coords_`, ships.cpp:231). HD EXTENSION, as above."""
    rungs = scale_rungs(max_zoom_count, num_stars, max_map_scale)
    return min(rungs, key=lambda r: (abs(map_scale - r), r))


def zoom_level(map_scale, max_zoom_count=3, num_stars=0,
               max_map_scale=None):
    """HAROLD::Map_Scale_To_Zoom_Level_.

    Returns 0..3. `max_zoom_count` clamps the result, exactly as
    the original does — a small galaxy never leaves zoom 0.

    `max_map_scale` is only consulted on the extended path (more
    than 72 stars), where the scale ladder is built by halving it
    rather than by the fixed 10/15/20 comparison. **It has to be
    passed there.** Omitting it makes _extended_zoom_level fall back
    to `map_scale`, which satisfies its own top rung at every scale
    and pins an extended galaxy to max_zoom no matter how far the
    player zooms in — every sprite, font and icon then draws at its
    smallest step. That was the state until 29 August; the argument
    existed on the inner function and no caller supplied it.
    """
    if num_stars > ORIGINAL_MAX_STARS:
        return _extended_zoom_level(map_scale, max_zoom_count,
                                    max_map_scale)

    if map_scale == 10 and max_zoom_count >= 0:
        return 0
    if map_scale == 15 and max_zoom_count >= 1:
        return 1
    if map_scale == 20 and max_zoom_count >= 2:
        return 2
    if map_scale not in (10, 15, 20) and max_zoom_count >= 3:
        return 3
    return max_zoom_count


def _extended_scale_for_zoom(max_map_scale, max_zoom, level):
    """MAP_SCALE::Extended_Scale_For_Zoom_Level_ — repeated halving."""
    level = max(0, level)
    if level >= max_zoom:
        return max_map_scale
    scale = max_map_scale
    for _ in range(max_zoom, level, -1):
        scale = (scale + 1) // 2
    return scale


def _extended_zoom_level(map_scale, max_zoom, max_map_scale=None):
    """MAP_SCALE::Extended_Zoom_Level_For_Scale_."""
    if max_map_scale is None:
        max_map_scale = map_scale
    for level in range(max_zoom, 0, -1):
        if map_scale >= _extended_scale_for_zoom(
                max_map_scale, max_zoom, level):
            return level
    return 0


def star_scale_percent(num_stars, map_scale):
    """MAP_SCALE::Star_Scale_Percent_.

    100 in every ordinary game. Only a galaxy with more stars than
    the original supported, viewed beyond scale 30, shrinks icons.
    """
    if num_stars <= ORIGINAL_MAX_STARS or map_scale <= 30:
        return 100
    return 3000 // map_scale


def scale_star_dimension(dimension, percent):
    """MAP_SCALE::Scale_Star_Dimension_ — never below 3 px."""
    if percent >= 100:
        return dimension
    dimension = (dimension * percent) // 100
    return 3 if dimension < 3 else dimension


def star_dimension(star_size, zoom, num_stars=0, map_scale=10):
    """Native pixel size of a star icon.

    HAROLD::Map_Scale_Star_Size_To_Zoom_Level_: the zoom level and
    the star's own size index the SAME table, added together.
    """
    idx = zoom + int(star_size)
    idx = max(0, min(len(STAR_FIELDS_DIM) - 1, idx))
    return scale_star_dimension(
        STAR_FIELDS_DIM[idx], star_scale_percent(num_stars, map_scale))


def black_hole_dimension(zoom, num_stars=0, map_scale=10):
    """Native pixel size a black hole is DRAWN at (ignores star.size):
    its sprite header, shrunk as `Draw_Scaled_Star_Picture_` shrinks it
    on an extended map (mainscr.cpp:20-46, :43)."""
    zoom = max(0, min(len(BLACK_HOLE_HEADER_DIM) - 1, zoom))
    return scale_star_dimension(
        BLACK_HOLE_HEADER_DIM[zoom], star_scale_percent(num_stars, map_scale))


def black_hole_origin(zoom, num_stars=0, map_scale=10):
    """Native distance from the black hole's draw point to its sprite's
    top-left. At full size `centre - zoom_dist / 2` (mainscr.cpp:28, :740),
    one pixel less than half the sprite; shrunk, the scaled picture's own
    half width (:43)."""
    zoom = max(0, min(len(BLACK_HOLE_DIM) - 1, zoom))
    if star_scale_percent(num_stars, map_scale) >= 100:
        return BLACK_HOLE_DIM[zoom] // 2
    return black_hole_dimension(zoom, num_stars, map_scale) // 2


def black_hole_animates(num_stars, map_scale):
    """MAP_SCALE::Advance_Black_Hole_Animation_.

    The original freezes black hole animation once icons are being
    shrunk — a huge galaxy at maximum zoom-out has still frames.
    """
    return star_scale_percent(num_stars, map_scale) >= 100


def names_suppressed(num_stars, map_scale, max_map_scale):
    """MAINSCR::Print_Star_Names_ bails out entirely here.

    MAP_SCALE::Is_Extended_Max_Map_View_: a galaxy larger than the
    original maximum, viewed at its widest, draws no star names at
    all — they would be unreadable and overlap.
    """
    return (num_stars > ORIGINAL_MAX_STARS
            and map_scale == max_map_scale)


def orbit_stack_step(zoom):
    """Vertical spacing of stacked orbit slots, native pixels."""
    return ORBIT_STACK_STEP_BASE - max(0, min(3, zoom))


def ship_icon_dimension(zoom):
    """(width, height) of a player ship icon in native pixels.

    Ship icons are NOT affected by star_scale_percent: the original
    has no scaling path for them at all (Get_Ship_Icon_Pict_Seg_ just
    picks a sprite). On an extended galaxy zoomed all the way out the
    stars shrink and the ships do not — that is original behaviour,
    not an oversight here.
    """
    zoom = max(0, min(len(SHIP_ICON_DIM) - 1, int(zoom)))
    return SHIP_ICON_DIM[zoom]


def ship_icon_header_dimension_for_colour(colour, index):
    """(width, height) of BUFFER0.LBX entry 205 + colour * 4 + index's
    header, both clamped — the owner's own sprite (Print_Eta_On_Ship_Icon_)."""
    colour = max(0, min(len(SHIP_ICON_HEADER_DIM_BY_COLOUR) - 1, int(colour)))
    index = max(0, min(3, int(index)))
    return SHIP_ICON_HEADER_DIM_BY_COLOUR[colour][index]


def ship_icon_header_dimension(index):
    """(width, height) of BUFFER0.LBX entry 205 + index's header, index
    clamped to 0..3 as `Draw_Ship_Destination_Line_` clamps 3 - zoom."""
    index = max(0, min(len(SHIP_ICON_HEADER_DIM) - 1, int(index)))
    return SHIP_ICON_HEADER_DIM[index]


def monster_icon_dimension(kind, zoom):
    """(width, height) of a monster icon in native pixels: what the
    original's sprite for this kind and zoom draws (MONSTER_ICON_DIM).
    Unknown types fall back to the player ship so a new monster never
    renders at a nonsense size.
    """
    rows = MONSTER_ICON_DIM.get(kind)
    if rows is None:
        return ship_icon_dimension(zoom)
    zoom = max(0, min(len(rows) - 1, int(zoom)))
    return rows[zoom][2:]


def monster_icon_inset(kind, zoom):
    """(x0, y0) of the drawn pixels inside the sprite's header box, native
    px — where the original's monster shows, from s_ship_icon.x/y. (0, 0)
    for an unknown type, as the player ship's icon sits at its corner."""
    rows = MONSTER_ICON_DIM.get(kind)
    if rows is None:
        return (0, 0)
    zoom = max(0, min(len(rows) - 1, int(zoom)))
    return rows[zoom][:2]


def monster_icon_header_dimension(kind, zoom):
    """(width, height) of the header of the sprite the original picks for
    this kind at `zoom` (MONSTER_ICON_HEADER_DIM), or None if unknown."""
    rows = MONSTER_ICON_HEADER_DIM.get(kind)
    if rows is None:
        return None
    return rows[max(0, min(len(rows) - 1, int(zoom)))]


def nebula_dimension(neb_type, zoom, num_stars=0, map_scale=10):
    """(width, height) of a nebula in native pixels.

    Indexed by type AND zoom level, because the original ships four
    separately drawn variants per type and never scales them
    (MAINSCR::Draw_Nebulae_). Galaxy size enters only through the
    zoom level: a small galaxy is stuck at zoom 0 and therefore
    always shows the large variant, a huge one reaches zoom 3.

    The caller passes the raw s_nebula.type; the modulo mirrors
    _nebula_pict_seg[type % 12].
    """
    row = NEBULA_DIM[int(neb_type) % NEBULA_TYPE_COUNT]
    w, h = row[max(0, min(len(row) - 1, int(zoom)))]
    if NEBULA_EXTENDED_SHRINK:
        percent = star_scale_percent(num_stars, map_scale)
        w = scale_star_dimension(w, percent)
        h = scale_star_dimension(h, percent)
    return (w, h)


def nebula_world_dimension(neb_type):
    """(width, height) of a nebula in GALAXY units.

    The zoom-0 column: at map scale 10 one world unit is one native
    pixel, so that column is the footprint the map coordinates place
    the sprite into. Independent of zoom, unlike nebula_dimension().
    """
    return NEBULA_DIM[int(neb_type) % NEBULA_TYPE_COUNT][0]


def nebula_native_dimension(neb_type, map_scale, num_stars=0,
                            max_map_scale=None, max_zoom=3):
    """(width, height) in native pixels for a CONTINUOUS map scale.

    HD EXTENSION, NOT TRANSCRIBED — same class as hd_zoom_level().

    A nebula is not an icon. A star sprite may be any size at any
    zoom, because nothing on the map is measured against it; a
    nebula is a patch of SKY, and the stars inside it are inside it
    in the world, not on the screen (s_star_data.in_nebula,
    geo.cpp Point_Is_In_Nebula_N_). So its screen size must be its
    world footprint pushed through the current scale, exactly like a
    distance between two stars — nebula_world_dimension x 10 /
    map_scale — and never a per-zoom sprite size.

    What this deviates from, and why:

    The original ships four pre-drawn variants per type and swaps
    them by zoom level (nebula_dimension). Those variants are NOT
    exact reductions of each other — the measured ratios wander
    between 0.62 and 0.75 where 10/map_scale says 0.667 — so even
    in the original a nebula covers 12 % more sky at scale 15 than
    at scale 10, anchored top-left. The original gets away with it
    because it can only stand on four rungs and the mismatch is
    frozen at each one.

    A continuous HD scale cannot get away with it: the sprite size
    would hold still between two rungs while the world shrank under
    it, so the nebula would swell from 50 % to 130 % of its true
    footprint across the zoom range and snap back by up to 36 % at
    every rung change. Stars would cross the gas edge while
    standing still.

    On rung 0 (scale 10, where one world unit is one native pixel)
    this returns the transcribed value exactly. The deviation is
    confined to scales at which the original's own answer is
    self-inconsistent.

    Past the scale of the original's own rung the size HOLDS
    (TRANSCRIPTION `nebula_zoom3_hold`): the original keeps the variant
    of its zoom level there (`zoom_level`, the transcription, with
    `num_stars`, `max_map_scale` and `max_zoom`). What is held is HD's
    own size at that rung's ordinary scale (NEBULA_RUNG_SCALE), the
    footprint x 10 / rung, not the sprite's header. On an ordinary map
    that is a hold past 30 (zoom 3); on an extended one the footprint / 2
    of zoom 2 from max_map_scale / 2 up to max_map_scale - 1 and the
    footprint / 3 only at the maximum, as the original steps there.
    """
    w, h = nebula_world_dimension(neb_type)
    if not map_scale:
        map_scale = 10
    zoom = zoom_level(map_scale, max_zoom, num_stars, max_map_scale)
    rung = NEBULA_RUNG_SCALE[max(0, min(len(NEBULA_RUNG_SCALE) - 1, zoom))]
    factor = 10.0 / min(float(map_scale), float(rung))
    w, h = w * factor, h * factor
    if NEBULA_EXTENDED_SHRINK:
        percent = star_scale_percent(num_stars, map_scale)
        w = scale_star_dimension(w, percent)
        h = scale_star_dimension(h, percent)
    return (w, h)


def icon_step_count():
    """Number of pre-rendered ship sprite steps (one per zoom level)."""
    return len(SHIP_ICON_DIM)


def font_scale(zoom):
    zoom = max(0, min(len(FONT_SCALE_BY_ZOOM) - 1, zoom))
    return FONT_SCALE_BY_ZOOM[zoom]
