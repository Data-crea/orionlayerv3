# Work order 128 — progress log

One line per finished part, appended before the next starts (126's rule 9,
which applies here unchanged). Baseline: smoke **197**, exit 0, orionlayerv3
at 90b9f76; orion2re `orionlayer-local` at 7067c366.

Noted at filing: work order 125's file is still missing from `doc/briefs/`;
Data supplies it, nothing is reconstructed here. And a conflict between the
order and the tree: "NOT IN THIS ORDER" names Open Fix 22 as a colony-view
patch, but in the tree open fix 22 IS the screen-6 synthetic id that part B
decides (filed by 126 G). Part B is carried out as decided; the tree's open
fix 22 is what it implements.
- **A** — done, no difference. SAVE4 (3509.0) loaded from the main menu
  before each run, the game restarted between them. The same eleven steps
  through the real `main.App` (star click on Sol, ESC, wheel in x3, wheel
  out x3, right-drag pan, key 0, click on the own fleet, ESC, GAME menu
  open, ESC) on a copy at 5e62885 (before 126 F) and on HEAD: sends with
  arguments, screen id, overlay and field count identical at every step.
  Framebuffers differ by 21-71 px, all inside the animated Zin travel line
  and a map spot at x 564-575 (`evidence/work_order_128/A_framebuffer_diff.txt`,
  A_preF/, A_HEAD/). Part F stands. Smoke 197.
- **B** — done. Reproduced live (RACES: game 6 / Race Relations, HD
  select_race). orion2re 3305d78c: race selection reports 51. OrionLayer: table,
  select_race 51, locks, version_check marker + enum maximum, docs, open fix 22
  APPLIED, rule check (red twice). Live after: custom and stock New Game paths
  end to end; RACES falls back to the framebuffer. Stock-accept "leak": kept,
  now 51 and load-bearing for Empire Identity. Smoke 197 -> **198**. SAVE1-9
  and 11 identical; SAVE10 rewritten by the new games (logged).
- **C** — done. Guard by live list shape (`mapboxes.live_field`, extracted
  from the map cancel; `layout.json` `zoom_out_field`), index read live,
  `ZOOM_OUT_FIELD` gone. Smoke 198 -> **199**, red with the old guard. Live:
  the fault not reached (the game's own map was not zoomed in, so nothing to
  park); my driver sent ACTIVATE_FIELD 1 into the research prompt on a stale
  reading and orion2re segfaulted in TECH::_Tech_Select_ — the reading's
  null-dereference confirmed; open fix 23 (observation). SAVE1-9, 11
  identical; SAVE10 the turn's autosave.
