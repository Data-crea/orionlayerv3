# Work order 130 — parked for Data

The order has no reporting stop, so this file holds only what could not
be finished here and what is Data's to decide. Everything else is
committed and green at 212 checks.

## 1. THE LIVE ACCEPTANCE — run on 18 September, one occasion short

**Ran.** orion2re rebuilt from `orionlayer-local` (e9d07528, the binary
checked for `ext::g_activated_input`), a new Psilon game, one client,
SAVE1-9 and SAVE11 identical before and after, SAVE10 logged only.
Evidence: `~/orionlayer-fixtures/evidence/work_order_130/`.

**Part A — done, twice.** `A_step/` and the earlier
`A_science_room_52/`: on wire id 52 the window shows the game's picture
and a click in it advances the room; four and five clicks walked two
rooms out and handed over to 53. No F12. `A0_colony/` is the same on
SCREEN_COLONY (1), where RETURN through the fallback moved the game to
39.

**Part B — done, twice, two categories.** `F1/` (HD row click -> field
4, category 4) and `B2/` (bare ACTIVATE_FIELD -> field 22, category 6).
Each read back off the wire and each matched the row. The pointer was
never moved by the run.

**Still owed, and why:**

- **the third occasion**, in a third category. Two attempts lost it to
  open fix 26 (below), and by the time the driver was reshaped to win
  that race, the machine's display server had stopped accepting new
  clients — `SDL_Init(SDL_INIT_VIDEO) failed: The video driver did not
  add any displays`, with gnome-shell still running and the sockets
  still there. orion2re could not be started again. Nothing about the
  build or the patch; the desktop session.
- **HD beside the native frame at three resolutions.** There is one
  resolution, 1920x1080 (`F1/001_F1_select_list_hd.png` beside
  `..._native.png`).
- **the 128 crash case.** It needs a category with nothing left to
  offer, and no list this run reached had one.

**To finish it**, with the display back:

    cd "$HOME/Master of Orion 2" && \
        ~/orion2re/out/build/Linux/linux-debug/orion2re &
    cd ~/orionlayerv3
    python tools/research_hd.py newgame     # to the map, turn one
    python tools/research_hd.py advance     # to the first dialog
    python tools/research_hd.py roomchoose 1 hd F4
    python tools/research_hd.py crash       # when a category runs dry

`roomchoose` walks the science room out and chooses in ONE process,
which is what beats open fix 26. Expect `MATCH` on the last line of
each choose; anything else is the finding, not the tool.

## 1b. A NEW OBSERVATION — open fix 26

`SELECT NEW RESEARCH` commits a row by itself, about a second and a half
after the science room hands over, with a send counter proving the
client sent nothing (the table is in `doc/orion2re_open_fixes.md`).
Three times in one run; the committed field was the first offered
entry's each time. `_last_button_number` is ruled out — written in three
places, read in none. The mechanism is NOT established, which is why it
is filed as an observation and not a request.

**Why yours:** it decides whether the HD screen should do more than
re-read. Today it re-reads the list on every entry and hands back to the
fallback when it cannot vouch — which is the right behaviour either way.
**Answer:** leave it as an observation / chase the mechanism next.

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

**Closing state, 18 September 2026: five items.** The run happened;
parts A and B are proven and part F is one occasion short, for a reason
that is the desktop's and not the build's. Nothing was pushed in either repository. `~/orion2re` has one
new commit on `orionlayer-local` with its push URL still disabled.
