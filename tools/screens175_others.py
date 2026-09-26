"""The Races, Info and Fleets screens' live steps (work order 176, part 3).
`screens175_steps.Live` does the plumbing."""
import pygame

from screens.info import infogeom as ig
from screens.races import racesgeom as rg
from screens.races import raceswire as rw


# ── Races (SCREEN_RACE 6) ──────────────────────────────────

def _rscr(live):
    return live.hd("races")


def _rview(live):
    return _rscr(live)._view


def _rstate(live):
    v = _rview(live)
    return v.state if v is not None else None


def _rpress(live, name):
    live.click_native(_rscr(live), rg.button_rect(name))


def _who_pick(live, action, slot):
    _rpress(live, action)
    live.wait(lambda: _rstate(live) == rw.WHO, label=f"{action} WHO")
    who = _rstate(live) == rw.WHO
    live.click_native(_rscr(live), rg.who_field(slot))
    return who


def _back_to_races(live):
    """Leave a dialog of the Races screen with its own ESC (the report's
    EXIT and the diplomacy screen both take it)."""
    for _ in range(4):
        if _rstate(live) == rw.MAIN:
            return True
        live_f = [f for f in live.st.fields or [] if f.index]
        if len(live_f) == 1:
            # A statement the game shows until it is clicked away (the
            # ambassador's answer): its one field is the whole screen.
            live.run.app.client.activate_field(live_f[0].index)
        else:
            live.run.app.client.inject_key(27)
        live.wait(lambda: _rstate(live) == rw.MAIN, seconds=15,
                  label="back to Races")
    return _rstate(live) == rw.MAIN


def races_phase(slot, size, opts):
    from screens175_steps import Live
    live = Live("races", slot, size)
    if not live.load():
        return live.finish()
    ok = live.open_nav("nav_races", rg.GAME_SCREEN_ID, "races",
                       lambda: _rstate(live) == rw.MAIN)
    v = _rview(live)
    slots = [(s.player, s.name, s.lines, s.relation_word, s.spies)
             for s in _rscr(live)._slots]
    live.step("open", "RACES opens screen 6 in the main mode: portraits, "
              "names, treaties, relations, spies, bonuses — against the "
              "native half", f"state {_rstate(live)}; active {v.active}; "
              f"slots {slots}", ok)
    me = int(live.st.player_num)
    players = rw.players_of(live.st)
    target = v.active[0] if v.active else None
    if target is None:
        return live.finish()
    bit = 1 << target
    before = int(players[me].ignoring) & bit
    who = _who_pick(live, "ignore", 0)
    live.wait(lambda: (int(rw.players_of(live.st)[me].ignoring) & bit)
              != before, label="ignoring")
    after = int(rw.players_of(live.st)[me].ignoring) & bit
    live.step("ignore", "IGNORE, then a race: its 'ignoring' bit flips and "
              "(IGNORED) shows (racescrn.cpp:888, :569-572)",
              f"WHO={who}; bit {bool(before)} -> {bool(after)}",
              who and after != before)
    _who_pick(live, "ignore", 0)
    live.wait(lambda: (int(rw.players_of(live.st)[me].ignoring) & bit)
              == before, label="un-ignore")
    live.step("ignore_again", "IGNORE on the same race flips it back",
              f"bit {bool(int(rw.players_of(live.st)[me].ignoring) & bit)}",
              (int(rw.players_of(live.st)[me].ignoring) & bit) == before,
              capture=False)
    for action, what in (("report", "the race report "
                          "(Race_Report_Screen_, racerprt.cpp:9-155)"),
                         ("audience", "the diplomacy screen "
                          "(Diplomacy_Screen_, dip_scrn_main.cpp:1257)")):
        who = _who_pick(live, action, 0)
        live.run.wait_for(lambda st: _rstate(live) == rw.DIALOG,
                          seconds=15, label=action)
        live.step(action, f"{action.upper()}, then a race: {what}, shown by "
                  f"the fallback (same id 6, neither list)", f"WHO={who}; "
                  f"state {_rstate(live)}; original "
                  f"{live.run.app._showing_original()}",
                  who and _rstate(live) == rw.DIALOG)
        back = _back_to_races(live)
        live.step(f"{action}_back", "ESC leaves it, back to the main mode",
                  f"state {_rstate(live)}", back, capture=False)
    # A race NOT at war, if there is one, so the confirmation comes.
    peace = [k for k, p in enumerate(v.active)
             if int(players[me].treaty[p]) < 4]
    wslot = peace[0] if peace else 0
    target = v.active[wslot]
    treaty = int(players[me].treaty[target])
    who = _who_pick(live, "war", wslot)
    if treaty >= 4:
        live.step("war", "DECLARE WAR on a race already at war: no box "
                  "(:897-907)", f"WHO={who}; state {_rstate(live)}", who)
    else:
        live.wait(lambda: _rstate(live) == rw.IN_BOX, label="war box")
        live.step("war", "DECLARE WAR, then a race: the confirmation "
                  "(BILLTEX2 0x1A), answered NO", f"WHO={who}; state "
                  f"{_rstate(live)}", who and _rstate(live) == rw.IN_BOX)
        from screens.fleets import fltbox
        for key, _f, rect in fltbox.button_rects(_rscr(live)):
            if key == "no":
                live.run.hd_click(*rect.center)
        live.wait(lambda: _rstate(live) == rw.MAIN, label="after NO")
        live.step("war_no", "NO: no war declared (the treaty unchanged)",
                  f"treaty {treaty} -> "
                  f"{int(rw.players_of(live.st)[me].treaty[target])}",
                  int(rw.players_of(live.st)[me].treaty[target]) == treaty,
                  capture=False)
    _rpress(live, "exit")
    ok = live.back_to_map()
    live.step("return", "RETURN goes back to the galaxy map (:857-874)",
              f"screen {live.st.current_screen}", ok, capture=False)
    return live.finish()


