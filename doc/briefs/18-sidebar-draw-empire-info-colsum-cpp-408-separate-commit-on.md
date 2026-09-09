cd ~/orionlayerv3

Sidebar / Draw_Empire_Info_ (colsum.cpp:408). Separate commit on
top of 443aff1.

A. Add s_player to core/structs/unverified.py with the six
   scalars. Header source only (sizeof asserted at 3854 == 0xf0e
   against sizes.h):
     bc                  i32 @ 50
     surplus_freighters  i16 @ 56
     total_pop           i16 @ 266
     research_produced   i16 @ 272
     surplus_food        i16 @ 276
     surplus_bc          i16 @ 278
   Assert the three already-verified anchors in the same spec:
     race @ 37, traits @ 2308, tech_applications @ 379
   Record per field what KIND of number it is -- they are not one
   kind: bc is a stock, surplus_bc and surplus_food are net flows,
   research_produced is gross, total_pop and surplus_freighters
   are counts.

B. Extend tools/struct_probe.py to read those six from the live
   game and print them beside what the game shows on screen.
   That is source two. Nothing renders until it agrees.
   Note the hazard: surplus_food @276 and surplus_bc @278 are two
   bytes apart, both i16, both net, both signed-printed. Swapped,
   they look entirely plausible on screen.

C. Document, from source, with file:line provenance:
   - draw order and labels: Reserve, Income, Population,
     Freighters, Food, Research
     (ESTR 118, 106, 114, 103, 102, 117)
   - only Income and Food print a sign (%+d); the other four %d
   - entries are joined by CR, not newline: String_Builder2_
     (eric.cpp:425) appends via E_Strings_(71) = "%s%c%s" with
     c = 13
   - justify=3 is INERT here: fmtpara.cpp:1056 drops to LEFT
     whenever the next char is CR/LF/FF, so all six lines are
     left aligned. Label-left/value-right would be an invention.
   - colour attributes: \0330 label, \0331 value; Income adds
     \0332 when negative (Red_If_Negative_Fmt_String_,
     eric.cpp:176)
   - E_Strings_(12) is not in the source; two uses are both
     consistent with the empty string. Mark OPEN, single source.
   - native geometry: paragraph x520 y354 w104;
     name column x12 w89 (w87 with event) h23;
     building x512 w85 h22; row y = slot*31 + 38

D. Mark output_panel as HD EXTENSION -- in the module, in
   v3_fundament.md, and in a smoke assertion. colsum.cpp draws no
   per-colony food/industry/research at all; grep the file, the
   only two hits are the sidebar lines. The seven sort buttons
   sort by values the screen never displays.

E. Fix the stale research note: the "%" is NOT in ESTR 117
   (%sResearch: %s%d) and not in any research label. The only
   literal %% in the string table are 108, 112, 120, 121
   (maintenance, morale, worker penalty) and HESTR 0x142.
   "Absolute, no % shown" stays correct; the cited source does not.

F. Run tools/version_check.py and report what it does. Do not
   change it. This archive is 1.31: no src/version.h, no
   ENGINE_VERSION, consts.h:47 says "Version 1.31-re".
   Fundament decision 36 describes the checker as reading both
   literals with value 1.60.0.