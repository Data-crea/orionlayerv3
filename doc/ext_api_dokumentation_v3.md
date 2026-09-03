# orion2re Extension API — Patch Documentation

This document describes all changes to the orion2re source code
required for the Extension API. Target audience: Joes and anyone
reviewing or integrating the patch.

Rewritten: 28 August 2026, extended 29 and 30 August. Field dumps re-verified
against the running game and against mainscr.cpp; one label in the
Galaxy Map dump was wrong and has been corrected (see the note there).

**30 August, later:** "Known limitations of the current server" reduced to a
pointer at `doc/orion2re_open_fixes.md`, after this copy had drifted
from it a second time — it still described two fixes as open that the
fixes file had marked applied. The risk table was corrected the same
way. This document describes the patch; the fixes file alone says
what is still being asked for.

**29 August:** added "What the snapshot deliberately omits", which
records that `MOX::_ship_node[]` does NOT need to be serialized. That
question came up while building the HD fleet icons and briefly
produced a patch proposal; it is withdrawn.

**30 August:** a second withdrawn proposal recorded in the same
section — **no map-scrolling command is needed**. Building a
pointer-anchored zoom for the HD galaxy map looked like it required
a way to move `MOX::_cur_map_x/_cur_map_y` from outside. It does not.

**30 August, later:** a third — **no engine version on the wire**.
`HELLO_REPLY` reports the protocol version, not the engine's, and the
main menu's "Version 1.60.0" would need a patch to travel. OrionLayer
maintains the string itself and checks it against orion2re's source
instead. Same section.

---

## Summary

The Extension API allows external programs to read game state from
orion2re over TCP and inject input. It is implemented as an optional
build feature activated via a CMake flag.

| Metric | Value |
|---|---|
| New files | 4 (all under `src/ext/`, 792 lines) |
| Changed files | 5 (`mox2.cpp`, `fields.cpp`, `platform.cpp`, `racesel.cpp`, `CMakeLists.txt`) |
| Inserted lines total | 45 (in existing files) |
| Deleted / changed lines | 0 |
| Default state | OFF (`-DORION2RE_EXT=OFF`) |
| Impact without flag | None (zero line difference in the binary) |

---

## New files

All four live in `src/ext/` and are only compiled when
`ORION2RE_EXT=ON`.

| File | Lines | Contents |
|---|---|---|
| `ext_api.h` | 27 | Public interface. Depends only on `<cstdint>` |
| `ext_api.cpp` | 335 | Init/Tick/Shutdown, serialization, input processing |
| `ext_server.h` | 109 | Server class + wire protocol constants |
| `ext_server.cpp` | 321 | TCP server (POSIX / Winsock) |

### Public interface

```cpp
namespace ext {
    bool Init(uint16_t port = 17362);   // Start server
    void Tick(int16_t current_screen);  // Send state, read input
    void Shutdown();                    // Stop server
    extern bool g_hide_window;          // Suppress the SDL window
    extern int16_t g_pending_field;     // Pending field activation
}
```

`g_pending_field` bridges external input injection and the field
system. It is set by `ProcessInput()` and consumed by the early exit
in `Get_Input_()`. It deliberately does not reuse
`_last_button_number`, so external and local input cannot interfere
(see "the g_pending_field mechanism" below).

### What Tick() does

1. `AcceptClients()` — non-blocking accept on port 17362.
2. `ReadInput()` — non-blocking read of queued client commands.
3. `ProcessInput()` — applies them (see the input section).
4. Returns immediately if no client is connected — no serialization
   cost in a normal game.
5. Serializes game state from existing globals, **read-only**.
6. Sends to every client whose subscription flags match.

State is copied out of `MOX::`, `fields::`, `platform::` and
`video::` globals. Nothing is written back. The one exception is
`MOX::_current_screen` in `racesel.cpp`, which is documented below
and only ever set to a value the game itself would report.

---

## Changes to existing files

### mox2.cpp — 3 insertions

