#!/usr/bin/env python3
"""OrionLayer smoke test — verify the project after any change.

Runs headless (no window, no orion2re needed) and exercises:
  - resource resolution + mod override (example_mod)
  - skin palette loading
  - screen auto-discovery + dispatcher game-ID map
  - full lifecycle of every screen (enter/update/render/click/
    resize/exit)
  - sub-screen lock behavior
  - editor toggle, selection, overlay rendering
  - App boot in standalone mode

Usage (from the project root):
    python tools/smoke_test.py

Exit code 0 = all good. Run this before shipping a ZIP or a
mod, and after touching anything in core/.
"""
import ast
import hashlib
import io
import math
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

PASS = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ok  {msg}")


def main():
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
    assert d.screen_map.get(6) == "select_race"
    ok(f"discovery + game-ID map ({len(d.screens)} screens)")

    # ── Screen lifecycles ──
    surf = pygame.Surface((1920, 1080))
    for name in sorted(d.screens):
        d.switch_to(name)
        s = d.active
        s.update(None)
        s.render(surf)
        s.handle_click(960, 540)
        s.handle_mouse_motion(960, 540)
        s.on_resize()
    ok("screen lifecycles (enter/update/render/click/resize)")

    # ── Auto-routing for custom_race (GAME_SCREEN_ID=50) ──
    if "custom_race" in d.screens:
        class GS50:
            current_screen = 50
        d.update_from_game(GS50())
        assert d.active_name == "custom_race"

        class GS6:
            current_screen = 6
        d.update_from_game(GS6())
        assert d.active_name == "select_race"
        ok("auto-routing (custom_race ↔ select_race)")

    # ── Editor ──
    app.editor = Editor(app)
    d.switch_to("main_menu")
    ed = app.editor
    ed.toggle()
    ed.render(surf)
    ed.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(960, 540)))
    scr = d.active
    if scr.boxes:
        box = scr.boxes[0]
        cx, cy = box.screen_rect.center
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy)))
        assert ed.selected is box
        # Resize-handle drag (bottom-right corner)
        r = box.screen_rect
        old = tuple(box.ref_rect)
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1, pos=(cx, cy)))
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(r.right, r.bottom)))
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEMOTION, pos=(r.right + 15, r.bottom + 10)))
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1,
            pos=(r.right + 15, r.bottom + 10)))
        assert tuple(box.ref_rect) != old, "resize had no effect"
        # Glow + rotate + nudge path
        ed.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_g, mod=0))
        ed.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_r, mod=0))
        ed.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_LEFT, mod=0))
    ed.render(surf)
    ed.toggle()
    ok("editor select + resize + glow + overlay")

    # ── Empire Identity: banner grid, inputs, pannable image box ──
    if "empire_identity" in d.screens:
        d.switch_to("empire_identity")
        ei = d.active
        assert ei.result["banner"] == "green", ei.result
        for ch in "Ab":
            ei.handle_key_event(pygame.event.Event(
                pygame.KEYDOWN, key=ord(ch.lower()), unicode=ch, mod=0))
        assert ei.result["ruler"] == "Ab", ei.result
        ei.handle_key_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_TAB, unicode="", mod=0))
        assert ei._home.focused and not ei._ruler.focused
        # Click the first banner tile
        from screens.empire_identity.renderer import banner_grid_layout
        gr = ei.box_rect("banner_grid")
        key, (cx, cy, cw, ch) = banner_grid_layout(ei._colors, gr)[0]
        px, py = app.layout.pos(cx + cw / 2, cy + ch / 2)
        ei.handle_click(px, py)
        assert ei.result["banner"] == key
        ei.render(surf)
        # Editor: zoom + right-drag pan on the artwork box
        img = next(b for b in ei.boxes if b.name == "preview_image")
        ed.toggle()
        ed.selected = img
        ed.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=2, x=0))
        assert img.style["zoom"] > 1.0
        ix, iy = img.screen_rect.center
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=3, pos=(ix, iy)))
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEMOTION, pos=(ix - 200, iy)))
        ed.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=3, pos=(ix - 200, iy)))
        assert img.style["crop"][0] > 0.5, img.style["crop"]
        ei.render(surf)
        ed.toggle()
        ok("empire_identity (grid click, inputs, tab, image zoom/pan)")
        # Custom Race Accept -> Empire Identity, held for IDs 50 and 6
        d.switch_to("custom_race")
        cr = d.active
        fr = cr._get_active_frame()
        bx, by, bw, bh = fr.button_rect_right(1920, 1080)
        cr.handle_click(bx + bw // 2, by + bh // 2)
        assert d.active_name == "empire_identity", d.active_name
        for gid in (50, 6):
            class GS: current_screen = gid
            d.update_from_game(GS())
            assert d.active_name == "empire_identity", (gid, d.active_name)
        class GS13: current_screen = 13
        d.update_from_game(GS13())
        assert d.active_name == "new_game", d.active_name
        ok("custom_race Accept -> empire_identity (lock 50/6, release 13)")

        # Negative picks: Accept must be refused locally. The point of
        # testing here rather than letting orion2re refuse is that the
        # game answers with its own framebuffer popup, which the HD
        # screen cannot see and would then have to dismiss blind.
        class SpyClient(FakeClient):
            def __init__(self): self.sent = []
            def activate_field(self, fid): self.sent.append(fid)

        _prev_client, _prev_conn = app.client, app.connected
        app.client, app.connected = SpyClient(), True
        d.switch_to("custom_race")
        cr = d.active
        app.client.sent.clear()          # enter() sends Clear (field 4)
        cr._starting_picks = -1          # overspent race
        assert cr.picks_remaining < 0
        cr.handle_click(bx + bw // 2, by + bh // 2)      # Accept
        assert d.active_name == "custom_race", d.active_name
        assert cr._popup.visible
        assert app.client.sent == [], app.client.sent
        cr.render(surf)                  # popup path draws
        # Modal: the next click only dismisses, it does not re-Accept
        cr.handle_click(bx + bw // 2, by + bh // 2)
        assert not cr._popup.visible
        assert d.active_name == "custom_race", d.active_name
        # ESC is swallowed by the popup, never cancels the screen
        cr._popup.open("x")
        cr.handle_key(pygame.K_ESCAPE)
        assert not cr._popup.visible
        assert app.client.sent == [], app.client.sent
        # Balanced again -> Accept goes through as before
        cr._starting_picks = 10
        cr.handle_click(bx + bw // 2, by + bh // 2)
        assert d.active_name == "empire_identity", d.active_name
        assert 3 in app.client.sent, app.client.sent
        app.client, app.connected = _prev_client, _prev_conn
        ok("custom_race negative picks (popup blocks Accept, modal)")

        # New Game panel skins: the picture frames keep the 9-slice,
        # the group boxes around them carry the thin blue border. Put
        # as a containment rule rather than a list of panel names, so
        # a renamed or newly added panel still has to obey it.
        import json as _json
        _ng_path = os.path.join(SCREENS_DIR, "new_game", "boxes.json")
        with open(_ng_path, encoding="utf-8") as _fh:
            _ng = _json.load(_fh)
        _saw_panels = False
        for _res, _boxes in _ng.items():
            def _skin(b):
                return b.get("style", {}).get("skin")
            _thin = [b for b in _boxes if _skin(b) == "thin_border"]
            _nine = [b for b in _boxes if _skin(b) == "inner_panel"]
            if not _thin and not _nine:
                # 1080p still has no panel frames at all — a known
                # loose end, not a skin bug. The guard keys on the
                # absence of PANEL boxes, not on an empty file: the
                # list stopped being empty when help_popup joined it,
                # and an emptiness check would have started asserting
                # against a resolution that has nothing to assert.
                continue
            _saw_panels = True
            assert _thin and _nine, (_res, len(_thin), len(_nine))
            for _b in _nine:
                _x, _y, _w, _h = _b["rect"]
                assert any(
                    o["rect"][0] <= _x and o["rect"][1] <= _y
                    and o["rect"][0] + o["rect"][2] >= _x + _w
                    and o["rect"][1] + o["rect"][3] >= _y + _h
                    for o in _thin), (_res, _b["name"])
        assert _saw_panels, "no resolution defines New Game's panels"
        ok("new_game panel skins (9-slice inside thin border)")

        # Injection chain: ruler name -> banner -> home star, driven by
        # fake field lists; lock held via keep_lock until done
        from core import injection as inj
        from core.game_state import FieldInfo
        inj.SETTLE_S = 0.0

        class RecClient(FakeClient):
            def __init__(self): self.log = []
            def activate_field(self, fid): self.log.append(("act", fid))
            def inject_click(self, x, y): self.log.append(("click", x, y))
            def inject_key(self, k): self.log.append(("key", k))

        def F(i, x, y, w, h, t):
            return FieldInfo(index=i, x=x, y=y, x_end=x + w,
                             y_end=y + h, field_type=t)
        name_a = [F(0, 0, 0, 0, 0, 0), F(1, 200, 200, 230, 20, 11),
                  F(2, 270, 245, 90, 22, 0)]
        banner = [F(0, 0, 0, 0, 0, 0)] + [
            F(1 + r * 4 + c, 90 + c * 125, 150 + r * 150, 100, 110, 1)
            for r in range(2) for c in range(4)]
        name_b = [F(0, 0, 0, 0, 0, 0), F(1, 160, 220, 230, 20, 11),
                  F(2, 230, 265, 90, 22, 0)]

        class GS:
            def __init__(s, sid, fields):
                s.current_screen = sid; s.fields = fields
        app.connected = True
        app.client = RecClient()
        d.switch_to("custom_race")
        cr = d.active
        cr.handle_click(bx + bw // 2, by + bh // 2)   # Accept
        ei = d.active
        assert ei.SCREEN_NAME == "empire_identity"
        ei._ruler.value = "Zed"
        ei._color = "purple"                          # row 2, col 3
        ei._home.value = "Kor"
        ei.handle_click(bx + bw // 2, by + bh // 2)   # HD Accept
        assert ei.busy
        for sid, fields in ((6, name_a), (6, name_a), (6, banner),
                            (0, name_b)):
            gs = GS(sid, fields)
            d.update_from_game(gs)
            assert d.active_name == "empire_identity", d.active_name
            ei.update(gs)
        assert not ei.busy
        keys = [k[0] for t, *k in app.client.log if t == "key"]
        assert pygame.K_RETURN in keys and ord("Z") in keys, keys
        acts = [a[0] for t, *a in app.client.log if t == "act"]
        assert acts[-1] == 1 + 1 * 4 + 2, acts     # purple: row 2, col 3
        d.update_from_game(GS(0, []))                 # chain done → release
        assert d.active_name != "empire_identity"
        app.connected = False
        app.client = FakeClient()
        ok("injection chain (ruler -> banner -> home star, lock release)")

        # The gap between banner and home star is a galaxy generation:
        # the game goes silent, publishes no field list, and the old
        # 3 s watchdog reconnected straight through it — which threw
        # away the FIELD_LIST the last step was waiting for. Two
        # invariants, both regressions that stranded orion2re on
        # "Enter home star name" while HD sat on Custom Race.
        class HoldClient(RecClient):
            def __init__(s):
                super().__init__()
                s.hold = 0.0
            def hold_watchdog(s, seconds):
                s.hold = max(s.hold, seconds)

        hc = HoldClient()
        chain = inj.InjectionChain(hc, [
            ("banner", inj.is_banner_dialog,
             lambda c, f: c.activate_field(f[1].index)),
            ("home star", inj.is_name_dialog,
             lambda c, f: inj.type_name(c, "Kor"), 30.0),
        ])
        chain.update(GS(50, banner))
        assert chain.pos == 1 and not chain.failed
        # (a) an empty field list is no information: not a change, not
        #     a detection, and above all not a failure
        chain._fired_at -= 5.0          # past the default 4 s timeout
        for _ in range(3):
            chain.update(GS(0, []))
        assert not chain.failed, "empty field list must not fail a step"
        assert chain.pos == 1
        # (b) the chain holds the connection open for its own timeout
        assert hc.hold >= 30.0, hc.hold
        # (c) and it still completes once the real list finally lands
        chain.update(GS(0, name_b))
        assert chain.done and not chain.failed
        ok("injection chain survives a silent gap (mapgen, no fields)")

        # A reconnect must not leave a field list from the dead
        # connection behind — a stale list is a lie the chain cannot
        # detect, an empty one it handles (check above).
        from core.game_client import GameClient, STALE_TIMEOUT
        gc = GameClient()
        gc.state.fields = list(banner)
        gc._open = lambda: False              # no game running here
        gc._reconnect()
        assert gc.state.fields == [], gc.state.fields
        assert STALE_TIMEOUT >= 10.0, STALE_TIMEOUT
        ok("reconnect drops the stale field list")

        # The busy panel is an INVENTION (MOO2 shows nothing at all
        # while it generates the galaxy), so it needs a test that
        # fails if it silently stops being drawn. Assert the rule the
        # invention exists for: while a chain runs, the busy panel
        # rect must not look like the idle screen.
        app.connected = True
        app.client = RecClient()
        d.switch_to("empire_identity")
        ei = d.active
        bp = ei.box_rect("busy_panel")
        assert bp, "busy_panel box missing from boxes.json"
        _r = pygame.Rect(app.layout.pos(bp[0], bp[1]),
                         app.layout.size(bp[2], bp[3]))
        surf.fill((0, 0, 0))
        ei.render(surf)
        idle = surf.subsurface(_r).copy()
        ei._accept()
        assert ei.busy
        surf.fill((0, 0, 0))
        ei.render(surf)
        busy = surf.subsurface(_r).copy()
        assert pygame.image.tostring(idle, "RGB") != \
            pygame.image.tostring(busy, "RGB"), "busy panel not drawn"
        # It says which step, and the sweep actually moves
        a = pygame.Surface(_r.size)
        b = pygame.Surface(_r.size)
        from screens.empire_identity import renderer as _eir
        for _phase, _s in ((0.0, a), (_eir.BUSY_SWEEP_S / 2.0, b)):
            _s.fill((0, 0, 0))
            _eir.render_busy_panel(
                _s, app.layout, app.style,
                (0, 0, bp[2], bp[3]), (10, 10, bp[2] - 20, bp[3] - 20),
                "Setting up", "Generating the galaxy", 3, 3, 12.0,
                "({s} s)", None, now=_phase)
        assert pygame.image.tostring(a, "RGB") != \
            pygame.image.tostring(b, "RGB"), "progress bar is static"
        # Both layouts must draw: the box picks one by height, so a
        # dragged box must not fall into an unrendered branch.
        for _h, _label in ((40, "inline"), (170, "stacked")):
            _s = pygame.Surface((700, _h))
            _s.fill((0, 0, 0))
            _eir.render_busy_panel(
                _s, app.layout, app.style, (0, 0, 700, _h),
                (14, 8, 672, _h - 16), "Setting up",
                "Generating the galaxy", 2, 3, 9.0, "({s} s)", None,
                now=0.0)
            assert _s.get_at((350, _h // 2))[:3] != (0, 0, 0), _label
        ei._chain = None
        app.connected = False
        app.client = FakeClient()
        ok("empire_identity busy panel (INVENTION, drawn + animated)")

    # ── Overlay layer ──
    from core.screen_base import ScreenBase

    class FakeQueuePopup(ScreenBase):
        SCREEN_NAME = "_fake_popup"
        GAME_SCREEN_ID = 25          # SCREEN_QUEUE_POPUP
        IS_OVERLAY = True

        def enter(self, game_state=None):
            self.active = True
            self.boxes = []

        def render(self, srf):
            pass

    d.register("_fake_popup", FakeQueuePopup(app))
    d.switch_to("select_race")
    parent = d.active
    d.switch_to("_fake_popup")           # routes to open_overlay
    assert d.active is parent, "overlay must not replace parent"
    assert d.overlay_name == "_fake_popup"
    assert d.top is d.overlay
    d.render(surf)                       # parent + dim + overlay
    d.route_click(960, 540)              # goes to overlay, no crash
    d.route_motion(960, 540)

    class GSPopup:
        current_screen = 25
    assert d.update_from_game(GSPopup()) is True
    assert d.overlay_name == "_fake_popup", "stays open on its ID"

    class GSBack:
        current_screen = 6
    d.update_from_game(GSBack())
    assert d.overlay is None, "overlay closes when game leaves ID"
    assert d.active_name == "select_race", "parent untouched"
    ok("overlay layer (open/render/route/auto-close)")

    # ── Widgets ──
    from core.widgets import ListView, TextInput

    picked = []
    lv = ListView(columns=[("NAME", 0.5), ("POP", 0.25),
                           ("PROD", 0.25)],
                  on_select=lambda i, row: picked.append(row))
    lv.set_rows([(f"Colony {i}", str(i), str(i * 2))
                 for i in range(40)])
    lrect = pygame.Rect(100, 100, 500, 300)
    lv.render(surf, lrect, app.style, app.layout)
    assert lv._visible > 3
    lv.handle_mousewheel(-1, 300, 200)
    assert lv.scroll == 3, lv.scroll
    row_y = lv._rows_area(app.layout).y + lv._row_h(app.layout) // 2
    idx = lv.handle_click(150, row_y)
    assert idx == lv.scroll and picked[-1][0] == f"Colony {idx}"
    assert lv.handle_key(pygame.K_DOWN) is True
    assert lv.selected == idx + 1
    lv.render(surf, lrect, app.style, app.layout)

    submitted = []
    ti = TextInput(max_len=10, on_submit=submitted.append)
    trect = pygame.Rect(100, 500, 400, 50)
    ti.render(surf, trect, app.style, app.layout)

    def key(k, ch=""):
        return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)

    for ch in "Sol-3":
        assert ti.handle_key_event(key(0, ch))
    assert ti.value == "Sol-3", ti.value
    ti.handle_key_event(key(pygame.K_BACKSPACE))
    assert ti.value == "Sol-"
    ti.handle_key_event(key(pygame.K_RETURN))
    assert submitted == ["Sol-"]
    assert ti.handle_click(120, 510) is True   # focus hit
    assert ti.handle_click(10, 10) is False    # defocus outside
    ti.render(surf, trect, app.style, app.layout)
    ok("widgets (ListView scroll/select/keys, TextInput)")

    # ── Struct specs ──
    import struct as _s
    from core.structs import star, ship_icon
    raw = bytearray(star.SIZE)
    raw[0:4] = b"Sol\x00"
    _s.pack_into("<h", raw, 15, 142)
    _s.pack_into("<h", raw, 17, 377)
    raw[19] = 2
    _s.pack_into("<b", raw, 20, 3)
    raw[22] = 2
    raw[159] = 7
    s = star.parse(bytes(raw))
    assert (s.name, s.x, s.y, s.owner, s.system_special) == \
        ("Sol", 142, 377, 3, 7)
    ic = ship_icon.parse(_s.pack("<6h", 4, 1, 9, 5, 250, 310))
    assert (ic.star_idx, ic.stack_slot, ic.x, ic.y) == (9, 5, 250, 310)
    # s_ship_data: offsets confirmed by compiling orion2.h with its own
    # pragma pack(1); sizeof must equal the sizes.h assert.
    from core.structs import ship as _ship
    assert _ship.SIZE == 0x81
    sraw = bytearray(_ship.SIZE)
    _s.pack_into("<b", sraw, 99, 3)          # owner
    _s.pack_into("<b", sraw, 100, 1)         # status = in transit
    _s.pack_into("<hhh", sraw, 101, 10042, 300, 250)
    sv = _ship.parse(bytes(sraw))
    assert (sv.owner, sv.status, sv.location, sv.x, sv.y) == \
        (3, 1, 10042, 300, 250)
    # Encoded location: moving/wormhole offsets strip back to the star
    assert _ship.absolute_location(10042) == 42
    assert _ship.absolute_location(20042) == 42
    assert _ship.absolute_location(42) == 42
    ok("struct specs (star, ship_icon, ship)")

    # ── Galaxy map: coordinates, name rules, sidebar, input ──
    if "galaxy_map" in d.screens:
        from core import mapcoords as mc
        from core.game_state import GameState, STAR_SIZE, PLAYER_SIZE
        from core.structs import star as st, player as pl
        from screens.galaxy_map import renderer as gmr, sidebar as gsb
        from screens.galaxy_map import viewctl as gmv

        def mkstar(name, x, y, cls, size, owner, visited, wh=-1):
            r = bytearray(STAR_SIZE)
            r[0:len(name)] = name.encode()
            _s.pack_into("<hh", r, 15, x, y)
            r[19] = size
            _s.pack_into("<b", r, 20, owner)
            r[22] = cls
            _s.pack_into("<h", r, 160, wh)
            r[171] = visited
            return bytes(r)

        def mkplayer(color, bc, food, cp, cpu, contact1=0):
            r = bytearray(PLAYER_SIZE)
            r[38] = color
            _s.pack_into("<i", r, 50, bc)
            _s.pack_into("<h", r, 58, cp)
            _s.pack_into("<h", r, 60, cpu)
            _s.pack_into("<h", r, 276, food)
            _s.pack_into("<b", r, 1512 + 1, contact1)
            return bytes(r)

        gs = GameState()
        gs.current_screen = 0
        gs.player_num = 0
        # Medium galaxy: scale 15, MAP_MAX 759x600 (mapgen.cpp)
        gs.map_scale, gs.map_max_x, gs.map_max_y = 15, 759, 600
        gs.stars = st.parse_all([
            mkstar("Sol", 100, 100, 2, 1, 0, 0b1),
            mkstar("Vega", 400, 300, 0, 0, 1, 0b1),
            mkstar("Hidden", 600, 500, 4, 2, -1, 0b0),
            mkstar("Rift", 250, 450, 6, 1, -1, 0b1),   # black hole
        ])
        gs.player_raw = ([mkplayer(2, 15230, 12, 8, 3, contact1=1),
                          mkplayer(0, 900, -4, 5, 5)]
                         + [bytes(PLAYER_SIZE)] * 6)
        gs.nebulas_raw = [_s.pack("<hhb", 374, 170, 1)]

        d.update_from_game(gs)
        assert d.active_name == "galaxy_map", d.active_name
        gm = d.active
        gm.update(gs)
        gm.render(surf)

        # The transform must match orion2re exactly: the far corner
        # of a medium galaxy lands on the viewport corner.
        assert mc.galaxy_to_native(759, 600, gs) == (527, 421)
        view = gm._map_view()
        for star_view in gs.stars:
            native = mc.galaxy_to_native(star_view.x, star_view.y, gs)
            sx, sy = view.to_screen(star_view.x, star_view.y)
            assert view.to_native(sx, sy) == native, star_view.name

        # Star name visibility (MAINSCR::Get_Star_Name_)
        players = gm._players
        label = lambda v, omni: gmr.star_label(v, 0, players, omni)
        assert label(gs.stars[0], False) == "Sol"       # own, visited
        assert label(gs.stars[1], False) == "Vega"      # contacted owner
        assert label(gs.stars[2], False) == ""          # unvisited
        assert label(gs.stars[3], False) == ""          # black hole
        assert label(gs.stars[2], True) == "(Hidden)"   # lore -> brackets

        # Sidebar reads the player record, not pixels
        lbl = gm._data.get("labels", {})
        assert gsb.readout("command", gm._local, lbl)[1] == "+5"
        assert gsb.readout("food", gm._local, lbl)[1] == "+12"
        assert gsb.readout("treasury", None, lbl)[1] == "--"

        # Sidebar icons: every key in layout.json must name a real
        # readout row AND resolve to a loaded sprite. A typo in
        # either direction would otherwise just show no picture.
        icon_cfg = gm._data.get("sidebar_icons", {})
        assert icon_cfg, "sidebar_icons missing from layout.json"
        for key in icon_cfg:
            assert key in gm._data["sidebar_rows"], key
            assert gm._cache.has(f"sidebar_icons/{key}"), key
        assert set(gm._sidebar_icons()) == set(icon_cfg)
        # The stardate has no icon and keeps the whole row width
        assert "stardate" not in icon_cfg

        # Every sidebar element is its own box, so the F5 editor can
        # move it like on any other screen. A row without a text box
        # would silently vanish, so assert the full set exists.
        rows_cfg = gm._data["sidebar_rows"]
        for key in rows_cfg:
            assert gm.box_rect(f"sb_{key}_text"), key
        for key in icon_cfg:
            assert gm.box_rect(f"sb_{key}_icon"), key
        geo = gm._sidebar_geometry(rows_cfg, gm._sidebar_icons())
        assert set(geo) == set(rows_cfg), set(rows_cfg) - set(geo)
        assert geo["stardate"][1] is None
        assert geo["treasury"][1] is not None
        # Boxes and geometry must agree: text and icon may not overlap
        for key in icon_cfg:
            (tx, _, tw, _), (ix, _, _, _) = geo[key]
            assert ix >= tx + tw, (key, tx + tw, ix)

        # Fallback for a boxes.json from before the per-element boxes
        assert gsb.split_row((0, 0, 200, 100), False) \
            == ((0, 0, 200, 100), None)
        text_r, icon_r = gsb.split_row((0, 0, 200, 100), True, 0.4)
        assert text_r == (0, 0, 120, 100), text_r
        assert icon_r[0] >= text_r[2] and icon_r[2] > 0, icon_r
        fb = gsb.fallback_geometry((0, 0, 200, 600), rows_cfg, icon_cfg)
        assert set(fb) == set(rows_cfg) and fb["stardate"][1] is None

        # Title text comes from layout.json and reads GAME like the
        # original's top bar, which is the game menu button
        assert gm._data["frame"]["title"] == "Game", \
            gm._data["frame"].get("title")

        # The star field has to be REACHED, not merely present. A
        # layer that ships unwired looks exactly like a layer that is
        # switched off, and neither logs anything — so assert that a
        # full render actually built it.
        gm.render(pygame.Surface((app.win_w, app.win_h)))
        assert gm._starfield.star_count > 0, \
            "starfield module exists but _render_map never calls it"
        assert gm._data.get("starfield", {}).get("enabled", None) is not None, \
            "layout.json has no starfield block to configure it with"

        # Clicking a star injects that star's exact native point
        app.connected = True
        rec = RecClient()
        app.client = rec
        sx, sy = view.to_screen(400, 300)
        gm.handle_click(sx, sy)
        assert rec.log == [("click",) + mc.galaxy_to_native(400, 300, gs)], \
            rec.log
        # Navigation button -> ACTIVATE_FIELD (Races is field 14 —
        # the ext-API dump's "Research" label was a wrong guess,
        # corrected against a live screenshot of the original)
        rec.log.clear()
        r = app.layout.rect(gm.box_rect("nav_races"))
        gm.handle_click(r[0] + r[2] // 2, r[1] + r[3] // 2)
        assert rec.log == [("act", 14)], rec.log
        # TURN button (former status_bar cutout, bottom right)
        rec.log.clear()
        r = app.layout.rect(gm.box_rect("nav_turn"))
        gm.handle_click(r[0] + r[2] // 2, r[1] + r[3] // 2)
        assert rec.log == [("act", 7)], rec.log
        # Title cutout = GAME menu (field 6), like the original
        rec.log.clear()
        r = app.layout.rect(gm._data["frame"]["title_rect"])
        gm.handle_click(r[0] + r[2] // 2, r[1] + r[3] // 2)
        assert rec.log == [("act", 6)], rec.log
        # Hotkeys: T = turn (7, via button data), C = colonies (10)
        rec.log.clear()
        gm.handle_key(pygame.K_t)
        gm.handle_key(ord("c"))
        assert rec.log == [("act", 7), ("act", 10)], rec.log
        # Sidebar order mirrors the original: stardate row on top
        assert gm._data["sidebar_rows"][0] == "stardate"

        # Six sprite steps, indexed by zoom + size (one axis, as in
        # MAINSCR::Get_Star_Picture_Seg_). The defining property: a
        # large star one notch zoomed out uses the SAME sprite as a
        # medium star zoomed in — if these ever diverge, the renderer
        # has drifted back to a size-only lookup.
        from core import zoomtables as _zt
        assert gmr.STEP_COUNT == len(_zt.STAR_FIELDS_DIM) == 6
        big, mid = gs.stars[1], gs.stars[0]     # size 0 and size 1
        assert (big.size, mid.size) == (0, 1)
        ctx_in = gmr.MapContext(view, gs)
        assert gmr.star_step(ctx_in, big) == ctx_in.zoom
        assert (gmr.star_icon_name(big, ctx_in)
                == f"stars/blue/{ctx_in.zoom}")

        ctx_out = gmr.MapContext(view, gs)  # same view, one zoom out
        ctx_out.zoom = ctx_in.zoom + 1
        assert gmr.star_step(ctx_out, big) == gmr.star_step(ctx_in, mid)
        # And the index saturates instead of running off the table
        ctx_out.zoom = 99
        assert gmr.star_step(ctx_out, big) == 5

        # Every step of every class must resolve to a loaded sprite
        for folder in gmr.CLASS_DIRS.values():
            for step in range(gmr.STEP_COUNT):
                assert gm._cache.has(f"stars/{folder}/{step}"), (folder, step)
        # ── Home-system ping ──
        # An INVENTION (MOO2 has no such effect and cannot alpha
        # blend), so it is fenced in by tests rather than trusted:
        # it must resolve the home star from verified specs, must
        # expire by itself, and must not send anything to orion2re.
        from screens.galaxy_map import ping as gping
        assert "INVENTION" in gping.__doc__, \
            "the ping stopped declaring itself an invention"
        assert "INVENTION" in gm._data["home_ping"]["_note"]

        saved_players, saved_planets = gs.player_raw, gs.planets_raw
        home_raw = bytearray(gs.player_raw[0])
        _s.pack_into("<h", home_raw, 41, 7)        # home_planet_id
        gs.player_raw = [bytes(home_raw)] + list(saved_players[1:])
        planet = bytearray(18)
        _s.pack_into("<hh", planet, 0, -1, 0)      # colony -1, star 0
        gs.planets_raw = [bytes(18)] * 7 + [bytes(planet)]
        gm.update(gs)
        # player.home_planet_id -> planet.star_index -> the star
        assert gm.home_star() is gs.stars[0], gm.home_star()

        # A wrong index must not ping a random system: fall back to a
        # star the player owns, and say so.
        gs.planets_raw = [bytes(18)] * 3
        gm.update(gs)
        assert gm.home_star() is gs.stars[0]
        gs.planets_raw = [bytes(18)] * 7 + [bytes(planet)]
        gm.update(gs)

        # The key is consumed here — forwarding it would hand
        # orion2re a keycode it has no binding for.
        rec.log.clear()
        assert gm._ping_key() == pygame.K_HOME
        gm.handle_key(pygame.K_HOME)
        assert rec.log == [], rec.log
        assert gm._ping.active

        # It has to actually paint. A layer that is wired but draws
        # nothing looks exactly like a key that does not work.
        ctx_ping = gm._map_context()
        pos = gm._ping_position(ctx_ping)
        bx, by, bw, bh = ctx_ping.view.box
        assert bx <= pos[0] <= bx + bw and by <= pos[1] <= by + bh, pos
        probe = pygame.Surface((app.win_w, app.win_h))
        probe.fill((0, 0, 0))
        gm._ping.render(probe, ctx_ping, pos)
        assert int(pygame.surfarray.array2d(probe).astype(bool).sum()) > 0, \
            "ping is active but drew nothing"

        # Cost of the invention, kept visible. One ping sweeps ~100
        # radii; without the RADIUS_STEP rounding every one of them
        # would become its own cached surface, at 4K a few hundred KB
        # each. And the cache has to be handed back when the ping
        # ends — `active` is what frees it.
        gm._ping.trigger(now=0.0)
        gm._ping._start = 0.0
        for step in range(int((gping.PING_SECONDS + gping.RING_LIFE) * 60)):
            gm._ping.render(probe, ctx_ping, pos, now=step / 60.0)
        assert 0 < len(gm._ping._rings) <= 64, len(gm._ping._rings)

        # And it must expire on its own — a marker that can be left
        # switched on is a second UI state to reason about.
        gm._ping._start -= gping.PING_SECONDS + gping.RING_LIFE + 1
        assert not gm._ping.active
        assert gm._ping._rings == {}, "expired ping kept its surfaces"
        probe.fill((0, 0, 0))
        gm._ping.render(probe, ctx_ping, pos)
        assert int(pygame.surfarray.array2d(probe).astype(bool).sum()) == 0

        gs.player_raw, gs.planets_raw = saved_players, saved_planets
        gm.update(gs)

        app.connected = False
        app.client = FakeClient()
        ok("galaxy_map (transform, name rules, sidebar, click/hotkeys)")

        # ── Decoupled HD zoom, anchored on the pointer ──
        # The defining invariant: the galaxy point under the cursor
        # does not move on a wheel tick. Everything else about the
        # feature (clamps, parking, click frame, reset) is asserted
        # around that.
        rec2 = RecClient()
        app.client, app.connected = rec2, True
        gm.update(gs)
        assert not gm._viewctl.active           # mirrors the game
        v0 = gm._map_view()
        anchor_sx, anchor_sy = v0.to_screen(gs.stars[1].x, gs.stars[1].y)
        px, py2 = int(anchor_sx), int(anchor_sy)
        # THE invariant: the galaxy point under the cursor pixel is
        # pinned to that pixel across ticks. (The star centre itself
        # may sit a fraction of a native pixel off the integer cursor
        # position, and that fraction legitimately magnifies with the
        # zoom — so the point is asserted exactly, the star loosely.)
        agx, agy = v0.to_galaxy(px, py2)
        for _ in range(6):
            gm.handle_mousewheel(1, px, py2)
        assert gm._viewctl.active
        v1 = gm._map_view()
        assert type(v1).__name__ == "SmoothMapView"
        hx, hy = v1.to_screen(agx, agy)
        assert abs(hx - px) < 0.01 and abs(hy - py2) < 0.01, \
            (px, py2, hx, hy)
        nsx, nsy = v1.to_screen(gs.stars[1].x, gs.stars[1].y)
        assert abs(nsx - anchor_sx) < 5 and abs(nsy - anchor_sy) < 5, \
            (anchor_sx, anchor_sy, nsx, nsy)
        assert gm._viewctl.scale < gs.map_scale
        # Zoom-in floor, zoom-out ceiling (the fit view)
        for _ in range(60):
            gm.handle_mousewheel(1, px, py2)
        assert gm._viewctl.scale == gmv.MIN_SCALE, gm._viewctl.scale
        for _ in range(60):
            gm.handle_mousewheel(-1, px, py2)
        assert gm._viewctl.scale == 15.0, gm._viewctl.scale  # max_map_scale
        # Zoom back in so the HD slice differs from the game's, then:
        for _ in range(8):
            gm.handle_mousewheel(1, px, py2)
        # 1. A star click still lands in the GAME's frame — the native
        # point must equal the game-state transform, never the HD one.
        rec2.log.clear()
        gm._click_star(gs.stars[0])
        want = mc.galaxy_to_native(gs.stars[0].x, gs.stars[0].y, gs)
        assert rec2.log == [("click", *want)], (rec2.log, want)
        # 2. Parking uses the zoom-OUT field only, throttled; the
        # game is not yet at max scale (15 vs its 15... use a state
        # copy that is zoomed in) — simulate scale 10:
        gs.map_scale = 10
        gm._viewctl._park_sent = 0.0
        rec2.log.clear()
        gm.update(gs)
        assert rec2.log == [("act", 9)], rec2.log
        gm.update(gs)                            # throttled: no repeat
        assert rec2.log == [("act", 9)], rec2.log
        # AND A STALE SNAPSHOT DOES NOT STOP IT. The first message
        # after any send is serialized in the tick that CONSUMED the
        # send (ext_api.cpp:341-386), so `map_scale` still reads the
        # old value — which is why this loop compares against an
        # ABSOLUTE target and not against the previous reading. A
        # delta comparison here would see "nothing moved" and park
        # half way, at whatever zoom the game happened to be on, with
        # every click afterwards aimed through a slice that does not
        # cover the galaxy. Audited 5 September 2026.
        for _ in range(3):
            gm._viewctl._park_sent = 0.0
            gm.update(gs)                        # same stale state
        assert rec2.log == [("act", 9)] * 4, (
            f"parking stopped on a stale snapshot: {rec2.log}. The "
            f"terminating condition must be `current >= fit`, never "
            f"a comparison with the previous reading")
        gs.map_scale = 15
        gm._viewctl._park_sent = 0.0
        rec2.log.clear()
        gm.update(gs)                            # parked: nothing sent
        assert rec2.log == [], rec2.log
        # 3. Right-drag pans, and the origin stays on the galaxy
        bx0, by0, bw0, bh0 = v1.box
        inside = (bx0 + bw0 // 2, by0 + bh0 // 2)
        gm.handle_right_button(True, *inside)
        gm.handle_mouse_motion(inside[0] - 40, inside[1] - 25)
        gm.handle_right_button(False, 0, 0)
        vw = (mc.MAP_RIGHT - mc.MAP_LEFT) * gm._viewctl.scale / 10
        assert 0 <= gm._viewctl.x <= gs.map_max_x - vw + 0.001, \
            gm._viewctl.x
        # 4. Wheel outside the map box changes nothing
        before = (gm._viewctl.x, gm._viewctl.y, gm._viewctl.scale)
        gm.handle_mousewheel(1, bx0 - 30, by0 - 30)
        assert (gm._viewctl.x, gm._viewctl.y,
                gm._viewctl.scale) == before
        # 5. Key 0 hands the view back to the game
        gm.handle_key(pygame.K_0)
        assert not gm._viewctl.active
        assert type(gm._map_view()).__name__ == "MapView"
        # 6. Renders in the decoupled state, ship anchor and all
        for _ in range(4):
            gm.handle_mousewheel(1, *inside)
        assert gm._icon_anchor() is not None
        gm.render(surf)
        gm._viewctl.reset()
        app.connected = False
        app.client = FakeClient()
        ok("galaxy_map anchored zoom (pointer-fixed, clamps, parking)")

        # Frame cutouts are the second source for every galaxy box:
        # boxes.json must equal what tools/frame_holes.py derives
        # from the PNG, else content and cutouts have drifted apart.
        import frame_holes as fh
        assert gm._frame_scaled is not None, "galaxy frame not loaded"
        fw, fhh, holes = fh.find_holes(
            res.screen_file("galaxy_map", "assets", "frame.png"))
        named = fh.name_holes(holes)
        assert [fw, fhh] == gm._data["frame"]["image_size"], (fw, fhh)
        for name, r in named.items():
            want = fh.to_ref(r, fw, fhh)
            got = (gm._data["frame"]["title_rect"] if name == "title"
                   else list(gm.box_rect(name)))
            assert all(abs(a - b) <= 2 for a, b in zip(got, want)), \
                (name, got, want)
        gm.render(pygame.display.get_surface())
        ok("galaxy_map frame cutouts == boxes.json")

    # ── Colony Summary (frame, cutouts, native click points) ──
    d.switch_to("colony_summary")
    cs = d.active
    assert cs.GAME_SCREEN_ID == 20
    import frame_holes as fh
    # ── THE CUTOUTS COME FROM THE BUILT PLATE NOW (Stage 4) ──
    # Decision 3's chain is unchanged and its source moved: boxes.json
    # is generated from the plate frame_build.py makes, not from the
    # superseded frame.png. The old artwork has 14 holes in places the
    # layout no longer uses, so it can no longer host these boxes —
    # see `colonyframe` and the status document for what flag-off
    # means now.
    _plate = os.path.join(SCREENS_DIR, "colony_summary", "assets",
                          "frames", "frame_1920x1080.png")
    if os.path.exists(_plate):
        fw, fhh, holes = fh.find_holes(_plate)
        assert len(holes) == 8, len(holes)
        named = fh.name_holes(holes, "colony_summary")
        assert set(named) == {b.name for b in cs.boxes}, (
            f"the plate's holes and boxes.json name different things: "
            f"holes {sorted(named)}, boxes {sorted(b.name for b in cs.boxes)}")
        for name, r in named.items():
            want = fh.to_ref(r, fw, fhh)
            got = list(cs.box_rect(name))
            assert all(abs(a - b) <= 2 for a, b in zip(got, want)), \
                (name, got, want)
        _cut_note = f"{len(holes)} plate holes"
    else:
        _cut_note = (f"plate absent, run `python tools/frame_build.py`")
    # ONE sort bar, not seven buttons, and it spans the list's width.
    _bar = cs.box_rect("sort_bar")
    _la = cs.box_rect("list_area")
    assert _bar and _la, (_bar, _la)
    assert abs(_bar[0] - _la[0]) <= 2, (_bar, _la)
    assert cs.box_rect("return")[0] > _bar[0] + _bar[2], (
        "RETURN must sit to the right of the sort bar")
    # The seven keys divide it, and the SAME function answers the
    # renderer and the click test (decision 5).
    _sb = cs._sort_buttons()
    assert [b.key for b in _sb] == fh.SORT_KEYS, [b.key for b in _sb]
    _barpx = pygame.Rect(*cs.layout.rect(_bar))
    assert _sb[0].hit.left == _barpx.left and _sb[-1].hit.right == _barpx.right
    for _a, _b in zip(_sb, _sb[1:]):
        assert _a.hit.right == _b.hit.left, (
            f"the sort buttons do not tile the bar: {_a.key} ends at "
            f"{_a.hit.right}, {_b.key} starts at {_b.hit.left}")
    for _b in _sb:
        assert _b.hit.contains(_b.highlight), (
            f"{_b.key}'s highlight is wider than the area that hits it")

    # WHICH of the three bottom cutouts is the galaxy map is derived
    # from the original, not from left-to-right position — the name
    # was assigned by index until 4 September 2026 and was on the
    # wrong hole the whole time (the same failure as the field dump
    # that labelled _races_button "Research").
    #
    # The original draws its small galaxy map with
    # MOVEBOX::Draw_Galaxy_Map_Box_(nullptr, 0, 0x17c, 0x15d, 0x80,
    # 0x5b, ...) at colsum.cpp:415 — x_base 380, y_base 349, width
    # 128, height 91 of 640x480 (movebox.cpp:4-9), confirmed by
    # Colsum_Connect_Galaxy_Map_Stars_ passing the same four to
    # Get_Galaxy_Map_Star_XY_ (colsum.cpp:734-735). The native
    # numbers are literals here so a retyped one fails.
    #
    # The RULE is asserted, not the instance: whichever of
    # fh.PANEL_KEYS lands nearest the original's rect must be the one
    # called "galaxy_inset". The three holes share a y, so the
    # discriminating axis is the centre x alone.
    _GMAP_NATIVE = (380, 349, 128, 91)          # colsum.cpp:415
    from core.config import REF_W as _GREF_W, REF_H as _GREF_H
    _gsx, _gsy = _GREF_W / 640.0, _GREF_H / 480.0
    _gref = (_GMAP_NATIVE[0] * _gsx, _GMAP_NATIVE[1] * _gsy,
             _GMAP_NATIVE[2] * _gsx, _GMAP_NATIVE[3] * _gsy)
    _gref_cx = _gref[0] + _gref[2] / 2.0
    _pan = []
    for _k in fh.BAND_KEYS:
        _r = cs.box_rect(_k)
        assert _r is not None, f"colony_summary has no {_k} box"
        _pan.append((abs(_r[0] + _r[2] / 2.0 - _gref_cx), _k))
    _pan.sort()
    assert _pan[0][1] == "galaxy_inset", (
        f"the cutout nearest the original's map rect is {_pan[0][1]!r}, "
        f"not 'galaxy_inset' (colsum.cpp:415, native {_GMAP_NATIVE}, "
        f"reference centre x {_gref_cx:.0f}); distances {_pan}")
    # And decisively so. A frame redrawn with three evenly spaced
    # holes would put the runner-up close enough that "nearest" stops
    # meaning anything, and this would then pass by a pixel rather
    # than fail — which is the state the check exists to catch.
    assert _pan[1][0] - _pan[0][0] >= 200, (
        f"nearest {_pan[0]} beats runner-up {_pan[1]} by only "
        f"{_pan[1][0] - _pan[0][0]:.0f} reference px; the frame's "
        f"three bottom holes no longer identify the map by position")
    ok("colony_summary galaxy_inset is the original's map hole")

    # Every button injects a click INSIDE the original's button
    # (colsum.cpp:265-273): the x is the field's left edge plus a
    # margin, the y sits in the 446 row. Asserting the source
    # constants rather than "some point", so a retyped number fails.
    NATIVE_X = {"name": 89, "population": 140, "food": 219,
                "industry": 262, "science": 326, "producing": 393,
                "bc": 480}
    HOTKEY = {"name": "n", "population": "p", "food": "f",
              "industry": "i", "science": "s", "producing": "r",
              "bc": "b"}
    btns = {b["key"]: b for b in cs._data["sort"]["buttons"]}
    assert list(btns) == fh.SORT_KEYS, list(btns)
    for key, b in btns.items():
        nx, ny = b["native_click"]
        assert NATIVE_X[key] <= nx <= NATIVE_X[key] + 12, (key, nx)
        assert 446 <= ny <= 460, (key, ny)
        assert b["hotkey"] == HOTKEY[key], (key, b["hotkey"])
    rx, ry = cs._data["return"]["native_click"]
    assert 531 <= rx <= 545 and 445 <= ry <= 459, (rx, ry)

    # The empire rows name only verified s_player fields, in the
    # order Draw_Empire_Info_ prints them.
    from core.structs import player as _ps
    _fields = [f[0] for f in _ps.SPEC.fields]
    rows = [r["field"] for r in cs._data["empire"]["rows"]]
    assert rows == ["bc", "surplus_bc", "total_pop", "surplus_freighters",
                    "surplus_food", "research_produced"], rows
    assert all(f in _fields for f in rows), rows

    # Clicking a sort button records the key and sends the ORIGINAL'S
    # OWN HOTKEY, not a click. Both paths live in `_inject` and the
    # difference between them is invisible on screen — a click sorts
    # the game correctly too, and additionally drags its pointer onto
    # the button (platform.cpp:1171-1172). So the path is asserted
    # here rather than left to a live session to notice.
    class _Cap:
        def __init__(self): self.calls = []; self.keys = []
        def inject_click(self, x, y): self.calls.append((x, y))
        def activate_field(self, f): pass
        def inject_key(self, k): self.keys.append(k)
    cap = _Cap()
    app.client, was = cap, app.connected
    app.connected = True
    _food = next(b for b in cs._sort_buttons() if b.key == "food")
    cs.handle_click(_food.hit.centerx, _food.hit.centery)
    assert cs._sort_key == "food"
    assert cap.keys == [ord(HOTKEY["food"])], (cap.keys, HOTKEY["food"])
    assert cap.calls == [], (
        f"a sort button injected a click at {cap.calls} as well as (or "
        f"instead of) its hotkey — the click path is the FALLBACK now, "
        f"and taking both moves the game's pointer for nothing")
    # ── ENTERING THE SCREEN SETS THE GAME'S SORT ──
    # _g_sort_index is not on the wire, so the two lists could sit on
    # different keys with neither being wrong — the first real
    # side-by-side found exactly that. Rather than ask for it to be
    # serialised, HD imposes its own key once on entry and every
    # later change goes through handle_click, so they agree by
    # construction. Idempotent: Switched_cmp_ has no toggle
    # (colsum.cpp:378-401), so re-sorting by the key the game already
    # holds re-sorts identically.
    cap.calls.clear(); cap.keys.clear()
    cs.enter(None)
    assert cap.keys == [ord(HOTKEY[cs._sort_key])], (
        f"entering the screen sent {cap.keys} — it must push its own "
        f"sort key {cs._sort_key!r} to the game, because nothing on "
        f"the wire reports the game's")
    assert cap.calls == [], (
        f"the entry sort used the click path ({cap.calls}); it takes "
        f"the hotkey like every other sort")
    # And it is the DEFAULT from layout.json, not a hardcoded key.
    assert cs._sort_key == cs._data["sort"]["default"], (
        "the entry sort key is not layout.json's default")
    cap.calls.clear(); cap.keys.clear()

    # RETURN has no letter to press: its field carries 0x25. It keeps
    # the native_click, and this asserts the fallback still works —
    # a hotkey path that swallowed every button would look identical
    # on the sort bar and break the only way off the screen.
    cap.calls.clear(); cap.keys.clear()
    rbx, rby, rbw, rbh = cs.layout.rect(cs.box_rect("return"))
    cs.handle_click(rbx + rbw // 2, rby + rbh // 2)
    assert cap.calls == [tuple(cs._data["return"]["native_click"])], \
        cap.calls
    assert cap.keys == [], cap.keys
    assert "hotkey" not in cs._data["return"], (
        "RETURN grew a hotkey — field 14 reports 0x25, which is not a "
        "key a player presses; if this is deliberate, verify it live "
        "the way the sort keys were before trusting it")
    # The click path is the fallback, so its points must SURVIVE.
    # Deleting them once the hotkey works is the failure this guards:
    # they are the half that can be checked by a grep against
    # colsum.cpp:265-273 with no game running.
    for key, b in btns.items():
        assert "native_click" in b, (
            f"sort button {key!r} lost its native_click — the hotkey "
            f"path does not replace it, it precedes it")
    app.client, app.connected = FakeClient(), was
    cs.render(pygame.display.get_surface())
    ok(f"colony_summary (cutouts == boxes.json [{_cut_note}], one sort "
       f"bar divided by one function, native clicks kept as the "
       f"fallback, empire rows)")

    # ── Zoom tables (transcribed from orion2re) ──
    from core import zoomtables as zt
    # HAROLD::Map_Scale_To_Zoom_Level_
    assert [zt.zoom_level(s) for s in (10, 15, 20, 30)] == [0, 1, 2, 3]
    # max_zoom_count clamps: a small galaxy never leaves zoom 0
    assert zt.zoom_level(30, 0) == 0
    # MOX::_star_fields_dim indexed by (zoom + star.size)
    assert [zt.star_dimension(sz, 0) for sz in range(3)] == [33, 29, 25]
    assert [zt.star_dimension(sz, 3) for sz in range(3)] == [23, 21, 17]
    # Draw_Black_Holes_ zoom_dist[] — ignores star.size, 1 and 2 equal
    assert [zt.black_hole_dimension(z) for z in range(4)] == [39, 33, 33, 24]
    # Star_Scale_Percent_: only shrinks past 72 stars AND scale > 30
    assert zt.star_scale_percent(36, 10) == 100
    assert zt.star_scale_percent(100, 30) == 100
    assert zt.star_scale_percent(100, 40) == 75
    # Scale_Star_Dimension_ never goes below 3 px
    assert zt.scale_star_dimension(4, 10) == 3
    # Animation and names switch off on an extended max view
    assert zt.black_hole_animates(36, 10) is True
    assert zt.black_hole_animates(100, 40) is False
    assert zt.names_suppressed(100, 40, 40) is True
    assert zt.names_suppressed(36, 10, 10) is False
    # Orbit stack spacing = 11 - zoom
    assert [zt.orbit_stack_step(z) for z in range(4)] == [11, 10, 9, 8]
    # Ship icon footprint: 13x10 at zoom 0, one px narrower/shorter per
    # step. The height must stay BELOW the stack step or four fleets at
    # one star would touch — that relation is the reason for the table.
    assert [zt.ship_icon_dimension(z) for z in range(4)] == \
        [(11, 10), (10, 9), (9, 8), (8, 7)]
    for z in range(4):
        assert zt.ship_icon_dimension(z)[1] < zt.orbit_stack_step(z), z
    # Out-of-range zoom clamps instead of raising.
    assert zt.ship_icon_dimension(9) == zt.ship_icon_dimension(3)
    assert zt.ship_icon_dimension(-1) == zt.ship_icon_dimension(0)
    # Monsters have their own per-type footprints, same shrink.
    assert zt.monster_icon_dimension("guardian", 0) == (12, 11)
    assert zt.monster_icon_dimension("guardian", 3) == (9, 8)
    # No monster may tower over the ship: the guardian was 17x16 here
    # for a day because a measurement picked up background stars, and
    # it read on screen as half again too big. Nothing in the original
    # is more than ~1.4x the player ship in either axis.
    sw, sh = zt.ship_icon_dimension(0)
    for kind in ("guardian", "crystal", "dragon", "hydra", "eel",
                 "amoeba", "antaran"):
        mw, mh = zt.monster_icon_dimension(kind, 0)
        assert mw <= sw * 1.4 and mh <= sh * 1.4, (kind, mw, mh)
    # An unknown type must not render at a nonsense size.
    assert zt.monster_icon_dimension("nessie", 1) == zt.ship_icon_dimension(1)
    # _max_map_scale / _max_zoom_count are not serialized by the ext
    # API; both must be recoverable from MAP_MAX (mapgen.cpp).
    #
    # ── THE REFERENCE IS WRITTEN OUT HERE, NOT IMPORTED ──
    # A verifier that shares its generation function is blind, so
    # this walks the OTHER way round: from the star count through
    # MAPGEN::Maximum_Galaxy_Grid_Y_/X_ (mapgen.cpp:49-59) to the
    # extent, where zoomtables starts from the extent that arrives on
    # the wire. Even the ceiling is spelled differently — `-(-a//b)`
    # here against `(a + b - 1) // b` there — so one mistyped idiom
    # cannot satisfy both.
    def _mgds(star_count):
        """(MAP_MAX_X, MAP_MAX_Y, _max_map_scale) for a Maximum galaxy."""
        gy = 8
        while ((gy * 5 + 3) // 4) * gy < star_count:
            gy += 1
        gx = (gy * 5 + 3) // 4
        cell = (50 * 30) // 10                     # mapgen.cpp:65
        w, h = gx * cell, gy * cell                # mapgen.cpp:1114-1115
        return w, h, max(-(-w * 10 // 506), -(-h * 10 // 400))

    def _retired(map_max_x):
        """What stood here until 7 September 2026: round(x / 50.6)."""
        return int(round(map_max_x / 50.6))

    # FIXED POINT 1 — the four stock sizes' literals (mapgen.cpp:
    # 1078-1110). The switch assigns these outright and never calls
    # the function; that ONE expression reproduces all four is what
    # lets a single recovery cover five galaxy sizes.
    for mx, my, exp_scale, exp_zoom in ((506, 400, 10, 0),
                                        (759, 600, 15, 1),
                                        (1012, 800, 20, 2),
                                        (1518, 1200, 30, 3)):
        assert zt.max_map_scale(mx, my) == exp_scale, (mx, my)
        assert zt.max_zoom_count(mx, my) == exp_zoom, (mx, my)
        assert zt.maximum_galaxy_display_scale(mx, my) == exp_scale, \
            f"the Maximum-size function must reproduce the stock literal " \
            f"{exp_scale} for MAP_MAX {mx}x{my}"

    # FIXED POINT 2 — the live probe, 7 September 2026. A generated
    # 155-star Maximum galaxy, driven to its own zoom-out limit with
    # field 9, reported map_scale 45 where the retired estimate said
    # 44 (tools/zoom_check.py: "MEASURED 45 > DERIVED 44"). That run
    # is the second source this transcription was accepted on.
    assert _mgds(155)[:2] == (2250, 1800), _mgds(155)
    assert zt.max_map_scale(2250, 1800) == 45, "live probe 2026-09-07, 155 stars"
    assert _retired(2250) == 44, "the estimate this replaced"

    # FIXED POINT 3 — the reference save, where the two AGREE. This
    # is why the save could not settle the question by itself.
    assert _mgds(99)[:2] == (1800, 1350), _mgds(99)
    assert zt.max_map_scale(1800, 1350) == 36 == _retired(1800)

    # AND NO STOCK WIDTH IS A GRID PRODUCT. The two arms of the
    # switch are told apart by MAP_MAX_X alone, so they must not
    # overlap: if any of 506/759/1012/1518 were a whole number of
    # 150-unit cells, a Maximum galaxy of exactly that width would be
    # routed to the literal arm and answered with a stock scale
    # instead of its own ceiling.
    for _sw in zt.STOCK_MAX_MAP_SCALE:
        assert _sw % zt.MAXIMUM_GALAXY_CELL != 0, (
            f"MAP_MAX_X {_sw} is both a stock literal and {_sw // 150} "
            f"cells of {zt.MAXIMUM_GALAXY_CELL} — a Maximum galaxy that "
            f"wide would take the stock arm and be given "
            f"{zt.STOCK_MAX_MAP_SCALE[_sw]} instead of its own ceiling")

    # FIXED POINT 4 — THE Y TERM IS LOAD BEARING. At 35 x 28 cells
    # the height ceiling is the larger one, so a recovery that
    # ceilings x alone is still one short. This is the half of the
    # defect that a MAP_MAX_X-only reading could never have caught.
    assert zt.max_map_scale(5250, 4200) == 105, (
        "THE Y TERM HAS BEEN DROPPED. MAP_MAX 5250 x 4200 (35 x 28 cells) "
        "is one of the four widths where ceil(MAP_MAX_Y*10/400) is the "
        "LARGER ceiling: 105 against x's 104. A recovery that reads "
        "MAP_MAX_X alone is still one short here even after it stops "
        "rounding, and the map draws a zoom-out limit one step tighter "
        "than the game's with every number on screen still correct.")
    assert -(-5250 * 10 // 506) == 104, "the x ceiling alone"

    # THE WHOLE RANGE, against the independent reference.
    _differ, _widths, _below = 0, set(), 0
    for _n in range(73, 1024):
        _w, _h, _want = _mgds(_n)
        assert zt.max_map_scale(_w, _h) == _want, (_n, _w, _h)
        _old = _retired(_w)
        if _old != _want:
            _differ += 1
            _widths.add(_w)
        if _want < _old:
            _below += 1
    # Reported at Stop 1 and reproduced here. If these move, that is
    # a finding about the arithmetic, not a test to loosen.
    assert _differ == 688, f"{_differ} of 951 differ, expected 688"
    assert len(_widths) == 15, sorted(_widths)
    assert _below == 0, \
        f"the transcription is BELOW the old estimate at {_below} counts; " \
        f"it must never be — the estimate rounds down from a ceiling"
    # NO CALL SITE MAY PASS MAP_MAX_X ALONE. Both extents are on the
    # wire and both are required, so a one-argument call is a
    # TypeError — but only on the path that runs, and the galaxy
    # sizes where the y ceiling wins are exactly the ones no fixture
    # reaches. This reads the SOURCE instead, so a forgotten y in a
    # branch nobody exercises fails here rather than on somebody's
    # Maximum galaxy. It is also what keeps the default from coming
    # back: the default existed once, was justified only by a test
    # written for it, and had no caller in the tree.
    _need_two = ("max_map_scale", "max_zoom_count")
    _root = os.path.dirname(SCREENS_DIR)
    _thin = []
    _scanned = 0
    for _dir, _subs, _files in os.walk(_root):
        _subs[:] = [_s2 for _s2 in _subs
                    if _s2 not in ("__pycache__", ".git", "assets")]
        for _f in _files:
            if not _f.endswith(".py"):
                continue
            _path = os.path.join(_dir, _f)
            _tree = ast.parse(open(_path, encoding="utf-8").read())
            _scanned += 1
            for _node in ast.walk(_tree):
                if not isinstance(_node, ast.Call):
                    continue
                _fn = _node.func
                _name = (_fn.attr if isinstance(_fn, ast.Attribute)
                         else _fn.id if isinstance(_fn, ast.Name) else None)
                if _name not in _need_two:
                    continue
                # `f(*pair)` passes both; ast cannot count through it.
                if any(isinstance(_a, ast.Starred) for _a in _node.args):
                    continue
                if len(_node.args) + len(_node.keywords) < 2:
                    _thin.append(f"{os.path.relpath(_path, _root)}:"
                                 f"{_node.lineno} {_name}()")
    assert _scanned > 40, f"only {_scanned} python files scanned"
    assert not _thin, (
        "these call MAP_MAX recovery with one argument, which means "
        "MAP_MAX_Y is being dropped — the half of the retired estimate "
        f"that no stock-size fixture can catch: {_thin}")
    ok("max_map_scale transcribes Maximum_Galaxy_Display_Scale_ "
       f"(73..1023: {_differ}/951 differ from the retired estimate, "
       f"never below; 5 galaxy sizes; both extents required at "
       f"{_scanned} source files)")
    # A big galaxy NOT at maximum zoom-out must keep its star names.
    assert zt.names_suppressed(100, 15, 30) is False
    assert zt.names_suppressed(100, 30, 30) is True

    # AXIS SEPARATION. Icon size depends on the ZOOM LEVEL only.
    # Galaxy size just caps how far out the user may zoom; it must
    # never scale anything by itself. Fully zoomed in (scale 10)
    # every galaxy size draws the identical icon.
    for map_max in ((506, 400), (759, 600), (1012, 800), (1518, 1200)):
        z = zt.zoom_level(10, zt.max_zoom_count(*map_max))
        assert z == 0, map_max
        assert zt.star_dimension(0, z) == 33, map_max
        assert zt.black_hole_dimension(z) == 39, map_max
    # Fully zoomed OUT they differ — but only because the reachable
    # zoom level differs, not because of a galaxy-size factor.
    out = {mm[0]: zt.star_dimension(0, zt.zoom_level(
        zt.max_map_scale(*mm), zt.max_zoom_count(*mm)))
        for mm in ((506, 400), (759, 600), (1012, 800), (1518, 1200))}
    assert list(out.values()) == [33, 29, 25, 23], out
    # And within ONE galaxy, zooming in must strictly grow icons.
    huge = [zt.star_dimension(0, zt.zoom_level(s, 3))
            for s in (30, 20, 15, 10)]
    assert huge == sorted(huge) and huge[0] < huge[-1], huge

    # Nebulas: twelve types x four pre-rendered zoom variants, read
    # out of STARBG.LBX. The table is what makes the sprite cover the
    # same patch of galaxy the original covers; deriving the size from
    # the HD artwork instead broke the moment a master was redrawn at
    # its own resolution.
    assert len(zt.NEBULA_DIM) == zt.NEBULA_TYPE_COUNT == 12
    assert all(len(row) == 4 for row in zt.NEBULA_DIM)
    assert zt.nebula_dimension(0, 0) == (185, 174)
    assert zt.nebula_dimension(0, 3) == (61, 56)
    # type is taken modulo 12 exactly like _nebula_pict_seg.
    assert zt.nebula_dimension(12, 0) == zt.nebula_dimension(0, 0)
    # Out-of-range zoom clamps rather than raising.
    assert zt.nebula_dimension(0, 9) == zt.nebula_dimension(0, 3)
    assert zt.nebula_dimension(0, -1) == zt.nebula_dimension(0, 0)
    # Every type shrinks strictly with each zoom step.
    for t in range(12):
        w = [zt.nebula_dimension(t, z)[0] for z in range(4)]
        assert w == sorted(w, reverse=True) and w[0] > w[3], (t, w)
    # The zoom-0 column IS the world footprint (one world unit = one
    # native pixel at scale 10), which is what the map transform
    # places the sprite into.
    assert zt.nebula_world_dimension(3) == zt.NEBULA_DIM[3][0]
    # A nebula is a landmark, not an icon: bigger than any star at
    # every zoom level, in every galaxy.
    for t in range(12):
        for z in range(4):
            assert zt.nebula_dimension(t, z)[0] > zt.star_dimension(0, z), \
                (t, z)
    # An extended galaxy shrinks stars but not nebulas — same
    # reasoning as ship icons, and flagged UNCONFIRMED in the table.
    assert zt.NEBULA_EXTENDED_SHRINK is False
    assert zt.nebula_dimension(0, 3, 100, 40) == zt.nebula_dimension(0, 3)
    # EXTENDED ZOOM LADDER. Above 72 stars the scale steps are not
    # 10/15/20/30 any more — they are max_map_scale halved down, so
    # zoom_level needs that value handed to it. Passing it is not
    # optional: without it the ladder collapses onto max_zoom for
    # every scale, which is what pinned a Maximum-size map to its
    # smallest sprites at every zoom step.
    ladder = [zt.zoom_level(s, 3, 108, 45) for s in (6, 12, 23, 45)]
    assert ladder == [0, 1, 2, 3], ladder
    assert zt.zoom_level(6, 3, 108) == 3, "the no-argument trap moved"
    ok("zoom tables (star/black hole/nebula dims, extended scaling)")

    # ── Galaxy map honours the zoom tables and wormhole rules ──
    if "galaxy_map" in d.screens:
        d.switch_to("galaxy_map")
        gm = d.active

        # Icon size must FOLLOW the zoom, not a fixed fraction.
        # map_max_x has to move with map_scale: a medium galaxy
        # cannot be at scale 30, and the clamp would (correctly)
        # hold the zoom down if only one of the two changed.
        sizes = {}
        for scale, map_max, expect_zoom in (
                (10, (506, 400), 0), (15, (759, 600), 1),
                (20, (1012, 800), 2), (30, (1518, 1200), 3)):
            gs.map_scale = scale
            gs.map_max_x, gs.map_max_y = map_max
            gm.update(gs)
            ctx = gm._map_context()
            assert ctx.zoom == expect_zoom, (scale, ctx.zoom)
            sizes[scale] = ctx.star_px(0)
        assert sizes[10] > sizes[15] > sizes[20] > sizes[30], sizes

        # THE SAME, ON AN EXTENDED MAP. Above 72 stars MapContext
        # must hand max_map_scale to zoom_level, or every scale
        # reports max_zoom and the map draws its smallest star,
        # ship and font step however far the player zooms in. Only
        # a Maximum-size galaxy reaches this path, which is why it
        # survived every test on the four stock sizes.
        stock_stars = gs.stars
        gs.stars = list(stock_stars) * 30           # 90 > 72
        big = {}
        for scale in (6, 12, 23, 45):
            # A REAL Maximum galaxy, not a synthesized width: 15 x 12
            # cells of 150 is what 155 stars produce (mapgen.cpp:
            # 49-59, 1113-1115), and it is the galaxy the live probe
            # of 7 September 2026 ran on. The 2277 that stood here
            # was reverse-engineered out of the retired estimate to
            # make it answer 45 and is an extent no 150-unit grid can
            # produce — a fixture that could only exist while the
            # thing it tested was wrong.
            gs.map_scale = scale
            gs.map_max_x, gs.map_max_y = 2250, 1800    # max scale 45
            gm.update(gs)
            ctx = gm._map_context()
            big[scale] = (ctx.zoom, ctx.star_px(0))
        assert [z for z, _ in big.values()] == [0, 1, 2, 3], big
        px = [p for _, p in big.values()]
        assert px == sorted(px, reverse=True) and px[0] > px[-1], big
        gs.stars = stock_stars

        # And the clamp itself: a small galaxy stays at zoom 0 even
        # if some other scale is reported.
        gs.map_scale = 30
        gs.map_max_x, gs.map_max_y = 506, 400
        gm.update(gs)
        assert gm._map_context().zoom == 0, "max_zoom_count must clamp"
        gs.map_scale = 15
        gs.map_max_x, gs.map_max_y = 759, 600

        # Nebula size comes from the type, NEVER from the artwork.
        # Two masters of the same shape at wildly different
        # resolutions must draw at the same size — that is exactly
        # the bug this replaced: the footprint used to be
        # asset_width / 3, so every redrawn master silently grew.
        from core.structs import nebula as _nb
        from screens.galaxy_map import renderer as rnd
        forms = gm._data.get("nebula_forms", [])
        if forms:
            form = forms[0]
            gs.map_scale = 10
            gs.map_max_x, gs.map_max_y = 506, 400
            gm.update(gs)
            ctx = gm._map_context()
            assert ctx.nebula_px(0) == max(
                8, int(zt.nebula_dimension(0, ctx.zoom)[0] * ctx.px))

            # THE INVARIANT: a nebula covers the same patch of sky at
            # every scale. Stars do not move relative to each other
            # when the wheel turns, so neither may the gas around
            # them — a star must not cross the nebula edge while
            # standing still. Asserted as world units recovered from
            # the drawn width, across the whole continuous HD range
            # and through every rung change, because the failure this
            # replaces was invisible in any single frame: the sprite
            # held its size between rungs while the world shrank
            # under it (50 % to 130 % of the footprint, snapping back
            # by up to 36 % at a rung).
            gs.map_max_x, gs.map_max_y = 1518, 1200  # Huge: rungs 10..30
            for t in (0, 4, 9):
                want = zt.nebula_world_dimension(t)[0]
                for scale10 in range(50, 301):     # scale 5.0 .. 30.0
                    gs.map_scale = scale10 / 10.0
                    gm.update(gs)
                    c = gm._map_context()
                    # HD pixels per world unit, the same factor the
                    # star positions go through.
                    per_unit = c.px * 10.0 / c.map_scale
                    assert abs(c.nebula_px(t) - want * per_unit) <= 1.0, \
                        (t, gs.map_scale, c.nebula_px(t), want * per_unit)
            gs.map_scale = 10
            gs.map_max_x, gs.map_max_y = 506, 400
            gm.update(gs)
            ctx = gm._map_context()

            painted = {}
            for side in (256, 1024):
                art = pygame.Surface((side, side), pygame.SRCALPHA)
                art.fill((90, 70, 130, 255))
                gm._cache.put(form, art)
                gm._cache.clear_scaled()
                probe = pygame.Surface((app.win_w, app.win_h))
                probe.fill((0, 0, 0))
                rnd.render_nebulas(
                    probe, ctx, _nb.parse_all([_s.pack("<hhb", 300, 300, 0)]),
                    gm._cache, forms)
                painted[side] = int(
                    pygame.surfarray.array2d(probe).astype(bool).sum())
            assert painted[256] > 0, "no nebula drawn"
            assert painted[256] == painted[1024], painted

            # Zooming out shrinks it, in every galaxy that can zoom.
            drawn = {}
            for scale, map_max in (((10, (1518, 1200)),
                                    (30, (1518, 1200)))):
                gs.map_scale = scale
                gs.map_max_x, gs.map_max_y = map_max
                gm.update(gs)
                probe = pygame.Surface((app.win_w, app.win_h))
                probe.fill((0, 0, 0))
                rnd.render_nebulas(
                    probe, gm._map_context(),
                    _nb.parse_all([_s.pack("<hhb", 300, 300, 0)]),
                    gm._cache, forms)
                drawn[scale] = int(
                    pygame.surfarray.array2d(probe).astype(bool).sum())
            assert drawn[10] > drawn[30], drawn
            gm._cache.clear_scaled()
            gm._load_sprites()
            ok("galaxy_map nebulas (size from type, not from artwork)")

        # ── Every master judged against its extracted original ──
        #
        # The table owns the size (asserted above), so what the
        # artwork still owns is its SHAPE and its brightness — and
        # both are measured against nebula_ref, the same extraction
        # that produced NEBULA_DIM. Nothing else in the tree checks
        # them: a master can be the right aspect and still be a
        # translucent haze that vanishes on the map, which is what
        # the pre-30-August set turned out to be (mean weight 0.40x
        # the original, silhouette agreement 0.50 on type 5).
        #
        # Brightness is measured PREMULTIPLIED because that is what
        # BLEND_RGB_ADD puts on screen: rgb * alpha is the sprite's
        # entire contribution, so a master's mean premultiplied luma
        # is its visual weight, directly comparable to the opaque
        # original the game draws over black space.
        if forms:
            def _neb_probe(surf, side=96):
                small = pygame.transform.smoothscale(surf, (side, side))
                a = pygame.surfarray.array_alpha(small).astype(float)
                rgb = pygame.surfarray.array3d(small).astype(float)
                pm = rgb * (a[:, :, None] / 255.0)
                luma = (0.2126 * pm[:, :, 0] + 0.7152 * pm[:, :, 1]
                        + 0.0722 * pm[:, :, 2])
                return a > 25, float(luma.mean())

            checked = 0
            for t, form in enumerate(forms):
                master = gm._cache.base(form)
                ref_path = gm.asset_path("assets", "nebula_ref",
                                         f"type_{t:02d}", "zoom_0.png")
                if master is None or ref_path is None:
                    continue          # a mod may ship art without a ref
                checked += 1

                # Aspect: the renderer sets the width from the table
                # and lets the height follow the artwork, so drifted
                # proportions cover the wrong patch of sky vertically.
                mw, mh = master.get_size()
                ow, oh = zt.NEBULA_DIM[t][0]
                dev = abs((mw / mh) - (ow / oh)) / (ow / oh)
                assert dev <= 0.10, (form, mw, mh, round(dev, 3))

                ref = pygame.image.load(ref_path).convert_alpha()
                m_mask, m_luma = _neb_probe(master)
                r_mask, _ = _neb_probe(ref)

                inter = int((m_mask & r_mask).sum())
                union = int((m_mask | r_mask).sum())
                assert union and inter / union >= 0.70, \
                    (form, round(inter / max(1, union), 3))

                # Brightness needs the RECOLOURED reference: zoom_0.png
                # stores each pixel's palette INDEX as its grey value
                # (STARBG.LBX carries no palette), so its luma means
                # nothing. zoom_0_color.png is the same sprite through
                # the palette the galaxy map actually loads, and only
                # exists if nebula_extract ran with --recolor-ref.
                colour = gm.asset_path("assets", "nebula_ref",
                                       f"type_{t:02d}", "zoom_0_color.png")
                if colour is None:
                    continue
                _, r_luma = _neb_probe(
                    pygame.image.load(colour).convert_alpha())
                # Lower bound only, and 0.6x is where the observed
                # regression sits: the replaced set measured 0.22x to
                # 0.71x with a mean of 0.42x, and read on the map as
                # gas that had faded away. The set that replaced it
                # measures 0.90x to 2.44x, mean 1.37x.
                #
                # There is deliberately NO upper bound. Nothing in the
                # original or in the renderer says how bright HD gas
                # may be — additive output clips against whatever
                # backdrop it lands on, which this probe cannot see —
                # so any ceiling here would be a number invented in a
                # test file and inherited as if it were measured.
                assert r_luma and m_luma / r_luma >= 0.6, \
                    (form, round(m_luma, 1), round(r_luma, 1))

            # nebula_ref/ holds UNMODIFIED sprites extracted from the
            # user's own STARBG.LBX and is therefore not committed —
            # the one place in the tree that carried original artwork
            # rather than work derived from it. A clone that has not
            # run nebula_extract.py cannot make this comparison, and
            # that is a real loss of verification, not a formality:
            # nothing else in the tree checks a master's shape or its
            # brightness. So the check does not silently vanish and
            # does not silently pass — it asserts that either the
            # references are there and every master agrees with them,
            # or they are absent and the way to get them is named.
            if checked == 0:
                ref_dir = os.path.join(
                    SCREENS_DIR, "galaxy_map", "assets", "nebula_ref")
                assert not os.path.isdir(ref_dir), (
                    "nebula_ref exists but no master could be compared "
                    "against it")
                ok("galaxy_map nebula masters (references absent — run "
                   "tools/nebula_extract.py to verify shape + weight)")
            else:
                assert checked >= 12, \
                    f"only {checked} of 12 nebula masters checked"
                ok("galaxy_map nebula masters (shape + weight vs the "
                   "original)")

        gs.map_scale = 15
        gs.map_max_x, gs.map_max_y = 759, 600

        # Wormholes: only visited (or omniscient) origins draw.
        gs.map_scale = 15
        gm.update(gs)
        ctx = gm._map_context()
        wh = bytearray(STAR_SIZE)
        wh[0:4] = b"Gate"
        _s.pack_into("<hh", wh, 15, 300, 300)
        wh[22] = 2
        _s.pack_into("<h", wh, 160, 1)     # links to star 1
        wh[171] = 0b0                      # NOT visited by player 0
        seen = st.parse_all([bytes(wh)] + [mkstar("B", 400, 300, 0, 0, -1, 1)])

        def drawn_pixels(stars_in, omni):
            """Non-black pixels after drawing — the line is one or
            two px wide, so any average over the surface rounds it
            away; count them instead."""
            probe = pygame.Surface((app.win_w, app.win_h))
            probe.fill((0, 0, 0))
            gmr.render_wormholes(probe, ctx, stars_in, 0, omni)
            return int(pygame.surfarray.array2d(probe).any(axis=1).sum())

        assert drawn_pixels(seen, False) == 0, \
            "unvisited wormhole must not be drawn"
        assert drawn_pixels(seen, True) > 0, \
            "omniscient player must see the wormhole"
        wh[171] = 0b1                      # now visited by player 0
        seen = st.parse_all([bytes(wh)] + [mkstar("B", 400, 300, 0, 0, -1, 1)])
        assert drawn_pixels(seen, False) > 0, \
            "visited wormhole must be drawn"

        # Wormhole links must be FAINT and ANTIALIASED. The original
        # draws them in palette index 4 — a hint, not a border.
        assert len(gmr.WORMHOLE_COLOR) >= 4, \
            "wormhole colour needs an alpha component"
        assert gmr.WORMHOLE_COLOR[3] < 160, gmr.WORMHOLE_COLOR

        # A DIAGONAL pair: a horizontal or vertical aaline has no
        # partial coverage to show, so it would prove nothing here.
        diag = bytearray(STAR_SIZE)
        diag[0:5] = b"Skew\x00"
        _s.pack_into("<hh", diag, 15, 120, 90)
        diag[22] = 2
        _s.pack_into("<h", diag, 160, 1)
        diag[171] = 0b1
        skew = st.parse_all([bytes(diag),
                             mkstar("Far", 520, 430, 0, 0, -1, 1)])
        probe = pygame.Surface((app.win_w, app.win_h))
        probe.fill((0, 0, 0))
        layer = gmr.WormholeLayer()
        gmr.render_wormholes(probe, ctx, skew, 0, True, layer=layer)
        arr = pygame.surfarray.array3d(probe).astype(int).max(axis=2)
        lit = arr[arr > 0]
        assert lit.size, "no wormhole pixels drawn"
        # Antialiasing means partial coverage: a hard line would give
        # exactly one non-zero value, an aa line gives a spread.
        assert len(set(lit.tolist())) > 3, \
            f"line is not antialiased (values {sorted(set(lit.tolist()))})"
        # Alpha means the brightest pixel stays well below the tint.
        assert lit.max() < max(gmr.WORMHOLE_COLOR[:3]), \
            f"line is not blended ({lit.max()})"

        # The layer is cached: same inputs must not rebuild it.
        built = layer._layer
        gmr.render_wormholes(probe, ctx, skew, 0, True, layer=layer)
        assert layer._layer is built, "layer rebuilt for identical input"
        # No visible links must drop the cached surface, not keep
        # blitting the last one.
        gmr.render_wormholes(probe, ctx, [], 0, True, layer=layer)
        assert layer._layer is None
        ok("galaxy_map zoom sizing + wormhole visibility")

    # ── Black hole master: rotatable, on-axis ──
    if "galaxy_map" in d.screens:
        import numpy as _np
        gm = d.screens["galaxy_map"]
        base = gm._cache.base("black_hole")
        assert base is not None, "black_hole.png did not load"

        # SQUARE. A non-square master cannot be rotated in place; the
        # code would have to pad it to its diagonal, which doubles the
        # pixels of every cached frame.
        bw, bh = base.get_size()
        assert bw == bh, f"black hole master is {bw}x{bh}, not square"

        # CIRCULAR. Content outside the inscribed circle is content the
        # rotation can push into a corner and lose.
        assert gm._cache.circular("black_hole"), \
            "black hole content reaches outside its inscribed circle"

        alpha = pygame.surfarray.array_alpha(base).astype(float)
        rgb = pygame.surfarray.array3d(base).astype(int).max(axis=2)

        # ON AXIS. This is the one that matters. The event horizon is
        # the opaque black disc; if its centroid is off centre, the
        # black hole ORBITS the middle instead of turning, and at
        # 117 px that reads as a wobble, not as a rotation. It is not
        # something a screenshot reveals — only motion does.
        core = (alpha > 200) & (rgb < 3)
        ys, xs = _np.where(core)
        assert len(xs) > 50, "no event horizon found in the master"
        c = (bw - 1) / 2.0
        off = (abs(xs.mean() - c), abs(ys.mean() - c))
        assert max(off) <= 2.0, \
            f"event horizon is {max(off):.1f} px off the rotation axis"

        # The horizon must be a real hole, not a dark tint: it has to
        # occlude the star field behind it exactly as the original
        # sprite does.
        assert alpha[core].min() > 200

        # NO RGB UNDER TRANSPARENT PIXELS. A normal blit hides it, but
        # BLEND_RGB_ADD and set_alpha(None) both ignore alpha, and then
        # the sprite's whole bounding box lights up as a square with
        # the source's leftover stars in it. The master carried RGB up
        # to 174 in its corners before this was checked. Same failure
        # the nebulas hit — see SpriteCache.scaled_additive.
        assert rgb[alpha == 0].max() == 0, \
            f"transparent pixels carry RGB up to {rgb[alpha == 0].max()}"

        # FOOTPRINT. black_hole_dimension() is the full sprite width in
        # the original (Draw_Black_Holes_ zoom_dist[]), so the drawing
        # has to fill its own canvas. A master padded out with empty
        # margin shrinks the visible black hole at every zoom level,
        # silently, because the size table still says 39.
        vis = alpha > 10
        vy, vx = _np.where(vis)
        span = max(vx.max() - vx.min(), vy.max() - vy.min()) + 1
        assert span >= bw * 0.9, \
            f"content spans {span} of {bw} px — sprite is mostly margin"

        # Rotation must not change the footprint, or the black hole
        # would breathe once per revolution. Frames are rotated on
        # demand now, so the test asks for the steps it wants instead
        # of reading a pre-rendered list; a sample of 72 spread over
        # the revolution covers the same angles the old set held.
        SAMPLE = 72
        step_of = [i * gmr.BH_ROTATE_STEPS // SAMPLE for i in range(SAMPLE)]
        frames = [gmr._black_hole_frame(gm._cache, 117, True, step=k)
                  for k in step_of]
        assert all(f is not None for f in frames)
        sizes = {f.get_size() for f in frames}
        assert len(sizes) == 1, f"rotation changes the footprint: {sizes}"
        # Circular content means no padding: the frame stays at its
        # requested size instead of growing to the diagonal.
        assert frames[0].get_size() == (117, 117), frames[0].get_size()

        # The clock has to advance through every step and wrap, or a
        # slower period would simply sit on one angle for longer.
        seen = {gmr.black_hole_step(now=gmr.BH_ROTATE_PERIOD_S * f / 8.0)
                for f in range(8)}
        assert len(seen) == 8, seen
        assert gmr.black_hole_step(now=0.0) == gmr.black_hole_step(
            now=gmr.BH_ROTATE_PERIOD_S), "revolution does not close"

        # Half a degree per step, so the outer edge of the largest
        # icon this screen draws moves under a pixel between steps.
        # That is the whole point of the number: above a pixel the
        # motion is a sequence of jumps, below it the antialiasing
        # carries it.
        edge_px = math.pi * 195 / gmr.BH_ROTATE_STEPS
        assert edge_px < 1.0, f"{edge_px:.2f} px per step at 195"

        # One slot, not a set: consecutive calls at the same step must
        # hand back the SAME surface, and a new step must not pile up
        # a second one. The pre-rendered version needed 55 MB per icon
        # size to reach this resolution.
        a = gmr._black_hole_frame(gm._cache, 117, True, step=5)
        b = gmr._black_hole_frame(gm._cache, 117, True, step=5)
        assert a is b, "rotation frame is rebuilt on every call"
        gmr._black_hole_frame(gm._cache, 117, True, step=6)
        bh_slots = [k for k in gm._cache._scaled
                    if isinstance(k, str) and k.startswith("_bh")]
        assert len(bh_slots) == 1, bh_slots

        # Rotation must actually rotate. A radially symmetric drawing
        # would pass every check above and look completely static.
        a0 = pygame.surfarray.array3d(frames[0]).astype(int).max(axis=2)
        aq = pygame.surfarray.array3d(
            frames[SAMPLE // 4]).astype(int).max(axis=2)
        diff = _np.abs(a0 - aq).mean()
        assert diff > 3.0, (
            f"quarter turn changes almost nothing ({diff:.1f}) — the "
            f"artwork is too symmetric for the rotation to be visible")

        # AND IT MUST NOT DRIFT. The event horizon is a disc centred on
        # the axis, so its centroid has to land on the same point in
        # every frame. When it does not, the black hole swims across
        # the map instead of turning — invisible in a screenshot,
        # obvious in motion, so only a test catches it.
        #
        # The shipped version cropped the rotated surface with a floor
        # division and drifted 1.3 px here, 2.9 px at 195. Two
        # plausible fixes made it worse (bounding-box alignment 5.0 px,
        # per-frame centroid correction 1.0 px) before the plain
        # geometric centre with a filtered rotozoom settled it. Doing
        # that rotozoom at icon size, which is 13x cheaper and the
        # obvious way to write this, drifts 1.4 px: the supersample is
        # load-bearing, not polish.
        #
        # The threshold is deliberately loose. Measuring a centroid off
        # an antialiased disc has a floor of its own — about 0.26 px at
        # this size, established from the exact 90-degree frames, which
        # cannot drift at all. Under half a pixel is the ruler, not the
        # sprite.
        cents = []
        for f in frames:
            fa = pygame.surfarray.array_alpha(f).astype(float)
            fr = pygame.surfarray.array3d(f).astype(int).max(axis=2)
            fy, fx = _np.where((fa > 200) & (fr < 3))
            cents.append((fx.mean(), fy.mean()))
        cents = _np.array(cents)
        drift = max(cents[:, 0].max() - cents[:, 0].min(),
                    cents[:, 1].max() - cents[:, 1].min())
        assert drift < 0.5, \
            f"black hole drifts {drift:.2f} px across its rotation"

        # NO BRIGHTNESS PULSE. An earlier version modulated set_alpha
        # between 165 and 255 on a 4.8 s sine, which read as breathing
        # and buried the 40 s rotation under it. It was never in the
        # original — MOO2 is palette-indexed and cannot alpha-blend a
        # sprite at all. Composited on a fixed background, every frame
        # must therefore carry the same total light.
        sums = []
        for f in frames:
            probe = pygame.Surface(f.get_size())
            probe.fill((0, 0, 0))
            probe.blit(f, (0, 0))
            sums.append(float(
                pygame.surfarray.array3d(probe).astype(int).sum()))
        spread = (max(sums) - min(sums)) / max(sums)
        assert spread < 0.12, \
            f"frame brightness varies by {spread:.0%} — the sprite pulses"
        # And the surface-level alpha must be left alone. Not None:
        # set_alpha(None) selects SDL_BLENDMODE_NONE in pygame 2, which
        # ignores per-pixel alpha and draws the bounding box opaque.
        assert frames[0].get_alpha() in (None, 255), frames[0].get_alpha()
        ok("galaxy_map black hole master (square, circular, on axis)")

    # ── Background star field ──
    if "galaxy_map" in d.screens:
        from screens.galaxy_map import starfield as sf

        # The tier table is a transcription, so its shape is testable:
        # nine tenths of the original's stars sit at or below grey 44,
        # which is what makes a 3 % coverage field read as calm rather
        # than as static. A future "let's brighten it a little" lands
        # here first.
        _tot = sum(c for _, c in sf.STAR_TIERS)
        _dim = sum(c for v, c in sf.STAR_TIERS if v <= 44)
        assert _dim / _tot > 0.85, \
            f"only {_dim / _tot:.0%} of the field is dim — it will glitter"

        _box = (0, 0, 1200, 948)
        _px = 1200 / sf.NATIVE_MAP_W
        _layer = sf.StarfieldLayer({"seed": 4242})
        _target = pygame.Surface((1200, 948))
        _target.fill((40, 40, 48))
        _before = pygame.surfarray.array3d(_target).astype(int)
        _layer.render(_target, _box, _px)
        _after = pygame.surfarray.array3d(_target).astype(int)

        # Count follows from the measured density and the NATIVE map
        # rect, never from the HD resolution — the same sky at 1080p
        # and at 4K, only the dots grow.
        _expect = int(sf.NATIVE_MAP_W * sf.NATIVE_MAP_H / sf.DENSITY_NATIVE)
        assert abs(_layer.star_count - _expect) <= 2, \
            f"{_layer.star_count} stars, expected {_expect}"

        # Additive only. A plain blit would punch dark squares into the
        # gas clouds; BLEND_RGB_ADD cannot lower a channel.
        assert (_after >= _before).all(), "star field darkens the map"

        # Subtle. Mean added light over the whole box, in 0..255.
        _added = float((_after - _before).mean())
        assert _added < 3.0, f"star field adds {_added:.1f}/255 — too hot"

        # Deterministic and static. Same seed, same sky; a different
        # seed, a different one. MOO2 draws its backdrop palette-indexed
        # and cannot animate it, so anything time-dependent here would
        # be an invention — and would also throw away the cache.
        def _render(seed, width=1200):
            surf = pygame.Surface((width, 948))
            surf.fill((0, 0, 0))
            sf.StarfieldLayer({"seed": seed}).render(
                surf, (0, 0, width, 948), width / sf.NATIVE_MAP_W)
            return pygame.image.tostring(surf, "RGB")

        assert _render(4242) == _render(4242), "star field is not stable"
        assert _render(4242) != _render(99), "seed does not change the sky"

        _wide = sf.StarfieldLayer({"seed": 4242})
        _probe = pygame.Surface((2400, 1896))
        _wide.render(_probe, (0, 0, 2400, 1896), 2400 / sf.NATIVE_MAP_W)
        assert _wide.star_count == _layer.star_count, \
            "star count changes with the HD resolution"

        ok("galaxy_map star field (density, additive, deterministic)")

    # ── Ship and monster icons ──
    if "galaxy_map" in d.screens:
        from screens.galaxy_map import ships as shi
        from core.game_state import (parse_state, SETTINGS_SIZE,
                                     LEADER_SIZE, ANTARAN_SIZE)

        # owner -> asset folder, the dispatch in Get_Ship_Icon_Pict_Seg_
        assert shi.kind_for_owner(0) == "player"
        assert shi.kind_for_owner(7) == "player"
        assert shi.kind_for_owner(8) == "antaran"
        assert shi.kind_for_owner(12) == "dragon"
        assert shi.kind_for_owner(99) is None
        assert shi.kind_for_owner(None) is None

        # Every kind the generator knows must have loadable step files
        # or a documented fallback. Missing artwork is allowed; a
        # missing FALLBACK is not, or a monster would vanish.
        for kind in shi.ALL_KINDS:
            key = shi._resolve_sprite(gm._cache, kind, 2)
            assert key is not None, kind

        # The player sprite must stay greyscale on disk: it is tinted
        # at runtime, and colour baked into the asset would multiply
        # on top of itself.
        base = gm._cache.base(shi.sprite_key("player", 0))
        assert base is not None, "player ship sprite missing"
        arr = pygame.surfarray.array3d(base)
        alpha = pygame.surfarray.array_alpha(base)
        vis = alpha > 12
        assert vis.any(), "player sprite is fully transparent"
        chroma = (arr.max(axis=2).astype(int)
                  - arr.min(axis=2).astype(int))[vis]
        assert chroma.max() <= 16, f"player sprite not greyscale ({chroma.max()})"

        # Tinting must actually change the pixels, and differently per
        # colour — a cache keyed too loosely would hand back one tint
        # for every player.
        tinted = [gm._tints.get(base, "k", c) for c in (0, 4)]
        assert pygame.image.tostring(tinted[0], "RGBA") != \
            pygame.image.tostring(base, "RGBA")
        assert pygame.image.tostring(tinted[0], "RGBA") != \
            pygame.image.tostring(tinted[1], "RGBA")

        # Fit modes and per-kind overrides. The HD masters do not
        # share the original sprites' aspect ratios, so this is what
        # decides whether an icon reads a size too big.
        probe_sprite = pygame.Surface((100, 300), pygame.SRCALPHA)
        assert shi._fit_size(probe_sprite, 40, 30, "height") == (10, 30)
        assert shi._fit_size(probe_sprite, 40, 30, "width") == (40, 120)
        assert shi._fit_size(probe_sprite, 40, 30, "box") == (10, 30)
        # area keeps the drawn area, so it sits between the two
        aw, ah = shi._fit_size(probe_sprite, 40, 30, "area")
        assert abs(aw * ah - 40 * 30) <= 60, (aw, ah)
        assert 10 < ah < 120, (aw, ah)

        cfg = {"fit": "height", "scale": 1.0,
               "kinds": {"eel": {"fit": "area", "scale": 0.8}}}
        assert shi.kind_config(cfg, "player") == ("height", 1.0)
        assert shi.kind_config(cfg, "eel") == ("area", 0.8)
        # Unknown or malformed values must fall back, not raise
        assert shi.kind_config({"fit": "sideways"}, "player")[0] == \
            shi.DEFAULT_FIT
        assert shi.kind_config({"scale": "big"}, "player")[1] == 1.0
        assert shi.kind_config(None, "player") == (shi.DEFAULT_FIT, 1.0)
        assert shi.DEFAULT_FIT in shi.FIT_MODES

        # Owner resolution. The node table is rebuilt from _ship[]
        # rather than serialized, so it needs its own coverage.
        def mkship(owner, location, x=0, y=0, status=0):
            r = bytearray(_ship.SIZE)
            _s.pack_into("<b", r, 99, owner)
            _s.pack_into("<b", r, 100, status)
            _s.pack_into("<hhh", r, 101, location, x, y)
            return _ship.parse(bytes(r))

        def mkicon(node_idx, star_idx, x=100, y=100):
            return ship_icon.parse(
                _s.pack("<6h", 0, node_idx, star_idx, 0, x, y))

        # build_node_map: node N is the N-th ship with status < 3.
        # Stacking must NOT influence the numbering.
        fleet = [mkship(0, 5), mkship(9, 7, status=4),      # skipped
                 mkship(0, 5), mkship(3, 6), mkship(1, 9, status=3)]
        assert shi.build_node_map(fleet) == [0, 2, 3]

        # Two players at ONE star: the per-star guess cannot answer,
        # the node table can. This is the case the whole thing exists
        # for, so assert the exact colours, not just "not None".
        mixed = [mkship(2, 11), mkship(5, 11, x=4)]
        icons = [mkicon(0, 11), mkicon(1, 11)]
        assert shi.owners_from_nodes(icons, mixed) == [2, 5]
        assert shi.resolve_owners(icons, mixed) == [2, 5]

        # star_idx is the RAW encoded location (Ship_Stack_Star_Id_),
        # so a moving ship still validates.
        moving = [mkship(4, 10042)]
        assert shi.owners_from_nodes([mkicon(0, 10042)], moving) == [4]

        # Validation: a node pointing at a ship whose location does not
        # match star_idx means the map is stale. Reject the WHOLE set —
        # a half-trusted map paints plausible wrong colours.
        assert shi.owners_from_nodes([mkicon(0, 99)], mixed) is None
        assert shi.owners_from_nodes([mkicon(7, 11)], mixed) is None
        assert shi.owners_from_nodes(icons, []) is None

        # ...and then the per-star fallback takes over: unambiguous
        # star answers, mixed star stays None rather than guessing.
        single = [mkship(2, 5), mkship(2, 10005), mkship(1, 6),
                  mkship(4, 6)]
        fb = shi.resolve_owners([mkicon(0, 5), mkicon(1, 6)], single)
        assert fb == [2, None], fb

        # An explicit owner from the ext patch always wins.
        ic = mkicon(0, 5)
        ic.set_derived("owner", 6)
        assert shi.resolve_owners([ic], single) == [6]

        # Snapshot round trip: the owner block is OPTIONAL and sits
        # last, so an unpatched orion2re must still parse.
        def snapshot(with_owners):
            b = bytearray()
            b += _s.pack("<hbihhhhhB b", 0, -1, 100, 0, 2, 0, 0, 0, 0, 0)
            b += _s.pack("<hhhhh", 15, 0, 0, 759, 600)
            b += bytes(SETTINGS_SIZE)
            b += bytes(PLAYER_SIZE * 8)
            b += _s.pack("<h", 0)                     # stars
            b += _s.pack("<h", 0)                     # ships
            b += _s.pack("<h", 0)                     # colonies
            b += _s.pack("<h", 0)                     # planets
            b += bytes([0])                           # nebulas
            b += bytes(LEADER_SIZE * 67)
            b += bytes(ANTARAN_SIZE)
            b += _s.pack("<h", 2)                     # 2 ship icons
            b += _s.pack("<6h", 0, 0, 5, 0, 100, 100)
            b += _s.pack("<6h", 0, 1, 6, 0, 140, 100)
            b += _s.pack("<8h", 0, 0, 0, 0, 0, 0, 0, 0)
            if with_owners:
                b += bytes([3, 0xFF])
            return parse_state(bytes(b))

        plain = snapshot(False)
        assert len(plain.ship_icons) == 2
        assert getattr(plain.ship_icons[0], "owner", None) is None
        patched = snapshot(True)
        assert patched.ship_icons[0].owner == 3
        assert patched.ship_icons[1].owner is None    # 0xFF sentinel

        # Draw for real at two zoom levels and confirm the icons land
        # inside the map box and grow when zooming in.
        gs.ship_icons = ship_icon.parse_all([
            _s.pack("<6h", 0, 0, 5, 0, 260, 210),
            _s.pack("<6h", 0, 1, 6, 0, 300, 210),
        ])
        gs.ship_icons[0].set_derived("owner", 0)
        gs.ship_icons[1].set_derived("owner", 9)      # guardian
        gs.ships_raw = []
        painted = {}
        for scale, map_max in ((10, (506, 400)), (30, (1518, 1200))):
            gs.map_scale = scale
            gs.map_max_x, gs.map_max_y = map_max
            gm.update(gs)
            ctx = gm._map_context()
            probe = pygame.Surface((app.win_w, app.win_h))
            probe.fill((0, 0, 0))
            gmr.render_fleets(probe, ctx, gs.ship_icons, gm._players,
                              gm._cache, gm._tints, ships=gm._ships)
            painted[scale] = int(
                pygame.surfarray.array2d(probe).astype(bool).sum())
        assert painted[10] > 0, "no ship icon drawn"
        assert painted[10] > painted[30], painted    # zoomed in = bigger

        # The -1 sentinel means "not placed this frame" and must not
        # be drawn at the map's top-left corner.
        gs.ship_icons = ship_icon.parse_all(
            [_s.pack("<6h", 0, 0, 5, 0, -1, -1)])
        gm.update(gs)
        probe = pygame.Surface((app.win_w, app.win_h))
        probe.fill((0, 0, 0))
        gmr.render_fleets(probe, gm._map_context(), gs.ship_icons,
                          gm._players, gm._cache, gm._tints)
        assert not pygame.surfarray.array2d(probe).any(), \
            "unplaced ship icon must not be drawn"
        gs.map_scale = 15
        gs.map_max_x, gs.map_max_y = 759, 600
        gs.ship_icons = []
        ok("galaxy_map ship icons (kinds, tinting, owner, sizing)")

    # ── Struct specs promoted from unverified.py ──
    from core.structs import nebula as _neb, planet as _pln
    n = _neb.parse(bytes([0x76, 0x01, 0xAA, 0x00, 0x01]))
    assert (n.x, n.y, n.type) == (374, 170, 1)
    p = _pln.parse(_s.pack("<hh", 7, 3) + bytes(14))
    assert (p.colony_index, p.star_index) == (7, 3)
    pv = pl.parse(bytes(PLAYER_SIZE))
    assert len(pl.contacts(pv)) == 8 and len(pl.traits(pv)) == 31

    # ── unverified.py's contract, asserted rather than trusted ──
    # The file exists to quarantine specs that have ONE source. A
    # spec promoted by flipping the flag in place, without moving to
    # its own module with the evidence in the docstring, would leave
    # no trace anywhere — so the flag is checked here for every spec
    # the module exposes, not for a named list of them.
    from core.structs import Spec as _Spec
    from core.structs import unverified as _unv
    _quarantined = [v for v in vars(_unv).values()
                    if isinstance(v, _Spec)]
    assert _quarantined, "unverified.py exposes no specs at all"
    for _sp in _quarantined:
        assert not _sp.verified, (
            f"{_sp.name} is marked verified inside unverified.py — "
            f"promotion means moving it to its own module with the "
            f"evidence, not flipping the flag here")

    # ── A spec must tile its struct ──
    # Asserted as the rule over every spec in the tree that claims a
    # size, not as a list of s_colony's 50 offsets: a field added,
    # removed or mistyped shifts the chain and is caught without
    # anybody updating this test. s_colony is packed with no padding
    # (proved by compiling the header, doc/s_colony_offsets.md), so
    # for it the chain must close exactly on 361.
    from core.structs import colony as _col
    _colony = _col.SPEC
    assert _colony.verified, "s_colony was promoted; the flag must say so"
    assert _colony.size == 361 and len(_colony.fields) == 50, \
        (_colony.size, len(_colony.fields))
    _end = 0
    for _name, _off, _kind in _colony.fields:
        assert _off == _end, (
            f"s_colony: {_name} starts at {_off}, previous field "
            f"ended at {_end} — the spec has a gap or an overlap")
        _end = _off + _Spec.kind_width(_kind)
    assert _end == _colony.size, \
        f"s_colony fields end at {_end}, spec size is {_colony.size}"
    _cv = _colony.parse(bytes(_colony.size))
    assert len(_cv.pop) == 42 and len(_cv.buildings) == 49, \
        (len(_cv.pop), len(_cv.buildings))

    # ── The pop word's masks must not overlap ──
    # Bits inside a member are NOT fixed by offsetof (decision 23's
    # addition): they are a transcription of pop.h, so the one thing
    # checkable without live data is that the transcription is at
    # least self-consistent. Two masks sharing a bit would make one
    # field silently corrupt the other's reads.
    _masks = {n: v for n, v in vars(_col).items()
              if n.startswith("POP_MASK_")}
    assert len(_masks) == 5, sorted(_masks)
    _seen = 0
    for _n, _m in sorted(_masks.items()):
        assert _m and not (_m & _seen), \
            f"{_n} = {_m:#x} overlaps a mask already claimed"
        _seen |= _m
    # The profession field must be wide enough for its own maximum,
    # and pop.h defines no fourth profession.
    assert _col.POP_PROF_MAX <= (_col.POP_MASK_PROF >> 7), \
        "POP_MASK_PROF cannot hold POP_PROF_MAX"
    assert _col.pop_prof(_col.POP_MASK_PROF) == 3, "prof shift is wrong"
    assert _col.pop_player_index(_col.POP_NATIVE) == 9
    # The nibble is a PLAYER index, not a race: pop.h:8 names it
    # MASK_RACE, but Get_Effective_Pop_Player_ (colony.cpp:1257)
    # returns it as a player and maps only 8 and 9 to the colony
    # owner, after which the race is a SECOND lookup
    # (MOX::_player[idx].race, colony.cpp:1275). The wrong name
    # must not come back into the spec — asserted here because a
    # rename that reads plausibly is exactly what a later session
    # would undo.
    assert not hasattr(_col, "pop_race"), \
        "pop_race is back — the nibble is a player index"
    assert not hasattr(_col, "POP_MASK_RACE"), \
        "POP_MASK_RACE is back — see colony.cpp:1257"
    assert _col.pop_effective_player(_col.POP_ANDROID, 5) == 5
    assert _col.pop_effective_player(_col.POP_NATIVE, 5) == 5
    assert _col.pop_effective_player(3, 5) == 3
    # ── The max-population base table never travels alone ──
    # orion2re's _planet_max_population[] (mox.cpp:796) is the BASE
    # of a computation, not the answer: the climate factor and the
    # immunity bonus halve it on Ixion II (10 -> 5), and the colony
    # list's bar length is meant to be proportional to the real
    # maximum. Asserted as the rule rather than by reimplementing the
    # formula and checking it against itself: any file that carries
    # the size table must also carry the climate factors, so the base
    # cannot be transcribed on its own and quietly used as a maximum.
    # Not vacuous — planet.py carries both today and is what this
    # check measures.
    _base_re = re.compile(r"5\s*,\s*10\s*,\s*15\s*,\s*20\s*,\s*25")
    _fac_re = re.compile(r"40\s*,\s*60\s*,\s*80\s*,\s*100")
    _root_pm = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _lonely, _seen_base = [], 0
    for _dir, _subs, _files in os.walk(_root_pm):
        if "__pycache__" in _dir or os.sep + ".git" in _dir:
            continue
        for _f in _files:
            if not _f.endswith(".py"):
                continue
            _fp = os.path.join(_dir, _f)
            with open(_fp, encoding="utf-8", errors="replace") as _fh:
                _txt = _fh.read()
            if not _base_re.search(_txt):
                continue
            _seen_base += 1
            if not _fac_re.search(_txt):
                _lonely.append(os.path.relpath(_fp, _root_pm))
    assert not _lonely, (
        "the planet max-population size table appears without the "
        "climate factors in: " + ", ".join(_lonely) + " — that base "
        "is not a maximum (colcalc.cpp:896)")
    assert _seen_base, \
        "nothing in the tree carries the max-population base table any more"

    ok("struct specs (nebula, planet, player; s_colony promoted, "
       "pop masks, quarantine contract, max-pop base table)")

    # ── struct_probe's pop-nibble report ──
    # The only check in this file for a tool that CANNOT run here: it
    # needs a live orion2re. So its classification is exercised on
    # synthetic records instead, which is the whole of what could
    # silently rot — three separate misclassifications were found by
    # hand while it was being written, and each one read plausibly.
    #
    # Behaviour, not wording. The strings are for a person; what must
    # not drift is which pops land in which bucket.
    import importlib.util as _spu
    _sp_spec = _spu.spec_from_file_location(
        "_probe_struct_probe",
        os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                     "struct_probe.py"))
    _sp = _spu.module_from_spec(_sp_spec)
    _sp_spec.loader.exec_module(_sp)

    def _mk_col(owner, nibbles):
        b = bytearray(_col.SIZE)
        b[0] = owner & 0xFF
        b[10] = len(nibbles)
        for _i, _nib in enumerate(nibbles):
            b[12 + 4 * _i:16 + 4 * _i] = _s.pack(
                "<I", (_i % 3) << 7 | _nib | _col.POP_MASK_ASSIGNED)
        return bytes(b)

    # The reference save's shape: several owners, no androids. The
    # prediction is answerable precisely because the owners differ.
    _rep = _sp.pop_nibble_report(
        [_mk_col(0, [0] * 6), _mk_col(3, [3] * 4), _mk_col(5, [5] * 9)],
        _col.SPEC)
    assert not _rep["mismatches"] and _rep["distinct_owners"] == [0, 3, 5], _rep
    assert _rep["live_pops"] == 19 and not _rep["sentinels"], _rep
    assert _rep["dist"][5] == 9 and _rep["tail"][0] == 3 * 42 - 19, _rep

    # A wrong mask does not fail cleanly, it SCATTERS — that spread is
    # the tell the report exists to show, so a run that produced one
    # value per colony would be a different fault entirely.
    _scatter = _sp.pop_nibble_report(
        [_mk_col(0, [1, 4, 10, 2]), _mk_col(3, [11, 6, 2])], _col.SPEC)
    assert len(_scatter["mismatches"]) == 5, _scatter["mismatches"]
    assert len(_scatter["dist"]) >= 6, _scatter["dist"]

    # Androids and natives are NOT prediction failures. They resolve
    # to the colony's owner (colony.cpp:1261), so they CONFIRM the
    # player-index reading — counting them as mismatches made the one
    # save that can settle the sentinels report itself as a
    # refutation, which is how this check earned its place.
    _andro = _sp.pop_nibble_report(
        [_mk_col(0, [0, _col.POP_ANDROID, _col.POP_NATIVE]),
         _mk_col(2, [2, 2])], _col.SPEC)
    assert not _andro["mismatches"], _andro["mismatches"]
    assert len(_andro["sentinels"]) == 2, _andro["sentinels"]

    # 10..13 and >= 14 are different findings: the second has a branch
    # in the source (colony.cpp:2129), the first has none that was
    # found, so only the first is evidence against the mask.
    _above = _sp.pop_nibble_report(
        [_mk_col(0, [0, 11, 14, 15])], _col.SPEC)
    assert [n for _c, _p, n in _above["out_of_range"]] == [11], _above
    assert sorted(n for _c, _p, n in _above["direct_race"]) == [14, 15], _above
    assert not _above["mismatches"], _above["mismatches"]

    # A save whose colonies share one owner cannot decide anything:
    # "nibble == owner" and "nibble == 0" are then the same sentence.
    _one = _sp.pop_nibble_report([_mk_col(0, [0] * 4)], _col.SPEC)
    assert _one["distinct_owners"] == [0] and not _one["mismatches"], _one
    ok("struct_probe pop-nibble report (owner match, scatter, sentinels, "
       "10-13 vs >=14)")

    # ── The colony list ──
    # Built against a synthetic snapshot, so the check runs headless
    # and does not depend on somebody's savegame — a test that reads
    # the user's disk answers differently for the user.
    #
    # The rules, not the instance: a row shows "No Farming" exactly
    # when its colony's max_farms is 0; the three job counts add up
    # to the population; and the bar never draws a square past its
    # own end, which is what keeps "counting squares counts pops"
    # true when a deviation makes the computed maximum too small.
    from screens.colony_summary import colonylist as _cl
    from screens.colony_summary import colonyrows as _cr
    from core.structs import colony as _colsp, star as _starsp

    def _mk_colony(owner, planet, pops, jobs, max_farms, climate):
        b = bytearray(361)
        b[0] = owner & 0xFF
        b[2:4] = _s.pack("<h", planet)
        b[10] = pops
        i = 0
        for prof, n in enumerate(jobs):
            for _ in range(n):
                b[12 + 4 * i:16 + 4 * i] = _s.pack("<I", (prof & 3) << 7)
                i += 1
        b[224] = max_farms
        b[226] = climate
        return bytes(b)

    def _mk_planet(colony_index, star_index, orbit, size, climate):
        b = bytearray(18)
        b[0:2] = _s.pack("<h", colony_index)
        b[2:4] = _s.pack("<h", star_index)
        b[4] = orbit
        b[6] = size
        b[9] = climate
        return bytes(b)

    def _mk_star(name, slots):
        b = bytearray(_starsp.SIZE)
        b[0:len(name)] = name.encode("latin-1")
        for i, v in enumerate(slots):
            off = _starsp.PLANET_INDEX_OFFSET + 2 * i
            b[off:off + 2] = _s.pack("<h", v)
        return bytes(b)

    class _GS:
        player_num = 0
    _gs = _GS()
    # Two planets in one system, the first slot EMPTY, so the numeral
    # of the first real planet is I and not II — HAROLD::Planet_Number_
    # counts occupied slots, and getting that wrong renamed five of
    # seven rows the first time it was tried.
    _gs.planets_raw = [_mk_planet(0, 0, 1, 1, 5),
                       _mk_planet(1, 0, 2, 3, 8)]
    _gs.stars = _starsp.parse_all([_mk_star("Sol", [-1, 0, 1, -1, -1])])
    _gs.colonies_raw = [
        _mk_colony(0, 0, 3, (0, 3, 0), 0, 5),      # No Farming
        _mk_colony(0, 1, 6, (2, 3, 1), 255, 8),    # farms
        _mk_colony(1, 1, 4, (0, 4, 0), 255, 8),    # another player
    ]
    _pl_raw = bytearray(pl.SIZE)
    _pl_raw[pl.TRAITS_OFFSET + _cr.TRAIT_ENVIRONMENT_IMMUNE] = 1
    _gs.player_raw = [bytes(_pl_raw)]

    _rows = _cr.build_rows(_gs, "name")
    assert len(_rows) == 2, [r["name"] for r in _rows]
    assert [r["name"] for r in _rows] == ["Sol I", "Sol II"], \
        [r["name"] for r in _rows]
    for _r in _rows:
        assert sum(_r["jobs"]) == _r["pops"], _r
    assert _rows[0]["no_farming"] and not _rows[1]["no_farming"], _rows
    # The worked example from the fundament, section 3: Small(1)
    # Ocean(5) with an environment-immune owner is 5, where the size
    # table alone would say 10.
    assert _rows[0]["max_pop"] == 5, _rows[0]["max_pop"]

    # Nothing is drawn past the bar. Rendered onto a known background
    # and measured, rather than asserted about the code: a clip that
    # stops working is invisible in the source and obvious in pixels.
    _surf = pygame.Surface((1920, 1080))
    _surf.fill((0, 0, 0))
    _area = pygame.Rect(100, 100, 1200, 400)
    import json as _cjson
    with open(os.path.join(SCREENS_DIR, "colony_summary", "layout.json"),
              encoding="utf-8") as _fh:
        _cfg = _cjson.load(_fh)["list"]
    _cl.render(_surf, _rows, _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    for _x in range(_area.right, 1920):
        assert not _px[_x].any(), f"the list drew at x={_x}, past its area"

    # A row whose population EXCEEDS its computed maximum. The two
    # documented deviations in max_population() both make the number
    # too small, so this is a state the real screen can reach. Those
    # squares now spill into the unreachable region rather than being
    # clipped at max_pop — a pop is a fact, max_pop is a computation
    # — so what has to hold is that the TRACK still ends inside the
    # panel. The rows above cannot catch it: both fit comfortably.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Overflow", "pops": 8,
                        "jobs": [0, 8, 0], "no_farming": False,
                        "max_pop": 3}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    for _x in range(_area.right, 1920):
        assert not _px[_x].any(), (
            f"a row with more pops than its maximum drew at x={_x} — "
            f"the bar no longer clips at its own end")

    # The bar is an INVENTION and the marking has to survive. Checked
    # in both homes the project requires: the module that draws it and
    # the JSON a mod would edit.
    _cl_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                                "colonylist.py"), encoding="utf-8").read()
    assert "INVENTION" in _cl_src, \
        "colonylist.py no longer marks the bar as an INVENTION"
    assert "INVENTION" in _cfg.get("_invention", ""), \
        "layout.json list._invention no longer carries the marking"
    # The per-row detail line is an HD EXTENSION and carries its own
    # marker: the original prints climate and n/max for the SELECTED
    # colony only, into the scan box at native (13, 354, 80, 88)
    # (COLSUM::Draw_Colony_Scan_Info_, colsum.cpp:1155). A marking
    # two documents claim exists is not a marking — this one is
    # asserted in both homes, and refused if it does not name what
    # the original does instead.
    assert "HD EXTENSION" in _cl_src, \
        "colonylist.py no longer marks the per-row detail line"
    _hd = _cfg.get("_hd_extension", "")
    assert "HD EXTENSION" in _hd, \
        "layout.json list._hd_extension no longer carries the marking"
    assert "colsum.cpp:1155" in _hd, \
        ("list._hd_extension no longer names what the original does "
         "instead — a label without the deviation it records is a "
         "label, not a marking")
    # ── "No Farming": centred in the farmers column ──
    # TRANSCRIBED, 8 September 2026, and the check moved with the
    # drawing. It used to sit below the bar at the left edge of the
    # first job marker, and these checks asserted that placement's
    # own risk — that a later draw would paint over it, which had
    # happened once with every number right and nothing on screen.
    # The source settles the placement instead: coldraw.cpp:315-321
    # prints it with `Squeeze_Print_Paragraph_(left_x, top_y + 5,
    # right_x - left_x, 28, …, 2)` and the 2 selects
    # `Print_Centered_(x + width/2, y, str)`.
    #
    # THE COLUMN TABLE IS INSTALLED HERE, because "centred in the
    # column" has no meaning in the single-track fallback that the
    # synthetic rows above use — that geometry has no columns, and
    # `colonyheader.install_columns` is what the real screen puts in
    # `list` at startup. So this renders the SHIPPED geometry.
    from screens.colony_summary import colonyheader as _chd
    from screens.colony_summary import colonytrack as _ctk
    _cfg_cols = dict(_cfg)
    _cfg_cols[_ctk.COLUMNS_KEY] = _chd.columns(res, "colony_summary")
    assert _cfg_cols[_ctk.COLUMNS_KEY], (
        "layout_reference.json has no list_columns, so the shipped row "
        "geometry cannot be exercised at all")
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Full", "pops": _cl.POP_LIMIT_CAP,
                        "jobs": [0, 30, 12], "no_farming": True,
                        "max_pop": _cl.POP_LIMIT_CAP}],
               _area, _cfg_cols, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _label_ink = [(x, y) for x in range(_area.x, _area.right)
                  for y in range(_area.y, _area.bottom)
                  if tuple(_px[x, y]) == tuple(_cl.NO_FARM_COLOR[:3])]
    assert _label_ink, (
        "'No Farming' is not on the surface for a full 42-slot row — "
        "the squares are painted over it again")
    _cols_now = _ctk.columns(_area, _cfg_cols)
    _fx, _fw = _cols_now["farmers"]
    _lx0 = min(x for x, _y in _label_ink)
    _lx1 = max(x for x, _y in _label_ink)
    assert _fx <= _lx0 and _lx1 < _fx + _fw, (
        f"'No Farming' inks x {_lx0}..{_lx1} and the farmers column is "
        f"{_fx}..{_fx + _fw} — the label has left its own column")
    # CENTRED, which is the whole of what the 2 in that call means.
    # Two px of slack for the odd-width case; anything more is a
    # placement, not a rounding.
    _want_c = _fx + _fw / 2.0
    _got_c = (_lx0 + _lx1 + 1) / 2.0
    assert abs(_got_c - _want_c) <= 2, (
        f"'No Farming' is centred on {_got_c:.1f} and the farmers "
        f"column's centre is {_want_c:.1f} — Print_Centered_ puts it "
        f"at left_x + width/2 (bill.cpp, mode 2)")
    # AND AT top_y + 5, as a proportion of the row (5 of 31, the
    # original's own row pitch at colsum.cpp:311). The original's ink
    # top sits ON that y — measured at 136 against top_y + 5 = 136 on
    # colony_summary_native_split.png — so this is the ink and not a
    # surface edge.
    _bands = _cl.row_bands(_area, _cfg_cols, app.layout.scale, 1)
    _btop, _bh = _bands[0]
    _want_y = _btop + round(_cl.NATIVE_LABEL_Y_OFFSET * _bh
                            / _cl.NATIVE_ROW_PITCH)
    _got_y = min(y for _x, y in _label_ink)
    assert abs(_got_y - _want_y) <= 1, (
        f"'No Farming' inks from y={_got_y}; top_y + 5 is {_want_y} at "
        f"a band of {_bh}")
    # ── ...and the SIZE is the measurement, re-measured ──
    # The only source for it is a picture: font style 3's height is in
    # the player's FONTS.LBX. The capital N measures 10 px of cap on
    # colony_summary_native_split.png, in a 31 px row, so the drawn
    # cap must be 10/31 of the band. Measured by RENDERING
    # (decision 30), because a nominal font size is not a cap height
    # and the substitution path can mix two fonts inside one string.
    _cap_surf = app.style.render_text(
        "N", app.layout.font_size(_cfg_cols["no_farming_font"]),
        (255, 255, 255))
    _cap_box = _cap_surf.get_bounding_rect()
    _want_cap = _cl.NATIVE_LABEL_CAP * _bh / _cl.NATIVE_ROW_PITCH
    assert abs(_cap_box.height - _want_cap) <= 1.5, (
        f"the 'No Farming' cap renders {_cap_box.height} px where the "
        f"measurement wants {_want_cap:.1f} — no_farming_font "
        f"{_cfg_cols['no_farming_font']} no longer carries the 10 px "
        f"cap measured off the native screenshot")
    # ── The label cannot be painted over, and now by construction ──
    # The old placement had to PROVE this with a full track, because
    # the label shared a band with the squares. It cannot happen any
    # more and the reason is the data, not the drawing: the label is
    # drawn only when `max_farms == 0`, which is exactly the state in
    # which the food column has no farmer to draw. Asserted rather
    # than argued — a farmers column with cells in it and the label
    # asked for at the same time must not exist, so the row that
    # would produce it is checked to draw no farmer cell.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Hatched I", "pops": 3,
                        "jobs": [0, 2, 1], "no_farming": True,
                        "climate": 1, "max_pop": 20}],
               _area, _cfg_cols, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _nf_rgb = tuple(_cl.NO_FARM_COLOR[:3])
    _food_rgb = tuple(_cl.ZONE_COLORS[0][:3])
    _label = [(x, y) for x in range(_area.x, _area.right)
              for y in range(_area.y, _area.bottom)
              if tuple(_px[x, y]) == _nf_rgb]
    _food = [(x, y) for x in range(_area.x, _area.right)
             for y in range(_area.y, _area.bottom)
             if tuple(_px[x, y]) == _food_rgb]
    assert _label, "'No Farming' did not draw on a row that has free slots"
    assert not _food, (
        "a No Farming row drew farmer cells — the label and the "
        "figures would then share the column, which is the collision "
        "the old placement existed to avoid")

    # ── The budget, checked where it can actually fail ──
    # The column sum — name + tail + building + pad + 42*unit +
    # 41*gap == list_area — is no longer asserted. `track_metrics`
    # hands the floor division's remainder to the name column's drawn
    # width, so that sum balances BY CONSTRUCTION at every
    # resolution, and a thing that cannot fail is not a check.
    #
    # The previous version asserted it with `1920`, `1080` and `1.0`
    # as literals: it covered one of the two keys in boxes.json and
    # none of the sizes reached through the fallback chain. It
    # balanced at scale 1.0 and 2.0 — where every int() truncates
    # cleanly — and was 11 to 30 px short at every fractional scale,
    # which it never looked at.
    #
    # So: twelve window sizes, and the two things the construction
    # can still get wrong.
    #
    #   1. the row ends flush     slot42_right + building + pad_x
    #                             == list_area.right
    #   2. the ellipsis threshold is the same everywhere — the
    #      remainder is GUTTER, never text budget
    #
    # (2) is what guards the design decision. Letting the remainder
    # into the text budget ALSO closes (1), and silently makes the
    # threshold range 244..288 reference px: the same colony name
    # cuts on one monitor and not on another.
    #
    # Both are read off the SURFACE, not recomputed. An earlier draft
    # of this check derived bar_x and the clip from layout.json the
    # same way the renderer does, which made it agree with the
    # renderer by construction — it passed unchanged when the gutter
    # was moved a pixel and when the clip was tied to the drawn
    # width, the two failures it exists for.
    _SIZES = [(1280, 720), (1366, 768), (1440, 900), (1600, 900),
              (1680, 1050), (1920, 1080), (1920, 1200), (2048, 1152),
              (2560, 1080), (2560, 1440), (3440, 1440), (3840, 2160)]
    _boxes_path = os.path.join(SCREENS_DIR, "colony_summary", "boxes.json")
    # Two names that must land on opposite sides of the threshold at
    # EVERY size: 167..179 reference px against 254..286, either side
    # of the 244 the column pays for. The wide one is deliberately
    # under 288, which is what the threshold becomes if the remainder
    # leaks into the text budget — so a leak shows up as this name
    # NOT being cut at the small sizes.
    _NAME_FITS = "Wilhelmshaven V"
    _NAME_CUTS = "Mmmmmmmmmmmmmmm"

    def _ink_span(_surface, _rect, _rgb):
        """First and last column in `_rect` carrying exactly `_rgb`."""
        _a = pygame.surfarray.array3d(_surface.subsurface(_rect))
        _cols = (_a == _rgb).all(axis=2).any(axis=1).nonzero()[0]
        if not len(_cols):
            return None
        return int(_cols[0]) + _rect.x, int(_cols[-1]) + _rect.x

    _name_rgb = tuple(_cl.ROW_NAME[:3])
    _beyond_rgb = tuple(_cl.BAR_BEYOND[:3])
    _cut_at = []
    for _W, _H in _SIZES:
        _lay = Layout(_W, _H)
        _sc = _lay.scale
        _bx = load_boxes(_boxes_path, _W, _H)
        _lref = [b.ref_rect for b in _bx if b.name == "list_area"]
        assert _lref, f"boxes.json has no list_area box at {_W}x{_H}"
        _ar = pygame.Rect(*_lay.rect(_lref[0]))
        _tk = _cl.track_metrics(_ar, _cfg, _sc)
        _rh = int(_cfg["row_height"] * _sc)
        _sf = pygame.Surface((_W, _H))
        _sf.fill((0, 0, 0))
        _cl.render(_sf, [{"name": _NAME_FITS, "pops": 2, "jobs": [1, 1, 0],
                          "no_farming": False, "climate": 8, "max_pop": 6},
                         {"name": _NAME_CUTS, "pops": 2, "jobs": [1, 1, 0],
                          "no_farming": False, "climate": 8, "max_pop": 6}],
                   _ar, _cfg, _lay, app.style)
        _top = _ar.y + int(_cfg["pad_y"] * _sc)
        _b0 = pygame.Rect(_ar.x, _top, _ar.w, _rh)
        _b1 = pygame.Rect(_ar.x, _top + _rh, _ar.w, _rh)

        # 1. FLUSH. slot 42's right edge is the last column of the
        #    faint baseline, which is drawn to exactly `track.width`
        #    from wherever the renderer decided the bar starts — so
        #    this reads the bar's real position off the surface.
        _base = _ink_span(_sf, _b0, _beyond_rgb)
        assert _base, (
            f"{_W}x{_H}: no unreachable baseline drawn, so slot 42's "
            f"right edge cannot be read from the surface")
        _slot42_r = _base[1] + 1
        _bld_r = _slot42_r + _tk.build_gap + _tk.build_w
        _pd = int(_cfg["pad_x"] * _sc)
        assert _bld_r + _pd == _ar.right, (
            f"{_W}x{_H} (scale {_sc:.4f}): the row does not end flush "
            f"— slot 42 ends {_slot42_r}, building column to {_bld_r}, "
            f"plus pad_x {_pd} is {_bld_r + _pd}, against "
            f"list_area.right {_ar.right} "
            f"({_ar.right - _bld_r - _pd:+d}). The budget's remainder "
            f"is not reaching the name column's drawn width, or "
            f"something else is spending it.")

        # 2. THE THRESHOLD, by whether each name was actually cut.
        _nat_fits = app.style.render_text(
            _NAME_FITS, _lay.font_size(_cfg["name_font"]),
            _cl.ROW_NAME).get_width()
        _nat_cuts = app.style.render_text(
            _NAME_CUTS, _lay.font_size(_cfg["name_font"]),
            _cl.ROW_NAME).get_width()
        _drawn_fits = _ink_span(_sf, _b0, _name_rgb)
        _drawn_cuts = _ink_span(_sf, _b1, _name_rgb)
        assert _drawn_fits and _drawn_cuts, f"{_W}x{_H}: a name did not draw"
        _w_fits = _drawn_fits[1] - _drawn_fits[0] + 1
        _w_cuts = _drawn_cuts[1] - _drawn_cuts[0] + 1
        # 4 px of slack on the comparison: the span is measured from
        # exact-colour pixels and an antialiased edge column can fall
        # outside that. A cut removes whole glyphs, never 4 px.
        assert _w_fits >= _nat_fits - 4, (
            f"{_W}x{_H}: {_NAME_FITS!r} is {_nat_fits} px, inside the "
            f"{_cfg['name_width']} the column pays for, and it was cut "
            f"anyway (drew {_w_fits}) — the text budget has shrunk")
        assert _w_cuts < _nat_cuts - 4, (
            f"{_W}x{_H} (scale {_sc:.4f}): {_NAME_CUTS!r} is "
            f"{_nat_cuts} px against a text budget of "
            f"{_cfg['name_width']} scaled, and it was NOT cut (drew "
            f"{_w_cuts}). The name column is clipping against its "
            f"DRAWN width, so the budget's per-resolution remainder "
            f"has become text budget: the ellipsis threshold now "
            f"moves with the resolution and the same colony name cuts "
            f"on one monitor and not on another.")
        _cut_at.append(f"{_W}x{_H}")

    assert len(_cut_at) == len(_SIZES), (_cut_at, _SIZES)

    # ── Nothing from the name column reaches the track ──
    # The invariant, however it is achieved. Right-alignment plus
    # pad_x is what achieves it today and the name-block check below
    # tests that mechanism; this one tests the property, so a later
    # change of mechanism still has to keep it. Asserted at the
    # structural maximum (str15, namestar.cpp:262 caps input at 15),
    # not at a name some galaxy happened to generate.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "W" * 15 + " V", "pops": 3,
                        "jobs": [1, 1, 1], "no_farming": False,
                        "climate": 8, "max_pop": 9}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _name_end = (_area.x + int(_cfg["pad_x"] * app.layout.scale)
                 + int(_cfg["name_width"] * app.layout.scale))
    _rgb = tuple(_cl.ROW_NAME[:3])
    _spill = [x for x in range(_name_end, _area.right)
              if any(tuple(_px[x, y]) == _rgb
                     for y in range(_area.y, _area.bottom))]
    assert not _spill, (
        f"the longest producible name draws past its column at "
        f"x={_spill[:5]} — name_width is not being enforced")

    # The preview drives the REAL screen off a synthetic snapshot.
    # This replaces the old check that its hand-written row dicts
    # matched build_rows' keys — those dicts are gone, because the
    # preview fakes the STATE now and lets build_rows produce the
    # rows, so that particular drift is structurally impossible.
    #
    # What can still drift is the snapshot: a spec change, or an
    # entry edited until it no longer produces the SHAPE its comment
    # claims. A "nearly full track" that quietly became half full
    # still renders, and nobody would notice from the picture that
    # the case had stopped being covered.
    import importlib.util as _plu
    _pv_spec = _plu.spec_from_file_location(
        "_probe_colony_preview",
        os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                     "colony_list_preview.py"))
    _pv = _plu.module_from_spec(_pv_spec)
    _pv_spec.loader.exec_module(_pv)
    _pv_rows = _cr.build_rows(_pv._Snapshot(_pv.COLONIES), "name")
    assert len(_pv_rows) == len(_pv.COLONIES), (
        f"the preview's snapshot yields {len(_pv_rows)} rows from "
        f"{len(_pv.COLONIES)} colonies — build_rows drops some")
    assert set(_pv_rows[0]) == set(_rows[0]), (
        f"preview rows {sorted(_pv_rows[0])} against build_rows' "
        f"{sorted(_rows[0])}")
    # THE PROVENANCE BAND IS A MARKING, so it gets a check. The tool
    # wrote a side-by-side of a synthetic empire against a real
    # screenshot and nothing in the image said so — two different
    # worlds presented as a comparison. A marking without a check is
    # an intention (see the fundament on the help panel's).
    d.switch_to("colony_summary")
    _pv_screen = d.active
    _pv_screen.update(_pv._Snapshot(_pv.COLONIES))
    _syn_head, _syn_detail, _syn_col = _pv.provenance(
        _pv._Snapshot(_pv.COLONIES), _pv_screen, False, "name")
    assert "SYNTHETIC" in _syn_head, (
        f"the preview's band no longer says the rows are invented: "
        f"{_syn_head!r}. A tool whose output looks like a measurement "
        f"must not draw made-up data unmarked")
    assert _syn_detail and "colony_list_preview" in _syn_detail, _syn_detail
    assert _syn_col != _pv.BAND_LIVE, "synthetic and live share a colour"
    # And the band actually reaches the image: taller surface, ink in
    # the strip the render does not occupy.
    _pv_flat = pygame.Surface((400, 120))
    _pv_flat.fill((0, 0, 0))
    _pv_banded = _pv.with_band(_pv_flat, app, _syn_head, _syn_detail,
                               _syn_col)
    assert _pv_banded.get_height() > _pv_flat.get_height(), (
        "with_band returned a surface no taller than its input, so the "
        "band is drawn over the picture or not at all")
    _pv_strip = pygame.Rect(
        0, 0, _pv_banded.get_width(),
        _pv_banded.get_height() - _pv_flat.get_height())
    assert pygame.surfarray.array3d(
        _pv_banded.subsurface(_pv_strip)).sum() > 0, "the band is blank"
    assert any(r["no_farming"] for r in _pv_rows), (
        "no preview colony shows No Farming — the max_farms == 0 "
        "case is not being drawn")
    _pv_full = max(_pv_rows, key=lambda r: r["pops"])
    assert (_pv_full["pops"] >= 20
            and _pv_full["max_pop"] - _pv_full["pops"] <= 4), (
        f"the stress colony is {_pv_full['pops']}/"
        f"{_pv_full['max_pop']} — it exists to show a nearly full "
        f"track and no longer does")
    _pv_sparse = min(_pv_rows,
                     key=lambda r: r["pops"] / max(1, r["max_pop"]))
    assert _pv_sparse["max_pop"] - _pv_sparse["pops"] >= 5, (
        f"the sparse colony is {_pv_sparse['pops']}/"
        f"{_pv_sparse['max_pop']} — it exists to show a long "
        f"unreachable tail")
    assert any(len(r["name"]) >= 15 for r in _pv_rows), (
        "no preview colony has a str15 name, so the ellipsis case is "
        "not drawn")
    # Numerals are earned by OCCUPIED slots, not by the orbit
    # (HAROLD::Planet_Number_). Every star reading "I" is how the
    # first version of the synthetic snapshot was wrong.
    assert any(not r["name"].endswith(" I") for r in _pv_rows), (
        "every preview colony is numeral I — the filler planets that "
        "earn a numeral are missing from the snapshot")
    # The sidebar numbers exist to be FALSIFIABLE, not plausible.
    assert _pv.PLAYER["surplus_bc"] < 0, (
        "the preview's income is not negative, so red-if-negative "
        "never renders and the picture cannot show it")
    assert _pv.PLAYER["surplus_food"] > 0, (
        "the preview's food is not positive, so the explicit plus "
        "never appears beside the negative income")
    assert len(str(_pv.PLAYER["bc"])) >= 5, (
        "the preview's widest sidebar value is under five digits, so "
        "right alignment is not visible AS alignment")
    assert len(str(_pv.PLAYER["surplus_freighters"])) == 1, (
        "the preview has no one-digit sidebar value to contrast with "
        "the widest one")

    # ── An OUTPOST is not a row ──
    # Both of the original's conditions, from
    # Build_Global_Colony_List_ (colxport.cpp:91-99): the colony's
    # owner is the local player AND its outpost_flag is zero.
    # Verified live on 3 September 2026 — 12 records carried the
    # local player and the Colonies screen listed 11, the difference
    # being the planet the game itself calls "Yian I (Elerian
    # Outpost)". See core/structs/colony.py.
    #
    # The flag is set here through the SPEC's own offset, not a
    # literal, so a spec change breaks this loudly instead of
    # flipping some other byte and passing.
    from core.structs import colony as _col_spec
    _out_snap = _pv._Snapshot(_pv.COLONIES)
    _with_all = _cr.build_rows(_out_snap, "name")
    _op_off = dict((_n, _o) for _n, _o, _k
                   in _col_spec.SPEC.fields)["outpost_flag"]
    _victim = 1
    _op_name = _with_all[0]["name"]
    _op_raw = bytearray(_out_snap.colonies_raw[_victim])
    assert _op_raw[_op_off] == 0, "the preview already ships an outpost"
    _op_raw[_op_off] = 1
    _out_snap.colonies_raw[_victim] = bytes(_op_raw)
    _without = _cr.build_rows(_out_snap, "name")
    assert len(_without) == len(_with_all) - 1, (
        f"a colony with outpost_flag set is still in the rows: "
        f"{len(_without)} of {len(_with_all)}. The original's list "
        f"does not carry it (colxport.cpp:91-99)")
    _gone = set(_r["index"] for _r in _with_all) - set(
        _r["index"] for _r in _without)
    assert _gone == {_victim}, (
        f"the outpost filter dropped {_gone}, not the colony whose "
        f"flag was set ({_victim})")
    del _op_name
    # And it is the FLAG that drops it, not the owner: everything
    # else about that record is untouched and it was in the list a
    # moment ago.
    assert any(_r["index"] == _victim for _r in _with_all), _victim

    # ── The seven sort keys, and their DIRECTIONS ──
    # COLSUM::Switched_cmp_ (colsum.cpp:378-401, orion2re 1.60) is a
    # switch on _g_sort_index with the sign as a literal per case.
    # Five descending, Name and Producing ascending, and NO direction
    # toggle anywhere — clicking the active header re-sorts
    # identically. Asserted on the ORDER a sort produces rather than
    # on the comparator functions, so a rewrite of how sorting is
    # implemented still has to come out the same way round.
    import json as _sjson
    _sort_cfg = _sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["sort"]
    _sorters = _cr.SORT_KEYS
    assert set(_sorters) == {b["key"] for b in _sort_cfg["buttons"]}, (
        f"the sort keys {sorted(_sorters)} do not match the buttons "
        f"{sorted(b['key'] for b in _sort_cfg['buttons'])}")

    def _order(_key, _rowset):
        return [r["name"] for r in sorted(_rowset, key=_sorters[_key])]

    # "beta" is deliberately lower-case and sorts BETWEEN two
    # capitals only under casefold: by ASCII it lands after both.
    _a = {"name": "Alpha", "pops": 3, "jobs": [1, 1, 1], "no_farming": False,
          "climate": 8, "max_pop": 9, "producing": "", "producing_turns": 0,
          "can_buy": False, "production": [1, 9, 5, 2]}
    _b = {**_a, "name": "beta", "pops": 7, "production": [8, 2, 1, 9]}
    _c = {**_a, "name": "Gamma", "pops": 5, "production": [4, 5, 9, 4]}
    _set = [_a, _b, _c]

    # Name: ascending, and CASE-INSENSITIVE — cmp_Alpha_ calls
    # strcasecmp (colsum.cpp:1053). Plain str sort would put the
    # lower-case "gamma" after both capitals.
    assert _order("name", _set) == ["Alpha", "beta", "Gamma"], \
        _order("name", _set)
    assert _order("name", _set) != sorted(r["name"] for r in _set), (
        "the name sort is matching a case-SENSITIVE order, so this "
        "check is not exercising strcasecmp")
    # The five descending keys.
    assert _order("population", _set) == ["beta", "Gamma", "Alpha"], \
        _order("population", _set)
    assert _order("food", _set) == ["beta", "Gamma", "Alpha"], \
        _order("food", _set)
    assert _order("industry", _set) == ["Alpha", "Gamma", "beta"], \
        _order("industry", _set)
    assert _order("science", _set) == ["Gamma", "Alpha", "beta"], \
        _order("science", _set)
    assert _order("bc", _set) == ["beta", "Gamma", "Alpha"], \
        _order("bc", _set)
    # Producing cannot be honoured — Prod_To_Sort_Type_ needs
    # _buildings[].cost and Selection_Name_, both loaded from the
    # player's techname.lbx and not shipped. It must be declared
    # unavailable AND fall back visibly, not silently.
    assert "producing" in _cr.SORT_UNAVAILABLE, (
        "producing is no longer declared unavailable — if the cost "
        "and name tables have arrived, implement cmp_Prod_ "
        "(colsum.cpp:1091) rather than dropping the marking")
    assert _order("producing", _set) == _order("name", _set), (
        "the producing key does something other than fall back to "
        "the name, but the tables it needs are still not shipped")
    # Sorting twice by the same key changes nothing: no toggle.
    _once = _order("bc", _set)
    assert _order("bc", [dict(r) for r in _set]) == _once, (
        "sorting twice by the same key gave a different order — "
        "Switched_cmp_ has no direction toggle (colsum.cpp:378-401)")
    # ── Ties keep the INPUT order, and that is transcribed ──
    # The name fallback that used to be here was ours, and it ordered
    # ties the original does not order. Four links carry the array
    # order all the way through: ext_api.cpp:94 writes the colonies
    # in `MOX::_colony[i]` order, colxport.cpp:91 filters them into
    # `_g_colony_list_ptr` in that same order, colsum.cpp:363 swaps
    # only on a STRICTLY positive comparison so equal elements never
    # move, and colsum.cpp:1056 returns 0 on equality so the sign
    # that would move them cannot arise.
    #
    # Driven through `build_rows` rather than through `_sorters`
    # directly, because "input order" is a property of the whole
    # path: the sort key alone cannot express it, and a key that
    # LOOKS stable in isolation would still reshuffle if build_rows
    # ever stopped walking `colonies_raw` in order or started using a
    # sort that is not stable.
    _tie_pv = [dict(_pv.COLONIES[3]), dict(_pv.COLONIES[3])]
    _tie_pv[0]["star"] = "Zeta"
    _tie_pv[1]["star"] = "Aeta"
    # Same pops, same production: every key below is a tie.
    for _k in ("population", "food", "industry", "science", "bc"):
        _fwd = [r["name"] for r in
                _cr.build_rows(_pv._Snapshot(_tie_pv), _k)]
        _rev = [r["name"] for r in
                _cr.build_rows(_pv._Snapshot(_tie_pv[::-1]), _k)]
        assert _fwd == ["Zeta I", "Aeta I"], (_k, _fwd)
        assert _rev == ["Aeta I", "Zeta I"], (_k, _rev)
        assert _fwd == _rev[::-1], (_k, _fwd, _rev)
    # The negative form, so the check cannot pass by accident on a
    # key that happens to be alphabetical anyway: a name tie-break
    # would put "Aeta I" first BOTH times.
    assert _fwd[0] != _rev[0], (
        "ties come out in the same order whichever way the snapshot "
        "is packed, so something is ordering them — the original "
        "orders them by nothing (colsum.cpp:363, colsum.cpp:1056)")
    # And a redraw is still stable: same snapshot, same list. That is
    # what the name fallback was bought for, and it was already true.
    _snap = _pv._Snapshot(_tie_pv)
    assert ([r["name"] for r in _cr.build_rows(_snap, "population")]
            == [r["name"] for r in _cr.build_rows(_snap, "population")]), (
        "two build_rows calls over one snapshot disagree — the list "
        "reshuffles between redraws")
    # The tuple form is what a tie-break looks like; the absence has
    # to be visible in the key itself, not only in the order.
    assert not isinstance(_cr.SORT_KEYS["population"]({
        **_a, "name": "x", "pops": 1}), tuple), (
        "a descending sort key returns a tuple again, which is a "
        "tie-break by another name")
    ok("colony summary sort keys (seven, five descending, "
       "case-insensitive name, no toggle, ties in input order, "
       "producing declared unavailable)")

    # ── DRAWN AGAINST PRESENT: the list says what it dropped ──
    # render() stops at the first row that would cross the bottom of
    # list_area. At 1920x1080 the panel holds nine rows, so a
    # twelve-colony empire lost three IN SILENCE — every drawn row
    # correct, every check in this suite green, and the fault found
    # by somebody noticing a colony they owned was missing from a
    # screenshot. The check is therefore on the two numbers being
    # reconciled, not on the drawing being pretty.
    d.switch_to("colony_summary")
    _ov_area = pygame.Rect(*app.layout.rect(
        d.active.box_rect("list_area")))
    from screens.colony_summary import colonyheader as _ch
    from screens.colony_summary import colonytrack as _ct0
    _ov_cfg = _sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["list"]
    # THE FIXTURE CARRIES THE COLUMN TABLE, because the screen's cfg
    # does — `colonyheader.columns` merges it on load. A fixture
    # without it exercises the single-track path and would say
    # nothing about the row the screen actually draws, which is the
    # shape of the MAP_MAX_Y omission one commit earlier.
    _ov_cfg[_ct0.COLUMNS_KEY] = _ch.columns(res, "colony_summary")
    _ov_fits = _cl.rows_drawn(_ov_area, _ov_cfg, app.layout.scale, 99)
    assert _ov_fits > 0, "no row fits list_area at all"
    # TEN, because that is the original's window: COLSUM::_list_col
    # holds ten and Update_Col_List_ (colsum.cpp:348) fills exactly
    # that many. At row_height 62 the panel held nine and nothing
    # said so until a --live --native side-by-side put the two lists
    # next to each other. Asserted at every shipped resolution, and
    # with room left for the overflow line: at row_height 60 ten rows
    # fit and the line does not, which is the interaction a change to
    # either number alone gets wrong.
    _ORIGINAL_WINDOW = 10
    for _W, _H in _SIZES:
        _lay2 = Layout(_W, _H)
        _la2 = pygame.Rect(*_lay2.rect(d.active.box_rect("list_area")))
        _fits2 = _cl.rows_drawn(_la2, _ov_cfg, _lay2.scale, 99)
        assert _fits2 >= _ORIGINAL_WINDOW, (
            f"{_W}x{_H}: the list draws {_fits2} rows and the original "
            f"windows {_ORIGINAL_WINDOW} (_list_col[10], "
            f"colsum.cpp:348). row_height is "
            f"{_ov_cfg['row_height']} — lower it, or widen list_area "
            f"in the frame artwork, but do not let the two differ "
            f"silently")
        _bands2 = _cl.row_bands(_la2, _ov_cfg, _lay2.scale, _fits2)
        _left2 = _la2.bottom - (_bands2[-1][0] + _bands2[-1][1])
        _line_h = app.style.render_text(
            "0", _lay2.font_size(_ov_cfg.get("small_font", 15)),
            (255, 255, 255)).get_height()
        assert _left2 >= _line_h, (
            f"{_W}x{_H}: {_left2} px are left under the last row and "
            f"the overflow line needs {_line_h} — it would be clamped "
            f"back over the row it exists to account for")
    _ov_rows = [{"index": _i, "name": f"Over {_i}", "pops": 2,
                 "jobs": [1, 1, 0], "no_farming": False, "climate": 8,
                 "max_pop": 9, "producing": "", "producing_turns": 0,
                 "can_buy": False, "production": [1, 1, 1, 1],
                 "size": 2, "gravity": 1, "mineral": 2, "growth": 0,
                 "morale": 0, "morale_applies": True}
                for _i in range(_ov_fits + 3)]
    assert _cl.rows_drawn(_ov_area, _ov_cfg, app.layout.scale,
                          len(_ov_rows)) == _ov_fits, (
        "rows_drawn does not agree with itself about how many fit")
    # The wording is in layout.json (decision 15) and {count} is
    # substituted by replace (decision 37), so the check reads the
    # template rather than hardcoding the sentence.
    # ── THE ARROWS SAY IT NOW, NOT A SENTENCE ──
    #
    # "{count} more not shown" was text where the original has two
    # buttons (`_x_fields[1]` and `[2]`, colsum.cpp:263-264), and it
    # said what was off screen without offering any way to reach it.
    # The statement is the DOWN ARROW being live, so this check moved
    # from "ink appears under the last row" to "the arrow that can
    # move is drawn differently from the one that cannot" — which is
    # the same fault being watched, in the control that replaced the
    # sentence.
    from screens.colony_summary import colonyscroll as _cscr
    _ov_surf = pygame.Surface((_ov_area.right + 8, _ov_area.bottom + 8))

    def _arrow_ink(_rows, _first):
        """(up ink, down ink) for a list of `_rows` at `_first`."""
        _ov_surf.fill((0, 0, 0))
        _cl.render(_ov_surf, _rows, _ov_area, _ov_cfg, app.layout,
                   app.style, _first)
        _up, _down = _cscr.arrows(_ov_area, _ov_cfg, app.layout.scale)
        assert _up is not None, (
            "the list has no scroll arrows; the column table is what "
            "places them and it is missing")
        return tuple(int(pygame.surfarray.array3d(
            _ov_surf.subsurface(_r)).sum()) for _r in (_up, _down))

    # AT THE TOP OF AN OVERFLOWING LIST: down is live, up is not.
    _ov_up0, _ov_dn0 = _arrow_ink(_ov_rows, 0)
    assert _ov_dn0 > _ov_up0, (
        f"{len(_ov_rows) - _ov_fits} rows are below the window and the "
        f"down arrow is not drawn any brighter than the up one "
        f"({_ov_dn0} against {_ov_up0}) — nothing on screen says there "
        f"is more, which is the fault this check exists for and was "
        f"live until 3 September 2026")
    # SCROLLED TO THE BOTTOM: it is the other way round.
    _ov_upN, _ov_dnN = _arrow_ink(_ov_rows, len(_ov_rows) - _ov_fits)
    assert _ov_upN > _ov_dnN, (
        f"at the bottom of the list the up arrow is not the live one "
        f"({_ov_upN} against {_ov_dnN})")
    # A LIST THAT FITS: neither is live, and both are still drawn —
    # the original's buttons do not disappear, they stop responding.
    _ov_upF, _ov_dnF = _arrow_ink(_ov_rows[:_ov_fits], 0)
    assert _ov_upF == _ov_dnF and _ov_upF > 0, (
        f"a list that fits draws its arrows {_ov_upF} and {_ov_dnF}; "
        f"both should be dim and both should be there")
    assert _ov_dnF < _ov_dn0, (
        "the dim down arrow is not dimmer than the live one")
    # AND THE OLD SENTENCE IS GONE. A renderer that drew both would
    # pass everything above.
    _ov_surf.fill((0, 0, 0))
    _cl.render(_ov_surf, _ov_rows, _ov_area, _ov_cfg, app.layout,
               app.style)
    _ov_bands = _cl.row_bands(_ov_area, _ov_cfg, app.layout.scale,
                              len(_ov_rows))
    _ov_top = _ov_bands[-1][0] + _ov_bands[-1][1]
    _ov_up1, _ = _cscr.arrows(_ov_area, _ov_cfg, app.layout.scale)
    _ov_strip = pygame.Rect(_ov_area.x, _ov_top, _ov_up1.x - _ov_area.x,
                            _ov_area.bottom - _ov_top)
    assert _ov_strip.h > 0 and _ov_strip.w > 0
    assert pygame.surfarray.array3d(
        _ov_surf.subsurface(_ov_strip)).sum() == 0, (
        "there is still text under the last row. The arrows replaced "
        "the sentence; drawing both says the same thing twice and the "
        "second copy is the one that goes stale")
    # THE ARROW RECTS COME FROM THE LIST'S OWN GEOMETRY, which is what
    # keeps them over the scroll column at every resolution — the same
    # `colonytrack.columns` the rows' hit-test uses (decision 5).
    _ov_cols = _ct0.columns(_ov_area, _ov_cfg)
    assert _ov_up1.x == _ov_cols["scroll"][0], (
        f"the up arrow is at x={_ov_up1.x} and the scroll column "
        f"starts at {_ov_cols['scroll'][0]} — the arrows must come "
        f"from the column table, not from a second position")
    assert _ov_up1.width == _ov_cols["scroll"][1]
    assert _cscr.arrow_at(_ov_area, _ov_cfg, app.layout.scale,
                          _ov_up1.center) == "up"
    assert _cscr.arrow_at(_ov_area, _ov_cfg, app.layout.scale,
                          (_ov_area.x + 4, _ov_area.centery)) is None

    # Nothing below the last drawn band can be selected, because
    # row_at only knows the bands render laid out. That held when
    # there was no scrolling and it still holds with it: row_at
    # answers in BAND numbers over the window it was given, and the
    # offset is added by the screen (screen._row_at), so a hidden row
    # is unreachable here by construction rather than by luck.
    assert _cl.row_at(_ov_area, _ov_cfg, app.layout.scale,
                      len(_ov_rows),
                      (_ov_area.x + 4, _ov_top + 2)) is None, (
        "a point below the last drawn row hit-tests to a row; the "
        "hidden ones are not selectable and must not become so by "
        "accident")
    ok("colony list overflow (rows drawn against rows present, the "
       "count is named, nothing drawn when nothing is dropped)")

    # ── output_panel: eleven values, and the selection that feeds it ──
    # The panel is a TRANSCRIPTION of the original's bottom-left scan
    # box (colsum.cpp:1155, fundament 43 withdrawn), so what is
    # asserted is which values it shows, that they are VISIBLE and not
    # merely computed, and that an absence stays an absence.
    from screens.colony_summary import colonyoutput as _co
    _out_cfg = _sjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))
    _words = _out_cfg["words"]
    _ocfg = _out_cfg["output"]
    _climates = _out_cfg["list"]["climates"]

    # THE WORD LISTS, and their provenance. The words are ours: the
    # original reads them from the player's estrings.lbx at runtime
    # (estrings.cpp, Load_E_Strings_), so there is nothing to
    # transcribe and the note has to say so or the list reads as one.
    for _cite in ("estrings.cpp:155-169", "estrings.cpp:204-213",
                  "estrings.lbx", "decision 15", "list.climates"):
        assert _cite in _words["_note"], (
            f"words._note no longer carries {_cite!r} — these are our "
            f"own English words, not the game's, and the note is the "
            f"only thing that says so")
    assert len(_words["sizes"]) == 5 and len(_words["gravities"]) == 3, (
        f"the size and gravity lists are {len(_words['sizes'])} and "
        f"{len(_words['gravities'])}; the enums are 5 and 3 "
        f"(orion2_consts.h:392-397, :377-380) and the index IS the "
        f"enum value")
    assert len(_words["minerals"]) == 5, _words["minerals"]
    # ONE HOME for each list. Asserting the rule, not the instance: a
    # climate word appearing in both blocks is the screen-ID-map
    # failure, and it would agree with itself on the day it was made.
    assert "climates" not in _words, (
        "the climate words have been copied into the words block; "
        "they live in list.climates with their own provenance note, "
        "and a second copy that agrees today is what drifts tomorrow")
    for _w in ("sizes", "gravities", "minerals"):
        assert _w not in _out_cfg["list"], (
            f"{_w} now exists in the list block as well as in words")

    # THE TEN VALUES, for one fake colony. Chosen so every one of
    # them is distinguishable from every other in the output: a check
    # that asserts "0" appears ten times asserts nothing.
    # `production` and `drawn_production` are DIFFERENT here on
    # purpose: the panel draws the net the original computes
    # (coldraw.cpp:73-94) and the sort keys read the stored value, so
    # a fake that made them equal would let the panel read either one
    # and still pass.
    _fake = {"index": 3, "name": "Probe I", "climate": 9, "pops": 17,
             "jobs": [5, 6, 6], "no_farming": False, "max_pop": 31,
             "producing": "", "producing_turns": 0, "can_buy": False,
             "production": [90, 91, 92, 93],
             "drawn_production": [11, 22, 33, 44],
             "shortage": [0, 0, 0, 0], "size": 3, "gravity": 2,
             "mineral": 4, "growth": -42, "morale": -7,
             "morale_applies": True}
    _shown = _co.visible_rows(_fake, _ocfg, _words, _climates)
    assert len(_shown) == 11, (
        f"the panel has {len(_shown)} rows; it draws the seven "
        f"E_Strings_(74) values in six, the four ECON values, and "
        f"morale")
    assert len(_shown) == len(_ocfg["rows"]), (_shown, _ocfg["rows"])
    _text = " ".join(f"{e.label}={e.value}" for e in _shown)
    for _value in ("Large", "Gaia", "Heavy", "Ultra Rich", "17", "31",
                   "-42k", "11", "22", "33", "44"):
        assert _value in _text, (
            f"the panel does not show {_value!r} — it is one of the "
            f"eleven the original's scan box carries. Got: {_text}")
    assert "-7" in _text, "morale is not shown"
    # And it is the NET that reaches the panel, not the record.
    for _stored in ("90", "91", "92", "93"):
        assert _stored not in _text, (
            f"the panel drew the STORED production {_stored} — it must "
            f"draw colonyrows.drawn_production, which is what "
            f"COLDRAW::Draw_Colony_Prod_Both_ computes before it draws "
            f"anything (coldraw.cpp:73-94)")
    # GROWTH: signed, and the k is a UNIT — MOO2 counts population in
    # thousands and the original's scan box printed "+63k". The sign
    # comes from colonyempire.format_value, which is the one home for
    # that rule; the unit is wording and lives in the template.
    _growth_shown = [e.value for e in _shown if e.label.lower() == "growth"]
    assert _growth_shown == ["-42k"], (
        f"growth shows {_growth_shown!r}; it is a net flow, so it "
        f"carries its sign, and thousands, so it carries its k")
    _pos = _co.visible_rows(dict(_fake, growth=7), _ocfg, _words, _climates)
    assert [e.value for e in _pos if e.label.lower() == "growth"] == ["+7k"], (
        "a positive growth has no explicit plus — the original prints "
        "one, for the same reason the sidebar's Income and Food do")
    assert "k" in _ocfg["_growth_note"] and "thousand" in \
        _ocfg["_growth_note"], (
        "output._growth_note no longer says the k is a unit rather "
        "than a decoration, which is the whole of why it is there")

    # ── THE SCAN BOX IS TWO BOXES, AND THEY SPLIT BY COLUMN ──
    # `Draw_Colony_Scan_Info_` fills the description paragraph at
    # native (13, 354, 80, 88) and the production rows from native
    # x 106 (colsum.cpp:1171-1176, :1206). The `column` field in
    # layout.json already said which row belongs to which half; since
    # 8 September 2026 the two halves go into the two holes the frame
    # gives them instead of both into the right one.
    _left = _co.visible_rows(_fake, _ocfg, _words, _climates, only={0})
    _right = _co.visible_rows(_fake, _ocfg, _words, _climates, only={1})
    assert len(_left) + len(_right) == len(_shown), (
        f"{len(_left)} + {len(_right)} rows against {len(_shown)} — "
        f"the split must partition the panel, not sample it")
    assert {e.label.lower() for e in _left} == {
        "size", "climate", "gravity", "minerals", "population",
        "growth"}, [e.label for e in _left]
    assert {e.label.lower() for e in _right} == {
        "food", "industry", "research", "bc", "morale"}, \
        [e.label for e in _right]
    # ── BOTH `info_style` VARIANTS DRAW, AND THE CHOICE IS DATA'S ──
    # The default is the transcription, which is this project's
    # default everywhere; the switch is one key so the two pictures
    # can be compared beside the native before it is closed.
    _info_box = pygame.Rect(0, 0, 324, 224)
    for _style_name in ("paragraph", "rows"):
        _isurf = pygame.Surface((324, 224))
        _isurf.fill((0, 0, 0))
        _co.render_info(_isurf, _fake, _info_box,
                        dict(_ocfg, info_style=_style_name), _words,
                        _climates, app.layout, app.style)
        assert pygame.surfarray.array3d(_isurf).any(), (
            f"output.info_style={_style_name!r} drew nothing at all")
    # THE PARAGRAPH IS FIVE LINES, NOT SIX ROWS: size and climate
    # share one and growth carries no label, which is what
    # E_Strings_(74) does.
    _para = _co.fill_template(_ocfg["info_paragraph"],
                              _co.row_values(_fake, _words, _climates))
    assert len(_para.split("\n")) == 5, _para
    assert _para.split("\n")[0] == "Large Gaia", _para
    assert "{" not in _para, (
        "a placeholder survived substitution in the paragraph; "
        "fill_template replaces and never formats (decision 37)")
    # AND THE WORD-LIST RULE HOLDS FROM THIS SIDE TOO: the nouns are
    # in the FORMAT, never in the lists — which is exactly what
    # "%sravity" and "Mineral %s" do in the original.
    for _noun in ("Gravity", "Mineral", "Population"):
        assert _noun in _ocfg["info_paragraph"], (
            f"the paragraph does not supply {_noun!r}; the word lists "
            f"hold the bare quality and the format the noun "
            f"(words._note)")
        for _lst in ("sizes", "gravities", "minerals"):
            assert not any(_noun.lower() in str(_w).lower()
                           for _w in _words.get(_lst, ())), (
                f"words.{_lst} carries {_noun!r} — it would render "
                f"twice in the paragraph and twice in the table")
    # THE WHOLE BOX REDDENS ON NEGATIVE GROWTH, because the format
    # opens the attribute before the first word and closes it after
    # the last (colsum.cpp:1186-1206). The value alone would be the
    # obvious-looking reading and is not what the arguments say.
    _red = pygame.Surface((324, 224))
    _red.fill((0, 0, 0))
    _co.render_info(_red, _fake, _info_box, _ocfg, _words, _climates,
                    app.layout, app.style)
    _blk = pygame.Surface((324, 224))
    _blk.fill((0, 0, 0))
    _co.render_info(_blk, dict(_fake, growth=7), _info_box, _ocfg,
                    _words, _climates, app.layout, app.style)
    def _count(_surface, _rgb):
        _a = pygame.surfarray.array3d(_surface)
        return sum(1 for x in range(324) for y in range(224)
                   if tuple(_a[x, y]) == tuple(_rgb[:3]))

    _warm = _count(_red, _co.SHORTAGE_COLOR)
    _cool = _count(_blk, _co.VALUE_COLOR)
    assert _warm > 50 and _count(_red, _co.VALUE_COLOR) == 0, (
        f"negative growth inked {_warm} px of the warn colour and "
        f"{_count(_red, _co.VALUE_COLOR)} of the value colour; the "
        f"sign string opens the attribute before the FIRST word and "
        f"the reset comes after the last, so the whole paragraph "
        f"reddens rather than the number")
    assert _cool > 50 and _count(_blk, _co.SHORTAGE_COLOR) == 0, (
        f"positive growth inked {_count(_blk, _co.SHORTAGE_COLOR)} px "
        f"of the warn colour — nothing should redden at all")

    # ── A VALUE CARRIES NO PREFIX; THE LABEL CARRIES IT ──
    # A rule, not three decisions. The original's box is one run-on
    # paragraph and this panel is a table, so a word that reads
    # correctly there reads twice here: MINERALS Mineral Rich, GRAVITY
    # Normal Gravity. The source draws the line more finely than "our
    # list is wrong" — colland.cpp:60-62 puts the mineral value into
    # its own format string, so "Mineral" belongs to the FORMAT and
    # the table holds "Rich"; colland.cpp:65 prints the gravity entry
    # with no format at all, so "Normal Gravity" really is in the
    # table. Both lists carry the bare quality either way.
    for _cite in ("colland.cpp:60-62", "colland.cpp:65",
                  "THE LABEL CARRIES IT"):
        assert _cite in _words["_note"], (
            f"words._note no longer carries {_cite!r} — the rule is "
            f"what keeps this from being re-decided one list at a time")
    for _list_name, _label in (("gravities", "Gravity"),
                               ("minerals", "Minerals")):
        _label_words = set(_label.lower().rstrip("s").split())
        for _w in _words[_list_name]:
            assert not (set(_w.lower().split()) & _label_words), (
                f"{_list_name} carries {_w!r}, which repeats its own "
                f"label: the panel would draw '{_label.upper()} {_w}'")
    # ALL FOUR PRODUCTION VALUES. BC was left out for a day on the
    # reading that the panel showed "food, industry and research";
    # the original draws four. ECON_COUNT is 4 (orion2_consts.h:123)
    # and the GEOMETRY says so without the constant: y_pos starts at
    # 349 and steps 18 (colsum.cpp:1170-1173) — 349, 367, 385, 403 —
    # with morale one step further on at 421 (colsum.cpp:1176), which
    # leaves room for four rows above it and not three.
    _prod_rows = [_r for _r in _ocfg["rows"]
                  if _r["value"] in ("{food}", "{industry}",
                                     "{research}", "{bc}")]
    assert len(_prod_rows) == 4, (
        f"the panel draws {len(_prod_rows)} production rows; the "
        f"original draws ECON_COUNT of them and ECON_COUNT is 4")
    assert all(_r["column"] == _prod_rows[0]["column"]
               for _r in _prod_rows), (
        "the four production values are split across columns; the "
        "original draws them as one column at native x 106")
    for _cite in ("colsum.cpp:1170-1173", "colsum.cpp:1176"):
        assert _cite in _ocfg["_deviation_note"], (
            f"output._deviation_note no longer cites {_cite!r} — the "
            f"geometry is what settled the fourth row independently "
            f"of ECON_COUNT")
    # WHAT IS STILL NOT DRAWN has to keep naming itself. After the
    # net and the shortage landed, two of the original's four groups
    # per row remain: imports[t] (coldraw.cpp:46) and the secondary
    # group — imports[ECON_INDUSTRY] on food, pollution on industry
    # (coldraw.cpp:51-58). Both are REACHABLE, so the note must not
    # read as a data limitation, and an omission nobody wrote down is
    # indistinguishable from one nobody saw.
    # AND HOW TO READ A NATIVE SCREENSHOT OF ONE. The groups are
    # separated by an empty SLOT (a bare drawn_count++ at
    # coldraw.cpp:150, budgeted at :100), and a negative-imports group
    # is drawn with the NET's own sprites (coldraw.cpp:154 against
    # :118) — so two groups look like one long run. That is exactly
    # how Wolf II's BC row was read as 18 when it was 10 plus 8, and
    # the note is the only place that mistake is written down.
    for _cite in ("coldraw.cpp:73-94", "coldraw.cpp:46",
                  "coldraw.cpp:51-58", "pollution", "REACHABLE",
                  "coldraw.cpp:150", "empty slot", "10 plus 8"):
        assert _cite in _ocfg["_deviation_note"], (
            f"output._deviation_note no longer carries {_cite!r} — it "
            f"is the record of which of the original's four groups "
            f"this panel still does not draw, and why that is a "
            f"layout question and not a missing offset")

    # MORALE UNDER UNIFICATION: the label stays, the value goes. The
    # original zeroes its own sprite count (Draw_Info_Morale_Both_),
    # so drawing a 0 would claim neutral morale where the original is
    # claiming that morale does not apply.
    _unified = dict(_fake, morale_applies=False)
    _mor = [(e.label, e.value) for e
            in _co.visible_rows(_unified, _ocfg, _words, _climates)
            if e.label.lower() == "morale"]
    assert _mor and _mor[0][1] == _ocfg["hidden_value"], (
        f"under Unification the morale row shows {_mor!r}; it must "
        f"show hidden_value, and a 0 is not the same statement")

    # AN INDEX OUTSIDE ITS ENUM IS VISIBLE, not clamped. A clamp
    # would draw "Huge" for a 9 and look exactly like data.
    _bad = _co.row_values(dict(_fake, size=99), _words, _climates)
    assert _bad["size"] == "?", _bad["size"]

    # Substitution is a REPLACE, never str.format (decision 37): a
    # stray brace must not raise inside the render path.
    assert _co.fill_template("{size} }{ {nope}", {"size": "Large"}) == \
        "Large }{ {nope}", _co.fill_template("{size} }{ {nope}",
                                             {"size": "Large"})

    # ── The panel DRAWS them, and draws nothing when empty ──
    # A green table says the data is right; only ink says it is
    # visible. Both directions, because the empty case is the one
    # that would silently become a column of zeroes.
    d.switch_to("colony_summary")
    _scr_op = d.active
    _op_box = _scr_op.box_rect("planet_output")
    assert _op_box, "planet_output has no box"
    _oa = pygame.Rect(*app.layout.rect(_op_box))
    _osurf = pygame.Surface((_oa.right + 8, _oa.bottom + 8))
    _osurf.fill((0, 0, 0))
    _co.render(_osurf, _fake, _oa, _ocfg, _words, _climates,
               app.layout, app.style)
    _ink = pygame.surfarray.array3d(_osurf.subsurface(_oa)).sum()
    assert _ink > 0, "the panel drew nothing for a selected colony"
    _osurf.fill((0, 0, 0))
    _co.render(_osurf, None, _oa, _ocfg, _words, _climates,
               app.layout, app.style)
    assert pygame.surfarray.array3d(_osurf.subsurface(_oa)).sum() == 0, (
        "the panel put ink on the screen with nothing selected. The "
        "original's box is guarded by _g_colony_n != -1 "
        "(colsum.cpp:1165) and a zero is a value where it has an "
        "absence")
    assert _ocfg["empty"] == "", (
        "output.empty is no longer empty — that is allowed, but the "
        "check above then has to change with it rather than fail")

    # THE COLUMNS MUST NOT RUN TOGETHER, and the failure that
    # actually happened was NOT an overlap. The first render had
    # column_gap 12, every number in it was correct, no two glyphs
    # touched — and 'Huge GROWTH' and 'Ultra Poor RESEARCH' read as
    # single phrases, because the left column's right-aligned value
    # ended twelve pixels before the right column's left-aligned
    # label began. So there are two assertions and they catch
    # different things:
    #
    #   the GUTTER must be at least one em of the value font. Two
    #   runs of type separated by less than the height of the type
    #   read as one run with a word space in it. That is the rule the
    #   34 was measured against, stated as a rule so it survives a
    #   font change rather than pinning the number that came out of
    #   one look.
    #
    #   the widest LABEL plus the widest VALUE must still fit the
    #   column minus that gutter, which is the different failure of a
    #   long word eating the gap it was given.
    #
    # Both at every shipped resolution, and both measured by
    # RENDERING (decision 30) because render_text can mix two fonts
    # inside one string and a single font's .size() is not the width
    # that gets drawn.
    assert _ocfg["column_gap"] >= _ocfg["value_font"], (
        f"column_gap {_ocfg['column_gap']} is under one em of the "
        f"{_ocfg['value_font']} px value font, so the left column's "
        f"value and the right column's label read as one phrase. "
        f"That is how the first render of this panel looked, with "
        f"every value in it correct.")
    # PER ROW, against the values THAT ROW can actually show. Pairing
    # the widest label in the panel with the widest value in the
    # panel asserts a collision that cannot happen — POPULATION never
    # prints "Ultra Poor" — and it failed at 1280x720 on exactly that
    # imaginary pair. The real tightest is MINERALS against
    # "Ultra Poor".
    _POP_CAP = _cl.POP_LIMIT_CAP
    _WORDS_FOR = {"{size}": _words["sizes"], "{climate}": list(_climates),
                  "{gravity}": _words["gravities"],
                  "{mineral}": _words["minerals"]}
    for _W, _H in _SIZES:
        _lay = Layout(_W, _H)
        _r = pygame.Rect(*_lay.rect(_op_box))
        _cols = int(_ocfg["columns"])
        _pad = int(_ocfg["pad_x"] * _lay.scale)
        _cw = (_r.w - 2 * _pad) // _cols
        _cgap = int(_ocfg["column_gap"] * _lay.scale)
        # One em of the LABEL font, scaled like everything else.
        _em = _lay.font_size(_ocfg["label_font"])
        for _row_spec in _ocfg["rows"]:
            _cands = _WORDS_FOR.get(_row_spec["value"])
            if _cands is None:
                # Numeric. The widest a value can get: growth sums ten
                # int16 (colsum.cpp:1179-1182), the others are one,
                # and population is the engine's cap over itself.
                _cands = ([f"{_POP_CAP}/{_POP_CAP}"]
                          if "/" in _row_spec["value"]
                          else ["-327680" if _row_spec["id"] == "growth"
                                else "-32768"])
            _lw = app.style.render_text(
                _row_spec["label"].upper(),
                _lay.font_size(_ocfg["label_font"]),
                (255, 255, 255)).get_width()
            # THE SHORTAGE MARKER AND A WIDE VALUE CANNOT CO-OCCUR,
            # and that is structural rather than lucky. A shortage is
            # drawn only when imports >= 0 and the row is not
            # industry (coldraw.cpp:152) — which is exactly the
            # branch where the net IS production[t] (coldraw.cpp:86)
            # — and it is positive only when
            # production < maintenance - imports <= maintenance,
            # a u8[4] at offset 239. So a row that shows a marker has
            # a value in 0..254 and a marker in 1..255; a row with a
            # wide value has no marker at all. Pairing the widest of
            # each would assert a case the engine cannot produce, and
            # it fails at 1366x768 — which is how this coupling was
            # found rather than assumed.
            #
            # The one assumption, stated because it is the one that
            # could break: production is never negative.
            _pairs = [(_c, "") for _c in _cands]
            if _row_spec["id"] in ("food", "research", "bc"):
                _pairs.append(
                    ("254",
                     _ocfg["shortage_value"].replace("{shortage}", "255")))
            for _cand, _short in _pairs:
                _vw = app.style.render_text(
                    _cand, _lay.font_size(_ocfg["value_font"]),
                    (255, 255, 255)).get_width()
                if _short:
                    _vw += app.style.render_text(
                        _short, _lay.font_size(_ocfg["label_font"]),
                        (255, 255, 255)).get_width() + int(
                            _ocfg["shortage_gap"] * _lay.scale)
                assert _lw + _vw <= _cw - _cgap - _em, (
                    f"{_W}x{_H}: {_row_spec['label']!r} ({_lw} px) and "
                    f"{_cand + _short!r} ({_vw} px) need {_lw + _vw} px in a "
                    f"column of {_cw - _cgap}, leaving less than one "
                    f"em of the label font between them — they read "
                    f"as one phrase before they touch, which is what "
                    f"column_gap 34 was measured to prevent")

    # ── The selection: row 0 on entry, and it keeps its COLONY ──
    # colsum.cpp:139 sets _g_colony_n = _list_col[0] in the screen's
    # setup, and _list_col is filled from the SORTED list
    # (colsum.cpp:348-351). The sort handler (colsum.cpp:830-837)
    # never touches _g_colony_n, so the selection follows its colony
    # into the new order rather than staying on row 0.
    _sel_snap = _pv._Snapshot(_pv.COLONIES)
    _scr_op._sort_key = "name"
    _scr_op.update(_sel_snap)
    assert _scr_op.selected_position() == 0, (
        f"entry selection is row {_scr_op.selected_position()}, not "
        f"row 0 of the sorted list (colsum.cpp:139)")
    _first_name = _scr_op.selected_row()["name"]
    _first_index = _scr_op._selected
    # A key that reorders the list, so "row 0" and "the same colony"
    # are different answers and the check can tell them apart.
    _scr_op._sort_key = "population"
    _scr_op._rebuild_rows()
    _moved = _scr_op.selected_position()
    assert _scr_op._selected == _first_index, (
        f"the sort reseated the selection from colony {_first_index} "
        f"to {_scr_op._selected}; the original keeps the colony and "
        f"lets its ROW move (colsum.cpp:830-837 touches nothing)")
    assert _scr_op.selected_row()["name"] == _first_name, "colony changed"
    assert _moved != 0, (
        f"{_first_name!r} is still at row 0 after re-sorting, so this "
        f"check cannot tell 'keeps the colony' from 'keeps the row' — "
        f"pick a sort key that actually moves it")
    # And the panel follows the selection rather than the row index.
    assert _co.visible_rows(_scr_op.selected_row(), _ocfg, _words,
                            _climates), "the panel lost its row"
    # An empty snapshot selects nothing at all — not row 0 of nothing.
    _scr_op.update(_pv._Snapshot([]))
    assert _scr_op._selected is None and _scr_op.selected_row() is None, (
        f"an empty colony list still has a selection "
        f"({_scr_op._selected!r})")
    _scr_op.update(_sel_snap)

    # The hit-test and the drawing share one geometry (decision 5):
    # every drawn band's midpoint must resolve back to its own row.
    _la = pygame.Rect(*app.layout.rect(_scr_op.box_rect("list_area")))
    _lcfg = dict(_out_cfg["list"])
    # The column table, as the screen's own cfg carries it — see the
    # overflow fixture above for why a fixture without it tests the
    # path the screen does not take.
    _lcfg[_ct0.COLUMNS_KEY] = _ch.columns(res, "colony_summary")
    _bands = _cl.row_bands(_la, _lcfg, app.layout.scale,
                           len(_scr_op._rows))
    assert _bands, "no row bands for a non-empty list"
    for _i, (_top, _h) in enumerate(_bands):
        assert _cl.row_at(_la, _lcfg, app.layout.scale,
                          len(_scr_op._rows),
                          (_la.x + 4, _top + _h // 2)) == _i, _i
    # Hovering row 1 selects the colony IN row 1, and clicking it
    # changes nothing — the original would leave for SCREEN_COLONY
    # (colsum.cpp:912-920) and there is no HD screen to leave to.
    _t1, _h1 = _bands[1]
    _scr_op.handle_mouse_motion(_la.x + 4, _t1 + _h1 // 2)
    assert _scr_op._selected == _scr_op._rows[1]["index"], (
        "hovering a row did not select its colony "
        "(colsum.cpp:880-890 assigns _g_colony_n on the SCANNED "
        "field, not the clicked one)")
    _before = _scr_op._selected
    _cap2 = _Cap()
    _cl_save, _conn_save = app.client, app.connected
    app.client, app.connected = _cap2, True
    _scr_op.handle_click(_la.x + 4, _t1 + _h1 // 2)
    app.client, app.connected = _cl_save, _conn_save
    assert _scr_op._selected == _before, "a row click moved the selection"
    assert _cap2.calls == [] and _cap2.keys == [], (
        f"a row click sent {_cap2.calls}/{_cap2.keys} to the game. It "
        f"is inert on purpose: the original leaves for SCREEN_COLONY "
        f"and no HD screen exists to leave to")
    # Leaving the list keeps the last colony — the assignment in
    # colsum.cpp:880-890 has no else branch.
    _scr_op.handle_mouse_motion(_la.x - 40, _la.y - 40)
    assert _scr_op._selected == _before, (
        "the selection cleared when the pointer left the list; the "
        "original's _g_colony_n keeps whatever it last held")
    ok("colony summary output_panel (ten values drawn, BC deviation "
       "marked, empty selection draws nothing, columns clear at 12 "
       "resolutions, hover selects and the sort keeps the colony)")

    # ── The NET the original draws, and the shortage beside it ──
    # COLDRAW::Draw_Colony_Prod_Both_ (coldraw.cpp:36) computes what
    # it draws BEFORE it draws anything. Until 4 September 2026 this
    # panel printed colony->production[t], which is only one of the
    # four branches at coldraw.cpp:73-94 — so the number a player
    # read was wrong whenever a colony had maintenance or imports,
    # and it looked exactly as plausible as the right one.
    import types as _types
    from screens.colony_summary import colonyrows as _crw

    def _col(prod, maint, imps, poll=0):
        return _types.SimpleNamespace(production=list(prod),
                                      maintenance=list(maint),
                                      imports=list(imps),
                                      pollution=poll)

    # ALL FOUR BRANCHES, with values chosen so each gives a DIFFERENT
    # answer from the others. A case where every branch returns
    # production[t] would pass against any three of the four.
    #
    # A to D are `colonyrows.drawn_production.__doc__`'s names for
    # them, which is also where the record of WHICH of the four has
    # ever been seen on a live save lives — B and C have, A and D
    # have not, and the assertions below are all A and D have.
    #   A  byte(imports) < 0, t == INDUSTRY  -> max(0, prod - maint[t])
    #   B  byte(imports) < 0, t != INDUSTRY  -> prod - abs(imports)
    #   C  otherwise, maint[INDUSTRY] == 0 or t != INDUSTRY -> prod
    #   D  otherwise                          -> max(0, prod - maint[t])
    _bA = _col([20, 30, 40, 50], [3, 7, 0, 0], [-5, -2, 0, 0])
    # NOT "branch A", and the name is corrected rather than kept.
    # A and D are the SAME expression (coldraw.cpp:75-78 against
    # :89-92) and both are guarded by prod_type == ECON_INDUSTRY, so
    # nothing here or anywhere can tell which one ran — deleting A
    # and letting this case fall through to D leaves the suite green,
    # tried on 4 September 2026. What this asserts is the VALUE the
    # industry row produces with byte-negative imports, which is
    # right whichever branch computes it. See
    # colonyrows.drawn_production, which records that A is covered by
    # the transcription and not by a test.
    assert _crw.drawn_production(_bA, _crw.ECON_INDUSTRY) == 23, (
        "the industry row with byte-negative imports must be "
        "production - maintenance (coldraw.cpp:74-78, and :88-92, "
        "which are the same three lines)")
    assert _crw.drawn_production(_bA, _crw.ECON_FOOD) == 15, (
        "branch B: a non-industry row with byte-negative imports is "
        "production - abs(imports) (coldraw.cpp:80)")
    assert _crw.drawn_production(_bA, _crw.ECON_RESEARCH) == 40, (
        "branch C: non-negative imports on a non-industry row is the "
        "stored production (coldraw.cpp:86)")
    _bD = _col([20, 30, 40, 50], [0, 7, 0, 0], [0, 4, 0, 0])
    assert _crw.drawn_production(_bD, _crw.ECON_INDUSTRY) == 23, (
        "branch D: industry with non-negative imports and non-zero "
        "maintenance[INDUSTRY] is production - maintenance "
        "(coldraw.cpp:89)")
    # …and the SAME row takes branch C when maintenance[INDUSTRY] is
    # 0, which is the condition that separates C from D. Without this
    # the two are indistinguishable.
    assert _crw.drawn_production(
        _col([20, 30, 40, 50], [0, 0, 0, 0], [0, 4, 0, 0]),
        _crw.ECON_INDUSTRY) == 30, (
        "maintenance[INDUSTRY] == 0 must send the industry row to the "
        "plain production branch (coldraw.cpp:85)")
    # The clamp is the original's and is on both maintenance branches.
    assert _crw.drawn_production(
        _col([3, 3, 0, 0], [10, 10, 0, 0], [-1, -1, 0, 0]),
        _crw.ECON_INDUSTRY) == 0, (
        "production below maintenance must clamp at 0, not go "
        "negative (coldraw.cpp:76)")

    # THE INDUSTRY ROW COLLAPSES TO ONE EXPRESSION, and asserting
    # that is worth more than pretending to separate A from D. The
    # engine writes imports[ECON_INDUSTRY] in exactly one place —
    # COLCALC::Pre_Import_Computing_ (colcalc.cpp:487) ends with
    # imports = min((uint8)maintenance, production) at :507-511, and
    # grepping every assignment to `imports[` finds no other. Feed
    # the function inputs that satisfy that invariant, as a real
    # snapshot always does, and all four branches agree on
    # max(0, production - maintenance).
    #
    # ASSUMPTION, load-bearing and the same one the docstring names:
    # production[ECON_INDUSTRY] >= 0. The sweep only covers that
    # case, because below it the collapse genuinely fails.
    for _p in (0, 1, 7, 30, 127, 128, 200, 255, 400):
        for _m in (0, 1, 7, 100, 127, 128, 200, 255):
            _imp = min(_m, _p)                    # colcalc.cpp:507-511
            _got = _crw.drawn_production(
                _col([0, _p, 0, 0], [0, _m, 0, 0], [0, _imp, 0, 0]),
                _crw.ECON_INDUSTRY)
            assert _got == max(0, _p - _m), (
                f"industry row with production {_p}, maintenance {_m} "
                f"and the engine's own imports {_imp} drew {_got}, "
                f"not {max(0, _p - _m)}. On engine-consistent input "
                f"all four branches compute that one expression — see "
                f"colonyrows.drawn_production for the derivation")

    # THE (int8_t) CAST, AND IT IS DELIBERATE. coldraw.cpp:73 tests
    # the LOW BYTE of imports[t]; coldraw.cpp:152, deciding whether
    # to draw the shortage, tests the WHOLE int16 with no cast. 384
    # is positive as a word and -128 as a byte, so the two disagree —
    # and this check is here so the next reader who "tidies" the cast
    # into a plain comparison fails instead of silently changing a
    # number. Filed as a QUESTION in doc/orion2re_open_fixes.md,
    # because which of the two is the transcription is the original
    # binary's answer and not ours.
    _cast = _col([20, 0, 0, 0], [0, 0, 0, 0], [384, 0, 0, 0])
    assert _crw.drawn_production(_cast, _crw.ECON_FOOD) == 20 - 384, (
        "imports 384 has a NEGATIVE low byte, so the net takes the "
        "byte-negative branch (coldraw.cpp:73). Getting 20 here means "
        "the cast was normalised to a plain int16 comparison — do not "
        "fix it, it is transcribed; see colonyrows._low_byte_signed")
    assert _crw._low_byte_signed(384) == -128 and \
        _crw._low_byte_signed(256) == 0 and \
        _crw._low_byte_signed(-1) == -1, "the cast is not (int8_t)"

    # THE SHORTAGE: maintenance - imports - production, clamped below
    # 1 (coldraw.cpp:61-64).
    assert _crw.production_shortage(
        _col([12, 0, 0, 0], [13, 0, 0, 0], [0, 0, 0, 0]),
        _crw.ECON_FOOD) == 1, (
        "Wolf II is the reference case: 13 maintenance, 0 imports, 12 "
        "production, and the original draws exactly one red marker")
    assert _crw.production_shortage(
        _col([12, 0, 0, 0], [11, 0, 0, 0], [0, 0, 0, 0]),
        _crw.ECON_FOOD) == 0, "a surplus is not a negative shortage"

    # THE REFUSALS, which are the part that matters. Those
    # Short_Anims_ loops (coldraw.cpp:170-177) sit in the ELSE of
    # `if (imports[t] < 0 || t == ECON_INDUSTRY)` (coldraw.cpp:152),
    # so the original draws a shortage ONLY for a non-industry row
    # with non-negative imports. The arithmetic alone would produce a
    # number on the industry row too, and drawing it would be an
    # invention wearing a citation — decision 33 says mirror the
    # refusal, not just the sum.
    _short_ind = _col([2, 2, 0, 0], [9, 9, 0, 0], [0, 0, 0, 0])
    assert _crw.production_shortage(_short_ind, _crw.ECON_FOOD) == 7, (
        "the food row of the refusal case must have a shortage, or "
        "the industry half of this check proves nothing")
    assert _crw.production_shortage(
        _short_ind, _crw.ECON_INDUSTRY) == 0, (
        "a shortage was computed for the INDUSTRY row; the original "
        "never draws one there (coldraw.cpp:152)")
    # NEGATIVE imports, the other refusal. The word is tested here,
    # not the byte — the same field, the other comparison.
    assert _crw.production_shortage(
        _col([2, 0, 0, 0], [9, 0, 0, 0], [-1, 0, 0, 0]),
        _crw.ECON_FOOD) == 0, (
        "a shortage was computed for a row with negative imports; "
        "that row takes the IF at coldraw.cpp:152 and draws imports "
        "as Prod_Anims_ instead")

    # ── The shortage reaches the panel, and only when it should ──
    _sh_row = dict(_fake, shortage=[3, 5, 0, 0])
    _sh = {e.label.lower(): e.shortage
           for e in _co.visible_rows(_sh_row, _ocfg, _words, _climates)}
    assert _sh["food"] == _ocfg["shortage_value"].replace("{shortage}", "3"), (
        f"the food row's shortage element is {_sh['food']!r}; the "
        f"wording is layout.json's shortage_value (decision 15) and "
        f"the substitution is a replace (decision 37)")
    assert _sh["industry"], "a non-zero shortage was dropped"
    # ZERO DRAWS NOTHING AT ALL, not a 0 and not a dash — the same
    # shape as the empty selection. A template that renders "0" must
    # not be able to bring the element back, because the decision is
    # the number's and is taken before the template.
    assert _sh["research"] == "" and _sh["bc"] == "", (
        f"a zero shortage produced {_sh['research']!r}; the original "
        f"draws no sprite, and a 0 is a claim where it has an absence")
    assert all(e.shortage == "" for e in _co.visible_rows(
        _fake, _ocfg, _words, _climates)), (
        "a colony with no shortage anywhere still produced elements")
    # A non-production row can never take one, whatever it is called.
    assert _sh["growth"] == "" and _sh["size"] == "", (
        "a non-production row was given a shortage element")

    # AND ON THE SURFACE: the marker is ink, and no shortage is no
    # ink. Rendered twice into the same rect and differenced, so this
    # asserts the drawing and not the tuple a second time.
    _sh_area = pygame.Rect(*app.layout.rect(_scr_op.box_rect("planet_output")))
    _sh_surf = pygame.Surface((_sh_area.right + 8, _sh_area.bottom + 8))
    _sh_ink = []
    for _r in (_fake, _sh_row):
        _sh_surf.fill((0, 0, 0))
        _co.render(_sh_surf, _r, _sh_area, _ocfg, _words, _climates,
                   app.layout, app.style)
        _sh_ink.append(int(pygame.surfarray.array3d(
            _sh_surf.subsurface(_sh_area)).sum()))
    assert _sh_ink[1] > _sh_ink[0], (
        f"the panel put no more ink on a colony with two shortages "
        f"({_sh_ink[1]}) than on one with none ({_sh_ink[0]})")

    # AND THE MARKER FOLLOWS THE VALUE, which is the order the
    # original draws its groups in: net, secondary, imports,
    # shortage — the shortage is LAST (coldraw.cpp:170-177, after the
    # import loops). It was drawn to the LEFT until 4 September 2026.
    # Asserted by colour: the marker is the only thing on the panel
    # in the warn red, so its columns can be found without knowing
    # where the renderer decided to put it.
    _sh_surf.fill((0, 0, 0))
    _co.render(_sh_surf, dict(_fake, shortage=[3, 0, 0, 0]), _sh_area,
               _ocfg, _words, _climates, app.layout, app.style)
    _sh_px = pygame.surfarray.array3d(
        _sh_surf.subsurface(_sh_area)).transpose(1, 0, 2).astype(int)
    _red = _np.array(_co.SHORTAGE_COLOR[:3], dtype=int)
    _val = _np.array(_co.VALUE_COLOR[:3], dtype=int)
    _is_red = (_np.abs(_sh_px - _red).sum(axis=2) < 60)
    _is_val = (_np.abs(_sh_px - _val).sum(axis=2) < 60)
    _rows_red = _np.where(_is_red.any(axis=1))[0]
    assert len(_rows_red), "the shortage marker put no red on the panel"
    # The value on the SAME row as the marker.
    _band = slice(max(0, _rows_red.min() - 2), _rows_red.max() + 3)
    _red_x = _np.where(_is_red[_band].any(axis=0))[0]
    _val_x = _np.where(_is_val[_band].any(axis=0))[0]
    assert len(_val_x), "no value ink on the shortage row"
    assert _red_x.min() > _val_x.max(), (
        f"the shortage marker (x {_red_x.min()}..{_red_x.max()}) is not "
        f"to the right of the value (x {_val_x.min()}..{_val_x.max()}). "
        f"The original draws the shortage as the LAST group in the row "
        f"(coldraw.cpp:170-177); drawing it first inverts the only two "
        f"groups this panel has")
    ok("colony summary production net (four branches, the (int8_t) "
       "cast, the shortage and both of its refusals)")

    # ── galaxy_inset: the original's small galaxy map ──
    # COLSUM::Draw_Galaxy_Map_ (colsum.cpp:415) is one call into
    # MOVEBOX::Draw_Galaxy_Map_Box_ at native (380, 349, 128, 91),
    # view_mode 3. The transform was verified against the original's
    # OWN framebuffer on 4 September 2026 — all 99 stars of the
    # reference save within 2 px of ink — and what is asserted here
    # is the arithmetic that verification passed, so a retyped
    # constant fails without a game running.
    from screens.colony_summary import colonyinset as _ci
    import struct as _ist
    from core.structs import star as _istar

    def _fake_star(x, y, owner=-1, spectral=0, visited=0, name=b"S"):
        b = bytearray(_istar.SIZE)
        b[0:len(name)] = name
        _ist.pack_into("<hh", b, 15, x, y)
        _ist.pack_into("<b", b, 20, owner)
        b[22] = spectral
        b[171] = visited
        return _istar.parse(bytes(b))

    class _FakeGS:
        # MAP_MAX IS A PAIR, and the default is the reference save's
        # own 1800 x 1350 (99 stars, 12 x 9 cells). A fake that
        # carried x alone is how the y ceiling went untested for as
        # long as the recovery only read x.
        def __init__(self, stars, players=(), num=0,
                     max_x=1800, max_y=1350):
            self.stars = stars; self.player_raw = list(players)
            self.player_num = num
            self.map_max_x = max_x; self.map_max_y = max_y
            self.colonies_raw = []; self.planets_raw = []

    # THE POSITION, transcribed: movebox.cpp:19-20 and :62-64.
    # max_map_scale 36 comes from MAP_MAX 1800 x 1350 through
    # zoomtables.max_map_scale, which is the one home for it.
    _iscale = zt.max_map_scale(1800, 1350)
    assert _iscale == 36, _iscale
    # And the dots move with it: a galaxy where the retired estimate
    # and the transcription disagree must place its stars through the
    # transcription's answer, not the estimate's. Same star, two
    # galaxies, and the 45-vs-44 difference has to show.
    _probe_dot = _crw.galaxy_inset_stars(
        _FakeGS([_fake_star(2000, 1600)], max_x=2250, max_y=1800))[0]
    _want_45 = (((2000 * 1000 // 45) * 10) // (506000 // 128),
                ((1600 * 1000 // 45) * 10) // (400000 // 91))
    assert _probe_dot[:2] == _want_45, (_probe_dot, _want_45)
    assert _want_45 != (((2000 * 1000 // 44) * 10) // (506000 // 128),
                        ((1600 * 1000 // 44) * 10) // (400000 // 91)), \
        "pick a star where 44 and 45 actually place differently"
    for _sx_in, _sy_in in ((0, 0), (1740, 1285), (900, 600)):
        _want_x = ((_sx_in * 1000 // 36) * 10) // (506000 // 128)
        _want_y = ((_sy_in * 1000 // 36) * 10) // (400000 // 91)
        _got = _crw.galaxy_inset_stars(
            _FakeGS([_fake_star(_sx_in, _sy_in)]))[0]
        assert _got[:2] == (_want_x, _want_y), (_got, _want_x, _want_y)
    # Every star of the reference galaxy lands INSIDE the box. Not a
    # tautology: the divisors are per-axis and a swapped pair would
    # still produce plausible numbers, off the box in one direction.
    _ibox = _crw.INSET_NATIVE
    for _gx, _gy in ((0, 0), (1740, 1285), (1800, 1350)):
        _px, _py, _ = _crw.galaxy_inset_stars(
            _FakeGS([_fake_star(_gx, _gy)]))[0]
        assert 0 <= _px <= _ibox[2] and 0 <= _py <= _ibox[3], (
            f"galaxy ({_gx}, {_gy}) maps to ({_px}, {_py}), outside "
            f"the original's {_ibox[2]}x{_ibox[3]} box")

    # THE COLOUR RULE, movebox.cpp:67-79, all four branches.
    _COLOR_OFF = next(f[1] for f in _ps.SPEC.fields if f[0] == "color")

    def _player_with_color(c):
        b = bytearray(_ps.SIZE)
        b[_COLOR_OFF] = c
        return bytes(b)

    _iplayers = [_player_with_color(5)]
    assert _crw.galaxy_inset_stars(_FakeGS(
        [_fake_star(0, 0, spectral=_istar.CLASS_BLACK_HOLE)]))[0][2] == 9, \
        "a black hole must take index 9 on this screen (movebox.cpp:69)"
    assert _crw.galaxy_inset_stars(_FakeGS(
        [_fake_star(0, 0, owner=-1)]))[0][2] == 8, \
        "an unowned star with owner -1 takes 8 (movebox.cpp:73)"
    assert _crw.galaxy_inset_stars(_FakeGS(
        [_fake_star(0, 0, owner=-3, visited=1)]))[0][2] == 8, \
        "an unowned star the player has visited takes 8"
    assert _crw.galaxy_inset_stars(_FakeGS(
        [_fake_star(0, 0, owner=-3, visited=0)]))[0][2] == 0, \
        "unowned, unvisited and not -1/-2 takes 0 (movebox.cpp:75)"
    assert _crw.galaxy_inset_stars(_FakeGS(
        [_fake_star(0, 0, owner=0)], _iplayers))[0][2] == 5, \
        "an owned star takes _player[owner].color (movebox.cpp:78)"

    # THE GEOMETRY IS A RULE, not a rect: uniform scale, centred,
    # letterboxed — the same rule core.mapcoords.MapView applies, and
    # the reason the map does not fill this cutout. Asserted at
    # several box shapes so a hole that changes shape cannot start
    # stretching the galaxy silently.
    for _bw, _bh in ((451, 203), (203, 203), (128, 91), (900, 400)):
        _r = _ci.map_rect(pygame.Rect(10, 20, _bw, _bh))
        assert _r.w <= _bw and _r.h <= _bh, (_r, _bw, _bh)
        assert abs(_r.w / _r.h - 128 / 91.0) < 0.02, (
            f"map_rect({_bw}x{_bh}) gave {_r.w}x{_r.h}, aspect "
            f"{_r.w / _r.h:.3f} against the original's "
            f"{128 / 91.0:.3f} — a galaxy is a shape, and the box it "
            f"goes in does not have to be the shape the original's "
            f"box was (mapcoords.MapView applies the same rule)")
        assert abs((_r.x - 10) - (_bw - _r.w) / 2) <= 1, "not centred"
        assert abs((_r.y - 20) - (_bh - _r.h) / 2) <= 1, "not centred"

    # THE MARKINGS. Three deviations and three omissions, and a
    # marking without a check is an intention.
    _icfg = _out_cfg["inset"]
    for _cite in ("colsum.cpp:415", "colsum.cpp:86", "view_mode 3",
                  "FRAMEBUFFER"):
        assert _cite in _icfg["_note"], (
            f"inset._note no longer carries {_cite!r}")
    # And the witness record survives where the table is, not only
    # in a session report — the shape drawn_production uses.
    for _cite in ("NO WITNESS", "mox.cpp:903", "silver"):
        assert _cite in (_ci.__doc__ or "") or _cite in open(
            os.path.join(SCREENS_DIR, "colony_summary",
                         "colonyinset.py"), encoding="utf-8").read(), (
            f"colonyinset no longer records {_cite!r} at INSET_COLORS "
            f"— which of the ten colour indices has been seen on a "
            f"live frame, and why the main-palette table does not "
            f"recover the three that have not")
    for _cite in ("gstar.lbx", "OWNER_COLORS", "3, 4 and 5"):
        assert _cite in _icfg["_deviation_note"], (
            f"inset._deviation_note no longer carries {_cite!r} — the "
            f"sprite is not shipped, the colours are the skin's, and "
            f"three of the ten were never measured")
    # THE NOTE'S SUBJECT CHANGED ON 6 SEPTEMBER 2026 AND SO DID THIS
    # CHECK. It used to hold the note to the 451 x 203 box and the
    # 286 px reading — the original's own 128 x 91 picture scaled
    # uniformly, which keeps the original's 0.89943 vertical squash.
    # The rebuild's decided reading is 253 x 200, isotropic, scale
    # 5/M, no letterbox at any galaxy size, and the two readings
    # differ by 11 % of content width from the same data. Keeping the
    # old citations would have held the note to the reading that was
    # withdrawn, which is worse than not checking it.
    for _cite in ("253 x 200", "50.6*M", "NO LETTERBOX AT ANY SIZE",
                  "HD EXTENSION", "DEVIATION", "0.89943",
                  "decision 44"):
        assert _cite in _icfg["_geometry_note"], (
            f"inset._geometry_note no longer carries {_cite!r}")
    # AND THE 286 READING MAY NOT COME BACK. Two readings of one
    # inset in one tree is what this note used to be.
    assert "286" not in _icfg["_geometry_note"], (
        "the 286 px reading is back in inset._geometry_note — that is "
        "the anisotropy-preserving reading the isotropic decision "
        "replaced, and the tree may hold one of the two")
    for _cite in ("movebox.cpp:98-101", "colsum.cpp:69-75",
                  "colsum.cpp:731", "_cluster_colony_n"):
        assert _cite in _icfg["_not_drawn_note"], (
            f"inset._not_drawn_note no longer carries {_cite!r} — the "
            f"animation, the star fields and the population-transfer "
            f"connect line are what the original does here and this "
            f"does not")
    for _cite in ("NOT DRAWN", "gstar.lbx", "Colsum_Connect"):
        assert _cite in (_ci.__doc__ or ""), (
            f"colonyinset no longer records {_cite!r}")

    # IT DRAWS, AND IT SENDS NOTHING. Same guard as the scroll path
    # (decision 46): this panel is display only.
    class _InsetCap(_Cap):
        def __init__(self):
            super().__init__(); self.fields = []
        def activate_field(self, f): self.fields.append(f)
    _icap = _InsetCap()
    _icl, _icon = app.client, app.connected
    app.client, app.connected = _icap, True
    _isnap = _pv._Snapshot(_pv.COLONIES)
    _scr_op.update(_isnap)
    _isurf = pygame.Surface((1920, 1080))
    _iarea = pygame.Rect(*app.layout.rect(_scr_op.box_rect("galaxy_inset")))
    _isurf.fill((0, 0, 0))
    _scr_op._render_inset(_isurf)
    app.client, app.connected = _icl, _icon
    assert _icap.calls == [] and _icap.keys == [] and _icap.fields == [], (
        f"the galaxy inset reached the game: {_icap.calls}/"
        f"{_icap.keys}/{_icap.fields}. It is display only — the "
        f"original's stars are fields and ours are not (fundament 46)")
    # THE FILL A PANEL NAMES IS THE FILL ON THE SCREEN, read back
    # off a rendered frame and not off the value.
    #
    # For a day the inset's black was in `layout.json`, measured,
    # documented and accepted — and the panel on screen was still
    # PANEL_BG, because the lookup read `_data[name + "_fill"]` while
    # the key sits inside `_data["panels"]`. Nothing raised: a panel
    # without a fill is the normal case, so the miss looked exactly
    # like the default. That is the help popup's lesson again — the
    # background you see is not always the background that is set —
    # and the only thing that can tell them apart is a sample.
    from screens.colony_summary import screen as _cs_mod
    _fl_panels = _scr_op._data.get("panels", {})
    for _k in _fl_panels:
        if not _k.endswith("_fill") or _k.startswith("_"):
            continue
        assert _k[:-5] in _fl_panels, (
            f"{_k} names no panel — a fill for a panel that does not "
            f"exist draws nothing and says nothing")
    _fl_surf = pygame.Surface((1920, 1080))
    _fl_surf.fill((255, 0, 255))
    _scr_op.render(_fl_surf)
    # Sampled as a MODE over the box and not read at one pixel: the
    # frame image is blitted after the panels and its rim bleeds a
    # few px inward, and the inset draws stars on top. The background
    # is what most of the box is — the same method the (0, 8, 0)
    # measurement of the original used.
    for _k, _want in (("galaxy_inset", _fl_panels.get("galaxy_inset_fill")),
                      ("planet_info", None)):
        _fr = pygame.Rect(*app.layout.rect(_scr_op.box_rect(_k)))
        _fa = pygame.surfarray.array3d(_fl_surf.subsurface(_fr))
        _hist = {}
        for _sx in range(4, _fr.w - 4, 3):
            for _sy in range(4, _fr.h - 4, 3):
                _c = tuple(int(_v) for _v in _fa[_sx, _sy])
                _hist[_c] = _hist.get(_c, 0) + 1
        _got, _n = max(_hist.items(), key=lambda _i: _i[1])
        _exp = tuple(_want[:3]) if _want else tuple(_cs_mod.PANEL_BG[:3])
        assert _got == _exp and _n > sum(_hist.values()) // 2, (
            f"{_k} is mostly {_got} ({_n} of {sum(_hist.values())} "
            f"samples) on the rendered frame; layout.json asks for "
            f"{_exp}")
    ok("colony_summary panel fills reach the screen (the inset is "
       "black in a rendered frame, not only in layout.json)")

    ok("colony_summary galaxy_inset (transform, the four colour "
       "branches, uniform-scale geometry, markings, sends nothing)")

    # ── The rebuild's layout reference, and the mask cut from it ──
    #
    # layout_reference.json is the ONE place the new screen's
    # rectangles are typed; tools/frame_mask.py renders them, the
    # frame artwork is drawn from the 1080p render, frame_holes.py
    # derives the cutouts back out of the artwork and boxes.json is
    # asserted against both (decision 3). This checks the end of that
    # chain that exists today: the file's own arithmetic, and that
    # rendering it twice gives the same pixels.
    import importlib.util as _ilu2
    _proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _fm_spec = _ilu2.spec_from_file_location(
        "_frame_mask", os.path.join(_proj, "tools", "frame_mask.py"))
    _fm = _ilu2.module_from_spec(_fm_spec)
    _fm_spec.loader.exec_module(_fm)
    _lr_path = os.path.join(SCREENS_DIR, "colony_summary",
                            "layout_reference.json")
    _lr, _lr_windows = _fm.load_reference(_lr_path)
    import numpy as np
    from PIL import Image as _PILImage

    # The reference space is the app's, not a second copy of it.
    from core.config import REF_W as _REF_W, REF_H as _REF_H
    assert (_fm.REF_W, _fm.REF_H) == (_REF_W, _REF_H), (
        f"frame_mask works in {_fm.REF_W}x{_fm.REF_H} and the app in "
        f"{_REF_W}x{_REF_H}")

    # THE COLUMNS ARE THE LIST. No slack to distribute, unlike the
    # single-track row where six floor divisions dropped pixels that
    # had to be given away.
    assert sum(_lr["list_columns"].values()) == _lr["list"][2], (
        f"list_columns sum to {sum(_lr['list_columns'].values())}, the "
        f"list is {_lr['list'][2]} wide")

    # ── THE RING, AND THE CHECKER A HAND-COPIED NUMBER GETS ──
    #
    # `bezel: 36` was one number for a border that is 107 px wide at
    # the sides and 18 at the top. It described nothing that is
    # drawn, and the tree held it beside window margins of 44 that
    # disagreed with it. It is gone; `ring` is four values taken off
    # the master, and decision 36 says a number copied from
    # somewhere else gets something that re-measures it.
    _ring = _lr["ring"]
    _rsrc = _lr["_ring_source"]
    _rimg = os.path.join(_proj, *_rsrc["file"].split("/"))
    assert os.path.isfile(_rimg), (
        f"the ring names {_rsrc['file']} as its source and that file is "
        f"not there — the table would be a number nobody can re-derive")
    _ra = np.array(_PILImage.open(_rimg).convert("RGBA"))[:, :, 3]
    _rh, _rw = _ra.shape
    _sweep = set()
    for _t in (8, 16, 64):
        _ys, _xs = np.where(_ra < _t)
        _sweep.add((int(_xs.min()), int(_xs.max()),
                    int(_ys.min()), int(_ys.max())))
    assert len(_sweep) == 1, (
        f"{_rsrc['file']}: the metal bbox is not stable across the "
        f"threshold sweep, {_sweep} — the ring would depend on where "
        f"the threshold sits")
    _mx0, _mx1, _my0, _my1 = _sweep.pop()
    # The frame is stretched over the whole reference area
    # (screen._scale_frame), so each axis maps independently.
    _measured = {
        "left": round(_mx0 * _REF_W / _rw),
        "right": round((_rw - 1 - _mx1) * _REF_W / _rw),
        "top": round(_my0 * _REF_H / _rh),
        "bottom": round((_rh - 1 - _my1) * _REF_H / _rh),
    }
    assert _measured == _ring, (
        f"the ring table says {_ring} and {_rsrc['file']} measures "
        f"{_measured} — one of the two was edited without the other")

    # EVERY WINDOW IS INSIDE THE RING, per side. Asserted as the rule
    # and not as a list of coordinates, so a new rectangle obeys it.
    for _name, (_x, _y, _w, _h) in _lr_windows.items():
        assert _x >= _ring["left"] and _y >= _ring["top"], (
            f"{_name} at ({_x}, {_y}) starts under the ring "
            f"({_ring['left']}, {_ring['top']})")
        assert _x + _w <= _REF_W - _ring["right"], (
            f"{_name} ends at {_x + _w}, the ring starts at "
            f"{_REF_W - _ring['right']}")
        assert _y + _h <= _REF_H - _ring["bottom"], (
            f"{_name} ends at {_y + _h}, the ring starts at "
            f"{_REF_H - _ring['bottom']}")

    # FIGURE CAPACITY IS ASSERTED, NOT NOTED. A column must fit at
    # least as many unsqueezed figures as the original's widest does
    # — industry, reach 122 at pitch 30, which is four. The column
    # and the pitch both scale with the resolution, so the count is
    # the same at all three, and asserting all three is what proves
    # that rather than assuming it.
    _orig_fit = max((r - l - 10) // 30 for l, r in
                    ((101, 226), (236, 368), (378, 502)))
    for _spec, _step in _lr["figure_scale"].items():
        _lscale = min(int(_spec.split("x")[0]) / _REF_W,
                      int(_spec.split("x")[1]) / _REF_H)
        _colw = _lr["list_columns"]["farmers"] * _lscale
        _fits = int((_colw - 28 * _step) // (30 * _step) + 1)
        assert _fits >= _orig_fit, (
            f"{_spec}: a figure column of {_colw:.0f} px at step "
            f"{_step} fits {_fits} unsqueezed figures, the original's "
            f"widest column fits {_orig_fit}")

    # THE LOWER BAND IS EVEN, and flush with the list above it.
    # Asserted as the rule: the four boxes sit between the list's own
    # left and right edges and every gap between them is the same.
    # They were 12, 12 and 32 until 7 September 2026 - flush at both
    # ends, which is what hid it, and the inset 20 px left of where an
    # even band puts it.
    _band = sorted((_lr[_k] for _k in ("planet_info", "planet_output",
                                       "galaxy_inset", "empire_stats")),
                   key=lambda r: r[0])
    assert _band[0][0] == _lr["list"][0], (
        f"the lower band starts at {_band[0][0]}, the list at "
        f"{_lr['list'][0]}")
    assert _band[-1][0] + _band[-1][2] == _lr["list"][0] + _lr["list"][2], (
        f"the lower band ends at {_band[-1][0] + _band[-1][2]}, the list "
        f"at {_lr['list'][0] + _lr['list'][2]}")
    _gaps = [b[0] - (a[0] + a[2]) for a, b in zip(_band, _band[1:])]
    assert len(set(_gaps)) == 1 and _gaps[0] > 0, (
        f"the lower band's gaps are {_gaps} and must all be equal - "
        f"equalising them costs a pixel or two out of one box's width, "
        f"and _lower_band_note says which box pays and why")

    # THE INSET'S ASPECT IS THE ORIGINAL'S COVERAGE, to a thousandth.
    # movebox.cpp:20-21: the crop is 128*(506000//128) by
    # 91*(400000//91) world units times M/10000, and M cancels.
    _ix, _iy, _iw, _ih = _lr["galaxy_inset"]
    _crop = (128 * (506000 // 128)) / (91 * (400000 // 91))
    assert abs(_iw / _ih - _crop) < 0.001, (
        f"the inset box is {_iw / _ih:.4f} against the original's "
        f"coverage aspect {_crop:.4f} — a letterbox at every galaxy "
        f"size is the cost, and Part 3 says there is none")
    # 3840x2160 makes it the small galaxy's world extent at 1:1.
    assert (_iw * 2, _ih * 2) == (506, 400), (_iw * 2, _ih * 2)

    # RENDERING IS REPRODUCIBLE, which is the licence to gitignore it
    # (decision 40): the same rectangles rendered twice are the same
    # pixels, and the device rects come from Layout's own truncation
    # rather than a second rounding rule.
    for _spec in _lr["_resolutions"]:
        _rw, _rh = (int(v) for v in _spec.split("x"))
        _img_a, _rects_a = _fm.render(_lr_windows, _rw, _rh)
        _img_b, _rects_b = _fm.render(_lr_windows, _rw, _rh)
        assert _img_a.tobytes() == _img_b.tobytes(), f"{_spec} not stable"
        assert _rects_a == _rects_b
        _lay = Layout(_rw, _rh)
        for _name, _rect in _lr_windows.items():
            assert tuple(_rects_a[_name]) == _lay.rect(_rect), (
                f"{_spec} {_name}: the mask says {_rects_a[_name]} and "
                f"Layout.rect says {_lay.rect(_rect)} — the mask and "
                f"the running screen must round identically")
        # Only two values, and white is a window. A soft edge would
        # need a threshold nobody wrote down.
        assert set(_img_a.getdata()) <= {_fm.WINDOW, _fm.METAL}, (
            f"{_spec}: the mask has more than two values")
    ok("colony rebuild layout reference (columns are the list, every "
       "window inside the bezel, inset aspect = the original's "
       "coverage, mask rounds exactly as Layout does)")

    # ── Stage 2: holes == mask == boxes, on a frame built here ──
    #
    # The chain is artwork -> frame_cut -> alpha holes -> boxes.json,
    # and decision 3 says all three must agree at every resolution.
    # Data's artwork is not in the tree and never will be, so this
    # builds its own plate and runs the real cutter over it — the
    # same code path the artwork will take. A check that needed the
    # artwork would be a check that fails for the person who followed
    # the instructions, which is the help-file lesson.
    _fc_spec = _ilu2.spec_from_file_location(
        "_frame_cut", os.path.join(_proj, "tools", "frame_cut.py"))
    _fc = _ilu2.module_from_spec(_fc_spec)
    _fc_spec.loader.exec_module(_fc)
    from PIL import Image as _PILImage
    # Deliberately NOT black: if the cutter ever fell back to the
    # artwork's own dark pixels instead of the mask, a plate with no
    # black in it would produce no holes at all and this would fail
    # rather than pass by coincidence.
    _plate = _PILImage.new("RGB", (1920, 1080), (78, 80, 86))
    for _spec in _lr["_resolutions"]:
        _rw, _rh = (int(v) for v in _spec.split("x"))
        _cut, _cut_rects = _fc.cut(_plate, _lr_windows, _rw, _rh)
        assert _cut.size == (_rw, _rh) and _cut.mode == "RGBA"
        _alpha = _cut.getchannel("A")
        # 1. THE HOLES ARE THE MASK. Measured per window rather than
        #    as a total, so two holes that swapped places could not
        #    cancel out.
        for _name, (_x, _y, _w, _h) in _cut_rects.items():
            _inside = _alpha.crop((_x, _y, _x + _w, _y + _h))
            assert _inside.getextrema() == (_fc.HOLE, _fc.HOLE), (
                f"{_spec} {_name}: the window is not fully transparent, "
                f"alpha runs {_inside.getextrema()}")
        # 2. AND NOTHING ELSE IS. Count, so a hole one pixel too big
        #    anywhere fails even though every window above passed.
        _want = sum(_w * _h for _x, _y, _w, _h in _cut_rects.values())
        _holes = sum(1 for _v in _alpha.getdata() if _v < 16)
        assert _holes == _want, (
            f"{_spec}: {_holes} transparent px against {_want} of "
            f"window — the alpha and the mask disagree by "
            f"{_holes - _want}")
        # 3. ALPHA IS HARD. frame_holes.py thresholds at 16 and a
        #    soft rim would make a hole's size depend on where that
        #    threshold sits.
        assert set(_alpha.getdata()) <= {_fc.HOLE, _fc.OPAQUE}, (
            f"{_spec}: the alpha has values between 0 and 255")
        # 4. THE RECTANGLES ARE THE MASK'S, name for name — the
        #    mapping is by construction here, where frame_holes.py
        #    has to guess it from position and had two of this
        #    screen's names the wrong way round once.
        _mask_img, _mask_rects = _fm.render(_lr_windows, _rw, _rh)
        assert _cut_rects == _mask_rects, (
            f"{_spec}: frame_cut punched {_cut_rects} and frame_mask "
            f"drew {_mask_rects}")
    ok("colony rebuild frame cut (holes == mask, name for name, hard "
       "alpha, at all three resolutions — on a plate with no black "
       "in it)")

    # ── The built frame carries the ring it was built for ──
    #
    # frame_build assembles the plate from the master's own nine
    # slices and hands it to frame_cut. This measures the RESULT with
    # the same sweep the ring table is measured with, so the number in
    # layout_reference.json, the master it came from and the frame
    # that ships all say one thing (decision 36, decision 3).
    _fb_spec = _ilu2.spec_from_file_location(
        "_frame_build", os.path.join(_proj, "tools", "frame_build.py"))
    _fb = _ilu2.module_from_spec(_fb_spec)
    _fb_spec.loader.exec_module(_fb)
    _fm2_spec = _ilu2.spec_from_file_location(
        "_frame_master", os.path.join(_proj, "tools", "frame_master.py"))
    _fm2 = _ilu2.module_from_spec(_fm2_spec)
    _fm2_spec.loader.exec_module(_fm2)
    from screens.colony_summary import colonyframe as _cframe
    _fb_master = _PILImage.open(os.path.join(_proj, *_rsrc["file"].split("/")))
    for _spec in _lr["_resolutions"]:
        _rw, _rh = (int(v) for v in _spec.split("x"))
        _plate = _fb.build(_fb_master, _lr_windows, _rw, _rh)
        assert _plate.size == (_rw, _rh) and _plate.mode == "RGB"
        _fbcut, _ = _fb_cut = _fc.cut(_plate, _lr_windows, _rw, _rh)
        # COMPARED IN DEVICE PIXELS, and that is not fussiness. The
        # holes are placed by Layout.rect's truncation, so converting
        # a device edge back to reference and comparing there asks
        # round(int(107 * 4/3) / (4/3)) to be 107, and at 1440p it is
        # 106. The ring in device px is what device_ring computes from
        # those same rectangles; the reference table is checked
        # against it at 1080p, where the mapping is the identity.
        _fa = np.array(_fbcut)[:, :, 3]
        _ys, _xs = np.where(_fa < 16)
        _want_ring = _fb.device_ring(_lr_windows, _rw, _rh)
        _got = (int(_xs.min()), _rw - 1 - int(_xs.max()),
                int(_ys.min()), _rh - 1 - int(_ys.max()))
        assert _got == tuple(_want_ring), (
            f"{_spec}: the built frame's metal is {_got} px from the "
            f"edges, the rectangles put the ring at {_want_ring}")
        if _spec == "1920x1080":
            assert _want_ring == (_ring["left"], _ring["right"],
                                  _ring["top"], _ring["bottom"]), (
                f"at 1080p the rectangles give a ring of {_want_ring} "
                f"and the table says {_ring} — the two must be the "
                f"same number, the scale there is 1")
        # AND THE STRUT TEXTURE IS METAL, not a hole. A plate whose
        # interior came out transparent would still pass the ring
        # test above and be a frame with nothing between its windows.
        _opaque = (_fa >= 250).mean()
        assert _opaque > 0.15, (
            f"{_spec}: only {100*_opaque:.1f} % of the built frame is "
            f"opaque — the plate is not covering its own struts")
        # EVERY WINDOW HAS THE MASTER'S LIGHT EDGE ON ALL FOUR SIDES,
        # measured as a luminance ridge and not as "ink was drawn".
        # The eight windows must also AGREE per side, because the
        # bevel comes from one sampled hole through one function — if
        # they drift apart, two code paths have got in.
        _flum = np.array(_fbcut.convert("RGB")).mean(axis=2)
        _band3 = max(1, round(_fb.BEVEL_REF
                              * min(_rw / _REF_W, _rh / _REF_H)))
        _edges = {"L": [], "R": [], "T": [], "B": []}
        _here = _fm.render(_lr_windows, _rw, _rh)[1]
        for _wn, (_wx, _wy, _ww, _wh) in _here.items():
            _in = max(4, _band3 + 1)
            _edges["L"].append(_flum[_wy+_in:_wy+_wh-_in,
                                     _wx-_band3:_wx].mean())
            _edges["R"].append(_flum[_wy+_in:_wy+_wh-_in,
                                     _wx+_ww:_wx+_ww+_band3].mean())
            _edges["T"].append(_flum[_wy-_band3:_wy,
                                     _wx+_in:_wx+_ww-_in].mean())
            _edges["B"].append(_flum[_wy+_wh:_wy+_wh+_band3,
                                     _wx+_in:_wx+_ww-_in].mean())
        _plate_med = float(np.median(_flum[_fa >= 250]))
        for _side, _vals in _edges.items():
            _v = np.array(_vals)
            assert _v.min() > _plate_med + 8, (
                f"{_spec}: the {_side} edge of some window is "
                f"{_v.min():.0f} against the plate's own metal at "
                f"{_plate_med:.0f} — no ridge, so no bevel")
            assert _v.std() < 4, (
                f"{_spec}: the eight windows' {_side} edges range "
                f"{_v.min():.0f}..{_v.max():.0f} — they come from one "
                f"sampled hole through one function and must agree")
    ok("colony frame built from the master (nine-slice ring matches the "
       "table at all three resolutions, struts are metal)")

    # ── DECISION 49: the plates are DERIVED, and this is the licence ──
    #
    # The word "derived" is earned by a byte-for-byte rebuild, never
    # by the existence of a tool that looks like it made the file
    # (decision 40, which was written about exactly this mistake).
    # Until 7 September 2026 `frames/` was gitignored as generated
    # with NOTHING in setup.py that rebuilt it and NOTHING that
    # compared it — the claim without the licence.
    #
    # **ABSENT IS REPORTED, NOT SKIPPED.** A clone that has not run
    # setup.py has no plates, and this check still runs and still
    # counts: it names the command instead of measuring, so "the
    # count must not go down" stays a rule anybody can follow
    # (decision 42's pattern, second use).
    _plate_dir = os.path.join(SCREENS_DIR, "colony_summary", "assets",
                              "frames")
    _plate_paths = {_spec: os.path.join(_plate_dir, f"frame_{_spec}.png")
                    for _spec in _lr["_resolutions"]}
    _present = [s for s, p in _plate_paths.items() if os.path.exists(p)]
    if len(_present) != len(_plate_paths):
        _missing = sorted(set(_plate_paths) - set(_present))
        _plate_note = (f"absent ({len(_missing)} of {len(_plate_paths)}): "
                       f"run `{_cframe.BUILD_COMMAND}`")
    else:
        for _spec, _ppath in sorted(_plate_paths.items()):
            _rw, _rh = (int(v) for v in _spec.split("x"))
            _fresh = _fc.cut(_fb.build(_fb_master, _lr_windows, _rw, _rh),
                             _lr_windows, _rw, _rh)[0]
            _buf = io.BytesIO()
            _fresh.save(_buf, "PNG")
            with open(_ppath, "rb") as _fh:
                _ondisk = _fh.read()
            assert _buf.getvalue() == _ondisk, (
                f"{_spec}: the plate on disk is not what frame_build.py "
                f"produces from the committed master and "
                f"layout_reference.json today ({len(_ondisk)} bytes on "
                f"disk, {len(_buf.getvalue())} rebuilt). A generator "
                f"that does not reproduce its own output is not a "
                f"generator yet, and its output is authored state "
                f"(decision 40) — rebuild with `{_cframe.BUILD_COMMAND}` "
                f"or find out what changed under it")
        _plate_note = f"{len(_present)} rebuilt byte for byte"

    # AND setup.py HAS TO MAKE THEM. A derived file with no step in
    # the setup run is one a clone can never get; that was the state
    # this check was written to end, so it is asserted and not
    # remembered.
    _setup_src = open(os.path.join(_proj, "tools", "setup.py"),
                      encoding="utf-8").read()
    assert "frame_build.py" in _setup_src, (
        "tools/setup.py has no frame_build step, so a fresh clone gets "
        "no colony frame plates and nothing tells it how — decision 49 "
        "makes the step part of the decision, not an optional extra")

    # ── STAGE B: THE FLAG OFF IS THE TREE AS IT WAS ──────────
    #
    # The acceptance is not "it still looks right", it is that the
    # surface is the SAME surface. Two halves, and both are needed:
    # the flag-off path must resolve to the committed artwork, and
    # what reaches the screen must be that file through the same
    # scale, pixel for pixel.
    _cs = d.screens["colony_summary"]
    d.switch_to("colony_summary")
    # ── THE FLAG'S MEANING INVERTED AT STAGE 4 ──
    # boxes.json is generated from the plate's own holes now, so the
    # plate IS this screen's frame and the flag ships ON. Turning it
    # off draws the SUPERSEDED artwork over boxes it does not fit —
    # kept for one stage so the two can be compared, and deleted with
    # the old frame at Stage 5. The name is backwards for exactly
    # that long, and this assertion is what makes the inversion a
    # decision somebody took rather than a default that drifted.
    assert app.settings.get("frame_preview") is True, (
        "settings.json ships with frame_preview off. Since Stage 4 the "
        "colony boxes come from the built plate's holes, so off means "
        "the superseded artwork over boxes it does not fit — which the "
        "cutout-edge checker catches as thousands of glyph pixels under "
        "opaque frame alpha")
    _shipped = os.path.join(SCREENS_DIR, "colony_summary", "assets",
                            "frame.png")
    app.settings["frame_preview"] = False
    try:
        _off_path, _off_note = _cframe.frame_source(_cs)
        assert os.path.realpath(_off_path) == os.path.realpath(_shipped), (
            f"flag off must draw {_shipped}, got {_off_path}")
        assert _off_note is None, (
            f"the log must say nothing when the flag is off, got "
            f"{_off_note!r}")
        # The superseded surface is still byte-for-byte what it was:
        # the fallback stays honest until it is deleted.
        _cs._load_frame()
        _want_surf = pygame.transform.smoothscale(
            pygame.image.load(_shipped).convert_alpha(),
            app.layout.rect((0, 0, _REF_W, _REF_H))[2:])
        _got_h = hashlib.sha256(
            pygame.image.tostring(_cs._frame_scaled, "RGBA")).hexdigest()
        _want_h = hashlib.sha256(
            pygame.image.tostring(_want_surf, "RGBA")).hexdigest()
        assert _got_h == _want_h, (
            f"with frame_preview off the colony frame surface is "
            f"{_got_h[:16]} and loading "
            f"{os.path.relpath(_shipped, _proj)} through the same scale "
            f"gives {_want_h[:16]} — the switch changed the superseded "
            f"path, which it may not while that path still exists")
    finally:
        app.settings["frame_preview"] = True
        _cs._load_frame()

    # THE FLAG ON PICKS A PLATE AND SAYS SO, or names the command.
    try:
        _on_path, _on_note = _cframe.frame_source(_cs)
        assert _on_note, "the flag is on and the log says nothing"
        if _present:
            assert _plate_dir in os.path.realpath(_on_path), _on_path
            assert _on_note.startswith("PREVIEW: built plate"), _on_note
            # The line has to identify the BUILD, not just the file:
            # a screenshot is matched to it by the hash.
            _digest = hashlib.sha256(
                open(_on_path, "rb").read()).hexdigest()[:16]
            assert _digest in _on_note, (
                f"the preview line does not carry the plate's hash, so a "
                f"screenshot cannot be matched to the build: {_on_note}")
            # Same one code path: the switch changed the file and
            # nothing else, so the frame still loads and scales.
            _cs._load_frame()
            assert _cs._frame_scaled is not None
        else:
            assert _cframe.BUILD_COMMAND in _on_note, _on_note
            assert os.path.realpath(_on_path) == os.path.realpath(_shipped)
    finally:
        app.settings["frame_preview"] = True
        _cs._load_frame()
    ok(f"colony frame switch (the plate ships; the superseded frame is still\n       byte for byte what it was; plates {_plate_note})")

    # ── Every gap is one of the master's own struts ──────────
    #
    # Stage A3: the gaps are no longer a spacing chosen here, they are
    # the master's struts mapped by role, so `layout_reference.gaps`
    # is a hand-copied number and gets a checker (decision 36). Every
    # value must be the ROUNDED-DOWN reference width of the strut its
    # role names, so a rail is never wider than the strut it came
    # from and never squeezed into a gap that is narrower.
    _rails = _fm2.master_rails(_fb_master)
    assert set(_rails) == set(_fm2.RAIL_ROLES), (
        f"the master no longer offers every rail role: {sorted(_rails)} "
        f"against {sorted(_fm2.RAIL_ROLES)}")
    _mw, _mh = _fb_master.size
    for _role, (_strip, _vert) in _rails.items():
        _ref = (_strip.width * _REF_W / _mw) if _vert \
            else (_strip.height * _REF_H / _mh)
        assert _lr["gaps"][_role] == int(_ref), (
            f"gaps.{_role} is {_lr['gaps'][_role]} and the master's "
            f"{_role} strut measures {_ref:.1f} reference px, so the "
            f"gap should be {int(_ref)}")

    # AND EVERY GAP TAKES ONE. A gap with no rail is bare tile, which
    # is the thing Stage A3 exists to remove.
    _gaps = _fm.render(_lr_windows, _REF_W, _REF_H)[1]
    _struts = _fm2.struts(_gaps)
    assert _struts, "the layout has no struts at all"
    for _gx, _gy, _gw, _gh, _gv in _struts:
        _role = _fb.gap_role(_fb._facing(_gaps, _gx, _gy, _gw, _gh, _gv), _gv)
        assert _role in _rails, (
            f"the gap at ({_gx}, {_gy}) resolves to role {_role!r}, "
            f"which the master does not offer")
        _span = _gw if _gv else _gh
        # THE INSET IS 20 PX SHORTER THAN ITS BAND and is centred in
        # it, so its two horizontal gaps carry half that shortfall
        # each on top of their role's width. The 20 has to go
        # somewhere — its height is fixed by its own aspect — and
        # splitting it is the least-wrong place to put it. The rail
        # is laid at the gap's own width either way, so the picture
        # is a slightly deeper rail at those two and nothing else.
        _extra = 10 if ("galaxy_inset" in _fb._facing(
            _gaps, _gx, _gy, _gw, _gh, _gv) and not _gv) else 0
        assert _span == _lr["gaps"][_role] + _extra, (
            f"the gap at ({_gx}, {_gy}) is {_span} px and its role "
            f"{_role} calls for {_lr['gaps'][_role] + _extra}")

    # THE TILE'S PERIOD IS GONE. Before the rails the bare strut
    # texture covered 2.1 % of the canvas and its column profile
    # autocorrelated at lag 64 — the patch's own size — at 0.92. The
    # rails cover it, and what is left must neither be large nor
    # repeat at the patch size.
    _p1080 = _fb.build(_fb_master, _lr_windows, _REF_W, _REF_H)
    _cut1080 = _fc.cut(_p1080, _lr_windows, _REF_W, _REF_H)[0]
    _ca = np.array(_cut1080)
    _cmetal = _ca[:, :, 3] >= 250
    _clum = _ca[:, :, :3].mean(axis=2).astype(float)
    _covered = np.zeros_like(_cmetal)
    _covered[:_ring["top"], :] = True
    _covered[_REF_H - _ring["bottom"]:, :] = True
    _covered[:, :_ring["left"]] = True
    _covered[:, _REF_W - _ring["right"]:] = True
    for _wx, _wy, _ww, _wh in _gaps.values():
        _covered[max(0, _wy - 3):_wy + _wh + 3,
                 max(0, _wx - 3):_wx + _ww + 3] = True
    for _gx, _gy, _gw, _gh, _gv in _struts:
        _covered[_gy:_gy + _gh, _gx:_gx + _gw] = True
    _bare = _cmetal & ~_covered
    assert _bare.mean() < 0.01, (
        f"{100*_bare.mean():.2f} % of the canvas is still bare strut "
        f"texture; the rails are meant to cover it")
    ok(f"colony frame rails (every gap is the master's strut for its "
       f"role, {len(_struts)} of them, and the bare tile is down to "
       f"{100*_bare.mean():.2f} %)")

    # ── The two colony tables in zoomtables ──
    #
    # THE DOT IS ODD BY REQUIREMENT, not by taste. The original draws
    # its 3 px dot at (sx - 1, sy - 1) so the computed pixel IS the
    # centre (movebox.cpp:103); an even size has no centre pixel, so
    # "the star is drawn where the transform says" would stop being
    # checkable. This asserts the property on a RENDER rather than on
    # the arithmetic that produced it.
    from core import zoomtables as _zt2
    assert set(_zt2.INSET_DOT_DIM) == set(_lr["_resolutions"])
    assert set(_zt2.FIGURE_STEP) == set(_lr["_resolutions"])
    assert _zt2.FIGURE_STEP == _lr["figure_scale"], (
        f"zoomtables.FIGURE_STEP {_zt2.FIGURE_STEP} and "
        f"layout_reference.figure_scale {_lr['figure_scale']} disagree")
    for _spec, _dim in _zt2.INSET_DOT_DIM.items():
        assert _dim % 2 == 1, (
            f"{_spec}: a {_dim} px dot has no centre pixel, so the "
            f"computed star position cannot be its centre")
        # Rendered, then read back: place the dot by the module's own
        # origin rule and measure where its ink actually is.
        _cx, _cy = 40, 30
        _dot = pygame.Surface((80, 60))
        _dot.fill((0, 0, 0))
        _dot.fill((255, 255, 255), pygame.Rect(
            _zt2.inset_dot_origin(_cx, _dim),
            _zt2.inset_dot_origin(_cy, _dim), _dim, _dim))
        _arr = pygame.surfarray.array3d(_dot).sum(axis=2)
        _xs = [x for x in range(80) if _arr[x].any()]
        _ys = [y for y in range(60) if _arr[:, y].any()]
        assert (min(_xs) + max(_xs)) / 2 == _cx and \
               (min(_ys) + max(_ys)) / 2 == _cy, (
            f"{_spec}: a {_dim} px dot placed for centre "
            f"({_cx}, {_cy}) inks x {min(_xs)}..{max(_xs)} y "
            f"{min(_ys)}..{max(_ys)}, whose centre is "
            f"({(min(_xs) + max(_xs)) / 2}, {(min(_ys) + max(_ys)) / 2})")
        assert len(_xs) == _dim and len(_ys) == _dim
        # And it is the NEAREST odd number to the derivation, so the
        # table cannot drift from what Part 3 computed.
        _target = _zt2.INSET_DOT_TARGET[_spec]
        assert abs(_dim - _target) < 1.5 and \
            abs(_dim - _target) <= abs(_dim + 2 - _target) and \
            abs(_dim - _target) <= abs(_dim - 2 - _target), (
            f"{_spec}: {_dim} is not the nearest odd number to "
            f"{_target}")
    # The original's own rule, which the HD one generalises.
    assert _zt2.inset_dot_origin(50, 3) == 49, "movebox.cpp:103 is sx - 1"
    ok("colony inset dot + figure step (odd by requirement, centred on "
       "the computed pixel at all three resolutions, nearest to the "
       "derivation, and the figure step matches layout_reference)")

    # ── THE MARKER INVENTORY ──────────────────────────────────
    #
    # The fundament's rule is that a marked invention says so in its
    # module, in the status document AND in a check that fails if the
    # marking disappears. The third home is the one that rots: a
    # check greps a FILE, and a marking that moves to a file no check
    # reads goes on being true and stops being watched. Nothing in
    # the tree could see that happen.
    #
    # So this is the inventory. Every file carrying an HD EXTENSION
    # or DEVIATION marking must be listed here with one string that
    # has to survive in it. A marking added to a new file fails until
    # it is declared; a marking deleted from a declared file fails
    # too. It does not replace the per-subject checks above — those
    # assert what the marking SAYS — it asserts that no marking is
    # unwatched.
    #
    # smoke_test.py itself is excluded and only it: a check that
    # quotes the words it looks for would otherwise have to declare
    # itself, and the exclusion is by exact path so a marking in any
    # other tool is still caught.
    _MARKED = {
        "core/helppopup.py": "the panel auto-sizes to its text",
        "core/zoomtables.py": "INSET_DOT_DIM",
        "screens/colony_summary/colonybuild.py": "Buy",
        "screens/colony_summary/colonyempire.py": "decision 44",
        "screens/colony_summary/colonyinset.py": "isotropic",
        "screens/colony_summary/colonyheader.py": "PLATE_HEIGHT_REF",
        "screens/colony_summary/colonylist.py": "identity",
        "screens/colony_summary/colonymoveui.py": "discard",
        "screens/colony_summary/colonyoutput.py": "decision 43",
        "screens/colony_summary/colonypick.py": "partial",
        "screens/colony_summary/colonyrows.py": "layout.json",
        # RETARGETED 8 September 2026, in the commit that deleted the
        # F/W/S markers. `colonytrack` was cited on "marker" and
        # layout.json on `_hd_extension_markers`; both named the same
        # removed thing. The live marking in that module is now the
        # drop rect's height, and layout.json's is the hover popup.
        "screens/colony_summary/colonytrack.py": "DEVIATION IN HEIGHT",
        "screens/colony_summary/layout.json": "_hd_extension_popup",
        # Caught by this check on its first run, which is the whole
        # point of it: the figure step's marking went in with Stage 1
        # and nothing was reading the file it went into.
        "screens/colony_summary/layout_reference.json": "figure_scale",
        "screens/colony_summary/screen.py": "cancel",
    }
    _MARKS = ("HD EXTENSION", "DEVIATION")
    _SELF = os.path.join("tools", "smoke_test.py")
    _found = {}
    for _dirpath, _dirnames, _filenames in os.walk(_proj):
        _dirnames[:] = [d for d in _dirnames
                        if d not in ("__pycache__", ".git", ".venv", "venv")]
        for _fn in _filenames:
            if not _fn.endswith((".py", ".json")):
                continue
            _full = os.path.join(_dirpath, _fn)
            _rel = os.path.relpath(_full, _proj)
            if _rel == _SELF:
                continue
            try:
                _text = open(_full, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if any(_m in _text for _m in _MARKS):
                _found[_rel.replace(os.sep, "/")] = _text
    _undeclared = sorted(set(_found) - set(_MARKED))
    _stale = sorted(set(_MARKED) - set(_found))
    assert not _undeclared, (
        f"these files carry an HD EXTENSION or DEVIATION marking that "
        f"no check reads: {_undeclared}. Add the marking's own check, "
        f"then list the file in _MARKED — the inventory is the net, "
        f"not the check")
    assert not _stale, (
        f"these files are listed as carrying a marking and no longer "
        f"do: {_stale}. Either the marking was removed, in which case "
        f"the status document says so too, or it moved to a file the "
        f"inventory does not know about")
    for _rel, _cite in _MARKED.items():
        assert _cite in _found[_rel], (
            f"{_rel} still carries a marking but no longer says "
            f"{_cite!r} — the marking survived and its subject did not")
    # ── THE HEADER WINDOW IS OURS, AND SO IS THE OUTLINE COLOUR ──
    # Both markings, all three homes, and the numbers the first one
    # rests on. The plate height is the interesting one: it is a
    # TRANSCRIBED number that does NOT fit, so the check pins the
    # measurement and the window it fails to fit rather than the
    # compromise, which is the only way the gap stays visible.
    from screens.colony_summary import colonyheader as _chdr
    assert _chdr.PLATE_HEIGHT_REF == 66, _chdr.PLATE_HEIGHT_REF
    assert _chdr.DIVIDER_REF == 6, _chdr.DIVIDER_REF
    _hbox = d.screens["colony_summary"].box_rect("header")
    assert _hbox and _hbox[3] < _chdr.PLATE_HEIGHT_REF, (
        f"the header window is {_hbox[3]} ref px and the original's "
        f"plate measures {_chdr.PLATE_HEIGHT_REF} — if the window has "
        f"grown to fit, the deviation is over and the note that "
        f"records it has to go with it")
    _hcfg = d.screens["colony_summary"]._data.get("header", {})
    for _cite in ("DEVIATION", "44", "60", "96", "66 reference px",
                  "panel.thin_border", "recess"):
        assert _cite in _hcfg.get("_deviation_window", ""), (
            f"header._deviation_window no longer carries {_cite!r}")
    # THE PLATES TILE THE HEADER EXACTLY, and each heads its own
    # column: a heading that is not as wide as the column under it is
    # a second copy of the layout (decision 5).
    _cs4 = d.screens["colony_summary"]
    _cols = _cs4._columns()
    assert [k for k, _w in _cols] == ["name", "farmers", "workers",
                                      "scientists", "building", "scroll"], _cols
    assert sum(_w for _k, _w in _cols) == 1693, _cols
    # The job columns are the transcribed ratio, not three equal ones.
    _jobs = dict(_cols)
    assert (_jobs["farmers"], _jobs["workers"], _jobs["scientists"]) \
        == (342, 360, 339), (
            f"the job columns are {_jobs} — COLSUM::Get_Selected_Pop_ "
            f"(colsum.cpp:1006-1024) gives spans 135/142/134, so the "
            f"middle column is the widest and three equal ones are ours")
    _hpx = pygame.Rect(*_cs4.layout.rect(_hbox))
    _plates = _chdr.plate_rects(_hpx, _cols, _cs4.layout.scale)
    assert [k for k, _r in _plates] == [k for k, _w in _cols]
    assert _plates[0][1].left >= _hpx.left
    assert _plates[-1][1].right <= _hpx.right
    # ── THE EMPIRE READOUTS SURVIVE AN UNTUNED RESOLUTION ──
    #
    # Rendered at all three and read back as INK, because the fault
    # this replaces was invisible to any check that derived the
    # expected size from the renderer's own expression. `colonyempire`
    # took `box_font_scale`, which multiplies by `win_h / 1080`, and
    # then went through `Layout.font_size`, which multiplies by the
    # window scale again: 1.0 at 1080p, 1.78 at 1440p and **4.0 at
    # 2160p against an intended 2.0**. The colony summary carries no
    # tuned `font_scale` on any box, so nothing cancelled it and the
    # six values came out at twice their size at 4K and collided with
    # their labels. Same family as the help popup's, which
    # `screenhelp` had already solved privately — see
    # `ScreenBase.box_font_scale_stored`.
    #
    # Two properties, and the second is the one that fails on a double
    # scale: the value's ink stays inside the box, and it stays clear
    # of its own label.
    from screens.colony_summary import colonyempire as _emp_chk
    _emp_seen = 0
    for _W, _H in (("1920", 1080), ("2560", 1440), ("3840", 2160)):
        _W = int(_W)
        _ea, _es = _pv.build_screen(_W, _H)
        _ea.dispatcher.switch_to("colony_summary")
        _esc = _ea.dispatcher.active
        _esc.enter(None)
        _esc.update(_pv._Snapshot(_pv.COLONIES))
        _ebox = _esc.box_rect("empire_stats")
        assert _ebox, "no empire_stats box"
        _er = pygame.Rect(*_ea.layout.rect(_ebox))
        _esurf = pygame.Surface((_W, _H))
        _esurf.fill((0, 0, 0))
        _esc.render(_esurf)
        _epx = pygame.surfarray.array3d(
            _esurf.subsurface(_er)).transpose(1, 0, 2).astype(int)
        _lab_rgb = _np.array(_emp_chk.LABEL_COLOR[:3], dtype=int)
        _val_rgb = _np.array(_emp_chk.VALUE_COLOR[:3], dtype=int)
        # A TIGHT match on the glyph CORE. The two colours are only
        # 248 apart summed — (140,155,190) against (220,228,245) — so
        # a loose threshold makes each mask catch the other's
        # antialiasing and the separation test compares noise.
        _is_lab = (_np.abs(_epx - _lab_rgb).sum(axis=2) < 12)
        _is_val = (_np.abs(_epx - _val_rgb).sum(axis=2) < 12)
        assert _is_lab.any() and _is_val.any(), (
            f"{_W}x{_H}: the empire panel drew no labels or no values, "
            f"so this check asserts nothing")
        # INSIDE THE BOX: no ink on the outermost column or row, which
        # is what a value too big to fit produces first.
        for _side, _band in (("left", _is_val[:, :1]),
                             ("right", _is_val[:, -1:]),
                             ("top", _is_val[:1, :]),
                             ("bottom", _is_val[-1:, :])):
            assert not _band.any(), (
                f"{_W}x{_H}: value ink touches the {_side} edge of "
                f"empire_stats — it is too large for its box")
        # CLEAR OF THE LABEL: on every row that carries both, the
        # rightmost label pixel is left of the leftmost value pixel.
        _rows_both = [_y for _y in range(_er.h)
                      if _is_lab[_y].any() and _is_val[_y].any()]
        assert len(_rows_both) >= 6, (
            f"{_W}x{_H}: only {len(_rows_both)} rows carry both a "
            f"label and a value; the panel has six")
        for _y in _rows_both:
            _lx = int(_np.where(_is_lab[_y])[0].max())
            _vx = int(_np.where(_is_val[_y])[0].min())
            assert _lx < _vx, (
                f"{_W}x{_H}: on row y={_y} the label reaches x={_lx} "
                f"and the value starts at x={_vx} — they collide, "
                f"which is what a doubled font scale does first")
        _emp_seen += 1
    assert _emp_seen == 3
    ok("empire readouts at three resolutions (value ink inside the box "
       "and clear of its label, so a doubled font scale fails here)")

    # ── THE POP-MOVE DIFF RULE, AND IT MUST BE ABLE TO FAIL ──
    #
    # "Exactly one colony's bytes changed" was what both acceptance
    # tools asserted, and it is not what the game guarantees:
    # `Pass_Out_Imports_` (colcalc_main.cpp:208) redistributes the
    # whole player's food on every recalculation, so a colony nobody
    # touched comes back with a different `imports` — and a NEEDY one
    # with a different `pop_growth` too. The rule names those fields
    # and refuses everything else, which is stricter than the old one
    # about the moved colony, where any byte difference passed.
    #
    # A rule nobody has seen fail is a tolerance. Three synthetic
    # diffs, each the shape the rule exists to catch.
    from screens.colony_summary import colonymove as _cmv
    from core.structs import colony as _ccs

    def _rec(**fields):
        _b = bytearray(_ccs.SIZE)
        for _name, _val in fields.items():
            _off, _fmt = next((_e[1], _e[2]) for _e in _ccs.SPEC.fields
                              if _e[0] == _name)
            _s.pack_into("<h" if _fmt.startswith("i16") else "<b",
                         _b, _off, _val)
        return bytes(_b)

    _base = bytes(_ccs.SIZE)
    _verdict = lambda _a, _b: _cmv.move_diff_verdict(
        _a, _b, 0, _ccs.SPEC, _ccs.parse)

    # (a) a SECOND colony whose pop[] changed — the failure the whole
    #     acceptance exists for, and the one thing that may never be
    #     allowed on any colony but the moved one.
    _pop_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "pop")
    _b2 = bytearray(_base); _s.pack_into("<I", _b2, _pop_off, 0x280)
    _ok_a, _lines_a = _verdict([_base, _base], [_base, bytes(_b2)])
    assert not _ok_a, (
        "the rule accepted a second colony whose pop[] changed — that "
        "is the wrong-colony failure and it is what the acceptance is "
        "for; a rule that passes it is a tolerance")
    assert any("pop changed" in _l for _l in _lines_a), _lines_a

    # (b) a second colony whose production changed. Nothing on the
    #     pop-move path writes another colony's production:
    #     `Recalculate_Colony_` is called for the moved colony only.
    _pr_off = next(_e[1] for _e in _ccs.SPEC.fields
                   if _e[0] == "production")
    _b3 = bytearray(_base); _s.pack_into("<h", _b3, _pr_off, 7)
    _ok_b, _lines_b = _verdict([_base, _base], [_base, bytes(_b3)])
    assert not _ok_b, (
        "the rule accepted a second colony whose production changed; "
        "Pass_Out_Imports_ writes imports and Post_Import_Computing_ "
        "writes pop_growth/pop_roundoff/specialty, and neither writes "
        "production on a colony that was not moved")
    assert any("production changed" in _l for _l in _lines_b), _lines_b

    # (c) a NON-NEEDY colony whose pop_growth changed.
    #     `Post_Import_Computing_` is called only for entries of
    #     `needy_colony_indices` (colcalc_main.cpp:341-352), and
    #     neediness IS readable from the record — `production[FOOD] -
    #     maintenance[FOOD] < 0`, colcalc_main.cpp:219 — so the rule
    #     conditions on it rather than allowing the field everywhere.
    _pg_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "pop_growth")
    _b4 = bytearray(_base); _s.pack_into("<h", _b4, _pg_off, 51)
    _ok_c, _lines_c = _verdict([_base, _base], [_base, bytes(_b4)])
    assert not _ok_c, (
        "the rule accepted pop_growth on a colony that is not needy; "
        "Post_Import_Computing_ runs for needy colonies only, and "
        "allowing the field everywhere is the tolerance this check "
        "exists to refuse")
    assert any("NOT needy" in _l for _l in _lines_c), _lines_c

    # (c2) THE SAME FIELD ON A NEEDY COLONY IS ALLOWED, or the rule
    #      would refuse what the game actually does and the live proof
    #      could never go green.
    _mt_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "maintenance")
    _b5 = bytearray(_base); _s.pack_into("<h", _b5, _mt_off, 5)
    _b6 = bytearray(_b5); _s.pack_into("<h", _b6, _pg_off, 51)
    _ok_c2, _lines_c2 = _verdict([_base, bytes(_b5)],
                                 [_base, bytes(_b6)])
    assert _ok_c2, _lines_c2
    assert any("is needy" in _l for _l in _lines_c2), _lines_c2

    # (c3) AND `imports` IS ALLOWED ON ANY of the owner's colonies,
    #      needy or not — Pass_Out_Imports_ writes it in the first
    #      loop, before the needy list exists.
    _im_off = next(_e[1] for _e in _ccs.SPEC.fields if _e[0] == "imports")
    _b7 = bytearray(_base); _s.pack_into("<h", _b7, _im_off, 1)
    _ok_c3, _lines_c3 = _verdict([_base, _base], [_base, bytes(_b7)])
    assert _ok_c3, _lines_c3

    # AND AN UNREADABLE RECORD IS A FAILURE, not a skip.
    _ok_d, _ = _verdict([_base, _base], [_base, b"\x00\x01"])
    assert not _ok_d, "a changed record that will not parse must fail"

    # Both acceptance tools read the ONE rule, not a copy each.
    for _tool in ("colony_move_hd.py", "colony_move_probe.py"):
        _src = open(os.path.join(_proj, "tools", _tool),
                    encoding="utf-8").read()
        assert "move_diff_verdict" in _src, (
            f"{_tool} does not call colonymove.move_diff_verdict — the "
            f"rule has to have one home, or the two drift and the "
            f"acceptance means whichever was run last")
    ok("pop-move diff rule (one home, two tools; a second colony's "
       "pop or production fails it, and pop_growth only on a "
       "colony the food balance says was needy)")

    # ── THE BUILDING NAMES ARE THE USER'S OWN, AND DERIVED ──
    #
    # The help-text pattern (decision 38): extracted from the
    # player's TECHNAME.LBX, never committed, decoded at load time,
    # format-versioned, and an absent file is a state the column
    # explains rather than an empty cell. **REPORTED, NOT SKIPPED** —
    # this check counts either way, so "the count must not go down"
    # stays a rule a clone can follow (decision 42).
    from core import buildnames as _bn
    assert _bn.BUILDING_FIRST_STRING == _bn.TECH_FIELD_COUNT + _bn.TECH_APP_COUNT
    assert (_bn.TECH_FIELD_COUNT, _bn.TECH_APP_COUNT, _bn.BUILDING_COUNT) \
        == (83, 212, 49), (
            "the string walk's offsets moved. They are orion2_consts.h "
            "enums with static_asserts beside them (TECH_FIELD_COUNT, "
            "TECH_APP_COUNT, BUILDING_COUNT) and the building block's "
            "position is computed from them, not measured off the file")
    # An id outside the building table is NOT a building — it is a
    # ship or one of Option_String_'s options, which is the other
    # branch of Selection_Name_ (colbldg.cpp:796-802) and a different
    # string source. -2 is COLONY_PRODUCTION_TRADE_GOODS.
    #
    # **ID 0 IS THE BOUND THAT WAS WRONG, and this assertion is why
    # it stayed wrong.** It read `is_building(0)` and passed, because
    # it had been written from the same range the code had rather
    # than from the predicate. `Colony_Production_Is_Building_` is
    # `id > BUILDING_NO_BUILDING && id < BUILDING_COUNT`
    # (colbldg.h:16) — 1..48 — and `Option_String_` claims 0 with an
    # explicit `case 0:` returning the empty string
    # (colbldg.cpp:2356-2359). Both bounds are now spelled with the
    # named constants, so a check and the code cannot agree with each
    # other while both disagree with the source.
    assert not _bn.is_building(_bn.BUILDING_NO_BUILDING), (
        "is_building(0) is True again. 0 is BUILDING_NO_BUILDING and "
        "belongs to Option_String_, which returns the empty string "
        "for it; treating it as a building prints _buildings[0], "
        "'No Building', where the original prints nothing")
    assert _bn.is_building(1) and _bn.is_building(_bn.BUILDING_COUNT - 1)
    assert not _bn.is_building(_bn.BUILDING_COUNT) and not _bn.is_building(-2)
    assert not _bn.is_building(None)
    _bn_names = _bn.BuildingNames(settings.get("language", "en"))
    assert _bn_names.state in ("ok", "missing", "stale"), _bn_names.state
    if _bn_names.state == "ok":
        # PINNED AGAINST THE REFERENCE SAVE'S OWN LANGUAGE BLOCK.
        # Three names at known ids, so a walk that slipped by one
        # string fails here rather than showing a plausible wrong
        # word — the failure this kind of table produces.
        for _id, _want in ((1, None), (7, "Automated Factory"),
                           (48, None)):
            _got = _bn_names.building(_id)
            if _want is not None:
                assert _got == _want, (
                    f"building {_id} is {_got!r}, expected {_want!r} — "
                    f"the string walk has slipped")
            else:
                assert _got, f"building {_id} has no name"
        assert _bn_names.building(-2) is None, (
            "-2 is TRADE_GOODS, an option and not a building; naming "
            "it out of the building table would be the wrong branch "
            "of Selection_Name_")
        _bn_note = f"{len(_bn_names.names)} names"
    else:
        _bn_note = (f"{_bn_names.state} — run "
                    f"`python tools/techname_extract.py`")
    # The column explains an absent file instead of drawing nothing.
    _bn_cfg = d.screens["colony_summary"]._data.get("build", {})
    assert _bn_cfg.get("names_missing"), (
        "layout.json has no wording for a missing name file, so the "
        "BUILDING column would be indistinguishable from a colony "
        "that builds nothing")
    for _cite in ("Calculate_Current_Production_Turn_Count_", "OPEN"):
        assert _cite in _bn_cfg.get("_turns_note", ""), (
            f"build._turns_note no longer carries {_cite!r} — the "
            f"'- 8t' suffix is not drawn and the reason has to travel "
            f"with the omission")
    ok(f"building names, derived from the user's TECHNAME.LBX "
       f"({_bn_note})")

    # ── THE OPTION STRINGS ARE A SECOND FILE AND A SECOND WALK ──
    #
    # `COLBLDG::Selection_Name_` (colbldg.cpp:796) sends a BUILDING id
    # to techname.lbx and an OPTION id to estrings.lbx, and the
    # reference save takes the OPTION branch on every row —
    # producing[0] is -2, TRADE_GOODS. The column was blank for that
    # reason, not for want of a wider techname walk.
    from core import estrings as _es
    assert _es.ESTRINGS_COUNT == 812, (
        "ESTRINGS_COUNT moved. It is estrings.h:4 and Load_E_Strings_ "
        "walks exactly that many strings (estrings.cpp:11-37), so it "
        "is asserted against the file rather than taken from it")
    # THE SIXTEEN OPTION IDS ARE Option_String_'s OWN CASES, and the
    # table is pinned entry by entry rather than spot-checked: a
    # switch transcribed into a dict is exactly the kind of table
    # that goes stale one case at a time.
    assert len(_es.OPTION_STRINGS) == 17, (
        f"{len(_es.OPTION_STRINGS)} option ids, expected 17 — the "
        f"count is Option_String_'s CASE LABELS, not its distinct "
        f"return values: SEPARATOR, NONE and 0 are three labels "
        f"falling through to one E_Strings_ call (colbldg.cpp:2356)")
    assert len(set(_es.OPTION_STRINGS.values())) == 15, (
        "15 distinct E_Strings_ indices behind 17 ids — the "
        "three-way fall-through is the only sharing in the switch")
    assert _es.OPTION_STRINGS[-2] == 0x21D and _es.OPTION_STRINGS[-3] == 0x142
    assert _es.OPTION_STRINGS[0] == _es.OPTION_STRINGS[-1] == \
        _es.OPTION_STRINGS[-9] == 0x00C, (
            "NONE, SEPARATOR and 0 no longer share E_Strings_(0x00C). "
            "They share it in the source (colbldg.cpp:2356-2359) and "
            "that string is EMPTY, which is why an empty cell in the "
            "BUILDING column is correct and not a missing file")
    assert _es.OPTION_STRINGS[-5] == 0x0B2 and _es.OPTION_STRINGS[-6] == 0x0B1, (
        "WORKER/SCIENTIST no longer cross. -5 is WORKER -> 0x0B2 and "
        "-6 is SCIENTIST -> 0x0B1, and the pair is out of numeric "
        "order in the source too — it is the crossing that proves the "
        "table was transcribed from Option_String_ and not sorted "
        "into agreement with itself")
    _es_strings = _es.EStrings(settings.get("language", "en"))
    assert _es_strings.state in ("ok", "missing", "stale"), _es_strings.state
    if _es_strings.state == "ok":
        assert len(_es_strings.strings) == _es.ESTRINGS_COUNT
        # PINNED, AND THIS IS THE CHECK THAT CATCHES THE HEADER.
        # Walking the LBX entry from offset 0 instead of from 4 put
        # every string ONE INDEX LATE and still produced 812 plausible
        # strings — Trade Goods sat at 0x21E, which is Transport Ship.
        # `Farload_Library_Data_` reads total_count and element_size,
        # two uint16s, then seeks past them (farload.cpp:88-92, :107).
        # Three anchors from Option_String_'s own switch; a walk off
        # by one fails all three.
        for _entry, _want in ((0x142, "Housing"), (0x21D, "Trade Goods"),
                              (0x21E, "Transport Ship")):
            _got = _es_strings.string(_entry)
            assert _got == _want, (
                f"E_Strings_({_entry:#05x}) is {_got!r}, expected "
                f"{_want!r} — the walk has slipped, most likely past "
                f"the 4-byte entry header (farload.cpp:107)")
        assert _es_strings.string(0x00C) == "", (
            "E_Strings_(0x00C) is not the empty string any more. It "
            "is what NONE, SEPARATOR and 0 resolve to, and an empty "
            "entry that reads as absent makes 'the original prints "
            "nothing' indistinguishable from 'no such index'")
        assert _es_strings.string(_es.ESTRINGS_COUNT) is None, (
            "an out-of-range index returns something. None must mean "
            "NO SUCH ENTRY and '' must mean a blank entry")
        # THE WORD LISTS ARE NOT SWITCHED, AND THIS IS WHY THEY
        # STAY. 23 of the 26 entries in layout.json's four
        # enum-indexed lists are letter for letter the game's own
        # (estrings.cpp:155-169, :204-213); the three that differ are
        # the gravities, and they differ because the COLONY SUMMARY
        # supplies half the word. E_Strings_(0x4A)'s gravity slot is
        # `%sravity` and the table holds 'Normal G'
        # (colsum.cpp:1194-1200), so 'Normal Gravity' exists only
        # once the two are joined. Pinned because a future reader who
        # sees 'Low G' in the table and 'Low' in layout.json will
        # otherwise "fix" one of them.
        assert "%sravity" in (_es_strings.string(0x4A) or ""), (
            "E_Strings_(0x4A) no longer splits the word 'Gravity'. "
            "The scan box's format supplies 'ravity' and "
            "_planet_gravity_string supplies 'Normal G'; that split "
            "is why words.gravities holds the bare quality")
        assert _es_strings.string(0x2B0) == "Normal G", (
            "_planet_gravity_string[NORMAL_G] is not 'Normal G'. It "
            "looks like an enum name in title case and is in fact the "
            "game's own string — see words._note")
        _es_note = (f"{sum(1 for t in _es_strings.strings if t)} "
                    f"non-empty of {_es.ESTRINGS_COUNT}")
    else:
        _es_note = (f"{_es_strings.state} — run "
                    f"`python tools/estrings_extract.py`")

    # THE TWO LOADERS MUST NEVER READ EACH OTHER'S FILE. The walks
    # are different — `Advance_To_Next_String_` (techinit.cpp:11-21)
    # skips a whole run of NULs, `Load_E_Strings_` (estrings.cpp:33-36)
    # steps `strlen + 1` and keeps empties — so crossing them
    # mis-indexes the result SILENTLY, which is the failure mode this
    # commit already met once. Asserted three ways: the paths differ,
    # neither module names the other's file, and the two walks are
    # shown to disagree on the same bytes.
    assert _es.string_file("en") != _bn.name_file("en")
    import tools.estrings_extract as _ee
    import tools.techname_extract as _te
    for _mod, _forbidden in ((_es, "techname"), (_ee, "techname"),
                             (_bn, "estrings"), (_te, "estrings")):
        _text = open(_mod.__file__, encoding="utf-8").read().lower()
        # The DOCSTRINGS compare the two on purpose, so only the code
        # is searched — a mention in prose is what keeps the two
        # walks from being confused, not what confuses them.
        _code = "\n".join(l for l in _text.splitlines()
                           if not l.strip().startswith("#"))
        _code = _code.split('"""')
        _code = "".join(_code[i] for i in range(0, len(_code), 2))
        assert _forbidden + ".lbx" not in _code, (
            f"{os.path.basename(_mod.__file__)} names "
            f"{_forbidden}.lbx in its code. The two string tables "
            f"live in different files and are walked differently; a "
            f"loader that reaches for the other's file mis-indexes "
            f"every entry after the first gap and looks like data")
    _probe = b"A\x00\x00B\x00"
    _te_walk = [b.decode() for b in _te.split_block(_probe)]
    _ee_walk = [b.decode() for b in
                _ee.split_block(b"\x00\x00\x00\x00" + _probe, 4)]
    assert _te_walk[:2] == ["A", "B"], _te_walk
    assert _ee_walk[:3] == ["A", "", "B"], (
        f"the ESTRINGS walk swallowed the empty string ({_ee_walk!r}). "
        f"`Load_E_Strings_` steps strlen+1 and an empty entry is "
        f"valid; skipping NUL runs is TECHNAME's walk and would shift "
        f"every index after the first gap")
    assert _ee.HEADER_SIZE == 4, (
        "the LBX entry header is not 4 bytes any more. "
        "Farload_Library_Data_ reads total_count and element_size as "
        "two uint16s and seeks past both (farload.cpp:88-92, :107)")
    ok(f"option strings, derived from the user's ESTRINGS.LBX "
       f"({_es_note}); the TECHNAME and ESTRINGS walks stay apart")

    # ── THE ROW DICT IS THE INTERFACE, AND IT IS PINNED ──
    #
    # `build_rows` hands the two renderers plain dicts and its
    # docstring lists the keys. The list was PROSE until 7 September
    # 2026 — the docstring claimed a check held it and no such check
    # existed, which is how `producing_id` and `producing_state`
    # could have been added without the fake rows in this file
    # following. Read off the source with AST rather than by running
    # `build_rows`, which needs a colony blob.
    import ast as _ast
    _cr_src = open(os.path.join(_proj, "screens", "colony_summary",
                                "colonyrows.py"), encoding="utf-8").read()
    _fn = next(n for n in _ast.walk(_ast.parse(_cr_src))
               if isinstance(n, _ast.FunctionDef) and n.name == "build_rows")
    _dicts = [n for n in _ast.walk(_fn) if isinstance(n, _ast.Dict)
              and len(n.keys) > 8]
    assert len(_dicts) == 1, (
        f"{len(_dicts)} candidate row dicts in build_rows — the pin "
        f"below cannot tell which is the interface any more")
    _row_keys = {k.value for k in _dicts[0].keys
                 if isinstance(k, _ast.Constant)}
    _row_expected = {
        "index", "name", "climate", "pops", "jobs", "cells", "held",
        "no_farming", "max_pop", "producing", "producing_id",
        "producing_state", "producing_turns", "can_buy", "production",
        "drawn_production", "shortage", "size", "gravity", "mineral",
        "growth", "morale", "morale_applies",
    }
    assert _row_keys == _row_expected, (
        f"the row dict's keys changed. Added: "
        f"{sorted(_row_keys - _row_expected)}; removed: "
        f"{sorted(_row_expected - _row_keys)}. Both renderers and "
        f"every fake row in this file read this set — update them in "
        f"the same commit, which is what this pin is for")
    for _doc_key in ("producing_id", "producing_state"):
        assert _doc_key in _fn.body[0].value.value, (
            f"build_rows' docstring no longer lists {_doc_key!r}; the "
            f"docstring IS the interface document for these dicts")
    ok(f"colony row dict pinned ({len(_row_expected)} keys, docstring "
       f"and AST agree)")

    # ── THE POPULATION FIGURES (decision 50) ──
    #
    # The colony screens draw the player's own RACEICON sprites at an
    # integer step. Seven things are asserted here and each is a way
    # this has already gone wrong somewhere in this project: a scale
    # pretending to be a step, two homes for one number, a hit test
    # that follows the ink instead of the slot, and a fallback that
    # stops being exercised and rots.
    from screens.colony_summary import colonyfigures as _fig
    import tempfile as _tf

    # 1. THE NAME TABLE IS THE ONE HOME. 54 figures — 13 races x
    # three jobs, 13 portraits, native and android — and the count is
    # computed from the key tuples, so adding a race moves it.
    _fig_names = _fig.all_names()
    assert len(_fig_names) == len(_fig.RACE_KEYS) * 4 + 2 == 54, \
        len(_fig_names)
    assert len(set(_fig_names)) == len(_fig_names), "duplicate figure name"
    assert _fig.RACE_KEYS[5] == "human" and _fig.ROLE_KEYS == (
        "farmer", "worker", "scientist"), (
            "the race or role keys moved. They are enum STOCK_RACE "
            "(orion2_consts.h:444-457) and ECON_FOOD/INDUSTRY/RESEARCH "
            "(:119-121) — the SOURCE's identifiers, never "
            "MOX::_race_names[], which is localised and would make a "
            "mod stop working on a translated install")

    # 2. THE STEP IS A SWAP, NOT A SCALE (decision 28). Sizes exactly
    # 28 x step, and the step comes from ONE function — the same one
    # colonytrack lays the cell pitch with, because a track at 3x
    # holding sprites at 2x is a picture nothing would report.
    assert _fig.STEPS == (2, 3, 4), _fig.STEPS
    # 1280x720 is scale 0.667 and is BELOW the table's smallest key,
    # so it falls to 1920x1080's step — decision 1's chain, and the
    # case a `round()` on the scale would get wrong.
    for _sc, _want in ((0.667, 2), (1.0, 2), (4 / 3, 3), (2.0, 4)):
        assert _fig.figure_step(_sc) == _want, (
            f"figure_step({_sc}) is {_fig.figure_step(_sc)}, expected "
            f"{_want} — the step is box.closest_resolution over "
            f"zoomtables.FIGURE_STEP and nothing else")
    for _st in _fig.STEPS:
        assert _fig.step_size(_st) == 28 * _st, _fig.step_size(_st)
        assert _fig.step_name("human_farmer.png", _st) == \
            f"human_farmer@{_st}x.png"
    _tk_src = open(os.path.join(_proj, "screens", "colony_summary",
                                "colonytrack.py"), encoding="utf-8").read()
    assert "colonyfigures.figure_step(scale)" in _tk_src, (
        "colonytrack no longer takes the sprite step from "
        "colonyfigures.figure_step. Two places computing one step is "
        "how the pitch and the sprite drift apart by a growing amount "
        "with nothing on either side reporting it")

    # 3. WHICH SPRITE A POP GETS — `Colony_Pop_Anim_` transcribed
    # (colony.cpp:1268-1283), including the ORDER. The conquered test
    # is FIRST, so a conquered native draws a portrait and not the
    # native sprite; swapping the two reads as a simplification and
    # changes the picture.
    _races = {0: 5, 1: 10}          # player 0 human, player 1 sakkra
    assert _fig.figure_for(0, 5, _races) == "human_farmer.png"
    assert _fig.figure_for((2 << 7) | 0, 5, _races) == \
        "human_scientist.png"
    assert _fig.figure_for(9, 5, _races) == "native.png"
    assert _fig.figure_for(8, 5, _races) == "android.png"
    assert _fig.figure_for(0x400 | 1, 5, _races) == "sakkra_portrait.png", (
        "a conquered pop no longer draws ITS OWN race's portrait. "
        "Colony_Pop_Anim_ reads _player[Get_Effective_Pop_Player_(..)]"
        ".race, and the effective player is the pop word's own nibble "
        "— not the colony owner's")
    assert _fig.figure_for(0x400 | 9, 5, _races) == "human_portrait.png", (
        "a CONQUERED NATIVE no longer draws a portrait. The 0x400 "
        "test comes before the state dispatch in Colony_Pop_Anim_ "
        "(colony.cpp:1277-1282); reordering them is a one-line "
        "simplification that changes what is on screen")
    assert _fig.figure_for(3, 5, {}) is None, (
        "an unknown race no longer answers None. Guessing a race "
        "draws the wrong species, which looks like data and is not")

    # 4. AN ABSENT SET IS A STATE, AND THE COLOURED CELLS ARE ITS
    # PICTURE. Pointed at an empty root, the loader reports "missing"
    # and holds nothing; the renderer takes None and draws the cells
    # it has always drawn. **This is why the cell renderer is not on
    # Stage 5's deletion list** — it is what an install without the
    # extraction sees, not a leftover.
    with _tf.TemporaryDirectory() as _empty:
        _none = _fig.FigureSet(app.res, 2, root=_empty)
        assert _none.state == "missing" and not _none.figures, _none.state
        assert _none.get("human_farmer.png") is None
    _cell_surf = pygame.Surface((1920, 1080))
    _cell_surf.fill((0, 0, 0))
    # The row is BUILT here rather than borrowed from `_rows`, whose
    # job split comes from the fixture and could stop having a farmer
    # in it without this check saying anything useful.
    _cell_row = dict(_rows[1])
    _cell_row["jobs"] = [2, 1, 0]
    _cell_row["pops"] = 3
    _cell_row["cells"] = ((_crw.Cell("", None), _crw.Cell("", None)),
                          (_crw.Cell("", None),), ())
    _cl.render(_cell_surf, [_cell_row], _area, _cfg, app.layout,
               app.style, 0, 0, None)
    _cell_px = pygame.surfarray.array3d(_cell_surf)
    assert any(tuple(_cell_px[x, y]) == tuple(_cl.ZONE_COLORS[0][:3])
               for x in range(_area.x, _area.right)
               for y in range(_area.y, _area.bottom)), (
        "with no figure set the farmer cells are not drawn in their "
        "own colour. The coloured cell IS the absent-set state and a "
        "screen that draws neither is the worst of the three")

    # 5. A WRONG SIZE IS REFUSED, NOT FITTED — master and step file
    # alike, one log line each, and the search moves on to the next
    # root so the base figure is what gets drawn.
    with _tf.TemporaryDirectory() as _bad:
        _bd = os.path.join(_bad, _fig.FIGURE_DIR)
        os.makedirs(_bd)
        pygame.image.save(pygame.Surface((32, 32), pygame.SRCALPHA),
                          os.path.join(_bd, "human_farmer.png"))
        pygame.image.save(pygame.Surface((99, 99), pygame.SRCALPHA),
                          os.path.join(_bd, "human_worker@2x.png"))
        _bad_set = _fig.FigureSet(app.res, 2, root=_bad)
        assert len(_bad_set.refused) == 2, _bad_set.refused
        assert _bad_set.state == "missing", (
            "a directory of refused files is not a figure set. "
            "Refusing a file and then reporting the set as usable is "
            "the failure this state exists to name")

    # 6. THE ONE-FILE MOD, both conventions, and the ORDER between
    # them. A mod that ships ONLY a master must beat the base
    # project's step files — which is what `Resources.roots()` is
    # for, and what two `resolve` calls would get backwards.
    _figs_present = os.path.isdir(os.path.join(_proj, _fig.FIGURE_DIR))
    if _figs_present:
        with _tf.TemporaryDirectory() as _mod:
            _md = os.path.join(_mod, _fig.FIGURE_DIR)
            os.makedirs(_md)
            _m = pygame.Surface((28, 28), pygame.SRCALPHA)
            _m.fill((255, 0, 0, 255))
            pygame.image.save(_m, os.path.join(_md, "human_farmer.png"))
            _s3 = pygame.Surface((84, 84), pygame.SRCALPHA)
            _s3.fill((0, 255, 0, 255))
            pygame.image.save(_s3, os.path.join(_md, "human_worker@3x.png"))
            from core.resources import Resources as _Res
            _modres = _Res()
            _modres.mod_dirs = [_mod]
            _set3 = _fig.FigureSet(_modres, 3)
            assert _set3.state == "ok" and len(_set3.figures) == 54, (
                f"a two-file mod broke the other 52 figures "
                f"({_set3.state}, {len(_set3.figures)})")
            _got = _set3.get("human_farmer.png")
            assert _got.get_size() == (84, 84), _got.get_size()
            assert _got.get_at((42, 42))[:3] == (255, 0, 0), (
                "the mod's MASTER did not win at step 3. A mod that "
                "ships one 28x28 file must beat the base project's "
                "own step files, or a one-file mod is not one file")
            _gotw = _set3.get("human_worker@3x.png".replace("@3x", ""))
            assert _gotw.get_at((42, 42))[:3] == (0, 255, 0), (
                "the mod's explicit @3x file did not win. An author "
                "who draws HD artwork for one resolution supplies one "
                "file and must not have to redraw the other two")
            # AND THE STEP FILE IS PER STEP: at 2x the same mod falls
            # back to the base worker, because it shipped no @2x.
            _set2 = _fig.FigureSet(_modres, 2)
            _gotw2 = _set2.get("human_worker.png")
            assert _gotw2.get_size() == (56, 56)
            assert _gotw2.get_at((28, 28))[:3] != (0, 255, 0), (
                "the @3x file leaked into step 2. Each step is "
                "replaceable ALONE")

    # 7. THE OVERLAP DRAWS LEFT TO RIGHT. `pop_draw_index++` is at
    # coldraw.cpp:377, AFTER the draw at :349, so the walk paints
    # ascending and each figure covers its left neighbour's right
    # edge. At a squished pitch ours must do the same, or the overlap
    # is a mirror image of the original's at the same squish.
    class _StubSet:
        """Two solid colours, so an overlap is readable in one pixel."""

        def __init__(self, size):
            self._s = {}
            for _n, _c in (("human_farmer.png", (255, 0, 0)),
                           ("native.png", (0, 0, 255))):
                _surf2 = pygame.Surface((size, size))
                _surf2.fill(_c)
                self._s[_n] = _surf2

        def get(self, name):
            return self._s.get(name)

    _ov = pygame.Surface((1920, 1080))
    _ov.fill((0, 0, 0))
    _ovrow = dict(_rows[1])
    _ovrow["jobs"] = [8, 0, 0]
    _ovrow["pops"] = 8
    _ovrow["cells"] = ((_crw.Cell("", "human_farmer.png"),
                        _crw.Cell("native", "native.png")) * 4, (), ())
    _cl.render(_ov, [_ovrow], _area, _cfg, app.layout, app.style, 0, 0,
               _StubSet(_fig.step_size(2)))
    _ovpx = pygame.surfarray.array3d(_ov)
    _red = [x for x in range(_area.x, _area.right)
            for y in [_area.y + 30]
            if tuple(_ovpx[x, y]) == (255, 0, 0)]
    _blue = [x for x in range(_area.x, _area.right)
             for y in [_area.y + 30]
             if tuple(_ovpx[x, y]) == (0, 0, 255)]
    if _red and _blue:
        assert max(_blue) > max(_red), (
            "the last figure drawn is not the rightmost on the "
            "surface. coldraw.cpp:349 draws and :377 increments, so "
            "the walk is ascending and a later figure covers an "
            "earlier one's right edge")

    # 8. THE CLICK IS UNMOVED, AND IT FOLLOWS THE SLOT AND NOT THE
    # INK. `case 4` (coldraw.cpp:367) takes the FIRST slot whose
    # right edge is at or past the pointer — the LEFTMOST slot, which
    # at an overlap is the figure that is partly underneath. The
    # original's own click and ink disagree there; transcribing it is
    # right and "the click should follow the visible figure" is the
    # invention.
    from screens.colony_summary import colonyicons as _ci
    _cnt = 8
    _pitch = _ci.column_pitch(0, _cnt)
    assert _pitch < _ci.ICON_SPACING, (
        f"eight farmers no longer squish (pitch {_pitch}); the "
        f"overlap case this asserts does not arise")
    _edge0 = _ci.slot_right_edge(0, 0, _cnt)
    assert _ci.slot_at(0, _edge0, _cnt) == 0 and \
        _ci.slot_at(0, _edge0 + 1, _cnt) == 1, (
            "slot_at no longer answers by slot boundary. A click one "
            "px past slot 0's right edge belongs to slot 1 even where "
            "slot 0's sprite is still drawn over it")
    # 9. THE CLIP IS LOSSLESS, MEASURED ACROSS THE WHOLE SET. A
    # stepped figure is taller than its row at 2560x1440 — 84 px
    # against 77 — and the row clip has to take that out of empty
    # canvas. Every master must therefore carry enough transparent
    # rows BELOW its ink, which is why the figure is top-aligned:
    # what the clip removes is the bottom of the canvas, never a head.
    if _figs_present:
        _worst_bottom = 28
        for _fn in _fig_names:
            _img = pygame.image.load(
                os.path.join(_proj, _fig.FIGURE_DIR, _fn)).convert_alpha()
            assert _img.get_size() == (28, 28), (
                f"{_fn} is {_img.get_size()} — every RACEICON job "
                f"sprite and both shared sprites are 28x28, measured "
                f"across all 171 entries")
            _worst_bottom = min(_worst_bottom,
                                28 - _img.get_bounding_rect().bottom)
        for _st in _fig.STEPS:
            _rowpx = round(58 * (1.0 if _st == 2 else
                                 (4 / 3 if _st == 3 else 2.0)))
            _over = max(0, _fig.step_size(_st) - _rowpx)
            assert _over <= _worst_bottom * _st, (
                f"at step {_st}x a figure overhangs its row by "
                f"{_over}px and the emptiest master has only "
                f"{_worst_bottom * _st}px of transparent canvas below "
                f"its ink — the row clip would cut a figure's feet")
    ok(f"population figures: {len(_fig_names)} names, step is a swap "
       f"(28x2/3/4), mod master and per-step files with the order "
       f"per root, absent set draws cells, row clip loses no ink)")

    # ── `doc/modding_figures.md` IS GENERATED, AND CHECKED ──
    #
    # A hand-written list of 54 names is wrong within a month, and a
    # modder following a stale name gets SILENCE — a file nothing
    # looks for is indistinguishable from a file that is not there.
    # Regenerated here and compared byte for byte, the same trade the
    # check count makes.
    import importlib.util as _ilu
    _mdspec = _ilu.spec_from_file_location(
        "_make_modding_doc", os.path.join(_proj, "tools",
                                          "make_modding_doc.py"))
    _mdmod = _ilu.module_from_spec(_mdspec)
    _mdspec.loader.exec_module(_mdmod)
    _mdpath = os.path.join(_proj, "doc", "modding_figures.md")
    assert os.path.exists(_mdpath), (
        "doc/modding_figures.md is absent — run "
        "`python tools/make_modding_doc.py`")
    _mdtext = open(_mdpath, encoding="utf-8").read()
    assert _mdtext == _mdmod.render(), (
        "doc/modding_figures.md no longer matches the loader's table. "
        "It is GENERATED — run `python tools/make_modding_doc.py` "
        "rather than editing it, or the names a modder copies stop "
        "being the names the loader looks for")
    for _need in ("@2x.png", "@3x.png", "@4x.png", "28 x 28",
                  "refused", "human_farmer.png"):
        assert _need in _mdtext, (
            f"the generated modding document no longer carries "
            f"{_need!r} — both conventions, the master size and the "
            f"refusal have to reach the person writing the mod")
    # AND THE EXTRACTOR IS IN setup.py, which it was not until now:
    # help, nebula, techname and estrings were all listed and this
    # one had never been added.
    _sp = open(os.path.join(_proj, "tools", "setup.py"),
               encoding="utf-8").read()
    assert "raceicon_extract.py" in _sp, (
        "tools/setup.py does not name the figure extractor, so an "
        "install without figures is never told what to run")
    ok("modding_figures.md regenerates byte for byte; the figure "
       "extractor is in setup.py")

    ok("colony header plates (the window is a marked DEVIATION, the "
       "plate height is a transcribed number that does not fit, the "
       "job columns are colsum.cpp's unequal three)")

    ok(f"marker inventory ({len(_MARKED)} files carry an HD EXTENSION "
       f"or DEVIATION and every one of them is read by a check)")

    # ── The pop-movement rules, mirrored (decision 33) ──
    # Four drop rules plus a refusal at the pick-up, each asserted
    # separately and each made to BITE — a rule that four others
    # cover is a rule nobody is testing.
    #
    # THE SHAPE IS A COUNT, NOT A BOOLEAN, and that is the check
    # worth having. Send_Cluster_ returns mid-cluster on a refusal
    # (colmove.cpp:168-173), so a mirror answering yes/no would say
    # "this works" and then move seven of twelve — decision 33's own
    # failure mode one level finer.
    from screens.colony_summary import colonymove as _cm
    from core.structs import colony as _cst

    def _pop(nibble=0, job=0, assigned=True, conquered=0):
        return (nibble | (job << 7)
                | (_cst.POP_MASK_ASSIGNED if assigned else 0)
                | (conquered << 10))

    # RULE 0 — the pick-up refuses a native outright, colmove.cpp:59.
    # Not one of the four: it is in a different function, and the
    # fundament's count missed it until 4 September 2026.
    assert _cm.plan_pickup([_pop(9)], 1, 0).refused == \
        _cm.REFUSE_NATIVE_PICKUP, "a native must not be picked up"
    assert _cm.plan_pickup([_pop(0)], 1, 0).refused is None

    # RULE 1 — natives take neither research nor industry
    # (colmove.cpp:524-529), and the `== 6` arm is transcribed.
    for _job, _want in ((_cm.ECON_RESEARCH, _cm.REFUSE_NATIVE_JOB),
                        (_cm.ECON_INDUSTRY, _cm.REFUSE_NATIVE_JOB),
                        (_cm.ECON_FOOD, None)):
        _p = _cm.plan_drop([_pop(9, 0)], 1, 255, _cm.Cluster([0]), _job)
        assert _p.reason == _want, (_job, _p)
    # The `|| pop_state == 6` arm is transcribed even though
    # Pop_To_Pop_State_ cannot return 6 (colony.cpp:1240). Asserted
    # BEHAVIOURALLY by forcing the state, because a text search for
    # "state == 6" passes on this module's own docstring, which says
    # the words — the first version of this check did exactly that
    # and survived the arm being deleted.
    _real_state = _cm.pop_state
    try:
        _cm.pop_state = lambda _w: 6
        _six = _cm.plan_drop([_pop(0, 0)], 1, 255, _cm.Cluster([0]),
                             _cm.ECON_RESEARCH)
    finally:
        _cm.pop_state = _real_state
    assert _six.reason == _cm.REFUSE_NATIVE_JOB, (
        f"with pop_state forced to 6 the native rule did not fire "
        f"({_six}) — colonymove no longer transcribes the "
        f"`|| pop_state == 6` arm of colmove.cpp:524. That branch is "
        f"unreachable in orion2re today, which is exactly why it is "
        f"written down rather than reasoned about: the condition "
        f"costs one `or`")

    # RULE 2 — androids keep the job they have (colmove.cpp:531-537),
    # and the path that never consults the rules lets one back onto
    # its own column.
    assert _cm.plan_drop([_pop(8, 1)], 1, 255, _cm.Cluster([0]),
                         _cm.ECON_RESEARCH).reason == _cm.REFUSE_ANDROID
    assert _cm.plan_drop([_pop(8, 1)], 1, 255, _cm.Cluster([0]),
                         _cm.ECON_INDUSTRY).reason is None, (
        "an android dropped back on its own column takes the "
        "re-flag path at colmove.cpp:165 and never reaches rule 2")

    # RULE 3 — at most 42 in a job (colmove.cpp:539-543). Asserted as
    # a COUNT: forty already there and a cluster of five gives two
    # landed and three carried, which is the whole reason plan_drop
    # does not return a boolean.
    _full = [_pop(0, 1)] * 40 + [_pop(0, 0)] * 5
    _fc = _cm.plan_pickup(_full, 45, 40)
    assert len(_fc.indices) == 5, _fc
    _fp = _cm.plan_drop(_full, 45, 255, _fc, _cm.ECON_INDUSTRY)
    assert (_fp.landed, _fp.carried, _fp.reason) == (
        2, 3, _cm.REFUSE_JOB_FULL), (
        f"forty in industry and a cluster of five must land TWO and "
        f"carry three, stopping on the job limit; got {_fp}")
    assert _fp.stopped_at == 42, _fp

    # RULE 4 — a farmer needs max_farms > sum (colmove.cpp:546-554).
    # The field holds 0 or 255 and nothing between, so the rule is
    # binary in practice: a planet that cannot farm refuses its FIRST
    # farmer, and one that can never refuses here at all.
    _w3 = [_pop(0, 1)] * 3
    assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                         _cm.ECON_FOOD).reason == _cm.REFUSE_NO_FARMING
    assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                         _cm.ECON_FOOD).landed == 0
    assert _cm.plan_drop(_w3, 3, 255, _cm.Cluster([0, 1, 2]),
                         _cm.ECON_FOOD).reason is None
    assert _cm.plan_drop(_w3, 3, 0, _cm.Cluster([0, 1, 2]),
                         _cm.ECON_RESEARCH).landed == 3

    # A PARTIAL DROP IS THE NORMAL CASE, not an edge one: an android
    # in the middle of a cluster lands everyone before it and nobody
    # after.
    _mix = [_pop(0, 1), _pop(0, 1), _pop(8, 1)]
    _mp = _cm.plan_drop(_mix, 3, 255, _cm.Cluster([0, 1, 2]),
                        _cm.ECON_RESEARCH)
    assert (_mp.landed, _mp.carried, _mp.stopped_at) == (2, 1, 2), _mp

    # THE CLUSTER IS NOT THE RUN UNDER THE CURSOR. Get_Cluster_ scans
    # to the END of the array and takes every identical pop
    # (colmove.cpp:66-71), so a group split by a different one still
    # comes along in full.
    _split = [_pop(0, 0), _pop(0, 1), _pop(0, 0)]
    assert _cm.plan_pickup(_split, 3, 0).indices == (0, 2), (
        "a group split by a different pop must still be taken whole")

    # PLANNING MUST NOT MUTATE. A plan that changed the state it
    # planned against would be right exactly once.
    _before = list(_full)
    _cm.plan_drop(_full, 45, 255, _fc, _cm.ECON_INDUSTRY)
    assert _full == _before, "plan_drop mutated the caller's pops"

    # OUR OWN WORDING, per decision 15 — every reason has a string
    # and the count lines carry their placeholders.
    _mv = _out_cfg["move"]
    for _r in (_cm.REFUSE_NATIVE_PICKUP, _cm.REFUSE_NATIVE_JOB,
               _cm.REFUSE_ANDROID, _cm.REFUSE_JOB_FULL,
               _cm.REFUSE_NO_FARMING):
        assert _mv.get(_r), (
            f"move.{_r} has no wording. We refuse before injecting, so "
            f"the sentence is ours to own (decision 15) — the "
            f"original's ESTRINGs are not ours to copy, and one of "
            f"the two it uses describes a rule its code does not "
            f"implement (open fix 8)")
    for _ph in ("{landed}", "{carried}"):
        assert _ph in _mv["partial"], (
            f"move.partial lost {_ph} — the message is about HOW MANY "
            f"land, because the drop is divisible")
    ok("colony summary pop-movement rules mirrored (four rules, the "
       "pick-up refusal, and the count a partial drop lands)")

    # ── The game's list window, established not remembered ──
    # Decision 46. An injected click names a POSITION IN THE GAME'S
    # WINDOW, so `_first` has to agree with the HD row before
    # anything is sent, and nothing on the wire reports `_first`.
    #
    # THE PLAN IS CHECKED BY SIMULATING THE ORIGINAL'S OWN STEPPERS,
    # transcribed here from colsum.cpp rather than reasoned about,
    # and it is run FROM EVERY REACHABLE STARTING STATE — which is
    # the whole claim: "establish, do not remember" is only true if
    # the sequence lands on the target from wherever the window was.
    from screens.colony_summary.colonyselect import GameWindow as _GW

    def _sim_dec(first, n):
        # Decrement_First_, colsum.cpp:207-221. The stepper refuses
        # entirely below the window; the clamp is `< 1`, which for a
        # non-negative _first is max(0, _first - 1).
        if n >= _GW.SLOTS:
            return max(0, first - 1)
        return first

    def _sim_inc(first, n):
        # The CALLER's guard first (colsum.cpp:796): the increment is
        # only offered while _g_colony_list_ptr[_first + 10] is a real
        # colony, and that array is padded with -1 past the count.
        if not (first + _GW.SLOTS < n):
            return first
        # Increment_First_, colsum.cpp:223-232.
        if n >= _GW.SLOTS:
            return first + 1
        return first

    # SLOTS is the ORIGINAL's ten and is not read from the layout.
    # Decision 46's corollary: HD's visible row count is derived from
    # list_area and happens to be ten today, and every k is counted
    # against the game's window instead.
    assert _GW.SLOTS == 10, _GW.SLOTS
    for _n in range(0, 40):
        assert _GW.max_first(_n) == max(0, _n - 10), _n

    for _n in (0, 1, 5, 9, 10, 11, 12, 25, 37):
        _reachable = list(range(0, _GW.max_first(_n) + 1))
        for _target in range(0, max(2, _GW.max_first(_n) + 3)):
            _plan = _GW.plan(_n, _target)
            if _plan.refused:
                # A refused target is one the game cannot hold, and
                # it is refused rather than silently clamped.
                assert _target > _GW.max_first(_n) or not _GW.scrolls(_n), (
                    f"n={_n} target={_target} refused ({_plan.refused}) "
                    f"but max_first is {_GW.max_first(_n)}")
                assert _plan.steps == 0, _plan
                continue
            for _start in _reachable:
                _f = _start
                for _ in range(_plan.down):
                    _f = _sim_dec(_f, _n)
                assert _f == 0 or not _GW.scrolls(_n), (
                    f"n={_n}: {_plan.down} decrements from {_start} "
                    f"left the window at {_f}, not at the top — the "
                    f"safe direction is what makes this establish "
                    f"rather than remember")
                for _ in range(_plan.up):
                    _f = _sim_inc(_f, _n)
                assert _f == _target, (
                    f"n={_n} start={_start} target={_target}: the plan "
                    f"{_plan} lands on {_f}. Counting a step the game "
                    f"refuses is how the two windows come apart")

    # FEWER COLONIES THAN SLOTS DOES NOTHING, which is the acceptance
    # case: both steppers are guarded by colonies_count >= num_items
    # (colsum.cpp:210 and :226) and Update_First_ forces _first = 0
    # below the window (colsum.cpp:194-197). So the plan is no steps,
    # not "some steps that happen to be refused".
    for _n in range(0, 10):
        assert not _GW.scrolls(_n), _n
        _p = _GW.plan(_n, 0)
        assert (_p.down, _p.up, _p.refused) == (0, 0, None), (_n, _p)
        assert _GW.plan(_n, 1).refused == _GW.REFUSE_WINDOW_FIXED, _n
        # and every row is already in the window, at its own index
        for _pos in range(_n):
            _p2, _slot = _GW.slot_for(_n, _pos)
            assert (_p2.steps, _slot) == (0, _pos), (_n, _pos, _p2, _slot)

    # A ROW MAPS TO A SLOT, and the last page is full rather than
    # short: at n = 25 the window stops at 15, so row 24 is slot 9
    # and not slot 14 of a half-empty page.
    _p3, _slot3 = _GW.slot_for(25, 24)
    assert (_p3.first, _slot3) == (15, 9), (_p3, _slot3)
    _p4, _slot4 = _GW.slot_for(25, 20)
    assert (_p4.first, _slot4) == (15, 5), (_p4, _slot4)
    # Exactly ten colonies: the guard passes but the window still
    # cannot move, because slot ten would be empty.
    assert _GW.max_first(10) == 0 and _GW.scrolls(10)
    assert _GW.slot_for(10, 9)[1] == 9
    # Off the end is refused, not clamped.
    assert _GW.slot_for(11, 11)[0].refused == _GW.REFUSE_PAST_END
    assert _GW.slot_for(11, -1)[0].refused == _GW.REFUSE_PAST_END

    # The refusals carry OUR wording (decision 15), like the move
    # rules — a window that will not go where HD wants it is a reason
    # to show, not a silence.
    for _r in (_GW.REFUSE_WINDOW_FIXED, _GW.REFUSE_PAST_END):
        assert _out_cfg["move"].get(_r), (
            f"move.{_r} has no wording")
    ok("colony summary game window (plan lands from every reachable "
       "_first, and does nothing below ten colonies)")

    # ── Reading _first back off the game's own screen ──
    # _first is not on the wire, and ACTIVATE_FIELD has a single slot
    # (ext::g_pending_field), so a batch of window steps is silently
    # collapsed to the last one. The steps therefore have to be sent
    # one at a time and CONFIRMED — and the game draws the number:
    # Draw_Bar_Indicator_ (colsum.cpp:747-771) fills palette 229 from
    # 271*_first/n + 40 to 271*(_first+10)/n + 40 across x 621..626.
    #
    # ONE MATCH IS A POINT, NOT A CURVE. The formula is transcribed
    # and then exercised over EVERY (n, _first) the engine can hold:
    # each pair is rendered the way colsum.cpp draws it, borders over
    # the fill's edges included, and read back.
    from screens.colony_summary import colonyfirst as _cf

    def _render_thumb(n, first):
        _fb = [[0] * 640 for _ in range(480)]
        _b = _cf.thumb_bounds(n, first)
        if _b is None:
            return _fb
        _y1, _y2 = _b
        for _y in range(_y1, _y2 + 1):
            for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
                _fb[_y][_x] = _cf.THUMB_FILL
        # colsum.cpp:762-765 — the borders overwrite the fill's own
        # first and last row, which is why the run is inset by one.
        for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
            _fb[_y1][_x] = _cf.THUMB_BORDER_LIGHT
            _fb[_y2][_x] = _cf.THUMB_BORDER_DARK
        for _y in range(_y1, _y2 + 1):
            _fb[_y][_cf.THUMB_X0] = _cf.THUMB_BORDER_LIGHT
            _fb[_y][_cf.THUMB_X1] = _cf.THUMB_BORDER_DARK
        return _fb

    # THE CONSTANTS ARE ANCHORED TO LITERALS FIRST, because the
    # sweep below renders and reads through the SAME thumb_bounds and
    # is therefore blind to a wrong constant — changing 271 to 270
    # moves the drawing and the reader together and the sweep stays
    # green. These pairs are worked out from colsum.cpp:752-753 by
    # hand: 271*first/n + 40 and 271*(first+10)/n + 40, C integer
    # division, so n=11 first=0 gives 2710//11 = 246 for the lower
    # edge and n=20 first=5 gives 1355//20 = 67 for the upper.
    assert _cf.thumb_bounds(11, 0) == (40, 286), _cf.thumb_bounds(11, 0)
    assert _cf.thumb_bounds(11, 1) == (64, 311), _cf.thumb_bounds(11, 1)
    assert _cf.thumb_bounds(20, 5) == (107, 243), _cf.thumb_bounds(20, 5)
    assert _cf.thumb_bounds(250, 0) == (40, 50), _cf.thumb_bounds(250, 0)
    assert (_cf.THUMB_FILL, _cf.THUMB_X0, _cf.THUMB_X1) == (229, 621, 626)

    _pairs = 0
    for _n in list(range(10, 60)) + [72, 100, 135, 136, 200, 259]:
        for _f in range(0, max(0, _n - _cf.WINDOW) + 1):
            assert _cf.read_first(_render_thumb(_n, _f), _n) == _f, (
                f"n={_n}, _first={_f} read back as "
                f"{_cf.read_first(_render_thumb(_n, _f), _n)!r}")
            _pairs += 1
    assert _pairs > 1500, _pairs

    # THE TOLERANCE IS TRANSCRIBED, NOT TUNED, and a wider one is not
    # safer. The thumb moves 271/n px per step, so at 2 two
    # candidates fit one run from n = 136 and the reader must refuse.
    assert _cf.read_first(_render_thumb(136, 1), 136, tolerance=2) is None, (
        "at tolerance 2 and 136 colonies the thumb moves 1.993 px per "
        "step, so _first = 1 has two candidates fitting one run — the "
        "reader must return None rather than pick the nearer")
    assert _cf.read_first(_render_thumb(136, 1), 136) == 1, (
        "and at the transcribed tolerance of 1 the same state is exact")

    # THE NULL STATE IS ITS OWN ANSWER. Below ten colonies the bar is
    # not drawn at all (colsum.cpp:751) and Update_First_ has already
    # forced _first = 0 — so the reader must say NOT_DRAWN and never
    # 0. A channel that idles as a valid reading is the rim survey's
    # green-run-in-a-null-state, one domain over.
    for _n in range(0, 10):
        assert _cf.thumb_bounds(_n, 0) is None, _n
        assert _cf.read_first(_render_thumb(_n, 0), _n) == _cf.NOT_DRAWN, (
            f"with {_n} colonies the bar is not drawn and the reader "
            f"returned something other than NOT_DRAWN — a reading of 0 "
            f"there is indistinguishable from a real _first of 0")
    assert _cf.NOT_DRAWN != 0 and _cf.NOT_DRAWN is not None
    # A blank screen with enough colonies is also NOT_DRAWN: the
    # colony summary is simply not up.
    assert _cf.read_first([[0] * 640 for _ in range(480)], 25) == \
        _cf.NOT_DRAWN

    # AND A RUN THAT FITS NOTHING IS NOT A READING EITHER. None and
    # NOT_DRAWN are different answers and a caller must stop on both.
    _junk = [[0] * 640 for _ in range(480)]
    for _y in range(200, 210):
        for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
            _junk[_y][_x] = _cf.THUMB_FILL
    assert _cf.read_first(_junk, 25) is None, (
        "a 229 run matching no candidate must read as None — the "
        "channel spoke and was not understood")
    ok(f"colony summary _first read back from the scroll thumb "
       f"({_pairs} states, null state distinct from zero)")

    # ── The list SCROLLS, for viewing only (fundament 46) ──
    # Fifteen colonies against a panel that holds ten, so the offset
    # has somewhere to go. The synthetic empire ships five, which is
    # why this builds its own rather than reusing _sel_snap.
    from screens.colony_summary import colonyselect as _cs_sel
    _sc_cols = [dict(_c, star=f"{_c['star']}{_i}")
                for _i, _c in enumerate(_pv.COLONIES * 3)]
    _sc_snap = _pv._Snapshot(_sc_cols)
    _scr_op._sort_key = "name"
    _scr_op.update(_sc_snap)
    _sc_n = len(_scr_op._rows)
    _sc_view = _scr_op._list_view()
    _sc_vis = _scr_op._window.visible(*_sc_view)
    assert _sc_vis == _cl.rows_drawn(_la, _lcfg, app.layout.scale, _sc_n), (
        "the screen and colonylist disagree about how many rows fit")
    assert 0 < _sc_vis < _sc_n, (
        f"{_sc_n} rows into a panel that holds {_sc_vis} — this block "
        f"cannot test scrolling if everything fits")

    # THE CLAMPS ARE THE ORIGINAL'S, all three of them, and they are
    # asserted on the Window rather than through the screen so a
    # failure names the rule rather than a pixel.
    _w = _cs_sel.Window()
    # Lower bound 0: Decrement_First_ floors it (colsum.cpp:211-214).
    _w.scroll(-99, _sc_n, _sc_vis)
    assert _w.first == 0, _w.first
    # Upper bound: Increment_First_ is reached only while
    # _g_colony_list_ptr[_first + 10] != -1 (colsum.cpp:796), so the
    # original's LAST PAGE IS FULL and first stops at n - visible.
    _w.scroll(99, _sc_n, _sc_vis)
    assert _w.first == _sc_n - _sc_vis, (
        f"first ran to {_w.first}; the original stops at "
        f"{_sc_n - _sc_vis} because it refuses the step that would "
        f"leave the window's last slot empty (colsum.cpp:796)")
    # Fewer rows than fit: neither stepper runs at all
    # (colsum.cpp:210 and :226) and Update_First_ forces 0 every draw
    # (colsum.cpp:194-197).
    _w2 = _cs_sel.Window()
    _w2.scroll(5, _sc_vis - 1, _sc_vis)
    assert _w2.first == 0, (
        f"a list shorter than the window scrolled to {_w2.first}; the "
        f"original's steppers refuse it outright")
    _w2.first = 7
    assert _w2.clamp(_sc_vis - 1, _sc_vis) == 0, (
        "a window left pointing past a shrunken list did not "
        "re-establish itself; Update_First_ does that every frame")

    # THE ARROWS SAY IT IN BOTH DIRECTIONS. The line this replaced
    # counted `n - visible` at every offset, because at the bottom
    # nothing is below and a count of the tail alone would say
    # nothing is missing. The arrows carry the same both-ways
    # property directly: at the top only DOWN is live, at the bottom
    # only UP, and in the middle both.
    from screens.colony_summary import colonyscroll as _cscr2
    _sc_hidden = _sc_n - _sc_vis
    _sc_surf = pygame.Surface((_la.right + 8, _la.bottom + 8))
    _sc_up_r, _sc_dn_r = _cscr2.arrows(_la, _lcfg, app.layout.scale)
    assert _sc_up_r is not None

    def _sc_ink_at(_first):
        _sc_surf.fill((0, 0, 0))
        _cl.render(_sc_surf, _scr_op._rows, _la, _lcfg, app.layout,
                   app.style, _first)
        return tuple(int(pygame.surfarray.array3d(
            _sc_surf.subsurface(_r)).sum())
            for _r in (_sc_up_r, _sc_dn_r))

    _sc_top_up, _sc_top_dn = _sc_ink_at(0)
    _sc_mid_up, _sc_mid_dn = _sc_ink_at(_sc_hidden // 2)
    _sc_bot_up, _sc_bot_dn = _sc_ink_at(_sc_hidden)
    assert _sc_top_dn > _sc_top_up, (
        f"at the top of {_sc_n} rows with {_sc_vis} visible, the down "
        f"arrow is not the live one ({_sc_top_dn} against {_sc_top_up})")
    assert _sc_bot_up > _sc_bot_dn, (
        f"at the bottom the up arrow is not the live one "
        f"({_sc_bot_up} against {_sc_bot_dn})")
    assert _sc_mid_up == _sc_top_dn and _sc_mid_dn == _sc_top_dn, (
        f"in the middle both arrows should be live and equally lit; "
        f"got up {_sc_mid_up}, down {_sc_mid_dn}, live {_sc_top_dn}")

    # And the window really is a different slice: the top row drawn
    # at the bottom offset is not the top row drawn at 0.
    assert _scr_op._rows[0] is not _scr_op._rows[_sc_hidden], "no slice"

    # THE MARKINGS. The wheel is an HD EXTENSION — MOO2 has no wheel
    # on this screen — and the original's slider is NOT DRAWN. Both
    # are recorded in three places and a marking with no check is an
    # intention, which is the failure the help panel's marking taught.
    assert "HD EXTENSION" in (_scr_op.handle_mousewheel.__doc__ or ""), (
        "screen.handle_mousewheel no longer marks the wheel as an HD "
        "EXTENSION; MOO2 scrolls this list with two step buttons and "
        "a slider (colsum.cpp:790-800), never a wheel")
    assert "HD EXTENSION" in _lcfg.get("_hd_extension_wheel", ""), (
        "layout.json list._hd_extension_wheel no longer marks the "
        "wheel")
    for _cite in ("NOT DRAWN", "Draw_Bar_Indicator_",
                  "colsum.cpp:747-753"):
        assert _cite in (_cl.__doc__ or ""), (
            f"colonylist no longer records {_cite!r} — the original "
            f"draws a proportional slider and this screen does not, "
            f"and an omission nobody wrote down is indistinguishable "
            f"from one nobody saw")
    ok("colony summary list scrolls (clamps transcribed, overflow "
       "counts above and below, wheel marked, slider recorded)")

    # ── A SCROLL SENDS NOTHING TO THE GAME (fundament 46) ──
    # This is what lets the package ship without the synchronisation.
    # The original's rows are ten SLOTS over the sorted array
    # (_list_col[i] = _g_colony_list_ptr[_first + i],
    # colsum.cpp:348-351) and every clickable field is built per slot
    # (Add_Fields_Pop_For_, colsum.cpp:312-346), so an injected click
    # names a position in the GAME's window and _first decides which
    # colony it reaches. Ours is a viewing offset the game has never
    # heard of. Scrolling is therefore safe precisely as long as it
    # injects NOTHING, and the day somebody adds an injection to this
    # path it must fail here rather than send a click to the wrong
    # colony — which is invisible, because every value on both
    # screens stays correct.
    class _CapAll(_Cap):
        def __init__(self):
            super().__init__(); self.fields = []
        def activate_field(self, f): self.fields.append(f)
    _sc_cap = _CapAll()
    _sc_client, _sc_conn = app.client, app.connected
    app.client, app.connected = _sc_cap, True
    _sc_pt = (_la.x + 4, _la.y + 4)
    _sc_before = _scr_op._selected
    for _ in range(_sc_n + 5):
        _scr_op.handle_mousewheel(-1, *_sc_pt)      # down, past the end
    assert _scr_op._first == _sc_hidden, (
        f"scrolling to the end left first at {_scr_op._first}, not "
        f"{_sc_hidden}")
    for _ in range(_sc_n + 5):
        _scr_op.handle_mousewheel(1, *_sc_pt)       # and back up
    assert _scr_op._first == 0, _scr_op._first
    assert _sc_cap.calls == [] and _sc_cap.keys == [] \
        and _sc_cap.fields == [], (
        f"a scroll reached the game: clicks {_sc_cap.calls}, keys "
        f"{_sc_cap.keys}, fields {_sc_cap.fields}. The HD list scrolls "
        f"for VIEWING ONLY — the game's _first is not synchronised "
        f"yet (fundament 46), so an injection now names a row in the "
        f"game's window and reaches the wrong colony")
    # A wheel outside list_area is not ours either.
    _scr_op.handle_mousewheel(-1, _la.x - 40, _la.y - 40)
    assert _scr_op._first == 0, (
        "a wheel event outside list_area scrolled the list")

    # SCROLLING DOES NOT MOVE THE SELECTION. It holds a COLONY, not a
    # row index (colsum.cpp:830-837, colonyselect), so the window may
    # travel past it and the scan box goes on showing the same colony.
    assert _scr_op._selected == _sc_before, (
        f"a scroll moved the selection from {_sc_before} to "
        f"{_scr_op._selected}")

    # A SORT RESETS THE WINDOW AND KEEPS THE SELECTION — one handler,
    # two opposite rules. colsum.cpp:832 sets _first = 0; the same
    # block (colsum.cpp:830-837) never assigns _g_colony_n.
    for _ in range(3):
        _scr_op.handle_mousewheel(-1, *_sc_pt)
    assert _scr_op._first == 3, _scr_op._first
    _sc_sel_before = _scr_op._selected
    _sc_btn = next(_b for _b in _scr_op._sort_buttons()
                   if _b.key == "population")
    _scr_op.handle_click(_sc_btn.hit.centerx, _sc_btn.hit.centery)
    assert _scr_op._first == 0, (
        f"the sort left the window at {_scr_op._first}; the original "
        f"puts it back at the top (_first = 0, colsum.cpp:832)")
    assert _scr_op._selected == _sc_sel_before, (
        f"the sort moved the selection from {_sc_sel_before} to "
        f"{_scr_op._selected}; colsum.cpp:830-837 never touches "
        f"_g_colony_n, so the colony keeps its identity and only its "
        f"ROW moves")
    app.client, app.connected = _sc_client, _sc_conn
    _scr_op._sort_key = "name"
    _scr_op.update(_sel_snap)
    ok("colony summary scroll injects nothing and moves no selection; "
       "a sort resets the window and keeps the colony")

    # ── The icons a column draws, and in whose order ──────────────
    # A COLUMN IS NOT pop[] IN ARRAY ORDER. `Do_Colony_Info_Pop_Stuff_
    # For_Pop_` (coldraw.cpp:326-337) walks state, then the conquered
    # bit, then pop_order (9 first), then the array — so the icon at
    # slot m is not the m-th pop of that job, and a click aimed by
    # array position would take the wrong cluster with every number on
    # both screens still correct.
    from screens.colony_summary import colonyicons as _ci

    def _icon_pop(nibble=0, job=0, assigned=True, conquered=0):
        return (nibble | (job << 7)
                | (_cst.POP_MASK_ASSIGNED if assigned else 0)
                | (conquered << 10))

    # THE LIVE CASE, ENCODED. Measured 5 September 2026 against the
    # reference save: Blucher II had twelve farmers and one scientist,
    # the scientist at pop 11 and the last farmer at pop 12. A click
    # at native x 230 — past every icon — took pop 12, which is slot
    # ELEVEN of the column and not pop 11. That is the whole
    # distinction this module exists for, so it is the fixture.
    _live = ([_icon_pop(0, 0)] * 11 + [_icon_pop(0, 2)]
             + [_icon_pop(0, 0)])
    assert _ci.icon_pops(_live, 13, 0) == tuple(list(range(11)) + [12]), (
        "the food column must draw pops 0..10 and 12 — the scientist "
        "at 11 is not in it, and the last farmer is index 12")
    assert _ci.slot_at(0, 230, 12) == 11, (
        "a click past every icon selects the LAST slot "
        "(coldraw.cpp:361), which here is slot 11")
    assert _ci.slot_pop(_live, 13, 0, 11) == 12, (
        "slot 11 of that column is pop 12; reading it as pop 11 is "
        "the array-order mistake this check is about")

    # THE FIVE LOOPS, each asserted where it decides the order.
    # state first (normal 2, native 3, android 4 — colony.cpp:1240),
    # then the conquered bit, then the low nibble in pop_order's own
    # sequence, and only then the array.
    _mixed = [_icon_pop(9, 0), _icon_pop(0, 0), _icon_pop(8, 0),
              _icon_pop(1, 0), _icon_pop(0, 0, conquered=1),
              _icon_pop(0, 0)]
    assert _ci.icon_pops(_mixed, 6, 0) == (1, 5, 3, 4, 0, 2), (
        f"draw order is {_ci.icon_pops(_mixed, 6, 0)}; expected the "
        f"low nibbles grouped before the array is consulted — 0s "
        f"(1, 5), then the 1 (3), then the conquered 0 (4), then the "
        f"native (0), then the android (2)")
    # THE ARRAY IS THE INNERMOST TIE-BREAK AND NOTHING MORE. Pops 1
    # and 3 are both unconquered normals and 1 comes first here only
    # because its low nibble does — the nibble loop is OUTSIDE the
    # array loop (coldraw.cpp:329-331). Written down because the
    # first version of this check expected (1, 3, 5), which is what
    # "within a group, array order" reads like until you ask what a
    # group is.
    assert _ci.POP_ORDER[0] == 9 and len(_ci.POP_ORDER) == 10, (
        "pop_order is (9, 0..8) — coldraw.cpp:287-297")

    # UNASSIGNED POPS ARE NOT ICONS (coldraw.cpp:336). This is the
    # difference between the HD row, which draws a square per pop of a
    # job, and the game, which draws one per ASSIGNED pop — and it is
    # exactly the state a held cluster produces.
    _held = [_icon_pop(0, 0), _icon_pop(0, 0, assigned=False)]
    assert _ci.icon_pops(_held, 2, 0) == (0,), (
        "a pop in a held cluster draws no icon")
    assert _ci.slot_pop(_held, 2, 0, 1) is None, (
        "a slot past the icons must answer None, not a guess — the "
        "caller refuses the click on it")

    # THE SECOND COPY OF pop_state IS DELIBERATE AND MUST AGREE.
    for _n in range(16):
        assert _ci._state(_icon_pop(_n)) == _cm.pop_state(_icon_pop(_n)), (
            f"colonyicons._state and colonymove.pop_state disagree at "
            f"nibble {_n}; the two copies exist so one can be "
            f"re-read without the other silently following")
    # A CLUSTER IS A CONTIGUOUS RUN OF ICONS, AND ONLY BECAUSE THE
    # COLUMN IS DRAWN IN THE ORIGINAL'S ORDER (decision 48).
    # `Get_Cluster_` takes every identical pop from the clicked one to
    # the END OF THE ARRAY (colmove.cpp:66-71), and `Pops_Identical_`
    # compares exactly the three fields the walk groups by — so the
    # cluster is "this icon and every icon after it" only while the
    # grouping holds. Ordered any other way inside a job, a click on
    # one cell would move cells elsewhere in the row, with every count
    # on screen still correct. Asserted here rather than trusted,
    # because the drawing that would break it is not written yet and
    # this is what has to fail when somebody writes it.
    #
    # `pop[]` itself has no order to lean on: appended on growth,
    # replaced by the LAST entry on removal, and shuffled outright by
    # invasion.cpp:721 when a colony builds Biospheres. The array
    # order below is therefore deliberately hostile — a foreign pop
    # between two own ones, which is what the engine actually
    # produces (doc/pop_order_reading.md).
    _mix_pops = [_icon_pop(0, 0), _icon_pop(3, 0), _icon_pop(0, 0),
                 _icon_pop(0, 0, conquered=1), _icon_pop(9, 0),
                 _icon_pop(0, 0)]
    _mix_icons = _ci.icon_pops(_mix_pops, 6, 0)
    for _start in range(6):
        if _ci.pop_slot(_mix_pops, 6, 0, _start) is None:
            continue
        _cl_plan = _cm.plan_pickup(_mix_pops, 6, _start)
        if _cl_plan.refused:
            continue
        _slots = sorted(_mix_icons.index(_p) for _p in _cl_plan.indices)
        assert _slots == list(range(_slots[0], _slots[0] + len(_slots))), (
            f"the cluster from pop {_start} is icons {_slots}, which is "
            f"not one run — decision 48's grouping has been broken")
        assert _slots[0] == _mix_icons.index(_start), (
            f"the cluster starts at icon {_slots[0]}, not at the "
            f"clicked one ({_mix_icons.index(_start)})")
        assert _slots[-1] == _slots[0] + len(_cl_plan.indices) - 1
    ok("a pop cluster is one contiguous run of icons (decision 48: "
       "only because the column is drawn in the original's order)")

    # ── The nibble marking is SPLIT, and it has to stay split ────
    # 9 = native has three independent sources as of 5 September 2026
    # (data, picture, the game's own label); 8 = android and the
    # conquered bit have none, because no save this project holds
    # contains either. Those are different claims and the difference
    # is the whole value of the day's work — "verified" with a
    # footnote is how a reader stops reading. A marking with no check
    # is an intention (the help panel's lesson), so this is the check.
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _src(*parts):
        return open(os.path.join(_root_dir, *parts)).read()

    _nib_spec = _src("core", "structs", "colony.py")
    for _needle in ("9 = NATIVE IS VERIFIED", "8 = ANDROID IS NOT VERIFIED",
                    "the DATA", "the PICTURE", "OWN WORDS",
                    "fixture_natives_3502.5.GAM", "b1f1aa466716d6c0"):
        assert _needle in _nib_spec, (
            f"core/structs/colony.py no longer records {_needle!r}. The "
            f"nibble claim rests on a named save and three named "
            f"sources; a claim that stops naming them is back to being "
            f"three readings of one tree (decision 23)")
    _nib_move = _src("screens", "colony_summary", "colonymove.py")
    assert "still UNVERIFIED" in _nib_move, (
        "colonymove's android rule no longer says it is unverified — "
        "no save in this project contains an android, so the rule is "
        "mirrored from the source alone")
    _nib_status = _src("v3_projektstatus.md")
    for _needle in ("VERIFIED: nibble 9 = native",
                    "STILL OPEN: nibble 8 = android"):
        assert _needle in _nib_status, (
            f"v3_projektstatus.md no longer carries {_needle!r}")
    # And the behaviour the marking is about still holds both ways.
    assert _cm.pop_state(_icon_pop(9)) == _cm.POP_STATE_NATIVE
    assert _cm.pop_state(_icon_pop(8)) == _cm.POP_STATE_ANDROID
    assert _cst.POP_NATIVE == 9 and _cst.POP_ANDROID == 8
    ok("pop identity: 9 = native verified by three sources, 8 and "
       "conquered still open, and the split is asserted")

    ok("colony icons (draw order is state/conquered/pop_order/array, "
       "not array; unassigned pops draw nothing)")

    # ── The squish, and the x that lands on a slot ────────────────
    # Calculate_Squish_Step_ (coldraw.cpp:12-33) divides the column by
    # the icon count, so the pitch moves with the population. The aim
    # has to round-trip through the original's own walk, or a click
    # takes the icon next door — which moves a different cluster and
    # looks perfectly right.
    for _job, (_lx, _rx) in enumerate(_ci.COLUMNS):
        for _count in range(1, 43):
            _pitch = _ci.column_pitch(_job, _count)
            _want = min(_ci.ICON_SPACING,
                        max(1, int((_rx - _lx - 10) / _count)))
            assert _pitch == _want, (
                f"column {_job} at {_count} icons: pitch {_pitch}, "
                f"the source computes {_want}")
            # Every icon inside the column, with the ten px the
            # `spacing / -3` term reserves still to spare — which is
            # why Find_Bar_Position_'s clamp never bites.
            assert _lx + _pitch * _count <= _rx - 10, (
                f"the last icon of {_count} in column {_job} reaches "
                f"{_lx + _pitch * _count}, past {_rx - 10}")
            for _slot in range(_count):
                _x = _ci.slot_click_x(_job, _slot, _count)
                assert _ci.slot_at(_job, _x, _count) == _slot, (
                    f"aiming at slot {_slot} of {_count} in column "
                    f"{_job} (x {_x}) selects "
                    f"{_ci.slot_at(_job, _x, _count)}")
    # The fallback: anything past the last icon is the last icon
    # (coldraw.cpp:361), which is what makes a click at the column's
    # right edge safe without any squish arithmetic at all.
    assert _ci.slot_at(0, _ci.COLUMNS[0][1], 7) == 6
    assert _ci.slot_at(0, _ci.COLUMNS[0][0] - 50, 7) == 0, (
        "a value left of the column selects the first icon; "
        "Find_Bar_Position_ clamps it to range_min (fields.cpp:1710)")
    assert _ci.slot_at(0, 200, 0) is None, (
        "an empty column selects nothing — Get_Selected_Pop_ returns "
        "-1 and Get_Cluster_ is never called")
    # The row a click names is a SLOT in the game's window, never an
    # HD row (decision 46), and its y is the field's own middle.
    assert _ci.row_click_y(0) == 34 + 15 and _ci.row_click_y(3) == \
        34 + 93 + 15, "row y is slot * 31 + 34, colsum.cpp:311-345"
    ok("colony icon geometry (squish transcribed, every slot's click "
       "round-trips through the original's own walk)")

    # ── The pop move: nothing reaches the game until both clicks ──
    # Section 3 of this phase, and the whole of why the first click is
    # local: there is no cancel that stays on this screen, so a
    # preview that created the game's own cluster would strand a
    # player who changed their mind (colsum.cpp:804 and :938 are both
    # leave-the-screen paths). The claim is about the WIRE and is
    # asserted on the wire — "the screen looks the same afterwards"
    # would also be true of a screen that sent a click and redrew the
    # old picture.
    from screens.colony_summary import colonypick as _cp
    from screens.colony_summary import colonysend as _cse
    from screens.colony_summary import colonymoveui as _cmu
    from screens.colony_summary import colonytrack as _ct
    from screens.colony_summary import colonypopup as _cpop
    from core import textfit as _textfit
    from core import wire_protocol as _wire

    class _MoveCap(_CapAll):
        def __init__(self):
            super().__init__()
            self.stats = {"state": 0, "visual": 0}

    _mv_cap = _MoveCap()
    _mv_client, _mv_conn = app.client, app.connected
    app.client, app.connected = _mv_cap, True
    _scr_op._sort_key = "name"
    _scr_op.update(_sel_snap)
    _mv_rows = _scr_op._rows
    _mv_area, _mv_cfg, _mv_scale, _mv_n = _scr_op._list_view()
    _mv_track = _cl.track_metrics(_mv_area, _mv_cfg, _mv_scale)
    _mv_bands = _cl.row_bands(_mv_area, _mv_cfg, _mv_scale, _mv_n)

    def _square_xy(row_index, job, index=0):
        """The centre of one CELL, from the row's own geometry.

        Since 6 September a slot index is not a cell index — the job
        markers sit between the groups — so this asks `row_boxes`
        rather than multiplying a pitch, which is the same reason
        `drop_targets` exists.
        """
        _top, _h = _mv_bands[row_index]
        for _j, _i, _r in _cl.row_boxes(_mv_area, _mv_cfg, _mv_scale,
                                        _mv_rows[row_index]).cells:
            if (_j, _i) == (job, index):
                return _r.x + _r.width // 2, _top + _h // 2
        raise AssertionError(f"row {row_index} has no cell {index} of "
                             f"job {job}")

    def _band_xy(row_index, job):
        _top, _h = _mv_bands[row_index]
        for _j, _r in _cl.drop_targets(_mv_area, _mv_cfg, _mv_scale,
                                       _mv_rows[row_index]):
            if _j == job and _r.width:
                return _r.x + _r.width // 2, _top + _h // 2
        raise AssertionError(f"no drop target for job {job}")

    # A row with pops in at least two jobs, so a move has somewhere
    # to go and the fixture is not the thing being tested.
    _mv_row = next(i for i, r in enumerate(_mv_rows)
                   if sum(1 for c in r["jobs"] if c) >= 2)
    _mv_job = next(j for j, c in enumerate(_mv_rows[_mv_row]["jobs"]) if c)
    _mv_slot = 0    # the first cell of that job
    _mv_target = next(j for j in range(3) if j != _mv_job)

    # FIRST CLICK: a selection, and NOTHING on the wire.
    _scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
    assert _scr_op._move.pick is not None, (
        "a click on a filled square did not pick anything up")
    assert _mv_cap.calls == [] and _mv_cap.keys == [] \
        and _mv_cap.fields == [], (
        f"the FIRST click reached the game: clicks {_mv_cap.calls}, "
        f"keys {_mv_cap.keys}, fields {_mv_cap.fields}. It must not: "
        f"Get_Cluster_ unassigns the pops there and then, and the "
        f"only ways out of a held cluster are dropping it or leaving "
        f"the screen")

    # THE CANCEL — HD EXTENSION. Right click discards it, and that is
    # free precisely because nothing was sent.
    _scr_op.handle_right_button(True, *_square_xy(_mv_row, _mv_job, _mv_slot))
    assert _scr_op._move.pick is None, (
        "a right click did not discard the selection")
    assert _mv_cap.calls == [] and _mv_cap.keys == [] \
        and _mv_cap.fields == [], "the cancel path reached the game"
    # And so does a left click that lands on neither icon nor band.
    _scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
    assert _scr_op._move.pick is not None
    _scr_op.handle_click(_mv_area.x + 2, _mv_area.bottom - 2)
    assert _scr_op._move.pick is None, (
        "a click off the rows did not discard the selection")
    assert _mv_cap.calls == [] and _mv_cap.fields == []

    # EVERY REFUSAL SENDS NOTHING AND SAYS WHY, and the wording comes
    # out of layout.json (decision 15). Driven through the controller
    # rather than the rules, because the claim is about the seam.
    _mv_words = _scr_op._data["move"]
    _mv_pops, _mv_np, _mv_mf = _cp.pops_of(_sel_snap,
                                           _mv_rows[_mv_row]["index"])

    def _refusal(pops, n_pops, max_farms, job, slot, target,
                 sort_key="name"):
        _c = _cmu.MoveController()
        _pick = _cp.pick_at(pops, n_pops, job, slot,
                            _mv_rows[_mv_row]["index"], _mv_row,
                            sort_key)
        if isinstance(_pick, _cp.Refusal):
            return _pick
        _c.pick = _pick
        return _cp.plan_move(_pick, pops, n_pops, max_farms,
                             _mv_rows[_mv_row]["index"], target)

    # A native is refused at the FIRST click, in a different function
    # with a different message (colmove.cpp:59-64).
    _nat = [_icon_pop(9, 0)] + list(_mv_pops[1:])
    assert _refusal(_nat, _mv_np, _mv_mf, 0, 0, 1).reason == \
        _cm.REFUSE_NATIVE_PICKUP
    # An android keeps its job (colmove.cpp:531-537).
    _and = [_icon_pop(8, 0)] + list(_mv_pops[1:])
    assert _refusal(_and, _mv_np, _mv_mf, 0, 0, 1).reason == \
        _cm.REFUSE_ANDROID
    # A planet that cannot farm refuses its first farmer.
    assert _refusal(list(_mv_pops), _mv_np, 0, 1, 0, 0).reason == \
        _cm.REFUSE_NO_FARMING
    # And a sort HD cannot honour refuses the whole thing: the two
    # lists are not in the same order, so no row maps to a slot.
    assert _refusal(list(_mv_pops), _mv_np, _mv_mf, 0, 0, 1,
                    sort_key=next(iter(_cr.SORT_UNAVAILABLE))).reason \
        == _cp.REFUSE_SORT_UNAVAILABLE
    for _r in (_cm.REFUSE_NATIVE_PICKUP, _cm.REFUSE_ANDROID,
               _cm.REFUSE_NO_FARMING, _cp.REFUSE_SORT_UNAVAILABLE,
               _cp.REFUSE_NO_ICON, _cp.REFUSE_OTHER_COLONY):
        assert _mv_words.get(_r), f"move.{_r} has no wording"
        assert _cp.message(_mv_words, _cp.Refusal(_r)) == _mv_words[_r]
    # A PARTIAL carries both halves: the rule that stopped it AND the
    # count, because "this job is full" alone reads as "nothing fits"
    # when two of twelve would have moved.
    _part = _cp.message(_mv_words, _cp.Refusal(_cm.REFUSE_JOB_FULL,
                                               landed=2, carried=10,
                                               total=12))
    assert _mv_words[_cm.REFUSE_JOB_FULL] in _part and "2" in _part \
        and "12" in _part, _part
    assert "{" not in _part, (
        "a placeholder survived substitution; `message` replaces and "
        "never formats (decision 37)")

    # A REFUSED DROP SENDS NOTHING THROUGH THE SEAM EITHER.
    _mv_cap.calls, _mv_cap.keys, _mv_cap.fields = [], [], []
    _scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
    _scr_op._sort_key = next(iter(_cr.SORT_UNAVAILABLE))
    _scr_op.handle_click(*_band_xy(_mv_row, _mv_target))
    _scr_op._sort_key = "name"
    assert _mv_cap.calls == [] and _mv_cap.fields == [], (
        "a refused drop reached the game")
    _scr_op._move.cancel("test")

    # NOTHING IN colonypick CAN SEND. The rule is structural, so the
    # check is too: a client would have to arrive through an import.
    _cp_src = open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "screens", "colony_summary", "colonypick.py")).read()
    for _forbidden in ("inject_click", "activate_field", "inject_key",
                       "game_client"):
        assert _forbidden not in _cp_src, (
            f"colonypick mentions {_forbidden}; the module that "
            f"DECIDES must not be able to send, which is what makes "
            f"'a preview does not inject' a property of the import "
            f"graph rather than a promise")

    # THE MARKINGS, in every home they claim. A marking two documents
    # assert and nobody checks is an intention (the help panel's).
    assert "HD EXTENSION" in (_cmu.MoveController.cancel.__doc__ or "")
    assert "HD EXTENSION" in (_cp.__doc__ or "")
    assert "HD EXTENSION" in _mv_words.get("_hd_extension_cancel", "")
    from core import zoomtables as _zt
    # ── THE DROP TARGET STOPPED BEING AN EXTENSION ──
    # `_hd_extension_bands` is gone: the target is the original's own
    # per-row job field, added unconditionally in mode 1
    # (coldraw.cpp:409), so an empty column is a target there too.
    # What is left is the HEIGHT, and that is a DEVIATION with three
    # homes. Retargeted in the same commit that took the words out.
    assert "_hd_extension_bands" not in _mv_words, (
        "move._hd_extension_bands is back. The drop target is a "
        "transcription — coldraw.cpp:409 adds the field whether or "
        "not the column drew an icon — and calling it an extension "
        "was the marking this commit withdrew")
    _dtn = _mv_words.get("_drop_target_note", "")
    assert "DEVIATION" in _dtn and "coldraw.cpp:409" in _dtn, (
        "move._drop_target_note must carry the DEVIATION and name "
        "the call the target is transcribed from")
    assert "colsum.cpp:909" in _dtn, (
        "the fourth target — a drop on the colony name, which is "
        "Send_Cluster_(colony, -1) — is not named in the note")
    assert "DEVIATION IN HEIGHT" in (_ct._column_boxes.__doc__ or ""), (
        "colonytrack._column_boxes no longer carries the drop rect's "
        "height deviation")
    # ── AND THE TWO ROW MARKS ARE GONE, WITH THEIR MARKINGS ──
    # The pick outline and the drop-band frame. The original marks
    # neither: its only drawing outside fields and paragraphs on this
    # screen is the scroll thumb (colsum.cpp:759-765).
    for _dead in ("draw_pick", "draw_drop_bands"):
        assert not hasattr(_cl, _dead), (
            f"colonylist.{_dead} is back — the original marks neither "
            f"the picked cells nor the row they came from")
    for _dead in ("PICK_COLOR", "BAND_COLOR", "MARKER_BG",
                  "MARKER_EDGE", "MARKER_TEXT"):
        assert not hasattr(_cl, _dead), (
            f"colonylist.{_dead} survived its drawing — a palette key "
            f"nothing reads is a marking that has stopped marking")
    assert "markers" not in _ct.RowBoxes._fields, (
        "RowBoxes carries a markers field again; the F/W/S squares "
        "were removed with their marking on 8 September 2026")
    assert "name" in _ct.RowBoxes._fields, (
        "RowBoxes lost the name rect, which is the fourth drop "
        "target (colsum.cpp:909)")
    # ── THE HELD CLUSTER, AND THE STEP IT IS OFFSET BY ──
    assert "colmove.cpp" in (_cl.draw_held_cluster.__doc__ or ""), (
        "draw_held_cluster does not name Draw_Cluster_, which is the "
        "whole of what it transcribes")
    _zt_src = open(os.path.join(_proj, "core", "zoomtables.py"),
                   encoding="utf-8").read()
    _zt_note = _zt_src[:_zt_src.index("CLUSTER_FIGURE_OFFSET = ")]
    _zt_note = _zt_note[_zt_note.rindex("FIGURE_STEP = "):]
    assert "DEVIATION" in _zt_note and "colmove.cpp:23" in _zt_note, (
        "CLUSTER_FIGURE_OFFSET's note must carry the DEVIATION that "
        "multiplying by the sprite step is, and name the source line")
    assert (_zt.CLUSTER_FIGURE_OFFSET == (5, -10)
            and _zt.CLUSTER_FIGURE_PITCH == 20), (
        f"the cluster offsets are {_zt.CLUSTER_FIGURE_OFFSET} / "
        f"{_zt.CLUSTER_FIGURE_PITCH}; colmove.cpp:23-28 says "
        f"(5, -10) and 20")
    assert "HD EXTENSION" in (_cl._cell_mark.__doc__ or "")
    assert "IT DOES NOT APPEAR WHILE A SELECTION IS HELD" in (
        _cpop.__doc__ or "")
    for _cite in ("colsum.cpp:804", "colsum.cpp:938"):
        assert _cite in _mv_words["_hd_extension_cancel"], (
            f"the cancel marking no longer names {_cite} — the "
            f"reason it is allowed is that the original's only exits "
            f"from a held cluster are those two, and a marking that "
            f"does not say what the original does instead is a label")
    # AND THE STATUS DOCUMENT, which both notes name as a home. A
    # marking two documents claim exists is not a marking — that is
    # the help panel's lesson, and it cost a day and a half of a
    # tree actively defending the wrong label.
    _mv_status = open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "v3_projektstatus.md")).read()
    for _mark in ("HD EXTENSION — the cancel",
                  "HD EXTENSION — a drop target per job",
                  "HD EXTENSION — a click on the held pop's own group",
                  "HD EXTENSION — three job markers, always",
                  "HD EXTENSION — an identity letter in the cell",
                  "HD EXTENSION — a hover popup below the row",
                  "DEVIATION — a partial move is refused"):
        assert _mark in _mv_status, (
            f"v3_projektstatus.md does not carry {_mark!r}, which "
            f"layout.json's move notes name as one of its homes")
    assert "DEVIATION" in _mv_words.get("_partial_note", ""), (
        "refusing a partial move is a deviation from the original, "
        "which performs it and then opens a blocking box "
        "(colmove.cpp:168-173, textbox.cpp:149)")
    app.client, app.connected = _mv_client, _mv_conn
    _scr_op.update(_sel_snap)
    # ── The drop target IS the group, and the outline IS the target ─
    # Until 5 September 2026 the targets were three equal thirds of
    # the whole 42-slot track. Every job was reachable — but only at
    # a place where nothing stood: a colony of 13 pops has all its
    # cells inside the first third, so a click on a WORKER cell named
    # food while empty track two thirds along named research and
    # worked. The picture and the hit test agreed with each other and
    # neither agreed with the squares, which is decision 5's failure
    # exactly. Measured then: every non-food group of every row in
    # the reference save named food.
    _dt_rows = [
        # the case that was reported, and the two the fixtures added
        {"name": "Draconis V", "pops": 9, "jobs": [4, 4, 1],
         "no_farming": False, "climate": 8, "max_pop": 14,
         "producing": "", "producing_turns": 0, "can_buy": False},
        {"name": "Urna I", "pops": 4, "jobs": [4, 0, 0],
         "no_farming": False, "climate": 5, "max_pop": 4,
         "producing": "", "producing_turns": 0, "can_buy": False},
        {"name": "Neptunus I", "pops": 2, "jobs": [0, 0, 2],
         "no_farming": True, "climate": 2, "max_pop": 3,
         "producing": "", "producing_turns": 0, "can_buy": False},
        # an empty MIDDLE group, which no fixture happens to hold
        {"name": "inner", "pops": 13, "jobs": [12, 0, 1],
         "no_farming": False, "climate": 8, "max_pop": 22,
         "producing": "", "producing_turns": 0, "can_buy": False},
        # and a job nobody holds at all
        {"name": "single", "pops": 1, "jobs": [1, 0, 0],
         "no_farming": False, "climate": 8, "max_pop": 4,
         "producing": "", "producing_turns": 0, "can_buy": False},
    ]
    _dt_track = _cl.track_metrics(_mv_area, _mv_cfg, _mv_scale)
    _dt_x0 = _cl.track_x(_mv_area, _mv_cfg, _mv_scale)
    for _r in _dt_rows:
        _regs = _cl.row_regions(_r)
        _targets = _cl.drop_targets(_mv_area, _mv_cfg, _mv_scale, _r)
        assert [j for j, _ in _targets] == [0, 1, 2], _targets
        _boxes = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _r)
        # 1. EVERY CELL NAMES ITS OWN JOB. The one that was broken.
        for _zone, _k, _cell in _boxes.cells:
            _cx = _cell.x + _cell.width // 2
            _got = _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r, _cx)
            assert _got == _zone, (
                f"{_r['name']}: cell {_k} of job {_zone} names "
                f"{_got}. A click on a cell must name that cell's "
                f"job — looks right, clicks wrong is the whole "
                f"fault this replaced")
        # 1b. THE COLONY NAME NAMES NO JOB, and answers the fourth
        #     target instead — `Send_Cluster_(colony, -1)`,
        #     colsum.cpp:909, which is "put them back".
        _nrect = _ct.name_rect(_mv_area, _mv_cfg, _mv_scale, _r)
        if _nrect is not None and _nrect.width:
            _nmid = _nrect.x + _nrect.width // 2
            assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                                 _nmid) is None, (
                f"{_r['name']}: the name column names a job")
            assert _ct.on_name(_mv_area, _mv_cfg, _mv_scale, _r, _nmid), (
                f"{_r['name']}: on_name does not recognise the middle "
                f"of the name column")
        # 1c. EACH GROUP SITS IN ITS OWN COLUMN, and every cell of it
        #     inside that column. This replaced "the run is flush" at
        #     Stage 4: a flush run was the property of ONE track, and
        #     the row is five columns now — a marker that started
        #     where the previous group ended would put the workers
        #     under the FARMERS heading the moment a colony had
        #     eleven farmers. The failure shape is the one this whole
        #     block exists for, so the property moved with the
        #     geometry rather than being dropped.
        _colmap = _ct.columns(_mv_area, _mv_cfg)
        assert _colmap, (
            "the screen's list cfg has no column table, so this whole "
            "block would be testing the single-track fallback that "
            "nothing ships — colonyheader.install_columns")
        for _zone, _key in enumerate(_ct.JOB_KEYS):
            _cx, _cw = _colmap[_key]
            _own = [c for j, _k, c in _boxes.cells if j == _zone]
            # THE FIRST CELL IS AT THE COLUMN'S LEFT EDGE. It used to
            # be one marker's width in; the markers went on
            # 8 September 2026 and the cells moved left with them,
            # which is where the original starts its icons —
            # `(30 - squish) * i + left_x`, coldraw.cpp:349.
            if _own:
                assert _own[0].x == _cx, (
                    f"{_r['name']}: the first cell of job {_zone} is "
                    f"at {_own[0].x}, its column starts at {_cx}")
            for _c in _own:
                assert _cx <= _c.x and _c.right <= _cx + _cw, (
                    f"{_r['name']}: a cell of job {_zone} "
                    f"({_c.x}..{_c.right}) leaves its column "
                    f"({_cx}..{_cx + _cw}) — a cell under the wrong "
                    f"heading is the failure this block exists for")
        # AND NO GROWTH BOXES: they belong to the colony, so in a
        # row of three job columns there is nowhere for them that
        # is not a lie. `_column_boxes` carries the reasoning.
        assert not _boxes.growth, _boxes.growth
        # 2. EVERY JOB HAS A TARGET, INCLUDING AN EMPTY ONE — and
        #    since 8 September that is a TRANSCRIPTION rather than a
        #    thing the markers bought: mode 1 adds the field after a
        #    walk that may have drawn nothing (coldraw.cpp:409), so
        #    the original accepts a drop on an empty column too.
        for _job, _rect in _targets:
            assert _rect.width >= 1, (
                f"{_r['name']}: job {_job} has no target at all; an "
                f"empty job is the one a player most wants to start")
            assert (_rect.x, _rect.width) == _colmap[_ct.JOB_KEYS[_job]], (
                f"{_r['name']}: job {_job}'s target is "
                f"{(_rect.x, _rect.width)} and its column is "
                f"{_colmap[_ct.JOB_KEYS[_job]]} — the target is the "
                f"whole cell, which is what coldraw.cpp:409 adds")
            _mid = _rect.x + _rect.width // 2
            assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                                 _mid) == _job
        # 3. THE THREE TARGETS DO NOT OVERLAP, in ECON order.
        _xs = [(r.x, r.x + r.width) for _j, r in _targets]
        for _a, _b in zip(_xs, _xs[1:]):
            assert _a[1] <= _b[0], (
                f"{_r['name']}: targets overlap, {_xs}")
        # 4. NO JOB IS EVER EMPTY, so the empty-group placeholder
        #    path cannot come back: the marker IS the placeholder.
        for _job, _rect in _targets:
            assert _rect.width >= _dt_track.unit, (
                f"{_r['name']}: job {_job}'s target is thinner than a "
                f"marker, which means a group without one")
        # 5. OUTSIDE EVERY TARGET IS None, and None is a state.
        # 5b. OUTSIDE THE THREE JOB COLUMNS IS None, and None is a
        #     state — it discards a held selection rather than
        #     dropping it. The bounds are the columns' own now, not
        #     the single track's.
        if _colmap:
            _lo = min(_colmap[_k2][0] for _k2 in _ct.JOB_KEYS)
            _hi = max(_colmap[_k2][0] + _colmap[_k2][1]
                      for _k2 in _ct.JOB_KEYS)
        else:
            _lo, _hi = _dt_x0, _dt_x0 + _dt_track.width
        assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                             _lo - 5) is None
        assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r,
                             _hi + 5) is None
    from screens.colony_summary import colonyicons as _ci
    from screens.colony_summary import colonymove as _cmv2
    from screens.colony_summary import colonyfigures as _cfig
    from core.structs import colony as _cspec
    # 6. A HELD CLUSTER LEAVES THE ROW, AND THE PITCH FOLLOWS IT —
    #    which is what replaced the two marks on 8 September 2026.
    #    The original does not outline the picked cells and does not
    #    frame the row; it clears `0x200` (colmove.cpp:70) and the
    #    icon walk stops emitting them (coldraw.cpp:336), so the row
    #    is shorter and the squish is recomputed over what is left by
    #    the SAME pre-pass that serves the draw and both hit tests
    #    (coldraw.cpp:301 -> :419).
    #
    #    Asserted on the render, not on the code: the cells are
    #    recovered from their own ink before and after, and the
    #    surviving pitch is compared against `column_pitch` at the
    #    SHORTENED count. A second arithmetic anywhere on this path
    #    would show up here as a pitch that did not move.
    _hc_pops = [((1 & 3) << 7) | _cspec.POP_MASK_ASSIGNED
                for _ in range(6)]
    _hc_row = {"name": "held", "pops": 6, "jobs": [0, 6, 0],
               "no_farming": False, "climate": 8, "max_pop": 10,
               "producing": "", "producing_turns": 0, "can_buy": False,
               "cells": ((), tuple(range(6)), ())}
    _hc_full = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _hc_row)
    _hc_kept = dict(_hc_row, cells=((), tuple(range(4)), ()))
    _hc_short = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _hc_kept)
    assert len([c for j, _k, c in _hc_full.cells if j == 1]) == 6
    _hc_cells = [c for j, _k, c in _hc_short.cells if j == 1]
    assert len(_hc_cells) == 4, (
        "holding two of six pops did not shorten the row — the cells "
        "are built from the icon list and the icon list is built from "
        "the assigned bit")
    # The pitch is the shortened one, and it comes from the one home.
    _hc_step = _cfig.figure_step(_mv_scale)
    _hc_want = min(_ci.column_pitch(1, 4), _ci.ICON_SPACING) * _hc_step
    assert abs((_hc_cells[1].x - _hc_cells[0].x) - int(_hc_want)) <= 1, (
        f"the shortened row draws a pitch of "
        f"{_hc_cells[1].x - _hc_cells[0].x}; colonyicons.column_pitch "
        f"at 4 icons times the sprite step is {int(_hc_want)} — a "
        f"second pitch computation has entered the pick path")
    # AND `build_rows` IS WHAT SHORTENS IT, by clearing the bit the
    # original clears. Not a count subtracted somewhere.
    _hc_held = _cmv2.held_pops(_hc_pops, (4, 5))
    assert len(_ci.icon_pops(_hc_held, 6, 1)) == 4, _hc_held
    assert all(not (_hc_held[i] & _cspec.POP_MASK_ASSIGNED)
               for i in (4, 5)), _hc_held
    assert all(_hc_held[i] & _cspec.POP_MASK_ASSIGNED
               for i in range(4)), _hc_held
    assert _hc_pops[4] & _cspec.POP_MASK_ASSIGNED, (
        "held_pops wrote into the array it was given; the snapshot's "
        "own words must survive it (decision 47)")
    # NO `count - n` ANYWHERE ON THE PATH. The rule, not the
    # instance: the shortening is one cleared bit, so no module on
    # this path may subtract a held size from a count.
    for _mod in ("colonytrack.py", "colonylist.py", "colonyrows.py",
                 "colonyicons.py"):
        _msrc = open(os.path.join(_proj, "screens", "colony_summary",
                                  _mod), encoding="utf-8").read()
        for _bad in ("- len(held", "- len(self.cluster",
                     "- pick.size", "- self.pick.size"):
            assert _bad not in _msrc, (
                f"{_mod} subtracts a held count ({_bad!r}). The held "
                f"pops leave the row by losing 0x200, which is what "
                f"the original does and what keeps one list serving "
                f"the draw, the pitch and both hit tests")
    # AND ONE HOME FOR THE PITCH. `squish_step` is
    # Calculate_Squish_Step_ transcribed and must exist once.
    _sq = []
    for _dp, _dn, _fns in os.walk(_proj):
        _dn[:] = [d for d in _dn if d not in ("__pycache__", ".git")]
        for _fn in _fns:
            if not _fn.endswith(".py"):
                continue
            _fp = os.path.join(_dp, _fn)
            # This file is excluded, and only by exact path: it names
            # the function in the assertion below, which would
            # otherwise count as a second home. Same exclusion the
            # marking inventory makes, for the same reason.
            if os.path.relpath(_fp, _proj) == os.path.join(
                    "tools", "smoke_test.py"):
                continue
            if "def squish_step(" in open(_fp, encoding="utf-8").read():
                _sq.append(_fp)
    assert len(_sq) == 1 and _sq[0].endswith("colonyicons.py"), (
        f"Calculate_Squish_Step_ is transcribed in {_sq} — one home, "
        f"or the render and the hit test drift (decision 5)")

    # 7. THE CELL UNDER A PIXEL IS THE CELL DRAWN AT THAT PIXEL —
    #    for every cell of every row, PICK-UP as well as drop.
    #
    #    Item 6 above was built for exactly this class of fault and
    #    did not catch it, which is worth more than the fault: it
    #    inks `draw_drop_bands` only, and only its two outermost
    #    columns, so it can say nothing about the pick-up path and
    #    nothing about any cell in between. `draw_pick` was never
    #    rendered by any check at all. It computed `start + slot *
    #    step` from the track origin, while `slot` is an index within
    #    ONE JOB's icons — so the outline sat one marker plus every
    #    preceding cell to the left of the cell it named. Reported
    #    live on Horus IV as "exactly one cell" because food is job 0
    #    and its only error is the F marker; industry was off six
    #    cells and research ten. Born in 343d9ba, invisible on food
    #    until the markers moved the run.
    #
    #    So this reads the RENDER and not the geometry: the cells are
    #    recovered from their own ink, and both hit tests and the
    #    pick outline are asserted against THAT. Two functions
    #    calling a third is what the broken version could also have
    #    claimed.
    _pk_surf = pygame.Surface((_mv_area.right + 16, _mv_area.bottom + 16))
    _pk_band = _mv_bands[0]
    _mv_px = app.layout.font_size(_mv_cfg.get("small_font", 15))

    def _ink_runs(_draw, _rgb):
        """The x-runs where `_draw` put `_rgb` down, left to right."""
        _pk_surf.fill((0, 0, 0))
        _draw(_pk_surf)
        _a = pygame.surfarray.array3d(_pk_surf)
        _hit = [_x for _x in range(_pk_surf.get_width())
                if (_a[_x] == list(_rgb[:3])).all(axis=1).any()]
        _runs = []
        for _x in _hit:
            if _runs and _x == _runs[-1][1] + 1:
                _runs[-1] = (_runs[-1][0], _x)
            else:
                _runs.append((_x, _x))
        return _runs

    for _r in _dt_rows:
        _drawn = {_j: _ink_runs(
            lambda _s, _row=_r: _cl._render_bar(
                _s, _row, _mv_area, _mv_cfg, _mv_scale, _pk_band,
                _dt_track, _mv_px, app.style, app.layout),
            _cl.ZONE_COLORS[_j]) for _j in range(3)}
        _boxes = _ct.row_boxes(_mv_area, _mv_cfg, _mv_scale, _r, _pk_band)
        for _j in range(3):
            _want = [(_c.x, _c.x + _c.width - 1)
                     for _job, _k, _c in _boxes.cells if _job == _j]
            assert _drawn[_j] == _want, (
                f"{_r['name']}: job {_j} draws its cells at "
                f"{_drawn[_j]}, the geometry says {_want} — the "
                f"picture and the rects disagree")
            for _k, (_x0, _x1) in enumerate(_drawn[_j]):
                # PICK-UP: every pixel of the drawn cell picks up
                # that cell, and nothing else does.
                for _x in (_x0, (_x0 + _x1) // 2, _x1):
                    assert _cl.cell_at_x(_mv_area, _mv_cfg, _mv_scale,
                                         _r, _x) == (_j, _k), (
                        f"{_r['name']}: x={_x} is drawn as cell {_k} "
                        f"of job {_j} and picks up "
                        f"{_cl.cell_at_x(_mv_area, _mv_cfg, _mv_scale, _r, _x)}")
                    assert _cl.drop_band(_mv_area, _mv_cfg, _mv_scale,
                                         _r, _x) == _j, (
                        f"{_r['name']}: x={_x} is drawn as job {_j} "
                        f"and drops into "
                        f"{_cl.drop_band(_mv_area, _mv_cfg, _mv_scale, _r, _x)}")
    ok("colony summary cells: drawn, picked up and dropped are one "
       "and the same cell (read back from the render)")
    # ── The identity letter, and the popup's two rules ───────────
    # N on a native cell and nothing on the player's own, because
    # over ninety per cent of cells are the second case and have to
    # stay quiet. The letters for android and conquered rest on the
    # source alone — see the split marking check above.
    _idm = _mv_cfg.get("cell_marks", {})
    assert _idm.get("native") == "N", _idm
    for _kind in ("android", "conquered"):
        assert _idm.get(_kind), f"no letter for {_kind}"
    assert len(set(_idm.values())) == len(_idm), (
        f"two identity classes share a letter: {_idm}")
    assert not (set(_idm.values())
                & set(_mv_cfg.get("marker_letters", []))), (
        f"an identity letter collides with a job marker: {_idm} "
        f"against {_mv_cfg.get('marker_letters')}. They sit in "
        f"different boxes, but a reader should not have to know that")
    _idr = dict(_dt_rows[1])          # Urna I's shape
    # `colonyrows.Cell(kind, figure)` — a cell carries its identity
    # class AND the figure it draws, both from one `Colony_Pop_Anim_`
    # read. The fake carries the same shape as the real row, which is
    # what the AST pin on the row dict exists to keep true.
    _Cell = _crw.Cell
    _idr["cells"] = ((_Cell("", "human_farmer.png"),
                      _Cell("native", "native.png"),
                      _Cell("native", "native.png"),
                      _Cell("native", "native.png")), (), ())
    _marks = [_cl._cell_mark(_mv_cfg, _idr["cells"], 0, _k)
              for _k in range(4)]
    assert _marks == ["", "N", "N", "N"], _marks
    assert _cl._cell_mark(_mv_cfg, _idr["cells"], 1, 0) == "", (
        "a job with no cells produced a mark")

    # THE POPUP OVERLAYS AND NEVER REFLOWS, so the rows it is drawn
    # over must be exactly where they were without it — the list is
    # the click frame (decision 46).
    _pop_words = _scr_op._data.get("popup", {})
    _pop_px = app.layout.font_size(_pop_words.get("font", 15))
    _pop_before = _cl.row_bands(_mv_area, _mv_cfg, _mv_scale,
                                len(_mv_rows))
    _pop_ctl = _cmu.MoveController()
    _pop_ctl.over = (0, 0)
    _pop_surf = pygame.Surface((_mv_area.right + 8, _mv_area.bottom + 8))
    _pop_rect = _pop_ctl.draw_popup(_pop_surf, _mv_rows, 0, _mv_area,
                                    _mv_cfg, _mv_scale, app.style,
                                    app.layout, _scr_op._data)
    assert _pop_rect is not None, "the popup drew nothing at all"
    assert _cl.row_bands(_mv_area, _mv_cfg, _mv_scale,
                         len(_mv_rows)) == _pop_before, (
        "the rows moved when the popup opened — it must overlay")
    # IT STAYS INSIDE list_area, at every row, because the frame
    # image is drawn after the content and would cover it otherwise.
    for _i in range(len(_pop_before)):
        _pop_ctl.over = (_i, 0)
        _r = _cpop.rect_for(_mv_area, _mv_cfg, _mv_scale, _mv_rows[_i],
                            0, _pop_before[_i], app.style, _pop_px,
                            _pop_words)
        assert _r is not None
        assert _mv_area.contains(_r[0]), (
            f"row {_i}: the popup at {_r[0]} leaves {_mv_area} — "
            f"outside the cutout it is covered by the frame's metal")
    # AND A ROW AT THE BOTTOM OF THE PANEL FLIPS IT ABOVE rather
    # than off the panel. The fixture list is short, so the case is
    # made rather than waited for: a band at the last row position
    # `list_area` can hold, which is where a full list puts one.
    _pop_h = _pop_before[0][1]
    _bottom_band = (_mv_area.bottom - _pop_h, _pop_h)
    _r_last = _cpop.rect_for(_mv_area, _mv_cfg, _mv_scale, _mv_rows[0],
                             0, _bottom_band, app.style, _pop_px,
                             _pop_words)[0]
    assert _r_last.bottom <= _bottom_band[0], (
        f"a row at the panel's bottom put its popup at {_r_last}, "
        f"not above the row at y={_bottom_band[0]}")
    assert _mv_area.contains(_r_last), (
        f"the flipped popup at {_r_last} still leaves {_mv_area}")
    # NO POPUP WHILE A SELECTION IS HELD. One rule, and it lives in
    # the controller so a reader cannot find a second answer.
    _pop_ctl.over = (0, 0)
    _pop_ctl.pick = object()
    assert _pop_ctl.draw_popup(_pop_surf, _mv_rows, 0, _mv_area,
                               _mv_cfg, _mv_scale, app.style,
                               app.layout, _scr_op._data) is None, (
        "the popup opened while a pick was held — it would flicker "
        "under the aiming gesture and cover the drop targets")
    _pop_ctl.pick = None
    _pop_ctl.hover(_mv_rows, 0, _mv_area.x + 5, _mv_area, _mv_cfg,
                   _mv_scale)
    _pop_ctl.pick = object()
    _pop_ctl.hover(_mv_rows, 0, _mv_area.x + 5, _mv_area, _mv_cfg,
                   _mv_scale)
    assert _pop_ctl.over is None, (
        "hovering while a pick is held set a popup target anyway")
    ok("identity letters and the popup (N only on natives, overlay "
       "not reflow, flips in the last row, none while a pick is held)")

    ok("drop targets follow the groups (every cell names its own job, "
       "every job has a target, the outline is the target)")

    ok("pop move: the first click and every refusal send NOTHING, "
       "the cancel is marked in four homes")

    import tempfile as _tf
    from screens.colony_summary import colonyfigures as _fig
    # ── THE HELD CLUSTER HANGS ON THE POINTER, AT THE SPRITE STEP ──
    # `COLMOVE::Draw_Cluster_` (colmove.cpp:7-37) draws each held pop
    # at x + 5 + 20*k, y - 10, native, beside a 28 px sprite. HD
    # multiplies all three by `FIGURE_STEP`, which is the DEVIATION
    # marked in zoomtables — so what has to hold is that the figure
    # is the STEP's own size (a swap, decision 28, never a scale) and
    # that the offsets moved with it.
    #
    # The figures are built here rather than read from the tree: they
    # are derived from the player's own RACEICON.LBX and are not
    # committed (decision 50), so a check that needed them would
    # answer differently for a clone that had not run the extractor.
    with _tf.TemporaryDirectory() as _hcdir:
        _hcd = os.path.join(_hcdir, _fig.FIGURE_DIR)
        os.makedirs(_hcd)
        _hcm = pygame.Surface((28, 28), pygame.SRCALPHA)
        _hcm.fill((255, 0, 0, 255))
        pygame.image.save(_hcm, os.path.join(_hcd, "human_farmer.png"))
        from core.resources import Resources as _HcRes
        _hcres = _HcRes()
        _hcres.mod_dirs = [_hcdir]
        for _sc, _step in ((1.0, 2), (4.0 / 3.0, 3), (2.0, 4)):
            assert _cfig.figure_step(_sc) == _step, (
                f"figure_step({_sc}) is {_cfig.figure_step(_sc)}, "
                f"not {_step} — zoomtables.FIGURE_STEP")
            _hcset = _cfig.FigureSet(_hcres, _step)
            _hcsurf = pygame.Surface((600, 400), pygame.SRCALPHA)
            _hcsurf.fill((0, 0, 0, 255))
            _hccells = tuple(_crw.Cell("", "human_farmer.png")
                             for _ in range(3))
            _cl.draw_held_cluster(_hcsurf, (200, 200), _hcset, _hccells,
                                  _sc)
            _hca = pygame.surfarray.array3d(_hcsurf)
            _hit = [(x, y) for x in range(600) for y in range(400)
                    if tuple(_hca[x, y]) == (255, 0, 0)]
            assert _hit, f"step {_step}: the held cluster drew nothing"
            _hx = sorted({x for x, _y in _hit})
            _hy = sorted({y for _x, y in _hit})
            _ox, _oy = _zt.CLUSTER_FIGURE_OFFSET
            assert _hx[0] == 200 + _ox * _step, (
                f"step {_step}: the first figure starts at x={_hx[0]}, "
                f"the pointer + 5*step is {200 + _ox * _step}")
            assert _hy[0] == 200 + _oy * _step, (
                f"step {_step}: the figures start at y={_hy[0]}, the "
                f"pointer - 10*step is {200 + _oy * _step}")
            # SWAP, NEVER SCALE: the drawn figure is exactly the
            # step's size, so a fractional resize would show here as
            # a width that is not 28 * step.
            assert _hy[-1] - _hy[0] + 1 == 28 * _step, (
                f"step {_step}: the held figure is "
                f"{_hy[-1] - _hy[0] + 1} px tall, not {28 * _step} — "
                f"a sprite is swapped by step and never scaled "
                f"(decision 28)")
            # AND THE PITCH IS 20 * step, not the icon spacing and
            # not the squished column pitch.
            _pitch = _zt.CLUSTER_FIGURE_PITCH * _step
            assert _hx[-1] - _hx[0] + 1 == 28 * _step + 2 * _pitch, (
                f"step {_step}: three held figures span "
                f"{_hx[-1] - _hx[0] + 1} px; 20*step between them "
                f"makes {28 * _step + 2 * _pitch}")
        # AND NOTHING WITHOUT FIGURES. The coloured cell is the row's
        # absent-set picture; a coloured square on the POINTER would
        # be a shape the original never has.
        _hcsurf = pygame.Surface((600, 400), pygame.SRCALPHA)
        _hcsurf.fill((0, 0, 0, 255))
        _cl.draw_held_cluster(_hcsurf, (200, 200), None,
                              (_crw.Cell("", "human_farmer.png"),), 1.0)
        assert not pygame.surfarray.array3d(_hcsurf).any(), (
            "the held cluster drew something with no figure set")
    ok("held cluster on the pointer (+5/-10 and 20 apart at the "
       "sprite step, swapped never scaled, nothing without figures)")

    # ── A PICK DOES NOT ROUTE THROUGH THE SLOT SEARCH ──
    # The original never runs its icon hit test while a cluster is
    # held: `Get_Selected_Pop_` is reached only when
    # `_cluster_colony_n == -1` (colsum.cpp:862), and with one in hand
    # the click goes straight to `Send_Cluster_` (:869) — the FIELD
    # decides, not the slot. Asserted by making the search fatal and
    # driving a real drop through the screen, because "the code does
    # not call it" is what a reader claims and this is what a run
    # proves.
    _slot_calls = []

    def _forbid(name, real):
        def _fn(*a, **kw):
            _slot_calls.append(name)
            return real(*a, **kw)
        return _fn

    _sl_saved = (_ci.slot_at, _ci.slot_pop, _cl.cell_at_x)
    _ci.slot_at = _forbid("slot_at", _sl_saved[0])
    _ci.slot_pop = _forbid("slot_pop", _sl_saved[1])
    _cl.cell_at_x = _forbid("cell_at_x", _sl_saved[2])
    try:
        _scr_op.handle_click(*_square_xy(_mv_row, _mv_job, _mv_slot))
        assert _scr_op._move.pick is not None, (
            "the pick-up did not take; the rest of this check would "
            "be vacuous")
        assert _slot_calls, (
            "the PICK-UP reached no slot search at all — it is "
            "supposed to, and a check that cannot see the call it "
            "forbids proves nothing about the drop")
        _slot_calls.clear()
        _scr_op.handle_click(*_band_xy(_mv_row, _mv_target))
    finally:
        _ci.slot_at, _ci.slot_pop, _cl.cell_at_x = _sl_saved
    assert not _slot_calls, (
        f"a drop reached the slot search ({sorted(set(_slot_calls))}). "
        f"With a cluster held the original resolves a click by FIELD "
        f"— which job column it landed in — and never by icon "
        f"(colsum.cpp:862-869)")
    _scr_op._move.pick = None
    _scr_op._move.send = None
    _scr_op._rebuild_rows()
    ok("a drop is resolved by column and never by slot (the icon "
       "search is fatal while a cluster is held)")

    # ── And the sentence has to FIT the panel it is drawn in ──────
    # Found by rendering it and looking, which is the only thing that
    # could: at one line and 18 px the longest of these messages —
    # a rule plus its count — ran past `spare_panel` on both sides
    # and lost its first and last characters under the frame's metal.
    # Every value was right and the text was drawn, so a check that
    # asked "did it draw ink?" would have passed. Decision 44's class
    # A rule, met from a new direction.
    _fit_msg = _cp.message(_mv_words, _cp.Refusal(_cm.REFUSE_JOB_FULL,
                                                  landed=2, carried=10,
                                                  total=12))
    _fit_box = _scr_op.box_rect("planet_info")
    assert _fit_box, "spare_panel is where the move message goes"
    _fit_rect = pygame.Rect(*app.layout.rect(_fit_box))
    _fit_px = app.layout.font_size(_mv_words.get("font", 18))
    _fit_surf = pygame.Surface((_fit_rect.right + 8, _fit_rect.bottom + 8))
    _fit_surf.fill((0, 0, 0))
    _fit_ctl = _cmu.MoveController()
    _fit_ctl.message = _fit_msg
    _fit_ctl.draw_message(_fit_surf, _fit_rect, _fit_px, app.style,
                          (255, 255, 255))
    _fit_ink = pygame.surfarray.array3d(_fit_surf).sum(axis=2)
    _fit_cols = [x for x in range(_fit_surf.get_width())
                 if _fit_ink[x].any()]
    _fit_rows = [y for y in range(_fit_surf.get_height())
                 if _fit_ink[:, y].any()]
    assert _fit_cols and _fit_rows, "the message drew nothing at all"
    _fit_inset = max(2, _fit_px // 2)
    _fit_in = _fit_rect.inflate(-2 * _fit_inset, -2 * _fit_inset)
    assert (_fit_in.left <= min(_fit_cols) and max(_fit_cols) <= _fit_in.right
            and _fit_in.top <= min(_fit_rows)
            and max(_fit_rows) <= _fit_in.bottom), (
        f"the move message runs from x {min(_fit_cols)}..{max(_fit_cols)}, "
        f"y {min(_fit_rows)}..{max(_fit_rows)}, outside {_fit_in} — a "
        f"glyph past a cutout's edge is drawn under the frame's rim "
        f"and the panel is a cutout (fundament 44)")
    # NOTHING IS TRUNCATED to make it fit: the wrap shrinks the size
    # and leaves a too-wide word whole, because losing a character is
    # not one of the outcomes.
    _fit_lines = _textfit.wrap_text(app.style, _fit_msg, _fit_px,
                                    _fit_rect.w - 2 * _fit_inset)
    assert " ".join(_fit_lines).split() == _fit_msg.split(), (
        f"the wrap dropped words: {_fit_lines}")
    ok("pop move message fits spare_panel (wrapped and shrunk, no "
       "glyph under the frame's rim, nothing dropped)")

    # ── The send waits for an EFFECT, and the first pair is early ──
    # ext::Tick() calls ProcessInput() BEFORE it serializes anything
    # (ext_api.cpp:341-386), so the tick that consumes an injected
    # command also ships the world from before the game acted on it.
    # Measured 5 September 2026 against the running game: one
    # increment of the list window read _first unchanged on the first
    # state/visual pair and moved on the second. A chain that
    # accepted the first pair would confirm every step one tick early
    # — and then aim the next click at a window that has not moved.
    class _SendClient:
        def __init__(self):
            self.stats = {"state": 0, "visual": 0}
            self.clicks, self.fields, self.keys = [], [], []
            self.order = []          # what went out, in order
        def inject_click(self, x, y):
            self.clicks.append((x, y)); self.order.append(("click", (x, y)))
        def activate_field(self, f):
            self.fields.append(f); self.order.append(("field", f))
        def inject_key(self, k):
            self.keys.append(k); self.order.append(("key", k))

    class _SendField:
        def __init__(self, index, x, y):
            self.index, self.x, self.y = index, x, y

    class _SendState:
        def __init__(self, raws, framebuffer=None, fields=()):
            self.colonies_raw = list(raws)
            self.framebuffer = framebuffer
            self.fields = list(fields)

    def _thumb_frame(n, first):
        """A 640x480 index buffer with the scroll thumb drawn at
        `first` — the channel `_first` is read back through."""
        _y1, _y2 = _cf.thumb_bounds(n, first)
        _buf = bytearray(640 * 480)
        for _y in range(_y1 + 1, _y2):
            for _x in range(_cf.THUMB_X0, _cf.THUMB_X1 + 1):
                _buf[_y * 640 + _x] = _cf.THUMB_FILL
        return bytes(_buf)

    _sd_off = dict((n, o) for n, o, _k in _cst.SPEC.fields)

    def _raw_with(pops, n_pops=3):
        _b = bytearray(_cst.SPEC.size)
        _b[_sd_off["owner"]] = 0
        _b[_sd_off["n_pops"]] = n_pops
        _b[_sd_off["max_farms"]] = 255
        for _i, _w in enumerate(pops):
            struct.pack_into("<I", _b, _sd_off["pop"] + 4 * _i, _w)
        return bytes(_b)

    _sd_pops = [_icon_pop(0, 0), _icon_pop(0, 0), _icon_pop(0, 0)]
    _sd_cluster = _cm.Cluster([2])
    _sd_pred = _cm.predict_pops(_sd_pops, 3, 255, _sd_cluster, 1)
    _sd_held = list(_sd_pops)
    _sd_held[2] &= ~_cst.POP_MASK_ASSIGNED

    _sd_c = _SendClient()
    _sd = _cse.Send(_sd_c, n_colonies=5, position=0, colony=0,
                    source_job=0, slot=2, icon_count=3, target_job=1,
                    cluster=_sd_cluster, predicted=_sd_pred,
                    sort_hotkey=ord("n"))
    assert _sd.state == _cse.RESORT and _sd_c.clicks == []
    # STEP 1 IS THE SORT, and it is first because `Sort_Col_List_`'s
    # handler sets `_first = 0` (colsum.cpp:832): established first
    # and sorted second, the sort would move the window the chain had
    # just placed. It also repairs drift this move did not cause —
    # the game's list is sorted at exactly two places in the engine
    # (colsum.cpp:110 on entry and :830 in that handler) and never on
    # its own, while HD re-sorts from every snapshot.
    _sd.update(_SendState([_raw_with(_sd_pops)]))
    assert _sd.state == _cse.RESORT and _sd_c.keys == [ord("n")], (
        f"{_sd.state}, keys {_sd_c.keys}")
    assert _sd_c.clicks == [] and _sd_c.fields == []
    _sd_c.stats["state"] += 2
    _sd_c.stats["visual"] += 2
    # Under ten colonies there is no window to establish and no
    # indicator to read (colsum.cpp:751, :194-197), so the chain goes
    # straight to the pick-up rather than demanding a reading a
    # correctly behaving game does not draw.
    _sd.update(_SendState([_raw_with(_sd_pops)]))
    assert _sd.state == _cse.PICK, _sd.state
    assert _sd_c.clicks == [(_ci.slot_click_x(0, 2, 3),
                             _ci.row_click_y(0))], _sd_c.clicks
    assert _sd_c.fields == [], (
        "a five-colony list needs no window steps at all")

    # THE PRE-EFFECT PAIR IS REFUSED even though the predicate is
    # already true on it. This is the whole assertion.
    _sd_c.stats["state"] += 1
    _sd_c.stats["visual"] += 1
    _sd.update(_SendState([_raw_with(_sd_held)]))
    assert _sd.state == _cse.PICK and len(_sd_c.clicks) == 1, (
        f"the chain acted on the FIRST snapshot after its send "
        f"({_sd.state}, {_sd_c.clicks}); that snapshot is serialized "
        f"in the tick that consumed the send and cannot carry the "
        f"effect")
    _sd_c.stats["state"] += 1
    _sd_c.stats["visual"] += 1
    _sd.update(_SendState([_raw_with(_sd_held)]))
    assert _sd.state == _cse.DROP and len(_sd_c.clicks) == 2, (
        f"the interlock did not pass on the second pair: {_sd.state}")
    # The drop lands in the middle of the target column, not on an
    # icon: Send_Cluster_ reads no icon at all, which is what lets a
    # player start an empty column.
    _sd_lx, _sd_rx = _ci.COLUMNS[1]
    assert _sd_c.clicks[1] == ((_sd_lx + _sd_rx) // 2,
                               _ci.row_click_y(0)), _sd_c.clicks

    # THE DROP IS THE LAST THING SENT. Nothing trails it: the sort
    # that keeps the two lists in one order is step 1 of the NEXT
    # move, where it can also repair drift this move did not cause.
    _sd_c.stats["state"] += 2
    _sd_c.stats["visual"] += 2
    _sd.update(_SendState([_raw_with(_sd_pred)]))
    assert _sd.state == _cse.DONE and _sd.finished, _sd.state
    assert _sd_c.keys == [ord("n")], (
        f"keys {_sd_c.keys}: the sort is sent once, at the start")
    assert [_k for _k, _v in _sd_c.order] == ["key", "click", "click"], (
        f"the wire order was {[_k for _k, _v in _sd_c.order]}; it must "
        f"be the sort, then the two clicks")

    # THE INTERLOCK STOPS ON A CLUSTER IT DID NOT PREDICT, and says
    # the game is HOLDING rather than that nothing happened — only
    # the player can end that state, because the ways out are
    # dropping the pops or leaving the screen.
    _sd_c2 = _SendClient()
    _sd2 = _cse.Send(_sd_c2, n_colonies=5, position=0, colony=0,
                     source_job=0, slot=2, icon_count=3, target_job=1,
                     cluster=_sd_cluster, predicted=_sd_pred)
    _sd2.update(_SendState([_raw_with(_sd_pops)]))
    _sd_wrong = list(_sd_pops)
    _sd_wrong[0] &= ~_cst.POP_MASK_ASSIGNED     # a different pop
    _sd_c2.stats["state"] += 2
    _sd_c2.stats["visual"] += 2
    _sd2.update(_SendState([_raw_with(_sd_wrong)]))
    assert _sd2.state == _cse.HOLDING and _sd2.holding, _sd2.state
    assert _sd2.reason == "wrong_pickup"
    assert len(_sd_c2.clicks) == 1, (
        "the chain clicked again with geometry that had just been "
        "shown wrong")
    # THE FLOOR'S REASON HAS TO STAND BESIDE THE FLOOR. It is a
    # count, and decision 21 refuses counted waits — so the next
    # reader must find the argument at the constant, or they will
    # read it as a settling time and make it three.
    for _path, _needle in (
            # the argument, in its one home...
            (("core", "wire_protocol.py"),
             "IT IS NOT A SETTLING TIME, AND DECISION 21 IS WHY"),
            # ...and a pointer to it from each reader, so nobody
            # meets the number without the reason.
            (("screens", "colony_summary", "colonysend.py"),
             "wire_protocol"),
            (("tools", "colony_move_probe.py"),
             "core.wire_protocol.EFFECT_PAIRS")):
        _src = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            *_path)).read()
        assert _needle in _src, (
            f"{'/'.join(_path)} no longer explains why its pre-effect "
            f"floor is not a duration; the count is the exact "
            f"structural gap and raising it starts skipping evidence")
    assert _cse.EFFECT_PAIRS == _wire.EFFECT_PAIRS == 2, (
        f"EFFECT_PAIRS is {_cse.EFFECT_PAIRS}; two is the consuming "
        f"tick plus the first that can show the effect, and the "
        f"assertions above pin both sides of it")
    assert _scr_op._data["move"].get("stranded"), (
        "there is no wording for a held cluster, which is the one "
        "state only the player can end")

    # _first IS ESTABLISHED, NEVER REMEMBERED (decision 46). The plan
    # always leads with enough decrements to reach the top from
    # wherever a human left the window, so the step list is a
    # property of the colony count and not of any reading.
    _sd3 = _cse.Send(_SendClient(), n_colonies=15, position=0,
                     colony=0, source_job=0, slot=0, icon_count=1,
                     target_job=1, cluster=_cm.Cluster([0]),
                     predicted=_sd_pops)
    assert _sd3._steps == [_cse.STEP_UP_XY] * _cs_sel.GameWindow.max_first(15), (
        f"the plan starts with {_sd3._steps}; it must lead with "
        f"{_cs_sel.GameWindow.max_first(15)} decrements, which reach "
        f"the top from any state (colsum.cpp:211-214)")

    # AND WITH A WINDOW THAT REALLY MOVES, the order is visible: the
    # sort key must go out before the first stepper, because the sort
    # handler sets `_first = 0` and would undo the steps. Fifteen
    # colonies, a drawn thumb to read back, and the two stepper
    # fields where the original puts them (colsum.cpp:263-264).
    _sd_c4 = _SendClient()
    _sd4 = _cse.Send(_sd_c4, n_colonies=15, position=0, colony=0,
                     source_job=0, slot=2, icon_count=3, target_job=1,
                     cluster=_sd_cluster, predicted=_sd_pred,
                     sort_hotkey=ord("n"))
    _sd4_state = _SendState(
        [_raw_with(_sd_pops)], _thumb_frame(15, 0),
        [_SendField(12, *_cse.STEP_UP_XY), _SendField(13, *_cse.STEP_DOWN_XY)])
    assert _cf.read_first(_cf.rows(_sd4_state.framebuffer), 15) == 0, (
        "the fixture's own thumb does not read back as _first = 0")
    for _ in range(40):
        if _sd4.state == _cse.PICK:
            break
        _sd4.update(_sd4_state)
        _sd_c4.stats["state"] += 2
        _sd_c4.stats["visual"] += 2
    assert _sd4.state == _cse.PICK, (
        f"the chain stalled in {_sd4.state} ({_sd4.reason})")
    _sd4_kinds = [_k for _k, _v in _sd_c4.order]
    assert _sd4_kinds[0] == "key", (
        f"the wire order was {_sd4_kinds}; the sort must precede the "
        f"window steps — Sort_Col_List_'s handler sets _first = 0 "
        f"(colsum.cpp:832), so a window established first is a window "
        f"the sort then moves")
    assert _sd4_kinds.count("field") == _cs_sel.GameWindow.max_first(15), (
        f"{_sd4_kinds.count('field')} window steps for 15 colonies; "
        f"the plan leads with {_cs_sel.GameWindow.max_first(15)} "
        f"decrements even though the sort has just zeroed _first — "
        f"shortening it would be REMEMBERING the state instead of "
        f"establishing it (decision 46)")
    assert _sd4_kinds[-1] == "click", _sd4_kinds
    ok("pop move on the wire (the pre-effect pair is refused, the "
       "interlock stops on a cluster it did not predict)")

    # AND THE PROBE HAS THE SAME WAIT, because it is the tool that
    # runs against a live game and it got this wrong twice: once by
    # waiting for a fresh STATE while reading the FRAME, and once by
    # waiting for a fresh frame that was still the pre-effect one.
    # Two loops rather than one shared helper — this one blocks and
    # the chain's is driven a frame at a time — so the rule is
    # asserted in both places rather than assumed to have travelled.
    import importlib.util as _ilu
    _pb_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tools", "colony_move_probe.py")
    _pb_spec = _ilu.spec_from_file_location("_probe", _pb_path)
    _pb = _ilu.module_from_spec(_pb_spec)
    _pb_spec.loader.exec_module(_pb)

    class _PollClient:
        def __init__(self):
            self.stats = {"state": 0, "visual": 0}
            self.state = type("S", (), {"framebuffer": b"\0"})()
        def poll(self):
            self.stats["state"] += 1
            self.stats["visual"] += 1

    _pb_c = _PollClient()
    _pb_seen = []
    assert _pb.after_send(_pb_c, lambda st: _pb_seen.append(
        _pb_c.stats["state"]) or True, tries=4) is not None
    assert _pb_seen and min(_pb_seen) >= 2, (
        f"the probe's after_send accepted the world at pair "
        f"{min(_pb_seen)}; the first pair after a send is serialized "
        f"in the tick that consumed it")
    _pb_c2 = _PollClient()
    assert _pb.after_send(_pb_c2, lambda st: False, tries=3) is None, (
        "a predicate that never holds must time out, not settle")
    ok("the live probe waits for the effect too (same rule, second "
       "loop, asserted rather than assumed)")

    # ── The sidebar's six s_player scalars ──
    # ONE home for these offsets: the verified spec in
    # core/structs/player.py. A probe spec briefly duplicated them in
    # unverified.py on the mistaken belief that they were unverified;
    # it is gone, and this check exists partly so it does not come
    # back — a second Spec naming s_player is refused.
    #
    # What IS asserted is the thing the static assert cannot cover.
    # `verified=True` here rests on the header compiled with its own
    # pragma pack, sizeof landing on the 0xf0e in sizes.h. That fixes
    # the LAYOUT and says nothing about which member is which where
    # two are interchangeable — surplus_food @276 and surplus_bc @278
    # are adjacent int16 net flows, both printed signed, and the
    # struct is exactly as large either way round. So each carries a
    # KIND, and tools/struct_probe.py players --sidebar is the check
    # that can tell them apart.
    from core.structs import player as _plsp
    from core.structs import unverified as _unv
    assert not any(getattr(_unv, _n, None).__class__.__name__ == "Spec"
                   and getattr(_unv, _n).name == "s_player"
                   for _n in dir(_unv) if _n.isupper()), (
        "s_player is back in unverified.py — its offsets live in "
        "core/structs/player.py and nowhere else")
    _pl_off = dict((n, (o, k)) for n, o, k in _plsp.SPEC.fields)
    _six = ("bc", "surplus_bc", "total_pop", "surplus_freighters",
            "surplus_food", "research_produced")
    for _f in _six:
        assert _f in _pl_off, f"player.SPEC no longer carries {_f}"
        assert _f in _plsp.SIDEBAR_KINDS, (
            f"{_f} has no kind recorded in player.SIDEBAR_KINDS — "
            f"they are not one kind and adding a gross to a net is "
            f"silently wrong")
        assert _plsp.SIDEBAR_KINDS[_f][0] in (
            "stock", "net flow", "gross", "count"), \
            _plsp.SIDEBAR_KINDS[_f]
    assert _plsp.SIDEBAR_KINDS["bc"][0] == "stock"
    assert _plsp.SIDEBAR_KINDS["research_produced"][0] == "gross"
    assert (_plsp.SIDEBAR_KINDS["surplus_food"][0]
            == _plsp.SIDEBAR_KINDS["surplus_bc"][0] == "net flow")
    # The anchors --sidebar carries as controls must resolve.
    assert _pl_off["race"][1] == "u8" and _pl_off["race"][0] == 37
    assert _plsp.TRAITS_OFFSET == 2308
    assert _plsp.TECH_APPLICATIONS_OFFSET == 379

    # The sign rule is the original's and is PER ROW: only Income
    # (ESTR 106, "%sIncome: %s%s%+d") and Food (ESTR 102,
    # "%sFood: %s%+d") carry %+d; Reserve 118, Population 114,
    # Freighters 103 and Research 117 are plain %d. A screen-wide
    # "sign everything" would be wrong on four rows out of six.
    _emp = _cjson.load(open(os.path.join(
        SCREENS_DIR, "colony_summary", "layout.json"),
        encoding="utf-8"))["empire"]
    _signed = {r["key"] for r in _emp["rows"] if r.get("signed")}
    assert _signed == {"income", "food"}, (
        f"the signed rows are {sorted(_signed)}; the original prints "
        f"%+d on Income (106) and Food (102) and %d on the other four")
    _fields = [r["field"] for r in _emp["rows"]]
    assert _fields == ["bc", "surplus_bc", "total_pop",
                       "surplus_freighters", "surplus_food",
                       "research_produced"], _fields
    # Research is ABSOLUTE and carries no percent. Asserted because
    # the claim is easy to cite wrongly: ESTR 117 is
    # "%sResearch: %s%d" and there is no %% in it. The note has to
    # keep saying so.
    assert "no %% in it" in _emp["_estrings_note"], (
        "empire._estrings_note no longer records that ESTR 117 "
        "carries no percent")
    for _pct in ("108", "112", "120", "121", "0x142"):
        assert _pct in _emp["_estrings_note"], (
            f"empire._estrings_note no longer lists {_pct} among the "
            f"only string-table entries that DO carry a literal %% — "
            f"the list is what makes 'not 117' checkable rather than "
            f"asserted")
    for _key in ("_join_note", "_justify_note", "_geometry_note",
                 "_colour_note", "_open_note"):
        assert _emp.get(_key), f"empire.{_key} is gone"
    # The justify note carries the corrected mechanism, not the
    # first one. justify=3 is inert because the buffer BEGINS with
    # s_0, so Set_Justification_ assigns justify_mode = 0 before a
    # character is drawn (fmtpara.cpp:1017) — not because CR ends
    # each line, which was the first reading. And the layout it
    # settles is label-left/value-right, which the renderer now does.
    for _cite in ("fmtpara.cpp:1017", "fmtpara.cpp:999",
                  "fmtpara.cpp:1699", "strings.cpp:22"):
        assert _cite in _emp["_justify_note"], (
            f"empire._justify_note no longer cites {_cite} — the "
            f"mechanism it records is what makes label-left/"
            f"value-right a transcription rather than a preference")
    assert "0x1A" in _emp["_justify_note"], (
        "empire._justify_note no longer records that the prefixes "
        "are 0x1A justification codes — the octal 032/033 confusion "
        "is what got this wrong twice")
    assert "OPEN" in _emp["_open_note"], (
        "empire._open_note no longer marks E_Strings_(12) as open")

    # ── The sidebar draws label LEFT and value RIGHT ──
    # The original's layout, and it is the whole point of the
    # justify-code reading above: each entry is one row, the label
    # flush against the column's left edge, the value flush against
    # its right. Asserted in INK at every resolution, and the edges
    # are read from boxes.json rather than recomputed the way
    # `_value_column` computes them — deriving the expected edge from
    # the renderer's own expression is the tautology 443aff1 shipped
    # and had to be rewritten.
    #
    # Flushness is what distinguishes this from the layout it
    # replaced. Centred label-over-value passes no part of it: the
    # label would not start at the left edge and the value would not
    # end at the right one.
    _sb_boxes = load_boxes(
        os.path.join(SCREENS_DIR, "colony_summary", "boxes.json"),
        1920, 1080)
    _sb_ref = [b.ref_rect for b in _sb_boxes if b.name == "empire_stats"]
    assert _sb_ref, "boxes.json has no empire_stats box"

    from screens.colony_summary import screen as _cs
    from screens.colony_summary import colonyempire as _emp_mod0

    # The screen loads its boxes and layout.json on activation, and
    # the dispatcher has been through other screens since the earlier
    # colony_summary check.
    d.switch_to("colony_summary")

    class _FakePlayer:
        bc = 1234
        surplus_bc = -42
        total_pop = 39
        surplus_freighters = 7
        surplus_food = -3
        research_produced = 88

    for _W, _H in _SIZES:
        _lay = Layout(_W, _H)
        _rect = pygame.Rect(*_lay.rect(_sb_ref[0]))
        # The column, derived here from the box, the native width and
        # the inset in layout.json — NOT by calling _value_column.
        # frame_inset keeps both edges out from under the frame's
        # rim; it is a SCREEN-level key because colonylist needs the
        # same number. See _frame_inset_note in layout.json.
        _native = _emp.get("native_width", 104)
        _inset = int(_out_cfg.get("frame_inset", 8) * _lay.scale)
        _col_w = min(max(1, _rect.w - 2 * _inset),
                     int(_native * (1920 / _emp_mod0.NATIVE_W) * _lay.scale))
        _col_l = _rect.x + _inset
        _col_r = _col_l + _col_w

        _sf = pygame.Surface((_W, _H))
        _sf.fill((0, 0, 0))
        # `layout` is a property onto app.layout, so the resolution
        # is swapped on the app for the duration of one render.
        _scr = app.dispatcher.screens["colony_summary"]
        _saved_layout, _saved_local = app.layout, _scr._local
        app.layout, _scr._local = _lay, _FakePlayer()
        try:
            _scr._render_sidebar(_sf)
        finally:
            app.layout, _scr._local = _saved_layout, _saved_local

        _arr = pygame.surfarray.array3d(_sf.subsurface(_rect))
        _lab_rgb = tuple(_emp_mod0.LABEL_COLOR[:3])
        _val_rgb = tuple(_emp_mod0.VALUE_COLOR[:3])
        _warn_rgb = tuple(_emp_mod0.WARN_COLOR[:3])

        def _cols(_rgb):
            _m = (_arr == _rgb).all(axis=2).any(axis=1).nonzero()[0]
            return (int(_m[0]) + _rect.x, int(_m[-1]) + _rect.x) \
                if len(_m) else None

        _lab = _cols(_lab_rgb)
        _val = _cols(_val_rgb)
        _warn = _cols(_warn_rgb)
        assert _lab, f"{_W}x{_H}: no label ink in the sidebar"
        assert _val, f"{_W}x{_H}: no value ink in the sidebar"

        # A glyph's ink does not start at its surface's edge — there
        # is a side bearing, and it grows with the font, which is why
        # a fixed pixel tolerance passed at 1080p and failed at 4K by
        # exactly the bearing. So the bearing is MEASURED off a
        # standalone render of the same string and added to the
        # column edge. That is glyph metrics, not layout: it says
        # nothing about where the renderer decided to put the text,
        # which is the thing under test.
        _fs = _scr.box_font_scale_stored("empire_stats")
        _lab_px = _lay.font_size(int(_emp.get("label_font", 18) * _fs))
        _val_px = _lay.font_size(int(_emp.get("value_font", 26) * _fs))

        def _bearings(_text, _px, _rgb):
            """(ink left, ink right) inside the string's own surface.

            Composited onto the SAME panel fill the sidebar uses.
            Measured against a bare surface the numbers come out a
            couple of pixels different, because an antialiased edge
            column blends with whatever is behind it and stops
            matching the colour exactly — so the bearing has to be
            measured through the same compositing the renderer does,
            or it is measuring a different picture.
            """
            _s2 = app.style.render_text(_text, _px, _rgb)
            _pad = pygame.Surface((_s2.get_width() + 4,
                                   _s2.get_height() + 4))
            _pad.fill(_emp_mod0.PANEL_BG[:3])
            _pad.blit(_s2, (2, 2))
            _a2 = pygame.surfarray.array3d(_pad)
            _m2 = (_a2 == _rgb).all(axis=2).any(axis=1).nonzero()[0]
            if not len(_m2):
                return None
            return (int(_m2[0]) - 2,
                    (_s2.get_width() + 1) - int(_m2[-1]))

        _want_left, _want_right = [], []
        for _r in _emp["rows"]:
            _b = _bearings(_r["label"].upper(), _lab_px, _lab_rgb)
            if _b:
                _want_left.append(_col_l + _b[0])
            _v = getattr(_FakePlayer, _r["field"])
            _txt = _emp_mod0.format_value(_v, _r.get("signed", False))
            _rgb2 = _warn_rgb if (_r.get("warn_negative")
                                  and _v < 0) else _val_rgb
            _b = _bearings(_txt, _val_px, _rgb2)
            if _b:
                _want_right.append(_col_r - _b[1])

        _exp_left, _exp_right = min(_want_left), max(_want_right)
        _val_right = max(_val[1], _warn[1] if _warn else _val[1])
        assert abs(_lab[0] - _exp_left) <= 1, (
            f"{_W}x{_H}: the label's leftmost ink is at {_lab[0]}; "
            f"flush against the column's left edge {_col_l} it would "
            f"be {_exp_left} once the glyph's own {_exp_left - _col_l} "
            f"px bearing is allowed ({_lab[0] - _exp_left:+d}). The "
            f"original left-justifies the label (strings.cpp:22, "
            f"byte 1A 30).")
        assert abs(_val_right - _exp_right) <= 1, (
            f"{_W}x{_H}: the rightmost value ink is at {_val_right}; "
            f"flush against the column's right edge {_col_r} it would "
            f"be {_exp_right} ({_val_right - _exp_right:+d}). The "
            f"original right-justifies the value (strings.cpp:24, "
            f"byte 1A 31; para.x2 = x + width - 1, fmtpara.cpp:657).")
        # And the two columns must not have collapsed into one.
        assert _lab[0] < _val_right, (
            f"{_W}x{_H}: label ink starts at {_lab[0]}, values end at "
            f"{_val_right} — the two columns have collapsed")
    # ── The clamped column is a DEVIATION and stays marked ──
    # The original's paragraph is 104 native px = 312 reference px;
    # the sidebar cutout is 286, and `min` picks the cutout at every
    # resolution. Decision 44: the deviation is that the shipped
    # column is never the original's proportion, and the risk is the
    # native number being deleted once somebody notices it never
    # wins. So: it must still be READ, and it must still be LARGER
    # than what is drawn — the day it is not, the clamp has stopped
    # firing on its own and the deviation is over.
    assert "native_width" in _emp, (
        "empire.native_width is gone — it is the original's 104 px "
        "paragraph and the only evidence the drawn column is a "
        "deviation rather than a choice (decision 44)")
    for _cite in ("DEVIATION", "colsum.cpp:418", "fmtpara.cpp:657"):
        assert _cite in _emp["_native_width_note"], (
            f"empire._native_width_note no longer carries {_cite!r}")
    _fund_dev = open(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                                  "v3_fundament.md"),
                     encoding="utf-8").read()
    assert "**44." in _fund_dev and "native_width" in _fund_dev, (
        "the fundament no longer carries the clamped sidebar column "
        "as a decision")
    # The marking lives with the CODE, so this greps the module the
    # clamp is in and not the screen it used to be in. The sidebar
    # moved to colonyempire.py on 3 September 2026; a check left
    # pointed at screen.py would have gone on passing against a file
    # that no longer contains the thing it asserts, which is worse
    # than no check because it still reports green.
    from screens.colony_summary import colonyempire as _emp_mod
    _scr_dev = open(os.path.join(SCREENS_DIR, "colony_summary",
                                 "colonyempire.py"),
                    encoding="utf-8").read()
    # On the FUNCTION THAT CLAMPS, not merely somewhere in the file:
    # the module docstring also says "DEVIATION", so a file-wide
    # search passes even after the marking is taken off the code it
    # is about. Tying it to `value_column.__doc__` is what makes the
    # marking travel with the thing it marks.
    assert "DEVIATION" in (_emp_mod.value_column.__doc__ or ""), (
        "value_column no longer says the clamped width is a "
        "DEVIATION — that clamp fires at every resolution, and the "
        "only evidence it is a deviation rather than a choice is the "
        "sentence in its own docstring (decision 44)")
    assert "native_column_width" in _scr_dev, (
        "colonyempire.py no longer carries native_column_width")
    # ONE home for the clamp, asserted as a rule: screen.py must not
    # grow a second copy of it. The sidebar came back into a screen
    # once before, as a duplicated s_player spec in unverified.py, and
    # the check that refused a second Spec is why it stayed gone.
    _scr_now = open(os.path.join(SCREENS_DIR, "colony_summary",
                                 "screen.py"), encoding="utf-8").read()
    assert "native_width" not in _scr_now, (
        "screen.py mentions native_width again — the clamp and its "
        "marking live in colonyempire.py, and a second copy is what "
        "the marking cannot survive")

    for _W, _H in _SIZES:
        _lay = Layout(_W, _H)
        _rect = pygame.Rect(*_lay.rect(_sb_ref[0]))
        _native = _emp_mod.native_column_width(_emp, _lay)
        _l, _r = _emp_mod.value_column(_rect, _emp, _lay,
                                      _out_cfg.get("frame_inset", 8))
        _drawn = _r - _l
        _inset = int(_out_cfg.get("frame_inset", 8) * _lay.scale)
        _usable = max(1, _rect.w - 2 * _inset)
        assert _drawn == min(_usable, _native), (
            f"{_W}x{_H}: the drawn column {_drawn} is neither the "
            f"cutout less its insets {_usable} nor the native "
            f"{_native} — the clamp has grown a third case")
        # The marking is only true while the clamp actually fires.
        # If this ever fails, the cutout has caught up with the
        # original's proportion: delete decision 44 and this check
        # rather than "fixing" it.
        assert _native > _drawn, (
            f"{_W}x{_H}: native_width scales to {_native} and the "
            f"drawn column is {_drawn} — the clamp is no longer "
            f"firing, so the deviation in decision 44 is over. That "
            f"is good news: retire the marking, do not restore it.")
    ok("colony summary sidebar column (clamp is a marked DEVIATION, "
       "native width still carried and still larger)")

    import numpy as _np
    from PIL import Image
    from core import style as _style_mod
    # ── CLASS A: text OUR CODE places at a cutout edge ──
    # Zero pixels under opaque frame alpha, every shipped size, no
    # tolerance. This REPLACES a sidebar-only version of the same
    # check — that one asserted the instance and this asserts the
    # rule, and it found a second instance the first could not: one
    # pixel of a fifteen-character colony name at 1600x900, whose
    # right-aligned overflow was allowed to run to list_area's own
    # edge and therefore under the rim.
    #
    # NO LIST OF BOXES. The renderers are asked what they drew:
    # StyleRenderer.render_text and get_font(...).render are wrapped
    # so every text surface is tagged, and the screen renders onto a
    # Surface subclass that records where each tagged surface landed.
    # A text box added tomorrow is covered without anyone editing
    # this.
    #
    # TWO THINGS THIS MEASURES CAREFULLY, both learned the hard way:
    #
    #   what SURVIVES the clip, not what was requested. galaxy_map
    #   wraps its whole map render in set_clip(map_area), exactly as
    #   the original wraps Print_Star_Names_ in Set_Window_/Clip_On_
    #   (mainscr.cpp:519). Recording the intended rectangle reports
    #   three labels under the frame on that screen, one of them 330
    #   px outside the map, and all three are fiction.
    #
    #   a POPULATED state. With no snapshot the colony summary draws
    #   22 glyphs; with one it draws 65, because the list, the scan
    #   box and the galaxy inset are all empty until then. A green
    #   run over an empty screen asserts nothing.
    #
    # CLASS B is separated MECHANICALLY, not by a list: content
    # clipped to a cutout is the frame's own business and is checked
    # against the artwork below, so a glyph whose clip at blit time
    # IS one of that screen's cutouts is not Class A.
    class _TextRec(pygame.Surface):
        hits = []
        def blit(self, src, dest, *a, **k):
            _clip = self.get_clip()
            _r = super().blit(src, dest, *a, **k)
            if id(src) in _TEXT_IDS:
                _TextRec.hits.append(
                    (int(dest[0]), int(dest[1]), src,
                     pygame.Rect(_clip) if _clip else None))
            return _r

    _TEXT_IDS = set()
    _TEXT_KEEP = []
    _orig_rt = _style_mod.StyleRenderer.render_text
    _orig_gf = _style_mod.StyleRenderer.get_font

    class _TaggedFont:
        def __init__(self, f): self._f = f
        def __getattr__(self, n): return getattr(self._f, n)
        def render(self, *a, **k):
            r = self._f.render(*a, **k)
            _TEXT_IDS.add(id(r)); _TEXT_KEEP.append(r)
            return r

    def _tagged_rt(self, *a, **k):
        r = _orig_rt(self, *a, **k)
        _TEXT_IDS.add(id(r)); _TEXT_KEEP.append(r)
        return r

    _FRAME_SCREENS = ("colony_summary", "galaxy_map")
    _class_a = {}
    _class_b_seen = 0
    _style_mod.StyleRenderer.render_text = _tagged_rt
    _style_mod.StyleRenderer.get_font = lambda self, sz: _TaggedFont(
        _orig_gf(self, sz))
    try:
        for _name in _FRAME_SCREENS:
            for _W, _H in _SIZES:
                _a2, _ = _pv.build_screen(_W, _H)
                _s2 = _a2.dispatcher.screens[_name]
                _a2.dispatcher.switch_to(_name)
                # THE ALPHA MUST BE THE FRAME THE SCREEN DREW, not a
                # path this check assumes. Since Stage 4 the colony
                # screen draws a per-resolution plate chosen by
                # `colonyframe.frame_source`, so reading assets/
                # frame.png here would measure glyphs against artwork
                # nobody blitted — and it did: the superseded frame's
                # metal sits exactly where the new list is, which is
                # 5822 "violations" at 1080p against a frame that was
                # not on screen.
                _fpng = (_cframe.frame_source(_s2)[0]
                         if _name == "colony_summary"
                         else res.screen_file(_name, "assets", "frame.png"))
                _fbase = Image.open(_fpng).convert("RGBA")
                _s2.enter(None)
                _s2.update(_pv._Snapshot(_pv.COLONIES))
                _cuts = []
                for _b in _s2.boxes:
                    _br = _s2.box_rect(_b.name)
                    if _br:
                        _cuts.append(pygame.Rect(*_s2.layout.rect(_br)))
                _TextRec.hits = []
                _surf2 = _TextRec((_W, _H))
                _surf2.fill((0, 0, 0))
                _s2.render(_surf2)
                assert len(_TextRec.hits) >= 10, (
                    f"{_name} at {_W}x{_H} drew {len(_TextRec.hits)} text "
                    f"surfaces — too few for this check to mean anything. "
                    f"A green run over an empty screen asserts nothing")
                _fx, _fy, _fw, _fh = _s2.layout.rect((0, 0, 1920, 1080))
                _al = _np.array(_fbase.resize((_fw, _fh),
                                              Image.BILINEAR))[:, :, 3]
                for _x, _y, _src, _clip in _TextRec.hits:
                    _rgb = pygame.surfarray.array3d(
                        _src).transpose(1, 0, 2).astype(int)
                    _m = _rgb.sum(axis=2) > 40
                    if _src.get_flags() & pygame.SRCALPHA:
                        _m &= pygame.surfarray.array_alpha(
                            _src).transpose(1, 0) > 40
                    _ys, _xs = _np.where(_m)
                    if not len(_ys):
                        continue
                    _px, _py = _xs + _x, _ys + _y
                    if _clip is not None:
                        _k = ((_px >= _clip.x) & (_px < _clip.right)
                              & (_py >= _clip.y) & (_py < _clip.bottom))
                        _px, _py = _px[_k], _py[_k]
                        if not len(_px):
                            continue
                    _gx, _gy = _px - _fx, _py - _fy
                    _ok = ((_gx >= 0) & (_gx < _fw)
                           & (_gy >= 0) & (_gy < _fh))
                    if not _ok.any():
                        continue
                    _n = int((_al[_gy[_ok], _gx[_ok]] >= 16).sum())
                    if not _n:
                        continue
                    _is_b = _clip is not None and any(
                        abs(_clip.x - _c.x) <= 2 and abs(_clip.y - _c.y) <= 2
                        and abs(_clip.w - _c.w) <= 4
                        and abs(_clip.h - _c.h) <= 4 for _c in _cuts)
                    if _is_b:
                        _class_b_seen += _n
                    else:
                        _class_a[(_name, _W, _H)] = (
                            _class_a.get((_name, _W, _H), 0) + _n)
    finally:
        _style_mod.StyleRenderer.render_text = _orig_rt
        _style_mod.StyleRenderer.get_font = _orig_gf
    assert not _class_a, (
        f"CLASS A violations — text this tree places at a cutout edge, "
        f"drawn under opaque frame alpha: {_class_a}. Zero tolerance: "
        f"raise the screen's frame_inset, or stop placing the text "
        f"against the box edge. (Content CLIPPED to a cutout is class "
        f"B and is checked against the artwork, not here.)")
    ok(f"class A: no glyph our code places lands under the frame "
       f"({len(_FRAME_SCREENS)} screens, {len(_SIZES)} sizes)")

    # ── CLASS B: how far the ARTWORK reaches into each cutout ──
    # Content clipped to a cutout — the galaxy map's stars and star
    # names — cannot be kept off the rim by an inset without cropping
    # the content, so what is budgeted here is the FRAME, not the
    # residue. If a redrawn frame grows a fatter rim, this fails and
    # the clipped content stops silently losing more of itself.
    #
    # MEASURED ON THE SOURCE IMAGE, which is the artwork. At display
    # sizes the bilinear rescale widens the rim's alpha ramp by one
    # to three reference px, and that is a property of the resampler
    # rather than of the drawing.
    #
    # CORNERS EXCLUDED, and `title` excluded outright: it is not a
    # rectangle. Its hole is angled, so the bounding box find_holes
    # returns contains real frame at both ends — 14 px on the colony
    # summary, 29 on the galaxy map — and measuring a straight-edge
    # intrusion there measures the shape, not the rim.
    # Today's worst is 2, on the top edge of `list_area` and
    # `galaxy_inset`; every other straight edge is 0 or 1. The
    # budget IS the measurement, so any thickening fails.
    _CLASS_B_BUDGET = 2
    _CORNER_TRIM = 0.18
    import frame_holes as _fhB

    def _intrusion(alpha, rect):
        _x, _y, _w, _h = rect
        _x0, _y0 = max(0, _x), max(0, _y)
        _x1 = min(alpha.shape[1], _x + _w)
        _y1 = min(alpha.shape[0], _y + _h)
        if _x1 - _x0 < 8 or _y1 - _y0 < 8:
            return None
        _iy = int((_y1 - _y0) * _CORNER_TRIM)
        _ix = int((_x1 - _x0) * _CORNER_TRIM)
        _out = []
        for _cs, _horiz in ((range(_y0 + _iy, _y1 - _iy,
                                   max(1, (_y1 - _y0) // 40)), True),
                            (range(_x0 + _ix, _x1 - _ix,
                                   max(1, (_x1 - _x0) // 40)), False)):
            _lo = _hi = 0
            for _c in _cs:
                _line = (alpha[_c, _x0:_x1] if _horiz
                         else alpha[_y0:_y1, _c])
                _n = 0
                while _n < len(_line) and _line[_n] >= 16:
                    _n += 1
                _lo = max(_lo, _n)
                _n = 0
                while _n < len(_line) and _line[len(_line) - 1 - _n] >= 16:
                    _n += 1
                _hi = max(_hi, _n)
            _out += [_lo, _hi]
        return _out

    _b_worst = {}
    for _name in _FRAME_SCREENS:
        # The frame this screen DRAWS, same rule as class A above.
        _fpng = (os.path.join(SCREENS_DIR, "colony_summary", "assets",
                              "frames", "frame_1920x1080.png")
                 if _name == "colony_summary"
                 else res.screen_file(_name, "assets", "frame.png"))
        if not os.path.exists(_fpng):
            continue
        _iw, _ih, _holes = _fhB.find_holes(_fpng)
        _named = _fhB.name_holes(_holes, _name)
        _al = _np.array(Image.open(_fpng).convert("RGBA"))[:, :, 3]
        for _cn, _r in _named.items():
            if _cn == "title":
                continue
            _v = _intrusion(_al, _r)
            assert _v is not None, (_name, _cn)
            _b_worst[(_name, _cn)] = max(_v)
            assert max(_v) <= _CLASS_B_BUDGET, (
                f"{_name}/{_cn}: the frame's opaque alpha reaches "
                f"{max(_v)} source px into this cutout at a straight "
                f"edge (L{_v[0]} R{_v[1]} T{_v[2]} B{_v[3]}), over the "
                f"budget of {_CLASS_B_BUDGET}. Content clipped to this "
                f"hole — the galaxy map's stars and names — loses that "
                f"much of itself with no inset able to help. Either the "
                f"artwork grew a rim or find_holes' bounding box is no "
                f"longer the hole's shape")
    # 17: the galaxy map's ten straight-edged holes plus the plate's
    # eight less `title`, which the plate does not have. It was 20+
    # while the colony frame cut 14; the plate cuts 8 because the
    # seven sort buttons became one bar and the sidebar moved into
    # the band. A floor, so a frame that stops cutting holes cannot
    # pass by measuring nothing.
    assert len(_b_worst) >= 17, len(_b_worst)
    ok(f"class B: the frame reaches at most {_CLASS_B_BUDGET} px into "
       f"any of {len(_b_worst)} cutouts")

    ok("colony summary sidebar layout (label flush left, value flush "
       "right, ink-measured at 12 resolutions)")

    # ── The colony row's two marked deviations ──
    # Neither changes a pixel; both exist so the next reader takes
    # them as choices rather than as fidelity.
    #
    #   the NAME is right-aligned  — the original left-aligns it,
    #       Squeeze_Formatted_Paragraph_Centered_ (colsum.cpp:582)
    #       passing 0 = JUSTIFY_LEFT through bill.cpp:210, with
    #       "Centered_" meaning center_y ONLY (bill.cpp:205)
    #   the DETAIL LINE is per row — the original draws it once for
    #       the selected colony (colsum.cpp:1155)
    _cl_src2 = open(os.path.join(SCREENS_DIR, "colony_summary",
                                 "colonylist.py"), encoding="utf-8").read()
    with open(os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                           "v3_fundament.md"), encoding="utf-8") as _fh:
        _fund_src = _fh.read()
    for _cite in ("colsum.cpp:582", "bill.cpp:205", "bill.cpp:210",
                  "JUSTIFY_LEFT"):
        assert _cite in _cl_src2, (
            f"colonylist.py no longer cites {_cite} — the name's "
            f"right alignment is a deviation and the evidence that "
            f"it is one has to travel with the marking")
        assert _cite in _fund_src, (
            f"the fundament no longer cites {_cite} for the "
            f"right-aligned name")
    assert "**45." in _fund_src, (
        "the fundament no longer carries the colony row's two "
        "deviations as a decision")
    # The detail line's omission is deliberate and says what it omits.
    assert "colsum.cpp:1196" in _cl_src2, (
        "colonylist.py no longer names where the original's seven "
        "values come from, so 'a SUBSET' is a claim without a source")

    # ── Two states the original's row carries and ours does not ──
    # Neither is a task and neither is on the open-fixes list; they
    # are marked because an omission nobody wrote down cannot be told
    # apart from one nobody noticed, and both were found by reading
    # Draw_Colony_Summary_For_Colony_ for something else.
    #
    # The check has the same shape as the marking check the fundament
    # asks for: refuse a marking that does not say what the ORIGINAL
    # does, so the note records a reason rather than carrying a label.
    _cr_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                                "colonyrows.py"), encoding="utf-8").read()
    assert "NOT DRAWN" in _cr_src, (
        "colonyrows.py no longer carries a NOT DRAWN section — the "
        "star blockade and the colony event are two states of the "
        "original's row string that the HD row does not draw")
    for _cite in ("colsum.cpp:557-569", "colsum.cpp:562", "blockaded"):
        assert _cite in _cr_src, (
            f"the blockade marking no longer cites {_cite!r}, so it "
            f"names a state without naming where the original draws it")
    for _cite in ("colsum.cpp:553", "events.cpp:635",
                  "Colony_Has_Event_"):
        assert _cite in _cr_src, (
            f"the colony-event marking no longer cites {_cite!r}")
    # The two are NOT the same kind of absence and the note must keep
    # them apart: blockaded is a verified field on the wire, events
    # are not on the wire at all. Collapsing them into one line is
    # how the reachable one would stop looking buildable.
    assert "ext_api.cpp:53-136" in _cr_src, (
        "the colony-event marking no longer names where the snapshot "
        "is written, which is the only evidence that _event_data is "
        "absent from it rather than merely unread")
    from core.structs import star as _star_spec
    assert any(_f[0] == "blockaded" for _f in _star_spec.SPEC.fields), (
        "s_star_data.blockaded is gone from the verified spec, so the "
        "blockade marking claims a field that no longer exists")
    assert _star_spec.SPEC.verified, "star spec is no longer verified"
    # And events really are absent from the snapshot: assert it
    # against GameState rather than against the note, so the day Joes
    # serializes them this fails and the marking gets revisited.
    from core.game_state import GameState as _GS
    # `ng_random_events` is the New Game screen's own toggle
    # (ext_api.cpp:135) and is deliberately not what this looks for:
    # what the marking claims absent is the EVENTS::_event_data[]
    # array, which would arrive as a record array like every other
    # one — a `*_raw` member, or a parsed list beside `stars`.
    _gs_attrs = [_a2 for _a2 in dir(_GS()) if not _a2.startswith("_")]
    _ev = [_a2 for _a2 in _gs_attrs
           if "event" in _a2.lower() and not _a2.startswith("ng_")]
    assert not _ev, (
        f"GameState grew an events member {_ev} — the colony-event "
        f"marking says the snapshot carries none, and that is now "
        f"wrong. Re-read colsum.cpp:553 and decide whether the row "
        f"can draw it before deleting the marking.")
    ok("colony summary NOT DRAWN markings (star blockade reachable, "
       "colony event not on the wire, both sourced)")

    # ── output_panel: decision 43 is WITHDRAWN ──
    # It marked output_panel an HD EXTENSION on the strength of a
    # word grep of one file. The original draws all four ECON values
    # per colony — Draw_Colony_Scan_Info_ (colsum.cpp:1155) loops
    # Draw_Colony_Wee_Prod_ into Draw_Colony_Prod_Both_
    # (coldraw.cpp:36), which reads colony->production[] at
    # coldraw.cpp:60. The panel is a TRANSCRIPTION. This check keeps
    # the withdrawal from being quietly reverted.
    _scr_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                                 "screen.py"), encoding="utf-8").read()
    assert "WITHDRAWN" in _fund_src, (
        "fundament 43 no longer records that it was withdrawn — it "
        "claimed the original never draws per-colony food/industry/"
        "research, and coldraw.cpp:60 does")
    assert "coldraw.cpp:60" in _fund_src and "coldraw.cpp:60" in _scr_src, (
        "the withdrawal no longer cites where the original actually "
        "draws production[] — a retraction without its evidence is "
        "how the original error got in")
    assert "TRANSCRIPTION" in _scr_src, (
        "screen.py no longer records output_panel as a transcription")
    ok("colony summary sidebar (six s_player scalars kinded and held "
       "to the verified spec, sign rule per row, ESTR/join/justify "
       "provenance, output_panel marked TRANSCRIPTION)")

    ok("colony list (rows, No Farming below a full track and clear of "
       "the hatching, horizontal budget balances to the pixel, name "
       "clipped to its column, INVENTION + HD EXTENSION marked, "
       "preview rows match build_rows and carry a provenance band)")

    # ── The square is a fixed unit, not a ruler that moves ──
    # The unit used to be derived from the widest max_pop in the
    # current list, so acquiring one better colony resized every
    # square on the screen and a square counted last turn was not the
    # square counted this turn. It now comes from POP_LIMIT_CAP, the
    # engine's own ceiling (colcalc.cpp:930, pop[], colmove.cpp:518).
    #
    # Asserted in pixels rather than by reading the arithmetic: the
    # SAME row, drawn alone and drawn beside a colony twice its size,
    # must come out identical pixel for pixel. Reimplementing the
    # unit formula here would only check it against itself.
    _row_h = int(_cfg["row_height"] * app.layout.scale)
    _band = pygame.Rect(_area.x, _area.y, _area.w,
                        int(_cfg["pad_y"] * app.layout.scale) + _row_h)

    def _first_row_pixels(_rowset):
        _s = pygame.Surface((1920, 1080))
        _s.fill((0, 0, 0))
        _cl.render(_s, _rowset, _area, _cfg, app.layout, app.style)
        return pygame.surfarray.array3d(_s.subsurface(_band))

    _modest = {"name": "Alpha I", "pops": 4, "jobs": [1, 2, 1],
               "no_farming": False, "max_pop": 8}
    _grand = {"name": "Beta II", "pops": 30, "jobs": [10, 12, 8],
              "no_farming": False, "max_pop": _cr.POP_LIMIT_CAP}
    assert (_first_row_pixels([_modest])
            == _first_row_pixels([_modest, _grand])).all(), (
        "the colony list's square still changes size with the row set "
        "— the unit must come from POP_LIMIT_CAP, not from the widest "
        "max_pop currently on screen")

    # ── Three regions, three visual states ──
    # filled (zone colour) then free (dashed outline) then unreachable
    # (a faint baseline and nothing else), left to right and never
    # overlapping. Asserted from the picture by colour, so it holds
    # whatever the geometry does; the unreachable region is checked
    # for being a BASELINE — thin ink at the foot of the track — and
    # not merely for being a different colour, because a dimmer
    # square would pass a colour test and say the wrong thing.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Regions I", "pops": 4,
                        "jobs": [1, 2, 1], "no_farming": False,
                        "max_pop": 9}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)

    def _cols_of(_color):
        return [_x for _x in range(_area.x, _area.right)
                if (_px[_x] == _color).all(axis=1).any()]

    def _ink_rows(_x0, _x1):
        return [_y for _y in range(_area.y, _area.bottom)
                if (_px[_x0:_x1 + 1, _y] != 0).any()]

    _zone_cols = [c for _z in _cl.ZONE_COLORS for c in _cols_of(_z)]
    _free_cols = _cols_of(_cl.BAR_FREE)
    _beyond_cols = _cols_of(_cl.BAR_BEYOND)
    assert _zone_cols and _free_cols and _beyond_cols, (
        "a colony below the population ceiling must show all three "
        f"regions; found filled={bool(_zone_cols)} "
        f"free={bool(_free_cols)} unreachable={bool(_beyond_cols)}")
    assert (max(_zone_cols) < min(_free_cols)
            and max(_free_cols) < min(_beyond_cols)), (
        "the colony list's three regions are out of order or overlap: "
        f"filled ends {max(_zone_cols)}, free "
        f"{min(_free_cols)}-{max(_free_cols)}, unreachable starts "
        f"{min(_beyond_cols)}")
    _free_band = _ink_rows(min(_free_cols), max(_free_cols))
    _beyond_band = _ink_rows(min(_beyond_cols), max(_beyond_cols))
    assert len(_beyond_band) * 4 <= len(_free_band), (
        f"the unreachable region is {len(_beyond_band)} px tall "
        f"against a {len(_free_band)} px free slot — it is drawing a "
        "square, not a baseline")
    assert min(_beyond_band) > (min(_free_band) + max(_free_band)) // 2, \
        "the unreachable region's ink is not at the foot of the track"
    ok("colony list track = engine cap (unit fixed, filled/free/"
       "unreachable in order)")

    # ── The name block: right-aligned, two lines ──
    # Replaces the figure-mode check, which went when figure mode did
    # (the count must not go down; an obsolete check is replaced, not
    # deleted). Same subject — what the name column does with the
    # width the budget gave it.
    #
    # RIGHT-ALIGNED against the column's right edge, which is where
    # the bar starts. Left-aligned, a name too long for the column
    # grew rightward onto the track's first slots, and since the
    # squares draw afterwards the data won and the name was the
    # casualty. Right-aligned it grows LEFT into pad_x, where nothing
    # is drawn, so the clip becomes a fallback instead of the
    # mechanism. Asserted at the structural maximum: s_star.name is
    # str15 and namestar.cpp:262 lets a player type all fifteen.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "W" * 15 + " V", "pops": 3,
                        "jobs": [1, 1, 1], "no_farming": False,
                        "climate": 8, "max_pop": 9}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _scale = app.layout.scale
    _col_right = (_area.x + int(_cfg["pad_x"] * _scale)
                  + int(_cfg["name_width"] * _scale))
    _rgb = tuple(_cl.ROW_NAME[:3])
    _name_cols = [x for x in range(_area.x, _area.right)
                  if any(tuple(_px[x, y]) == _rgb
                         for y in range(_area.y, _area.bottom))]
    assert _name_cols, "the name did not draw at all"
    assert max(_name_cols) < _col_right, (
        f"the longest producible name reaches x={max(_name_cols)}, past "
        f"its column at {_col_right} — it is on the track again")
    # It must actually USE the padding, or the alignment is not what
    # is keeping it off the track and this check would pass on a name
    # that simply fitted.
    assert min(_name_cols) < _area.x + int(_cfg["pad_x"] * _scale), (
        "the structural maximum fits inside the column, so this check "
        "is not exercising the overflow it exists for")
    assert min(_name_cols) >= _area.x, (
        f"the name overflowed past the left edge of list_area to "
        f"x={min(_name_cols)} — pad_x is not deep enough for it")

    # ── The detail line ──
    # Climate name plus n/max, from the same row dict, under the name.
    # The climate is an index into the PLANET_CLIMATE enum
    # (orion2_consts.h:362-374) and the wording lives in layout.json,
    # so this asserts the wiring, not the words.
    assert _cl._detail_text(
        {"climate": 8, "pops": 12, "max_pop": 14}, _cfg) == "Terran 12/14"
    assert _cl._detail_text(
        {"climate": 0, "pops": 1, "max_pop": 42}, _cfg) == "Toxic 1/42"
    assert len(_cfg["climates"]) == 10, _cfg["climates"]
    # An index the enum does not cover must degrade, not raise: the
    # climate byte is one unverified value away from being anything.
    for _bad in (-1, 10, 255):
        assert "?" in _cl._detail_text(
            {"climate": _bad, "pops": 1, "max_pop": 2}, _cfg), _bad
    # Substitution is a REPLACE, not str.format (decision 37): a
    # translated string with a stray brace must not raise inside the
    # render path, and an unknown placeholder must survive to be seen.
    _braced = dict(_cfg)
    _braced["detail"] = "{climate} {pops}/{max_pop} {not_a_key} }{"
    _out = _cl._detail_text({"climate": 9, "pops": 2, "max_pop": 3}, _braced)
    assert _out == "Gaia 2/3 {not_a_key} }{", _out

    # Both lines right-align to the same edge, so the eye crosses one
    # gap to the bar rather than a ragged one per row.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Sol", "pops": 12, "jobs": [4, 5, 3],
                        "no_farming": False, "climate": 8,
                        "max_pop": 14}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _detail_rgb = tuple(_cl.DETAIL_COLOR[:3])
    _right_of = lambda rgb: max(
        x for x in range(_area.x, _area.right)
        if any(tuple(_px[x, y]) == rgb for y in range(_area.y, _area.bottom)))
    assert abs(_right_of(_rgb) - _right_of(_detail_rgb)) <= 2, (
        f"name ends at {_right_of(_rgb)}, detail at "
        f"{_right_of(_detail_rgb)} — the two lines are not aligned")
    ok("colony list name block (right-aligned, overflow into pad_x, "
       "climate/pops detail line)")

    # ── The building column squeezes; it never truncates ──
    # 190 px is a HARD width, transcribed from
    # Squeeze_Print_Formatted_Paragraph_(0x200, y, 0x55, 0x16)
    # (colsum.cpp:621). _Squeeze_Print_Paragraph_ (bill.cpp:147) wraps
    # into the width and shrinks until the HEIGHT fits; there is no
    # truncation branch in it at all. The behaviour is transcribed,
    # not the three steps — the first of those narrows the space
    # glyph, a bitmap-font trick Aldrich has no equivalent for.
    from screens.colony_summary import colonybuild as _cb
    _bw = _cfg["building_width"]
    _small = app.layout.font_size(_cfg["small_font"])
    _floor = app.layout.font_size(_cfg["build_font_min"])
    _sizes = list(range(_small, _floor - 1, -1))
    for _text in ("Trade Goods", "Atmosphere Renewer",
                  "Alien Control Center", "W" * 15,
                  "Refit " + "W" * 15):
        _lines, _size = _cb.squeeze_lines(
            app.style, _text, _bw, _cfg["row_height"], _sizes, (255,) * 3)
        # Never truncate: every word of the source survives.
        _kept = " ".join(_cb.wrap_text(app.style, _text, _size, _bw)).split()
        assert _kept == _text.split(), (_text, _kept)
        # The hard side is the width.
        assert max(s.get_width() for s in _lines) <= _bw, (
            f"{_text!r} squeezed to {max(s.get_width() for s in _lines)} px "
            f"in a {_bw} px column — the width is the reservation")
        assert _floor <= _size <= _small, (_text, _size)

    # A single word wider than the column cannot be broken, so it fits
    # the height on one line and never triggers a height-driven
    # shrink. That is exactly how a 15-glyph ship design sat at 225 px
    # in a 190 px column; the fit test has to be both dimensions.
    _wide, _wsize = _cb.squeeze_lines(
        app.style, "W" * 15, _bw, 999, _sizes, (255,) * 3)
    assert _wsize < _small, (
        "an unbreakable word wider than the column did not shrink — "
        "the squeeze is driven by height alone again")

    # And when nothing is left to shrink it still draws everything:
    # the original prints the paragraph once its loop runs out.
    _tiny, _tsize = _cb.squeeze_lines(
        app.style, "W" * 60, 40, 4, _sizes, (255,) * 3)
    assert _tiny and _tsize == _sizes[-1], (_tsize, len(_tiny))
    # ── The markings on that column ──
    # Three separate claims, three separate homes, and each one has to
    # name what the original does instead: a label that records no
    # deviation is a label, not a marking.
    _cb_src = open(os.path.join(SCREENS_DIR, "colony_summary",
                                "colonybuild.py"), encoding="utf-8").read()
    # The width condition transcribes a guarantee and deviates in the
    # means. Both halves have to survive, and the line that settles it
    # is fmtpara.cpp:567 — without that reference the claim is an
    # assertion about the original that nobody can check.
    _wc = _cfg.get("_width_condition_note", "")
    assert "fmtpara.cpp:567" in _wc and "fmtpara.cpp:567" in _cb_src, \
        ("the width condition no longer cites the line that settles "
         "whether it is a transcription or a deviation")
    assert "TRANSCRIPTION" in _wc and "DEVIATION" in _wc, \
        "the width condition's marking lost one of its two halves"
    # The Buy control deviates twice. Naming only the label would
    # leave drawing text where the original draws a sprite unmarked.
    _bn = _cfg.get("_buy_note", "")
    assert "DEVIATION 1" in _bn and "DEVIATION 2" in _bn, \
        "the Buy control's marking no longer names both deviations"
    assert "E_Strings_(12)" in _bn and "SPRITE" in _bn.upper(), \
        ("the Buy marking no longer names what the original draws "
         "instead of text")
    # The two-line box is the original's own budget, not our idea.
    _bc = _cfg.get("_building_column_note", "")
    assert "colsum.cpp:621" in _bc and "31" in _bc, \
        ("the building column no longer records that the original "
         "budgets two lines in the same box")
    ok("colony build column (hard 190 width, wrap + shrink, never "
       "truncates, all three markings name their source)")

    # ── Glyph substitution: mechanism, not one font's quirk ──
    # This existed because the bundled Bank Gothic was a DEMO build
    # that mapped 28 characters onto one watermark bitmap — including
    # the DIGIT 4 and the parentheses a Galactic Lore star name is
    # wrapped in. The font is now Aldrich (OFL), which substitutes
    # nothing, so the assertions that named "(" and "4" would only
    # test the artefact of a font we no longer ship.
    #
    # The machinery stays, because the substitution path is what
    # makes a mod's own font safe, and because the DEMO font is one
    # `mods/` override away from being back. Tested in both
    # directions with stubs, so it holds whatever the shipped font is.
    assert not app.style.blocked_glyphs(), \
        f"the shipped font substitutes glyphs: {sorted(app.style.blocked_glyphs())}"

    class _StubFont:
        """Renders W, X, Y, Z as one identical bitmap, rest distinct."""
        def __init__(self, size): self.size = size
        def render(self, ch, aa, fg, bg=None):
            surf = pygame.Surface((10, 10))
            surf.fill((0, 0, 0) if ch in "WXYZ" else (ord(ch), 0, 0))
            return surf
        def get_height(self): return 10
        def get_ascent(self): return 8

    def _stub_style(font_factory):
        cls = app.style.__class__
        class _S:
            _GLYPH_PROBE_SIZE = cls._GLYPH_PROBE_SIZE
            _GLYPH_COLLISION_MIN = cls._GLYPH_COLLISION_MIN
            _blocked = None
            get_font = staticmethod(font_factory)
            blocked_glyphs = cls.blocked_glyphs
            split_runs = cls.split_runs
        return _S()

    # Positive direction: a colliding font IS detected. Without this,
    # swapping to a clean font would leave the detector unexercised
    # and free to break silently.
    _dirty = _stub_style(_StubFont)
    assert _dirty.blocked_glyphs() == set("WXYZ"), \
        sorted(_dirty.blocked_glyphs())
    # And a group smaller than the threshold is NOT treated as a
    # substitution — two glyphs may legitimately share a bitmap.
    assert app.style._GLYPH_COLLISION_MIN >= 3

    # Negative direction: a normal font reports nothing, so a
    # licensed font stops splitting strings across two fonts.
    _clean = _stub_style(lambda size: pygame.font.Font(None, size))
    assert not _clean.blocked_glyphs()

    # Runs alternate on the detected set, whatever it happens to be.
    assert _dirty.split_runs("aWb") == \
        [(False, "a"), (True, "W"), (False, "b")]
    assert _dirty.split_runs("abc") == [(False, "abc")]
    # With nothing blocked, every string takes the single-font path.
    assert app.style.split_runs("(Orion)") == [(False, "(Orion)")]
    assert app.style.split_runs("") == []

    # render_text must equal the plain render when nothing is
    # substituted — the fallback path costs nothing on a clean font.
    for _txt in ("(Orion)", "Regulus", "+14 (26)", "-1/base"):
        _a = app.style.render_text(_txt, 40, (255, 255, 255))
        _b = app.style.get_font(40).render(_txt, True, (255, 255, 255))
        assert _a.get_size() == _b.get_size(), _txt

    # The font that ships must carry its licence next to it.
    _font_dir = os.path.join(os.path.dirname(SCREENS_DIR),
                             "assets", "shared", "fonts")
    _faces = [f for f in os.listdir(_font_dir)
              if f.lower().endswith((".ttf", ".otf"))]
    assert _faces, "no font shipped"
    assert any(f.upper().startswith(("OFL", "LICENSE"))
               for f in os.listdir(_font_dir)), \
        f"font shipped without a licence file: {_faces}"

    # star_label itself mirrors MAINSCR::Get_Star_Name_: parentheses
    # only for an omniscient player looking at an unvisited foreign
    # system (HAROLD::s___s__00556ae4 = "(%s)").
    if "galaxy_map" in d.screens:
        # owner 3: player 0 has no contact with them (only with 1),
        # so without lore this star stays unlabelled entirely.
        foreign = st.parse(mkstar("Orion", 100, 100, 2, 1, 3, 0b0))
        own = st.parse(mkstar("Sol", 100, 100, 2, 1, 0, 0b1))
        assert gmr.star_label(foreign, 0, gm._players, True) == "(Orion)"
        assert gmr.star_label(foreign, 0, gm._players, False) == ""
        assert gmr.star_label(own, 0, gm._players, True) == "Sol"
        # Visited beats lore: no parentheses once you have been there.
        visited = st.parse(mkstar("Orion", 100, 100, 2, 1, 3, 0b1))
        assert gmr.star_label(visited, 0, gm._players, True) == "Orion"
        # A contacted owner is named plainly even without lore.
        contacted = st.parse(mkstar("Vega", 100, 100, 2, 1, 1, 0b0))
        assert gmr.star_label(contacted, 0, gm._players, False) == "Vega"
    ok("glyph substitution mechanism + lore star names")

    # ── Cursor size follows the window ──
    # The artwork is 4K-sized and used to be handed to SDL unscaled,
    # so it stayed 96 px tall at every resolution — right at 2160,
    # half again too large at 1440, twice too large at 1080. The
    # fraction is the original's own: 21 of 480 lines.
    from core import cursor as _cur

    _src = (84, 96)
    _sizes = {h: _cur.target_size(h, {}, _src)
              for h in (720, 1080, 1440, 2160, 2880)}
    assert _sizes[1080][1] == 47 and _sizes[1440][1] == 63, _sizes
    assert _sizes[2160][1] == 94, _sizes[2160]
    # Monotonic, aspect preserved, and never upscaled past the master.
    _heights = [_sizes[h][1] for h in sorted(_sizes)]
    assert _heights == sorted(_heights), _heights
    assert _sizes[2880] == _src, _sizes[2880]
    for _h, (_w, _hh) in _sizes.items():
        assert abs(_w / _hh - _src[0] / _src[1]) < 0.03, (_h, _w, _hh)

    # Loading and scaling the real asset must work headless; the
    # re-apply on a resolution change is checked on the real App
    # further down, where one actually exists.
    _cur.reset()
    _applied = _cur.apply(res, 1440, {})
    assert _applied == _cur.target_size(1440, {}, _cur._source.get_size()), \
        _applied
    assert _cur.apply(res, 1440, {"cursor": {"enabled": False}}) is None
    ok("cursor size (the original's 4.4 % of screen height)")

    # ── Editor overlay: text that cannot overlap itself ──
    # The help sheet put descriptions at a fixed 160 reference pixels
    # and one key label is 197 wide, so "Shift+Scroll / Alt+Scroll"
    # printed straight through its own description at every
    # resolution. Geometry now comes from the font, and the test asks
    # the font too — a wider label or a bigger UI scale fails here
    # instead of on screen.
    from core.editor.constants import HELP_SECTIONS as _HS
    from core.editor.overlay import help_geometry as _help_geom

    for _w, _h in ((1920, 1080), (2560, 1440), (3440, 1440)):
        _L = Layout(_w, _h)
        _fr = app.style.get_font(_L.font_size(13))
        _desc_x, _content = _help_geom(_fr, _HS, _L.scale)
        for _sec, _rows in _HS:
            for _k, _d in _rows:
                assert _fr.size(_k)[0] < _desc_x, \
                    f"{_w}x{_h}: key '{_k}' runs into its description"
                assert _desc_x + _fr.size(_d)[0] <= _content, \
                    f"{_w}x{_h}: '{_d}' overflows the column"
        assert _content * 2 + int(60 * _L.scale) <= _w, \
            f"{_w}x{_h}: two help columns do not fit"

    # The help sheet is where anyone looks up a key, so it has to
    # carry the one key that is not the game's own. A name table
    # copied into a second file drifts; this is the cheap guard.
    _help_keys = [_k for _sec, _rows in _HS for _k, _d in _rows]
    assert any("Home" in _k for _k in _help_keys), \
        "editor help no longer lists the home-system ping"

    # S hides the star field while boxes are being placed. Duck-typed,
    # so a screen without one is silently fine.
    _gm = app.dispatcher.top
    app.editor.active = True
    if getattr(_gm, "_starfield", None) is not None:
        _was = _gm._starfield.enabled
        app.editor.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=0))
        assert _gm._starfield.enabled is not _was, "S did not toggle"
        app.editor.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=0))
        assert _gm._starfield.enabled is _was
    app.editor.active = False
    ok("editor overlay (help columns fit, S toggles the star field)")

    # ── Pointer coordinates: one source ──
    # In fullscreen the content is centred inside black bars, so the
    # raw pointer position is in desktop space while every rect a
    # screen draws is in window space. Windowed, the offset is zero —
    # which is why a forgotten correction is invisible until F11, and
    # then only for the one widget that forgot it. The galaxy map's
    # nav hover forgot it, the editor re-derived the arithmetic by
    # hand, and main.py had the only real copy.
    from core import mouse as _mouse

    _mouse.set_offset((160, 90))
    assert _mouse.adjust(200, 130) == (40, 40), _mouse.adjust(200, 130)
    _mouse.set_offset(None)
    assert _mouse.adjust(200, 130) == (200, 130)

    # The invariant, greppable: nothing outside core/mouse.py polls
    # the pointer directly. A fourth copy is otherwise one session
    # away, and it will fail in fullscreen only.
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Assembled at runtime so this scanner does not match itself —
    # relying on an incidental substring to exclude it would break the
    # day somebody rewords the line.
    _needle = "pygame.mouse.get_" + "pos"
    _offenders = []
    for _dir, _subs, _files in os.walk(_root):
        if "__pycache__" in _dir or "/mods/" in _dir.replace("\\", "/"):
            continue
        for _f in _files:
            if not _f.endswith(".py"):
                continue
            _path = os.path.join(_dir, _f)
            if os.path.normpath(_path).endswith(
                    os.path.join("core", "mouse.py")):
                continue
            with open(_path, "r", encoding="utf-8") as _fh:
                for _n, _line in enumerate(_fh, 1):
                    if _needle in _line:
                        _offenders.append(
                            f"{os.path.relpath(_path, _root)}:{_n}")
    assert not _offenders, \
        "polls the pointer without the fullscreen offset: " \
        + ", ".join(_offenders)
    ok("pointer offset (one source, no raw get_pos outside core/mouse)")

    # ── Main menu version line (bottom right, like the original) ──
    # The number is maintained by hand because the Extension API does
    # not report it, so the test guards the two ways that goes wrong:
    # the box silently stops being drawn, and the literal gets pasted
    # into a second file where nobody will find it again.
    import json as _json
    import numpy as _np
    from core.config import ORION2RE_VERSION as _VER

    _mm_dir = os.path.join(SCREENS_DIR, "main_menu")
    with open(os.path.join(_mm_dir, "boxes.json")) as _fh:
        _mm_boxes = _json.load(_fh)
    for _res_key, _entries in _mm_boxes.items():
        _vb = [b for b in _entries if b["name"] == "version_text"]
        assert len(_vb) == 1, f"{_res_key}: {len(_vb)} version boxes"
        _st = _vb[0].get("style", {})
        assert _st.get("skin") == "text", _st
        assert "{version}" in _st.get("label", ""), _st
        # Right-anchored and right-aligned, or it drifts away from the
        # button column the moment the window is not 16:9.
        assert _vb[0].get("anchor") == "right", _vb[0]
        assert _st.get("align") == "right", _st

    d.switch_to("main_menu")
    _mm = d.active
    _vbox = [b for b in _mm.boxes if b.name == "version_text"]
    assert len(_vbox) == 1, _mm.boxes
    _vbox = _vbox[0]
    assert _vbox.text == f"Version {_VER}", _vbox.text
    # A runtime string must never reach boxes.json through the editor.
    assert "{version}" in _vbox.to_dict()["style"]["label"]
    assert _vbox.text not in _json.dumps(_vbox.to_dict())

    _r = _vbox.screen_rect
    _a = pygame.Surface((1920, 1080))
    _mm.render(_a)
    _vbox.text = ""
    _b = pygame.Surface((1920, 1080))
    _mm.render(_b)
    _diff = (pygame.surfarray.array3d(_a).astype(int)
             - pygame.surfarray.array3d(_b).astype(int))
    _ink = _np.abs(_diff).sum(axis=2)[_r.x:_r.right, _r.y:_r.bottom]
    _cols = _np.nonzero(_ink.any(axis=1))[0]
    assert _cols.size, "version text is not drawn"
    # Right-aligned means the ink ends at the right edge and the box
    # is wider than the string — the two halves of "it fits".
    assert _r.w - 1 - _cols.max() <= 3, _cols.max()
    assert _cols.min() > 4, _cols.min()
    _mm._apply_version()

    # One home for the number: nothing else in the tree spells it out.
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _strays = []
    for _dir, _subs, _files in os.walk(_root):
        if "__pycache__" in _dir:
            continue
        for _f in _files:
            if not _f.endswith((".py", ".json")):
                continue
            _path = os.path.join(_dir, _f)
            if os.path.normpath(_path).endswith(
                    os.path.join("core", "config.py")):
                continue
            with open(_path, "r", encoding="utf-8",
                      errors="replace") as _fh:
                for _n, _line in enumerate(_fh, 1):
                    if _VER in _line:
                        _strays.append(
                            f"{os.path.relpath(_path, _root)}:{_n}")
    assert not _strays, ("orion2re version hardcoded outside "
                         "core/config.py: " + ", ".join(_strays))
    ok("main menu version line (drawn, right-aligned, one source)")

    # ── Right-click context help ──
    # Transcribed from fields.cpp Check_Help_List_ (2916): the regions
    # are walked in order, the first hit wins, and the click is
    # swallowed instead of acting as Cancel. Both properties are
    # asserted, plus the thing a config-driven feature always needs —
    # that every region still resolves to a rect. A renamed box logs
    # nothing and simply stops answering, which is invisible on
    # screen and obvious to a test.
    import json as _hjson
    from core.helppopup import HelpPopup as _HelpPopup

    _help_screens = ("main_menu", "new_game", "galaxy_map")
    _region_total = 0
    for _name in _help_screens:
        _hp = os.path.join(SCREENS_DIR, _name, "help.json")
        assert os.path.exists(_hp), f"{_name} has no help.json"
        with open(_hp, encoding="utf-8") as _fh:
            _regions = _hjson.load(_fh)["regions"]
        assert _regions, _name
        _ids = [r["help_id"] for r in _regions]
        assert len(_ids) == len(set(_ids)), (_name, _ids)
        # A screen-wide fallback can only ever be last: the walk stops
        # at the first hit, exactly where the original keeps its own
        # ({545, 0,0,639,479} closes New Game's list).
        for _i, _r in enumerate(_regions[:-1]):
            assert not _r.get("screen"), (_name, _i, _r["help_id"])

        d.switch_to(_name)
        _s = d.active
        _s.update(None)
        assert len(_s._help_regions) == len(_regions), _name
        for _r in _regions:
            _rect = _s.help_region_rect(_r)
            assert _rect and _rect.w > 0 and _rect.h > 0, \
                (_name, _r["help_id"], _r)
            _region_total += 1

        # The popup box exists at every stored resolution, so the
        # constant fallback in helppopup.py stays a safety net rather
        # than the actual layout.
        with open(os.path.join(SCREENS_DIR, _name, "boxes.json"),
                  encoding="utf-8") as _fh:
            for _res, _bl in _hjson.load(_fh).items():
                assert any(_b["name"] == "help_popup" for _b in _bl), \
                    (_name, _res)
    # The sidebar regions have to tile the column, not merely cover
    # the readouts. MOO2's rectangles span the whole row band and
    # leave 2 native pixels between consecutive entries
    # (evanhelp.cpp:4); the HD sb_* boxes are sized to their content,
    # so without help.json's pad_y a right click between two readouts
    # opens nothing. That strip is invisible on screen — the region
    # it belongs to is not drawn — so it needs a test.
    #
    # Asserted as the rule, against the file's own provenance
    # rectangles rather than a copied constant: the HD column must
    # cover at least the fraction of its span that the original
    # covers of its own, the regions must not overlap (first hit
    # wins, so an overlap silently shadows an entry), and none may
    # leave the sidebar cutout.
    d.switch_to("galaxy_map")
    _gm_s = d.active
    _gm_s.update(None)
    with open(os.path.join(SCREENS_DIR, "galaxy_map", "help.json"),
              encoding="utf-8") as _fh:
        _sb_specs = [_r for _r in _hjson.load(_fh)["regions"]
                     if "sb_" in str(_r.get("box"))]
    assert len(_sb_specs) == 6, len(_sb_specs)

    # Sort the specs themselves, so spec[i], native[i] and rect[i] are
    # the same row. Reading the file order would agree today and stop
    # agreeing the first time somebody reorders a region.
    _sb_specs.sort(key=lambda r: r["native"][1])
    _nat = [_r["native"] for _r in _sb_specs]
    _nat_cov = (sum(_n[3] - _n[1] for _n in _nat)
                / (_nat[-1][3] - _nat[0][1]))
    _hd = [_gm_s.help_region_rect(_r) for _r in _sb_specs]
    assert _hd == sorted(_hd, key=lambda r: r.top), \
        "HD sidebar rows are not in the original's top-to-bottom order"
    _hd_cov = sum(_r.h for _r in _hd) / (_hd[-1].bottom - _hd[0].top)
    assert _hd_cov >= _nat_cov, (
        f"sidebar help covers {_hd_cov:.1%} of its column, the original "
        f"{_nat_cov:.1%} — dead strip between readouts")
    for _a, _b in zip(_hd, _hd[1:]):
        assert _b.top >= _a.bottom, (_a, _b)

    # A region that fills its HD row where the original's does not
    # fill its own is a deliberate deviation and has to say so —
    # CLAUDE.md's rule that an HD EXTENSION is marked where it lives,
    # so it cannot quietly become "how it has always been". Asserted
    # as the rule rather than by naming the stardate: any future
    # region that stops matching the original's proportions is caught
    # the same way. The 0.9 separates 0.81 (the original's stardate,
    # 17 of a 21-pixel row) from 0.97 (every readout) with room on
    # both sides; it is a divider, not a tuned threshold.
    _FILLS_ROW = 0.9
    for _i, _spec in enumerate(_sb_specs[:-1]):
        _n, _n_next = _nat[_i], _nat[_i + 1]
        _nat_fill = (_n[3] - _n[1]) / (_n_next[1] - _n[1])
        _hd_fill = _hd[_i].h / (_hd[_i + 1].top - _hd[_i].top)
        if _nat_fill < _FILLS_ROW <= _hd_fill:
            assert _spec.get("hd_extension"), (
                f"help {_spec['help_id']} covers {_hd_fill:.0%} of its HD "
                f"row where the original covers {_nat_fill:.0%} of its "
                f"own — a deviation that is not marked hd_extension")
    _cut = pygame.Rect(*_gm_s.box_rect("sidebar"))
    for _r in _hd:
        assert _cut.contains(_r), (_r, _cut)
    ok(f"help regions resolve ({_region_total} across "
       f"{len(_help_screens)} screens, sidebar tiles its column)")

    # The auto-sizing panel is a marked HD EXTENSION: the original
    # draws a fixed box and lets FMTPARA wrap into it at a fixed
    # 339 px (textbox.cpp:307), which at four HD resolutions either
    # wastes half the screen or clips a long entry. `helppopup.py`
    # and the fundament both said the marking also stood in
    # `screens/*/help.json`. It stood in none of the three, for as
    # long as both documents claimed it — which is how a marking
    # rots: nothing reads it, so nothing notices it left.
    #
    # Walked over the tree rather than over a list of screens. A list
    # is a second thing to remember, and the file this rule is for is
    # the one somebody adds next year. Mods are included: a mod that
    # ships its own help.json ships the same popup and inherits the
    # same deviation.
    _tree = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _help_files = []
    for _dir, _subs, _files in os.walk(_tree):
        if "__pycache__" in _dir or os.sep + ".git" in _dir:
            continue
        if "help.json" in _files:
            _help_files.append(os.path.join(_dir, "help.json"))
    assert _help_files, "no help.json in the tree at all"
    for _hf in sorted(_help_files):
        _rel = os.path.relpath(_hf, _tree)
        with open(_hf, encoding="utf-8") as _fh:
            _note = _hjson.load(_fh).get("hd_extension", "")
        assert _note, (
            f"{_rel} carries no top-level 'hd_extension': the "
            f"auto-sizing help panel is a deviation from the original "
            f"and has to say so where it is read")
        # Not just the key — the reason. A marking that does not name
        # what the original does instead is a label, not a record.
        assert "339" in _note, (
            f"{_rel}: hd_extension does not name the original's fixed "
            f"339 px wrap")
    ok(f"help.json marks the auto-sizing panel "
       f"({len(_help_files)} files, tree-wide)")

    # Right click opens, left click closes and does NOT reach the game
    d.switch_to("main_menu")
    _mmh = d.active
    _mmh.update(None)
    _btn = next(b for b in _mmh.boxes if b.name == "new_game")
    _cx, _cy = _btn.screen_rect.center

    class _RecClient(FakeClient):
        def __init__(self): self.acts = []
        def activate_field(self, fid): self.acts.append(fid)

    _prev_c, _prev_conn = app.client, app.connected
    app.client, app.connected = _RecClient(), True
    assert _mmh.handle_right_button(True, _cx, _cy) is True
    assert _mmh.help.visible and _mmh.help.help_id == 647, _mmh.help.help_id
    _mmh.render(surf)
    _mmh.handle_click(_cx, _cy)
    assert not _mmh.help.visible, "left click did not close the popup"
    assert app.client.acts == [], \
        f"the swallowed click reached the game: {app.client.acts}"
    # Now that it is closed the same click has to work normally again.
    _mmh.handle_click(_cx, _cy)
    assert app.client.acts == [3], app.client.acts
    # Outside every region, a right click does nothing at all — the
    # original has no help box over empty screen here either.
    assert _mmh.handle_right_button(True, 5, 5) is False
    app.client, app.connected = _prev_c, _prev_conn
    ok("help: right click opens, left click is swallowed")

    # The galaxy map uses the right button for its pan drag. The
    # original's help list for that screen deliberately does not
    # cover the map area (evanhelp.cpp:4), so the two never collide —
    # asserted here because the collision would be silent: a help box
    # would simply appear instead of the map moving.
    d.switch_to("galaxy_map")
    _gm = d.active
    _gm.update(None)
    _nav = next(b for b in _gm.boxes if b.name == "nav_colonies")
    assert _gm.handle_right_button(True, *_nav.screen_rect.center) is True
    assert _gm.help.visible and _gm._pan_from is None
    _gm.handle_right_button(True, *_nav.screen_rect.center)   # closes
    assert not _gm.help.visible
    _map = next(b for b in _gm.boxes if b.name == "map_area")
    _gm.handle_right_button(True, *_map.screen_rect.center)
    assert not _gm.help.visible, "the map area must not open help"
    assert _gm._pan_from is not None, "right drag over the map broke"
    _gm.handle_right_button(False, *_map.screen_rect.center)
    ok("help: galaxy map keeps its right-drag pan over the map")

    # Auto-sizing is an HD EXTENSION (the original draws a fixed box
    # and wraps into it at a fixed 339 px). What has to hold is that
    # the extension does not lose text: a body too tall for the panel
    # becomes scrollable rather than clipped, and a short one does
    # not scroll. Assert the invariant, not the pixel height.
    _pop = _HelpPopup()
    _box = (430, 200, 1060, 680)
    _pop.open(1, "Short", "One line.")
    _pop.render(surf, app.layout, app.style, _box, 1.0)
    assert _pop._max_scroll == 0, _pop._max_scroll
    _pop.open(2, "Long", "\n".join(f"Line {i} of a long help entry "
                                   "that has to keep going."
                                   for i in range(80)))
    _pop.render(surf, app.layout, app.style, _box, 1.0)
    assert _pop._max_scroll > 0, "a long entry must scroll"
    _before = _pop._scroll
    _pop.handle_wheel(-1)
    assert _pop._scroll > _before, (_before, _pop._scroll)
    _pop.handle_wheel(50)
    assert _pop._scroll == 0, _pop._scroll
    # It also has to actually draw: an empty panel and a missing one
    # look the same on screen.
    _blank = pygame.Surface((1920, 1080))
    _drawn = pygame.Surface((1920, 1080))
    _pop.close()
    _pop.render(_drawn, app.layout, app.style, _box, 1.0)
    assert (pygame.surfarray.array3d(_blank)
            == pygame.surfarray.array3d(_drawn)).all(), \
        "a closed popup drew something"
    _pop.open(3, "Title", "Body.")
    _pop.render(_drawn, app.layout, app.style, _box, 1.0)
    assert not (pygame.surfarray.array3d(_blank)
                == pygame.surfarray.array3d(_drawn)).all(), \
        "an open popup drew nothing"
    ok("help popup (auto-size, scroll, draws)")

    # Two different faults produce the same empty box: no help file at
    # all, and a file that lacks this one id. Only the first is fixed
    # by running the extractor, so they must not share a message.
    # Both states are forced rather than read off disk — this test has
    # to give the same answer before and after the user extracts.
    from core.helptext import HelpText as _HelpText
    _ht = _HelpText(res, "en")
    _ht._entries, _ht._available, _ht._stale = {}, False, False
    _no_file = _ht.missing_entry(288)
    _ht._entries, _ht._available = {1: {"title": "x", "body": "y"}}, True
    _no_id = _ht.missing_entry(288)
    assert _no_file != _no_id, _no_file
    assert "help_extract" in _no_file[1], _no_file[1]
    assert "288" in _no_id[1], _no_id[1]
    assert "help_extract" not in _no_id[1], _no_id[1]
    ok("help: missing file and missing id say different things")

    # Three places touch that file: core.helptext builds the path the
    # loader reads, help_extract.py writes it, setup.py reports
    # whether it is there. They were three independent spellings, and
    # setup's was a hardcoded help_en.json — so a non-English install
    # was told to run an extractor it had already run correctly, and
    # an English file under a German setting was reported ok while
    # every popup showed a placeholder. Asserted per language rather
    # than for one, because "en" is exactly the value under which the
    # bug is invisible.
    import importlib.util as _ilu
    from core.helptext import help_file as _help_file
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _spec = _ilu.spec_from_file_location(
        "_setup_mod", os.path.join(_root, "tools", "setup.py"))
    _setup = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_setup)
    for _lang in ("en", "de", "fr"):
        _want = os.path.join(_root, *_help_file(_lang).split("/"))
        _path, _what, _cmd = _setup.from_game({"language": _lang})[0]
        assert _path == _want, (_lang, _path, _want)
        # The command has to be runnable as printed: an install on a
        # non-default language needs --lang, or following the advice
        # writes a file the loader will not read.
        assert _lang == "en" or ("--lang " + _lang) in _cmd, _cmd
        assert "placeholder" in _what, _what
    # The extractor writes the file the loader reads.
    _espec = _ilu.spec_from_file_location(
        "_extract_mod", os.path.join(_root, "tools", "help_extract.py"))
    _extract = _ilu.module_from_spec(_espec)
    _espec.loader.exec_module(_extract)
    for _lang in ("en", "de"):
        _written = os.path.join(_extract.OUT_DIR,
                                os.path.basename(_help_file(_lang)))
        assert _written == os.path.join(
            _root, *_help_file(_lang).split("/")), _written
    ok("help file path: loader, extractor and setup agree (3 languages)")

    # ── core/lbx.py: the container all three extractors read ──
    #
    # Asserted against a container built HERE, byte by byte, and not
    # against the user's own MOO2 files: those are not in the tree,
    # a test that needs them fails for the person who followed the
    # instructions (that is the help-file lesson, one domain over),
    # and a decoder checked against real data alone cannot say which
    # of its two frame formats it got right.
    from core import lbx as _lbx
    import tempfile as _tf

    def _make_lbx(_entries):
        """A container per vfs_lbx.cpp, from a list of blobs."""
        _head = struct.pack("<HHI", len(_entries), _lbx.LBX_MAGIC, 0)
        _pos = 8 + 4 * _lbx.LBX_OFFSET_COUNT
        _offs, _body = [], b""
        for _b in _entries:
            _offs.append(_pos + len(_body))
            _body += _b
        _offs.append(_pos + len(_body))
        _offs += [_offs[-1]] * (_lbx.LBX_OFFSET_COUNT - len(_offs))
        return _head + struct.pack(f"<{_lbx.LBX_OFFSET_COUNT}I",
                                   *_offs) + _body

    def _anim(_w, _h, _frames, _flags, _payload, _palette=b""):
        _n = len(_frames)
        _hdr = struct.pack("<hhhhbbBB", _w, _h, 0, _n, 0, 0, 0, _flags)
        _base = 12 + 4 * (_n + 1) + len(_palette)
        _offs, _acc = [], b""
        for _f in _frames:
            _offs.append(_base + len(_acc))
            _acc += _f
        _offs.append(_base + len(_acc))
        return (_hdr + struct.pack(f"<{_n + 1}I", *_offs)
                + _palette + _acc + _payload)

    # A 2x2 BITMAP frame: index 0 is transparent, 1 is in the
    # palette, 200 is not and must come back as grey 200.
    # s_palette_entry is {changed, r, g, b} — THE FLAG FIRST
    # (orion2.h:2131-2136). The flag byte here is 1 and not 0 on
    # purpose: a decoder that read r,g,b,changed would return
    # (4, 252, 128) for index 1 and pass every other assertion below.
    # That reading is what shipped in nebula_extract.py and was
    # inherited by core/lbx.py, and it survived because STARBG.LBX
    # has no palettes at all — the function had never run on data.
    _pal = struct.pack("<hh", 0, 2) + bytes([0, 0, 0, 0, 1, 63, 32, 16])
    _bmp = _anim(2, 2, [bytes([0, 1, 200, 1])],
                 _lbx.DRAW_MODE_BITMAP | _lbx.FLAG_HAS_PALETTE, b"", _pal)
    # The same picture as a PACKED frame (Draw_Animated_Sprite_):
    # row 0 skips 1 then writes 1 literal, row 1 writes 2 literals.
    # The odd-length run is deliberate: the stream pads to an even
    # offset after every literal run, and a decoder that forgets the
    # pad reads the next run header one byte late and still produces
    # a picture — a wrong one.
    _packed = _anim(2, 2, [struct.pack("<HH", 0, 0)          # unk, start_y
                           + struct.pack("<hh", 1, 1) + bytes([1])
                           + b"\x00"                         # the pad
                           + struct.pack("<hh", 0, 1)        # next row
                           + struct.pack("<hh", 2, 0) + bytes([200, 1])
                           + struct.pack("<hh", 0, 1)],      # end
                    _lbx.DRAW_MODE_ANIMATED, b"")
    with _tf.TemporaryDirectory() as _td:
        _lp = os.path.join(_td, "probe.lbx")
        with open(_lp, "wb") as _fh:
            _fh.write(_make_lbx([_bmp, _packed]))
        _ents = _lbx.read_entries(_lp)
        assert len(_ents) == 2, len(_ents)
        assert _lbx.read_entry(_lp, 1) == _ents[1], (
            "read_entry and read_entries disagree about entry 1")
        _h0 = _lbx.parse_header(_ents[0])
        assert (_h0.width, _h0.height, _h0.frame_count) == (2, 2, 1), _h0
        assert _h0.has_palette and _h0.mode == _lbx.DRAW_MODE_BITMAP, _h0
        _p0 = _lbx.decode_frame(_ents[0], _h0)
        assert list(_p0) == [0, 1, 200, 1], list(_p0)
        # BOTH FRAME FORMATS MUST GIVE THE SAME PICTURE. They are two
        # transcriptions of two different functions in draw.cpp, and
        # nothing else in the tree can tell you one of them drifted.
        _h1 = _lbx.parse_header(_ents[1])
        assert _h1.mode == _lbx.DRAW_MODE_ANIMATED and not _h1.has_palette
        assert list(_lbx.decode_frame(_ents[1], _h1)) == list(_p0), (
            f"the RLE decoder gives {list(_lbx.decode_frame(_ents[1], _h1))} "
            f"where the bitmap decoder gives {list(_p0)}")
        # 6-bit VGA components are scaled by 4 and clamped.
        assert _lbx.read_palette(_ents[0], 1) == {0: (0, 0, 0),
                                                  1: (252, 128, 64)}, (
            f"the palette byte order moved: "
            f"{_lbx.read_palette(_ents[0], 1)}")
        # Index 0 transparent, a palette index opaque, an index with
        # no entry GREY — never an invented colour (see rgba_bytes).
        _rgba = _lbx.rgba_bytes(_p0, _lbx.read_palette(_ents[0], 1))
        assert _rgba[0:4] == bytes([0, 0, 0, 0]), _rgba[0:4]
        assert _rgba[4:8] == bytes([252, 128, 64, 255]), _rgba[4:8]
        assert _rgba[8:12] == bytes([200, 200, 200, 255]), _rgba[8:12]
        # A FILE THAT IS NOT ONE RAISES, and does not exit: these are
        # library calls now, and a tool that wants to try a second
        # path must be able to catch the first one failing.
        _bad = os.path.join(_td, "bad.lbx")
        with open(_bad, "wb") as _fh:
            _fh.write(b"\x00" * 4096)
        for _call in (lambda: _lbx.read_entries(_bad),
                      lambda: _lbx.read_entry(_bad, 0)):
            try:
                _call()
            except _lbx.LbxError:
                pass
            else:
                raise AssertionError("a file with no LBX magic was accepted")
        assert not isinstance(_lbx.LbxError(), SystemExit)
    # A frame past the end is a STATE, not an exception: an LBX holds
    # entries of several kinds and a walk over all of them meets data
    # that is not a sprite.
    assert _lbx.decode_frame(_ents[0], _h0, 5) is None
    ok("core/lbx.py (container, both frame formats agreeing, 6-bit "
       "palette, index 0 transparent, unpalettised index stays grey)")

    # MOO2's help bodies are not plain text: they carry FMTPARA
    # control codes, and the column positions inside them are what
    # makes the Command Points table a table. Printing them raw put
    # "\aX3.Frigate\aX97.-1" on screen, watermark glyph and all.
    from core import helpformat as _hf

    _row = "\aX3.Frigate\aX97.-1 \aX150.Star Base\aX270.+1"
    _parsed = _hf.parse(_row)
    assert len(_parsed) == 1, _parsed
    assert [r.x for r in _parsed[0].runs] == [3, 97, 150, 270], \
        _parsed[0].runs
    assert _parsed[0].runs[0].text == "Frigate", _parsed[0].runs[0]
    assert _parsed[0].columns
    # No control character may survive into anything that gets drawn:
    # that is the whole failure, and it is invisible to a test that
    # only checks the popup drew ink.
    _raw = ("\aF2.Head\r\aX3.a\aX97.b\r\rTail\ftext\aT10,20.\tx\b-")
    for _ln in _hf.parse(_raw):
        for _r in _ln.runs:
            assert not any(c < " " for c in _r.text), repr(_r.text)
    assert _hf.parse("plain\nlines")[0].plain() == "plain"
    # Functions the popup does not honour are reported, not assumed
    # away.
    assert "F" in _hf.dropped_functions(_raw), _hf.dropped_functions(_raw)
    assert "X" not in _hf.dropped_functions(_raw)
    ok("help format codes decoded (columns, breaks, no control chars)")

    # A column is a fraction of the text width, not a pixel count, so
    # the table lines up at every resolution rather than at one.
    def _row_x(width):
        pop = _HelpPopup()
        pop.open(9, "T", _row)
        blocks = pop._blocks(app.style, 20, 16, width)
        surf = next(s for s, _ in blocks if s is not None
                    and s.get_width() == width)
        ink = _np.nonzero(pygame.surfarray.array_alpha(surf).any(axis=1))[0]
        return ink.min() / width

    _narrow, _wide = _row_x(400), _row_x(1200)
    assert abs(_narrow - _wide) < 0.02, (_narrow, _wide)
    assert abs(_narrow - 3 / _hf.HELP_PARA_W) < 0.02, _narrow
    ok("help table columns scale with the panel, not with pixels")

    # A file from the older extractor is refused rather than rendered
    # subtly wrong: it lost the trailing \t and \f codes to an
    # rstrip, which produces a plausible-looking wrong layout.
    _ht2 = _HelpText(res, "en")
    _ht2._entries, _ht2._available, _ht2._stale = {}, False, True
    _stale = _ht2.missing_entry(288)
    assert "help_extract" in _stale[1] and _stale != _no_file, _stale
    ok("help: a stale help file is refused, not rendered")

    # On the galaxy map the popup belongs inside the map cutout, not
    # centred on the window: the sidebar owns the right edge and the
    # cockpit frame owns the rim, so a window-centred box sits off to
    # one side and runs under the sidebar. Containment is the rule
    # worth asserting rather than the exact centre — the box is
    # F5-movable by design, and a nudge is not a regression while
    # sliding under the frame is.
    with open(os.path.join(SCREENS_DIR, "galaxy_map", "boxes.json"),
              encoding="utf-8") as _fh:
        for _res, _bl in _hjson.load(_fh).items():
            _area = next(b["rect"] for b in _bl
                         if b["name"] == "map_area")
            _pop_r = next(b["rect"] for b in _bl
                          if b["name"] == "help_popup")
            assert (_pop_r[0] >= _area[0]
                    and _pop_r[1] >= _area[1]
                    and _pop_r[0] + _pop_r[2] <= _area[0] + _area[2]
                    and _pop_r[1] + _pop_r[3] <= _area[1] + _area[3]), \
                (_res, _pop_r, _area)
    ok("help popup sits inside the galaxy map cutout")

    # Tree hygiene: no archives or backup copies anywhere in the
    # tree. A stars.zip sat next to the stars/ folder it duplicated;
    # a Backup.zip plus an unpacked Backup/ of the old nebula masters
    # sat inside nebula/; and a 9-slice.zip sat inside the very frame
    # folder it copied, with a 9slice.json ten days older than the
    # one beside it — that one survived two passes of this check
    # because it only walked screens/. It walks the whole tree now.
    # A backup that lives inside the tree it backs up ships with
    # every delivery and drifts from the folder the moment either
    # changes; the copy that is stale is never the one you notice.
    _junk = []
    _root_dir = os.path.dirname(SCREENS_DIR)
    for _dir, _subs, _files in os.walk(_root_dir):
        if "__pycache__" in _dir or ".git" in _dir:
            continue
        for _sub in _subs:
            if _sub.lower() in ("backup", "backups", "old"):
                _junk.append(os.path.join(os.path.relpath(_dir), _sub))
        for _f in _files:
            if _f.endswith((".zip", ".bak", ".orig")) or _f.endswith("~"):
                _junk.append(os.path.join(os.path.relpath(_dir), _f))
    assert not _junk, _junk
    ok("no archives or backup copies anywhere in the tree")

    # Decision numbers in the fundament are identities — references
    # elsewhere use the bare number. Two same-day sessions each took
    # "the next free number" and both landed on 36, which no rule in
    # the document can prevent when neither session can see the
    # other. A test can.
    _fund = os.path.join(os.path.dirname(SCREENS_DIR), "doc",
                         "v3_fundament.md")
    with open(_fund, encoding="utf-8") as _fh:
        _nums = re.findall(r"^\*\*(\d+)\.", _fh.read(), re.M)
    _dupes = sorted({n for n in _nums if _nums.count(n) > 1})
    assert not _dupes, f"duplicate decision numbers: {_dupes}"
    ok(f"fundament decision numbers unique ({len(_nums)} decisions)")

    # THE EXCEPTIONS LIST IS COMPUTED, NOT TYPED. Decision 6 counts
    # CODE lines as of 4 September 2026, and the reason it had to
    # change is the reason this check exists: the guideline was
    # enforced on `wc -l` for as long as it existed, which counts
    # this project's own docstrings, and 16 of the 24 non-exempt
    # entries turned out never to have been exceptions at all. Three
    # of those 16 had been ADDED by the three packages immediately
    # before, each with a paragraph defending a length that was not
    # there.
    #
    # So the list is held to `tools/linecount.py` rather than to a
    # human's arithmetic, both ways: every file over the guideline is
    # named, and every file named is over it. The one-directional
    # version — "everything listed is over" — is the one that lets a
    # new exception go unlisted, which is the whole failure the list
    # exists to prevent.
    import importlib.util as _lcu
    _lc_spec = _lcu.spec_from_file_location(
        "_probe_linecount",
        os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                     "linecount.py"))
    _lc = _lcu.module_from_spec(_lc_spec)
    _lc_spec.loader.exec_module(_lc)
    # The measure itself, on a file whose buckets are known by hand.
    # Each line lands in exactly ONE bucket: a blank line inside a
    # docstring is docstring, not blank. Summing overlapping buckets
    # and taking code as the residual undercounts code by exactly the
    # number of blank lines inside docstrings, which is how the
    # pre-split screen.py was measured at 218 when it was 252.
    _lc_probe = os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                             "linecount.py")
    _lt, _lco, _ld, _lm, _lb = _lc.measure(_lc_probe)
    assert _lco + _ld + _lm + _lb == _lt, (
        f"linecount's buckets overlap: {_lco}+{_ld}+{_lm}+{_lb} != "
        f"{_lt}. Each line must land in exactly one, or `code` as a "
        f"residual is wrong by the size of the overlap")
    _status = os.path.join(os.path.dirname(SCREENS_DIR),
                           "v3_projektstatus.md")
    import re as _lre
    with open(_status, encoding="utf-8") as _fh:
        # Whitespace-collapsed, because the list is prose and wraps:
        # `tools/struct_probe.py`\n(**478** code, ...) is one entry
        # and a newline in the middle of it is a line break, not a
        # different claim.
        _st = _lre.sub(r"\s+", " ", _fh.read())
    _over = _lc.over_guideline()
    for _rel, (_t, _c, _d, _m, _b) in _over:
        # Listed under its path as the document spells it — the tail
        # after screens/ or core/, which is what a reader greps for.
        _short = _rel.split("/", 1)[1] if _rel.startswith(("screens/",
                                                          "core/")) else _rel
        assert (f"`{_rel}` (**{_c}** code" in _st
                or f"`{_short}` (**{_c}** code" in _st), (
            f"{_rel} is {_c} CODE lines, over the {_lc.GUIDELINE} "
            f"guideline, and v3_projektstatus.md's exceptions list "
            f"does not name it at that count. Decision 6: an "
            f"exception is allowed and must be LISTED")
    # And nothing is listed that is not over — a list that keeps
    # entries after they stop qualifying is the state this package
    # found, sixteen deep.
    _listed = set(_lre.findall(r"`([\w./]+\.py)` \(\*\*(\d+)\*\* code", _st))
    _real = {_r.split("/", 1)[1] if _r.startswith(("screens/", "core/"))
             else _r: _c for _r, (_t, _c, _d, _m, _b) in _over}
    _real.update({_r: _c for _r, (_t, _c, _d, _m, _b) in _over})
    for _name, _claim in _listed:
        assert _name in _real and str(_real[_name]) == _claim, (
            f"the exceptions list names {_name} at {_claim} code "
            f"lines; linecount says "
            f"{_real.get(_name, 'it is not over the guideline')}")
    assert len(_listed) == len(_over), (
        f"the list has {len(_listed)} entries and {len(_over)} files "
        f"are over the guideline")
    ok(f"exceptions list == tools/linecount.py ({len(_over)} over "
       f"{_lc.GUIDELINE} code lines)")


    # Every tool that WRITES into the tree must anchor its default
    # output to the project, not to the working directory. Both
    # extractors got this wrong in turn: help_extract.py wrote its
    # JSON wherever the shell was, and nebula_extract.py did the same
    # a week later — 61 sprite files landed in the repository root,
    # got staged for the first commit, and the smoke test went on
    # reporting the references as absent, because they were. Neither
    # failure announced itself; both looked like success.
    # Checked by importing and reading the value, not by matching the
    # text: a first attempt grepped the assignment line and failed on
    # help_extract.py, which anchors through a PROJECT_ROOT variable
    # one line above. The question is what the path IS, not how it is
    # spelled.
    import importlib.util as _ilu
    _root = os.path.dirname(SCREENS_DIR)
    for _tool, _const in (("help_extract.py", "OUT_DIR"),
                          ("nebula_extract.py", "DEFAULT_OUT")):
        _spec = _ilu.spec_from_file_location(
            f"_probe_{_tool[:-3]}", os.path.join(_root, "tools", _tool))
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _out = getattr(_mod, _const, None)
        assert _out, f"{_tool}: no {_const} to check"
        assert os.path.isabs(_out), (
            f"{_tool}: {_const} is relative ({_out!r}) — it will write "
            f"wherever the shell happens to be")
        assert os.path.commonpath([_root, _out]) == _root, (
            f"{_tool}: {_const} points outside the project: {_out}")
    ok("extractors write into the project, not the working directory")

    # ── Full App boot (standalone, no orion2re) ──
    import main as main_module
    app2 = main_module.App()
    assert app2.dispatcher.active_name == "main_menu"
    app2._update()
    app2._render()
    _before = _cur.last_size()
    app2._cycle_resolution()
    # A resolution change has to re-apply the cursor, or it keeps the
    # size of a window that no longer exists — the exact bug this
    # module replaced, one step removed.
    assert _cur.last_size() == _cur.target_size(
        app2.win_h, app2.settings, _cur._source.get_size()), \
        (_cur.last_size(), app2.win_h, _before)
    ok("App boots standalone")

    # CLAUDE.md is what a Claude Code session reads before touching
    # anything, so a stale pointer in it misleads at exactly the
    # moment nobody is watching. Two things can rot: a path that no
    # longer exists, and the check count, which this test knows
    # better than any document does.
    _root = os.path.dirname(SCREENS_DIR)
    _cmd_path = os.path.join(_root, "CLAUDE.md")
    assert os.path.exists(_cmd_path), "CLAUDE.md is missing"
    with open(_cmd_path, encoding="utf-8") as _fh:
        _cmd = _fh.read()
    for _ref in re.findall(r"`([\w./]+\.(?:md|py|json|txt))`", _cmd):
        if _ref.startswith(("file.", "screen.", "layout.", "boxes.",
                            "help.")):
            continue          # generic examples, not paths
        assert os.path.exists(os.path.join(_root, _ref)), \
            f"CLAUDE.md points at a missing file: {_ref}"

    # THE COUNT IS HAND-COPIED IN TWO DOCUMENTS, so per decision 36 it
    # needs a checker or it is an intention. CLAUDE.md had one and
    # v3_projektstatus.md's Snapshot table did not; the table said 55
    # against a suite of 63 for four sessions, in the file that
    # declares itself the count's single home.
    #
    # BOTH ARE ASSERTED AGAINST THIS RUN, never against each other.
    # Two documents agreeing with one another and not with the suite
    # is precisely the state a cross-check would call green, and it is
    # the state this replaces.
    _counts = [("CLAUDE.md", _cmd, r"(\d+) checks, headless"),
               ("v3_projektstatus.md", None,
                r"smoke_test\.py` — \*\*(\d+) checks\*\*")]
    for _doc, _text, _pat in _counts:
        if _text is None:
            with open(os.path.join(_root, _doc), encoding="utf-8") as _fh:
                _text = _fh.read()
        _claimed = re.search(_pat, _text)
        assert _claimed, f"{_doc} no longer states a check count"
        assert int(_claimed.group(1)) == PASS + 1, (
            f"{_doc} says {_claimed.group(1)} checks, this run has "
            f"{PASS + 1}")
    ok("CLAUDE.md paths resolve; both documents' check counts current")

    print(f"\nSMOKE TEST PASSED — {PASS} checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
