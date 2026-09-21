# Work Order 161 — The galaxy map reloads 81 sprites on every return

First line for references: "Work Order 161 — The galaxy map reloads 81 sprites on every return"

Filed as 161: the highest number in `doc/briefs/` was 160 when this was
filed.

## Why

Data, 21 September 2026: *"das overlay lädt den screen beinahe gleich
schnell wie das original aber bei return ist es definitiv langsamer"* —
over all three screens reached from the galaxy map (Colonies, Planets,
Fleets).

**Measured, and it is ours, not the engine's.**

1. **On the wire the return is not slower.** A passive log of the
   running game (screen id from `MSG_STATE`, lists from `MSG_FIELDS`)
   over six transitions: the new field list arrives **0.06–0.17 s**
   after the screen id changes, in **both** directions. At the
   measured ~18 snapshots/s that is about two snapshots.
2. **`enter()` is where the asymmetry is**, at 1920x1080:
   `galaxy_map` **439 / 433 / 429 ms** every time, against `fleets`
   84 ms, `planets` 31 ms, `colony_summary` 27 ms. **Every RETURN goes
   to the galaxy map**, which is why all three screens feel the same.
3. **409 of those 432 ms are 81 `pygame.image.load` calls** in
   `_load_sprites()` (`screens/galaxy_map/screen.py`), which `enter()`
   calls unconditionally.
4. **The surfaces are already in memory.** `SpriteCache` is built once
   in `__init__`; resize calls only `clear_scaled()`, and nothing calls
   `SpriteCache.clear()` at all. The reload replaces each surface with
   an identical one.
5. **Skipping it: 426.7 ms → 44.2 ms (−383 ms, 90 %), rendered frame
   byte-identical** (sha256 `323ce3328de9bc67` both ways).

## What this order does

Load the sprites **once per screen object**, and reload only when
something that changes which FILE a name resolves to has changed.

**The guard is not "load once" — that would be wrong.** `asset_path`
goes through `res.screen_file`, so the resolved file depends on the
**skin** and the **active mods**; and `nebula_forms` and
`sidebar_icons` come from `layout.json`, which `enter()` re-reads and a
mod can replace. The key is those four things together. A guard keyed
on anything less would pin the map to artwork from a skin that is no
longer active — which is the fault this project calls a second copy
nobody updates, in a new place.

## Hard constraints

- **No behaviour change.** Prove it: the galaxy map renders
  byte-identically before and after, at 1920x1080, 2560x1440,
  3440x1440 and 3840x2160.
- The check asserts the **rule**, not the instance: a second `enter()`
  loads nothing, and a changed key loads again.
- Markers move with their code.
- One commit, through the fast tier. No push unless Data asks.

## Acceptance

- Second entry to the galaxy map performs **zero** image loads.
- A changed skin / mod / `nebula_forms` / `sidebar_icons` **does**
  reload.
- Renders byte-identical at four resolutions.
- Before/after timing recorded in `doc/briefs/161-progress.md` and in
  the status document.
