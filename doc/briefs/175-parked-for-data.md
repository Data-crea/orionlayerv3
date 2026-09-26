# Work order 175 — parked for Data

Every choice and question this unattended run parked, with the default
taken.

---

## 1. Fix 31's re-measure — waits for the port

**Why parked:** the Extension API's port is fixed (17362,
`src/ext/ext_api.h:11`) and Data's engine (PID 368253) held it for the
whole run; the order forbids connecting to it or stopping it. A second
engine cannot start.

**Default taken:** fix 31 is applied and built; nothing about tearing is
claimed. When the port is free:

    python tools/engine_start.py          # backs up, starts with ORION2RE_NO_VSYNC=1
    # 20 starts with a full-screen window in front; count hangs
    # load SAVE4, scroll the galaxy map and the Colonies list; look for tearing
    python tools/liveguard.py verify <folder printed above> --restore --allow SAVE4.GAM

If tearing shows, the proposal is **VSync off only during startup**
(the present that hangs is in the logo frames, before the window has
ever been drawn); a VSync with a timeout is the fallback.

## 2. Leaders live test — waits for the port

Same reason. `python tools/leaders_hd.py run 5` loads SAVE5 (scratch)
and walks both tabs. Every button, the map and the grid need no special
state; **hiring needs a scratch save in which the player has a leader
FOR HIRE (status 4) and the BC to pay** — SAVE2 offered three in 167's
offline reading, so a copy of it into slot 4 or 5 is the state.

## 3. Races: the missions and the spy drag are drawn, not sent

**Why:** a mission button (multi-button, type 3) changes its value only on
a real click inside `Draw_Field_`, and a mission or a moved spy reaches
`s_player.spies` only when the screen commits (`Update_Spy_Stuff_`,
racescrn.cpp:518-530 — on exit, report, war, diplomacy). HD could not see
the effect of such a send (decision 65); the drag also needs the pointer X
(`Draw_Icon_Group_Cursor_` counts the carried spies from it).
**Default taken:** display only (HD STATE `missions_and_spies`); in the
game's own picture (F-key fallback) both work as in the original.
**What would unlock it:** an OFFS-like block for screen 6 carrying
`race_display_data[].agent_mission_idx` and the carried count — an open
fix, not written in this order.

## 4. Races live test — waits for the port

`python tools/engine_start.py`, load SAVE4 (scratch; five living players,
two at war/limited war), open RACES, press every button: RETURN, AUDIENCE
(then a race → diplomacy in the fallback, ESC back), REPORT (→ report in
the fallback), IGNORE (→ a race: "(IGNORED)" appears, press again), DECLARE
WAR (→ a race → the confirmation, answer NO). Verify with
`tools/liveguard.py verify … --allow SAVE4.GAM` — IGNORE changes the save's
player record only if the game is saved, which the test does not do.
