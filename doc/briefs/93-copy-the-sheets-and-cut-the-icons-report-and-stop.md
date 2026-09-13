Copy the three files from ~/Downloads/ (symbols.png,
normal_moral.png, low_moral.png) to
screens/colony_summary/assets/_src/output/ and mockup.png to
doc/briefs/92-mockup.png; report sha256 of each.

Then cut the icons out of the sheets:
1. symbols.png: find every separate icon (connected components of
   non-transparent / non-background pixels, merged if they touch
   within 2 px), crop each to its bbox plus 1 px, list them left
   to right / top to bottom with size and position. Do NOT name
   them yet — show a contact sheet with index numbers and stop, so
   Data assigns food / industry / research / BC (and anything
   else on the sheet).
2. normal_moral.png and low_moral.png: one icon each (the two
   morale states); crop the same way; report size. If a sheet
   holds more than one, treat it like symbols.png.
3. Background: if the sheets are on a solid colour instead of
   alpha, key that exact colour only (report it), never a
   tolerance — the icons' own dark pixels must survive.
4. Save the crops to assets/_src/output/cut/<index>.png, native
   size, plus a 4x contact sheet. Nothing under assets/output/ yet
   — that comes after Data names them. Tree otherwise untouched.
Report and stop.
