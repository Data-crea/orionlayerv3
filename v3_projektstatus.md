# OrionLayer v3 — Project Status

Updated: 31 August 2026 (evening)

**The gap this document warned about is closed.** The previous
version opened with a warning that the context-help work was
described here but missing from the tree — a package lost to the
mis-copy. Both streams have now been merged into one tree and
measured there. The counts live in the Snapshot table below and
nowhere else in this file: they were restated here as well, and the
copy said 48 while the table said 49.

**The project is now a git repository, not a chain of ZIPs.** See
"Repository layout" below for what is committed, what is generated,
and the one asset set that looks generated and is not.

This session (31 August), last of all, in one line each: `s_colony`
is **verified** and promoted to `core/structs/colony.py` — `owner`,
`planet`, `n_pops` and `max_farms` all agree with the original's
colony summary from an 85-turn savegame, `n_pops` twice over
(39 against the empire sidebar, 3 against a planet description); the
`pop[]` masks came along as a separate, partly open claim, with only
`MASK_PROF` confirmed; `Spec` grew an array kind and
`tools/struct_probe.py` a `--spec` decode mode; and the displayed
maximum population turned out to be a computation rather than the
size table, which the colony list's bar design depends on.

This session (31 August), earlier, in one line each: `s_colony` (361 B)
was transcribed from `orion2.h:487-537` and its size confirmed by
compiling orion2re's own headers — 50 members, contiguous, matching
`ORION2RE_STATIC_SIZE_ASSERT(s_colony, 0x169)`, written up in
`doc/s_colony_offsets.md` as **Phase A only**, with `COLONY` in
`unverified.py` still deliberately empty because the second source
(a live probe) does not exist yet; and **decision 23 was made more
precise, not renumbered**: the header route was worded as if it
verified a struct outright, which held for `s_planet_data` because
every field there is a whole member, but `s_colony` packs race,
original owner, profession, assigned and conquered into each `pop[]`
word, and `offsetof` reaches the word without reaching its contents.
Those masks live in `pop.h` and are orion2re's own reading of the
original — a transcription of meaning, which a size assert cannot
check.

This session (31 August), latest, in one line each: the galaxy map's
sidebar help regions were pulled onto the full row band — they had
covered 87 % of the column against the original's 97 %, leaving five
dead strips where a right click opened nothing; and two deviations
from the original are now marked where they are read, one of which
`helppopup.py` and the fundament had both claimed for weeks was
already marked in `screens/*/help.json` when it was marked in none
of the three.

This session (31 August), later, in one line each: the colony summary
package and the context-help work were merged (they were built in
parallel from a common ancestor and neither knew about the other);
the delivery scaffolding was replaced with `.gitignore`,
`tools/setup.py` and `requirements.txt`; and `make_star_icons.py`
turned out not to reproduce the star sprites in the tree, which is
why they stay committed.

Earlier this session (31 August), in one line each: the colony summary screen
got its cockpit frame, its cutout-derived boxes and a live empire
sidebar; a mis-copied package destroyed part of the working tree and
the repair left two permanent tools behind, `make_manifest.py` and
`verify_tree.py`; and the delivery rules in the fundament gained the
four lessons that cost that afternoon.

Previous session, in one line each: MOO2's right-click context help
works on Main Menu, New Game and the Galaxy Map — 31 regions, the
FMTPARA format codes decoded, verified against the real HELP.LBX; the
tree lost 15 MB of files nothing referenced; and the two documents
that had drifted from `doc/orion2re_open_fixes.md` were brought back
in line with it. Earlier the same day: the decoupled HD viewport on
the galaxy map, the Custom Race Accept guard, the two named panel
skins, the on-demand black hole rotation, and the main menu's engine
version line.

This file is the volatile half: what exists today, what is missing,
and how to run things. Decisions and lessons live in
`doc/v3_fundament.md`; long investigation records live in their own
files under `doc/` and are only summarised here.

---

## Snapshot

| | |
|---|---|
| Python | 20,859 lines across 92 modules (core, screens, tools) |
| Smoke test | `python tools/smoke_test.py` — **50 checks**, headless |
| Assets | 170 MB (select_race 68, galaxy_map 51, shared 23, new_game 21, colony_summary 1) |
| Screens in HD | 7 of ~20–22 (colony summary is frame + sidebar only) |
| Setup from clone | `python tools/setup.py` (deps via the system package manager) |
| orion2re | required for live data, not for the smoke test |

Three positioning systems coexist, by design:

- **Reference 1920x1080 with anchors** — main menu, select race,
  custom race, empire identity
- **Background-relative cover-scale** — new game, fully driven by
  `layout.json`
- **Frame-cutout derived** — galaxy map and colony summary, boxes
  generated from the transparent holes in `frame.png`

---

## File tree

Line counts are current. Files over the 300-line guideline are listed
with their count, which is the point of decision 6: the list is meant
to stay uncomfortable to extend.

