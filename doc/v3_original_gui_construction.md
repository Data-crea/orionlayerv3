# How the original builds its GUI

Work Order 147 — How the original builds its GUI. **Stop 1 only:
findings from source. No code, no patches, nothing changed in either
tree.** Observations, not proposals; Data decides what follows.

Read against orion2re at `e6199966`, read-only. Line numbers are in the
appendix; the prose names files and functions.

**The order arrived truncated** — it ends mid-sentence at
`## Acceptance` / `- Every`, so whatever acceptance criteria followed
are not answered here. See `doc/briefs/147-parked-for-data.md`.

---

## The short answer

**The original has a real template layer, but it is an INPUT layer, not
a drawing layer.**

`fields.cpp` owns a single array of up to 150 field records. A field
carries its rect, its type, its hotkey, its sound, its font style and
colour — and for buttons and radios **its own picture**. One generic
walker, `Draw_Visible_Fields_`, draws every one of them, prints its
label centred in its own rect, and renders its pressed state. Twenty-
eight source files add button fields this way; forty-eight add hidden
ones.

What there is **no** shared layer for is the screen itself. There is no
generic window, frame, border or panel routine anywhere in the tree —
no `Draw_Frame_`, and every "box" drawer that exists (`Draw_Weapons_
Rack_Box_`, `Draw_Small_Fleet_Box_Frame_`, `Draw_Confirm_Box_`) belongs
to one screen. **Each screen's frame is painted into its own
full-screen background bitmap.**

The exception is dialogs, which are genuinely shared and genuinely
portable — see question 2.

---

## 1. Where the art comes from

**One LBX per screen, named after the screen**, plus shared archives for
text and dialogs. Every screen loads through the same primitive,
`farload::Far_Reload_Next_` (457 calls across 48 files), into
`MOX::_screen_seg`.

Measured on the shipped archives (evidence, not committed):

| archive | entries | entry 0 | 640x480 entries |
|---|---|---|---|
| MAINMENU.LBX | 44 | 640x480 | 8 |
| FLEET.LBX | 112 | 640x480 | 1 |
| DESIGN.LBX | 72 | 640x480 | 1 |
| PLNTSUM.LBX | 84 | 640x480 | 1 |
| OFFICER.LBX | 344 | 640x480 | 1 |
| COLSUM.LBX | 22 | 640x480 | 1 |
| INFO.LBX | 26 | 640x480 | 1 |
| RACES.LBX | 64 | 640x480 | 1 |
| TECHSEL.LBX | 28 | **472x480** | 0 |
| GAME.LBX | 32 | **279x378** | 0 |
| CONFIRM.LBX | 3 | **313x227** | 0 |
| WARNING.LBX | 1 | **331x191** | 0 |

**The pattern is MIXED, and the same everywhere:** entry 0 is a
640x480 background with the frame, the panels, the rails and the empty
button faces **painted into it**, and everything that changes is a
separate small entry blitted on top at run time. `FLT1::Draw_Fleet_
Screen_` is the clearest case — `_fleet_background_seg` is FLEET.LBX 0
and the grid plates are part of it.

The four archives whose entry 0 is **not** 640x480 are the ones that
are not screens: TECHSEL is a panel over the main screen, GAME is the
load/save popup, CONFIRM and WARNING are dialogs. Their sizes match
what the tree already recorded independently for the GAME menu.

## 2. Shared building blocks

Found in at least two screens' code, as the order requires.

| block | where it lives | callers | parameterised? |
|---|---|---|---|
| the field array and its walker | `fields.cpp` | 48 files add fields | yes — rect, type, hotkey, sound, picture, font |
| `Add_Button_Field_` | `fields.cpp` | 28 files, 142 calls | yes — position and picture; **size comes from the picture** |
| `Add_Hidden_Field_` | `fields.cpp` | 48 files, 216 calls | yes — all four coordinates given |
| `Add_Radio_Button_Field_` | `fields.cpp` | 10 files, 29 calls | yes — plus a pointer to the state variable |
| `HAROLD::User_Box_` | `harold.cpp` | 8 files, 68 calls | **text only** — six fixed types |
| `GENDRAW` message/confirm/warning boxes | `gendraw.cpp` | 20+ files | **text only** — fixed size and position |
| `TEXTBOX::Do_Text_Box_`, `Timed_Text_Box_` | `textbox.cpp` | via `User_Box_` | text, and a timeout |
| `FIELDSAV::Save_Field_Stats_` / `Restore_` | `fieldsav.cpp` | `gendraw`, `mainpups`, `textbox`, `tech` | — |
| `remap::Calculate_Picture_Remap_Colors_` + `animate::Remap_Draw_` | `remap.cpp`, `animate.cpp` | 10 files | — |
| `farload::Far_Reload_Next_` | `farload.cpp` | 48 files, 457 calls | archive and entry |
| `fonts::Set_Font_Style_` | `fonts.cpp` | 55 files, 490 calls | style index + 8 palette indices |
| the per-screen dirty flag | `mox.cpp` | main, fleet, officer, design, game popup | — |

