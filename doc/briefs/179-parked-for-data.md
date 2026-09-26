# Work order 179 — parked for Data

Every choice and question this unattended run parked, with the default
taken.

---

## 1. Open fix 34's ESC side effect — ask Joes for a reset? (default: no)

Leaving the main menu's Load dialog with ESC keeps `_screen_data` 2
(loadsave.cpp:388-391; CANCEL resets it at :382-383), so with fix 34 the
menu's own field list is followed by a slot message. HD ignores it (it needs
the dialog's fields too), so nothing is wrong on screen. A one-line reset on
the ESC path would be an engine change beyond fix 34; not written as a patch.
Default: leave it, recorded in entry 34.
