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
| 3 | INJECT_CLICK: coordinates mapped as window coordinates, AND the real mouse overwrites the injected pointer every frame | **Both halves patched locally** 4 Sep 2026 (`doc/ext_inject_click.patch`); open upstream | Without them an injected click lands on the wrong pixel on any window that is not 640x480, and the pointer walks off it before a handler that reads `Pointer_X_()` looks |
| 4 | INJECT_CLICK pushes no MOUSEMOTION before the buttons | Open | Radio buttons toggle unreliably |
| 5 | `racesel.lbx [entry 138]` crash on Custom Race Accept | **Applied** in the 30 Aug tree — that is why it stopped reproducing | Nothing |
| — | Custom Race reports screen ID 50 | **Applied** | — |
| 6 | `s_0_0055110c` / `s_1_00551110` declared `[3]` and `[4]`, defined three times | **Question, not a fix** | Nothing today |
| 7 | `Draw_Colony_Prod_Both_` sign-tests `imports[t]` as a byte once and as a word once | **Question, not a fix** | Nothing today; changes the FOOD/RESEARCH/BC rows, never INDUSTRY |
| 8 | Two native messages in `colmove.cpp` disagree, and the one describing a capability is on an unreachable branch | **Question, not a fix** | Nothing today; decides which refusal HD shows |

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

## Applied: Custom Race reports screen ID 50

Not a request; recorded so it is not proposed again.
`Racial_Option_Screen_()` is a sub-screen of SCREEN_RACE and the game
never changes `MOX::_current_screen` on entry, so the API kept
reporting 6 and no client could tell the two apart. The patch sets 50
behind `#ifdef ORION2RE_EXT` and restores on cancel; the accept path
was already correct. Documented in
`doc/ext_api_dokumentation_v3.md` under "racesel.cpp — 3 insertions",
and confirmed live: OrionLayer's Custom Race screen declares
`GAME_SCREEN_ID = 50` and switches to it.

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
