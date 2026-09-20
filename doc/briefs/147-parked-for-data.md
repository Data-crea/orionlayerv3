# 147 — parked for Data

## 1. The order arrived truncated

It ends mid-sentence:

> `## Acceptance`
> `- Every`

Everything up to that point is answered in
`doc/v3_original_gui_construction.md`. Whatever acceptance criteria
followed did not reach me, so I held the order to its own Method and
Deliverable sections and to the tree's usual rules (fresh clone, smoke
green before any commit, nothing left dirty). **This is the second
order in a row to arrive cut off** — 145 ended at "Report edge
thickness per side". If they are being pasted from a longer document,
the tail is being lost somewhere between there and here.

## 2. "The reading budget in CLAUDE.md" does not exist

The order says to respect it. `CLAUDE.md` has no budget section, and
neither does `doc/v3_fundament.md` — the only thing by that name is
`~/Downloads/workorder_reading_budget.md`, drafted 17 September against
`d8006d7` and **never filed or run**. It proposes splitting the status
document and giving the split a checker.

I read economically and cited rather than quoted, but I could not obey
a rule that is not in the tree. If that work order is still wanted it
needs a number; it is currently the only `workorder_*.md` in
`~/Downloads` that was never filed.

## 3. The live part was stopped, per protocol

A client was attached for the whole run: Data's own OrionLayer,
pid 327353, on a restarted engine, pid 327095 — both up about an hour.
The live-test protocol says stop if another client is on 17362, so
nothing of mine connected.

**Consequence:** the report's pixel evidence comes from the shipped LBX
archives, which is the original's own art and exact, but there is no
native screenshot of a running screen taken for *this* order. The
composition claims in question 6 are from source only. SAVE1-6, 9 and
11 were hashed before and after and are unchanged, which is what one
would expect when nothing connected; SAVE8 untouched.

A later run with the port free could confirm question 6 against pixels
in one pass: open a screen, open a dialog over it, dismiss it, and
check that the area underneath comes back from the background rather
than from a saved copy.

## 4. Three things source reading could not settle

**a. Why the main menu's hidden field is a pixel shorter than its art.**
`Add_Hidden_Field_(0x19F, 0xAC, 0x237, 0xC1, …)` gives 153x22 and
MAINMENU.LBX entry 3 is 153x23. The width matches exactly, so this is
not a different convention — it looks like one number typed slightly
wrong, thirty years ago, with nothing able to notice. I could not find
anything that depends on the difference. Recorded because it is the
cleanest evidence in the whole report that hidden-field rects and art
are two independent sets.

**b. What `field0_0x0` is for on the main menu.** Each button loads
three entries; `field1_0x4` is drawn on hover and `field2_0x8` when the
button is unavailable, but **`field0_0x0` is loaded and never drawn**
in `mainmenu.cpp`. The normal state is already in the background, so
the most likely reading is that it exists for a redraw path that is not
taken any more — but I did not find a caller, and "probably vestigial"
is not a finding.

**c. Whether any screen shares a scroll bar.** I found none —
`FLT1::Fill_FltScrn_Scroll_Bar_` branches on `_current_screen` and
draws its own gradient, which means it serves at least two screens
through one function while still living in a screen's own file. That is
a borderline case for the order's "shared if found in at least two
screens" rule and I have counted it as *not* shared, because it is not
callable as a building block. If Data reads that differently, the
function is the place to look.
