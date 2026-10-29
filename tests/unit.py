#!/usr/bin/env python3
"""The quick tests: plain asserts, standard library only, no display, no engine.

    python tests/unit.py          # about a second; exit 0 when all pass

What they hold is what a contributor breaks first and a player notices last:
the wire frame reader, the record parsers on short and wrong input, the
block reader's whole-or-raise contract, the LBX header, and the engine
LAYOUT overriding a spec's kind. The maintainer's full suite takes minutes
and renders screens; this file needs nothing but the repository.
"""
import logging
import os
import select
import socket
import struct
import sys
import tempfile
import threading
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import imagecap, lbx  # noqa: E402
from core.blockreader import BlockError, Reader  # noqa: E402
from core.game_client import GameClient  # noqa: E402
from core.structs import Spec, layout  # noqa: E402
from core.structs import (colony, leader, nebula, planet, player,  # noqa: E402
                          settings, ship, ship_icon, star)
from core.wire_protocol import (CAP_DEMOLISH, MAGIC,  # noqa: E402
                                MSG_HELLO_REPLY)


def frame(msg_type, payload, seq=1):
    return (struct.pack("<II", MAGIC, 8 + len(payload))
            + struct.pack("<HHI", msg_type, 0, seq) + payload)


def pair():
    """Two connected sockets, closed when the test is over."""
    a, b = socket.socketpair()
    OPEN.extend((a, b))
    return a, b


OPEN = []


def poll(c, wait=True):
    """`poll()` once the data has arrived: on a loopback pair (Windows) a
    send is not delivered at once, and a non-blocking read would see none."""
    if wait:
        select.select([c.sock], [], [], 1.0)
    return c.poll()


def client_on(sock):
    """A client reading from `sock`, whose loss is recorded, not retried."""
    sock.setblocking(False)
    c = GameClient()
    c.sock, c.connected = sock, True
    c.lost_reasons = []
    c._lost = lambda reason: c.lost_reasons.append(reason)
    return c


def test_frame_split_across_reads():
    a, b = pair()
    c = client_on(b)
    data = frame(MSG_HELLO_REPLY, struct.pack("<HH", 1, CAP_DEMOLISH))
    a.sendall(data[:11])
    assert poll(c) is False and len(c._recv_buf) == 11, (
        "half a frame was acted on, or dropped")
    assert c.capabilities == 0
    a.sendall(data[11:])
    assert poll(c) is True
    assert c.capabilities == CAP_DEMOLISH and not c.lost_reasons


def test_two_frames_in_one_read():
    a, b = pair()
    c = client_on(b)
    seen = []
    real = c._handle_message
    c._handle_message = lambda t, f, p: (seen.append(p), real(t, f, p))[1]
    a.sendall(frame(MSG_HELLO_REPLY, struct.pack("<HH", 1, 0), 1)
              + frame(MSG_HELLO_REPLY, struct.pack("<HH", 1, CAP_DEMOLISH), 2))
    poll(c)
    assert len(seen) == 2, f"{len(seen)} of two frames were handled"
    assert c.capabilities == CAP_DEMOLISH and not c.lost_reasons


def test_bad_magic_is_a_loss():
    a, b = pair()
    c = client_on(b)
    a.sendall(b"\x00" * 32)
    assert poll(c) is False and len(c.lost_reasons) == 1
    assert "magic" in c.lost_reasons[0], c.lost_reasons
    assert len(c._recv_buf) == 0, "an out-of-step stream was kept"


def test_impossible_length_is_a_loss():
    a, b = pair()
    c = client_on(b)
    a.sendall(struct.pack("<II", MAGIC, 0xFFFFFFF0) + b"\x00" * 16)
    assert poll(c) is False and len(c.lost_reasons) == 1
    assert "length" in c.lost_reasons[0], c.lost_reasons


def test_closed_socket_is_a_loss():
    a, b = pair()
    c = client_on(b)
    a.close()
    assert poll(c) is False and len(c.lost_reasons) == 1
    assert "disconnected" in c.lost_reasons[0], c.lost_reasons


def test_reader_is_whole_or_raises():
    r = Reader(b"\x01\x02\x03")
    for call in (lambda: r.take("I"), lambda: r.raw(4), lambda: r.raw(-1),
                 lambda: r.one("Q")):
        try:
            call()
        except BlockError:
            continue
        raise AssertionError("a read that does not fit returned")
    assert Reader(b"\x01\x02").take("BB") == (1, 2)


