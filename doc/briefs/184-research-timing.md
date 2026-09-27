# Work order 184 — where the time goes when the research screen opens

Part 1's findings, 27 September 2026, measured before anything was changed
(OrionLayer `5b24070` plus the instrumentation, which is off in normal
play; orion2re `orionlayer-local` `4bf152e4`). Evidence:
`~/orionlayer-fixtures/evidence/work_order_184/P1_*` (one `timing.json`
per run, every entry with its snapshots, field lists and visual digests).

"The research screen" here is what the galaxy map's research window
opens: CHANGE mode, wire id 36, `screens/research_change/`, an overlay over
the HD galaxy map. The turn-start prompt (SELECT mode, 53) is the same
class; see "Other ways in" below.

## How it was measured

`core/entrytiming.py` (switched on by `ORIONLAYER_ENTRY_TIMING`; off, it
wraps nothing and `main.App` pays nothing) timestamps one entry at five
points and derives the order's phases from them:

| phase | from → to | what it is |
|---|---|---|
| (a) | the frame that handled the click began → its message left | the input to the wire |
| (b) | message sent → first snapshot with id 36 parsed | the engine switching screens |
| (c) | that snapshot → the snapshot whose field list the screen validates, parsed | the wait for the panel's data; snapshots counted |
| (d) | every call into the research screen's `enter` / `update` / `render` during the entry | HD preparation (runs inside (c) and (e); reported, not added) |
| d_ready | the list parsed → the frame's render starts | HD's part between the data and the picture |
| (e) | that frame's `_render`, flip included | drawing the first frame |

(a)+(b)+(c)+d_ready+(e) is the whole time, click to the first HD frame of
the panel. Not visible to it: the time a click waits in SDL's queue before
its frame, and a snapshot in the socket before the next `poll` — each at
most one frame.

`tools/research_timing.py W H` drives it: the real `main.App`, the
product's own loop paced by `app.clock.tick(60)` as `main.App.run` is, SAVE4
loaded from the main menu (the flash walk's loader), then per entry a left
click in the HD window on the research window's text (`sb_research_text`;
five more on its icon), 20 frames of the drawn panel, ESC (the exit, which
changes nothing), and 60 frames of map before the next. No research row is
ever activated. The frame trace is on too, so every entry says how many
native frames it presented.

## The phases

Milliseconds, median / maximum. "first" is the first entry after the
client started (one per run), "later" the 19 that followed (9 on the real
desktop). Shares are of the summed totals.

| display, size | entry | n | total | (a) | (b) | (c) | (d) | d_ready | (e) | shares a / b / c / d_ready / e | native frames |
|---|---|---:|---|---|---|---|---|---|---|---|---:|
| Xvfb 1920x1080 | first | 1 | **1238** | 0.1 | 118 | 548 | 537 | 2.3 | 571 | 0 / 10 / 44 / 0 / 46 % | 0 |
| | later | 19 | **685 / 720** | 0.1 / 0.1 | 79 / 118 | 547 / 586 | 6.8 / 7.0 | 2.3 / 2.6 | 40 / 40 | 0 / 14 / 80 / 0 / 6 % | 0 |
| Xvfb 2576x1432 | first | 1 | **1658** | 0.1 | 67 | 592 | 935 | 2.3 | 997 | 0 / 4 / 36 / 0 / 60 % | 0 |
| | later | 19 | **728 / 794** | 0.1 / 0.3 | 128 / 133 | 530 / 594 | 7.0 / 7.4 | 2.4 / 3.7 | 66 / 69 | 0 / 16 / 75 / 0 / 9 % | 0 |
| Xvfb 3840x2160 | first | 1 | **3022** | 0.1 | 144 | 569 | 2171 | 2.4 | 2306 | 0 / 5 / 19 / 0 / 76 % | 0 |
| | later | 19 | **872 / 880** | 0.1 / 0.2 | 144 / 147 | 575 / 581 | 9.0 / 9.6 | 2.4 / 3.1 | 149 / 150 | 0 / 17 / 66 / 0 / 17 % | 0 |
| real desktop 2576x1371 | first | 1 | **1610** | 0.1 | 129 | 577 | 843 | 2.3 | 902 | 0 / 8 / 36 / 0 / 56 % | 0 |
| | later | 9 | **727 / 792** | 0.1 / 0.1 | 131 / 133 | 524 / 589 | 8.4 / 8.7 | 2.4 / 4.2 | 69 / 69 | 0 / 18 / 73 / 0 / 9 % | 0 |

