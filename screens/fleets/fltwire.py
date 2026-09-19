"""What the Fleets screen may believe, and what it refuses to draw.

**THE CONTENT OF THIS SCREEN CANNOT BE RECONSTRUCTED, AND THAT WAS
ESTABLISHED BEFORE A PATCH WAS ASKED FOR** — decision 25's order of
operations. Three routes were followed to their end first:

1. **The FSEL block** (open fix 20) sends the whole `_ship_node` table
   but only ONE chain, the galaxy map's fleet box's, and that chain is
   `-1` here because the fleet screen closes box 2 (flt1.cpp:826-832).
   `_ship_stack_start[]` and `next_node` are not on the wire at all.
2. **Walking the node table** names ships the player cannot see:
   `Remove_Non_Detected_Ships_` unlinks nodes of foreign stacks
   (shipstak.cpp:200-250) and `Delete_Ship_Node_` leaves their
   `ship_idx` in place (:5-11).
3. **Grouping own ships by `s_ship.location`** produces a different list
   from the engine's in both membership and order — the two filters
   (flt2.cpp:130-146) and `Ok_To_Add_Ship_` decide membership, and the
   officer move-to-front decides order (flt2.cpp:263-265) — and it has
   no way to say that it differs.

So open fix 27 asks for the state and open fix 28 for the one write.
What this module then does is NOT reconstruction, it is a READ with a
validation, which is the other half of decision 25's rule.

**THE VALIDATION IS THE FIELD LIST, AND IT IS A REAL SECOND SOURCE.**
`Add_Fltscrn_Big_Icon_Fields_` (flt2.cpp:279-336) adds one hidden field
per DISPLAYED icon at exactly `(x, y, x+58, y+57)` with `x, y` from
`Get_Fltscrn_Big_Icon_XY_(slot)` — the same twenty cells `fltgeom`
draws. The block says how many icons are displayed; the field list says
where they are. If the two disagree, this screen has misread something
and says so rather than drawing a grid.

The one case where they legitimately differ is a FOREIGN stack: the
builder adds fields only when `_PLAYER_NUM == owner` (flt2.cpp:312-322),
so a foreign stack shows icons and adds no fields. The block carries
`_fltscrn_stack_owner`, so that case is recognised and is not a
mismatch.

**WHAT IS STILL NOT DRAWN, AND IT IS MARKED EVERYWHERE, NOT HIDDEN:**

- **OMISSION — the ship's own picture in a grid cell.** The original
  draws `SHIPS.LBX picture_num + 50*colour` (ken.cpp:451-466), which is
  MOO2's artwork and is never in this tree. The cell carries the ship's
  name, its owner colour and its damage instead. HD has the small map
  marker (derived artwork, decision 42) and no big design picture.
- **OMISSION — the attack and defense bonuses** in the ship panel.
  `INITSHIP::Get_Ship_Combat_Bonuses_` (initship.cpp:638-687) derives
  them from officer skills, `_crew_data`, traits, the strategic-combat
  flag and `Best_Warp_Drive_`; three of those inputs are UNVERIFIED
  offsets and one is not decoded, so a number here would be a guess
  wearing two decimal places.
- **OMISSION — the move preview** ("N turns to X"). Hover-computed by
  `SHIPMOVE::Ships_Try_To_Move_To_` (flt2.cpp:356-429), never on the
  wire, and transcribing it means copying a function nobody has read.
- **OMISSION — the captain's portrait.** `s_leader_data` is UNVERIFIED
  (`core/structs/unverified.py`) and the portrait is LBX art.

Every one of them is in `layout.json` under `marks` and in
`doc/briefs/134-parked-for-data.md`, which is where decision 61 puts
them.
"""
from core import livefields

#: Ready to draw: the block is there and the field list agrees.
READY = "READY"
#: No FLTS block. Three situations with one shape — another screen, an
#: engine without `doc/ext_fleet_screen_state.patch`, or a block cut
#: short — and the screen cannot tell them apart from the outside, so it
#: says all three and hands over.
NO_BLOCK = "NO_BLOCK"
#: The block is there and shows no stack (`_small_ship_stack_ptr` -1,
#: which is the state before `Set_Initial_Stack_Pointer_` finds one, and
#: after the last own ship is scrapped).
NO_STACK = "NO_STACK"
#: No field list. Nothing can be sent, because a send resolves its field
#: in the list it was handed (decision 20) — so nothing may be drawn as
#: if it could be clicked.
NO_FIELDS = "NO_FIELDS"
#: The block and the field list disagree about the displayed icons.
MISMATCH = "MISMATCH"
#: A field is in the list that `Fleet_Screen_` does not build. Something
#: else is on screen — a native message box is the case that named this
#: state — and HD must not go on drawing over it.
FOREIGN_FIELDS = "FOREIGN_FIELDS"

