Brief 95, Run 2: Data's decisions on the Stop 1 report, then Stops 2
and 3 ("Colony Summary: the list palette from Data's table, RETURN at
the sort buttons' font size, and the scan box's paragraph and disc as
boxes").

First, the picture: copy `~/Downloads/95-palette.png` to
`doc/briefs/95-palette.png` and report its sha256 and pixel size. Data
downloads it there before you start; if it is not in `~/Downloads`,
stop and say so.

## Decisions (Data, 13 Sep 2026)

1. **Hover: option (a).** The row under the pointer is the scanned
   colony already (transcribed from colsum.cpp:880-890), so it gets
   `row_selected` #182B72 and there is no separate `row_hover` key.
   Note in `colors.json` and in the module that the table offered a
   hover colour and why it has no key.
2. **Panel base applies to every panel.** Change the existing
   `panel_background` to #080E17; no new key. The galaxy inset keeps
   its black override.
3. **Separators = the existing cell outlines**, recoloured to #29394C.
   `plate_outline` moves from its code default into `colors.json` →
   `colony_summary`, and the code default goes (decision 14). The
   output panel's own line (`output_separator`) stays as it is. Fix the
   colonylist comment that claims header and cells share one key.
4. **Keys:** `row_a` #0A121E, `row_b` #111E2E, `row_selected` #182B72,
   `header_background` #09111D, `header_text` #79A8E8. `label` is not
   touched. `render_fills` gets a per-panel fill so the header can
   differ from the panel base.
5. **Cleanup, in this run:** remove the dead `nav_background`
   (full-project grep first); move `galaxy_inset_fill` from
   `layout.json` to `colors.json`, updating its reader.

## Stop 2 — as in brief 95, Part A

Row A/B alternate by list index. Selected fill under the name colour
change, never disagreeing with it (one variable,
`Selection.colony`). HD EXTENSION marking on the row fills in the
module, in `colors.json` notes, in the status document, and asserted
by the smoke test. File the decision under the next free number
(57 unless something landed since) — the row fills, the header
colour, and why a hover key was deliberately not added.

Smoke test additions: the five new keys and `plate_outline` present in
the default skin; no `nav_background` anywhere; no colour literal in
`screens/colony_summary/` for a row background or plate outline
(assert the rule, not the instance).

## Part B — as in brief 95

RETURN `font_size` to the sort buttons' value in both resolution lists.
Re-run the "RETURN is an opaque plate" check at all twelve sizes; report
fit and slack; do not resize the box.

## Stop 3 — as in brief 95, Part C

Paragraph as a `text`-skin box, disc as a rect-only box, both inside
`planet_info`, both resolution lists, placed to reproduce today's
picture. No image path in `boxes.json`, ever; the disc stays resolved
by climate through `core/resources.py`. Editor round-trip test as
written in the brief. Delete the replaced padding/gap arithmetic after a
grep.

## Reporting

Smoke test green under `SDL_VIDEODRIVER=dummy`. Screenshots at 1080p
and 1440p beside the last native screenshot of this screen. Before
Data reads the diff: name the one check that would break a fresh clone
— first suspect is a mod skin whose `colors.json` predates the new keys;
check whether any shipped mod carries one. Push is Data's.