The research window's icon is the same field and measured the same (1920:
670 / 707; 2576: 767 / 772; 3840: 877 / 880, five entries each).

**(c) took exactly two snapshots in every one of the 89 entries** — the
switch snapshot and the list snapshot, 505-594 ms apart, with NOTHING in
between. The "snapshot rate" in that phase is therefore not a rate at
all: the engine sends nothing for ~550 ms (see below). On the galaxy map
the rate is 18.2 a second (55.9 ms, measured in Part 2 — **corrected**:
this line said "6.06 a second (183)", which is the MAIN MENU's rate,
6.05 a second, 164.6 ms; the number was copied, not measured, and the
first pacing probe of Part 2 caught it); in the research loop it is 9 a
second once the list is out (110 ms a pass).

**The real desktop agrees with Xvfb.** At Data's size the window manager
granted 2576x1371, not 1432 (as `main.App._set_mode` records, work order
146); the times and shares are those of Xvfb at 2576 within a few percent
— pygame draws in software on both, so a GPU buys nothing here. Nothing
differs materially.

## Where the time actually goes

1. **The engine's silence, (c): ~550 ms on every entry — the engine's.**
   The first snapshot at 36 is `Screen_Control_`'s own `ext::Tick`
   (mox2.cpp:41), sent before `Tech_Change_` runs, with the empty list
   `Clear_Fields_` left behind (mainscr_main.cpp:699) — the wire said 0
   fields in every entry. `_Tech_Select_` then loads its art, builds the
   entries, draws and fades the panel in (tech.cpp:130-319), and enters
   its loop with `Set_Input_Delay_(5)` (tech.cpp:306). **`Get_Input_`
   returns on a pending input delay BEFORE it calls `ext::Tick`**
   (fields.cpp:161-167), and each idle pass waits `Release_Time_(2)` —
   2 x 55 ms (tech.cpp:349-351, timer.cpp:15). So the first five passes
   send nothing, and the list, and the native picture with it, go out on
   the sixth: 5 x 110 = 550 ms, the measured gap. HD cannot draw a list it
   has not received and must not draw one it has not validated (work
   order 130 C, decision 33).
2. **The engine's switch, (b): 65-147 ms — mostly the engine's.** The
   click is read at the map's next `Get_Input_` (its loop runs at 55 ms,
   18 a second, measured in Part 2 — so 0-55 ms; this said 165 ms, the
   main menu's loop, until Part 2 measured the map), then
   `Draw_Mini_Main_Screen_` and the switch. At 3840 the HD frame is itself
   ~150 ms, so the snapshot waits up to a frame before `poll` reads it:
   there (b) and (c) carry HD's frame time too.
