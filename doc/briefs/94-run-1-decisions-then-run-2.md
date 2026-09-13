1. #1 = BC (coin), #2 = food (corn), #3 = industry (pickaxe),
   #4 = research (test tube), #5 = normal morale (green, laughing),
   #6 = low morale (brown, sad).
2. Background: flood fill from the sheet border, any channel >= 2
   counts as icon, enclosed black stays.
3. Eyes and mouths stay black.
4. The sheets have a pixel look but no true grid (like the planet
   sheet): downscale ONCE with Lanczos to the native size from the
   brief's icon table, save that as the asset, scale from there
   with the figure path. Report the native sizes chosen.
Continue Run 1 as the brief says.

---

1. (b): the icon is a row label here, not a counter. Sign picks the
   mask (negative = low, else = normal), morale ÷ 2 = 0 shows the
   normal mask. Unification: icon follows the MORALE row — if the
   row prints, the icon prints.
2. DEVIATION, with the 12 Sept table's INVENTION reserved for the
   bars that were not built.
3. Confirmed: output.icon_size 31, output.icon_gap 8, source note
   beside them. Decision 56.
Continue with Run 2.
