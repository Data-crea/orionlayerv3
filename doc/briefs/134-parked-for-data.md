# Work order 134 — parked for Data

The Fleets screen is **built, NOT accepted**. Everything below needs
either a running game or a decision, and neither is available to the
session that built it.

---

## 1. The live acceptance — PARKED, and why

`:0` is not reachable from this session (`xdpyinfo -display :0` fails;
the game hangs at "mox2: data space allocated"), so no client was
connected and no field list was ever read from a running engine. The
two engine patches **compile and parse; nothing has driven them.**

Both patch headers and both `tools/version_check.py` entries say
`NOT CONFIRMED LIVE`, and a smoke check holds that sentence in the
patches.

### The steps, in order, under work order 126 rule 8

Rule 8: exactly one client, scratch saves SAVE4/SAVE5 only, **never
SAVE8**, hash SAVE1–9 and SAVE11 before and after, SAVE10 logged only.
If Data's own orion2re or OrionLayer is already running, do not connect
a second client — stop here.

1. **Build and start.** `cmake --build ~/orion2re/out/build/Linux/linux-debug`,
   then start the engine. The tree must be at `e6199966` on
   `orionlayer-local` (both patches), which `python tools/version_check.py`
   reports as APPLIED.
2. **Reach the screen.** Load SAVE5. On the galaxy map, the Fleets
   button is the only door: `mainscr_main.cpp:632-643` is the only
   assignment of `_current_screen = SCREEN_FLEET`. HD's map sends
   `ACTIVATE_FIELD 12` for it (`screens/galaxy_map/layout.json:35-38`) —
   **that id was never re-checked and is the first thing to verify
   against the live field list.**
3. **Evidence 1 — the block arrives.** With the screen up, dump the
   snapshot and confirm a `FLTS` block after `FSEL`. Record
   `_small_ship_stack_ptr`, `_fltscrn_stack_owner`,
   `_n_fltscrn_big_icons`, `_n_fltscrn_big_icons_added`,
   `first_visible_row` and the per-icon `ship_idx`/`selected` list.
4. **Evidence 2 — the validation holds.** Read the field list in the
   same step and confirm one type-7 field at `(x, y, x+58, y+57)` for
   each displayed cell, `x, y` from `Get_Fltscrn_Big_Icon_XY_`. This is
   what `fltwire` refuses on; a live disagreement means the read is
   wrong, not the check.
5. **Evidence 3 — the framebuffer and the HD picture, side by side**,
   for the same stack, at 1920x1080.
