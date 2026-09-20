"""Sending the selected ships to a star, from the Fleets map.

**THE FLOW IS THE ORIGINAL'S AND IT HAS NO BUTTON** (flt1.cpp:628-664):
select ships in the grid, then click a star in the inset. The loop
calls `MAINSCR::Scan_Galaxy_Map_Fields_(scan_val.full, input, …)`; a
match on `input` answers **result 0** with `clicked_star_id`, and with
`_relocate_button_mode != 1` and `_merging_relocations == 0` that goes
to `FLT2::Fltscrn_Move_Ships_(clicked_star_id)`. RELOCATE is the other
branch entirely.

**THE POLARITY IS THE TRAP.** In `Scan_Galaxy_Map_Fields_` the second
argument is `input` and a match there is the CLICK; the hover is the
first argument and answers result 4. That is the opposite way round
from `Scan_Fltscrn_Big_Icons_` on the same screen, where a positive
field index is the HOVER and the click is its negative
(flt2.cpp:924-934, measured live in work order 151 B). Two scanners,
one screen, opposite conventions.

So the send is `ACTIVATE_FIELD` on the star's own hidden field, which
decision 20 names for a type 7, and **decision 35 is satisfied
outright**: the field IS the game's frame, so no HD rectangle is in the
path and the API's missing INJECT_CLICK mapping (open fixes 3 and 4) is
not in the way.

**THE STAR-TO-FIELD MAPPING IS MATCHED, NOT COMPUTED.**
`Add_Galaxy_Map_Fields_2_` adds one field per star at `(sx-3, sy-3,
sx+8, sy+9)` (movebox.cpp:504-511) from `Get_Galaxy_Map_Star_XY_`, and
HD computes its own inset positions from the snapshot. Live on SAVE4
the two agreed to a CONSTANT offset on all 54 stars — same offset every
time, so the correspondence is exact — but a constant read off one save
is a number this module would then have to be trusted about. Instead
each drawn star takes the NEAREST field origin, and the assignment has
to be a clean bijection inside `TOLERANCE`; anything else refuses and
sends nothing. That is `name_holes`' rule applied to a different pair
of lists, and it survives an offset changing.
"""
import logging

from core.structs import star as star_struct

from . import fltgeom
from . import fltwire

log = logging.getLogger("fleets")

#: How far a click may be from a drawn star and still be that star.
TOLERANCE = 12

#: How far a star may be from the majority offset and still be matched.
#: The one-pixel rounding difference between HD's inset arithmetic and
#: the game's, and nothing more — the star pitch is far larger, so two
#: stars can never claim one field inside it.
SLACK = 2


def star_fields(fields):
    """Every star field in the live list (`fltwire`'s rule 3a)."""
    return [f for f in (fields or [])
            if f.field_type == fltwire.TYPE_HIDDEN
            and (f.x_end - f.x, f.y_end - f.y) == fltwire.STAR_FIELD_SIZE
            and fltwire._in_inset(f.x, f.y)]


def match(drawn, fields):
    """`{star index: field}` for a clean bijection, else `{}`.

    `drawn` is `[(x, y), …]`, one per star HD put on the map, in star
    order, **in the game's own 640x480 frame** — so the caller adds the
    inset box's origin, because `_inset_stars` answers inside the box
    and `Add_Galaxy_Map_Fields_2_` places the field on the screen.
    Comparing the two frames directly is what the first attempt did and
    the offsets came out scattered instead of constant.

    **THE OFFSET IS DERIVED, NOT TYPED.** `Add_Galaxy_Map_Fields_2_`
    puts the field at `(sx-3, sy-3)` from `Get_Galaxy_Map_Star_XY_`
    (movebox.cpp:504-511) and HD's own inset arithmetic lands in a
    frame that differs from it by a constant — measured on SAVE4 as the
    same constant on all 54 stars. Writing that constant down would
    make this module a number to be trusted about; instead the offset
    is taken from the data each time, as the one both lists agree on,
    and everything is matched through it. If the lists do not agree on
    ONE offset, or the assignment is not one-to-one, this refuses and
    the caller sends nothing — `name_holes`' rule on a different pair
    of lists.
    """
    live = star_fields(fields)
    if not drawn or len(live) != len(drawn):
        return {}
    # The offset the two lists agree on: the one most stars see to
    # their nearest field. Measured live on SAVE4 it is (-6, -6) for 46
    # of 54, with five at (-7, -6) and three at (-6, -7) — HD's inset
    # arithmetic and the game's round the same division differently by
    # a pixel. So the offset is taken from the majority and every star
    # then has to land within SLACK of it; demanding that all 54 agree
    # exactly refused a mapping that is right.
    votes = {}
    for sx, sy in drawn:
        best = min(live, key=lambda f: abs(f.x - sx) + abs(f.y - sy))
        key = (best.x - sx, best.y - sy)
        votes[key] = votes.get(key, 0) + 1
    off = max(votes.items(), key=lambda kv: kv[1])[0]
    out, taken = {}, set()
    for i, (sx, sy) in enumerate(drawn):
        want = (sx + off[0], sy + off[1])
        best, bestd = None, None
        for f in live:
            d = abs(f.x - want[0]) + abs(f.y - want[1])
            if bestd is None or d < bestd:
                best, bestd = f, d
        if best is None or bestd > SLACK or best.index in taken:
            return {}
        taken.add(best.index)
        out[i] = best
    return out


