# The Planets screen in orion2re — a reading

`src/game/plntsum.cpp`, namespace `PLNTSUM`, 2252 lines. Read
4 September 2026 against **orion2re 1.60.0** (`src/version.h`); a 1.31
archive numbers these differently.

Committed because the reading is paid for and the screen is not built
yet — it waits on frame artwork, which nothing in this tree can
produce. Nothing here is drawn anywhere; this is the source, written
down once so the next session does not buy it twice.

**`SCREEN_PLANET_SUMMARY = 32`** (`orion2_consts.h:487`). Not to be
confused with `SCREEN_PLANET_DATA = 18`, which is a different screen.

---

## The row set, and the trap first

`Filter_Explored_Planets_` (plntsum.cpp:976-1043) rebuilds the list.
The order of its tests matters and **the first one is the trap
`core/structs/planet.py` warns about**:

1. `planet_type != PLANET_TYPE_PLANET` → out. *This is checked before
   anything reads `colony_index`.*
2. `Planet_Has_Players_Colony_` (:365) → out. Reads `colony_index`,
   then `_colony[...].owner == _PLAYER_NUM`.
3. `Planet_Is_Outpost_Planet_` (:355) → out. `colony_index > -1` and
   `_colony[...].outpost_flag != 0`.
4. `Planet_Has_Been_Visited_` (:376) → out unless visited or
   omniscient. Visitation is by the planet's STAR, through
   `HAROLD::Player_Has_Visited_`.
5. Five optional filters, each behind its own toggle: out of range
   (`Star_In_Extended_Range_Of_Player_`), adverse gravity
   (`Productivity_Penalty_ > 0`), enemy controlled, hostile
   environment (`food_per_farmer <= 0`), mineral scarcity
   (`mineral_class` POOR or ULTRA_POOR).

What is stored per surviving row (`s_plntsum_planet`): `max_pop` from
`COLCALC::Planet_Max_Population_For_Player_`, `food_per_farmer`,
`minerals` from `COLCALC::_minerals_per_mine[mineral_class]`,
`mineral_class`, `climate`, and `explored` — the planet index.

The list is rebuilt and re-sorted **only when the count changes**
(:1044-1049), which also resets `_scanned_field`.

## Eight rows, and the pitch is a table

`Summary_Screen_Print_Data_` clamps to eight
(plntsum.cpp:54-56), and `Draw_Rotating_Planets_` clamps to eight
again (:1704-1707).

```
_plntscrn_delta_y[9] = {0, 55, 109, 164, 219, 274, 329, 383, 479}
                                                  plntsum.cpp:11
y_base = _plntscrn_delta_y[row] + 0x27              (:60)
```

**The gaps are 55, 54, 55, 55, 55, 55, 54 — not uniform**, and the
ninth entry (479) is a sentinel used as the bottom of the last row's
clip window. Transcribe the table; a step of 55 is wrong on three of
the seven gaps and wrong by a whole row at the bottom.

## Five columns, each a bold line over a small line

All centred, at these native x (plntsum.cpp:57-195):

| x | upper (font style 2) | lower (font style 1) |
|---|---|---|
| 61 `0x3d` | planet name, fitted to 86 px wide | `(Race)` when colonised, or a monster's race |
| 140 `0x8c` | climate | `"<n> Food"` from `food_per_farmer` |
| 217 `0xd9` | gravity | productivity penalty, `H_Message_(0x142)` |
| 311 `0x137` | mineral class | `H_Message_(0x152)` with `minerals` |
| 386 `0x182` | planet size | `H_Message_(0x143)` with `max_pop` |

Above the name, when the system or planet carries one, a **special**
string at `Print_Centered_(0x3d, y_base)` — a space monster's ship
name, Ancient Artifacts, or `_planet_special_string[]`.

**The gravity column moves when there is no penalty**
(plntsum.cpp:171-179). With a penalty it prints gravity at
`y_climate` and the penalty line below. With none it prints gravity
alone at `y_climate + gravity_h / 2` — half a line down, filling the
space the second line would have used. Two different y for the same
column depending on data; transcribe it, do not unify it.

The name column is clipped: `Set_Window_(0x12, y_base, 0x68, …)` then
`Clip_On_` (:75-76), i.e. native x 18..104.

## What else is on the screen

- **A rotating planet sprite per row** (`Draw_Rotating_Planets_`,
  :1699-1731), centred in an 86x25 cell at native x 18,
  `_p_rotating_planet[climate * PLANET_SIZE_COUNT + size]`.
- **Its own small galaxy map** at native (443, 17, 180, 116)
  (`Wrapper_For_Planet_Summary_Galaxy_Map_`, :1351).
- **A scroll bar** at native x 421..431, y 37..444
  (`Fill_Summary_Screen_Scroll_Bar_`, :1734), ten one-pixel lines
  with the colour stepping every second column.
- **Three sort buttons** at native (441, 200), (501, 200), (567, 200)
  and **five filter radio buttons** at x 441, y 266/289/312/335/358
  (`Add_Plntsum_Fields_`, :692-706).
- **Send Colony / Send Outpost** sprites at (454, 386) and (454, 413).
- **Row hit boxes**: `Add_Hidden_Field_(18, delta_y[i] + 36, 414,
  … + 50)` (:733-735).
- **ETA markers** per row, `pics[13]`, at native x 18 (outpost) and
  x 102 minus the sprite width (colony) (:2160, :2197).

## Three sort keys, all descending

`_sort_choice` selects among them (`Sort_Planet_Summary_`, :1234):

| choice | comparator | line |
|---|---|---|
| 0 | `rhs->climate - lhs->climate` | :1216 |
| 1 | `rhs->minerals - lhs->minerals` | :1222 |
| 2 | `rhs->max_pop - lhs->max_pop` | :1228 |

All three subtract left from right, so all three sort **descending**.
There is no ascending mode and no toggle.

---

## Three things to hold on to when this is built

Written here rather than left in a session report, because the
build is a later package and these are the parts a reader will get
wrong from the shape of the code alone.

1. **`_plntscrn_delta_y` is transcribed as a TABLE, never as a
   step.** See above: three of its seven gaps are 54, not 55.
2. **The gravity column's half-line shift is transcribed, not
   unified.** It is data-dependent layout, and a renderer that puts
   gravity at one y is wrong on every planet whose gravity costs
   nothing.
3. **The small galaxy map here is the SECOND site of the inset**, and
   it has its own centre offset: this screen calls
   `Get_Galaxy_Map_Star_XY_` with `star_marker_mode = 2`
   (plntsum.cpp:1370), where the colony summary passes 0
   (colsum.cpp:734). That argument picks the centre offset —
   `star_center_offset = (mode == 0) ? 2 : 3` (movebox.cpp:374). Two
   sites, not three, so this is **noted and not extracted**; the
   third is the signal.