#: `Add_Hidden_Field_` type, which every big icon and the star fields
#: use (fields.cpp; the reading's §2 table).
TYPE_HIDDEN = 7
#: `Add_Button_Field_` type.
TYPE_BUTTON = 0
#: `Add_Scroll_Field_` type (fields.cpp:605).
TYPE_SCROLL = 6
#: `Add_Radio_Button_Field_` type.
TYPE_RADIO = 1

#: The seven controls and the two radios, by the hotkey their builder
#: gave them (flt1.cpp:1188-1258). A send finds its field by this in the
#: list that is on the wire at the moment of the click, never by index.
HOTKEYS = {
    "btn_scrap": (ord("S"), TYPE_BUTTON),
    "btn_all": (ord("A"), TYPE_BUTTON),
    "btn_return": (0x1B, TYPE_BUTTON),
    "btn_leaders": (ord("L"), TYPE_BUTTON),
    "btn_relocate": (ord("R"), TYPE_HIDDEN),
    "btn_support": (ord("U"), TYPE_RADIO),
    "btn_combat": (ord("C"), TYPE_RADIO),
    "scroll_up": (ord("-"), TYPE_BUTTON),
    "scroll_down": (ord("+"), TYPE_BUTTON),
    "prev_fleet": (ord(","), TYPE_BUTTON),
    "next_fleet": (ord("."), TYPE_BUTTON),
}


#: EVERY FIELD `FLT1::Add_Fleet_Screen_Fields_` BUILDS (flt1.cpp:1177-1263),
#: read out of the builders rather than off a dump, because a dump is an
#: interpretation ("A field dump is not documentation") and because the
#: one thing a dump cannot give is the set that is NOT there.
#:
#: Recognition is by GEOMETRY AND TYPE, never by index: the ids are
#: running numbers and shift with the icon count, the star count and the
#: officer. Three shapes of rule, for three shapes of field.
#:
#: 1. EXACT RECTANGLE, where the source gives all four numbers.
#: 2. EXACT ORIGIN, where the extent comes from FLEET.LBX artwork at
#:    runtime (`x_end = x + Get_Width_(pic) - 1`, fields.cpp:372-373) and
#:    is therefore not in any source. The top-left IS in the source, and
#:    a foreign field would have to land on it exactly AND carry the
#:    right type.
#: 3. AS A CLASS, for the two families whose members are one per star or
#:    one per ship icon. Both are bounded by the inset window.

#: Rule 1. `(x, y, x_end, y_end)` -> the types it may carry.
EXACT_FIELDS = {
    #: The screen-filling catcher, added last (flt1.cpp:1261).
    (0, 0, 639, 479): (TYPE_HIDDEN,),
    #: MAINSCR::_debug_field (flt1.cpp:1252).
    (0, 470, 10, 479): (TYPE_HIDDEN,),
    #: The big-icon scroll bar: Add_Scroll_Field_(605, 86, …, 14, 234)
    #: (flt1.cpp:1246 -> flt2.cpp:106), and Add_Scroll_Field_ writes
    #: `x_end = x + width` and `y_end = y + height` (fields.cpp:602-603)
    #: — a PLUS, not a plus-minus-one, unlike the button builders.
    (605, 86, 619, 320): (TYPE_SCROLL,),
}

#: Rule 2. Control -> (origin, the types it may carry). Every number is
#: the literal in the call that adds it.
CONTROL_ORIGINS = {
    "btn_scrap":    ((549, 380), (TYPE_BUTTON,)),   # flt1.cpp:1187
    "btn_all":      ((348, 380), (TYPE_BUTTON,)),   # :1195
    "btn_return":   ((556, 430), (TYPE_BUTTON,)),   # :1201
    "scroll_up":    ((606,  59), (TYPE_BUTTON,)),   # :1214
    "scroll_down":  ((605, 325), (TYPE_BUTTON,)),   # :1215
    "prev_fleet":   (( 19, 249), (TYPE_BUTTON,)),   # :1217
    "next_fleet":   ((283, 249), (TYPE_BUTTON,)),   # :1218
    "btn_relocate": ((441, 380), (TYPE_HIDDEN,)),   # :1229
    #: LEADERS is a BUTTON with an officer and a HIDDEN field without
    #: one, at the same origin (:1234, :1240) — which is why the type
    #: alone never identifies a control here.
    "btn_leaders":  ((342, 430), (TYPE_BUTTON, TYPE_HIDDEN)),
    "btn_support":  ((425, 435), (TYPE_RADIO,)),    # :1256
    "btn_combat":   ((487, 435), (TYPE_RADIO,)),    # :1257
}

