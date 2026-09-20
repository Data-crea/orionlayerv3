# 152 — Fleets: function and parity pass, Stop 1

**Work Order 152 — Fleets: function and parity pass.** Findings for all
eight items. **No code changed.**

**THE LIVE HALF DID NOT RUN, AND THE REASON IS IN THE ORDER'S OWN
RULES.** "Exactly one client at the server — Data's OrionLayer must be
closed." At 13:31 an `orion2re` (pid 517332) was serving port 17362 with
a `python main.py` (pid 517577) already connected. That is Data's
OrionLayer, playing. Connecting would have made a second client, so
nothing was sent. §9 lists every question that is waiting on that, and
what will be run for each.

Items 4 and 5 have their cause; they are **not** implemented here, for
one reason each, given in place.

---

## 1 and 2 — ONE CAUSE, and it is not the one the tree says

Data's two items are the same fault, and the order's question ("is this
the same cause?") has a source answer.

**What happens when SCRAP is pressed.** `input == btn_scrap` →
`Scrap_Ships_` (flt1.cpp:698-700, :1504) → for a scrap that yields
credits, `HAROLD::User_Box_(…, msg, 1)` (:1565-1570) → `type 1` →
`GENDRAW::Confirmation_Box_` (harold.cpp:1280). Message 128/129 is the
"…will yield %d bcs" Data photographed.

**`Confirmation_Box_` opens with `Message_Box_Startup_`, and that is
where the field list goes.** `Message_Box_Startup_` (gendraw.cpp) calls
`FIELDSAV::Save_Field_Stats_`, and that function does this:

```c
data->fields      = fields::_fields;          // remember the base
fields::_fields  += fields::_fields_count;    // RE-BASE past them
max_fields_count -= fields::_fields_count;
fields::Clear_Fields_();                      // count = 1 on the new base
```

It **re-bases the field array and clears it**. `Confirmation_Box_` then
adds its own two:

```c
_first_field = Add_Hidden_Field_(0xeb, 0x12e, 0x11e, 0x143, "Y", 0x29);
second_field = Add_Hidden_Field_(0x159, 0x12e, 0x18c, 0x143, "N", 0x29);
```

= **(235, 302)-(286, 323) hotkey 'Y'** and **(345, 302)-(396, 323)
hotkey 'N'**, both type 7. `SerializeFields` (ext_api.cpp:320-336) walks
`fields::_fields[0 … _fields_count)` — the RE-BASED window — so while
the box is up **the wire carries three fields: the dead slot 0, YES and
NO.** Not one field the Fleets screen built is on the wire.

**What that does to HD.** `fltwire.View._read`: `has_fleet_list()` looks
for the catcher `(0,0,639,479)` type 7 hotkey 0 that `Fleet_Screen_`
adds last (flt1.cpp:1262). It is not in the list, so the state is
**`WAITING`** — and `WAITING` is the one non-READY state that KEEPS HD's
own picture up (`wants_original` returns False for it, work order
142 A), while `update()` still clears `self._cells` and `self._panel`
because the view is not `ok`.

**That is Data's screenshot exactly: the HD frame with an empty grid
and a blank text box, no dialog, while the game shows the dialog and
four Katanas.** Items 1 and 2 are one fault with one cause.

**AND IT CORRECTS THE TREE.** `fltwire`'s `FOREIGN_FIELDS` docstring
says of this very box: *"SCRAP's confirmation box adds two hidden fields
and clears nothing (gendraw.cpp:172-173) … every field this screen built
is still in place, so nothing else could have noticed."* The first half
is right and the second is wrong: `Save_Field_Stats_` clears, on a moved
base. `FOREIGN_FIELDS` therefore **never fires for a message box** — the
state named after that case cannot reach it. Work order 137 A's reading
has been wrong since it was written, and nothing failed loudly because
`WAITING` looks like a screen that is merely early.

**Also explained: "ships vanishing when he selects them."** Not
verified live yet, but the shape is the same and there is a second
`User_Box_` on the selection path — `Scrap_Ships_` is not the only
caller. Any `User_Box_` on this screen (black hole refusal :641,
officer confirmation :1543, "cannot order" :648, relocation confirmed
:660) empties the list the same way. §9 says how it gets tested.

**What HD needs in order to answer the dialog.** Nothing new on the
wire. `Confirmation_Box_`'s loop is
`do { input = fields::Get_Input_(); } while (input != yes && input != no);`
and `Get_Input_` is the same function that honours `ext::g_pending_field`
(fields.cpp:166-182). So **`ACTIVATE_FIELD` on the YES or the NO field
answers it** — the same mechanism 151 B used for the ship scan. On the
re-based array those are indices **1 and 2**, and they must be resolved
from the live list by hotkey ('Y'/'N') and rect, never by index
(decision 20).

**Three ways to fix it, all Data's to choose:**

1. **Hand over.** Recognise "the list is a message box's" as its own
   state and return True from `wants_original` for it, so the player
   answers through the original picture, which already forwards clicks
   (work order 130 A). Smallest change; HD's screen disappears for the
   duration.
2. **Show it in HD.** A two-box popup on this screen and two
   `ACTIVATE_FIELD`s — decision 11's "a popup that belongs to exactly
   one screen … is two boxes and a render call", which is what Custom
   Race's message box already is. The text is on the wire only as
   pixels, so the WORDING would have to come from the player's own
   HESTRNGS (`tools/hestrings_extract.py`, message 128/129 formatted
   with the value) — which is decision 38's route and is already built
   for other strings.
3. **Refuse before sending** (decision 33). Not available here: whether
   the box appears depends on `Get_Scrap_Ship_Value_()`, a colony test
   and an officer test — three comparisons over data HD does not fully
   hold. Decision 33 is for a rule that is *one* comparison; this is
   not one.

**The `WAITING` state needs splitting either way.** "The list is not
ours yet" and "the list is somebody else's modal box" are different
facts that currently land on the same constant, and the second one is
the one that keeps an empty grid on screen indefinitely.

---

## 3 — Star names on hover: confirmed, and HD draws the wrong thing

**The original does show it.** `MAINSCR::Scan_Galaxy_Map_Fields_`
(mainscr.cpp) returns 4 with `scanned_star_id` when the hover value
matches a star's field, the Fleets loop sets
`MOX::_galaxy_map_scanned_star = scanned_star_id` (flt1.cpp:629-631),
and `flt1.cpp:397-398` prints
`FLT2::Print_Fltscrn_Scanned_Star_Name_()` under
`if (_galaxy_map_scanned_star > -1)`. Black holes are excluded from the
hover branch, so they show no name. Data's observation is correct.

**`_galaxy_map_scanned_star` IS NOT ON THE WIRE.** The FLTS block
(open fix 27) carries `scanned_big` and `scanned_small` and not this.
→ `doc/orion2re_open_fixes.md`, as a request.

**AND HD IS DRAWING SOMETHING THE ORIGINAL DOES NOT.**
`screen._status_line` reads `scanned_small` — the hovered SMALL SHIP
icon — and prints its star's name. In the original the two are mutually
exclusive (`_scanned_small_ship = h; _galaxy_map_scanned_star = -1;`
at :680, and the reverse at :631), and a hovered small ship drives a
different printer entirely: `OFFICER::Print_Galmap_Scanned_Ship_`
(flt1.cpp:439-440), which is not this strip. So HD takes the ship
branch and prints the star branch's content. That is an invention and
it is not marked as one.

**HD could do it without any API change, and that is the interesting
half.** The snapshot carries every star's galaxy coordinates and HD
already maps them into the inset (`colonyrows.galaxy_inset_stars`); HD
owns the pointer inside its own window. So HD can name the star under
**HD's own pointer**, client-side, with no MOUSEMOTION and nothing
asked of Joes. It would be an **HD EXTENSION**, because the line would
follow HD's hover and not the game's, and the two can differ. Data
chooses: ask for the value, or draw HD's own.

---

## 4 — The grey line above the ship icons: an off-by-two in the cut

**Found, at its source, and it is the renderer's cut and not the
artwork.**

`fltart.plate(native_x, native_y, size=NATIVE_CELL)` cuts a **57x57**
square out of FLEET.LBX 0 **at the icon origin** from
`Get_Fltscrn_Big_Icon_XY_`. Measured on the extracted background at
cell 0, icon origin (347, 53), column x=347:

```
  y=52  (108,108,116)   the well's top highlight  <- cut includes it
  y=53  (124,124,132)   ditto                     <- cut starts here
  y=54  ( 44, 44, 52)   the shadow row            <- and this
  y=55  (  0,  0,108)   the blue interior begins here
```

So the cut takes two rows of the chrome that belongs **around** the
cell and blits them **inside** the HD cell, which already has its own
border from the frame artwork. That is the thin grey line, on every
occupied cell, along the top edge.

**The original never draws a plate at all.** The well is painted into
the background and the icon is drawn ON it, at
`(x + half_w_diff + 1, y + half_h_diff + 2)` (flt1.cpp:106) — the same
`+1, +2` `fltart.cell_offset` transcribes.

**What the right rect is.** The original's own answer is in the
selection sprite: `_selected_box_seg` is FLEET.LBX 17, measured
**59 x 58**, drawn at `(x - 2, y + 1)` on this screen (flt1.cpp:93-103).
A 59x58 box at `(x-2, y+1)` frames the well exactly, and `y+1` sits one
row above the blue that starts at `y+2`. So the well is
**`(x - 2, y + 1)`, 59 x 58** and the plate should be cut there, not at
`(x, y)` 57 x 57.

**NOT IMPLEMENTED HERE, deliberately.** The number above is derived
from two sources that agree (the measured background and the sprite the
original frames the well with), but a plate cut is artwork on screen and
the tree's rule for that is a render, not an argument. It is a
three-line change and it goes in Stop 2 with a 1440p before/after, or
now if Data would rather have it immediately.

---

## 5 — Selection: the original's mark, verified

**It is a sprite, and Data read it right.** flt1.cpp:93-103:

```c
if (MOX::_fltscrn_big_icon[i].selected != 0) {
    draw_y = y + 1;  draw_x = x - 2;          // SCREEN_FLEET
    animate::Draw_(draw_x, draw_y, MOX::_selected_box_seg);
}
```

`_selected_box_seg` is **FLEET.LBX 17, 59 x 58** — a light frame around
the whole cell, on the well's own edge, not behind the ship. There is a
second one, `scanned_box` (62 x 61), drawn by
`Draw_Box_Around_Scanned_Ship_` for the HOVERED ship (:89-91) — a
distinction HD does not make at all.

**What HD does today.** `fltdraw.draw_cells`:
`pygame.draw.rect(col("scroll_thumb"), rect, max(2, 3 * scale))` — an
outline on the cell rect, in `(24, 12, 252)`. So HD is already "on the
edge"; what Data is seeing as the selected state is almost certainly
the **plate** of item 4 (the blue square, drawn on every occupied cell,
selected or not), with the 2-3 px selection line lost against the
frame's own bright border. The two items are coupled and item 4 should
be fixed first.

**NOT IMPLEMENTED HERE**, for a different reason from item 4: the order
says "draw the HD state on the cell edge, following the new cell
frame's shape". The new cell has a **chamfer** (`CONTENT_INSET_SRC` = 9
source px), so "following its shape" means a chamfered outline and not
`pygame.draw.rect`. That is a drawing decision with a look to it, and it
wants Data's eye on a render before it is committed, not after.

