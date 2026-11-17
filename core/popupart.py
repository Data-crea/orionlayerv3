"""The turn popups' pictures out of the player's own game — work order 402.

Two pictures of the original that HD's popups did not draw, read from the
raw LBX entries `tools/popup_art_extract.py` stores in
`assets/shared/turnpopup/gamedata/` (decisions 38, 40, 42, 95: never in a
repository, never in the base pack) and decoded here through `core/lbx.py`:

  EVENTS.LBX   TRANSCRIPTION `gnn_event_picture`: the GNN popup's news
               picture. `Load_Event_Picture` loads entry `event_id + 2`
               (events.cpp:2053-2056, :2371) and the event screen draws it
               at (320, 14) over the studio (`Draw_Event_Screen`,
               events.cpp:2708-2709). Every one of the 36 events has one
               (entries 2..37 of the player's file, 157 x 125, its own
               palette 184..247, index 0 transparent) — not only the five
               monsters. The ids 0..35 are `EVENT` (orion2_consts.h:126-
               164). Id 33, EVENT_ANTARANS_DEFEATED, is dead code in the
               engine (nothing sets it triggered; events.cpp:709, :2330):
               its picture exists and no popup ever asks for it. The intro
               of a GNN report (event id -1: no picture, `event_display_seg
               = 0`, events.cpp:2349, :2352) and an id outside 0..35 have
               none; the popup keeps Data's studio (mod folder) for them.
  ANTAROOM.LBX TRANSCRIPTION `antaran_room_picture`: the Antaran room.
               Entry 0 is a 24 x 24 mouse picture whose PALETTE the room
               uses (`Reload_Main_Antaran_Room_Screen`, antaroom.cpp:
               96-130: `Draw_Palette(pic)`), entry 1 the full-screen FILE
               ANIMATION (640 x 480, flags 0x20, 55 frames, loop frame 25),
               not entry 0 as a first reading of the function said. Frame 0
               is drawn whole on black (`Draw_File_Animation`); every frame
               after it is a delta painted over what is there
               (`Draw_Animated_Sprite_Back_Diff`, animate.cpp:391-440, run
               by `Draw_File_Animation_Stencil`, file_ani.cpp:156-222), and
               after the last the animation goes on at the header's loop
               frame (:200-207: loop_frame != frame_count - 1). One frame a
               pass of the room's loop, which waits `Release_Time(2)`
               (antaroom.cpp:62-75): two 55 ms ticks (timer.cpp:10, :53).
               UNVERIFIED `antaran_room_pace`: the auto function the room
               assigns (antaroom.cpp:57) may draw once more a pass
               (fields.cpp:815, :832); the pace is read from the code, not
               measured live.
               DEVIATION `antaran_room_speed`: the original's wait is
               `(ticks - animation_speedup) * 55 ms` (timer.cpp:50-62), so
               its PageUp/PageDown animation speed changes the room's pace
               (at +1 a 55 ms pass, at +2 and above none); HD keeps the
               fixed 110 ms of speed 0 and does not apply the battle's
               speed control (`cbclock`) to a popup.
               OMISSION `antaran_room_animations_off`: the original draws
               no animation with the "animations" option off
               (antaroom.cpp:17-19); HD always animates.

Nothing here is a picture of the repository's: without the player's files
every function answers None and the popup is drawn as before.
"""
import logging
import os
import struct

import numpy as np
import pygame

from core import blobart, lbx

log = logging.getLogger("popupart")

REL = "assets/shared/turnpopup/gamedata"
HOW = "python tools/popup_art_extract.py"
FORMAT_VERSION = 1
#: `EVENT_COUNT` (orion2_consts.h:164): the events 0..35.
EVENT_COUNT = 36
#: EVENTS.LBX holds an event's picture at `event_id + 2` (events.cpp:2055).
EVENT_FIRST_ENTRY = 2
#: EVENT_ANTARANS_DEFEATED: a picture no popup ever asks for (dead code).
EVENT_ANTARANS_DEFEATED = 33
#: Two 55 ms ticks a frame (antaroom.cpp:62-75, timer.cpp:10).
ROOM_FRAME_S = 0.110
#: The most frames one draw catches up after a pause, so a stalled window
#: never decodes the whole animation at once.
ROOM_MAX_CATCH_UP = 6
#: `antaran_room_normal_colors` (antaroom.cpp:9) in the room's palette: the
#: text colour 255 and the outline `Set_Outline_Color(0, 0xFA)` (:25).
TEXT_INDEX, OUTLINE_INDEX = 255, 250
ROOM_ENTRY_PALETTE, ROOM_ENTRY_ANIM = 0, 1

_events = {}
_room = {"folder": None, "obj": None, "tried": False}


def source(folder=None):
    return blobart.Source(REL, folder)


def _read(src, name):
    try:
        return src.read(name)
    except OSError:
        return None


def _rgba(index_pixels, width, height, palette):
    """Palette indices -> a pygame surface, index 0 transparent."""
    pal = np.zeros((256, 4), np.uint8)
    for i, (r, g, b) in palette.items():
        if 0 <= i < 256:
            pal[i] = (r, g, b, 255)
    pal[0] = (0, 0, 0, 0)
    arr = pal[np.frombuffer(bytes(index_pixels), np.uint8)]
    return pygame.image.frombuffer(arr.tobytes(), (width, height), "RGBA")


