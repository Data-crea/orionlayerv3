"""The Leaders screen's live steps (work order 176, part 3) — every
button in both tabs, the star/stack box, the galaxy box, the grid, and
hire on a scratch slot that offers a leader. `screens175_steps.Live`."""
from screens.leaders import ldrgeom as g, ldrmap, ldrwire

SCREEN = g.GAME_SCREEN_ID


def _scr(live):
    return live.hd("leaders")


def _view(live):
    return _scr(live)._view


def _block(live):
    v = _view(live)
    return v.block if v is not None else None


def _ready(live):
    v = _view(live)
    return v is not None and v.state == ldrwire.READY


def _press(live, name):
    live.click_native(_scr(live), g.button_rect(name))


def _row_of(live, idx):
    v = _view(live)
    return v.rows.index(idx) if v is not None and idx in v.rows else None


def _open(live):
    ok = live.open_nav("nav_leaders", SCREEN, "leaders", lambda: _ready(live))
    live.step("open", "RACES bar LEADERS opens screen 29 with the list and "
              "the OFFS block (open fix 30)", f"ready={ok} block="
              f"{_block(live) is not None}", ok and _block(live) is not None)
    return ok


def _tab(live, view):
    name = "tab_ship" if view == g.VIEW_SHIP else "tab_colony"
    if _view(live).view != view:
        _press(live, name)
        live.wait(lambda: _ready(live) and _view(live).view == view,
                  label=name)
    return _view(live).view == view


def _box_answer(live, key_wanted):
    """Answer a native box through HD's own drawing of it (fltbox)."""
    from screens.fleets import fltbox
    for key, field, rect in fltbox.button_rects(_scr(live)):
        if key == key_wanted:
            live.run.hd_click(*rect.center)
            live.run.pump(20)
            return True
    return False


