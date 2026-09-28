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
