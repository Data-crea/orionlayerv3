# 144 — Fleets: moving ships + minimap lines (progress)

Read before designing anything, as the order asks. Every claim below
cites the function it came from.

**Two blockers shaped what this run could deliver** — both in
`144-parked-for-data.md`: another client was on 17362 for the whole
run, so no live step ran; and `workorder_fleets_screen.md` does not
exist on this machine, so I built on the Fleets screen alone.

---

## Part 1 — moving ships: what the original does

### The flow, and the order of it

`FLT1::Fleet_Screen_`'s loop (flt1.cpp:588-665) is the whole state
machine. A minimap click is `MAINSCR::Scan_Galaxy_Map_Fields_`
(flt1.cpp:627), and what happens next depends on two mode flags:

| `_relocate_button_mode` | `_merging_relocations` | a minimap click does |
|---|---|---|
| 0 | 0 | **move the selected ships** (flt1.cpp:644-653) |
| 1 | 0 | set a relocation (`Star_Relocation_`, :640) |
| 1 | — | `ret_map == 1` cancels it (`Cancel_Star_Relocation_`, :636) |
| 2 | 1 | relocate **all** stars to the click (`Set_All_Star_Relocations_`, :657) |

So **moving ships is the default branch**, not a button: select cells,
then click a star. `Relocate` (`input == 0xFC13`, :601) is a different
verb — it sets rally points. `All` on the relocate side is the
merging mode; the grid's own `All` is a selection verb.

The move branch is guarded twice before it fires:

```
first_ship = First_Selected_Ship_()                     flt1.cpp:646
if first_ship >= 0:
    if HACCESS::Player_Can_Order_Ship_(_PLAYER_NUM, ...)  :647
        FLT2::Fltscrn_Move_Ships_(clicked_star_id)        :649
    else Cant_Order_Ship_Message_                         :651
```

and a black hole is refused before any of that (`:642`, message 0x78).

### The function that performs the move

`FLT2::Fltscrn_Move_Ships_` (flt2.cpp:775-822):

1. `Build_Fltscrn_Ship_List_` collects the selected ships; **0 means
   nothing happens at all**, silently.
2. `SHIPMOVE::Ships_Try_To_Move_To_(list, target, &_g_ship_move_info)`
   — this is where legality is decided.
3. `if (_g_ship_move_info.moving != 0)` →
   `SHIPMOVE::Apply_Player_Movement_Order_` and the order stands.
4. otherwise one of three refusals, each a `HAROLD::User_Box_`:
   `blackhole_blocks` (msg 0x21), `out_of_range` (0x90/0x91),
   `hyperspace_flux` (0x24).

### Which state is on the wire, and which is not

| | on the wire | where |
|---|---|---|
| per-icon selection | **yes** | FLTS block, `_fltscrn_big_icon[i].selected` (ext_api.cpp:309-310) |
| `relocate_mode` | **yes** | FLTS `relocate_mode` |
| `merging_relocations` | **yes** | FLTS |
| which star was clicked | n/a — HD chooses it | |
| **legality / result** | **no** | `MOX::_g_ship_move_info` is written nowhere in `src/ext/` |

### Patch or reconstruct (decision 25), and decision 33

`_g_ship_move_info` is the output of `Ships_Try_To_Move_To_`, which
weighs fuel range, drive speed, nebulae, wormholes, jumpgates,
stargates and a navigator officer. It is **not** a pure function of
anything already serialized, so reconstructing it would be "a guess
with extra steps" in decision 25's own words.

And decision 33 draws the line exactly here: it applies "where the
rule is one comparison and the failure is silent; anything larger
belongs on the C++ side or not at all." Three of the four refusals
are silent to HD (a `User_Box_` in the framebuffer), and the rule
behind them is a long computation. **So it belongs on the C++ side:
serialize `_g_ship_move_info`.**

One refusal *is* one comparison and can be held in HD under decision
33: the black hole (`_star[clicked].spectral_class == 6`,
flt1.cpp:642), which `core/structs/star.is_black_hole` already
answers.

**Not built this run**, because the patch cannot be validated: the
running engine predates any new build and since work order 140 Data
starts the engine. Designing against an unvalidated wire field and
committing the result would be the thing this project keeps warning
about.

### One thing worth knowing before the HD side is written

A refused move opens a **modal** `User_Box_` in the engine. That is a
screen-state change HD must expect, not merely a message it misses —
the same shape as decision 59's GAME popup. Any HD move path needs an
answer for "the engine is now showing a box" before it sends its first
order.