#: Rule 3a. A star field of the inset: `Add_Galaxy_Map_Fields_2_` with
#: `field_style` 1 adds `(sx-3, sy-3, sx+8, sy+9)` per star
#: (movebox.cpp:504-511) at positions `Get_Galaxy_Map_Star_XY_` puts
#: inside the inset window. So the SIZE is exact and the position is
#: bounded — which is the class, and it is tight enough that nothing
#: else in this list has that shape.
STAR_FIELD_SIZE = (11, 12)      # x_end - x, y_end - y
STAR_FIELD_MARGIN = 3           # the -3 in the call

#: The inset window, `Set_Window_(15, 52, 320, 234)` (movebox.cpp:469
#: with flt1.cpp:1250's four numbers). Inclusive.
INSET_WINDOW = (15, 52, 320, 234)


def _in_inset(x, y, margin=STAR_FIELD_MARGIN):
    left, top, right, bottom = INSET_WINDOW
    return (left - margin <= x <= right + margin
            and top - margin <= y <= bottom + margin)


def foreign_fields(fields, cells, icons):
    """Every field in the live list that `Fleet_Screen_` does not build.

    Rule 3b lives here rather than in a table: a small ship icon's field
    is `Add_Hidden_Field_(icon.x, icon.y, icon.x + w, icon.y + h)`
    (flt2.cpp:34-41), and while its extent comes from FLEET.LBX its
    TOP-LEFT is `_ship_icon[i].x/y` — which is on the wire. So the class
    is matched against the snapshot's own icon positions and needs no
    margin at all. (Those coordinates are the fleet inset's while this
    screen is up, which is exactly what `ships.ScreenStateGate` keeps
    off the galaxy map; here they are what they say they are.)
    """
    cell_rects = {(x, y, x + 58, y + 57) for x, y in cells}
    origins = {(icon.x, icon.y) for icon in (icons or [])}
    control_origins = {}
    for _origin, _types in CONTROL_ORIGINS.values():
        control_origins[_origin] = control_origins.get(_origin, ()) + _types
    out = []
    for f in (fields or []):
        # FIELD 0 IS NOT A FIELD. `fields::Clear_Fields_` sets
        # `_fields_count = 1`, not 0 (fields.cpp:207), so slot 0 is
        # never cleared and no `Add_*_Field_` ever writes it — while
        # `SerializeFields` sends every field from `i = 0`
        # (ext_api.cpp:326). Nothing in the engine sets the count to 0,
        # so a real field can never land there.
        #
        # The fundament has said so since decision 59 — "never field 0,
        # which after a message box carries whatever geometry the list
        # held before" — and this rule was written without it. Measured
        # live on 19 September 2026 (work order 140): it was the ONE
        # stranger in a list of 92, it read `(0, 0, 0, 0)` type 0, and
        # it was the whole reason the Fleets screen was never seen.
        if f.index == 0:
            continue
        r = livefields.rect(f)
        types = EXACT_FIELDS.get(r)
        if types is not None and f.field_type in types:
            continue
        if f.field_type == TYPE_HIDDEN and r in cell_rects:
            continue
        if f.field_type == TYPE_HIDDEN and (f.x, f.y) in origins:
            continue
        if (f.field_type == TYPE_HIDDEN
                and (r[2] - r[0], r[3] - r[1]) == STAR_FIELD_SIZE
                and _in_inset(f.x, f.y)):
            continue
        types = control_origins.get((f.x, f.y))
        if types is not None and f.field_type in types:
            continue
        out.append(f)
    return out


def hotkey_field(fields, name):
    """The live field for one control, or None.

    LEADERS is the case that shows why the type matters as well as the
    key: with no officer the builder adds it as a HIDDEN field with no
    hotkey at all (flt1.cpp:1238-1240), so asking for type 0 with "L"
    returns None exactly when the button is dead. RELOCATE is the mirror
    — it is a hidden field WITH a hotkey, always (:1229).
    """
    want = HOTKEYS.get(name)
    if not want:
        return None
    key, ftype = want
    return next((f for f in (fields or [])
                 if f.hotkey == key and f.field_type == ftype), None)


def icon_field(fields, cell):
    """The live field for one native grid cell `(x, y)`, or None.

    The rect is exact and not a guess: `Add_Fltscrn_Big_Icon_Fields_`
    builds it as `(x, y, x + 0x3a, y + 0x39)` on this screen
    (flt2.cpp:288-290, :313-320).
    """
    x, y = cell
    want = (x, y, x + 58, y + 57)
    return next((f for f in (fields or [])
                 if f.field_type == TYPE_HIDDEN
                 and livefields.rect(f) == want), None)


