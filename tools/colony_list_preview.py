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

**`--live` builds the rows from a running game's snapshot, and
without it `--native` is not a comparison.** For its first weeks this
tool rendered the synthetic empire and nothing else, and a run
against a game with 55 colonies at stardate 3502.4 wrote a
side-by-side whose HD half listed Vega I, Sol III, Kif II, a name of
ten W's and Nazin I over a sidebar of 18432 / -214 / 39 / 7 / +12 /
1180, and whose native half showed Blucher II, Wolf II, Draconis V
over 878 / +42 / 78 / 17 / -3 / 27. Two different empires side by
side, offered as a comparison, with nothing in the image saying so.
The API was reachable throughout — `struct_probe.py` read the same
game in the same minute. The tool simply never asked.

`--live` asks. It takes one STATE_SNAPSHOT through
`core.game_client.fetch_snapshot` — the same call `struct_probe`
makes, in one place rather than two — and hands the real state to the
real screen, so `build_rows` runs over the wire's own colonies. It
does NOT fall back to the synthetic empire when the game is
unreachable: that substitution is the thing the switch exists to
prevent.

**`--native` puts a 640x480 original screenshot beside the HD render,
scaled to the same height, in one image.** That side-by-side is the
method that caught the mislabelled Research field, the misplaced TURN
button and the oversized ship icons. It is not optional rigour; it is
the only check that has never come back empty. The original half
cannot be synthesised here — it has to come off a running game (the
Extension API carries the 640x480 framebuffer, see
`doc/ext_api_dokumentation_v3.md`), so without `--native` this tool
writes the HD half and says the comparison is incomplete. With
`--native` but without `--live` it writes the image and says, on the
image, that it is not a comparison.

**Every image carries a band naming where its rows came from**, under
`--live` as well as without it. See `provenance`.

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
from core.game_client import fetch_snapshot  # noqa: E402
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
            # prof lives in POP_MASK_PROF, >> 7 (pop.h:10), and the
            # ASSIGNED bit is set because a colonist in a live
            # snapshot always has it: `Get_Cluster_` is the only
            # thing that clears it (colmove.cpp:70) and it clears it
            # for exactly as long as a cluster is in hand. A fixture
            # without it is a state no game reaches, and it drew
            # every row correctly while the original would have shown
            # a column of NO icons — which is what `colonyicons`
            # counts and what a pop move aims at.
            struct.pack_into("<I", b, off["pop"][0] + 4 * slot,
                             ((prof & 3) << 7)
                             | spec.POP_MASK_ASSIGNED)
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

def render_screen(app, screen, state, width, height, sort_key="name"):
    """One full screen, through `ColonySummaryScreen.render`.

    Everything on it — background, panel fills, the list, the
    sidebar, the sort bar, the frame, the title — comes from the
    screen's own method. Nothing is drawn here.

    `state` is a snapshot-shaped object: `_Snapshot` for the
    synthetic empire, or a real `GameState` off the wire under
    `--live`. The screen cannot tell them apart, which is the whole
    point of faking the state rather than the drawing — and it is
    also why the caller has to say which one it handed over. See
    `provenance`.
    """
    screen._sort_key = sort_key
    screen.update(state)
    surface = pygame.Surface((width, height))
    surface.fill(tuple(app.colors.get("background", [6, 8, 16]))[:3])
    screen.render(surface)
    return surface


# ── Where the rows came from, ON the picture ──────────────────────
#
# The failure this exists for was live, and it was invisible. A run
# against a game with 55 colonies at stardate 3502.4 wrote a
# side-by-side whose HD half showed Vega I, Sol III, Kif II, a name
# of ten W's and Nazin I with a sidebar of 18432 / -214 / 39 / 7 /
# +12 / 1180, and whose native half showed Blucher II, Wolf II,
# Draconis V and 878 / +42 / 78 / 17 / -3 / 27. Two different
# empires side by side, presented as a comparison, and nothing in
# the image said so. The API was reachable the whole time; the tool
# simply never asked.
#
# So: every image this tool writes carries a band naming its source,
# under --live as well. A tool whose output LOOKS like a measurement
# must not draw invented data without a mark on it — the same class
# as the tenth row that used to vanish in silence, an absence shaped
# like a result.
#
# The band is deliberately not styled like the game. It is tool
# chrome and has to read as an annotation somebody added, not as
# part of the screen being annotated.
BAND_BG = (24, 24, 28)
BAND_SYNTHETIC = (232, 172, 72)
BAND_LIVE = (120, 210, 140)
BAND_SUB = (170, 176, 190)


