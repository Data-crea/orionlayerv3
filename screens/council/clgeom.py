"""The galactic council's geometry — work order 270.

The original draws one 640 x 480 chamber (COUNCIL.LBX's animation 1, a
file animation) with the members' portraits round the hall, the two
nominees standing in front, three lines along the top and the message
along the foot (`Draw_Main_Council_Screen`, council.cpp:148-211). HD puts
what it says into the screen shell's content rectangle:

  cl_top       the three top lines: nominee 0's, the total's, nominee 1's
               (printed at (30, 30), centred at (320, 30) and at (451, 30))
  cl_nominee_a nominee 0 (drawn at (115, 225)), left
  cl_members   the members, voting order (the original's portraits at its
               six places, the one voting lit), middle
  cl_nominee_b nominee 1 (drawn at (320, 225)), right
  cl_message   the message (`_Print_Paragraph_` at (55, 470 - h), 550
               wide) and, while the game asks, its list (`Get_List_Field_`
               at (214, 388), 180 wide): the vote, the ruling

HD EXTENSION `shell` (decisions 86-90); DEVIATION `no_chamber`: the hall,
the portraits and their animation are not drawn — the members and nominees
are named rows and panels in their players' colours.
"""
import pygame

TOP, NOMINEE_A, MEMBERS, NOMINEE_B, MESSAGE = (
    "cl_top", "cl_nominee_a", "cl_members", "cl_nominee_b", "cl_message")
PANELS = (TOP, NOMINEE_A, MEMBERS, NOMINEE_B, MESSAGE)
#: The bands' heights as shares of the rectangle: the top lines, the hall,
#: the message with its list.
BANDS = (0.10, 0.52, 0.38)
#: The hall's three panels across: the nominees narrower than the members.
HALL = (1.0, 1.3, 1.0)


def shell_boxes(layout):
    """{box name: (x, y, w, h)}: the shell's cut of the content rectangle
    (no button row: the council has no button of its own)."""
    from core.hud import shell
    area = shell.panels(layout, row=False)
    top, hall, message = shell.split(area, layout, list(BANDS),
                                     vertical=True)
    a, members, b = shell.split(hall, layout, list(HALL))
    return {TOP: tuple(top), NOMINEE_A: tuple(a), MEMBERS: tuple(members),
            NOMINEE_B: tuple(b), MESSAGE: tuple(message)}


def rect(t):
    return pygame.Rect(t)
