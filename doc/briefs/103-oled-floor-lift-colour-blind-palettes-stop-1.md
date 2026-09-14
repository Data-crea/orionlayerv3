rief: OrionLayer settings menu — OLED black lift and colour-blind palettes

Intended part: two extra rows at the bottom of the existing HD Game Settings screen (GAME → SETTINGS), holding user settings that the game itself knows nothing about.

Both features are HD EXTENSIONS. MOO2 draws its map floor as palette black and assigns its eight player colours fixed; neither a lifted floor nor a swapped tint table is something the original can do. Mark them where the fundament says marked inventions live: the module docstring, the status document, and a smoke test that fails if they silently disappear.

Line numbers, field IDs and exact values are deliberately absent — Claude Code establishes those from source in Stop 1.

Scope

In:

The Game Settings screen gains a divider, a small "OrionLayer" heading, and two rows: map floor (OLED black lift) and the player-colour tint preset.
A user settings file that persists both.

Out (do not build today):

Driving the engine's own Save / Load / Settings / Quit items from HD. They stay on the framebuffer path until they get their own event-driven chain per decision 21.
A colour picker widget. Per-entry editing happens in the settings file for now; the UI offers presets only.
A separate popup or overlay. The rows live in the list that exists.
Alternate star sprites. Star colour is game semantics and stays as it is.
Decisions already taken (Data, 14 Sep 2026)
The two rows have no field ID. The click handler branches on that before the send path: an OrionLayer row changes a value in settings.py and nothing else. A click that is not recognised as one of these rows must not fall through into a generic INJECT_CLICK; the smoke test pins this.
Two state sources, two read paths. The thirteen engine checkboxes keep reading their state from the game (Stop 1 says whether that is snapshot or FIELD_LIST); the OrionLayer rows read from settings.py. Never merge the two.
Black lift is live. The value is read at draw time by the map renderer; changing it shows on the real map behind the settings panel. That is the preview — no example images.
Tint table needs a restart. Tints are applied at sprite load. A restart note sits beside the preset row, shown only while the saved preset differs from the active one, so it disappears by itself after the restart.
Preview for the tint table: eight swatches beside the preset row, drawn from the selected preset's table, so they cannot disagree with what the restart will produce.
The rows are marked on screen: a thin divider and an "OrionLayer" heading below the last engine row. The hotkey column stays empty for both — there is none. Floor control: start with a three-step toggle (Off / Light / Haze, values in the palette with their source). A slider only if three steps prove insufficient — it would be a new widget class for one use. Value changes apply in memory at once; the file is written on ACCEPT (and on screen close), not on every change.
Defaults are the original: floor (0, 0, 0), preset "original". The lift is a property of the user's display, not of the game; on a non-OLED panel a lifted floor is a grey veil.
Second preset is Okabe–Ito — eight colours, documented for deuteranopia and protanopia, citable. Source goes in the palette file next to the values.
The settings file is user data: not in boxes.json, not on the editor save path (decision 19), in .gitignore, never shipped. An absent file is a state (defaults, silent); a corrupt file is an error (logged loudly, defaults, continue). Unknown keys are kept, not dropped, so an old build does not eat a newer build's settings.
One loader, one home: core/settings.py (name open). Everything else asks it. The palette import reads the active preset from it, which means the settings file is loaded before the palette import, and that ordering is written down in the module, not left to happen.
Stop 1 — findings from source, no code

Report, do not implement:

How the existing Game Settings screen is wired. Which module renders it, how a row maps to its engine field, where the checkbox state is read from (snapshot or FIELD_LIST), and what ACCEPT sends. Where in the click handler the send happens — the branch for the new rows goes in front of it.
Layout room. The list ends at "Ship Initiative" with space below; confirm the divider, heading and two rows fit above ACCEPT at every listed resolution in boxes.json.
Where the map floor is drawn. Which function blits the star field into map_area, and is the star field surface opaque. If opaque, confirm that a rect fill in the floor colour followed by a BLEND_RGB_ADD blit of the star field produces the lift without touching the artwork. If not opaque, say so and propose the alternative before building.
Where tints are applied. Which module holds the eight-entry tint table today, in what format, and at what moment it is applied to the greyscale sprites. Confirm "at load" or correct it.
Which other colours are red/green. Sidebar status values (Food, Treasury deltas) — are they palette entries or literals. List them. Anything that is a literal is a decision-14 violation to file, not to fix silently.
Existing widget inventory. Is there anything in core/widgets close to a slider or a radio group. The third copy is the signal to extract; the first is not.
Next free decision number for the fundament entry.
Stop 2 — implement, after Data's go on Stop 1
core/settings.py: load / save / defaults / corrupt-file handling as in decisions 9–10.
Palette: second tint table with its source line; palette import selects the table via settings.
Map renderer: draw-time floor read, fill + additive blit.
Game Settings screen: divider, heading, two rows, swatch strip, restart note. Wording in labels.json (decision 15), geometry in boxes.json, text skin for bare labels (decision 37), shared geometry for render and hit-test (decision 5). HD EXTENSION marker in the screen module.
Fundament entry under the next free number. Status document lists the two inventions. .gitignore gains the settings file.
Acceptance — smoke test additions
Corrupt settings file does not crash the loader; defaults apply; a log line says so.
Settings file path is in .gitignore.
Both presets have exactly eight entries.
Pairwise distance of the eight colours in a deuteranopia simulation (Brettel/Viénot matrix) exceeds a threshold, for every shipped preset — and, at load time, for the user's table as a warning, never an abort.
A click on each OrionLayer row, and on the gap between them, produces no outgoing message on the wire.
A click on any engine row still produces exactly the message it produced before the change.
Floor lift with the slider at 0 renders byte-identical to the pre-change map (the extension is invisible when off).
The two HD EXTENSION markers are present (grep), so the inventions cannot silently vanish.

Run headless: SDL_VIDEODRIVER=dummy python tools/smoke_test.py, after every step.

Docs to update
doc/v3_fundament.md — new decision (number from Stop 1).
doc/v3_projektstatus.md — inventions list, file-length exception if the Game Settings module crosses ~300 lines (it grows by six boxes and a branch; check, do not assume).
CLAUDE.md — nothing, unless the settings-before-palette ordering turns out to need a startup note there.
