#!/usr/bin/env python3
"""The colony screen and the build popup rendered OFFLINE from recorded stops.

    python tools/colony_offline.py [RECORD_DIR] [--sizes 1920x1080,...]

Work order 180 B and C. `tools/colony_record.py` keeps, at each stop, the
raw STATE payload, the field list and the game's own picture of the same
moment. This rebuilds the snapshot from exactly those bytes (the engine's
own wire format — `core.game_state.parse_state`), hands it to the real
dispatcher of an offline App, and writes the HD screen that claims it
beside the native picture: `<stop>_<W>x<H>_offline_side.png`.

"The same state" is literal here: one payload, one field list, one
framebuffer, recorded together. What cannot be recorded is the pointer,
so no hover is drawn.
"""
import argparse
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

RECORD = os.path.expanduser(
    "~/orionlayer-fixtures/evidence/work_order_180/B_record")
SIZES = [(1920, 1080), (2576, 1432), (3840, 2160)]


def load_stop(base):
    """The recorded snapshot of one stop, fields and all."""
    from core import game_state as gsm
    with open(base + "_state.bin", "rb") as fh:
        gs = gsm.parse_state(fh.read())
    with open(base + "_fields.json", encoding="utf-8") as fh:
        rows = json.load(fh)
    fields = []
    for index, x, y, xe, ye, ftype, hk in rows:
        f = gsm.FieldInfo()
        (f.index, f.x, f.y, f.x_end, f.y_end, f.field_type,
         f.hotkey) = index, x, y, xe, ye, ftype, hk
        fields.append(f)
    gs.fields = fields
    return gs


def render(gs, size):
    """(surface, screen name) as the real dispatcher routes this snapshot."""
    import hud_evidence as he
    app = he.make_app(*size)
    d = app.dispatcher
    d.update_from_game(gs)
    d.update_screens(gs)
    surf = pygame.Surface(size)
    surf.fill((0, 0, 0))
    if d.active is not None and not d.use_original:
        d.render(surf)
    return surf, (d.overlay_name or d.active_name or "-")


def side_by_side(native_png, hd):
    native = pygame.image.load(native_png)
    h = hd.get_height()
    w = int(640 * h / 480)
    out = pygame.Surface((w + hd.get_width(), h))
    out.blit(pygame.transform.scale(native, (w, h)), (0, 0))
    out.blit(hd, (w, 0))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("record", nargs="?", default=RECORD)
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--only", default=None, help="stop name prefix")
    args = ap.parse_args(argv)
    sizes = SIZES if not args.sizes else [
        tuple(int(v) for v in s.split("x")) for s in args.sizes.split(",")]
    with open(os.path.join(args.record, "record.json"),
              encoding="utf-8") as fh:
        stops = json.load(fh)["stops"]
    out = []
    for e in stops:
        if args.only and not e["name"].startswith(args.only):
            continue
        base = os.path.join(args.record, f"{e['step']:03d}_{e['name']}")
        if not os.path.exists(base + "_state.bin"):
            continue
        gs = load_stop(base)
        for size in sizes:
            hd, who = render(gs, size)
            tag = f"{base}_{size[0]}x{size[1]}_offline"
            pygame.image.save(hd, tag + "_hd.png")
            native = os.path.join(args.record, e["native_png"])
            if os.path.exists(native):
                pygame.image.save(side_by_side(native, hd), tag + "_side.png")
            out.append((e["name"], size, who))
            print(f"  {e['name']:24s} {size[0]}x{size[1]}  HD screen: {who}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
