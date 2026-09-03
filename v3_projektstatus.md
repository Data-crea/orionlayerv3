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
| Python | 21,642 lines across 94 modules (core, screens, tools) |
| Smoke test | `python tools/smoke_test.py` — **55 checks**, headless |
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

**Over 300 lines, knowingly** — recounted 3 September 2026, because
several entries had drifted and a list of counts that is wrong is
worse than no list: `galaxy_map/screen.py` (805),
`tools/struct_probe.py` (758), `galaxy_map/renderer.py` (747),
`custom_race/screen.py` (558), `galaxy_map/ships.py` (529),
`zoomtables.py` (515), `colony_summary/screen.py` (511),
`colony_summary/colonylist.py` (492), `tools/ext_diag.py` (473),
`style.py` (453), `tools/colony_list_preview.py` (443),
`colony_summary/colonyrows.py` (443), `screen_base.py` (390),
`editor/editor.py` (390), `empire_identity/renderer.py` (383),
`new_game/screen.py` (382), `empire_identity/screen.py` (372),
`helppopup.py` (349), `main.py` (328), `select_race/screen.py` (322),
`core/game_client.py` (321), `core/injection.py` (307),
`galaxy_map/sidebar.py` (301). `smoke_test.py` is exempt by nature.

`colony_summary/colonyrows.py` crossed the line this session and is
listed rather than split: it went 234 -> 443 without gaining a
function. The growth is the tie-break block, the NOT DRAWN section
and the two comments around the row filter — all of it the sources
for numbers that are already there. Splitting on that would put a
value in one file and the evidence for it in another, which is the
thing the guideline exists to prevent, not an instance of it. If the
file grows CODE, that is a different conversation.

`screen_base.py` reached 572 lines while the help code sat in it and
was split rather than listed higher: `core/screenhelp.py` is a mixin,
and none of what moved was about being a screen. `helppopup.py`
crossed the line this session (column renderer + backdrop) and is
listed instead of split, because everything in it is one widget.

`struct_probe.py` grew from 243 to 459 with the pop-nibble report and
is listed rather than split: it is one instrument with several views
of the same snapshot — hexdump, int16 columns, spec decode, and now
one named prediction — and a view that lived in its own file would
still need the connection, the spec registry and the array table from
this one.

`colony_list_preview.py` is listed rather than split because a
preview tool IS one thing, and the two halves it appears to have —
four documented scenario rows, and the machinery that renders them —
are useless apart. Most of its length is the rationale for each row:
what that row is meant to settle, and, for the race-group row, what
it cannot.

`colonylist.py` has been on and off this list twice. It crossed at
380 when the track was re-based on the population cap, split into
`colonyrows.py` (the numbers) and `colonylist.py` (the drawing) along
the seam the data flow already had, and is back at 348 now that the
name block is two aligned lines rather than one blit. It is listed
rather than split again: the obvious seam — name block against track
— is one renderer drawing one row, and the earlier split is not the
precedent for it, because that seam already existed in the data flow
and this one would have to be invented. The building column DID go to
its own file (`colonybuild.py`), and the difference is the test: it
carries a transcription with its own source and its own fitting
behaviour, so it is a thing rather than a slice.

It is on the list at 414 with that reasoning stated, which is the
uncomfortable half of the rule working as intended: the next addition
to this file should split it, not extend it.

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
that Aldrich renders them fine, because a mod's font may not. RETURN injects a click at a point inside the original's own button
(`colsum.cpp:265-273`), so no field id is needed. The seven sort
buttons now send the original's own HOTKEY instead and keep that
point as their fallback — decision 39, amended, and see "The sort bar
sends keys" below.

**Everything below was read in orion2re 1.60.0** (`src/version.h`,
`consts.h:43`). Line numbers from a 1.31 archive differ — three were
carried in from one and are corrected here: `Draw_Empire_Info_` is
colsum.cpp:**418** not 408, the justify test is fmtpara.cpp:**1057**
not 1056, and `GAME_VERSION_LABEL` is consts.h:**43** not 47.

**What `s_player`'s `verified=True` actually rests on.** A **static
assert**, not a live probe: `core/structs/player.py`'s own docstring
says the offsets come from compiling orion2re's `orion2.h` with its
`#pragma pack(1)` and reading `offsetof`, with `sizeof` landing on
the `0xf0e` in `sizes.h`. That was reproduced on 2 September 2026 and
every offset is exact — `bc` 50, `surplus_freighters` 56,
`total_pop` 266, `research_produced` 272, `surplus_food` 276,
`surplus_bc` 278, `race` 37, `tech_applications` 379, `traits` 2308.
Git adds nothing: the whole tree arrives in one squashed commit
(`e0ae910`, 31 August), so there is no per-field history to read.

Two fields picked up live corroboration incidentally, both during the
pop-nibble work: `race` @37 (the five players decoding 5, 2, 3, 4, 0)
and `total_pop` @266 (the 39 that agreed with the empire sidebar's
Population). The other four have never been read against the game's
own screen.

**A static assert fixes the layout and cannot tell interchangeable
members apart**, which is the risk that actually bites here:
**`surplus_food` (276) and `surplus_bc` (278) are two bytes apart,
both `int16`, both net flows, both printed with an explicit sign.**
Swapped, every value on screen stays plausible and the struct is
exactly as large either way. So `tools/struct_probe.py players
--sidebar` prints the six beside the labels and signs the original
uses, for a human to hold against the game's own screen, with `race`,
`traits` and `tech_applications` along as controls — right anchors
and wrong scalars means the scalars.

A probe spec briefly duplicated the six in
`core/structs/unverified.py`, on the mistaken premise that they were
unverified. **They never were.** It is deleted, the offsets have one
home again, and a smoke check refuses any `Spec` named `s_player`
outside `player.py`.

`player.py`'s docstring now says **which evidence stands per field**
rather than leaving a spec-wide flag to imply it covers everything:
`race` @37 and `total_pop` @266 have incidental live corroboration
from other work, and `bc`, `surplus_freighters`, `research_produced`,
`surplus_food` and `surplus_bc` have none. The flag stays `True` —
flipping it is a decision to take deliberately, not in passing — but
it should not be read as more than the compile it came from.
`--sidebar` now ends with a printed **expected-vs-actual table**, six
blanks to fill from the original's own screen and a tick box each, so
the run that closes this needs eyes and not interpretation.

They are also **not one kind of number**, which is recorded per
field: `bc` is a stock, `surplus_bc` and `surplus_food` are net
flows, `research_produced` is gross, `total_pop` and
`surplus_freighters` are counts. Adding a gross to a net is the
mistake that table exists to prevent.

**What the six actually are, from source.** `Draw_Empire_Info_` is
colsum.cpp:418. The strings are NOT in the source — `Load_E_Strings_`
(estrings.cpp:11) loads them from the player's own `estrings.lbx` at
runtime — but `orion2_str.h` carries each one as a comment on the
enum, which is where these come from: 118 `%sReserve: %s%d`, 106
`%sIncome: %s%s%+d`, 114 `%sPopulation: %s%d`, 103
`%sFreighters: %s%d`, 102 `%sFood: %s%+d`, 117 `%sResearch: %s%d`.
**Only Income and Food carry `%+d`**, which is why `signed` is per
row.

