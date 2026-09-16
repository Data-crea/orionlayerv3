Work order 123 — game-menu fit, frame edge, protocol line, eta proof (16 Sep 2026)

Follow-up to 122. Four items, separate commits. Push stays with Data. Data's own OrionLayer is running right now: it must be closed before any live run, and Claude Code says so in the report when it starts one.

1. Confirmation and warning inside the octagon (Data's decision)

Data decided: both boxes are drawn INSIDE the frame opening, not over it. They are wider than the opening in native coordinates (313 and 331 against 279), so they get scaled to fit the opening's width at every resolution. This is a deliberate HD deviation from the original, where the box is screen-centred and overhangs the popup:

mark it in gmframe.py / gmdraw.py (docstring: HD DEVIATION, original size and reason), amend decision 69 with one sentence, note it in the status document;
scale the box, not the text metrics independently: font size and button size follow the same factor so the layout is the original's, smaller. Text still goes through Style.render_text (decision 30). Check that the wrapped question does not gain a line at 1080p; if it does, report before touching the wrap width;
the box is centred in the opening horizontally and keeps its original vertical position relative to the popup;
what NO / cancel shows afterwards is taken from the original, not from Data's wording: read loadsave.cpp (the fields from Add_Game_Popup_Fields_) and the quit path and say which screen state the game returns to. Match that. If it returns to the menu, the menu frame is already there and nothing extra needs drawing;
smoke check: both boxes have 0 px outside the opening at 1080p, 1440p, 2160p — replaces the "reports the numbers" check from 122.

Acceptance: live screenshots of both boxes at three resolutions beside the native image; smoke green; decision amended.

2. Frame top edge 1–2 px above the window at 1080p

Find the rounding — it is in the scale factor or in the anchor arithmetic, not in the artwork. Fix it so the frame's top row is at or below y=0 at all three resolutions, without moving the opening off the popup anchor. Say which expression it was.

3. Live-protocol line (Fundament, Working principles / Diagnosis)

Add one rule, from the CLOSE incident in 122 (scrapped colony base on the scratch save through repeated blind clicks): an injected click on a live game is followed by a framebuffer read before the next one. Two clicks without a picture in between is a blind sequence, and the game may have moved under the second. Put it under Diagnosis next to "A wait needs its traffic", and add the incident as the source in one sentence. Also add the scratch-save fact to the status document: in SAVE4/SAVE5 the Scout stands at Zin, not at Sol, and a click on the own star cancels the order.

4. eta proof: two consecutive turns of ONE flight

The 122 run got two exact digits from two different flights. The acceptance was two consecutive turns of the same flight, and the two-turn reference route ended under a star.

Find a route in SAVE4/SAVE5 of at least three turns so that turns 1 and 2 both end in open space. Say which ship, from where to where, and how many turns the original reports. If the scratch save has no such route, say so and stop — Data will provide one; do not create a new scratch save.
Protocol as before: one instance, SAVE4/SAVE5, SAVE1–9 hashed before and after, SAVE10 logged, every click with a picture (item 3).
Table: (turn, turns_left from framebuffer read, digit HD drew, match). Two consecutive rows of the same flight, both matching.

Acceptance: the table; smoke unchanged; SAVE hashes identical. Commit only the evidence pointer and the status-document line — no code change is expected here. If a code change turns out to be needed, that is a finding: report it, do not fold it in.

Report

Same order as above. For item 4, if it could not be done, the reason in one line under "braucht Datas Hand". Still open and not to be touched: scroll bar, Part C, Open Fix 14/15/19, right-click in the save dialog, colony_move_hd.py import error, research readout ("500 RP" vs "~16 turns").
