#!/usr/bin/env python3
"""Drive the GAME menu by CLICKING THE HD OVERLAY, and prove where it landed.

    python tools/game_menu_hd.py walk      # every node, side by side with native
    python tools/game_menu_hd.py esc       # ESC at every level
    python tools/game_menu_hd.py help      # right click on every region
    python tools/game_menu_hd.py toggle    # one checkbox on, ESC, off again
    python tools/game_menu_hd.py probe     # native: a key BURST into a name, then ESC
    python tools/game_menu_hd.py save NAME # save to slot 10 through HD
    python tools/game_menu_hd.py load      # load slot 10 through HD
    python tools/game_menu_hd.py quit      # QUIT -> YES: game and client end

The real `main.App`, headless, real pygame events through the front door
(the colony tool's shape, and its helpers — not a copy of them). Every
wait is on the dialog's field-list shape, `nodes.classify`.

**THE SAVE-FILE RULE, Data's, 14 September 2026**, runs around every step:
SAVE1-SAVE9 are hashed before and after and must be identical; SAVE10 —
the autosave, rewritten at every turn end and on every popup exit — has
its hash and mtime LOGGED and never compared. Save and load use slot 10
only. The step names the loaded game by fixture, or says it is none.

Output goes OUTSIDE the tree: pictures of the player's game are the
player's data (decision 42, the fixtures README).
"""
import hashlib
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

# THE PALETTE BEFORE ANY SCREEN MODULE (decision 14, `palette.require`
# reads at import); `toolenv` is the one home since work order 126 D.
import toolenv  # noqa: E402
toolenv.init_palette()

from colony_move_hd import (Counter, click_at, native_png,  # noqa: E402
                            pump, wait_for)
from fixtures import fixture_name  # noqa: E402
from screens.game_menu import gmdraw, nodes  # noqa: E402

GAME_DIR = os.path.expanduser("~/Master of Orion 2")
EVIDENCE = os.path.expanduser("~/orionlayer-fixtures/evidence/game_menu")
OUT = os.path.join(EVIDENCE, "hd_live")


def save_rule():
    def sha(n):
        p = os.path.join(GAME_DIR, f"SAVE{n}.GAM")
        return hashlib.sha256(open(p, "rb").read()).hexdigest() if \
            os.path.exists(p) else None
    s10 = os.path.join(GAME_DIR, "SAVE10.GAM")
    return ({n: sha(n) for n in range(1, 10)},
            (sha(10), os.path.getmtime(s10) if os.path.exists(s10) else None))


def report_rule(before, after):
    same = before[0] == after[0]
    print(f"  SAVE1-9 identical before/after: {same}")
    print(f"  SAVE10 before {str(before[1][0])[:16]} mtime {before[1][1]}")
    print(f"  SAVE10 after  {str(after[1][0])[:16]} mtime {after[1][1]}")
    return same


def overlay(app):
    return app.dispatcher.overlay if app.dispatcher.overlay_name == \
        "game_menu" else None


def node_is(app, name):
    ov = overlay(app)
    return ov is not None and ov.node == name


def centre(app, box_name):
    r = gmdraw.rect(overlay(app), box_name)
    return r.center


def click_box(app, box_name, expect, label):
    click_at(app, *centre(app, box_name))
    return wait_for(app, lambda: node_is(app, expect), 30.0, label)


def key(app, code, char=""):
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN, {"key": code, "unicode": char, "mod": 0}))
    pump(app, 2)


def row_centre(app, box_name, count, index):
    area = gmdraw.rect(overlay(app), box_name)
    return gmdraw.bands(area, count)[index].center


def snap(app, name):
    pump(app, 6)
    os.makedirs(OUT, exist_ok=True)
    native = os.path.join(OUT, f"_native_{name}.png")
    native_png(app.client.state, native)
    hd = pygame.transform.smoothscale(app.surface, (1920, 1080))
    side = pygame.Surface((1920 + 1440, 1080))
    side.blit(hd, (0, 0))
    side.blit(pygame.transform.scale(pygame.image.load(native),
                                     (1440, 1080)), (1920, 0))
    pygame.image.save(side, os.path.join(OUT, f"{name}.png"))
    os.remove(native)
    print(f"  picture: {name}")


def fields_tuple(state):
    return [(f.index, f.x, f.y, f.x_end, f.y_end, f.field_type, f.hotkey)
            for f in state.fields]


def open_menu(app):
    galaxy = app.dispatcher.screens["galaxy_map"]
    title = galaxy._data["frame"]["title_rect"]
    click_at(app, *pygame.Rect(*app.layout.rect(title)).center)
    return wait_for(app, lambda: node_is(app, nodes.MENU), 30.0, "menu")


def back_on_galaxy(app, seconds=30.0):
    return wait_for(app, lambda: overlay(app) is None
                    and app.client.state.current_screen == 0
                    and app.dispatcher.active_name == "galaxy_map",
                    seconds, "the galaxy map")


