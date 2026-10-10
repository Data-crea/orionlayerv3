"""The pickers' right clicks — work order 200 B (it replaces work order 185's
omission of them, which carried the name `picker_help`).

TRANSCRIPTION `picker_right`: what the original answers a right click in
each picker with (desbox.cpp), item by item —

  generic (shield / computer), `Draw_Generic_Replacement_Box_Help_`
  (:873-948): Clear 683 / 686, OK 682 / 685, the box 681 / 684 (shield /
  computer), the "none" row 692 / 693 — help entries; a shield or computer
  row: its description, a `Text_Box_`
  special systems (:225-256): the "none" row 691, the first button 689,
  the second 687 — help entries; a system row: its description
  weapons: the box's own help list (`Set_Weapon_Replacement_Screen_Help_
  List_`, evanhelp.cpp:419-465 — the four filters 392-395, Cancel 396,
  Accept 397, the arcs 398 or racks 399 area), then the list's first row,
  "no weapon", 690 (desbox.cpp:1510-1516), a weapon row's description, a
  modification's
  (`Print_Weapon_Mod_Help_Description_`, :1462-1464 and :1938-1964)

A help entry is HD's own help popup with the game's text (the game's
help box is not on the wire); a description is the game's own
`Text_Box_`, which comes back on the wire: HD sends the right click to
that row's or button's field (`core/rightinfo`).
"""
from core import rightinfo
from screens.leaders import ldrdraw as nd

SHIELD, COMPUTER = 2, 8          # TECH_APPLICATION_TYPE_* (orion2_consts.h)
GENERIC = {SHIELD: {"clear": 683, "ok": 682, "box": 681, "none": 692},
           COMPUTER: {"clear": 686, "ok": 685, "box": 684, "none": 693}}
SPECIAL = {"ok": 689, "clear": 687, "none": 691}
WEAPON = {"filters": (392, 393, 394, 395), "clear": 396, "ok": 397,
          "arcs": 398, "racks": 399, "none": 690}


def target(screen, box, x, y):
    """('help', id) or ('field', field, why) for a right click, or None."""
    hit = lambda f: f is not None and \
        nd.field_hit(screen.layout, f, x, y)  # noqa: E731
    acc = box.accept()
    if box.kind == "weapon":
        for f, hid in zip(box.filter_fields(), WEAPON["filters"]):
            if hit(f):
                return "help", hid
        if hit(box.cancel):
            return "help", WEAPON["clear"]
        if hit(acc):
            return "help", WEAPON["ok"]
        arc = box.arc_box_field()
        if hit(arc):
            return "help", WEAPON["racks" if box.rack_fields() else "arcs"]
        for _i, f, _on in box.mods():
            if hit(f):
                return "field", f, "modification"
        for _y, row, f in box.rows():
            # the weapon a row shows is `Weapon_Index_(row)`, not DSBX's
            # `item` (`_design_choice_items`); the list's first row is the
            # "no weapon" row (ext_api.cpp's DSBX: `weapon > 0 && row > 0`)
            if hit(f):
                first = next(i for i, r in enumerate(box.box["rows"])
                             if r is row) == 0
                return ("help", WEAPON["none"]) if first \
                    else ("field", f, "weapon row")
        return None
    words = GENERIC.get(box.box.get("replacement_type")) \
        if box.kind == "generic" else SPECIAL
    if words is None:
        return None
    for _y, row, f in box.rows():
        if hit(f):
            return ("help", words["none"]) if row["item"] <= 0 \
                else ("field", f, f"{box.kind} row")
    if hit(box.cancel):
        return "help", words["clear"]
    if hit(acc):
        return "help", words["ok"]
    if box.kind == "generic" and hit(box.base):
        return "help", words["box"]
    return None


def answer(screen, box, x, y):
    """Do it. True when the click was taken."""
    t = target(screen, box, x, y)
    if t is None:
        return False
    if t[0] == "help":
        entry = screen.helptext.entry(t[1]) or \
            screen.helptext.missing_entry(t[1])
        screen.help.open(t[1], *entry)
        return True
    return rightinfo.send(screen.app, t[1], t[2], rightinfo.opener(screen))
