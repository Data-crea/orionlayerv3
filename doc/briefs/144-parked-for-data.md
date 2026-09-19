# 144 — parked for Data

Questions and blockers from work order 144 (Fleets: moving ships +
minimap lines). Nothing here was worked around silently.

## 1. `workorder_fleets_screen.md` does not exist on this machine

The order says to build on it and to reference it by "next free number
/ first line". It is not in the repo, not in `~/Downloads`, and not in
the paste cache — the only recent pastes are work order 143 and this
one. Searched: `find ~ -iname "*fleets_screen*"` and every
`workorder_*.md` in `~/Downloads` (six files, none about Fleets).

**I built on the current Fleets screen alone.** If that document
carries decisions that differ from what I read out of the source, they
did not reach me.

## 2. A client was already attached — no live steps were run

The live protocol (work order 126 rule 8, restated in 140) is: before
anything connects, check that no other client is on 17362; if one is,
**stop**. One was, for the whole of this run:

```
127.0.0.1:50994 -> 127.0.0.1:17362   python main.py   pid 213166
```

It started roughly 15:41, after this session stopped its own client
(pid 209061) at 15:32, so it is **Data's own OrionLayer**, not a
leftover of mine. I did not connect, did not send anything, and did not
touch that process.

**Consequence:** none of the live acceptance could be run — no move on
SAVE4/SAVE5, no before/after hashes, no native side-by-side screenshot
of the minimap lines. Those four acceptance points are outstanding and
are listed as such in `144-progress.md`.

## 3. The move patch cannot be validated without an engine restart

Part 1 needs `MOX::_g_ship_move_info` on the wire (reasoning in
`144-progress.md`). The patch is written and committed on
`orionlayer-local`, but the running engine (pid 186620, up 5 h) was
built on 19 September at 00:02 and predates it. Since work order 140
Data starts the engine, so **a live test of the patch needs Data to
restart orion2re on the new build.**

## 4. One question I could not answer from the source

`_settings.show_relocation_lines` is at **offset 8** of `s_settings`
(nine leading `uint8_t`, unambiguous by inspection) and `settings_raw`
is already on the wire. What I could not establish is whether the
option is reachable in the game's own options screen in this build, so
I do not know whether a player can turn it off and make the galaxy
map's lines vanish while the Fleets minimap's stay (the minimap's are
NOT gated by it — see `144-progress.md`). If that asymmetry is real it
is the original's, not ours, and I would rather transcribe it knowingly
than discover it later.