def step_walk(app, counter):
    native = json.load(open(os.path.join(EVIDENCE, "fields_capture.json")))
    galaxy = fields_tuple(app.client.state)
    ok = open_menu(app)
    want = [(d["i"], d["x"], d["y"], d["xe"], d["ye"], d["t"], d["hk"])
            for d in native["nodes"]["01_game_menu"]["fields"]]
    got = fields_tuple(app.client.state)
    print(f"  HD GAME click -> field list equals the native GAME click's: "
          f"{got == want} ({len(got)} fields)")
    ok = ok and got == want
    snap(app, "01_game_menu")
    ok &= click_box(app, "menu_settings", nodes.SETTINGS, "settings")
    snap(app, "02_settings")
    ok &= click_box(app, "settings_accept", nodes.MENU, "accept -> menu")
    ok &= click_box(app, "menu_load", nodes.LOAD, "load")
    snap(app, "03_load")
    click_at(app, *row_centre(app, "slot_list", nodes.SLOTS, 3))
    ok &= wait_for(app, lambda: node_is(app, nodes.WARNING), 30.0, "warning")
    snap(app, "03a_warning_slot_4")
    click_at(app, app.win_w // 2, app.win_h // 2)
    ok &= wait_for(app, lambda: node_is(app, nodes.LOAD), 30.0, "back to load")
    ok &= click_box(app, "load_cancel", nodes.MENU, "cancel -> menu")
    ok &= click_box(app, "menu_save", nodes.SAVE, "save")
    snap(app, "04_save")
    before = counter.total()
    click_at(app, *row_centre(app, "slot_list", nodes.SLOTS, 9))
    snap(app, "04a_save_slot_10_editing")
    print(f"  starting an edit sent nothing: {counter.total() == before}")
    ok &= counter.total() == before
    key(app, pygame.K_ESCAPE)
    ok &= wait_for(app, lambda: node_is(app, nodes.MENU), 30.0,
                   "ESC while editing -> menu")
    ok &= click_box(app, "menu_new", nodes.CONFIRM, "new confirm")
    snap(app, "05_new_confirm")
    ok &= click_box(app, "confirm_no", nodes.MENU, "no -> menu")
    ok &= click_box(app, "menu_quit", nodes.CONFIRM, "quit confirm")
    snap(app, "06_quit_confirm")
    ok &= click_box(app, "confirm_no", nodes.MENU, "no -> menu")
    click_at(app, *centre(app, "menu_return"))
    ok &= back_on_galaxy(app)
    same = fields_tuple(app.client.state) == galaxy
    print(f"  RETURN -> galaxy map, field list as before GAME: {same}")
    return ok and same


def step_esc(app, counter):
    ok = True
    for box_name, node in ((None, None), ("menu_settings", nodes.SETTINGS),
                           ("menu_load", nodes.LOAD),
                           ("menu_save", nodes.SAVE)):
        ok &= open_menu(app)
        if box_name:
            ok &= click_box(app, box_name, node, node)
        key(app, pygame.K_ESCAPE)
        landed = back_on_galaxy(app)
        print(f"  ESC in {node or 'menu'} -> galaxy map: {landed}")
        ok &= landed
    ok &= open_menu(app) and click_box(app, "menu_new", nodes.CONFIRM, "new")
    sent = counter.total()
    key(app, pygame.K_ESCAPE)
    pump(app, 25)
    still = node_is(app, nodes.CONFIRM) and counter.total() == sent
    print(f"  ESC in the confirmation: ignored, nothing sent: {still}")
    ok &= still and click_box(app, "confirm_no", nodes.MENU, "no")
    click_at(app, *centre(app, "menu_return"))
    return ok and back_on_galaxy(app)


def step_help(app, counter):
    ok = open_menu(app)
    for box_name, node in ((None, nodes.MENU), ("menu_settings",
                           nodes.SETTINGS), ("settings_accept", nodes.MENU),
                           ("menu_load", nodes.LOAD), ("load_cancel",
                           nodes.MENU), ("menu_save", nodes.SAVE)):
        if box_name:
            ok &= click_box(app, box_name, node, node)
        if node == nodes.MENU and box_name:
            continue
        ov = overlay(app)
        specs = [s for s in ov._help_regions if s.get("node") == node]
        hits = 0
        for spec in specs:
            r = ov.help_region_rect(spec)
            click_at(app, *r.center, button=3)
            if ov.help.help_id == spec["help_id"]:
                hits += 1
            click_at(app, *r.center, button=3)       # closes it
        print(f"  help in {node}: {hits} of {len(specs)} regions open "
              f"their own entry")
        ok &= hits == len(specs)
    key(app, pygame.K_ESCAPE)
    return ok and back_on_galaxy(app)


def settings_byte(app, offset):
    return app.client.state.settings_raw[offset]


def step_toggle(app, counter):
    row, offset = 3, 4           # Expanding Help, s_settings byte 4
    start = settings_byte(app, offset)
    ok = True
    for want in (1 - start, start):
        ok &= open_menu(app) and click_box(app, "menu_settings",
                                           nodes.SETTINGS, "settings")
        click_at(app, *row_centre(app, "settings_rows", nodes.OPTIONS, row))
        pump(app, 6)
        snap(app, f"toggle_expanding_help_to_{want}")
        key(app, pygame.K_ESCAPE)
        ok &= back_on_galaxy(app) and wait_for(
            app, lambda: settings_byte(app, offset) == want, 30.0,
            f"byte {offset} == {want}")
        print(f"  Expanding Help toggled, ESC: byte {offset} is "
              f"{settings_byte(app, offset)} (wanted {want})")
    return ok


def step_probe(app, counter):
    ok = open_menu(app) and click_box(app, "menu_save", nodes.SAVE, "save")
    strip = nodes.save_strips(app.client.state.fields)[9]
    app.client.activate_field(strip.index)
    pump(app, 4)
    for ch in "ABCDEFGHIJKLMNO":          # fifteen keys in ONE burst
        app.client.inject_key(ord(ch))
    pump(app, 20)
    snap(app, "probe_burst_of_15_into_slot_10")
    app.client.inject_key(pygame.K_ESCAPE)
    landed = wait_for(app, lambda: node_is(app, nodes.MENU), 30.0,
                      "native ESC while editing -> menu")
    print(f"  native ESC while editing lands in the menu: {landed}")
    click_at(app, *centre(app, "menu_return"))
    return ok and landed and back_on_galaxy(app)


def step_save(app, counter, name):
    ok = open_menu(app) and click_box(app, "menu_save", nodes.SAVE, "save")
    click_at(app, *row_centre(app, "slot_list", nodes.SLOTS, 9))
    for ch in name:
        key(app, pygame.key.key_code(ch.lower()) if ch.isalpha() else
            ord(ch), ch)
    snap(app, "save_slot_10_typed")
    key(app, pygame.K_RETURN, "\r")
    ok &= back_on_galaxy(app, 120.0)
    raw = open(os.path.join(GAME_DIR, "SAVE10.GAM"), "rb").read(41)[4:41]
    desc = raw.split(b"\0", 1)[0].decode("latin-1")
    # THE ENGINE'S OWN TRAILING CURSOR. A name saved with Enter keeps the
    # edit cursor `_` — measured 14 September 2026 on this path, and the
    # native list already held "ddddd_" saved by hand. Open fix 19; HD
    # reproduces it and does not repair it (Data's order on quirks).
    exact = desc in (name, name + "_")
    print(f"  SAVE10.GAM description: {desc!r} (typed {name!r}): "
          f"{exact}{' — with the engine cursor' if desc != name else ''}")
    return ok and exact


def step_load(app, counter):
    before = app.client.state.stardate
    ok = open_menu(app) and click_box(app, "menu_load", nodes.LOAD, "load")
    click_at(app, *row_centre(app, "slot_list", nodes.SLOTS, 9))
    ok &= wait_for(app, lambda: app.client.state.current_screen not in
                   (0, 8), 180.0, "the game leaving the popup")
    state = app.client.state
    print(f"  loaded: screen {state.current_screen}, stardate "
          f"{state.stardate} (before {before}), overlay closed "
          f"{overlay(app) is None}")
    return ok and overlay(app) is None


def step_quit(app, counter):
    ok = open_menu(app) and click_box(app, "menu_quit", nodes.CONFIRM, "quit")
    click_at(app, *centre(app, "confirm_yes"))
    ended = wait_for(app, lambda: app.client.game_ended or not app.running,
                     180.0, "the game ending")
    print(f"  client game_ended {app.client.game_ended}, app running "
          f"{app.running}")
    return ok and ended and not app.running


class Log(logging.Handler):
    lines = []

    def emit(self, record):
        Log.lines.append(f"{record.name}: {record.getMessage()}")


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "walk"
    logging.getLogger().addHandler(Log())
    from main import App
    app = App()
    if not app.connected:
        print("no game on the extension port")
        return 1
    counter = Counter(app.client)
    if not back_on_galaxy(app, 20.0):
        print("  put the game on the galaxy map first")
        return 1
    state = app.client.state
    print(f"game: fixture {fixture_name(state)!r} — stardate "
          f"{state.stardate}, {state.num_stars} stars, "
          f"{state.num_colonies} colony records")
    before = save_rule()
    fn = {"walk": step_walk, "esc": step_esc, "help": step_help,
          "toggle": step_toggle, "probe": step_probe, "load": step_load,
          "quit": step_quit,
          "save": lambda a, c: step_save(a, c, sys.argv[2])}[step]
    ok = fn(app, counter)
    rule = report_rule(before, save_rule())
    reconnects = [l for l in Log.lines if "econnect" in l]
    print(f"  reconnect lines in this run's log: {len(reconnects)}")
    for line in reconnects:
        print(f"    {line}")
    print(f"{step}: {'PASS' if ok and rule else 'FAIL'}")
    return 0 if ok and rule else 1


if __name__ == "__main__":
    sys.exit(main())
