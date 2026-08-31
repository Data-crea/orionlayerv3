# Modding OrionLayer

Every file OrionLayer loads — assets, data, skins, even whole
screens — resolves through `core/resources.py`. Active mods are
searched first, the base project last. Overriding anything means
shipping a file at the same relative path inside your mod.

## Quick start

```
mods/my_mod/
├── mod.json                     name, version, author
└── screens/main_menu/assets/logo.png    replaces one file
```

```json
// settings.json
{ "active_mods": ["my_mod"] }
```

Restart. That is the whole mechanism — there is no registration
step and no manifest listing your files.

Mods are searched in the order they appear in `active_mods`; the
first mod that has a file wins, and the base project is the final
fallback. Files you do not override are unaffected, so a mod that
replaces one portrait leaves the other thirteen alone.

## What you can override

### Assets (per file)

```
mods/my_mod/screens/select_race/assets/portraits/human.png
mods/my_mod/screens/galaxy_map/assets/stars/blue/3.png
mods/my_mod/assets/shared/fonts/Aldrich-Regular.ttf
mods/my_mod/assets/shared/cursor.png
```

### Banners (whole directory)

```
mods/my_mod/assets/shared/banner/             cloth/frame/gloss layers
mods/my_mod/assets/shared/banner/emblems/     one PNG per race key
```

Banners are tinted at runtime (`core/banner.py`); a mod replaces the
whole folder or nothing.

### Data (JSON, whole file)

```
mods/my_mod/screens/select_race/races.json       race descriptions,
                                                 traits, portrait crops
mods/my_mod/screens/custom_race/traits.json      trait picks/costs
mods/my_mod/screens/empire_identity/layout.json  labels, name limits,
                                                 home star defaults
mods/my_mod/screens/galaxy_map/layout.json       buttons, field IDs,
                                                 sidebar rows, labels
mods/my_mod/screens/<name>/boxes.json            layout positions
mods/my_mod/screens/<name>/help.json             right-click help
                                                 regions
mods/my_mod/assets/shared/help/labels.json       CLOSE label and the
                                                 "not extracted yet"
                                                 message
mods/my_mod/assets/shared/help/help_<lang>.json  the help texts
                                                 themselves
```

JSON overrides replace the **whole file** — there is no deep merge.
Copy the base file into your mod and edit it.

Note on `boxes.json`: the in-game F5 editor always saves to the base
project folder, never into a mod. When designing a layout for a mod,
edit with mods disabled, then copy the result into your mod folder.

### Context help

Right-click help has three overridable pieces, and they are separate
on purpose.

`screens/<name>/help.json` maps a screen region to a help id. Each
region names what it resolves against — a `box`, a list of boxes, a
`frame_button`, or a screen-specific kind — plus the original's
640x480 rectangle as `native`, which is documentation only. **Order
matters**: the list is walked top to bottom and the first hit wins,
so a `"screen": true` fallback has to be last or it swallows
everything below it.

A region may add `"pad_y": <n>` to grow its hit area by n reference
pixels above and below, without moving anything that is drawn. It is
there because MOO2's rectangles cover a whole row band while an HD
box is usually sized to its content, which leaves a strip between
two controls where a right click finds nothing — invisible, because
help regions are not drawn. Resize the region, never the box: the
box is what appears on screen.

**Every `help.json` needs a top-level `hd_extension` string, and the
smoke test refuses one without it.** The help panel grows to fit its
text and scrolls when it cannot, where the original draws a fixed box
and wraps into it at a fixed 339 px — a deliberate deviation, and the
project's rule is that a deviation is marked where it is read, not
only in the module that implements it. The string has to name the
339 px wrap, so that the note records the reason rather than merely
carrying the label. Copy the one from any shipped `help.json`. The
same key on a single region marks a deviation belonging to that
region alone; `screens/galaxy_map/help.json` has an example.

