# The fundament, part 9 of 9 — orion2re and pygame facts

Details that are cheap to look up and expensive to get wrong: the orion2re facts and the pygame facts.

**Decisions in this part:** no decisions.

The index is [`../v3_fundament.md`](../v3_fundament.md), and it is
what to read first. This file is one part of the fundament and
carries no rule that is not in it; the text below is what stood in
`doc/v3_fundament.md` before work order 164 moved it, unchanged.

<!-- fundament-body -->
## 3. orion2re facts worth memorising

Details that are cheap to look up but expensive to get wrong. Full
references in `doc/v3_orion2re_index.md`.

- `INJECT_CLICK` needs both DOWN and UP; DOWN alone hangs the game.
- `ACTIVATE_FIELD` works through `g_pending_field`, consumed by the
  early exit in `Get_Input_()`.
- Radio buttons (type 1) never respond to `ACTIVATE_FIELD` — the
  toggle happens inside `Interpret_Mouse_Input_()`, which the early
  exit skips.
- Prefer `ACTIVATE_FIELD` whenever the target code compares field IDs.
  `Flag_Screen_` compares `Get_Input_()`'s return against its eight
  hidden-field IDs.
- **Field types are not what they look like.** Banner tiles are hidden
  fields (type 7), not radio buttons. Detect by geometry, not by type.
- **A screen that ignores an injected click and key may still take
  `ACTIVATE_FIELD` on its screen-filling hidden field.** Measured in work
  order 123's eta run, 16 September 2026: the colony landing screen (screen
  33, `COLLAND::Colony_Landing_Screen_`, a plain `Get_Input_` loop at
  colland.cpp:203-213) listed a dummy and one type-7 field at (0, 0)-(639,
  479) with no hotkey. An `INJECT_CLICK` at (320, 240) and an `INJECT_KEY`
  ESC left it standing, each checked on the framebuffer; `ACTIVATE_FIELD 1`
  ended it, and the "just colonized" message box after it (a full-screen
  type-7 field with hotkey ESC) and the turn summary's CLOSE went the same
  way. Why the injected input is not taken is NOT established. **The GNN
  screen of work order 122** (screen 0 with the same two-field list, which
  took neither a click nor ESC) **is inferred to be the same case, not
  confirmed**: it was not re-tested with an activation.
- `inject_key(ESC)` can cascade across sub-screens.
- **The server only talks inside an input loop.** `ext::Tick()` is
  called from `fields::Get_Input_()`, so galaxy generation, turn
  processing and savegame loading are periods of total silence — a
  connection that looks dead is usually a game that is busy. A
  reconnect during one is worse than the silence: `accept()` also
  runs in `Tick()`, so the new connection sits there without even a
  HELLO_REPLY, which is the tell in the log.
- **The home star name is not part of race selection.**
  `racesel.cpp` asks only for the ruler name and the banner; the game
  then returns, generates the galaxy, and asks for the home system on
  the main screen. Anything driving those three dialogs as one
  sequence has a mapgen sitting between the second and the third.
- **Galaxy-map zoom-in (field 8) is a trap.** It leaves the game in a
  darkened rubber-band selection state a client cannot escape. Field 9
  (zoom-out) is safe. Nothing in OrionLayer activates 8.
- **A right click is not always Cancel.** `fields::Get_Input_()`
  checks the active help list first (`Check_Help_List_`,
  fields.cpp:2916); over a help rectangle it draws the entry and
  returns 0, and only outside one does the right button return -1.
  Every screen installs its table through `fields::Set_Help_List_`,
  and the tables are in `evanhelp.cpp`, `erichelp.cpp` and
  `billhelp.cpp`. Help text lives in the game's own `HELP.LBX`, not
  in the source and not on the Extension API.