---

## 6 — Right-click help: already built, and it matches the original

**Everything the order asks for is in the tree.**
`screens/fleets/help.json` carries all twelve static regions transcribed
from `EVANHELP::_static_fleet_screen_help_list` (evanhelp.cpp:153-166),
each resolved from a box name — and all twelve names exist in
`boxes.json` after 151. `FleetsScreen` inherits `ScreenHelp`, so
`handle_right_button` is routed from `main.py:230-236`, and
`render_help` is called **after** `_render_frame_image`, so the popup is
not under the frame. `assets/shared/help/help_en.json` is present in
Data's tree and `settings.json` says `language: en`.

**And HD already has the dynamic half.** `Set_Fleet_Screen_Help_List_`
(evanhelp.cpp:378-407) appends help **360** over the EMPTY slots — one
region per slot from `start_index` to 19, or one over the whole grid
when no icon was added — and `FleetsScreen.open_help_at` implements
exactly that.

**So the likeliest answer is that nothing is wrong.** The original has
**no help entry over an occupied cell and none over the inset map**
(`help.json` already records `_no_help_over_the_map`). A right click
there does nothing in the original either. What must be confirmed live
is one right click on a control that DOES have an entry — RELOCATE
(369) is the clearest — and one on the map, to show that the second
doing nothing is parity and not a fault.

