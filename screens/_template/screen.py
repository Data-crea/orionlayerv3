"""Screen Template — copy this folder to create new screens.

1. Copy folder:  cp -r screens/_template screens/my_screen
2. Set SCREEN_NAME = "my_screen" (must match the folder name)
3. Set GAME_SCREEN_ID if orion2re should auto-switch to this
   screen (see SCREEN enum in the orion2re index doc), or leave
   it at None for sub-screens opened via dispatcher.switch_to().
4. Edit boxes.json (F3 editor in-game).
5. Optional files, as the real screens carry them (see
   screens/research_change/ for a small complete one): layout.json
   (geometry), help.json (right-click help) and box_labels.json. The
   boxes.json written by the F3 editor is a dict keyed by resolution,
   e.g. "1920x1080"; this template's list form is the legacy one the
   loader still reads.
6. Beyond the folder, a screen is also named in the status-bar names
   (core/screen_names.py), has a smoke-check group and a state file
   (dev:doc/state/<screen>.md).

Screens are auto-discovered, no registration is needed in the loader.
This also works from inside a mod: put the same folder structure
under mods/<your_mod>/screens/my_screen/.

Conventions:
  - Load assets via self.asset_path("assets", "file.png") so
    mods can override them.
  - Load data via self.app.res.load_json("screens/my_screen/...").
  - Get colors via palette.col("my_screen", "key", default) and
    document them in the skin's colors.json.
  - Folders starting with "_" are ignored by discovery.
"""
from core.screen_base import ScreenBase


class TemplateScreen(ScreenBase):
    SCREEN_NAME = "_template"
    GAME_SCREEN_ID = None   # orion2re screen ID, or None (sub-screen)
    IS_OVERLAY = False      # True -> popup ABOVE the active screen
                            # (parent keeps rendering; OVERLAY_DIM
                            # darkens it; auto-closes when the game
                            # leaves GAME_SCREEN_ID)
    USE_FRAME = False       # True -> HUD title plate + frame buttons
    FRAME_TITLE = ""        # title bar text when USE_FRAME

    def enter(self, game_state=None):
        super().enter(game_state)   # boxes, layout, background

    def update(self, game_state=None):
        pass                        # per-frame data update

    def render(self, surface):
        super().render(surface)     # background, boxes, frame

    def handle_click(self, screen_x, screen_y):
        # Base handles frame buttons + boxes with field_ids.
        return super().handle_click(screen_x, screen_y)

    def handle_key(self, key):
        super().handle_key(key)     # forwards to orion2re
