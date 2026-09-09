Task 3 — fixture, nibble, then pictures

Read doc/v3_fundament.md first. Three steps, a stop after each. Step 3 produces pictures and no opinion.

A save with mixed population is loaded. The side-by-side shows the original drawing visibly different sprites inside one job column (Urna I, Zhadoom III) where the HD row draws identical cells. That the original encodes something there is established. What it encodes is step 2.

Step 1 — make the save a fixture

Copy it somewhere stable and record it: path, stardate, and the colonies that carry mixed population by name. Add it to the acceptance protocol beside the existing reference save.

A test whose data lives only on Data's disk fails for everybody else (fundament §2, the help-file check). Anything below that reads this save reads it by its fixture name.

Stop: report the path and the colony list.

Step 2 — pop type, from the data and from the picture

Two independent sources, per decision 23 — this is the first time both exist at once.

From the snapshot: the pop-type value per pop, per colony, for the colonies named in step 1.
From the picture: what the original draws for those same pops, same snapshot, using the side-by-side tool.

Then answer, and say which of the four classes this save actually contains. If it holds no androids or no conquered pops, say so — two untested classes reported are better than four assumed.

This is also the evidence the open question to Joes has been missing: Colony_Has_Natives_ tests nibble 8 where 9 was expected. Confirm or correct it against the data, and update doc/orion2re_open_fixes.md either way.

If the nibble assignment comes out confirmed, the UNVERIFIED marking planned for Task 4's identity marks comes off — say so explicitly.

Stop: report the mapping, the class coverage, and the state of the Joes item. No pictures before this is answered — a mark drawn from a guessed mapping is a picture of the wrong thing.

Step 3 — the pictures

One pair per open design question. Same colony, same snapshot, same held state; only the variant changes. Every image carries the original half from the same snapshot.

Resolutions: 1920x1080 and one 4K.

Q1 — identity mark. Glyph/letter in the cell vs border/shading treatment. The comparison question is not which is prettier: the original's sprite colour carries profession AND race, our cell colour carries profession only. Which variant shows what the original shows there?

Hard cases, not flattering ones:

the mark immediately beside a dashed free slot (the predicted collision)
the widest row in the fixture, where cells are narrowest

Q2 — context. Inspector in spare_panel vs tooltip below the row. Render the state while a pick is held, so the drop targets are in frame and the question "does the context cover them" can be seen. For the tooltip, additionally in the last visible row, where it either fits or runs off the edge. If the tooltip variant reflows the list rather than overlaying it, it is out under decision 46 — say so and skip it.

Q3 — job band vs blocker cell. A colony with an empty middle group, held state. This is the case the seam rule in drop_targets already solves, so the picture is asking whether the permanent blocker cell earns its track width on top.

Stop: PNGs, a one-line caption per pair saying which colony and which variant is on which side, and nothing else. No recommendation, no table of pros and cons, no labels drawn onto the images. Data decides.