**One real gap found while reading:** Fleets is the only help-enabled
screen with **no `help_popup` box** in `boxes.json`. `screenhelp` falls
back to `HELP_FALLBACK_BOX`, so the popup still draws — but its
position and font are not F5-editable on this screen while they are on
the other six. Worth a box either way.

---

## 7 — Ship panel content: the original's, line by line

`FLT2::Print_Scanned_Ship_Data_` (flt2.cpp:524-747), in print order,
against what HD draws:

| # | the original prints | source | on the wire? | HD today |
|---|---|---|---|---|
| 1 | ship name, font 3 | :580 | yes, `s_ship.name` | **yes** |
| 2 | crew description + " (%d EP)" | :585-591 | **crew_quality yes, crew_experience UNVERIFIED** | no |
| 3 | shield name | :597 | yes, `shield_type` | **yes** |
| 4 | "Beam OCV" + attack bonus | :604-608 | **NO** — derived | no, marked OMISSION |
| 5 | "Beam DCV" + defense bonus | :610-637 | **NO** — derived | no, marked OMISSION |
| 6 | location line | :645-677 | yes | **yes** |
| 7 | "WEAPONS" / "SPECIALS" headings | :681-682 | wording in HESTRNGS 0x9D/0x9E | no |
| 8 | weapons column, x **0x17 = 23** | :686-717 | yes | yes, no arc, one column |
| 9 | specials column, x **0xBC = 188** | :722-738 | yes | **yes**, but stacked under the weapons |
| 10 | "none" (0x9F) when a column is empty | :719, :740 | wording in HESTRNGS | no |

