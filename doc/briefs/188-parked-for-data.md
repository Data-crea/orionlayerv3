# Work order 188 — parked for Data

Every item names the default this run continued with and why. First what
this order decided or left open, then the items carried over unchanged.

## 1. From this order

### 1a. Answered from 187 (no decision needed any more)

- 187's 2a, "The audience menu's title colour": the order decided it — the
  items' colour. Built (Part 2).

### 1b. The fleet box's ETA text on hover (Part 3)

The original also prints "%d turns to %s" / "%d parsecs to %s" / the refusal
in the fleet box while a star is hovered (fleetpop.cpp:1063-1091). FMOV now
carries every number it needs (turns_left, parsecs, flags). **Default: not
built** (the order asked for the line); the box keeps its status line.

### 1c. The turn-time screens that still show the F12 notice (Parts 4, 5)

Tactical combat (and combat's own boxes), the invasion / bombard choice,
ground combat, the galactic council, the Antaran room, the evolutionary
mutation picker, the monster bribe, the star rename, the occupation-policy
popup and the end of game run under 12 / 0 / 33 without an HD view: the
F12 notice stands there (Stage 1), so the game is answered on F12. What each
needs is in `doc/brief_turn_messages.md` ("What would need engine fixes" of
the reading: the council's state and lists, the combat popups' data, the
star name field). **Default: notice**; proposal: the council and the star
rename next (they appear in normal play without combat).

### 1d. The popups' artwork (Part 4)

The HD turn popups and the message box are HUD panels (DEVIATION
`hud_turn_popup`, `hud_message_box`): the science room, the GNN studio and
its picture, the colony landing art, TURNSUM.LBX, the BUFFER0.LBX frames and
the system display's planet pictures are not drawn — the system display is
a list of the star's planets by name. **Default: as built**; the pictures
are an extractor away if Data wants them.

### 1e. The Online endpoint reads "ATZ" (Part 7)

The multiplayer setup's Online type (its artwork still says MODEM) connects
to one endpoint, which orion2re keeps in the settings (MOX.SET); the source's
default is "127.0.0.1:47800" (multplay.cpp:233-237), but on this machine the
dialog shows "ATZ" — a modem init string, apparently what the player's own
MOX.SET holds at that place from the original game. Joining an Online game
with it would fail. **Default: unchanged** (MOX.SET is Data's; HD shows what
the engine holds and lets the player type another); proposal: Data types
his router's endpoint once, or orion2re resets an endpoint that does not
parse as host:port.

### 1f. Network multiplayer across two engines (Part 7)

The multiplayer setup, COMM INFO, the join list, the load list's message and
a whole hotseat game were walked in HD on one engine. Hosting and joining a
NETWORK or ONLINE game need a second engine, and one machine cannot run two
on OrionLayer's wire (ext port 17362 fixed, ext_api.h:12) nor host twice
(router port 47800 fixed). **How Data can test it**: on a second machine (or
a second user account with its own game folder) start orion2re and choose
NETWORK → START NEW GAME; on this machine, in OrionLayer, MULTIPLAYER →
NETWORK → JOIN GAME — the HD list should show the host's game with its
player count; or ONLINE with COMM INFO's endpoint set to the host's
`address:47800`. What to look at: the host's waiting panel counting players,
the race picks, the "Choose your empire" list for a loaded game, and the
chat between turns (37). **Default: parked** (drawn from MPLY, checked
offline in 090zf, not seen live).

### 1g. Five engine bugs found reading multiplayer (open fix 51's entry)

The chat buffer's overrun, the endpoint's one-byte overrun, two ESC buttons
in the Online dialog, the pick-position screen's dead cancel (a joiner sends
an uninitialised pick on ESC), the setup's four-field first pass. HD stays
inside the buffers; nothing else is changed. **Default: reported** (for
Joes), not fixed — no part of this order needs them fixed.

## 2. Carried over unchanged (not acted on in this order)

- **From 185** (`doc/briefs/185-parked-for-data.md` item 2c, "The Ship
  Designer live test (part 8) — three differences, as questions", and 2d,
  "The audience live test (part 11) — questions"): the chosen hull only
  faintly marked (default: as built); the audience's header line (text) not
  drawn (default: not added), its fade-in and talking animation not played
  (default: still).
- **The extra slot message after ESC in the load dialog** — `doc/briefs/
  179-parked-for-data.md` item 1, "Open fix 34's ESC side effect — ask Joes
  for a reset? (default: no)". Default: leave it.
- **Narrow buttons with the word only** — decision 71, "The cockpit frames
  give way to ONE FRAMELESS STYLE, drawn in code, on every screen.".
  Default: unchanged until icons arrive.
- **Buildings as a list instead of the grid** — open fix 36, "Where the
  colony screen puts its buildings", applied and unused; UNVERIFIED
  `building_placement`. Default: unchanged.
- **The research query at turn start not measured** — `doc/briefs/
  184-parked-for-data.md` item 2, "The turn-start research prompt was not
  measured live". Default: not measured.