`assets/shared/help/help_<lang>.json` is the text, stored **raw**:
MOO2's bodies carry `FMTPARA` control codes and the column positions
inside them are the table layout, so the file keeps the bytes and
`core/helpformat.py` decodes them at load time. Hand-editing an entry
means keeping those codes intact. The file carries `"format": 2`; an
older one is refused rather than rendered subtly wrong. It is
generated
from the game's own `HELP.LBX` by `tools/help_extract.py` and is not
part of the project, so a mod that ships one is shipping content it
does not own — for a translation, prefer telling users to run the
tool with `--lang`. A mod may of course ship *its own* entries for a
screen it added.

`assets/shared/help/labels.json` holds OrionLayer's own words around
the text (the CLOSE label, the message shown before extraction).
That one is safe and expected to be translated.

The popup's geometry is the ordinary `help_popup` box in the
screen's `boxes.json`, with its own `font_scale`. The box bounds the
panel; the panel shrinks to its text inside it.

### Colors

Every screen palette lives in the skin's `colors.json`, grouped by
section (`galaxy_map`, `select_race`, `custom_race`,
`empire_identity`, `new_game`, `main_menu`, plus the core
`button` / `text` / `panel` / `widgets` sections). Missing keys fall
back to the defaults in code, so you only list what you change.

### Skins (whole directory)

```
mods/my_mod/assets/shared/skins/neon/
```

```json
// settings.json
{ "skin": "neon" }
```

Skins resolve as complete directories: frame tiles, inner panels,
buttons, corner glows and `colors.json` all come from the selected
skin. Copy `skins/default/` as a starting point.

### New or replaced screens

```
mods/my_mod/screens/my_screen/screen.py
mods/my_mod/screens/galaxy_map/screen.py     replaces the base screen
```

Screens are auto-discovered in `screens/` and in every active mod.
A folder with the same name as a base screen replaces it entirely.

---

## Galaxy map star sprites

This is the one asset set with a rule worth knowing before you draw
anything.

```
screens/galaxy_map/assets/stars/<class>/0.png .. 5.png
```

Classes are `blue`, `white`, `yellow`, `orange`, `red`, `brown`
(spectral classes B, F, G, K, M and Dwarf). Black holes use
`assets/black_hole.png` and their own size table — with extra rules,
see below.

**The six steps are not "large to small" in the obvious sense.**
orion2re picks a sprite with `zoom_level + star.size`, added into a
single index 0..5 — the same axis, not two. A large star viewed one
zoom step out uses the *same sprite* as a medium star viewed one
step in. Step 0 is only ever seen for a large star at maximum zoom
in; step 5 only for a small star at maximum zoom out.

Their native sizes in the original are:

| Step | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Native px | 33 | 29 | 25 | 23 | 21 | 17 |
| HD px @1440p | 122 | 107 | 93 | 85 | 78 | 63 |

Two things follow, and both go against instinct:

1. **Draw each step for its size, do not scale one drawing.** The
   original does not scale either — it swaps sprites. Reduce
   *detail* as the steps go down: fewer and thicker rays, a larger
   core relative to the canvas.
2. **Keep the class colour in the core at the small steps.** A
   white-hot centre sells a big star, but at 63 px it swallows the
   hue and every class looks alike — and colour is the only thing
   left that identifies a class at that size.

Any step you do not ship falls back to the nearest legacy artwork
(`large.png` / `medium.png` / `small.png`), so an incomplete set
still renders. That fallback is also the usual reason new artwork
seems to be ignored:

```bash
python tools/star_icon_check.py
```

prints, per class and step, which file actually resolves and whether
it came from a mod, the base project or the legacy fallback.

To generate a full set as a starting point:

```bash
python tools/make_star_icons.py --out mods/my_mod/screens/galaxy_map/assets/stars --sheet
```

---

## Galaxy map: the black hole