**Corrections to the order's own list, both in Data's favour to know:**

* **The location line IS the original's**, not an HD addition:
  `fonts::Print_(0x12, y_cursor + 0x11F, loc_str)` at :672, with the
  wording from `H_Message_(0x9B)` formatted with the star name, or
  0x9C when the player has no information, or 0x68 for "in transit".
  What IS HD's own is the **label**: HD prints a hardcoded English
  "Location: ", where the original's whole string comes from HESTRNGS.
  So the line stays and its wording should come from the player's own
  strings (decision 38's route, `tools/hestrings_extract.py`).
* **The weapon line's format is `"%d %s (%s)"`** — count, name (plural
  form when count != 1, `TECHDATA::_weapons[t].name_plural`), and
  `DESIGN::Weapon_Arc_String_(firing_arc, …)`. HD prints `"%d %s"` and
  drops both the plural and the arc. The arc field is in the ship
  struct beside `type` and `count`; whether `core/structs/ship.py`
  decodes `firing_arc` has to be checked before it is promised.
* **A damaged special is printed in RED** (`_red_colors`, :727-731),
  from `special_device_damage_flags`. HD draws every special the same.

**The two columns are the layout**, and 151 B already measured that HD
stacking them in one is why HD runs out of room sooner. Weapons at
x 23, specials at x 188, each with its own cursor, both starting from
the same `base_y` (:683-685).

**For `doc/orion2re_open_fixes.md`**, if Data wants items 4 and 5 of the
table: the attack/defense bonuses are the one thing here that is neither
on the wire nor derivable —
`INITSHIP::Get_Ship_Combat_Bonuses_` needs officer skills, the crew
fields at 113-116, `strategic_combat_flag` and tech applications, three
of them UNVERIFIED. The request is for the two computed int16 values,
not for their inputs.

---

## 8 — Moving ships over the map: the whole flow, and it needs no new API

**The chain, from source** (flt1.cpp:628-664):

