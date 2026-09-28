#!/usr/bin/env python3
"""Renders of every HD screen in the HUD style, for Data to look at.

    python tools/hud_evidence.py                     # all, 3 sizes
    python tools/hud_evidence.py galaxy_map --size 1920x1080
    python tools/hud_evidence.py --mockups           # + side by sides

Work order 169's evidence: every screen at 1080p, 1440p and 2160p, and
the galaxy map and the colony summary beside Data's mockups. Written to
`~/orionlayer-fixtures/evidence/work_order_169/`. Pictures, not findings
— what they are FOR is the list in `doc/briefs/169-progress.md`.

**OFFLINE, AND SAYS SO.** No game runs here. Each screen gets the state
the smoke suite's own fixtures give it — a synthetic galaxy of forty
named stars, the colony preview's eight colonies (`colony_list_preview`),
the recorded GAME menu field list — or none, and a screen that needs a
live game to show content shows its empty state. Every file name says
`offline`, so no render can be mistaken for a live capture.
"""
import argparse
import json
import os
import random
import struct
import sys

# Work order 182: SDL's dummy drivers FORCED, never a window or a sound in
# the user's session (a setdefault lost to an exported SDL_VIDEODRIVER).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vdisplay  # noqa: E402
import standins  # noqa: E402
from design_fixture import state as design_state  # noqa: E402,F401
vdisplay.headless_clients()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

OUT = os.path.expanduser("~/orionlayer-fixtures/evidence/work_order_169")
SIZES = [(1920, 1080), (2560, 1440), (3840, 2160)]
MOCKUPS = {"galaxy_map": os.path.join(ROOT, "doc", "briefs",
                                      "169-mockup-galaxy.png"),
           "select_race": os.path.join(ROOT, "doc", "briefs",
                                       "174-mockup-select-race.png"),
           "colony_summary": os.path.expanduser(
               "~/Downloads/colony_screen.png")}

STAR_NAMES = ["Poculum", "Cephee", "Revati", "Zak", "Obelus", "Dante",
              "Thaur", "Inak", "Galileo", "Draconis", "Zin", "Hamete",
              "Goi", "Tond", "Hase", "Ascellus", "Habor", "Zhadoom",
              "Hammis", "Zib", "Gorgonis", "Beta Ceti", "Taq", "Lemuria",
              "Mirak", "Sal", "Kae", "Kadath", "Helios", "Orion",
              "Ivielda", "Tal", "Kyusho", "Lawdon", "Min", "Lurnis",
              "Hircus", "Castor", "Hali", "Sahu"]


def make_app(width, height):
    """The real screens, on an app-shaped host (colony_list_preview's
    pattern, generalised to every screen)."""
    pygame.init()
    pygame.display.set_mode((64, 64))
    from core import palette, resources
    from core.config import SCREENS_DIR, load_settings
    from core.dispatcher import Dispatcher
    from core.layout import Layout
    from core.screens_loader import register_all
    from core.style import StyleRenderer
    settings = load_settings()
    res = resources.init(settings)
    colors = res.load_json(f"assets/shared/skins/{res.skin}/colors.json",
                           {}) or {}
    palette.init(colors)

    class _Client:
        class state:
            fields = []

        def activate_field(self, fid):
            pass

        def inject_click(self, x, y):
            pass

        def inject_key(self, key):
            pass

        def send_raw(self, *a, **k):
            pass

    class _App:
        _fs_offset = None

        def __init__(self):
            self.win_w, self.win_h = width, height
            self.res = res
            self.colors = colors
            self.settings = settings
            self.layout = Layout(width, height)
            self.style = StyleRenderer(res.skin_dir(), res.font(), colors)
            self.screens_dir = SCREENS_DIR
            self.connected = False
            self.client = _Client()
            self.dispatcher = Dispatcher()
            # The DEFAULTS, as a fresh install has them — a bare dict
            # answered None for every key and the settings rows drew
            # blank values (found in work order 173's renders). Never
            # saved: the path names no file this tool writes.
            from core import usersettings
            self.user_settings = usersettings.UserSettings(
                path=os.devnull)

    app = _App()
    register_all(app, app.dispatcher, res)
    return app


