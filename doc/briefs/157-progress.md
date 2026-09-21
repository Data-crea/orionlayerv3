# Work order 157 — progress

Unattended run, 21 September 2026. Updated after each part.

---

## Part 1 — close 156 with C — **DONE**

**Commit `1be0af0`.** Suite green, 243, count unchanged.

`RowBoxes` loses `growth` and `beyond`. Both were constants at both
construction sites since `514ebb2` (8 September) and carried no
marking; both belonged to the HD allocation bar, an INVENTION, and the
original's row draws population sprites only
(`Do_Colony_Info_Pop_Stuff_For_Pop_`, coldraw.cpp:282).

**What replaced the suite's assertion.** It asserted `not
_boxes.growth` per fixture. That is now `"growth"` and `"beyond"` not
in `RowBoxes._fields`, placed beside the `markers` assertion of 8
September that it is modelled on. **Strictly stronger**: the old one
said the field was empty for the rows that block happens to build, the
new one says the field cannot come back at all. No check was added or
removed — the count is 243 either way.

**The rewritten note**, first line in both `colonytrack._column_boxes`
and `v3_projektstatus.md`: *"A PER-ROW CAPACITY DISPLAY IS AN OPEN
DESIGN QUESTION FOR DATA."* It then records that the original shows
headroom only as a number in the scan box for the scanned colony
(`Draw_Colony_Scan_Info_`, colsum.cpp:1155), so a per-row display
would be a **marked HD EXTENSION**; that if it comes it is built new
against the six column boxes and does not bring back `growth`,
`beyond` or `growth_gap`; and where the old code is —`514ebb2`'s
parent for the bar, `1be0af0` for the fields.

**Render identity**: 16 PNGs at four resolutions, byte-identical, in
**both** input states (54 figures present; directory moved aside for
the coloured-cell fallback). The two states are different pictures, so
both branches were exercised. Evidence:
`~/orionlayer-fixtures/evidence/work_order_157/part1_rowboxes_render_identity.txt`.

**Nothing surprising.** Full-project grep found exactly one consumer
of either field (the suite's per-fixture assertion) and no positional
unpacking of `RowBoxes` anywhere.

C is marked resolved in `156-parked-for-data.md` with the hash.
