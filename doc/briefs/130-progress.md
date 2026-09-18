# Work order 130 — progress log

One line per finished part, appended before the next starts (126's rule 9,
which applies here unchanged). Baseline: smoke **205**, exit 0, orionlayerv3
at 700b788 (nothing pushed); orion2re `orionlayer-local` at f838c754.

This order has NO reporting stop. Where a wrong build would result it names a
fallback instead, and part C's fallback is the one that matters.
- **A** — code done. `App._showing_original` is the one question the renderer
  and the click handler ask; `OriginalView.placement` is the one home for
  where the picture lands (decision 5). FINDING, worse than the order's
  premise: the fallback did not show the original picture either — it filled
  (6, 8, 16) and `use_original` was read by nothing. Measured, not read.
  version_check now requires the COORDINATE half of open fix 3. Smoke
  205 -> **207**, exit 0, commit 3105f98. Live proof deferred to the one live
  session with parts B and F.