def galaxy_state():
    """Forty stars, a nebula and the player record the mockup shows."""
    from core.game_state import GameState, PLAYER_SIZE, STAR_SIZE
    from core.structs import star as st
    rng = random.Random(169)
    raws = []
    for i, name in enumerate(STAR_NAMES):
        r = bytearray(STAR_SIZE)
        r[0:len(name)] = name.encode()
        struct.pack_into("<hh", r, 15, 40 + (i % 8) * 88 + rng.randint(-20, 20),
                         40 + (i // 8) * 110 + rng.randint(-25, 25))
        r[19] = rng.randint(0, 2)
        struct.pack_into("<b", r, 20, 0 if i in (3, 9, 13, 14) else -1)
        r[22] = rng.randint(0, 5)
        struct.pack_into("<h", r, 160, -1)
        r[171] = 1
        raws.append(bytes(r))
    gs = GameState()
    gs.current_screen = 0
    gs.player_num = 0
    gs.map_scale, gs.map_max_x, gs.map_max_y = 15, 759, 600
    gs.stars = st.parse_all(raws)
    p = bytearray(PLAYER_SIZE)
    p[38] = 2
    struct.pack_into("<i", p, 50, 304)
    struct.pack_into("<h", p, 58, 47)
    struct.pack_into("<h", p, 60, 19)
    struct.pack_into("<h", p, 276, -11)
    gs.player_raw = [bytes(p)] + [bytes(PLAYER_SIZE)] * 7
    gs.nebulas_raw = [struct.pack("<hhb", 374, 170, 1)]
    gs.stardate = 35004
    return gs


def colony_state():
    import colony_list_preview as clp
    return clp._Snapshot(clp.COLONIES) if hasattr(clp, "COLONIES") else None


def new_game_state():
    """A setting for each of the five pictures, two toggles on."""
    class _S:
        pass
    gs = _S()
    for a, v in dict(ng_difficulty=1, ng_galaxy_size=1, ng_galaxy_age=1,
                     ng_opponents=3, ng_tech_level=1, ng_tactical_combat=1,
                     ng_random_events=0, ng_antarans=1,
                     current_screen=13).items():
        setattr(gs, a, v)
    return gs


def game_menu_state(node="menu"):
    from core.game_state import GameState

    class _F:
        pass
    fix = json.load(open(os.path.join(ROOT, "tools", "game_menu_fields.json")))
    gs = GameState()
    gs.current_screen = 8
    fields = []
    for row in fix[node]:
        f = _F()
        (f.index, f.x, f.y, f.x_end, f.y_end, f.field_type, f.hotkey) = row
        fields.append(f)
    gs.fields = fields
    return gs


def stage(app, name):
    """Put `name` on screen with its offline state; return the state."""
    d = app.dispatcher
    # THE POPUPS an offline state can open (work order 174's inventory):
    # a help entry over the galaxy map, Custom Race's message box.
    if name == "help_popup":
        d.switch_to("galaxy_map")
        gs = galaxy_state()
        d.active.update(gs)
        d.active.help.open("inventory", "Help",
                           "A help entry, as the popup draws one. " * 12)
        return gs
    if name == "custom_race_message":
        d.switch_to("custom_race")
        d.active.update(None)
        d.active._popup.open("You have spent more picks than you have. "
                             "Remove some before you accept.")
        return None
    if name == "game_menu" or name.startswith("game_menu_"):
        d.switch_to("galaxy_map")
        d.active.update(galaxy_state())
        node = name[len("game_menu_"):] if name != "game_menu" else "menu"
        gs = game_menu_state(node)
        # The settings record the suite's GAME menu fixture uses (070).
        from core.structs import settings as _set
        gs.settings_raw = bytes([1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0,
                                 0, 0, 0, 1, 50, 1, 49, 7]) + bytes(
                                     _set.SIZE - 22)
        d.update_from_game(gs)
        d.overlay.update(gs)
        return gs
    if name in standins.STAND_INS:
        return standins.stage(app, name)
    d.switch_to(name)
    gs = {"galaxy_map": galaxy_state, "colony_summary": colony_state,
          "new_game": new_game_state}.get(name, lambda: None)()
    d.active.update(gs)
    return gs


def render(name, width, height):
    app = make_app(width, height)
    stage(app, name)
    surf = pygame.Surface((width, height))
    d = app.dispatcher
    d.active.render(surf)
    if d.overlay_name:
        d.screens[d.overlay_name].render(surf)
    return surf


def side_by_side(hd, mockup_path):
    from PIL import Image
    m = Image.open(mockup_path).convert("RGB")
    h = 1080
    m = m.resize((round(m.width * h / m.height), h), Image.LANCZOS)
    raw = pygame.image.tostring(hd, "RGB")
    a = Image.frombytes("RGB", hd.get_size(), raw).resize(
        (round(hd.get_width() * h / hd.get_height()), h), Image.LANCZOS)
    out = Image.new("RGB", (a.width + m.width + 20, h), (90, 200, 90))
    out.paste(a, (0, 0))
    out.paste(m, (a.width + 20, 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("screens", nargs="*")
    ap.add_argument("--size", help="WxH, default all three")
    ap.add_argument("--mockups", action="store_true")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--hue", type=float, default=None,
                    help="the HUD frame colour to render in (degrees); "
                         "file names then carry it")
    ap.add_argument("--sat", type=float, default=None,
                    help="the frame colour's saturation factor, 0..1")
    ap.add_argument("--bright", type=float, default=None,
                    help="the frame colour's brightness factor, 0.1..1.6")
    ap.add_argument("--tag", default=None,
                    help="a name for the colour in the file names")
    ap.add_argument("--glass", type=float, default=None,
                    help="the Panel glass slider, 0 see-through .. 1 solid "
                         "(work order 174); file names then carry it")
    ap.add_argument("--corner-lines", action="store_true",
                    help="draw the glass's optional inner corner lines")
    args = ap.parse_args()
    from core.hud import glass as hudglass
    from core.hud import style as hudstyle
    hudstyle.set_tone(args.hue, args.sat, args.bright)
    if args.corner_lines:
        hudstyle.get().chosen["glass"]["corner_lines"] = True
    if args.glass is not None:
        hudglass.set_value(args.glass)
    tag = ("" if args.hue is None else f"_hue{int(args.hue):03d}")
    if args.tag:
        tag = f"_{args.tag}"
    if args.glass is not None:
        tag += f"_glass{args.glass:.2f}"
    if args.corner_lines:
        tag += "_corners"
    os.makedirs(args.out, exist_ok=True)
    sizes = ([tuple(int(v) for v in args.size.split("x"))] if args.size
             else SIZES)
    names = args.screens or sorted(
        n for n in os.listdir(os.path.join(ROOT, "screens"))
        if os.path.isfile(os.path.join(ROOT, "screens", n, "screen.py"))
        and not n.startswith("_"))
    for name in names:
        for w, h in sizes:
            surf = render(name, w, h)
            path = os.path.join(args.out,
                                f"{name}_{w}x{h}{tag}_offline.png")
            pygame.image.save(surf, path)
            print(path)
            if args.mockups and (w, h) == (3840, 2160) and name in MOCKUPS \
                    and os.path.exists(MOCKUPS[name]):
                sbs = side_by_side(surf, MOCKUPS[name])
                p = os.path.join(args.out, f"{name}_beside_mockup_offline.png")
                sbs.save(p)
                print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── SCALED ONCE (work order 182, part 4) ──────────────────────────────
#
# The fault of 179 and 182 — the window's factor applied twice, 4x at 2160p
# where 2x is proportional — lives in arithmetic (`box_font_scale` into
# `Layout.font_size`, a `win_h / 1080` into a reference-space helper) that
# a pattern cannot follow across modules. So it is measured where it lands:
# every font size a render asks for, attributed to the first caller outside
# the shared text helpers (a fitting loop's trials belong to its caller),
# at 1920x1080 and at 3840x2160. Per call site the largest size at 3840 may
# not exceed twice the largest at 1920 (+2 for rounding): scaled once is 2x,
# scaled twice is 4x. Fewer is allowed — a capped size, a measuring font —
# and is not what this is about.
TEXT_HELPERS = ("core/style.py", "core/textfit.py", "core/hud/text.py",
                "screens/leaders/ldrdraw.py")
#: Helper FUNCTIONS in a screen's own drawing module that every string of
#: the screen passes through: walked past like the files above, so a size
#: is charged to the line that chose it, not to the one helper they share.
TEXT_HELPER_FUNCTIONS = {("screens/colony/coldraw.py", "text"),
                         ("screens/colony/coldraw.py", "lines")}


def font_sites(style, render):
    """{(file, line): largest size} of the fonts `render()` asks `style`
    for, by the first caller outside TEXT_HELPERS."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seen = {}
    real = (style.get_font, style.get_prop_font)

    def rec(fn):
        def inner(size, *a, **k):
            f = sys._getframe(1)
            while f is not None and (
                    os.path.relpath(f.f_code.co_filename, root) in TEXT_HELPERS
                    or (os.path.relpath(f.f_code.co_filename, root),
                        f.f_code.co_name) in TEXT_HELPER_FUNCTIONS):
                f = f.f_back
            key = (os.path.relpath(f.f_code.co_filename, root), f.f_lineno) \
                if f is not None else ("?", 0)
            seen[key] = max(seen.get(key, 0), int(size))
            return fn(size, *a, **k)
        return inner
    style.get_font, style.get_prop_font = rec(real[0]), rec(real[1])
    try:
        render()
    finally:
        style.get_font, style.get_prop_font = real
    return seen


def scaled_twice(small, large, factor=2):
    """The call sites whose largest size at the large window exceeds
    `factor` times the one at the small window (+2): {site: (a, b)}."""
    return {k: (small[k], v) for k, v in large.items()
            if k in small and v > factor * small[k] + 2}


def same_boxes(section="1920x1080"):
    """Load every screen's boxes from ONE resolution section, so a size
    measured at two windows differs only by code — not by the per-
    resolution `font_scale` Data tunes with F5 (colony summary's
    `planet_paragraph` is 1.6 in 2560x1440, the section 3840 falls back to).
    Returns the function that undoes it."""
    from core import box as _box
    from core import screen_base as _sb
    real = _box.load_boxes
    w, h = (int(v) for v in section.split("x"))
    fixed = lambda source, win_w=1920, win_h=1080: real(source, w, h)  # noqa
    # `screen_base` binds the name at import; both homes are replaced.
    _box.load_boxes = _sb.load_boxes = fixed

    def undo():
        _box.load_boxes = _sb.load_boxes = real
    return undo
