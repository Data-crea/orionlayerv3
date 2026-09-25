# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 007_galaxy_map_galaxy_map_transform_name_rules_sideba.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 4 check(s) it holds:
#   - galaxy_map (transform, name rules, sidebar, click/hotkeys)
#   - galaxy map parks only into its own list shape: nothing sent to a research-shaped list at screen 
#   - galaxy_map anchored zoom (pointer-fixed, clamps, parking)
#   - galaxy_map frame cutouts == boxes.json


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
    # Through the real click path (brief 110: mapclick.plan), on the
    # anchor star, which the zoomed-in view is sure to show.
    rec2.log.clear()
    csx, csy = v1.to_screen(gs.stars[1].x, gs.stars[1].y)
    gm.handle_click(int(round(csx)), int(round(csy)))
    want = mc.galaxy_to_native(gs.stars[1].x, gs.stars[1].y, gs)
    assert [e for e in rec2.log if e[0] == "click"] == \
        [("click", *want)], (rec2.log, want)
    # 2. Parking uses the zoom-OUT field only, throttled; the
    # game is not yet at max scale (15 vs its 15... use a state
    # copy that is zoomed in) — simulate scale 10:
    gs.map_scale = 10
    # The galaxy map's own list, recorded live (work order 128 C: the
    # map parks only where the zoom-out button and the grid are in the
    # list, and to the index it finds there).
    import json as _pk_json
    from core.game_state import FieldInfo as _PkField
    _pk_rec = _pk_json.load(open(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools", "galaxy_box_fields.json")))

    def _pk_fields(rows):
        out = []
        for _r in rows:
            _f = _PkField()
            (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
             _f.hotkey) = _r
            out.append(_f)
        return out
    _pk_saved_fields = getattr(gs, "fields", None)
    gs.fields = _pk_fields(_pk_rec["closed"])
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
    # AND NOT INTO ANOTHER LIST UNDER THE SAME SCREEN NUMBER (work order
    # 128 C). The turn-start research prompt runs under screen 0
    # (mainscr2.cpp:119), and in its list field 9 is a choice row whose
    # commit reads the pointer (tech.cpp:354-369). Shaped as
    # doc/tech_change_reading.md section 2 builds it: dummy, choice
    # rows, eight entry blocks, category radios, the whole-screen field.
    gs.map_scale = 10
    _pk_research = [(0, 0, 0, 0, 0, 0, 0)]
    for _k, (_ex, _ey) in enumerate([(176, 30), (403, 31), (176, 135),
                                     (403, 135), (176, 240), (403, 240),
                                     (176, 347), (403, 347)]):
        _pk_research.append((len(_pk_research), _ex, _ey + 21,
                             _ex + 218, _ey + 54, 7, 0))
    for _ex, _ey in [(176, 30), (403, 31), (176, 135), (403, 135),
                     (176, 240), (403, 240), (176, 347), (403, 347)]:
        _pk_research.append((len(_pk_research), _ex - 2, _ey + 18,
                             _ex + 215, _ey + 99, 7, 0))
    for _ex, _ey in [(102, 30), (329, 31), (102, 135), (329, 135)]:
        _pk_research.append((len(_pk_research), _ex, _ey, _ex + 60,
                             _ey + 15, 1, 0))
    _pk_research.append((len(_pk_research), 0, 0, 639, 479, 7, 0))
    gs.fields = _pk_fields(_pk_research)
    assert gs.fields[9].field_type == 7          # a row, not zoom-out
    for _ in range(3):
        gm._viewctl._park_sent = 0.0
        rec2.log.clear()
        gm.update(gs)
        assert rec2.log == [], (
            f"the map parked into a research-shaped list at screen 0: "
            f"{rec2.log}")
    # The same list with the zoom-out button moved to another index
    # parks to THAT index — the number is read, never assumed.
    _pk_moved = [r if r[0] != 9 else (9, 244, 428, 298, 443, 0, 43)
                 for r in _pk_rec["closed"]] + [(24, 244, 455, 298, 473, 0, 45)]
    gs.fields = _pk_fields(_pk_moved)
    gm._viewctl._park_sent = 0.0
    rec2.log.clear()
    gm.update(gs)
    assert rec2.log == [("act", 24)], rec2.log
    gs.fields = _pk_saved_fields
    gs.map_scale = 15
    ok("galaxy map parks only into its own list shape: nothing sent to a "
       "research-shaped list at screen 0, and the zoom-out index read live")
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

    # THE HUD IS THE SECOND SOURCE FOR EVERY GALAXY BOX — decision 71,
    # work order 169. This replaced "galaxy_map frame cutouts ==
    # boxes.json": the frame image is no longer drawn, so its holes are
    # the holes of a picture nobody sees, and the check that held the
    # boxes to them measured nothing. What the boxes follow now is the
    # HUD's measured layout, and `tools/hud_boxes.py` writes them from
    # it; a box dragged off its place in the artwork fails here.
    import hud_boxes as _hb
    _hb_icons = {_k: _v[1] for _k, _v in
                 ((_n[5:], _p) for _n, _p in _hc_pieces().items()
                  if _n.startswith("icon_"))}
    _hb_want = _hb.owned(icons=_hb_icons)
    for _hb_key in ("1920x1080", "2560x1440"):
        _hb_file = {_b["name"]: _b for _b in _hj.load(open(
            res.screen_file("galaxy_map", "boxes.json")))[_hb_key]}
        for _hb_n, _hb_b in _hb_want.items():
            assert _hb_n in _hb_file, f"{_hb_key}: {_hb_n} missing"
            assert all(abs(_a - _c) <= 1 for _a, _c in zip(
                _hb_file[_hb_n]["rect"], _hb_b["rect"])), (
                f"{_hb_key}/{_hb_n}: boxes.json {_hb_file[_hb_n]['rect']} "
                f"but the HUD puts it at {_hb_b['rect']} — run "
                f"python tools/hud_boxes.py --write, or move the artwork")
    assert gm._frame_scaled is None, (
        "the galaxy map loaded its frame image again; decision 71 draws "
        "the HUD instead")
    gm.render(pygame.display.get_surface())
    ok(f"galaxy_map boxes == the HUD's measured layout "
       f"({len(_hb_want)} boxes, 2 resolutions)")
