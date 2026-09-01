"""Render the colony list to PNGs, without the game and without a save.

Judging an allocation track needs to be possible in one second, not
one game start plus 85 turns. This builds the real screen — the real
`frame.png` over the real `boxes.json` geometry — around fake rows
defined below, and writes both drawing modes from ONE run.

    python tools/colony_list_preview.py
    python tools/colony_list_preview.py --pop-dir ~/moo2/pop_sprites
    python tools/colony_list_preview.py --size 2560x1440 --out-dir /tmp/x

Every image is written twice, full size and 50 %. **The 50 % version
is the noise test.** A track is forty-two repeating slots with a
dashed region and a hairline in it — exactly the kind of picture that
looks detailed at 1:1 and turns to grain one step away. Structure
that survives the reduction reads as calm at full size; structure
that dissolves was noise pretending to be information. No pixel check
can say that: it measures whether ink landed, not whether it settles.

**Both modes come out of one invocation**, against one `Layout` and
one `boxes.json` read. From two runs a changed argument or an edited
layout.json could slip between them, and the pair would compare two
LAYOUTS rather than two renderings of one — the exact failure the
shared `track_metrics`/`row_regions` exist to prevent, put back by
the instrument meant to inspect it.

Figure mode needs `--pop-dir`: the sprites are cut from the player's
own game and are not in the repository (decision 40), so nothing here
reads them from the tree. Without it the tool says so in one line and
renders squares. It never crashes for a missing or malformed set — it
reports through the exit code.

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

#: 22 pops on one planet. This is where the ORIGINAL squishes
#: hardest: it packs one icon per colonist into a fixed column and
#: `Calculate_Squish_Step_` closes the spacing until they fit. The HD
#: track does not squish — the slot is a fixed unit — so this row is
#: exactly where the two designs diverge most, and the thing to judge
#: is whether twenty-two adjacent slots still read as countable.
STRESS = {"name": "Vega I", "pops": 22, "jobs": [8, 9, 5],
          "no_farming": False, "max_pop": 24}

#: Meant to be three race groups in one row. **It cannot be drawn as
#: one.** Race shading needs the pop word's low nibble, whose mask
#: has no second source, so `colonyrows` never reads it and every row
#: reaching the renderer is race-blind. This row is identical to any
#: single-race row with the same split. Kept, with a line in the
#: tool's output, because a preview that quietly substituted
#: professions for races would answer a question nobody asked.
RACE_GROUPS = {"name": "Sol III", "pops": 12, "jobs": [4, 5, 3],
               "no_farming": False, "max_pop": 16}

#: max_farms == 0. The label is drawn AFTER the track, in the
#: reserved tail column, because the collapsed food zone has no width
#: to hold it — the first version drew it at the bar's left and the
#: worker squares painted straight over it.
NO_FARMING = {"name": "Kif II", "pops": 9, "jobs": [0, 7, 2],
              "no_farming": True, "max_pop": 14}

#: max_pop 9, so 33 of the 42 slots are unreachable. The judgement
#: this row exists for: does that long faint baseline read as room
#: the colony can still be GIVEN — Advanced City Planning,
#: Biospheres, Subterranean, terraforming — or as a track cut off?
#: Opposite meanings, and only a picture settles which one it has.
SMALL = {"name": "Nazin I", "pops": 3, "jobs": [1, 1, 1],
         "no_farming": False, "max_pop": 9}

ROWS = [STRESS, RACE_GROUPS, NO_FARMING, SMALL]


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

    from screens.colony_summary import colonyfigures, colonylist

    layout = Layout(width, height)
    style = StyleRenderer(res.skin_dir(), res.font(), colors)
    data = res.load_json("screens/colony_summary/layout.json", {}) or {}
    boxes = load_boxes(os.path.join(SCREEN, "boxes.json"), width, height)
    return dict(res=res, colors=colors, layout=layout, style=style,
                data=data, boxes=boxes,
                colonylist=colonylist, colonyfigures=colonyfigures)


def box_rect(boxes, name):
    """The screen's own box lookup, including `content_offset`."""
    for box in boxes:
        if box.name == name:
            x, y, w, h = box.ref_rect
            offset = box.style.get("content_offset")
            return (x + offset[0], y + offset[1], w, h) if offset else \
                box.ref_rect
    return None


