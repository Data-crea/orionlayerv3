# Work order 169 — progress

Unattended run, 25 September 2026. Decision 71: the cockpit frames give
way to one frameless style drawn in code, on every screen, galaxy map
first.

**Written so a fresh session can resume from this file alone.**

Evidence root: `~/orionlayer-fixtures/evidence/work_order_169/`.

---

## Part 0 — the order filed, the decision recorded — **DONE**

169 was free: `doc/briefs/` had nothing above 168 and the README's last
row was 168. The order is filed byte for byte as it arrived, under
`169-work-order-new-ui-style-on-every-screen-galaxy-screen-first.md`
(its `<n>` placeholders left as they came, as 167 did).

"Clone per CLAUDE.md (full tree)" was read as 167 read it: the full
working tree at `/home/data/orionlayerv3`, a complete clone of
`origin/main` with every generated and extracted file present. CLAUDE.md
names no separate clone step (parked, P0).

Decision 71 is in `doc/fundament/04-decisions-screen-artwork-and-markings.md`,
after 69. 71 was free: the highest heading in `doc/fundament/` was 70 and
no file in the tree cited a 71.

**What hangs on per-screen frame images — checked, not assumed.** Every
decision heading in parts 01-05 was scanned for `frame`, `cutout` and
`hole`, and each hit read:

| decision | verdict |
|---|---|
| 3 cutout boxes from the frame | superseded for the galaxy map (the only screen `frame_holes --write` serves) |
| 12 frame variants only | superseded |
| 13 frame-button clicks in `ScreenBase` | amended: HUD buttons, same home |
| 34 two panel skins | superseded in appearance; names kept |
| 44 a cutout narrower than the original | already RETIRED (12 Sep) — nothing to do |
| 49 derived colony plates | already SUPERSEDED by 55 — nothing to do |
| 53 / 54 | their frame examples were already marked gone; the rules stand |
| 55 colony: one fixed image | superseded in appearance; rectangles kept |
| 69 GAME menu: one fixed frame | superseded in appearance; placement kept |
| 70 3840 canvas for frames | superseded |
| 5, 51, 61 | not about a frame image; stand |

Each superseded entry carries a pointer to 71 in its own text.

## The screens — the list, from the tree

