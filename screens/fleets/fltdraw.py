"""What the Fleets screen draws inside its boxes.

**HD DRAWS EVERY PIXEL OF THIS SCREEN ITSELF.** The original's whole
picture is one full-screen image, `FLEET.LBX` entry 0 (`Draw_Fleet_Screen_`,
flt1.cpp:385): the twenty sunken icon slots, the scroll column's rails,
the panel surrounds and the seven button faces are painted into it, not
drawn. That art is MOO2's and is never in this tree (CLAUDE.md), so
every one of them is drawn here, in this project's own palette, at the
places `fltgeom` seats.

That is also why the seven controls need words: `Add_Button_Field_` is
called with an empty label for all of them (flt1.cpp:1188, :1195, :1201,
:1236) because the word is in the artwork. The words are in
`layout.json`, marked OUR WORDING.

The scroll bar is ours twice over: its geometry is the original's (the
`SCROLL_PARTS` fractions) and its position is NOT — the thumb rides
`s_scroll_bar.thumb_center_y`, a pointer value the snapshot does not
carry (`SerializeState`, ext_api.cpp:92-241), so HD draws the bar from
the row it is itself showing. `layout.json` `scroll._hd_note`.
"""
import pygame

from core import palette

from screens.galaxy_map import maplines

from . import fltart
from . import fltgeom

#: Every colour this module uses, with the same names in
#: `assets/shared/skins/default/colors.json` under `fleets`.
#: THESE ARE THE ORIGINAL'S OWN COLOURS, resolved from the game's
#: palette at the indices the engine names — `colors.json`'s `_source`
#: under `fleets` carries the index and the engine line for each, and
#: that is the table. They are defaults, not constants: `col` reads
#: them through `palette.col`, so a skin and a colour-blind palette
#: still override them. What changed in work order 142 D3 is that the
#: default is no longer this project's guess at what the screen looked
#: like — the fleet screen's text is GREEN (palette 116), not the
#: blue-white that was here before, and its scroll thumb is the blue
#: gradient `Fill_FltScrn_Scroll_Bar_` writes.
#:
#: Two of the seven have NO palette index and say so in `_source`: the
#: grid plate is painted into FLEET.LBX 0 rather than filled by code,
#: so its two colours are sampled from that entry's own pixels.
DEFAULTS = {
    "slot_fill": (0, 0, 36),
    "slot_edge": (0, 0, 128),
    "scroll_track": (8, 8, 80),
    "scroll_thumb": (24, 12, 252),
    "scroll_arrow": (184, 228, 136),
    "label": (72, 144, 56),
    "label_dim": (8, 112, 8),
    "radio_on": (8, 8, 80),
    "cell_selected": (216, 232, 255),
    "cell_hover": (120, 152, 200),
}


def col(key):
    return palette.col("fleets", key, DEFAULTS[key])


def _rect(screen, name):
    """One box's window rect, or None. The boxes are the only geometry —
    decision 5, and the reason nothing here recomputes a seat."""
    for box in screen.boxes:
        if box.name == name and box.screen_rect:
            return box.screen_rect
    return None


#: The grid, as `flt1.cpp:506-507` sizes it. Kept here as the number
#: the CHECK compares the frame against, not as a layout the code
#: derives anything from — the rects come from the holes.
GRID_COLS, GRID_ROWS = 4, 5


def content_rect(screen, name):
    """A box's rect shrunk clear of the frame's chamfered corner.

    The frame draws LAST, so anything put in the corner of a hole is
    covered rather than clipped — silently, and only at the corners.
    `fltgeom.CONTENT_INSET_SRC` holds the measured chamfer per hole and
    a smoke check re-derives it from the artwork.
    """
    r = _rect(screen, name)
    if r is None:
        return None
    k = fltgeom.CONTENT_INSET_SRC.get(name)
    if not k:
        return r
    scale = screen.layout.rect((0, 0, 1920, 1080))[2] / fltgeom.FRAME_SRC_SIZE[0]
    pad = max(1, int(round(k * scale)))
    return r.inflate(-2 * pad, -2 * pad)