- **A POP MOVE RECALCULATES THE WHOLE PLAYER'S FOOD DISTRIBUTION, so
  colonies nobody touched come back different.** `Send_Cluster_`
  (colmove.cpp:460-463) always ends in `Col_Calc_Wrapper_`
  (colony.cpp:1091) -> `Colony_Calculation_` (colcalc.cpp:1580) ->
  `Recalculate_Colony_` (colcalc.cpp:519-524) ->
  `COLCALC::Pass_Out_Imports_` (colcalc_main.cpp:208), which
  redistributes food across the empire:

  - `imports[ECON_FOOD]` on **every** non-outpost colony of the owner
    that is not in a space anomaly — `= 0` for a deficit
    (colcalc_main.cpp:222), `= -balance` for a surplus (:228), `++` in
    the three distribution passes (:254, :268 and the third);
  - `pop_growth`, `pop_roundoff` and `specialty` on every **NEEDY**
    colony — food balance below zero and not blockaded
    (colcalc_main.cpp:217-226) — because :341-352 calls
    `Post_Import_Computing_` for each entry of `needy_colony_indices`,
    which is `Colony_Pop_Grows_` (colcalc.cpp:760-810) plus
    `Colony_Specialty_` (colcalc.cpp:736).

  `pop[]` is written for the moved colony only. So "exactly one
  colony's record changed" is NOT a property of a pop move, and an
  acceptance run that asserts it fails on a real one;
  `colonymove.move_diff_verdict` is that rule with the fields named.

- Galaxy size never scales anything. It caps `_max_zoom_count`, which
  caps the reachable zoom levels — and zoom level is what scales.
- **`_max_map_scale` is `max(ceil(MAP_MAX_X*10/506),
  ceil(MAP_MAX_Y*10/400))`**, and the community Maximum size is now
  covered — corrected 7 September 2026. Neither `_max_map_scale` nor
  `_max_zoom_count` is serialized; both are recovered from the two
  extents, which are. The expression is
  `MAPGEN::Maximum_Galaxy_Display_Scale_` (mapgen.cpp:64-71), whose
  own `map_width`/`map_height` are character for character what the
  same branch assigns to `_MAP_MAX_X`/`_MAP_MAX_Y` (mapgen.cpp:
  1113-1115) — so the extent is read off the wire rather than rebuilt
  from a star count. It reproduces the four stock sizes' literals as
  well (506/400 → 10, 759/600 → 15, 1012/800 → 20, 1518/1200 → 30),
  so **one expression covers all five galaxy sizes**.

  **BOTH ceilings, and it is a CEILING.** What stood here was
  `MAP_MAX_X / _max_map_scale` being "a constant 50.6", measured from
  the four stock sizes and inverted with commercial rounding. The
  constant is real at those four sizes; the *rounding* is not the
  original's operation, and the y term was missing entirely. Result:
  exactly one too small — never too large — for 688 of the 951 star
  counts in 73…1023, at 15 distinct map widths, with the x ceiling
  the larger at 11 of them and the y ceiling at 4. The reference save
  is one of the counts where it happened to be right, which is why it
  survived every acceptance run.

  50.6 still appears in the tree, and it is a different fact there:
  `506/10` is the map viewport's own reach per scale unit
  (movebox.cpp:19-20), which is what the galaxy inset's 506000 and
  400000 divide by. Cite it to movebox.cpp, never to a scale
  recovered from a width.
- **The map viewport is 506 x 400, and 505 x 399 is the same
  rectangle counted differently.** `MAINSCR::Draw_Influence_Overlay_`
  declares it — `map_left = 22, map_top = 22, map_width = 506,
  map_height = 400` (mainscr.cpp:161-164) — and the galaxy map's
  field 23 arrives on the wire as (22, 22)-(527, 421), the same
  506 x 400 counted inclusively. `MAINSCR::Star_On_Screen_`
  (mainscr.cpp:399-410) then admits the near edge (`x > 0x15` passes
  at 22) and excludes the far one (`x < 0x20f` stops at 526), so a
  STAR reaches 505 of those columns and 399 of those rows. The
  rectangle is what a scale has to cover, so the rectangle is what
  the two ceilings divide by; 505 x 399 is `mapcoords.MAP_WIDTH`'s
  number and belongs to hit-testing, not to zoom. Not two constants —
  one rectangle, inclusive against exclusive.
- At `_max_map_scale` the game's own viewport therefore covers the
  galaxy by construction rather than by luck, at every size including
  Maximum: the last 1-3 units on the far edge (Small 1, Medium 2,
  Large 2, Huge 3) fall in the column a star cannot occupy anyway.
  That is what lets a parked game serve clicks for a decoupled HD
  view.