```
~/orionlayerv3/
├── main.py                       328  Entry point, window, main loop,
│                                      event routing
├── settings.json                      Window, connection, skin,
│                                      active_mods, render_mode,
│                                      language (help texts)
├── LICENSE                            MIT for code and docs; the
│                                      artwork is explicitly out of
│                                      scope, and says why
├── CLAUDE.md                          Working agreement, read by a
│                                      Claude Code session on start
├── .gitignore                         What is generated, and why
├── requirements.txt                   Pinned pygame / numpy / Pillow
├── README.md                          Overview, quickstart, hotkeys
├── MODDING.md                         Complete modding guide
├── v3_projektstatus.md                This file
├── core/
│   ├── resources.py              141  Mod-aware file resolution —
│   │                                  the heart of the mod system
│   ├── palette.py                 64  col(), for_section()
│   ├── wire_protocol.py           81  O2XE frame + FIELD_LIST bytes,
│   │                                  shared with tools/ext_diag*
│   ├── screen_names.py            74  Screen-ID -> name, ONE source
│   ├── gridlayout.py              73  grid_cell_rect, packed_grid
│   ├── screens_loader.py         101  Screen auto-discovery
│   ├── config.py                  53  Constants, paths, defaults
│   ├── mouse.py                   56  Pointer position, ONE source
│   │                                  (fullscreen offset lives here)
│   ├── cursor.py                 122  Sci-fi cursor, sized like the
│   │                                  original's
│   ├── layout.py                  65  1080p reference -> window
│   ├── box.py                    249  UI element (rect, field_id,
│   │                                  anchor, style, panel skins)
│   ├── screen_base.py            390  Base class, frame buttons,
│   │                                  key handling
│   ├── screenhelp.py             265  Right-click help mixin:
│   │                                  regions, region padding,
│   │                                  modal guards, render
│   ├── helppopup.py              346  The help panel (auto-size,
│   │                                  columns, scroll, backdrop)
│   ├── helptext.py               180  Extracted HELP.LBX strings,
│   │                                  format versioning
│   ├── helpformat.py             272  MOO2 FMTPARA control codes
│   ├── style.py                  448  Skins, fonts, buttons, panels,
│   │                                  render_text (glyph fallback),
│   │                                  draw_inner_panel /
│   │                                  draw_thin_border
│   ├── banner.py                 233  Runtime-tinted MOO2 banners
│   ├── injection.py              166  InjectionChain by field shape
│   ├── mapcoords.py              183  Galaxy <-> 640x480 <-> HD,
│   │                                  MapView + SmoothMapView
│   ├── zoomtables.py             460  Zoom levels, sprite sizes,
│   │                                  font scales — ONE sizing source
│   ├── nineslice.py              127  NineSlice + tile loading
│   ├── frame.py                  207  Cockpit frame renderer
│   ├── dispatcher.py             216  Screen switching, overlay
│   │                                  layer, sub-screen lock
│   ├── game_client.py            240  TCP client (auto-reconnect)
│   ├── game_state.py             271  Snapshot parser
│   ├── original_view.py          150  Framebuffer view + input
│   ├── structs/                       Declarative struct specs:
│   │                                  star, ship, ship_icon, player,
│   │                                  planet, nebula, unverified
│   ├── widgets/                       ListView (187), TextInput (118)
│   └── editor/                        editor.py (390), overlay.py
│                                      (229), constants.py (74)
├── screens/
│   ├── main_menu/                219  ID 10 (+ help.json)
│   ├── new_game/                 382  ID 13, data-driven (+ help.json)
│   ├── select_race/                   ID 6
│   │   ├── screen.py             322  Grid, picture mode, info panel
│   │   ├── renderer.py           174  Portrait grid
│   │   └── info_panel.py         278  Name, description, traits
│   ├── custom_race/                   Synthetic ID 50
│   │   ├── screen.py             558  Panels, picks, Accept guard
│   │   ├── renderer.py           288  Race picks + specials panels
│   │   ├── description.py        157  Trait text, markup, wrapping
│   │   ├── popup.py              151  Message box (negative picks)
│   │   └── traits.json                Traits, picks, messages
│   ├── empire_identity/               Sub-screen, two entry paths
│   │   ├── screen.py             342  Ruler, banner, home star
│   │   └── renderer.py           235
│   ├── galaxy_map/                    ID 0 (+ help.json)
│   │   ├── screen.py             805  Star field, sidebar, nav,
│   │   │                              input routing, help regions
│   │   ├── renderer.py           746  Stars, nebulas, black holes,
│   │   │                              wormhole layer, star names
│   │   ├── ships.py              529  Ship/monster icons, tinting,
│   │   │                              owner resolution, re-anchoring
│   │   ├── sidebar.py            301  Stardate + five readouts
│   │   ├── starfield.py          274  Decorative background stars
│   │   ├── ping.py               194  Home-system marker (INVENTION)
│   │   ├── viewctl.py            189  Decoupled HD viewport: zoom at
│   │   │                              the pointer, pan, game parking
│   │   ├── layout.json                Buttons, field IDs, rows,
│   │   │                              ship_icons, starfield, ping
│   │   ├── boxes.json                 map_area, sidebar, nav_* (7),
│   │   │                              sb_<row>_text / _icon (11),
│   │   │                              help_popup
│   │   └── assets/                    frame.png, map_background.png,
│   │                                  stars/, nebula/, icons/,
│   │                                  ships/<kind>/0..3.png
│   ├── colony_summary/                ID 20, frame + sidebar; list
│   │   ├── screen.py             258  list pending; s_colony now
│   │   │                              verified, so the data is there
│   │   ├── layout.json                frame, sort/return native
│   │   │                              click points, empire rows
│   │   ├── boxes.json                 14 cutouts, all derived
│   │   └── assets/                    frame.png (1672x941)
│   └── _template/                 50  Copy to create a screen
├── assets/shared/                     fonts, banner, cursor, skins,
│                                      help/ (labels.json + the
│                                      GENERATED help_<lang>.json)
├── mods/example_mod/                  Working example
├── doc/
│   ├── v3_fundament.md                Decisions, principles, rules
│   ├── v3_orion2re_index.md           Source-code reference
│   ├── ext_api_dokumentation_v3.md    Extension API, for Joe
│   ├── orion2re_open_fixes.md         What is asked of Joe — the
│   │                                  ONLY home of that list
│   ├── empire_identity_slowload.md    The 23-second gap: full
│   │                                  investigation record, dormant
│   ├── UMZUG.md                       Git/GitHub setup and the
│   │                                  day-to-day workflow (German)
│   ├── ext_ship_icon_owner.patch      Optional, not needed
│   ├── ship_icon_measurement.md       Where the icon sizes come from
│   └── starfield_measurement.md       Background star density
└── tools/
    ├── smoke_test.py            2374  Headless verification (47)
    ├── help_extract.py           287  HELP.LBX -> help_<lang>.json
    ├── ext_diag.py               473  Extension API diagnostics
    ├── ext_diag_race.py          228  Race screen field diagnostics
    ├── nebula_extract.py         249  Pull nebula sprites from LBX
    ├── nebula_asset_check.py     238  Nebula asset resolution
    ├── make_nebula_icons.py      228  Render the HD nebula shapes
    ├── make_star_icons.py        224  Generate the 36 star sprites
    ├── make_black_hole_master.py 208  Rotatable black hole master
    ├── make_ship_icons.py        207  Generate ship/monster steps
    ├── zoom_probe.py             205  What a zoom step does to the
    │                                  game's view origin (live)
    ├── starfield_measure.py      179  Background star density
    ├── nebula_check.py           161  Nebula spec check
    ├── ship_icon_check.py        158  Live owner/kind/sprite per icon
    ├── zoom_check.py             153  Zoom ladder against a live map
    ├── struct_probe.py           144  Live offset verification
    ├── make_sidebar_icons.py     129  Cut the five sidebar icons
    ├── frame_holes.py            168  Boxes from frame cutouts,
    │                                  one naming rule per screen
    ├── setup.py                  158  Rebuild generated artwork
    │                                  after a clone, then verify
    ├── star_icon_check.py        109  Which star sprite resolves
    ├── version_check.py               Engine version vs orion2re src
    └── starfield_preview.py       94  Render the field to a PNG
```

## Repository layout

The project is a git repository. `.gitignore` carries the reasoning
per line; this is the summary.

