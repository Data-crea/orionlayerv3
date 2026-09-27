"""What a Ship Designer picker reads off the wire, and whether it may draw.

Work order 185. A picker draws ONLY from open fix 45's "DSBX" block
(`core/designblocks.py`) and the field list the game built for it; fix 45
is NOT APPLIED (UNVERIFIED `fix45`). Without DSBX the ids 54-56 never
reach the wire — an engine without the fix reports 3 for a picker, and the
page hands that list to the game's picture (`screens/ship_design/sdwire`).

THE STATES:
  READY     DSBX on the wire and the picker's own list up: its catch-all
            field (whose origin is the box's base) and its Cancel button
            (type 0, hotkey ESC). The picker draws and takes input.
  GAME_BOX  DSBX on the wire and a list that is not the picker's — a
            message box over it ("Beam weapons must have …", a special's
            exclusion warning): HD has no view for it and hands over, a
            modal net (`handover_is_modal`), decision 22's case.
  MISMATCH  the list and DSBX disagree (the weapon picker's modification
            fields are not as many as DSBX says it offers): the picker
            cannot name what it would draw, and hands back to the game's
            picture rather than guess (the research panel's rule).
"""
from . import dbgeom as geom

READY, GAME_BOX, MISMATCH = "ok", "game_box", "mismatch"


def _rect(f):
    return (f.x, f.y, f.x_end, f.y_end)


def _area(f):
    return (f.x_end - f.x) * (f.y_end - f.y)


def claims(state):
    """Ids 54-56 are HD's only with DSBX and DSGN on the wire (45, 44)."""
    return getattr(state, "design_box", None) is not None and \
        getattr(state, "ship_design", None) is not None


class Box:
    """One snapshot's reading of the open picker."""

    def __init__(self, state):
        self.box = getattr(state, "design_box", None)
        self.design = getattr(state, "ship_design", None)
        self.fields = [f for f in (getattr(state, "fields", None) or [])
                       if f.index != 0]
        self.kind = self.box["kind"] if self.box else None
        hidden = [f for f in self.fields if f.field_type == geom.TYPE_HIDDEN
                  and _rect(f) != geom.FULL_SCREEN]
        self.base = max(hidden, key=_area) if hidden else None
        self.cancel = next((f for f in self.fields
                            if f.field_type == geom.TYPE_BUTTON
                            and f.hotkey == geom.ESC), None)
        self.full_screen = next((f for f in self.fields
                                 if _rect(f) == geom.FULL_SCREEN), None)
        if self.box is None:
            self.state, self.reason = GAME_BOX, "no DSBX block (open fix 45)"
        elif self.base is None or self.cancel is None:
            self.state = GAME_BOX
            self.reason = ("a box over the picker HD has no view for — the "
                           "game's own picture answers it")
        elif self.kind == "weapon" and \
                len(self.mod_fields()) != len(self.box["mods_offered"]):
            self.state = MISMATCH
            self.reason = (f"{len(self.mod_fields())} modification fields, "
                           f"DSBX offers {len(self.box['mods_offered'])}")
        else:
            self.state, self.reason = READY, ""

    @property
    def draws(self):
        return self.state == READY

    @property
    def origin(self):
        return self.base.x, self.base.y

    def _hidden_at_x(self, dx, width=None):
        bx = self.base.x
        return sorted((f for f in self.fields
                       if f.field_type == geom.TYPE_HIDDEN and
                       f.x == bx + dx and
                       (width is None or f.x_end - f.x == width)),
                      key=lambda f: f.y)

    # ── The rows ─────────────────────────────────────────────────────

    def rows(self):
        """[(native y of the row's text, row dict, its field or None)] for
        every row the picker prints, top to bottom."""
        bx, by = self.origin
        rows = self.box["rows"]
        if self.kind == "generic":
            fields = {f.y: f for f in self._hidden_at_x(10)}
            y0 = by + geom.GENERIC_HEAD_Y + geom.GENERIC_ROW_DY
            # `-1` rows (not researched) are neither printed nor fielded
            # (desbox.cpp:751-781, :810-864).
            return [(y0 + i * geom.GENERIC_STEP, r,
                     fields.get(y0 + i * geom.GENERIC_STEP))
                    for i, r in enumerate(rows) if r["item"] >= 0]
        first = max(0, self.box["first_row"])
        if self.kind == "weapon":
            fields = self._hidden_at_x(0x1C, 0x256 - 0x1C)
            return [(f.y, rows[first + k], f) for k, f in enumerate(fields)
                    if first + k < len(rows)]
        fields = self._hidden_at_x(25)
        return [(f.y, rows[first + k], f) for k, f in enumerate(fields)
                if first + k < len(rows)]

    # ── The weapon picker's lower box ────────────────────────────────

    def arc_box_field(self):
        """The arc / rack box's field (base + 0x1D), or None."""
        found = self._hidden_at_x(0x1D)
        return found[0] if found else None

    def rack_fields(self):
        return [f for f in self._hidden_at_x(0x77) if f.y_end - f.y == 0xF]

    def arc_fields(self):
        return [f for f in self._hidden_at_x(0x77) if f.y_end - f.y == 0xD]

    def mod_fields(self):
        """The modification fields in the order the original adds them
        (mod index ascending — `Get_Weapon_Mod_Field_XYs_` lays them out
        left, right, next line)."""
        bx = self.base.x if self.base else 0
        found = [f for f in self.fields if f.field_type == geom.TYPE_HIDDEN
                 and f.x - bx in (233, 386) and f.x_end - f.x == 0x8C]
        return sorted(found, key=lambda f: (f.y, f.x))

    def mods(self):
        """[(mod index, field, on)] — DSBX's offered list beside the
        fields, one for one."""
        return [(i, f, self.box["mod_status"][i] == 1)
                for i, f in zip(self.box["mods_offered"], self.mod_fields())]

    def filter_fields(self):
        """The four filters' fields, in DSBX's filter order (beam, missile,
        bomb, special), found by their x (base + FILTER_XS)."""
        bx = self.base.x
        out = []
        for dx in geom.FILTER_XS:
            out.append(next((f for f in self.fields
                             if f.x == bx + dx and
                             f.field_type == geom.TYPE_HIDDEN), None))
        return out

    def accept(self):
        """The Accept field: a button (hotkey A) while the choice is
        valid, a hidden field at its place otherwise
        (`Add_Replacement_Weapon_Fields_`, desbox.cpp:503-525)."""
        if self.cancel is None:
            return None
        return next((f for f in self.fields if f is not self.cancel and
                     abs(f.x - self.cancel.x) <= 1 and
                     f.y > self.cancel.y), None)

    def scroll_buttons(self):
        """Buttons that are neither Cancel nor Accept: the scroll arrows
        a list of more than ten rows gets."""
        acc = self.accept()
        return [f for f in self.fields if f.field_type == geom.TYPE_BUTTON
                and f is not self.cancel and f is not acc]
