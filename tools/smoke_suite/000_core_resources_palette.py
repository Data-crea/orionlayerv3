# smoke-suite area: core
#
# Part of the OrionLayer smoke suite — 000_core_resources_palette.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 1 check(s) it holds:
#   - resources + palette

pygame.init()
pygame.display.set_mode((1920, 1080))

from core import resources, palette
from core.box import load_boxes
from core.config import load_settings, SCREENS_DIR
from core.layout import Layout
from core.style import StyleRenderer
from core.dispatcher import Dispatcher
from core.editor import Editor
from core.screens_loader import register_all, discover_screens

# ── Resources + palette ──
settings = load_settings()
settings["active_mods"] = ["example_mod"]
res = resources.init(settings)
assert res.shared("cursor.png")
assert res.skin_dir()
colors = res.load_json(
    f"assets/shared/skins/{res.skin}/colors.json", {})
palette.init(colors)
assert palette.col("select_race", "heading", (0, 0, 0)) != (0, 0, 0)
ok("resources + palette")