**Include** after line 1:

```cpp
#ifdef ORION2RE_EXT
#include "ext/ext_api.h"
#endif
```

**Hook in `Screen_Control_()`**, after `int16_t current_screen = ...`:

```cpp
#ifdef ORION2RE_EXT
            ext::Tick(current_screen);
#endif
```

**Init / Shutdown in `main2_()`**, around `MOX2::Screen_Control_()`:

```cpp
#ifdef ORION2RE_EXT
        ext::Init();
#endif
        MOX2::Screen_Control_();
#ifdef ORION2RE_EXT
        ext::Shutdown();
#endif
```

### fields.cpp — 2 insertions

Include as above, plus the Tick hook and early exit in
`Get_Input_()`, after the `_input_delay` check:

```cpp
#ifdef ORION2RE_EXT
        ext::Tick(MOX::_current_screen);
        if (ext::g_pending_field > 0) {
            int16_t result = ext::g_pending_field;
            ext::g_pending_field = 0;
            _last_button_number = result;
            const s_field& f = _fields[result];
            _last_button_x = (f.x + f.x_end) / 2;
            _last_button_y = (f.y + f.y_end) / 2;
            video::Set_Page_Off_();
            return result;
        }
#endif
```

Two jobs in one block. `ext::Tick()` publishes state continuously —
the `Screen_Control_()` hook only fires on screen changes, while
`Get_Input_()` is the game's actual inner loop. The early exit
consumes `g_pending_field` before `Interpret_Mouse_Input_()` runs.

`_last_button_number` and `_last_button_x/y` are set because calling
screens expect them; `Set_Page_Off_()` mirrors the normal return
path.

### platform.cpp — 2 insertions

Include as above, plus the window guard:

```cpp
#ifdef ORION2RE_EXT
        if (!ext::g_hide_window)
#endif
        SDL_ShowWindow(g_sdl_window);
```

The game keeps running — rendering, logic, input — only the SDL
window is not shown.

### racesel.cpp — 3 insertions

Two screens run their own input loops and never pass through
`Screen_Control_()`, so they need a `_current_screen` assignment or
the API reports a stale ID.

**`Race_Selection_Screen_()`** (line 212), before the input loop:

```cpp
#ifdef ORION2RE_EXT
        MOX::_current_screen = SCREEN_RACE;
#endif
```

**`Racial_Option_Screen_()`** (line 454), before its `while (true)`:

```cpp
#ifdef ORION2RE_EXT
    const int16_t ext_saved_screen = MOX::_current_screen;
    MOX::_current_screen = 50;
#endif
```

and the restore on cancel (line 634):

```cpp
#ifdef ORION2RE_EXT
                MOX::_current_screen = ext_saved_screen;
#endif
```

50 is outside the SCREEN enum range (0–43), so it cannot collide.
Adding a real enum value would mean touching `orion2.h`, which this
patch avoids. On the success path the original code already sets
`MOX::_current_screen = MOX::_return_screen`.

### CMakeLists.txt — 1 block (line 483)

```cmake
option(ORION2RE_EXT "Build with Extension API (TCP server
       for external clients)" OFF)
if(ORION2RE_EXT AND TARGET orion2re)
    target_sources(orion2re PRIVATE
        src/ext/ext_api.cpp
        src/ext/ext_server.cpp)
    target_compile_definitions(orion2re PRIVATE ORION2RE_EXT)
    target_include_directories(orion2re PRIVATE ${CMAKE_SOURCE_DIR}/src)
    if(WIN32)
        target_link_libraries(orion2re PRIVATE ws2_32)
    endif()
endif()
```

```bash
cmake --preset linux-debug -DORION2RE_EXT=ON
cmake --build --preset linux-debug
```

---

## What is not touched

- No headers change (`orion2.h`, `mox.h`, `fields.h`, `platform.h`)
- No game logic changes (calculations, AI, combat, savegames)
- No existing global is written except the documented
  `_current_screen` assignments
