#!/usr/bin/env python3
"""The Leaders screen, live: the acceptance of work order 167.

    python tools/leaders_hd.py probe            # read only: the struct, live
    python tools/leaders_hd.py run 5            # load SAVE5, look, leave

ONE CLIENT ONLY (CLAUDE.md, the live protocol). This tool IS that client
— `tools/livedrive.Run` builds the real `main.App` — so it refuses to
start while anything else holds port 17362: two clients reading the
same game see different field lists at different moments, and a send
decided from one of them is decision 20's failure one level out.

WHAT `probe` MEASURES, and it sends nothing: the leader records off the
wire through `tools/leader_check.measure` — the live half of the
struct's second source (`core/structs/leader.py`) — beside the
fingerprint of whatever game is loaded.

WHAT `run` DOES, each step decided from the list read AT THAT MOMENT:

  1. hashes SAVE1-11 and names the loaded game;
  2. loads the scratch slot (`tools/gameload.py`, never SAVE8, SAVE4 or
     SAVE5 only), which is the only thing it writes into the game;
  3. opens the Leaders screen through the HD map's own LEADERS button,
     and records EVERY rendered frame of the entry: the game's screen,
     the HD state, and whether the window showed the game's picture —
     the no-glimpse measurement of work order 166 A, for this screen;
  4. holds the LIVE field list against `Add_Officer_Screen_Fields_` as
     transcribed (the smoke group's builder) — the geometry's second
     source;
  5. captures native and HD from ONE snapshot, and a side-by-side, for
     each view it can reach (both tabs), hire mode if the view offers
     HIRE, and HD's skill help box;
  6. RETURN; hashes again. Nothing is hired, pooled, dismissed or
     assigned — those change the game, and the order keeps them to
     scratch slots AND to a state that offers them (item L of the
     parked file names the state).

Evidence goes to `~/orionlayer-fixtures/evidence/work_order_167/`.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCRATCH = (4, 5)
FOLDER = "work_order_167"
PORT = 17362


def other_clients():
    """Established connections to the engine's port, as `ss` lists them.

    The engine's own side of each connection is listed too, so a count
    of two lines is ONE client. A tool that cannot run `ss` says so and
    refuses rather than guessing the port is free.
    """
    try:
        out = subprocess.run(["ss", "-tanp"], capture_output=True,
                             text=True, timeout=10).stdout
    except OSError as exc:
        raise SystemExit(f"`ss` could not be run ({exc}) — cannot tell "
                         f"whether another client holds the engine")
    return [line for line in out.splitlines()
            if "ESTAB" in line and f":{PORT}" in line
            and "orion2re" not in line]


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("probe", "run"):
        print(__doc__)
        return 2
    busy = other_clients()
    if busy:
        print("ANOTHER CLIENT IS ATTACHED to the engine — the live "
              "protocol allows one; nothing was started:")
        for line in busy:
            print("   ", " ".join(line.split()))
        return 3
    import leaders_live
    if args[0] == "probe":
        return leaders_live.probe(FOLDER)
    slot = int(args[1]) if len(args) > 1 else SCRATCH[1]
    if slot not in SCRATCH:
        print(f"slot {slot} is not a scratch slot {SCRATCH} — nothing "
              f"loaded")
        return 2
    started = time.monotonic()
    rc = leaders_live.acceptance(FOLDER, slot)
    print(f"  {time.monotonic() - started:.0f} s")
    return rc


if __name__ == "__main__":
    sys.exit(main())
