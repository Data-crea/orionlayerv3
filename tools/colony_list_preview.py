"""Render the whole colony summary to PNGs, without the game or a save.

Judging a screen has to be possible in one second, not one game start
plus 85 turns. This drives the REAL `ColonySummaryScreen.render` —
the real frame.png over the real boxes.json, the real sidebar, the
real sort bar — around a synthetic snapshot built below.

    python tools/colony_list_preview.py
    python tools/colony_list_preview.py --size 2560x1440 --out-dir /tmp/x
    python tools/colony_list_preview.py --native shot.png

**Nothing here reimplements any drawing.** Earlier versions called
`colonylist.render` directly and drew nothing else, so the sidebar
and the sort bar — two commits' worth of work — had no picture at
all, and the two deviations in the row renderer were found by reading
rather than by looking. What is faked is the STATE: real `s_star`,
`s_planet_data`, `s_colony` and `s_player` bytes, parsed by the real
specs, so `build_rows` and `_render_sidebar` cannot tell the
difference. Fake the state, never the drawing — a preview that draws
its own version of a screen is a picture of the preview.

Every image is written twice, full size and 50 %. **The 50 % version
is the noise test.** A track is forty-two repeating slots with a
dashed region and a hairline in it — exactly the kind of picture that
looks detailed at 1:1 and turns to grain one step away. Structure
that survives the reduction reads as calm at full size; structure
that dissolves was noise pretending to be information.

**`--native` puts a 640x480 original screenshot beside the HD render,
scaled to the same height, in one image.** That side-by-side is the
method that caught the mislabelled Research field, the misplaced TURN
button and the oversized ship icons. It is not optional rigour; it is
the only check that has never come back empty. The original half
cannot be synthesised here — it has to come off a running game (the
Extension API carries the 640x480 framebuffer, see
`doc/ext_api_dokumentation_v3.md`), so without `--native` this tool
writes the HD half and says the comparison is incomplete.

Output goes to /tmp, never into the tree, and every path printed is
absolute: both extractor faults in the fundament printed a success
line with a RELATIVE path in it, which is what hid them.
"""
import argparse
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402

from core import palette, resources  # noqa: E402
from core.config import SCREENS_DIR, load_settings  # noqa: E402
from core.layout import Layout  # noqa: E402
from core.style import StyleRenderer  # noqa: E402

DEFAULT_OUT_DIR = os.path.join("/tmp", "colony_list_preview")

# ── The synthetic empire ──────────────────────────────────────────
#
# One entry per colony, in the order they are packed. These are the
# INPUTS the engine computes from, not the outputs: `max_pop` is
# `COLCALC::Planet_Max_Population_For_Player_` over climate and size
# and cannot be chosen directly, so each row states the shape it is
# here to produce and the climate/size that yields it. A preview that
# hand-set max_pop would be drawing a state the game cannot reach.
#
# climate indexes PLANET_CLIMATE (orion2_consts.h:362-374); size
# indexes PLANET_SIZE, 0 Tiny to 4 Huge.

