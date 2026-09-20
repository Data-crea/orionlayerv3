# 148 — parked for Data

## 1. The work order was not filed, and that is a conflict in the order

It says, first line: *"put it in the title above, and rename this file
to match. Do not leave an unnumbered work order behind."* It also says
`148-progress.md` and `148-parked-for-data.md` are **"the only repo
changes allowed"**.

Filing the work order text would be a third file. I kept the explicit
limit and did not file it, so the number lives here and in
`148-progress.md` instead. **The order text itself is still
unnumbered wherever you keep it** — it reached me as a paste, so there
was no file on this machine for me to rename.

Orders 142 and earlier were filed under `doc/briefs/<n>-work-order-*.md`.
If that should continue, say so and it is one commit.

## 2. Three files from work order 147 are still uncommitted

`git status` in the repo shows, besides this order's two briefs:

```
 M doc/briefs/README.md
?? doc/briefs/147-parked-for-data.md
?? doc/v3_original_gui_construction.md
```

That is work order 147's deliverable. It said "no changes to either
tree", so I wrote the documents and left them uncommitted, and offered
to commit them; you asked about the extraction instead, so they are
still sitting there.

**This order's acceptance asks that `git status` show only its two
brief files**, which it cannot while 147's are pending. I did not
commit them on my own initiative, because that would be a repo change
this order does not allow either. Naming the conflict rather than
picking a side: one word and they go in.

## 3. Composites beyond the Fleets screen

`_composite.png` exists for all 18 folders, but only the Fleets one
places sprites — it is the screen whose source names both the entry and
its field origin in a form I could read mechanically
(`flt1.cpp` loads FLEET.LBX 0..18 into named globals, and the
`Add_*_Field_` calls carry literal origins).

For the rest, tying a button sprite to a field position means following
each `Add_Button_Field_` call back to the variable holding its picture
and then to the `Far_Reload_Next_` that filled it. It is mechanical but
it is a per-screen read of seventeen screens, and the finding in
`148-progress.md` makes it less valuable than it sounds: the normal
state is already in the background, so those composites would come out
identical to the backgrounds they start from. Worth doing only if you
want the *dimmed* and *pressed* variants placed, which would show what
changes rather than what is already there.

## 4. Two judgement calls worth knowing about

**a. Scope per screen is the whole archive, not the proved subset.**
The order says "every LBX entry the screen's own code draws". I
extracted each screen's own archive **whole** rather than only the
entries I could prove a draw call for. Extracting the superset loses
nothing and every file carries its LBX and entry, but it means a
manifest row does not by itself prove the screen draws that entry. The
`role` column is filled only where the source names it; everything else
says `other` rather than guessing.

**b. Archive-to-screen assignment is mine, from the previous report.**
`INDEX.md`'s screen list comes from work order 147's overview table plus
the archives each screen's file loads. Where a screen loads many —
the colony screen loads nine — I assigned them all to that screen. A
few could reasonably belong elsewhere or to `_shared/`: GSTAR.LBX and
RACEICON.LBX I did put in `_shared/` because the previous report found
more than one caller, but COLPUPS.LBX and MAINPUPS.LBX are popups that
may deserve their own folders rather than living under `colony/` and
`galaxy_map/`.