def ship_view(live, me):
    b = _block(live)
    stack0 = b["stack"]
    _press(live, "next")
    live.wait(lambda: _block(live)["stack"] != stack0, label="NEXT")
    live.step("ship_next", "NEXT cycles the ship view's stack (Cycle_Ship_"
              "Icons_, officer.cpp:1100-1106)", f"stack {stack0} -> "
              f"{_block(live)['stack']}", _block(live)["stack"] != stack0)
    s1 = _block(live)["stack"]
    _press(live, "prev")
    live.wait(lambda: _block(live)["stack"] != s1, label="PREV")
    live.step("ship_prev", "PREV cycles back (:1106-1112)",
              f"stack {s1} -> {_block(live)['stack']}",
              _block(live)["stack"] == stack0)
    # The galaxy box: a stack icon of the player's that is not on show.
    st = live.st
    head = _block(live)["head_node"]
    icons = [ic for ic in st.ship_icons if getattr(ic, "owner", None) == me
             and int(ic.node_idx) != head and int(ic.x) >= 0]
    if icons:
        f = ldrmap.icon_field(_view(live).fields, icons[0])
        if f is not None:
            live.click_native(_scr(live), (f.x, f.y, f.x_end, f.y_end))
            live.wait(lambda: _block(live)["head_node"] == int(icons[0].node_idx),
                      label="stack icon")
        live.step("galaxy_stack", "a click on a stack icon in the galaxy box "
                  "makes it the stack on show (flt1.cpp:851-861)",
                  f"head {head} -> {_block(live)['head_node']} (wanted "
                  f"{icons[0].node_idx})",
                  _block(live)["head_node"] == int(icons[0].node_idx))
    # The extractor fix, live: the strip under the map prints "%s Fleet: "
    # and its counts with their spaces (HESTR 0x131, 175's finding X).
    st = live.st
    from core import researchnative as nat
    point = None
    for i, ic in enumerate(st.ship_icons):
        # A PLAYER's stack: a monster's strip prints a race name the wire
        # does not carry and stays empty (OMISSION `map_strip_monsters`).
        owner = getattr(ic, "owner", None)
        f = ldrmap.icon_field(_view(live).fields, ic) \
            if int(ic.x) >= 0 and owner is not None and owner < 8 else None
        if f is None:
            continue
        # A point of the icon's field that no star's field covers: over a
        # star the star wins (the loop's order, officer.cpp:1052-1071).
        for px, py in ((f.x + 1, f.y), (f.x_end - 1, f.y), (f.x, f.y_end)):
            if ldrmap.star_at(st, (px, py)) is None:
                point = (px, py)
                break
        if point:
            break
    text = ""
    if point:
        r = nat.window_rect((point[0], point[1], point[0], point[1]),
                            _scr(live).layout)
        live.run.hd_motion(r[0] + max(1, r[2] // 2), r[1] + max(1, r[3] // 2))
        scan = _scr(live)._scan
        if scan and scan[0] == "icon":
            text = ldrmap.fleet_words(st, st.ship_icons[scan[1]],
                                      _scr(live)._words, _scr(live)._parts)
    live.step("fleet_strip_spaces", "the fleet strip under the map keeps "
              "the string's spaces: '<RACE> FLEET: n Hull' (HESTR 0x131 ends "
              "in a space, 175's finding X)", f"scan {_scr(live)._scan}: "
              f"{text!r}", "FLEET: " in text.upper())
    grid = list(_block(live).get("ship_idx") or [])
    live.step("grid", "the big icons of the stack on show, in the block's "
              "display order, drawn in the view box", f"{len(grid)} ships "
              f"{grid[:6]}", len(grid) > 0)


def assign_ship(live, idx):
    """Select the officer, then a COMBAT ship's big icon: Assign_Captain_
    (officer.cpp:1004-1034, :1440-1452); an officer already serving is
    asked about first (a confirmation, answered YES)."""
    from core.structs import ship as ship_struct
    row = _row_of(live, idx)
    raws = live.st.ships_raw
    grid = list(_block(live).get("ship_idx") or [])
    first = max(0, int(_block(live).get("first_row", 0))) * g.GRID_COLUMNS
    cells = [k for k, s in enumerate(grid[first:first + 15])
             if ship_struct.parse(raws[s]).ship_type == 0]
    if row is None or not cells:
        live.step("assign", "an officer listed and a combat ship on show",
                  f"row {row}, combat cells {cells}", False, capture=False)
        return
    ship = grid[first + cells[0]]
    live.click_native(_scr(live), g.text_field(row))
    live.wait(lambda: _block(live)["selected"] == idx, label="select")
    sel = _block(live)["selected"]
    live.click_native(_scr(live), g.grid_cell(cells[0]))
    live.run.pump(40)
    if _view(live).state == ldrwire.IN_BOX:
        kind = _view(live).box.name
        live.step("assign_box", "a box asks first (an officer already "
                  "serving: SHIPMOVE::Confirm_Officer_Change_)", f"box {kind}",
                  True)
        _box_answer(live, "yes" if kind == "confirmation" else "dismiss")
        live.wait(lambda: _ready(live), label="box answered")
    rec = live.leaders()[idx]
    live.step("assign", "select an officer, then a combat ship's big icon: "
              "he serves on it (status 1, location the ship)",
              f"selected={sel}; leader {idx} status {rec.status} location "
              f"{rec.location}, ship {ship}",
              int(rec.status) == 1 and int(rec.location) == ship)


def pool_and_dismiss(live):
    v = _view(live)
    mine = [i for i in v.rows if int(live.leaders()[i].status) in (0, 1)]
    _press(live, "pool")
    live.wait(lambda: _block(live)["mode"] == 1, label="POOL mode")
    live.step("pool_mode", "POOL switches to pool mode 1 (officer.cpp:"
              "1124-1136)", f"mode {_block(live)['mode']}",
              _block(live)["mode"] == 1)
    if mine:
        i = mine[0]
        before = int(live.leaders()[i].status)
        live.click_native(_scr(live), g.text_field(_row_of(live, i)))
        live.wait(lambda: int(live.leaders()[i].status) != before,
                  label="to the pool")
        live.step("pool_leader", "in pool mode a click on an assigned "
                  "officer moves him to the pool (Move_Officer_To_Limbo_, "
                  ":1415-1422); a free one ends the mode", f"leader {i} status "
                  f"{before} -> {live.leaders()[i].status}, mode "
                  f"{_block(live)['mode']}", True)
    if _block(live)["mode"] == 1:
        _press(live, "pool")
        live.wait(lambda: _block(live)["mode"] == -1, label="POOL off")
    _press(live, "dismiss")
    live.wait(lambda: _block(live)["mode"] == 2, label="DISMISS mode")
    live.step("dismiss_mode", "DISMISS switches to mode 2 (:1114-1122)",
              f"mode {_block(live)['mode']}", _block(live)["mode"] == 2)
    rows = _view(live).rows
    if rows:
        i = rows[0]
        live.click_native(_scr(live), g.text_field(0))
        live.wait(lambda: _view(live).state == ldrwire.IN_BOX, label="box")
        live.step("dismiss_box", "a click on an officer asks 'Dismiss %s?' "
                  "(HESTR 0x126, :1395-1401)", f"state {_view(live).state}",
                  _view(live).state == ldrwire.IN_BOX)
        _box_answer(live, "yes")
        live.wait(lambda: _ready(live) and i not in _view(live).rows,
                  label="dismissed")
        live.step("dismiss", "YES dismisses him (Dismiss_Officer_) — a "
                  "scratch slot, never saved", f"leader {i} status "
                  f"{live.leaders()[i].status}, listed "
                  f"{i in _view(live).rows}", i not in _view(live).rows)
    if _ready(live) and _block(live)["mode"] == 2:
        _press(live, "dismiss")
        live.wait(lambda: _block(live)["mode"] == -1, label="DISMISS off")


def colony_view(live, me):
    b = _block(live)
    s0 = b["star_displayed"]
    _press(live, "next")
    live.wait(lambda: _block(live)["star_displayed"] != s0, label="NEXT star")
    s1 = _block(live)["star_displayed"]
    live.step("colony_next", "NEXT shows the next star of the player's "
              "(Cycle_Star_Icons_, :1100-1112) — the system display and the "
              "strip follow", f"star {s0} -> {s1}, chosen "
              f"{_block(live)['star_chosen']}", s1 != s0)
    _press(live, "prev")
    live.wait(lambda: _block(live)["star_displayed"] != s1, label="PREV star")
    live.step("colony_prev", "PREV shows the star before", f"star {s1} -> "
              f"{_block(live)['star_displayed']}",
              _block(live)["star_displayed"] == s0)
    st = live.st
    stars = [i for i in range(len(st.stars)) if i != s0 and
             me in ldrmap.colony_owners(st, st.stars[i])]
    if stars:
        r = ldrmap.star_field_rect(st, stars[0])
        live.click_native(_scr(live), r)
        live.wait(lambda: _block(live)["star_chosen"] == stars[0],
                  label="star click")
        live.step("galaxy_star", "a click on a star with the player's colony "
                  "chooses and shows it (:1060-1070)", f"chosen "
                  f"{_block(live)['star_chosen']} displayed "
                  f"{_block(live)['star_displayed']} (wanted {stars[0]})",
                  _block(live)["star_chosen"] == stars[0])


def leaders_phase(slot, size, opts):
    from screens175_steps import Live
    live = Live("leaders", slot, size)
    if not live.load() or not _open(live):
        return live.finish()
    me = int(live.st.player_num)
    _tab(live, g.VIEW_SHIP)
    live.step("ship_tab", "Ship Officers: rows, the stack on show, the grid",
              f"view {_view(live).view} rows {_view(live).rows}",
              _view(live).view == g.VIEW_SHIP)
    rows = _scr(live)._rows
    if rows and rows[0].skills:
        from screens.leaders import ldrdraw
        line = ldrdraw.skill_line_rects(_scr(live), rows[0])[0]
        live.run.hd_click(line.centerx, line.centery, button=3)
        title, body = _scr(live)._skill_help or ("", "")
        live.step("skill_help_spaces", "the skill help names the leader "
                  "'<Title> <Name>, the <Rank>' with the string's own spaces "
                  "(HESTRNGS, 175's finding X)", repr(body[:90]),
                  ", the " in body)
        live.run.hd_click(5, 5)
    if opts.get("quick") is None:
        ship_view(live, me)
        pool_ids = [i for i in _view(live).rows
                    if int(live.leaders()[i].status) == 0]
        if pool_ids:
            assign_ship(live, pool_ids[0])
        pool_and_dismiss(live)
    _tab(live, g.VIEW_COLONY)
    live.step("colony_tab", "Colony Leaders: rows, the system display of "
              "the star on show, the strip", f"view {_view(live).view} star "
              f"{_block(live)['star_displayed']}",
              _view(live).view == g.VIEW_COLONY)
    if opts.get("quick") is None:
        colony_view(live, me)
    _press(live, "return")
    ok = live.back_to_map()
    live.step("return", "RETURN goes back to the galaxy map (:1172-1175)",
              f"screen {live.st.current_screen}", ok, capture=False)
    return live.finish()


def hire_phase(slot, size, opts):
    """HIRE on a scratch slot that offers a leader (SAVE2's game copied
    into the slot beforehand): hire mode, a leader, the popup, HIRE."""
    from screens175_steps import Live
    live = Live("leaders", slot, size)
    live.phase_tag = "hire_"
    if not live.load() or not _open(live):
        return live.finish()
    _tab(live, g.VIEW_SHIP)
    v = _view(live)
    me = int(live.st.player_num)
    offer = [i for i in v.rows if int(live.leaders()[i].status) == 4
             and int(live.leaders()[i].player_index) == me]
    live.step("hire_offer", "the view offers leaders for hire (HIRE live)",
              f"for hire {offer}, HIRE field {'hire' in v.buttons}",
              bool(offer) and "hire" in v.buttons)
    if not offer:
        return live.finish()
    _press(live, "hire")
    live.wait(lambda: _view(live).mode == 0, label="hire mode")
    live.step("hire_mode", "HIRE switches to hire mode: CANCEL, the panel "
              "with the price (:961-980, :796-808)", f"mode "
              f"{_view(live).mode} cancel {'cancel' in _view(live).buttons}",
              _view(live).mode == 0)
    i = offer[0]
    bc0 = int(live.run.player().bc)
    live.click_native(_scr(live), g.text_field(_row_of(live, i)))
    live.wait(lambda: _view(live).state == ldrwire.POPUP, label="popup")
    pop = _view(live).popup
    live.step("hire_popup", "a leader in hire mode opens the hire popup with "
              "his offer (Do_Hire_Officer_, mainpups.cpp:784-930)",
              f"state {_view(live).state} popup leader "
              f"{getattr(pop, 'leader', None)}",
              _view(live).state == ldrwire.POPUP and
              getattr(pop, "leader", None) == i)
    from screens.leaders import ldrdialog
    for key, rect in ldrdialog.popup_rects(_scr(live)):
        if key == "hire":
            live.run.hd_click(*rect.center)
            live.run.pump(30)
    live.wait(lambda: int(live.leaders()[i].status) != 4, label="hired")
    rec = live.leaders()[i]
    bc1 = int(live.run.player().bc)
    live.step("hire", "HIRE in the popup hires him: he joins the player "
              "(status leaves 'for hire') and the price is paid — a scratch "
              "slot, never saved", f"leader {i} status {rec.status} "
              f"player {rec.player_index}; BC {bc0} -> {bc1}",
              int(rec.status) != 4 and bc1 < bc0)
    if _ready(live) and _view(live).mode == 0 and "cancel" in _view(live).buttons:
        _press(live, "cancel")
    _press(live, "return")
    live.back_to_map()
    return live.finish()