COLONIES = [
    # 22 of 25 slots. This is where the ORIGINAL squishes hardest —
    # it packs one icon per colonist into a fixed column and
    # Calculate_Squish_Step_ closes the spacing until they fit
    # (coldraw.cpp:12). The HD track does not squish, so this is
    # where the two designs diverge most and the thing to judge is
    # whether twenty-two adjacent slots still read as countable.
    dict(star="Vega", numeral=0, climate=9, size=4, pops=22,
         jobs=(8, 9, 5), max_farms=255, production=(16, 27, 11, 9),
         why="a nearly full track: 22 of a computed 25"),
    # Meant to be three race groups in one row. It cannot be drawn as
    # one: the nibble's mask IS confirmed live for 0..7, what is open
    # is the meaning of 8 and 9 (the android and native sentinels,
    # which are the cases the shading was wanted for), and
    # `colonyrows` reads no nibble at all. Kept, with a line in the
    # output, because a preview that quietly substituted professions
    # for races would answer a question nobody asked.
    dict(star="Sol", numeral=2, climate=8, size=3, pops=12,
         jobs=(4, 5, 3), max_farms=255, production=(8, 15, 7, 5),
         why="a mid-size colony with all three zones and a free tail"),
    # max_farms == 0, so "No Farming" renders. The food zone is
    # collapsed to nothing, which is exactly the case where a label
    # drawn at the bar's left edge got painted over by the worker
    # squares — every number right and nothing on screen.
    dict(star="Kif", numeral=1, climate=7, size=4, pops=9,
         jobs=(0, 7, 2), max_farms=0, production=(0, 21, 4, 6),
         why="No Farming, with a collapsed food zone"),
    # 3 of 9, so 33 of the 42 slots are unreachable. The judgement
    # this row exists for: does that long faint baseline read as room
    # the colony can still be GIVEN — Advanced City Planning,
    # Biospheres, Subterranean, terraforming — or as a track cut off?
    # Opposite meanings, and only a picture settles which.
    dict(star="Nazin", numeral=0, climate=7, size=2, pops=3,
         jobs=(1, 1, 1), max_farms=255, production=(2, 3, 2, 1),
         why="a long unreachable tail: 3 of a computed 9"),
    # The structural maximum of the name column, and the one case it
    # is deliberately NOT sized to hold. s_star.name is str15
    # (star.py:35) and a player can type all fifteen when renaming a
    # home star (namestar.cpp:262); fifteen W's plus " V" measures
    # 336 px at name_font 21 against a text budget of 244, so this
    # ellipsises. That is the designed degradation, and the two
    # things no assertion covers are whether the cut still reads as a
    # name and whether the leftward overflow reads as overflow.
    dict(star="W" * 15, numeral=4, climate=7, size=3, pops=6,
         jobs=(2, 2, 2), max_farms=255, production=(4, 6, 5, 3),
         why="the 336 px structural maximum, ellipsised"),
]

# ── The empire numbers ────────────────────────────────────────────
#
# Chosen to make the SIDEBAR'S LAYOUT FALSIFIABLE, not to look like a
# plausible empire. Plausible numbers are the ones that hide an
# alignment bug: six values of similar width sit in a column whether
# they are right-aligned or centred, and nothing in the picture says
# which. So:
#
#   bc 18432        five digits, the widest value
#   surplus_freighters 7   one digit, the narrowest
#     -> right alignment is visible AS alignment. Centred, these two
#        would be offset from each other by about two digit widths.
#   surplus_bc -214 NEGATIVE, so Red_If_Negative_Fmt_String_'s
#        transcription actually renders (eric.cpp:176). Every earlier
#        preview had a positive income and never drew it.
#   surplus_food +12 signed POSITIVE, so the explicit plus shows.
#   research_produced 1180  gross, and UNSIGNED — beside a signed
#        +12 and a signed -214 it is what makes the sign a per-row
#        property rather than a screen-wide one.
#   total_pop 39    a count, and it agrees with the colonies above.
#
# The four KINDS are therefore all distinguishable in one picture:
# a stock (18432), two net flows with their signs (-214, +12), a
# gross without one (1180) and two counts (39, 7).
PLAYER = dict(bc=18432, surplus_bc=-214, total_pop=39,
              surplus_freighters=7, surplus_food=12,
              research_produced=1180)


# ── Packing the snapshot ──────────────────────────────────────────

def _colony_bytes(owner, planet_idx, pops, jobs, max_farms, climate,
                  production):
    """One s_colony record, packed at the offsets the spec reads.

    Written through `core.structs.colony`'s own offsets rather than
    literals, so a spec change breaks this loudly instead of shifting
    the preview's meaning by two bytes.
    """
    from core.structs import colony as spec
    off = dict((n, (o, k)) for n, o, k in spec.SPEC.fields)
    b = bytearray(spec.SPEC.size)
    b[off["owner"][0]] = owner & 0xFF
    struct.pack_into("<h", b, off["planet"][0], planet_idx)
    b[off["n_pops"][0]] = pops
    slot = 0
    for prof, count in enumerate(jobs):
        for _ in range(count):
            # prof lives in POP_MASK_PROF, >> 7 (pop.h:10)
            struct.pack_into("<I", b, off["pop"][0] + 4 * slot,
                             (prof & 3) << 7)
            slot += 1
    b[off["max_farms"][0]] = max_farms
    b[off["climate"][0]] = climate
    for i, v in enumerate(production):
        struct.pack_into("<h", b, off["production"][0] + 2 * i, v)
    return bytes(b)


def _planet_bytes(colony_idx, star_idx, orbit, size, climate):
    from core.structs import planet as spec
    off = dict((n, (o, k)) for n, o, k in spec.SPEC.fields)
    b = bytearray(spec.SPEC.size)
    struct.pack_into("<h", b, off["colony_index"][0], colony_idx)
    struct.pack_into("<h", b, off["star_index"][0], star_idx)
    b[off["orbit"][0]] = orbit
    b[off["size"][0]] = size
    b[off["climate"][0]] = climate
    return bytes(b)


