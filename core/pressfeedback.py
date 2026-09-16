"""The pressed state of a clickable word — work order 124, item B.

TRANSCRIBED for picture buttons. While a button field is held down,
`fields::Draw_Field_` draws frame 1 of the field's own picture
(`Set_Animation_Frame_(pic, 1)`, fields.cpp:2710-2717), and the confirmation
box does the same for YES and NO (`Draw_Confirm_Box_`, gendraw.cpp:35-49).
In every picture this covers — BUFFER0.LBX 1 (the galaxy map's GAME
button), GAME.LBX 1-6, 10, 12, 13, 15 (the menu's buttons), CONFIRM.LBX 1-2
— frame 1 is the same word in ORANGE, palette index 126 = (252, 136, 0)
through the main screen's palette, measured 16 September 2026. It lasts as
long as the press does, and moving off the field ends it
(`Push_Field_Down_`, fields.cpp:1387-1412). HD draws the word in
`button.pressed_text` for exactly that span.

OMISSION: the pressed pictures also move the word by about one or two native
pixels in the menu buttons (none on GAME); it could not be measured cleanly
against the bevel shadows, so HD does not move it.

HD INVENTION — the load and save ROWS. They are hidden fields
(loadsave.cpp:263, :279) and `_Draw_Load_Save_Game_Popup_` colours a row by
`active_save_slot` alone (loadsave.cpp:852-878): the original shows nothing
on a pressed row. HD gives a pressed row the same orange, because Data wants
every click in the menu tree to show that it landed (work order 124 B).
Marked here, in the status document and in the smoke test.

The feedback is drawn in HD and never waits for the game: it starts on the
press, whether or not anything is sent, and a refusal is drawn as it always
was (decision 33).

Not the 9-slice frame's side-button flash in `core/screen_base.py`
(`BTN_FLASH_*`): that one is a timed blue overlay on the old frame's two
buttons and has no counterpart here. Two feedback mechanisms, not three.
"""
from core import mouse as mouse_input
from core import palette

_PRESSED = []


def pressed_colour():
    """`button.pressed_text`, read on first use: this module is imported by
    `core/screen_base.py`, which loads before `App` initialises the palette,
    so a module-level `require` would run against an empty skin."""
    if not _PRESSED:
        _PRESSED.append(palette.require("button", "pressed_text"))
    return _PRESSED[0]


class Pressed:
    """One held press per screen: a name and the rect it was pressed in."""

    def __init__(self):
        self.name = None
        self.rect = None

    def press(self, name, rect):
        self.name, self.rect = name, rect

    def release(self):
        self.name = self.rect = None

    def is_down(self, name):
        """Held on `name` with the pointer still inside its rect."""
        return (name is not None and self.name == name
                and self.rect is not None
                and self.rect.collidepoint(mouse_input.pos()))

    def colour(self, name, normal):
        return pressed_colour() if self.is_down(name) else normal
