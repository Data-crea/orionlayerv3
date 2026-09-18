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

#: `Add_Hidden_Field_` type, which every big icon and the star fields
#: use (fields.cpp; the reading's §2 table).
TYPE_HIDDEN = 7
#: `Add_Button_Field_` type.
TYPE_BUTTON = 0
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
