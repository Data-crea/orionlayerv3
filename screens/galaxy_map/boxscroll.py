"""Which cells of a stack past nine ships the fleet box shows — work order
197 A2, split out of `boxmodel` at the 300-line guideline (decision 6).

The original's fleet box shows three rows of three and, past nine ships, a
scroll bar (fleetpop.cpp:189-216) whose `first_visible_row` picks the rows
(`_first_fleet_movement_icon = row * 3`, fleetpop.cpp:643). Only open fix
59's "FBSC" block carries that row (`core/fleetscroll.py`); this module
turns it into the first cell, or says why it cannot.
"""

FLEET_ICONS_MAX = 9             # fleetpop.cpp:648-650

#: The bar's buttons, `Add_Button_Field_(…, "-")` and `(…, "+")`
#: (fleetpop.cpp:197-207); the galaxy map answers them with
#: `Scroll_Up_One_Item_` / `Scroll_Down_One_Item_` (mainscr.cpp:3404-3408).
SCROLL_UP_HOTKEY, SCROLL_DOWN_HOTKEY = ord("-"), ord("+")


def scroll_window(state, count):
    """`(first cell, scroll, None)` for a stack of `count` ships, or
    `(None, None, reason)`.

    Up to nine ships the box has no bar (fleetpop.cpp:189) and shows them
    all from cell 0. Past nine the engine shows three rows from
    `_fltpop_scroll_bar.first_visible_row` (fleetpop.cpp:643), which only
    FBSC carries (open fix 59); the block must name the stack FSEL names,
    and its row must lie inside the bar, or the two are not one moment.
    `scroll` names the bar's rows and the up / down fields as the live list
    carries them (None where the list does not — the engine adds them only
    while the box takes input, fleetpop.cpp:196)."""
    if count <= FLEET_ICONS_MAX:
        return 0, None, None
    bar = getattr(state, "fleet_box_scroll", None)
    sel = getattr(state, "fleet_selection", None) or {}
    if not bar:
        return None, None, (f"a stack of {count} ships and no FBSC block "
                            f"(open fix 59): which rows the box shows is "
                            f"not on the wire")
    if bar["stack"] != sel.get("stack"):
        return None, None, (f"FBSC names stack {bar['stack']}, FSEL "
                            f"{sel.get('stack')}")
    rows = (count + 2) // 3                      # fleetpop.cpp:568
    row = bar["first_visible_row"]
    if bar["total_rows"] != rows or not 0 <= row <= rows - 3:
        return None, None, (f"FBSC row {row} of {bar['total_rows']} for a "
                            f"stack of {count} ships ({rows} rows)")
    fields = {f.index: f for f in (getattr(state, "fields", None) or [])}

    def button(index, hotkey):
        f = fields.get(index)
        return index if f is not None and f.field_type == 0 and \
            f.hotkey == hotkey else None
    return row * 3, {"first_row": row, "rows": rows, "visible_rows": 3,
                     "up": button(bar["up_field"], SCROLL_UP_HOTKEY),
                     "down": button(bar["down_field"],
                                    SCROLL_DOWN_HOTKEY)}, None