def icon_slots(screen):
    """The twenty slot rects in window px, in display order, or [].

    **THE CELLS ARE THE FRAME'S HOLES** (decision 3, work order 146).
    `tools/frame_holes.py --write` cuts `cell_00`..`cell_19` out of
    `assets/frame.png` and `boxes.json` carries them; this reads those
    boxes and computes nothing. Before v4 the grid was seated from the
    native geometry (`fltgeom.grid_rect` + `icon_cells`) into one
    `icon_area` hole, which was right while the frame had one opening
    and is wrong now that it has twenty.

    **DECISION 5 IS WHY THIS FUNCTION STILL EXISTS AT ALL.** Drawing
    and hit-testing both call it — `draw_cells` for the picture,
    `screen._slot_at` for the click — so there is one geometry and it
    is the artwork's. A grid widget that computed its own cell layout
    beside the holes would be the second copy that decision is about,
    and the symptom would be a cell that looks right and clicks wrong.

    Order is row-major, which is `cell_NN`'s own order and the order
    `Set_Fltscrn_Big_Icons_` fills the grid in (flt2.cpp:122, :126).
    """
    out = []
    for i in range(GRID_COLS * GRID_ROWS):
        r = _rect(screen, f"cell_{i:02d}")
        if r is None:
            return []
        out.append(pygame.Rect(r.x, r.y, r.width, r.height))
    return out


def draw_slots(surface, screen):
    """The twenty sunken slots the original paints into its background."""
    edge = col("slot_edge")
    fill = col("slot_fill")
    width = max(1, int(round(screen.layout.scale)))
    for slot in icon_slots(screen):
        # **NO EDGE UNDER v4**: the slot IS a hole and the frame paints
        # its border. Drawing one here as well gave every cell two
        # outlines, the inner one offset by the hole bleed. The FILL
        # stays — it is the backdrop the plate sits on, not a border.
        pygame.draw.rect(surface, fill, slot)
    _ = edge, width


def scroll_rects(screen):
    """`{up, track, down}` in window px, or None without the box."""
    column = _rect(screen, "scroll_column")
    if column is None:
        return None
    parts = fltgeom.scroll_parts(tuple(column))
    return {name: pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h)))
            for name, (x, y, w, h) in parts.items()}


def thumb_rect(screen, first_row, total_rows):
    """Where the thumb sits for the row HD is showing, or None.

    The original's own arithmetic, in its own terms: the track is
    `track_len_px = 234` long (flt1.cpp:35) and shows `visible_rows = 5`
    of `total_rows` (:34, :1247). A list that fits needs no thumb, and
    the original hides the two arrow FIELDS in that case as well
    (`_n_fltscrn_big_icons > 20`, flt1.cpp:1212).
    """
    rects = scroll_rects(screen)
    if rects is None:
        return None
    visible = fltgeom.SCROLL_VISIBLE_ROWS
    if total_rows <= visible:
        return None
    track = rects["track"]
    share = visible / float(total_rows)
    height = max(int(round(track.height * share)),
                 max(4, int(round(6 * screen.layout.scale))))
    span = track.height - height
    steps = total_rows - visible
    top = track.y + int(round(span * (min(first_row, steps) / float(steps))))
    return pygame.Rect(track.x, top, track.width, height)


def draw_scroll(surface, screen, first_row, total_rows):
    """Track, thumb and the two arrows."""
    rects = scroll_rects(screen)
    if rects is None:
        return
    pygame.draw.rect(surface, col("scroll_track"), rects["track"])
    thumb = thumb_rect(screen, first_row, total_rows)
    if thumb is not None:
        pygame.draw.rect(surface, col("scroll_thumb"), thumb)
    live = total_rows > fltgeom.SCROLL_VISIBLE_ROWS
    for name, up in (("up", True), ("down", False)):
        _arrow(surface, rects[name], up,
               col("scroll_arrow") if live else col("label_dim"))


