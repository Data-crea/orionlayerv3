# Work order 129 — progress log

One line per finished part, appended before the next starts (126's rule 9,
which applies here unchanged). Baseline: smoke **201**, exit 0, orionlayerv3
at 2aa6af4 (pushed); orion2re `orionlayer-local` at 3305d78c.
- **A** — done. `tools/livesend.py`; three tools moved onto it
  (colony_move_probe, game_menu_hd, zoom_probe); the ones that drive the
  product through pygame events are named in the status and left. Two
  fundament entries filed (live driver is a client; stale bytecode in
  counter-tests). Smoke 201 -> **202**, exit 0.
- **B** — done. Reading `doc/newtech_reading.md`; the finding that the game
  draws from `_current_screen` (textbox.cpp:40-50, :284), so the ids go on the
  wire only: orion2re **f838c754** (`ext::g_screen_override`, 52 and 53),
  bundle `~/orion2re_bundle_17sep_f838c754.bundle`; `doc/ext_research_screens.patch`,
  open fix 24, version_check, `core/screen_names.py`. Live: both dialogs seen
  as the original picture with HD silent, HD returns to the map by itself, and
  the choice through OrionLayer is NOT reliable (three occasions recorded) —
  reported, not worked around. Smoke **203** at this point.
- **C** — done. `core/research.py` (cost table, cost, chance, turns),
  `tools/research_cost_check.py` (run by the suite), `tech_fields` verified
  into the player spec, `hyper_advanced_tech` left in unverified.py with its
  consequence written down. Three live points reproduce the native readout
  (18, 17, and the document's 16); the chance>0 point was not reachable.
- **D** — done. `sidebar.research_readout` is the original's four cases
  through `core/research.py`; the row takes up to three lines and shrinks the
  values rather than the label; both docstrings corrected. Evidence beside the
  native frame at three sizes. Smoke **205**, exit 0.
- **E** — done, a report: `doc/research_screen_stop1.md` (the reconstruction
  validated live — 8 of 8 categories and their offered field, the choice rows
  not reconstructible yet and exactly why; the extractor plan; the twelve
  questions marked; the presentation dialog in the six headings). Parked:
  three items in `129-parked-for-data.md`. Also recorded Data's answer to
  point 5 of `126-parked-for-data.md`: the draft one-content-box rule is NOT
  filed.
- **Observation (if there was time)** — done, report only: the original draws
  the eta at the ship icon (ships.cpp:470-473) and so does HD
  (`mapeta.anchor_point`); what differs is that HD's stars are drawn larger
  and AFTER the label, so it can end up under the sprite. Nothing changed.
- **Run closed.** Parts A-E reached. orionlayerv3: nothing pushed, smoke 201
  at the start and **205** at the end, exit 0 on every commit. orion2re: one
  commit (f838c754), push URL still disabled, bundle written beside the tar
  backup. SAVE1-9 and SAVE11 identical over the whole run; SAVE10 was
  rewritten by the games' own autosaves (logged, never compared).