- No function signature changes, no modified includes
- Every condition is additive, never alternative

---

## Sub-screen pattern

| Function | Called from | Screen ID | Patched |
|---|---|---|---|
| `Race_Selection_Screen_()` | `Newgame_Screen_()`, `hotpop.cpp`, `netstart.cpp` | 6 (SCREEN_RACE) | Yes |
| `Racial_Option_Screen_()` | `Race_Selection_Screen_()` | 50 (synthetic) | Yes |

**Dialogs are not sub-screens.** `Naming_Popup_` and `Flag_Screen_`
run inside whichever screen called them and report that caller's ID.
Both the stock-race path (racesel.cpp:253/262) and the custom path
(racesel.cpp:662/675) call the *same two functions*, so a client
cannot tell the flows apart by ID — it must detect them by the shape
of the field list. That is deliberate and does not need a patch.

---

## Input injection

### The g_pending_field mechanism

```
ACTIVATE_FIELD(3)
  → ext_server.cpp ReadInput()  : queue InputCommand
  → ext_api.cpp   ProcessInput(): ext::g_pending_field = 3
  → fields.cpp    Get_Input_()  : early exit consumes it, returns 3
```

A separate variable is required. `_last_button_number` is also set
by normal game input, so an early exit keyed on it would re-fire a
user's own click on the next poll.

### Field types and which command to use

| Type | Name | ACTIVATE_FIELD |
|---|---|---|
| 0 | Button | Works |
| 1 | Radio button | **Does not work** — use INJECT_CLICK |
| 7 | Click-through / hidden | Works |
| 8 | Dynamic (ship icon slots) | Coordinates often (-1,-1) |
| 11 | String input | Works |
| 12 | Map area | Large rect — use INJECT_CLICK |
| 13 | Sidebar button | Works |

Radio buttons (type 1) toggle their bound variable inside
`Interpret_Mouse_Input_()`. The early exit skips that code path, so
their state would never change.

### INJECT_CLICK and CANCEL_FIELD

Both push SDL mouse events. **DOWN and UP are both required** —
`Interpret_Mouse_Input_()` waits for the release, and DOWN alone
hangs the game.

### Known bug: INJECT_CLICK coordinates

INJECT_CLICK carries 640x480 game coordinates, but `platform.cpp`
maps the injected SDL event through
`Map_Window_Point_To_Game_Point_()` as *window* coordinates, and
`Sync_Mouse_State_From_SDL_()` overwrites the position every frame.
On a 1828 px window, (510, 326) lands near (178, 114).

Not patched. Clients should prefer ACTIVATE_FIELD wherever a field
ID exists; INJECT_CLICK is only reliable at a 640x480 window size.

---

## Wire protocol

### Frame format

```
┌─────────────────────────────────────┐
│ Frame Header (8 bytes)              │
│   magic      uint32  0x4F325845     │  "O2XE"
│   length     uint32  payload size   │
├─────────────────────────────────────┤
│ Message Header (8 bytes)            │
│   msg_type   uint16                 │
│   flags      uint16                 │
│   sequence   uint32                 │
├─────────────────────────────────────┤
│ Payload (variable)                  │
└─────────────────────────────────────┘
```

### Message types

```
Server → Client:
  0x01  HELLO_REPLY     Version, capabilities
  0x10  STATE_SNAPSHOT  Complete game state
  0x11  FIELD_LIST      Active UI fields
  0x12  VISUAL_FRAME    Framebuffer 640x480 + palette
  0x13  EVENT           Screen change, turn end

Client → Server:
  0x01  HELLO           Version (uint16), subscriptions (uint16)
  0x80  ACTIVATE_FIELD  field_id (int16)
  0x81  INJECT_KEY      keysym (int16)
  0x82  INJECT_CLICK    x, y (int16 x2) in 640x480
  0x83  CANCEL_FIELD    field_id (int16)
```

### Subscriptions (bitmask in HELLO)

