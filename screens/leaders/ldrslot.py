"""One leader slot laid out after Data's mockup — work order 255, Part B.

WHAT THE ORIGINAL DOES. `Print_Officer_Data_` (officer.cpp:3578-3838) prints
a row at native places (`ldrgeom`): the 73 x 88 portrait in a 75 x 90 cell
at the left, the name centred in 160 px, the two cost lines in the right
column, one line per skill (icon, name, bonus) stepping 17 px, the status
line under the portrait. The WORDS and the RULES stay the original's
(`ldrrows`: the name with its title, the two cost alignments, the red "For
Hire", the ETA, which skills in which order).

WHAT HD DOES — DEVIATION `mockup_slot`. The slot is the HD row box
(`ldrdraw.row_box`, WO 238's margins) and everything in it is placed at a
fraction of that box measured off Data's mockup (`Mockup.png`, 11 October
2026, the picture work orders 237 and 255 name; its slot 1 is 925 x 181 at
(46, 120), slot 2 925 x 180 at (46, 305), measured for work order 255 by
the ink of each line): the portrait large on the left, standing on the
box's floor in front of the slot's picture; the name at the top of a text
column; the cost at the top right; one skill per line as icon, name and
value, the value right-aligned in a column of its own. The status line the
original prints under the portrait stands under the name (the mockup has
none — INVENTION `status_under_name`, the order's own suggestion). The ETA
stays over the portrait, as the original prints it (:3742-3745).

SINCE WORK ORDER 278 the text column follows Data's second mockup
(`~/claude/references/leaders_skills_mockup_278.png`, 726 x 872, the left
half of a 1080p Leaders screen: its slot 1 spans y 56-258 from x 11, HD's
slot 1 at 1920x1080 is 1079 x 206 from x 28 — positions below are the
mockup's ink, taken from its slot's left edge and scaled by 206 / 202):
the name, the status line and the skills further left and the skill block
compact, the value column close after the names, the name a little higher
and smaller; the skill lines' heights were already the mockup's.

ONE HOME. Every rectangle of a slot comes from `Slot`, and the drawing
(`ldrdraw`), the words' dimmed ground (`ldrdraw.word_zones`), the skill
help's right click and the portrait's right click (`ldrinput`) all read it
(decision 5).
"""
import pygame

#: The text column's left edge: the name's and the status line's x (mockup
#: 2: the name's ink from x 387 — (387 - 11) * 1.02 = 383 of 1079 = 0.355),
#: moved left by TEXT_SHIFT since 16 Oct 2026 (Data: half the space
#: between the portrait and the words).
TEXT_X = 0.312
#: The space between a skill icon and its name: 8 px of a 206 px slot at
#: 1920x1080 (Data's readability test of 16 Oct 2026; the icon's left
#: edge follows from it — was ICON_X, mockup 2's x 396, 0.364 before the
#: shift).
ICON_GAP = 0.039
#: 16 Oct 2026's shift of the whole text column: half the median space
#: between a portrait's ink and the name, measured over all 67 portraits
#: at 1920x1080 (93 px of a 1079 px slot — 0.086; half is 0.043). The
#: portraits stay where they stood: their column keeps its right edge.
TEXT_SHIFT = 0.043
#: The portrait column's right edge (mockup 2's text column less its
#: 0.015 gap). It no longer follows TEXT_X: the column's clear right part
#: now lies under the name and the skill icons, short of the skills'
#: words — the widest figure's ink (ship officer 52) reaches 4 px past
#: TEXT_X at 1080p, at its foot, 6 px short of the icons.
PORTRAIT_RIGHT = 0.340
#: The name: cap tops at 0.084 of the box, capitals 0.086 tall (mockup 2:
#: ink from y 73 in the slot from y 56 — 17 of 202 — and 17 px tall;
#: work order 255's mockup had 0.110 and 0.094).
NAME_TOP, NAME_CAP = 0.084, 0.086
#: The status line under the name (INVENTION `status_under_name`), in
#: capitals since work order 278 (mockup 2: "OFFIZIERSSTAB", cap tops at
#: y 103 = 0.233 of the slot, 9 px of ink at the mockup's scale — 0.052
#: holds its look beside the rendered capitals, measured side by side).
STATUS_GAP, STATUS_CAP = 0.063, 0.052
#: The cost at the top right: right edge 0.037 of the width in from the
#: box's (937 against 971 of 925), the value's capitals from 0.149 of the
#: height and 0.066 tall (147-158 in slot 1), the label's from 0.260 and
#: 0.044 tall ("MAINT", 167-174).
COST_RIGHT, COST_TOP, COST_CAP = 0.037, 0.149, 0.066
LABEL_TOP, LABEL_CAP = 0.260, 0.044
#: The skills: the name from 0.410 of the width (mockup 2: x 445), the
#: value column's right edge at 0.617 (x 664), both less TEXT_SHIFT since
#: 16 Oct 2026 — the compact block of work
#: order 278; the words' capitals 0.062 tall (mockup 2: 12 of 202), an
#: icon 0.150 of the height at most (mockup 2's five lines: 22 px, which
#: the closed-up pitch gives), the lines 0.156 apart, closed up to 0.124 at
#: five (mockup 2: 25 px).
SKILL_NAME_X, VALUE_RIGHT = 0.367, 0.574
#: Data's readability test of 16 Oct 2026: every icon 26 x 26 at
#: 1920x1080 (26 of a 206 px slot), at every skill count but never taller
#: than its line — was 0.150, closed to ICON_OF_PITCH of the line at five.
#: The lines' pitch is kept.
SKILL_CAP, ICON, PITCH = 0.062, 0.126, 0.156
#: An icon takes at most this share of its line's pitch.
ICON_OF_PITCH = 0.95
#: Where the skill block may run: from under the status line to the
#: slot's floor. The original's limit is five lines (`ldrgeom.
#: SKILL_HELP_MAX`): at five the lines close up and the icons shrink.
SKILLS_TOP, SKILLS_BOTTOM = 0.330, 0.950
#: The value column keeps this gap, a share of the width, after the
#: widest skill name (mockup slot 1: "Navigator" ends at 555, "+1" starts
#: at 636 — 0.088; the gap only matters where a language needs more).
VALUE_GAP = 0.020


