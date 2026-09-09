cd ~/orionlayerv3

Sidebar layout. This overturns last session's OPEN item.

1. The question is settled from source: ONE row per entry, not
   two. Set_Justification_ (fmtpara.cpp:999) flushes the pending
   segment but never calls Vertical_Move_; y advances only on
   \r \n \v \f (the dispatch at fmtpara.cpp:321-333). So each
   entry is: label LEFT, then value justified mode 1, then CR.
   Justify_Line_ mode 1 adds remaining_width to the first char
   = right aligned.

   Therefore: six rows, label left, value right aligned at the
   104 px column edge. Verify all of this in YOUR 1.60 tree
   before acting -- my line numbers are 1.31.

2. Re-mark the extension. The current stacked/centred layout is
   the invention, not label-left/value-right. Change the note,
   and note WHY it was wrong: an octal 032 read as 033.

3. Implement label-left/value-right in the sidebar, matching the
   original. Right edge of the value column derives from the
   native 104 px width scaled, not from a tuned constant.
   Smoke assertion, ink-measured, at every resolution: the value
   glyphs' rightmost inked column is flush with the column's
   right edge, and the label's leftmost is flush with the left.
   Do not derive either from the same expression the renderer
   uses -- that is the tautology from 443aff1.

4. justify=3: correct the note. It IS inert, but not because CR
   terminates each line. The first \0320 overwrites the mode
   before any character is drawn, so 3 never reaches
   Justify_Line_.

5. Red_If_Negative_Fmt_String_ is UNSAFE to build on. The literal
   is "\0332" = 0x1A '2' = justification mode 2 = CENTRED, while
   the function name and its own comment say colour, and
   colsum.cpp spells the same described effect "\x1B" "2" = the
   real colour path. One of the two is a decompilation bug.
   Do NOT implement red-on-negative. Do not implement centring
   either. Render negative income exactly like positive, and
   mark it OPEN with both readings written out.
   Add it to doc/orion2re_open_fixes.md as a QUESTION for Joe,
   not a fix request: which byte does the original binary emit?
   Include the [3] vs [4] extern size mismatch of
   s_0_0055110c between strings.h and estrings.h in the same
   entry.

6. player.py is verified=True on header + static_assert alone.
   Four of the six sidebar fields have never been read against
   the game's own screen. That is decision 23 as written, but
   the docstring should say WHICH evidence stands: race and
   total_pop have incidental live corroboration, bc,
   surplus_freighters, research_produced, surplus_food and
   surplus_bc have none. Make that explicit in the spec, and
   leave the flag alone -- I am not reversing a decision while
   Data is away.

7. If time remains: the sidebar's six values still need source
   two. Have struct_probe ready to run the moment a game is up,
   and write the expected-vs-actual table so it only needs
   eyes, not interpretation.

Commit 1-6 (and 7 if reached) with docs. Data pushes.