def refusal(game_state, view, star_index):
    """Why the move may not be sent, or None.

    **DECISION 33, and only where it is one comparison.** The black
    hole is: `_star[clicked].spectral_class == STAR_CLASS_BLACK_HOLE`
    (flt1.cpp:640), one test, and the original answers it with a
    `User_Box_` warning — which empties the field list, so refusing it
    here also keeps the screen out of a box it did not need to enter.
    Everything else the original checks —
    `HACCESS::Player_Can_Order_Ship_` — reads data HD does not hold,
    and is left to the game.
    """
    if view is None or not view.ok:
        return "the screen is not ready"
    if not view.selected_ships():
        return ("no ship is selected — `First_Selected_Ship_()` is -1 "
                "and the original's own click does nothing")
    if int((view.block or {}).get("relocate_mode", 0)) == 1:
        return ("RELOCATE mode is on: the same click sets a relocation "
                "target instead (flt1.cpp:637)")
    stars = getattr(game_state, "stars", None) or []
    if not 0 <= star_index < len(stars):
        return "no such star"
    if star_struct.is_black_hole(stars[star_index]):
        return "the game refuses a black hole (flt1.cpp:640-645)"
    return None


def star_at(screen, screen_x, screen_y):
    """`(the point is in the inset, the star index or None)`.

    ONE COPY, because the click and the hover ask the same question —
    work order 155. `Add_Galaxy_Map_Fields_2_` puts a hidden field on
    every star (movebox.cpp:504-511) and the original's click and its
    scan both go through that one field list; HD has no fields of its
    own here, so this is the equivalent, and having it twice is
    decision 5's failure.

    The index IS the star index: `galaxy_inset_stars` emits one entry
    per star in `game_state.stars` order and skips none.
    """
    box = None
    for b in screen.boxes:
        if b.name == "inset_map" and b.screen_rect:
            box = b.screen_rect
            break
    if box is None or not box.collidepoint(screen_x, screen_y):
        return False, None
    stars = screen._inset_stars()
    if not stars:
        return True, None
    native = fltgeom.REGIONS["inset_map"]
    px = (screen_x - box.x) / (box.width / float(native[2]))
    py = (screen_y - box.y) / (box.height / float(native[3]))
    best, bestd = None, None
    for i, (sx, sy, _c) in enumerate(stars):
        d = abs(sx - px) + abs(sy - py)
        if bestd is None or d < bestd:
            best, bestd = i, d
    if best is None or bestd > TOLERANCE:
        return True, None
    return True, best


def click(screen, screen_x, screen_y):
    """A click on a star in the inset: send the selected ships there.

    Returns True when the click BELONGED to the map, sent or not — a
    refusal is still an answer and must not fall through to whatever is
    underneath it.
    """
    in_box, best = star_at(screen, screen_x, screen_y)
    if not in_box:
        return False
    if best is None:
        return True
    stars = screen._inset_stars()
    native = fltgeom.REGIONS["inset_map"]
    why = refusal(screen._state, screen._view, best)
    if why:
        log.info("map click on star %d: not sent — %s", best, why)
        return True
    pairs = match([(native[0] + sx, native[1] + sy)
                   for sx, sy, _c in stars],
                  getattr(screen._state, "fields", None))
    field = pairs.get(best)
    if field is None:
        log.info("map click on star %d: the drawn stars and the live star "
                 "fields are not a clean one-to-one, so nothing is sent",
                 best)
        return True
    if not screen.app.connected:
        return True
    log.info("map click: star %d -> field %d, moving %d ship(s)",
             best, field.index, len(screen._view.selected_ships()))
    screen.app.client.activate_field(field.index)
    return True