```
  0x01  STATE    Game state every tick
  0x02  FIELDS   Field list on change
  0x04  VISUAL   Framebuffer + palette
  0x08  EVENTS   Screen / turn events
```

### State snapshot order

```
Offset  Content                        Type / size
──────────────────────────────────────────────────────────
  0     current_screen                 int16
  2     previous_screen                int8
  3     stardate                       int32
  7     player_num                     int16
  9     num_players                    int16
 11     num_stars                      int16
 13     num_ships                      int16
 15     num_colonies                   int16
 17     num_nebulas                    uint8
 18     game_type                      int8
 19     cur_map_scale                  int16
 21     cur_map_x                      int16
 23     cur_map_y                      int16
 25     MAP_MAX_X                      int16
 27     MAP_MAX_Y                      int16
 29     settings                       sizeof(s_settings)
  ?     players[8]                     sizeof(s_player) x 8
  ?     num_stars + stars[n]           int16 + s_star_data x n
  ?     num_ships + ships[n]           int16 + s_ship_data x n
  ?     num_colonies + colonies[n]     int16 + s_colony x n
  ?     num_planets + planets[n]       int16 + s_planet_data x n
  ?     num_nebulas + nebulas[n]       uint8 + s_nebula x n
  ?     leaders[67]                    sizeof(s_leader_data) x 67
  ?     antarans                       sizeof(s_antaran)
  ?     ship_icon_count + ship_icons   int16 + s_ship_icon x n
  ?     ng_* (8 values)                int16 x 8
```

Not serialized, though OrionLayer needs them: `_max_map_scale` and
`_max_zoom_count`. Both are derivable from `MAP_MAX_X` (the ratio
`MAP_MAX_X / max_map_scale` is 50.6 for every galaxy size), so no
patch is required.

### Field list

13 bytes per field, `count(uint16)` followed by `count x 13`:

```
Offset  Content      Type
──────────────────────────
  0     field_index  int16
  2     x            int16
  4     y            int16
  6     x_end        int16
  8     y_end        int16
 10     field_type   int16
 12     hotkey       uint8
```

### Visual frame

```
      0  framebuffer   307,200 B (640x480x8bit)
 307,200  palette          768 B (256 x RGB)
```

---

## What the snapshot deliberately omits

Globals and values a client might expect are absent, and each is
absent on purpose. Recording the reasoning here so the question does
not come back as a patch request.

### The engine version

Not on the wire at all. `HELLO_REPLY` carries
`{ PROTO_VERSION, 0 }` — that is the *wire protocol* version, not
the engine's — and `STATE_SNAPSHOT` has no version field. orion2re
keeps the number in two separate literals:

```
src/version.h:10      ENGINE_VERSION[] = "1.60.0"
src/game/consts.h:43  GAME_VERSION_LABEL[] = "Version 1.60.0"
```

and prints the second one on the main menu (`mainmenu.cpp:295`,
`Print_Centered_(0x205, 0x1BB - (font_h + 1), ...)`).

**Proposed and withdrawn on 30 August 2026.** The obvious patch is
four more fields on `HELLO_REPLY` — append-only, so a client reading
the first four bytes is unaffected, and one send per connection.
It was not requested, for one reason: OrionLayer needs the string to
draw one line of text on one screen, and a patch to somebody else's
tree is a permanent cost paid for a cosmetic gain. The number lives
in `core/config.ORION2RE_VERSION` instead, with
`tools/version_check.py` reading orion2re's two literals and failing
on a mismatch — a hand-copied number with a check is cheaper than a
line of C++ with a maintainer.

This changes if a client ever has to *behave* differently per engine
version: gating a feature on a number a human retypes is a different
proposition from labelling a screen with it, and that is when the
patch should come back.

### `MOX::_max_map_scale` and `_max_zoom_count`

Derivable from the serialized `MAP_MAX_X`: the ratio
`MAP_MAX_X / max_map_scale` is 50.6 for every galaxy size
(mapgen.cpp), and `max_map_scale` maps one-to-one onto
`max_zoom_count`. No patch required.