**The dialog layer is the one place the original does what OrionLayer
calls a skin.** `User_Box_` takes a message and a type and dispatches to
a message box, a confirmation box, a warning box or a timed text box.
Every one of them is **fixed size at a fixed position** — `Confirmation_
Box_` draws CONFIRM.LBX 0 at a literal (0xa1, 0x75) with its two buttons
at literal (0xeb, 0x12e) and (0x159, 0x12e). Only the text varies.

**What makes them portable is not scaling but palette remapping.**
`Calculate_Picture_Remap_Colors_` reads the dialog sprite's own embedded
palette and builds a 256-entry table by nearest-colour search
(`Find_Closest_Color_`) against whatever palette the screen underneath
has loaded; `Remap_Draw_` then draws through that table. So one dialog
bitmap appears over any screen without disturbing its palette. Text over
it goes through `Set_Remap_Font_Style_` for the same reason.

**There is no shared scroll bar, list row, or window frame.** The Fleets
scroll bar is `FLT1::Fill_FltScrn_Scroll_Bar_`, which draws its own
gradient and knows the Fleets screen by `_current_screen`.

## 3. Fields vs. art — two answers, by field type

**This is the sharpest finding of the order, and it cuts both ways.**

For **buttons and radios the rect is derived from the art**:

```
field->x_end = field->x + animate::Get_Width_(pic) - 1;
field->y_end = field->y + animate::Get_Height_(pic) - 1;
```

The field also *stores* the picture, and `Draw_Visible_Fields_` draws it
and prints its label centred in that same rect. For these, the hit area
and the drawn art are **one object with one source of coordinates** —
only the origin is a literal.

For **hidden fields all four coordinates are literals**, typed at the
call site, and the art is drawn by a *different function* with its own
literals. The main menu is the example: `Add_Hidden_Field_(0x19F, 0xAC,
0x237, 0xC1, "C", …)` in `Add_Fields_`, and `animate::Draw_(0x19F, 0xAC,
…)` in the draw routine. Two independent sets.

**And they do not quite agree.** MAINMENU.LBX entry 3 is 153x23. The
field is 0x237−0x19F+1 = **153** wide and 0xC1−0xAC+1 = **22** tall. The
width matches exactly; the height is one pixel short of the art, and
nothing in the program could notice.

A third case is worth recording because OrionLayer met it the hard way:
the main menu adds six hidden fields whose rects are a meaningless
staircase — (10,20,25,35), (20,30,35,45), … — carrying nothing but the
hotkeys C, S, L, M, H, Q. **Some fields exist only for the keyboard and
their geometry means nothing.** The same screen also adds a
`(0, 0, 639, 479)` catcher, an idiom that recurs on the Fleets screen.

## 4. Button states

Two mechanisms, one generic and one per-screen.

**Generic, in `fields.cpp`.** `Draw_Field_(i, action)`: with `action`
0 the button draws frame 0 and its label centred; with `action` 1 —
which `Draw_Visible_Fields_Back_` passes for the field under a held
mouse button — it draws **frame 1 of the same sprite** and shifts the
label by `_selected_button_text_x_offset` / `_y_offset`. Whether a
second frame exists at all is read off the sprite:
`draw_style = animate::Get_Full_Store_Flag_(pic)`, and when it is 0 the
art does not change and only the text moves. Radios do the same, keyed
on the value behind their state pointer.

**Per-screen, by separate LBX entries.** The main menu loads *three*
entries per button and picks between them in its own draw routine:
normal is baked into the background, `field1` is drawn when the field
is `_scanned_field` (hovered), `field2` when the field id is `-1000`,
the sentinel it uses for "this button is not available".

