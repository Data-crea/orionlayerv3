"""The Space Dragon's bribe's TPOP tail — open fix 108 (work order 319).

The wire half of the bribe popup HD draws over the map
(`core/turnpopupcontent.py`, `screens/galaxy_map/dragonpopup.py`): kind 24
of open fix 49's "TPOP" block, reported as id 84 while
`MAINPUPS::Dragon_New_Star_Popup` runs (mainpups.cpp:493-542, opened by
COMBFIND when the Space Dragon reaches a human player's colony,
combfind.cpp:157; the network's :482). The engine's lines here are the
branch `orionlayer`'s just before open fix 108 (`39c5cc6d^`, i.e.
`21bdc2b8`, the earlier fixes included — not plain v2.0.0's); open fix 108
itself moves them. The layout is
`doc/ext_dragon_bribe.patch`'s header, byte by byte:

    args  [0] the dragon's star, [1] the player, [2] the bribe
          (`COMBFIND::dragon_bribe_bc`, combfind_config.cpp:7, capped at
          32767), [3] field_mode (0 the offer, 1 paid: choose a star, 2 too
          poor — set again after every input), [4] mp_fields[2] refuse /
          close (hotkey ESC), [5] mp_fields[25] YES (hotkey E 561 "y")
    text  the message as `Draw_Dragon_New_Star_Popup_` last formatted it
          (E 555 the offer, E 464 choose a star, E 583 too poor, :2594-2599)
    tail  int16 field_mode as it is now, int16 n, n x (int16 star field,
          int16 star) — kind 4's (field, index) pairs: the hidden fields
          `MOVEBOX::Add_Galaxy_Map_Fields_2_` adds for each star of the
          popup's own galaxy map (movebox.cpp:438-521, style 0: a 5 x 5
          field at the star's place in the map at (302, 156) 148 x 94,
          mainpups.cpp:2155-2167); n is the star count in mode 1, else 0

`Update_Dragon_New_Star_Fields_` runs ONCE, before the loop (:522), so the
fields of mode 0 — YES included — stay in the list in modes 1 and 2.
"""
import struct as _st

#: field_mode's three values (`Evaluate_Dragon_New_Star_Input_`,
#: mainpups.cpp:2611-2657).
OFFER, CHOOSE, TOO_POOR = 0, 1, 2
#: The popup's galaxy map (`Add_Galaxy_Map_Fields_2_(302, 156, 148, 94, …)`,
#: mainpups.cpp:2155-2167) and its star fields: `Add_Hidden_Field_` (type 7,
#: FIELD_TYPE_HIDDEN, orion2_consts.h:244) from (x, y) to (x + 5, y + 5),
#: x and y the star's place less 2 (`Get_Galaxy_Map_Star_XY_`, style 0,
#: movebox.cpp:362-374).
MINI_MAP = (302, 156, 148, 94)
#: The most stars a v2 galaxy can have: MAX_STARS 1024 (consts.h:8; the
#: config allows 1023, specs/config/main.json5:5843), the same 1024 the
#: star record's BITMAP assumes (`core/structs/star.py`). The tail carries
#: one pair per star in mode 1, so a bound below it would lose the popup.
MAX_STARS = 1024
STAR_FIELD_TYPE, STAR_FIELD_SIZE, STAR_CENTRE_OFFSET = 7, 5, 2


def read_tail(take):
    """The tail as a dict: `{"mode", "stars": [{"field", "star"}]}`."""
    mode, n = take("hh")
    if not 0 <= n <= MAX_STARS:
        raise ValueError("star count")
    stars = [take("hh") for _ in range(n)]
    return {"mode": mode,
            "stars": [{"field": f, "star": s} for f, s in stars]}


def build_tail(dragon=None):
    """The tail as the engine writes it — for the checks' stand-ins."""
    dragon = dragon or {}
    stars = dragon.get("stars") or []
    out = _st.pack("<hh", dragon.get("mode", OFFER), len(stars))
    for s in stars:
        out += _st.pack("<hh", s["field"], s["star"])
    return out


def mode(popup):
    """The mode the popup is in: the tail's, which the engine reads live,
    else args[3]."""
    tail = popup.get("dragon")
    return tail["mode"] if tail is not None else popup["args"][3]


def _is_star_field(f):
    """A field of the shape `Add_Galaxy_Map_Fields_2_` gives a star of the
    popup's map: hidden, 5 x 5, inside the map less the centre offset."""
    x, y, w, h = MINI_MAP
    lo = -STAR_CENTRE_OFFSET
    return (getattr(f, "field_type", None) == STAR_FIELD_TYPE and
            f.x_end - f.x == STAR_FIELD_SIZE and
            f.y_end - f.y == STAR_FIELD_SIZE and
            x + lo <= f.x <= x + w + lo and y + lo <= f.y <= y + h + lo)


def star_field(popup, state, star):
    """The live field a click on `star` activates, or None (P816: the
    tail names the field, the list just read must have it, by its index,
    its type and its rectangle; anything else sends nothing)."""
    if mode(popup) != CHOOSE:
        return None
    tail = popup.get("dragon") or {}
    fid = next((s["field"] for s in tail.get("stars") or ()
                if s["star"] == star), None)
    if fid is None or fid <= 0:
        return None
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == fid and _is_star_field(f)),
                None)
