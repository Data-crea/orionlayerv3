# Redundancy audit: screens/ and core/

Work order 126 part I, 17 September 2026. The fundament's rule: the THIRD copy
is the signal to extract (decision 10, "Refactoring"), except where redundancy
is the point. `tools/` is out of scope.

**How this was made.** A read-only sub-session ran the scan and wrote the
tables below against the tree as it stood after part E (before part F moved
the galaxy map's input into `mapinput.py`, and before the extractions listed
next). **Line numbers are that tree's**; the functions named in "Extracted"
no longer sit where the tables say. The session that filed this verified the
four extraction candidates against the source before moving anything, and
checked finding D8 by reading `screens/planets/screen.py:293` against
`core/listgrid.all_bands`. Every other entry is the scan's claim with its line
reference.

## Headline

| | groups |
|---|---|
| Groups found | **39** |
| Identical or names-only, 3+ copies (clear extraction candidates) | **4** — 3 extracted, 1 parked (G3) |
| Identical or names-only, 2 copies | **7** (T1-T7), parked |
| Drifted | **24** (D1-D24), parked |
| Deliberate | **4** (P1-P4), left alone |

All eight groups of chat's pre-scan are confirmed; four had more copies than
it saw (`_load_frame`, `_render_frame_image`, `cover`, `fill`).

## Extracted — one commit each, moves only, smoke count 197 unchanged

