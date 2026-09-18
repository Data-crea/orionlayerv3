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

from . import fltgeom

#: Every colour this module uses, with the same names in
#: `assets/shared/skins/default/colors.json` under `fleets`.
DEFAULTS = {
    "slot_fill": (18, 30, 38),
    "slot_edge": (58, 92, 108),
    "scroll_track": (14, 24, 31),
    "scroll_thumb": (96, 148, 172),
    "scroll_arrow": (150, 196, 214),
    "label": (198, 226, 238),
    "label_dim": (96, 118, 128),
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


def icon_slots(screen):
    """The twenty slot rects in window px, in display order, or []."""
    area = _rect(screen, "icon_area")
    column = _rect(screen, "scroll_column")
    if area is None or column is None:
        return []
    grid = fltgeom.grid_rect(tuple(area), tuple(column))
    return [pygame.Rect(int(x), int(y), int(w), int(h))
            for x, y, w, h in fltgeom.icon_cells(grid)]


def draw_slots(surface, screen):
    """The twenty sunken slots the original paints into its background."""
    edge = col("slot_edge")
    fill = col("slot_fill")
    width = max(1, int(round(screen.layout.scale)))
    for slot in icon_slots(screen):
        pygame.draw.rect(surface, fill, slot)
        pygame.draw.rect(surface, edge, slot, width)


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


def draw_labels(surface, screen, words, enabled=None):
    """The seven control words, centred in their boxes.

    `enabled` is a set of box names that are live this frame; anything
    else is drawn dim. The original dims by swapping the button's
    artwork (flt1.cpp:459-480) and by adding the field as type 7 instead
    of type 0 (:1232-1241), which is the same information.
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
    rect = _rect(screen, "status_text")
    if rect is None or not text:
        return
    _centred(surface, screen, rect, text, color or col("label"), share=0.62)
