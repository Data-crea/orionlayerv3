"""orion2re Extension API — wire-protocol constants and raw parsing.

Pure stdlib (only `struct`), no other project imports, so this can
be imported by tools/ext_diag.py and tools/ext_diag_race.py without
compromising their "must still work if the rest of the project is
broken" design goal — while still being the single place the byte
layout is defined.

Before this module existed, the frame header, message-type/
subscription constants, and the FIELD_LIST (13 bytes/field) parser
were each reimplemented independently in core/game_state.py,
tools/ext_diag.py, and tools/ext_diag_race.py — three copies of the
same byte offsets, silently able to drift out of sync with each
other and with ext_api_dokumentation_v3.md.

See ext_api_dokumentation_v3.md for the authoritative protocol
description (frame format, message types, field-list layout).
"""
import struct

MAGIC = 0x4F325845          # "O2XE"
PROTO_VERSION = 1

# Message types
MSG_HELLO         = 0x01
MSG_HELLO_REPLY   = 0x01
MSG_STATE         = 0x10
MSG_FIELDS        = 0x11
MSG_VISUAL        = 0x12
MSG_EVENT         = 0x13
MSG_ACTIVATE      = 0x80
MSG_INJECT_KEY    = 0x81
MSG_INJECT_CLICK  = 0x82
MSG_CANCEL_FIELD  = 0x83

#: How many STATE/VISUAL pairs after an injected command can still
#: describe the world BEFORE it. One — so a caller that waits for an
#: effect must let that one go by.
#:
#: `ext::Tick()` runs `ProcessInput()` first and serializes the
#: snapshot and the frame afterwards, in the same tick
#: (ext_api.cpp:341-386), so the message that follows a send was
#: built from the world the send has not reached yet: the command has
#: been handed over, not consumed. Measured 5 September 2026 — one
#: increment of the colony summary's list window read the old `_first`
#: at pair 1 and the new one at pair 2, every time.
#:
#: **IT IS NOT A SETTLING TIME, AND DECISION 21 IS WHY THAT HAS TO BE
#: SAID.** Nothing may advance because a count or a clock ran out;
#: what ends a wait is the caller's own predicate about the world.
#: This is a bolt against one specific way that predicate can lie —
#: it can have been true before the send. Two is the whole structural
#: gap (the consuming tick, and the first tick that can show the
#: effect); three would start skipping evidence, waiting past a step
#: that landed on the first eligible pair.
#:
#: It lives here because it is a property of the PROTOCOL's tick
#: ordering, not of any screen — and because there are two wait
#: shapes that need it and cannot share code: a blocking one in the
#: tools and a frame-driven one in the screens.
EFFECT_PAIRS = 2

MSG_NAMES = {
    0x01: "HELLO_REPLY", 0x10: "STATE_SNAPSHOT",
    0x11: "FIELD_LIST",  0x12: "VISUAL_FRAME",
    0x13: "EVENT",
}

# Subscription flags (bitmask in HELLO)
SUB_STATE  = 0x01
SUB_FIELDS = 0x02
SUB_VISUAL = 0x04
SUB_EVENTS = 0x08

FIELD_RECORD_SIZE = 13  # bytes per FIELD_LIST entry


def frame_header(msg_type, payload, seq=0, flags=0):
    """Build one O2XE frame: 8B frame header + 8B message header +
    payload."""
    msg_header = struct.pack('<HHI', msg_type, flags, seq)
    body = msg_header + payload
    return struct.pack('<II', MAGIC, len(body)) + body


def parse_frame_header(header_bytes):
    """Unpack the 8-byte frame header. Returns (magic, length)."""
    return struct.unpack('<II', header_bytes)


def parse_field_list_raw(data):
    """Parse a FIELD_LIST payload into raw tuples.

    Returns a list of (index, x, y, x_end, y_end, field_type,
    hotkey) — the byte layout ext_api_dokumentation_v3.md documents
    under "Field list" (13 bytes/field). Callers that want objects
    (core.game_state.FieldInfo) or dicts wrap this; the byte offsets
    themselves live only here.
    """
    count = struct.unpack_from('<h', data, 0)[0]
    out = []
    pos = 2
    for _ in range(count):
        idx, x, y, xe, ye, ft = struct.unpack_from('<hhhhhh', data, pos)
        hk = data[pos + 12]
        out.append((idx, x, y, xe, ye, ft, hk))
        pos += FIELD_RECORD_SIZE
    return out