---

## Part 2 — the lines on the minimap (delivered)

### What they are

`FLT1::Draw_Fltscrn_Relocation_Lines_` (flt1.cpp:1451-1490). For every
star where `HACCESS::Star_Has_Relocation_(star, _PLAYER_NUM)` — that
is `relocate_ship_to[player] != -1` (haccess.cpp:114) — it draws a
line from that star to `Relocation_(star, player)`.

They are **relocation lines**, and the mockup is not evidence about
them in two ways:

* **They are grey, not green.** The table is palette
  `6,7,7,8,8,9,9,10` (flt1.cpp:1460-1467); in FONTS.LBX entry 9, the
  palette this screen installs, those are `(52,52,60)` through
  `(88,88,96)`. The green table `0x6E,0x6F,0x70` belongs to the
  *galaxy map's* version (mainscr.cpp:684).
* The minimap's version is **not gated** by
  `_settings.show_relocation_lines`; the galaxy map's is
  (mainscr.cpp:690).

### Are they the same thing as the galaxy map's? (decision 68)

**Same fact, two looks, and one routine underneath.**

| | Fleets minimap | galaxy map |
|---|---|---|
| function | `Draw_Fltscrn_Relocation_Lines_` flt1.cpp:1451 | `Draw_Relocation_Links_` mainscr.cpp:682 |
| data | `relocate_ship_to[player]` | **identical** |
| colours | palette 6..10, grey | 0x6E,0x6F,0x70, green |
| gated | no | `show_relocation_lines` |
| ends | star +4 → target +3 | star → target |
| reaches | `Draw_Ship_Destination_Line_` → `Draw_Directional_Multi_Colored_Line_` | `Draw_Directional_Multi_Colored_Line_` |

The last row is the answer: both end in the same animated
multi-coloured line routine with `_multi_colored_line_start`, which
`maplines.directional`, `phase_at` and `wave_pieces` already
transcribe. So decision 68 is satisfied by sharing that path, not by
making the two look alike — the difference in colour and gating is the
original's, and flattening it would be inventing.

### What this means for the galaxy map's existing marker

The omission in `maplines.py` read: *"the setting and
`relocate_ship_to` (star offset 205) are not verified."*

**Half of that is now spent.** `relocate_ship_to` is verified at
offset 205 by decision 23's header route: the whole `s_star_data`
layout was taken from `orion2.h`'s field order and reproduces every
offset the spec already held — name 0, x 15, y 17, size 19, owner 20,
pict_type 21, spectral_class 22, system_special 159, wormhole_star_id
160, blockaded 162, visited 171, colonize_player 175, planet_index
195 — and the total size 234. Twelve agreements and the size; 205 is
the thirteenth value, and `195 + 5*2 = 205` independently.

**The other half still stands**: `show_relocation_lines` gates the
galaxy map and nobody has read whether the option is reachable in this
build. So the marker was **rewritten to say exactly that**, not
deleted and not quietly satisfied, and the remaining half is parked as
question 4.

### What was built

* `core/structs/star.RELOCATE_OFFSET` / `relocation_target()` — the
  verified offset with its derivation in the comment.
* `maplines.relocation_pairs()` — the shared fact, one walk over the
  stars, used by the minimap and available to the galaxy map.
* `fltdraw.draw_relocation_lines()` — the minimap's lines through
  `maplines.directional`, `wave_pieces`, `clip` and `stroke`
  (decision 68), clipped to the inset as the original clips, ends
  nudged +4/+3 as the original nudges, colours from the skin with
  their palette indices recorded.
* Five smoke checks (one `ok`), including one that fails if the ramp
  ever becomes green — i.e. if the mockup is ever believed over the
  source.

Renders: `~/orionlayer-fixtures/evidence/work_order_144/`, four
resolutions with and without the extracted artwork, with three
relocations in the fixture.

---

## Acceptance, honestly

| | |
|---|---|
| moving ships live on SAVE4/SAVE5 | **not run** — client attached; and the patch it needs is not built |
| SAVE1-9, SAVE11 hashed before/after | **not run** — nothing connected, so nothing could change |
| SAVE8 untouched | held: nothing connected |
| one client at the server | **held by not connecting** — one was already there |
| minimap lines vs native, side by side | **not run** — needs the engine |
| deviations marked in module, status doc and smoke | done for what was built |
| smoke green, commit through the hook, no push | done |
