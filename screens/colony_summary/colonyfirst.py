"""Reading `COLSUM::_first` back off the original's own screen.

`_first` is not on the wire. Decision 46 says it must be ESTABLISHED
and never remembered, and the reason is that a visible game window
lets a human move it (platform.cpp:1379) — so a remembered value is a
lie the caller cannot detect. Establishing alone is still open loop,
though, and there is a channel: **the game draws `_first`.**

`COLSUM::Draw_Bar_Indicator_` (colsum.cpp:747-771) fills the scroll
thumb with palette index 229 from

    y1 = 271 * _first / n + 40
    y2 = 271 * (_first + 10) / n + 40

across x 621..626, where `n` is `COLXPORT::N_Colonies_` and the
divisions are C integer division. Borders are drawn over the fill's
edges in 230 (top, left) and 228 (right, bottom), so the 229 run is
inset by one row from `y1` and `y2` — measured, not assumed, and
`read_first` allows for it rather than pretending the fill reaches
its own bounds.

**IT IS ONLY DRAWN WHEN `n >= 10`** (colsum.cpp:751). Below that the
whole block is skipped, and `Update_First_` has already forced
`_first = 0` (colsum.cpp:194-197) — so the answer is genuinely "not
drawn", and `read_first` returns `NOT_DRAWN` rather than 0. A reader
that returned 0 there would be indistinguishable from a real
`_first = 0`, and an idle channel that looks like a valid reading is
the null-state failure the rim survey paid for, one domain over: a
green run in a state where nothing was measured.

**Why read it at all, when the plan already establishes it.** Because
`ACTIVATE_FIELD` has a single slot: `ext::g_pending_field` is one
`int16_t` and `ProcessInput` drains the whole queue before the game
consumes it, so a batch of activations leaves only the last (see
`doc/ext_api_dokumentation_v3.md` and the fundament). The steps
therefore have to be sent one at a time and CONFIRMED, and this is
what confirms them.
"""

#: Palette index of the thumb's fill, colsum.cpp:759.
THUMB_FILL = 229
#: Its border indices, drawn over the fill's own edge rows —
#: colsum.cpp:762-765. Named so the one-row inset below is a
#: transcription rather than a fudge factor.
THUMB_BORDER_LIGHT = 230
THUMB_BORDER_DARK = 228

#: The thumb's column range, colsum.cpp:759.
THUMB_X0, THUMB_X1 = 621, 626

#: The window the indicator is drawn for, colsum.cpp:749 and :751.
WINDOW = 10

#: `read_first` returns this when the game is not drawing the bar at
#: all. NOT 0, and not None-as-an-afterthought: it is a distinct
#: answer meaning "this channel has nothing to say", which is the
#: only honest reading below ten colonies.
NOT_DRAWN = "not_drawn"


def thumb_bounds(n_colonies, first):
    """(y1, y2) the original would draw for this state, or None.

    Transcribed from colsum.cpp:751-753, integer division included.
    None when `n < 10`, because the whole block is skipped.
    """
    n = int(n_colonies)
    if n < WINDOW:
        return None
    f = int(first)
    return ((271 * f) // n + 40, (271 * (f + WINDOW)) // n + 40)


def read_first(framebuffer, n_colonies, tolerance=1):
    """`_first` as the game is currently drawing it, or `NOT_DRAWN`.

    `framebuffer` is the 640x480 palette-index array the Extension
    API reports — indices, not RGB, so no palette is needed and the
    comparison is against the literal 229 the source fills with.

    Returns `NOT_DRAWN` when the bar is absent, which is both the
    `n < 10` case and any state where the screen is not the colony
    summary. Returns None when a run IS found but matches no
    candidate `_first`, which is a different answer again: the
    channel spoke and was not understood, and a caller must not treat
    that as a reading.

    The match is by SEARCH over the candidates rather than by
    inverting the formula. Two integer divisions do not invert
    cleanly, and every candidate's pair is one line to compute — so
    the reader agrees with the drawing by construction instead of by
    algebra.

    **`tolerance` IS TRANSCRIBED, NOT TUNED.** The borders at
    colsum.cpp:762-765 are drawn over the fill's own first and last
    row, so the 229 run is inset by exactly one row at each end and 1
    is the right allowance. A larger value is not safer: the thumb
    moves `271 / n` px per step of `_first`, so at tolerance 2 two
    candidates start fitting one run at **n = 136** (1.993 px per
    step) and the reader has to refuse. At tolerance 1 it is exact
    for every colony count from 10 to 259, which covers the engine's
    whole range — measured over all 1749 (n, `_first`) pairs in that
    span, each one rendered from `thumb_bounds` and read back.

    Two candidates fitting one run returns None rather than the
    nearer of them. None is not a reading: it means the channel spoke
    and was not understood, and a caller must stop rather than treat
    it as a value.
    """
    n = int(n_colonies)
    if n < WINDOW:
        return NOT_DRAWN
    rows = [y for y in range(len(framebuffer))
            if any(framebuffer[y][x] == THUMB_FILL
                   for x in range(THUMB_X0, THUMB_X1 + 1))]
    if not rows:
        return NOT_DRAWN
    lo, hi = min(rows), max(rows)
    best = None
    for candidate in range(0, max(0, n - WINDOW) + 1):
        y1, y2 = thumb_bounds(n, candidate)
        if abs(lo - y1) <= tolerance and abs(hi - y2) <= tolerance:
            if best is not None:
                # Two candidates fitting one run means the tolerance
                # is wider than the spacing; refuse rather than pick.
                return None
            best = candidate
    return best
