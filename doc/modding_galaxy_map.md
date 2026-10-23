# Modding the galaxy map's pictures

This is the second half of the mod guide, [MODDING.md](../MODDING.md): the
galaxy map's star sprites, the black hole, the ship and monster icons,
wormhole links, nebulas and the sidebar. Everything else (the mod folder,
what you can override, writing a screen, gotchas) is in the first half.

## Galaxy map star sprites

This is the one asset set with a rule worth knowing before you draw
anything.

```
screens/galaxy_map/assets/stars/<class>/0.png .. 5.png
```

Classes are `blue`, `white`, `yellow`, `orange`, `red`, `brown`
(spectral classes B, F, G, K, M and Dwarf). Black holes use
`screens/galaxy_map/assets/black_hole.png` and their own size table — with extra rules,
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

`screens/galaxy_map/assets/black_hole.png` is not a normal sprite. There is exactly one
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
is one master rendered four times. The masters are hand-drawn HD
pictures and come with the base pack
(`screens/galaxy_map/assets/ships/_src/<kind>.png`, 1536 x 1024).

**Your mod folder replaces them two ways:**

```
files/screens/galaxy_map/assets/ships/<kind>/2.png      ONE icon
files/screens/galaxy_map/assets/ships/_src/<kind>.png   a WHOLE master
```

- **One icon** replaces exactly that icon — one step, or a monster's
  `panel.png` (its picture in the Planets panel). Another size is scaled
  to the built-in one.
- **A whole master** replaces every icon cut from it: OrionLayer cuts it
  at the next start by the shipped icons' own rule (`core/shipcut.py`:
  the four steps and, for a monster, `panel.png`) and keeps the cut in
  the folder's `cache/`. A kind with no shipped master (`amoeba`,
  `antaran`) gets one this way.
- **Both at once:** the single icon wins for its own file, the master's
  cut fills the rest. A master under a name that is not a kind is skipped
  with one line in the log.

**A stack shows its strongest ship** (setting *Map ship pictures*, on by
default): your own stack the Avenger first, then the largest hull, then
the dearest design; another empire's the ship the game puts at its head.
It is the battle's picture, facing right, fitted into the icon's box.
The map's own slot comes first, by the ship's picture number (45 colony
ship, 46 outpost ship, 47 transport, which have no battle picture; 0-44
a warship's):

```
files/screens/galaxy_map/assets/ship_pictures/all_<picture>.png
files/screens/galaxy_map/assets/ship_pictures/<colour>_<picture>.png
```

`all_47.png` is the transport for every player: paint the hull neutral
grey, as for the battle's `all_` pictures, and it takes the owner's
colour. `<colour>_47.png` (colour 0-7) is one colour's, drawn as
painted. Facing right, any size; only the visible pixels count. Without
a file a stack with no warship keeps the tinted icon. Restart after
adding one. The same files paint these three ships in the lists too:
the Fleets grid and its bottom panel, the Leaders ship view and the
Ship Designer (never enlarged, aspect kept). The colony screen's
build box and the build queue's picture box paint them too, the file of
your colour (a queued ship: its builder's), fitted into the place
where the game's own picture stood; without a file they draw the game's
own picture. The freighters (48) and the warship designs keep it.

Which file wins: the builder's `<colour>_<picture>.png` before
`all_<picture>.png` (a captured ship keeps its builder's shape and never
takes its owner's own file), each looked up in your folder, then the
base pack (so the pack's `3_47.png` beats your `all_47.png`); then the battle's painted picture, coloured on the map at
full strength, whatever the livery's strength. Another name is reported
in the log and skipped.

**Aspect ratio matters more than it looks.** The original sprites and
your artwork will not share proportions, and which edge you match
decides whether an icon reads as the right size. `layout.json`
`ship_icons.fit`:

- `"height"` (default) matches the original height. Height is the
  dimension that decides whether a four-deep orbit stack collides —
  the slots sit only `11 - zoom` px apart.
- `"width"` matches the width instead. If your drawing is taller than
  the original's 13 x 10, it overflows top and bottom and looks a size
  too big.
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

To see a set cut from your own masters before you start the game (the
same cut, written to a folder you name, with a contact sheet):

```bash
python tools/make_ship_icons.py \
  --src  <folder with your masters> \
  --out  <a scratch folder> --sheet
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

The readouts' icons are the HUD's own glyphs (`assets/shared/hud/`); there
is no separate picture per readout.

**Positions are not in layout.json.** Every readout owns two boxes
in `boxes.json`, `sb_<row>_text` and `sb_<row>_icon`, both movable
in the F3 editor. A text box's style may carry `"align"` with
`left`, `center` (default) or `right`, and `font_scale` as usual.
Reference font sizes for label, value and sub are `sidebar_fonts`
in `layout.json`.

### The HUD is the layout — for the galaxy map's boxes

The galaxy map's `map_area`, info panel rows, nav buttons and TURN
boxes are **derived from the HUD's measured layout**, not positioned
by hand. Moving one of them by hand slides it off its place in the HUD
artwork.

Boxes the HUD does not own — the help popup, the system window, the
fleet box, the `sb_*` sidebar text boxes — are placed by hand and kept
as they are when the derived ones are rewritten.