```c
ret_map = MAINSCR::Scan_Galaxy_Map_Fields_(scan_val.full, input,
                                           &scanned_star, &clicked_star);
...
} else if (ret_map == 0) {                     // a star field was ACTIVATED
    if (_merging_relocations == 0) {
        if (_relocate_button_mode == 1)        -> Star_Relocation_(...)
        else if (spectral_class == BLACK_HOLE) -> User_Box_(H_Message_(0x78), 3)
        else {
            first_ship = First_Selected_Ship_();
            if (first_ship >= 0) {
                if (Player_Can_Order_Ship_(...)) FLT2::Fltscrn_Move_Ships_(clicked_star);
                else                             Cant_Order_Ship_Message_(...);
            }
        }
    }
```

**So the interaction is: select one or more ships in the grid, then
click a star in the inset map.** No button. RELOCATE is a different
branch (`_relocate_button_mode == 1`), which is the relocation lines
work order 144 already read.

**The polarity, which is the one thing that must not be guessed.**
`Scan_Galaxy_Map_Fields_(field_id_1, field_id_2, …)`: `field_id_2` is
`input`, and a match gives **`result 0` and `clicked_star_id`** — the
move branch. `field_id_1` is the hover value and gives result 4.
**So a POSITIVE field index is the CLICK here**, which is the opposite
way round from `Scan_Fltscrn_Big_Icons_`, where a positive index is the
HOVER and the negative is the click (flt2.cpp:924-934, measured live in
151 B). Two scanners on one screen with opposite conventions is exactly
the kind of thing that gets transcribed wrong once.

**What that means for the send.** Each star in the inset is its own
hidden field — `Add_Galaxy_Map_Fields_2_`, `(sx-3, sy-3, sx+8, sy+9)`,
movebox.cpp:504-511 — and `fltwire` already has that rule (rule 3a).
So the send is **`ACTIVATE_FIELD` on the star's own field**, type 7,
which decision 20 names for exactly this. **No `INJECT_CLICK`, no
coordinate mapping, and decision 35 is satisfied outright**: the field
IS the game's frame, so there is no HD rect in the path at all. Open
fixes 3 and 4 are not in the way of this one.

**What HD still has to do before sending:**

* **Map a star to its field.** The field rect is derived from the
  star's inset position, which HD computes already; the match is
  `(sx-3, sy-3)` against the live list. It has to be resolved in the
  list at the moment of the click, not cached.
* **Refuse a black hole** (decision 33). This one qualifies: it is
  literally `spectral_class == STAR_CLASS_BLACK_HOLE`, one comparison,
  and `core/structs/star.py` already has `is_black_hole`. Refusing it
  in HD avoids a `User_Box_` that would empty the field list — item 1's
  fault, reached a second way.
* **Expect the field list to go away anyway.** A move that succeeds
  ends in `Fltscrn_Move_Ships_`, and several of its outcomes end in a
  `User_Box_`. Item 1's fix is a prerequisite for item 8, not a
  neighbour of it.
* **`First_Selected_Ship_() >= 0`**, or the click does nothing — so HD
  should not send when nothing is selected.

---

## 9 — What is waiting on the port, and what will be run

Data closes OrionLayer; this is one run on **SAVE4**, one client,
hashes before and after, nothing saved:

| item | the send | what it settles |
|---|---|---|
| 1, 2 | SCRAP, then read the field list | that the list is exactly {0, YES, NO}, and the HD state is `WAITING` — the one prediction this whole reading rests on |
| 1 | `ACTIVATE_FIELD` on NO | that the dialog is answerable from HD, and that the Fleets list comes back on `Restore_Field_Stats_` |
| 2 | select a ship, watch the list | whether "vanishing on select" is the same `User_Box_` shape or its own fault |
| 6 | right click RELOCATE, then the map | that help works, and that the map having none is parity |
| 7 | scan a ship, dump the struct | whether `firing_arc` and `crew_experience` decode |
| 8 | select, then `ACTIVATE_FIELD` a star | that a positive field index moves the ships — **state-changing, SAVE4 only, not saved** |

Nothing above is sent twice, and every one reads the fresh field list
first.

---

# Stop 2, part 1 — the live run, and what it settled