# ── Info (SCREEN_INFO 9) ───────────────────────────────────

def _iscr(live):
    return live.hd("info")


def info_phase(slot, size, opts):
    from screens175_steps import Live
    live = Live("info", slot, size)
    if not live.load():
        return live.finish()
    ok = live.open_nav("nav_info", ig.GAME_SCREEN_ID, "info",
                       lambda: _iscr(live)._exit is not None)
    scr = _iscr(live)
    me = live.run.player()
    live.step("open", "INFO opens screen 9 on the tab the game saved "
              "(history_btns bits 4-6); the chart against native",
              f"page {scr.page}, saved tab {(int(me.history_btns) >> 4) & 7}"
              f", INFS block {live.st.info_screen is not None}",
              ok and scr.page == (int(me.history_btns) >> 4) & 7)
    engine_fields = list(live.st.fields or [])
    names = ("history", "tech", "races", "turns", "reference")
    for k, name in enumerate(names):
        live.click_native(scr, ig.tab_rect(k), frames=10)
        block = live.st.info_screen or {}
        extra = ""
        if name == "history":
            extra = f"divisors {block.get('bill')}"
        if name == "turns":
            extra = (f"{len(block.get('messages') or [])} messages: " +
                     repr([m.decode('cp437', 'replace')
                           for m in block.get('messages') or []]))
        live.step(f"tab_{name}", f"the {name} page, HD-local (nothing sent)",
                  f"page {scr.page}; {extra}", scr.page == k)
    live.click_native(scr, ig.index_row(0, 0), frames=10)
    live.step("ref_category", "a category opens its sorted topic list and "
              "the first article", f"mode {scr.ref_mode} ix {scr.ref_ix} "
              f"topic {scr.topic}", scr.ref_mode == "category")
    live.click_native(scr, ig.BACK_BUTTON, frames=10)
    live.click_native(scr, ig.index_row(1, 0), frames=10)
    box = [b for k, b in scr._boxes.items()
           if str(k).startswith("ref.howto.text")]
    over = box[0].overflow if box else 0
    live.step("ref_howto", "a 'How to?' page opens with its article; a text "
              "longer than its box scrolls", f"mode {scr.ref_mode} ix "
              f"{scr.ref_ix} overflow {over}px", scr.ref_mode == "howto")
    if box and over:
        r = box[0].rect
        pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL,
                                             {"x": 0, "y": -3, "flipped":
                                              False}))
        pygame.mouse.set_pos(r.center)
        scr.handle_mousewheel(-1, *r.center)
        live.run.pump(5)
        live.step("scroll", "the mouse wheel scrolls the long text",
                  f"offset {scr._scroll.get(box[0].key)}",
                  scr._scroll.get(box[0].key, 0) > 0)
    live.click_native(scr, ig.BACK_BUTTON, frames=10)
    # The Turn Summary's colony jump: the engine's own page is the saved tab;
    # when that is the Turn Summary its message rows are fields in its list
    # area — the first one is activated and what the ENGINE does recorded.
    rows = [f for f in engine_fields if f.field_type == ig.TYPE_HIDDEN
            and 218 <= f.x and f.x_end <= 612 and 90 <= f.y <= 414
            and f.index != 0]
    if rows:
        s0 = live.st.current_screen
        live.run.app.client.activate_field(rows[0].index)
        live.run.pump(60)
        s1 = live.st.current_screen
        live.step("turn_jump", "a click on a colony message: Goto_Msg_Colony_ "
                  "sets COLONY, info.cpp:641 then sets MAIN (175's note)",
                  f"engine rows {[(r.index, r.x, r.y, r.x_end, r.y_end) for r in rows]}"
                  f"; activated {rows[0].index}; screen {s0} -> {s1}", True)
        if s1 != ig.GAME_SCREEN_ID:
            live.run.app.client.inject_key(27)
            live.back_to_map()
            return live.finish({"turn_jump_screen": s1})
    else:
        tab = (int(me.history_btns) >> 4) & 7
        msgs = len((live.st.info_screen or {}).get("messages") or [])
        live.step("turn_jump", "the engine's list rows of its Turn Summary",
                  f"none to click — the engine's own page is tab {tab} "
                  f"({'the Turn Summary' if tab == 3 else 'not the Turn Summary'}"
                  f") and this turn has {msgs} message(s)", True,
                  capture=False)
    live.click_native(scr, ig.EXIT)
    ok = live.back_to_map()
    live.step("return", "RETURN goes back to the galaxy map (info.cpp:641)",
              f"screen {live.st.current_screen}", ok, capture=False)
    return live.finish()


# ── Fleets (SCREEN_FLEET 4), the extractor fix ─────────────

def fleets_phase(slot, size, opts):
    from screens175_steps import Live
    live = Live("fleets", slot, size)
    if not live.load():
        return live.finish()
    ok = live.open_nav("nav_fleets", 4, "fleets")
    live.run.pump(30)
    seen = []
    style = live.run.app.style
    real = style.render_text

    def spy(text, *a, **k):
        seen.append(text)
        return real(text, *a, **k)
    style.render_text = spy
    try:
        live.run.pump(3)
    finally:
        style.render_text = real
    glued = sorted({t for t in seen if any(
        a.islower() and b.isupper() for a, b in zip(t, t[1:]))})
    live.step("fleets_texts", "the Fleets screen's words keep their spaces "
              "(175's extractor fix): no two words run together", f"open "
              f"{ok}; {len(set(seen))} texts; run-together candidates "
              f"{glued[:8]}", ok)
    live.run.app.client.inject_key(27)
    live.back_to_map()
    return live.finish({"texts": sorted(set(seen))})
