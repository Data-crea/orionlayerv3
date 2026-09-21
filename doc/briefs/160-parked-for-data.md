# Work order 160 — parked for Data

21 September 2026. **Repair not made.** Work order 160 was a
verification run with no code changes, and both items below are
documents in our own repo, not in the handover.

---

## 1. Two patch headers claim they are not applied, and both are

Found while settling the contradiction the order named. **Neither
affects the handover to Joes** — it quotes neither header — so nothing
was corrected in a hurry.

### 1a. `doc/ext_move_pop.patch`, line 11 — **stale**

> STATUS: needed to retire the RESORT / ESTABLISH / PICK / DROP click
> chain, which costs four snapshot round trips per drop and has to
> steer the game's own ten-row window first. **NOT YET APPLIED.**

It is applied. `MSG_SET_JOBS` is on `orionlayer-local`
(`ext_api.cpp:699`) and the engine side is `7067c366`, "Open fix 12:
pop-move refusals without the message box (colmove)". The other
source, `doc/orion2re_open_fixes.md` item 12, is **right**: "patched
locally 10 September 2026, VERIFIED LIVE the same day".

### 1b. `doc/ext_save_slots.patch`, line 16 — **stale**

> STATUS: REPORTED, NOT APPLIED (14 September 2026). Until it is, the
> HD Load and Save dialogs show slot numbers only, a marked HD STATE.

It is applied. `MSG_SAVE_SLOTS = 0x14` is on the branch
(`ext_server.h:27`, sent from `ext_api.cpp:843`), and item 14 says
"**Applied** 16 September 2026 by Data, confirmed live the same
evening". `CLAUDE.md` also says "slot names from
`doc/ext_save_slots.patch` **(applied)**".

**Why this shape keeps happening, and it is worth one line:** a patch
file's STATUS is written when the patch is *drafted* and has to be
edited again when it is *applied*. Nothing checks it. Two of the ten
`doc/ext_*.patch` headers have drifted; the other eight are right.

**What Data decides:** whether to fix the two headers, and whether a
check should hold every `doc/ext_*.patch` STATUS against
`doc/orion2re_open_fixes.md`'s status for the same item. That check is
the same shape as the ones that already hold the check count and the
line-count list — a hand-maintained claim is legitimate only with a
checker — but adding it raises the suite count and is a decision, not
cleanup, which is why it is here and not done.

---

## 2. Part A's tree is not on this machine — for Data, not for Joes

**Out of scope and not changed.** The handover says Part A was checked
against the upload with `ENGINE_VERSION "2.0.0"` and
`GAME_BUILD_DATE "Aug 15 2026"`, and A4 quotes both strings back to
Joes.

Neither orion2re tree here reports that: `~/orion2re` and
`~/orion2re-main-neu` both say `ENGINE_VERSION[] = "1.60.0"`, and
neither defines `GAME_BUILD_DATE` at all.

That is **not evidence Part A is wrong** — the order scoped Part A out
because it was checked elsewhere, and the 2.0.0 tree may simply not be
on this disk. It is raised because A4's two quoted version strings are
the first thing Joes can check in his own tree, and if they came from
a tree nobody here can open, nobody here can re-check them before the
document goes out.

**Auf Deutsch:** Teil A wurde laut Auftrag gegen Joes' 2.0.0-Upload
geprüft und war hier ausdrücklich außen vor. Nur zur Kenntnis: auf
dieser Maschine meldet kein orion2re-Baum 2.0.0 — beide sagen 1.60.0,
und `GAME_BUILD_DATE` gibt es in keinem. A4 zitiert Joes beide
Strings; falls der 2.0.0-Baum hier nicht liegt, kann das vor dem
Versand niemand nachprüfen.
