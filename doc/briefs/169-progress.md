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

`screens/` holds 13 HD screens (plus `_template`). Commit per screen.

| # | screen | wire id | what it wore before 169 | status |
|---|---|---|---|---|
| 1 | galaxy_map | 0 | `assets/frame.png` (1707x921) | pending |
| 2 | colony_summary | 20 | `assets/frame.png` (1672x941) | pending |
| 3 | planets | 32 | `assets/frame.png` (1920x1080) | pending |
| 4 | fleets | 4 | `assets/frame.png` (3840x2160) | pending |
| 5 | game_menu (overlay) | 8 | `assets/frame.png` (1108x1419) | pending |
| 6 | research_select | 53 | nine-slice cut from the Fleets frame (`core/researchframe`) | pending |
| 7 | research_change | 36 | the same | pending |
| 8 | leaders | 29 | no frame (167) | pending |
| 9 | main_menu | 10 | its own background art | pending |
| 10 | new_game | 13 | the skin 9-slice frame | pending |
| 11 | select_race | 51 | the skin 9-slice frame, `select_race` variant | pending |
| 12 | custom_race | 50 | the skin 9-slice frame | pending |
| 13 | empire_identity | none (sub-screen) | the skin 9-slice frame | pending |
