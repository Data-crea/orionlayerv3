Brief — Transcribe Maximum_Galaxy_Display_Scale_, retire the 50.6 rounding estimate
Read doc/v3_fundament.md before touching anything. This brief sets direction and acceptance criteria; every number, line and offset is yours to establish and report.
Why this comes first
The status document records the finding (7 September): the galaxy map derives _max_map_scale from zoomtables.MAP_MAX_X_PER_SCALE with commercial rounding, while the game takes the maximum of two ceiling operations. Your finding: the estimate is exactly one too small for the majority of star counts in 73…1023, never too large, and happens to be right for the reference save. It touches the HD zoom-out limit, the extended rung ladder and galaxy_inset_stars.

Stage 4 of the colony rebuild brings the 253×200 inset with the dot table onto a live screen. If the estimate is still in place at that point, the first side-by-side comparison of the inset will attribute the offset to the dot table. So this ships before Stage B/C and Stage 4, as its own commit.
Scope
Locate Maximum_Galaxy_Display_Scale_ in the orion2re tree and transcribe it into core/zoomtables.py (decision 26: all sizing comes from there; the docstring names source file and function). The orion2re tree is not modified.
Replace every consumer of the estimate with the transcription. Prove by grep that no consumer remains — name the callers you re-pointed.
Add a smoke-test check over the full star-count range that compares the transcription against an independent reference written out in the test, not imported from zoomtables. A verifier that shares its generation function is blind.
Correct doc/v3_fundament.md section 3, bullet on MAP_MAX_X / _max_map_scale: the constant holds across the stock sizes, the rounding does not. Keep the note that the community Maximum size was not part of the derivation unless your transcription now covers it — say which.
Same commit, same file: the three fundament paragraphs already queued in the status document —
byte-identical output after a refactor proves only the paths that were exercised (palette lesson);
the percentage is the transcription, the pixel count is derived (colonybuild column width);
ring from the artwork, window from the layout, boundary measured — artwork that does not fit the ring fails at the checker, not at the eye. File each under the working-principles group it belongs to, not by date. Check the next free decision number only if one of them turns out to be a decision rather than a principle; I expect none is.
Status document entry. CLAUDE.md stays untouched unless the fundament-first rule itself changed (it did not).
Acceptance criteria
Two independent sources for the transcription before it replaces anything. Source one is the orion2re function. Source two is yours to name at Stop 1 — a live probe against a state the snapshot actually carries, or a second game constant that must agree. The reference save alone is not a second source: the estimate is already right there, so it cannot tell the two apart. If no second source is reachable without a new save, say so at Stop 1 and we decide whether to generate one.
The check fails when the old rounding comes back. Prove it: temporarily reinstate commercial rounding, run the smoke test, paste the failing output into the report, revert. A check that is green today is not the criterion; a check that goes red on the regression is.
The check states, for the range 73…1023, how many star counts differ between old estimate and transcription, and asserts that the transcription is never below the old estimate. If your earlier count does not reproduce, that is a finding, not a test to loosen.
galaxy_inset_stars and the HD zoom-out limit are re-run against the reference save and reported before/after. Same numbers on this save is the expected result; different numbers means something else moved.
Parking stays on the safe direction (decision 35 corollary). Report whether the corrected scale changes the parked zoom-out step count on the reference save.
tools/smoke_test.py green, check count reported.
Reference save (stardate 3502.4, 99 stars, Greywind/Elerian) is not overwritten.
Reporting stops
Stop 1 — before any code. Report: where the function lives (file, line), the two operations it takes the maximum of, in your words; every consumer of the current estimate by file and function; your proposed second source. Wait.

Stop 2 — after implementation. Report: diff summary, the red run from the reinstated rounding, the range comparison figures, the before/after on the reference save, the smoke-test count, and the fundament diff. No push — Data reviews and pushes.

