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

ONE HOME. Every rectangle of a slot comes from `Slot`, and the drawing
(`ldrdraw`), the words' dimmed ground (`ldrdraw.word_zones`), the skill
help's right click and the portrait's right click (`ldrinput`) all read it
(decision 5).
"""
import pygame

#: The text column's left edge: the name's and the icons' x (mockup slot
#: 1: the name's ink from x 419, the icons' frames from 420, box from 46).
TEXT_X = 0.403
#: Between the portrait column and the text column.
COLUMN_GAP = 0.015
#: The name: cap tops at 0.110 of the box (slot 2, 325 - 305 = 20 of 180;
#: slot 1 sets it at 0.160 with two skills — the denser slot is the one a
#: five-skill leader needs), capitals 0.094 tall (17 px in both slots, the
#: empty caption's title's height, `ldrdraw.CAPTION`).
NAME_TOP, NAME_CAP = 0.110, 0.094
#: The status line under the name (INVENTION `status_under_name`): the
#: cost label's small size raised to the empty caption's hint (0.066).
STATUS_GAP, STATUS_CAP = 0.032, 0.055
#: The cost at the top right: right edge 0.037 of the width in from the
#: box's (937 against 971 of 925), the value's capitals from 0.149 of the
#: height and 0.066 tall (147-158 in slot 1), the label's from 0.260 and
#: 0.044 tall ("MAINT", 167-174).
COST_RIGHT, COST_TOP, COST_CAP = 0.037, 0.149, 0.066
LABEL_TOP, LABEL_CAP = 0.260, 0.044
#: The skills: the name from 0.461 of the width (472 in slot 1), the value
#: column's right edge at 0.659 (656 and 653 in both slots), the words'
#: capitals 0.067 tall (12 px), an icon 0.15 of the height (27 px in slot
#: 2), the lines 0.156 apart (28 px in slot 2, four skills; 31 in slot 1).
SKILL_NAME_X, VALUE_RIGHT = 0.461, 0.659
SKILL_CAP, ICON, PITCH = 0.067, 0.150, 0.156
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
        """Where the portrait may stand: the panel's inner rect left of the
        text column, its full height."""
        right = self.x(TEXT_X - COLUMN_GAP)
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
        return self.px(min(ICON, self.pitch * ICON_OF_PITCH))

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
            out.append((line, pygame.Rect(self.text_x, y0, s, s), cy))
        return out

    @property
    def skill_name_x(self):
        return self.x(SKILL_NAME_X)


def value_right(slot, widest_name, widest_value):
    """The value column's right edge: the mockup's, moved right only as far
    as the widest skill name of the language needs (German's are longer)."""
    need = slot.skill_name_x + widest_name \
        + int(round(slot.box.w * VALUE_GAP)) + widest_value
    return max(slot.x(VALUE_RIGHT), need)
