# Work order 185 — parked for Data

Every item names the default this run continued with and why. Open fixes
first, then the decisions this order asked to park, then everything else,
then the items carried over unchanged.

## 1. Open fixes awaiting approval

### 1a. Open fix 42 — approve? (the question from part 1: are clicks lost in the gap?)

**Answer, measured** (entry 42, "A screen is silent on the wire while its
input delay counts down", section "Clicks in the gap"): **no input is
lost and none is taken twice.** 260 inputs at 13 offsets from the HD
screen's first frame, on the patched scratch engine and on your applied
build, into the research panel (by activation, injected key and injected
click), the colony screen and the build popup. Only the research panel
has a gap with the fix — its five-pass delay outlasts HD's first frame —
and an input landing in it is held (in `g_pending_field` or SDL's queue)
and takes effect when the delay ends, 560-610 ms after the panel appeared.
The colony screen and the build popup showed no gap at all (their
three-pass delays end before HD's first frame).

**Recommendation: approve fix 42 as it is.** No addition is needed: the
engine already keeps what arrives during the delay. What the player
notices is the opposite of a loss — the panel ~550 ms sooner, and a click
in its first half-second answered up to half a second late instead of the
panel appearing half a second late. Not covered by the trials: the Ship
Designer's 20-pass delay before its weapon picker (design.cpp:870) — the
same mechanism, a longer wait. **Default: not applied** (this order
changes no engine).

## 2. Decisions asked for in this order

(Filled per part below.)

## 3. Everything else

- **`doc/CREDITS.md` quotes the 1.50 patch's own credits verbatim**, and
  that quotation contains a personal name; the on-screen roll
  (`screens/main_menu/assets/credits.txt`) does not. Default: the document
  is left unchanged, because the order names the roll and the document
  marks the quotation as unchanged.

## 4. Carried over unchanged (not acted on in this order)

- **The extra slot message after ESC in the load dialog** — leaving the
  main menu's Load dialog with ESC keeps `_screen_data` 2
  (`doc/briefs/179-parked-for-data.md` item 1, "Open fix 34's ESC side
  effect — ask Joes for a reset? (default: no)"). Default: leave it; it is
  in the handover package for Joes (part 4) as a note.
- **Narrow buttons with the word only** — buttons the HUD has no icon for
  draw their word alone (decision 71, "The cockpit frames give way to ONE
  FRAMELESS STYLE, drawn in code, on every screen.": "a screen that needs
  an icon the HUD does not have draws a text-only button until Data
  supplies one"). Default: unchanged until icons arrive.
- **Buildings as a list instead of the grid** — open fix 36 ("Where the
  colony screen puts its buildings") is applied but unused; the colony
  screen lists the buildings (DEVIATION `building_list`) and does not place
  them (UNVERIFIED `building_placement`). Default: unchanged.
- **Plague and population boom not yet seen live** — open fix 37 ("The
  colony screen's Plague and Pop Boom word") carries them; no scratch save
  has either event. Default: unchanged until a save has one.
- **The research query at turn start not measured** — it appears only
  after a turn that completes a project, and ending a turn writes SAVE10
  (`doc/briefs/184-parked-for-data.md` item 2, "The turn-start research
  prompt was not measured live"). Default: not measured.