### A command to move `_cur_map_x/_cur_map_y`

Proposed and withdrawn on 30 August. OrionLayer's galaxy map zooms
and pans under the mouse pointer, which means moving the origin of
the *visible slice* — and the Extension API has no command that does
that. ACTIVATE_FIELD on the zoom buttons changes the scale but
anchors wherever the game decides.

It turned out to be the wrong question. `STATE_SNAPSHOT` already
carries `_star[]`, `_nebula[]` and `_ship[]` with their galaxy
coordinates, so a client can render any slice of the galaxy at any
scale without the game's view participating at all. OrionLayer now
does exactly that: the HD viewport keeps its own origin and scale,
and orion2re is never told that the wheel turned.

Two consequences worth knowing, because they constrain any client
that copies the approach:

1. **INJECT_CLICK still lands in the game's slice.** A star the HD
   view shows but `MOX::_cur_map_*` does not contain is unreachable,
   since `Star_On_Screen_` gates it. OrionLayer solves this by
   driving the game to `_max_map_scale` (zoom-out field only,
   throttled) while its own view is decoupled: at that scale the
   game's 505x399 native viewport covers the galaxy to within 1-3
   units on the far edge, for every stock size. Every galaxy->native
   conversion that reaches the wire uses the game's state, never the
   client's view.

2. **`s_ship_icon.x/y` are in the game's screen space.** They stay
   correct only for the game's own slice. A client with its own
   viewport must re-anchor them — OrionLayer draws in-transit ships
   at `s_ship_data.x/y` and orbiting ships at their star's position
   plus the game-computed slot offset, so `Build_Ship_Icons_` still
   owns the slot geometry.

Neither needs a patch. Recorded here so the request does not come
back.

### `MOX::_ship_node[]`

A ship icon carries only `node_idx`, and resolving it to an owner
needs `_ship_node[node].ship_idx` -> `_ship[ship].owner`. The table
looks unavoidable — it is not.

`SHIPSTAK::Find_Ship_Stacks_` (shipstak.cpp:45) allocates nodes
strictly sequentially, in BOTH branches of its loop:

```cpp
next_free = MOX::_next_free_node;
MOX::_ship_node[next_free].ship_idx = i;
MOX::_next_free_node++;
```

So node N is simply the N-th ship with `status < 3`, in array order.
The `location`/`x`/`y`/`owner` comparison decides which *stack* a ship
joins, never which node it occupies. And `_ship_node[].ship_idx` is
written nowhere else in the source — checked across all 319 .cpp
files.

`_ship[]` is already in the snapshot, so a client can rebuild the
mapping exactly. It can also verify it for free:
`SHIPSTAK::Ship_Stack_Star_Id_` (shipstak.cpp:25) returns
`_ship[_ship_node[node].ship_idx].location`, and
`Build_Ship_Icons_` stores that value in `s_ship_icon.star_idx` — so
every icon carries a checksum for its own node assignment.

Serializing the table itself would cost `MAX_SHIPS * 5` bytes, 45 KB
per tick, for something the client collapses into one byte per icon.

**`doc/ext_ship_icon_owner.patch` in the OrionLayer tree proposes
appending that one byte anyway. It is marked OPTIONAL and is not
being requested.** Its only remaining value is the narrow case where
`_ship[]` changed since the last `Find_Ship_Stacks_` call; the
client's own validation already detects that and falls back.

---

## Sprite dispatch (for clients drawing their own icons)

Not protocol, but the mapping a client needs if it renders ship icons
itself instead of using VISUAL_FRAME.
`SHIPS::Get_Ship_Icon_Pict_Seg_` (ships.cpp:337) dispatches on
`ship.owner`:

| owner | Meaning | BUFFER0.LBX index |
|---|---|---|
| 0–7 | player | `205 + player.color*4 + (3 - zoom)` |
| 8 | antaran | `237 + (3 - zoom)` |
| 9–14 | monster | `241 + (owner - 9)*4 + zoom` |

