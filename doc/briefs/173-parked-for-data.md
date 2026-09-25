# Work order 173 — parked for Data

Every choice this unattended run made that is Data's to confirm, with
the default taken.

---

## P1 — Where the mod folder lives

The order says "a user-writable location next to the settings file",
and also "outside the tree". `user_settings.json` is in the tree root
(git-ignored), so the two cannot both hold. **Default taken: outside
the tree**, the platform's user configuration folder —
`~/.config/orionlayer/mod`, `%APPDATA%\OrionLayer\mod`. **Alternative,
not built:** move `user_settings.json` there too (with a one-time move
of the old file), which makes both true.

## P2 — The galaxy map's floor

**Default taken:** the universal background IS the map floor.
`map_background.png` was faint gas and carried no game content; every
nebula, wormhole, star, line and fleet is drawn over the floor, so
nothing the engine draws can be hidden. The universal picture's
brighter clouds sit at the edges, mostly under the sidebar and the nav
row. Renders: `galaxy_floor_before_map_background.png`,
`galaxy_floor_after_universal.png`. **Alternative:** keep the old floor
on the map and the universal picture everywhere else — one line.

## P3 — Several mods side by side

**Default taken: one folder.** It is the simple thing the order's goal
asks for, and developers already have `mods/` with an ordered
`active_mods` list. **Alternative, not built:** `mods/<name>/` under
the user folder and a choice in the settings row.

## P4 — The Main Menu keeps its title art

**Default taken:** the Main Menu wears its own picture (169 P6); a mod's
`background.png` does not replace it unless the mod also names
`backgrounds/main_menu.png` (file for file). Render of the alternative:
`main_menu_alternative_on_universal_1920x1080_offline.png`.

## P5 — Text groups on the panel fill

**Default taken:** where words sit in an outline group over the picture
(Select Race's grid and info panel, Custom Race's three columns), the
group takes the HUD panel's fill (`"fill": true`), measured: the race
names went from 3.4 back to placeholder-level contrast at 2160p. The
picture no longer shows inside those five groups. **Alternative:** a
translucent fill, keeping some of the picture — a style value.

## P6 — The background at 2160p

1675 x 939 is a 2.3x upscale at 3840x2160. The clouds hold up; the
grain and the point stars go soft. **Suggestion only:** a 3840x2160
source, if the stars should be crisp.

## P7 — The live part

Not run: Data's engine holds the port and may not be connected to.
