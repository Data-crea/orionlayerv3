# smoke-suite area: main_menu
#
# Part of the OrionLayer smoke suite — 001_main_menu_mod_file_override_example_mod.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - mod file override (example_mod)
#   - discovery + game-ID map ( screens)


# ── Mod override ──
p = res.screen_file("main_menu", "assets", "credits.txt")
assert p and "example_mod" in p, p
base = res.screen_file("main_menu", "assets", "logo.png")
assert base and "example_mod" not in base
ok("mod file override (example_mod)")

# ── Discovery + dispatcher map ──
found = discover_screens(res)
assert "main_menu" in found and "select_race" in found, found

class FakeClient:
    class state:
        fields = []
    def activate_field(self, fid): pass
    def inject_click(self, x, y): pass
    def inject_key(self, k): pass

class FakeApp:
    win_w, win_h = 1920, 1080
    _fs_offset = None
    def __init__(self):
        self.res = res
        self.colors = colors
        # THE FAKE CARRIES WHAT THE REAL APP CARRIES. main.py:25
        # sets this and screens read it; a FakeApp without it
        # meant no screen could be tested through a settings-
        # driven branch at all — the same shape as the fake game
        # states that were missing MAP_MAX_Y.
        self.settings = settings
        self.layout = Layout(1920, 1080)
        self.style = StyleRenderer(res.skin_dir(), res.font(),
                                   colors)
        self.screens_dir = SCREENS_DIR
        self.connected = False
        self.client = FakeClient()
        self.dispatcher = Dispatcher()

app = FakeApp()
register_all(app, app.dispatcher, res)
d = app.dispatcher
assert d.screen_map.get(10) == "main_menu", d.screen_map
assert d.screen_map.get(13) == "new_game"
assert d.screen_map.get(51) == "select_race"
# 6 is the Races screen, which has no HD version: it falls back
# (decision 22) instead of routing to race selection (open fix 22).
assert d.screen_map.get(6) is None, d.screen_map.get(6)
ok(f"discovery + game-ID map ({len(d.screens)} screens)")