Note the inversion: players and Antarans index backwards by zoom,
monsters forwards. `NONPLAYER_SHIP_TYPE` is 8 antaran, 9 guardian,
10 amoeba, 11 crystal, 12 dragon, 13 eel, 14 hydra
(orion2_consts.h:528).

Icon dimensions are NOT in the source — they are read back from the
LBX at runtime into `MOX::_ship_icon_width/_height[4]`
(ships.cpp:328).

---

## Known limitations of the current server

**The list of what is being asked of Joes lives in
`doc/orion2re_open_fixes.md` and nowhere else.** An earlier version
of this section described two server bugs in full — SendFrame
dropping a client on a short write, and FIELD_LIST only being sent on
a field-count change — and kept describing them as open after the
fixes file had marked both **applied** in the 30 August tree. Two
documents disagreeing about what is being asked of somebody else is
the exact failure the fixes file exists to prevent, and this copy was
the second time it happened. So: a pointer, not a copy.

State at the last check (30 August 2026): items 1, 2 and 5 of that
list are applied in the source tree; items 3 and 4 remain open, and
both concern INJECT_CLICK — the coordinate mapping and the missing
MOUSEMOTION. The fixes file carries a grep per item to verify any
working copy, which beats trusting this paragraph's date.

---

## Live field dumps

Captured from the running game. **Labels in brackets are
interpretation, not protocol** — the API reports only geometry,
type and hotkey. One of them was wrong for two weeks; see the
Galaxy Map note.

### Main Menu (8 fields)

```
[0] (  0,  0)-(  0,  0) type=0  hotkey=---  (dummy)
[1] (415,172)-(567,193) type=7  hotkey=C    (Continue)
[2] (415,195)-(567,215) type=7  hotkey=L    (Load)
[3] (415,217)-(567,238) type=7  hotkey=N    (New Game)
[4] (415,240)-(567,260) type=7  hotkey=M    (Multiplayer)
[5] (415,262)-(567,283) type=7  hotkey=H    (Hall of Fame)
[6] (415,285)-(567,306) type=7  hotkey=Q    (Quit)
[7] (5000,5000)-(5000,5000) type=7 hotkey=N (hidden)
```

### New Game (17 fields)

```
[0]  (  0,  0)-(  0,  0)  type=0  (dummy)
[1]  (136,124)-(203,189)  type=7  (Difficulty picture)
[2]  (120,209)-(220,229)  type=7  (Difficulty label)
[3]  (291,124)-(358,189)  type=7  (Galaxy Size picture)
[4]  (276,209)-(376,229)  type=7  (Galaxy Size label)
[5]  (446,124)-(513,189)  type=7  (Galaxy Age picture)
[6]  (432,209)-(532,229)  type=7  (Galaxy Age label)
[7]  (136,264)-(203,329)  type=7  (Players picture)
[8]  (120,354)-(220,374)  type=7  (Players label)
[9]  (291,264)-(358,329)  type=7  (Tech Level picture)
[10] (276,354)-(376,374)  type=7  (Tech Level label)
[11] (395,300)-(538,329)  type=1  (Random Events toggle)
[12] (395,335)-(538,365)  type=1  (Antarans Attack toggle)
[13] (395,264)-(538,295)  type=1  (Tactical Combat toggle)
[14] (115,391)-(209,412)  type=0  (Cancel)
[15] (433,392)-(527,414)  type=0  (Accept)
[16] (5000,5000)-(5000,5000) type=7 hotkey=ESC (hidden)
```

### Race Selection (16 fields)

Fields 2–15 are the 14 race radios, laid out by
`(i / 7) * 126 + 351, (i % 7) * 48 + 90` (racesel.cpp:203).
All type 1 — INJECT_CLICK only.

```
[0]  (   0,   0)-(   0,   0) type=0 (dummy)
[1]  (5000,5000)-(5000,5000) type=7 hotkey=ESC
[2..8]   x 351..473, y 90 + n*48   Alkari … Klackon
[9..15]  x 477..599, y 90 + n*48   Meklar … Custom
```

