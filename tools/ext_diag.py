#!/usr/bin/env python3
"""
ext_diag.py — Extension API diagnostic tool.

Connects to orion2re, receives raw frames, and validates
the binary parse step by step. Reports offsets, sizes,
and any mismatches. The wire-protocol parsing is standalone
by design (this tool must still work if core/game_client.py
itself is what's broken) — only the id -> screen-name table
is shared with the rest of the project, via core/screen_names.py
(pure data, no pygame import, so it doesn't compromise the
standalone-ness this tool relies on).

Usage:
    python ext_diag.py              # default localhost:17362
    python ext_diag.py host port    # custom address

Run from the project root (python tools/ext_diag.py) while
orion2re is running with -DORION2RE_EXT=ON.
"""
import os
import socket
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.screen_names import SCREENS as _SCREENS  # noqa: E402
from core.wire_protocol import (  # noqa: E402
    MAGIC, PROTO_VERSION, MSG_HELLO, MSG_HELLO_REPLY, MSG_STATE,
    MSG_FIELDS, MSG_VISUAL, MSG_EVENT,
    SUB_STATE, SUB_FIELDS, SUB_VISUAL, SUB_EVENTS,
    MSG_NAMES, parse_frame_header,
    frame_header as wp_frame_header,
)

# Single source: core/screen_names.py. Was an independent copy here
# that had already drifted (missing id 50, the synthetic Custom Race
# screen) before being unified.
SCREEN_NAMES = {sid: name for sid, (name, _) in _SCREENS.items()}

# ── Struct sizes (from sizes.h, orion2re 64-bit) ──────
# These are the values game_state.py uses.
# The diag will CHECK if they match the actual data.

SETTINGS_SIZE = 0x229       # 553
PLAYER_SIZE   = 0xF0E       # 3854
COLONY_SIZE   = 0x169       # 361
PLANET_SIZE   = 0x12        # 18
NEBULA_SIZE   = 0x05        # 5
LEADER_SIZE   = 0x3B        # 59
ANTARAN_SIZE  = 0x42        # 66
SHIP_SIZE     = 0x81        # 129
SHIP_ICON_SIZE = 12
MAX_PLAYERS   = 8
MAX_LEADERS   = 67

# STAR_SIZE is the risky one. Two candidates:
# sizes.h says 0x73 = 115, but game_state.py calculates 234
# because black_hole_blocks uses BITMAP(MAX_STARS=1024) = 128 bytes.
# We try both and report which one works.
STAR_SIZE_SMALL = 0x73      # 115 (sizes.h literal)
STAR_SIZE_LARGE = 234       # 0x6A + 128 (game_state.py)


# ── Helpers ────────────────────────────────────────────

class ParseCursor:
    """Tracks position in a byte buffer with named reads."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def i16(self, label=""):
        v = struct.unpack_from('<h', self.data, self.pos)[0]
        self.pos += 2
        return v

    def u16(self, label=""):
        v = struct.unpack_from('<H', self.data, self.pos)[0]
        self.pos += 2
        return v

    def i32(self, label=""):
        v = struct.unpack_from('<i', self.data, self.pos)[0]
        self.pos += 4
        return v

    def u8(self, label=""):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def skip(self, n):
        self.pos += n

    def raw(self, n):
        v = self.data[self.pos:self.pos + n]
        self.pos += n
        return v

    def remaining(self):
        return len(self.data) - self.pos


def star_name_at(data: bytes, offset: int) -> str:
    """Read a 15-byte star name, validate it's printable."""
    name_bytes = data[offset:offset + 15]
    name = name_bytes.split(b'\x00')[0].decode('latin-1', errors='replace')
    return name


def is_valid_star_name(name: str) -> bool:
    """Check if a star name looks reasonable."""
    if not name or len(name) < 2:
        return False
    return all(c.isalpha() or c in " '-" for c in name)


# ── Connection ─────────────────────────────────────────