class View:
    """The fleet screen's state, read and validated, or a refusal.

    `state` is one of the constants above and `reason` is the sentence
    the screen shows when it is not READY. Nothing else in this class is
    valid unless `state == READY`.
    """

    def __init__(self, game_state, cells):
        self.state = NO_BLOCK
        self.reason = ""
        self.block = None
        self.rows = []          # (slot, ship_idx, selected) in display order
        self.own_stack = False
        self._read(game_state, cells)

    # ── Reading ───────────────────────────────────────────

    def _read(self, game_state, cells):
        block = getattr(game_state, "fleet_screen", None)
        if not block:
            self.reason = (
                "The fleet screen's own state is not on the wire. Either "
                "this engine does not carry doc/ext_fleet_screen_state.patch "
                "(open fix 27), or the block arrived short. Nothing here "
                "can say WHICH ships are in the grid without it, so the "
                "original picture is shown instead.")
            return
        self.block = block
        fields = getattr(game_state, "fields", None)
        if not fields:
            self.state = NO_FIELDS
            self.reason = (
                "No field list. Every send on this screen resolves its "
                "field in the list that is on the wire at the moment of "
                "the click (decision 20), so with no list nothing may be "
                "drawn as though it could be clicked.")
            return
        if block.get("stack", -1) < 0 or not block.get("ship_idx"):
            self.state = NO_STACK
            self.reason = (
                "The game is showing no fleet. `_small_ship_stack_ptr` is "
                "-1, which is the state before the screen has found a "
                "stack and after the last own ship is gone.")
            return

        # A FIELD NOBODY HERE BUILT MEANS SOMETHING ELSE IS ON SCREEN.
        # Checked before the cell validation, because it is the more
        # actionable answer when both could fire: "the list disagrees
        # with the block" reads as a misreading of ours, and this is
        # not one. Work order 137 A, from the state 136 D found —
        # SCRAP's confirmation box adds two hidden fields and clears
        # nothing (gendraw.cpp:172-173), the screen id stays 4, the
        # FLTS block keeps arriving, and every field this screen built
        # is still in place, so nothing else could have noticed.
        strangers = foreign_fields(fields, cells,
                                   getattr(game_state, "ship_icons", None))
        if strangers:
            self.state = FOREIGN_FIELDS
            where = ", ".join(f"{livefields.rect(f)} type {f.field_type}"
                              for f in strangers[:6])
            more = "" if len(strangers) <= 6 else f" and {len(strangers) - 6} more"
            self.reason = (
                f"{len(strangers)} field(s) in the live list that this "
                f"screen does not build: {where}{more}. Something else "
                f"is on screen — a native message box adds its own "
                f"fields and clears none — so the original picture is "
                f"shown until they are gone.")
            return

        player = getattr(game_state, "player_num", None)
        self.own_stack = (player is not None
                          and player == block.get("owner"))

        first = max(0, int(block.get("first_row", 0))) * 4
        shown = max(0, int(block.get("icons_added", 0)))
        ships = block["ship_idx"]
        selected = block.get("ship_selected") or []
        rows = []
        for slot in range(min(shown, len(cells))):
            idx = first + slot
            if idx >= len(ships):
                break
            rows.append((slot, ships[idx],
                         bool(selected[idx]) if idx < len(selected) else False))

        # THE VALIDATION. One hidden field per displayed cell, at the
        # cell's own rect — but only for an OWN stack, because the
        # builder adds no fields for a foreign one (flt2.cpp:312-322).
        if self.own_stack:
            missing = [slot for slot, _ship, _sel in rows
                       if icon_field(fields, cells[slot]) is None]
            if missing:
                self.state = MISMATCH
                self.reason = (
                    f"The fleet state and the field list disagree: the "
                    f"game says {len(rows)} ship icons are displayed and "
                    f"the field list has no field at "
                    f"{len(missing)} of their cells. Something here has "
                    f"been misread, so nothing is drawn.")
                return

        self.rows = rows
        self.state = READY

    # ── What the screen asks it ───────────────────────────

    @property
    def ok(self):
        return self.state == READY

    def scrollable(self):
        """True when the original would show its two scroll arrows —
        `_n_fltscrn_big_icons > 20` (flt1.cpp:1212)."""
        return bool(self.block) and int(self.block.get("icons", 0)) > 20

    def enabled_buttons(self, fields):
        """The control boxes that are live, read off the LIVE field list.

        This is the honest source and the block is not: SCRAP and ALL
        exist only under conditions (flt1.cpp:1185-1199) and LEADERS
        turns into a hidden field with no hotkey when no officer exists
        (:1232-1241), so "is there a field with this hotkey and this
        type" IS the question, asked of the list the click would go to.
        """
        return {name for name in HOTKEYS
                if hotkey_field(fields, name) is not None}

    def selected_ships(self):
        return [ship for _slot, ship, sel in self.rows if sel]