**Committed.** All source, all documentation, `settings.json` (no
secrets, and a clone should start in the last known-good state), and
every piece of authored artwork: the HD masters under `_src/`, the
sidebar `_source_sheet.png`, `_black_hole_src.png`, the nebula
`type_*.png`, the cockpit frames, the portraits and banners.

**Generated, therefore ignored.** Ship and monster steps, the five
cut sidebar icons, the black hole master, contact sheets.
`tools/setup.py` rebuilds all of it after a clone and then runs the
smoke test, so a clone can answer "did this come out complete?"
itself.

The licence to ignore a file is that regenerating it reproduces the
committed one **byte for byte**, which was checked for each of them
rather than assumed. Git stores images as whole blobs rather than
diffs, so every regeneration of a set that stayed in the repository
would leave another full copy in the history permanently — and these
are exactly the sets that get regenerated.

**`stars/` looks generated and is not.** The 36 committed sprites are
trimmed to their content, 44 to 206 px and varying;
`make_star_icons.py` as it stands emits uniform 256x256 canvases.
Some earlier version or invocation produced the tree's set and no
longer exists. The smoke test does not notice — its star checks are
size-agnostic — so ignoring them would have handed every clone
different artwork from the one all the zoom and icon work was
measured against, silently. They stay committed until the tool
reproduces them. See "Loose ends".

**Derived from the user's own MOO2 installation, never committed.**
`assets/shared/help/help_*.json` (from HELP.LBX) and
`nebula_ref/` (from STARBG.LBX). The distinction that decided this:
the HD artwork in `nebula/` is *derived* work — upscaled, redrawn,
hours of somebody's effort — while `nebula_ref/` is the original
sprite, pixel for pixel, with nothing added. That was the one place
in the tree carrying unmodified original artwork, and it left before
the repository went public.

It costs something real. Nothing else in the tree checks a nebula
master's shape or brightness, so a clone that has not run
`nebula_extract.py` cannot make that comparison. The check does not
vanish and does not quietly pass: it asserts that either the
references are present and every master agrees with them, or they are
absent and says which command produces them. The count stays at 48
either way, which is what keeps "the number must not go down" a
usable rule.

**What git replaced.** `make_manifest.py`, `verify_tree.py` and
`tree_manifest.sha256` existed because there was no version control —
a sha256 per file was the only way to find out what a bad `cp -r` had
rolled back. `git status` and `git diff` do that job continuously and
without a manifest to keep fresh. The four delivery lessons in the
fundament stay: they are about verifying a copy, and they are the
reason the repository exists.

---

**Over 300 lines, knowingly:** `galaxy_map/screen.py` (805),
`galaxy_map/renderer.py` (746), `custom_race/screen.py` (558),
`galaxy_map/ships.py` (529), `zoomtables.py` (460), `style.py` (448),
`screen_base.py` (390), `editor/editor.py` (390),
`new_game/screen.py` (382), `helppopup.py` (346),
`empire_identity/screen.py` (342), `main.py` (328),
`select_race/screen.py` (322), `galaxy_map/sidebar.py` (301).
`smoke_test.py` is exempt by nature.

`screen_base.py` reached 572 lines while the help code sat in it and
was split rather than listed higher: `core/screenhelp.py` is a mixin,
and none of what moved was about being a screen. `helppopup.py`
crossed the line this session (column renderer + backdrop) and is
listed instead of split, because everything in it is one widget.

**Deleted this session, verified unreferenced by grep first:**
`galaxy_map/assets/{map_background1,map_background2,3}.png`,
`galaxy_map/assets/stars.zip`, `galaxy_map/assets/_contact_sheet.png`
(regenerable via `--sheet`), `galaxy_map/assets/nebula/Backup{,.zip}`
(the pre-replacement nebula masters, found by the new hygiene check
on its first run), `main_menu/assets/background1.png` — 15 MB. Later
also `assets/shared/skins/default/frame/9-slice.zip`, a copy of the
frame folder it sat in whose `9slice.json` was ten days older than
the one beside it and had no `button_font_scale`. That one survived
two passes because the check only walked `screens/`; it walks the
whole tree now. The smoke test refuses archives and backup folders
anywhere. Kept: `_black_hole_src.png`, which is the INPUT to
`make_black_hole_master.py`, not a leftover.

---

## What works

### Connection
TCP client parses the binary snapshot with auto-reconnect. F12
toggles HD against the scaled 640x480 framebuffer; original-mode
clicks route through `original_view.forward_click`. Screens switch
automatically from each screen's `GAME_SCREEN_ID`.

### Right-click context help — three screens, verified on real data
A transcription: `fields::Check_Help_List_` (fields.cpp:2916) runs
*before* the right button becomes Cancel, and on a hit draws the
entry and swallows the click. HD does the same. 31 regions on Main
Menu (6), New Game (11) and the Galaxy Map (14 of 15), transcribed
from the C++ tables into `screens/<name>/help.json` with the native
640x480 rectangle recorded beside each — never as box properties,
because `Box.to_dict` would drop a foreign key on the next F5 save.
That is decision 38 in the fundament; it was born as a second "36"
because two same-day sessions each took the next free number, and
was renumbered since the version-line decision had been cited first.
The walk stops at the first hit, so screen-wide fallbacks sit last,
and the smoke test enforces that ordering.

**The regions are derived from the boxes, and may be larger than
them.** A region names its boxes and the rect is their union, so it
follows an F5 nudge instead of drifting from it. That left the galaxy
map's sidebar covering 87 % of its column where the original covers
97 %: the `sb_*` boxes are sized to their content, 93 reference
pixels inside a row pitch of 109/110, so 16–17 pixels between every
pair of readouts answered a right click with nothing. A `pad_y` on
the region closes it — 7 reference pixels, the largest value that
keeps the band inside the `sidebar` cutout — without touching what is
drawn. The pad applies to every region kind rather than to the `box`
branch alone, so it cannot become a silent no-op, and it scales with
the window, because an unscaled pad is correct only at the resolution
it was tuned on.

**Two deviations are marked where they are read**, under an
`hd_extension` key in `help.json`: the stardate region fills its HD
row where the original's fills 17 of a 21-pixel one, and the
auto-sizing panel. The second is the one worth remembering —
`helppopup.py` and the fundament both stated it was marked in
`screens/*/help.json`, and it was marked in none of the three for as
long as both said so. A smoke check now walks the tree, not a list of
screens, and refuses a `help.json` that carries no marking or a
marking that does not name the 339 px wrap it deviates from.