def connect(host, port):
    """Connect and send HELLO. Returns socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    sock.connect((host, port))
    print(f"  Connected to {host}:{port}")

    # Send HELLO with all subscriptions
    subs = SUB_STATE | SUB_FIELDS | SUB_VISUAL | SUB_EVENTS
    payload = struct.pack('<HH', PROTO_VERSION, subs)
    sock.sendall(wp_frame_header(MSG_HELLO, payload))
    print("  HELLO sent (all subscriptions)")
    return sock


def recv_exact(sock, n):
    """Receive exactly n bytes."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf.extend(chunk)
    return bytes(buf)


def recv_frame(sock):
    """Receive one framed message. Returns (msg_type, payload)."""
    header = recv_exact(sock, 8)
    magic, length = parse_frame_header(header)
    if magic != MAGIC:
        raise ValueError(f"Bad magic: 0x{magic:08X}")

    body = recv_exact(sock, length)
    msg_type, flags, seq = struct.unpack_from('<HHI', body, 0)
    payload = body[8:]
    return msg_type, payload


# ── Diagnostics ────────────────────────────────────────

def diag_fields(payload):
    """Parse and print FIELD_LIST.

    Deliberately NOT using wire_protocol.parse_field_list_raw: this
    function's job is to independently re-derive the byte offsets
    with ParseCursor so a drift between this tool and the shared
    parser is itself something the tool can catch (project rule —
    two independent sources before trusting a value).
    """
    c = ParseCursor(payload)
    count = c.i16()
    print(f"  Field count: {count}")
    for i in range(count):
        idx = c.i16()
        x = c.i16()
        y = c.i16()
        xe = c.i16()
        ye = c.i16()
        ft = c.i16()
        hk = c.u8()
        hk_str = chr(hk) if 32 < hk < 127 else f"0x{hk:02X}"
        print(f"    [{idx:2d}] ({x:4d},{y:4d})-({xe:4d},{ye:4d})"
              f"  type={ft}  hotkey={hk_str}")
    left = c.remaining()
    if left:
        print(f"  WARNING: {left} bytes remaining after fields")


def diag_visual(payload):
    """Check VISUAL_FRAME size and palette."""
    expected = 640 * 480 + 768
    actual = len(payload)
    ok = "OK" if actual == expected else "MISMATCH"
    print(f"  Visual frame: {actual} bytes (expected {expected}) [{ok}]")
    if actual >= expected:
        # Check palette — color 0 is usually black
        pal_start = 640 * 480
        r, g, b = payload[pal_start], payload[pal_start+1], payload[pal_start+2]
        print(f"  Palette[0] = ({r},{g},{b})")
        # Check if framebuffer has non-zero pixels
        fb = payload[:640*480]
        nonzero = sum(1 for b in fb if b != 0)
        pct = nonzero / (640*480) * 100
        print(f"  Framebuffer: {pct:.1f}% non-zero pixels")