Pixel evidence: `MAINMENU_button_states.png` shows entries 3, 4 and 5 —
all 153x23, one frame each — as CONTINUE dim, lit and greyed.

**Nothing anywhere produces a state by recolouring at run time.** The
states are either separate frames or separate entries.

## 5. Text

**One font file per language**, chosen by `HAROLD::Get_Font_File_` and
loaded once by `fonts::Load_Font_File_`: FONTS.LBX for English, FONTSG,
FONTSF, FONTSS, FONTSI for the others.

**Colour is palette indices, never RGB.** A font style is an index plus
an `s_colors` of eight palette entries; `MISC::Font_Colors2_(mode,
primary, secondary)` builds that ramp from two indices, and
`fonts::Set_Font_Style_` installs it. Variants exist for outline, heavy
outline and shadow. Over remapped art, `Set_Remap_Font_Style_` puts the
text through the same nearest-colour table as the picture.

The screen's palette itself is an LBX entry: `fonts::Load_Palette_
(palette_id, start, end)` reloads entry `palette_id + 1` from the font
archive and copies it into `video::_current_palette`.

**Wrap widths are call-site literals, not a table.** `BILL::_Print_
Paragraph_(x, y, width, text, alignment)` and `FMTPARA::Print_
Formatted_Paragraph_To_Bitmap_` take the width as an argument, and each
caller passes its own. Single-line positions are literals too, computed
against the string's measured width where they are centred — e.g. the
Fleets status line prints at `169 − str_w/2`.

## 6. Composition order

Per frame a screen draws over a background it does not usually reload.
The background is blitted only when `MOX::_FULL_DRAW_SCREEN_FLAG` is
set, which is also when the palette is installed; after that the screen
draws its changing parts on top and flips pages (`Set_Page_Off_`,
`Copy_Off_To_Back_`, 89 calls across 43 files). Each screen carries its
own dirty flag — `_draw_main_screen_to_back` (65 uses),
`_draw_fleet_screen_to_back` (33), `_draw_officer_to_back` (25),
`_draw_design_screen_to_back`, `_draw_game_popup_to_back`.

**For popups, the fields are saved and restored; the pixels are not.**
`GENDRAW::Message_Box_Startup_` saves the mouse list, pushes a memory
block, disables the help list, draws the visible fields once, and calls
`FIELDSAV::Save_Field_Stats_`. `Message_Box_Cleanup_` calls
`Restore_Field_Stats_`, pops the block and restores the refresh mode.
Nothing copies the framebuffer aside. Instead `User_Box_` sets the
**caller's own dirty flag** — it takes a pointer to it and writes 1 both
before and after — so the screen underneath repaints itself from its
background when the dialog goes.

## 7. Variants

State changes are a **partial redraw over the same background**, not
swapped art and not a different background. The main menu draws one
extra sprite over the background for whichever button is hovered and
leaves everything else alone. The Fleets screen, when the displayed
stack's owner changes, sets `_fix_palette`, and `FLT2::Fix_Palette_`
installs the new ship palette and redraws the whole screen —
**a palette change, not new art**.

The one case of genuinely swapped art found is the main menu's
three-entries-per-button, which is per-screen code, not a pattern.

---

## Overview table

Screens reachable in a normal game, tactical combat excluded.

| screen | builder | archive | pattern | shared blocks used |
|---|---|---|---|---|
| main menu | `MAINMENU::Main_Menu_Screen_` | MAINMENU.LBX | baked bg + per-state entries | fields, GENDRAW |
| galaxy main | `MAINSCR::Main_Screen_` | STARBG.LBX, BUFFER0.LBX | assembled over a starfield | fields, User_Box_, lines |
| colony | `COLONY::Colony_Screen_` | COLONY.LBX (+ ~20 others) | baked bg + many pieces | fields, GENDRAW, remap |
| colony summary | `COLSUM::Colony_Summary_Screen_` | COLSUM.LBX | baked bg + rows | fields |
| planet summary | `PLNTSUM::Planet_Summary_Screen_` | PLNTSUM.LBX | baked bg + rows | fields |
| fleets | `FLT1::Fleet_Screen_` | FLEET.LBX | baked bg + icons | fields, User_Box_, own scroll bar |
| ship design | `DESIGN::Design_Screen_` | DESIGN.LBX | baked bg + pieces | fields, GENDRAW |
| research select | `TECH::Tech_Change_` | TECHSEL.LBX | **panel over the main screen** | fields, FIELDSAV |
| officers | `OFFICER::Officers_Screen_` | OFFICER.LBX | baked bg + portraits | fields, own User_Box_ wrapper |
| race / diplomacy | `RACESCRN::Race_Screen_` | RACES.LBX | baked bg + pieces | fields, BILLTEXT |
| info / library | `INFO::Info_Screen_` | INFO.LBX | baked bg + pieces | fields, BILLTEXT |
| new game | `NEWGAME::Newgame_Screen_` | RACEOPT.LBX | baked bg + pieces | fields |
| load / save | `LOADSAVE::_Game_Popup_` | GAME.LBX | **popup panel** | fields, FIELDSAV |
| confirm / warning | `GENDRAW::Confirmation_Box_`, `Warning_Box_` | CONFIRM.LBX, WARNING.LBX | **dialog panel, remapped** | fields, FIELDSAV, remap |

## Observations against OrionLayer's decisions

Stated as differences. No recommendation is made.

**Decision 3, "Cutout boxes come from the frame; content boxes do not."**
The original does the opposite for hidden fields and the same thing for
buttons. A button field's rect is the sprite's size at a given origin —
art and hit area from one source, which is decision 3's spirit. A hidden
field's rect is four literals typed independently of the drawing code,
and on the main menu the result is one pixel shorter than the art it
covers. OrionLayer derives its Fleets cutouts from the frame's alpha and
asserts the agreement in the smoke test; the original has no such check
and no way to notice the mismatch.

**Decision 12, "Frame variants only — no runtime tile swapping."**
The original agrees, and more strongly: it has no tiles to swap. Every
screen's frame is painted into one 640x480 bitmap, and no routine
assembles a frame from pieces anywhere in the tree.

**Decision 34, "Two panel skins, and which one means what."**
The original has no panel skin at all. What OrionLayer draws with
`inner_panel` or `thin_border`, the original has already painted into
its background. The nearest equivalent is the dialog set — CONFIRM,
WARNING and the text box — which is a fixed-size panel with fixed button
positions, varying only in its text, made portable across screens by
palette remapping rather than by being drawn to fit.

**Decision 37, "A third box skin, `text`, draws nothing but the string."**
The original has this, in two forms. `Add_Button_Field_` stores a
`help` string and the field walker prints it centred in the field's own
rect in the field's own stored font — a label whose position comes from
the same record as the hit area. Free-standing text is `Print_Centered_`
or `_Print_Paragraph_` at call-site literals, with the wrap width passed
per call. Where OrionLayer puts position, size and font in `boxes.json`,
the original puts them in the field record for labels and in the source
for everything else.

## Appendix — line references

`mox2.cpp:35` screen dispatcher · `mainmenu.cpp:49-59` the hotkey-only
fields and the catcher · `mainmenu.cpp:126-137` the main menu's field
rects · `mainmenu.cpp:143-162` three entries per button ·
`mainmenu.cpp:240-283` hover and disabled drawing · `fields.cpp:302`
`Add_Hidden_Field_` · `fields.cpp:361-391` `Add_Button_Field_` and the
rect from the sprite · `fields.cpp:1806-1827` the field walker, from
index 1 · `fields.cpp:2673-2740` pressed state and label offset ·
`gendraw.cpp:18-49` the shared boxes · `gendraw.cpp:51-70`
`Message_Box_Startup_` · `gendraw.cpp:153-190` `Confirmation_Box_` ·
`gendraw.cpp:239-262` `Message_Box_Cleanup_` · `harold.cpp:1274-1336`
`User_Box_` · `harold.cpp:142-160` the language font files ·
`remap.cpp:47` `Find_Closest_Color_` · `remap.cpp:132-152`
`Create_Picture_Remap_Palette_` · `remap.cpp:189-201`
`Calculate_Picture_Remap_Colors_` · `fonts.cpp:72-85` `Load_Palette_` ·
`misc.cpp:40` `Font_Colors2_` · `bill.cpp:76` `_Print_Paragraph_` ·
`flt1.cpp:1130` the Fleets background · `flt1.cpp:260-309` the Fleets
scroll bar · `flt2.cpp:196` `Fix_Palette_`.
