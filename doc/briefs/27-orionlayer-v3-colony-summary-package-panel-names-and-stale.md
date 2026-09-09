OrionLayer v3 — Colony Summary, package "panel names and stale markings"

READ FIRST: doc/v3_fundament.md. Decisions 3, 14, 15, 43 (withdrawn) and
the "an unmarked deviation is a bug" rule all apply below. Do not modify
anything outside this repository. Do not run git push.

All line numbers below were read in the clone at 0907b63 and in orion2re
1.60.0 (src/version.h, consts.h:43). Verify each one before editing; if a
line has moved, fix the citation in the same commit.

CONTEXT
A live side-by-side of the HD screen against orion2re 1.60 was measured on
4 September 2026. The allocation tracks match the original's three pop
columns on all ten rows, filled and empty cells both, and the six sidebar
values match exactly. Nothing in the drawing is wrong. What the comparison
found is one mis-derived box name and four places where the tree documents
a state it no longer has.

=== COMMIT 1 — the galaxy inset hole is the third one, not the second ===

EVIDENCE. The original draws its small galaxy map with
  COLSUM::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d, 0x80, 0x5b,
                               0, 0, 0, 0, 3, 0)      colsum.cpp:415
and the signature (movebox.cpp:4-9) reads those four as
x_base 380, y_base 349, width 128, height 91. Second, independent source:
COLSUM::Colsum_Connect_Galaxy_Map_Stars_ passes the same four numbers to
MOVEBOX::Get_Galaxy_Map_Star_XY_ (colsum.cpp:734-735).

Scaled to the reference area (x*3, y*2.25) that native rect is
(1140, 785, 384, 205), centre x 1332.

The three bottom cutouts in screens/colony_summary/boxes.json have centre
x 330 (output_panel), 809 (galaxy_inset) and 1281 (spare_panel). The hole
that matches the original's map is the one currently named spare_panel.
The one currently named galaxy_inset covers native x ~193-347, which is
where the original draws its production and morale sprite column
(Draw_Colony_Wee_Prod_(..., 106, y_pos, 366, 20), colsum.cpp:1171-1176) —
and output_panel already draws those values. That hole is the spare one.

The wrong name is not a typo: tools/frame_holes.py:58 assigns
PANEL_KEYS left to right and nothing ever checked it against the source.
This is the same failure as the field dump that labelled _races_button
"Research" (fundament, "A field dump is not documentation").

TASK 1.1  tools/frame_holes.py
  - PANEL_KEYS (line 58) becomes
        ["output_panel", "spare_panel", "galaxy_inset"]
  - Update the module docstring (lines 18-20), which spells the old order
    out as "output / galaxy inset / spare".
  - Add one comment above PANEL_KEYS carrying the evidence: colsum.cpp:415,
    native (380, 349, 128, 91), reference centre x 1332, and the note that
    the order is left to right so the map is the RIGHTMOST of the three.

TASK 1.2  regenerate the boxes
  python tools/frame_holes.py screens/colony_summary/assets/frame.png --write
  Then check the diff: boxes.json must change in exactly two places per
  resolution — the rects behind "galaxy_inset" and "spare_panel" swap. Both
  stored resolutions carry identical reference rects today, so both must
  change identically. If any other rect moves, stop and report; that means
  the frame PNG or the regenerator changed something else and this package
  is not the place to absorb it.

TASK 1.3  tools/smoke_test.py — assert the RULE, not the instance
  Insert after the existing colony_summary cutout block (around line 948,
  after the seven sort cutouts are checked, before the native click point
  block). Do NOT hardcode which box is which:

  - compute REF = the reference image of the native rect (380, 349, 128, 91)
    using REF_W/640 and REF_H/480 from core.config, with the native numbers
    written as literals next to the colsum.cpp:415 citation;
  - of the three boxes in fh.PANEL_KEYS, the one whose centre is nearest to
    REF's centre must be named "galaxy_inset";
  - assert the margin is decisive, not marginal: the nearest must be closer
    than the runner-up by at least 200 reference px. Today the numbers are
    ~51 against ~522, so a frame redrawn with three evenly spaced holes
    would fail this rather than pass by a pixel.
  - close with ok("colony_summary galaxy_inset is the original's map hole")

  Verify the check bites: put PANEL_KEYS back in the old order, confirm the
  smoke test fails, restore. Report both outcomes.

TASK 1.4  screens/colony_summary/layout.json, "panels" block (line ~150)
  The _note names galaxy_inset and spare_panel as "still fill only". Keep
  that, but say which is which now: galaxy_inset is the original's map hole
  (colsum.cpp:415) and spare_panel is where the original draws its
  production column, which output_panel already answers for. The two
  empty-string entries at lines 153-154 keep their names; only the note
  changes. ONE PANEL PER STEP still holds — this commit draws nothing.