def provenance(state, screen, live, sort_key):
    """(headline, detail, colour) for the band. Never empty."""
    # Imported here and not at the top: decision 18 has the renderers
    # resolve their palette colours at IMPORT time, so `build_screen`
    # must run `palette.init` before this module is pulled in. A
    # top-level import would bind the code defaults and every colour
    # in the preview would be a lie.
    from screens.colony_summary import colonylist
    rows = screen._rows
    if live:
        drawn = colonylist.rows_drawn(
            pygame.Rect(*screen.layout.rect(screen.box_rect("list_area"))),
            screen._data.get("list", {}), screen.layout.scale, len(rows))
        return ("LIVE — rows built from the running game's snapshot",
                f"stardate {state.stardate_str}, screen "
                f"{state.current_screen}, {state.num_colonies} colony "
                f"records, {len(rows)} of them the local player's and not "
                f"outposts, {drawn} drawn, sorted by {sort_key}",
                BAND_LIVE)
    return ("SYNTHETIC — these colonies do not exist",
            f"{len(rows)} rows hand-built in colony_list_preview.py to "
            f"exercise shapes, not to measure anything. Run with --live "
            f"against a running game for rows off the wire.",
            BAND_SYNTHETIC)


def with_band(surface, app, headline, detail, colour):
    """The surface with a provenance band above it.

    Above and not over: an overlay hides the thing being judged, and
    the first instinct — a small corner watermark — is exactly what
    somebody stops seeing by the third run.
    """
    head_px = app.layout.font_size(26)
    sub_px = app.layout.font_size(17)
    head = app.style.render_text(headline, head_px, colour)
    sub = app.style.render_text(detail, sub_px, BAND_SUB)
    pad = max(8, head_px // 2)
    band_h = pad * 3 + head.get_height() + sub.get_height()
    out = pygame.Surface((surface.get_width(),
                          surface.get_height() + band_h))
    out.fill(BAND_BG)
    out.blit(head, (pad, pad))
    out.blit(sub, (pad, pad * 2 + head.get_height()))
    out.blit(surface, (0, band_h))
    return out


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


def side_by_side(hd, native_path):
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
    return pair


def colony_track_rect(app, screen, colony_index):
    """The TRACK of the colony with `colony_index`, where it is now.

    By IDENTITY, not by row number: the invariant check renders the
    same colony twice with different neighbours, and under any sort
    but the name it is not in the same row both times.

    **The track and not the whole row band.** The frame PNG is drawn
    over everything, and its metal edge bleeds three or four pixels
    into `list_area` on both sides — artwork that legitimately
    differs between one y and another. Comparing whole bands reported
    310 differing pixels, all of them in x 0..3 and 1405..1407, and
    none of them anything to do with the list. The track is also the
    exact object the invariant is about: `track_metrics` derives the
    slot from `POP_LIMIT_CAP` and the panel, so the squares are what
    must not move.
    """
    from screens.colony_summary import colonylist   # see `provenance`
    box = screen.box_rect("list_area")
    area = pygame.Rect(*app.layout.rect(box))
    cfg = screen._data.get("list", {})
    rows = screen._rows
    position = next((i for i, r in enumerate(rows)
                     if r["index"] == colony_index), None)
    bands = colonylist.row_bands(area, cfg, app.layout.scale, len(rows))
    if position is None or position >= len(bands):
        return None
    top, height = bands[position]
    scale = app.layout.scale
    track = colonylist.track_metrics(area, cfg, scale)
    left = (area.x + int(cfg.get("pad_x", 18) * scale)
            + int(cfg.get("name_width", 320) * scale) + track.slack)
    return pygame.Rect(left, top, track.width, height)


def check_invariant(app, screen, width, height, sort_key, out_dir):
    """One square is the same size whatever else is in the list.

    **This checked the wrong object until 3 September 2026.** It
    compared the FIRST ROW BAND across two renderings, which is the
    same colony only while the sort happens to leave it first: with
    `--sort population` it reported "NO — the unit moved with the row
    set" every time, correctly observing that two different colonies
    look different. The slot width is computed by
    `colonylist.track_metrics` from `POP_LIMIT_CAP` and the panel,
    and takes no rows at all, so it could not have moved.

    Asserting `track_metrics` directly would be worse, not better: it
    is a pure function of things the row set does not touch, so the
    assertion cannot fail and therefore says nothing. What CAN fail
    is the RENDER — an earlier version of the bar derived the unit
    from the widest `max_pop` in the list, and that is the fault this
    exists to catch. So it renders one colony alone and again beside
    a much larger one, finds THAT COLONY in each result by its own
    index, and demands the two bands be identical pixel for pixel.

    The synthetic pair is used even under `--live`, and the band on
    the image says so: the check needs two row sets that differ by a
    colony big enough to move a derived unit, and a live empire is
    whatever it is.
    """
    small = _Snapshot([COLONIES[3]])
    both = _Snapshot([COLONIES[3], COLONIES[0]])
    alone = render_screen(app, screen, small, width, height, sort_key)
    band_alone = colony_track_rect(app, screen, 0)
    together = render_screen(app, screen, both, width, height, sort_key)
    # COLONIES[3] is packed first, so it is colony 0 in both snapshots
    # — the identity is the array index and survives the re-sort.
    band_together = colony_track_rect(app, screen, 0)

    pair = pygame.Surface((width, height * 2))
    pair.blit(alone, (0, 0))
    pair.blit(together, (0, height))
    pair = with_band(
        pair, app,
        "SYNTHETIC — the slot invariant, one colony alone then beside "
        "a bigger one",
        f"the same colony in both halves, found by identity and not by "
        f"row; sorted by {sort_key}. One square must be the same size "
        f"in both, because the unit comes from POP_LIMIT_CAP and the "
        f"panel, never from the rows.",
        BAND_SYNTHETIC)
    write_pair(pair, out_dir, "colony_summary_invariant")

    if band_alone is None or band_together is None:
        print("  the colony is not drawn in both renderings — cannot "
              "compare")
        return False
    same = (pygame.surfarray.array3d(alone.subsurface(band_alone))
            == pygame.surfarray.array3d(
                together.subsurface(band_together))).all()
    print(f"  the same colony's track is identical in both renderings: "
          f"{'yes' if same else 'NO — the unit moved with the row set'}")
    return same


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="1920x1080", help="WxH")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--native", default=None,
                    help="640x480 screenshot of the original's own "
                         "colony summary, for the side-by-side")
    ap.add_argument("--sort", default="name",
                    help="which sort key the bar shows as active")
    ap.add_argument("--live", action="store_true",
                    help="build the rows from a running game's snapshot "
                         "instead of the synthetic empire — what makes "
                         "--native a comparison rather than two "
                         "unrelated pictures")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=17362)
    args = ap.parse_args()

    width, height = (int(v) for v in args.size.lower().split("x"))
    os.makedirs(args.out_dir, exist_ok=True)

    # The snapshot is fetched BEFORE pygame comes up, so a tool that
    # cannot reach the game says so in a second instead of opening a
    # window first.
    state, live = _Snapshot(COLONIES), False
    if args.live:
        state, why = fetch_snapshot(host=args.host, port=args.port)
        if state is None:
            print(why)
            print("  --live cannot fall back to the synthetic empire: "
                  "that is exactly the\n  substitution this switch "
                  "exists to prevent.")
            return 1
        live = True

    pygame.init()
    pygame.display.set_mode((32, 32))
    app, screen = build_screen(width, height)

    print(f"{width}x{height} -> {os.path.abspath(args.out_dir)}\n")
    full = render_screen(app, screen, state, width, height, args.sort)
    head, detail, colour = provenance(state, screen, live, args.sort)
    print(f"{head}\n  {detail}\n")
    if live and not screen._rows:
        print("  the running game has no colony for the local player, "
              "so the list is\n  empty and there is nothing to compare. "
              "Load a game with colonies.")
    print("full screen (list + sidebar + sort bar, one render):")
    write_pair(with_band(full, app, head, detail, colour),
               args.out_dir, "colony_summary")

    print("\ninvariant (same colony alone, then beside a larger one):")
    same = check_invariant(app, screen, width, height, args.sort,
                           args.out_dir)

    print("\nside by side with the original:")
    if args.native:
        # The band goes on the COMPOSED image, because this is the
        # picture the two-empires failure was in: whatever the halves
        # are, the caption has to be attached to them together.
        pair = side_by_side(full, args.native)
        native_head = (head if live else
                       "MISMATCHED — synthetic rows beside a real "
                       "screenshot")
        native_detail = (
            f"left: {detail}   |   right: {os.path.abspath(args.native)}")
        if not live:
            native_detail = (
                "left: rows that do not exist. right: a real game. THIS "
                "IS NOT A COMPARISON — re-run with --live so both halves "
                "come from the same empire. | " + detail)
        write_pair(with_band(pair, app, native_head, native_detail,
                             colour if live else BAND_SYNTHETIC),
                   args.out_dir, "colony_summary_vs_original")
        if not live:
            print("  WRITTEN, AND IT IS NOT A COMPARISON. The HD half "
                  "was drawn from the\n  synthetic empire and the other "
                  "half is a real game: two different\n  worlds side by "
                  "side. Re-run with --live.")
    else:
        print("  NOT RENDERED — no --native given, and the original "
              "half cannot be\n  synthesised here. It has to come off "
              "a running game: the Extension API\n  carries the "
              "640x480 framebuffer (ext_api_dokumentation_v3.md), so "
              "capture the\n  original's own Colonies screen and pass "
              "it as --native shot.png.\n  With --live as well, that "
              "is the one check that has never come back empty.")

    if not live:
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