`assets/black_hole.png` is not a normal sprite. There is exactly one
drawing and the renderer **rotates it at runtime**, which puts four
hard requirements on the file. Break any of them and the black hole
still draws, but wrongly — and three of the four are invisible in a
still image.

1. **Square.** Anything else has to be padded to its diagonal, which
   doubles the pixels of all 72 cached frames.
2. **Content inside the inscribed circle.** The corners must be
   empty, or rotation moves artwork into them and clips it.
3. **The event horizon on the exact centre.** The black disc is what
   the eye tracks. Off centre by more than about two pixels and the
   black hole *orbits* the middle instead of turning — it looks like
   it is swimming across the map. This one only exists in motion.
4. **No RGB under transparent pixels.** Leftover colour hiding at
   alpha 0 is invisible under a normal blit and becomes a bright
   rectangle the moment anything draws additively.

Do not hand-build the file. Feed a single still into the tool, which
enforces all four and refuses to write a master that fails:

```bash
python tools/make_black_hole_master.py \
    --src my_black_hole.png \
    --out mods/my_mod/screens/galaxy_map/assets/black_hole.png
```

The source should be a black hole on a **black background**, roughly
centred, at 512 px or more. Baked-in stars are fine — the tool
removes point sources with a median filter. It reports what it found:

```
horizon offset:     (+0.3, +0.4) px from the rotation axis
horizon / sprite:   27%
faint haze:         13% of visible area
```

`--margin` controls how much empty space surrounds the disc; raise it
if the black hole reads too large in game. `OUTER_THRESHOLD` in the
tool decides where the accretion disc is considered to end — raise it
to cut away a faint outer haze, lower it to keep more.

Sizes come from `Draw_Black_Holes_`: 39, 33, 33, 24 native px by zoom
level, ignoring `star.size`, with zoom 1 and 2 deliberately equal. The
drawing has to fill its own canvas, because that table is the full
sprite width — a master with a wide empty margin silently shrinks the
black hole at every zoom level.

Rotation is one revolution per `BH_ROTATE_PERIOD_S` (40 s) in 72
steps. There is no brightness pulse and adding one would be a
deviation: MOO2 is palette-indexed and cannot alpha-blend a sprite.

Colours and the six parameter sets are tables at the top of that
script. `--sheet` writes a contact sheet at the *true* on-screen
sizes — judging step 5 at canvas resolution is misleading.

### Ship and monster icons

```
screens/galaxy_map/assets/ships/<kind>/0.png .. 3.png
```

Kinds are `player`, `antaran`, `guardian`, `amoeba`, `crystal`,
`dragon`, `eel` and `hydra`. Four steps, one per zoom level, and the
zoom level is the index — no addition trick like the stars.

**The player sprite must be greyscale.** It is tinted to the eight
MOO2 player colours at runtime, so one drawing covers all of them.
Colour baked into the file gets multiplied on top of the tint and the
result is muddy. `make_ship_icons.py` forces the player export to true
luma; if you hand-draw one, do the same.

Monsters keep their own colours and are never tinted.

Native sizes at zoom 0, and what each step shrinks to:

| Kind | Zoom 0 | Zoom 1 | Zoom 2 | Zoom 3 |
|---|---|---|---|---|
| player, antaran | 11 x 10 | 10 x 9 | 9 x 8 | 8 x 7 |
| guardian | 12 x 11 | 11 x 10 | 10 x 9 | 9 x 8 |
| crystal | 13 x 13 | 12 x 12 | 11 x 11 | 10 x 10 |
| dragon | 13 x 10 | 12 x 9 | 11 x 8 | 10 x 7 |
| hydra | 11 x 12 | 10 x 11 | 9 x 10 | 8 x 9 |
| eel, amoeba | 9 x 9 | 8 x 8 | 7 x 7 | 6 x 6 |

Nothing in the original is dramatically bigger than the player ship —
the widest is the crystal at 13. If a kind you add wants to be much
larger than that, it is a deviation, not a measurement.

