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


---

## 3. Androids — a live observation, and two of three sources

Follow-up to the Part A check, 21 September 2026. **Read-only, nothing
sent to the game, no commit.** Evidence:
`~/orionlayer-fixtures/evidence/work_order_160/android/`.

### 3a. Data's live observation — NOT a verification of the nibble

**Data, 21 September 2026, in the running game:** androids can be moved
to another planet, but only into the job they already have; they cannot
change jobs.

That is exactly `COLMOVE::Give_Colonist_New_Job_`: `pop_state == 4` is
refused **only** when `current_job != new_job`
(`colmove.cpp`, the `if (pop_state == 4)` block).

**It is recorded here as an observation of BEHAVIOUR, not as evidence
about the nibble.** It says the android rule behaves as the source
reads; it does not show which nibble an android carries. Those are two
different claims and 3b is the one about the nibble.

### 3b. OrionLayer against that rule — the rule is right, the gesture is absent

**`REFUSE_ANDROID` is correct.** `screens/colony_summary/colonymove.py:192-194`:

```python
if state == POP_STATE_ANDROID:
    if colony_struct.pop_prof(pops[index]) != new_job:
        return False, REFUSE_ANDROID
```

Job change refused; same job falls through. That mirrors the engine
line for line.

**But HD does refuse moving an android to another colony** —
`screens/colony_summary/colonypick.py:215-216`:

```python
if colony != pick.colony:
    return Refusal(REFUSE_OTHER_COLONY)
```

**This is a missing feature, not the android rule misfiring**, and the
distinction matters:

- it refuses **every** pop across colonies, not androids specifically;
- the inter-colony move is **not `Give_Colonist_New_Job_` at all**. It
  is the long branch of `Send_Cluster_` → `SETTLER::Pop_Tries_To_Settle_`
  / `Settle_Pop_` (`colmove.cpp:278-279`), with eleven refusals, an ETA
  and two confirmation boxes — the fundament says so under the
  four-drop-rules entry, and `v3_projektstatus.md` records the decision:
  *"Population TRANSFER stays out and gets its own decision if it is
  ever wanted."*
- the player is told, in `layout.json`: *"Pops can only be moved inside
  one colony here."*

**So nothing here is to be fixed as a bug.** What Data saw the original
do, HD does not offer at all. Whether population transfer is built is
the decision already parked in the status document.

### 3c. Nibble 8 = android — two sources hold, the third is yours

**The save.** `SAVE7.GAM`, in-game name **"Androids"**, sha256
`21b865aaf4b59f8093213fb959d46eeed7c811e1d60dcd36a595e7755d5498a8`,
72 837 bytes, copied to the evidence folder as `SAVE7_Androids.GAM`.

**Source 1 — the raw data, from BOTH readings, and they agree.**
Colony 15, owner 0, 11 pops:

| pop | word | nibble | profession | conquered |
|---|---|---|---|---|
| 9 | `0x308` | **8** | 2 | no |
| 10 | `0x288` | **8** | 1 | no |

- **Live snapshot** (game running, read-only, no input sent): as above.
- **Save file**, independently: the colony record sits at offset 6022
  in `SAVE7.GAM`, and **357 of its 361 bytes are identical to the live
  record**. The four that differ are at record offsets 180, 181, 220
  and 302 — `pop_roundoff`, `n_turns_existed` and `occupation_points`,
  all state that advances with turns. **The pop array is `@12`,
  `u32[42]`, so it ends at offset 180: every byte of it matches, and
  the first difference is the byte immediately after it.**

**Source 2 — the sprite, and it does not depend on our naming.**
`COLONY::Pop_To_Pop_State_` maps nibble 8 → state 4, and
`People_Anim_` (`colony_main.cpp:437`) answers state 4 with **RACEICON
entry 0xA9** and state 3 (nibble 9, native) with **0xAA** — both
race-independent. Entry 0xA9, extracted and enlarged in the evidence
folder as `android_x8.png`, is unmistakably a **metallic segmented
robot**; 0xAA (`native_x8.png`) is an organic figure in brown and
blue. The chain nibble → state → entry is read out of the engine, and
the picture at the end of it is what it is regardless of what our
extractor chose to call the file.

**Source 3 — the game's own words: MISSING, and it is Data's to
supply.** The order says not to do this myself. **Please hover a pop of
colony 15 ("Androids" save, the two pops in the scientist and worker
columns) on the colony screen and read out the label, or send a
screenshot.** For the natives this read "Native farmers"; the question
is whether this one says "Android" something.

### 3d. The change to propose IF the hover text agrees — not made

`8 = ANDROID IS NOT VERIFIED` is held in **five** places by one smoke
check (`tools/smoke_test.py`, the "nibble marking is SPLIT" block).
Promoting it means editing all five together, and the check is what
makes that impossible to do by halves:

1. `core/structs/colony.py` — the `**8 = ANDROID IS NOT VERIFIED.**`
   block, which would gain the new save, its sha256 and its three
   sources the way the natives' entry names
   `fixture_natives_3502.5.GAM` and `b1f1aa466716d6c0`;
2. `screens/colony_summary/colonymove.py` — `still UNVERIFIED`;
3. `v3_projektstatus.md` — `STILL OPEN: nibble 8 = android`;
4. `tools/smoke_test.py` — the needle list itself, which currently
   asserts the *old* strings are present;
5. and the new save named beside the old one, so the claim keeps
   resting on a named save rather than on a memory of a session.

**Not done.** The third source is missing, and the order says to
propose rather than change.

### 3e. Out of scope, recorded as asked

**The "Androids" save does have a colony with androids and no
conquered pops:** colony 15 carries two nibble-8 pops and **no pop with
`MASK_CONQUERED` (0x400)** — checked over all 11 pops, in both the live
snapshot and the save file. That is the shape A1's counter-proof would
need; A1 itself was not examined.