**The two per-line prefixes are NOT colour attributes** — this was
got wrong first time and is worth the space. `s_0_0055110c` and
`s_1_00551110` (estrings.cpp:8-9) are the literals `"\0320"` and
`"\0321"`, and octal `032` is **0x1A, not ESC**: compiled, they are
the bytes `1A 30` and `1A 31`. FMTPARA sends 0x1A to
`Set_Justification_` and 0x1B to `Set_Current_Colors_`
(fmtpara.cpp:364-368). Only the red one is a colour —
`Red_If_Negative_Fmt_String_` (eric.cpp:176) returns `"\0332"` =
`1B 32`, and `Set_Current_Colors_` (fmtpara.cpp:1154) sets
`color_attr = code << 5`.
Red-if-negative is the original's and applies to Income **alone**;
this screen also colours Food and Freighters, and those two are
marked HD EXTENSION.

**Two findings that would have become inventions.** The six lines are
joined by `String_Builder2_` (eric.cpp:425) through `E_Strings_(71)`
= `%s%c%s` with the character `13` — a **carriage return**, not a
newline, and the whole block reaches `Print_Formatted_Paragraph_` as
one string. And that call passes **justify=3**, which is
`JUSTIFY_FULL` and **inert here**: `Complete_Line_` (fmtpara.cpp:1057)
checks the next character and drops to `Justify_Line_(0)` on CR, LF,
FF or a terminating NUL. Every line is followed by that CR, so
justify=3 never applies.

**The conclusion drawn from that was wrong twice, and is now
settled.** The two prefixes are justification codes, and the 1.60
tree says so three separate ways: `colsum.cpp:36-37` and
`estrings.cpp:8-9` spell them `"\0320"` / `"\0321"`, and
`strings.cpp:22,24` spells the same symbols `"\x1A" "0"` /
`"\x1A" "1"` — unambiguous hex, and commented in the source itself
as *"switches paragraph justification to left alignment"* and
*"to right alignment"*. `Set_Justification_` (fmtpara.cpp:999) takes
`mode = next char - '0'`, flushes the pending segment through
`Complete_Line_` when `char_count > 0`, then assigns `justify_mode`
(:1017); `Justify_Line_` (:1699) implements **mode 1 by adding the
whole remaining width to the first character's advance** — right
alignment — against `para.x2 = x + width - 1` = 623 of 640 (:657).

**One row per entry, not two.** `Set_Justification_` never advances
y; y moves only on CR, LF, VT and FF (fmtpara.cpp:322-341, where CR
falls through to `Vertical_Move_Line_Advance_`). The CR that
`String_Builder2_` joins the six with is what ends each row.

**So the invention was the other way round.** Label-left /
value-right is the transcription, and the stacked centred
label-over-value this screen drew until 2 September 2026 was the
invention. The renderer now does label-left / value-right, with the
column's width taken from the original's own 104 px paragraph rather
than a margin somebody liked.

**The width is itself a DEVIATION, and a live one — decision 44.**
104 native px is 312 reference px; the `sidebar` cutout is 286, and
`min` picks the cutout at every resolution, so the original's
proportion is never the one drawn. That is 8.3 % of the column and
26 reference px per value. The alignment is transcribed, the width is
not, and the two are marked apart. The clamp is written as `min` and
not as a hardcoded 286 so it **expires by itself** if the frame art
ever gives that hole 312 or more; the art is not being widened to
suit it, which would be deriving artwork from a deviation. The smoke
check asserts `native_width` is still read and still *larger* than
what is drawn — deleting it as dead weight fails, and the day it
stops being larger the marking should be retired rather than
restored. A smoke
check measures it in **ink at twelve resolutions**: the label's
leftmost inked column flush with the column's left edge, the
rightmost value ink flush with its right, both after subtracting the
glyph's own side bearing — measured through the same compositing the
renderer does, because an antialiased edge blends differently over
the panel fill and a fixed pixel tolerance passed at 1080p and
failed at 4K by exactly the bearing. Reverting to the centred layout
fails it by 56 px.

**`justify=3` is inert for a different reason than first recorded.**
Not because CR terminates each line — that is true and would also do
it — but because the buffer BEGINS with `s_0`, so
`Set_Justification_` assigns `justify_mode = 0` with `char_count`
still 0, before a single character is drawn. Mode 3 never reaches
`Justify_Line_` at all.

**Why this was wrong twice: an octal `032` read as `033`.** `"\0320"`
looks like ESC + `'0'` and is SUB + `'0'` — a C octal escape is
greedy to three digits, so `\032` is 0x1A, not `\033` = 0x1B. Read
as ESC it is a colour code and the six lines are plain left-aligned
text; read correctly it is a justification code and the original
does label-left / value-right.

**The same trap does NOT catch `Red_If_Negative_Fmt_String_`, which
was queried and stands.** Its literal is `"\0332"`, and there the
greedy escape takes `\033` = **0x1B**, leaving `'2'` — bytes
`1B 32`, which FMTPARA routes to `Set_Current_Colors_`
(:364-368, :1154). Three things agree: the bytes, the function's own
comment, and `colsum.cpp` itself, which spells the same effect
`"\x1B" "2"` at :567, :575 and :1189. Red-if-negative is real, is
the original's, and is kept. Two literals one octal digit apart,
opposite meanings, and the trap is on the other one.

**What IS open about those symbols is a declaration, not a value.**
`s_0_0055110c` and `s_1_00551110` exist three times in three
namespaces at two declared sizes — `const char[3]` in `colsum.h` and
`strings.h`, `const char[4]` in `estrings.h` — in two spellings, all
producing the same bytes. Nothing misbehaves; it is item 6 in
`doc/orion2re_open_fixes.md` as a **question** for Joe (which byte
does the original binary emit at `0x0055110c`?), not a fix request.

`E_Strings_(12)` is **OPEN, single source**: it has no entry in
`orion2_str.h` at all, so only its uses can be read. Every use in the
tree is consistent with the empty string — button labels where the
sprite carries the artwork, "no help", "no prefix", the not-negative
branch of `Red_If_Negative_Fmt_String_` — and consistent is not
confirmed.

**Research is absolute and carries no percent — but not for the
reason it is tempting to cite.** ESTR 117 is `%sResearch: %s%d`;
there is no `%%` in it and none in any research label. The only
entries in the whole table with a literal `%%` are 108 (maintenance
penalty), 112 (morale), 120 and 121 (worker penalty) and HESTR
`0x142`. The conclusion stands; the citation had to be the string
table rather than the field.

