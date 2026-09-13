Colony Summary: the list palette from Data's table, RETURN at the sort buttons' font size, and the scan box's paragraph and disc as boxes.

Brief 95. Chat session 13 September 2026. Three parts, one package, three stops. Line numbers are yours to establish; nothing below asserts what a file contains, only where to look.

Read doc/v3_fundament.md first. Highest decision is 56 as of commit f841e12; take the next free number yourself before filing.

Data's colour table is doc/briefs/95-palette.png, copied beside this brief. The values, verbatim:

Element    Hex
panel base    
#080E17
row A    
#0A121E
row B    
#111E2E
separators    
#29394C
hover    
#18345A
selected row    
#182B72
header background    
#09111D
header text    
#79A8E8 (Data's table says "ca.")

Row A/B alternate down the list: A, B, A, B.

Part A — palette
What is transcribed and what is not

The status document (entry "Data's planet discs, and what else the mockup asks for", 12 Sep, table row "Row highlighting") records that the original has no row backgrounds, no hover and no lit row: the only Fill_/Line_ calls in colsum.cpp are the scroll thumb's, and the only per-row state is the NAME's colour (Set_Colony_Font_To_Blue_). That row said the lit row needs Data's call. Data made the call in this session: alternating rows, a hover with a visible effect, and a filled selected row are wanted. All three are therefore HD EXTENSIONS and must be marked as such — in the module that draws them, in colors.json next to the keys (the existing _row_name_note and _output_separator_note show the form), in the status document, and in a smoke-test assertion that fails if the marking disappears.

Header background, header text, panel base and separators are colour choices in the project's own palette (decision 34 territory), not transcriptions either; they need the source note but no extension mark.

Stop 1 — report, no code
Where do the list rows get their background today — one fill for list_area, per row, or nothing but the panel? Name the module.
Does the list react to the mouse at all today (any hover state, any mouse.pos() read in the row renderer)? If not, name where a hover would have to be computed so that render and hit-test share one geometry (decision 5).
What is the selected row? The intended source is the scanned colony — the same state that brightens the name and fills the scan box. Confirm from the code that this is one variable and name it. If there is any second "selected" notion on the screen, say so.
Which existing keys in colors.json → colony_summary does Data's table replace, and which are new? Propose the key names. Watch for keys that the sort bar or the scan box read as well — a changed panel_background reaches every panel on the screen, and the table's "panel base" may or may not mean all of them. List every reader of each key you intend to change.
Does the F5 editor edit font_size? (Needed for Part B.)

Stop and report. Data decides on the key mapping and on whether the panel base applies to all panels or the list only.

Stop 2 — implement
Keys in colors.json only; no RGB literal in code (decision 14, 15).
Rows alternate A/B by list index, not by colony index — sorting and scrolling must not break the stripe.
Hover: the row under the pointer via core.mouse.pos() (the letterbox lesson in screen.py's render comment), never pygame's raw pointer. Hover and selected on the same row: selected wins.
Selected fill is driven by the scanned colony and nothing else, so the fill and the bright name can never disagree.
Separators between rows use the separator key.
Header: background and text keys.
File the decision (next free number, group "Sizing and artwork" or "Structure" — your call, say which and why).
Smoke test: asserts the new keys exist in the default skin, that the HD-extension marking is present in the drawing module, and — assert the rule, not the instance — that no row-background colour literal exists in screens/colony_summary/.
Part B — RETURN font size

boxes.json gives return a larger font_size than the seven sort buttons. Data wants it equal to theirs. Change it at every resolution list in boxes.json, not one. Then re-run the existing "RETURN is an opaque plate" check (status document, twelve-size table) and report whether the word still fits with HIGHLIGHT_PAD per side at all twelve sizes; if the box now has visible slack, say so — do NOT resize the box, Data moves it.

If Stop 1 item 5 says the F5 editor already edits font_size, still do the change in the file; mention in the report that Data could have done it in-game, so next time he knows.

Part C — the scan box paragraph and disc as boxes

Today colonyoutput computes the paragraph's x from panel padding plus the disc's width plus planet_disc_gap, and the disc's position from the padding. Neither is a box, so neither is F5-draggable. Data wants both draggable.

Constraint that outranks convenience

The disc image must stay moddable. The disc is loaded by climate through colonyplanets and resolved through core/resources.py (decisions 16, 17): a mod replaces the skin directory and gets its own discs. The box gives position and size ONLY. It must never carry an image path, and the editor must never write one (decision 19 — the editor saves to the base project, and a path in boxes.json would turn a per-skin asset into a base-project constant). Check that the existing pannable-image box (decision 4) does not smuggle a path in; if it does, this needs a box that references the image by role ("planet disc of the scanned colony") and lets the renderer resolve it.

Stop 3 — implement
Paragraph: a text-skin box (decision 37) inside planet_info. Template stays in layout.json (info_paragraph); the rendered string is set on Box.text at runtime and is NOT serialized. The word wrap must keep measuring by rendering (decision 30) — check where the wrap width comes from now and make it the box's width.
Disc: a box inside planet_info giving rect only; image resolved as today. Aspect: the disc is square — decide whether the box enforces that or the renderer fits the disc into the box's shorter side, and say which.
Both boxes at every resolution list, placed so that the first screenshot matches the current picture — this brief is about making them movable, not about moving them.
The red-on-negative-growth colour (transcribed, colonyoutput) still applies to the whole paragraph via Box.text_color.
Smoke test: the two boxes exist at every resolution that defines planet_info; neither box carries an image path or a text value in boxes.json after an editor round-trip (load, save, diff).
Then delete the padding/gap arithmetic that the boxes replace, and planet_disc_gap if nothing reads it any more — full-project grep first.
Runs and reporting

Run 1: Stop 1 report. Run 2: Stops 2 and 3 after Data's answers, smoke test green (SDL_VIDEODRIVER=dummy), screenshots at 1080p and one other resolution beside the last native screenshot of this screen. Report the one check that would break a fresh clone (new keys missing from a mod skin that copies the old colors.json? — check whether any shipped mod does) before Data reads the diff. Push is Data's.
