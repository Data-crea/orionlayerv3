#!/usr/bin/env python3
"""The live tests of work order 175's screens — run by work order 176.

    python tools/screens175_live.py leaders 4      # load SAVE4, Leaders
    python tools/screens175_live.py races 4
    python tools/screens175_live.py info 4 [--mod DIR]
    python tools/screens175_live.py fleets 4
    python tools/screens175_live.py hire 4         # SAVE4 holding SAVE2's game
    ... [--size 2576x1432]

ONE CLIENT (the live protocol): this process IS the client (`livedrive.Run`,
the real `main.App`), and it refuses when anything else is attached. The
engine is started by `tools/engine_start.py`, which takes the liveguard
backup first; `tools/liveguard.py verify` after. Scratch slots only (4, 5).

Every step records EXPECTED and OBSERVED in `record.json` and captures the
native framebuffer and the HD window from ONE snapshot, with a side-by-side
(`leaders_live.side_by_side`); files are named `..._LIVE_...` under
`~/orionlayer-fixtures/evidence/work_order_176/<screen>/`.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FOLDER = "work_order_176"
SCRATCH = (4, 5)


def _args():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = {}
    it = iter(sys.argv[1:])
    for a in it:
        if a.startswith("--"):
            opts[a[2:]] = next(it, "")
    return args, opts


def main():
    args, opts = _args()
    if len(args) < 2 or args[0] not in ("leaders", "races", "info", "fleets",
                                        "hire"):
        print(__doc__)
        return 2
    slot = int(args[1])
    if slot not in SCRATCH:
        print(f"slot {slot} is not a scratch slot {SCRATCH}")
        return 2
    import leaders_hd
    busy = leaders_hd.other_clients()
    if busy:
        print("ANOTHER CLIENT IS ATTACHED — nothing started:", busy)
        return 3
    if opts.get("mod"):
        # A mod folder of the run's own, never the player's: usermod reads
        # $ORIONLAYER_USER_DIR/mod.
        os.environ["ORIONLAYER_USER_DIR"] = opts["mod"]
    import screens175_steps as steps
    size = tuple(int(v) for v in opts.get("size", "1920x1080").split("x"))
    return steps.PHASES[args[0]](slot, size, opts)


if __name__ == "__main__":
    sys.exit(main())
