"""Render the colony list to PNGs, without the game and without a save.

Judging an allocation track needs to be possible in one second, not
one game start plus 85 turns. This builds the real screen — the real
`frame.png` over the real `boxes.json` geometry — around fake rows
defined below, and writes both drawing modes from ONE run.

    python tools/colony_list_preview.py
    python tools/colony_list_preview.py --size 2560x1440 --out-dir /tmp/x

Every image is written twice, full size and 50 %. **The 50 % version
is the noise test.** A track is forty-two repeating slots with a
dashed region and a hairline in it — exactly the kind of picture that
looks detailed at 1:1 and turns to grain one step away. Structure
that survives the reduction reads as calm at full size; structure
that dissolves was noise pretending to be information. No pixel check
can say that: it measures whether ink landed, not whether it settles.

This rendered the comparison that deleted figure mode: a sprite per
colonist lost to a square per colonist, because the silhouettes did
not survive the 50 % copy and the zone rule ended up carrying the
profession they were supposed to carry. Only squares remain, and
`--pop-dir` with it.

Output goes to /tmp, not into the tree, and every path printed is
absolute: both extractor faults in the fundament printed a success
line with a RELATIVE path in it, which is what hid them.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

from core import palette, resources  # noqa: E402
from core.box import load_boxes  # noqa: E402
from core.config import REF_W, REF_H, load_settings  # noqa: E402
from core.layout import Layout  # noqa: E402
from core.style import StyleRenderer  # noqa: E402

SCREEN = os.path.join(ROOT, "screens", "colony_summary")
DEFAULT_OUT_DIR = os.path.join("/tmp", "colony_list_preview")

# ── The rows ──────────────────────────────────────────────────────
#
# Fake, and defined here rather than read from a savegame: a preview
# that needs somebody's save answers differently for everybody, and
# the interesting rows are the ones a real empire rarely holds all at
# once. Keys are exactly what `colonyrows.build_rows` produces —
# name, pops, jobs, no_farming, max_pop — so the renderer cannot tell
# the difference.
#
# `jobs` is (food, industry, research) in ECON order.

#: Production names are real, out of the player's TECHNAME.LBX
#: (techinit.cpp:43-73 gives the walk). They are NOT shipped and
#: `build_rows` leaves `producing` empty for want of an extractor —
#: these are here so the column can be seen at all.
#:
#: 22 pops on one planet. This is where the ORIGINAL squishes
#: hardest: it packs one icon per colonist into a fixed column and
#: `Calculate_Squish_Step_` closes the spacing until they fit. The HD
#: track does not squish — the slot is a fixed unit — so this row is
#: exactly where the two designs diverge most, and the thing to judge
#: is whether twenty-two adjacent slots still read as countable.
STRESS = {"name": "Vega I", "pops": 22, "jobs": [8, 9, 5],
          "no_farming": False, "climate": 8, "max_pop": 24,
          "producing": "Atmosphere Renewer", "producing_turns": 8,
          "can_buy": True}

#: Meant to be three race groups in one row. **It still cannot be
#: drawn as one — but not for the reason this note used to give.**
#: The mask DOES have a second source. The pop word's low nibble was
#: verified live on 1 September 2026: 131 colonists across five
#: owners, each carrying its own colony's `owner`, against
#: `s_player.race` values (5, 2, 3, 4, 0) that equal no player's own
#: index — so the data refutes the "race" reading rather than merely
#: agreeing with the player one (`core/structs/colony.py`).
#:
#: What remains open is only the meaning of 8 and 9. Those are the
#: android and native sentinels, which `Get_Effective_Pop_Player_`
#: maps to the colony's owner (colony.cpp:1261); neither occurs in
#: any sample save, so that one branch is still transcription only —
#: and androids and natives are exactly the cases the shading was
#: wanted for. `colonyrows` reads no nibble, so every row reaching
#: the renderer is race-blind and this one is identical to any
#: single-race row with the same split. Kept, with a line in the
#: tool's output, because a preview that quietly substituted
#: professions for races would answer a question nobody asked.
RACE_GROUPS = {"name": "Sol III", "pops": 12, "jobs": [4, 5, 3],
               "no_farming": False, "climate": 9, "max_pop": 16,
               "producing": "Research Lab", "producing_turns": 3,
               "can_buy": True}

#: max_farms == 0. The label is drawn AFTER the track, in the
#: reserved tail column, because the collapsed food zone has no width
#: to hold it — the first version drew it at the bar's left and the
#: worker squares painted straight over it.
NO_FARMING = {"name": "Kif II", "pops": 9, "jobs": [0, 7, 2],
              "no_farming": True, "climate": 1, "max_pop": 14,
              "producing": "Alien Control Center",
              "producing_turns": 12, "can_buy": False}

#: max_pop 9, so 33 of the 42 slots are unreachable. The judgement
#: this row exists for: does that long faint baseline read as room
#: the colony can still be GIVEN — Advanced City Planning,
#: Biospheres, Subterranean, terraforming — or as a track cut off?
#: Opposite meanings, and only a picture settles which one it has.
SMALL = {"name": "Nazin I", "pops": 3, "jobs": [1, 1, 1],
         "no_farming": False, "climate": 5, "max_pop": 9,
         "producing": "Trade Goods", "producing_turns": 0,
         "can_buy": False}

#: The structural maximum of the name column — and the one case the
#: column is deliberately NOT sized to hold. `s_star.name` is str15
#: (star.py:35) and a player can type all fifteen when renaming a
#: home star (namestar.cpp:262); fifteen W's plus " V" measures 336 px
#: at `name_font` 21. The column is 236 and the room before the clip
#: is 244 — 236 less `name_gap` 14, plus the `pad_x` 22 that right
#: alignment lets the name grow LEFT into — so this row ellipsises.
#: That is the designed outcome and not a fault: reserving for 336
#: would spend a hundred px of the one horizontal budget on a name
#: nobody types (`layout.json`, `_name_width_note`).
#:
#: What the picture has to settle is the two things no assertion
#: covers — whether the cut still reads as a name, and whether the
#: overflow going left looks like overflow rather than like a second
#: column. The failure this row exists to catch is the one LEFT
#: alignment produced: the name printed onto the track's first slots
#: and the squares, drawn after it, painted over the evidence.
EXTREME_NAME = {"name": "WWWWWWWWWWWWWWW V", "pops": 6, "jobs": [2, 2, 2],
                "no_farming": False, "climate": 7, "max_pop": 11,
                "producing": "Deuterium Fuel Cells", "producing_turns": 5,
                "can_buy": False}

ROWS = [STRESS, RACE_GROUPS, NO_FARMING, SMALL, EXTREME_NAME]


def build_context(width, height):
    """Everything the real screen renders with, minus the screen.

    `palette.init` must run BEFORE the renderers are imported:
    decision 18 has them resolve their colour constants at import
    time, so importing first would bind the code defaults and every
    skin colour in the preview would be a lie.
    """
    settings = load_settings()
    res = resources.init(settings)
    colors = res.load_json(
        f"assets/shared/skins/{res.skin}/colors.json", {}) or {}
    palette.init(colors)

    from screens.colony_summary import colonylist

    layout = Layout(width, height)
    style = StyleRenderer(res.skin_dir(), res.font(), colors)
    data = res.load_json("screens/colony_summary/layout.json", {}) or {}
    boxes = load_boxes(os.path.join(SCREEN, "boxes.json"), width, height)
    return dict(res=res, colors=colors, layout=layout, style=style,
                data=data, boxes=boxes, colonylist=colonylist)


def box_rect(boxes, name):
    """The screen's own box lookup, including `content_offset`."""
    for box in boxes:
        if box.name == name:
            x, y, w, h = box.ref_rect
            offset = box.style.get("content_offset")
            return (x + offset[0], y + offset[1], w, h) if offset else \
                box.ref_rect
    return None


