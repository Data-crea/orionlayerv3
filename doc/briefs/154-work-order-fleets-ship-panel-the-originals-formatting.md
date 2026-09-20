Work Order 154 — Fleets ship panel: the original's formatting

First line for references: "Work Order 154 — Fleets ship panel: the original's formatting"

Before anything else: check the next free work-order number in the tree, put it in the title above, and rename this file to match.

Purpose

The panel now holds the right content (153) but is laid out differently from the original and reads as a wall of text. Data compared the two side by side. This order is formatting only — no new values, no new data from the wire.

What the comparison shows
Beam OCV and Beam DCV are missing in HD. The original prints them on one line, label left and value at its own tab stop, OCV in the left column and DCV in the right. HD shows nothing. Establish first why: are they absent for a hovered ship, absent always, or dropped by the layout? That answer decides whether this is a formatting fix or a content bug.
No separation. The original leaves an empty line between the head block and the Weapons/Specials block. HD runs every line together.
No indentation. The original indents the weapon and special entries under their headers. HD starts them at the same margin as the headers.
Tab stops. The original places values at fixed column positions, not after the label. Transcribe the positions it uses (the two column origins were documented in 151 B) and express them as fractions of the panel width, since the HD hole is not 305 px wide.
The task

Transcribe the original's line layout for this panel from source: the order of lines, which lines are blank, the indentation of entries, the tab stops for values, and what changes when a field is empty (no specials, no shield, no destination). Then lay out the HD panel by that transcription. Anything the original does that HD cannot do, or that HD does in addition, is marked as a deviation in the module and in the status document, as usual.

The known omissions stay as they are: the weapon plural and the red for a damaged special.

Running

Unattended, no stops. Questions go to doc/briefs/<n>-parked-for-data.md.

Acceptance: a 1440p capture of the panel beside the original's own panel at a comparable size, for the same ship, so the line order, blank lines and indentation can be checked against each other.

Live rules

Exactly one client — Data's OrionLayer must be closed; if it is attached, skip the live part and say so. Scratch saves only, never save, hashes as usual.

Acceptance
Line order, blank lines, indentation and tab stops match the original, or the difference is marked.
OCV/DCV shown, or the reason they cannot be reported.
Smoke test green before every commit. Pushing is Data's decision.

End of work order.