def _star_bytes(name, slots):
    from core.structs import star as spec
    b = bytearray(spec.SIZE)
    b[0:len(name)] = name.encode("latin-1")
    for i, v in enumerate(slots):
        struct.pack_into("<h", b, spec.PLANET_INDEX_OFFSET + 2 * i, v)
    return bytes(b)


def _player_bytes(values):
    from core.structs import player as spec
    off = dict((n, (o, k)) for n, o, k in spec.SPEC.fields)
    b = bytearray(spec.SIZE)
    b[off["name"][0]:off["name"][0] + 8] = b"Terrans\x00"
    b[off["race_name"][0]:off["race_name"][0] + 6] = b"Human\x00"
    b[off["race"][0]] = 5
    for field, value in values.items():
        offset, kind = off[field]
        struct.pack_into("<i" if kind == "i32" else "<h", b, offset, value)
    return bytes(b)


class _Snapshot:
    """What `ColonySummaryScreen.update` reads out of a snapshot.

    Deliberately only the attributes the screen touches. A fuller
    fake would be a second implementation of `GameState` and would
    drift from it silently.
    """

    def __init__(self, colonies):
        from core.structs import star as star_spec
        self.player_num = 0
        stars, planets, colony_raws = [], [], []
        for entry in colonies:
            star_idx = len(stars)
            slots = [-1] * 5
            # HAROLD::Planet_Number_ counts the OCCUPIED slots before
            # the planet, not the orbit (harold.cpp), so a numeral
            # has to be earned with real planets in front of it. The
            # fillers carry colony_index -1: they are planets nobody
            # has settled, which is what a numeral above I means.
            # Setting the orbit alone would leave every colony at
            # "I", and the first version of this did exactly that.
            for n in range(entry["numeral"]):
                slots[n] = len(planets)
                planets.append(_planet_bytes(-1, star_idx, n, 2, 0))
            planet_idx = len(planets)
            colony_idx = len(colony_raws)
            slots[entry["numeral"]] = planet_idx
            stars.append(_star_bytes(entry["star"], slots))
            planets.append(_planet_bytes(colony_idx, star_idx,
                                         entry["numeral"], entry["size"],
                                         entry["climate"]))
            colony_raws.append(_colony_bytes(
                0, planet_idx, entry["pops"], entry["jobs"],
                entry["max_farms"], entry["climate"],
                entry["production"]))
        self.stars = star_spec.parse_all(stars)
        self.planets_raw = planets
        self.colonies_raw = colony_raws
        self.player_raw = [_player_bytes(PLAYER)]


