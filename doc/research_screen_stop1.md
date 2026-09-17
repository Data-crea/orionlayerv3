# Stop 1 for the research select screen — work order 129 E, 17 September 2026

Report only: nothing of the screen is built. The reading it rests on is
`doc/tech_change_reading.md` (the select and change lists) and
`doc/newtech_reading.md` (the presentation dialog). Everything measured here
was measured against the engine at orion2re `f838c754` on `orionlayer-local`.

---

## 1. Is the offered list reconstructible? (decision 25)

**The category set and the field each offers: YES, exactly.** The
reconstruction walks, per entry, `MOX::_first_field_in_group[_entry_to_group[i]]`
(mox.cpp:103, tech.cpp:45) along `next_field_id` until
`tech_fields[f] == 2` and — in select mode — `f != current_research_field`
(tech.cpp:513-533), using `core/structs/player.tech_fields` (verified in
129 C) and the static table out of techdata.cpp.

Live, on SAVE4 (3509.0) in CHANGE mode (the same builder, with the current
field offered):

| | reconstruction | live FIELD_LIST |
|---|---|---|
| non-empty entries | 8 | 8 radio buttons (type 1) |
| entry 4's field | 60 | the game's own `current_research_field` is 60, and change mode offers it |
| entries offering | 21, 41, 2, 10, 60, 1, 31, 7 | — (not separately labelled on the wire) |

`evidence/work_order_129/E_reconstruct_change_SAVE4.json`.

**The CHOICE ROWS per entry: NOT reconstructible yet, and here is exactly
where.** A row is one application of the offered field, and which
applications exist is not in the static table: `s_tech_field_data.tech[4]` is
all zeros in techdata.cpp and is filled at runtime (techinit.cpp:444-474),
and which of them the player may pick is `tech_applications[212]`, whose
offset (@379) has no verified source. So the row COUNT and the row Y
positions cannot be predicted from the wire today. Two live lists in a new
game had 20 rows over 8 entries (3500.1) and 17 rows (3500.9 in change mode
on SAVE4), and the row rectangles follow the reading's formula
(`x, y+21+y1[k] .. x+218, y+21+y2[k]`, tech.cpp:27-29) — the SHAPE is
confirmed, the CONTENT is not.

**Verdict:** the list needs no patch for WHICH fields are offered. It needs
two spec entries — `tech_applications[]` and the runtime `tech[4]`
derivation — before the rows can be drawn from the wire. Until then a build
can still read the row RECTS off the FIELD_LIST, which is what the game
itself hands over.

## 2. What a build would have to extract, and from where

Nothing extracted from a game installation is committed (decision 40); every
target is already ignored by git under `assets/shared/names/`, and an absent
file is a state the screen explains rather than an error (decision 38).

| what | player's file | records | output | absent |
|---|---|---|---|---|
| field names (Construction, Power, …) and application names | TECHNAME.LBX | strings 1..294 — the same file `tools/techname_extract.py` already reads for building names, as a SECOND output | `assets/shared/names/techfields_<lang>.json`, format-versioned like the others | the screen names the command and shows the numeric ids |
| the panel's own words (headline, "no available application", the RP suffix) | BILLTEXT.LBX | messages 61-73 (change/select), 0-4 (the science room, of which 1 is its headline) | `assets/shared/names/billtext_<lang>.json`, a new extractor in the `hestrings_extract.py` pattern | the JSON labels in `layout.json` stand in |
| the description shown for a selected application | HELP.LBX | ONE record per application id (tech.cpp:732-733) — `help_extract.py` joins CHAINS today, so it needs a single-record mode or a flag | the existing `assets/shared/help/help_<lang>.json`, plus the flag | the box stays empty and says so |

## 3. The twelve questions of `doc/tech_change_reading.md` §8