The machinery: `core/screenhelp.py` (mixin on ScreenBase — every
screen has the behaviour, a `help.json` opts in),
`core/helppopup.py` (the panel), `core/helptext.py` (the strings),
`core/helpformat.py` (the decoder). The panel is the `help_popup`
box, F5-movable, auto-sized to its text, wheel-scrolled when too
tall — a marked HD EXTENSION against the original's fixed 339 px
box. On the galaxy map the box is centred on `map_area`, not the
window, and the smoke test asserts containment in the cutout rather
than the exact centre, so an F5 nudge is legal and sliding under the
sidebar is not. Font size reads the box's stored `font_scale`
directly, bypassing `box_font_scale`'s resolution auto-factor, which
double-scales anything not hand-tuned per resolution. Right-drag
panning survives untouched: the original's help list pointedly does
not cover the map area.

**The bodies are not plain strings.** They carry MOO2's FMTPARA
control codes; the Command Points table is four absolute column
positions (`\aX3.Frigate\aX97.-1…`), not spaces.
`core/helpformat.py` transcribes `fmtpara.cpp`: X (column) and T
(tab stops) are honoured, columns scale from the original's 339 px
paragraph space to the panel's text width (so the table lines up at
1080p through 4K), everything else is dropped and recorded per entry
as `dropped_functions`. The extractor hands the bytes over untouched
and decoding happens at load time; the file carries `"format": 2`
and a stale one is refused with the command that fixes it, because a
mangled body renders *almost* right.

**Verified against the real HELP.LBX on 30 August**: 707 records,
every id the three screens use is present, and `dropped_functions`
is empty across the entire file — the claim "nothing in the help
text uses more than X, T and the line breaks" is now a measurement,
not an assumption. Text colour is the original's RGB (72, 144, 56),
measured; title and body share it and differ only in font style,
exactly as in `Draw_Help_Entry_`.

The text itself is derived from the player's installation
(`tools/help_extract.py`, language per `settings.json`) and never
ships; until extracted, the popup says so with the command.

**31 August — the file name had three independent spellings.**
`core.helptext` built the path the loader reads, `help_extract.py`
built the one it writes, and `setup.py` checked a hardcoded
`help_en.json`. The two directions of the resulting lie: a German
install that had extracted `help_de.json` correctly was told the
texts were absent, and an English file under `"language": "de"` was
reported ok while every popup showed a placeholder. `help_file()` in
`core/helptext.py` is now the single source, all three go through it,
and the smoke test asserts they agree for `en`, `de` and `fr` — `en`
alone cannot catch it. `setup.py` also names the consequence and
prints the `--lang` the settings actually call for, because the
report was accurate and still read as optional.
OrionLayer's own wording around it lives in
`assets/shared/help/labels.json`. Not drawn, deliberately: the
per-entry animation (`anim_lbx` is preserved in the JSON so the
omission stays a decision).

### Core UI
NineSlice with per-size cache, **Aldrich** (SIL Open Font License)
with a font cache and per-character fallback for substituted
glyphs, corner glows, anchors,
per-resolution box storage, frame title bars and button bars, the mod
system, skin selection.

**F9** cycles 1080p → 1440p → Ultrawide → 4K. **F11** is fullscreen
with pillarboxing and corrected mouse coordinates. Boxes are stored
for 1920x1080 and 2560x1440.

**F5 editor**: select, drag, resize handles, arrow nudge, content
offset, font scale (Ctrl+Wheel), glow position and rotation, field
assignment, portrait zoom/pan, pannable image boxes, per-resolution
save (Ctrl+S), help overlay (H).

### Main Menu — logo, scrolling credits, engine version
The version line sits bottom right, where the original puts it, in
its own `version_text` box: right-anchored, right-aligned, drawn with
the new `text` box skin, F5-draggable like everything else.

**The number is maintained by hand, and that is a decision** (36).
The Extension API does not report it — `HELLO_REPLY` carries
`PROTO_VERSION`, which is the wire protocol's number, and the
snapshot has no version field. Appending it to the reply would have
been four backwards-compatible lines of C++ in Joe's tree for one
line of cosmetic text, so the proposal was written down and withdrawn
(`doc/ext_api_dokumentation_v3.md`, `doc/orion2re_open_fixes.md`).

It lives in `core/config.ORION2RE_VERSION`; the word "Version" is a
template in `boxes.json`, so a translation replaces it without
touching code. `tools/version_check.py` compares the constant against
orion2re's *two* literals — `src/version.h` and `src/game/consts.h`
are separately written and can disagree with each other as well as
with us — and the smoke test asserts the number appears in exactly
one file in this tree.

Position and colour are measured, not styled. The source centres the
string on native x=517 (`Print_Centered_(0x205, …)`,
mainmenu.cpp:295); a native screenshot puts it at 516.4 with a 7 px
ink height, which also pins `font_h` at 10. The same screenshot gives
the glyph colour as RGB (104, 56, 20) against the credits' (164, 100,
40) — **the original draws its version dimmer than its credits**, at
59 % of their luma. The HD default is `credit_role` at that same
ratio rather than the raw colour of a palette OrionLayer does not
use, and lives in `colors.json` as `main_menu.version`.

### Panel skins — two, with a job each
`inner_panel` (the 9-slice art) frames pictures; `thin_border` (a
rounded blue outline) groups things. Both are box skins in
`core/box.py`, selected per box in `boxes.json`, coloured from
`panel.thin_border` in `colors.json`.

New Game pairs them: each setting image keeps its 9-slice frame, the
group box around image, title and label carries the thin border, as
does the toggle group. The smoke test asserts the containment — every
`inner_panel` box must sit inside a `thin_border` box — so the rule
survives a renamed or added panel.

Select Race and Custom Race are border-only, in every mode including
picture-select. `inner_panel` therefore has exactly one job left in
the tree: New Game's five setting pictures.

### New Game — complete, data-driven
All layout, field wiring, value maps and labels in `layout.json`.
Five setting categories via `ACTIVATE_FIELD`, three toggles via
`INJECT_CLICK`, Cancel/Accept through the frame button bars.

### Select Race — complete
5x3 portrait grid (13 stock races plus Custom Race), hover selection,
click sends `INJECT_CLICK` on the race radio. Info panel as three
independently movable boxes. Picture mode for the Custom Race
portrait. A stock portrait click injects the radio and switches to the
HD Empire Identity screen with `lock_ids=(6,)`; click and ENTER share
one code path.

### Custom Race — complete, with a local Accept guard
Three panels (Race Picks, Special Abilities, Description) plus the
combined picks/score bar, all F5-movable with their own font scales.
Exclusive trait groups and the Lithovore/Farming block are honoured
locally and mirrored to the game field by field.

**Message box on an overspent race.** MOO2 refuses a race whose
remaining picks are negative and answers with an error box.
OrionLayer tests the same condition *before* it forwards Accept, so
orion2re never receives the invalid Accept, never draws its own box
into the framebuffer, and the HD screen is never left sitting on
Empire Identity while the game stays on 50.

