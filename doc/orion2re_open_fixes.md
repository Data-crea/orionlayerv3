# orion2re — open fixes for Joes

Rewritten 30 August 2026. **Replaces `patch_inject_click_motion.md`**,
which had drifted: the status document listed three open fixes and
named that file as their home, and the file contained three different
items, one of which was already applied. Two documents disagreeing
about what is being asked of somebody else is the worst place for
that failure mode, so there is now exactly one list and everything
else points at it.

**This file is the complete list.** If a request is not here, it is
not being made.

**Checked against a source tree the same day** — three of the five
are already in it, and the statuses below say so. See the grep
section for what was found where.

---

## Status at a glance

| # | Item | Status | Costs us |
|---|---|---|---|
| 1 | `Server::SendFrame` drops a client on a short write | **Applied** in the 30 Aug tree — verify | Nothing, if applied |
| 2 | FIELD_LIST only sent on a field-count change | **Applied** in the 30 Aug tree — verify | Nothing, if applied |
| 3 | INJECT_CLICK: coordinates mapped as window coordinates, AND the real mouse overwrites the injected pointer every frame | **Both halves patched locally** 4 Sep 2026 (`doc/ext_inject_click.patch`), **and both VERIFIED LIVE 5 Sep 2026**; open upstream | Without them an injected click lands on the wrong pixel on any window that is not 640x480, and the pointer walks off it before a handler that reads `Pointer_X_()` looks |
| 4 | INJECT_CLICK pushes no MOUSEMOTION before the buttons | Open | Radio buttons toggle unreliably |
| 5 | `racesel.lbx [entry 138]` crash on Custom Race Accept | **Applied** in the 30 Aug tree — that is why it stopped reproducing | Nothing |
| — | Screen IDs for Select Race and Custom Race | **Applied** (`doc/ext_screen_id.patch`), four hunks, live-confirmed 5 Sep 2026 | Nothing |
| 6 | `s_0_0055110c` / `s_1_00551110` declared `[3]` and `[4]`, defined three times | **Question, not a fix** | Nothing today |
| 7 | `Draw_Colony_Prod_Both_` sign-tests `imports[t]` as a byte once and as a word once | **Question, not a fix** | Nothing today; changes the FOOD/RESEARCH/BC rows, never INDUSTRY |
| 8 | Two native messages in `colmove.cpp` disagree, and the one describing a capability is on an unreachable branch | **Question, not a fix** | Nothing today; decides which refusal HD shows |
| 9 | `Do_Colony_Info_Pop_Stuff_For_Pop_`'s second loop is named `race_idx` and iterates `MASK_CONQUERED` | **Question, not a fix** | Nothing today; decides how a pop cell is read and named in HD |
| 10 | `ENGINE_VERSION` does not move when a serialized record layout changes | **Request** | A client cannot tell two incompatible builds apart and reads at the wrong offset |
| 11 | `COLONY::Colony_Has_Natives_` tests nibble **8** (android), not 9 (native) | **Fix** — reproducible in a named save | Nothing for us; for the game, the occupation-policy popup is offered to the wrong colonies |
| 12 | A pop move has no command: it has to be a click choreography into the game's own list window | **Request**, and **patched locally** 10 September 2026 (`doc/ext_move_pop.patch`), **VERIFIED LIVE** the same day; open upstream | Without it a move costs four snapshot round trips instead of one — 725 ms against 55 ms measured — and every one of them is a click that can land on the wrong row |
| 13 | The Planets screen's five restriction toggles (`PLNTSUM::_filter_out_*`) are not in the snapshot | **Request** | HD cannot know which filters the game already has on; seen live 13 September 2026 — the range toggle was on before the HD screen opened, and the two lists disagreed |
| 14 | The GAME popup's save slot list (names, stardates, dates, status, type) is not on the wire | **Applied** 16 September 2026 by Data (`doc/ext_save_slots.patch`), confirmed live the same evening; required by `tools/version_check.py`; open upstream | The HD Load and Save dialogs show slot numbers only; reading SAVEn.GAM from a folder of our own is refused (fundament 60) |
| 15 | A scroll field's value can only be set by the pointer | **Answered 16 September 2026**: with open fix 3 applied an injected click sets it (measured live); no request | Nothing while open fix 3 is applied; the HD volume bars depend on it |
| 16 | Save dates print the year as `tm_year`: 126 | **Observation** | Nothing; HD shows what the engine formats |
| 17 | The Load dialog's first visit prints dates without a month | **Observation** | Nothing; HD shows what the engine formats |
| 18 | The Settings dialog has two different Alt-key label sets | **Observation** | Nothing; HD shows the screen path's set |
| 19 | A save name confirmed with Enter keeps the edit cursor `_` | **Observation** | Nothing; HD reproduces it |
| 20 | The fleet box's ship selection is not on the wire, and a single ship cannot be toggled from outside | **Applied** 15 September 2026, revision 2 (`doc/ext_fleet_selection.patch`: icon owners, then per node ship_idx and selected, then the fleet box chain; revision 1 applied and taken back out the same day, briefs 118/119), confirmed live on SAVE5; required by `tools/version_check.py` | — while applied. Without it HD draws no fleet box and cannot move a fleet from the map |
| 21 | One ship in the fleet box cannot be selected or deselected from outside | **Applied** 15 September 2026 (`doc/ext_fleet_select_ship.patch`, `MSG_SELECT_SHIP` 0x85), confirmed live on SAVE5 (brief 119); required by `tools/version_check.py` | — while applied. Without it HD can show the selection but not change it |
| 22 | Select Race reported `SCREEN_RACE` (6), which the Races/diplomacy screen owns — our own `ext_screen_id.patch` hunk 1 | **Applied** 17 September 2026 (work order 128 B, Data's decision: a synthetic id): race selection reports 51; orion2re 3305d78c on `orionlayer-local`; `doc/ext_screen_id.patch` revision 2; required by `tools/version_check.py`; seen live before and after | — while applied. Before: the HD map's RACES button opened HD Select Race over the Races screen (seen live on SAVE4) |
| 23 | An activation of a research choice row with the pointer over no entry crashes the game | **Observation**, seen live 17 September 2026 (work order 128 C); **CLOSED locally 18 September 2026 by item 25**, which guards the dereference at the line that performed it. Still open upstream | Nothing while item 25 is applied. Without it, a client that activates a choice by field id kills the game |
| 24 | The two turn-start research dialogs (science room, SELECT NEW RESEARCH) both report SCREEN_MAIN, so a client cannot tell them from the galaxy map | **Applied** 17 September 2026 (work order 129 B, Data's decision: synthetic ids on the wire only), orion2re f838c754 on `orionlayer-local`, `doc/ext_research_screens.patch`; required by `tools/version_check.py`; open upstream | — while applied. Without it HD draws the map with an active TURN button over both dialogs, and a field sent into the select list crashes the engine (item 23) |
| 25 | The research selection commits the entry under the POINTER, not the field that was activated | **Applied** 18 September 2026 (work order 130 B, Data's decision: option (c) of `doc/tech_change_reading.md` §5.1), orion2re e9d07528 on `orionlayer-local`, `doc/ext_tech_activate.patch`; required by `tools/version_check.py`; open upstream | — while applied. Without it an HD research screen cannot choose a row at all: the choice lands on whatever the cursor rests on, or crashes the engine (item 23) |
| 26 | SELECT NEW RESEARCH commits a row by itself, about a second and a half after the science room hands over to it | **OPEN, deferred by Data 19 September 2026.** Observation, seen three times and measured once with a send counter on 18 September (work order 130's live run). Data reproduced the counter-case on 19 September: same binary, NO client connected, the dialog clicked away with a real mouse — the list waits. So open fix 25 is not the cause | A client cannot rely on reaching the list before it has chosen; three of six attempts to choose in HD lost the occasion. The player's way round it is to click the completion dialog away in the orion2re window with a real mouse |
| 27 | The fleet screen's view state is not in the snapshot | **Applied** 19 September 2026 (work order 134 C), orion2re `cc5ec133` on `orionlayer-local`, `doc/ext_fleet_screen_state.patch`; required by `tools/version_check.py`; **NOT CONFIRMED LIVE** — 134's live part is parked; open upstream | — while applied. Without it HD cannot know which stack the fleet screen shows, which ships are in the grid, which are selected, where the list is scrolled or which filters are on, and hands over to the original picture |
| 28 | One ship cannot be selected on the fleet screen | **Applied** 19 September 2026 (work order 134 C), orion2re `e6199966` on `orionlayer-local`, `doc/ext_fleet_screen_select.patch`; required by `tools/version_check.py`; **NOT CONFIRMED LIVE**; open upstream | — while applied. Without it only ALL changes the selection, so a subset of a stack cannot be moved or scrapped from HD |
| 30 | The Leaders screen's view state is not in the snapshot — button mode, selection, the colony view's two stars, the ship view's stack and grid, the hire popup's leader | **Applied** 26 September 2026 by work order 175 (orion2re `cc542e02`, `doc/ext_officer_screen_state.patch`); open upstream | Without it the HD Leaders screen shows every leader, both views, the buttons and the galaxy box, and sends only what it can confirm on the wire (the view tabs, HIRE, CANCEL, RETURN, a click on a leader for hire); pool, dismiss, assignment, the star display and the ship grid are drawn as a marked placeholder |
| 31 | A session-launched engine hangs in its first logo frames when its window is not being drawn: every present waits for VSync, and the game thread waits for the present without a timeout | **Applied** 26 September 2026 by work order 175 (orion2re `f98b8547`, `doc/ext_present_no_vsync.patch`): `ORION2RE_NO_VSYNC=1` presents without waiting; open upstream | Without it an unattended live run hangs in about one start in eight while the screen is locked or another window covers the engine's; `tools/engine_start.py` detects the hang and starts again |

Items 3 and 4 are both about INJECT_CLICK and both live in the same
code path, but they are separate faults: 3 is where the coordinates
land, 4 is whether the game notices the click at all. Fixing one does
not fix the other.

---

## Checked against a source tree, 30 August 2026

The four greps below were run against the orion2re tree as uploaded
on 30 August. **Three of the five items are already in it** — the
table above still lists them as open because it was written against
the 28 August snapshot, and a request list that asks for work
somebody has already done is the same failure as one that has drifted
the other way.

```
grep -n "EWOULDBLOCK\|POLLOUT\|EAGAIN" src/ext/ext_server.cpp
   -> ext_server.cpp:305 err != EAGAIN, :316 pollfd{fd, POLLOUT, 0}
      item 1 APPLIED — retry loop, no longer "if (n <= 0) return false"
grep -n "HELLO_REPLY" -A 20 src/ext/ext_api.cpp | grep FIELD_LIST
   -> ext_server.cpp:190 fields_dirty_ = true,
      ext_api.cpp:307 || g_server.TakeFieldsDirty()
      item 2 APPLIED — a connecting client gets the list at once
grep -n "_old_race = static_cast" src/game/racesel.cpp
   -> racesel.cpp:305
      item 5 APPLIED — which explains why the crash stopped reproducing
grep -n "SDL_EVENT_MOUSE_MOTION" src/ext/ext_api.cpp
   -> nothing; ext_api.cpp:204 still pushes DOWN and UP only
      item 4 OPEN
```

Item 3 is unchanged too: `MSG_INJECT_CLICK` passes `cmd.param1/2`
straight into the SDL event, so the window-coordinate mapping in
`platform.cpp` still applies.

**So the real list is two items, 3 and 4, and they are the same code
path.** Confirm against your own working copy before acting on this —
what was uploaded is a tree, not necessarily *the* tree.

## Check what your working copy already has

Four greps settle it:

```bash
cd ~/orion2re
grep -n "EWOULDBLOCK\|POLLOUT\|EAGAIN" src/ext/ext_server.cpp
grep -n "SDL_EVENT_MOUSE_MOTION" src/ext/ext_api.cpp
grep -n "_old_race = static_cast" src/game/racesel.cpp
grep -n "HELLO_REPLY" -A 20 src/ext/ext_api.cpp | grep -n "FIELD_LIST"
```

In order: item 1 (a retry loop rather than `if (n <= 0) return false`),
item 4 (a motion event before the button events), item 5 (the one-line
`_old_race` assignment), item 2 (a field list sent right after the
handshake).

---

## 1. `Server::SendFrame` drops a client on a short write

### Symptom

A client disappears and has to reconnect. Historically this was
blamed for every "orion2re disconnected / reconnecting" line in
OrionLayer's log.

### Root cause

The send loop is `if (n <= 0) return false;`, and on a non-blocking
socket `EWOULDBLOCK` returns -1 without anything being wrong. A
client that stalls briefly — loading assets, say — while 300 KB
visual frames keep arriving is dropped rather than waited for.

### Fix

Poll for `POLLOUT` and retry with a timeout instead of failing on the
first short write.

### Correction, 30 August 2026 — read this before prioritising it

**The claim that this caused OrionLayer's reconnects was wrong, and
it was our fault, not yours.** OrionLayer's own stale-connection
watchdog was set to 3 seconds and fired during periods when orion2re
is legitimately silent — `ext::Tick()` runs from
`fields::Get_Input_()`, so anything without an input loop publishes
nothing. The tell was in the log all along: after each reconnect
there was no `HELLO_REPLY`, and `AcceptClients()` also runs inside
`Tick()`, so the server had not ticked at all. A healthy server that
had merely dropped a client would have answered the new connection in
milliseconds.

The watchdog is now 10 seconds and can be held open by anything that
knows the game is about to go quiet. Since that change, no reconnects
have been observed at all.

So item 1 may still be a real bug — the code path is still wrong as
written — but it has **no confirmed symptom**. It should not be
prioritised on the strength of the old claim.

---

## 2. FIELD_LIST is only sent when the field count changes

### Symptom

A client that connects or reconnects in the middle of a screen never
receives the current field list, and cannot act on that screen at
all.

### Root cause

`ext_api.cpp` compares the field count against the previous tick and
sends only on a change. `EVT_SCREEN_CHANGED` triggers an extra
resend, which covers a reconnect *between* screens but not one
inside a dialog.

### Fix

Send the field list right after `HELLO_REPLY`.

### Why it still matters

This is what turned a harmless reconnect into a stuck game: the
client came back during MOO2's home-star-name dialog, the field count
had not changed since, so no list ever arrived and the injection
chain waited forever. OrionLayer no longer reconnects mid-chain, so
the specific case is closed on our side — but any client that
reconnects for any other reason still hits it.

---

## 3. INJECT_CLICK coordinates are mapped as window coordinates

### Symptom

An injected click lands somewhere else entirely on any window larger
than 640x480. On a 1828 px window, (510, 326) arrives near (178, 114).

### Root cause

INJECT_CLICK carries 640x480 game coordinates, but `platform.cpp`
maps the injected SDL event through `Map_Window_Point_To_Game_Point_()`
as a *window* coordinate, and `Sync_Mouse_State_From_SDL_()`
overwrites the position every frame.

### Fix

**Done, and it is the first of the two options below.** The second
was considered and is wrong: documenting the command as taking window
coordinates pushes onto every client a number that is on no wire
message and, under Wayland, not measurable at all.

Either bypass the mapping for injected events, or document the
command as taking window coordinates and let clients convert.

### Cost to us

Every free map click and the New Game toggles are affected, because
those are the places where no field ID exists and INJECT_CLICK is the
only option. OrionLayer prefers ACTIVATE_FIELD wherever a field ID
exists precisely to avoid this.

### Confirmed again 4 September 2026, on the colony summary

The population move needs two clicks at computed positions and there
is no field id for "icon 7 of the farmers" (decision 39), so it is
the first thing in OrionLayer that actually depends on this. The
first attempt picked up **nothing**: `Get_Cluster_` clears bit 0x200
on exactly the pops it takes and that is on the wire, so "nothing
held" is a reading rather than a guess.

**The measured example above predicts that shape.** A click sent at
game (230, 49) on a window of width W arrives near
`(230 * 640 / W, 49 * 480 / H)` — for the 1828 px window in the
symptom that is about (80, 17), which is in the title bar and hits
no field at all. Picking up nothing is what landing outside every
field looks like.

**And the other three things that "work live" are not evidence
against it**, which is worth stating because it looked like they
were:

  the sort tabs go through `INJECT_KEY` and carry no coordinate at
  all — verified in OrionLayer's own log, `Action: entry sort name ->
  hotkey 'n'`, not the `native_click` fallback;
  the HD list's scrolling is viewing-only and sends nothing to the
  game at all (fundament 46, asserted by a smoke check);
  the detail panel is drawing.

So every path that avoids coordinates works and the one path that
uses them does not. RETURN is the only other coordinate user in the
tree and has never been exercised live.

**A client cannot work around it blind.** The mapping needs the
window size, and nothing on the wire reports it — neither
`HELLO_REPLY` nor the snapshot. A client can pre-scale its
coordinates only if a human tells it how big the window is, which is
not a fix so much as a note about what the missing number costs.

### And at 640x480 it still does not work — the mapping is only half of it

Run again with the game window at 640x480, where
`Map_Window_Point_To_Game_Point_` is the identity and there is
nothing to pre-scale, the pick-up **still picked up nothing**. So the
coordinate mapping is not the whole cause, and the rest of it is the
second sentence of the root cause above, which turns out to matter
more than the first.

`Sync_Mouse_State_From_SDL_` (platform.cpp:825-846) reads the REAL
mouse with `SDL_GetMouseState` and calls
`Set_Present_Mouse_Position_` again, from the main loop (`:390`) and
from `Service_Pending_Window_Events_` (`:1127`). `INJECT_CLICK` sets
the position and then enqueues the button (`:1171-1172`), so the
injected position is correct for an instant and is overwritten before
the game consumes the click.

**Which half of a click survives, and which does not.** The button
event carries the injected coordinates in the queue, so a handler
that reads the EVENT sees the right place — the field is resolved
correctly. A handler that reads the POINTER sees the real mouse. The
colony summary's population pick-up does the second:
`COLSUM::Get_Selected_Pop_` (colsum.cpp:1006) walks the icons against
`mouse::Pointer_X_()`, finds none where the real cursor is not
standing, returns -1, and `Get_Cluster_` is never called. The visible
result is a click that does nothing whatsoever.

Consistent with that, the scan box after the attempt showed a
different row's colony — the one under the physical cursor — rather
than the row that was clicked.

**So the fix proposed above is not sufficient.** Bypassing the
coordinate mapping for injected events leaves the sync overwriting
the position a frame later.

**And of the two ways round it, one is already how the engine
works.** "Carry the position with the queued event" is not a change
to make: `Enqueue_Mouse_Input_Event_` already carries x and y
(platform.cpp:132), `mouse::Pointer_X_()` calls
`Pump_Game_Input_Queue_()` before reading (mouse.cpp:51-54), and
`User_Mouse_Handler_` sets the logical position from the event
(mouse.cpp:237). The design is right and something else defeats it.

**What defeats it is the coalescing, not just the overwrite.**
`Enqueue_Mouse_Input_Event_` merges into the previous event when the
button state matches, overwriting its coordinates rather than
appending (platform.cpp:138-147). An injected button-up carries
`buttons = 0` and so does the sync's position event, so the sync
rewrites the injected release to wherever the physical mouse is.
Pumped, the press is handled at the injected point — which is why
the right field is reached — and the release then walks the pointer
away before `Get_Selected_Pop_` asks.

**A patch is in OrionLayer's tree at `doc/ext_inject_click.patch`,
and it now covers BOTH halves of this item.** For the pointer, it
suppresses the sync while injected input is unconsumed, cleared when
the queue drains rather than after a fixed number of frames, so the
window is exactly as long as the events are in flight; its price is
written up with it, that during those one or two frames the game does
not see real mouse movement. For the coordinates, see the section
below.

### THE COORDINATE HALF — applied 4 September 2026

`MSG_INJECT_CLICK` (ext_api.cpp:205) pushed the SDL event with
`down.button.x = (float)cmd.param1` verbatim, and the game then runs
it through `Map_Window_Point_To_Game_Point_` (platform.cpp:219) like
any real event — which calls `SDL_RenderCoordinatesFromWindow`, i.e.
**window space -> logical 640x480 space**. So the client's game
coordinates were read as window coordinates. The mapping is the
identity only when the window happens to be exactly 640x480, which is
its creation size (`k_windowed_logical_width/height`,
platform.cpp:893) — and a resizable, *visible* window that a human
can drag.

Visible: `SDL_ShowWindow` is guarded by `if (!ext::g_hide_window)`
(platform.cpp:1391), but `ext::Init()` — which sets that flag — is
called from `mox2.cpp:382`, long after `Run_Main_Loop_` has created
and shown the window. The flag therefore never suppresses anything.
The fundament said the game window is hidden; it is not.

**A client cannot compute its way out of this.** The window size is
on no wire message, and it is not measurable from outside either: on
GNOME Shell under Wayland, `xdotool` and `xwininfo` see only X clients
and report nothing, `org.gnome.Shell.Eval` answers `(false, '')`
because unsafe-mode is off, and
`org.gnome.Shell.Introspect.GetWindows` answers `AccessDenied`.

**And setting the window to 640x480 is the worse answer**, which is
why it was rejected rather than merely not chosen. Under Wayland it
is reachable only by restarting the game, it has to be redone every
session, and — by the paragraph above — nobody can afterwards check
whether it is still true. A precondition no one can verify is one
that goes quietly missing, and the failure it then produces is a
click that lands on the wrong row with every number on both screens
still correct.

### The fix stays inside the ORION2RE_EXT boundary

The engine already owns the inverse mapping and exports what is
needed to reach it, so **no `platform.cpp` change was required for
this half**:

    platform::g_main_window                platform.h:31 (void*)
    SDL_GetRenderer(window)                SDL_render.h:434
    SDL_RenderCoordinatesToWindow(...)     SDL_render.h:1680

`Game_Point_To_Window_Point_` in ext_api.cpp converts with those
three, and both injection sites call it: `MSG_INJECT_CLICK` and
`MSG_CANCEL_FIELD`, the latter because its point comes from a field
rect and is in game space too — the same defect through a different
door. The comment that was already above the first one — *"Push a
mouse click at (x, y) in 640x480 space"* — is now true.

Using the exact inverse rather than a scale factor is the point:
letterboxing and non-integer scales come out right without anyone
computing them, and asking the renderer at the moment of the click is
the only way to be current, since the window can be resized between
one click and the next. If the renderer cannot be reached the point
passes through unchanged, which is the previous behaviour rather than
a silent zero.

**This half diverges from nothing.** `src/ext/` is the Extension
API's own directory and is untracked in Joes' tree, so ext_api.h and
ext_api.cpp are our code. The single `platform.cpp` hunk from the
pointer half remains the whole local divergence.

### APPLIED LOCALLY — 4 September 2026

Applied by decision to the working tree at `~/orion2re`, engine
**1.60.0**, git `cf4d9617`, and rebuilt. Recorded here rather than
left implicit: **OrionLayer is now running against an engine that
exists only on this machine.** At the next update from Joes that
either conflicts visibly or vanishes silently, and the second is the
one to watch for — the symptom of it vanishing is the population move
going quiet again in exactly the way it did before.

To take it back off, one line:

```bash
cd ~/orion2re && patch -R -p1 < ~/orionlayerv3/doc/ext_inject_click.patch
```

then rebuild. The patch is checked in all three directions, and the
third is the one that makes it a request rather than a note: applying
it FORWARD to a reconstructed pristine tree reproduces the live tree
**byte-for-byte** in all three files. Reverse also applies cleanly
against the live tree, and a second forward apply there is refused as
"previously applied" rather than doubling the hunks.

The pristine tree it was checked against is not a guess either: it
was produced by reverse-applying the previous version of this patch
to copies of the three files, so the baseline is the engine as Joes
has it.

Note the tree was **not** clean when this went in — `CMakeLists.txt`,
`fields.cpp`, `mox2.cpp`, `platform.cpp` and `racesel.cpp` already
carried local changes and `src/ext/` is untracked entirely, because
the Extension API itself lives there as a local addition. So
`git checkout -- src/game/platform.cpp` is NOT the way back: it would
take the existing ext hooks with it. The reverse-patch line above is.

**There is one accidental lever and it is not a workaround.** The
sync returns early when `g_window_focus_state == 0`
(platform.cpp:826), so an injected position survives while the window
is unfocused. Nothing on the wire reports focus, so a client cannot
know whether it is in that state, and a rule of "click only while
unfocused" would be a behaviour depending on something invisible.
Recorded because it explains why an injected click may appear to work
intermittently, not because it is a way to live with the bug.

---

## 4. INJECT_CLICK pushes no MOUSEMOTION before the button events

### Symptom

INJECT_CLICK sometimes toggles a radio button and sometimes does
nothing. Affects New Game fields 11–13 and every other type=1 field.

### Root cause

`ProcessInput()` pushes button events with correct coordinates, but
`Scan_Field_()` reads the pointer through
`mouse::Pointer_X/Y_()` → `platform::Get_Mouse_X/Y_()` → `g_mouse_x/y`,
which are updated from `Enqueue_Mouse_Input_Event_` via the present
thread. `ext::Tick()` pushes the events and `Get_Input_()` polls
immediately afterwards; if the present thread has not processed them
yet, the game thread sees no mouse input that frame.

### Fix

Push an `SDL_EVENT_MOUSE_MOTION` before the button events, so the
position is enqueued before the button state changes.
`platform.cpp` handles motion events at lines 1136–1143.

```cpp
case MSG_INJECT_CLICK:
{
    SDL_Event motion{};
    motion.type = SDL_EVENT_MOUSE_MOTION;
    motion.motion.x = (float)cmd.param1;
    motion.motion.y = (float)cmd.param2;
    motion.motion.xrel = 0;
    motion.motion.yrel = 0;
    SDL_PushEvent(&motion);

    SDL_Event down{};
    down.type = SDL_EVENT_MOUSE_BUTTON_DOWN;
    down.button.button = SDL_BUTTON_LEFT;
    down.button.x = (float)cmd.param1;
    down.button.y = (float)cmd.param2;
    down.button.down = true;
    SDL_PushEvent(&down);

    SDL_Event up{};
    up.type = SDL_EVENT_MOUSE_BUTTON_UP;
    up.button.button = SDL_BUTTON_LEFT;
    up.button.x = (float)cmd.param1;
    up.button.y = (float)cmd.param2;
    up.button.down = false;
    SDL_PushEvent(&up);
    break;
}
```

The same applies to CANCEL_FIELD (right-click).

---

## 5. `racesel.lbx [entry 138]` crash on Custom Race Accept

### Symptom

Accepting a Custom Race crashes the Flag Screen with
"racesel.lbx [entry 138] could not be found", when the Custom Race
portrait (index 13) was the last displayed race before entering
`Racial_Option_Screen_`.

### Root cause

`Draw_Flag_Screen_()` (racesel.cpp:819) computes the LBX entry as
`race_index + _old_race * MAX_PLAYERS + 0x22`. With `_old_race = 13`
that is `0 + 13 * 8 + 34 = 138`, which does not exist. `_old_race` is
set to `_displayed_race` by `Draw_Race_Selection_Screen_()`
(line 973), and the stock-race handler at line 301 enters
`Racial_Option_Screen_()` without correcting it. The lastrace.rac
path at line 388 already does.

### Fix — one line

Around line 304, before calling `Racial_Option_Screen_`:

```cpp
} else {
    struct_::Copy_Structure_(plr->traits, _race_specials[i], sizeof(plr->traits));
    plr->race = (uint8_t)i;
    strlcpy(plr->race_name, MOX::_race_names[i], sizeof(plr->race_name));
    _old_race = static_cast<int16_t>(i);    // <- ADD THIS
    fields::Deactivate_Auto_Function_();
    fields::Clear_Fields_();
    if (Racial_Option_Screen_(plr) == 1) {
```

`i` is always 0–12, so the entry is always valid. No other path is
affected — stock race and lastrace.rac already set `_old_race`.

### Status: not reproducing

On 30 August this exact path was walked repeatedly — Select Race,
Custom Race portrait, Elerian as the base portrait, Accept — and the
Flag Screen came up every time with its eight tiles. Either the fix
is in the working copy or the analysis was incomplete. **Run the
grep above before spending time on it.** Recorded rather than
deleted, because a crash that stops reproducing is not the same as a
crash that is fixed.

---

## Applied: screen IDs for Select Race and Custom Race

Not a request; recorded so it is not proposed again. **The patch is
`doc/ext_screen_id.patch`** as of 5 September 2026 — until then it
lived as a loose file in the orion2re working tree and was therefore
in no list at all, which is the failure this document exists to
prevent.

`MOX::_current_screen` is the engine's dispatcher variable
(`MOX2::Screen_Control_`, mox2.cpp:35) and neither screen is in its
switch: race selection is CALLED from `newgame.cpp:108` and three
other sites, and `Racial_Option_Screen_()` is called from inside it.
So the API kept reporting the caller and no client could tell any of
the three apart. Four hunks, all `#ifdef ORION2RE_EXT`: SCREEN_RACE on
entry to race selection and the restore on its cancel, the synthetic
50 on entry to Custom Race and the restore on its cancel. Documented in
`doc/ext_api_dokumentation_v3.md` under "racesel.cpp — 3 insertions",
and confirmed live: OrionLayer's Custom Race screen declares
`GAME_SCREEN_ID = 50` and switches to it.

**Both screens are correct on every exit as of 5 September 2026, and
one of the four hunks exists because they were not.** Found while
writing the patch file: `Race_Selection_Screen_` wrote the ID once,
on entry, and nothing ever cleared it — its cancel path returned 0
untouched and `newgame.cpp:113` just reloads New Game, so the API
reported SCREEN_RACE while New Game was on screen for as long as the
player stayed there. Hunk 2 closes it with the same save-and-restore
the Custom Race pair uses. **Confirmed live the same day**: from the
main menu into New Game, into race selection (id 6), ESC — the next
snapshot reports 13.

The Accept paths are untouched on purpose. Every accept from race
selection passes through `Racial_Option_Screen_` (racesel.cpp:308),
whose own accept sets `MOX::_current_screen = MOX::_return_screen`
(racesel.cpp:692, the ORIGINAL's line) immediately before
`finished = 1` — so the value already names the destination and a
restore of ours would overwrite the game's intent.

If it ever goes upstream, a named constant such as
`EXT_SCREEN_CUSTOM_RACE` would be cleaner than a literal.

---

## Withdrawn proposals

Kept so they do not come back as requests.

**A ship-icon owner byte in STATE_SNAPSHOT.** Drafted while building
the HD fleet icons. `MOX::_ship_node[]` turned out to be a pure
function of `_ship[]`, which the snapshot already carries:
`Find_Ship_Stacks_` allocates nodes strictly sequentially in both
branches of its loop, so node N is the N-th ship with `status < 3`.
The draft survives as `doc/ext_ship_icon_owner.patch`, marked
OPTIONAL. Do not add it to this list.

**The engine version in `HELLO_REPLY`.** Drafted while putting
"Version 1.60.0" on the HD main menu, which the reply cannot supply:
it carries `PROTO_VERSION`, the wire protocol's number, and the
snapshot has no version field. Appending the string to the reply
would be four lines and backwards compatible — and still not worth a
permanent change to somebody else's tree for one line of cosmetic
text. OrionLayer keeps the number in `core/config.ORION2RE_VERSION`
and `tools/version_check.py` compares it against `src/version.h` and
`src/game/consts.h`, so drift fails a command instead of going
unnoticed. Bring it back only if a client ever has to behave
differently per engine version.

**A command to move `_cur_map_x` / `_cur_map_y`.** Drafted while
building the pointer-anchored HD zoom, which appeared to need a way
to move the visible slice from outside. It does not: the snapshot
already carries every star's galaxy coordinate, so a client can
render any slice at any scale without the game's view participating.
Reasoning in `doc/ext_api_dokumentation_v3.md` under "What the
snapshot deliberately omits".

The lesson both share, and the reason they are written down: read the
function that BUILDS a structure before concluding it has to be
transmitted.

---

## 6. `s_0_0055110c` / `s_1_00551110` — a question, not a fix request

**This asks for an answer, not a patch.** Nothing misbehaves today
and OrionLayer is not blocked. It is here because the answer decides
whether a transcription we have just shipped is right, and because
the declaration disagreement is the kind that stays harmless until
somebody changes one of the three copies.

### What we found (orion2re 1.60, `src/version.h`)

The two format prefixes that `COLSUM::Draw_Empire_Info_` passes into
every sidebar line exist **three times, in three namespaces, at two
declared sizes, in two spellings**:

| Where | Declared | Defined | Spelling |
|---|---|---|---|
| `colsum.h:87-88` / `colsum.cpp:36-37` | `const char[3]` | COLSUM | `"\0320"` / `"\0321"` |
| `estrings.h:9-10` / `estrings.cpp:8-9` | `const char[4]` | ESTRINGS | `"\0320"` / `"\0321"` |
| `strings.h:39-40` / `strings.cpp:22,24` | `const char[3]` | strings | `"\x1A" "0"` / `"\x1A" "1"` |

All three produce the same bytes — `1A 30` and `1A 31` — so the
**value is not in doubt** and nothing is broken at runtime.

### The question

**Which byte does the original binary emit here — 0x1A or 0x1B?**

It matters because the two are different FMTPARA commands:
`0x1A` is `Set_Justification_` and `0x1B` is `Set_Current_Colors_`
(`fmtpara.cpp:364-368`). On 0x1A the sidebar is six rows of
label-left / value-right; on 0x1B it is six plain left-aligned lines
with a label colour and a value colour. We have implemented the
first, because `strings.cpp` writes the hex escape deliberately and
comments it *"switches paragraph justification to left alignment"* —
three independent spellings agreeing is as far as we can get from
outside the binary.

What would settle it from your side is the byte at the original's
own data addresses, which the Ghidra-derived names still carry:
`0x0055110c` and `0x00551110`.

### The smaller half: `[3]` vs `[4]`

`estrings.h` declares both as `const char[4]` while `colsum.h` and
`strings.h` declare them `const char[3]`, and the definitions follow
their own headers. Two of the three are `extern` declarations of
symbols defined elsewhere, so this is an ODR-adjacent disagreement
that a linker will not necessarily complain about. Worth a look even
if the answer to the question above is "0x1A, as written".

### Why this is not a fix request

Because we cannot tell you what the right answer is, only that three
places disagree about the type and two about the spelling. If the
bytes are correct as written, the only change worth making is
picking one home for the pair — and that is your call about your
tree, not ours.

---

## 7. `Draw_Colony_Prod_Both_` sign-tests `imports[t]` twice, two different widths — a question, not a fix request

**This asks for an answer, not a patch.** Nothing misbehaves today
and OrionLayer is not blocked. It is here for the same reason item 6
is: the answer decides which of two readings is the transcription,
and it is the kind of disagreement that stays invisible until a value
crosses a boundary nobody was watching.

### What we found (orion2re 1.60, `src/version.h`)

`COLDRAW::Draw_Colony_Prod_Both_` (`coldraw.cpp:36`) tests the sign of
the same field, `colony->imports[prod_type]`, in two places, and casts
in only one of them:

| Where | Test | Decides |
|---|---|---|
| `coldraw.cpp:73` | `if ((int8_t)colony->imports[prod_type] < 0)` | which of four branches computes the NET that is drawn |
| `coldraw.cpp:152` | `if (colony->imports[prod_type] < 0 \|\| prod_type == ECON_INDUSTRY)` | whether the row draws `Import_Anims_` plus a shortage, or `Prod_Anims_` |

`imports` is `int16_t[4]` at offset 243. `(int8_t)` takes the **low
byte**, so the two tests disagree for every value whose low byte and
whole differ in sign — 256 is positive as a word and 0 as a byte, 384
is positive as a word and -128 as a byte, and -256 is negative as a
word and 0 as a byte.

### The question

**Does the original binary sign-test the byte or the word here?**

If the byte: the cast at `:73` is the transcription and `:152` has
lost one, or the original genuinely differs between the two and this
is faithful. If the word: the cast at `:73` is an artefact of the
decompilation — a `movsx`/`cmp al` read as a narrowing cast — and
`Draw_Colony_Prod_Both_` computes the wrong net for large imports.

What would settle it from your side is the comparison width at the
original's own address for this function.

### WHICH ROWS THE ANSWER CAN CHANGE — not the industry one

Worth stating, because it decides how much this matters and it turns
the question from a curiosity into a narrow one.

**On the INDUSTRY row the answer changes nothing.** The cast picks
between the two branches at `coldraw.cpp:74-78` and `:88-92`, and
those are the same three lines: both are guarded by
`prod_type == ECON_INDUSTRY` and both compute
`max(0, production - maintenance[prod_type])`. So on that row the
byte and the word reach one expression by two routes, and no
savegame can tell them apart.

**On FOOD, RESEARCH and BC it changes the number.** There the cast
picks between `production - abs(imports[t])` and `production`, which
differ by the whole import amount.

### The example, and it is 18 BC away from our reference save

`imports[ECON_BC]` is `(uint8)maintenance[ECON_BC] - production[ECON_BC]`
(`colcalc.cpp:1265`) and is **not clamped**, so it can leave the range
where the byte and the word agree. Which direction it can leave in is
the whole of how much this matters, and we got it wrong twice before
checking, so here is the arithmetic.

The two tests agree except where the low byte's sign differs from the
word's. For a NEGATIVE `imports[ECON_BC]` that window opens at
**-129**, not at -256: `(int8_t)(-128)` is -128 and still negative,
`(int8_t)(-129)` is **+127** and is not.

    imports   -1   -111   -128   -129   -130   -255   -256   -257
    (int8_t)  -1   -111   -128   +127   +126     +1      0     -1
    branch     B      B      B      C      C      C      C      B

**So one BC of production flips the drawn number by the whole import
amount.** With `maintenance[ECON_BC]` 17, which is a value our
reference save actually holds:

    production 145 -> imports -128 -> byte NEGATIVE     -> B
                   -> production - abs(imports) = 17
    production 146 -> imports -129 -> byte +127         -> C
                   -> production = 146

The row goes from 17 to 146 because production went up by one. The
uncast reading draws 17 in both cases, which is the colony's BC after
its own upkeep and is the number the row is evidently for.

**This is close, not theoretical.** Across all 55 colony records of
our reference save at stardate 3502: `production[ECON_BC]` runs
0..128, `maintenance[ECON_BC]` runs 0..20, and `imports[ECON_BC]`
runs -111..7. The most negative is **-111** against a boundary of
-129 — eighteen away. The colony holding it has maintenance 17 and
production 128; at production 146 it crosses.

**The POSITIVE direction looks out of reach, and saying so is itself
half an answer.** A positive `imports[ECON_BC]` of 128 or more needs
`maintenance[ECON_BC]` of at least 128, since production cannot be
negative. That field is a `uint8` written by a truncating cast
(`colcalc.cpp:1261`) and the largest value in those 55 records is
**20**. We first proposed 200 as the example and withdrew it for that
reason: for a positive disagreement the field would have to hold a
value we cannot make it hold.

For completeness on the other two rows: `imports[ECON_FOOD]` is
written at `colcalc_main.cpp:222`, `:229`, `:335` and `:1408` and
runs -28..15 in that save, and `imports[ECON_RESEARCH]` is **never
assigned anywhere in the engine** — grepping every write to
`imports[` finds ECON_FOOD, ECON_INDUSTRY and ECON_BC and no fourth —
so the research row is on `production` unless a savegame carries a
value into it.

### Why we are asking rather than picking

We have transcribed it **as written**, cast and all
(`screens/colony_summary/colonyrows.drawn_production`, with
`_low_byte_signed` as a named function so it cannot be quietly tidied
away, and a smoke check that fails if it is). That is the only
defensible choice from outside the binary: normalising it to a plain
comparison would be correcting the source on a guess, and the guess
would be invisible, because **at every import value MOO2 realistically
produces the two tests agree**. That is exactly why nobody has ever
noticed it, and exactly why it is worth an answer rather than a
shrug.

### Not a fix request

Because we cannot tell you which is right. If the byte is correct,
`:152` is the one missing a cast; if the word is correct, `:73` has
one too many. Either way it is one line in your tree and the choice
is yours.

---

## 8. Two native messages that disagree, one of them unreachable — a question, not a fix request

**This asks for an answer, not a patch.** Nothing misbehaves and
OrionLayer is not blocked. It is here for the same reason as items 6
and 7: we are about to mirror this rule so a refusal can be shown
before a click is sent, and the two strings the original carries say
different things about what natives may do.

### What we found (orion2re 1.60, `src/version.h`)

Natives are refused twice, in two functions, with two different
messages:

| Where | Test | String |
|---|---|---|
| `Get_Cluster_`, `colmove.cpp:59-64` | `pop[i] & 0x0F == 9` | ESTR **382** — *"Natives cannot be moved to another job or planet!"* |
| `Give_Colonist_New_Job_`, `colmove.cpp:524-529` | `pop_state == 3 \|\| pop_state == 6` and the new job is `ECON_RESEARCH` or `ECON_INDUSTRY` | ESTR **522** — *"This colonist is a native, natives can only farm or mine."* |

Three things do not line up.

**The two strings contradict each other.** 382 says natives cannot be
moved to another job at all. 522 says they can, to two of the three
jobs.

**522's code does not match its own text.** It refuses
`ECON_RESEARCH` and `ECON_INDUSTRY`, which leaves only `ECON_FOOD` —
farming. The string offers farming *or mining*, and mining is the
industry job it refuses.

**And 522 looks unreachable.** `Give_Colonist_New_Job_` has exactly
two callers (`colmove.cpp:168` and `:262`), both inside
`Send_Cluster_`, which needs a cluster. `_cluster_colony_n` is
assigned a colony in exactly one place — `colmove.cpp:66`, inside
`Get_Cluster_`, after the check at `:59` has already returned for a
native. So a native can never be in a cluster, and a rule that only
fires on a native in a cluster can never fire.

### The question

**Which of the two describes the intended rule?** If 382 does, then
522 and its branch are dead weight and the "or mine" text has never
been true. If 522 does, then `Get_Cluster_`'s blanket refusal is too
strong and natives were meant to be movable between farming and
industry — in which case the refusal at pick-up is the bug, not the
message.

There is a third possibility we cannot rule out from outside: that
`pop_state == 6` was reachable in the original and is not here.
`Pop_To_Pop_State_` (`colony.cpp:1240`) returns only 2, 3 or 4 and is
defined once, so a state 6 would have to come from somewhere this
tree no longer has.

### The same shape, a second site — an OBSERVATION, 6 September 2026

Not a fix request and not part of the question above; it is here
because it is the same pattern and a reader who meets one should
meet the other.

`COLONY::People_Anim_` (`colony_main.cpp:444-450`) branches on
`pop_state` four ways: **0** and **2** pick a race sprite,
`race * 13 + job * 2 (+ 1 for state 2)`; 3 gives the native (0xAA)
and 4 the android (0xA9).

**The `pop_state == 0` arm looks unreachable, exactly as `== 6` does
above, and for the same reason.** `Pop_To_Pop_State_`
(`colony.cpp:1240-1255`) returns only 2, 3 or 4, and it is the only
thing that feeds `Colony_Pop_Anim_` (`colony.cpp:1270-1283`). The
other eight call sites in the tree pass a literal 2 or 4
(`colbldg.cpp:923`, `:933`, `:943`, `colony_main.cpp:930`,
`colony.cpp:2238`, `mainpups.cpp:2658`). Nothing passes 0.

The consequence is visible in the file: **the EVEN entry of every
job pair is never drawn.** RACEICON.LBX holds both — 13 races x 13
entries + 0xA9 + 0xAA is exactly its 171 — and only the odd one of
each pair reaches the screen. Confirmed against the original's own
framebuffer on 6 September 2026: Elerian entries 40, 42 and 44 match
14, 4 and 8 figures on the colony summary index for index, entries
39, 41 and 43 match none.

So the same third possibility applies: a state 0 may have been
reachable in the original and not here, in which case those thirteen
even entries per race are what it drew. **No change is wanted** — we
transcribe the code, and `tools/raceicon_extract.py` writes the even
entries out as `_state0` so the reference shows what is being
skipped rather than hiding it.

### What we did with it

**We mirrored the code, not either string**, because the code is what
runs — including the `== 6` arm, which costs one `or` to transcribe
and saves us being right about an unreachable branch. Our own refusal
wording is ours and lives in `layout.json` (decision 15): we refuse
*before* injecting, so the sentence a player reads is a thing this
project chose and has to own, and copying an ESTRING that may be
describing a rule the code does not implement would be the worst of
both.

If the answer is "382 is the rule", nothing changes for us. If it is
"522 is the rule", our mirror is currently stricter than the game
intends and we would want to know.

### VERIFIED LIVE, 5 September 2026 — both halves, at the game's own window size

The patch had been applied and reasoned about but never exercised:
the binary that was running when it was written was the pre-fix one.
It has now been run twice, against the rebuilt binary, on the
reference save.

**What was run.** `tools/colony_move_probe.py --commit` injects the
two clicks a population move needs at computed native points, and
`tools/colony_move_hd.py --commit` does the same thing through the
whole HD path — a real `MOUSEBUTTONDOWN` posted into pygame's queue,
routed by the app to the colony summary screen, which then plans and
sends. Both predict the resulting `pop[]` words BEFORE clicking and
diff the whole colony array afterwards.

**What it showed.** The pick-up took exactly the predicted cluster —
which is the pointer half, because `COLSUM::Get_Selected_Pop_`
resolves the icon from a value written out of `mouse::Pointer_X_()`
and the physical cursor was nowhere near the column. The drop landed
exactly the predicted pop words in exactly one colony, at the window
size the game happened to have, which is the coordinate half. Under
the pre-fix binary the same sequence picked up nothing at all, twice.

**One correction to this item's own text, while it is being
verified.** The reading above says `Get_Selected_Pop_` "walks the
icons against `mouse::Pointer_X_()`". It walks them against the
SCROLL FIELD's value: `Get_Selected_Pop_` (colsum.cpp:1006) passes
mode 3, whose test is `*scroll_value_ptr` (coldraw.cpp:361), and
`fields::Find_Bar_Position_` (fields.cpp:1702-1743) writes that value
from `mouse::Pointer_X_() + _pointer_offset` when the field is pushed
down. Mode 4 is the one that reads the pointer directly
(coldraw.cpp:367) and is not what this screen uses. The diagnosis and
the fix are unaffected — the pointer is still what decides the icon —
but the chain is one link longer than written, and the extra link
carries two things worth knowing: the value persists between clicks,
and `_pointer_offset` (the mouse picture's frame, mouse.cpp:115) is
added to it.

**A second finding from the same run, which is not a fix request.**
Every refusal in `COLMOVE::Give_Colonist_New_Job_` (colmove.cpp:526,
:534, :541, :555) and the native refusal in `Get_Cluster_`
(colmove.cpp:60) call `GENDRAW::Help_`, which is
`TEXTBOX::Do_Text_Box_` — a blocking box, `do { … } while
(fields::Get_Input_() == 0)` (textbox.cpp:149). A client that injects
a move the game refuses therefore parks the engine in a modal, while
the API keeps talking because `ext::Tick()` runs from `Get_Input_()`.
OrionLayer's answer is to mirror the rules and refuse before sending
(fundament decision 33 and 47); it is recorded here because it is a
property of the injection boundary rather than of our screen, and any
other client will meet it.

---

## 9. `Do_Colony_Info_Pop_Stuff_For_Pop_`'s `race_idx` loop iterates the CONQUERED bit — a question, not a fix request

**This asks for an answer, not a patch.** Nothing misbehaves. It is
here for the same reason items 6 and 7 are: a name and a mask
disagree, the name is the one a later reader will believe, and this
particular loop decides which pop is drawn differently from its
neighbours.

### What we found (orion2re 1.60, `src/version.h`)

`COLDRAW::Do_Colony_Info_Pop_Stuff_For_Pop_` (coldraw.cpp:282) picks
the icons of one column with five nested loops. The second level is

    for (int16_t race_idx = 0; race_idx < 2; race_idx++)        :327
        ...
        if (((pop_val & 0x400) >> 10) == race_idx)              :337

`0x400` is `POP::MASK_CONQUERED` (pop.h:12). The RACE lives in the
low nibble, `POP::MASK_RACE = 0x0F` (pop.h:8), and that one is
iterated by a DIFFERENT loop in the same nest — the `pop_order`
level at :329-330, which walks (9, 0, 1 … 8) from the table at
:287-297.

So as far as we can read it, the identifier is a misnomer for
something like `conquered_idx`, and the nest groups: state, then
conquered, then job, then race, then array order.

### Why it is worth an answer rather than a rename

The bit it iterates is not cosmetic. `COLONY::Colony_Pop_Anim_`
(colony.cpp:1268) draws a conquered pop from a completely different
sprite class — `Colony_Pop_Icon_(race)`, a static race portrait at
RACEICON entry `race * 13 + 12` — while every other pop gets an
animated figure from `People_Anim_` (colony_main.cpp:444). So this
loop is what makes the drawn column read "working figures first, then
portraits", and a client that mirrors the walk has to know whether
that grouping is the intent or an artefact.

### The question

1. Is `race_idx` at coldraw.cpp:327 a decompilation misnomer for the
   conquered flag, or was something else meant there?
2. If it is a misnomer: is there any objection to it being named for
   what it tests? We are not asking for the change — this is your
   tree — only whether the reading is right, so that our own
   transcription can be named correctly and cite this answer.

### What it costs us today

Nothing that moves. OrionLayer transcribes the walk in
`screens/colony_summary/colonyicons.py` and names the level
`conquered`, with a comment saying the source calls it `race_idx`.
The full reading is in `doc/pop_order_reading.md`, which is ours and
not part of this list.

---

## 10. Bump `ENGINE_VERSION` when a serialized record layout changes

### Symptom

Between the tree we build against (`cf4d9617`, `GAME_BUILD_DATE`
"May 31 2026") and the current main (`GAME_BUILD_DATE` "Aug 15
2026"), `s_ship_data` grew from 0x81 to 0x87 and `s_antaran` from
0x42 to 0x44, and `s_player` became size-configurable (0xf0e or
0x2d86 depending on `MAX_FREIGHTED_SETTLERS`). Both
`ENGINE_VERSION[]` and `GAME_VERSION_LABEL[]` still read "1.60.0" in
both trees.

### Why it costs us

The Extension API's snapshot is a sequential concatenation of raw
records, so a client walks it with the sizes it was built against. A
size change with an unchanged version string is therefore not a
compile error and not a protocol error — it is a client that reads
every record after the changed one at the wrong offset and draws
plausible nonsense. Our own `tools/version_check.py` compares exactly
those two literals against a hand-copied constant and would have
reported this update as no change.

### The request

Move `ENGINE_VERSION_PATCH` (or whichever component you consider
right) whenever a struct that `sizes.h` asserts a size for changes
that size. It is a one-line change per layout change and it is the
only signal a client outside the build can act on.

### What we are doing on our side regardless

Not waiting for this. `HELLO_REPLY` will carry the record sizes or a
hash of them, additive in `src/ext/`, and the client will refuse to
parse on a mismatch. The request stands because that only protects
clients that use our Extension API, and the version literal protects
everyone.

---

## 11. `Colony_Has_Natives_` tests the android nibble

### Symptom

    bool __cdecl Colony_Has_Natives_(int16_t colony_idx) {
        ...
        if ((MOX::_colony[colony_idx].pop[i] & 0x0F) == 8) {
                                                     ^^^
            return true;

`colony.cpp:1391`. The function returns true for a colony holding
ANDROIDS and false for one holding NATIVES. Its name says natives.

### Why we are sure which nibble is which

Not from reading the same tree three times. **Three independent
sources, 5 September 2026**, against a savegame made for it —
in-game name "2Natives", stardate 3502.5, sha256
`b1f1aa466716d6c0c6b28c84fe270f430c732ec7cb3172d221be44b68708e2c8`.
It is the player's own file and is not ours to ship; the sha256 is
here so anyone reproducing this can say whether they have the same
one.

1. **The data.** Colony "Urna I" holds four pops: one with low
   nibble 0 (the player, Elerian) and three with low nibble 9. All
   four carry profession 0.
2. **The picture.** On the colony summary, that row's FARMERS column
   draws four sprites from the same snapshot: one thin Elerian
   farmer with a staff, and three stocky figures that are a
   different creature rather than a recolour. Same three-to-one
   split, same column.
3. **The game's own words.** Hovering those three on the colony
   screen makes it print **"Native farmers"**.

Nibble 9 is the native marker. `pop.h:15` says so
(`RACE_NATIVE = 9u`), `Pop_To_Pop_State_` (colony.cpp:1240) agrees,
and so does `Pop_Race_String_` (colony.cpp:948). Only
`Colony_Has_Natives_` uses 8.

### What it costs the engine

One caller, `Do_Informational_And_Decision_Popups_` (colony.cpp:996):

    if (colony->occupation_policy == 4) {
        population_count = Sum_Colonists_(handle, -1, -1, -1, -1, 1);
        if (population_count < 1) {
            if (!Colony_Has_Natives_(handle)) goto check_production;
        }
        OCPOLPUP::Occupation_Policy_Popup_();

`Sum_Colonists_` with `conquered_flag = 1` counts the assigned pops
carrying the conquered bit (colony.cpp:2137-2140), so
`population_count < 1` means "no conquered population here". The
gate then asks whether there is a native population to decide about
instead — and asks the wrong nibble. So:

- a colony with natives and no conquered pops **never offers the
  occupation-policy popup**;
- a colony with androids and no conquered pops **does** offer it, for
  a population that has nothing to decide.

`occupation_policy` is what `Apply_Colony_Pop_Growth_`
(colcalc.cpp:2106-2139) reads to decide whether to assimilate or
remove a native or conquered pop each turn, and `OCPOLPUP` is the
only place a player choice writes it (`ocpolpup.cpp:40`). Everything
else that writes it writes 4, which is also the initial value
(`initgame.cpp:458`). Consistent with that, Urna I in the save above
sits at `occupation_policy == 4` with three natives and no conquered
pops.

**What we have NOT established:** whether a player can reach policy 0
for such a colony by another route, and therefore whether this is a
lost choice or only a popup that never appears. That is a question
about intended behaviour and it is yours.

### The fix

One character, if the reading is right: `== 8` becomes `== 9` at
colony.cpp:1396. We have not applied it — it is a behaviour change in
your code with a gameplay consequence, not a compatibility shim, and
it is not ours to decide. If you would rather the function keep its
current test, the name is the thing that should move instead.

### What it costs us

Nothing. OrionLayer never calls it and does not mirror it. This is
reported because we had the save, the picture and the label in one
place, and a bug that can be shown three ways should not stay
unreported.


---

## 12. A pop move has no command, only a click choreography

**Request.** Patched locally as `doc/ext_move_pop.patch` and verified
live on 10 September 2026; open upstream. The brief is
`doc/briefs/90-pop-move-one-command-instead-of-a-click-chain.md`
and the decision is fundament entry 52.

### What we need

One message that moves pops by INDEX: a colony, and a list of
(pop index, job). `MSG_SET_JOBS` (0x84) in our own `src/ext/`, plus
the one thing it needs from your code — see below.

### Why the click path is not enough

`COLMOVE::Give_Colonist_New_Job_` (colmove.cpp:518-557) already
takes exactly the arguments a command would: colony, pop, job. It
reads no screen state and no `_cluster_colony_n`. But it can only
be *reached* by a click, and a click names a SLOT in the game's own
ten-row list window — so a client that wants to move a pop must
first push a sort key, then step `_first` until the target row is
inside that window, then click twice. Measured over ten drops:
597 ms of a 725 ms move is that apparatus, and none of it is
arithmetic anybody wants to do. With a command the same five-pop
move measures **55 ms and one snapshot round**, and costs the same
whether the row is the first or the last.

### What the patch needs from YOUR code, and it is four lines

Everything else is in `src/ext/`, which is ours. The one thing that
is yours: **all four refusals in `Give_Colonist_New_Job_` answer
with `GENDRAW::Help_`** (colmove.cpp:527, :534, :541, :556), which
is `TEXTBOX::Do_Text_Box_` -> `Text_Box_Get_Input_(0)`, whose
zero-ticks path spins waiting for a human
(`do { … } while (fields::Get_Input_() == 0)`, textbox.cpp:145-149).

Called from the Extension API's drain loop that stops the engine —
and worse, the inner `Get_Input_()` calls `ext::Tick`
(fields.cpp:167), so a refusal recurses into the command queue it
was called from. The patch adds `COLMOVE::_ext_suppress_refusal_help`
and routes the four calls through one `Refusal_Help_` wrapper. The
refusal still happens and still returns 0; only the box is skipped,
and only while the flag is set. Every line is inside
`#ifdef ORION2RE_EXT` or is a rename to an unconditional wrapper, so
a build without the flag is your code unchanged — verified by
compiling `colmove.cpp` both ways.

### What we would rather have

A refusal-free inner form of `Give_Colonist_New_Job_` — the checks
returning a reason code, with the message box moved to the caller
that has a human in front of it. Then the flag is unnecessary and
the split is yours rather than ours. We did not write that, because
it changes the shape of your function and that is your call.

### What it costs us

Today, nothing: the patch is applied locally and
`tools/version_check.py` fails on a tree without it, so an
unpatched engine is caught by a check rather than by a move that
silently does nothing. Upstream it decides whether OrionLayer has
to carry a patch for the one gesture that drives the game.

---

## 13. The Planets screen's restriction toggles are not in the snapshot

**A request.** Nothing in the game misbehaves; OrionLayer's Planets
screen cannot know the state it is supposed to mirror.

### What we found (orion2re 1.60)

`PLNTSUM::Filter_Explored_Planets_` (plntsum.cpp:976-1053) filters the
list on five globals — `_filter_out_enemy_controlled_planets`,
`_filter_out_adverse_gravity_planets`,
`_filter_out_hostile_environment_planets`,
`_filter_out_mineral_scarcity_planets` and
`_filter_out_planets_out_of_range` — set by five radio fields with
hotkeys 1-5 (`Add_Plntsum_Fields_`, plntsum.cpp:697-701). They are not
reset when the screen opens and they are not in STATE_SNAPSHOT
(ext_api.cpp:53-136), so a client that shows the list has no way to
read them. A radio click TOGGLES, so unlike the sort key
(`_sort_choice`, which a client can impose by clicking the key it
wants) a flag cannot be set by sending input without knowing its value
first.

### Seen live

13 September 2026, the reference save in slot 8: the game's range
toggle was already on when the HD Planets screen opened, and the HD
list (all toggles off) and the game's list disagreed — 140 rows
against 41 — until the toggle was flipped from outside the screen.

### The request

Carry the five flags in the snapshot — five bytes, or one bitmask in
the order of the fields above — while the Planets screen is up, or
always. Anything that lets a client read them before it sends a click.

### Why not read the picture

The radio sprites are in the framebuffer, and reading them would work
until a skin, a palette or a sprite changed. Data's decision after
brief 101 Stop 3: a documented gap until the flags are on the wire, and
no frame reading.

---

## 14. The GAME popup's save slot list is not on the wire — a request, with a patch

### What we found (orion2re 1.60, 14 September 2026)

`LOADSAVE::Set_Up_Load_Save_Popup_` (loadsave.cpp:136-171) and
`Check_For_Saved_Games_` (:599-640) read SAVE1.GAM … SAVE10.GAM into
`MOX::_save_game_description[10]`, `MOX::_save_game_dates`,
`MOX::_save_game_stardates` and `_game_popup_fields->slot_status` /
`saved_game_types`. None of it is serialized, so a client drawing the
Load or Save dialog knows neither the names nor which slots are empty.

### Why not read the files

A client could open the ten headers itself. It would need the game's
working directory, which is not on the wire either, and the day the
two folders differ the names on screen stop belonging to the slots a
click reaches — with every name still plausible. OrionLayer's decision
60 refuses that.

### The request

`MSG_SAVE_SLOTS` (0x14), sent right after a FIELD_LIST while the game
is on SCREEN_GAME with `_screen_data` 2 or 3: the engine's own status,
game type and three strings per slot. `doc/ext_save_slots.patch`, two
files, both in `src/ext/`; compiled -fsyntax-only against the build's
flags, **not built into a binary and not applied** — reported first,
by Data's order.

### What it costs us today

The HD rows show "Slot N", the warning after a refused slot cannot say
why, and the save name field starts empty.

### Re-checked 16 September 2026 (work order 124 A) — still needed, still not applied

- **Where the names come from: the file headers, into an in-memory table,
  every time the dialog opens.** `Set_Up_Load_Save_Popup_` (loadsave.cpp:136)
  calls `FILEDEF::Get_Saved_Game_Descriptions_` (filedef.cpp:207-243), which
  opens SAVE1.GAM … SAVE10.GAM and reads `int32 type`, `char[37]
  description` and `int32 save time` into `MOX::_save_game_description[10]`.
  An absent or invalid file gets HESTRNGS 0x184 ("empty slot" wording,
  :234 and :239), slot 10 the literal "(Auto Save)" (:228), an empty
  description "<< no description >>" (:230); a description still empty
  with a stardate present gets HESTRNGS 203 (loadsave.cpp:162-165). The
  dialog draws the table (`_Draw_Load_Save_Game_Popup_`, :856-884), and the
  Save dialog's row edit starts from the same string
  (`strlcpy(fields::_continuous_string, …)`, :517).
- **No path reaches a client today.** The snapshot serializes
  `MOX::_settings` (ext_api.cpp:117) — which carries `active_save_slot` and
  nothing about names — and not the description table, the stardates, the
  dates or the slot status. Reading SAVEn.GAM ourselves stays refused
  (fundament 60). The one other carrier is the framebuffer, where the game
  still renders its own dialog under HD: a glyph read with FONTS.LBX is
  possible in principle, but a name is free text with embedded colour codes
  (`Embed_Special_Color_Codes_`, :251) and glyphs that print alike, the Save
  dialog needs the exact bytes to pre-fill, and nothing on the wire could
  validate the read (decision 25). Not a reconstruction, a guess.
- **The patch still applies** to the current tree, which now carries open
  fixes 20 and 21 as well: `git apply --check` passes on both files
  (offsets 60 and 114 lines), nothing written.

### APPLIED — 16 September 2026, confirmed live

Data applied `doc/ext_save_slots.patch` to `~/orion2re` and rebuilt
(preset linux-debug). Live, with SAVE4 loaded and the GAME menu's Load
dialog open: `MSG_SAVE_SLOTS` arrived with `screen_data` 2 and the ten
descriptions exactly as the native dialog prints them ("Darlok's colony
destroyed" … "... empty slot ..." … "(Auto Save)"), the HD rows drew them
with their stardates and dates, and in the Save dialog (`screen_data` 3) a
click on a valid row started the name edit with that row's name, sending
nothing. The main menu's own Load dialog gets no block — the patch sends on
SCREEN_GAME only, and that dialog has no HD version. `tools/version_check.py`
now requires the patch.

## 15. A scroll field's value can only come from the pointer — a question

`Add_Game_Popup_Fields_` adds the GAME menu's two volume sliders as
scroll fields (loadsave.cpp:200-201). Their value is written by
`fields::Find_Bar_Position_` (fields.cpp:1702) from `mouse::Pointer_X_()`,
and `Set_Music_For_Game_Popup_` / `Set_Sound_For_Game_Popup_` only read
it. `ACTIVATE_FIELD` reaches the handler with the old value; an
injected click loses its pointer to `Sync_Mouse_State_From_SDL_`
whenever the window has focus. **Would a `SET_FIELD_VALUE(field, value)`
command be acceptable** — the scroll field's `value` pointer written,
then the field activated? Until there is an answer, OrionLayer leaves
the sliders out.

**ANSWERED WITHOUT A COMMAND — 16 September 2026, work order 124 C.** The
premise was stale: open fix 3's second half (`doc/ext_inject_click.patch`,
applied and verified 5 September) already suppresses
`Sync_Mouse_State_From_SDL_` while injected input is unconsumed, so an
injected click on the bar keeps its pointer through `Find_Bar_Position_`.
Measured live: with the GAME menu up, `INJECT_CLICK` at native (321, 247)
set `_settings.sound_fx_level` 50 -> 74 and (284, 247) set it back to 50,
exactly what `(x - 206) * 156 / 155` and `* 100 / 155` predict. HD builds
the bars on that (`screens/game_menu/gmsliders.py`); no request remains
here, and the dependency on open fix 3 is named in that module.

## 16. Save dates print the year as years since 1900 — an observation

`MISC::Get_Time_Stamp_` hands over `time_info->tm_year` unchanged
(misc.cpp:699), and `LOADSAVE::Get_File_Date_String_` prints it with
`%-4d` (loadsave.cpp:1772). A save from 2026 reads "Sep 13, 126".
Seen in the native Load and Save dialogs, 14 September 2026.

## 17. The Load dialog's first visit has no month names — an observation

`_Game_Popup_` runs `Set_Up_Load_Save_Popup_` (loadsave.cpp:1573),
which builds the date strings through `Get_Save_Game_Date_Strings_`
(:153) from `LOADSAVE::_months`, before `Do_Load_Game_Popup_` fills
`_months` with `Load_Month_Names_` (:304). So the first Load of a
session prints "31, 126 13:52" and every later one "Jul 31, 126 13:52".
`Do_Save_Game_Popup_` calls `Load_Month_Names_` at :479, also after.

## 18. Two different Alt-key label sets in the Settings dialog — an observation

`_Draw_Options_Game_Popup_` prints the hotkey hints twice, once per
path. The screen path (loadsave.cpp:1503-1523) puts `(ALT-F1)` …
`(ALT-F3)` on rows 0-2 and `(ALT-F4)` … `(ALT-F8)` on rows 4-8. The
bitmap path, drawn during the slide animation (:1473-1492), spells
them `ALT_F`, has no F4, and puts F5 … F8 on rows 5-8. Which set
matches `MAINSCR::Check_Function_Keys_` (mainscr.cpp:3055,
`Toggle_Game_Option_(-1101 - key)`) was not checked.

## 19. A save name confirmed with Enter keeps the edit cursor — an observation

Measured 14 September 2026: slot 10 saved through the Save dialog's
Enter path with the name "HD Save Test Slot Ten" holds
"HD Save Test Slot Ten_" in SAVE10.GAM, and the native list already
showed a hand-saved "ddddd_". `Copy_Continuous_String_` strips one
trailing `_` (fields.cpp, the `_continuous_string[len - 1] == '_'`
test), so that is not where it stays. The leading explanation, **not
measured**: the Enter branch calls the auto function after the copy
(fields.cpp:1043-1050, `Quick_Call_Auto_Function_`), the redraw puts the
cursor back into `_continuous_string`, and `Do_Save_Game_Popup_` copies
that string into the description (loadsave.cpp:552-553).

## 20. The fleet box's ship selection is not on the wire — a request, with a patch

### Applied (15 September 2026, briefs 118 and 119) — revision 2

Applied to the working tree and built `-DORION2RE_EXT=ON`;
`tools/version_check.py` requires it (marker `fsel_chain_len`).
**Revision 1 was applied first and taken back out the same day**: it sent
one selected byte per node and said node n is the n-th ship with status
below 3. Live (brief 118) HD sent `MSG_SELECT_SHIP` for ship 13, which it
took for node 9; the engine flipped node 11 and the original's THIRD cell.
`SHIPSTAK::Sort_Ships_In_Stack_` (shipstak.cpp:261-278) qsorts each
stack's ships by type and writes `ship_idx` back along the chain — the
node places stay, the ships move — and qsort is not stable, so no client
can rebuild the table.

**Revision 2**, what went into the tree: after "FSEL" and the stack, per
node int16 `ship_idx` and uint8 `selected`, then the fleet box stack's
chain (int16 length, one int16 node per link from `_ship_stack_start`
along `next_node`, the order FLEETPOP builds its cells in,
fleetpop.cpp:643-676); the stack is -1 also for an out-of-range index.
The first visible row of a scrolled box is not sent. Confirmed live on
SAVE5 (brief 119): the Yoth chain 9 -> 10 -> 11 carries ships 14, 15, 13;
a click on HD's first cell flipped exactly node 9 and the original's first
cell; on the mixed selection HD's cells, the node bytes and the
framebuffer agreed. OrionLayer reads the node table from here and nowhere
else (owners, icon anchors, the fleet box).

The sections below are the request as it was reported.

### What we found (orion2re 1.60, 15 September 2026, live)

Brief 116, on a scratch save (SAVE5) with one client attached. The fleet
box of an own three-ship stack was opened from the HD map, ALL was sent
by field id, then ALL again. The framebuffer's ship cells went from
30.3 % blue (selected) to 0 % and back, measured by machine per cell.
Across twelve STATE_SNAPSHOTs in each state, **all 69 112 payload bytes
stayed constant** — not one byte followed the selection — and the
FIELD_LIST did not change. `MOX::_ship_node[].selected` and
`_fleet_icon_selection_status` are not serialized; the Stop 1 reading of
brief 110 is confirmed.

An `INJECT_CLICK` at the centre of one ship field (checked to be that
field's alone in the live list) did **not** toggle the ship: the cell
stayed 30.3 % blue. The toggle is painted in the draw pass from the
pointer under a held button (`mainscr_main.cpp:983-995`,
`MAINSCR::Set_Painted_Fleet_Fields_`, mainscr.cpp:2468), and the id
`Get_Input_` returns for a ship field is not acted on
(mainscr.cpp:3422-3436) — so `ACTIVATE_FIELD` cannot toggle either. Open
fix 3's pointer sync is the likely reason the injected click misses, and
it was not separated from the draw-pass reason.

### Why not read the picture

The selection IS visible in the framebuffer, and this run read it. It is
still the route open fix 14 and OrionLayer's decision 60 refuse as a
data source: a picture says what was drawn, not what a move order will
take, and the day the two differ every cell on the HD screen stays
plausible.

### The request

Two optional trailing blocks at the end of `ext::SerializeState()`: the
ship icon owners of `doc/ext_ship_icon_owner.patch` (carried, because
OrionLayer reads exactly one byte per icon there as owners), then
`"FSEL"`, the fleet box's stack (-1 while closed), the node count, and one
byte per node — `_ship_node[i].selected`, the flag
`HACCESS::Get_Fleet_Box_Selected_Ship_Ids_` builds a move order from.
`doc/ext_fleet_selection.patch`, one file in `src/ext/`; compiled
-fsyntax-only against the build's flags, **not built and not applied**.

Reading the selection gives HD a correct blue/black cell per ship. It
does not give HD a way to CHANGE one ship's selection; that would be a
second request (a command, like open fix 12's), and is not made here.

### What it costs us today

The HD fleet box shows no selection, and a fleet order from HD can only
move what the game auto-selected or what ALL selects.

## 21. One ship in the fleet box cannot be (de)selected from outside — a request, with a patch

### Applied (15 September 2026, briefs 118 and 119)

Applied unchanged (it lands 60 lines lower on top of open fix 20
revision 2), built `-DORION2RE_EXT=ON`; `tools/version_check.py` requires
it (marker `Select_Ship_`). Confirmed live on SAVE5: one HD cell click
sent one `MSG_SELECT_SHIP` and the next block showed exactly that ship's
node changed. A star click with the fleet box open is a move order in the
original — confirmed by hand by Data (brief 119), so fundament 65's
premise is measured, not only read.

The sections below are the request as it was reported.

### What we found (orion2re 1.60, 15 September 2026, live)

The write half of open fix 20, from the same run (brief 116): an
`INJECT_CLICK` on a single ship field does not toggle the ship, and an
`ACTIVATE_FIELD` on it is not acted on (mainscr.cpp:3422-3436). The
original paints the selection in the draw pass from the pointer under a
held button (`mainscr_main.cpp:983-995`, `Set_Painted_Fleet_Fields_`,
mainscr.cpp:2468). ALL (`mainscr.cpp:3411-3419`) is the only selection
control a client reaches, and it selects or clears the whole stack.

### The request

`MSG_SELECT_SHIP` (0x85), client -> server: int16 ship_idx, uint8
selected. The handler is the checker, modelled on open fix 12: every
precondition before any write — the fleet box open, its stack existing,
the ship the player's, `MAINSCR::Ship_Can_Be_Selected_` (so a ship in
transit needs the communications tech, `SHIPMOVE::Can_Order_Ship_`), and
the ship found in that stack's node chain. Then it writes
`_ship_node[node].selected` and the `_fleet_icon_selection_status` bit
`Save_Ship_Selection_Status_` keeps, exactly what a painted cell writes.
A refused command writes nothing and draws nothing.
`doc/ext_fleet_select_ship.patch`, three files in `src/ext/`; generated
hunks; dry-run in both orders together with open fix 20 (the two give the
same file); compiled -fsyntax-only with the build's flags alone and
together with 20. **Not built, not applied.** `tools/version_check.py`
reports both markers (`FSEL`, `Select_Ship_`) without failing while they
are only reported; applied, they move into its LOCAL_PATCHES.

### What OrionLayer does with it (built 15 September 2026, brief 117)

Only while the snapshot carries open fix 20's FSEL block: the HD fleet box
colours each ship cell blue or black from that block, a click on a cell
sends `MSG_SELECT_SHIP` with the opposite state, and what the engine did
is read back off the next block, never assumed. With the block, a star
click moves exactly the ships shown blue (fundament 65, amended). Without
it nothing changes from today.

### What it costs us today

Nothing more than open fix 20 already costs: no selection shown, no subset
of a stack moved from HD.

## 22. Select Race borrows SCREEN_RACE, which the Races screen owns — APPLIED 17 September 2026

**APPLIED by work order 128 B** (Data decided the synthetic id). Seen live
first on SAVE4 (3509.0): RACES on the HD map made the game report 6 and draw
Race Relations while HD drew Select Race
(`~/orionlayer-fixtures/evidence/work_order_128/B_before/`). Race selection
now reports **51** (`EXT_SCREEN_RACE_SELECTION`, orion2re 3305d78c,
`doc/ext_screen_id.patch` revision 2), checked against the SCREEN enum's last
value 43, which `tools/version_check.py` now reads and compares with
`core/screen_names.ENGINE_SCREEN_MAX`. Live after: New Game -> race selection
(51) -> Custom Race (50) -> Empire Identity -> galaxy map, and the stock-race
path, both end to end; RACES then falls back to the original framebuffer
(decision 22). **The stock-race accept (below) was NOT changed:** it still
leaves the id set — now 51 — through the name and banner dialogs until galaxy
generation (39), and HD's Empire Identity holds its lock on exactly that, so
the "leak" is load-bearing; it no longer reads as the Races screen. What
follows is the description as filed by work order 126 G.

### As described (126 G)

Filed 17 September 2026 by work order 126 G from `doc/races_screen_reading.md`
(§4 settles the id question, §5 carries this draft). **Not a request to Joes
yet:** the fault is in OUR patch, and the choice between this change and an
HD-side distinction is Data's (parked in `doc/briefs/126-parked-for-data.md`).

**What we found (orion2re 1.60.0).** `SCREEN_RACE` (6) is the Races/diplomacy
screen: `Screen_Control_` runs `RACESCRN::Race_Screen_` for it (mox2.cpp:61-63)
and the galaxy map's RACES button sets it (mainscr_main.cpp:666).
`doc/ext_screen_id.patch` hunk 1 makes `Race_Selection_Screen_` report the same
6 (racesel.cpp:222, inside `#ifdef ORION2RE_EXT`). OrionLayer's `select_race`
claims `GAME_SCREEN_ID = 6` (screens/select_race/screen.py:30) and the
dispatcher routes on the id alone, so HD Select Race would be drawn over the
Races screen and its clicks would land there (source reading, not seen live).
The stock-race Accept returns at racesel.cpp:451 without restoring the caller's
id; only Custom Race's accept sets `_return_screen` (racesel.cpp:704).

**The change, described.** Inside `#ifdef ORION2RE_EXT` in racesel.cpp:
(1) hunk 1 reports a synthetic 51 instead of `SCREEN_RACE` (outside 0-43, as
Custom Race's 50 is); (2) before `return 1` at :451, restore the saved id when
the current one is still 51. Hunks 2-4 unchanged.

**What it carries.** Nothing new on the wire: STATE's existing `current_screen`.

**Why no existing path gives it by id.** The snapshot's screen is
`MOX::_current_screen` as handed to `ext::Tick`; nothing else names the running
function. `previous_screen` (0 on the Races screen, 10/8/15 during race
selection) and the field-list shape separate the two by inference only
(decision 25 allows that route; see the reading §4).

**What it would cost OrionLayer.** `select_race` 6 -> 51, the `lock_ids` of
`empire_identity` and `custom_race` (and the observed 50 -> 6 hop in Custom
Race must be re-measured), `core/screen_names.py`, and Select Race's own
comparison against 6.

## 23. Activating a research choice row by field id crashes the game — an observation

Seen live 17 September 2026 (work order 128 C), by accident: at the
turn-start "SELECT NEW RESEARCH" prompt (reported as screen 0, 38 fields) an
`ACTIVATE_FIELD 1` — a choice row — killed orion2re with SIGSEGV in
`TECH::_Tech_Select_`, from `REPORT::Set_Initial_Tech_` <- `Display_Report_Aux_`
<- `Main_Screen_Report_Handler_` (backtrace in
`~/orionlayer-fixtures/evidence/work_order_128/C_orion2re_segfault_backtrace.txt`).
The source reading had predicted it (`doc/tech_change_reading.md`): any
positive input below the category buttons commits `Get_Selected_Entry_`, the
entry under the POINTER, not the activated field (tech.cpp:354-369), and with
the pointer over no entry the result is dereferenced (tech.cpp:367). Not a
request: nothing in OrionLayer activates those rows, and the galaxy map's
parking no longer can. A future HD research screen needs either a commit by
field id or the pointer set first — that is the research screen's order.

**Closed locally, 18 September 2026 — item 25, work order 130 B.** The
research screen's order arrived, and it chose the commit by field id.
`doc/ext_tech_activate.patch` does two things to this item. It makes an
activation select the row it names, so the pointer is no longer what decides
— which removes the cause. And it returns to the input loop when no entry is
selected instead of dereferencing the null, which removes the crash itself,
for the mouse path as well as for a client. Both are inside
`#ifdef ORION2RE_EXT`, so this remains an OBSERVATION for Joes rather than a
request: upstream still dereferences, and the way to reach it from outside
the extension build is the narrow one this item describes.

The observation is kept rather than deleted because the fix is ours and
local. A tree without `doc/ext_tech_activate.patch` crashes exactly as
described above, and `tools/version_check.py` is what notices.

## 24. The two turn-start research dialogs report SCREEN_MAIN — a request, with a patch (APPLIED locally)

Applied 17 September 2026 by work order 129 B; the reading is
`doc/newtech_reading.md`, the patch `doc/ext_research_screens.patch`.

**What we found (orion2re 1.60.0).** When a project completes,
`TECH::Tech_Select_` runs `SCIENCE::Show_Off_Researched_Tech_` ->
`SCIENCE::Science_Room_` (science.cpp:112-392) and then
`TECH::_Tech_Select_(0)` (tech.cpp:103-106). `REPORT::Reports_Screen_` has
set `MOX::_current_screen = SCREEN_MAIN` (mainscr2.cpp:119) and neither
dialog writes it, so both are reported as screen 0. Seen live: OrionLayer
kept the galaxy map up, with its TURN button, while the player answered in
the game's own window — and an activation into the select list killed the
engine (item 23).

**Why not the path item 22 takes.** That one writes `MOX::_current_screen`.
Here the game DRAWS from it: the description box's x is 84 on the main
screen and 130 otherwise (textbox.cpp:40-50), and its colour group is a
switch on the same variable (textbox.cpp:284). Reporting through it would
move the dialog it makes visible.

**The change.** `ext::g_screen_override`, read by `ext::Tick` when it
serializes, and `ext::ScreenOverride`, which sets it for a scope and
restores it on every exit. 52 in the science room, 53 in the select list's
select mode, no override in change mode (which is SCREEN_TECH_CHANGE, 36).
Nothing the game reads is touched.

**What it costs us.** Nothing: no HD screen claims 52 or 53, so decision 22
takes over and OrionLayer shows the original picture until a research screen
is built.

---

## 25. The research selection commits the entry under the POINTER, not the activated field — a request, with a patch (APPLIED locally)

Applied 18 September 2026 by work order 130 B, Data's decision. The reading
is `doc/tech_change_reading.md` §2 and §5.1; the live measurement is work
order 129 B; the patch is `doc/ext_tech_activate.patch`.

**What we found (orion2re 1.60.0).** `TECH::_Tech_Select_`'s input loop
treats any positive input below the category radio buttons — every choice
row and every entry block — as a commit. It then ignores the field id it was
handed: `Get_Selected_Entry_` (tech.cpp:508-520) returns whichever of the
eight entries carries `current_app_index != 0`, and only
`Set_Selected_Entry_` sets that. `Set_Selected_Entry_` is called from
`Draw_Tech_Select_` (tech.cpp:458-476), which reads `fields::Scan_Input_()`
— the game pointer — on every idle frame, and clears all eight entries when
the pointer is over nothing selectable.

An `ACTIVATE_FIELD` moves no pointer. Work order 129 B activated three rows
on three occasions and got: the row the cursor happened to rest on, no
commit at all, and a different row. The third outcome, with the pointer over
nothing, is item 23's SIGSEGV.

**What it costs us.** Without this, an HD research screen cannot choose a
research at all. Decision 20 ("Field IDs for input.") reserves INJECT_CLICK
for radio buttons and free map clicks, and an injected click into this list
depends on the pointer surviving the frame (open fix 3's pointer half, and
its own caveat) — so the one path HD is meant to use is the one that does
not work here.

**The change.** `ext::g_activated_input` carries the field id of the input
`Get_Input_` is returning this call when it came from an activation, and 0
when it came from the mouse; it is cleared at the top of every call. The
commit branch, for an activation only, selects that field before asking
which entry is selected. An entry BLOCK field resolves to that entry's last
visible row, the same resolution `Draw_Tech_Select_` performs for the
pointer. And a null selection continues the input loop instead of being
dereferenced.

**Why the mouse path is unchanged.** `g_activated_input` is 0 for every
mouse input, so the inserted selection never runs for one — and it would be
a no-op if it did, because for a real click `Draw_Tech_Select_` has already
selected that same field from the pointer on the previous idle frame. The
only behaviour a mouse can reach that this changes is the crash.

**Why not the other two options.** `doc/tech_change_reading.md` §5.1 lists
three. (a) a new `ext_api` command writing `current_research_field` directly
leaves the game's own input loop open, and select mode has no exit but a
commit. (b) placing the game pointer at the activated field's centre in the
`Get_Input_` early return would fix every pointer-reading handler in the
game at once — and change behaviour on every screen, which is far more than
this needs. (c), this patch, is confined to the one handler with the defect.

**Why it is a request and not only a local fix.** Upstream, a client of the
Extension API cannot drive this screen, and the failure mode is a crash
rather than a refusal. The shape of the fix is ours to choose only because
`src/ext/` is ours; the fault is in `tech.cpp`.

---

## 26. SELECT NEW RESEARCH commits a row by itself after the science room — an observation

Seen three times and measured once during work order 130's live
acceptance, 18 September 2026, on a new Psilon game against orion2re
**e9d07528** (`orionlayer-local`, open fixes 24 and 25 applied).

**What happens.** The science room (wire id 52) is walked out with
clicks forwarded through OrionLayer's fallback view; each advances one
discovery and the last hands over to `_Tech_Select_(0)`, wire id 53.
The list comes up correctly — 36 or 38 fields, `current_research_field`
0, exactly as `Tech_Select_` leaves it (tech.cpp:104-105). Roughly a
second and a half later the list commits a field and the game returns
to the galaxy map, **with no input sent into it**.

**The measurement** (`evidence/work_order_130/A_step/record.json`). The
client's three send paths were wrapped by a counter that still calls
the real method, so a send cannot happen unseen. After the hand-over:

| frames | screen | `current_research_field` | sends from the client |
|---|---|---|---|
| 25 | 53 | 0 | 0 |
| 50 | 53 | 0 | 0 |
| 75 | 0 | **20** | **0** |

**The last column is ONE reading, not three — noted 23 September 2026,
work order 165 part H.** `tools/livedrive.SendCounter` handed out the
live counts dict rather than a copy, so the three `sends` entries in
`watch` are four serialisations of one object (with
`driver_sends_after`), taken when the file was written.

**The conclusion is untouched, and the reason is arithmetic.** That one
number is the TOTAL for the counted period and it is zero; a counter
only increases, so every moment inside the period was zero too. The
aliasing can make a later number too HIGH — it cannot invent a zero.
What is not in the evidence is the per-frame resolution the table's
shape implies. `evidence/work_order_130/A_step/NOTE-165H-send-counter.md`
has it in full.

Three occasions in the same run: fields 3, 21 and 20, each of them the
first offered entry's field.

**What was ruled out.** `_last_button_number`, which the ext early
return in `Get_Input_` sets, is written in three places and **read in
none** (`grep -rn _last_button_number src/`), so a stale value from the
room's whole-screen field is not the path. `ext::g_pending_field` is
cleared when it is consumed, so one activation cannot be delivered
twice. And the count above shows the client sent nothing.

**What was NOT established.** The mechanism. It is recorded as an
observation rather than a request because nobody has read the path that
produces it, and a fix request without one would be a guess.

**What it costs us.** A client cannot assume it will be asked. Three of
six attempts to choose a research from HD lost the occasion to this,
and the work-around that made a choice reliable was to walk the room
and click the row **in the same process**, without letting go between
them — which is a timing dependency, not a design.

### Data's counter-test, 19 September 2026 — and what it rules out

Data ran the same binary (**e9d07528**, open fix 25 applied) with **no
client connected at all**, clicking the completion dialog away with the
**real mouse**. The select list WAITS. It does not choose by itself.

**So open fix 25 is not the cause.** That was the first thing to
suspect — it is the only change this project made to that handler, and
it changes what the commit branch selects. The counter-test removes it:
with the patch in and the two other conditions absent, the behaviour
does not appear.

**What is still suspect, and neither is settled:**

1. **The completion dialog dismissed by INJECTED clicks.** Every
   occasion on 18 September walked the science room out with
   `ACTIVATE_FIELD` forwarded through OrionLayer's fallback view.
   Data's run used the real mouse for exactly that step.
2. **A connected client, as such.** `ext::Tick` runs inside
   `Get_Input_` whenever a client is attached, and the early return for
   a pending field sits in the same function. Data's run had no client
   attached at all, so this is not separated from (1) yet.

Separating them is one run each: the room clicked away with the real
mouse WITH a client attached, and the room clicked away by injection
with the client detached immediately afterwards. Neither has been done.

**Status: OPEN, and deferred by Data on 19 September 2026.** It is not
being chased now; it is written down here, in the status document and
in `screens/research_select/`'s own docstring, and a smoke check holds
that marking in place for as long as this entry says OPEN.

It is also the reason the first build's screen validates on every entry
and hands back to the fallback rather than drawing: a list that can
commit without being asked is a list whose state HD must re-read, never
remember.

**The player's way round it, while this is open:** click the completion
dialog away in the orion2re window with the real mouse. The research
selection then waits, and the HD screen can be used for the choice.

---

## 27. The fleet screen's view state is not in the snapshot

**Applied locally 19 September 2026** (work order 134 C), orion2re
`cc5ec133` on `orionlayer-local`, `doc/ext_fleet_screen_state.patch`.
Required by `tools/version_check.py`. **NOT CONFIRMED LIVE.**

### Symptom

An HD client on `SCREEN_FLEET` (4) knows the screen is up and knows the
field list, and nothing else. It cannot say which stack is shown, which
ships are in the big-icon grid, which of them are selected, where the
list is scrolled, or which of the two filters are on.

### Why reconstruction does not reach it

Followed to the end first, which is what decision 25 of the OrionLayer
fundament requires, and closed by three separate facts:

1. FSEL (item 20 revision 2) sends the whole `_ship_node` table but the
   only CHAIN it sends is the fleet box's, and that is `-1` here because
   the fleet screen closes box 2 (`flt1.cpp:826-832`).
   `_ship_stack_start[]` and `next_node` are not on the wire.
2. Walking the node table names ships the player cannot see:
   `SHIPSTAK::Remove_Non_Detected_Ships_` (shipstak.cpp:200-250) unlinks
   nodes of foreign stacks and `Delete_Ship_Node_` (:5-11) leaves their
   `ship_idx` in place.
3. Grouping own ships by `s_ship.location` gives a different list in
   both membership and order — the two filters (flt2.cpp:130-146) and
   `Ok_To_Add_Ship_` decide membership, the officer move-to-front
   decides order (flt2.cpp:263-265) — and has no way to say so.

What a client CAN see is how many big-icon FIELDS the screen added, at
known grid rects. That says how many and where, never which.

### Fix

An optional trailing block `"FLTS"` in `ext::SerializeState`, written
only while `MOX::_current_screen == SCREEN_FLEET` and LAST in the
snapshot, after FSEL — so nothing above it moves and an older client is
unaffected. Fourteen scalars, then N × (`int16 ship_idx`, `uint8
selected`) in the screen's own DISPLAY order. One file,
`src/ext/ext_api.cpp`. Full layout in the patch header.

### Cost to us

Without it the HD fleet screen draws nothing and says so
(`screens/fleets/fltwire.py`, state `NO_BLOCK`).

---

## 28. One ship cannot be selected on the fleet screen

**Applied locally 19 September 2026** (work order 134 C), orion2re
`e6199966` on `orionlayer-local`,
`doc/ext_fleet_screen_select.patch`. Required by
`tools/version_check.py`. **NOT CONFIRMED LIVE.** The write half of 27.

### Symptom

On `SCREEN_FLEET` a single ship's selection cannot be changed from
outside by any route. Only ALL, which selects or clears the whole list.

### Root cause — three shut doors, three different reasons

- **A click.** The per-ship toggle is painted in the DRAW pass, which
  tests `mouse::Mouse_Button_()` for the LIVE button state
  (`flt1.cpp:413-436`). An injected click is a buffered event and the
  button has gone up by the time the draw pass looks. This is item 20's
  finding on the fleet box, at a second site.
- **`ACTIVATE_FIELD` on a big icon.** It reaches
  `Scan_Fltscrn_Big_Icons_` result 0, which only SCANS the ship — the
  stats panel follows, the selection does not (flt2.cpp:924-928,
  flt1.cpp:615-620).
- **`MSG_SELECT_SHIP`, i.e. item 21.** It refuses unless
  `MOVEBOX::Moveable_Box_Selected_(2)`, and this screen closes box 2;
  and it writes `_ship_node[].selected`, which this screen never reads —
  it paints from `_fltscrn_big_icon[].selected` (flt1.cpp:429). Two
  independent reasons, so widening one would not have been enough.

### Fix

`MSG_SELECT_SHIP` (0x85) branches on the screen: `SCREEN_FLEET` goes to
a new `Select_Fltscrn_Ship_`, everything else keeps item 21's handler
unchanged. One message id because it is one question, two handlers
because the two screens keep the answer in different arrays. The checks
are the original's own, in its order (screen, own stack, relocate mode
≠ 1, ship in the list) and the write is the single line ALL writes
(`Set_Fltscrn_Big_Icons_`, flt1.cpp:1610-1624). Nothing else is
maintained: the loop's `Update_Selection_Flags_` (:811, :1069-1093)
recounts `_n_big_icons_selected` and mirrors
`_fltscrn_icon_selection_status[]` on the next iteration, exactly as it
does after ALL.

### Cost to us

Without it a subset of a stack cannot be moved or scrapped from HD.

---

## 29. A native message box's text is not in the snapshot

**Asked for by work order 152. OPEN.**

### Symptom

An HD screen cannot say what the game is asking it. When the engine
opens one of its own boxes — `GENDRAW::Confirmation_Box_`,
`Message_Box_Exploding_`, anything through `HAROLD::User_Box_` — the
question reaches a client only as PIXELS in the framebuffer. Measured
live on 20 September 2026: SCRAP on the fleet screen left exactly two
fields on the wire, the box's YES and NO, and no text anywhere.

### Why reconstruction does not reach it

The string is `HAROLD::H_Message_(n)` run through `snprintf` with values
the engine has just computed. For the scrap confirmation that value is
`FLT1::Get_Scrap_Ship_Value_()` (flt1.cpp:962-971), a sum of
`maintain::Ship_Scrap_Value_` over the selected ships — a cost model a
client does not have. Extracting HESTRNGS gives the FORMAT and not the
number, so a client can print "…will yield ? bcs", which is the one
fact the answer turns on.

### Fix

Either the formatted string itself, or the two or three values the
formats take. The narrow version, and the one work order 152 would use
today: **`Get_Scrap_Ship_Value_()` as an int16 in the FLTS block**,
beside the fields open fix 27 already added. The general version is a
`MSGB` block written whenever `_fields` has been re-based by
`FIELDSAV::Save_Field_Stats_` — the box's id and its finished text.

### Cost to us

Until then HD shows the game's own rendering of the box: the
rectangle is transcribed (`core/gamebox.py`), the crop comes out of
the framebuffer HD already subscribes to, and it is blitted at an
integer magnification into an HD panel. It works and it is answerable,
and it is the one place in an HD screen where the original's 640x480
type appears. That is the marked limitation this fix replaces.

---

## 30. The Leaders screen's view state is not in the snapshot

**Asked for by work order 167, 24 September 2026. APPLIED 26 September
2026** by work order 175 on Data's authorisation — orion2re
`orionlayer-local` `cc542e02`, `doc/ext_officer_screen_state.patch`;
`tools/version_check.py` requires its marker. Open upstream. Before the
apply it was shown to apply to `src/ext/ext_api.cpp` at `e6199966` and
to compile with the engine's own flags (with a control that is refused).

### Symptom

An HD client on `SCREEN_OFFICERS` (29) has the field list and all 67
leader records, and cannot say which button mode is on (hire, pool,
dismiss), which leader is selected, which star the colony view shows or
has chosen for an assignment, which stack the ship view shows, which
ships are in its grid or which one is picked, where the grid is
scrolled, or which leader the hire popup offers.

### Why reconstruction does not reach it

Followed to the end first (decision 25):

1. The VIEW and HIRE MODE are readable, and HD reads them without this
   fix: the ship view adds the scroll arrows `-` / `+` at (613, 22) and
   (613, 170) and the colony view does not (officer.cpp:2942-2963); hire
   mode replaces HIRE `H` with CANCEL `X` (:2857-2881).
2. The LISTED LEADERS are `Build_Captain_Id_List_` (:2705-2730), a pure
   function of the records — rebuilt by HD, and checked against the
   block when it is there.
3. POOL and DISMISS mode are not: both buttons are the same hidden
   fields in modes -1, 1 and 2 (:2831-2855); only the drawn frame
   differs. The selection, the displayed and the chosen star, the stack
   and the popup's leader leave no trace in the list at all; the ship
   grid reaches it as identical rectangles (:2959).

A click on a leader in pool or dismiss mode ACTS (:1415-1438), so a
client that guessed the mode would send an order nobody gave
(decision 65).

### Fix

An optional trailing block `"OFFS"` in `ext::SerializeState`, written
only while `current_screen == SCREEN_OFFICERS` and LAST, after FSEL — it
can never meet FLTS, which is written only on `SCREEN_FLEET`. Four
int8, sixteen int16 (the four listed leaders among them), an int16
count, then
N × (`int16 ship_idx`, `uint8 selected`) in display order — the array
and the order FLTS already sends. The popup's leader and state are
written only while `MAINPUPS::_on_officer_screen_flag` is set, which
`OFFICER::Hire_Officer_Popup_` holds for exactly the popup's lifetime
(officer.cpp:3391-3400). Full layout in the patch header. One file.

### Cost to us

Without it the HD Leaders screen draws every leader in both views, the
buttons, the galaxy box and the hire popup it can identify, and sends
only what it can confirm on the wire afterwards: the two view tabs,
HIRE and CANCEL, RETURN, and a click on a leader who is for hire. POOL,
DISMISS, assigning a leader, PREV / NEXT, the colony view's star display
and the ship view's grid are drawn as a placeholder that names this
item (`screens/leaders/ldrwire.py`, HD STATE).

## 31. A session-launched engine hangs in its first logo frames

**Asked for by work order 174 A, 26 September 2026. APPLIED the same
day** by work order 175 on Data's authorisation — orion2re
`orionlayer-local` `f98b8547`, `doc/ext_present_no_vsync.patch`;
`tools/version_check.py` requires its marker. Open upstream. Before the
apply a scratch copy of `e6199966` built with it RAN (numbers below).

### Symptom

Started from a session (139 E, 169 P1, 170 P1, and 26 September), the
engine stops after `mox2: data space allocated` and never reaches
`ext: server started`; Data's own start works. `ps` shows the main
thread in `drm_syncobj_array_wait_timeout`.

### Where it waits — evidence

Backtraces of hung starts (`~/orionlayer-fixtures/evidence/work_order_174/
hang_backtrace_*.txt`): the main thread in `SDL_RenderPresent` → the
NVIDIA GLX swap → `drmSyncobjTimelineWait`; the game thread in
`JIM::Draw_Logos_` → `palstore::Slow_Fade_In_` / `video::Toggle_Pages_`
→ `video::Submit_Palette_` / `video::Publish_Off_Page_`, in
`SDL_WaitCondition` with no timeout, waiting for that present. VSync is
switched on at platform.cpp:644 and :1390.

### When — the trigger

A present to a window the compositor is not drawing can wait forever.
On 26 September a full-screen game covered the whole monitor, and 8 of
60 counted starts of Data's build hung; one start made before the game
was launched ran cleanly. On 25 September (169) the hang began nine and
a half minutes after the last input, with GNOME's screen blanked and
locked after 300 s idle — circumstantial, not measured. Disabling NVIDIA's
explicit sync (`__NV_DISABLE_EXPLICIT_SYNC=1`) moved the wait to
`xcb_wait_for_special_event`; the Vulkan renderer to
`VULKAN_AcquireNextSwapchainImage`; the software renderer still hung
(SDL accelerates its window surface through GL). Only not waiting for
VSync removed it.

### Fix

An environment variable, `ORION2RE_EXT`-gated: `ORION2RE_NO_VSYNC=1`
passes 0 to both `SDL_SetRenderVSync` calls. The default is unchanged.
Measured in the scratch build: with it, 48 of 50 starts ready and none
in the hang (the other two were not caught hanging; 30 further starts
with a backtrace armed were all ready); without it, 1 of 20 hung.
A timeout on the game thread's wait would be the deeper fix; it was not
attempted.

### Cost to us

Without it an unattended live run hangs in about one start in eight
while the engine's window is covered or the screen is locked.
`tools/engine_start.py` sets the variable (ignored by an engine
without the patch), recognises the hang by its signature and starts
again, stopping only the PID it started.

