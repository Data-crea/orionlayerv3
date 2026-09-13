Answers to Stop 1 (brief 99 → renumber to 101 if that is the next free brief number; make file name and first line agree before anything else).

Planets In Range: (c) now, (a) as its own follow-up brief. The toggle drives the game; the HD list does not filter on it yet, and the screen says so in a marked gap (status document + a test that fails if the marking disappears). (b) is ruled out by decision 25: the check is reconstructable from state we can verify, so a patch is not the first move. Read the unread distance helper as part of this stop's close-out so the follow-up brief has no unknowns.
(a), extractor. HESTRNGS.LBX and the race names come from the user's install, byte for byte, decoded at load time, format-versioned, never committed — the decision-38 pattern. Our own wording only for what the original has no string for.
(c) for Stop 2. Display, sort, restrictions, row select, Return — the round trip is the acceptance. Sending ships is a second brief, and it will be (b), an event-driven chain per decision 21, not the framebuffer. Do not start it in this brief.
(a). Owner colours and the original's hover/armed highlights, keyed in colors.json. The mockup scheme is dropped.
Drop the detail panel and the coordinates. The system readout box carries the original's status line (star name, ETA, out of range, black hole, unexplored, in its colours). The bottom-left hole shows only what the row already has — disc, name, special line — larger; no computed production or research. That is layout, not data, and needs no marking beyond "HD EXTENSION: panel".
Race name only. The ship name waits for the design part of the ship spec, verified against two sources, in its own step.
Yes. Acceptance: same row set, same order between distinct keys. HD uses a stable sort; the status document notes that the original's qsort is not, so tie order may differ from the game.
Confirmed. Extract column boxes, heading plates, row bands, fills and outlines into a shared module; colonylist keeps figures, allocation track and pop moves. Full-project grep on every rename.
ETA markers and send cancel: deferred with the send brief, listed under "What is missing". The galaxy-inset star click (scroll list to that star's first planet) may be built in Stop 2 if the inset already exposes the hit star — it needs no data the snapshot lacks.

Also for Stop 3: try the restriction hotkeys 1–5 before INJECT_CLICK; if they work at HD window size, prefer them (decision 20). Availability of the two send buttons comes from the field list as you proposed.