def render_screen(ctx, rows, figures, width, height):
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
                             data.get("list", {}), layout, ctx["style"],
                             figures)

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


def load_pop_set(ctx, pop_dir):
    """A FigureSet from `pop_dir`, or None with a reason on one line.

    Goes through the real `colonyfigures.load_figures`, so the crop
    baseline guard runs here exactly as it would in the game instead
    of being skipped by the instrument meant to surface it. The
    filenames come from layout.json, so this tool holds no second
    copy of them; `enabled` is forced on because the shipped default
    is off and `--pop-dir` IS the decision to turn it on.
    """
    cfg = dict(ctx["data"].get("list", {}))
    figures_cfg = dict(cfg.get("figures") or {})
    figures_cfg["enabled"] = True
    cfg["figures"] = figures_cfg
    names = figures_cfg.get("sprites") or []

    class _DirRes:
        """Resolves the sprite names into --pop-dir and nowhere else."""

        @staticmethod
        def screen_file(_screen, *parts):
            path = os.path.join(pop_dir, parts[-1])
            return path if os.path.exists(path) else None

    try:
        figures = ctx["colonyfigures"].load_figures(_DirRes(), cfg)
    except ValueError as exc:
        # The crop-baseline guard. Loud, but not a traceback: a
        # diagnostic should degrade, not crash. The non-zero exit at
        # the end is how the tool reports that it found something.
        print(f"\n  FIGURE SET REFUSED\n  {exc}\n")
        return None, False
    if figures is None:
        # Asked for by name and not delivered. Not a crash, but not
        # nothing either: --pop-dir IS the request for figure mode, so
        # an empty directory is a finding and leaves through the exit
        # code. Omitting the argument entirely is the quiet path.
        print(f"  figure mode skipped: {pop_dir} has none of "
              f"{', '.join(names)}")
        return None, False
    return figures, True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="1920x1080", help="WxH")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--pop-dir", help="directory holding the pop sprites; "
                                      "without it, square mode only")
    args = ap.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    os.makedirs(args.out_dir, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((32, 32))
    ctx = build_context(width, height)

    figures, ok = (None, True)
    if args.pop_dir:
        figures, ok = load_pop_set(ctx, args.pop_dir)
    else:
        print("  figure mode skipped: no --pop-dir given (the pop sprites "
              "are cut from the player's own game and are not shipped)")

    modes = [("squares", None)] + ([("figures", figures)] if figures else [])
    print(f"\n{width}x{height} -> {os.path.abspath(args.out_dir)}")
    for name, figure_set in modes:
        print(f"\n{name}:")
        write_pair(render_screen(ctx, ROWS, figure_set, width, height),
                   args.out_dir, f"colony_list_{name}")

    # ── The invariant, made visible ──
    # One square is the same size whatever else is on screen, because
    # the unit comes from the engine's population cap and not from the
    # widest colony in the list. The smoke test asserts it in pixels;
    # this renders the two cases so a human can see the thing the
    # assertion is about. Stacked rather than left-and-right on
    # purpose: the tracks then share an x axis, and a difference of
    # one slot shows up as a step instead of needing to be measured.
    print("\ninvariant (same row alone, then beside a larger colony):")
    alone = render_screen(ctx, [SMALL], figures, width, height)
    together = render_screen(ctx, [SMALL, STRESS], figures, width, height)
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
          "single-race row.\n  Race shading needs the pop nibble, whose mask has "
          "no second source, so nothing\n  reads it and no row can differ "
          "by race. Not a fault in this tool.")
    return 0 if (ok and same) else 1


if __name__ == "__main__":
    sys.exit(main())
