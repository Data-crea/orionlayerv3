# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 010_galaxy_map_zoom_tables_star_black_hole_nebula.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 8 check(s) it holds:
#   - zoom tables (star/black hole/nebula dims, extended scaling)
#   - galaxy_map nebulas (size from type, not from artwork)
#   - galaxy_map loads its sprites once per screen object, not once per entry: a second entry reads no
#   - galaxy_map zoom sizing + wormhole visibility
#   - galaxy_map nebula masters (references absent — run tools/nebula_extract.py to verify shape + wei
#   - galaxy_map nebula masters (shape + weight vs the original)
#   - galaxy_map black hole master (square, circular, on axis)
#   - galaxy_map star field (density, additive, deterministic)

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
        # force=True: this block PUT a flat test surface over the
        # real nebula artwork, and since work order 161 a plain
        # `_load_sprites()` is a no-op when the skin and mods have
        # not moved. Without the flag the fake would survive into
        # every later check that renders a nebula.
        gm._load_sprites(force=True)
        ok("galaxy_map nebulas (size from type, not from artwork)")

# ── THE MAP LOADS ITS SPRITES ONCE, NOT ONCE PER ENTRY ──────
#
# Work order 161. `_load_sprites` ran on every `enter` and cost 81
# `pygame.image.load` calls, 409 ms of a 432 ms entry at 1920x1080
# — and every RETURN from Colonies, Planets and Fleets lands on
# this screen, so it was paid on every return. `SpriteCache` is
# built in `__init__` and nothing ever calls its `clear()`, so the
# reload replaced each surface with an identical one.
#
# ASSERTED AS THE RULE, in both directions: a second entry loads
# NOTHING through this path, and a changed key loads again. The
# counter is here because the first version of the guard stored
# the sidebar loop's variable instead of the key — it never
# matched, nothing reloaded less, and only counting the loads
# showed it.
if "galaxy_map" in d.screens:
    _sp_gm = d.screens["galaxy_map"]
    _sp_real = pygame.image.load
    _sp_n = [0]

    def _sp_counting(*a, **k):
        _sp_n[0] += 1
        return _sp_real(*a, **k)

    pygame.image.load = _sp_counting
    try:
        _sp_gm._sprite_key_loaded = None       # cold
        _sp_n[0] = 0
        _sp_gm._load_sprites()
        _sp_cold = _sp_n[0]
        assert _sp_cold > 40, (
            f"a cold _load_sprites read {_sp_cold} files; the star, "
            f"ship, nebula and sidebar sets should be far more, so "
            f"this check has stopped measuring what it names")
        _sp_n[0] = 0
        _sp_gm._load_sprites()
        assert _sp_n[0] == 0, (
            f"_load_sprites re-read {_sp_n[0]} files with the skin, "
            f"the mods and layout.json unchanged — the guard is not "
            f"holding and every return to the map pays for it again")
        # force= is the restore path, and it must still reload.
        _sp_n[0] = 0
        _sp_gm._load_sprites(force=True)
        assert _sp_n[0] == _sp_cold, (
            f"force=True read {_sp_n[0]} files, not {_sp_cold}; the "
            f"nebula check restores real artwork through it")
        # A CHANGED KEY RELOADS. `nebula_forms` is part of it
        # because a mod can replace layout.json.
        _sp_saved = _sp_gm._data.get("nebula_forms")
        _sp_gm._data["nebula_forms"] = list(_sp_saved or [])[:1]
        _sp_n[0] = 0
        _sp_gm._load_sprites()
        assert _sp_n[0] > 0, (
            "nebula_forms changed and nothing reloaded — the guard "
            "is keyed on too little, and a mod's artwork would "
            "never reach the screen")
        if _sp_saved is None:
            _sp_gm._data.pop("nebula_forms", None)
        else:
            _sp_gm._data["nebula_forms"] = _sp_saved
        _sp_gm._load_sprites(force=True)
    finally:
        pygame.image.load = _sp_real
    ok(f"galaxy_map loads its {_sp_cold} sprites once per screen "
       f"object, not once per entry: a second entry reads no file, "
       f"force= still does, and a changed skin, mod list or "
       f"layout.json reloads")

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

    # Wormhole links are FAINT (the skin's colour, with alpha) and
    # ANTIALIASED. The original draws a hard 1 px line in palette
    # index 4, RGB (36,36,40) measured: the antialiasing is HD
    # EXTENSION B1 (brief 111), one rule for every map line through
    # maplines.stroke — marked there and held by the map-lines check,
    # no longer an unmarked choice this check defended.
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
