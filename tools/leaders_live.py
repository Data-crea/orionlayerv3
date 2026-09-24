"""The live half of `tools/leaders_hd.py` — imported only once the port is
known to be free, because importing it builds the real App and connects.

Every capture is native and HD from ONE snapshot, plus a side-by-side
(native scaled to the HD window's picture height, the two halves next to
each other), and every one is listed in `record.json` as a QUESTION for
Data — the order's words: "questions to check, not findings".
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
import leader_check  # noqa: E402
import livesend  # noqa: E402
from livedrive import Run, SendCounter, close, hashes  # noqa: E402

from core import leaderskills as ls  # noqa: E402
from core import researchnative as nat  # noqa: E402
from core.structs import leader as leader_struct  # noqa: E402
from screens.leaders import ldrgeom, ldrpopup, ldrwire  # noqa: E402

SCREEN = ldrgeom.GAME_SCREEN_ID


def screen(run):
    return run.app.dispatcher.screens.get("leaders")


def measure_struct(run):
    """The struct's live second source: the same measurements as the
    saves, on the arrays the wire carries right now."""
    st = run.state
    hero = leader_check.herodata()
    out = leader_check.measure(st.leaders_raw, [s.raw for s in st.stars],
                               st.ships_raw, hero)
    leader_check.report(f"LIVE: screen {st.current_screen}, stardate "
                        f"{st.stardate_str}, {st.num_ships} ships", out)
    return {k: list(v[:2]) for k, v in out.items()}, leader_check.verdict(out)


def diff_fields(run):
    """The live list against `ldrgeom.field_shapes` — both directions,
    and the fields the transcription does not claim named separately."""
    st = run.state
    view = screen(run)._view
    recs = leader_struct.parse_all(st.leaders_raw)
    rows = view.rows
    split = [tuple(len(p) for p in ldrpopup.split_skills(recs[i]))
             for i in rows]
    want = ldrgeom.field_shapes(len(rows), split, view.view,
                                view.mode if view.mode == 0 else -1,
                                view.for_hire_here())
    live = [((f.x, f.y, f.x_end, f.y_end), f.field_type, f.hotkey)
            for f in (st.fields or []) if f.index != 0]
    missing = [w for w in want if w not in live]
    extra = [x for x in live if x not in want]
    in_box = lambda r: (ldrgeom.GALAXY_BOX[0] <= r[0]
                        and r[2] <= ldrgeom.GALAXY_BOX[2]
                        and ldrgeom.GALAXY_BOX[1] <= r[1]
                        and r[3] <= ldrgeom.GALAXY_BOX[3])
    right = lambda r: r[0] >= ldrgeom.VIEW_BOX[0] - 8
    untranscribed = [x for x in extra if in_box(x[0]) or right(x[0])]
    extra = [x for x in extra if x not in untranscribed]
    print(f"  fields: {len(live)} live, {len(want)} transcribed; missing "
          f"{len(missing)}, unexplained {len(extra)}, not transcribed "
          f"(galaxy box / right half) {len(untranscribed)}")
    for m in missing:
        print(f"    MISSING  {m}")
    for x in extra:
        print(f"    EXTRA    {x}")
    as_json = lambda items: [[list(r), t, h] for r, t, h in items]
    return {"live": len(live), "transcribed": len(want),
            "missing": as_json(missing), "extra": as_json(extra),
            "untranscribed": len(untranscribed)}


def side_by_side(run, entry):
    """native | HD, one picture, the native scaled to the HD picture's
    height (nearest-neighbour, so its pixels stay whole)."""
    d = run.dir
    nat_png = os.path.join(d, entry["native_png"])
    hd_png = os.path.join(d, entry["hd_png"])
    if not (os.path.exists(nat_png) and os.path.exists(hd_png)):
        return None
    native = pygame.image.load(nat_png)
    hd = pygame.image.load(hd_png)
    h = hd.get_height()
    w = int(640 * h / 480)
    out = pygame.Surface((w + hd.get_width(), h))
    out.blit(pygame.transform.scale(native, (w, h)), (0, 0))
    out.blit(hd, (w, 0))
    path = hd_png.replace("_hd.png", "_side.png")
    pygame.image.save(out, path)
    return os.path.basename(path)


def open_leaders(run):
    """Press the HD map's own LEADERS button, and record every frame of
    the entry until the list is this screen's."""
    gm = run.app.dispatcher.screens.get("galaxy_map")
    box = gm.box_rect("nav_leaders") if gm else None
    if box is None:
        raise livesend.WrongDialog("the HD map has no LEADERS button")
    rect = pygame.Rect(*gm.layout.rect(box))
    frames = []
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         {"pos": rect.center, "button": 1}))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                         {"pos": rect.center, "button": 1}))
    for _ in range(400):
        run.pump()
        st = run.state
        scr = screen(run)
        frames.append({"screen": st.current_screen,
                       "own_list": ldrwire.is_officer_list(st.fields),
                       "hd": run.app.dispatcher.active_name,
                       "original": run.app._showing_original(),
                       "state": getattr(getattr(scr, "_view", None),
                                        "state", None)})
        if st.current_screen == SCREEN and frames[-1]["own_list"] \
                and frames[-1]["hd"] == "leaders":
            break
    glimpse = [i for i, f in enumerate(frames)
               if f["screen"] == SCREEN and f["original"]]
    print(f"  entry: {len(frames)} frames to the list; the game's picture "
          f"shown in {len(glimpse)} of them")
    return frames, glimpse


