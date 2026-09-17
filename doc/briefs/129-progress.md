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
