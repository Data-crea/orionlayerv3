# Work order 129 — parked for Data

Only what goes beyond Stop 1's own report. Each answerable in one line.

## 1. A click in OrionLayer's window cannot answer the two dialogs (part B)

**What:** with 52 or 53 up, OrionLayer draws the original picture but
`App._handle_click` forwards a click to the game only in render_mode
"original" (F12) — the dispatcher's fallback does not forward at all
(main.py:217-225). **Why yours:** it changes what the fallback IS — a picture
or a usable view. **Options:** (a) the fallback forwards clicks the way F12's
mode does (one condition in `_handle_click`), and every dialog HD has no
screen for becomes answerable in its window; (b) leave it, and the player
answers in the game's own window as today; (c) (a) plus a visible hint that
the picture is the game's. **Meanwhile:** unchanged, and reported in
`doc/research_screen_stop1.md` §5. **Answer:** a / b / c.

## 2. Choosing a research through an injected activation is unreliable (part B)

**What:** the commit takes the entry under the game's POINTER
(tech.cpp:354-369), not the activated field. Three occasions: a field
selected, nothing selected, and — with a real `INJECT_CLICK` — a different
field. **Why yours:** the fix is option (c) of `doc/tech_change_reading.md`
§5, a second change to orion2re, which this order did not authorise.
**Options:** (a) option (c), a small ORION2RE_EXT insertion that marks the
activated row as selected before it is evaluated; (b) HD drives the list with
`INJECT_CLICK` only, with the focus caveat of open fix 3; (c) HD sends
nothing into the list at all and the player answers in the game's window (the
state today). **Meanwhile:** (c) is what the tree does. **Answer:** a / b / c.

## 3. The two spec gaps the research screen needs (part E)

**What:** `tech_applications[212]` (@379, no verified source) and the runtime
derivation of `s_tech_field_data.tech[4]` (techinit.cpp:444-474). Without
them the offered CHOICES cannot be reconstructed, only the offered FIELDS.
**Why yours:** it decides whether the first research build reads its rows off
the FIELD_LIST or off the wire. **Options:** (a) verify both (header compile
plus a live read, as `tech_fields` was verified today); (b) build against the
FIELD_LIST's own rows and postpone. **Answer:** a / b.

---

**Closing state, 17 September 2026: three items.** Nothing on this list was
acted on. Nothing was pushed in either repository.
