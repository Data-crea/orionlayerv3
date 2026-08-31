# orion2re — open fixes for Joe

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
| 3 | INJECT_CLICK coordinates mapped as window coordinates | Open | INJECT_CLICK only reliable at a 640x480 window |
| 4 | INJECT_CLICK pushes no MOUSEMOTION before the buttons | Open | Radio buttons toggle unreliably |
| 5 | `racesel.lbx [entry 138]` crash on Custom Race Accept | **Applied** in the 30 Aug tree — that is why it stopped reproducing | Nothing |
| — | Custom Race reports screen ID 50 | **Applied** | — |

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

Either bypass the mapping for injected events, or document the
command as taking window coordinates and let clients convert.

### Cost to us

Every free map click and the New Game toggles are affected, because
those are the places where no field ID exists and INJECT_CLICK is the
only option. OrionLayer prefers ACTIVATE_FIELD wherever a field ID
exists precisely to avoid this.

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
