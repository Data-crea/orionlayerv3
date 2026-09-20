"""A native message box HD cannot render, shown by blitting the game's own.

**AN HD LIMITATION, DELIBERATELY DRAWN AS ONE.** When the engine opens
one of its own boxes, `FIELDSAV::Save_Field_Stats_` re-bases the field
array past the screen's fields and calls `fields::Clear_Fields_` on the
new base (fieldsav.cpp), so the wire carries the BOX's fields and not
one of the screen's. An HD screen therefore cannot go on drawing as if
it could be clicked — and, more to the point, it cannot rebuild the
box's TEXT: the string is `HAROLD::H_Message_(n)` formatted with values
the engine computed, and it reaches a client only as PIXELS in the
framebuffer.

So this shows the pixels. The box's rectangle is transcribed from the
call that draws it; the crop is taken out of the framebuffer HD already
subscribes to and blitted into an HD panel; and the buttons are
answered with `ACTIVATE_FIELD` on the box's own fields, which is the
same `fields::Get_Input_` loop the box is sitting in (fields.cpp:166-182).

**WHAT IS AND IS NOT TRANSCRIPTION.** The rectangles below are: the
origin is the literal in the `animate::Remap_Draw_` call and the size is
the LBX entry's own header, two independent sources that agree (work
order 152). The PANEL around the crop is HD's, and the crop is the
game's own 640x480 pixels shown at whatever the panel scales them to —
which is the limitation, and it is marked in `v3_projektstatus.md` and
held by a smoke check. The replacement is open fix 29: the scrap value
as an int16 in the FLTS block, after which the confirmation can be
drawn in HD's own font.

**CHAINS ARE THE NORMAL CASE, not an edge.** `Scrap_Ships_` answers a
NO with a second box (`User_Box_(…, 3)`, flt1.cpp:1524-1527), so
dismissing one box routinely reveals another. Nothing here assumes a
box is the last one: the detector runs on every snapshot.
"""
import pygame

#: 640x480, the frame every rectangle here is in (decision 35).
NATIVE_W, NATIVE_H = 640, 480


class BoxKind:
    """One native box: how to recognise it, where it is, how to answer."""

    __slots__ = ("name", "rect", "fields", "answers", "source")

    def __init__(self, name, rect, fields, answers, source):
        self.name = name
        self.rect = rect            # (x, y, w, h) in native px
        self.fields = frozenset(fields)   # (rect, hotkey, type) each
        self.answers = answers      # ((label_key, hotkey), …) in draw order
        self.source = source


#: `GENDRAW::Confirmation_Box_` (gendraw.cpp). The art is CONFIRM.LBX
#: entry 0, 313x227, drawn by `animate::Remap_Draw_(0xa1, 0x75, …)` =
#: (161, 117). Its two buttons are
#: `Add_Hidden_Field_(0xeb, 0x12e, 0x11e, 0x143, "Y", …)` and
#: `(0x159, 0x12e, 0x18c, 0x143, "N", …)` — measured live on 20
#: September 2026 as exactly those two fields and nothing else.
CONFIRMATION = BoxKind(
    "confirmation", (161, 117, 313, 227),
    (((235, 302, 286, 323), ord("Y"), 7),
     ((345, 302, 396, 323), ord("N"), 7)),
    (("yes", ord("Y")), ("no", ord("N"))),
    "GENDRAW::Confirmation_Box_, CONFIRM.LBX 0")

#: `GENDRAW::Message_Box_Exploding_`, which is what `Warning_Box_` and
#: the plain message box both come out at. The art is WARNING.LBX entry
#: 0, 331x191, drawn at `Remap_Draw_(0x9A, _message_box_y, …)` with
#: `_message_box_y = 0x90` = (154, 144), and it adds ONE field,
#: `Add_Hidden_Field_(0, 0, 0x27F, 0x1DF, "\x1B", …)`.
#:
#: **THE HOTKEY IS WHAT TELLS IT FROM A SCREEN'S OWN CATCHER.** The
#: Fleets screen ends its list with `Add_Hidden_Field_(0, 0, 639, 479,
#: "", 0)` (flt1.cpp:1262) — the same rectangle with hotkey 0. Matching
#: on the rectangle alone would read every fleet screen as a warning box.
WARNING = BoxKind(
    "warning", (154, 144, 331, 191),
    (((0, 0, 639, 479), 0x1B, 7),),
    (("dismiss", 0x1B),),
    "GENDRAW::Message_Box_Exploding_, WARNING.LBX 0")

KINDS = (CONFIRMATION, WARNING)


class GameBox:
    """A recognised box, with the live fields that answer it."""

    def __init__(self, kind, fields):
        self.kind = kind
        self.fields = fields        # {hotkey: FieldInfo}

    @property
    def name(self):
        return self.kind.name

    @property
    def rect(self):
        return self.kind.rect

    def buttons(self):
        """`[(label_key, FieldInfo)]` for the answers that are live."""
        return [(key, self.fields[hk])
                for key, hk in self.kind.answers if hk in self.fields]


def _shape(f):
    return ((f.x, f.y, f.x_end, f.y_end), f.hotkey, f.field_type)


def detect(fields):
    """The box the live field list IS, or None.

    **THE WHOLE LIST, NOT A SUBSET.** A box replaces the list rather
    than adding to it, so a match is an equality: anything else present
    means this is a screen with its own fields and not a box. That is
    also what keeps a screen whose own fields happen to include one of
    these rectangles from being read as a box.
    """
    live = [f for f in (fields or []) if f.index != 0]
    if not live:
        return None
    shapes = {_shape(f) for f in live}
    for kind in KINDS:
        if shapes == kind.fields:
            return GameBox(kind, {f.hotkey: f for f in live})
    return None


def crop(framebuffer_surface, kind_rect):
    """The box's own pixels, or None. `framebuffer_surface` is 640x480."""
    if framebuffer_surface is None:
        return None
    r = pygame.Rect(kind_rect)
    if not framebuffer_surface.get_rect().contains(r):
        return None
    return framebuffer_surface.subsurface(r).copy()