**SAVE4, one client, 20 September 2026.** SAVE1-6, 8, 9 and 11
byte-identical before and after; SAVE8 never touched; SAVE10 logged at
`07b2dd62…` and unchanged. Nothing was saved. Evidence in
`~/orionlayer-fixtures/evidence/work_order_152/`.

## Items 1 and 2 — the prediction held, exactly

| | fields | View state | cells | wants_original |
|---|---|---|---|---|
| on the Fleets screen | 73 | READY | 1 | False |
| after selecting a ship | 74 | READY | 1 | False |
| **after SCRAP** | **2** | **WAITING** | **0** | **False** |

and the two fields are

```
  1 t=7 (235,302)-(286,323) hk=89 'Y'
  2 t=7 (345,302)-(396,323) hk=78 'N'
```

— which is `Add_Hidden_Field_(0xeb, 0x12e, 0x11e, 0x143, "Y", …)` and
`(0x159, 0x12e, 0x18c, 0x143, "N", …)` (gendraw.cpp), to the pixel. The
wire carries three and HD sees two because `parse_fields` drops field 0
(work order 142 B). **`WAITING` with an empty grid is confirmed as the
fault Data photographed.**

**AND THE ANSWER IS A CHAIN, WHICH THE SOURCE READ DID NOT CATCH.**
`ACTIVATE_FIELD` on the NO field did not restore the screen: the list
went from 2 fields to **1**, still `WAITING`. That one field is
`(0,0,639,479)` hotkey 27 — `Warning_Box_`'s own catcher.
`Scrap_Ships_` answers a NO with a second box (`User_Box_(…, 3)`,
flt1.cpp:1524-1527). Dismissing that one returned all 74 fields and
`READY`. **HD has to handle a chain of boxes, not one box.**

**THE FLTS BLOCK NEVER GOES AWAY.** Measured through the whole
sequence: `FLTS=PRESENT`, `icons=1`, `ship_idx` intact, `selected=1` —
before, during and after. So the required result is reachable as Data
stated it: the grid and the panel can stay up from the block, and only
the CLICKING has to stop, because a send resolves its field in a list
that no longer has any (decision 20).

**ONE PART OF THE REQUIRED RESULT CANNOT BE MET AS WRITTEN, and the
order says report before building.** "HD shows the game's confirmation
text" — the text is **not on the wire as text**. It is
`H_Message_(128)` formatted with `Get_Scrap_Ship_Value_()`, and that
value is a sum of `maintain::Ship_Scrap_Value_` over the selected
ships, which HD cannot compute. Three ways out, and they differ in what
the player sees:

1. **HD's own wording, no number** — "Scrap the selected ship?" from
   `layout.json`. Nothing new needed. The player loses the figure the
   original gives them, which is the one fact that decides the answer.
2. **Ask for the value** — one int16 in the FLTS block, or a string in
   a new block. `doc/orion2re_open_fixes.md`. Correct, and it waits on
   Joes.
3. **Blit the game's own message.** The text IS on the wire — as
   pixels, in the framebuffer HD already subscribes to — and the box's
   rect is known exactly from `Confirmation_Box_`. Cropping the
   original's rendered message into the HD popup is a transcription,
   not an invention, and it needs nothing from anybody. What it changes
   is that the player sees 640x480 text inside an HD panel.

**Not built. Data chooses, because all three change what the player
sees.**

## Item 6 — and a correction to my own Stop 1 report

Right-click help **works**. Live on SAVE4: RELOCATE opens `help_id`
**369**, title *"Fleet Screen Relocate Button"*, **7 lines** of body out
of the player's own HELP.LBX.

My first probe read `scr.help.text`, which does not exist — the popup
keeps `_title` and `_lines` — and printed `len=0`. I nearly filed "the
popup opens with no text" as a finding. **It was the probe, not the
popup.** Measured properly: `open_help_at` returns True on
`btn_relocate`, `btn_scrap` and `cell_00`, and False on `inset_map`,
which is parity — the original has no entry over the map either. The
only real gap was the missing `help_popup` box, and that is now in.

## Item 7 — what the wire actually carries

Sampled on SAVE4's stack (one Scout, so the weapon list is empty and
the arcs are unsampled — a warship still has to be found):