def test_every_record_spec_rejects_a_short_record():
    seen = 0
    for mod in (colony, leader, nebula, planet, player, settings, ship,
                ship_icon, star):
        for name, spec in vars(mod).items():
            if not isinstance(spec, Spec):
                continue
            seen += 1
            for n in (0, spec.size - 1):
                try:
                    spec.parse(b"\x00" * n)
                except ValueError:
                    continue
                raise AssertionError(f"{mod.__name__}.{name} parsed {n} bytes")
            spec.parse(b"\x00" * spec.size)           # and the full size parses
    assert seen >= 9, f"only {seen} specs found"


def test_pack_parse_round_trip():
    raw = star.SPEC.pack({"name": "Sol"})
    assert star.SPEC.parse(raw).name == "Sol"
    assert len(raw) == star.SPEC.size


def test_layout_rejects_short_and_foreign_messages():
    for payload in (b"", b"\x01", struct.pack("<HH", layout.VERSION + 1, 0),
                    struct.pack("<HH", layout.VERSION, 1)):
        try:
            layout.parse(payload)
        except ValueError:
            continue
        raise AssertionError(f"LAYOUT {payload!r} was accepted")


def test_engine_layout_keeps_the_application_id_unsigned():
    raw = bytearray(player.SIZE)
    raw[902] = 196                                    # ids run past 127
    sizes = {"i8": 1, "u8": 1, "i16": 2, "u16": 2, "i32": 4, "u32": 4}
    members = {n: layout.Member(n, off, sizes[k], sizes[k],
                                layout.SIGNED if k.startswith("i")
                                else layout.UNSIGNED, "")
               for n, off, k in player.SPEC.fields if k in sizes}
    members["current_research_application"] = layout.Member(
        "current_research_application", 902, 1, 1, layout.SIGNED, "")
    layout.install(layout.Layout(1, {"s_player": layout.Record(
        "s_player", player.SIZE, members)}))
    try:
        assert player.SPEC.parse(bytes(raw)).current_research_application \
            == 196
    finally:
        layout.install(None)


def test_lbx_header_with_too_many_entries_is_an_lbx_error():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x.lbx")
        with open(path, "wb") as f:
            f.write(struct.pack("<HHI", 600, lbx.LBX_MAGIC, 0))
            f.write(b"\0" * (4 * lbx.LBX_OFFSET_COUNT))
        for call in (lambda: lbx.read_entries(path),
                     lambda: lbx.read_entry(path, 599)):
            try:
                call()
            except lbx.LbxError:
                continue
            raise AssertionError("an oversized LBX header was read")


def test_a_send_waits_for_a_full_buffer_instead_of_losing_the_connection():
    a, b = pair()
    c = client_on(b)
    b.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    a.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    while True:                    # fill what the engine has not read yet
        try:
            b.send(b"\0" * 4096)
        except BlockingIOError:
            break
    drained = []

    def engine_reads():
        time.sleep(0.3)
        a.settimeout(1.0)
        try:
            while True:
                drained.append(len(a.recv(65536)))
        except OSError:
            pass
    t = threading.Thread(target=engine_reads, daemon=True)
    t.start()
    c._send_message(MSG_HELLO_REPLY, b"\x01\x00\x00\x00")
    t.join(3)
    assert not c.lost_reasons, c.lost_reasons
    assert b.gettimeout() == 0.0, "the socket was left blocking"


def _png(width, height):
    """The smallest PNG whose header says width x height (never decoded)."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data)))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0,
                                         0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b""))


def test_a_mod_picture_is_judged_by_its_header_before_it_is_decoded():
    with tempfile.TemporaryDirectory() as d:
        small, huge, junk = (os.path.join(d, n) for n in
                             ("small.png", "huge.png", "junk.png"))
        with open(small, "wb") as f:
            f.write(_png(64, 48))
        with open(huge, "wb") as f:
            f.write(_png(30000, 30000))
        with open(junk, "wb") as f:
            f.write(b"not a picture")
        try:
            size = imagecap.header_size(small)
        except ImportError:
            return                        # no Pillow: the check is skipped
        assert size in ((64, 48), None), size
        for bad in (huge, junk, os.path.join(d, "missing.png")):
            try:
                imagecap.header_size(bad)
            except ValueError:
                continue
            raise AssertionError(f"{os.path.basename(bad)} was accepted")


def main():
    logging.disable(logging.CRITICAL)      # the code under test logs its refusals
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as err:                       # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(err).__name__}: {err}")
        else:
            print(f"ok   {name}")
        finally:
            while OPEN:
                OPEN.pop().close()
    print(f"{len(tests) - failed} of {len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