- **A sequence of `ACTIVATE_FIELD`s must be sent one at a time and
  confirmed; a batch is silently collapsed to the last one.**
  `ext::g_pending_field` is a single `int16_t`, and `ProcessInput()`
  drains the whole input queue in one loop before the game consumes
  it — so *n* activations sent together leave *n-1* discarded, with
  no refusal and no report. `INJECT_CLICK` queues properly through
  SDL and is unaffected; only field activation has the single slot.
  The mechanism is in `doc/ext_api_dokumentation_v3.md`, which owns
  it; the rule is here because it decides the SHAPE of every
  multi-step injection.

  **Observe the effect, do not count the sends.** Where the effect is
  not on the wire, it may still be on the screen — the colony
  summary's `_first` is not serialised but is drawn, as the scroll
  thumb's position (`Draw_Bar_Indicator_`, colsum.cpp:747-771).

  **And observing is harder than it looks: see "A fresh message is
  not a fresh world" under Diagnosis before writing one of these
  loops.** This paragraph used to name `tools/zoom_probe.py` as an
  example to copy — *"activates, waits for a fresh snapshot,
  compares, and stops when nothing moved"* — and that was a
  description of a tool that actually drained frames for a fixed
  0.6 s. It worked, because 0.6 s is about twelve snapshots and the
  effect needs two, and it was cited in two documents as this
  project's event-driven pattern while being a timed one. Audited and
  corrected 5 September 2026. `viewctl.park_game` is the one that was
  always right, and for a reason worth naming: it stops on an
  ABSOLUTE target rather than on a comparison with the previous
  reading, so a stale snapshot costs it one redundant step and never
  a wrong conclusion.

