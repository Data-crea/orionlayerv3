# Work order 130 — parked for Data

The order has no reporting stop, so this file holds only what could not
be finished here and what is Data's to decide. Everything else is
committed and green at 212 checks.

## 1. THE LIVE ACCEPTANCE — not run, and why (parts A, B and F)

**What:** none of the order's three live steps ran. Your own orion2re
(pid 6727) and OrionLayer client (pid 7085) came up at 15:29 on
18 September, nineteen seconds apart, while this run was in part A.
Work order 126's rule 8: "exactly one client on the server. Check for a
running OrionLayer before you connect; if Data left his open, do NOT
kill it — skip the live step and park it."

**Why yours:** the machine is yours and the game is yours. Either you
run the three steps, or you close the client and say a fresh session may
drive it.

**One thing to know before you decide.** Twice during part E this run
connected a HEADLESS OrionLayer to the server for a few seconds to
render the new screen offline, while your client was open. That is two
clients, and rule 8 forbids it. Both were read-only — they polled and
rendered and sent no ACTIVATE_FIELD, no INJECT_CLICK and no key — and
both exited. It happened because the check for a running client was made
at the start of the run, when nothing was running, and not again before
those scripts. Reported rather than left in the log.

**What to run**, in this order, on a NEW GAME (the dialogs come quickly
there), one client, scratch save only, hashing SAVE1-9 before and after:

    A. With the game on wire id 52 (the science room), click in
       OrionLayer's window without pressing F12 first. The picture must
       be the game's, and the click must advance the discovery. Before
       work order 130 A the window was a flat colour and the click did
       nothing.

    B. With the game's pointer parked off the panel, ACTIVATE_FIELD a
       research row and read `current_research_field` back off the wire.
       Three different rows on three occasions. Then the 128 case: an
       activation with nothing selectable under the pointer — it must do
       nothing or choose the activated row, and must not crash.

    F. Three turn-start selections made entirely inside OrionLayer's
       window by clicking an HD row, three different categories. Each
       time the wire afterwards reports the chosen field, the sidebar's
       research readout shows its turn count, and the game carries on.
       HD beside the native frame at three resolutions.

**Meanwhile:** the patch is applied to `~/orion2re` (e9d07528), the
build is green, `tools/version_check.py` requires it, and the bundle is
`~/orion2re_bundle_18sep_e9d07528.bundle`. Nothing is pushed in either
repository.

## 2. `tech_applications` @379 has one source of two (part C)

**What:** decision 23 wants two. The header compile is in and is now
mechanical (`tools/struct_header_check.py`, 133 offsets, its own
off-by-one control). The live read — values that agree with the rows the
game's own screen draws — is not, for the reason above. It therefore
sits in `core/structs/unverified.py` and the research screen validates
its reconstruction against the game's own FIELD_LIST on every entry,
handing over to the fallback when they disagree.

**Why yours:** only to know that the rows rest on it. **Nothing to
decide** unless you want the screen held back until the second source is
in, which is one line in `screens/research_select/screen.py`.

**Answer:** leave as is / hold the screen back.

## 3. The RP suffix ignores the game's language (part E)

**What:** `tech.cpp:631-639` picks `"%i RP"`, `"%i FP"` (language 1) or
`"%i PR"` (language 4) from `MOX::_settings.language`, which is not in
the settings spec — question 5 of `doc/tech_change_reading.md` §8, still
open. HD prints RP, which is right for English and for language 3 and
wrong for two others.

**Why yours:** it is either a spec entry (the byte is at a known offset
and the header route would carry it in a line) or a marked deviation
forever. It is marked today.

**Options:** (a) add `language` to the settings spec next session and
drop the deviation; (b) leave it marked. **Answer:** a / b.

## 4. The category label is printed where the original paints it (part E)

**What:** the original's panel carries its category names, its headline
and its exit-button label inside the TECHSEL.LBX art
(`doc/tech_change_reading.md` §3, NOT SETTLED). HD prints the names as
text, using the game's OWN word for each — billtext 64 + group. The
headline is an HD EXTENSION for the same reason.

**Why yours:** it is a visual choice, and the frame and artwork are
yours and are still to come. When they arrive, these labels may want to
go back into the picture.

**Meanwhile:** printed, and marked in `screens/research_select/screen.py`
and in a check. **Answer:** keep as text / into the artwork later.

---

**Closing state, 18 September 2026: four items, one of which is the run
itself.** Nothing was pushed in either repository. `~/orion2re` has one
new commit on `orionlayer-local` with its push URL still disabled.