* **`firing_arc` is in the VERIFIED spec** — `WEAPON_SPEC` offset 4,
  `core/structs/ship.py:137`. The arc can be printed.
* **`crew_quality` @113 and `crew_experience` @114 are UNVERIFIED**
  (`doc/fleet_screen_reading.md:199`). Raw bytes on the live Scout read
  `raw[113] = 0` and `raw[114:116] = [42, 0]` — consistent with "Green
  Crew (42 EP)", which is one sample and is **not** a second source.
  Decision 23 says a struct offset needs one, so the crew line is an
  OMISSION until `tools/struct_probe.py` confirms it against the
  game's own printed line.

## Item 8 — ready to send, not sent

**54 star fields** in the live list, every one matching `fltwire`'s
rule 3a `(sx-3, sy-3, sx+8, sy+9)`, and one cell selected. The move is
one `ACTIVATE_FIELD` away. Not sent: it is the one state-changing step
and it belongs in its own commit with its own before/after.

---

# Stop 2, part 2 — item 7's groundwork, measured

## The crew fields now have two sources, and can be promoted

Decision 23 wants a header route or a probe. Both are in hand.

**The header.** `s_ship_data` (orion2.h:2847-2868) runs `owner`,
`status`, `location`, `x`, `y`, `group_has_navigator`,
`travelling_speed`, `turns_left`, `shield_damage_percent`,
`drive_damage_percent`, `computer_damage`, **`crew_quality`**,
**`crew_experience`**, `officer_index`,
`special_device_damage_flags[5]`, `armor_damage`, `structural_damage`.
The tree's spec is already VERIFIED through `turns_left` @109 by exactly
that header plus a live reading (briefs 113/114), so 110-116 is the
same run of the same struct: **crew_quality @113 (i8), crew_experience
@114 (i16), officer_index @116 (i16)**.

**The live half, over SAVE4's 60 ships.** MOO2 derives the crew WORD
from the experience points, so if both offsets are right the quality
must be monotone in the experience — and two unrelated bytes cannot do
that across sixty ships.

| crew_quality | ships | crew_experience |
|---|---|---|
| 0 | 56 | 0 … 44 |
| 1 | 4 | **50 … 56** |

**The bands do not overlap and they rise.** Every value is in 0..3, and
`officer_index` @116 is in -1..66 on all sixty, which is the leader
pool's own range — a third consistency from the same run.

**So the crew line can be shown**, with its wording from the player's
HESTRNGS (`Crew_Description_String_` picks 0x8A-0x8D, flt2.cpp:749-773)
and " (%d EP)" from flt2.cpp:589-591.

## What still cannot be shown, and why

* **The red for a damaged special.** `special_device_damage_flags` @118
  follows in the same header run, and the obvious live check — a
  damaged device must be a FITTED one — holds on all 60 ships. **But
  not one ship in the save has any damage**, so the check is vacuous
  and proves nothing. UNVERIFIED stands; the red is an OMISSION until a
  save with a damaged ship confirms it.
* **Four of the five firing arcs.** The values decode:
  `firing_arc` is `WEAPON_SPEC` offset 4, VERIFIED, and SAVE4 shows a
  real spread — 1 (FORWARD), 2 (FORWARD_EXTENDED), 15 (ALL_SECTORS),
  16 (360). `DESIGN::Weapon_Arc_String_` (design.cpp) tests the bits in
  order and answers with `KEN::Ken_Get_Text_Message_(3..6, …)` for the
  first four and the **literal `"360"`** for 0x10. That literal is
  transcribable. The other four words are in KENTEXT.LBX through
  `JIM::Get_Text_Message_(lbx, index, buffer, arg)`, whose record
  addressing this session did not establish — entry 3 of that file
  holds `"Pob:"`, not an arc word, so `msg_index` is not the entry
  index in the way the call reads. **Not guessed.** Printing "(F)" and
  "(Fx)" from the enum names would be inventing English the game may
  not use.

So item 7 ships the arc it can transcribe and marks the other four,
unless Data would rather it waited for the KENTEXT reading.

## Item 8 is unchanged and ready

54 star fields in the live list, all matching rule 3a; the send is one
`ACTIVATE_FIELD`. Not sent.
