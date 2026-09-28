# Work order 188 — progress

Unattended run, 28-29 September 2026. Evidence root:
`~/orionlayer-fixtures/evidence/work_order_188/`. The order:
`doc/briefs/188-work-order-original-never-shown-turn-messages-travel-line-multiplayer-hall-of-fame.md`.

## Before part 1

- **Number 188**: the last brief in `doc/briefs/` is 187.
- **Baseline as Data expects**: main = origin/main = `b576bc7` (187, "Work
  order 187 Part 7: gates green and the end of the order"), 409 green by
  187's push gate; orion2re `orionlayer-local` = `230a0638` (fixes 34-41,
  43-47; fix 42 open), its three untracked files (`mox.set`,
  `racesel_custom_screen_id.patch`, `src.zip`) left alone.
- **Briefs live in the repo**, `doc/briefs/` (where 187's are).
- **The reference save is SAVE8** — `v3_projektstatus.md` ("the reference
  save (Slot 8)") and `load_slot`, which refuses SAVE8 in its first
  statement — the same slot the order names. SAVE8 is never written.
- Read: `doc/v3_fundament.md`, the three `principles-` parts (06, 07, 08),
  CLAUDE.md, 187's progress, parked file and `187-original-visibility.md`.
- Four source readings ran in the background while Part 1 was built (turn
  messages, Hall of Fame, Multiplayer, the travel line); their reports feed
  Parts 3, 4, 6, 7 and are kept in the evidence folder.

## Part 1 — Stage 1: the original is never shown — **DONE**

**The change, one place** (`core/handover.py`): `decide_for` ends in
`Gate.never_without_f12` — wherever the gate would have released the game's
picture without F12, the frame stays HELD; when the game waits for an answer
(a live list) the App draws the **F12 notice** over the dimmed last HD frame
(`core/f12notice.py`, **HD EXTENSION `f12_notice`**): "The game is waiting for
an answer" / what for (the screen's own reason, else the engine's screen name
and id, e.g. "NEXT_TURN (12)") / "F12 to answer". The words are in the HD
string file `assets/shared/fallback/labels.json` (mod-replaceable). An empty
list keeps the plain hold (path 2). Nothing is answered while it stands; F12
shows the picture and forwards input as before; F12 again returns to HD. The
withheld picture is logged once per change with the screen's reason
(`fallbacknote.Reporter.withheld`).

**All 6 paths of `187-original-visibility.md`** ("Work order 187, Part 6 —
where the original can still show without F12") go through that one place:
1 no HD screen with a list, 2 the empty list, 3 a screen declining its id
(the dispatcher's fallback), 4 a box over an HD page, 5 a net's box / unknown
list, 6 a screen that cannot vouch.

**A seventh way found (path 4b)**: the game's pixels CROPPED into an HD panel
— `screens/fleets/fltbox.py` (Fleets, Races, Leaders), the map's confirmation
(`mapmodal.py`), the Leaders hire popup before its leader is identified. 187's
inventory did not list it (it counted only `_showing_original`). Now
`fltbox.SHOW_CROP = False`: the notice in the box's place, and no button, click
or Y/N hotkey answers blind — the question is not on the wire until open fix
29 (a YES with no question is work order 122's scrapped colony base).

**The flash rule everywhere**: `frametrace.summarise`'s `flash_total` counts
EVERY native frame without F12 (180 A2's allowance for an answerable
no-screen id is gone); `main.App.native_frames` counts every presented native
frame, always on, by whether F12 asked for it; `tools/livedrive.close` prints
it for every live run and `flash_walk`, `design_walk`, `audience_walk` exit 1
on any — not only on their recorded transitions.

**Checks**: 090za (new, 2): every path through the gate — held, the notice
where there is something to answer, F12 still shows it, a hand-over still
counts as a failure; the counter-test with Stage 1 off brings the picture
back on every path; 4b — a box's framebuffer in a colour HD never draws, 0 of
its pixels in the render, no button rect, no screen crops outside `fltbox`
ungated; the flash rule in `summarise`, the App's count, `close` and the
walks; the notice's words from the string file, drawn without accumulating,
the held frame restored undimmed. 090t measures the notice's text at 1920 and
3840 (scaled once). Changed to Data's rule, not deleted: 090o (the replay: no
exception left; the counter-test with Stage 1 off), 048 (the withheld line),
061 (decision 22's fallback: in HD the notice and no forwarded click; the
picture and its click mapping on F12), 091 (the picture's reading under F12),
090e and 090h (the Races and map boxes answer nothing blind; the field mapping
asserted with the crop switch on). Count 409 → **411**, full suite green.

**Not live-tested in this part**: the live walks (flash walk, turns) run in
Parts 4, 5 and 8 on the same code.

## Part 2 — small items from 187 — **DONE**

**The audience menu's header** (187's parked 2a, "The audience menu's title
colour"): drawn in the items' own colour now (`audraw.TITLE_ROLE` =
`ITEM_ROLE` = `value`), as the original prints "How may I serve you:" in the
items' green. Check 090z #4 renders the recorded menu and asserts the colour
the title and every enabled item were drawn in is one and the same.

**The designer's name entry**: as many Backspaces as the engine's current
name has (DSGN, open fix 44), not a fixed 15 (`sdname.clear_count`). Read
first: the click that OPENS the field copies the name into it
(fields.cpp:1436-1444), but an already-active field keeps the text last
typed (`_continuous_string`, :1100-1109), which the engine only then trims
into the name (design_main.cpp:481) — so HD strips what it sends and bounds
the count by the text it sent last on the visit; too many Backspaces meet an
empty field and do nothing (:1193), too few was 187's "RafalHawke". 15 only
when DSGN is absent. Check 090x #7: the Backspaces are the fixture's name's
length, and the rule's cases.

**Live on Xvfb** (engine `230a0638`, SAVE4, guard `P2/guard` verified
identical, nothing saved; `evidence/work_order_188/P2_name_1920x1080`,
`P2/name.txt`):

| before | typed | Backspaces sent | engine's name after | clean |
|---|---|---:|---|---|
| Rafale | Ox | 6 | Ox | yes |
| Ox | Abcdefghijklmn (14, the field's maximum) | 2 | Abcdefghijklmn | yes |
| Abcdefghijklmn | Ox | 14 | Ox | yes |

0 native frames in the name entry and in the whole run (`native frames
without F12: 0`); SAVE1-11 identical. Count stays 411.

## Part 3 — Galaxy map: travel line on hover — **DONE**

**What the original does (read first, `evidence/.../readings/travel_line_reading.md`)**:
it already draws this preview ON HOVER — `Scan_Stars_XY_` calls
`SHIPMOVE::Ships_Try_To_Move_To_` for the fleet box's selection on every
hovered frame (mainscr.cpp:2987-2993), and `Draw_ETA_Destination_Line_`
(mainscr.cpp:535-568) draws the colour wave (not a true dash: an 8-pixel
crawling palette wave) green when `moving && turns_left`, red on a black hole
in the way, flux, or out of range (:558-567), nothing otherwise. HD had left
it out ("its colour is the move result, which is not on the wire").

**Engine fix 48, "FMOV"** (new, approved in advance): the engine's own verdict
for the box's selected ships at EVERY star, written only on screen 0 with
the box open and a ship selected (`doc/ext_fleet_move_verdict.patch`,
entry 48). Proof on `230a0638`: no offset, compiles, control
`Ships_Try_To_Mov_To_` refused. Applied: orion2re **`010870bc`**, rebuilt,
commit diff = patch (cmp); bundle `~/orion2re_bundle_28sep_010870bc_fixes34-48.bundle`
verified; `version_check` (LOCAL_PATCHES, FIX_NUMBERS), `patch_stack`,
README row 16, part 09 updated (`setup.py` reads version_check at run time:
its report lists 48 unchanged code).

**HD** (`core/moveblocks.py`, `maplines.render_hover_preview`): the wave from
the fleet box's head icon to the hovered star, under the stars, coloured by
FMOV's verdict — never recomputed. **HD EXTENSION `hover_line`** ("Data's
decision, 28 Sep"): the line leaves with the pointer (the original keeps it
on the last star hovered); red also for an immobile fleet and a black-hole
target (the original draws none). Clicking unchanged.

**Found live**: the first run drew nothing — `_hover_star` was matched by
identity, and every snapshot builds the star list anew. Now by position;
check 090zb walks the app's sequence (hover, then a snapshot that rebuilds
the stars, then the frame) and asserts the rebuild happened.

**Live on Xvfb** (engine `010870bc`, SAVE4, own fleet at peren, guards
`P3/guard_2576`, `P3/guard_1920` verified identical; `P3_hover_2576x1432`,
`P3_hover_1920x1080`): FMOV arrived with the box open (29 reachable, 24 out
of range on the map); hover Orion (moving, 6 turns) → **green**; out → no
line; hover star 53 (out of range, 12 parsecs) → **red**; out → no line;
click on Orion → the order as today (its destination line drawn). 0 native
frames. Screenshots `004_B1_hover_reachable_hd.png`, `006_B3_hover_unreachable_hd.png`,
`005/007_*_hover_out_hd.png`, `008_C1_after_click_hd.png`.

**Frame time** (`App._render`, 120 frames each, median / p95):

| size | line on | line off |
|---|---|---|
| 2576x1432 | 5.87 / 5.99 ms | 5.73 / 5.85 ms |
| 1920x1080 | 5.85 / 5.92 ms | 5.72 / 5.81 ms |

+0.14 ms with the line — smooth at 2576.

**Not built**: the fleet box's ETA / refusal text while hovering
(fleetpop.cpp:1063-1091) — FMOV carries its numbers; parked 1b.
Checks 090zb (2). Count 411 → **413**.

## Part 4 — Turn-change messages in HD — **DONE** (with Part 5's HD message box, which it uses)

**Inventory first**: `doc/brief_turn_messages.md` — 33 items read from the
source (a sub-agent's reading, `evidence/.../readings/turn_messages_reading.md`,
checked against the code where it was built on), each with its id, what it
shows, its buttons and where they lead, and the HD coverage. Before this
order every report-phase popup reported 0 (the galaxy map) and the Turn
Summary 40 for one tick; the texts were pixels only.

**Two engine fixes, both applied under the advance approval** (entries,
patches, proofs, bundles):

| fix | first line | commit | what |
|---|---|---|---|
| 29 | "A native message box's text is not in the snapshot" | `76f8c438` | "MSGB": every generic box's kind, title, text, answer fields (TEXTBOX / message / warning / confirmation) |
| 49 | "The turn-time popups have no id of their own, and what they show is not on the wire" (new) | `6859e163` | "TPOP": ids 59-64 (40 kept for the Turn Summary; 52, 33 keep theirs) and each popup's content |

Fix 49 was drafted by a sub-agent in its own scratch clone and reviewed,
proved (six files, six controls) and applied by the session. **A slip,
recorded**: when fix 49 was built, an engine of this session's (PID 260952,
the BUY test) was still running from the binary — the link replaced the
file, nothing broke, the engine was stopped and its guard verified.

**HD**: `core/msgbox.py` (the one HD message box, DEVIATION
`hud_message_box`), `core/turnpopup.py` + `turnpopupwire.py` +
`turnpopupcontent.py` (one panel, per-kind content, DEVIATION
`hud_turn_popup`), `core/overlays.py` (the App's one home for both:
drawn over the held frame, clicks and keys routed, the once-only answer),
the rule in `core/handover.overlay_for` (a box wins over a popup; F12 shows
the picture; the Leaders screen's own hire popup is left to it). Every
answer is the popup's own field — clicked at its centre where the original
reads the pointer (the Turn Summary's rows: fix 49's finding 1), activated
elsewhere. **Found on the way**: FMTPARA's justification codes (`\x1A` +
digit) printed their digits in HD — "0Food per farmer 10" for the original's
"Food per farmer … 0" — fixed in `core/helpformat` (shared with the help
popup), table rows drawn left / right; the leader offer's ESTRINGS words
were the buttons' hotkey letters ("H", "R") — now the Leaders screen's own
card (title, portrait, skills, HESTRNGS 0x124/0x125 with the engine's cost
and upkeep) and typed REJECT / HIRE (artwork words, decision 15); a popup
that ignores a click (a refused planet) locked the once-only guard — it now
re-arms after 20 unchanged snapshots.

**Jumps to a colony (known issue 33)**: the turn-time Turn Summary's jump
WORKS — seen live, a colony row opened that colony's screen (1) and its
RETURN came back to the Turn Summary (40). Open fix 33 is the Info screen's
own overwrite (info.cpp:641); no turn message runs into it, so no engine fix.

**Live** (engine `6859e163`, Xvfb, scratch saves in memory, nothing saved;
SAVE10 and MOX.SET restored from the guard taken before each engine; default
decisions listed in `turns.json`; `evidence/work_order_188/P4_turns_*`):
SAVE4 20 turns (until an AI's audience, 58), SAVE5 20 turns (until 58), and a
6-turn re-run on SAVE5 after the code moved into `core/overlays.py` —
**0 native frames, 0 F12-notice frames** in all three.

| type | HD | seen live | checked offline |
|---|---|---|---|
| planet choice (60) — the colony base, colony ship | popup | yes, SAVE4/5, every planet walked, CLOSE | 090zd |
| colony confirmation / "cannot build there" / "place your orders" / spy reports | box | yes | 090zc |
| colony landing (33) | popup | yes | 090zd |
| Turn Summary (40): rows, a colony jump and back, CLOSE | popup | yes (one page; PREV/NEXT not reached live) | 090zd (pages) |
| combat target (64) | popup | yes, CLOSE (no attack) | 090zd |
| leader for hire (59) | popup | yes, REJECT | 090zd |
| science room (52) | popup | yes, every entry | 090zd |
| GNN (63) | popup | yes, SAVE5 | 090zd |
| AI audience (58) | screen (187) | yes | 090z |
| research selection (53) | screen | yes | 080x |
| new system (61) | popup | **no** — a ship must reach an unexplored star (no move order in the run) | 090zd (stand-in) |
| leader's level / marooned hero (62) | popup | **no** — a leader must gain a level | 090zd (stand-in) |
| warning box (player attacked), strategic combat result, bombing report, treaty "really risk war", Artemis net, Loknar | box | **no** — an AI attack on the player / an attack on a treaty partner | 090zc (the kinds) |
| tactical combat, invasion choice, ground combat, council, Antarans, mutation picker, monster bribe, star rename, occupation popup, end of game | **notice** (parked 1c) | no | — |

Checks 090zc (2), 090zd (2); 090t measures the box's and the popup's text
at 1920 and 3840. Count 413 → **417**.

## Part 5 — Stage 2: HD for each of the six paths — **DONE as far as HD can go; what stays behind the notice is parked**

**The HD message box on fix 29** (built and committed in Part 4, which needed
it; proof first, then applied: see Part 4's table) replaces the notice for
every generic box, on every path a box takes. Walked live on `6859e163`
(Xvfb, SAVE4, guards verified; `evidence/work_order_188/P5_*`, each HD frame
with its native frame beside):

| path (187-original-visibility) | box / screen | HD now | live |
|---|---|---|---|
| 4 — a box over an HD page | the designer's shield warning (warning); the colony screen's BUY (text) | HD message box | drawn, CLOSE → gone, 0.04 / 0.08 s, 0 native frames |
| 4b — a native box's crop in an HD panel | the Races screen's DECLARE WAR confirmation; the Fleets screen's SCRAP confirmation and the "Scrapping ships aborted" warning it chains to | HD message box (the crop is never drawn: `fltbox.SHOW_CROP` False) | NO → treaty unchanged (0 → 0); NO → the chained warning drawn in HD too, ESC closed it (the walk's own "closed" step expected no box and read BAD — the chain is the original's, `gamebox`'s notes say so) |
| 5 — a box over a net screen | the colony-base planet choice (60) and its confirmation, "cannot build there", "really trash" | HD turn popup + HD box | Part 4's 46 turns |
| 1 — an id with no HD screen | the combat target (12 → 64), Turn Summary (40), science room (52), landing (33) | HD turn popups | Part 4's turns |
| 1 — the rest | tactical combat, council, Antarans, invasion, ground combat, mutation, monster bribe, star rename, occupation popup; Hall of Fame (Part 6), Multiplayer (Part 7) | F12 notice | parked 1c |
| 2 — an empty list past EMPTY_HOLD | — | the plain hold (nothing to answer, no notice) | — |
| 3 — a screen declining its id | an engine without the fixes that screen needs | the notice now SAYS so: "COLONY (1): this orion2re lacks the fixes its HD screen needs (python tools/version_check.py)" (HD string file `notice_engine`) | offline (090za) |
| 6 — a screen that cannot vouch | missing extraction; a research list HD cannot rebuild | the notice with the screen's own sentence ("… not extracted — run: python tools/techname_extract.py"); the research screens' "unvalidated" sentence no longer claims the picture is shown ("the game's own picture is on F12") | offline (090za, 048) |

**How many of the six paths are HD now**: 4, 4b and 5 wholly; 1 for every
turn-time popup of the report phase and the combat target; 2 needs none; 3
and 6 cannot be drawn by HD at all (the data is missing: an engine fix or an
extraction) and show the notice with what to do. Checks: 090za extended
(path 3's wording). Count stays 417.
