# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 011_galaxy_map_galaxy_map_stand_in_exactly_amoeba.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (91 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 13 check(s) it holds:
#   - galaxy map stand-in: exactly amoeba and antaran reach the player-ship fallback, marked DEVIATION
#   - galaxy_map ship icons (kinds, tinting, owner, sizing)
#   - galaxy_map box state (live lists: closed, fleet, monster, system, modal; a moved box followed; u
#   - galaxy_map icon hit test (icon before star, point inside the icon, decision 65 guard, decision 6
#   - galaxy_map box identity (Popup_XY_ against the live windows, planet fields by orbit, every misma
#   - galaxy_map HD boxes (drawn when the identity holds, CLOSE, ESC and a planet send their field, no
#   - fleet selection on the wire (FSEL after the owners: ship_idx and flag per node, the box's chain;
#   - fleet selection in the HD box (blue and black from the wire, MSG_SELECT_SHIP 0x85, orders only w
#   - galaxy_map destination lines (own moving, foreign bound for our colony or any outpost, the fleet
#   - galaxy_map colour wave (Draw_Directional_Multi_Colored_Line_ table and offset, one step per ctx.
#   - galaxy_map map lines (one routine, maplines.stroke; the wormhole through it; B1, B2 and the omis
#   - galaxy_map icon 9 x 8 against the 12 x 11 header: a DELIBERATE DEVIATION, the tables unequal and
#   - galaxy_map eta label (Print_Eta_On_Ship_Icon_: who, text, the owner's header from the HD viewpor


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

    # THE STAND-IN IS FOR EXACTLY TWO KINDS (Data, 14 September 2026,
    # fundament 64). The amoeba and the antaran have no HD master and
    # draw as the grey player ship — a marked DEVIATION, kept because
    # a monster that vanished from the map would be a gap against the
    # original. A master that arrives, or one that goes missing,
    # changes this set; then the status document's known gap and the
    # marking change with it, in the same commit.
    _player_prefix = shi.sprite_key(shi.PLAYER_KIND, "")
    _stand_in = {kind for kind in shi.MONSTER_KINDS.values()
                 if any(shi._resolve_sprite(gm._cache, kind, _st)
                        .startswith(_player_prefix)
                        for _st in range(zt.icon_step_count()))}
    assert _stand_in == {"amoeba", "antaran"}, (
        f"the player-ship stand-in is drawn for {sorted(_stand_in)}, "
        f"marked for amoeba and antaran")
    assert "DEVIATION" in shi._resolve_sprite.__doc__ and \
        "AMOEBA and the ANTARAN" in shi._resolve_sprite.__doc__
    assert "Amoeba and Antaran" in open(os.path.join(
        os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
        encoding="utf-8").read(), (
        "the status document's known gaps no longer name the two "
        "stand-ins")
    # AND THE AMOEBA'S FOOTPRINT IS MEASURED, off BUFFER0.LBX entry
    # 245 with a threshold sweep; the copy of the eel is gone.
    assert zt.MONSTER_ICON_DIM_ZOOM0["amoeba"] == (13, 13)
    assert "copy of eel" not in open(zt.__file__, encoding="utf-8").read()
    ok("galaxy map stand-in: exactly amoeba and antaran reach the "
       "player-ship fallback, marked DEVIATION and named in the status "
       "document; the amoeba's footprint is measured")

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

    # Owner resolution. The node table comes off the wire (open fix 20
    # revision 2) and is validated against star_idx before it is used.
    def mkship(owner, location, x=0, y=0, status=0):
        r = bytearray(_ship.SIZE)
        _s.pack_into("<b", r, 99, owner)
        _s.pack_into("<b", r, 100, status)
        _s.pack_into("<hhh", r, 101, location, x, y)
        return _ship.parse(bytes(r))

    def mkicon(node_idx, star_idx, x=100, y=100):
        return ship_icon.parse(
            _s.pack("<6h", 0, node_idx, star_idx, 0, x, y))

    # The rule brief 119 paid for: no node table is rebuilt from
    # _ship[] anywhere. Sort_Ships_In_Stack_ moves ships between the
    # nodes of a stack with an unstable qsort, so the only table is
    # the wire's.
    import types as _nt
    from screens.galaxy_map import boxmodel as _nt_bm
    assert not hasattr(shi, "build_node_map") \
        and not hasattr(_nt_bm, "stack_of") \
        and not hasattr(_nt_bm, "selection_of"), "a rebuilt node table"
    assert shi.wire_nodes(None) is None
    assert shi.wire_nodes(_nt.SimpleNamespace(fleet_selection={
        "stack": -1, "ships": [4, 2], "selected": [False, False],
        "chain": []})) == [4, 2]

    # Two players at ONE star: the per-star guess cannot answer,
    # the node table can. This is the case the whole thing exists
    # for, so assert the exact colours, not just "not None".
    mixed = [mkship(2, 11), mkship(5, 11, x=4)]
    icons = [mkicon(0, 11), mkicon(1, 11)]
    assert shi.owners_from_nodes(icons, mixed, [0, 1]) == [2, 5]
    assert shi.resolve_owners(icons, mixed, [0, 1]) == [2, 5]
    # Node order is NOT array order: the table decides, not the index.
    assert shi.owners_from_nodes(icons, mixed, [1, 0]) == [5, 2]
    assert shi.owners_from_nodes(icons, mixed, None) is None

    # star_idx is the RAW encoded location (Ship_Stack_Star_Id_),
    # so a moving ship still validates.
    moving = [mkship(4, 10042)]
    assert shi.owners_from_nodes([mkicon(0, 10042)], moving, [0]) == [4]

    # Validation: a node pointing at a ship whose location does not
    # match star_idx means the map is stale. Reject the WHOLE set —
    # a half-trusted map paints plausible wrong colours.
    assert shi.owners_from_nodes([mkicon(0, 99)], mixed, [0, 1]) is None
    assert shi.owners_from_nodes([mkicon(7, 11)], mixed, [0, 1]) is None
    assert shi.owners_from_nodes([mkicon(0, 11)], mixed, [9]) is None
    assert shi.owners_from_nodes(icons, [], [0, 1]) is None

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

    # ── Brief 110 Part A: the box state and the icon hit test ──
    # The movable boxes are read off the live field list, recorded on
    # the reference save (tools/galaxy_box_fields.json). A click on a
    # fleet icon must reach the FLEET and not the star it orbits
    # (Check_Ships_XY_ before Check_Stars_XY_, mainscr_main.cpp:425-438);
    # with the fleet box open the order flips, and a click the game
    # would read as a move order is not sent (decision 65). No test
    # here may send a fleet order: the guard is what this asserts.
    import inspect as _bx_insp
    import json as _bx_json
    from core.game_state import FieldInfo as _BxField
    from screens.galaxy_map import mapboxes as gmb, mapclick as gmc

    _bx = _bx_json.load(open(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools", "galaxy_box_fields.json")))

    def _bx_fields(rows):
        out = []
        for _r in rows:
            _f = _BxField()
            (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
             _f.hotkey) = _r
            out.append(_f)
        return out

    _bx_closed = gmb.classify(_bx_fields(_bx["closed"]))
    assert _bx_closed.known and not _bx_closed.open, _bx_closed
    _bx_own = gmb.classify(_bx_fields(_bx["fleet_own"]["fields"]))
    assert _bx_own.known and _bx_own.fleet and not _bx_own.system
    assert _bx_own.fleet.rect == (329, 205, 527, 421), _bx_own.fleet.rect
    assert (_bx_own.fleet.close.index, _bx_own.fleet.close.hotkey) == \
        (27, 0x1B), _bx_own.fleet.close
    _bx_mon = gmb.classify(_bx_fields(_bx["fleet_monster"]["fields"]))
    assert _bx_mon.fleet and _bx_mon.fleet.rect == (329, 261, 527, 421)
    assert not any(f.field_type == 0 and f.hotkey == 0
                   for f in _bx_mon.fleet.fields), \
        "a monster's fleet box carries no ALL field (fleetpop.cpp:172)"
    _bx_sys = gmb.classify(_bx_fields(_bx["system"]["fields"]))
    assert _bx_sys.system and not _bx_sys.fleet
    assert _bx_sys.system.rect == (180, 148, 527, 421)
    assert _bx_sys.system.close.index == 21
    assert gmb.classify(_bx_fields(_bx["modal"]["fields"])).modal
    # A box that has moved is wherever the list says it is.
    _bx_moved = [list(_r) for _r in _bx["fleet_own"]["fields"]]
    for _r in _bx_moved[21:29]:
        _r[1] -= 150
        _r[3] -= 150
        _r[2] -= 100
        _r[4] -= 100
    _bx_mv = gmb.classify(_bx_fields(_bx_moved))
    assert _bx_mv.fleet and _bx_mv.fleet.rect == (179, 105, 377, 321), \
        _bx_mv.fleet
    # A list it cannot read is reported as unreadable, never guessed.
    _bx_broken = [_r for _r in _bx["fleet_own"]["fields"] if _r[0] != 28]
    assert not gmb.classify(_bx_fields(_bx_broken)).known
    ok("galaxy_map box state (live lists: closed, fleet, monster, "
       "system, modal; a moved box followed; unreadable said so)")

    class _BxRec:
        def __init__(self):
            self.log = []

        def inject_click(self, x, y):
            self.log.append(("click", x, y))

        def activate_field(self, i):
            self.log.append(("act", i))

        def inject_key(self, k):
            self.log.append(("key", k))

        def cancel_field(self, i):
            self.log.append(("cancel", i))

    def _bx_sent(kind):
        return [e for e in app.client.log if e[0] == kind]

    _bx_real = (app.client, app.connected, gs.fields, gs.ship_icons)
    try:
        app.client, app.connected = _BxRec(), True
        gm._viewctl.reset()
        gs.fields = _bx_fields(_bx["closed"])
        gm.update(gs)
        _bx_zoom = gm._game_zoom()
        _bx_cfg = gm._data.get("ship_icons") or {}
        _bx_sol = gs.stars[0]
        _bx_scx, _bx_scy = mc.galaxy_to_native(_bx_sol.x, _bx_sol.y, gs)
        _bx_w, _bx_h = shi.native_size(shi.PLAYER_KIND, _bx_zoom)
        # An own fleet whose centre is 3 native px right of Sol: inside
        # the star's click radius in both frames, the case that sent
        # every fleet click to the star until now.
        gs.ship_icons = ship_icon.parse_all([
            _s.pack("<6h", 0, 0, 0, 0, _bx_scx + 3 - _bx_w // 2,
                    _bx_scy - _bx_h // 2),
            _s.pack("<6h", 0, 1, 0, 0, 330, 150)])
        for _ic in gs.ship_icons:
            _ic.set_derived("owner", 0)
        gm.update(gs)
        _bx_ctx = gm._map_context()

        def _bx_centre(i):
            _l, _t, _w, _h = shi.icon_box(gs.ship_icons[i], 0, _bx_ctx,
                                          None, _bx_cfg)
            return int(_l + _w / 2), int(_t + _h / 2)

        _bx_hx, _bx_hy = _bx_centre(0)
        assert gm._star_at(_bx_hx, _bx_hy) is _bx_sol, \
            "the test icon must sit on Sol's HD hit area"
        _bx_r0 = gmc.native_icon_rect(gs.ship_icons[0], 0, _bx_zoom)
        gm.handle_click(_bx_hx, _bx_hy)
        _bx_c = _bx_sent("click")
        assert len(_bx_c) == 1, app.client.log
        assert (_bx_r0[0] <= _bx_c[0][1] <= _bx_r0[2]
                and _bx_r0[1] <= _bx_c[0][2] <= _bx_r0[3]), (_bx_c, _bx_r0)
        assert _bx_c[0][1:] != (_bx_scx, _bx_scy), "the star got the click"

        # Fleet box open: stars first, and this click would move the
        # fleet to Sol — decision 65, nothing goes out.
        app.client.log.clear()
        gs.fields = _bx_fields(_bx["fleet_own"]["fields"])
        gm.update(gs)
        gm.handle_click(_bx_hx, _bx_hy)
        assert _bx_sent("click") == [], app.client.log
        # ...an icon clear of every star still reaches its stack,
        app.client.log.clear()
        gm.handle_click(*_bx_centre(1))
        _bx_r1 = gmc.native_icon_rect(gs.ship_icons[1], 0, _bx_zoom)
        _bx_c = _bx_sent("click")
        assert len(_bx_c) == 1 and _bx_r1[0] <= _bx_c[0][1] <= _bx_r1[2] \
            and _bx_r1[1] <= _bx_c[0][2] <= _bx_r1[3], (_bx_c, _bx_r1)
        # ...and a black hole is exempt: no move is ever ordered there
        # (mainscr_main.cpp:481).
        app.client.log.clear()
        _bx_rift = gs.stars[3]
        _bx_rx, _bx_ry = _bx_ctx.view.to_screen(_bx_rift.x, _bx_rift.y)
        gm.handle_click(int(_bx_rx), int(_bx_ry))
        assert _bx_sent("click") == [("click", *mc.galaxy_to_native(
            _bx_rift.x, _bx_rift.y, gs))], app.client.log

        # An earlier icon covering the centre is stepped around: the
        # game takes the first icon in array order.
        _bx_twin = ship_icon.parse_all([_s.pack("<6h", 0, 0, 0, 0, 200, 200),
                                        _s.pack("<6h", 0, 1, 0, 0, 204, 200)])
        _bx_p = gmc.icon_click_point(_bx_twin, [0, 0], 1, _bx_zoom)
        _bx_ra = gmc.native_icon_rect(_bx_twin[0], 0, _bx_zoom)
        assert _bx_p is not None and not (
            _bx_ra[0] <= _bx_p[0] <= _bx_ra[2]
            and _bx_ra[1] <= _bx_p[1] <= _bx_ra[3]), (_bx_p, _bx_ra)

        # Decision 66: no CANCEL_FIELD while a box is open.
        _bx_bx, _bx_by, _bx_bw, _bx_bh = _bx_ctx.view.box
        _bx_mx, _bx_my = int(_bx_bx + _bx_bw / 2), int(_bx_by + _bx_bh / 2)
        for _bx_name in ("system", "fleet_own"):
            app.client.log.clear()
            gs.fields = _bx_fields(_bx[_bx_name]["fields"])
            gm.update(gs)
            gm.handle_right_button(True, _bx_mx, _bx_my)
            gm.handle_right_button(False, _bx_mx, _bx_my)
            assert _bx_sent("cancel") == [], (_bx_name, app.client.log)
        app.client.log.clear()
        gs.fields = _bx_fields(_bx["closed"])
        gm.update(gs)
        gm.handle_right_button(True, _bx_mx, _bx_my)
        gm.handle_right_button(False, _bx_mx, _bx_my)
        assert _bx_sent("cancel") == [("cancel", 23)], app.client.log

        assert "DEVIATION" in gmc.__doc__ and "DECISION 65" in gmc.__doc__
        # The handling moved to `mapinput` (work order 126 F); the hook
        # must still reach it, and the marking lives where the rule does.
        from screens.galaxy_map import mapinput as _bx_mi
        assert "mapinput.right_button" in _bx_insp.getsource(
            type(gm).handle_right_button)
        assert "DECISION 66" in _bx_insp.getsource(_bx_mi.right_button)
    finally:
        app.client, app.connected, gs.fields, gs.ship_icons = _bx_real
        gm.update(gs)
    ok("galaxy_map icon hit test (icon before star, point inside the "
       "icon, decision 65 guard, decision 66 no cancel under a box)")

    # ── Brief 110 Part A step 2: HD draws the system window and the
    # fleet box, and only when the live list agrees with the last HD
    # click (decision A2). Popup_XY_ is held to the three windows
    # measured live; Yian's two planet fields are held to the planets
    # the engine resolves them to (field 23 opened the outpost, 239).
    from core.game_state import PLANET_SIZE as _BX_PLANET
    from core.structs import colony as _bx_colony
    from screens.galaxy_map import boxdraw as gbd, boxmodel as gbm

    assert gbm.popup_xy(0, 121, 79, 347, 273) == (180, 148)
    assert gbm.fleet_xy(131, 39, 198, 216) == (329, 205)
    assert gbm.fleet_xy(437, 183, 198, 160) == (22, 261)

    def _bx_planet(star_i, orbit, colony):
        _r = bytearray(_BX_PLANET)
        _s.pack_into("<hhbbb", _r, 0, colony, star_i, orbit, 3, 2)
        _r[9] = 5
        return bytes(_r)

    def _bx_ship(owner, loc, x, y, status=0):
        _r = bytearray(_ship.SIZE)
        _s.pack_into("<bbhhh", _r, 99, owner, status, loc, x, y)
        return bytes(_r)

    _bx_yian = bytearray(mkstar("Yian", 360, 210, 2, 1, 0, 0b1))
    _s.pack_into("<5h", _bx_yian, 195, -1, -1, -1, 239, 240)
    _bx_player0 = bytearray(PLAYER_SIZE)
    _bx_player0[21:27] = b"Humans"
    gs2 = GameState()
    gs2.current_screen, gs2.player_num = 0, 0
    gs2.map_scale, gs2.map_max_x, gs2.map_max_y = 36, 1518, 1200
    # Aten in ANOTHER quadrant (native 409, 37): a star in Yian's own
    # quadrant gets the same window, and only its planets tell it apart.
    gs2.stars = st.parse_all([mkstar("Aten", 1400, 60, 2, 1, 0, 0b1),
                              mkstar("Bor", 1400, 1100, 2, 1, 0, 0b1),
                              bytes(_bx_yian)])
    gs2.player_raw = [bytes(_bx_player0)] + [bytes(PLAYER_SIZE)] * 7
    _bx_planets = [bytes(_BX_PLANET)] * 241
    _bx_planets[239] = _bx_planet(2, 3, 54)
    _bx_planets[240] = _bx_planet(2, 4, -1)
    gs2.planets_raw = _bx_planets
    _bx_col = bytearray(_bx_colony.SIZE)
    _bx_col[6] = 1                                   # outpost, owner 0
    gs2.colonies_raw = [bytes(_bx_colony.SIZE)] * 54 + [bytes(_bx_col)]
    gs2.fields = _bx_fields(_bx["system"]["fields"])
    assert mc.galaxy_to_native(360, 210, gs2) == (121, 79)

    _bx_sysbox = gmb.classify(gs2.fields).system
    _bx_m, _bx_why = gbm.system_model(
        gs2, gbm.Identity("system", star=2), _bx_sysbox, None, False)
    assert _bx_m is not None, _bx_why
    assert [(p["field"], p["planet"], p["orbit"])
            for p in _bx_m["planets"]] == [(23, 239, 3), (24, 240, 4)], \
        _bx_m["planets"]
    assert _bx_m["close"] == 21
    _bx_m, _bx_why = gbm.system_model(
        gs2, gbm.Identity("system", star=0), _bx_sysbox, None, False)
    assert _bx_m is None and "would put it" in _bx_why, _bx_why
    _bx_planets[239] = _bx_planet(2, 1, 54)          # wrong orbits
    _bx_planets[240] = _bx_planet(2, 2, -1)
    _bx_m, _bx_why = gbm.system_model(
        gs2, gbm.Identity("system", star=2), _bx_sysbox, None, False)
    assert _bx_m is None and "orbits" in _bx_why, _bx_why
    _bx_planets[239] = _bx_planet(2, 3, 54)
    _bx_planets[240] = _bx_planet(2, 4, -1)

    _bx_fleetbox = gmb.classify(
        _bx_fields(_bx["fleet_own"]["fields"])).fleet
    gs2.ships_raw = [_bx_ship(0, 1, 300, 100)] * 4 + [_bx_ship(0, 5, 9, 9)]
    _bx_ident = gbm.Identity("fleet", ship=0, icon=(131, 39))
    # The stack and its cell order are the wire's chain, after the
    # engine's in-stack sort: node 0 carries ship 3, not ship 0.
    gs2.fleet_selection = {"stack": 2, "ships": [3, 1, 0, 2, 4],
                           "selected": [False] * 5, "chain": [0, 1, 2, 3]}
    _bx_m, _bx_why = gbm.fleet_model(gs2, _bx_ident, _bx_fleetbox, None)
    assert _bx_m is not None and _bx_m["stack"] == [3, 1, 0, 2] \
        and _bx_m["nodes"] == [0, 1, 2, 3], (_bx_m, _bx_why)
    assert _bx_m["close"] == 27
    assert gbm.fleet_model(gs2, gbm.Identity("fleet", ship=0,
                           icon=(400, 300)), _bx_fleetbox, None)[0] is None
    for _bx_wire, _bx_word in (
            (None, "FSEL"),
            ({"stack": -1, "ships": [3, 1, 0, 2, 4],
              "selected": [False] * 5, "chain": []}, "no fleet box"),
            ({"stack": 2, "ships": [3, 1, 4, 2, 0],
              "selected": [False] * 5, "chain": [0, 1, 2, 3]},
             "not one stack"),
            ({"stack": 2, "ships": [3, 1, 0, 2, 4],
              "selected": [False] * 5, "chain": [0, 1, 3]},
             "not in the stack")):
        gs2.fleet_selection = _bx_wire
        _bx_m, _bx_why = gbm.fleet_model(gs2, _bx_ident, _bx_fleetbox,
                                         None)
        assert _bx_m is None and _bx_word in _bx_why, (_bx_wire, _bx_why)
    gs2.ships_raw = [_bx_ship(0, 1, 300, 100)] * 3
    gs2.fleet_selection = {"stack": 2, "ships": [2, 1, 0],
                           "selected": [False] * 3, "chain": [0, 1, 2]}
    _bx_m, _bx_why = gbm.fleet_model(gs2, _bx_ident, _bx_fleetbox, None)
    assert _bx_m is None and "stack of 3" in _bx_why, _bx_why
    gs2.ships_raw = []
    gs2.fleet_selection = None
    ok("galaxy_map box identity (Popup_XY_ against the live windows, "
       "planet fields by orbit, every mismatch refused)")

    _bx_real2 = (app.client, app.connected)
    try:
        app.client, app.connected = _BxRec(), True
        gm._viewctl.reset()
        gm.update(gs2)
        gm._box_identity = gbm.Identity("system", star=2)
        _bx_probe = pygame.Surface((app.win_w, app.win_h))
        _bx_probe.fill((0, 0, 0))
        gm._render_map(_bx_probe)
        _bx_hits = gm._box_hits
        assert sorted(i for _, i in _bx_hits if i is not None) == \
            [21, 23, 24], _bx_hits
        _bx_panel = _bx_hits[0][0]
        assert pygame.surfarray.array3d(_bx_probe)[
            _bx_panel.x:_bx_panel.right,
            _bx_panel.y:_bx_panel.bottom].any(), "the box drew nothing"
        for _bx_field in (21, 23):
            app.client.log.clear()
            gm.handle_click(*next(r for r, i in _bx_hits
                                  if i == _bx_field).center)
            assert app.client.log == [("act", _bx_field)], app.client.log
        app.client.log.clear()
        gm.handle_key(pygame.K_ESCAPE)
        assert app.client.log == [("act", 21)], app.client.log
        app.client.log.clear()
        assert gm.handle_click(_bx_panel.x + 3, _bx_panel.bottom - 3) \
            is None and app.client.log == [], app.client.log
        gm._box_identity = gbm.Identity("system", star=0)
        _bx_probe.fill((0, 0, 0))
        gm._render_map(_bx_probe)
        assert gm._box_hits == [], "a box drawn against a wrong identity"
        assert "OMISSION" in gbd.__doc__ and "DEVIATION" in gbd.__doc__
        assert "DEVIATION" in gbm.__doc__
    finally:
        app.client, app.connected = _bx_real2
        gm._box_identity = None
        gm.update(gs)
    ok("galaxy_map HD boxes (drawn when the identity holds, CLOSE, ESC "
       "and a planet send their field, nothing else inside, nothing "
       "drawn against a wrong identity)")

    # ── Brief 117 phase 1: the fleet selection, read and written ──
    # No engine carries open fixes 20 and 21 yet, so the wire is built:
    # a snapshot tail in the patches' exact layout, and the live field
    # list of the own four-ship box recorded in brief 110 Stop 1.
    from core import game_client as _sel_gc
    from core.game_state import parse_state as _sel_parse

    def _sel_snapshot(tail):
        _b = bytearray()
        _b += _s.pack("<hbihhhhhB b", 0, -1, 100, 0, 2, 0, 0, 0, 0, 0)
        _b += _s.pack("<hhhhh", 15, 0, 0, 759, 600)
        _b += bytes(SETTINGS_SIZE)
        _b += bytes(PLAYER_SIZE * 8)
        _b += _s.pack("<h", 0) * 4               # stars ships cols planets
        _b += bytes([0])                          # nebulas
        _b += bytes(LEADER_SIZE * 67)
        _b += bytes(ANTARAN_SIZE)
        _b += _s.pack("<h", 2)                    # 2 ship icons
        _b += _s.pack("<6h", 0, 0, 5, 0, 100, 100)
        _b += _s.pack("<6h", 0, 1, 6, 0, 140, 100)
        _b += _s.pack("<8h", 0, 0, 0, 0, 0, 0, 0, 0)
        return _sel_parse(bytes(_b) + tail)

    def _sel_block(stack, ships, flags, chain):
        return (b"FSEL" + _s.pack("<hh", stack, len(flags))
                + b"".join(_s.pack("<hB", i, 1 if f else 0)
                           for i, f in zip(ships, flags))
                + _s.pack("<h", len(chain))
                + b"".join(_s.pack("<h", n) for n in chain))

    assert _sel_snapshot(b"").fleet_selection is None
    _sel_gs = _sel_snapshot(bytes([2, 0xFF]))
    assert _sel_gs.fleet_selection is None
    assert _sel_gs.ship_icons[0].owner == 2
    _sel_gs = _sel_snapshot(bytes([2, 0xFF]) + _sel_block(
        3, [7, 5, 6], [True, False, True], [2, 0]))
    assert _sel_gs.fleet_selection == {
        "stack": 3, "ships": [7, 5, 6], "selected": [True, False, True],
        "chain": [2, 0]}, _sel_gs.fleet_selection
    assert _sel_gs.ship_icons[0].owner == 2 and \
        _sel_gs.ship_icons[1].owner is None, "the owners moved"
    # Open fix 20 REVISION 1 (one byte per node, no ship index, no
    # chain) reads as no block: its table was the wrong one.
    assert _sel_snapshot(bytes([2, 0xFF]) + b"FSEL"
                         + _s.pack("<hh", 3, 3) + bytes([1, 0, 1])
                         ).fleet_selection is None, "revision 1 read"
    assert _sel_snapshot(bytes([2, 0xFF]) + _sel_block(
        3, [7, 5, 6], [True] * 3, [2, 3])).fleet_selection is None, \
        "a chain node beyond the table"
    assert _sel_snapshot(bytes([2, 0xFF]) + _sel_block(
        3, [7, 5, 6], [True] * 3, [0, 1, 2])[:-1]
                         ).fleet_selection is None, "a short chain read"

    # The model: the cells are the chain's nodes in order, each ship
    # the node's ship_idx, each colour the node's byte.
    gs2.fields = _bx_fields(_bx["fleet_own"]["fields"])
    gs2.ships_raw = [_bx_ship(0, 1, 300, 100)] * 4 + \
        [_bx_ship(0, 5, 9, 9)]
    _sel_ident = gbm.Identity("fleet", ship=0, icon=(131, 39))
    _sel_box = gmb.classify(gs2.fields).fleet
    _sel_wire = {"stack": 2, "ships": [3, 1, 0, 2, 4],
                 "selected": [True, False, True, True, False],
                 "chain": [0, 1, 2, 3]}
    gs2.fleet_selection = _sel_wire
    _sel_m, _sel_why = gbm.fleet_model(gs2, _sel_ident, _sel_box, None)
    assert _sel_m and _sel_m["stack"] == [3, 1, 0, 2] \
        and _sel_m["selected"] == [True, False, True, True], \
        (_sel_m, _sel_why)
    assert _sel_m["selectable"] == [True] * 4 and _sel_m["count"] == 4
    for _sel_bad in ({"stack": -1, "ships": [3, 1, 0, 2, 4],     # closed
                      "selected": [True] * 5, "chain": []},
                     None):                                    # no patch
        gs2.fleet_selection = _sel_bad
        _sel_m, _ = gbm.fleet_model(gs2, _sel_ident, _sel_box, None)
        assert _sel_m is None, _sel_bad
    ok("fleet selection on the wire (FSEL after the owners: ship_idx and "
       "flag per node, the box's chain; revision 1 and every unknown "
       "state draw no box)")

    class _SelRec(_BxRec):
        def select_ship(self, ship, selected):
            self.log.append(("select", ship, selected))

    _sel_real = (app.client, app.connected)
    try:
        app.client, app.connected = _SelRec(), True
        gm._viewctl.reset()
        gs2.fleet_selection = _sel_wire
        gm.update(gs2)
        gm._box_identity = _sel_ident
        _sel_probe = pygame.Surface((app.win_w, app.win_h))
        _sel_probe.fill((0, 0, 0))
        gm._render_map(_sel_probe)
        _sel_cells = [(r, a) for r, a in gm._box_hits
                      if isinstance(a, tuple)]
        # Cell i is chain node i: ship 3 first, as the engine sorted.
        assert [a for _, a in _sel_cells] == [
            ("select", 3, False), ("select", 1, True),
            ("select", 0, False), ("select", 2, False)], gm._box_hits
        _sel_px = pygame.PixelArray(_sel_probe)
        for (_sel_r, _), _sel_want in zip(_sel_cells, (True, False)):
            _sel_rgb = _sel_probe.unmap_rgb(
                _sel_px[_sel_r.x + 4, _sel_r.y + 4])[:3]
            assert tuple(_sel_rgb) == tuple(
                (gbd.SELECTED if _sel_want else gbd.DESELECTED)[:3]), \
                (_sel_rgb, _sel_want)
        del _sel_px
        app.client.log.clear()
        gm.handle_click(*_sel_cells[1][0].center)
        assert app.client.log == [("select", 1, True)], app.client.log
        assert gbd.orders_ok(gm)
        # A star click sent as an ORDER keeps the fleet identity: the
        # game keeps the box open (run 119), HD must keep drawing it.
        _sel_star = gmc.Plan("star", (121, 79), "Yian", target=2)
        gbm.remember(gm, _sel_star, [], order=True)
        assert gm._box_identity is _sel_ident, gm._box_identity
        gbm.remember(gm, _sel_star, [])
        assert gm._box_identity.kind == "system", gm._box_identity
        gm._box_identity = _sel_ident
        # Without the block: no box, no cell click, the guard stands.
        gs2.fleet_selection = None
        gm.update(gs2)
        gm._render_map(_sel_probe)
        assert not any(isinstance(a, tuple) for _, a in gm._box_hits)
        assert not gbd.orders_ok(gm)
        # The guard itself: a move-order click refused, then allowed.
        _sel_yian = gs2.stars[2]
        _sel_args = (gmb.classify(gs2.fields), _sel_yian, None, [], [],
                     gs2.stars, gs2, 0, (121, 79))
        assert gmc.plan(*_sel_args).what == "refused"
        _sel_go = gmc.plan(*_sel_args, orders_ok=True)
        assert _sel_go.what == "star" and _sel_go.send == (121, 79), _sel_go
        # HD STATE: the scroll bar past nine ships is drawn, not operated.
        _sel_probe.fill((0, 0, 0))
        _sel_grid = pygame.Rect(400, 300, 300, 240)
        gbd._draw_scroll(gm, _sel_probe, _sel_grid, 12)
        assert pygame.surfarray.array3d(_sel_probe)[
            _sel_grid.right:_sel_grid.right + 14,
            _sel_grid.y:_sel_grid.bottom].any(), "no scroll bar drawn"
        assert "HD STATE" in gbd._draw_scroll.__doc__
    finally:
        app.client, app.connected = _sel_real
        gm._box_identity = None
        gs2.fleet_selection = None
        gm.update(gs)
    _sel_sent = []
    _sel_client = _sel_gc.GameClient()
    _sel_client._send_message = lambda t, p: _sel_sent.append((t, p))
    _sel_client.select_ship(7, True)
    _sel_client.select_ship(7, False)
    assert _sel_sent == [(0x85, _s.pack("<hB", 7, 1)),
                         (0x85, _s.pack("<hB", 7, 0))], _sel_sent
    import version_check as _sel_vc
    # Applied and confirmed live (briefs 118, 119): required, not
    # reported — a tree without them fails the checker. The fleet
    # SCREEN's two (work order 134 C, open fixes 27 and 28) are
    # required as well but NOT confirmed live; they are listed here
    # so that adding a fleet patch without a marker fails, and the
    # two pairs are kept apart so the pairing stays visible: 20/21
    # is the galaxy map's box, 27/28 is screen 4.
    assert {k: v[1] for k, v in _sel_vc.LOCAL_PATCHES.items()
            if "fleet" in k} == {
        "doc/ext_fleet_selection.patch": "fsel_chain_len",
        "doc/ext_fleet_select_ship.patch": "Select_Ship_",
        "doc/ext_fleet_screen_state.patch": "_fltscrn_stack_owner",
        "doc/ext_fleet_screen_select.patch": "Select_Fltscrn_Ship_"}
    assert not any("fleet" in k for k in _sel_vc.REPORTED_PATCHES)
    ok("fleet selection in the HD box (blue and black from the wire, "
       "MSG_SELECT_SHIP 0x85, orders only with a known selection, "
       "scroll bar as HD STATE, both patches in the checker)")

    # ── Brief 110 Part B (brief 121): the destination lines ──
    from screens.galaxy_map import maplines as gml
    from core.structs import ship as _ml_ship_spec
    # Who gets a line (Do_Ship_Destination_Lines_). Yian (star 2) has
    # an outpost in gs2's planets, Bor (star 1) nothing; len(stars) is
    # Antares.
    _ml_raws = [_bx_ship(0, 10000, 500, 500, status=1),   # own, moving
                _bx_ship(0, 2, 360, 210),                 # own, parked
                _bx_ship(3, 10002, 600, 400, status=1),   # to our outpost
                _bx_ship(3, 10001, 700, 400, status=1),   # to nothing
                _bx_ship(0, 10003, 800, 400, status=1),   # Antares
                _bx_ship(0, 20001, 360, 210, status=2)]   # order turn
    _ml_ships = [_ship.parse(r) for r in _ml_raws]
    _ml_icons = [ship_icon.parse(_s.pack("<6h", 0, i, 0, 0, 100 + 20 * i,
                                         100)) for i in range(6)]
    _ml_gs = GameState()
    _ml_gs.player_num = 0
    _ml_gs.stars = gs2.stars
    _ml_gs.planets_raw, _ml_gs.colonies_raw = gs2.planets_raw, \
        gs2.colonies_raw
    _ml_gs.ship_icons = _ml_icons
    _ml_gs.fleet_selection = {"stack": -1, "ships": list(range(6)),
                              "selected": [False] * 6, "chain": []}

    def _ml_lines(zoom):
        return [(l["icon"], l["ship"], l["star"], l["colour"], l["start"])
                for l in gml.destination_lines(_ml_gs, _ml_ships,
                                               _ml_gs.stars, zoom)]

    assert _ml_lines(2) == [(0, 0, 0, "green", (106, 105)),
                            (2, 2, 2, "red", (146, 105)),
                            (5, 5, 1, "green", (206, 105))], _ml_lines(2)
    # The start is the icon corner plus half of BUFFER0.LBX entry
    # 205 + (3 - zoom)'s header, measured at the sprite (brief 121).
    assert [l[4] for l in _ml_lines(0)] == [(108, 106), (148, 106),
                                            (208, 106)], _ml_lines(0)
    assert [l[4] for l in _ml_lines(3)][0] == (105, 105), _ml_lines(3)
    assert zt.SHIP_ICON_HEADER_DIM == ((11, 11), (12, 11), (12, 10),
                                       (16, 12))
    assert zt.ship_icon_header_dimension(-1) == (11, 11) and \
        zt.ship_icon_header_dimension(9) == (16, 12)
    # The open fleet box's head node gets one too, while encoded.
    _ml_gs.fleet_selection = dict(_ml_gs.fleet_selection, stack=0,
                                  chain=[3])
    assert (3, 3, 1, "red", (166, 105)) in _ml_lines(2), _ml_lines(2)
    # The node table decides which ship an icon is, never the index.
    _ml_gs.fleet_selection = {"stack": -1, "ships": [5, 1, 2, 3, 4, 0],
                              "selected": [False] * 6, "chain": []}
    assert _ml_lines(2)[0][:4] == (0, 5, 1, "green"), _ml_lines(2)
    _ml_gs.fleet_selection = None
    assert _ml_lines(2) == [], "a line without the wire's node table"
    assert [n for n, _o, _k in _ml_ship_spec.SPEC.fields
            if n in ("travelling_speed", "turns_left")] == [
        "travelling_speed", "turns_left"]
    ok("galaxy_map destination lines (own moving, foreign bound for our "
       "colony or any outpost, the fleet box head; encoded locations "
       "only; start at the measured header half)")

    # The colour wave, transcribed; its step and clock, HD EXTENSION B2.
    _ml_t = tuple(range(8))
    _ml_r = tuple(reversed(_ml_t))
    assert gml.directional(0, 0, 10, 10, _ml_t, 2) == (_ml_t, 5)
    assert gml.directional(0, 10, 10, 0, _ml_t, 2) == (_ml_r, 2)
    assert gml.directional(10, 0, 0, 10, _ml_t, 2) == (_ml_t, 5)
    assert gml.directional(10, 10, 0, 0, _ml_t, 2) == (_ml_r, 2)
    assert gml.directional(5, 0, 5, 10, _ml_t, 0)[1] == 7
    _ml_p = gml.wave_pieces((0, 10), (0, 0), _ml_t, 3, 2.5)
    assert [c for c, _a, _b in _ml_p] == [3, 4, 5, 6], _ml_p
    assert _ml_p[0][1] == (0, 0), "the wave counts from the smaller y"
    assert len(gml.wave_pieces((0, 0), (0, 10), _ml_t, 0, 0.3)) == 10, \
        "a step below one HD pixel"
    assert [gml.phase_at(ms) for ms in (0, 54, 55, 110, 440)] == \
        [0, 0, 1, 2, 0]
    assert gml.clip((-10, 5), (10, 5), (0, 0, 5, 10)) == ((0, 5), (5, 5))
    assert gml.clip((-10, -5), (-1, -5), (0, 0, 5, 10)) is None
    ok("galaxy_map colour wave (Draw_Directional_Multi_Colored_Line_ "
       "table and offset, one step per ctx.px, at least 1 HD px, 55 ms)")

    # ONE line routine for the whole map: HD EXTENSION B1.
    # Calls, not words: renderer.py still EXPLAINS aaline in a
    # docstring. sidebar.py's panel divider is not on the map — the
    # one named exemption, with its reason, not a silent pass.
    import re as _ml_re
    _ml_dir = os.path.join(SCREENS_DIR, "galaxy_map")
    _ml_call = _ml_re.compile(r"(?:draw|gfxdraw)\.(?:aa)?lines?\(")
    _ml_users = sorted(
        _f for _f in os.listdir(_ml_dir) if _f.endswith(".py")
        and _ml_call.search(open(os.path.join(_ml_dir, _f)).read()))
    _ml_not_map = {"sidebar.py": "the sidebar panel's band divider"}
    assert _ml_users == sorted(["maplines.py"] + list(_ml_not_map)), \
        _ml_users
    assert "maplines.stroke" in open(os.path.join(
        _ml_dir, "renderer.py")).read(), "the wormhole bypasses stroke"
    assert "HD EXTENSION B1" in gmr.WormholeLayer.__doc__, \
        "the wormhole layer no longer names the rule it draws under"
    for _ml_mark in ("HD EXTENSION — B1", "HD EXTENSION — B2",
                     "OMISSION"):
        assert _ml_mark in gml.__doc__, _ml_mark
    assert "maplines.py" in open(os.path.join(
        os.path.dirname(SCREENS_DIR), "v3_projektstatus.md")).read()
    _ml_real = (gs2.ships_raw, gs2.ship_icons, gs2.fleet_selection)
    try:
        gs2.ships_raw, gs2.ship_icons = _ml_raws, _ml_icons
        gs2.fleet_selection = {"stack": -1, "ships": list(range(6)),
                               "selected": [False] * 6, "chain": []}
        gm._viewctl.reset()
        gm.update(gs2)
        _ml_probe = pygame.Surface((app.win_w, app.win_h))
        _ml_probe.fill((0, 0, 0))
        gml.render_destination_lines(_ml_probe, gm._map_context(), gs2,
                                     _ml_ships, gs2.stars, 2, None, 0)
        _ml_lit = pygame.surfarray.array3d(_ml_probe).max(axis=2)
        _ml_lit = _ml_lit[_ml_lit > 0]
        assert _ml_lit.size, "no destination line drawn"
        assert len(set(_ml_lit.tolist())) > 3, "not antialiased"
    finally:
        gs2.ships_raw, gs2.ship_icons, gs2.fleet_selection = _ml_real
        gm.update(gs)
    ok("galaxy_map map lines (one routine, maplines.stroke; the wormhole "
       "through it; B1, B2 and the omissions marked)")

    # THE ICON IS NOT THE HEADER, ON PURPOSE (work order 122, 2.2).
    # SHIP_ICON_DIM sizes and hit-tests the HD icon (9 x 8 at zoom 2,
    # click area live-confirmed); SHIP_ICON_HEADER_DIM is what the game
    # positions with (12 x 11). Held three ways: the two may not become
    # equal, as whole tables or at any zoom as they are used against
    # each other; the DELIBERATE DEVIATION note in maplines quotes both
    # as they are; and the comment on EACH table in zoomtables quotes
    # the OTHER's current values — so neither can change while the
    # other's note still describes the old one.
    import inspect as _dd_inspect
    assert zt.SHIP_ICON_DIM != zt.SHIP_ICON_HEADER_DIM
    for _dd_z in range(4):
        assert zt.ship_icon_dimension(_dd_z) != \
            zt.ship_icon_header_dimension(3 - _dd_z), _dd_z
    assert "DELIBERATE DEVIATION" in gml.__doc__
    for _dd_t in (zt.SHIP_ICON_DIM, zt.SHIP_ICON_HEADER_DIM):
        assert repr(_dd_t) in gml.__doc__, (
            f"maplines' DELIBERATE DEVIATION note does not quote {_dd_t}")
    _dd_lines = _dd_inspect.getsource(zt).splitlines()

    def _dd_comment(name):
        _i = next(_k for _k, _l in enumerate(_dd_lines)
                  if _l.startswith(f"{name} = "))
        _block = []
        while _i > 0 and _dd_lines[_i - 1].startswith("#:"):
            _i -= 1
            _block.insert(0, _dd_lines[_i][2:].strip())
        return " ".join(_block)

    _dd_icon, _dd_head = (_dd_comment("SHIP_ICON_DIM"),
                          _dd_comment("SHIP_ICON_HEADER_DIM"))
    assert "DELIBERATE" in _dd_icon and "DEVIATION" in _dd_head
    assert repr(zt.SHIP_ICON_HEADER_DIM) in _dd_icon, (
        "SHIP_ICON_HEADER_DIM changed and SHIP_ICON_DIM's note was not "
        "touched")
    assert repr(zt.SHIP_ICON_DIM) in _dd_head, (
        "SHIP_ICON_DIM changed and SHIP_ICON_HEADER_DIM's note was not "
        "touched")
    assert "DELIBERATE DEVIATION — SHIP_ICON_DIM" in open(os.path.join(
        os.path.dirname(SCREENS_DIR), "v3_projektstatus.md"),
        encoding="utf-8").read()
    ok("galaxy_map icon 9 x 8 against the 12 x 11 header: a DELIBERATE "
       "DEVIATION, the tables unequal and each note quoting the other")

    # ── Work order 122 item 2.1: the "eta N" label ──
    # Transcribed from Print_Eta_On_Ship_Icon_ with two locks of Data's
    # (16 September 2026): only in the map's own input loop (screen 0,
    # the map's own field list, no modal), and not between an HD order
    # and its effect. Position and size from the HD viewport.
    from screens.galaxy_map import mapeta as _eta
    from core import mapcoords as mc
    import json as _json
    from core.game_state import FieldInfo as _EtaField
    from core.wire_protocol import EFFECT_PAIRS as _eta_pairs
    _eta_fix = _json.load(open(os.path.join(
        os.path.dirname(SCREENS_DIR), "tools", "game_menu_fields.json")))

    def _eta_fields(rows):
        _out = []
        for _r in rows:
            _f = _EtaField()
            (_f.index, _f.x, _f.y, _f.x_end, _f.y_end, _f.field_type,
             _f.hotkey) = _r
            _out.append(_f)
        return _out

    _eta_raws = [bytearray(_r) for _r in _ml_raws]
    for _k, _tl in ((0, 3), (2, 4), (5, 7)):
        _eta_raws[_k][109] = _tl                  # turns_left, +109
    _eta_raws = [bytes(_r) for _r in _eta_raws]
    _eta_ships = [_ship.parse(_r) for _r in _eta_raws]
    assert zt.SHIP_ICON_HEADER_DIM_BY_COLOUR[0] == zt.SHIP_ICON_HEADER_DIM
    _ml_gs.fleet_selection = {"stack": -1, "ships": list(range(6)),
                              "selected": [False] * 6, "chain": []}
    # Who: the moving own ship and the foreign one bound for our
    # outpost; NOT the order-turn ship at 20001 (it has its line).
    assert [(_i, _t) for _, _i, _, _t in _eta.labels(
        _ml_gs, _eta_ships, _ml_gs.stars, [])] == [(0, 3), (2, 4)]
    assert any(l["ship"] == 5 for l in gml.destination_lines(
        _ml_gs, _eta_ships, _ml_gs.stars, 2))
    _eta_real = (gs2.ships_raw, gs2.ship_icons, gs2.fleet_selection,
                 gs2.fields, gs2.current_screen)
    _eta_said = []
    _eta_rt = app.style.render_text
    app.style.render_text = lambda _t, *_a, **_k: (
        _eta_said.append(_t), _eta_rt(_t, *_a, **_k))[1]
    try:
        gs2.ships_raw, gs2.ship_icons = _eta_raws, _ml_icons
        gs2.fleet_selection = {"stack": 0, "ships": list(range(6)),
                               "selected": [True] * 6, "chain": [0]}
        gs2.fields = _eta_fields(_eta_fix["galaxy_map"])
        gs2.current_screen = 0
        gm._viewctl.reset()
        gm.update(gs2)
        _eta_ctx = gm._map_context()
        _eta_surf = pygame.Surface((app.win_w, app.win_h))

        def _eta_draw(lock=None, state=gs2):
            return _eta.render(_eta_surf, _eta_ctx, state, _eta_ships,
                               state.stars, gm._players, None, app.style,
                               None, lock, {})

        _eta_drawn = _eta_draw()
        assert [(_s_, _t) for _s_, _t, _ in _eta_drawn] == [
            (0, "eta 3"), (2, "eta 4")], _eta_drawn
        assert "eta 4" in _eta_said, "the label bypassed Style.render_text"
        # Right edge and top: the icon corner plus the OWNER's header at
        # index 3 - ctx.zoom, in HD pixels (coupled view).
        _eta_icon = _ml_icons[0]
        _eta_w, _eta_h = zt.ship_icon_header_dimension_for_colour(
            0, 3 - _eta_ctx.zoom)
        _eta_v = _eta_ctx.view
        assert abs(_eta_drawn[0][2][0] - (_eta_v.off_x + (
            _eta_icon.x - mc.MAP_LEFT + _eta_w) * _eta_v.scale)) < 1e-6
        assert abs(_eta_drawn[0][2][1] - (_eta_v.off_y + (
            _eta_icon.y - mc.MAP_TOP + _eta_h) * _eta_v.scale)) < 1e-6
        # THE LOOP LOCK: a command outside the map's own input loop.
        gs2.current_screen = 8
        gs2.fields = _eta_fields(_eta_fix["menu"])
        assert _eta_draw() == [], "a digit under the GAME menu"
        gs2.current_screen = 0
        gs2.fields = _eta_fields(_eta_fix["menu"])
        assert _eta_draw() == [], "a digit with a foreign list on screen 0"
        gs2.fields = _eta_fields([[0, 0, 0, 0, 0, 0, 0],
                                  [1, 0, 0, 639, 479, 7, 0x1B]])
        assert _eta_draw() == [], "a digit under a modal box"
        gs2.fields = _eta_fields(_eta_fix["galaxy_map"])
        # THE ORDER LOCK: held from the order until the effect.
        _eta_lock = _eta.hold(gs2, _eta_ships)
        assert _eta_draw(_eta_lock) == []
        assert _eta.advance(_eta_lock, gs2, _eta_ships) is _eta_lock
        _eta_moved = [_ship.parse(_r) for _r in _eta_raws]
        _eta_moved[0] = _ship.parse(_bx_ship(0, 20003, 500, 500,
                                             status=2))
        _eta_next = GameState()
        assert _eta.advance(_eta_lock, _eta_next, _eta_moved) is None, \
            "the lock outlived the order's effect"
        _eta_l = _eta_lock
        for _k in range(_eta_pairs):
            _eta_l = _eta.advance(_eta_l, GameState(), _eta_ships)
            assert _eta_l is not None, "released before any effect"
        assert _eta.advance(_eta_l, GameState(), _eta_ships) is None, \
            "a refused order locks the label for ever"
        # The click path moved to mapinput.py (work order 126 F).
        _gm_src = open(os.path.join(_ml_dir, "mapinput.py")).read()
        assert 'if orders_ok and result.what == "star":\n' \
            '            screen._eta_lock = mapeta.hold(' in _gm_src
    finally:
        app.style.render_text = _eta_rt
        (gs2.ships_raw, gs2.ship_icons, gs2.fleet_selection, gs2.fields,
         gs2.current_screen) = _eta_real
        gm.update(gs)
    # DECISION 30: the label is game data through Style.render_text, and
    # the substitution fires on a blocked 4 — a stub font whose 4, X, Y
    # and Z share one bitmap, as the DEMO Bank Gothic's did.
    class _EtaStubFont:
        def __init__(self, size): self.size = size
        def render(self, ch, aa, fg, bg=None):
            _sf = pygame.Surface((10, 10))
            _sf.fill((0, 0, 0) if ch in "4XYZ" else (ord(ch) % 256, 1, 0))
            return _sf

    _eta_cls = app.style.__class__

    class _EtaStub:
        _GLYPH_PROBE_SIZE = _eta_cls._GLYPH_PROBE_SIZE
        _GLYPH_COLLISION_MIN = _eta_cls._GLYPH_COLLISION_MIN
        _blocked = None
        get_font = staticmethod(_EtaStubFont)
        blocked_glyphs = _eta_cls.blocked_glyphs
        split_runs = _eta_cls.split_runs

    _eta_text = _eta.printf(_eta.FALLBACK_TEXT, 4)
    assert (True, "4") in _EtaStub().split_runs(_eta_text), \
        _EtaStub().split_runs(_eta_text)
    for _eta_mark in ("TRANSCRIBED from SHIPS::Print_Eta_On_Ship_Icon_",
                      "DEVIATION — two locks"):
        assert _eta_mark in _eta.__doc__, _eta_mark
    assert "OMISSION" in gml.__doc__ and "eta N" not in gml.__doc__.split(
        "OMISSION")[1], "maplines still lists the eta label as omitted"
    ok("galaxy_map eta label (Print_Eta_On_Ship_Icon_: who, text, the "
       "owner's header from the HD viewport; no label outside the map's "
       "own loop or between an order and its effect; a blocked 4 "
       "substitutes)")
