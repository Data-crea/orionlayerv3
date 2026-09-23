#!/usr/bin/env python3
"""Hover the first row of every research box, live, at four resolutions.

    python tools/research_hover_hd.py            # SAVE4, change mode

Data's Nachtrag to work order 166: the drawn hover band and the click
area are two rectangles now, and this is the live half of saying so.

WHAT IT PROVES, and it is one claim per hover: the pointer stands on
the FIELD NAME's own line — the top of row 0's click area, which is
transcribed 34 px tall and takes the name in (list.cpp:94-116) — and

  * the row is hit, so the click area still reaches up there, and
  * the band that appears does NOT cover the name, because it starts
    at the application's label line where `Draw_Little_Arrow_` puts
    the original's own mark (tech.cpp:740-775).

The point is the one place where the two rectangles disagree, which is
the only place a picture can settle it. A hover in the middle of a row
looks the same either way.

NOTHING IS SENT. A hover assigns `_hover` and returns
(`researchscreen.handle_mouse_motion`), so the run counts sends around
the whole pass and reports the number rather than assuming it.

THE SAVES: SAVE4 is loaded through `tools/gameload.py`, nothing is ever
saved, and SAVE8 is refused by the loader itself.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import gameload  # noqa: E402
from core import researchnative  # noqa: E402
from livedrive import Run, SendCounter, close, hashes  # noqa: E402
import livesend  # noqa: E402
from researchchangephases import (SCRATCH, SCREEN_CHANGE,  # noqa: E402
                                  ensure_on_map, enter_change, esc_leave,
                                  hd, pair, panel_ready)


#: The four presets are F9's own (`main.App._resolutions`), and the
#: run goes FULLSCREEN at each one. A window cannot be trusted to be
#: the size it asked for — `_set_mode` logs "granted" when the
#: compositor cuts it, and it cut 1440 to 1371 on the display this ran
#: on. Fullscreen renders into a surface of the preset's own size and
#: letterboxes it (main.py:501-529), so the CAPTURE is the resolution
#: it is named after, which a picture Data is asked to look at has to
#: be.
def key(run, which, frames=8):
    """One key press through the product's own event queue."""
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(
        pygame.KEYDOWN, {"key": which, "unicode": "", "mod": 0}))
    run.pump(frames)
    pygame.event.clear()


