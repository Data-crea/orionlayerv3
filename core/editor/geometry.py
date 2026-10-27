"""Where a box may stand: inside the reference area, never outside it.

The editor used to let a drag leave the 1920x1080 space (a `help_popup`
was saved 114 reference px outside it, and only the smoke suite said
so, work order 153). Every way the editor changes a rect —
drag, handle, arrow key, the panel's number fields — ends here, so the
rule has one home (decision 5).
"""
from core.config import REF_W, REF_H

#: Smallest side a number field may set; a drag keeps its own 20.
MIN_SIZE = 8


def clamp_move(rect):
    """`rect` moved back inside the reference area, size unchanged."""
    x, y, w, h = (int(v) for v in rect)
    w, h = min(w, REF_W), min(h, REF_H)
    return (max(0, min(x, REF_W - w)), max(0, min(y, REF_H - h)), w, h)


def clamp_resize(rect, handle=""):
    """`rect` with its edges inside the area and a side of at least
    `MIN_SIZE`; `handle` names the edge the pointer drives ("l", "tr")
    so that edge is the one that gives way."""
    x, y, w, h = (int(v) for v in rect)
    left, top = max(0, x), max(0, y)
    right, bottom = min(REF_W, x + w), min(REF_H, y + h)
    if right - left < MIN_SIZE:
        if "l" in handle:
            left = max(0, right - MIN_SIZE)
        right = min(REF_W, left + MIN_SIZE)
    if bottom - top < MIN_SIZE:
        if "t" in handle:
            top = max(0, bottom - MIN_SIZE)
        bottom = min(REF_H, top + MIN_SIZE)
    return (left, top, right - left, bottom - top)