`screens/` holds 13 HD screens (plus `_template`). One commit per screen,
except where two cannot be green apart (the GAME menu is seated by the
galaxy map's boxes).

| # | screen | wire id | what it wore before 169 | now | commit |
|---|---|---|---|---|---|
| 1 | galaxy_map | 0 | `assets/frame.png` (1707x921) | HUD: title plate, info panel with the HUD's five icons, six slanted nav buttons with icons, TURN action button; boxes from the HUD's measured layout | `c251ab6` |
| 2 | colony_summary | 20 | `assets/frame.png` (1672x941) | windows as panels, table header, HUD table rows, sort keys + RETURN as slanted buttons | `42872f4` |
| 3 | planets | 32 | `assets/frame.png` (1920x1080) | windows as panels, small buttons, HUD scrollbar, HUD table | `24e67fc` |
| 4 | fleets | 4 | `assets/frame.png` (3840x2160) | windows as panels, small buttons in four states, slot outlines | `ea41cd9` |
| 5 | game_menu (overlay) | 8 | `assets/frame.png` (1108x1419) | popup block, small buttons, dialogs as popups, seated below the title plate | `c251ab6` |
| 6 | research_select | 53 | nine-slice cut from the Fleets frame | lit popup edge, eight boxes as panels, EXIT small button, list popup a popup | `2a09509`, `ab04137` |
| 7 | research_change | 36 | the same | the same, as an overlay over the HUD galaxy map | `2a09509`, `ab04137` |
| 8 | leaders | 29 | no frame (167), black | background slot, panels, small buttons with words, popups | `33c7615`, `ab04137` |
| 9 | main_menu | 10 | its own background art | background art kept (it is the slot's picture); slanted buttons through the `button` skin | `c251ab6` (shared skin) |
| 10 | new_game | 13 | the skin 9-slice frame + a cutout background | title plate, CANCEL/ACCEPT, pictures on panels, toggles as small buttons | `c251ab6`, `0c7b832` |
| 11 | select_race | 51 | the skin 9-slice frame, `select_race` variant | title plate; grid and info panel through the skins | `c251ab6` (shared) |
| 12 | custom_race | 50 | the skin 9-slice frame | title plate, CLEAR/ACCEPT, three columns as panel edges, picks/score bar as two panels, message box a popup | `c251ab6`, `4a75bf0`, `b2f0cf8` |
| 13 | empire_identity | none (sub-screen) | the skin 9-slice frame | title plate, CANCEL/ACCEPT, its own box and message box as HUD blocks | `c251ab6`, `baa5d0f` |

Every popup: the help popup (all screens), the GAME menu and its two
dialogs, the galaxy map's system window and fleet box, the research list
popup, the Leaders hire popup and skill help, the Custom Race and Empire
Identity message boxes — the popup block.

## What was built

- **Material:** `assets/shared/hud/galaxy_hud.png` (Data's HUD, authored,
  committed) and `doc/briefs/169-mockup-galaxy.png`. LICENSE: both
  AI-generated, no copyright claimed; the galaxy map's and the Fleets
  frames are now listed as AI-generated too (168's finding), "cockpit
  frames" left the MOO2-derived list.
- **Measured style:** `assets/shared/hud/style.json`, held to
  `tools/hud_measure.py` (+ `hud_layout.py`, `hud_colony.py`) by the
  suite. Every region the tool reads is named in it.
- **Blocks:** `core/hud/` — `style`, `raster`, `blocks`, `art`, `text`,
  `screenframe`. Panel, popup, separator, outline, slanted button (four
  states), action button, small button, title plate, table header / row /
  selected row / scrollbar. Drawn at the device size, cached per size and
  state. Decision 34's skins, decision 51's plate, the help popup and the
  9-slice frame path go through them.
- **Cut pieces:** `tools/hud_cut.py` (a `tools/setup.py` step, ignored by
  git, rebuilt byte for byte by the suite): 12 icons, the title plate.
- **Galaxy boxes:** `tools/hud_boxes.py` writes them from the HUD layout;
  the suite holds `boxes.json` to it.
- **Evidence tool:** `tools/hud_evidence.py`.
- **Decision 71**, with pointers at 3, 12, 13, 34, 55, 69, 70.

## Checks

294 -> **300**, none deleted. New: five in `006a_core_hud_style_blocks_and_cut_pieces.py`
(style file == tool; cut pieces byte for byte; blocks at three sizes with
the measured edge width; slanted button drawn == hit on every pixel; no
screen loads a frame image and every screen without a picture draws the
placeholder), one in `081a_fleets_...` (Fleets in the HUD style, the
marking's own check).

REWRITTEN because their subject is gone (each comment names its
replacement): galaxy frame cutouts -> the HUD's measured layout; the
GAME menu's three frame checks -> popup versions; RETURN "eighth cutout"
-> "eighth slanted button"; class A no longer lists the galaxy map.
Premises made explicit where the plate colour or shape changed (figures
on the plate floor, plate rect == drop rect, one home for the plate
arithmetic, the Planets hover band, the research popup drawn last and
kept to its box, panel fills read back, the planet surface's fades).

## Evidence — for Data to look at

`~/orionlayer-fixtures/evidence/work_order_169/`, 41 files, all OFFLINE
(in the file names): every screen at 1920x1080, 2560x1440 and 3840x2160
(`<screen>_<size>_offline.png`), and `galaxy_map_beside_mockup_offline.png`,
`colony_summary_beside_mockup_offline.png` (HD at 2160p left, the mockup
right). Screens that need a live game for content (fleets, leaders,
research) show their empty state. Rebuild: `python tools/hud_evidence.py
--mockups`.

## Live part — PARKED (P1)

The engine did not come up from this session (stopped after `mox2: data
space allocated`, waiting in `drm_syncobj_array_wait_timeout`). No save
loaded, nothing sent, SAVE1-11 identical before and after.

## What was parked

`169-parked-for-data.md`: P0 the clone reading, P1 the live part, P2 the
font (Aldrich), P3 the colony mockup kept out of the tree, P4 the chosen
states, P5 the title plate as a cut piece, P6 the background slot and New
Game's cutout picture, P7 the galaxy map's floor to the corner, P8 the
deviations this order added (and the Leaders art question), P9 star names
at 2160p (older than this order), P10 the frame images and code left in
the tree, P11 the missing-icon list, P12 skin keys now unread.

## What Data should look at first

1. `galaxy_map_beside_mockup_offline.png` and
   `colony_summary_beside_mockup_offline.png` — is this the look?
2. `game_menu_1920x1080_offline.png` — the popup block over the HUD map.
3. The 2160p renders of any screen at 100 % — sharpness is the reason
   for decision 71.
4. Parked P8's Leaders question and P11's icon list — both need Data's
   hand before the next order.
