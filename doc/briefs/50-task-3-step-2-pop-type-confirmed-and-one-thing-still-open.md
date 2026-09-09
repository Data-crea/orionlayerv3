Task 3, step 2 — pop type confirmed, and one thing still open

Read doc/v3_fundament.md first. Nothing here writes screen code. Step 3 (the design pictures) follows the drop-target rebuild, not this task.

1. The evidence files

Two screenshots are in /home/data/natives: the colony screen of Urna Prime, where the game labels the sprites "Native farmers", and the native list screen showing Urna I. Both from the loaded fixture_natives_3502.5.GAM.

Move them to the fixtures directory beside the saves and enter them in the README: which save, which colony, what each one shows. They do not go into the repo — a screenshot from the player's game is the same category as the savegame. Report the new path.

2. Nibble 9 = native — CONFIRMED, three sources
the data: Urna I holds four pops, 1 × nibble 0 and 3 × nibble 9
the list screen: the farmers column shows four sprites, three of them drawn differently — the same three-to-one split, same column
the colony screen: the game names them itself, "Native farmers"

Record it where the mapping is used, with all three sources named. This is the first pop-type value in the tree that has two independent sources in the sense of decision 23.

3. The Joes item moves from noticed to established

Colony_Has_Natives_ tests nibble 8. With nibble 9 confirmed as the native marker, that function tests the wrong half. Rewrite the item in doc/orion2re_open_fixes.md accordingly: the symptom, the three sources, the save it is reproducible in (by name and sha256, not by path — the file is Data's).

State in the item what the consequence is for the engine, or that it has none as far as the source shows. A bug report that cannot say what breaks is a report somebody has to investigate before they can act on it.

4. What stays unverified

No pop in this save carries nibble 8 or the conquered bit. Colony_Pop_Anim_ can draw four classes; this save witnesses two.

So the UNVERIFIED marking planned for Task 4's identity marks comes off by half: confirmed for 0 and 9, open for 8 and conquered. Write it that way — in the module, in the status document, and in whatever check carries the marking. "Partly verified" stated precisely is a different thing from "verified" with a footnote.

5. Zhadoom III — name it, do not solve it

The step-1 report noted the original drawing visibly different sprites in one job column there, and the data rules identity out: all 14 pops carry nibble 0. The second screenshot shows the farmers column looking uniform, so the earlier observation may have been about something else entirely, or about a different column.

Put HD and native side by side from one snapshot for Zhadoom III and say what the original distinguishes there, if anything. Candidates from the source are the shadow farmer for unused farm capacity and the darkened scanned pop — read, do not guess, and if the answer is "nothing, the earlier observation was mistaken", that is a fine answer.

Do not build it. If it turns out to be the shadow farmer, that is a Task 4 candidate: the original shows unused farm capacity in the row and our row shows it nowhere.

6. Reproducibility

Check whether the colony-screen evidence falls out of colony_move_hd.py rather than out of a screenshot somebody kept — the native frame comes from the snapshot either way, and the tool already composes both halves. If it does, say so; the two uploads are then a bridge, not the record.

Stop

Report: the new evidence path, the three-source record, the rewritten Joes item, the half-marking, and the Zhadoom III answer. Smoke green under SDL_VIDEODRIVER=dummy. d7abb22 is still unpushed — show the full diff; Data pushes.

Next after this: the drop-target rebuild (the seam rule is answered; the open question is whether "unreachable" meant only on a cell). Then step 3, the pictures.