- **Population moves on the colony screens are click-click, not
  drag** (`colsum.cpp:851`). The first click on an icon calls
  `COLMOVE::Get_Cluster_`, which unassigns that pop and every
  *identical* one after it in the array (same job, state, race,
  conquered flag — `Pops_Identical_`); the second click on a job
  column calls `Send_Cluster_`. **Which of the two a click is comes
  from `_cluster_colony_n`, not from where it lands**
  (`colsum.cpp:861-870`): with no cluster held it is a pick-up, with
  one held it is a drop, wherever it lands. `Get_Cluster_` is never
  reached while a selection exists, so there is no "replace".
  Within an identical group the icons are drawn in array order, so
  clicking icon m of a group of size G moves G-m+1 pops **when the
  group is contiguous** — `Get_Cluster_` scans to the END of the
  array and takes every identical pop, so a group split by a
  different pop takes more than the run under the cursor.

  **The drop rules in `Give_Colonist_New_Job_` are FOUR, not five**
  (`colmove.cpp:518-558`, corrected 4 September 2026): natives cannot
  take research or industry, androids (`pop_state == 4`) keep their
  job, at most 42 per job (`Sum_Colonists_ >= 42`), and farmers at
  most `max_farms` unless the move is an inter-colony transfer. The
  fifth — a click on another colony being a transport with an ETA
  dialog — is not in that function at all; it is the long branch of
  `Send_Cluster_` (`colmove.cpp:180-500`).

  **A fifth refusal sits at the FIRST click**, which that count
  missed entirely: `Get_Cluster_` rejects a native outright
  (`pop[i] & 0x0F == 9`, `colmove.cpp:59-64`), shows its own ESTRING
  and never sets `_cluster_colony_n`. Natives are refused twice, in
  two places, with two different messages.

  Two things about the native rule. Its test is `pop_state == 3 ||
  pop_state == 6`, and **state 6 is unreachable**:
  `Pop_To_Pop_State_` (`colony.cpp:1240`) returns 3 for low nibble 9,
  4 for 8 and 2 for everything else, and there is no other
  definition — so the `== 6` arm is dead and the rule reduces to the
  same nibble-9 test the pick-up uses. And **its message disagrees
  with its behaviour**: the string says natives can only farm *or
  mine*, while the code refuses `ECON_RESEARCH` and `ECON_INDUSTRY`
  and leaves only `ECON_FOOD`.

  **A refused drop is partial, not atomic.** `Send_Cluster_` returns
  the moment `Give_Colonist_New_Job_` says no (`colmove.cpp:168-173`),
  leaving the pops it already moved in their new job and the rest
  unassigned with the cluster still held.

  **AND EVERY REFUSAL OPENS A BLOCKING MESSAGE BOX — 5 September
  2026, and this is the half that changes what a client may do.**
  All four refusals in `Give_Colonist_New_Job_` (`colmove.cpp:527`,
  `:534`, `:541`, `:556`) and the pick-up's native refusal
  (`colmove.cpp:61`) answer with `GENDRAW::Help_`, which is
  `TEXTBOX::Do_Text_Box_`, whose input step is
  `do { … } while (fields::Get_Input_() == 0)` (`textbox.cpp:149`).
  The game sits in that loop until something clicks or types. It
  still TALKS — `ext::Tick()` runs from `Get_Input_()`, so snapshots
  keep arriving — which is precisely what makes the state easy to
  miss: the wire looks healthy and the game has left the screen the
  client is drawing.

  So a refused injection does not merely fail quietly. It parks the
  game in a modal the HD screen does not draw, over a screen the
  player can no longer reach, with a cluster still in hand. That is
  the strongest form of decision 33's argument found so far, and it
  is what makes "refuse before sending" the only state an HD screen
  can guarantee it can leave. The box adds a hidden field over the
  whole screen (`textbox.cpp:246`), so one injected click would
  probably dismiss it — probably, and nothing is built on it.

  **There is no cancel that stays on the screen.** Both
  `Clear_Cluster_` call sites on the colony summary (`colsum.cpp:804`
  and `:938`) are leave-the-screen paths. Clearing IS a true undo —
  `Get_Cluster_` only clears bit `0x200` and `Clear_Cluster_` sets it
  back, job bits untouched — but the only ways to reach it are
  leaving the screen or dropping the pops somewhere. Any HD preview
  that creates a real selection therefore strands the player, which
  is why a preview must not inject.

  **The pick-up reads the POINTER, not the click point — and the
  chain has one more link than this entry said until 5 September
  2026.** `Get_Selected_Pop_` (`colsum.cpp:1006`) does NOT call
  `Do_Colony_Info_Pop_Stuff_For_Pop_` in its pointer mode. It passes
  **mode 3**, whose test reads `*scroll_value_ptr`
  (`coldraw.cpp:361`); mode 4 is the one that reads
  `mouse::Pointer_X_()` directly (`coldraw.cpp:367`) and is not what
  this screen uses. The value comes from the SCROLL FIELD that mode 1
  added over the column (`coldraw.cpp:409`), and
  `fields::Find_Bar_Position_` (`fields.cpp:1702-1743`) writes it out
  of `mouse::Pointer_X_() + _pointer_offset` when the field is pushed
  down (through `Draw_Field_`, `fields.cpp:2837`). The field's range
  is built so that arithmetic reduces to the identity — the value IS
  the pointer x, clamped to `[left_x, right_x]`.

  The conclusion is unchanged and the extra link is not decoration.
  The value SURVIVES between clicks, because nothing resets it, so a
  column carries whatever it last held; `_pointer_offset` is the
  current mouse picture's frame number (`mouse.cpp:115`) and is added
  to it; and `Draw_Field_` returns early while `_draw_fields_flag` is
  0, in which case the value is not written at all. None of the three
  is worth reasoning about from outside — which is why an injected
  pick-up is VERIFIED against the cluster the game actually took
  (the bit is on the wire) instead of being trusted.

  **CORRECTED 4 September 2026: an injected click cannot supply that
  pointer, and the window size is not why.** `INJECT_CLICK` does set
  the position before enqueuing the button
  (`Set_Present_Mouse_Position_` then `Enqueue_Mouse_Input_Event_`,
  platform.cpp:1171-1172) — so the claim that the click carries its
  own pointer is true of that instant and false a frame later.
  `Sync_Mouse_State_From_SDL_` (platform.cpp:825-846) re-reads the
  REAL mouse and calls `Set_Present_Mouse_Position_` again, from the
  main loop (`:390`) and from the event service (`:1127`), so the
  injected position is overwritten before the game consumes the
  click.

  The click's FIELD still resolves from the enqueued coordinates, so
  the right row and column are hit; only the ICON lookup reads the
  clobbered pointer, and it finds nothing where the real mouse is not
  standing. `Get_Selected_Pop_` returns -1, `Get_Cluster_` is never
  called, and the observable result is a click that does nothing at
  all — measured, 4 September 2026, twice.

  **The one lever is focus:** the sync returns early when
  `g_window_focus_state == 0` (platform.cpp:826). So an injected
  pointer survives only while the game window is NOT focused, and
  nothing on the wire reports focus. This is `doc/orion2re_open_fixes.md`
  item 3, and it means that item's proposed fix — bypass the
  coordinate mapping — is not sufficient on its own.

  Icon x is
  `(30 - squish) * i + left_x` with `squish` from
  `Calculate_Squish_Step_` (`coldraw.cpp:12`), where `30 / -3` is C
  truncation toward zero — `int(a / b)` in Python, never `//`. Column
  edges on the summary screen: farmers 101-226, workers 236-368,
  scientists 378-502.

  **THE ROW HAS TWO Y VALUES AND THEY ARE FOUR PIXELS APART** —
  corrected 8 September 2026, when this entry carried only the second
  and a reader would have drawn the sprites at the field's y. The
  ICON ROW is `31*i + 38`: `Draw_Info_Pop_For_` passes
  `list_idx * 0x1f + 0x26` (`colsum.cpp:683`), and BOTH hit tests
  pass the same — `Get_Selected_Pop_` (`colsum.cpp:1006`) and
  `Get_Scanned_Pop_` (`colsum.cpp:963`). The FIELD's y is `31*i + 34`
  with a height of 30 (`Add_Fields_Pop_For_`, `colsum.cpp:311`), so
  the clickable band is `31*i+34 .. 31*i+64` and the sprite row
  starts four px into it. Neither number replaces the other: the
  first is where the icons are, the second is the drop rect, and the
  four pixels between them are the gap.

  **THE PICK READS A PIXEL AND THE DROP READS A FIELD — one gesture,
  two opposite sensitivities, and only the field's MODE separates
  them.** Measured 9 September 2026, thirteen points across two
  columns, identical struct diff at every one.

  The DROP is insensitive by construction. Mode 1's post-loop adds
  `fields::Add_Scroll_Field_(left_x, top_y, …)` (coldraw.cpp:409) and
  `COLSUM::Evaluate_Colony_Pop_Input_` turns a hit on it into
  `Send_Cluster_(colony, job)` (colsum.cpp:869) — which field was hit
  is the whole of the input. Centre, all four corners, the plate's
  own 1 px line and a point over an existing figure all produce the
  same bytes, in an empty column and a populated one alike.

  The PICK on the SAME SCREEN, through the SAME kind of field, is
  sensitive to a single pixel: `Get_Selected_Pop_` (colsum.cpp:1006)
  passes mode 3, whose test reads `*scroll_value_ptr`
  (coldraw.cpp:361), which `fields::Find_Bar_Position_`
  (fields.cpp:1702-1743) writes out of `mouse::Pointer_X_() +
  _pointer_offset`. The value survives between clicks because nothing
  resets it, and it is the pointer's x clamped to the column.

  **The consequence for anything that drives this screen**: a drop
  may be aimed anywhere inside the cell and a pick may not be aimed
  at all — it has to be verified against the cluster the game
  actually took, because the number it depends on is not on the wire
  and is overwritten by `Sync_Mouse_State_From_SDL_` before the game
  consumes an injected click (decision 39's correction). Two halves
  of one gesture with completely different failure modes is exactly
  the shape a reader assumes away, which is why it is measured here
  rather than argued.

  **THE DROP RECT IS THE WHOLE COLUMN CELL, AND AN EMPTY COLUMN HAS
  ONE.** Mode 1's post-loop ends in `fields::Add_Scroll_Field_(left_x,
  top_y, left_x, right_x + 8, left_x, right_x, right_x - left_x + 8,
  30, …)` (`coldraw.cpp:409`), and it runs after a walk that may have
  drawn nothing — so x `101..234` / `236..376` / `378..510` accept a
  drop whether or not the column holds an icon. Worth writing down
  because the obvious reading is the opposite one: the HD side
  carried a marked HD EXTENSION for three days on the belief that an
  empty job needed a target of ours.

  **A DROP ON THE COLONY NAME IS "PUT THEM BACK".**
  `_list_fields[i]` with a cluster held is `Send_Cluster_(_list_col[i],
  -1)` (`colsum.cpp:909`), and on the colony the cluster came from
  that is the re-flag branch — `requested_job == -1` sets `0x200` back
  and consults no rule (`colmove.cpp:161-165`), so the array ends
  exactly as it started. It is the nearest thing this screen has to a
  cancel that is not a leave-the-screen path.

  **THE HELD CLUSTER HANGS ON THE POINTER AND THE ROW SIMPLY LOSES
  IT.** `Get_Cluster_` clears `0x200` (`colmove.cpp:70`) and the icon
  walk's innermost test is `(pop_val & 0x200) != 0`
  (`coldraw.cpp:336`), so the held pops stop BEING icons — the row
  shortens, and the squish shortens with it because every mode runs
  the same mode-2 pre-pass over the same walk (`coldraw.cpp:301` ->
  `:419`). There is no `count - n` anywhere in the original and there
  must be none in a transcription of it. What is drawn instead is
  `COLMOVE::Draw_Cluster_` (`colmove.cpp:7-37`), called last with the
  raw pointer (`colsum.cpp:509-511`): the pointer picture is REPLACED
  by `C_Anims_(15)` rather than hidden, and each held pop is drawn at
  `x + 5 + 20*k, y - 10` in ARRAY order — which is not the icon
  walk's order.

  **AND THE ORIGINAL MARKS NOTHING ELSE ON THIS SCREEN.** The only
  `Fill_`/`Line_` calls in `colsum.cpp` are the scroll thumb
  (`colsum.cpp:759-765`). No frame round a picked cell, none round
  the row it came from. The one per-pop state it does draw is the
  HOVERED icon blinking dark (`coldraw.cpp:342-343`), which is a
  hover and not a selection.

  **"No Farming" is CENTRED IN THE COLUMN**, printed in mode 0 when
  `max_farms == 0`: `Squeeze_Print_Paragraph_(left_x, top_y + 5,
  right_x - left_x, 28, E_Strings_(387), 2)` (`coldraw.cpp:315-321`),
  where the 2 reaches `_Print_String_Bill_` as the mode that selects
  `fonts::Print_Centered_(x + width/2, y, str)`. Measured against the
  original's own screen: ink centre 163 = `101 + 125/2`, ink top 136
  = `top_y + 5`. Its SIZE is not in any source — `Set_Colony_Font_
  To_(3)` is a style index and `_font_header.font_heights[3]` comes
  from the player's FONTS.LBX — so 10 px of cap height off a
  screenshot is the only number there is, and it is MEASURED, single
  source, like `SHIP_ICON_DIM` is DERIVED.

  **The scan box is TWO boxes.** `Draw_Colony_Scan_Info_`
  (`colsum.cpp:1155`) fills a formatted paragraph at native
  (13, 354, 80, 88) over `E_Strings_(74)` and the four production
  rows plus morale from native x 106. The paragraph is FIVE lines and
  not six label/value pairs — size and climate share one, growth
  carries no label — and the format supplies the nouns (`%sravity`,
  `Mineral %s`) while the string tables hold the bare quality. Its
  sign string is taken TWICE, before the first word and before the
  number, with the reset after the last, so a negative growth reddens
  the WHOLE box.

  **A COLUMN IS NOT `pop[]` IN ARRAY ORDER.** The icon walk is five
  nested loops (`coldraw.cpp:326-337`): state
  (`Pop_To_Pop_State_`, so normals, then natives, then androids),
  then the conquered bit `0x400`, then the low nibble in the order
  `(9, 0, 1, … 8)`, and only innermost the array. So "within an
  identical group the icons are drawn in array order" is exactly
  true and exactly as far as it goes — a group is (state, conquered,
  nibble), which is what `Pops_Identical_` compares, and the icon at
  slot m of a column is NOT the m-th pop of that job. Only ASSIGNED
  pops are icons (`coldraw.cpp:336`), which is how a held cluster
  disappears from the screen.

  Measured on the reference save, 5 September 2026: a colony with
  twelve farmers and one scientist held the scientist at pop 11 and
  the last farmer at pop 12, so the column's last icon was pop 12.
  A click past every icon took pop 12 — array order would have said
  11. `screens/colony_summary/colonyicons.py` is that walk,
  transcribed.

  **The whole two-click move has now been driven from an HD screen**,
  5 September 2026, with `doc/ext_inject_click.patch` in the running
  binary: a real mouse click on a pop square, a second on a job
  column, and the whole colony array diffed against a prediction made
  before either. Exactly the predicted pop moved and no other colony
  changed. What that run did NOT exercise is any refusal — see the
  status document, because the reference save has no native, no
  android, no colony that cannot farm and nothing near the 42 cap, so
  every plan in it predicts "all".
- **The displayed maximum population is computed, and the size table
  is only its base.** `MOX::_planet_max_population[] = {5, 10, 15,
  20, 25}` (mox.cpp:796) is indexed by `PLANET_SIZE`, and reading it
  alone is wrong. `COLCALC::Planet_Max_Population_For_Player_`
  (colcalc.cpp:896) applies a climate factor from
  `_size_climate_max_pop_lookup[] = {25, 25, 25, 25, 25, 25, 40, 60,
  80, 100}` (colcalc.cpp:57), adds 25 for an environment-immune race,
  caps at 100, then rounds `(factor * base + 50) / 100`; Subterranean
  adds more and Advanced City Planning a flat +5, and on a colonised
  planet the result is the best limit over the races present.
  **Worked example, because the gap is small enough to look like a
  rounding difference:** Ixion II is Small(1) Ocean(5), so the base
  table says 10 — and the game prints 5, because Ocean is a 25 %
  climate and the owner's +25 immunity brings the factor to 50 %.
  Verified against the original's own planet description on 31 August
  2026. **Consequence: an HD bar whose length is proportional to
  maximum population reimplements that function, never the table.**
  A bar built on the table alone is twice too long on exactly the
  planets a player looks at most, and nothing about it looks wrong.

- **The engine version lives in two literals, not one.**
  `src/version.h` has `ENGINE_VERSION[] = "1.60.0"`; `consts.h` has a
  separately written `GAME_VERSION_LABEL[] = "Version 1.60.0"`, and
  that second one is what the main menu prints
  (`mainmenu.cpp:295`). They can disagree with each other, which is
  why `tools/version_check.py` reads both.
- **The DEMO Bank Gothic substituted 28 characters**, measured 29
  August by hashing every printable glyph:
  `! " # $ % & ' ( ) * + - / 4 < = > @ [ \ ] ^ _ ` { | } ~`
  **The digit 4 was in that list.** It had been rendering as the
  watermark in every number since the font was adopted, unnoticed
  because the eye reads the watermark as a smudge rather than as a
  wrong character. Replaced on 31 August by **Aldrich** (Matthew
  Desmond, SIL Open Font License) — see decision 41. The detection
  machinery stays and now reports nothing, which is exactly what it
  was written to do for a clean font.