def _arrow(surface, rect, up, color):
    """A filled triangle in `rect`, the way the original's LBX arrows
    point. Inset so it never touches the column's neighbours."""
    pad_x = max(1, rect.width // 5)
    pad_y = max(1, rect.height // 4)
    left, right = rect.left + pad_x, rect.right - pad_x
    top, bottom = rect.top + pad_y, rect.bottom - pad_y
    if right - left < 2 or bottom - top < 2:
        return
    mid = (left + right) // 2
    points = ([(mid, top), (right, bottom), (left, bottom)] if up
              else [(left, top), (right, top), (mid, bottom)])
    pygame.draw.polygon(surface, color, points)


#: The two filter radios and the `fleet_screen` key that holds each
#: one's state. `Add_Radio_Button_Field_` is handed a pointer to that
#: variable (flt1.cpp:1255-1256) and draws the matching frame, so the
#: wire field and the button face are the same fact.
RADIOS = {"btn_support": ("support", "support_filter"),
          "btn_combat": ("combat", "combat_filter")}


def draw_labels(surface, screen, words, enabled=None, art=None,
                filters=None):
    """The seven control words, centred in their boxes.

    `enabled` is a set of box names that are live this frame; anything
    else is drawn dim. The original dims by swapping the button's
    artwork (flt1.cpp:459-480) and by adding the field as type 7 instead
    of type 0 (:1232-1241), which is the same information.

    **THE TWO FILTER RADIOS SHOW THEIR STATE**, which this screen did
    not show at all before: `support_filter` and `combat_filter` have
    been in the FLTS block since open fix 27 and no reader existed, so
    a player could not tell from the HD screen whether a filter was on.
    With the artwork it is the original's own two-frame face
    (`fltart.radio`); without it, a filled backing in the screen's blue
    — which is what the original's lit frame is — and the word on top.
    """
    for name, key in (("btn_all", "all"), ("btn_relocate", "relocate"),
                      ("btn_scrap", "scrap"), ("btn_leaders", "leaders"),
                      ("btn_support", "support"), ("btn_combat", "combat"),
                      ("btn_return", "return")):
        rect = _rect(screen, name)
        text = words.get(key)
        if rect is None or not text:
            continue
        live = enabled is None or name in enabled
        on = bool((filters or {}).get(name))
        if on:
            # **THE ORIGINAL'S RADIO FACE IS NOT DRAWN ANY MORE**, and
            # this is the fix for the doubled label work order 146 part
            # 3 asked about. FLEET.LBX 9 and 10 are whole BUTTONS: a
            # border, a lit blue field and the words "Support" and
            # "Combat" baked into the pixels. Blitting one and then
            # drawing HD's own label on top printed the word twice,
            # offset, and the v4 hole is narrower than the art so the
            # baked word overflowed the blue field as well.
            #
            # Under v4 the FRAME is the border, so a whole button blitted
            # inside a hole is the wrong shape twice over. The state is
            # the lit field, which is what the face's frame 1 is for;
            # the word stays HD's, in HD's font, at HD's size.
            fill = content_rect(screen, name) or rect
            surface.fill(col("radio_on"), fill)
        _centred(surface, screen, rect, text,
                 col("label") if live else col("label_dim"))


def _centred(surface, screen, rect, text, color, share=0.52):
    """One line, centred, shrunk until it fits the box's width."""
    size = max(8, int(rect.height * share))
    while size > 8:
        surf = screen.style.render_text(text, size, color)
        if surf.get_width() <= rect.width - 2:
            break
        size -= 1
    else:
        surf = screen.style.render_text(text, size, color)
    surface.blit(surf, surf.get_rect(center=rect.center))


def draw_status(surface, screen, text, color=None):
    """The one line under the inset map (FLT2::Print_Fltscrn_Scanned_Star_Name_,
    flt2.cpp:338-522). Empty when nothing is scanned, which is the
    original's state too: it prints only on hover (flt1.cpp:397-399)."""
    # v4: the status line IS the arrow bar's middle hole (help 363,
    # evanhelp.cpp:154-157) — `status_text` was a box inside the old
    # one-opening frame and has no hole of its own any more.
    rect = content_rect(screen, "status_band")
    if rect is None or not text:
        return
    _centred(surface, screen, rect, text, color or col("label"), share=0.62)


# ── The grid's content ────────────────────────────────────

def owner_colour(index):
    """One player's colour, from the galaxy map's own eight — the one
    home for them (`colors.json` `galaxy_map.owner_0..7`), so this
    screen cannot drift from the map the player just came from."""
    if index is None or not (0 <= int(index) < 8):
        return col("label_dim")
    return palette.col("galaxy_map", f"owner_{int(index)}", DEFAULTS["label"])


def cell_seat(rect):
    """The native-sized area inside an HD slot, and its step.

    **DECISION 54: SHRINK THE SLOT, NOT THE CHECKED THING.** The
    original's cell is `0x39` square (flt1.cpp:81) and HD's slot is
    whatever the seat makes it — at 1080p 128x126, which is neither
    two nor three times 57. Stretching the original's plate to fill
    that would resample the game's own pixels at a fractional factor;
    seating an INTEGER multiple of the native cell inside the slot and
    centring it keeps every original pixel square. The leftover margin
    keeps HD's own slot fill, which is what it drew there before.
    """
    step = max(1, min(rect.width // fltart.NATIVE_CELL,
                      rect.height // fltart.NATIVE_CELL))
    side = fltart.NATIVE_CELL * step
    return pygame.Rect(rect.x + (rect.width - side) // 2,
                       rect.y + (rect.height - side) // 2,
                       side, side), step


def cell_art(art, cell, rect):
    """What to blit in one cell, back to front, or `[]`.

    **TRANSCRIPTION with one marked deviation.** The plate, the picture,
    the colours and the placement are the original's — `fltart` cuts
    the plate out of FLEET.LBX 0 and resolves the sprite set and the
    ramp, and `cell_offset` is the centring at flt1.cpp:81-86. The
    deviation is the MAGNIFICATION: SHIPS.LBX holds exactly one size of
    each ship, so there is no sprite to swap to and decision 28's rule
    cannot be followed as written. The factor is an integer one
    (`fltart.magnified`), and a slot smaller than native draws at 1:1
    rather than shrinking, because a shrink would drop original pixels.
    """
    if art is None or not art.available:
        return []
    seat, step = cell_seat(rect)
    out = []
    native = fltgeom.native_cells()
    if 0 <= cell.slot < len(native):
        plate = art.plate(*native[cell.slot])
        if plate is not None:
            # THE WELL IS OFFSET FROM THE ICON ORIGIN (fltart.WELL_OFFSET,
            # work order 152 item 4), so the blit carries the same offset
            # the cut did. The ship's own `cell_offset` is unchanged and
            # still measured from the SEAT, which is what keeps the ship
            # where the original puts it while the plate moves under it.
            ox, oy = fltart.WELL_OFFSET
            out.append((fltart.magnified(plate, step),
                        (seat.x + ox * step, seat.y + oy * step)))
    if cell.picture is not None:
        sprite = art.ship(int(cell.picture), cell.sprite_set,
                          owner=cell.ramp)
        if sprite is not None:
            off_x, off_y = fltart.cell_offset(sprite.get_width(),
                                              sprite.get_height())
            out.append((fltart.magnified(sprite, step),
                        (seat.x + off_x * step, seat.y + off_y * step)))
    return out


#: How far the cell hole's chamfer cuts each corner, in SOURCE pixels —
#: the same number the content inset uses, because it is the same
#: chamfer (`fltgeom.CONTENT_INSET_SRC["cell_00"]`). Read from there so
#: a new frame moves both together.
def _chamfer_px(screen):
    src = fltgeom.CONTENT_INSET_SRC.get("cell_00", 0)
    scale = (screen.layout.rect((0, 0, 1920, 1080))[2]
             / fltgeom.FRAME_SRC_SIZE[0])
    return max(1, int(round(src * scale)))


def draw_cell_mark(surface, screen, rect, colour, width):
    """One mark on a cell's edge, following the hole's own shape.

    **THE ORIGINAL USES TWO SPRITES AND SO DOES THIS** (work order 152,
    item 5). `_selected_box_seg` is FLEET.LBX 17, 59 x 58, drawn at
    `(x - 2, y + 1)` for a SELECTED ship (flt1.cpp:93-103);
    `Draw_Box_Around_Scanned_Ship_` draws `scanned_box`, 62 x 61, for the
    HOVERED one (:89-91). Both are the original's artwork and neither is
    in this tree, so HD draws a LINE on the same edge — and, like the
    original, a different one for each state.

    The edge is the HOLE's edge, chamfered: the cell is a cutout in the
    frame with its corners cut, so a plain rectangle would cross the
    metal at all four of them. The eight points below are that chamfer,
    taken from the one place it is measured.
    """
    # **INSIDE THE HOLE, NOT ON THE BOX'S EDGE.** A cutout box is the
    # hole grown by `BLEED` reference px on every side (frame_holes.to_ref)
    # and the frame image draws LAST, so a stroke on the box's own edge is
    # painted and then covered — which is why the old 3 px line showed as a
    # 1 px hairline and why the first version of this showed as nothing at
    # all. The mark is inset by the bleed and by its own width.
    bleed = int(round(fltgeom.BLEED * screen.layout.scale))
    rect = rect.inflate(-2 * (bleed + width), -2 * (bleed + width))
    k = _chamfer_px(screen)
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    if w <= 2 * k or h <= 2 * k:
        pygame.draw.rect(surface, colour, rect, width)
        return
    points = [(x + k, y), (x + w - 1 - k, y),
              (x + w - 1, y + k), (x + w - 1, y + h - 1 - k),
              (x + w - 1 - k, y + h - 1), (x + k, y + h - 1),
              (x, y + h - 1 - k), (x, y + k)]
    pygame.draw.lines(surface, colour, True, points, width)


def _mark_cell(surface, screen, cell, rect, hover):
    """The selected mark, the scanned mark, or neither — in that order.

    SELECTED WINS when a cell is both, because selection is a state the
    player set and the scan is where the pointer last was. The
    original draws both sprites and lets the later one sit on top
    (`Draw_Box_Around_Scanned_Ship_` at flt1.cpp:89-91, then
    `_selected_box_seg` at :93-104, so selection is on top there too);
    HD draws a line and two lines on one edge would read as one thick
    line of neither colour, so it picks.
    """
    width = max(2, int(round(3 * screen.layout.scale)))
    if cell.selected:
        draw_cell_mark(surface, screen, rect, col("cell_selected"), width)
    elif hover is not None and cell.slot == hover:
        draw_cell_mark(surface, screen, rect, col("cell_hover"),
                       max(2, width - 1))


def draw_cells(surface, screen, cells, art=None):
    """The ship's picture, its name and the selection frame, per cell.

    WITH the extracted artwork this is the original's own picture, in
    the original's own colours. WITHOUT it — the normal state of a
    fresh clone, since the files are never committed — the cell falls
    back to the block of the builder's colour that it drew before, and
    `screen.py` puts the "how to extract" line on screen. Both states
    are drawn from this one function, so neither can rot unnoticed.

    The frame is the original's own idea: `_selected_box_seg` is
    FLEET.LBX 17 drawn round a selected icon (flt1.cpp:93-104). Ours is
    a line, not that art.
    """
    slots = icon_slots(screen)
    if not slots:
        return
    # THE MARK AND THE PANEL ARE ONE VALUE, because the original has
    # one: `Draw_Box_Around_Scanned_Ship_` is drawn for
    # `_scanned_big_ship` (flt1.cpp:89-91) and the panel is printed for
    # the same index (:401-406). `screen._scan` is HD's copy of it —
    # HD's own pointer first, since the Extension API has no
    # MOUSEMOTION (open fixes 3 and 4) and the game's value never moves
    # for a client. It answers None when the scanned ship has scrolled
    # out of the five rows, which is also what the original does: the
    # box is drawn inside the loop over the VISIBLE icons.
    _scan = getattr(screen, "_scan", None)
    _block = getattr(getattr(screen, "_view", None), "block", None)
    hover = _scan.slot(_block) if (_scan is not None and _block) else None
    for cell in cells:
        if not (0 <= cell.slot < len(slots)):
            continue
        rect = slots[cell.slot]
        drawn = cell_art(art, cell, rect)
        if drawn:
            for picture, at in drawn:
                surface.blit(picture, at)
            if cell.name:
                band = max(10, rect.height // 4)
                _centred(surface, screen,
                         pygame.Rect(rect.x, rect.bottom - band,
                                     rect.width, band),
                         cell.name, col("label"), share=0.8)
            _mark_cell(surface, screen, cell, rect, hover)
            continue
        # The cell is split the way the original splits it: the picture
        # area above, the ship's name in a band along the bottom
        # (flt2.cpp:581 prints the name under the icon). The picture is
        # a plain block of the BUILDER's colour here — there is no
        # picture to draw, and a block that ran under the name would
        # make a silver hull's name unreadable, which is what the first
        # render showed.
        band = max(10, rect.height // 4)
        patch = pygame.Rect(rect.x, rect.y, rect.width, rect.height - band)
        pygame.draw.rect(surface, owner_colour(cell.builder),
                         patch.inflate(-patch.width // 3,
                                       -patch.height // 3))
        if cell.name:
            _centred(surface, screen,
                     pygame.Rect(rect.x, rect.bottom - band,
                                 rect.width, band),
                     cell.name, col("label"), share=0.8)
        _mark_cell(surface, screen, cell, rect, hover)


#: `graphics::Fill_(..., 0)` (movebox.cpp:38) — palette index 0, which
#: is `(0, 0, 0)` in FONTS.LBX entry 9, read rather than assumed. The
#: fill runs because this screen clears `_using_colony_screen_palette`
#: (flt1.cpp:522) and is not SCREEN_RACE (movebox.cpp:37).
INSET_BACKGROUND = (0, 0, 0)


def fill_inset(surface, screen):
    """The inset's black, BEFORE the boxes draw.

    Separate from `draw_inset` for an ordering reason, not a tidiness
    one: the hint strip is a `text` box and the boxes render before the
    screen's own drawing, so a fill inside `draw_inset` painted over
    the words that had already been drawn — which is exactly how it
    looked the first time, an empty black panel with no hint at all.
    """
    rect = _rect(screen, "inset_map")
    if rect is not None:
        surface.fill(INSET_BACKGROUND, rect)


def draw_inset(surface, screen, stars, markers, art=None):
    """The galaxy inset: the stars on black, one marker per stack.

    `stars` is `colonyrows.galaxy_inset_stars` for THIS screen's native
    box, `markers` is `(native_x, native_y, owner)` per live ship icon.
    Both are in the original's native pixels inside the box, so the only
    thing done here is the scale into the `inset_map` rect.

    **THE BACKGROUND IS BLACK BECAUSE THE ORIGINAL FILLS IT BLACK**, not
    because black suits it — `INSET_BACKGROUND` cites the fill.

    WITH the extracted artwork each star is the original's own 5x5
    sprite, FLEET.LBX `34 + colour_index` (`Load_Galaxy_Stars_`,
    flt1.cpp:1441-1444), drawn at frame 0 — `Reset_Animation_Frame_`
    immediately before `Draw_` (movebox.cpp:84-85) — and offset by
    `-2, -2` from the star's position (movebox.cpp:85), which is what
    centres a 5 px sprite on its star. WITHOUT it, the flat dot this
    screen drew before.
    """
    rect = _rect(screen, "inset_map")
    if rect is None:
        return
    from . import fltgeom
    _nx, _ny, nw, nh = fltgeom.REGIONS["inset_map"]
    fx, fy = rect.width / float(nw), rect.height / float(nh)
    dot = max(2, int(round(2 * screen.layout.scale)))
    have_art = art is not None and art.available
    step = max(1, int(round(min(fx, fy)))) if have_art else 1
    # CLIPPED TO THE BOX, as the original is: `Set_Window_` then
    # `Clip_On_` around exactly this loop (movebox.cpp:57-59), with
    # `Clip_Off_` after it. Without this a star or a stack marker whose
    # coordinates fall outside the map is drawn across the rest of the
    # screen — which is what a marker did, out beside the buttons.
    previous = surface.get_clip()
    surface.set_clip(rect)
    for sx, sy, colour_index in stars:
        x = rect.x + sx * fx
        y = rect.y + sy * fy
        sprite = art.star(colour_index) if have_art else None
        if sprite is not None:
            sprite = fltart.magnified(sprite, step)
            surface.blit(sprite, (int(x) - 2 * step, int(y) - 2 * step))
            continue
        pygame.draw.rect(surface, _star_colour(colour_index),
                         (int(x), int(y), dot, dot))
    for mx, my, owner in markers:
        x = rect.x + mx * fx
        y = rect.y + my * fy
        pygame.draw.rect(surface, owner_colour(owner),
                         (int(x), int(y), dot * 2, dot * 2))
    surface.set_clip(previous)


#: The relocation line's eight-step ramp, palette 6,7,7,8,8,9,9,10
#: (flt1.cpp:1460-1467). In the skin (decision 14), with its source.
RELOCATION_RAMP = tuple(tuple(c) for c in palette.require(
    "fleets", "relocation_line"))

#: `Draw_Ship_Destination_Line_` nudges the STAR end by +4
#: (ships.cpp:552-553, the non-main-screen branch) and
#: `Draw_Fltscrn_Relocation_Lines_` passes the TARGET end already
#: nudged by +3 (flt1.cpp:1486). Native px, inside the inset box.
RELOCATION_FROM_NUDGE = 4
RELOCATION_TO_NUDGE = 3


def draw_relocation_lines(surface, screen, state, stars, ms):
    """The relocation lines on the inset, under nothing and over black.

    **TRANSCRIPTION.** `FLT1::Draw_Fltscrn_Relocation_Lines_`
    (flt1.cpp:1451-1490) walks every star, and for each one the local
    player has relocated draws a line from that star to its target. It
    is NOT gated by `_settings.show_relocation_lines` — that gate is
    the galaxy map's (mainscr.cpp:690) and this screen does not consult
    it, so neither does this.

    The line goes through `maplines`: `relocation_pairs` for the fact,
    `directional` + `phase_at` + `wave_pieces` for the wave, `clip` for
    the box the original clips to (movebox.cpp:57-59 for the stars,
    and this loop draws inside the same window), and `stroke` for every
    piece — decision 68, one routine for every line on an HD map.

    `stars` is `colonyrows.galaxy_inset_stars`' output for THIS box, in
    star order, so a line's ends are the very positions the dots were
    drawn at: no second transform, and nothing here converts galaxy
    coordinates itself.
    """
    rect = _rect(screen, "inset_map")
    if rect is None or not stars:
        return
    pairs = maplines.relocation_pairs(state, getattr(state, "player_num", 0))
    if not pairs:
        return
    from . import fltgeom
    _nx, _ny, nw, nh = fltgeom.REGIONS["inset_map"]
    fx, fy = rect.width / float(nw), rect.height / float(nh)
    phase = maplines.phase_at(ms)
    step = max(1.0, min(fx, fy))
    previous = surface.get_clip()
    surface.set_clip(rect)
    for star_idx, target_idx in pairs:
        if not (0 <= star_idx < len(stars) and 0 <= target_idx < len(stars)):
            continue
        sx, sy, _c = stars[star_idx]
        tx, ty, _c2 = stars[target_idx]
        a = (rect.x + (sx + RELOCATION_FROM_NUDGE) * fx,
             rect.y + (sy + RELOCATION_FROM_NUDGE) * fy)
        b = (rect.x + (tx + RELOCATION_TO_NUDGE) * fx,
             rect.y + (ty + RELOCATION_TO_NUDGE) * fy)
        table, offset = maplines.directional(a[0], a[1], b[0], b[1],
                                             RELOCATION_RAMP, phase)
        seg = maplines.clip(a, b, (rect.x, rect.y, rect.width, rect.height))
        if seg is None:
            continue
        for colour, p, q in maplines.wave_pieces(seg[0], seg[1], table,
                                                 offset, step):
            maplines.stroke(surface, colour, p, q)
    surface.set_clip(previous)


def _star_colour(index):
    """`movebox.cpp:67-79`'s colour index, in HD's palette.

    8 is "unowned, seen"; on THIS screen the black hole is 10, and 9 is
    the colony screen's answer for the same star
    (`_using_colony_screen_palette ? 9 : 10`, movebox.cpp:70; this
    screen clears the flag at flt1.cpp:522). Both are accepted here
    because this fallback draws a flat dot either way.

    **NOT A DEFECT, AND THIS DOCSTRING SAID IT WAS.** It recorded 10 as
    an out-of-bounds read past a ten-entry array. `_fleet_galaxy_star_seg`
    is declared `[11]` (mox.h:110) and `Load_Galaxy_Stars_` fills all
    eleven from FLEET.LBX 34..44 (flt1.cpp:1441-1444), so 10 is a real
    sprite — the black hole the fleet screen is meant to draw. The ten
    entries belong to the COLONY screen's array, which never asks for
    10. Correcting it mattered the moment the sprites became the
    original's: 9 and 10 are different pictures.
    """
    if index in (9, 10):
        return col("scroll_track")
    if index == 8:
        return col("label_dim")
    return owner_colour(index)
