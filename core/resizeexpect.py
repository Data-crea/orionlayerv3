"""Which VIDEORESIZE a deliberate mode change provoked — work order 324 a.

HD EXTENSION `resize_expect` (UNVERIFIED live). F7 and F11 used to set a bare flag that
swallowed "the next resize". `App._set_mode` records that the event often
never comes, and the flag then ate the player's NEXT, real resize: win_w,
win_h and the Layout no longer matched the surface. An expectation is now
the size(s) the change may announce and a deadline; an event of any other
size, or a late one, is the player's, and any event ends the expectation.
"""
import time

#: How long after a deliberate change its own event may still arrive.
EXPECT_S = 1.0


class ResizeExpect:
    def __init__(self):
        self._sizes = None
        self._until = 0.0

    def expect(self, *sizes):
        self._sizes = {tuple(s) for s in sizes}
        self._until = time.monotonic() + EXPECT_S

    def is_ours(self, w, h):
        sizes, self._sizes = self._sizes, None
        return bool(sizes) and time.monotonic() <= self._until \
            and (w, h) in sizes
