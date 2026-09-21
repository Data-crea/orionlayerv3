# Work order 159 — progress

Unattended run, 21 September 2026. The last Fleets pass.

---

## Part 1 — the non-combat ship panel — **DONE**, `8b679c2`

`Print_Scanned_Ship_Data_` returns early for `ship_type` 1, 2 and 4
and prints one HELP.LBX record instead of the data panel
(flt2.cpp:548-575). HD drew the full data panel for all three, which
showed **more** than the original. It draws the paragraph now.

**The types came from the enum.** HD had no `SHIP_TYPE` constants at
all, so `orion2_consts.h:519-526` is transcribed into
`core/structs/ship.py` and `fltrows.PARAGRAPH_HELP` is keyed off it.
The numbering agrees with the source, so there was no finding and no
reason to stop this part.

**A correction: the rectangle is 299 px, not 305.** Both this order
and the status document said 305. `eric.cpp:171` declares the
primitive as `(x, y, width, box_height, text, color)`, so `0x12B` =
**299** is the width and the box is `(18, 282, 299, 183)`. **305 is
not wrong where it appears elsewhere** — it is the drawing window,
`Set_Window_(15, 282, 320, 465)`, which the tab-stop entries correctly
use, and the paragraph box sits inside it.

**The measured wrap, which the order asked for explicitly:**

| | 1920x1080 | 2560x1440 | 3440x1440 | 3840x2160 |
|---|---|---|---|---|
| hole | 694x242 | 925x322 | 925x322 | 1388x484 |
| colony `0x29`, 152 chars | **3 lines**, 60 px | 3, 81 | 3, 81 | 3, 120 |
| outpost `0x6D`, 220 chars | **4 lines**, 80 px | 4, 108 | 4, 108 | 4, 160 |
| transport `0xBD`, 236 chars | **4 lines**, 80 px | 4, 108 | 4, 108 | 4, 160 |

**All three fit at every resolution** — the longest block is the
transport's 160 px in a 484 px hole. So nothing was built for
overflow; the panel's existing `"+{n} more"` path is reused if a
translation ever needs it.

**The no-help state**: all three types show `"Help text not
installed"` and the extractor line — the help popup's own wording from
`labels.json` — and **never the data panel**, which would restore the
fault this removes on exactly the machines least able to notice.
Marked `fallback_panel_help_missing`.

**The colour is the one thing not transcribed** and is parked. See
`159-parked-for-data.md` §1.

**Nothing else moved**: a combat ship's panel is byte-identical at all
four resolutions. Captures, the wrap report and the harnesses in
`~/orionlayer-fixtures/evidence/work_order_159/part1/`.

**Markers moved with the code**: `omission_panel_support_ship_help` is
gone, `deviation_panel_paragraph_colour` and
`fallback_panel_help_missing` took its place, and the suite's tuple
moved in the same commit.

---

## Part 2 — one HStrings (D17) — **DONE**, `8c68edc`

**The stop condition was checked before anything moved.** The order
said to park if Planets' per-enter re-read had a reason. It has none —
not in `planetwords`, not at the call site, and not in `e8169d9`, the
commit that introduced `Words.load` with brief 101. `enter()` simply
rebuilds everything each time.

Four sites became one, `core.hestrings.for_app`: `galaxy_map/boxdraw`
(was per screen), `game_menu/screen` (per app), `planets/planetwords`
(fresh per enter), `screens/fleets/screen` (per screen). **ESTRINGS is
untouched** — 159's decision was about HESTRNGS and widening it would
have been a design choice taken in passing.

**The one intended behaviour change**, in one sentence:
`colonybuild.names_for` read `screen.app.settings.get("language",
"en")`, which raises `AttributeError` on an app-shaped object with no
`settings`, and it now uses the tolerant
`(getattr(app, "settings", {}) or {})` that every other site already
used — so that path draws in `"en"` where it used to crash. Both
states demonstrated in the evidence folder.

**The check the order told me to copy did not exist.** It said to hold
`HStrings` to one site "the same shape as the check that already holds
`HelpText` to one" — there is none. `screenhelp`'s docstring has
claimed "exactly one construction site" since it was written and
nothing enforced it. The new check holds **both** classes to one site
in `core/` and `screens/`, by `ast`.

**Nothing moved on screen**: galaxy_map, game_menu, planets, fleets
and colony_summary at four resolutions each — **all 20
byte-identical**.

D17 marked resolved in `157-parked-for-data.md`.

---

## Part 3 — damaged specials — **PARKED**, no code

**Settled, and worth keeping:** the serialised ship record **is** the
packed struct. `Read_Ship_` and `Read_Ship_Design_` read the
declaration order with no padding, so a record is 129 bytes with
`special_device_damage_flags[5]` at **@118** — the offset the project
already had, now confirmed from the writer's own side.

**Failed:** locating the ship array. A save is a serial stream
(`Read_Game_State_`, savegame.cpp:1419) — settings, a variable number
of colonies, planets and stars, leaders, players, then `_NUM_SHIPS`
and the array — so there is no fixed file offset for the ships. The
scanner written for this part was cross-checked against a number
nobody wrote for it: work order 154's officer count over these same
ten saves, **4 of 185**.

| attempt | ships | officered | saves located |
|---|---:|---:|---:|
| strict | 37 | 0 | 5 of 10 |
| loosened | 144 | 20 | 10 of 10 |
| **154 recorded** | **185** | **4** | — |

**Neither reproduces it**, and the loosened run "found" damaged ships
with one-character names and all-zero fitted-device flags — damage on
ships with no devices. **So no counts are reported.** Reporting "7
damaged ships" from that run would have been worse than the check 154
said proved nothing: a number that is not measuring what it names.

What would settle it is in `159-parked-for-data.md` §2; the cheapest
is one save where Data knows which ship carries special damage.

---

## Part 4 — Fleets is done — **DONE**

`v3_projektstatus.md` gains **"Fleets is done"** under What works: the
screen is complete for the 22 November release, what "done" means is
spelled out rather than implied, and the five remaining items are
tabulated with what each waits on. Each of the five also carries
**AFTER RELEASE** in its own entry under What is missing, with nothing
else changed; item 5 keeps its note that it is one piece of work with
the galaxy map's move preview.

Item 4 moved from What is missing to What works. Work order 154's
parked entry for the same item is marked **BUILT** with the hash.