def build_screen(width, height):
    """The REAL screen object, wired to a real app-shaped host.

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

    from core.dispatcher import Dispatcher
    from core.screens_loader import register_all

    class _Client:
        class state:
            fields = []

        def activate_field(self, fid):
            pass

        def inject_click(self, x, y):
            pass

        def inject_key(self, key):
            pass

    class _App:
        _fs_offset = None

        def __init__(self):
            self.win_w, self.win_h = width, height
            self.res = res
            self.colors = colors
            self.layout = Layout(width, height)
            self.style = StyleRenderer(res.skin_dir(), res.font(), colors)
            self.screens_dir = SCREENS_DIR
            self.connected = True
            self.client = _Client()
            self.dispatcher = Dispatcher()

    app = _App()
    register_all(app, app.dispatcher, res)
    app.dispatcher.switch_to("colony_summary")
    return app, app.dispatcher.screens["colony_summary"]


# ── Rendering ─────────────────────────────────────────────────────

def render_screen(app, screen, colonies, width, height, sort_key="name"):
    """One full screen, through `ColonySummaryScreen.render`.

    Everything on it — background, panel fills, the list, the
    sidebar, the sort bar, the frame, the title — comes from the
    screen's own method. Nothing is drawn here.
    """
    screen._sort_key = sort_key
    screen.update(_Snapshot(colonies))
    surface = pygame.Surface((width, height))
    surface.fill(tuple(app.colors.get("background", [6, 8, 16]))[:3])
    screen.render(surface)
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


def side_by_side(hd, native_path, out_dir):
    """The HD render beside a 640x480 original, same height, one image.

    NEAREST-NEIGHBOUR for the original, on purpose. Smoothing a
    640x480 screenshot up to 1080p invents intermediate pixels and
    makes the original look like a worse version of the HD render
    rather than like a different one — and it hides exactly the
    thing the comparison is for, which is where the original put an
    edge. The HD side is untouched.
    """
    native = pygame.image.load(native_path)
    if native.get_size() != (640, 480):
        print(f"  note: {native_path} is {native.get_size()[0]}x"
              f"{native.get_size()[1]}, not 640x480 — scaling anyway, "
              f"but check it is a full-screen capture")
    scale = hd.get_height() / native.get_height()
    scaled = pygame.transform.scale(
        native, (int(native.get_width() * scale), hd.get_height()))
    gap = 16
    pair = pygame.Surface((hd.get_width() + gap + scaled.get_width(),
                           hd.get_height()))
    pair.fill((0, 0, 0))
    pair.blit(hd, (0, 0))
    pair.blit(scaled, (hd.get_width() + gap, 0))
    return write_pair(pair, out_dir, "colony_summary_vs_original")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="1920x1080", help="WxH")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--native", default=None,
                    help="640x480 screenshot of the original's own "
                         "colony summary, for the side-by-side")
    ap.add_argument("--sort", default="name",
                    help="which sort key the bar shows as active")
    args = ap.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    os.makedirs(args.out_dir, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((32, 32))
    app, screen = build_screen(width, height)

    print(f"{width}x{height} -> {os.path.abspath(args.out_dir)}\n")
    print("full screen (list + sidebar + sort bar, one render):")
    full = render_screen(app, screen, COLONIES, width, height, args.sort)
    write_pair(full, args.out_dir, "colony_summary")

    # ── The invariant, made visible ──
    # One square is the same size whatever else is on screen, because
    # the unit comes from the engine's population cap and not from
    # the widest colony in the list. The smoke test asserts it in
    # pixels; this renders the two cases so a human can see the thing
    # the assertion is about. Stacked rather than side by side on
    # purpose: the tracks then share an x axis, and a difference of
    # one slot shows up as a step instead of needing to be measured.
    print("\ninvariant (same colony alone, then beside a larger one):")
    small = [COLONIES[3]]
    alone = render_screen(app, screen, small, width, height, args.sort)
    together = render_screen(app, screen, small + [COLONIES[0]],
                             width, height, args.sort)
    pair = pygame.Surface((width, height * 2))
    pair.blit(alone, (0, 0))
    pair.blit(together, (0, height))
    write_pair(pair, args.out_dir, "colony_summary_invariant")

    # Say it as well as show it: a picture of two tracks is only
    # evidence if somebody compares them, and a comparison is exactly
    # what a machine does better. The band is the FIRST ROW only —
    # comparing whole screens reported a difference every time, and
    # correctly, because the second rendering has a second row in it.
    cfg = screen._data.get("list", {})
    scale = app.layout.scale
    x, y, w, _h = app.layout.rect(screen.box_rect("list_area"))
    band = pygame.Rect(x, y, w, int((cfg.get("pad_y", 12)
                                     + cfg.get("row_height", 60)) * scale))
    same = (pygame.surfarray.array3d(alone.subsurface(band))
            == pygame.surfarray.array3d(together.subsurface(band))).all()
    print(f"  shared row identical in both renderings: "
          f"{'yes' if same else 'NO — the unit moved with the row set'}")

    print("\nside by side with the original:")
    if args.native:
        side_by_side(full, args.native, args.out_dir)
    else:
        print("  NOT RENDERED — no --native given, and the original "
              "half cannot be\n  synthesised here. It has to come off "
              "a running game: the Extension API\n  carries the "
              "640x480 framebuffer (ext_api_dokumentation_v3.md), so "
              "capture the\n  original's own Colonies screen and pass "
              "it as --native shot.png.\n  Until then this comparison "
              "is INCOMPLETE, and it is the one check that\n  has "
              "never come back empty.")

    print("\n  note: the 'three race groups' row renders identically "
          "to a single-race row.\n  The nibble's mask IS confirmed "
          "live — 0..7, verified 1 September 2026, and the\n  data "
          "refutes the 'race' reading. What is still open is only the "
          "meaning of 8\n  and 9, the android and native sentinels, "
          "which are the cases the shading\n  was wanted for. "
          "colonyrows reads no nibble, so no row can differ by "
          "race.\n  Not a fault in this tool.")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
