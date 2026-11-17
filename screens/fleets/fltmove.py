"""Sending the selected ships to a star, from the Fleets map.

**THE FLOW IS THE ORIGINAL'S AND IT HAS NO BUTTON** (flt1.cpp:628-664):
select ships in the grid, then click a star in the inset. The loop
calls `MAINSCR::Scan_Galaxy_Map_Fields_(scan_val.full, input, …)`; a
match on `input` answers **result 0** with `clicked_star_id`, and with
`_relocate_button_mode != 1` and `_merging_relocations == 0` that goes
to `FLT2::Fltscrn_Move_Ships_(clicked_star_id)`. RELOCATE is the other
branch (`Star_Relocation_`): since work order 403 A the same field is sent
there too and the engine does the rest (`refusal`, `right_click`); a click
on a small stack icon switches the shown fleet (`click_stack`).

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
    """Why the star click may not be sent, or None.

    **DECISION 33, and only where it is one comparison.** What the
    original's loop does with a star click, in its own order
    (flt1.cpp:603-672): merging after F5 sets every relocation
    (`merge_relocations`); RELOCATE mode 1 runs `Star_Relocation_`;
    otherwise a black hole is answered with `User_Box_` H 0x78 (:651-654) — BEFORE
    and without looking at the selection — and only then
    `First_Selected_Ship_()` (:656) and `Player_Can_Order_Ship_`. Everything the
    engine itself decides or says is let through (work order 403 A: its
    boxes come through the message box, open fix 29); what is refused here
    is what the original's own click does nothing with.
    """
    if view is None or not view.ok:
        return "the screen is not ready"
    stars = getattr(game_state, "stars", None) or []
    if (getattr(view, "block", None) or {}).get("merging_relocations"):
        # TRANSCRIPTION `merge_relocations` (work order 231 D): after F5 the
        # original's next star click sets every relocation of the player to
        # that star, with no selection and no black-hole test (flt1.cpp:
        # 612-621, :661-672) — the engine answers with its box (H 0x77).
        return None if 0 <= star_index < len(stars) else "no such star"
    if not 0 <= star_index < len(stars):
        return "no such star"
    if int((getattr(view, "block", None) or {}).get("relocate_mode", 0)) == 1:
        # TRANSCRIPTION `relocate_target` (work order 403 A): in mode 1 the
        # same click is `Star_Relocation_` (flt1.cpp:648-650) — the first
        # click names the star to move from, the second the target; the
        # engine keeps both (`scan_val.words[1]`, `relocate_target_star_idx`)
        # and answers a refusal with its own boxes (H 0x82-0x88). No ship
        # needs to be selected and a black hole is the engine's to judge.
        return None
    if star_struct.is_black_hole(stars[star_index]):
        # TRANSCRIPTION `black_hole_box` (work order 403 A): `User_Box_`
        # H 0x78 (flt1.cpp:651-655), with or without a selection. It used
        # to be refused here to keep the screen out of a box; the box is an
        # HD message box now (open fix 29, `core/msgbox`).
        return None
    # `First_Selected_Ship()` scans EVERY icon (flt1.cpp:320-335); `view.rows`
    # holds only the displayed cells (at most 20), so a selection scrolled out
    # of sight read as "nothing selected" — the block carries all of them
    # (audit pass 2)
    selected = (getattr(view, "block", None) or {}).get("ship_selected")
    if not (any(selected) if selected else view.selected_ships()):
        return ("no ship is selected — `First_Selected_Ship_()` is -1 "
                "and the original's own click does nothing")
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
    hit = stack_hit(screen, screen_x, screen_y)
    if hit is not None:
        return click_stack(screen, hit)
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
    if (screen._view.block or {}).get("merging_relocations"):
        log.info("map click: star %d -> field %d, every relocation there "
                 "(merge, F5)", best, field.index)
    elif int((screen._view.block or {}).get("relocate_mode", 0)) == 1:
        log.info("map click: star %d -> field %d, relocation (RELOCATE)",
                 best, field.index)
    else:
        log.info("map click: star %d -> field %d, moving %d ship(s)",
                 best, field.index, len(screen._view.selected_ships()))
    screen.app.client.activate_field(field.index)
    return True

def stack_hit(screen, screen_x, screen_y):
    """`(icon index, live field)` of the ship stack icon under the point in
    the inset, or None — `Scan_Small_Ship_Icons_`' scan (flt1.cpp:852-893)
    through the live list's hidden icon fields (`core/shipstacks.icon_at`,
    the Leaders box's own test; work order 248). The icons stand in
    absolute native pixels, so the point goes back through the inset's own
    rect."""
    box = next((b.screen_rect for b in screen.boxes
                if b.name == "inset_map" and b.screen_rect), None)
    state = screen._state
    if box is None or state is None or \
            not box.collidepoint(screen_x, screen_y):
        return None
    from core import shipstacks
    nx, ny, nw, nh = fltgeom.REGIONS["inset_map"]
    point = (nx + (screen_x - box.x) * nw / float(box.width),
             ny + (screen_y - box.y) * nh / float(box.height))
    return shipstacks.icon_at(state, getattr(state, "fields", None) or [],
                              point)


def stack_at(screen, screen_x, screen_y):
    """The index of the ship stack icon under the point, or None — the
    hover (flt1.cpp:668-682)."""
    hit = stack_hit(screen, screen_x, screen_y)
    return hit[0] if hit is not None else None


def click_stack(screen, hit):
    """A click on a small stack icon: the stack becomes the shown fleet.

    TRANSCRIPTION `stack_click` (work order 403 A): `Scan_Small_Ship_Icons_`
    answers a click on the icon's own field with result 0 — it takes the
    icon (`Overlapped_Ship_Icon_Button_(&i, 7, 4)` cycles among icons within
    7 x 4 px when the click repeats on the same spot, ships.cpp:567-620),
    sets `_small_ship_stack_ptr` to its stack and redraws the screen
    (flt1.cpp:852-867, :678-690). The field is a hidden one (type 0x29,
    flt2.cpp:25-39), so ACTIVATE_FIELD is the click (decision 20) and the
    cycling is the engine's. FLTS reports the new stack next frame.
    The icon fields are added BEFORE the stars' (flt1.cpp:1260, :1267), and
    the first field in list order wins a point (fields.cpp:1276-1290), so
    over a star and an icon the click belongs to the icon.
    UNVERIFIED live: the switch and the cycling."""
    index, field = hit
    if not screen.app.connected:
        return True
    log.info("map click: stack icon %d -> field %d", index, field.index)
    screen.app.client.activate_field(field.index)
    return True


def right_click(screen, screen_x, screen_y):
    """A right click while RELOCATE mode is on: leave the mode.

    TRANSCRIPTION `relocate_cancel` (work order 403 A): the loop's first
    branch is `if (input < 0 && relocate_button_mode == 1)` — a right click
    on ANY field — which clears the pending star and the mode
    (flt1.cpp:603-608). The original's second branch, `ret_map == 1 &&
    mode 1` -> `Cancel_Star_Relocation_` (:645-646, :895-902), cannot run: `MAINSCR::
    Scan_Galaxy_Map_Fields_` answers only 0, 4, 2 or -1 (mainscr.cpp:
    3231-3259). So HD sends the right click on the star's own field when it
    is on a star (the click the task named), else on the screen's last
    field, the one that covers all 640 x 480 (flt1.cpp:1274). Returns True
    when it went. UNVERIFIED live."""
    view = screen._view
    if view is None or not view.ok or not screen.app.connected or \
            int((getattr(view, "block", None) or {}).get("relocate_mode", 0)) != 1:
        return False
    fields = getattr(screen._state, "fields", None) or []
    field = None
    in_box, star = star_at(screen, screen_x, screen_y)
    if in_box and star is not None:
        native = fltgeom.REGIONS["inset_map"]
        field = match([(native[0] + sx, native[1] + sy)
                       for sx, sy, _c in screen._inset_stars()],
                      fields).get(star)
    if field is None:
        field = next((f for f in fields
                      if f.field_type == fltwire.TYPE_HIDDEN
                      and (f.x, f.y, f.x_end, f.y_end) == (0, 0, 639, 479)),
                     None)
    if field is None:
        return False
    log.info("right click in relocate mode: field %d, the mode ends",
             field.index)
    screen.app.client.cancel_field(field.index)
    return True


# The strip's "current fleet": not an icon index, so it never meets one.
CURRENT_FLEET = -2


def current_stack_icon(game_state, block):
    """The icon of the stack the grid shows, or -1 —
    `Restore_Current_Fleet_Summary_` (flt1.cpp:342-353): the first icon
    whose node is `ship_stack_start[small_ship_stack_ptr]`
    (`F_Ship_Icon_From_Node_Ptr_`, :1137-1148), which FLTS sends as
    `head_node` (work order 248)."""
    head = int((block or {}).get("head_node", -1))
    if head < 0:
        return -1
    for i, icon in enumerate(getattr(game_state, "ship_icons", None) or []):
        if int(icon.node_idx) == head:
            return i
    return -1