The spread from step 0 to step 3 is only 23 %, so unlike the stars
these four steps do not need four separate drawings — the shipped set
is one master rendered four times. Hand-drawn steps still win, and
dropping a single `2.png` into a mod replaces just that step.

**Aspect ratio matters more than it looks.** The original sprites and
your artwork will not share proportions, and which edge you match
decides whether an icon reads as the right size. `layout.json`
`ship_icons.fit`:

- `"height"` (default) matches the original height. Height is the
  dimension that decides whether a four-deep orbit stack collides —
  the slots sit only `11 - zoom` px apart.
- `"width"` matches the width instead. If your drawing is taller than
  the original's 13 x 10, it overflows top and bottom and looks a size
  too big. That was the first default here, and it was wrong.
- `"box"` fits entirely inside, never overflows, always smallest.
- `"area"` matches the box's *area* rather than either edge. For
  artwork whose aspect is nowhere near the original's — the shipped
  eel master is 3.3:1 against a 10 x 9 box — width-fit leaves a sliver
  and height-fit a banner three times too long.

Per-kind overrides inherit anything they do not set:

```json
"ship_icons": {
  "fit": "height",
  "scale": 1.0,
  "kinds": { "eel": { "fit": "area" } }
}
```

`scale` multiplies the native footprint. Anything but `1.0` is a
deliberate departure from orion2re — use it to taste, but know that
is what you are doing.

A kind you do not ship falls back to the player sprite, so an unknown
monster stays visible and in the right place instead of disappearing.
To see exactly what resolves for every icon in a running game:

```bash
python tools/ship_icon_check.py
```

It prints the owner value per icon, which is what identifies a
monster (`9` guardian, `10` amoeba, `11` crystal, `12` dragon,
`13` eel, `14` hydra, `8` antaran), plus the sprite file actually
used and whether it is a fallback.

To generate a set from your own masters:

```bash
python tools/make_ship_icons.py \
  --src  mods/my_mod/screens/galaxy_map/assets/ships/_src \
  --out  mods/my_mod/screens/galaxy_map/assets/ships --sheet
```

### Wormhole links

Colour and opacity come from the skin, not from code:

```json
"galaxy_map": { "wormhole": [128, 150, 190, 90] }
```

The fourth component is the alpha. The original draws these links in
palette index 4 — a dark grey barely above the star field, so they
read as a hint rather than as a border across the map. Raising the
alpha much past ~120 undoes that.

The line is one pixel wide and antialiased, and the two facts are
connected: `pygame.draw.aaline` antialiases but ignores the alpha in
its colour, while `pygame.gfxdraw.line` honours alpha but draws a hard
edge. `renderer.WormholeLayer` gets both by drawing white antialiased
lines onto a transparent surface and multiplying the result by the
RGBA tint, so the coverage the antialiasing produced survives as
alpha. Widening the line would need the same trick with a polygon.

### Nebulas

```
screens/galaxy_map/assets/nebula/<form>.png
```

Shapes are listed in `layout.json` under `nebula_forms`. orion2re
knows twelve shapes; four HD ones exist so far and the list wraps.
Add more files and more names to the list together.

### Sidebar readouts

```
screens/galaxy_map/assets/icons/<name>.png
```

Five icons — `treasury`, `command`, `food`, `freighters`,
`research` — sitting beside the numbers in the right-hand column.
Which file belongs to which row is `sidebar_icons` in `layout.json`;
a row left out of that map gets no icon, which is why the stardate
has none. The artwork is freestanding with an alpha channel and is
fitted into its box aspect-correct, so any resolution works.

To re-cut them from a single painted sheet:

```bash
python tools/make_sidebar_icons.py --sheet my_sheet.png --out mods/my_mod/screens/galaxy_map/assets/icons
```

The source rects are a table at the top of that script; `--probe`
prints the alpha components of a new sheet so the table can be
updated.