The box is outlined with `thin_border` and filled with the screen's
own scaled background blitted at the same window coordinates — so it
reads as bare backdrop with the panels lifted off it, and no sampled
RGB constant can go stale when the artwork changes. It is modal:
click, wheel and every key are swallowed, so ESC dismisses the
message instead of cancelling the screen. No dimming layer — MOO2 is
palette-indexed and cannot alpha-blend, so a darkened backdrop would
be an invention.

Two F5 boxes, the same split the picks/score bar uses: `picks_popup`
(panel) and `picks_popup_text` (text area with its own `font_scale`).
The box renders while the editor is open, with the real string,
because an empty panel gives no clue whether a font scale fits. The
wording lives in `traits.json` under `messages`. Word wrap measures
by rendering rather than by `font.size()`, because `render_text`
mixes two fonts wherever the DEMO font substitutes a glyph; rendered
lines are cached per (text, pixel size, width).

### Empire Identity — complete, both paths live-verified
Replaces MOO2's three dialogs (ruler name → banner colour → home star
name) with one HD screen. Custom Race Accept (lock 50+6) and stock
race selection (lock 6) both reach the *same* `Naming_Popup_` and
`Flag_Screen_` in `racesel.cpp`, so one field-shape detector serves
both without a branch.

Accept runs the InjectionChain, event-driven on FIELD_LIST: ruler name
(24 backspaces + name + Enter as one SDL burst) → banner (waits for
eight large hidden fields, then `ACTIVATE_FIELD`) → home star. ESC
returns cleanly to screen 6. The chain is not evenly spaced — the
galaxy is generated between banner and home star, in API silence —
which is why the watchdog is 10 s and holdable, a reconnect drops its
field list, and the home-star step carries its own 90 s timeout. A
failed chain switches to the original view instead of releasing
silently, so the dialog can be finished by hand.

**Progress box while the chain runs** — an INVENTION, marked in
`renderer.py`, `layout.json` and a smoke test that fails if it stops
being drawn. Two F5 boxes (`busy_panel`, `busy_text`), opaque, filled
from the screen's own background, `thin_border` outline; one bar
segment per chain step, the running one sweeping, waits over 3 s
shown in seconds. Wording in `layout.json` under `labels.busy_steps`.

### Colony Summary — frame, sidebar, buttons
The original's "Colonies" list (screen 20, `colsum.cpp`), built the
galaxy-map way: one cockpit frame PNG with 14 transparent cutouts,
generated from a black-and-white mask, boxes derived from the holes
by `frame_holes.py` — which now carries one naming rule per screen,
chosen from the path.

Live: the six empire readouts in the sidebar, transcribed from
`COLSUM::Draw_Empire_Info_` — Reserve, Income, Population, Freighters,
Food, Research, each one verified `s_player` field, with the
original's explicit plus and red-if-negative. They go through
`Style.render_text` — the reason was that `+` and `-` were on the
DEMO Bank Gothic's watermark list, and the habit is worth keeping now
that Aldrich renders them fine, because a mod's font may not. The seven sort buttons and RETURN inject a click at a
point inside the original's own button (`colsum.cpp:265-273`), so no
field id is needed and the hotkeys n p f i s r b keep working
natively — decision 39.

**The list is no longer blocked.** `s_colony` is verified as of
31 August (`core/structs/colony.py`): `owner`, `planet`, `n_pops` and
`max_farms` each agree with the original's own colony summary, and
`MASK_PROF` with its FARMERS column. What is still missing is the
work, not the data. The three panels under the list are filled and
empty.

One number the bar design depends on is **not** a struct field:
maximum population is computed by
`COLCALC::Planet_Max_Population_For_Player_` over climate, racial
immunity and Advanced City Planning, and
`MOX::_planet_max_population[size]` is only its base — 10 where the
game shows 5 on a Small Ocean planet. A bar proportional to the
table alone is twice too long on exactly the planets a player looks
at most. See section 3 of the fundament, and the smoke rule that
refuses the base table anywhere it appears without the climate
factors.

**Design for the list, agreed 31 August, not built.** Instead of the
original's three icon columns per colony, one allocation bar per row:
one small square per population unit, three colour zones (farm,
industry, research), two draggable dividers between them, race groups
as shades, androids and natives outlined as locked, `max_farms` as a
tick, "No Farming" as a collapsed zone. Bar length is proportional to
the colony's maximum population, so the squares are the same size in
every row and counting squares means counting pops. Hovering a row
opens a band directly below it with the original sprites, unsquished,
plus the hovered pop's race/job/state — the band pushes the rows
below it down rather than covering them, because the row underneath
is where the next drag goes.

Why this can drive the original: the pop move is click-click, not
drag (`colsum.cpp:851`), the pickup takes a whole identical group
from the clicked icon onward, and the five drop rules are all
checkable from the snapshot before a click is sent. Icon positions
are deterministic from the colony data, so every HD drag becomes
pairs of injected native clicks — two per race group touched. The
mechanics are recorded in the fundament's orion2re facts. The native
list window (`_first`) and sort order have to be tracked locally,
because the snapshot carries neither.

### Galaxy Map
Arranged like the original: bottom bar COLONIES · PLANETS · FLEETS ·
LEADERS · RACES · INFO, TURN bottom right, stardate as the sidebar's
top row, the frame title cutout clickable as the GAME menu.

**Decoupled HD viewport** (`viewctl.py`) — new this session. The
snapshot carries every star's galaxy coordinate, so the wheel zooms
the HD view **at the pointer** and the right button drags the map,
and the game is never told. The first wheel tick decouples from the
game's slice; `0` hands the view back; `+`/`-` zoom on the map centre.

- The float `SmoothMapView` renders. The transcribed integer
  transform would snap stars to whole native pixels at in-between
  scales and make them wobble against each other while panning; it
  stays in use for everything the game sees.
- Sprite steps come from `zoomtables.hd_zoom_level`, a **marked HD
  extension**: it quantizes the continuous scale to the nearest rung
  of the original ladder, and is identical to the transcription on
  every rung the game itself can report.