6. **Evidence 4 — one ship selected from outside.** Send
   `MSG_SELECT_SHIP(ship_idx, 1)` for a ship in the grid and confirm in
   the NEXT-but-one snapshot (`wire_protocol`'s one-pair rule) that its
   `selected` flag turned on, that `_n_big_icons_selected` rose, and
   that the SCRAP field appeared in the field list. Then send 0 and
   confirm all three go back. **This is the one thing open fix 28 exists
   for and the one thing nothing has shown.**
7. **Evidence 5 — the three refusals the command must make**: a foreign
   stack (walk NEXT until `_fltscrn_stack_owner != _PLAYER_NUM`),
   relocate mode 1, and a ship_idx not in the list. Each must leave the
   block unchanged.
8. **Evidence 6 — the two filters.** Send `INJECT_CLICK` at the live
   SUPPORT field's centre and confirm `_fltscrn_support_button_status`
   flips in the block and the icon list changes. Then confirm that
   `ACTIVATE_FIELD` on the same field does **not** flip it — that is the
   reason HD clicks instead of activating, and it has only been read,
   never measured.
9. **Evidence 7 — PREV/NEXT and the two scroll arrows** change `stack`
   and `first_visible_row` in the block.
10. **Evidence 8 — the map is intact after RETURN.** Leave the Fleets
    screen back to the galaxy map and check two things before anything
    else is sent. First, that every stack is drawn where the original's
    own framebuffer draws it, side by side at 1920x1080 — a stack still
    carrying the inset's coordinates sits in the top-left corner of the
    map and nothing else on the screen looks wrong. Second, that a
    click on a stack means THAT stack: click one and confirm the fleet
    box that opens is the one clicked, by the ships it lists, not by
    the box appearing at all.

    This is what work orders 135 B and 136 B built the gate for —
    `ships.ScreenStateGate` takes `s_ship_icon` from screen 0 and from
    no other screen id, held by a smoke check on real bytes through
    `parse_state`. The check
    proves the rule offline; only the live run proves the array comes
    back from the engine the way `mainscr_main.cpp:314-315` says it
    does. `MOX::_cur_map_scale` is gated with it as of work order 136
    (`flt.cpp:14`, saved and restored at `flt1.cpp:487`/`:835`), so
    record `map_scale` on the first snapshot after RETURN and confirm
    the engine puts back the value the map had before — the gate covers
    HD, not the engine.

### What must NOT be sent

- Anything into a field the reading marks dangerous.
- **F5 and Alt-F5 cannot be sent at all** — `INJECT_KEY`'s keysym is an
  int16 and `SDLK_F5` is `0x4000003e`.
- The scroll FIELD (type 6): it is read through a pointer. Use the two
  arrow buttons.
- SCRAP, on a scratch save, only with intent — it destroys ships.

---

## 2. Decisions for Data

1. **The four OMISSIONs.** The ship's picture (SHIPS.LBX is MOO2's art),
   the damage bar (offsets 123/125 unverified, and its geometry
   unsettled), the move preview (hover-computed, on no wire), the
   captain's portrait (`s_leader_data` unverified). Each is marked in
   the module that performs it and held by a smoke check. **Accept as
   omissions, or open a verification stop for 113/114/116/118/123/125,
   187, 205 and `s_leader_data`?**
2. **Relocation and the two-step star picking** are not built at all.
   The field list carries the star fields; the two-step flow, the merge
   mode and the refusals (`Okay_To_Set_Relocate_To_Star_`) are a brief
   of their own.
3. **Move orders** are not built. A star click on this screen is a move
   order (flt1.cpp:629-666) and the confirmation chain behind it is
   decision 21 work.
4. **The detailed ship view** (right click on an own big icon, and the
   rename on exit) is not built. Whether `CANCEL_FIELD` even opens it is
   NOT SETTLED — `Check_Help_List_` tests the POINTER, not the field.
5. **The native confirmation and warning boxes** are not mirrored. HD
   leaves them to the framebuffer today.
6. **The reading's §9 questions 1, 4, 9, 14, 15, 16** are still open.
   15 in particular is now a live hazard with a name: while screen 4 is
   up, every `s_ship_icon` on the wire is in FLEET-INSET space
   (flt.cpp:24-55) and its `stack_id` holds a FIELD ID (flt2.cpp:34).
   **The galaxy map must ignore `s_ship_icon` while the screen id is not
   0** — BUILT by work orders 135 B and 136 B (`ships.ScreenStateGate`,
   one gate in `galaxy_map/screen.update`, a smoke check that iterates
   the gate's own field list on real bytes). Question 15
   itself is still Data's to confirm as a rule, and the live half is
   Evidence 8 above.

---

## 3. The two engine patches

| # | file | orion2re commit | bundle |
|---|---|---|---|
| 27 | `doc/ext_fleet_screen_state.patch` | `cc5ec133` | `~/orion2re_bundle_19sep_cc5ec133.bundle` |
| 28 | `doc/ext_fleet_screen_select.patch` | `e6199966` | `~/orion2re_bundle_19sep_e6199966.bundle` |

Both on `orionlayer-local`, both build clean, both required by
`tools/version_check.py`. **orion2re is never uploaded anywhere** — the
hard rule in CLAUDE.md, and its push URL stays disabled.