| group | what moved | new home, and why there | commit |
|---|---|---|---|
| G2 `box_style` | colony_summary and galaxy_map `box_style`, empire_identity `_box_style`, planets `planetdraw._style` (4 copies, identical but for the name) | `core/screen_base.py`, beside `box_rect` and `box_font_scale_stored` — the named-box lookups already live there (decision 10's widgets are for controls; this is a ScreenBase helper) | 4c39b66 |
| G4 held pops | the inline "unassign the held cluster" prelude in `predict_pops` and `plan_drop` | the existing `colonymove.held_pops`, whose docstring already argued against a second copy; same module | e5cb136 |
| G1 frame trio | `_load_frame`, `_scale_frame`, `_render_frame_image` from colony_summary, galaxy_map and planets (planets inline) | `core/screen_base.py`, beside the background trio it mirrors (`_load_background`/`_scale_background`/`_render_background`) and the `USE_FRAME` fallback it calls; opt-in, the image name passed from each screen's `layout.json`. Renders of the three screens at three sizes byte-identical before and after (`~/orionlayer-fixtures/evidence/work_order_126/I_frame_trio_render_identity.txt`) | e845dd6 |

Decision 6's list was regenerated from `tools/linecount.py` after each
(galaxy_map/screen.py 461 -> 456 -> 436 code lines; screen_base 288,
colony_summary/screen.py 271 — both under 300).

## Not extracted, and why — parked for Data (`doc/briefs/126-parked-for-data.md`)

- **G3 cover-fill** — two FUNCTION copies are names-only (`imagebox.cover`,
  `select_race._make_thumbnail`), but the other three are blocks of different
  shape whose RESULT equals `cover(…, (0.5, 0.5), 1.0)` by arithmetic
  (`int(0.5*k) == k//2`). That is not "identical or names-only", so it is a
  judgement call, not a move.
- **D8, a decision-5 fault on Planets**: hover hit-tests with proportional
  division while the list draws with `listgrid.all_bands`; the scan computed
  7 disagreeing pixel rows at 1080p and 1440p, 10 at 2160p, 24 at 1366x768.
- **D4**: `colonyoutput.fill_template`'s own note asks for extraction at the
  third copy; a third and a fourth exist, drifted (None handling).
- Everything else below: two-copy groups, drifted groups, deliberate ones.

---

## Method

1. **AST pass** (`scan.py`, `scan2.py`) over 1309 functions and methods in `screens/**/*.py` and `core/**/*.py`:
   - Docstrings, decorators and annotations are stripped.
   - Arguments and assigned locals are renamed positionally. Attribute names and constants are kept.
   - Three comparisons: (a) exact normalised-dump equality; (b) same shape with constants erased; (c) `difflib` token-sequence ratio >= 0.80 with >= 5 statements, plus a looser pass (>= 0.72, >= 2 statements) to feed the manual reading.
2. **Targeted reading** of these families: grid/row arithmetic, hit-testing, text fitting, image loading and scaling, `_load*` helpers, palette wrappers, JSON loading, and pressed/hover handling.
3. **Smoke-test cross-check.** `tools/smoke_test.py` was grepped for every candidate name, and for source-text checks (`open(...).read()`, `split("def ...")`, and tree-wide "one home" greps) that would notice a move.

**Palette wrappers are already extracted.** The six-copy wrapper named in the Refactoring section is now `palette.for_section`. It is used as `_c = palette.for_section(...)` in custom_race, select_race, empire_identity and both widgets. No drifted copy remains.

**Excluded as interface one-liners, not duplication.** These were counted by the scan but are not groups:
- `clear_cache`/`clear` = `self._cache.clear()` ×5: custom_race/popup.py:76, core/nineslice.py:91, core/frame.py:188, core/helppopup.py:151, core/banner.py:203.
- `ScreenBase.update` / `_template` `update` (`pass`).
- `ScreenBase.editor_note` / `screenhelp.help_extra_rect` (`return None` hooks).
- `dispatcher.route_click/route_motion/route_key_event` (core/dispatcher.py:148-159).
- `screenhelp.help_consumes_click/key/wheel` (core/screenhelp.py:177-199).
- `mapcoords.galaxy_to_native/native_to_galaxy` (inverse pair).
- `game_state.read_i8/i16/i32/u8`: local closures that differ only in the struct format (core/game_state.py:118-140).
- Attribute-store `__init__`s: colonysort.py:134, viewctl.py:67, colonymove.py:310, colonyselect.py:303, colonypick.py:162.
- `colonyselect __init__/reset` (198/225) and `galaxy_map/renderer.py __init__/clear` (552/556).
- `gmsliders.spec` / `gmframe.spec` (`screen.words.get(X) or {}`).
- `on_resize` bodies that are `super()` plus one cache clear: new_game:380, select_race:147, empire_identity:157.

---

## Headline numbers

| | count |
|---|---|
| **Groups found** | **39** |
| IDENTICAL or names-only, 3+ copies (CLEAR EXTRACTION) | **4** |
| IDENTICAL or names-only, 2 copies (PARK-TWO-COPIES) | **7** |
| DRIFTED (PARK-DRIFTED) | **24** |
| Judged deliberate (PARK-DELIBERATE) | **4** |

Findings that are not only redundancy, flagged for Data (no fix decided):
- **D8: a decision-5 defect.** On Planets the hover row index uses `(y - area.y) * visible // area.height` (planets/screen.py:313). The drawing uses `listgrid.all_bands` (planetdraw.py:107): band = h // n, and the last band takes the remainder. Computed offline at the `rows` box height, the two disagree on **7 px rows at 1920x1080 and 2560x1440, 10 at 3840x2160, 24 at 1366x768, and 0 at 1280x720**. Hover also sets `_selected`/`_scanned`.
- **D4: extraction was asked for, and it did not happen.** `colonyoutput.fill_template`'s docstring calls itself the *second* `{key}` filler and asks that the third be extracted. Two more copies (`colonypopup` and `colonypick`) already exist.
- **D5: a leftover copy.** `textfit`'s docstring says the word-wrap was extracted at the third copy, but `custom_race/popup.MessagePopup._lines` still carries its own copy of the same algorithm.
- **D17: three separate `HStrings` instances.** HStrings is built at three sites with three different cache homes (`app.hstrings`, `screen._hstrings`, and a fresh instance per Planets entry). `screenhelp.helptext` argues for exactly one construction site.
- **D12: one construction, three fill mechanisms.** The backdrop-cut panel with a thin border exists three times, and the busy panel's docstring says it is "the same construction" as the Custom Race box.

---

## CLEAR EXTRACTION

### G1: Fixed frame image: load / scale / blit (+ resize hook)

| part | copy | file:line | status |
|---|---|---|---|
| `_scale_frame` | colony_summary | screens/colony_summary/screen.py:401-407 | identical |
| | galaxy_map | screens/galaxy_map/screen.py:200-206 | identical |
| | planets | screens/planets/screen.py:158-164 | identical |
| `_load_frame` | colony_summary | screens/colony_summary/screen.py:384-399 | names-only (inline `.get` chain + docstring) |
| | galaxy_map | screens/galaxy_map/screen.py:192-198 | names-only (temp `cfg`) |
| | planets | screens/planets/screen.py:152-156 | identical to colony |
| | (unrelated homonym) | core/style.py:101 `_load_frame(skin_dir)` | NOT a copy: 9-slice FrameRenderer |
| `_render_frame_image` | colony_summary | screens/colony_summary/screen.py:467-472 | identical |
| | galaxy_map | screens/galaxy_map/screen.py:392-396 | identical |
| | planets | screens/planets/screen.py:189-190 (inline in `render`) | drifted: no `elif self.USE_FRAME` branch; that branch is dead in all three (`USE_FRAME = False` at colony:143, galaxy:87, planets:46) |
| `on_resize` | colony_summary | screens/colony_summary/screen.py:249-251 | identical to planets |
| | planets | screens/planets/screen.py:96-98 | identical |
| | galaxy_map | screens/galaxy_map/screen.py:233-244 (`_scale_frame()` at 243, among cache clears) | superset |
| attribute init | all three | colony:149-151, galaxy:102-104, planets:51-53 (`_frame`, `_frame_scaled`, `_frame_pos`) | identical |
| exit | galaxy only | galaxy_map/screen.py:252 `self._frame_scaled = None` | drift: colony and planets define no `exit` and keep the scaled frame |
| lazy 4th variant | game_menu | screens/game_menu/gmframe.py:139-149 `_image(screen, size)` | drifted: size-keyed cache on `screen._frame_cache`, reads `screen.words` rather than `_data`, scales to a computed size rather than the reference area. Documented as decision 69; leave it out |

- Copies: 3. Status: identical (`_scale_frame`) or names-only (`_load_frame`); `_render_frame_image` has 2 identical copies plus an inline third.
- Intended? No comment anywhere explains keeping three copies. `doc/colsum_rebuild_inventory.md:128` lists `_load_frame`, `_scale_frame` and `box_style` as colony methods to be "Replaced".
- **Verdict: CLEAR EXTRACTION.** Every future screen with a fixed frame PNG will want the same trio.

**Body (colony_summary/screen.py:384-407, 467-472):**
```python
def _load_frame(self):
    path = self.asset_path("assets",
                           self._data.get("frame", {}).get(
                               "image", "frame.png"))
    self._frame = (pygame.image.load(path).convert_alpha()
                   if path else None)
    self._scale_frame()

def _scale_frame(self):
    if self._frame is None:
        self._frame_scaled = None
        return
    x, y, w, h = self.layout.rect((0, 0, REF_W, REF_H))
    self._frame_scaled = pygame.transform.smoothscale(self._frame, (w, h))
    self._frame_pos = (x, y)

def _render_frame_image(self, surface):
    """The frame, over the content and under the header plates."""
    if self._frame_scaled is not None:
        surface.blit(self._frame_scaled, self._frame_pos)
    elif self.USE_FRAME:
        self._render_frame(surface)
```

**Call sites that would change:**
- colony_summary/screen.py: `enter` 174 `self._load_frame()`; `on_resize` 249-251 (the whole method could go); `render` 426 `self._render_frame_image(surface)`; `__init__` 149-151.
- galaxy_map/screen.py: `enter` 121; `on_resize` 243; `exit` 252; `render` 386; `__init__` 102-104.
- planets/screen.py: `enter` 83; `on_resize` 96-98 (the whole method); `render` 189-190 (inline blit becomes a call); `__init__` 51-53.
- Prose that names the method: screens/colony_summary/colonytrack.py:250 (`screen._scale_frame`); v3_projektstatus.md:7037, 8407, 8439 (historical entries); doc/colsum_rebuild_inventory.md:128.

**Smoke-test references:**
- tools/smoke_test.py:1019 `assert gm._frame_scaled is not None`: the attribute name must survive.
- tools/smoke_test.py:16019 `_pf_gm._render_title(surf)`: galaxy's `_render_title` sits next to the trio but is NOT part of it (see D15). Do not move or rename it.
- tools/smoke_test.py:198 and 12358 call `on_resize()` on live screens. Adding the frame rescale to `ScreenBase.on_resize` changes what they exercise.
- No smoke check calls `_scale_frame`, `_load_frame` or `_render_frame_image` by name.
- tools/smoke_test.py:1390ff re-measures the colony frame's holes against `smoothscale` output. The arithmetic must stay byte-identical, which a move preserves.

**Home: `core/screen_base.py`.**
- It already owns the same trio for the background: `_load_background` 207-220, `_scale_background` 222-243, `_render_background` 245-251.
- It owns `asset_path`, `layout`, and the `USE_FRAME`/`_render_frame` fallback that `_render_frame_image` calls.
- It is 262 code lines by `tools/linecount.py`'s measure (~15 more fits under 300). colony_summary/screen.py is at 298 and gains headroom.
- `core/frame.py` does not fit: it is the 9-slice `FrameRenderer`, and `_frame` would clash in meaning. `core/imagebox.py` does not fit either: it is scoped to box pictures with pan, zoom and fade.

Two constraints for whoever moves it:
- **(a)** ScreenBase does not know `_data` (the layout.json dict is per screen), so the image name must come in as an argument or a hook.
- **(b)** ScreenBase.on_resize runs for every screen, including the smoke test's `FakeQueuePopup(ScreenBase)` (smoke_test.py:535). Either default `_frame`/`_frame_scaled`/`_frame_pos` in `ScreenBase.__init__`, or keep the resize call opt-in. The galaxy-only `exit` release is a drift to resolve one way or the other.

### G2: `box_style(name)`: a named box's style dict

| copy | file:line | status |
|---|---|---|
| colony_summary `box_style` | screens/colony_summary/screen.py:612-616 | identical |
| galaxy_map `box_style` | screens/galaxy_map/screen.py:339-343 | identical |
| empire_identity `_box_style` | screens/empire_identity/screen.py:262-266 | names-only (name) |
| planets `planetdraw._style(screen, name)` | screens/planets/planetdraw.py:304-308 | names-only (module function; `screen.boxes`) |
| inline | screens/galaxy_map/boxdraw.py:127 `next((b.style for b in screen.boxes if b.name == name), {})` | drifted form, same result |
| same loop in core | core/screen_base.py:261-268 `box_rect`, :289-292 `box_font_scale_stored` | sibling lookups |

- Copies: 4 function copies (plus 1 inline). Status: identical or names-only.
- Intended? No explanation anywhere; the colony copy is on the colsum inventory's "Replaced" list.
- **Verdict: CLEAR EXTRACTION.**

**Body (colony_summary/screen.py:612-616):**
```python
def box_style(self, name):
    for box in self.boxes:
        if box.name == name:
            return box.style
    return {}
```

**Call sites:**
- screens/colony_summary/colonysort.py:230 and :329 (`screen.box_style(...)`)
- screens/galaxy_map/screen.py:556 and :573
- screens/empire_identity/screen.py:197 (`self._box_style("preview_image")`)
- screens/planets/planetdraw.py:312 (`_font`) and screens/planets/monsterpanel.py:146 (`planetdraw._style(screen, SPRITE_BOX)`)
- Optional: screens/galaxy_map/boxdraw.py:127

**Smoke-test references:** tools/smoke_test.py:11624 `_rb_scr.box_style("return")`, where `_rb_scr` is the colony_summary screen (11565). If the public name `box_style` lives on ScreenBase, inheritance keeps this working. No smoke reference exists to `_box_style` or `planetdraw._style`.

**Home: `core/screen_base.py`**, under "Box helpers" beside `box_rect` and `box_font_scale_stored`, which already walk `self.boxes` by name.

**Related drifted siblings, not part of this extraction:**
- "the Box itself by name": colonyoutput.py:354-359 `_box` and gmdraw.py:38-39 `box`.
- "font px of a named box": D10.

### G3: Cover-fill scale plus centre or anchored crop

| copy | file:line | status |
|---|---|---|
| `imagebox.cover(img, tw, th, crop, zoom)` | core/imagebox.py:29-40 | reference |
| `select_race._make_thumbnail(img, tw, th, crop=(0.5,0.5), zoom=1.0)` | screens/select_race/renderer.py:142-158 | names-only (`base_scale` vs `base`, defaults added) |
| `ScreenBase._scale_background` (block) | core/screen_base.py:222-243 (math 227-242) | arithmetic-identical to `cover(img, win_w, win_h, (0.5, 0.5), 1.0)` |
| `helppopup.Backdrop.surface` (block) | core/helppopup.py:91-110 (math 96-105) | arithmetic-identical, same call |
| `galaxy_map._scale_map_background` (block) | screens/galaxy_map/screen.py:218-231 | arithmetic-identical to `cover(img, w, h, (0.5, 0.5), 1.0)` |
| `new_game._scale_background` | screens/new_game/screen.py:107-121 | DRIFTED, intended |

**Why the three blocks equal `cover` at those arguments:**
- `max(0.3, 1.0) = 1.0`, so the scale is identical.
- Both use `max(t, int(i * scale))` for the scaled size.
- For an integer k >= 0, `int(0.5 * k) == k // 2`, so the crop origin is identical.

**The new_game drift is intended.** Its docstring (100-101) says it "keeps scale/crop factors for _hd_to_screen". It has no `max(win, …)` guard and stores float crops.

- Copies: 5 (2 function copies plus 3 embedded blocks), and one intended drifted sixth.
- `imagebox.cover`'s docstring (line 31) says "Same semantics as the select_race portrait thumbnails", which acknowledges the pair.
- **Verdict: CLEAR EXTRACTION.** The two functions are names-only; the three blocks are value-identical.

**Body (core/imagebox.py:29-40):**
```python
def cover(img, tw, th, crop, zoom):
    iw, ih = img.get_width(), img.get_height()
    base = max(tw / iw, th / ih)
    scale = base * max(0.3, zoom)
    sw = max(tw, int(iw * scale))
    sh = max(th, int(ih * scale))
    scaled = pygame.transform.smoothscale(img, (sw, sh))
    cx = int(crop[0] * max(0, sw - tw))
    cy = int(crop[1] * max(0, sh - th))
    return scaled.subsurface((cx, cy, tw, th)).copy()
```

**Call sites that would change:**
- screens/select_race/renderer.py:111 (`_make_thumbnail(...)`, then delete 142-158)
- core/screen_base.py:227-243
- core/helppopup.py:97-105
- screens/galaxy_map/screen.py:225-231
- core/imagebox.py:31 docstring. imagebox.py:88 already calls `cover`.
- new_game stays as it is.

**Smoke-test references:**
- None to `_make_thumbnail`, `cover`, `_scale_background`, `_scale_map_background` or `Backdrop`.
- tools/smoke_test.py:15486 asserts that the SOURCE of galaxy `_render_map` contains `surface.blit(self._map_bg_scaled`. Keep the attribute name.
- tools/smoke_test.py:10131-10192 compares `imagebox.render_image_box` pixels. `cover` stays unchanged.

**Home: `core/imagebox.cover`** (already the named home; decision 4's module).

Side observation, no action decided: on a screen without its own background.png, `ScreenBase._bg` and `helppopup.Backdrop` both load and cover-scale `background_cockpit.png` to the same window size. That is two caches of the same surface.

### G4: "Unassign the held pops" prelude in `colonymove`

| copy | file:line | status |
|---|---|---|
| `held_pops(pops, indices)` | screens/colony_summary/colonymove.py:268-293 (body 289-293) | reference, already a named helper |
| inline in `predict_pops` | screens/colony_summary/colonymove.py:333-337 | identical (iterates a `set`; the bit-clear is idempotent and order-independent) |
| inline in `plan_drop` | screens/colony_summary/colonymove.py:378-382 | identical |

- Copies: 3, identical.
- Intended? No note. `held_pops`' own docstring argues against "a second copy of the row" (decision 5).
- **Verdict: CLEAR EXTRACTION.** It is within one module and the helper already exists, so the change is to call it.

**Body (colonymove.py:289-293):**
```python
out = list(pops)
for i in indices:
    if 0 <= i < len(out):
        out[i] &= ~colony_struct.POP_MASK_ASSIGNED
return out
```
The inline form (333-337 and 378-382) is `work = list(pops); held = set(...); for i in held: if 0 <= i < len(work): work[i] &= ~POP_MASK_ASSIGNED`. It would become `held = set(...); work = held_pops(pops, held)`. `held` is still needed for `len(held)` in `plan_drop`.

**Call sites:** colonymove.py:333-337 and :378-382 only.

**Smoke-test references (names stay the same):**
- tools/smoke_test.py:8755 `_cmv2.held_pops(...)`
- :10842 `predict_pops`
- :7518-7544 `plan_drop`
- :7526-7532 monkeypatches `_cm.pop_state` and relies on `plan_drop` reaching it through the module global. Unaffected.

**Home:** `colonymove.held_pops` stays where it is.

---

## PARK-TWO-COPIES

| id | function(s), file:line | copies | status | notes / intended? | verdict |
|---|---|---|---|---|---|
| T1 | `fallback_text_rect` screens/custom_race/popup.py:46-50; `busy_text_rect` screens/empire_identity/renderer.py:235-239 | 2 | names-only | Each reads its own module's `FALLBACK_INSET`: popup.py:43 `(60, 50)`, renderer.py:232 `(24, 7)`. The values differ on purpose (comments at popup 40-41 and renderer 229-230). Callers: custom_race/screen.py:310, empire_identity/screen.py:228 | PARK-TWO-COPIES |
| T2 | `EStrings.string` core/estrings.py:131-146; `HStrings.message` core/hestrings.py:93-101 | 2 | names-only | The names follow the originals (`H_Message_`). estrings' docstring explains None vs `""`. Smoke calls both (6733ff; 13667) | PARK-TWO-COPIES |
| T3 | `playercolors.lift(rgb, k)` core/playercolors.py:48-49; `ships._lift(color, keep=TINT_KEEP_WHITE)` screens/galaxy_map/ships.py:237-238 | 2 | names-only (a default argument added) | colors.json:1283 (`_k_ship_protocol`) measures presets "through ships.TintCache's own path (TINT_KEEP_WHITE lift…)". **tools/smoke_test.py:15363 emulates `_lift` with `playercolors.lift`**, so if the two ever drift, that measurement silently measures the wrong thing | PARK-TWO-COPIES |
| T4 | `colonyselect.Window.row` screens/colony_summary/colonyselect.py:130-135; `planets._selected_row` screens/planets/screen.py:132-136 | 2 | names-only | none | PARK-TWO-COPIES |
| T5 | `PlanetSet.get` screens/colony_summary/colonyplanets.py:123-126; `SurfaceSet.get` screens/colony_summary/colonysurfaces.py:83-86 | 2 | names-only (dict attribute) | none | PARK-TWO-COPIES |
| T6 | `planetdraw.render_scroll` arrow placement screens/planets/planetdraw.py:186-192 (`arrow = rect.width`, tops `rect.y` / `rect.bottom - arrow`); `planetdraw.scroll_arrows` :201-208 (same `a = rect.width`, same tops) | 2 | same geometry in two functions | Decision-5 shape, draw vs `handle_click` (planets/screen.py:239-243). They agree today. colonyscroll.arrows (colony) is the one-function form | PARK-TWO-COPIES |
| T7 | `FrameRenderer.button_rect_left` core/frame.py:191-198; `button_rect_right` :200-207 | 2 | names-only (`btn_left`/`btn_right`) | none | PARK-TWO-COPIES |

---

## PARK-DRIFTED

| id | group: every copy with file:line | copies | what differs | intended? (evidence) | verdict |
|---|---|---|---|---|---|
| D1 | **Versioned derived-JSON loaders**: `BuildingNames._load` core/buildnames.py:90-109 (+ `name_file` 68, `__init__` 84); `MainText._load` core/maintext.py:64-83 (+ `text_file` 49, `__init__` 58); `ShipPartNames._load` core/shipparts.py:86-107 (+ `name_file` 71, `__init__` 80); `EStrings._load` core/estrings.py:99-129 (+ `string_file` 79, `__init__` 93); `HStrings._load` core/hestrings.py:66-91 (+ `string_file` 48, `__init__` 60); 6th relative `HelpText.load` core/helptext.py:112-155 | 5 (+1) | See detail D1 below | The shared SHAPE is documented, the copying is not: docstrings call it "THE SAME SHAPE AS THE HELP TEXTS" (buildnames:3), "THE SAME SHAPE AS THE BUILDING NAMES" (shipparts:3), "THE THIRD USE OF THE HELP-TEXT PATTERN" (estrings:3), "AGAIN" (hestrings:4), and "DECISION 38'S RULES" (maintext:10). Nothing says the loader code must stay copied. The walks that do differ on purpose live in the tools/ extractors, not in these loaders | PARK-DRIFTED (parameter-only up to the payload; strongest drifted candidate) |
| D2 | **Colony sprite-directory loaders**: `PlanetSet._load` colonyplanets.py:82-121; `IconSet._load` colonyoutputicons.py:85-118; `SurfaceSet._load` colonysurfaces.py:56-81; `FigureSet._one/_read` colonyfigures.py:249-322 | 4 | See detail D2 below | FigureSet's "continue" is documented (`_one` docstring). Why planets and icons stop at the first refused root is not documented | PARK-DRIFTED |
| D3 | **Per-App LRU `set_for`**: colonyplanets.py:148-169; colonyoutputicons.py:124-141; colonyfigures.py:403-432 (and the non-LRU colonysurfaces.py:89-95) | 3 | The LRU block (get-or-create `OrderedDict` on `screen.app.<attr>`, `move_to_end`, construct, evict to `SET_CACHE`) is identical apart from parameters: attribute name (`planet_sets`/`output_icon_sets`/`figure_sets`), key (`size` / `(master, size)` / `size`), factory, and `SET_CACHE` (4 / 2 / 4). Guard before it: planets `size <= 0 → None`; icons `not size → None`; figures none | colonyplanets' docstring cites colonyfigures ("for the same reason `colonyfigures.set_for` is"). Each SET_CACHE value has its own comment | PARK-DRIFTED (parameter-only) |
| D4 | **`{key}` template fill**: `lines_for.fill` colonypopup.py:72-76 and `message.fill` colonypick.py:266-270 (these two identical); `fill_template(template, values)` colonyoutput.py:109-125; `_detail_text` colonylist.py:649-665 (a loop over pre-stringified `("{climate}", name)` pairs); single-key inline `.replace("{x}", …)`: main_menu/screen.py:101, core/helptext.py:197, colonybuild.py:156, colonylist.py:525, game_menu/screen.py:228, gmdraw.py:128 | 4 (+6 single-key) | The nested copies take `**values` and coerce with `str(template or "")` (None becomes `""`). `fill_template` takes a dict and has no None guard (`fill_template(None, …)` raises AttributeError). `_detail_text` is a hand-listed loop | fill_template's docstring (113-117): "The second copy of this shape … the THIRD copy is the signal to extract, so this note is here to make the third one obvious". The third and fourth now exist without a note. Smoke: 5050, 5185-5186, 9901 call `fill_template`; 8397-10672 call `colonypick.message` | PARK-DRIFTED (rule already triggered by the tree's own note) |
| D5 | **Word wrap measured by rendering**: `textfit.wrap_text` core/textfit.py:26-45 (home); `MessagePopup._lines` screens/custom_race/popup.py:123-151 | 2 | textfit has a fast path (whole string fits → `[text]` verbatim, keeping any runs of spaces); the popup always rejoins single-spaced. The popup measures in `COL_TEXT` instead of white (width is independent of colour) and caches rendered lines | textfit's docstring: "THE THIRD COPY, EXTRACTED … Both originals now call this" (helppopup, colonybuild); the popup is not mentioned. Its own docstring repeats the decision-30 rule verbatim. No reason given for not calling textfit | PARK-DRIFTED (home exists) |
| D6 | **Markup (`*hi*`, `~kw~`) wrap**: select_race/info_panel.py:57-113 `_render_description`; custom_race/description.py:33-62 `_words` + 65-127 `render_description_panel` + 130-157 `description_height` | 2 (+1 internal) | See detail D6 below | description.py:4-5: "Uses the same markup convention as the Select Race descriptions". The continuity rule is documented (`_words` docstring). The font.size/render split is not | PARK-DRIFTED |
| D7 | **Shrink-font-until-it-fits**: `planetdraw._text` planets/planetdraw.py:49-57; `gmdraw._blit_fit` game_menu/gmdraw.py:83-91; inline paragraph loop colonyoutput.py:468-480; `textfit.squeeze_lines` core/textfit.py:55-77; different technique `sidebar._fit_width` galaxy_map/sidebar.py:147-160 | 4 (+1) | planetdraw and gmdraw: same loop (render, `size -= 1` while wider and above 8); planetdraw returns the surface, gmdraw blits. colonyoutput: wraps with `textfit.wrap_text`, splits on `"\n"` first, sizes `px..8`, and checks height and width together (squeeze_lines' test inline, plus paragraphs). squeeze_lines: caller-supplied sizes, no paragraph split. sidebar: smoothscales the finished surface | planetdraw cites `Set_Fitted_Font_Style_` plntsum.cpp:85; gmdraw cites the fundament; colonyoutput explains its choice ("ONE SIZE FOR THE WHOLE PARAGRAPH — brief 97") and names textfit; sidebar explains why it scales the surface | PARK-DRIFTED |
| D8 | **N rows tiling a rect**: `listgrid.band_height`/`all_bands` core/listgrid.py:34-51 (band = h//n, last takes the remainder; used by colonytrack.row_bands 706-732 for draw AND hit, and by planetdraw.render_list :107); `gmdraw.bands` game_menu/gmdraw.py:52-56 (edges `y + h*i//n`); `gmorion.bands` game_menu/gmorion.py:58-60 (same edge expression inline, identical to gmdraw.bands); `monsterpanel._rows` planets/monsterpanel.py:171-179 (top `y + h*i//n`, height `h//n`, so it does not tile); `sidebar.row_rects` galaxy_map/sidebar.py:118-124 (float step); `ListView.row_at` core/widgets/list_view.py:83-89 (fixed row_h); **planets hover** planets/screen.py:313 `band = (y - area.y) * visible // area.height` | 7 | Three rounding rules (remainder-to-last, edge division, float) plus fixed pitch. **Planets draws with `all_bands` but hit-tests with proportional division** (mismatch figures in the headline). gmorion re-derives gmdraw.bands inline | gmdraw.bands' docstring states its rule. colonytrack.row_bands' docstring warns exactly "a second copy of this arithmetic would get wrong". The planets formula has no comment. The Refactoring section already records "Two independent grid-layout implementations" as paid for | PARK-DRIFTED (contains a decision-5 defect) |
| D9 | **Window rect / hit of a named box**: `planetdraw.window` planets/planetdraw.py:64-66 (`Rect(*layout.rect(box_rect(name)))`); `colony_summary._hit` screen.py:819-821 (same expression); `planets._hit` screen.py:335-337 (via window); `gmdraw.rect`/`hit` game_menu/gmdraw.py:42-49 (uses `Box.screen_rect`); ~23 inline `Rect(*…layout.rect(…))` (colony screen.py ×7, galaxy screen.py ×6, colonyoutput ×3, and one each in colonyempire, colonyheader, colonyhelp, colonymoveui, colonyplates, colonysort, boxdraw) | 4 (+~23 inline) | Two sources of truth. `layout.rect(box_rect(name))` applies `content_offset` and ignores `anchor`; `Box.screen_rect` (core/box.py:51-75, written once per layout change) honours `anchor` and ignores `content_offset`. Only main_menu's boxes.json uses either key today, so there is no live divergence on these screens. core/box.py:56-73 also re-derives `Layout.rect`'s arithmetic, and its `left` and `else` branches are identical | colonytrack.py:245-262 documents why the colony moved off `Box.screen_rect` ("a device coordinate with a lifetime"). game_menu uses `screen_rect` without comment | PARK-DRIFTED |
| D10 | **Font px of a named box**: `boxdraw._font` galaxy_map/boxdraw.py:126-128; `planetdraw._font` planets/planetdraw.py:311-312 (returns the REFERENCE size; every caller wraps it in `layout.font_size`: 221, 233, 246, 298, monsterpanel 166); galaxy inline screen.py:572-573; colonysort inline :327-330 and `font_size` :230-233; `gmdraw._size` game_menu/gmdraw.py:69-72 | 5 | Defaults 16 / 19-22 / 16 / 24 / 18 / 24. Same name `_font` with different return units (px vs reference). game_menu multiplies by `content_scale` | gmdraw comments the `content_scale` factor (gmframe.seat); the rest have no comment | PARK-DRIFTED |
| D11 | **"First item whose ref rect contains the point"**: `banner_hit_test` empire_identity/renderer.py:121-128; `picks_hit_test` custom_race/renderer.py:165-172; `specials_hit_test` custom_race/renderer.py:272-289; `_race_at_screen_pos` select_race/screen.py:202-217 | 4 | Core loop (L.pos + L.size, then Rect.collidepoint, return item) is names-only across banner/picks/select_race. picks nests over categories; specials clips to the panel first and offsets by scroll; select_race computes the cell per index and returns `race["id"]` | All four pair with a `*_layout` producer that drawing also uses (decision 5 is satisfied per screen); no comment on the loop | PARK-DRIFTED |
| D12 | **Opaque panel cut from a backdrop + thin border**: `MessagePopup.render` custom_race/popup.py:80-106; `render_busy_panel` empire_identity/renderer.py:242-260 (backdrop block 256-260); `HelpPopup.render` core/helppopup.py:205-211 | 3 | Fallback fill: popup blits an SRCALPHA surface filled with 4-tuple `COL_BG`; busy panel uses `surface.fill(COL_BOX_BG[:3])`; help uses an opaque Surface filled with `COL_FILL[:3]`. Guard: popup `if backdrop and`, the others `is not None`. Minimum size: popup and busy `pw < 8 or ph < 8 → return`; help computes its own height. Backdrop source: the screen's `_bg_scaled` vs `screenhelp.help_backdrop()` | busy panel's docstring: "Same construction as the Custom Race message box". helppopup.Backdrop (69-84) explains why the *source* differs. The three fill mechanisms are not explained | PARK-DRIFTED |
| D13 | **Hover-filled button + centred word from a named box**: galaxy `_render_nav` galaxy_map/screen.py:560-580; `colonysort.render_return` colony_summary/colonysort.py:293-332; `planetdraw.render_control` planets/planetdraw.py:211-225; `gmdraw.button` game_menu/gmdraw.py:108-117; `boxdraw._button` galaxy_map/boxdraw.py:145-148 | 5 | Hover source: mouse position (galaxy, colony, planets) vs `pressed.colour` (game_menu) vs none (boxdraw). Base fill: NAV_BG always (galaxy) vs only on hover (colony) vs active/hover (planets). Border: `draw_plate` (planets), `draw_thin_border` (boxdraw), none (galaxy, colony: the frame supplies the bezel). Label: `font.render` (galaxy, bypassing `style.render_text` and decision 30's substitution) vs `style.render_text` (others); planets shrinks to fit | colonysort's docstring explains its hover extent (whole box vs word); the galaxy nav has no comment on `font.render` | PARK-DRIFTED |
| D14 | **Centre a rendered surface in a rect** (idiom): ~36 inline `x + (w - s.get_width()) // 2` sites in 20 files (e.g. core/listgrid.py:230-231, core/screen_base.py:342-343 and 384-385, colonysort.py:293-295 and 331-332, empire_identity/renderer.py ×6); helpers `colonylist._blit_centered` :932-937 and `boxdraw._text` :131-138; `get_rect(center=…)` in planetdraw.py:225 and :235 | ~38 | Line box (most) vs ink box (galaxy `_render_title` galaxy_map/screen.py:411-417) vs `get_rect(center=)` (rounds odd differences the other way by 1 px) | The galaxy ink centring is documented ("CENTRED BY INK, NOT BY THE FONT'S LINE BOX", 16 September 2026); the others are not | PARK-DRIFTED |
| D15 | **Frame title in a cutout**: `_render_title` colony_summary/screen.py:474-485; galaxy_map/screen.py:398-417 | 2 | Galaxy: pressed colour (`self.pressed.colour("title", …)`) and ink-box centring. Colony: fixed `TITLE_COLOR`, line-box centring. Colony's copy is dormant: its layout.json `frame` has no `title_rect` (`_no_title_note`: "THE SCREEN HAS NO TITLE, and that is a transcription") | Galaxy changes are documented at 409-416. Colony keeps a now-unused copy | PARK-DRIFTED |
| D16 | **Push the HD sort key on entry**: `_push_sort_key` colony_summary/screen.py:193-228; planets/screen.py:100-106 | 2 | Colony `return`s after the first matching spec; planets does not (with duplicate keys in layout.json it would inject twice). Key source `self._sort_key` vs `self._list.sort_key` | planets' docstring: "the colony summary's trade". The loop difference has no comment | PARK-DRIFTED |
| D17 | **Get-or-create a per-language text table**: `HStrings(...)` at galaxy_map/boxdraw.py:68-75 (cached on `screen._hstrings`), game_menu/screen.py:93-97 (cached on `app.hstrings`, checked first), planets/planetwords.py:55-57 (fresh per `Words.load`, i.e. per Planets `enter`); `EStrings(...)` at colonybuild.py:219-224 (on `app.production_names`) and planetwords.py:56 (fresh); pattern home `screenhelp.helptext` core/screenhelp.py:55-68 (`app.helptext`) | 5 construction sites | Where the instance lives (app vs screen vs none). The language lookup is spelled three ways: `(getattr(app,"settings",{}) or {}).get(...)` (boxdraw, planets, screenhelp, game_menu) vs `screen.app.settings.get(...)` (colonybuild, which raises if `settings` is absent). The galaxy map and game menu therefore read HESTRNGS twice into two objects | screenhelp.py:57-60: "exactly one construction site … without a second copy of the same two lines". The others are not commented | PARK-DRIFTED |
| D18 | **Load a PNG from a resolved path** (idiom): ~38 `pygame.image.load(path)` sites (listed by grep: screens ×23, core ×15) | ~38 | Error handling: the colony sprite sets catch `pygame.error` and record `refused` (D2); every other site lets a corrupt file raise (decision 22 "Graceful fallback"). `if path:` without an `else` leaves the previous surface in place (new_game.py:103-105, main_menu.py:108-110, custom_race.py:91-93); the others assign None. `convert()` vs `convert_alpha()` (helppopup:96, galaxy:215, new_game:145 use `convert`) | Not commented as a policy | PARK-DRIFTED |
| D19 | **Scrollbar thumb geometry**: `colonyscroll.slider` colony_summary/colonyscroll.py:150-191 (`arrows` 194ff); `planetdraw.render_scroll` planets/planetdraw.py:181-198; `ListView.render` core/widgets/list_view.py:175-187; custom_race specials custom_race/renderer.py:250-261 | 4 | colony: `track.h*first//total`, extent from the WINDOW of 10, none below 10. planets: `(track.h - th)*first//(total - visible)`, min length = track width. ListView: `int(track.h*scroll/len)`, min 16. custom_race: fractions, min 20 | colony transcribes colsum.cpp:752-753 (documented). planets cites nothing for the formula; ListView and custom_race are HD inventions | PARK-DRIFTED |
| D20 | **Bounds- and size-guarded snapshot record access**: `colonypick.pops_of` colonypick.py:293-307 and `ColonySend._landed` colonysend.py:238-252 (identical guard block); colonysend.py:108-109; `planetrows._parse_list` planets/planetrows.py:57-59; unguarded on size: boxmodel.py:222-231 `_contact`, maplines.py:158-170, colonyrows.py:434-444 `galaxy_inset_label`, colonyrows.py:760-761 `build_rows` | 7 | `Spec.parse` raises ValueError on a short record (core/structs/__init__.py:99-103). pops_of, _landed, colonysend:109 and planetrows skip short records; boxmodel, maplines and colonyrows parse without the size check (colonyrows' player parse at 752-754 catches ValueError, its colony parse at 761 does not) | pops_of's docstring says a short record "reaches a render path (see `colonyrows.build_rows`)", yet build_rows' colony parse has no guard. Intent unclear; not decided here | PARK-DRIFTED |
| D21 | **Safe index into a table**: `planetwords._pick` planets/planetwords.py:67-68 and `monsterhull._table` core/monsterhull.py:77-78 (identical, default None); `colonyoutput.render_for…word` colony_summary/colonyoutput.py:158-159 (default `"?"`); inline colonylist.py:660 (`"?"`); `colonyplanets.name_for` :51-63 (+ `int()` and None input) | 5 | Default None vs `"?"`; name_for casts | planetwords/monsterhull: none. The `"?"` is a visible placeholder (same spirit as the fill_template note) | PARK-DRIFTED (trivial one-liners) |
| D22 | **Load `screens/<name>/layout.json`** (one statement): colony_summary/screen.py:171-172; galaxy_map/screen.py:118-119; empire_identity/screen.py:76-77; planets/screen.py:71-72; game_menu/screen.py:90-91; new_game/screen.py:92-93 | 6 | The screen name is hard-coded rather than `SCREEN_NAME`. new_game omits `or {}` (a JSON `null` would reach `.get`). The target attribute is `_data` / `words` / `_cfg`. game_menu loads BEFORE `super().enter` | game_menu's order is documented (84-89, work order 125); the new_game omission is not | PARK-DRIFTED (trivial) |
| D23 | **Frame-button hit geometry in ScreenBase**: `_frame_button_side` core/screen_base.py:397-415; `_frame_button_hit` :417-435; both are called on every click (handle_click 148, 151) | 2 | Same geometry (`button_rect_left/right`, collidepoint). One returns `"left"/"right"`, the other the field id. Nested `if r:` vs `r and …` | `_frame_button_side`'s docstring explains why it exists (unwired buttons). Keeping the geometry twice is not explained | PARK-DRIFTED |
| D24 | **Pop-drop walk**: `predict_pops` colony_summary/colonymove.py:325-353; `plan_drop` :356-402 | 2 | The walk statements are identical (after G4's prelude). predict returns `work`; plan counts `landed` and returns a `DropPlan` (with the refusal reason and index) | predict_pops' docstring: "Same walk, returning the state rather than the count". Acknowledged, not justified as a second copy | PARK-DRIFTED |

**Detail D1: what differs between the loaders.**
- Lines 1 to ~18 of each `_load` (path join, `exists` check with an info log naming the extractor, `open`/`json.load` with a warning, the `format < FORMAT_VERSION` stale check) are identical except for three strings: the log label ("building names", "maintext", "ship part names", "estrings", "hestrings"), the extractor path, and the `*_file` function name.
- The tail differs by payload:
  - buildnames and maintext: `{int(k): v}` from `"buildings"`/`"entries"`, state `ok` iff non-empty.
  - shipparts: nine tables, `ok` iff all are non-empty.
  - estrings: a dense list with a checked `ESTRINGS_COUNT` (assign, then clear on mismatch).
  - hestrings: the same check done the other way round (check, then assign). The result is equivalent.
- HelpText differs more: it goes through `res.load_json` (mods resolve) and keeps `_available`/`_stale` booleans instead of a `state`.
- **The five `_load`s bypass `core/resources.py`** (`os.path.join(root or BASE_DIR, …)`), which decision 16 speaks to. A mod cannot override them; HelpText can.

**Detail D2: what differs between the sprite-directory loaders.**
- planets and icons: identical structure. The size check is against `MASTER_SIZE` for planets and `self.master` for icons. Both use `convert_alpha` and nearest `scale`, and **`break` after a refused file** (the next root is not tried).
- surfaces: no size check and no scaling; `convert()`, and only when `display.get_surface()` exists.
- figures: per root, a step file first and then the master; **continues to the next root** after a refusal; two-stage resample.

**Detail D6: what differs between the markup wraps.**
- select_race splits markup runs and loses continuity: "*grow*." becomes two words, so a space is inserted before the ".".
- custom_race keeps punctuation attached across runs (its `_words` docstring).
- select_race measures by `font.size()`. custom_race's render measures with rendered `get_width()`, but its `description_height` measures with `font.size()`, so the two halves of one module use two measures.
- Both use `get_prop_font` directly rather than `style.render_text`.

---

## PARK-DELIBERATE

| id | function(s), file:line | copies | status | evidence | verdict |
|---|---|---|---|---|---|
| P1 | `colonyicons._state` colony_summary/colonyicons.py:124-139; `colonymove.pop_state` colonymove.py:86-101 | 2 | drifted (literal 3/4/2 vs named constants) | colonyicons' docstring: "A second copy of `colonymove.pop_state`, and deliberately not an import: … the smoke test holds them to agreeing"; smoke_test.py:8125-8128 "THE SECOND COPY OF pop_state IS DELIBERATE AND MUST AGREE" | PARK-DELIBERATE |
| P2 | Module `parse(raw)` ×8 and `parse_all(raw_list)` ×7: core/structs/planet.py:129/133, star.py:79/83, ship_icon.py:21/25, nebula.py:38/42, colony.py:348/352, player.py:207/211, ship.py:179/183, settings.py:68 | 8 / 7 | identical one-line facades over `SPEC` | core/structs/__init__.py:15-18 documents `star.parse(raw_bytes)` as the package's usage API ("one module per struct") | PARK-DELIBERATE |
| P3 | `nodes.slot_rows` game_menu/nodes.py:124-126; `nodes.save_strips` :135-143 | 2 | identical bodies (`_rows(fields, TYPE_HIDDEN, SLOTS)`) | Two different original field sets, each with its own citation: loadsave.cpp:263 (load) and loadsave.cpp:279 (save), plus the keyboard-edit semantics in the docstring | PARK-DELIBERATE |
| P4 | `Resources.resolve` core/resources.py:66-76; `Resources.resolve_dir` :97-108 | 2 | drifted (`exists` vs `isdir`) | resolve_dir's docstring: whole-directory override semantics (decision 17) | PARK-DELIBERATE |

(G3's `new_game._scale_background` is the other documented deliberate drift. It is recorded inside G3 and not counted as its own group.)

---

## The eight pre-scan claims

| claim | result | evidence |
|---|---|---|
| `_scale_frame` identical in colony_summary, galaxy_map, planets | **CONFIRMED** | colony_summary/screen.py:401-407, galaxy_map/screen.py:200-206, planets/screen.py:158-164: equal normalised AST dumps (scan.py EXACT group of 3, 6 statements) |
| `_load_frame` identical in colony_summary and planets (name in four files) | **CONFIRMED, and understated** | colony:384-399 and planets:152-156 are identical after docstring removal. galaxy_map:192-198 is semantically identical (a temp `cfg`; token ratio 0.77), making it 3 copies. The fourth file is core/style.py:101 `_load_frame(self, skin_dir)`: an unrelated 9-slice FrameRenderer loader, not a copy |
| `_render_frame_image` identical in colony_summary and galaxy_map | **CONFIRMED, plus a drifted third** | colony:467-472 = galaxy:392-396. planets inlines the first branch at planets/screen.py:189-190 without the (dead) `elif self.USE_FRAME` |
| `cover` / `_make_thumbnail` | **CONFIRMED, and understated** | core/imagebox.py:29-40 vs select_race/renderer.py:142-158: names-only (`base` vs `base_scale`, default arguments); ratio 0.98. Three more value-identical blocks exist: ScreenBase._scale_background, helppopup.Backdrop.surface, galaxy _scale_map_background (G3) |
| `fallback_text_rect` / `busy_text_rect` | **CONFIRMED** | custom_race/popup.py:46-50 = empire_identity/renderer.py:235-239 (exact normalised). Each reads its own module's `FALLBACK_INSET`, whose values differ on purpose. 2 copies, so PARK-TWO-COPIES (T1) |
| `fill` in colonypopup and colonypick | **CONFIRMED, and understated** | colonypopup.py:72-76 = colonypick.py:266-270 (exact, nested functions). A drifted third (`colonyoutput.fill_template`, 109-125) and a fourth (`colonylist._detail_text`, 649-665) exist; fill_template's own note asks for extraction at the third (D4) |
| `message` / `string` in core/hestrings and core/estrings | **CONFIRMED** | core/hestrings.py:93-101 = core/estrings.py:131-146 (exact after docstring). 2 copies (T2) |
| `lift` / `_lift` in core/playercolors and galaxy_map/ships | **CONFIRMED (names-only, not byte-identical)** | playercolors.py:48-49 `tuple(int(round(c + (255 - c) * k)) for c in rgb[:3])` = ships.py:237-238 with parameter `keep=TINT_KEEP_WHITE`. My exact pass did not group them only because of the default argument. The smoke test uses `playercolors.lift` as a stand-in for `_lift` (smoke_test.py:15363) (T3) |

No pre-scan claim was refuted. Four understated the group: `_load_frame`, `_render_frame_image`, `cover` and `fill`.

## Cautions for any extraction

- **Marking inventory.** smoke_test.py:6280-6300 walks every `.py`/`.json` for "HD EXTENSION"/"DEVIATION" and compares the set of files against `_MARKED` (6164ff). A move that carries a marked comment into a file not on that list, or empties one that is, fails the run.
- **One-home greps.** squish_step (8794), the plate radius (12113) and `palette.init(` (15414) are asserted by tree-wide text search. None of G1-G4 touch those strings.
- **Source-slice checks.** These are anchored on method bodies in files G1-G3 edit: `def _render_list(` in colony screen.py (12514), `def _render_map(` in galaxy screen.py (15484, which needs `surface.blit(self._map_bg_scaled`), `native_width` absent from colony screen.py (11306), and "coldraw.cpp:60" and "TRANSCRIPTION" present in colony screen.py (11865-11877). The extractions above do not touch these strings, but whoever does the work should re-read them.
- **Line-count guideline** (decision 6, `tools/linecount.py` code lines): core/screen_base.py 262, core/imagebox.py 50, colony_summary/screen.py 298, planets/screen.py 274, galaxy_map/screen.py 583 (listed exception), colonymove.py 191.