### Custom Race (58 fields)

```
[0]  (   0,  0)-(  0,  0) type=0  (dummy)
[1]  ( 248, 15)-(398, 29) type=11 (race name input)
[2]  (5000,5000)-(5000,5000) type=7 hotkey=ESC (cancel)
[3]  ( 506,448)-(572,468) type=0  hotkey=A (Accept)
[4]  (  76,448)-(143,468) type=0  hotkey=C (Clear)
[5-31]   9 categories x 3 options, type=7
[32-35]  governments, type=7
[36-57]  22 special abilities, type=7
```

No radio buttons: `Add_Race_Options_Fields_()` uses
`Add_Hidden_Field_()`, so ACTIVATE_FIELD works for every field on
this screen.

### Galaxy Map (24 fields)

```
[0]  (  0,  0)-(  0, 21)  type=0   (dummy)
[1-5]( -1, -1)-( -1, -1)  type=8   (dynamic — ship icon slots)
[6]  (249,  5)-(307, 21)  type=0   hotkey=G (Game menu)
[7]  (544,441)-(608,466)  type=0   hotkey=T (Turn)
[8]  (244,428)-(298,443)  type=0   hotkey=+ (Zoom in)
[9]  (244,455)-(298,473)  type=0   hotkey=- (Zoom out)
[10] ( 17,434)-( 79,471)  type=13  hotkey=C (Colonies)
[11] ( 91,434)-(154,471)  type=13  hotkey=P (Planets)
[12] (167,434)-(230,471)  type=13  hotkey=F (Fleets)
[13] (312,435)-(379,471)  type=13  hotkey=L (Leaders)
[14] (386,435)-(453,471)  type=13  hotkey=R (Races)      ← see note
[15] (462,435)-(526,471)  type=13  hotkey=I (Info)
[16-20] (545, y)-(613, y) type=7   (fleet icons 1..5)
[21-22] ( -1, -1)-( -1, -1) type=8 (dynamic)
[23] ( 22, 22)-(527,421)  type=12  (map click area)
```

**Correction, 28 August 2026.** Field 14 was previously listed here
as *Research*. It is the **RACES** button — mainscr.cpp:1398:

```cpp
_races_button = fields::Add_Irregular_Button_Field_(
    386, 435, 453, 471, "", MOX::_main_races_button_seg,
    306, 425, "R", 0x28);
```

The hotkey R fits both words, and the label in this dump was a
guess that was never checked against the source. It reached
OrionLayer's `layout.json`, where a click on the HD "Research"
button would have opened the diplomacy screen. There is no
Research button in the bottom bar at all — research is reached
through the sidebar. Treat every label in this document as
interpretation until the source confirms it.

---

## Risk assessment

| Risk | Rating |
|---|---|
| Broken build without the flag | Impossible (everything behind `#ifdef`) |
| Game logic change | None (read-only access) |
| Performance without clients | One call per loop, immediate return |
| Performance with clients | ~0.5 ms per tick |
| Memory leaks | `Server::Stop()` cleans up |
| Network exposure | Localhost only |
| Merge conflicts | Minimal (small insertions, stable locations) |
| Double-click from injection | Solved by separate `g_pending_field` |
| Hang from INJECT_CLICK | Solved by pushing DOWN and UP |
| Radio buttons unresponsive | Documented — INJECT_CLICK for type 1 |
| Client dropped on busy socket | **Fixed** in the 30 Aug tree (`orion2re_open_fixes.md` #1) |
| Reconnect blind mid-screen | **Fixed** in the 30 Aug tree (#2 — FIELD_LIST after HELLO) |
| INJECT_CLICK coordinate mapping | **Open** — `orion2re_open_fixes.md` #3 |
| INJECT_CLICK missing MOUSEMOTION | **Open** — `orion2re_open_fixes.md` #4 |
