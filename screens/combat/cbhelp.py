"""The battle's right-click help — work order 200 B.

TRANSCRIPTION `combat_help`: `COMBAT1::Set_Combat_Help_Fields_`
(combat1.cpp:2402-2590), the list the battle installs with its fields
(:72) and again when the weapon and special tabs switch (:580, :585),
walked in its order, the first entry with an id winning
(`Check_Help_List_`, fields.cpp:2935-2954; an id of -1 is passed over):

  OPTIONS panel down      the six buttons AUTO 623, SCAN 624, BOARD 625,
                          RETREAT 626, WAIT 627, DONE 628, and OPTIONS 617
  OPTIONS panel up        SELF DESTRUCT 695, the five lights 696-700
  then                    the current ship display 618 (HD's picture with
                          its shields), the reduced map (missile warning
                          panel 621 / map 620) — no HD element, HD draws no
                          reduced map (HD EXTENSION `whole_grid`, 199) —
                          the internals / target display 622 (HD's lines of
                          the unit's systems, which the original prints
                          there: drive, shields, computer, structure,
                          armour, speed, remaining), then the eight
                          weapon rows: a weapon's own entry, its tech
                          application's (`TECHDATA::_weapons[id].tech_app_id`),
                          or on the specials tab each special system's, -1
                          on an empty row; last the weapons display 629

The help ids of a row are HELP.LBX's entries for the tech applications —
the same records `Get_Application_Description_` reads. The battlefield
has no entry: a right click there turns the ship (`screen`).
"""
#: `TECHDATA::_weapons[i].tech_app_id`, techdata.cpp:481-527, copied by
#: script (the field after `weapon_id`); 46 weapons, `WEAPON_COUNT`.
WEAPON_APP = (
    0, 104, 78, 100, 123, 70, 97, 79, 115, 127, 54, 47, 137, 165, 121, 106,
    149, 202, 12, 146, 139, 119, 71, 10, 118, 48, 28, 105, 17, 83, 31, 66,
    171, 13, 80, 140, 148, 30, 174, 188, 0, 0, 0, 0, 0, 0)
#: `TECHDATA::_specials[i].tech_app_id`, techdata.cpp:438-479, likewise
#: (the field after `special_id`); 40 specials, `SPECIAL_COUNT`.
SPECIAL_APP = (
    0, 1, 20, 23, 25, 26, 38, 45, 53, 57, 60, 63, 64, 81, 82, 85, 90, 93,
    94, 102, 112, 111, 125, 126, 150, 151, 153, 56, 158, 159, 161, 172, 175,
    177, 185, 190, 192, 196, 199, 23)
BUTTON_HELP = {"auto": 623, "scan": 624, "board": 625, "retreat": 626,
               "wait": 627, "done": 628, "options": 617}
OPTION_HELP = {"self_destruct": 695, "missile_warning": 696, "fast": 697,
               "legal_moves": 698, "shield_arcs": 699, "grid": 700}
SHIP_DISPLAY, SYSTEMS_DISPLAY, WEAPONS_DISPLAY = 618, 622, 629


def row_ids(unit, specials):
    """The eight rows' help ids (combat1.cpp:2506-2531): the loop reads
    special bits 0..38."""
    if specials:
        flags = unit.get("special_device_flags") or [0] * 5
        ids = [SPECIAL_APP[b] for b in range(39)
               if flags[b >> 3] >> (b & 7) & 1]
        return (ids + [-1] * 8)[:8]
    out = []
    for w in unit["weapons"][:8]:
        wid = int(w["weapon_id"])
        app = WEAPON_APP[wid] if 0 <= wid < len(WEAPON_APP) else 0
        out.append(app if app else -1)
    return out + [-1] * (8 - len(out))


def help_at(panel, opts, options_up, unit, specials, x, y):
    """The help id under (x, y), or None."""
    if options_up:
        for key, r in opts.rects.items():
            if key in OPTION_HELP and r.collidepoint(x, y):
                return OPTION_HELP[key]
    else:
        key = next((k for k, r in panel.all_buttons.items()
                    if r.collidepoint(x, y)), None)
        if key in BUTTON_HELP:
            return BUTTON_HELP[key]
    if panel.facts is not None and panel.facts.collidepoint(x, y):
        return SYSTEMS_DISPLAY
    if panel.left is not None and panel.left.collidepoint(x, y):
        return SHIP_DISPLAY
    if unit is not None:
        ids = row_ids(unit, specials)
        for r, k in panel.help_rows:
            if r.collidepoint(x, y) and 0 <= k < 8 and ids[k] != -1:
                return ids[k]
    if panel.mid is not None and panel.mid.collidepoint(x, y):
        return WEAPONS_DISPLAY
    return None


def right(screen, x, y):
    """The screen's right CLICK (not a drag): close the help that is open,
    or open the entry under the point. True when it was help's."""
    if screen.help.visible:
        screen.help.close()
        return True
    hid = help_at(screen._panel, screen._opts, screen._opts.up(screen._state),
                  getattr(screen, "_panel_unit", None), screen._specials, x, y)
    if hid is None:
        return False
    entry = screen.helptext.entry(hid) or screen.helptext.missing_entry(hid)
    screen.help.open(hid, *entry)
    return True