def try_parse_state(payload, star_size, label):
    """Try parsing STATE_SNAPSHOT with given star_size.

    Returns True if parse completes without error and
    star names look valid.
    """
    print(f"\n  ── Trying STAR_SIZE = {star_size} ({label}) ──")
    c = ParseCursor(payload)

    try:
        # Game Identity (29 bytes)
        screen    = c.i16()
        prev_scr  = c.u8()
        stardate  = c.i32()
        player_n  = c.i16()
        n_players = c.i16()
        n_stars   = c.i16()
        n_ships   = c.i16()
        n_cols    = c.i16()
        n_nebs    = c.u8()
        game_type = c.u8()
        map_scale = c.i16()
        map_x     = c.i16()
        map_y     = c.i16()
        map_max_x = c.i16()
        map_max_y = c.i16()

        screen_name = SCREEN_NAMES.get(screen, f"?{screen}")
        sd_str = f"{stardate // 10}.{stardate % 10}"

        print(f"  Screen:     {screen} = {screen_name}")
        print(f"  Stardate:   {sd_str}")
        print(f"  Player:     {player_n} of {n_players}")
        print(f"  Stars:      {n_stars}")
        print(f"  Ships:      {n_ships}")
        print(f"  Colonies:   {n_cols}")
        print(f"  Nebulas:    {n_nebs}")
        print(f"  Game type:  {game_type}")
        print(f"  Map:        scale={map_scale} pos=({map_x},{map_y})"
              f" max=({map_max_x},{map_max_y})")
        print(f"  @ offset {c.pos}: settings ({SETTINGS_SIZE} B)")

        # Sanity check counts
        if n_stars < 0 or n_stars > 1024:
            print(f"  FAIL: n_stars={n_stars} out of range")
            return False
        if n_players < 0 or n_players > 8:
            print(f"  FAIL: n_players={n_players} out of range")
            return False

        # Settings
        settings = c.raw(SETTINGS_SIZE)
        print(f"  @ offset {c.pos}: players ({MAX_PLAYERS}x"
              f" {PLAYER_SIZE} = {MAX_PLAYERS * PLAYER_SIZE} B)")

        # Players
        for i in range(MAX_PLAYERS):
            c.skip(PLAYER_SIZE)
        print(f"  @ offset {c.pos}: star count + stars")

        # Stars
        ns2 = c.i16()
        if ns2 != n_stars:
            print(f"  WARNING: repeated star count {ns2} != {n_stars}")

        valid_names = 0
        sample_names = []
        star_start = c.pos
        for i in range(ns2):
            star_offset = c.pos
            star_raw = c.raw(star_size)
            name = star_raw[0:15].split(b'\x00')[0].decode(
                'latin-1', errors='replace')
            if is_valid_star_name(name):
                valid_names += 1
            if i < 5:
                x = struct.unpack_from('<h', star_raw, 15)[0]
                y = struct.unpack_from('<h', star_raw, 17)[0]
                sample_names.append(f"{name} ({x},{y})")

        if ns2 > 0:
            pct = valid_names / ns2 * 100
            print(f"  Stars parsed: {ns2}, valid names: "
                  f"{valid_names}/{ns2} ({pct:.0f}%)")
            if sample_names:
                print(f"  First stars: {', '.join(sample_names)}")
            if pct < 50:
                print(f"  FAIL: most star names are garbage "
                      f"→ wrong STAR_SIZE")
                return False

        print(f"  @ offset {c.pos}: ship count + ships")

        # Ships
        ns_ships = c.i16()
        if ns_ships != n_ships:
            print(f"  WARNING: repeated ship count "
                  f"{ns_ships} != {n_ships}")
        for i in range(ns_ships):
            c.skip(SHIP_SIZE)
        print(f"  @ offset {c.pos}: colony count + colonies")

        # Colonies
        nc = c.i16()
        if nc != n_cols:
            print(f"  WARNING: repeated colony count {nc} != {n_cols}")
        for i in range(nc):
            c.skip(COLONY_SIZE)
        print(f"  @ offset {c.pos}: planet count + planets")

        # Planets
        np = c.i16()
        expected_planets = ns2 * 5 if ns2 > 0 else 0
        if np != expected_planets and ns2 > 0:
            print(f"  NOTE: planet count {np}, expected "
                  f"{expected_planets} (stars×5)")
        for i in range(np):
            c.skip(PLANET_SIZE)
        print(f"  @ offset {c.pos}: nebula count + nebulas")

        # Nebulas
        nn = c.u8()
        if nn != n_nebs:
            print(f"  WARNING: repeated nebula count {nn} != {n_nebs}")
        for i in range(nn):
            c.skip(NEBULA_SIZE)
        print(f"  @ offset {c.pos}: leaders "
              f"({MAX_LEADERS}x {LEADER_SIZE} B)")

        # Leaders
        for i in range(MAX_LEADERS):
            c.skip(LEADER_SIZE)
        print(f"  @ offset {c.pos}: antarans ({ANTARAN_SIZE} B)")

        # Antarans
        c.skip(ANTARAN_SIZE)
        print(f"  @ offset {c.pos}: ship icon count + icons")

        # Ship icons
        ni = c.i16()
        for i in range(ni):
            c.skip(SHIP_ICON_SIZE)

        left = c.remaining()
        print(f"  @ offset {c.pos}: END — {left} bytes remaining")

        if left == 0:
            print(f"  ✓ PERFECT PARSE — zero bytes remaining")
            return True
        elif left < 100:
            print(f"  ~ CLOSE — small remainder, possible "
                  f"trailing field or padding")
            return True
        else:
            print(f"  ✗ FAIL — {left} bytes unaccounted for")
            return False

    except (struct.error, IndexError) as e:
        print(f"  ✗ PARSE ERROR at offset {c.pos}: {e}")
        print(f"  Remaining: {c.remaining()} bytes")
        return False