**`output_panel` is a TRANSCRIPTION — decision 43 is WITHDRAWN,
3 September 2026.** It was marked an HD EXTENSION on the claim that
`colsum.cpp` never draws per-colony food, industry or research. It
draws all four. `COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155),
reached from `Draw_Scan_Info_` at :485, loops `i < ECON_COUNT`
calling `Draw_Colony_Wee_Prod_(_g_colony_n, i, 106, y_pos, 366, 20)`
with `y_pos` stepping 18, and adds morale at (106, 421); that lands
in `COLDRAW::Draw_Colony_Prod_Both_` (coldraw.cpp:36), which reads
`colony->production[prod_type]` (coldraw.cpp:60) and draws it as
tens-and-units sprites at native x 106, y 349 upward — the
bottom-left, which is exactly where `output_panel` sits.

**Why the grep missed it.** The search was for the words
"food|industry|research" in one file. The call site contains none of
them: the value is chosen by a loop index against `ECON_COUNT`, and
the drawing lives in `coldraw.cpp`. Searching for the DATA
(`production[`) rather than the LABEL would have found it in one
step. That is decision 44's lesson from the other side — there one
definition was mistaken for the definition, here one file was
mistaken for the code path — and the marking was defended by a smoke
assertion for a day and a half, which is how a wrong marking becomes
worse than none.

The rule the entry proposed — *the original computing a value is not
permission to display it* — survives; it simply has no example here.

**Native geometry**, for re-deriving HD boxes: the empire paragraph
is x 520, y 354, w 104. A colony row is `slot * 31 + 38`; the name
column is x 12, w 89 — w 87 when the colony has an event — h 23; the
building column x 512, w 85, h 22.

**The preview draws the whole screen now — 3 September 2026.**
`tools/colony_list_preview.py` drove `colonylist.render` alone, so
the sidebar and the sort bar had no picture at all and both of the
row renderer's deviations were found by reading rather than by
looking. It now drives the real `ColonySummaryScreen.render` off a
synthetic snapshot: real `s_star`, `s_planet_data`, `s_colony` and
`s_player` bytes through the real specs, so `build_rows` and
`_render_sidebar` cannot tell the difference. **Fake the state, never
the drawing** — a preview that draws its own version of a screen is a
picture of the preview. The hand-written row dicts are gone with it,
and so is the check that they matched `build_rows`: that drift is now
structurally impossible, and what is asserted instead is that each
synthetic colony still produces the SHAPE its comment claims.

One thing the rewrite got wrong first and the picture caught at once:
every colony read numeral **I**. `HAROLD::Planet_Number_` counts
OCCUPIED slots before the planet, not the orbit, so a numeral has to
be earned with real planets in front of it — the snapshot now packs
filler planets carrying `colony_index -1`.

**The sidebar's numbers are chosen to be falsifiable, not
plausible.** Plausible numbers are what hide an alignment bug: six
values of similar width sit in a column whether they are right-
aligned or centred. So `bc` is 18432 and `surplus_freighters` is 7 —
five digits against one, which makes right alignment visible AS
alignment — `surplus_bc` is **negative**, so red-if-negative actually
renders for the first time, `surplus_food` is positive so the
explicit plus shows beside it, and `research_produced` is unsigned so
the sign is visibly a per-row property. All four kinds are
distinguishable in one frame: a stock, two signed net flows, an
unsigned gross, two counts.

**`--native` composes the side-by-side.** A 640x480 original beside
the HD render, same height, nearest-neighbour on the original so it
reads as a different picture rather than a worse one. **It has not
been run**: the original half cannot be synthesised and has to come
off a running game, whose framebuffer the Extension API already
carries. Without it the tool writes the HD half and says the
comparison is incomplete.

**Two deviations in the row, both kept, both marked — decision 45.**
The colony NAME is right-aligned and the original left-aligns it:
`Squeeze_Formatted_Paragraph_Centered_` (colsum.cpp:582) is
`center_y` ONLY (bill.cpp:205), and its sixth argument reaches
`Print_Formatted_Paragraph_` as JUSTIFY (bill.cpp:210) with colsum
passing 0 = `JUSTIFY_LEFT`. Kept, because right alignment is what
makes a 236 px column affordable. And the per-row second line has no
per-row counterpart: the original draws it once for the selected
colony. Both marked in `colonylist.py`, in the fundament and in
smoke checks.

**What the second line owes, if it stays.** `E_Strings_(74)` takes
SEVEN values (colsum.cpp:1196-1205): planet size, climate, gravity
class, mineral class, `n_pops`, computed maximum, growth. The row
draws three — climate, `n_pops`, `max_pop` — and omits size, gravity,
mineral class and growth. That omission is **deliberate**: a row is
62 px and the second line is one short string, so seven values there
would be a table rather than a caption, and the row exists to carry
the track. They have a home already and it is the original's own —
`output_panel` is the HD equivalent of that same bottom-left box. If
the hover band from the design lands, the row keeps its three and the
panel answers for the rest, which is what the original does one
colony at a time.

**The sort bar works — 3 September 2026.** Seven keys, and the
DIRECTIONS are transcribed rather than chosen: `Switched_cmp_`
(colsum.cpp:378-401, 1.60) is a switch on `_g_sort_index` with the
sign as a literal in each `case`. Five are descending — population,
food, industry, science, BC — and Name and Producing ascending.

**There is no direction toggle, and its absence is the
transcription.** Clicking the header that is already lit re-sorts
identically; the original has no reversal anywhere. No arrow is drawn
for that reason. Every list control written since 1996 does the
opposite, so this is the kind of fidelity that reads as a missing
feature and needs the note.

Name is CASE-INSENSITIVE, because `cmp_Alpha_` calls `strcasecmp`
(colsum.cpp:1053). Star names generate capitalised, but a player
renames a home star with free text (namestar.cpp:262), and a plain
`str` sort would file that after every capital.

**Six of seven are implemented; `producing` is not, and says so.**
`cmp_Prod_` (colsum.cpp:1091) orders by `Prod_To_Sort_Type_`, which
reads `TECHDATA::_buildings[].cost`, then breaks ties on
`Selection_Name_` — a cost table and a name table both loaded at
runtime from the player's own `techname.lbx` and neither shipped.
That is the same absence that leaves the building column empty. The
button is drawn DIMMED and still injects its click, because the
original's list behind us sorts fine and the injection keeps the two
screens agreeing; what it cannot do is reorder our rows. Falling back
silently to the name would have looked like it worked.

**Ties keep the input order — 3 September 2026, and the tie-break
that used to be here is gone.** Every key fell back to the planet
name on a tie, marked as an addition of ours, on the reasoning that
the original's bubble sort leaves equal elements wherever they were
and that for us this would mean a list reshuffling between redraws.
The first half is right and the second does not follow.

Four files carry the array order end to end, and only one of them is
the sort: `ext_api.cpp:94` writes the colonies in `MOX::_colony[i]`
order, so `colonies_raw` arrives in it; `colxport.cpp:91` filters the
original's own list out of the same array in the same order;
`colsum.cpp:363` swaps only when `Switched_cmp_` is STRICTLY
positive, so equal elements never move; and `colsum.cpp:1056` returns
0 on equality, so the sign that would move them cannot arise.
`build_rows` walks `colonies_raw` in order and `list.sort` is stable,
so the list was already stable across redraws — and the fallback was
ordering ties the original leaves unordered. Two colonies of equal
population sat alphabetically on our screen and in array order on
the original's, with every value on both correct. `_by()` now returns
a single negated number, because a tuple IS a tie-break and the
absence has to be visible in the key rather than asserted beside it.

The smoke check was turned around with it: it no longer demands the
name order for equal rows, it drives `build_rows` over two snapshots
packed in opposite orders and demands the output follow the input —
through the whole path, since "input order" is not a property a sort
key can express on its own.

`s_colony.production[4]` (offset 231, ECON order plus BC —
orion2_consts.h:119-123) now reaches the row dicts for the four keys
that need it. **Nothing in the ROW draws it**, and the original does
not put it in its row either — but it does draw all four per colony,
in the bottom-left box `output_panel` occupies (coldraw.cpp:60).
That is the withdrawal of decision 43, recorded above; the comment in
`colonyrows.py` still carried the old claim and has been corrected.

**The sort bar sends keys — 3 September 2026.** `_inject` has two
paths now. A button with a `hotkey` in `layout.json` sends
`INJECT_KEY` and nothing else; a button without one, or with a
malformed one, falls through to its `native_click`. The seven sort
buttons take the first path, RETURN the second — its field carries a
hotkey byte of 0x25, which is not a letter anybody presses.

**Why the key is preferred.** A click is not inert:
`INJECT_CLICK` arrives as an SDL button event, and platform.cpp:1171
feeds its coordinates to `Set_Present_Mouse_Position_` while :1172
enqueues them as a mouse input event, so every injected click leaves
the game's own pointer parked on the button we pressed. The key path
(platform.cpp:1131) touches neither.

**The click points STAY, and the smoke test refuses a sort button
that loses one.** They are the half that can be checked without a
running game — a grep against the `Add_Multi_Button_Field_` call at
colsum.cpp:265-273 — while a hotkey is a letter in a JSON file that
has to be taken on trust until somebody presses it. The two are an
order, not a replacement.

**It was verified live before it was switched on, because a silent
failure looks exactly like a success here.** The original re-sorts by
a key it already holds without moving a pixel — there is no direction
toggle — so "nothing changed" is both the working and the broken
outcome. Sorting AWAY from the active key is what separates them.
Against orion2re 1.60 on the reference save, Colonies screen up:
`p` from a name-sorted list moved 15071 of the 307200 framebuffer
bytes, `n` moved them back, `B` and `S` moved it again, and an idle
capture moved nothing at all. A frame taken after the key was
byte-identical to one taken after the equivalent `native_click`.

**Second source for the hotkeys, from the same session.** The
FIELD_LIST reports fields 16-22 at y 446-469 carrying N P F I S R B —
the same seven letters `layout.json` holds, UPPERCASE on the wire.
The game folds case: both `n` (110) and `N` (78) arrive. Worth
writing down, because the mismatch between the stored lowercase and
the reported uppercase looks like a bug and fixing it would fix
nothing.

**What was NOT observed: the pointer.** The cursor is composited onto
the ARGB present surface (platform.cpp:794-822) and the Extension API
sends the indexed `g_present_surface` (ext_api.cpp:165), so no cursor
of any kind is on the wire; the game's window is hidden while the API
is on (platform.cpp:1379), so there is nothing to photograph either.
That half of the claim rests on platform.cpp:1171-1172 against
:1131-1134 and on nothing else, and it is written down that way
rather than as "verified".

**The outpost filter is NOT applied, and the gate it is waiting on
was checked and failed — 3 September 2026.** The original's list is
built on two conditions — the colony's `owner` has to be the local
player and its `outpost_flag` has to be zero
(`Build_Global_Colony_List_`, colxport.cpp:91; `N_Colonies_` counts
with the same pair at colxport.cpp:67).
`build_rows` applies only the first, so an outpost of the local
player would appear as a row the original's list does not have.

`outpost_flag` sits at offset 6 of `s_colony` and has ONE source —
the header compiled with its own pragma pack, which fixes the byte
and its width and cannot say the byte MEANS outpost. A filter is a
claim about the meaning, so it needs the second source decision 23
asks for, and the obvious one is a count: colonies of the local
player with the flag clear, against the rows the original's own
screen lists.

**The reference save cannot produce that number.** The check is now a
mode of the probe — `python tools/struct_probe.py colonies
--outposts` — and against the stardate 3508.5 snapshot it reports all
21 colonies carrying 0, across all six owners. The filter removes
nothing, both counts are 7, and 7 is what the screen shows: which is
also exactly what "offset 6 is a byte that is zero everywhere"
predicts. Consistent, and not a second source. The probe says
INCONCLUSIVE rather than passing, and names what would settle it — a
save in which the local player holds at least one outpost. Another
turn of this one will not produce one.

The missing half is written into `build_rows` as a comment with its
source, and into `core/structs/colony.py` as what offset 6 does and
does not rest on. It is not on `doc/orion2re_open_fixes.md`: nothing
is being asked of Joe, the data is already on the wire, and the only
thing missing is a savegame.

**Two states the original's row carries and ours does not.** Found
while reading `Draw_Colony_Summary_For_Colony_` for the sort work,
marked NOT DRAWN in `colonyrows.py`, and deliberately not dressed up
as a task — an omission nobody wrote down cannot be told apart from
one nobody noticed.

- **The star's BLOCKADE** (colsum.cpp:557-569). `star->blockaded` is
  a bitmask over players, shifted by the local player and masked to
  one bit at colsum.cpp:562 — the same shape as `visited`, and read
  the same way by `star.visited_by`. A blockaded system colours the
  row through an inline attribute and appends a marker (ESTR 0x46 and
  0x86); an unblockaded one substitutes the empty string twice, which
  is why the native name column is 89 px wide and not 87.
  **Reachable:** `blockaded` is offset 162 in the verified
  `core/structs/star.py` spec and the stars are in the snapshot. Not
  drawn because nothing has been built for it.
- **A COLONY EVENT** (colsum.cpp:553, `EVENTS::Colony_Has_Event_` at
  events.cpp:635). A colony with an event takes the other branch of
  that function entirely: a different paragraph type, an inline
  colour chosen by `Event_Good_` (colsum.cpp:534), and the event's own
  label appended to the name. **Not reachable:** the function reads
  `EVENTS::_event_data[]`, and the snapshot carries settings,
  players, stars, ships, colonies, planets, nebulas, leaders, antarans
  and ship icons and no events (ext_api.cpp:53-136).

The two are listed apart because they are different kinds of absence,
and collapsing them into one line is how the buildable one would stop
looking buildable. A smoke check holds both markings to their sources
and fails if `GameState` ever grows an events array — at which point
the second entry is wrong and wants revisiting rather than deleting.

**Scrolling is deliberately not built.** The original windows ten
rows over the sorted list — `_list_col[10]`, `Update_Col_List_`
(colsum.cpp:348) filling from `_g_colony_list_ptr[_first + i]` — and
resets `_first = 0` on every sort click (colsum.cpp:828). The HD list
draws every row that fits and has no `_first`, so there is nothing to
reset yet; the place the reset goes is marked in `handle_click`. One
piece verified before the next.

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

**The list renders — first visible step, 31 August.**
`screens/colony_summary/colonyrows.py` (443 lines, the numbers),
`screens/colony_summary/colonylist.py` (492, the drawing) and
`screens/colony_summary/colonybuild.py` (207, the building column) —
their own modules because `screen.py` was at 258 against a ~300
guideline. One
row per colony of the local player, sorted by name: the planet name,
then one allocation bar, one square per colonist, three zones in ECON
order.
Static on purpose — no hover band, no draggable dividers, no click
injection; the screen stays read-only. Those belong on a picture
somebody already believes.

**The bar is an INVENTION** and is marked as one in `colonylist.py`,
in `layout.json` under `list._invention`, here, and in a smoke check
that fails if either marking disappears. The original draws three
columns of pop sprites per row, squished when a colony outgrows its
column (coldraw.cpp:282).

Verified against the original's own screen for the same savegame
(85 turns, stardate 3508.5): seven rows, same names in the same
order, "No Farming" on exactly Kif II, Malus I, Sol III and Sol IV,
per-row populations and job splits identical, total 39. Bar length is
`Planet_Max_Population_For_Player_` reimplemented, not the size table
— with two stated deviations that both make a bar too short rather
than too long: Advanced City Planning is not applied, because
`tech_applications` has no verified offset, and the limit is taken
for the owner's race rather than the best over races present, because
that walk needs the pop word's low nibble.

Race groups as shades and androids/natives as locked are **not
drawn** — but the mask is no longer the reason. The low nibble has a
second source for 0..7, verified live, and that source refutes the
"race" reading rather than merely agreeing with the player one. What
is still open is the meaning of 8 and 9, the android and native
sentinels, which are exactly the two cases the locking was wanted
for. The zone split is a list of runs so they can be added inside a
run later without moving anything.

One thing only the picture caught: "No Farming" was first drawn at
the bar's left edge and the worker squares painted straight over it.
Every number was right and the screen showed nothing. It now sits
after the track, in a `tail_width` column reserved for it — the
collapsed zone has zero width by construction, and the free tail is
one slot wide on Sol IV.

**The track is the engine's cap, not the empire's best colony.** The
square used to be sized from the widest `max_pop` in the list being
drawn, so the ruler moved with the empire: one new Gaia colony, or a
finished Biosphere, lengthened the longest bar and shrank every
square on screen. A square counted last turn was not the square
counted this turn, and nothing in the picture said the scale had
changed — the same class as the drift and double-scale faults, a
number that is wrong only in comparison with itself.

It now comes from `POP_LIMIT_CAP` in `colonyrows.py`, which is 42 in
one place in the tree and carries all three of its sources: `s_colony.pop[42]`
(orion2.h:497), the clamp closing
`COLCALC::Planet_Max_Population_For_Player_` (colcalc.cpp:930), and
the per-job cap in `COLMOVE::Give_Colonist_New_Job_`
(`Sum_Colonists_ >= 42`, colmove.cpp:518) — that last one is why one
zone may legitimately span the whole track, so it cannot be drawn
shorter. `max_population()` clamps with the same constant, so the two
cannot disagree about how long a full bar is.

Three regions per row, each with its own state: **filled**, one
square per assigned pop in its zone's colour; **free**, from `n_pops`
to `max_pop`, a dashed outline and no fill; **unreachable**, from
`max_pop` to the cap, no square at all and only a faint baseline.
The third is not padding — Advanced City Planning (+5), Biospheres
(+2), Subterranean and terraforming all move `max_pop` up during a
game, so it is room the colony does not have yet, and a square there
would claim it was either filled or free. Squares past `max_pop` are
now drawn rather than clipped: they land in the unreachable region,
where nothing else is, so the two stated deviations stay visible
without losing a colonist off the picture.

Two smoke checks hold it, both measured in pixels rather than by
re-deriving the arithmetic, which would only check the formula
against itself: the same row drawn alone and drawn beside a
42-population colony must come out identical pixel for pixel, and the
three regions must appear in order with the unreachable one thin and
at the foot of the track — so a dimmer square there fails instead of
passing a colour test.

### The horizontal budget of list_area — decided 1 September 2026

`list_area` is 1408 reference px and every column spends from the
same pot. Fixed costs are `pad_x` twice (44) and the 41 inter-slot
gaps (82), so

    unit = (1408 - name_width - tail_width - building - 126) // 42

| variant | no building col | +190 building |
|---|---|---|
| today: tail 150, label in tail | 19 | 14 |
| **1. label moved below the bar, tail 0** | **22** | **18** |
| 1 + name_width 230 | 25 | 20 |
| name_width 336 (the true maximum) instead | 18 | 14 |

The table lives in `layout.json` under `list._horizontal_budget`, so
the next session cannot spend the width without reading what it
costs. **Decided: candidate 1 adopted, candidate 2 rejected.**

**Candidate 1 — the label moved, and it was free.** `row_height` 62
against `bar_height` 34 leaves 28 px, split 14 above and 14 below by
centring the bar, and "No Farming" renders 88x14. So the label fits
in height the row already pays for, and `tail_width` went to 0: 150
px back into the track, unit 19 to 22. `no_farming_placement: "tail"`
restores the old position.

#### It is an identity now, and it was 38 px short — 2 September 2026

The budget was stated as a division and checked as a table, which is
not the same as being balanced. It was not:

    name 240 + tail 0 + building 206 + pad 44
         + 42*unit 798 + 41*gap 82  =  1370      against 1408

`unit` is a FLOOR division and 836/42 is 19.905, so 38 px were
dropped on the floor every frame. They were not slack and they were
not padding — nothing claimed them, so they surfaced as dead air
between the right edge of the building column (1446) and the right
edge of `list_area` (1506), a 60 px gap after the Buy buttons that
read as a misaligned panel rather than as a rounding error.

**`name_width` 240 -> 236, and the division comes out exact:**
(1408 - 236 - 0 - 206 - 44 - 82) / 42 = 840/42 = **20**, remainder 0.
The four pixels are not a measurement of anything; they are what
makes the pot divide, and they came off the name column because it
is the only one of the four with slack against its own stated range
— realistic maximum 230, room 244. `building_width` is a hard
transcription, `pad_x` and `square_gap` are the fixed costs, so
neither could give.

The square went 19 -> 20 as a side effect, which is the trade coming
out the right way round: the slack ended up in the thing the screen
exists to make countable. The row now ends flush — slot 42 at 1278,
building column 1294 to 1484, right `pad_x` to 1506.

**The smoke test asserts the relation, not the number.** It reads
`name_width`, `tail_width`, `building_width`, `building_gap`,
`pad_x`, `square_gap` and `POP_LIMIT_CAP` out of `layout.json` and
the width out of the `list_area` box, and requires the sum to equal
it. A budget checked against the constant 1408 stops being a budget
the first time `frame_holes.py` moves a cutout: the constant goes on
agreeing while the panel no longer does, and the check then reports
success about a screen that is wrong. A second assertion says the
same thing the other way — that the remainder is zero — because that
is the half a later edit to any of those keys breaks first.

#### …and it only balanced at scale 1.0 — 2 September 2026

The assertion above had `1920`, `1080` and `1.0` as literals. It was
scale-blind by construction: it covered one of the two keys in
`boxes.json` and none of the sizes reached through the fallback
chain, and the comment beside it called the truncation at other
scales "a bound and not an identity", which excused the gap instead
of measuring it.

Measured, across twelve window sizes:

| | | | |
|---|---|---|---|
| 1280x720 +30 | 1440x900 +22 | 1680x1050 +11 | 1920x1200 **0** |
| 1366x768 +29 | 1600x900 +15 | 1920x1080 **0** | 2048x1152 +21 |
| 2560x1080 **0** | 2560x1440 +15 | 3440x1440 +15 | 3840x2160 **0** |

It closes at four of twelve, and the pattern is exact: **only at
integer scale.** At 1.0 and 2.0 every term truncates cleanly and
42·unit divides; at every fractional scale the six independent
`int()` calls each drop a fraction, and 11 to 30 px land at the right
edge as the same dead air the reference-space fix had just removed.

**The name column absorbs the remainder — as DRAWN WIDTH, not as
text budget.** `track_metrics` computes `slack`, what `list_area` has
left after the building column, both `pad_x` and the whole track, and
`render` adds it to where the bar starts. Nothing is written back to
`layout.json`; it is a per-frame number. The row then ends flush at
all twelve.

The split matters, and it is the whole point of doing this in two
numbers. Adding the remainder to the column outright also closes the
right edge, and silently makes the ellipsis threshold range **244 to
288 reference px** — 288 at 1280x720 against 244 at 1080p, so the
same colony name cuts on one monitor and not on another. The name
still clips and ellipsises against `name_width * scale`, so the
threshold is 244 everywhere (241.9 to 244.0 measured, and that 2.1 px
is three terms being scaled and truncated independently, not slack).
The remainder becomes **gutter** between the name and the first slot,
which is the one thing that column can absorb without saying anything
untrue.

So `name_width` 236 changes meaning rather than value: it is the
**text budget**, and the drawn column is wider by a per-resolution
remainder. Said in `_name_width_note`.

**What is asserted now.** The column sum is gone — after the above it
balances by construction and cannot fail, and a check that cannot
fail asserts nothing. In its place, across the twelve sizes:

    slot42_right + building + pad_x == list_area.right
    the wide name is cut at EVERY size, the narrow one at none

Both are read off the **surface**. An earlier draft derived `bar_x`
and the clip from `layout.json` the same way the renderer does, which
made it agree with the renderer by construction: it passed unchanged
with the gutter moved a pixel and with the clip tied to the drawn
width — the two failures it exists for. Both breaks were then made
deliberately and both now fail, naming the resolution and the cause.

The condition it had to meet was named in advance, because this label
has failed once before — drawn at the bar's left edge, with the
worker squares painted over it, every number right and nothing on
screen. Below the bar is outside the track's band *by construction*
(squares occupy `y+1` to `y+bar_height-1`), so a full 42-slot row
cannot reach it. That is geometry rather than data, and the smoke
test asserts it against a row with all 42 slots filled — not against
a screenshot that happened to have a gap in it.

**Candidate 2 — measured, it goes the wrong way.** A planet name is a
star name plus a numeral. `s_star.name` is `str15` (star.py:35) and
the player can type all fifteen characters when renaming a home star
(`namestar.cpp:262` caps input at 15); the numeral is at most V,
since `star->planet_index` is [5]. Fifteen wide glyphs measure
**336 px through `Style.render_text`** at `name_font` 21 — six px
MORE than the 330 the column reserves. Holding the longest name the
game can produce therefore costs width instead of recovering it: unit
18 against today's 19.

Narrowing to 230 looks safe on any real galaxy — realistic 15-char
names run 190-230 px, and the widest of the 54 stars in the running
reference game is "Draconis IV" at 124 — and overruns on a name a
player can type. That is the trade being refused, and the render is
what refused it: at `name_width` 230 the name visibly prints over its
own track.

**A latent fault the measurement exposed.** `name_width` was a
reservation nothing enforced — `render_text` output was blitted
unclipped — so the 6 px overrun landed on the track's first slots.
The squares draw after the name, so the data won and the name was the
casualty: the same draw-order fault as the No Farming label, one
column to the left. The name is now clipped to its column, asserted
at the structural maximum rather than at whatever a galaxy generated.
Clipping does not make a narrow column correct; it confines the
damage to the name. Going below 336 needs a stated truncation policy,
an ellipsis being the obvious one, and that has not been built.

**The name column, once it had the width.** The render after the
budget decision showed the column three quarters empty, and two
things came out of that.

**Right-aligned to the column's right edge**, which is where the bar
starts. Left-aligned, a name too long for the column grew rightward
onto the track's first slots, and since the squares draw afterwards
the data won and the name was the casualty. Right-aligned, the same
overflow grows LEFT into `pad_x`, where nothing is drawn. The clip
becomes a fallback rather than the mechanism.

Re-run against the structural maximum: 15 W's plus " V" is 336 px.
That measurement is from the `name_width` 330 era, when it spanned
x=3 to x=335 inside `list_area` and never touched the clip. At the
shipped 236 it does not fit and is not meant to: the room before the
clip is 236 - `name_gap` 14 + `pad_x` 22 = 244 px, so this name is
ellipsised, uses the whole of the padding growing left, and still
finishes clear of the track. That is the designed degradation and it
is now a row in `tools/colony_list_preview.py` rather than a
one-off measurement, because the two things no assertion can settle
— whether the cut still reads as a name, and whether the leftward
overflow reads as overflow rather than as a second column — need a
picture. `name_gap` 14 is the gutter between the block and
the first slot, taken out of `name_width` rather than out of the
shared budget; without it the name ended on exactly the pixel the
first square began on and the two read as a collision, which is what
the first render after right-aligning showed.

**A second line under the name**, and it is an **HD EXTENSION**:
`climate` and `pops/max_pop`, e.g. "Terran 22/24", on EVERY row. The
original prints that pair for the SELECTED colony only, into the
bottom-left scan box at native (13, 354, 80, 88) —
`COLSUM::Draw_Colony_Scan_Info_` (colsum.cpp:1155) formats
`ESTRINGS::E_Strings_(74)` and squeezes it into that rect, guarded by
`_g_colony_n != -1`. The rows themselves carry a name and nothing
else. Per row it makes comparable what the original could only show
one at a time, which is the same family as the allocation bar: not
something MOO2 chose against, something its screen had no room for.
Marked in `colonylist.py`, in `layout.json` under
`list._hd_extension`, here, and in a smoke check that also refuses a
marking which does not name what the original does instead.

It is a SUBSET of that box, deliberately: the original's line carries
planet size, gravity, mineral class and growth as well. Those are not
drawn, and `output_panel` — the box they belong in — is still empty.

**`colony->climate` is what the original reads too.** That choice was
made by reasoning (the colony's field is rewritten when a shield
turns a Radiated world Barren, colcalc.cpp:682) and is now
source-backed: `Draw_Colony_Scan_Info_` takes
`climate_idx = colony->climate` at colsum.cpp:1167 and indexes the
same table. Still deliberately NOT `player_climate()`, which is an
Aquatic transform for the pop limit and would print Terran for an
Ocean world.

**The ten ESTR ids were a second copy, and they are gone.** The note
in `layout.json` listed climate → ESTR id for all ten, assembled by
reading `orion2_str.h`. The original maps climate to string in
exactly ONE place — `estrings.cpp:204-213`, which fills
`MOX::_planet_climate_string[]` from the enum — and every screen that
shows a climate indexes that table (colsum.cpp:1199, colland.cpp:40,
colsysdi.cpp:165, plntsum.cpp:151, mainpups.cpp:348). An independent
second derivation of the same table is the screen-ID-map failure in a
new costume. All ten were checked against `estrings.cpp` and agreed;
they were then removed in favour of a pointer, because a copy that
agrees today is the one that drifts later. The names themselves stay
in `layout.json` — they are not in the orion2re source at all, they
are in the player's LBX — in enum order, which is load-bearing and is
neither alphabetical nor a quality ranking.

Substitution is a `replace`, not `str.format` (decision 37), so a
stray brace in a translated string cannot raise inside the render
path — asserted, along with an out-of-range climate byte degrading to
"?" rather than raising.

### The building column — built at 190, and a correction

**The 190 was right and my measurement of it was wrong.** The number
comes from `Squeeze_Print_Formatted_Paragraph_(0x200, y, 0x55, 0x16)`
(colsum.cpp:621): x 512, width 85, max height 22, of a 640 px screen.
85/640 is 13.3 %, which is 190 of 1408.

I had rejected that as a scaled estimate and measured instead the
widest producing string, on ONE line, at FULL font — 311 px at
small_font — and concluded a column that holds its content does not
fit. `BILL::_Squeeze_Print_Paragraph_` (bill.cpp:147) says otherwise
and settles it: `width` is passed straight into
`get_height(width, text)` and the loop compares `max_height >=
height`. **The text is wrapped into the width and the HEIGHT is what
is made to fit. Width never moves, and there is no truncation branch
in the function at all.** So 85 of 640 is a width reservation, and
all three constraints in my measurement — one line, full font, whole
string unwrapped — are ones the original never imposes. A requirement
the original does not have is not a measurement of the original.

Worth keeping as the shape of the error: it was not a wrong number,
it was the right number measured against the wrong question, and it
came out nearly twice as large and looked exactly as authoritative.

**Built at 190, two lines, small font**, in
`screens/colony_summary/colonybuild.py`: the production name on the
first, `- 8t` and the Buy button on the second.

**The original budgets two lines in that same box.** colsum.cpp:621
passes max height `0x16` = 22 into a row whose pitch is 31 —
`buy_btn_y_coords` steps 35, 65, 96, 128, ... — so the box is two
thirds of its row and holds more than one line of its own font. The
two-line column is therefore the same PLACE as the original's, not
just the same technique applied somewhere else. Our vertical reserve
is the one that freed `tail_width`, `row_height` 62 against
`bar_height` 34.

**The behaviour is transcribed, not the mechanism.** The original
squeezes in three steps: narrow the space glyph
(`font_style_widths[32]--`), then the leading, then step down one
font style. The first is a bitmap-font trick with no Aldrich
equivalent and the third steps between discrete bitmap faces. What
carries over is the shape: **wrap into the width, reduce size until
it fits, never truncate.** At the floor it draws the text whole
anyway, which is what the original does once its loop runs out of
things to shrink.

One gap the render found: the fit test was height-only at first, so
a single word wider than the column — an unbreakable 15-glyph ship
design at 225 px in a 190 px column — sat there overflowing, because
it fits the height on one line and never triggered a shrink. Both
dimensions now.

**Whether that width condition is a transcription turned on one
function, and it is.** `_Squeeze_Print_Paragraph_` loops on height
alone, and `fmtpara.cpp` offers
`Get_Formatted_Paragraph_Max_Width_` right beside the height function
without ever calling it — which leaves two possibilities. Either
`_Print_Formatted_Paragraph_` breaks inside an over-wide token, in
which case height alone is sufficient and our width condition keeps
the same guarantee by other means; or it breaks only at spaces, in
which case a 15-glyph ship design overflows 85 px in the original too
and our refusal to overflow is a deviation.

It breaks inside the token. A character is placed when
`char_x_end <= right_limit_x || line_started != 0` (fmtpara.cpp:567);
`line_started` is 1 at the start of a line and 0 after the first
character (:540, :572), so the first character goes down
unconditionally and every later one must fit. When one does not and
it is not a space, `Return_To_Last_Break_()` is tried — and breaks
are recorded only at spaces, tabs and soft hyphens (:723, :731) — but
`_para_p->str--` runs whether that succeeded or not and the line ends
(:583-587). A token with no break inside it is broken mid-token, and
the paragraph never exceeds the width. **Height alone is sufficient
BECAUSE the width can never be exceeded.**

So the guarantee — no ink past the reserved width, nothing truncated
— is a **transcription**, and our width condition delivers it. The
**means is a marked deviation**: the original character-wraps the
token, we reduce the size and keep it whole. The reason is that the
over-wide token here is a ship design name, user-typed data whose
exact form is the point; a hyphen-less mid-word break that reads as
wrapping in a five-pixel face at 640x480 reads as corruption at HD.
Marked in `colonybuild.py`, in `layout.json` under
`list._width_condition_note`, here, and in a smoke check that refuses
a marking which drops either half or the line that settles it.

**The Buy control is transcribed in position and deviates twice in
form.** The original adds one per row at native x=599
(colsum.cpp:302, `_list_buy_fields[10]`, `buy_btn_y_coords`), right
of the producing text, gated on `Colony_Can_Buy_Product_0_`. That
much is transcribed. Two things are not, and naming only the first
would leave the larger one unmarked:

1. **The label.** `E_Strings_(12)` is empty, so "Buy" is a word this
   project chose. It lives in `layout.json`, decision 15.
2. **Drawing text at all.** The original's control is a **sprite** —
   `_anims[i + 11]` supplies the artwork, which is precisely why its
   label string can be empty. A text button is a different object,
   not a translation of that one; it is drawn this way because the
   sprite is in the player's LBX and is not shipped.

Nothing sends a click yet.

**Still missing: the production names.** `build_rows` leaves
`producing` empty. The id at offset 277 indexes
`TECHDATA::_buildings[]`, whose names load from the player's
`techname.lbx` at runtime (techinit.cpp:43-73) and are `kEmptyName`
in the orion2re source. There is no extractor for that table, so the
column renders empty on the real screen rather than inventing a name
— the rule the help texts and the nebulae already follow. The walk is
proven (it was used to measure the 49 names) and the extractor is a
sibling of `help_extract.py` when somebody wants it. Turn counts need
a cost calculation that is not built either.

### `name_width` re-opened, and lowered to 240

It was rejected at 230 because the render showed the name
overprinting the track — **under left alignment**. Right alignment
sends overflow left into `pad_x`, where nothing is drawn, so that
render no longer applies and the trade re-opened.

Reserved for the REALISTIC range now, with the structural maximum as
the **ellipsis case rather than the reservation**. The widest of the
54 stars in the running reference galaxy is "Draconis IV" at 124 px;
a realistic 15-character name is 190 to 230 ("New Constantine V" is
208). 336 px — fifteen wide glyphs, which a player can type
(namestar.cpp:262) — is cut with an ellipsis instead of being
reserved for. That spends nothing in every case it can hold and
degrades visibly in the one it cannot.

| name_width | no building col | + building 190 |
|---|---|---|
| 330 | 22 | 17 |
| 240 | 24 | 19 |
| **236** | 24 | **20** |

Shipped: `name_width` 236 with the 190 column, **unit 20**. 240 was
shipped for a day and left the budget 38 px short of balancing — see
"It is an identity now" above. The table is in `layout.json` under
`list._horizontal_budget`.

**Figure mode: built, compared, deleted.** For one session the
filled region could draw a sprite per colonist instead of a square,
with the zone colour as a 3 px rule beneath the figures instead of a
background fill, selected by a `list.figures.enabled` key and fed
from a `--pop-dir` outside the repository. It was built to be
compared against the squares and it lost.

What decided it was the preview's 50 % copies. Square mode survives
the reduction — the runs stay clean colour blocks and the zone
boundaries stay readable. The figures collapse into an
undifferentiated stipple, and the only thing still carrying the
profession is the 3 px rule, which is itself close to disappearing.
At a 22 px slot the rule was doing the work the silhouette was
supposed to do, which makes the sprites decoration over a bar that
already said the same thing.

Deleted rather than left switched off: **a dead branch is a file
nobody checks.** `colonyfigures.py`, the layout key, the `--pop-dir`
argument, the crop-baseline guard and the smoke check all went with
it. The smoke check was replaced rather than removed, per the rule
that the count must not go down — the replacement covers the name
block, which is what the freed width went into.

Two things are worth keeping from it. The **height-normalisation
rule** — `common_height = min over the set of (max_width * h/w)`, so
the widest sprite sets the height and every other follows from its
own aspect ratio — was correct and measured, and would be the rule
again for any future sprite set; normalising on width inverts it, the
narrowest figure becoming the tallest. And the **crop-baseline
guard**: a set whose source crops differ in height by more than 2 px
is not a set, because the sizing normalises the whole group onto one
height, so one crop taken two pixels low silently rescales every
figure beside it — and the symptom reads as an art problem when the
fault is a measurement. Both are recorded here rather than in code,
because there is no code left to carry them.

### Looking at it — `tools/colony_list_preview.py`

```bash
python tools/colony_list_preview.py
python tools/colony_list_preview.py --size 2560x1440
```

Headless, no game, no savegame: the real `frame.png` over the real
`boxes.json` geometry around fake rows defined in the script. Writes
to `/tmp/colony_list_preview/`, never into the tree, with absolute
paths in every line it prints. Modelled on `starfield_preview.py`,
for the same reason — judging a track has to cost one second, not one
game start plus 85 turns.

This rendered the comparison that deleted figure mode.

**Every image is written twice, and the 50 % copy is the point.** A
track is forty-two repeating slots with a dashed region and a
hairline in it, which is the kind of picture that looks detailed at
1:1 and turns to grain one step away. No pixel check can see that: it
measures whether ink landed, not whether it settles.

Four rows, each there to settle something: 22 pops (where the
original squishes hardest and the fixed-unit track diverges most),
`max_farms == 0`, a `max_pop` 9 colony whose 33 unreachable slots ask
whether the faint baseline reads as *expandable* or as *cut off*, and
a row meant to show three race groups. Plus the invariant pair — the
same row alone and beside a larger colony — which the tool also
*states*, comparing the two first-row bands and printing whether they
agree, because a picture of two tracks is only evidence if somebody
compares them.

**The race-group row cannot be drawn as one, and the tool says so.**
The note used to give the wrong reason and was corrected on
2 September 2026: the nibble's mask IS confirmed live for 0..7, and
what is still open is only the meaning of 8 and 9 — the android and
native sentinels, which are the cases the shading was wanted for.
`colonyrows` reads no nibble, so every row reaching the renderer is
race-blind. That row is identical to any single-race row with the
same job split. It is kept, with a line in the output, because a
preview that quietly substituted professions for races would answer a
question nobody asked — and would be believed, because it looks like
the screen.

Exit codes carry the findings, so do not chain it behind `&&`: 1 if
the shared row was not identical in both renderings.

Two decisions came out of its renders rather than out of argument:
figure mode was deleted, and the name column was right-aligned and
given a second line. Both are above.

The smoke test asserts the fake rows carry exactly the keys
`build_rows` produces. Nothing else would notice a drift: a stale row
dict still renders, so the preview would go on looking right while
showing a row the game cannot produce.

**Rest of the design, agreed 31 August, not built.** Instead of the
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

**Two of these are what still separates the colony list from full
accuracy.** Both are named in `colonyrows.py`, in `max_population()`,
as deviations; they belong here as well, because a limitation that
lives only in the module that works around it is a limitation nobody
finds.

- **The pop nibble is a PLAYER index, not a race — and for 0..7 it
  now has a second source; only the sentinels do not.** Read out of
  the C++ on 1 September 2026:
  `POP::MASK_RACE` (pop.h:8) is consumed by
  `COLONY::Get_Effective_Pop_Player_` (colony.cpp:1257), which
  returns `pop & 0x0F` as a player index and maps only 8 and 9 to the
  colony's owner. The race is a second lookup —
  `MOX::_player[idx].race` in `Colony_Pop_Anim_` (colony.cpp:1275).
  The header names the mask after the thing two steps away from it,
  and that name is no longer in the spec: the field is
  `player_index`, and the smoke test asserts `pop_race` and
  `POP_MASK_RACE` do not come back.

  A third meaning shares the nibble: `Sum_Colonists_`
  (colony.cpp:2129) matches `>= 14` against a race index directly,
  bypassing the player lookup. So the nibble is not bounded by 9, and
  14 or 15 in live data is a fourth state rather than corruption —
  while 10 to 13, which no branch found reads, would be.

  Both steps are on the wire already: this nibble, and
  `s_player.race` at offset 37 in the verified `player.py` spec. So
  race shading is reachable once the nibble is confirmed; it is the
  nibble that is missing, not the second step.

  `tools/struct_probe.py colonies --pop-nibble` runs the prediction
  the reference save CAN answer: across all 21 colonies, including
  the AI's, the nibble should equal each colony's own `owner`. That
  is falsifiable without a single android, because the AI colonies
  carry owners other than 0 — under the "race" reading the nibble
  would not track the owner across them. Half of the prediction is
  already recorded in `doc/s_colony_offsets.md`: 598 colonists across
  two samples, nibble never above 9. The owner match is the
  discriminating half and was never checked.

  It reports counts and a per-owner table, never a verdict alone,
  because **a wrong mask scatters rather than failing cleanly** — a
  spread across many values is a different fault from a few values
  clustered near the owners, and a pass/fail line throws away the one
  signal that separates them.

  **Run on 1 September 2026 against the reference save, and the race
  reading is refuted.** 21 colonies, 131 live colonists, five owners:
  owner 0 -> nibble 0 (x39), 1 -> 1 (x22), 2 -> 2 (x25), 3 -> 3
  (x28), 4 -> 4 (x17). Zero mismatches, nothing outside 0..9, 751
  unused slots all zero. The 39 for owner 0 agrees with the empire
  sidebar Population recorded when `owner` and `n_pops` were verified
  — a different field in a different struct.

  The decisive part is the second query: `s_player.race` for those
  five players is 5, 2, 3, 4, 0 (CyberToller, Darlok, Elerian,
  Gnolam, Alkari), and **not one player's race equals its own
  index**. Player 0 plays race 5, so a race nibble would decode his
  colonists as 5; they decode as 0. Player 4 plays race 0 and decodes
  as 4. The two readings predict a different number for every player
  here, and all 131 colonists follow the owner. Without that second
  query the correlation would have been suggestive and nothing more —
  it is the one check that separates "the nibble is the owner" from
  "the races happen to be numbered like the players".

  So the nibble has two independent sources for 0..7 and is no longer
  a bare transcription. **The sentinels are still not verified**: 8, 9
  and >= 14 do not occur in this save, so `Get_Effective_Pop_Player_`'s
  branch at colony.cpp:1261 stays untested and needs a savegame with
  androids, natives or a conquered population.

  Consequence for the colony list: race shading is now unblocked in
  principle for single-race and multi-player colonies — nibble ->
  player -> `s_player.race` — but NOT for androids and natives, which
  are exactly the cases the shading was wanted for. Not built.

- **The old note, still true of the sentinels.** Every colonist in the one
  savegame checked is race 0, so nothing there could confirm
  `MASK_RACE` or refute it. Until it is settled: the list draws no
  race shading and no locked androids or natives, and the bar takes
  the population limit for the colony owner's race instead of the
  best over the races present — `Planet_Max_Population_For_Player_`
  walks those races through the mask. What settles it is a savegame
  holding androids, natives or a conquered population, not another
  turn, since the race mix does not change across one.
- **`tech_applications` has no verified offset** in
  `core/structs/player.py`, which does not expose the field at all.
  Advanced City Planning therefore does not add its flat +5 to a bar,
  so every bar on a colony of a player who has researched it is five
  squares short. Confirming that offset is the whole fix; inventing
  one to make a bar longer is the trade decision 23 forbids.

  Both deviations shorten a bar rather than lengthen it, which shows
  as a bar that cannot hold its own squares — visible, and asserted
  by a smoke rule — rather than as a quietly wrong length.

- `s_leader_data` for the Officers screen. `tools/struct_probe.py
  --spec` now decodes any record against its spec, so the 64-byte
  ceiling on the int16 column view no longer stands in the way.

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