- Zoom range: scale 5 (twice the original's closest view) up to the
  fit view, which is `max_map_scale` — the same picture the game
  shows fully zoomed out.
- Panning clamps to the galaxy; an axis that overshoots is centred
  rather than pinned to a corner.

What stays coupled, and how:

- **Clicks** land in the game's 640x480 slice, so while decoupled the
  game is parked at maximum zoom-out — throttled activations of the
  zoom-OUT field only. Field 8 (zoom in) is never used by anything;
  it leaves the game in an inescapable rubber-band state. At
  `max_map_scale` the game's slice covers the galaxy to within 1–3
  units on the far edge, checked for all four sizes. HD pixel →
  galaxy goes through whatever view is on screen; galaxy → native
  **always** through the game's own state.
- **Ship icons** are baked in the game's screen space. They are
  re-anchored, not re-derived: in-transit ships draw at the ship's
  own galaxy x/y (exact), orbiting ships at their star's HD position
  plus the game-computed slot offset, scaled to the star sprite
  actually drawn. Which ship sits in which slot still comes from
  `Build_Ship_Icons_`, so decision 24 keeps standing.

Everything else on the map:

- **Stars** — 36 sprites, six per spectral class, selected with
  `clamp(zoom + star.size, 0, 5)`. Missing steps fall back to the
  legacy large/medium/small artwork.
- **Star names** — colour by owner, and a Galactic Lore name on an
  unvisited foreign system renders as `(Name)`.
- **Wormhole links** — 1 px, antialiased, RGBA `[128, 150, 190, 90]`
  from `colors.json`, drawn through `renderer.WormholeLayer` and
  cached on a key.
- **Ship and monster icons** — four size steps per kind under
  `assets/ships/<kind>/0..3.png`, indexed by zoom level. The player
  sprite is one greyscale drawing tinted to the eight MOO2 colours at
  runtime; monsters carry their own artwork and footprint. Owner is
  resolved without a C++ patch by rebuilding `_ship_node` from
  `_ship[]` and validating it against `star_idx`.
- **Sidebar** — five painted readout icons, every readout owning its
  own `sb_<row>_text` and `sb_<row>_icon` box so both are editable in
  F5. Dividers derive from the row boxes.
- **Black holes** — one drawing, rotated at runtime, **90 s per
  revolution in 720 half-degree steps**, stopping when
  `Advance_Black_Hole_Animation_` says the original stops. Frames are
  rotated **on demand and one at a time**, not pre-rendered: at half a
  degree the outer edge of a 195 px icon moves 0.85 px per step, and
  720 surfaces at that size would be 55 MB per icon size and about a
  second of freeze the first time a black hole appeared. The single
  slot costs 2.3–2.8 ms whenever the clock reaches a new step, 8 times
  a second, shared by every black hole on the map because they all
  turn off one clock; a cache hit is 4.5 µs. Roughly 2 % of one core
  while a black hole is on screen.
  Speed and smoothness are now **separate constants**
  (`BH_ROTATE_PERIOD_S`, `BH_ROTATE_STEPS`). They were one decision
  while the frames were pre-rendered, which is why the old 72-frame
  version could not be slowed down: stretching 40 s to 90 s with the
  same 72 frames spaces the same 5° jumps further apart and reads
  *more* stepped, not less.
  Residual drift of the event horizon across the revolution is
  unchanged at 0.37 px at 117 and 0.70 px at 195, against a
  measurement floor of 0.26 and 0.63 — the smoke test asserts under
  0.5 px at 117. The supersample is load-bearing: rotating at icon
  size instead is 13x cheaper (0.19 ms) and drifts 1.4 px, because
  the half-pixel centring rounding then lands at final scale with
  nothing to divide it. **No brightness pulse**: an
  earlier version faded between alpha 165 and 255 every 4.8 s, which
  read as breathing and buried the rotation. It was invented, not
  transcribed — MOO2 is palette-indexed and cannot alpha-blend a
  sprite at all. The smoke test now asserts that frame brightness
  varies by under 12 %. The master is built by
  `tools/make_black_hole_master.py` from a single still: point stars
  removed, alpha from luma, event horizon forced opaque, cut to a
  circle so rotation cannot clip a corner. The tool refuses to write
  a master whose horizon sits more than 2 px off the rotation axis —
  an off-axis horizon orbits the centre instead of turning, which no
  screenshot reveals and only motion does.
- **Nebulas** — twelve masters under `assets/nebula/type_NN.png`,
  one per `s_nebula.type`, sized from `zoomtables.NEBULA_DIM` and
  never from the artwork. Blitted additively, so a master's mean
  premultiplied luma *is* its weight on screen; the smoke test
  measures shape and weight against `assets/nebula_ref`, the same
  extraction that produced the table.
- Decorative star field, hover ring, hovered system name.
- **Home-system ping (HOME)** — three expanding rings over the local
  player's home star, ~3.7 s, then gone. An **invention**, labelled as
  such in `ping.py`, in `layout.json` and in the smoke test, which
  fails if the marker disappears: MOO2 has no ping and cannot
  alpha-blend at all. Kept cosmetic — the key is consumed by
  OrionLayer and never reaches orion2re, the effect expires on its own
  and hands its ring cache back, and radii are in native pixels times
  `ctx.px` so it scales with the zoom like every transcribed layer.
  The home star comes from `s_player.home_planet_id` →
  `s_planet_data.star_index`, both verified specs, with a fallback to
  the first owned star when the index is out of range. 0.22 ms per
  frame while running.
- A star click sends `INJECT_CLICK` at the star's exact 640x480
  point, computed with the game's view state in both modes.

---

## What is missing

### Galaxy Map
- **Anchored zoom — three things only a running game can answer.**
  (a) Does the game clamp `_cur_map_x/_cur_map_y` to 0 at maximum
  zoom-out? The parking logic assumes the parked slice starts at the
  origin; `tools/zoom_probe.py` measures exactly this. (b) Does
  mapgen ever place a star inside the 1–3 unit strip the parked slice
  misses on the far edge? If so, that star is unclickable while
  decoupled. (c) The orbiting-ship slot offsets stretch with the HD
  zoom by design — judge them against the original before calling the
  feature finished.
- **ZOOM rocker.** Fields 8/9 no longer drive the view; field 9 is
  used only by the parking logic. A visible rocker would need two
  cutouts in `frame.png` between FLEETS and LEADERS, then
  `frame_holes.py` and two names in `layout.json` — but with the HD
  zoom on the wheel and on `+`/`-`, it is now cosmetic rather than
  functional.
- **Ship icon artwork gaps.** No HD master for amoeba (owner 10) or
  antaran (8); both fall back to the player sprite. Only zoom level 0
  has been measured — steps 1..3 are extrapolated, see
  `doc/ship_icon_measurement.md`.
- **Maximum galaxy size (community map) — one bug fixed, one open.**
  Above 72 stars the game leaves the 10/15/20/30 scale ladder and
  builds one by halving `_max_map_scale`, so `zoom_level()` needs that
  value. No caller passed it, and `_extended_zoom_level` then fell back
  to `map_scale`, which satisfies its own top rung at every scale: an
  extended map reported max_zoom however far the player zoomed in, and
  drew its smallest star, ship and font step throughout. Fixed; the
  smoke test pins the ladder at both the table and the `MapContext`
  level. Still open: `max_map_scale` is recovered from `MAP_MAX_X`
  through `MAP_MAX_X_PER_SCALE = 50.6`, measured from the four stock
  sizes only — Maximum was never in that derivation. Run
  `tools/zoom_check.py` on the live map; the widest scale the game
  reaches *is* `_max_map_scale` and must equal the derived value. This
  now also bounds the HD zoom-out, since the fit view is that same
  number.
  Star names vanishing and the black hole freezing at the widest view
  are NOT bugs — `Print_Star_Names_` bails at
  `Is_Extended_Max_Map_View_`, and `Advance_Black_Hole_Animation_`
  stops once `Star_Scale_Percent_` drops below 100 (scale > 30). Both
  return one zoom step in, confirmed live 29 August. But both fire off
  the derived `max_map_scale`, so they are only right at the right
  scale.
- Popup overlays: system popup (25), build queue, colonisation (30).
- Info panels; the influence overlay the original can draw.

### Context help
- **The colony summary has no help.json yet, and the original has a
  list for it** — `ERICHELP::_colony_summary_screen_help_list`, 22
  entries (erichelp.cpp:65), installed by
  `Set_Colony_Summary_Screen_Help_List_` (colsum.cpp:144 and :531).
  That is the natural next step: the machinery is a mixin, so the
  screen opts in by shipping a `help.json` and a `help_popup` box,
  and the sort buttons and the empire sidebar are exactly the kind
  of control the entries explain. Nothing in `screenhelp.py` needs
  to change.
- **The per-entry animation is not drawn.** `s_help_record` carries
  an `anim_lbx` / `anim_info` pair and the original plays it beside
  the text. The extractor preserves the reference in the JSON, but
  nothing renders it.
- **Galaxy Map help 300 (the ZOOM rocker) has no HD element.** Fields
  8/9 no longer drive the view and there is no rocker cutout in
  `frame.png`; recorded in `help.json` under `_omitted` rather than
  left silently absent.
- **The sidebar help regions are padded vertically, not
  horizontally.** The box union spans 1556–1791 inside a `sidebar`
  cutout of 1546–1801, so about 10 reference pixels down each side of
  the column still answer a right click with nothing. The same
  `pad_y` mechanism would take a `pad_x`; the vertical strips were
  the ones worth 12.8 % of the column, these are worth 8 % of its
  width and were left rather than fixed unmeasured.
- **The runtime-appended Galaxy Map regions are not transcribed.**
  `Set_Main_Screen_Help_List_` appends more for the multiplayer bar
  and the fleet popup; neither exists in HD yet.
- Select Race, Custom Race and the naming dialogs have help lists in
  the original and are deliberately not wired: those screens are
  finished and the entries explain what the HD screens already show.

### The font was replaced — Bank Gothic (DEMO) is gone
Aldrich (Matthew Desmond, OFL) ships instead, with `OFL.txt` beside
it. A demo font is not licensed for redistribution, which stopped
being an abstract debt the moment the tree became a repository.
Chosen by measurement across six OFL candidates: closest in height
(38 vs 40 px at nominal 40) and ascent (29 vs 31), advance widths a
consistent 85-93 % of the old font's — narrower, which is the safe
direction, since text shrinks inside boxes tuned for the wider face
instead of overflowing. One visible change, worth naming: Bank
Gothic drew lowercase as small caps, Aldrich draws true lowercase.

The substitution machinery stays and now reports an empty set, so
every string takes the single-font path. The smoke check was
rewritten with it: it asserted that `(` and `4` *are* substituted,
which tested one font's defect rather than the mechanism. It now
asserts that the shipped font substitutes nothing, that a stub font
with a deliberate collision is still detected, and that any shipped
font has a licence file next to it. Decision 41.

The galaxy map's `help_popup` box grew from 745 to 800 reference
pixels: the new metrics pushed the Command Points table 35 px past
the old bound. Still centred on `map_area`, still inside it.

### DEMO font substitution — the machinery, now dormant
`Style.render_text` is wired into star names, frame titles, frame
buttons, the Custom Race popup and the two generic label helpers in
`style.py`. Several sites still call `get_font(...).render`
directly: the **F5 editor overlay**, `select_race`, `custom_race`'s
panels, `new_game`, `empire_identity`, and the ListView header.

**This stopped being visible on 31 August** — Aldrich substitutes
nothing, so a direct render and `render_text` now produce identical
output, and the smoke test asserts that for four sample strings. It
is no longer a bug; it is a latent one. The moment a mod ships a
demo font, every one of those sites shows watermarks again while the
converted ones stay readable. Still worth converting, now at leisure
rather than under pressure, and each site remains a regression risk
without test coverage.


### Empire Identity
- **The 23-second gap** — dormant since the 30 August reboot, not
  closed. The full record (evidence, ruled-out causes, the withdrawn
  conclusion, and the three commands to run when it reappears) moved
  to `doc/empire_identity_slowload.md`. Short version: one run spent
  23.6 s in the mapgen silence, every run since 2.7 s, a reboot ended
  it, and the likeliest — unproven — mechanism is orion2re
  serializing for dead clients left over from the old watchdog's
  reconnect storm.

### Custom Race
- **Cross-check the Accept guard against the game.** Accept is refused
  locally on `picks_remaining < 0`, computed from HD's own
  `_trait_state`. If the two sides ever drift apart the wrong way
  (HD >= 0, game < 0) the Accept still goes out, orion2re answers with
  its own framebuffer box, and the HD screen sits on Empire Identity
  while the game stays on 50. Reading the trait state from the player
  record removes the drift and therefore this case too.
- Read trait state live from the player record instead of the local
  `_trait_state`.
- Verify the government value mapping (still UNVERIFIED in
  `traits.json`).
- Race key for Custom Race from the player record — also unblocks the
  Empire Identity emblem for custom races.

### Struct verification
- `s_leader_data` for the Officers screen. `tools/struct_probe.py
  --spec` now decodes any record against its spec, so the 64-byte
  ceiling on the int16 column view no longer stands in the way.
- The `pop[]` bit masks in `core/structs/colony.py` beyond
  `MASK_PROF`. What settles `MASK_RACE` is a savegame holding
  androids, natives or a conquered population — not another turn,
  since the race mix does not change across one.

### Not built
Colony, Research, Fleet, Ship Design, Officers, Diplomacy, the
summary and list screens. Tactical Combat is recommended to stay in
original mode. Cross-platform builds. Planet images for 12 of the 13
races.

### Loose ends
- **`make_star_icons.py` does not reproduce the star sprites in the
  tree.** The committed 36 are trimmed to content (44 to 206 px); the
  tool emits uniform 256x256 canvases. Both render correctly — the
  renderer scales to the icon size either way — so nothing is broken
  today, and the smoke test's star checks are size-agnostic and do
  not see it. But it means the tool is not a faithful regenerator,
  which is why `stars/` stayed out of `.gitignore`. Either the tool
  gains the trim step that produced the tree's set, or the committed
  set is regenerated at 256 and the artwork re-measured; the first
  is cheaper and the second is more honest. Until then this is the
  only asset set whose generator and output disagree.
- **Nebula masters overhang the original outline** on types 1, 9 and
  11 — 13 to 16 % of the reference area at alpha > 25, and still 7 to
  13 % at alpha > 128, so it is body rather than fringe. The zoom-3
  variant doubles as the gameplay shape
  (`geo.cpp Point_Is_In_Nebula_N_`), so a star just outside the
  boundary can look wrapped in gas while the game counts it as clear.
  Membership is read from `s_star_data.in_nebula`, never from the
  artwork, so nothing computes the wrong answer — it only looks
  wrong, and only at the edge. The originals' own zoom-0 and zoom-3
  outlines already disagree by up to 7 %.
- **`tools/make_nebula_icons.py` writes a layout nothing loads.** It
  produces `type_NN/zoom_N.png`, four pre-rendered variants per type,
  which is what the renderer wanted before the size moved into
  `NEBULA_DIM`; it now loads a single `type_NN.png` per type and
  scales it. The tool is still the only path from STARBG.LBX to
  usable HD artwork, so it wants its output flattened rather than
  deleting it.
- `new_game/boxes.json`: `panel_0`–`10` exist at 2560x1440 but the
  1920x1080 list carries only `help_popup` — so at 1080p New Game
  draws no panel frames at all, in either skin.
- Custom Race homeworld information has no home in the new layout.
- Star size steps 3 and 4 differ by only 2 native pixels, so size is
  indistinguishable when zoomed out. This matches the original
  exactly; spreading `STAR_FIELDS_DIM` would be a design decision, not
  a transcription.

---

## orion2re: open C++ fixes

**The list lives in `doc/orion2re_open_fixes.md` and nowhere else.**
This section and `doc/ext_api_dokumentation_v3.md` have each drifted
from it once; both are pointers now, and the ext API document was
brought back in line this session after describing two applied fixes
as open.

Current state (30 August): **items 3 and 4 are open, both
INJECT_CLICK** — the window-coordinate mapping and the missing
MOUSEMOTION before the button events. Items 1 (SendFrame short
write), 2 (FIELD_LIST after HELLO) and 5 (the `racesel.lbx` crash,
via `_old_race`) are applied in the source tree; the fixes file
carries a grep per item to verify any working copy.

`doc/ext_ship_icon_owner.patch` is **not** requested — see the file
for why it turned out unnecessary. Nothing was added to the list for
the context help: the text lives in HELP.LBX, which a client reads
itself, and the regions live in the C++ only as tables to transcribe.

---

## Scope estimate

~20–22 full screens plus 10–15 dialogs and popups; roughly 30 % done.
Remaining Python is estimated at 20,000–25,000 lines without an HD
tactical combat, 25,000–30,000 with it.

Assets are the real cost driver: 166 MB today after the cleanup,
realistically 500 MB–1 GB at the master resolution.

The C++ side is essentially finished — two ext fixes remain, both
about INJECT_CLICK, both behind `#ifdef`.

Colony is the largest single remaining piece; every screen after it
gets cheaper thanks to the template, auto-discovery, widgets and the
frame system. Leaving Tactical Combat in original mode saves roughly
20 % of the total project.

---

## Commands

**Start the game** (built with `-DORION2RE_EXT=ON`):
```bash
cd "$HOME/Master of Orion 2" && ~/orion2re/out/build/Linux/linux-debug/orion2re
```
Wait for `ext: server started on port 17362`.

**Start the frontend, with a log:**
```bash
cd ~/orionlayerv3 && python main.py 2>&1 | tee ~/orionlayer.log
```

**Verify after any change:**
```bash
python tools/smoke_test.py
```

**Set up a fresh clone** (pygame, numpy and Pillow from your system's
package manager; `pip install` is refused on PEP 668 distributions):
```bash
python tools/setup.py
```
Rebuilds the generated artwork the repository does not carry, then
runs the smoke test. `--check` reports without changing anything.

**See what changed** — the job `verify_tree.py` used to do:
```bash
git status
git diff --stat
```

**Extract MOO2's context-help texts** (once, needs the game folder;
re-run after a game language change):
```bash
python tools/help_extract.py
python tools/help_extract.py --lang de          # GER_HELP.LBX
python tools/help_extract.py --ids 288,547      # print, write nothing
```

