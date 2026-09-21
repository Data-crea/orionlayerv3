# Work order 161 — progress

21 September 2026. One commit, fast tier. No push.

## What Data reported

*"das overlay lädt den screen beinahe gleich schnell wie das original
aber bei return ist es definitiv langsamer"* — over Colonies, Planets
and Fleets alike.

## What it turned out to be

**Not the engine.** A passive log of the running game over six
transitions: the new field list arrives **0.06–0.17 s** after the
screen id changes, **in both directions**.

| | entry | RETURN |
|---|---|---|
| Colonies (20) | 0.165 / 0.165 s | 0.123 / 0.128 s |
| Planets (32) | 0.066 / 0.060 s | 0.068 / 0.068 s |
| Fleets (4) | 0.121 / 0.127 s | 0.118 / 0.126 s |

At the measured ~18 snapshots/s that is about two snapshots either
way. **The asymmetry is in our own `enter()`**, at 1920x1080:

| screen | `enter()` |
|---|---:|
| **galaxy_map** | **439 / 433 / 429 ms**, every time |
| fleets | 84 ms |
| planets | 31 ms |
| colony_summary | 27 ms |

**Every RETURN goes to the galaxy map**, which is why all three felt
the same. 409 of those 432 ms were **81 `pygame.image.load` calls** in
`_load_sprites()`, which `enter()` ran unconditionally — although
`SpriteCache` is built once in `__init__`, resize clears only
`clear_scaled()`, and **nothing in the tree calls
`SpriteCache.clear()`**. Each reload replaced a surface with an
identical one.

## The fix

`_load_sprites` now loads once per screen object and reloads on
`_sprite_key`: **the skin, the active mods, `nebula_forms` and
`sidebar_icons`**. Not a boolean — `asset_path` resolves through
`res.screen_file`, so which file a name reaches depends on the skin
and the mods, and the last two come from `layout.json`, which a mod
can replace. A plain "load once" would have pinned the map to artwork
from a skin that is no longer active.

`force=True` reloads regardless and has exactly one caller: the nebula
check, which puts a flat test surface over the real artwork and has to
put it back.

## Measured after, four resolutions

| | 1st entry | loads | re-entry | loads | render |
|---|---:|---:|---:|---:|---|
| 1920x1080 | 436.5 ms | 81 | **45.3 ms** | **3** | identical |
| 2560x1440 | 436.0 ms | 81 | **49.8 ms** | **3** | identical |
| 3440x1440 | 437.5 ms | 81 | **53.4 ms** | **3** | identical |
| 3840x2160 | 448.7 ms | 81 | **63.0 ms** | **3** | identical |

**About 385 ms off every return, 90 %.** The three remaining loads are
the frame, the background and the map background, which are a separate
question and untouched. The rendered frame is **byte-identical to the
pre-fix run at all four resolutions** — sha256 `323ce3328de9bc67`,
`5f3390e94cb7208e`, `d0698eb70dc38b21`, `54ec82f55a3cb0b9`.

## The mistake this run made, and what caught it

The first version of the guard stored the wrong value: the sidebar loop
below it binds `key`, so `self._sprite_key_loaded = key` saved the last
icon name (`"research"`) instead of the tuple. **It never matched, so
nothing reloaded less and nothing looked broken** — the renders were
identical and the timings unchanged. Only the load counter showed it:
still 81 reads on re-entry.

That is why the smoke check counts loads rather than timing the entry:
a guard that silently fails to guard produces a correct picture and no
saving, and a timing assertion would be machine-dependent.

## What is NOT claimed

Data reports 1–2 s. This accounts for **~0.43 s** of it (our side) on
top of ~0.12 s on the wire. The rest is presumably the engine's own
redraw — `Build_Ship_Icons_`, and on one branch `Fast_Fade_Out_` before
`Add_Map_Fields_` — which was read but **not measured**. The very first
entry after a cold start, where the 5.1 MB Fleets frame is not yet in
the page cache, was also not measured.


## Confirmed in play

Every number above is headless. Data ran the built tree on 21 September
2026 and reported the return as **"viel besser"** — which is the half
`colony_list_preview.build_screen` cannot answer, and the reason this
line exists separately from the measurements.

**So the remainder is an open question, not a queued task.** The
complaint that started this order is gone; whether the engine's own
redraw is still worth measuring is Data's call, not a foregone next
step.