- **A SESSION-LAUNCHED ENGINE HANGS IN ITS FIRST LOGO FRAMES WHEN ITS
  WINDOW IS NOT BEING DRAWN — the start hang of 139 E, 169 and 170,
  explained by work order 174 A (26 September 2026).** It sits beside
  CLAUDE.md's live-run protocol because it is the part of that protocol
  that was open. **Where**, from backtraces of hung starts: the game
  thread in `JIM::Draw_Logos_` waits, with no timeout, for a present
  (`video::Submit_Palette_` / `Publish_Off_Page_`); the main thread is
  in that present — `SDL_RenderPresent` with VSync on (platform.cpp:644,
  :1390), inside the NVIDIA GLX swap, in `drmSyncobjTimelineWait`. The
  last log line, "data space allocated", is where it stopped
  (`SDL_LogInfo` is unbuffered stderr). **When**: a VSync present to a
  window the compositor is not drawing can wait forever — measured with
  a full-screen game covering the monitor (8 hangs in 60 starts of the
  same unchanged command), and very likely the locked, blanked screen
  of 169's unattended run (GNOME blanks and locks after 300 s idle).
  **Not the cause**, each changed alone: the parent process, `nohup`,
  a new session, an idle inhibitor, the window minimised, disabling
  explicit sync (the wait moved to `xcb_wait_for_special_event`), the
  Vulkan renderer (to `VULKAN_AcquireNextSwapchainImage`), the software
  renderer. **What removed it**: not waiting for VSync — open fix 31,
  `doc/ext_present_no_vsync.patch` (`ORION2RE_NO_VSYNC=1`, NOT
  APPLIED), 0 hangs in 50 starts of a scratch build. Until it is
  applied, `tools/engine_start.py` recognises the hang by its signature
  and starts again. Two readings from before 174 stand corrected:
  `drm_syncobj_array_wait_timeout` alone is NOT a hang — a healthy
  engine waits there most of every frame — and a hang is told apart
  from the intro cinematic, which holds the log at the same line, only
  by the two threads' waits over several samples.