def event_picture(event_id, folder=None):
    """The news picture of event `event_id` (157 x 125, index 0 clear), or
    None: no such event, no extracted file, or one that will not decode."""
    if not isinstance(event_id, int) or not 0 <= event_id < EVENT_COUNT:
        return None
    key = (folder, event_id)
    if key in _events:
        return _events[key]
    out = None
    src = source(folder)
    blob = _read(src, f"event_{event_id}.bin")
    if blob is not None:
        try:
            head = lbx.parse_header(blob, f"event {event_id}")
            pal = lbx.read_palette(blob, head.frame_count) \
                if head.has_palette else {}
            pix = lbx.decode_frame(blob, head, 0)
            if pix is not None and pal:
                out = _rgba(pix, head.width, head.height, pal)
        except (lbx.LbxError, ValueError, struct.error) as err:
            log.warning("event picture %d will not decode (%s)",
                        event_id, err)
    if out is not None and pygame.display.get_surface():
        out = out.convert_alpha()
    _events[key] = out
    return out


def event_scaled(event_id, width, height, folder=None):
    """The event picture whole, magnified by the greatest integer that fits
    `width` x `height` (decision 28: the game's pixel art is never
    smoothed), or None."""
    pic = event_picture(event_id, folder)
    if pic is None or width <= 0 or height <= 0:
        return None
    k = max(1, min(width // pic.get_width(), height // pic.get_height()))
    return pygame.transform.scale(pic, (pic.get_width() * k,
                                        pic.get_height() * k))


class Room:
    """The Antaran room's animation, advanced as the original's loop does:
    one frame a pass, deltas painted over the screen, a loop at the
    header's loop frame."""

    def __init__(self, blob, palette_blob):
        self.head = lbx.parse_header(blob, "antaroom animation")
        if self.head.mode != lbx.DRAW_MODE_ANIMATED:
            raise lbx.LbxError("the Antaran room's animation is not a "
                               "packed-sprite animation")
        self.blob = blob
        ph = lbx.parse_header(palette_blob, "antaroom palette")
        self.palette = lbx.read_palette(palette_blob, ph.frame_count)
        # animate header: width, height, current, count, loop (offset 8)
        self.loop_frame = blob[8] if blob[8] < self.head.frame_count else 0
        self.canvas = bytearray(self.head.width * self.head.height)
        self.next_frame = 0
        self.t0 = None
        self.drawn = 0
        self.surface = None
        #: set by `_step` when a frame will not decode (a truncated file):
        #: the room is then given up for the rest of the popup
        self.broken = False
        lut = np.zeros((256, 3), np.uint8)
        for i, rgb in self.palette.items():
            if 0 <= i < 256:
                lut[i] = rgb
        self.lut = lut

    @property
    def size(self):
        return self.head.width, self.head.height

    def colour(self, index):
        return self.palette.get(index, (0, 0, 0))

    def _step(self):
        h = self.head
        # Guarded as `event_picture` is: a truncated or half-written
        # antaroom_1.bin passes the header and fails on a later frame;
        # `decode_packed` answers None for a stream that runs out.
        try:
            done = lbx.decode_packed(self.blob, h.offsets[self.next_frame],
                                     h.width, h.height, into=self.canvas)
        except (lbx.LbxError, ValueError, IndexError, struct.error) as err:
            log.warning("the Antaran room's frame %d will not decode (%s) "
                        "- the panel is drawn", self.next_frame, err)
            done = None
        if done is None:
            self.broken = True
            return False
        self.next_frame += 1
        if self.next_frame >= h.frame_count:
            # file_ani.cpp:200-207: the header's loop frame, or frame 0 when
            # the loop frame is the last one
            self.next_frame = self.loop_frame \
                if self.loop_frame != h.frame_count - 1 else 0
        self.drawn += 1
        return True

    def frame(self, now):
        """The picture at time `now` (seconds, any clock): frame 0 at the
        first call, then one more every `ROOM_FRAME_S`. None once a frame
        will not decode (`broken`)."""
        if self.broken:
            return None
        if self.t0 is None:
            self.t0 = now
        due = int((now - self.t0) / ROOM_FRAME_S) + 1
        behind = due - self.drawn
        if behind > ROOM_MAX_CATCH_UP:
            self.t0 = now - (self.drawn + ROOM_MAX_CATCH_UP - 1) * ROOM_FRAME_S
            behind = ROOM_MAX_CATCH_UP
        if self.surface is None and behind < 1:
            behind = 1
        for _ in range(max(0, behind)):
            if not self._step():
                return None
        if behind > 0 or self.surface is None:
            w, h = self.size
            rgb = self.lut[np.frombuffer(self.canvas, np.uint8)]
            self.surface = pygame.image.frombuffer(rgb.tobytes(), (w, h),
                                                   "RGB")
            if pygame.display.get_surface():
                self.surface = self.surface.convert()
        return self.surface


def room(folder=None):
    """The Antaran room, or None when the player's files were not
    extracted (or do not decode). Kept between frames; `reset` ends it."""
    if _room["tried"] and _room["folder"] == folder:
        obj = _room["obj"]
        return None if obj is not None and obj.broken else obj
    src = source(folder)
    anim = _read(src, "antaroom_1.bin")
    pal = _read(src, "antaroom_0.bin")
    obj = None
    if anim is not None and pal is not None:
        try:
            obj = Room(anim, pal)
        except (lbx.LbxError, ValueError, IndexError, struct.error) as err:
            log.warning("the Antaran room will not decode (%s) — the panel "
                        "is drawn", err)
    _room.update(folder=folder, obj=obj, tried=True)
    return obj


def reset():
    """The room ends: the next one starts from frame 0 (the animation's
    state is the screen's, and the original reopens the file each time,
    antaroom.cpp:117)."""
    _room.update(obj=None, tried=False)
    _events.clear()


def present(folder=None):
    """True when the stored files exist (for the checks and the state)."""
    return os.path.isfile(source(folder).path("antaroom_1.bin"))
