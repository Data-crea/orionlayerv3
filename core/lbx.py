"""LBX containers and the sprites inside them, decoded once.

Three tools read the player's own Master of Orion 2 files —
`help_extract.py`, `nebula_extract.py` and `raceicon_extract.py` —
and the first two had grown a private copy each of the same two
formats. This module is where the third one made that stop being
acceptable.

Formats, transcribed from the orion2re source:

  LBX container      `vfs_lbx.cpp`  magic 0xFEAD, 510 uint32 offsets
  animation header   `orion2.h`     `s_animation_header`, 12 bytes
  bitmap frames      `draw.cpp`     `Draw_Bitmap_Sprite_`, 0 = alpha
  packed frames      `draw.cpp`     `Draw_Animated_Sprite_`, RLE runs
  embedded palette   `animate.cpp`  `Set_Animation_Palette_`,
                                    4 bytes per entry, 6-bit VGA

**NOTHING HERE IMAGES ANYTHING, AND THAT IS THE SEAM.** Decoding
gives palette INDICES; `rgba_bytes` turns those into a buffer a PNG
writer can take. Pillow is a tool dependency and must not become a
`core/` one — the game itself never opens an LBX, it talks to
orion2re over the wire, so this module is here for the tools' sake
and has to stay as cheap as the rest of `core/`.

**ERRORS ARE RAISED, NOT EXITED.** The tools that used to own this
code called `sys.exit` with a sentence a human could act on, which
is right for a tool and wrong for a library: a caller that wants to
try a second file cannot catch a `SystemExit` without catching every
other one too. `LbxError` carries the same sentences; the tools
still exit on them.
"""
import struct

#: `vfs_lbx.cpp` — the magic in the second uint16 and the fixed
#: offset table that follows the 8-byte header. The table is always
#: 510 entries whatever the file holds.
LBX_MAGIC = 0xFEAD
LBX_OFFSET_COUNT = 510

#: `orion2_consts.h` — the flag bits of `s_animation_header`.
FLAG_DRAW_MODE_MASK = 0x03
FLAG_HAS_PALETTE = 0x10
DRAW_MODE_ANIMATED = 0
DRAW_MODE_BITMAP = 1


class LbxError(Exception):
    """A file that is not the format it was opened as."""


