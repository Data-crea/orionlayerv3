The _value_column clamp is a DEVIATION and must be marked as
   one, not left as a caveat in a report. It fires at every
   resolution, so the shipped column is always 286 ref px where
   the original's proportion is 312. Mark it in the module, in
   v3_fundament.md, and in a smoke assertion that fails if the
   native number stops being carried alongside the clamped one.
   Do not touch frame art. If the cutout is ever widened, the
   clamp should stop firing on its own.

2. Correct the fundament entry on \032 vs \033. Both my readings
   were wrong and in opposite directions; what caught it was
   strings.cpp:22-24, a THIRD definition of the same two symbols
   with the answer in a comment. The lesson is not about octal:
   the symbol is defined three times in three namespaces, and I
   grepped one site and called it the definition. That is the
   "name table in three files" rule, so file it there.

3. Next screen piece, and it is a transcription job -- read the
   source before designing:
   - the seven sort buttons: which comparator each maps to, the
     active-header reset (_first = 0), and that Switched_cmp_
     has no direction toggle
   - the ten-row window: _list_col[10], Update_First_(10, ...),
     the click loop i < 10, row y = slot*31 + 38, and that no
     clickable area exists outside it
   - the scroll field appearing only at >= 10 colonies and
     renumbering every field after it
   Document each with file:line from YOUR 1.60 tree before any
   HD layout work. Numbers I have given you are 1.31 and must be
   re-read, not copied.

4. Then implement the sort bar only -- not the scrolling. One
   piece verified before the next.

Commit each of 1-2, 3, 4 separately. Data pushes.