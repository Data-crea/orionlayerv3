# Work order 177 — parked for Data

Every choice and question this unattended run parked, with the default
taken.

---

## 1. Open fix 34 — apply it? (default: not applied, the net shows the dialog)

The main menu's Load dialog has no save slots on the wire
(`SerializeSaveSlots` sends only on SCREEN_GAME). The patch
`doc/ext_main_menu_save_slots.patch` adds the main menu's case (entry 34).
Until it is applied the safety net shows the game's own dialog — list, LOAD
and CANCEL all work (live, both sizes' evidence in `continue_and_load_1920/`
and `main_menu_load/`); with it, the GAME menu overlay draws it in HD.

**What the Load dialog can and cannot do without it** (178, measured live at
both sizes): it CAN list the ten slots with the game's own names, load a
slot by clicking its row (the original's behaviour — the row loads at once),
cancel with CANCEL or ESC — every input reaches the game. It CANNOT be drawn
in HD: the player sees the 640x480 dialog scaled into the window with the
original's frame and font, not the popup block the GAME menu's Load uses; no
HD hover, no HD help regions, and the slot names and stardates are only
pixels to OrionLayer. Applying it is one condition in `SerializeSaveSlots`
and needs a rebuild and a live run; still NOT applied (178 was told not to).

## 2. `fltbox`'s WARNING crop is the wrong rectangle for text boxes

The WARNING shape (one full-screen field, hotkey ESC) is also every TEXTBOX
box's (textbox.cpp:249: 380 wide at x=84, height from the text). On the
galaxy map that shape now goes to the net; on the screens that already used
`fltbox` (Fleets, Leaders, Races) a text box would still be cropped at the
warning's fixed rectangle. Default: unchanged there.

## 3. The HD views not built in 177 (all go to the safety net, each logged)

#2 star name after colonising, #3 planet selection (the colony-base
question — seen live every TURN on SAVE4), #7 hire, #8 level, #9 scouts,
#10/#11 text and warning boxes, #13 tax, #14 GNN/diplomacy, and the turn
summary (below). The inventory in the progress file says what each shows
and takes. Which comes first is yours; my suggestion is #3, the one every
colonising player meets.

## 4. The turn summary reports screen 0 (found live)

After TURN the turn summary came up under screen **0** (10 fields, a
scrolling list, CLOSE hk ESC), not as screen 40. It is on the net now.

## 5. The typed-name mirror after a reconnect

The text being typed is not on the wire, so HD mirrors it. A client that
connects WHILE the dialog is open starts its mirror from the star's name,
not from what the game holds: live, the game had "Vega" typed, the new
client showed "Sol", and ACCEPT committed "Vega" (correctly — the game's
text wins). Only a reconnect mid-typing shows it. Default: accepted; the
cure would be a patch putting `_continuous_string` on the wire.

## 6. `engine_start --blanked-ok` (a rule change to confirm)

The screen was blanked for the whole unattended run and `engine_start`
refused: its rule predates open fix 31. I added `--blanked-ok` (default
unchanged, the start says it in its output, the other refusals stay) and
used it for all three starts — each came up through the intro, no hang.
If you want the default to change now that fix 31 is applied, say so.

## 7. The confirmation popup's size

The confirmation is the game's box scaled with the map's scale (`fltbox`'s
placement) — at 2576x1432 it fills most of the map. Readable, but large
(`turn_modals_2576x1432/002_…`). Default: unchanged, same as the other
screens' boxes.

## 8. Not done: `fltbox.draw` on the popup block

The summary's optional item (drawing `fltbox`'s frame with the HUD popup
block on every screen) was not done; the map's confirmation uses the popup
block, the other screens keep theirs.