def read_entries(path):
    """The raw bytes of every entry, per `vfs_lbx.cpp`."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 8 + 4 * LBX_OFFSET_COUNT:
        raise LbxError("File is too small to be an LBX container.")
    entry_count, magic, _header_data = struct.unpack_from("<HHI", data, 0)
    if magic != LBX_MAGIC:
        raise LbxError(f"Bad LBX magic 0x{magic:04X} (expected 0xFEAD).")
    offsets = struct.unpack_from(f"<{LBX_OFFSET_COUNT}I", data, 8)
    entries = []
    for i in range(entry_count):
        start, end = offsets[i], offsets[i + 1]
        if end < start or end > len(data):
            raise LbxError(f"Entry {i}: corrupt offsets {start}..{end}.")
        entries.append(data[start:end])
    return entries


def read_entry(path, index):
    """One entry, without holding the others.

    The bounds are checked against the file's OWN entry count and not
    against the offset table, which is 510 long in every LBX and
    would happily hand back a slice of whatever follows it.
    """
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 8 + 4 * LBX_OFFSET_COUNT:
        raise LbxError("File is too small to be an LBX container.")
    entry_count, magic, _ = struct.unpack_from("<HHI", data, 0)
    if magic != LBX_MAGIC:
        raise LbxError(f"Not an LBX file (magic 0x{magic:04X}).")
    if not 0 <= index < entry_count:
        raise LbxError(f"Entry {index} is outside the file's {entry_count}.")
    offsets = struct.unpack_from(f"<{LBX_OFFSET_COUNT}I", data, 8)
    start, end = offsets[index], offsets[index + 1]
    if not 0 < start <= end <= len(data):
        raise LbxError(f"Entry {index} has a bad offset pair "
                       f"({start}, {end}).")
    return data[start:end]


class Header:
    """`s_animation_header` (orion2.h) plus its frame-offset table.

    A class rather than a tuple because callers ask it questions —
    `mode`, `has_palette` — that a tuple would make every one of them
    re-derive from `flags`, which is how two tools end up disagreeing
    about what bit 4 means.
    """
    __slots__ = ("width", "height", "frame_count", "flags", "offsets")

    def __init__(self, width, height, frame_count, flags, offsets):
        self.width = width
        self.height = height
        self.frame_count = frame_count
        self.flags = flags
        self.offsets = offsets

    @property
    def mode(self):
        return self.flags & FLAG_DRAW_MODE_MASK

    @property
    def has_palette(self):
        return bool(self.flags & FLAG_HAS_PALETTE)

    def __repr__(self):
        return (f"Header({self.width}x{self.height}, "
                f"frames={self.frame_count}, flags=0x{self.flags:02X})")


def parse_header(blob, label="entry"):
    """The 12-byte header and the `frame_count + 1` offsets after it."""
    if len(blob) < 12:
        raise LbxError(f"{label}: entry too short for an animation header.")
    width, height, _cur, frame_count, _loop, _key, _unk, flags = \
        struct.unpack_from("<hhhhbbBB", blob, 0)
    if width <= 0 or height <= 0 or frame_count <= 0:
        raise LbxError(f"{label}: implausible header "
                       f"(w={width} h={height} frames={frame_count}).")
    if len(blob) < 12 + 4 * (frame_count + 1):
        raise LbxError(f"{label}: entry too short for {frame_count} "
                       f"frame offsets.")
    offsets = struct.unpack_from(f"<{frame_count + 1}I", blob, 12)
    return Header(width, height, frame_count, flags, offsets)


def read_palette(blob, frame_count):
    """The embedded palette, per `Set_Animation_Palette_`.

    It sits after the frame-offset table — `Animation_Palette_Header_`
    (orion2.h:3145) is exactly `frame_offsets + frame_count + 1` — as
    an `s_palette_header` (start_index, count) followed by one
    `s_palette_entry` each.

    **THE FLAG COMES FIRST: `{changed, r, g, b}`, orion2.h:2131-2136.**
    This function read `r, g, b, changed` until 6 September 2026,
    inherited verbatim by `core/lbx.py` from `nebula_extract.py`,
    so every colour it returned was one byte to the left — the
    `changed` flag as red, red as green, green as blue, and blue
    thrown away. COLSUM.LBX entry 0 came back with index 255 as
    (0, 252, 252), a cyan where the palette's own white is
    (252, 252, 252). Two things made it invisible for as long as it
    existed: the only caller was the nebula extractor, and **not one
    of STARBG.LBX's 48 nebula entries carries a palette at all**, so
    the function had never once run on real data. The correction
    therefore changes no file in the tree — which is luck, not
    diligence, and is why the smoke check now pins the byte ORDER
    against the struct rather than only the scaling.

    RGB are 6-bit VGA components, scaled by 4 and clamped. Callers
    must check `has_palette` first — the bytes at this offset are
    frame data in an entry without one.
    """
    pos = 12 + 4 * (frame_count + 1)
    start, count = struct.unpack_from("<hh", blob, pos)
    pos += 4
    palette = {}
    for i in range(count):
        _changed, r, g, b = struct.unpack_from("<BBBB", blob, pos + 4 * i)
        palette[start + i] = (min(r * 4, 255), min(g * 4, 255),
                              min(b * 4, 255))
    return palette


def decode_bitmap(blob, offset, width, height):
    """Raw indexed bitmap, index 0 transparent (`Draw_Bitmap_Sprite_`)."""
    pixels = blob[offset:offset + width * height]
    if len(pixels) < width * height:
        return None
    return bytearray(pixels)


def decode_packed(blob, offset, width, height):
    """RLE frame per `Draw_Animated_Sprite_`.

    A 4-byte frame header (unknown, start_y), then runs of
    (pixel_count, skip_count). `pixel_count == 0` advances
    `skip_count` ROWS; otherwise `skip_count` advances x, then
    `pixel_count` literal bytes follow and the stream is padded to an
    even offset.

    `None` for a truncated or out-of-bounds stream, which is a state
    and not an error: an LBX holds entries of several kinds and a
    caller walking all of them will meet data that is not a sprite.
    """
    out = bytearray(width * height)
    _unknown, start_y = struct.unpack_from("<HH", blob, offset)
    pos = offset + 4
    y = start_y
    x = 0
    remaining = height - start_y
    while remaining > 0:
        if pos + 4 > len(blob):
            return None
        pixel_count, skip_count = struct.unpack_from("<hh", blob, pos)
        pos += 4
        if pixel_count == 0:
            remaining -= skip_count
            y += skip_count
            x = 0
        else:
            x += skip_count
            run = blob[pos:pos + pixel_count]
            if len(run) < pixel_count or y >= height or x + pixel_count > width:
                return None
            out[y * width + x: y * width + x + pixel_count] = run
            x += pixel_count
            pos += pixel_count
            if (pos - offset) & 1:
                pos += 1
    return out


def decode_frame(blob, header, frame=0):
    """The indices of one frame, or None for anything undecodable.

    The draw mode picks the decoder, exactly as `animate::Draw_` does
    (animate.cpp) — a mode this module does not implement answers
    None rather than guessing at the other one.
    """
    if not 0 <= frame < header.frame_count:
        return None
    offset = header.offsets[frame]
    if header.mode == DRAW_MODE_BITMAP:
        return decode_bitmap(blob, offset, header.width, header.height)
    if header.mode == DRAW_MODE_ANIMATED:
        return decode_packed(blob, offset, header.width, header.height)
    return None


def rgba_bytes(pixels, palette):
    """Indices -> a flat RGBA buffer, ready for `Image.frombytes`.

    Index 0 is transparent (`Draw_Bitmap_Sprite_` and
    `Draw_Animated_Sprite_` both skip it), a palette entry is opaque,
    and an index with no palette entry becomes opaque GRAYSCALE OF
    THE INDEX ITSELF. That last one is not a colour and is not meant
    to look like one: an entry without an embedded palette is drawn
    by the game in whatever palette the screen last set, which no
    extractor can know from the file alone. A grey ramp says "this is
    an index" out loud, where an invented colour would say "this is
    the sprite" and be believed.
    """
    out = bytearray(len(pixels) * 4)
    for i, idx in enumerate(pixels):
        if idx == 0:
            continue                        # already 0,0,0,0
        r, g, b = palette.get(idx, (idx, idx, idx))
        out[4 * i] = r
        out[4 * i + 1] = g
        out[4 * i + 2] = b
        out[4 * i + 3] = 255
    return bytes(out)