COMMIT 1 MESSAGE: state that the name was derived by position and is now
derived from the source, with the colsum.cpp:415 citation in the body.

=== COMMIT 2 — four stale statements ===

None of these changes what is drawn. Each is a place where the tree says
something that was true and is not.

TASK 2.1  screens/colony_summary/screen.py, module docstring
  (a) Line 13-16, the box list: output_panel is still tagged
      "HD EXTENSION, see below (later)". Decision 43 is WITHDRAWN and the
      same docstring says so 60 lines further down. It is a TRANSCRIPTION
      (COLSUM::Draw_Colony_Scan_Info_, colsum.cpp:1155). The box list is
      the first thing anyone reads, and a wrong marking is worse than none.
      While you are there, give galaxy_inset and spare_panel the roles
      commit 1 established.
  (b) The paragraph beginning "Stacking the label above its value is a
      deviation too" (lines ~55-65) is settled and acted on since
      2 September: the two prefixes are justification codes (1A 30 / 1A 31),
      the renderer draws label-left / value-right, and what remains open is
      the WIDTH (decision 44), not the alignment. Replace it with two
      sentences pointing at colonyempire.value_column.__doc__ and
      colonyempire._justify_note. Do not restate the argument here — one
      home, per the fundament.

TASK 2.2  screens/colony_summary/colonylist.py — the geometry fallbacks
  Line 175-176 and 329-330 read the config with defaults:
      bar_height 30 (current), row_height 60, pad_y 12.
  layout.json ships row_height 58, pad_y 14, bar_height 30. 60 is not a
  stale-but-harmless number: layout.json's own _row_height_note records
  that 10 x 60 = 600 leaves 5 px and clamps the "{count} more not shown"
  line over the last row it exists to account for. The rejected value is
  the fallback, in two copies.

  Remove the fallback for row_height, pad_y and bar_height — read them as
  cfg["row_height"] etc., so a missing key raises instead of silently
  drawing nine rows. These three carry the ten-row arithmetic; an absence
  shaped like a result is exactly what the fundament refuses. Leave the
  cosmetic defaults (pad_x, name_width, fonts, gaps) as .get(), but pull
  their values in line with layout.json (pad_x 22, name_width 236) so the
  file does not hold a second, contradictory copy of the geometry.

  Add one comment at the first of the three saying WHY there is no default:
  cite _row_height_note and the 58/60 argument in one line.

  If a smoke check or tools/colony_list_preview.py builds a config dict
  by hand without these keys, it will now fail — fix the caller, do not
  restore the default.

TASK 2.3  the 62/34 numbers
  row_height is 58 and bar_height is 30 since the tenth row landed. Three
  places still quote the old pair:
    - screens/colony_summary/colonylist.py:47  "a row is 62 px"
    - screens/colony_summary/colonybuild.py:160 "row_height 62 against
      bar_height 34"
    - screens/colony_summary/layout.json:193, _no_farming_note, which
      computes the 28 px band from 62 and 34 — twelve lines above
      _row_height_note, which documents the change to 58 and 30.
  The conclusion (28 px, split 14 above and 14 below) is unchanged in all
  three; only the operands are wrong. Correct the numbers, keep the
  arguments. Do not delete _no_farming_note.

TASK 2.4  v3_projektstatus.md
  Same pair in the paragraph "What the second line owes, if it stays"
  ("a row is 62 px"). Correct it, and add this session's entry in the
  file's own one-line-each style: the live side-by-side confirmed ten of
  ten allocation tracks and six of six sidebar values against orion2re
  1.60; the galaxy inset hole was named by position and is now named from
  colsum.cpp:415; and four stale statements were brought back in line.

=== VERIFICATION BEFORE YOU REPORT ===
  - python tools/smoke_test.py passes, and report the check count before
    and after (it was 54+; commit 1 adds one).
  - The two commits are separate and each one passes the smoke test on its
    own. Commit 1 must not contain any of commit 2's edits.
  - git diff --stat for both commits in the report, plus the diff of
    boxes.json in full — it is two swapped rects per resolution and
    nothing else, and that is the one thing I want to read rather than
    take on trust.
  - Do not push.

=== WHAT YOU MAY SKIP, AND WHAT IT COSTS ===
  - TASK 1.3 (the smoke check): NOT skippable. Without it the rename is a
    second opinion, and the next regenerated frame reassigns the names by
    position again.
  - TASK 2.2 (the fallbacks): skippable if it drags a caller rewrite in
    with it. Cost: a mod or tool that supplies a partial `list` block
    silently gets row_height 60 and loses the tenth row. Report it as
    deferred rather than dropping it quietly.
  - TASK 2.4 (status document): skippable within this package, but then
    say so in the commit body — an undocumented session is how the status
    file and the tree drift apart, which this project has already paid for
    once.