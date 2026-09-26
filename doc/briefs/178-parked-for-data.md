# Work order 178 — parked for Data

Every choice and question this unattended run parked, with the default
taken. 177's own parked items stay in `177-parked-for-data.md`.

---

## 1. Open fix 34 — apply it? (default: NOT applied, as this order said)

The decision is yours; the facts are in `177-parked-for-data.md` item 1,
extended by this run: without fix 34 the main menu's Load dialog works
fully — list, a row click loads (SAVE4 at 1920 and 2576), CANCEL/ESC — but
it is the original's 640x480 picture scaled, not drawn in HD. With it, the
GAME menu overlay draws it like the in-game Load. Patch:
`doc/ext_main_menu_save_slots.patch`, entry 34 in `doc/orion2re_open_fixes.md`.

## 2. The stray file after the reboot

`go to the safety net (found live) (177-C)` in the tree root, created at
18:29:39 — three minutes after the machine came back, before this session
started — held only `less`'s help screen. Removed (commit 13cc8b1). If you
typed something at that moment and meant it to do something else, it did not.