3. **HD's first render on the first entry, (e) first: 571 / 997 / 2306 ms
   — ours.** `cProfile` of phase (d), first entry at 1920 (527 of its 537
   ms are the screen's first `render`):

   | # | call | calls | own ms | cum ms |
   |---:|---|---:|---:|---:|
   | 1 | `core/hud/blocks.py:91(panel)` | 18 | 0.1 | 483.8 |
   | 2 | `core/hud/raster.py:103(shape)` | 19 | 92.2 | 427.3 |
   | 3 | `core/researchscreen.py(render_content)` | 1 | 0.0 | 249.3 |
   | 4 | `core/box.py:99(render)` | 13 | 0.0 | 241.6 |
   | 5 | `core/hud/raster.py:64(_mask)` | 38 | 7.7 | 183.0 |
   | 6 | `core/hud/raster.py:84(blur)` | 37 | 20.4 | 148.8 |
   | 7 | `pygame.pixelcopy.surface_to_array` (the masks, read back) | 38 | 117.4 | 117.4 |
   | 8 | `numpy.ndarray.cumsum` (the blur's box passes) | 222 | 114.2 | 114.2 |
   | 9 | `pygame.transform.smoothscale` (the 3x supersampled masks) | 39 | 48.3 | 48.3 |
   | 10 | `core/hud/glass.py:88(_lin)` (the glass floor's luminance) | 170 | 23.5 | 24.2 |

   The HUD panels of the research screen — the eight entry boxes, the
   eight box skins, the content outline, the lit frame, the exit button —
   are built at the window's size on first use and cached
   (`blocks._cached`), and that building is the whole difference between
   a first and a later entry. **19 shapes, and only 4 distinct
   geometries**: the eight entry panels share one outline and differ only
   in the glass under them, the eight box panels another, and the frame
   is built twice (outline, then lit edge) — every one of them recomputed
   the same masks and blurs. It grows with the pixel count: 0.5 s at 1920,
   2.2 s at 3840. No file is read and no text laid out on the way — `enter`
   is 0.5-1.2 ms, the names and wording loaders are cached.
4. **HD's later frames, (e) later: 40 / 66 / 149 ms — ours, and mostly
   not the research screen's.** The screen's own render is 3-9 ms; the
   rest is the galaxy map drawn under the overlay, and of that the OLED
   floor lift is the bulk: the player's setting `floor_lift: light` makes
   `floorlift.apply` add a colour to the WHOLE window with
   `BLEND_RGB_ADD` on every frame — 33 ms at 1920, 59 at 2576, 130 at 3840
   (the offline profile of the same frame, `tools/research_render.py`).
   Every map frame pays it, and at 3840 it is also why (b) and (c) wait a
   frame for `poll`.
5. **(a), d_ready: negligible** — 0.1 ms and 2-4 ms.

## Other ways in

- The research window's **icon** is the same field as its text and was
  measured separately (above): the same.
- The **turn-start research prompt** (53) is not in SAVE4 as it stands: it
  comes up only when a turn ends with a completed project, and ending a
  turn writes SAVE10, the autosave — this order allows SAVE4 and SAVE5
  only. Parked. By the source it has no (c) at all: its id is set inside
  `_Tech_Select_` (the ScreenOverride, tech.cpp:137), so the first
  snapshot that carries 53 also carries the list — but the same five
  silent passes stand between the engine's own picture and that snapshot,
  and the same first-render cost (it is the same class and the same
  panels) falls on its first frame.

## The native floor (order part 1.4)

The engine's native research screen reaches the wire **in the same
snapshot as the list**: every visual between the switch and the list was
absent (the engine sends nothing in between), and the list snapshot's
framebuffer is the drawn panel — byte-identical to the settled panel's in
9 of 25 entries at 2576; the other 16 differ, by a part not measured here
(Part 2 records those framebuffers). **So on the wire the native screen is
no faster than HD: send → first snapshot of the native panel = (b) + (c) =
~630-720 ms**, and HD's own share after it is d_ready + (e).

The engine's OWN window cannot be watched (open fix 41 keeps it unmapped;
F12 to the original does not work, which Data has accepted for now). By
the source it has the panel drawn and faded in BEFORE the five silent
passes, i.e. ~550 ms before the wire gets it. That is the floor HD cannot
go below without an engine change: (b) plus the time to build and draw —
measured in Part 2 by a scratch build that serialises during the input
delay.

## What OrionLayer can influence, and what is the engine's

| | later entries | first entry | whose |
|---|---|---|---|
| (a) | 0.1 ms | 0.1 ms | ours, nothing to gain |
| (b) | 79-147 ms | 67-144 ms | the engine's (the map's loop, 55 ms — corrected in Part 2 — and the switch), plus up to one HD frame at 3840 |
| (c) | ~550 ms (66-80 %) | ~550 ms | **the engine's**: `Get_Input_` does not serialise during an input delay — an engine change (Part 2: an open fix, parked) |
| (d) / d_ready | 2-4 ms | 2 ms (the first render is in (e)) | ours |
| (e) | 40-150 ms | 0.6-2.3 s | **ours**: the HUD panels built on first use (research screen), the floor lift on every map frame (galaxy map under it) |

Part 2 therefore addresses (e) on both paths, and (c) as an open fix; (a),
(b) and d_ready carry no share worth an intervention.
