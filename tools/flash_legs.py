"""The pre-game leg of `tools/flash_walk.py` — work order 180 A.

Split out so `flash_walk.py` stays under the 300-line guideline: the main
menu, New Game, Select Race, Empire Identity and Custom Race, each way
in and back out, through the HD window.
"""
import pygame

from core.hud import screenframe


def pregame(walk):
    """Main menu, New Game, Select Race, Empire Identity, Custom Race."""
    on = walk.run.on_screen
    walk.transition("startup -> main_menu", "main_menu",
                    lambda: None, on(10))
    walk.transition("main_menu -> new_game", "new_game",
                    lambda: walk.key(pygame.K_n), on(13))
    ng = walk.hd("new_game")
    walk.transition("new_game -> select_race", "select_race",
                    lambda: walk.click_rect(
                        screenframe.button_rect(ng, "right")), on(51))
    sr = walk.hd("select_race")
    walk.transition("select_race -> empire_identity", "empire_identity",
                    lambda: walk.click_rect(race_cell(sr, 0)))
    ei = walk.hd("empire_identity")
    walk.transition("empire_identity -> select_race", "select_race",
                    lambda: walk.click_rect(
                        screenframe.button_rect(ei, "left")), on(51))
    # Custom: the 14th cell puts the game in picture select (still
    # 51); a portrait then opens Racial_Option_Screen_ (50).
    walk.click_rect(race_cell(sr, 13))
    walk.settle(40)
    walk.transition("select_race -> custom_race", "custom_race",
                    lambda: walk.click_rect(race_cell(sr, 0)),
                    on(50))
    walk.transition("custom_race -> select_race", "select_race",
                    lambda: walk.key(pygame.K_ESCAPE), on(51))
    walk.transition("select_race -> new_game", "new_game",
                    lambda: walk.click_rect(
                        screenframe.button_rect(sr, "left")), on(13))
    walk.transition("new_game -> main_menu", "main_menu",
                    lambda: walk.click_rect(
                        screenframe.button_rect(ng, "left")), on(10))


def race_cell(sr, index):
    """A Select Race cell's window rect — the screen's own grid."""
    from screens.select_race.screen import grid_cell_rect
    gr = sr.box_rect("race_grid")
    cx, cy, cw, ch = grid_cell_rect(gr, index)
    sx, sy = sr.layout.pos(cx, cy)
    sw, sh = sr.layout.size(cw, ch)
    return (sx, sy, sw, sh)
