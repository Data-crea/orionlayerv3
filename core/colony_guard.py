"""The fields nothing may activate on the colony screen and its popup.

Work order 180 B, from the reading reports of work order 126
(`doc/colony_screen_reading.md` §2a): on the single-colony screen,
**CRUNCH, TOGGLE and the full-screen field [0] must never be activated —
not live, not in a test, not by any HD control.**

- CRUNCH (`_colony_fields[19]`) and TOGGLE (`[20]`) are
  `Add_Multi_Hot_Key_Field_` fields — type 8 at (-1, -1), hotkey 0 on the
  wire (fields.cpp:634-639; colony_main.cpp:988-989) — and they are
  CHEATS: CRUNCH sets `production_spent = cost` and marks the player as
  having cheated (:1167-1173).
- `[0]` is a hidden field over the whole screen, (0,0)-(639,479)
  (colony_main.cpp:1030), whose handler looks the building up by the REAL
  POINTER's polygon (colony.cpp:1950-1953) — an activation opens the
  demolish confirmation for whatever building the pointer happens to be
  over.

So ONE function says no, and every sender on screens 1 and 25 goes
through it: `tools/colony_record.py`, and `screens/colony/` and
`screens/build_queue/`'s `send`. A type-8 field is refused everywhere on
those screens; a full-screen field is refused while either screen is
reported, which also covers a text box's own full-screen field — a box
over screen 1 is answered by a key, never by a field that shares [0]'s
shape. A smoke check holds the rule and that every send path uses it.
"""

FULL_SCREEN = (0, 0, 639, 479)
#: SCREEN_COLONY and SCREEN_QUEUE_POPUP (orion2_consts.h:463, :482).
GUARDED_SCREENS = (1, 25)
#: `Add_Multi_Hot_Key_Field_`'s type (fields.cpp:634-639).
MULTI_HOT_KEY = 8


class Refused(RuntimeError):
    """A send the safety rule forbids. Nothing was sent."""


def refusal(field, screen):
    """Why `field` may not be activated on `screen`, or None."""
    if screen not in GUARDED_SCREENS:
        return None
    if getattr(field, "field_type", None) == MULTI_HOT_KEY:
        return ("a multi-hot-key field (type 8) — CRUNCH or TOGGLE, the "
                "colony screen's cheats")
    rect = (getattr(field, "x", None), getattr(field, "y", None),
            getattr(field, "x_end", None), getattr(field, "y_end", None))
    if rect == FULL_SCREEN:
        return ("the full-screen field — on screen 1 that is [0], which "
                "demolishes whatever building the real pointer is over")
    return None


def check(field, screen):
    """Raise `Refused` for a field the rule forbids; return it otherwise."""
    why = refusal(field, screen)
    if why is not None:
        raise Refused(f"refused on screen {screen}: {why} — nothing sent")
    return field
