"""The tractor beam's line while a unit glides — work order 398 (gap 4 of
`dev:doc/combat_effects_table.md`'s audit, work order 397).

TRANSCRIPTION `moving_tractor`: during a move the original redraws the line
of every tractor the moving unit holds, or is held by, in each pass
(`Move_Ship_`, cmbtmov1.cpp:246-272, 416-422; `Draw_Moving_Tractor_`,
cmbtspec.cpp:203-242): CMBTSFX 2 frame `(_ship_frame % 3) + 4` (the lasting
line is frame 6, `Draw_Continuing_Tractor_` :140-173), between the two
centres — the moving unit's at its exact pixel (`center_x`, `center_y` are the
pass's position), the other's at its cell (:208-221). The main screen's
continuing line is not drawn for a pair that includes the moving unit
(`i != dont_draw_ship`, `cooldown != dont_draw_ship`, cmbtdrw1.cpp:598-606,
1917-1926), so one line is seen, not two. A pass is `speed_px` along the
longer axis: 2 px, 12 under FAST ANIMATIONS (cmbtmov1.cpp:299-310), and
`_ship_frame` grows once a pass (:431-434).

HD STATE `tractor_phase`: `_ship_frame` is the game's one running counter, so
the frame the first pass draws is whatever it stood at; HD's passes count from
0 in each move (`cbplay` writes `_pass` on the gliding unit). HD's glide is a
continuous `t` over the move's time (decision H of work order 202), the pass
the original would be in is `int(t * passes)`.
UNVERIFIED `moving_tractor_live`: not seen in a running battle.
"""
from . import cbdraw

#: CMBTSFX 2's frames: the lasting line and the gliding line's first
LASTING, MOVING = 6, 4
#: px a pass moves (cmbtmov1.cpp:299-310)
PASS_PX, PASS_PX_FAST = 2, 12


def move_pass(dx, dy, t, fast):
    """The pass of a move of (`dx`, `dy`) px that the glide at `t` (0..1)
    is in: the longer axis over the pass's px, rounded up, is how many the
    original takes."""
    px = PASS_PX_FAST if fast else PASS_PX
    passes = max(1, -(-int(max(abs(dx), abs(dy))) // px))
    return max(0, min(passes - 1, int(t * passes)))


def frame_of(unit):
    """CMBTSFX 2's frame of a line touching `unit`: the gliding frames
    `(_ship_frame % 3) + 4` while it moves, else the lasting 6."""
    if "_pass" in unit:
        return MOVING + int(unit["_pass"]) % 3
    return LASTING


def centre_at(unit):
    """A unit's end of the line (world px): its cell's centre, plus the
    glide's offset while it is the one moving (`_pass` set)."""
    cx, cy = cbdraw.centre(unit)
    if "_pass" in unit:
        dx, dy = unit.get("_off", (0, 0))
        return int(cx + dx), int(cy + dy)
    return int(cx), int(cy)


def line(holder, held):
    """(from, to, frame) of the line between a holder and the unit it
    holds: the gliding frame when either of them moves."""
    mover = holder if "_pass" in holder else held
    return centre_at(holder), centre_at(held), frame_of(mover)