def hover_point(entry, layout):
    """The CONTENT point on the FIELD NAME's line inside row 0.

    Native: the middle of the row's width, and five pixels into the
    row from its top — `ROW_Y1[0]` is 0, so that is the field name's
    own line, the part of the click area the band must stay off.
    """
    x1, y1, x2, _ = entry.row_rect(0)
    return researchnative.window_point(((x1 + x2) // 2, y1 + 5), layout)


def panel_open(run):
    """Is the change panel the thing on top right now?"""
    return (run.app.dispatcher.overlay_name == "research_change"
            and run.state.current_screen == SCREEN_CHANGE
            and hd(run).state == "ok")


def ensure_panel(run):
    """The change panel, open and READY — re-entered if it is not.

    Toggling the window in and out of fullscreen four times is a lot of
    desktop for one run, and on the display this was written for the
    compositor put its own keys into the window: the record of the
    first attempt has an `activate_field 1` — change mode's exit — that
    this driver did not send, and the last pass photographed the galaxy
    map. So the panel is CHECKED before every pass rather than assumed
    to have survived, and re-entered through the same front door the
    first entry used. Each re-entry is counted and reported; a pass
    whose picture is not the panel fails on `hd_active` regardless.
    """
    if panel_open(run) and panel_ready(run):
        return hd(run), False
    ensure_on_map(run)
    if not enter_change(run) or not panel_ready(run):
        raise livesend.WrongDialog(
            "change mode did not come back up between resolutions")
    return hd(run), True


def one_hover(run, screen, entry):
    """Hover row 0 of one box and read back what the screen made of it."""
    wx, wy = hover_point(entry, run.app.layout)
    # POSTED IN SCREEN COORDINATES, tested in content ones: in
    # fullscreen `App` subtracts `_fs_offset` off an incoming event's
    # position (main.py:181-195), so the driver adds it on the way in
    # and keeps the content point for the geometry.
    ox, oy = run.app._fs_offset or (0, 0)
    # THE STATE IS READ BACK, and it is read back because the first
    # run of this driver photographed the wrong row. The PHYSICAL
    # pointer is still lying wherever Data left it, and the frames
    # right after a fullscreen switch carry a real MOUSEMOTION for it
    # — one capture of thirty-two came out hovering entry 1 row 1 while
    # the driver had just asked for entry 0 row 0. The arithmetic said
    # yes both times, because `row_at` is a function of the POINT and
    # knows nothing about what the screen is holding.
    #
    # So the motion is posted until the screen's own `_hover` IS the
    # row, and how many tries it took is part of the record.
    attempts = 0
    with SendCounter(run.app.client) as counted:
        while attempts < 4:
            attempts += 1
            run.hd_motion(wx + ox, wy + oy)
            if screen._hover == (entry.index, 0):
                break
    counts, _ = counted.snapshot()
    band, row = entry.band_rect(0), entry.row_rect(0)
    point = screen.native_point(wx, wy)
    return {"entry": entry.index, "field": entry.field,
            "sends": counts, "quiet": sum(counts.values()) == 0,
            "attempts": attempts,
            "hover_is_the_row": screen._hover == (entry.index, 0),
            "point_window": [wx, wy], "point_native": list(point or ()),
            "hit": list(screen.row_at(wx, wy) or ()),
            "hover": list(screen._hover or ()),
            "row_rect": list(row), "band_rect": list(band),
            # The verdict, and it is arithmetic on the two rectangles
            # the screen itself drew with — not a repeat of them.
            "on_the_row": screen.row_at(wx, wy) == (entry.index, 0),
            "band_clear_of_the_point": point is not None
            and not (band[0] <= point[0] <= band[2]
                     and band[1] <= point[1] <= band[3])}


def one_resolution(run, screen):
    """One pass over the eight boxes at the size the window has now."""
    size = (run.app.win_w, run.app.win_h)
    run.pump(12)
    out = []
    for entry in screen._entries:
        if not entry.offered:
            continue
        got = one_hover(run, screen, entry)
        shot = run.capture(f"hover_e{entry.index}_{size[0]}x{size[1]}")
        got.update(hd_png=shot["hd_png"], native_png=shot["native_png"],
                   hd_active=shot["hd_active"],
                   showing_original=shot["showing_original"])
        out.append(got)
    return {"size": list(size), "hovers": out}


def main():
    args = [a for a in sys.argv[1:]]
    slot = int(args[0]) if args and args[0].isdigit() else SCRATCH[0]
    folder = args[-1] if args and not args[-1].isdigit() \
        else "work_order_166_nachtrag"
    run = Run(f"hover_{slot}", folder=folder)
    saves = hashes()
    counter = SendCounter(run.app.client)
    run.pump(40)

    # The GAME menu is on the MAP, and a run before this one may have
    # left the game somewhere else — `ensure_on_map` is what puts it
    # back, and without it the loader refuses with WrongDialog rather
    # than sending into the wrong dialog (livesend's own rule).
    ensure_on_map(run)
    record = gameload.load_slot(run, slot)
    ok, passes, before = False, [], None
    if record["loaded"] and enter_change(run) and panel_ready(run):
        screen, before = hd(run), pair(run)
        reentries = 0
        for _ in range(len(run.app._resolutions)):
            key(run, pygame.K_F11)              # into fullscreen
            screen, again = ensure_panel(run)
            reentries += bool(again)
            passes.append(one_resolution(run, screen))
            key(run, pygame.K_F11)              # back to a window
            key(run, pygame.K_F9)               # the next preset
        quiet = sum(1 for p in passes for h in p["hovers"]
                    if not h["quiet"])
        ensure_panel(run)
        left = esc_leave(run)
        after = pair(run)
        hovers = [h for p in passes for h in p["hovers"]]
        sizes = [tuple(p["size"]) for p in passes]
        wanted = [(w, h) for w, h, _ in run.app._resolutions]
        ok = bool(sorted(sizes) == sorted(wanted)
                  and len(passes) >= 4 and len(hovers) >= 4 * 4
                  and all(h["on_the_row"] for h in hovers)
                  and all(h["hover_is_the_row"] for h in hovers)
                  and all(h["band_clear_of_the_point"] for h in hovers)
                  and all(h["hd_active"] == "research_change"
                          and not h["showing_original"] for h in hovers)
                  and quiet == 0 and left.get("left") and after == before)
        print(f"    the four presets, each at its own size: "
              f"{sorted(sizes) == sorted(wanted)}")
        print(f"    {len(passes)} resolutions, {len(hovers)} hovers: "
              + ", ".join(f"{p['size'][0]}x{p['size'][1]}"
                          f"({len(p['hovers'])})" for p in passes))
        print(f"    every hover hit its row: "
              f"{all(h['on_the_row'] for h in hovers)}")
        print(f"    and the screen was holding that row when the "
              f"picture was taken: "
              f"{all(h['hover_is_the_row'] for h in hovers)} "
              f"({sum(h['attempts'] for h in hovers)} motions for "
              f"{len(hovers)} hovers)")
        print(f"    no band covered the field name under the pointer: "
              f"{all(h['band_clear_of_the_point'] for h in hovers)}")
        print(f"    hovers that sent something: {quiet} of {len(hovers)}")
        print(f"    the panel had to be re-entered {reentries} time(s) "
              f"between resolutions")
        print(f"    {before} -> {after} — unchanged {after == before}")
    run.save_record({"load": record, "passes": passes,
                     "reentries": reentries if passes else None,
                     "before": list(before or ()),
                     "sends": counter.counts,
                     "sent": [list(x) for x in counter.sent],
                     "ok": ok})
    close(run, saves)
    print("OK" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