**Positions are not in layout.json.** Every readout owns two boxes
in `boxes.json`, `sb_<row>_text` and `sb_<row>_icon`, both movable
in the F5 editor. A text box's style may carry `"align"` with
`left`, `center` (default) or `right`, and `font_scale` as usual.
Reference font sizes for label, value and sub are `sidebar_fonts`
in `layout.json`.

### The frame is the layout — for the boxes it cuts

The galaxy map's `map_area`, `sidebar` and seven `nav_*` boxes are
**derived from the transparent cutouts** in `assets/frame.png`, not
positioned by hand. If you ship your own frame, regenerate them:

```bash
python tools/frame_holes.py mods/my_mod/screens/galaxy_map/assets/frame.png --write
```

Moving one of those by hand would slide the content out from under
its hole in the frame, and the smoke test asserts the two agree.

Boxes that live *inside* a cutout are a different matter: the
`sb_*` sidebar boxes have no hole of their own and are placed by
hand. `frame_holes.py --write` keeps every box it did not derive
and reports how many it kept.

---

## Writing a screen

Start from `screens/_template/`. Key class attributes:

| Attribute | Meaning |
|---|---|
| `SCREEN_NAME` | Must match the folder name |
| `GAME_SCREEN_ID` | orion2re screen ID for auto-switching; `None` for sub-screens |
| `IS_OVERLAY` / `OVERLAY_DIM` | Render above the active screen (popups) |
| `USE_FRAME` / `FRAME_TITLE` / `FRAME_VARIANT` | Cockpit frame overlay |
| `FRAME_BTN_LEFT` / `FRAME_BTN_RIGHT` | `("Label", field_id)` button bars |

Rules that keep a screen consistent with the rest:

- **All file access through `self.asset_path()` / `res.load_json()`.**
  A hardcoded `os.path.join` for loadable content bypasses the mod
  system, which is exactly what the mod system is.
- **Share geometry between rendering and hit-testing.** Have one
  layout function return the rects both paths use, so click targets
  cannot drift from what is drawn.
- **Put content in JSON, not in the renderer.** Labels, values and
  texts belong in `layout.json`; the renderer only lays them out.
  This is also what makes translation possible.
- **Use `ACTIVATE_FIELD` where a field ID exists.** `INJECT_CLICK`
  is for radio buttons (type 1) and free map clicks, and it is
  currently only reliable at a 640x480 window (a known orion2re
  bug maps injected coordinates as window coordinates).
- **Take sizes from `core/zoomtables.py`** rather than tuning them.

## Gotchas

- Changing skin or mods requires a restart (palettes resolve at
  import time).
- The F5 editor saves to the base project, never into a mod.
- JSON overrides are whole-file; there is no merging.
- Always use `style.render_text(text, size, colour)` rather than
  `style.get_font(size).render(...)`. It detects which glyphs a font
  maps onto one shared bitmap and falls back to the proportional font
  for exactly those, aligned on the baseline. The shipped font
  (Aldrich, OFL) substitutes nothing, so detection finds nothing and
  the call costs what a plain render costs — but a mod may ship a
  demo font, and this is what keeps it readable. Until 31 August the
  project shipped a DEMO Bank Gothic that substituted 28 characters,
  **including the digit 4**, which hid inside every number.
- **A font you ship in a mod needs its licence next to it.** The
  smoke test enforces that for the base project.
- After any change: `python tools/smoke_test.py`.
- Some assets are **not in the repository** — the ship steps, the cut
  sidebar icons and the black hole master are generated, and the help
  texts and nebula sprites come from your own MOO2 files. If a file
  you want to override is missing after a clone, run
  `python tools/setup.py` first. `.gitignore` lists which and why.
- A mod overriding a generated asset works normally: resolution goes
  through `core/resources.py` either way, and the mod's copy wins
  before the generated one is ever consulted.