class Slot:
    """The window rectangles of one slot, for a box and a skill count."""

    def __init__(self, box, inner, n_skills, values_right=None):
        self.box = pygame.Rect(box)
        self.inner = pygame.Rect(inner)
        self.n = max(0, int(n_skills))
        self.values_right = values_right if values_right is not None \
            else self.x(VALUE_RIGHT)

    def x(self, f):
        return self.box.x + int(round(self.box.w * f))

    def y(self, f):
        return self.box.y + int(round(self.box.h * f))

    def px(self, f):
        return max(1, int(round(self.box.h * f)))

    @property
    def text_x(self):
        return self.x(TEXT_X)

    @property
    def portrait_column(self):
        """Where the portrait may stand: the panel's inner rect up to
        PORTRAIT_RIGHT, its full height."""
        right = self.x(PORTRAIT_RIGHT)
        return pygame.Rect(self.inner.x, self.inner.y,
                           max(1, right - self.inner.x), self.inner.h)

    def portrait_rect(self, size):
        """A picture of `size` standing on the column's floor, centred."""
        col = self.portrait_column
        r = pygame.Rect((0, 0), size)
        r.midbottom = col.midbottom
        return r

    @property
    def name_top(self):
        return self.y(NAME_TOP)

    @property
    def status_top(self):
        return self.y(NAME_TOP + NAME_CAP + STATUS_GAP)

    @property
    def cost_right(self):
        return self.box.right - int(round(self.box.w * COST_RIGHT))

    @property
    def pitch(self):
        """The skill lines' step: the mockup's, closed up so that `n`
        lines with their icons end on the slot's floor."""
        if self.n <= 1:
            return PITCH
        room = SKILLS_BOTTOM - SKILLS_TOP
        return min(PITCH, room / (self.n - 1 + ICON_OF_PITCH))

    @property
    def icon(self):
        """ICON, never taller than its line (at five lines and 2560x1440
        the rounding would make it 35 px in a 34 px line)."""
        return min(self.px(ICON), max(1, int(round(self.box.h * self.pitch))))

    def skill_lines(self):
        """[(line Rect, icon Rect, text centre y)] top down: the line from
        the icon's left to the value column, one pitch tall."""
        pitch = self.box.h * self.pitch
        top = self.box.y + self.box.h * SKILLS_TOP
        s = self.icon
        out = []
        for k in range(self.n):
            y0 = int(round(top + k * pitch))
            cy = y0 + s // 2
            line = pygame.Rect(self.text_x, int(round(cy - pitch / 2)),
                               self.values_right - self.text_x,
                               max(1, int(round(pitch))))
            out.append((line, pygame.Rect(self.skill_name_x
                                          - self.px(ICON_GAP) - s, y0, s, s),
                        cy))
        return out

    def skill_block(self, pad):
        """The skill list's shared ground: from the first icon's left to
        the value column's right edge, the first line's top to the last
        line's bottom, `pad` px round it (None without skills)."""
        lines = self.skill_lines()
        if not lines:
            return None
        top = min(min(l.top, i.top) for l, i, _cy in lines)
        bottom = max(max(l.bottom, i.bottom) for l, i, _cy in lines)
        left = min(i.left for _l, i, _cy in lines)
        return pygame.Rect(left, top, self.values_right - left,
                           bottom - top).inflate(2 * pad, 2 * pad)

    @property
    def skill_name_x(self):
        return self.x(SKILL_NAME_X)

    @property
    def text_area(self):
        """Where the words stand, for the shade behind them
        (`ldrpics.text_shade`, work order 286): from the name's x to the
        value column, the name's top to the last skill line's foot (the
        status line's without skills)."""
        bottom = self.status_top + self.px(STATUS_CAP)
        block = self.skill_block(0)
        if block is not None:
            bottom = max(bottom, block.bottom)
        top = self.name_top
        return pygame.Rect(self.text_x, top, self.values_right - self.text_x,
                           max(1, bottom - top))


def value_right(slot, widest_name, widest_value):
    """The value column's right edge: the mockup's, moved right only as far
    as the widest skill name of the language needs (German's are longer)."""
    need = slot.skill_name_x + widest_name \
        + int(round(slot.box.w * VALUE_GAP)) + widest_value
    return max(slot.x(VALUE_RIGHT), need)
