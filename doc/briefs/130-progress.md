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
- **B** — done bar the live proof. orion2re **e9d07528** (`ext::g_activated_input`,
  the commit branch selects the activated field, the null selection no longer
  dereferenced), bundle `~/orion2re_bundle_18sep_e9d07528.bundle`, build green.
  `doc/ext_tech_activate.patch` checked in all three directions; open fix 25
  filed, open fix 23 updated with what it closes; version_check entry. Commit
  5ef5356, smoke 207.
- **C** — done bar source two. `core/researchlist.py` (four transcribed tables,
  the techinit tech[4] derivation, the walk, the rows, and decision 25's
  validation); `tools/research_cost_check.py` extended to all four tables;
  `tools/struct_header_check.py` new — decision 23's header route, mechanical,
  133 offsets over seven specs with an off-by-one control. `tech_applications`
  @379 has source ONE and sits in `unverified.py` until a live read agrees.
  `core/livefields.py` is the one home for `live_field`. Smoke 207 -> **209**,
  exit 0.
- **D** — done. Research field and application names as a THIRD output of
  `tools/techname_extract.py` (`core/technames.py`); `tools/billtext_extract.py`
  new for the panel's wording (`core/billtext.py`), whose file is shaped by
  entry and not by block (`Get_Text_Message_`, jim.cpp:336-359). Both wired into
  `tools/setup.py`, both gitignored, absent/stale/short are three stated states.
  Cross-check: field 21 "Capsule Construction" -> Battle Pods, Survival Pods,
  Troop Pods; the eight panels name themselves BASIC..OTHER. Smoke 209 -> **210**,
  exit 0, commit 3261264.
- **E** — done. `screens/research_select/` on wire id 53: `native.py` holds
  every 640x480 rectangle with its tech.cpp line and seats the boxes derived
  (the provenance is NOT a box key — `Box.to_dict` would drop it); `panel.py`
  draws; `screen.py` owns the wire, the refusals and the hand-back.
  `ScreenBase.wants_original` is decision 22 one step in. Four omissions, one
  HD extension and three deviations marked and checked. Smoke 210 -> **212**,
  exit 0, commit 366e308.
- **F** — checks done, **LIVE NOT RUN**. Data's own orion2re (15:29) and
  OrionLayer client were up before part F was reached, and 126's rule 8 says
  not to touch them. Parked in `130-parked-for-data.md` with the three steps
  to run. Status document updated: the screen count, what works, and the live
  gap as the first entry under "What is missing".
- **Run closed.** orionlayerv3: nothing pushed, smoke **205** at the start and
  **212** at the end, exit 0 on every commit. orion2re: one commit (e9d07528),
  push URL still disabled, bundle beside the tar backup. No save file was
  touched: no live step ran.