**Regenerate artwork** after editing the parameters or a master:
```bash
python tools/make_star_icons.py --sheet
python tools/make_black_hole_master.py
python tools/make_ship_icons.py --sheet
python tools/make_sidebar_icons.py
```

**Measure what a zoom step does to the game's view origin** (game
running, savegame loaded, galaxy map open):
```bash
python tools/zoom_probe.py
```

**Check the zoom ladder** on an extended or Maximum galaxy:
```bash
python tools/zoom_check.py
```

**Diagnose "my new artwork is not showing":**
```bash
python tools/star_icon_check.py
```

**Diagnose a grey fleet or an unidentified monster** (game running):
```bash
python tools/ship_icon_check.py
```

**Regenerate galaxy map boxes** after editing `frame.png`:
```bash
python tools/frame_holes.py screens/galaxy_map/assets/frame.png --write
```

**Probe struct offsets** (game running, savegame loaded):
```bash
python tools/struct_probe.py nebulas
python tools/struct_probe.py colonies --records 2
```

---

## Reference

| Document | Location |
|---|---|
| Decisions, principles, rules | `doc/v3_fundament.md` |
| orion2re source index | `doc/v3_orion2re_index.md` |
| Extension API (for Joe) | `doc/ext_api_dokumentation_v3.md` |
| What is asked of Joe (ONLY home) | `doc/orion2re_open_fixes.md` |
| Empire Identity slow-load record | `doc/empire_identity_slowload.md` |
| Git/GitHub workflow | `doc/UMZUG.md` |
| Working agreement for Claude Code | `CLAUDE.md` |
| Ship icon measurements | `doc/ship_icon_measurement.md` |
| Star field measurements | `doc/starfield_measurement.md` |
| Modding guide | `MODDING.md` |
| Project README | `README.md` |
| Colour palette | `assets/shared/skins/default/colors.json` |
| Sizing tables | `core/zoomtables.py` |