def diag_state(payload):
    """Diagnose a STATE_SNAPSHOT payload."""
    print(f"\n{'='*60}")
    print(f"STATE_SNAPSHOT — {len(payload)} bytes")
    print(f"{'='*60}")

    # Try both star sizes
    ok_small = try_parse_state(payload, STAR_SIZE_SMALL,
                               "sizes.h = 0x73 = 115")
    ok_large = try_parse_state(payload, STAR_SIZE_LARGE,
                               "game_state.py = 234")

    print(f"\n  ── Result ──")
    if ok_small and not ok_large:
        print(f"  → STAR_SIZE = {STAR_SIZE_SMALL} is correct")
        print(f"    Fix game_state.py: STAR_SIZE = 0x73  # 115")
    elif ok_large and not ok_small:
        print(f"  → STAR_SIZE = {STAR_SIZE_LARGE} is correct")
        print(f"    game_state.py is already right")
    elif ok_small and ok_large:
        print(f"  → Both sizes parse (unlikely — need a game "
              f"with stars to distinguish)")
    else:
        print(f"  → NEITHER size works — struct sizes may have "
              f"changed, check sizeof() in C++")
        print(f"    Run this in orion2re to get actual sizes:")
        print(f'    printf("star=%zu player=%zu colony=%zu '
              f'planet=%zu\\n", sizeof(s_star_data), '
              f'sizeof(s_player), sizeof(s_colony), '
              f'sizeof(s_planet_data));')


# ── Main ───────────────────────────────────────────────

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 17362

    print(f"ext_diag — OrionLayer v3 Extension API diagnostic")
    print(f"Connecting to {host}:{port}...")

    try:
        sock = connect(host, port)
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        print(f"  FAILED: {e}")
        print(f"  Is orion2re running with -DORION2RE_EXT=ON?")
        return

    print(f"\nWaiting for messages (Ctrl+C to stop)...\n")

    state_count = 0
    fields_seen = False
    visual_seen = False

    try:
        while True:
            msg_type, payload = recv_frame(sock)
            name = MSG_NAMES.get(msg_type, f"0x{msg_type:04X}")

            if msg_type == MSG_HELLO_REPLY:
                print(f"  ✓ HELLO_REPLY ({len(payload)} bytes)")

            elif msg_type == MSG_STATE:
                state_count += 1
                # Only diagnose the first few, then just count
                if state_count <= 2:
                    diag_state(payload)
                elif state_count == 3:
                    print(f"\n  (Subsequent snapshots — counting only,"
                          f" Ctrl+C to stop)")
                if state_count % 100 == 0:
                    print(f"  ... {state_count} snapshots received",
                          end='\r')

            elif msg_type == MSG_FIELDS:
                print(f"\nFIELD_LIST — {len(payload)} bytes")
                diag_fields(payload)

            elif msg_type == MSG_VISUAL:
                if not visual_seen:
                    print(f"\nVISUAL_FRAME — {len(payload)} bytes")
                    diag_visual(payload)
                    visual_seen = True

            elif msg_type == MSG_EVENT:
                if len(payload) >= 4:
                    ef, es = struct.unpack_from('<Hh', payload, 0)
                    sn = SCREEN_NAMES.get(es, f"?{es}")
                    print(f"\n  EVENT: flags=0x{ef:04X} "
                          f"screen={es} ({sn})")

    except KeyboardInterrupt:
        print(f"\n\nStopped. Received {state_count} snapshots total.")
    except ConnectionError as e:
        print(f"\nConnection lost: {e}")
    finally:
        sock.close()


if __name__ == '__main__':
    main()