- **A LIVE RUN WRITES MORE THAN THE SAVES — work order 175, after 174.**
  The game writes, found in its source: SAVE1-10 (`Save_Game_`,
  filedef.cpp:64; SAVE10 is the autosave TURN writes), `MOX.SET` after
  every save AND when a loaded game is left for New Game
  (`Save_Game_Settings_`, filedef.cpp:24/82 — with the LOADED SAVE's
  settings, since a save carries its own, savegame.cpp:1368; in 174 that
  set `active_save_slot` to the scratch slot), `HOF.M2` (score.cpp:205,
  :614), `lastrace.rac` (racesel.cpp:704), `TEMP.TMP` (swap.cpp:24), and
  a new `logs/game.<pid>.log` beside its binary per process. OrionLayer
  writes `user_settings.json` (and `.tmp`, `.corrupt`) and, through the
  F5 editor, files in the tree. `tools/liveguard.py` backs up every one
  of them before a live run (`engine_start.py` calls it before the engine
  exists) and names every change after — changed, appeared, vanished —
  with `--restore` to put it back; the scratch slot a run saves to is
  the only file it may `--allow`.
- **AN ENGINE THIS SESSION DID NOT START — work order 176 (Data), WHILE
  DATA DOES NOT PLAY.** It replaces 171's "never connect, never kill":
  an orion2re or an OrionLayer client found running that Claude Code
  did not start is a leftover from Data looking at screens, not a game
  in progress, and may be closed — `tools/liveguard.py` first (the
  backup of every file a run can write), then SIGTERM, a few seconds,
  SIGKILL only if it is still there, and PID, command line, start time
  and how it ended recorded in the progress file
  (`python tools/engine_start.py --close-foreign` does all of it). It is
  still NEVER connected to — close it and start your own. When Data plays
  again he says so, and 171's rule is back.

---

## 4. pygame facts worth memorising

Same category as section 3, different library.

- `set_alpha(None)` does not mean "no extra alpha". In pygame 2 it
  selects `SDL_BLENDMODE_NONE`, which ignores the per-pixel alpha
  channel entirely and draws the sprite's whole bounding box opaque.
  To leave a per-pixel-alpha surface alone, do not call `set_alpha`.
- `transform.rotate` does not filter; `transform.rotozoom` does.
- `transform.rotate` returns the bounding box of the rotated
  rectangle and maps the source centre onto `(rw/2, rh/2)` exactly.
  The edge length is even at some angles and odd at others, so
  centring with `//` truncates in a direction that changes per frame.
- The alpha bounding box of a rotated sprite is **not** rotation
  invariant, even for circular content — the unfiltered edge gains
  and loses pixels per angle. Measured range on one 192 px master:
  179x183 to 185x186.
- `BLEND_RGB_ADD` ignores alpha, so RGB hiding under transparent
  pixels becomes a visible rectangle. Blank it in the asset rather
  than relying on every draw path to blend normally.
- A 9-slice assembled from tiles has a **transparent centre** unless
  the centre tile is opaque. Anything that must hide what is behind
  it fills its own rect first.
