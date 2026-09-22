# smoke-suite area: empire_identity
#
# Part of the OrionLayer smoke suite — 005_empire_identity_empire_identity_grid_click_inputs_tab.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (90 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - empire_identity (grid click, inputs, tab, image zoom/pan)
#   - custom_race Accept -> empire_identity (lock 50/51, release 13)
#   - custom_race negative picks (popup blocks Accept, modal)
#   - new_game panel skins (9-slice inside thin border)
#   - injection chain (ruler -> banner -> home star, lock release)
#   - injection chain survives a silent gap (mapgen, no fields)
#   - reconnect drops the stale field list
#   - empire_identity busy panel (INVENTION, drawn + animated)


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
    # Custom Race Accept -> Empire Identity, held for IDs 50 and 51
    d.switch_to("custom_race")
    cr = d.active
    fr = cr._get_active_frame()
    bx, by, bw, bh = fr.button_rect_right(1920, 1080)
    cr.handle_click(bx + bw // 2, by + bh // 2)
    assert d.active_name == "empire_identity", d.active_name
    for gid in (50, 51):
        class GS: current_screen = gid
        d.update_from_game(GS())
        assert d.active_name == "empire_identity", (gid, d.active_name)
    class GS13: current_screen = 13
    d.update_from_game(GS13())
    assert d.active_name == "new_game", d.active_name
    ok("custom_race Accept -> empire_identity (lock 50/51, release 13)")

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
