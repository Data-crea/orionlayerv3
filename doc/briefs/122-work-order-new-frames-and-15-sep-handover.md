Work order — new frames + 15 Sep handover (16 Sep 2026)

Read doc/v3_fundament.md from the clone first. Check the next free decision number before filing anything. Push is Data's checkpoint, never automatic. Result review by Data and Chat afterwards; do not wait for approval between runs unless a stop below says so.

Two runs. Run 1 is artwork installation, Run 2 is the three items decided on 15 Sep. Separate commits per item so any one can be reverted alone.

Run 1 — install both frames, correct the boxes

Both files are in ~/Downloads/ (Data's machine):

galaxy_map_frame_v2.png — 1706x922 RGBA, ten real cutouts (map, GAME hexagon, sidebar as ONE opening, TURN, six nav buttons), four outer corners transparent. Painted labels and sidebar tiles were removed on purpose: HD draws them.
game_menu_frame.png — 1108x1419 RGBA, one octagonal opening, everything outside the frame body transparent.

Both were cut by Chat with a re-implementation of find_holes (alpha < 16, MIN_AREA 2000). Treat those counts as a claim to verify, not a fact: run the real tool.

1a. Galaxy map
Replace screens/galaxy_map/assets/frame.png with the new file.
python tools/frame_holes.py screens/galaxy_map/assets/frame.png first WITHOUT --write: confirm ten holes and that the galaxy rule names them without ambiguity. Report the old and new reference rects side by side for all ten. Then --write.
The regenerator keeps non-cutout boxes verbatim (decision 3). That is exactly the problem: every hand-placed box that lives INSIDE a cutout was placed for the old master and is now wrong. Correct:
all sb_* sidebar readouts — must lie inside the new sidebar rect, spacing re-derived from the new height, not shifted by a constant;
the title text box / GAME label — centred in the new hexagon hole (the hole itself sits ~4-5 px right of the map centre in the artwork; leave the artwork, centre the text in the hole);
nav and TURN font sizes — the nav holes are ~39 px high in image pixels; check the labels still fit at 1080p and 2160p after scaling. Do this for EVERY resolution list in boxes.json, not only 1920x1080 (decision 1). Any per-resolution list that has no entries stays empty.
Sidebar contents (sb_*) and the system window / fleet box (boxmodel.py, mapboxes.py) — check nothing else derives a rect from the old frame size or from the old sidebar width. Grep for the old image dimensions (2322, 1256) and for any literal taken from the old sidebar rect.
Old frame: keep as frame_old.png? NO. Git has it. Delete.

Acceptance: smoke test green; screenshots at 1920x1080 and 2560x1440 beside a native screenshot (side-by-side rule); sidebar readouts and labels visibly inside their openings; no text clipped. Commit.

1b. Game menu

The overlay currently draws its outer panel with thin_border. The new frame replaces THAT outer panel only, the same way the colony screen took a fixed retouched image (decision of 12 Sep): plain-scaled per resolution, no 9-slice, no master, one image. Inner groupings inside the menu (lists, button rows, confirmation boxes) keep whatever skin they have unless they visibly clash — in which case report, don't restyle.

Add screens/game_menu/assets/frame.png.
Loading through core/resources.py (decision 16), never a path literal.
Size and placement: the frame scales to the menu's box, aspect preserved (1108:1419 ≈ 0.78, portrait). Decide the anchor from the original: where MOO2 puts the GAME menu relative to the galaxy map (centre of the map area, not of the window — verify in mainmenu.cpp / the screen that draws the in-game menu, and say which function). Every menu state (menu, settings, load, save, confirmations) must fit inside the octagonal opening at 1080p, 1440p and 2160p. If one state does not fit, report the numbers before shrinking anything.
Help regions (help.json) and click hit-tests are unaffected by the artwork — confirm with the smoke test, do not assume.
File a decision (next free number, group "Sizing and artwork"): fixed frame image for the game menu, plain-scaled, supersedes the thin_border outer panel on that screen only. Cross-reference the colony decision and mark the opaque fill rule from "A trick that works on one screen is not a rule" — the octagon interior is transparent, so the menu must fill its own background (opaque, no dimmed backdrop, per the popup rule).

Acceptance: smoke test green; screenshots of every menu state at the three resolutions; nothing clipped; decision filed. Commit.

Run 2 — 15 Sep handover items

Live-test protocol for anything live: exactly ONE instance on the server (Data's own OrionLayer must be closed), scratch saves SAVE4 / SAVE5, never SAVE8, hash SAVE1–SAVE9 before and after (identical), SAVE10 is autosave and is only logged. Reference case: Scout Sol→Zin or Sol→Dhira.

2.1 "eta N" arrival digit beside the travel line

Rules decided on 15 Sep, not to be re-litigated:

shown only from the next turn on (not in the turn the order is given), only for location < 20000, never during a command chain;
player's font colour;
offset from the line by the head size of the OWN sprite colour (zoomtables.SHIP_ICON_HEADER_DIM), not a hand-tuned constant;
verified live by reading turns_left machine-wise from the framebuffer (the number the original prints), NOT by eye. Rendering goes through maplines.stroke rule for the line and Style.render_text for the digit (decision 30 — the digit 4 is a blocked glyph in Bank Gothic; assert that the substitution fires). Marked HD EXTENSION if the original draws the ETA differently — check Draw_* in the map source first and say what it does before deciding whether this is a transcription or an extension.

Acceptance: live run on the reference case, table of (ship, turns_left from framebuffer, digit HD drew) for at least two turns; smoke test includes one check that the digit is suppressed during a command chain. Commit.

2.2 Icon size 9x8 — mark the deviation

SHIP_ICON_DIM stays 9x8. The line module works with the measured head size 12x11. Mark the discrepancy as a DELIBERATE DEVIATION in maplines.py (docstring), in the status document, and with a smoke check that fails if the two tables silently become equal or one of them changes without the other's note being touched. No code change to the icon itself — the click hit area is live-confirmed. Commit.

2.3 Nebula palette offset in tools/make_nebula_icons.py

The palette read from FONTS.LBX is shifted by one byte; entries are (flag, R, G, B). Fix the reader, regenerate the icons, and do the visual test: one nebula of each type rendered to PNG beside the native framebuffer of the same nebula. Report the before/after with the first three palette entries as bytes so the fix is verifiable without the game. Separate commit — this touches assets and must be revertable on its own.

Report at the end

One report, German is fine, in this order: per item — what was changed (files), decision numbers filed, smoke test count before / after, what could NOT be done and why, what needs Data's own hand (a click at the native window, a scratch save with more than nine ships). Do not describe what you would do next; list it under "offen" with the item's origin.

Not in this order: scroll bar (needs Data's big-fleet save), Part C (waits on the message-ID patch), Open Fix 14/15/19, right-click in the save dialog, colony_move_hd.py import error. Leave them listed as open; do not pick them up on the side.
