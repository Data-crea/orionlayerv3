# smoke-suite area: galaxy_map
#
# Part of the OrionLayer smoke suite — 065_galaxy_map_player_colours_no_preset_ship_is.py.
# `tools/smoke_test.py` executes this file, and every other
# module in tools/smoke_suite/ (93 of them), in file-name
# order and in ONE namespace: these statements stood inside
# main() and still bind the names the later ones read.
#
# Work order 162 moved them here by script, dedented and
# otherwise unchanged. Do not import this file; it is not a
# module. Add a check for this screen HERE, not in the core.
#
# The 2 check(s) it holds:
#   - player colours: no preset ship is darker than the darkest original ship at any of the four zoom 
#   - player colours: ship floor reported (sprites absent)


# 9. THE RULE HOLDS ON THE REAL SPRITES: no preset ship darker than the
#    darkest original ship at any zoom step (the mean is only reported).
_pc_dir = os.path.join(SCREENS_DIR, "galaxy_map", "assets", "ships",
                       "player")
_pc_steps = [os.path.join(_pc_dir, f"{_s}.png") for _s in range(4)]
if all(os.path.exists(_p) for _p in _pc_steps):
    from screens.galaxy_map import ships as _pc_ships

    # THROUGH THE SCREEN'S OWN TINT PATH, NOT A STAND-IN —
    # repaired 21 September 2026, work order 157 part 2.
    #
    # This used to tint by hand:
    #     _o.fill(_pc.lift(_tint, _keep), BLEND_RGB_MULT)
    # which retyped BOTH halves of `ships.TintCache.get` — the
    # lift and the blend — so the check measured
    # `playercolors.lift` while NAMING the ship tint. Proved, not
    # supposed: halving `ships._lift` left the whole suite green
    # at 243 with every fleet on the galaxy map drawing at half
    # its tint (evidence, work_order_157/part2_step1). Nothing
    # else in the suite calls `_lift` or `TintCache` at all.
    #
    # colors.json's `_k_ship_protocol` already said the criterion
    # was "Measured ... through ships.TintCache's own path
    # (TINT_KEEP_WHITE lift, then BLEND_RGB_MULT)". It was not.
    # It is now, and that is the point of the repair: the note was
    # true of the intent and false of the code.
    #
    # `TintCache.get` takes a colour INDEX and reads the colour
    # from `ships.SHIP_COLORS`, so the preset colour is put there
    # and the real cache does the rest. A fresh cache per call:
    # its key is (cache_key, w, h, idx) and the COLOUR is not in
    # it, so a shared cache would hand back the first preset's
    # sprite for every later one — which would be this same fault
    # in a new place.
    def _pc_lum(_sprite, _tint):
        _saved = _pc_ships.SHIP_COLORS.get(0)
        _pc_ships.SHIP_COLORS[0] = _tint
        try:
            _o = _pc_ships.TintCache().get(_sprite, "_wo157", 0)
        finally:
            _pc_ships.SHIP_COLORS[0] = _saved
        assert _o is not _sprite, (
            "TintCache.get handed back the untinted base — it does "
            "that when SHIP_COLORS has no entry for the index, and "
            "this check would then measure the grey sprite and pass")
        _rgb = pygame.surfarray.array3d(_o).astype(float) / 255.0
        _al = pygame.surfarray.array_alpha(_o).astype(float) / 255.0
        _lin = ((_rgb <= 0.04045) * (_rgb / 12.92)
                + (_rgb > 0.04045) * (((_rgb + 0.055) / 1.055) ** 2.4))
        _L = 0.2126 * _lin[..., 0] + 0.7152 * _lin[..., 1] + 0.0722 * _lin[..., 2]
        return float((_L * _al).sum() / _al.sum())

    _pc_orig = _pc.apply(_pc_skin, "original")[0]["galaxy_map"]
    for _pc_n in _pc_names[1:]:
        _pc_g = _pc.apply(_pc_skin, _pc_n)[0]["galaxy_map"]
        for _pc_p in _pc_steps:
            _spr = pygame.image.load(_pc_p).convert_alpha()
            _floor = min(_pc_lum(_spr, _pc_orig[f"ship_{_i}"])
                         for _i in range(8))
            _low = min(_pc_lum(_spr, _pc_g[f"ship_{_i}"])
                       for _i in range(8))
            assert _low >= _floor, (
                f"{_pc_n} {os.path.basename(_pc_p)}: darkest preset ship "
                f"{_low:.4f} below the darkest original {_floor:.4f}")
    ok("player colours: no preset ship is darker than the darkest "
       "original ship at any of the four zoom steps, measured "
       "through ships.TintCache's own path")
else:
    report("preset ship floor NOT measured — the player ship sprites are "
           "absent; run: python tools/setup.py")
    ok("player colours: ship floor reported (sprites absent)")