def render_screen(ctx, rows, width, height):
    """One full screen: background, panel fills, list, frame, title.

    The same order `ColonySummaryScreen.render` uses, minus the
    sidebar and the buttons, which need a player record and say
    nothing about the track.
    """
    layout, data = ctx["layout"], ctx["data"]
    surface = pygame.Surface((width, height))
    surface.fill(tuple(ctx["colors"].get("background", [6, 8, 16]))[:3])

    panel_bg = palette.col("colony_summary", "panel_background", (8, 11, 20))
    for name in data.get("panels", {}):
        if name.startswith("_"):
            continue
        ref = box_rect(ctx["boxes"], name)
        if ref:
            surface.fill(panel_bg[:3], pygame.Rect(*layout.rect(ref)))

    ref = box_rect(ctx["boxes"], "list_area")
    if ref is None:
        raise SystemExit("boxes.json has no list_area box for this size")
    ctx["colonylist"].render(surface, rows, pygame.Rect(*layout.rect(ref)),
                             data.get("list", {}), layout, ctx["style"])

    frame_path = os.path.join(SCREEN, "assets", "frame.png")
    if os.path.exists(frame_path):
        x, y, w, h = layout.rect((0, 0, REF_W, REF_H))
        frame = pygame.image.load(frame_path).convert_alpha()
        surface.blit(pygame.transform.smoothscale(frame, (w, h)), (x, y))
    else:
        print(f"  frame.png missing at {frame_path} — rendered without it")

    cfg = data.get("frame", {})
    if cfg.get("title_rect") and cfg.get("title"):
        x, y, w, h = layout.rect(cfg["title_rect"])
        text = ctx["style"].render_text(
            cfg["title"], layout.font_size(cfg.get("title_font", 30)),
            palette.col("colony_summary", "title", (200, 210, 238)))
        surface.blit(text, (x + (w - text.get_width()) // 2,
                            y + (h - text.get_height()) // 2))
    return surface


def write_pair(surface, out_dir, stem):
    """The image and its 50 % reduction. Absolute paths, both."""
    full = os.path.join(out_dir, f"{stem}.png")
    half = os.path.join(out_dir, f"{stem}_50.png")
    pygame.image.save(surface, full)
    w, h = surface.get_size()
    pygame.image.save(
        pygame.transform.smoothscale(surface, (w // 2, h // 2)), half)
    print(f"  {full}\n  {half}   (50 % — the noise test)")
    return full, half


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="1920x1080", help="WxH")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    os.makedirs(args.out_dir, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((32, 32))
    ctx = build_context(width, height)

    print(f"{width}x{height} -> {os.path.abspath(args.out_dir)}\n")
    print("rows:")
    write_pair(render_screen(ctx, ROWS, width, height),
               args.out_dir, "colony_list")

    # ── The invariant, made visible ──
    # One square is the same size whatever else is on screen, because
    # the unit comes from the engine's population cap and not from the
    # widest colony in the list. The smoke test asserts it in pixels;
    # this renders the two cases so a human can see the thing the
    # assertion is about. Stacked rather than left-and-right on
    # purpose: the tracks then share an x axis, and a difference of
    # one slot shows up as a step instead of needing to be measured.
    print("\ninvariant (same row alone, then beside a larger colony):")
    alone = render_screen(ctx, [SMALL], width, height)
    together = render_screen(ctx, [SMALL, STRESS], width, height)
    pair = pygame.Surface((width, height * 2))
    pair.blit(alone, (0, 0))
    pair.blit(together, (0, height))
    write_pair(pair, args.out_dir, "colony_list_invariant")

    # Say it as well as show it: a picture of two tracks is only
    # evidence if somebody compares them, and a comparison is exactly
    # what a machine does better.
    #
    # The band is the FIRST ROW only. Comparing the whole screen was
    # the first version and it reported a difference every time —
    # correctly, because the second rendering has a second row in it.
    # A comparison that is guaranteed to differ tests nothing, and it
    # reads as a failure of the thing being inspected rather than of
    # the instrument, which is the worse way round.
    cfg = ctx["data"].get("list", {})
    scale = ctx["layout"].scale
    x, y, w, _h = ctx["layout"].rect(box_rect(ctx["boxes"], "list_area"))
    band = pygame.Rect(x, y, w, int((cfg.get("pad_y", 12)
                                     + cfg.get("row_height", 60)) * scale))
    same = (pygame.surfarray.array3d(alone.subsurface(band))
            == pygame.surfarray.array3d(together.subsurface(band))).all()
    print(f"  shared row identical in both renderings: "
          f"{'yes' if same else 'NO — the unit moved with the row set'}")

    print("\n  note: the 'three race groups' row renders identically to a "
          "single-race row.\n  The nibble's mask IS confirmed live — 0..7, "
          "verified 1 September 2026, and the\n  data refutes the 'race' "
          "reading. What is still open is only the meaning of 8\n  and 9, the "
          "android and native sentinels, which are the cases the shading\n  "
          "was wanted for. colonyrows reads no nibble, so no row can "
          "differ by race.\n  Not a fault in this tool.")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