| # | question | state |
|---|---|---|
| 1 | change mode first, select mode on the framebuffer? | **Decided by Data in chat:** select mode first. |
| 2 | commit path: patch or INJECT_CLICK? | **Open.** Measured today (129 B): an activation commits the entry under the POINTER or nothing at all, a real INJECT_CLICK commits the row it lands on. Option (c) is not authorised. |
| 3 | may HD refuse to send any field id into this list? | **Settled by this order:** it sends nothing at all — no HD screen claims 52 or 53, and a smoke check holds that. |
| 4 | guard the map's parking against a non-map list at screen 0? | **Settled**, work order 128 C: the map parks only into its own list shape. |
| 5 | add @296, @640, @902 and `s_settings.language` to the specs? | **Partly settled** (129 C): `tech_fields` @296 verified; `hyper_advanced_tech` @640 stays unverified (a zero read confirms no offset); @902 and the language byte still open. |
| 6 | transcribe cost / next_field_id / first_field_in_group with a checker, or ask for them on the wire? | **Settled by this order:** transcribed with `tools/research_cost_check.py`; the chain and group tables are read from the source by the same checker's pattern when a build needs them. |
| 7 | extend `techname_extract.py` to fields and applications? | **Open**, planned in §2 above. |
| 8 | a billtext.lbx extractor? | **Open**, planned in §2 above. |
| 9 | descriptions from chained help records or single-record extraction? | **Open** — the reading says the screen reads ONE record; the extractor joins chains. |
| 10 | is the category list popup in scope for the first build? | **Decided by Data in chat:** no. |
| 11 | transcribe the radio index skew and the full-vs-remaining cost difference, or mark them? | **Open.** |
| 12 | who takes the live measurements still NOT SETTLED? | **Partly settled:** pointer survival after an injected click was measured today (129 B) — a real click does select; an activation does not. The art rects and the exit button's label are still open. |

Decided in chat and recorded here: select mode before change mode; the
offered list is reconstructed, not patched; names and texts come from
extractors; the category popup is not in the first build.

## 4. The presentation dialog (the science room), in the six headings

**Source files and builders.** `SCIENCE::Science_Room_` (science.cpp:112-392),
entered through `SCIENCE::Show_Off_Researched_Tech_` (science.cpp:400-430)
from `TECH::Tech_Select_` (tech.cpp:103). The room is one animation
(`SR_R<race>_SC.LBX`) with the device drawn over it, the description text
bitmap at native (221, 44) and the headline at x 145, y 420, width 380. The
same room presents stolen and artifact technology (report.cpp:814, :822).

**Field list and what reaches it.** Three fields: the dummy, a whole-screen
hidden field (0,0)-(639,479) (science.cpp:169) and an ESC hotkey at
(5000,5000) (:171). One input — a click, ESC, a right click, or
`ACTIVATE_FIELD` on either — advances ONE discovery; the last one closes the
room. Measured live: five activations walked a "Nuclear Fission" completion
through its discoveries and then left to the select list.

**Every displayed value against the wire.** The completed field is NOT on the
wire by the time the select list is up (`Tech_Select_` zeroes
`current_research_field` and `research_breakthrough` at tech.cpp:104-105);
while the ROOM is up, `research_breakthrough != 0` is what distinguishes a
research completion from the stolen/artifact case, and it is on the wire
(`s_player.research_breakthrough` @48, verified). The discovery ids come from
the field's own applications — the same gap as §1. The pictures are LBX art,
not on the wire.

**The screen id.** 52 since open fix 24, on the wire only.

**What a patch would carry — described only.** Nothing for this dialog: no
input is needed beyond what already works, and its id is now reported. What
is missing is spec and extractor work (§2).

**Right-click help.** None: the room deactivates the help list
(science.cpp:132) and a right click advances a discovery like any other
input.

## 5. Two findings this stop hands to Data rather than fixing

1. **A click in OrionLayer's window cannot answer either dialog today.**
   `App._handle_click` forwards to the original view only in render_mode
   "original" (F12) — the dispatcher's own fallback does not forward at all
   (main.py:217-225). So while 52 or 53 is up, the player sees the picture and
   clicks do nothing unless they press F12 first.
2. **Even then the choice is unreliable**, because the commit takes the entry
   under the game's own pointer (tech.cpp:354-369): three occasions gave a
   selected field, no selection at all, and a different field respectively
   (129 B, evidence in `evidence/work_order_129/`).
