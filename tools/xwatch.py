#!/usr/bin/env python3
"""TOOL — which X window is mapped, on top and focused, over time.

    python tools/xwatch.py OUT.jsonl [SECONDS]

Work order 180, part A1.3: is orion2re's own window ever mapped, raised or
focused in front of OrionLayer's? Both are X11 clients of Xwayland here
(SDL's x11 driver; its wayland driver does not work on this machine —
CLAUDE.md), so the X server itself is the observer:

  * root PropertyNotify for `_NET_ACTIVE_WINDOW` (focus, as mutter
    publishes it), `_NET_CLIENT_LIST` (managed = mapped top-levels) and
    `_NET_CLIENT_LIST_STACKING` (bottom-to-top order), each written out
    in full with the windows' PIDs and titles;
  * SubstructureNotify on the root: Map, Unmap and Configure of every
    top-level, so a raise shows even where the WM lists do not move.

WHAT IT CANNOT SEE, and it is written into every run's header: Wayland
native surfaces (the lock screen, a Wayland terminal) have no X window,
so "on top" means on top of the other X clients only; whether the
compositor actually PRESENTS a window (a locked or blanked screen draws
nothing) is not an X property; and focus while mutter's lock screen holds
the seat is reported as none at all.
"""
import json
import sys
import time

HEADER = ("X11 view only: Wayland-native surfaces are invisible here; "
          "'top' is among X clients; presentation on the monitor is not "
          "an X property; focus reads 0 while the lock screen holds it")


def main(out, seconds=600.0):
    # Imported here: python-xlib is a diagnostic's dependency, not the
    # product's (requirements.txt), and the suite imports every tool.
    from Xlib import X, display
    d = display.Display()
    root = d.screen().root
    atoms = {name: d.intern_atom(name) for name in (
        "_NET_ACTIVE_WINDOW", "_NET_CLIENT_LIST",
        "_NET_CLIENT_LIST_STACKING", "_NET_WM_PID", "_NET_WM_NAME",
        "UTF8_STRING")}
    root.change_attributes(event_mask=X.PropertyChangeMask
                           | X.SubstructureNotifyMask)

    def describe(wid):
        try:
            w = d.create_resource_object("window", wid)
            pid = w.get_full_property(atoms["_NET_WM_PID"], X.AnyPropertyType)
            name = w.get_full_property(atoms["_NET_WM_NAME"],
                                       atoms["UTF8_STRING"])
            return {"id": hex(wid),
                    "pid": int(pid.value[0]) if pid else None,
                    "name": (name.value.decode("utf-8", "replace")
                             if name else w.get_wm_name())}
        except Exception:                       # noqa: BLE001 — gone
            return {"id": hex(wid), "pid": None, "name": None}

    def prop(name):
        p = root.get_full_property(atoms[name], X.AnyPropertyType)
        return [int(v) for v in p.value] if p else []

    with open(out, "a", encoding="utf-8") as fh:
        def write(kind, **kw):
            fh.write(json.dumps({"t": time.time(), "kind": kind, **kw}) + "\n")
            fh.flush()
        write("header", note=HEADER)
        for name in ("_NET_ACTIVE_WINDOW", "_NET_CLIENT_LIST_STACKING"):
            write(name, windows=[describe(w) for w in prop(name) if w])
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if not d.pending_events():
                time.sleep(0.005)
                continue
            ev = d.next_event()
            if ev.type == X.PropertyNotify and ev.atom in (
                    atoms["_NET_ACTIVE_WINDOW"], atoms["_NET_CLIENT_LIST"],
                    atoms["_NET_CLIENT_LIST_STACKING"]):
                name = d.get_atom_name(ev.atom)
                write(name, windows=[describe(w) for w in prop(name) if w])
            elif ev.type in (X.MapNotify, X.UnmapNotify):
                write("map" if ev.type == X.MapNotify else "unmap",
                      window=describe(ev.window.id))
            elif ev.type == X.ConfigureNotify:
                above = ev.above_sibling.id if ev.above_sibling else 0
                write("configure", window=describe(ev.window.id),
                      above=hex(above))


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 600.0)
