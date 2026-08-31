#!/usr/bin/env python3
"""
ext_diag_race.py — Race Screen field diagnostic.

Connects to orion2re, waits for SCREEN_RACE (ID 6),
dumps the field list, and optionally tests field activations.

Usage:
    1. Start orion2re
    2. Navigate to New Game -> Accept -> Select Race screen
    3. Run: python ext_diag_race.py

Run from the project root: python tools/ext_diag_race.py

Wire-protocol constants and the FIELD_LIST byte parser come from
core.wire_protocol (pure stdlib, no pygame) instead of being
reimplemented here — this file used to carry its own third copy
of the same 13-byte field-record layout as core/game_state.py and
tools/ext_diag.py.
"""
import os
import socket
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.wire_protocol import (  # noqa: E402
    MAGIC, PROTO_VERSION, MSG_HELLO, MSG_STATE, MSG_FIELDS,
    MSG_VISUAL, MSG_EVENT, MSG_ACTIVATE, MSG_INJECT_CLICK,
    SUB_STATE, SUB_FIELDS, SUB_EVENTS,
    frame_header, parse_frame_header, parse_field_list_raw,
)

SCREEN_RACE = 6

FIELD_TYPE_NAMES = {
    0: "Button", 1: "Radio", 7: "ClickThru", 8: "Hidden/Dynamic",
    12: "MapArea", 13: "Sidebar",
}


def connect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    sock.connect((host, port))

    subs = SUB_STATE | SUB_FIELDS | SUB_EVENTS
    payload = struct.pack('<HH', PROTO_VERSION, subs)
    sock.sendall(frame_header(MSG_HELLO, payload))
    return sock


def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf.extend(chunk)
    return bytes(buf)


def recv_frame(sock):
    header = recv_exact(sock, 8)
    magic, length = parse_frame_header(header)
    if magic != MAGIC:
        raise ValueError(f"Bad magic: 0x{magic:08X}")
    body = recv_exact(sock, length)
    msg_type = struct.unpack_from('<H', body, 0)[0]
    payload = body[8:]
    return msg_type, payload


def send_activate(sock, field_id, seq=0):
    sock.sendall(frame_header(MSG_ACTIVATE, struct.pack('<h', field_id), seq))


def send_click(sock, x, y, seq=0):
    sock.sendall(frame_header(MSG_INJECT_CLICK, struct.pack('<hh', x, y), seq))


def get_screen_id(payload):
    """Extract current_screen from STATE_SNAPSHOT."""
    if len(payload) >= 2:
        return struct.unpack_from('<h', payload, 0)[0]
    return -1


def parse_fields(payload):
    """Parse FIELD_LIST payload. Returns list of field dicts.

    Byte layout lives in core.wire_protocol.parse_field_list_raw
    (single source, shared with core/game_state.py and ext_diag.py).
    """
    return [
        {"index": idx, "x": x, "y": y, "x_end": xe, "y_end": ye,
         "type": ft, "hotkey": hk}
        for idx, x, y, xe, ye, ft, hk in parse_field_list_raw(payload)
    ]


def print_fields(fields):
    print(f"\n  FIELD_LIST — {len(fields)} fields:")
    print(f"  {'Idx':>3}  {'Rect':>28}  {'Type':>5}  "
          f"{'TypeName':<14}  {'Hotkey'}")
    print(f"  {'---':>3}  {'---':>28}  {'---':>5}  "
          f"{'---':<14}  {'---'}")
    for f in fields:
        hk = f["hotkey"]
        hk_str = chr(hk) if 32 < hk < 127 else f"0x{hk:02X}"
        tn = FIELD_TYPE_NAMES.get(f["type"], f"?{f['type']}")
        rect = (f"({f['x']:4d},{f['y']:4d})-"
                f"({f['x_end']:4d},{f['y_end']:4d})")
        print(f"  [{f['index']:2d}]  {rect}  "
              f"type={f['type']:<2d}  {tn:<14}  {hk_str}")


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 17362

    print(f"ext_diag_race — Select Race screen diagnostic")
    print(f"Connecting to {host}:{port}...")

    try:
        sock = connect(host, port)
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        print(f"  FAILED: {e}")
        print(f"  Is orion2re running with -DORION2RE_EXT=ON?")
        return

    print(f"  Connected. Waiting for SCREEN_RACE (ID {SCREEN_RACE})...")
    print(f"  Navigate to: Main Menu -> New Game -> Accept"
          f" -> Select Race")

    current_screen = -1
    race_fields = None

    try:
        while True:
            msg_type, payload = recv_frame(sock)

            if msg_type == MSG_STATE:
                sid = get_screen_id(payload)
                if sid != current_screen:
                    current_screen = sid
                    print(f"\n  Screen changed -> {sid}")

            elif msg_type == MSG_FIELDS:
                fields = parse_fields(payload)
                if current_screen == SCREEN_RACE:
                    race_fields = fields
                    print_fields(fields)
                    print(f"\n  Race screen fields captured!"
                          f" ({len(fields)} fields)")
                    break
                else:
                    print(f"  Fields received on screen {current_screen}"
                          f" ({len(fields)} fields) — not race screen")

    except KeyboardInterrupt:
        if race_fields is None:
            print(f"\n  Stopped before reaching race screen.")
            sock.close()
            return

    if not race_fields:
        print(f"  No race fields captured.")
        sock.close()
        return

    # Interactive test mode
    print(f"\n{'='*60}")
    print(f"  INTERACTIVE TEST MODE")
    print(f"  Type a field index to send ACTIVATE_FIELD")
    print(f"  Type 'c X Y' to send INJECT_CLICK at (X,Y)")
    print(f"  Type 'q' to quit")
    print(f"{'='*60}")

    seq = 1
    try:
        while True:
            cmd = input("\n  > ").strip()
            if cmd == 'q':
                break
            if cmd.startswith('c '):
                parts = cmd.split()
                if len(parts) == 3:
                    x, y = int(parts[1]), int(parts[2])
                    send_click(sock, x, y, seq)
                    print(f"  Sent INJECT_CLICK ({x}, {y})")
                    seq += 1
            else:
                try:
                    fid = int(cmd)
                    send_activate(sock, fid, seq)
                    print(f"  Sent ACTIVATE_FIELD({fid})")
                    seq += 1
                except ValueError:
                    print(f"  Invalid input: {cmd}")

            # Drain incoming messages to see if screen changed
            sock.settimeout(0.5)
            try:
                while True:
                    msg_type, payload = recv_frame(sock)
                    if msg_type == MSG_STATE:
                        sid = get_screen_id(payload)
                        if sid != current_screen:
                            current_screen = sid
                            print(f"  Screen changed -> {sid}")
                    elif msg_type == MSG_FIELDS:
                        fields = parse_fields(payload)
                        print_fields(fields)
            except (socket.timeout, BlockingIOError):
                pass
            sock.settimeout(10.0)

    except (KeyboardInterrupt, EOFError):
        pass

    print(f"\n  Done.")
    sock.close()


if __name__ == '__main__':
    main()
