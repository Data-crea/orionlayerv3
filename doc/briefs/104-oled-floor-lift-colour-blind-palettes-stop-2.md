Brief: OLED floor lift and colour-blind palettes in the Game Settings screen

Intended part: two extra rows at the bottom of the HD Game Settings screen (GAME → SETTINGS, the settings node of the screens/game_menu/ overlay from d5e29dd), holding user settings that the game itself knows nothing about.

Both features are HD EXTENSIONS. MOO2 assigns its eight player colours fixed, and it has no user-adjustable floor. Mark them where the fundament says marked inventions live: the module docstring, the status document, and a smoke test that fails if they silently disappear. Fundament entry: decision 63.

Stop 1 is done (report of 14 Sep, 19:39). This is the Stop 2 order.

Scope

In:

Game Settings screen gains a divider, a small "OrionLayer" heading and two rows: map floor lift and player-colour preset.
core/usersettings.py + user_settings.json (ignored, never shipped).
Second player-colour preset (Okabe–Ito, black replaced by white).
Banner colour literals in core/banner.py moved into the palette.
palette.init takes the preset as an argument.

Out:

Any change to how the thirteen engine rows work.
A colour picker. Per-entry editing is by editing the JSON.
A slider. Floor lift is a three-step toggle (Off / Light / Haze).
Alternate star sprites.
Decisions (Data, 14 Sep 2026)
Rows go into the existing overlay's settings node. Nothing about the overlay's engine path changes.
Name: core/usersettings.py, file user_settings.json, in .gitignore. settings.json and core/structs/settings.py stay what they are.
The preset swaps all four colour tables, or none: ship_*, owner_*, owner_hover_* and the banner colours. One imperium, one colour everywhere. The preset is a table of eight base RGB. Derive a table only where the current tables prove the relation: check numerically whether ship_* is owner_* lifted toward white by one constant, whether owner_hover_* is one constant lightening, and whether the banner multiplier/addition pair is constant across all eight. Where yes: derive, constant with source in the palette. Where no: that table stays explicit per preset. No guessed relation. Moving the banner literals into the palette is a prerequisite, not an extra.
Okabe–Ito with black replaced by white (255,255,255); the palette says next to the value that this deviates from Okabe–Ito and why (the original has a white player; black is invisible on the floor). Mapping over the original's banner index, each original colour to its nearest relative: red → vermilion, green → bluish green, white → white, blue → blue, yellow → yellow, orange → orange, the remaining two by distance. The deuteranopia check decides whether the result holds.
Wording in screens/game_menu/layout.json under words.
File written on ACCEPT and on overlay exit (covers ESC), through one idempotent save function. Values apply in memory immediately.
Tools and the smoke test never read the user file. palette.init takes the preset with default original; main.App passes the value from the user file, every other caller passes nothing. Signature change → full-project grep for callers.
Default floor lift is (0,0,0) and means "no lift" — the floor graphic already averages (1.7, 3.7, 7.9). Say so in the doc.
The lift is applied at exactly one point after the floor is drawn, whichever floor path ran (graphic or (4,5,12) fill).
The three lift steps are measured against the real floor, not against black. "Light" may need less than (7,10,15).
State stays separate: the thirteen engine flags keep their local copy seeded from s_settings; the OrionLayer rows read from usersettings. Two read paths, never merged.
Layout: divider, heading, two rows as four row heights below the thirteen, ending above ACCEPT at 1080p (other resolutions scale). The hotkey column stays empty for both rows.
Absent user file → defaults, silent. Corrupt file → loud log line, defaults, continue. Unknown keys are preserved on save.
Build order

Run SDL_VIDEODRIVER=dummy python tools/smoke_test.py after every step, not at the end.

core/usersettings.py: load / save / defaults / corrupt handling. .gitignore entry. Smoke test: corrupt file does not raise, path is ignored.
Banner literals → palette. Numeric checks for the three derivation questions in decision 3; report the result before writing preset tables.
Preset tables in the palette with sources. palette.init(preset=) with grep of all callers. Smoke test: eight entries per table per preset; pairwise deuteranopia distance (Brettel/Viénot) above threshold for every shipped preset; the same check on the user's table at load time as a warning, never an abort.
Floor lift in _render_map: single application point, fill plus additive blit as measured. Smoke test: step Off renders byte-identical to the pre-change map; the (4,5,12) path is lifted as well.
Game Settings rows: divider, heading, toggle row, preset row with eight swatches drawn from the selected preset, restart note shown only while saved preset ≠ active preset. Branch before row_at / send. Smoke test: click on each OrionLayer row and the gap between them sends nothing; click on each engine row sends exactly what it sent before; last OrionLayer row ends above the ACCEPT box.
HD EXTENSION markers in screens/game_menu/ and in the floor code; smoke test greps for both.
Docs: fundament decision 63; status document (inventions list; file-length exception if game_menu crosses ~300 lines — check, do not assume); brief marked done.

Deliver one package, verified against a pristine tree.