def click_native(run, native_rect, button=1):
    scr = screen(run)
    r = nat.window_rect(native_rect, scr.layout)
    run.hd_click(r[0] + r[2] // 2, r[1] + r[3] // 2, button=button)
    run.pump(20)


def probe(folder):
    run = Run("probe", folder=folder)
    run.pump(40)
    print(f"  loaded game: {gameload.fingerprint(run.state)}")
    measured, good = measure_struct(run)
    run.save_record({"fingerprint": gameload.fingerprint(run.state),
                     "struct": measured, "struct_ok": good})
    return 0 if good else 1


def acceptance(folder, slot):
    run = Run(f"run_slot{slot}", folder=folder)
    saves = hashes()
    counter = SendCounter(run.app.client)
    run.pump(40)
    found = gameload.fingerprint(run.state)
    print(f"  the game as found: screen {run.state.current_screen}, {found}")
    record = {"found": found, "slot": slot}
    load = gameload.load_slot(run, slot)
    record["load"] = load
    if not load["loaded"]:
        run.save_record({**record, **close(run, saves)})
        return 1
    record["struct"], record["struct_ok"] = measure_struct(run)
    frames, glimpse = open_leaders(run)
    record["entry_frames"] = frames
    record["glimpse_frames"] = glimpse
    scr = screen(run)
    questions = []
    if scr is None or scr._view is None or scr._view.state != ldrwire.READY:
        print(f"  the Leaders screen is not READY: "
              f"{getattr(getattr(scr, '_view', None), 'reason', '')}")
        run.save_record({**record, **close(run, saves)})
        return 1
    for name in ("ship", "colony"):
        want = ldrgeom.VIEW_SHIP if name == "ship" else ldrgeom.VIEW_COLONY
        if scr._view.view != want:
            click_native(run, ldrgeom.button_rect(
                "tab_ship" if name == "ship" else "tab_colony"))
            run.wait_for(lambda st: screen(run)._view.view == want
                         and screen(run)._view.state == ldrwire.READY,
                         seconds=20, label=f"the {name} view")
        record[f"fields_{name}"] = diff_fields(run)
        entry = run.capture(f"{name}_view")
        entry["side"] = side_by_side(run, entry)
        questions.append((entry["side"], f"the {name} view: rows, "
                          f"portraits, cost column, status line, skills, "
                          f"buttons — against the native half"))
        if screen(run)._view.for_hire_here() and "hire" in \
                screen(run)._view.buttons:
            click_native(run, ldrgeom.button_rect("hire"))
            run.wait_for(lambda st: screen(run)._view.hire_mode,
                         seconds=20, label="hire mode")
            entry = run.capture(f"{name}_hire_mode")
            entry["side"] = side_by_side(run, entry)
            questions.append((entry["side"], "hire mode: the panel and "
                              "CANCEL"))
            click_native(run, ldrgeom.button_rect("cancel"))
            run.wait_for(lambda st: not screen(run)._view.hire_mode,
                         seconds=20, label="out of hire mode")
        rows = screen(run)._rows
        if rows and rows[0].skills:
            from screens.leaders import ldrdraw
            line = ldrdraw.skill_line_rects(screen(run), rows[0])[0]
            run.hd_click(line.centerx, line.centery, button=3)
            entry = run.capture(f"{name}_skill_help")
            questions.append((entry["hd_png"], "HD's skill help box "
                              "(the game's own box is NOT opened — the "
                              "screen's `hd_skill_help` marking)"))
            run.hd_click(5, 5)
    click_native(run, ldrgeom.button_rect("return"))
    run.wait_for(livesend.on_galaxy_map, seconds=30, label="the map again")
    record["questions"] = questions
    counts, sent = counter.snapshot()
    counter.release()
    run.save_record({**record, "sends": counts,
                     "sent": [list(x) for x in sent],
                     **close(run, saves)})
    return 0
