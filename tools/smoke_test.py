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
import math
import os
import re
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
    assert fh.screen_of(res.screen_file(
        "colony_summary", "assets", "frame.png")) == "colony_summary"
    fw, fhh, holes = fh.find_holes(
        res.screen_file("colony_summary", "assets", "frame.png"))
    assert len(holes) == 14, len(holes)
    named = fh.name_holes(holes, "colony_summary")
    assert [fw, fhh] == cs._data["frame"]["image_size"], (fw, fhh)
    for name, r in named.items():
        want = fh.to_ref(r, fw, fhh)
        got = (cs._data["frame"]["title_rect"] if name == "title"
               else list(cs.box_rect(name)))
        assert all(abs(a - b) <= 2 for a, b in zip(got, want)), \
            (name, got, want)
    # Seven sort cutouts, same size within a few px, evenly spaced.
    sorts = [cs.box_rect(f"sort_{k}") for k in fh.SORT_KEYS]
    assert all(s is not None for s in sorts)
    ws = [s[2] for s in sorts]
    assert max(ws) - min(ws) <= 6, ws
    gaps = [sorts[i + 1][0] - (sorts[i][0] + sorts[i][2])
            for i in range(6)]
    assert max(gaps) - min(gaps) <= 6, gaps

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

    # Clicking a sort button records the key and would inject.
    class _Cap:
        def __init__(self): self.calls = []
        def inject_click(self, x, y): self.calls.append((x, y))
        def activate_field(self, f): pass
        def inject_key(self, k): pass
    cap = _Cap()
    app.client, was = cap, app.connected
    app.connected = True
    bx, by, bw, bh = cs.layout.rect(cs.box_rect("sort_food"))
    cs.handle_click(bx + bw // 2, by + bh // 2)
    assert cs._sort_key == "food"
    assert cap.calls == [tuple(btns["food"]["native_click"])], cap.calls
    app.client, app.connected = FakeClient(), was
    cs.render(pygame.display.get_surface())
    ok("colony_summary (frame cutouts == boxes.json, native clicks, "
       "empire rows)")

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
    # API; both must be recoverable from MAP_MAX_X (mapgen.cpp).
    for mx, exp_scale, exp_zoom in ((506, 10, 0), (759, 15, 1),
                                    (1012, 20, 2), (1518, 30, 3)):
        assert zt.max_map_scale(mx) == exp_scale, mx
        assert zt.max_zoom_count(mx) == exp_zoom, mx
    # A big galaxy NOT at maximum zoom-out must keep its star names.
    assert zt.names_suppressed(100, 15, 30) is False
    assert zt.names_suppressed(100, 30, 30) is True

    # AXIS SEPARATION. Icon size depends on the ZOOM LEVEL only.
    # Galaxy size just caps how far out the user may zoom; it must
    # never scale anything by itself. Fully zoomed in (scale 10)
    # every galaxy size draws the identical icon.
    for map_max_x in (506, 759, 1012, 1518):
        z = zt.zoom_level(10, zt.max_zoom_count(map_max_x))
        assert z == 0, map_max_x
        assert zt.star_dimension(0, z) == 33, map_max_x
        assert zt.black_hole_dimension(z) == 39, map_max_x
    # Fully zoomed OUT they differ — but only because the reachable
    # zoom level differs, not because of a galaxy-size factor.
    out = {mx: zt.star_dimension(0, zt.zoom_level(
        zt.max_map_scale(mx), zt.max_zoom_count(mx)))
        for mx in (506, 759, 1012, 1518)}
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
        for scale, map_max, expect_zoom in ((10, 506, 0), (15, 759, 1),
                                            (20, 1012, 2), (30, 1518, 3)):
            gs.map_scale, gs.map_max_x = scale, map_max
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
            gs.map_scale, gs.map_max_x = scale, 2277   # max scale 45
            gm.update(gs)
            ctx = gm._map_context()
            big[scale] = (ctx.zoom, ctx.star_px(0))
        assert [z for z, _ in big.values()] == [0, 1, 2, 3], big
        px = [p for _, p in big.values()]
        assert px == sorted(px, reverse=True) and px[0] > px[-1], big
        gs.stars = stock_stars

        # And the clamp itself: a small galaxy stays at zoom 0 even
        # if some other scale is reported.
        gs.map_scale, gs.map_max_x = 30, 506
        gm.update(gs)
        assert gm._map_context().zoom == 0, "max_zoom_count must clamp"
        gs.map_scale, gs.map_max_x = 15, 759

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
            gs.map_scale, gs.map_max_x = 10, 506
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
            gs.map_max_x = 1518                    # Huge: rungs 10..30
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
            gs.map_scale, gs.map_max_x = 10, 506
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
            for scale, map_max in ((10, 1518), (30, 1518)):
                gs.map_scale, gs.map_max_x = scale, map_max
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

        gs.map_scale, gs.map_max_x = 15, 759

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
        for scale, map_max in ((10, 506), (30, 1518)):
            gs.map_scale, gs.map_max_x = scale, map_max
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
        gs.map_scale, gs.map_max_x = 15, 759
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
    # ── "No Farming" survives a FULL track ──
    # The label lives under the bar now, not in a horizontal tail: the
    # tail cost 150 reference px of the one budget every row shares,
    # the band under the bar is spare height row_height already pays
    # for. What that placement has to prove is the thing its first
    # position failed — the label was once drawn at the bar's left
    # edge and the worker squares painted over it, every number right
    # and nothing on screen. So: a 42-slot row, every slot filled,
    # and the label's own colour must still be on the surface.
    _surf.fill((0, 0, 0))
    _cl.render(_surf, [{"name": "Full", "pops": _cl.POP_LIMIT_CAP,
                        "jobs": [0, 30, 12], "no_farming": True,
                        "max_pop": _cl.POP_LIMIT_CAP}],
               _area, _cfg, app.layout, app.style)
    _px = pygame.surfarray.array3d(_surf)
    _label_ink = [(x, y) for x in range(_area.x, _area.right)
                  for y in range(_area.y, _area.bottom)
                  if tuple(_px[x, y]) == tuple(_cl.NO_FARM_COLOR[:3])]
    assert _label_ink, (
        "'No Farming' is not on the surface for a full 42-slot row — "
        "the squares are painted over it again")
    # And it is BELOW the bar, not inside it: inside is where the
    # squares are, and a label that happens to survive today because
    # one slot is empty is the same bug waiting.
    _t = _cl.track_metrics(_area, _cfg, app.layout.scale)
    _bar_top = (_area.y + int(_cfg["pad_y"] * app.layout.scale)
                + (_t.row_h - _t.bar_h) // 2)
    assert min(y for _x, y in _label_ink) >= _bar_top + _t.bar_h, (
        "'No Farming' is drawn inside the bar's own band, where the "
        "filled squares are")

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

    # The preview tool's fake rows must stay the shape build_rows
    # actually produces. Nothing else would notice: a row dict that
    # has drifted still renders, so the preview would go on looking
    # right while showing something the game cannot produce — and a
    # preview is trusted precisely because it looks like the screen.
    # Keys, not values: the values are invented on purpose.
    import importlib.util as _plu
    _pv_spec = _plu.spec_from_file_location(
        "_probe_colony_preview",
        os.path.join(os.path.dirname(SCREENS_DIR), "tools",
                     "colony_list_preview.py"))
    _pv = _plu.module_from_spec(_pv_spec)
    _pv_spec.loader.exec_module(_pv)
    for _fake in _pv.ROWS:
        assert set(_fake) == set(_rows[0]), (
            f"colony_list_preview row {_fake.get('name')!r} has keys "
            f"{sorted(_fake)} against build_rows' {sorted(_rows[0])}")
    ok("colony list (rows, No Farming below a full track, name clipped "
       "to its column, INVENTION + HD EXTENSION marked, preview rows "
       "match build_rows)")

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
    _claimed = re.search(r"(\d+) checks, headless", _cmd)
    assert _claimed, "CLAUDE.md no longer states a check count"
    assert int(_claimed.group(1)) == PASS + 1, (
        f"CLAUDE.md says {_claimed.group(1)} checks, this run has "
        f"{PASS + 1}")
    ok("CLAUDE.md: every path resolves, check count current")

    print(f"\nSMOKE TEST PASSED — {PASS} checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
