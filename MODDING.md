# Modding OrionLayer

## The easy way: your mod folder (no programming)

To change how OrionLayer
looks you do not need this repository at all. There is one folder for
you, outside it:

| system | folder |
|---|---|
| Linux | `~/.config/orionlayer/mod` (or `$XDG_CONFIG_HOME/orionlayer/mod`) |
| Windows | `%APPDATA%\OrionLayer\mod` |
| macOS | `~/Library/Application Support/OrionLayer/mod` |

```bash
python tools/mod_template.py
```

makes it for you, with a plain-language `MODDING.md` inside, a
`NAMES.txt` of every name it can hold (with sizes), and OrionLayer's own
files under `originals/` as starting points. Put a file in the folder
under the right name, restart, and it is used instead of the built-in
one; take it out and the original is back:

```
background.png             the picture behind every screen
backgrounds/<screen>.png   one screen's picture (wins over background.png)
hud/<piece>.png            a HUD icon or the title plate
frames/<screen>.png        a frame painted over one screen (see Frames)
style.json                 HUD colours and sizes — only the keys you write
colour.json                the frame colour OrionLayer starts with
files/<path in the tree>   any other picture listed in NAMES.txt
texts/<screen>/<key>.txt   a text, by its key
```

OrionLayer's own pictures are not in this repository either: they come
as the **base pack** (`basepack.json` names every file), which
`tools/setup.py` downloads and installs into its own folder
(`~/.local/share/orionlayer/base` on Linux; `python tools/basepack.py
install <zip>` installs a zip you have).
`files/<path in the tree>` replaces a base-pack picture by that same
path. Never edit the base pack itself; your mod folder is the place.

A file OrionLayer cannot read, or a name it does not know, is skipped
with one line in the log; a picture of another size is scaled to fit.
The GAME menu's SETTINGS has **Mod folder: Off / On** (takes effect at
the next start). **It is Off until you switch it on** (a folder you
switched on before stays on). Switching it on extracts the
game's pictures you have not extracted yet — the row says this can take
a while and shows how far it is — then writes the template and the frame
templates into the folder (`core/modsetup.py`). Switching it off leaves
your files where they are. The same SYSTEM tab of the OrionLayer settings
window has **Open mod folder**: it opens the folder in your file manager,
creating it if it is not there yet, whether the switch is on or off; where
no file manager answers, the window shows the folder's path instead.

### Frames

`frames/<screen>.png` is a picture laid over one whole screen: 3840 x 2160
with transparency, so the screen shows through where you leave it clear.
`python tools/frame_template.py` writes `templates/frames/<screen>.png`
into the folder (switching the folder on does it too): every box the
screen places, outlined and named, at exactly the size it is drawn — paint
over it and save the result under `frames/`. The template carries a hidden
stamp of the screen's layout; a frame is drawn only

- while the window is 16:9 (a painted picture scales evenly only there;
  the boxes move differently at other shapes), and
- while the screen's layout is the one the stamp names — move a box and
  the frame waits for a repaint instead of sitting crooked.

Each refusal is one line in the log. A paint program that drops the stamp
can be answered with a `mod.json` in the folder:
`{"frames": {"galaxy_map": "<stamp>"}}` — the tool prints every stamp.
Screens whose geometry is code (the battle) have no frame slot.

### Leader portraits in HD

Painted, cut-out portraits (PNG with transparency) for the leaders are an
optional download of their own, [`orionlayer-leader-portraits.zip`](https://github.com/Data-crea/orionlayerv3/releases/tag/leader-portraits-8218a046e53e) — not
part of the base pack: they are redrawings of the game's portraits, and
the base pack's licence cannot cover them. Unpack it into your mod folder;
the pictures land in `files/screens/leaders/assets/portraits/`
(`colony_leaders/`, `ship_officers/`, named `<nn>_<name>.png` by the
leader's number in the game). A leader without one, and every leader
while the mod folder is off, shows the game's own portrait. To replace a
portrait, or to give a leader one, put a PNG with transparency in your mod
folder under
`files/screens/leaders/assets/portraits/<colony_leaders|ship_officers>/`
named `<nn>_<anything>.png` — the number decides, the name after it is
yours. The largest place a portrait is drawn at 3840 x 2160 is 438 x 528
(the turn's leader offer); every place scales down from it.

The leaders' skill icons are the game's own 16 x 16 pictures. A redrawn
icon goes under `files/screens/leaders/assets/gamedata/officer/` as
`skill_<k>_0.png` (`<k>` = the skill's number / 2; one icon serves a
skill and its starred variant); it is drawn as painted, fitted into the
icon's square — at 3840 x 2160 64 x 64 in the hire offer, 61 x 61 on a
slot (49 x 49 with five skills); a square picture of 64 x 64 serves all.

### The Leaders screen's pictures

The Leaders screen has eight picture places, filled only from your mod
folder (OrionLayer ships none of them), each under
`files/screens/leaders/assets/pictures/`:

| file | where | size at 3840 x 2160 |
|---|---|---|
| `screen_background.png` | the screen's own background, the whole window | 3840 x 2160 |
| `slot_1_background.png` … `slot_4_background.png` | row 1 to 4 while a leader stands in it (both tabs) | 2158 x 413 |
| `slot_empty_background.png` | a row with no leader; OrionLayer writes the caption | 2158 x 413 |
| `minimap_background.png` | the galaxy box, under the stars and fleets | 1444 x 700 |
| `view_background.png` | the box above it in the colony view: a star in space; OrionLayer draws the system's orbits and planets over it, centred on the brightest warm disc it finds (the star), and keeps the ship view as it was | 1498 x 784 |

Paint them without a frame: OrionLayer draws the frame round each box in
your frame colour and clips the picture to it. Any size of roughly that
shape works — the picture is scaled to fill the box, never stretched,
and the overflow is cut evenly (the empty row's on the right, so its left
side stays). Where a word stands on a row's picture, the parts brighter
than the word needs are darkened behind it; the galaxy box's picture is
kept no brighter than the plain box, so every star stays as visible as
without it. A picture that is missing or cannot be read leaves its box as
it is without one; with the Mod folder Off the screen is as before.
`NAMES.txt` lists the names.

### The battle's pictures

The battle draws the game's own pictures from the files
`tools/combat_art_extract.py` extracts. One PNG replaces one stored
drawing, used as painted (no palette), at
`files/screens/combat/assets/gamedata/<file>/<entry>_<frame>.png`; the
facings the game draws as flips stay flips, so a ship needs its five
stored facings, not sixteen. `NAMES.txt` gives the numbering.

Paint at the stored drawing's size or at a whole multiple of it: a Doom Star is 59 x 60, so 118 x 120, 236 x 240 and so on.
OrionLayer draws the picture at the drawing's size and place and keeps
its detail as the camera zooms in; any other size is refused (the log
says so) and the game's drawing is used. A ship's frames are
`<entry>_0.png` to `<entry>_19.png`: the five stored facings (0 points
right, each next one 22.5 degrees counter-clockwise, 4 points up), four
engine-glow frames each. Its entry is `colour * 45 + picture`, so a
picture replaces one player colour's ship, drawn as painted. The game
itself draws each colour's ships as their own pictures (the red Doom Star
is a different drawing from the yellow one).

**Paint once, at the largest size you want to offer.**
The player chooses in Game Settings how finely the battle holds painted
pictures: Normal keeps them at 4 times the drawing at most, High at 8
times, Auto picks by the window (Normal up to 2560 pixels wide, High
above). The game shrinks a larger picture itself, once, when the battle
loads it, and never enlarges a smaller one — so put one file per name in
the folder, the largest you have (8 times for a sharp High: a Doom Star at
472 x 480), and both settings use it. There are no separate sets for 4x
and 8x.

**One picture for every player.** Save a ship as
`files/screens/combat/assets/gamedata/cmbtshp/all_<picture>_<frame>.png`
— `all_43_0.png` is the Doom Star — and it is drawn for every owner who
has no file of their own, in that owner's colour:

- **Paint the hull in neutral grey.** Grey is what takes the player's
  colour: any shade, dark to light, its light and shade kept. The colour
  is laid on at 70 % and fades out on the brightest and the darkest grey,
  so lit edges stay metal and panel lines stay dark: the
  ship reads as its owner's at battle size and as metal up close. "Neutral"
  means the red, green and blue of a pixel lie within about 13 of each
  other (on 0-255); a grey that leans a little blue still counts.
- **Paint in colour what should stay.** Engines, lights, copper trim,
  windows: anything clearly coloured (red, green and blue more than about
  25 apart) is drawn exactly as you painted it, for every player. White
  highlights stay white.
- **One file is enough:** `all_<picture>_0.png`, facing right, at twice
  the stored drawing's size or more (a Doom Star at 118 x 120 or
  236 x 240). The game turns it into the other facings and makes the
  engine-glow frames from it (below: an engine mask makes the engines
  pulse).
- **Every further file you paint is used:** `all_<picture>_4.png`,
  `_8.png`, `_12.png`, `_16.png` are your own drawings of the facings
  22.5, 45, 67.5 and 90 degrees round (counter-clockwise; 16 points up) —
  the game turns only what you leave out; `_1` to `_3` (and `_5` to `_7`
  and so on) are your own engine-glow frames and win over the ones the
  game makes.
- **Keep the ship inside the circle** the picture's square holds if you
  give only one facing: a turned picture stays on its canvas, and what
  sticks out past the circle is cut at the diagonals.
- A file under one colour's own name (`178_0.png`, silver's Doom Star)
  still wins for that colour, drawn exactly as painted.

**A livery: masks beside the ship.** A ship may say which
of its plates take the owner's colour; the player then chooses a pattern,
a tone of their colour, a second colour of their own and the strength in
GAME -> Settings -> Livery (the button shows once your folder holds a ship
with masks). Put the masks beside the ship's file, one pair per pattern:

```
cmbtshp/all_<picture>_<frame>.png                    the ship
cmbtshp/all_<picture>_<frame>_<pattern>_mask.png     first zone
cmbtshp/all_<picture>_<frame>_<pattern>_mask2.png    second zone
<pattern>: light, stripes, outer, mixed
```

- **A mask is a greyscale PNG of exactly the ship's size**: white = this
  plate takes the colour, black = it stays as painted, grey in between
  for soft edges. Another size is not used (one line in the log).
- **The first zone** takes the owner's colour at full strength, in the
  tone the player chose (Strong, Light, Muted), keeping the plate's light
  and shade; bright glints fade back to metal. It applies to every fleet.
- **The second zone** is the player's own mark: it takes the second
  colour the player picked — only on the player's own fleet, never on the
  others — laid on the same way. Make it a different set of plates than
  the first zone (they should not overlap; about an eighth of the ship
  works well). A pattern without a `_mask2` file simply has no second
  colour on that ship.
- Only neutral grey takes a colour under a mask, as above; engines,
  copper, lights stay as painted whatever the mask says.
- **No masks needed.** A ship without masks for the chosen pattern is
  drawn as Full: all its grey at the lighter strength described above.
  You may give some patterns and not others.
- The masks follow the ship through everything: the Painted detail
  setting shrinks them with the picture, and turned, mirrored and flipped
  facings, shield flares and the cloak take them along.

**Pulsing engines: an engine mask beside the ship.**
In the original a ship's engines pulse in battle: low, middle, high,
middle, one step every 55 ms, and they go dark when the ship is done for
the turn, captured, hit on its shield, cloaking, teleporting or blowing
up. A painted ship gets all of it from one more file, so you never paint
the glow frames yourself:

```
cmbtshp/all_<picture>_<frame>_engine.png    the engine mask
cmbtshp/<colour * 45 + picture>_<frame>_engine.png   for a colour's own file
```

- **A greyscale PNG of exactly the ship's size**, like a livery mask:
  white = an engine, black = not an engine (never changes), grey in
  between for a soft edge round the flame. A hole the white closes round
  (a white-hot core inside a purple ring) counts as engine too. Another
  size is not used (one line in the log).
- **Paint the engines lit, at their lowest light**: your picture is the
  bottom of the pulse. Towards the top the game lifts the light under the
  mask and lets a soft glow grow out of the ship's back, about one pixel
  of the original's drawing, in your engine's own colour — as strong as
  the original's pulse, measured against its drawings. For the engines
  off it takes the light under the mask down to a third and its colour
  to grey.
- The owner's colour and the livery never touch what the mask covers, nor
  the glow.
- **Your own engines-off frame**: paint frame 1 as well
  (`all_<picture>_1.png`, engines lit) and your frame 0 is drawn as you
  painted it wherever the engines are off — the original's own
  convention, frame 0 off and frame 1 lit; the pulse is then made from
  your frame 1. With frame 0 alone, frame 0 is the lit picture and the
  game makes the dark one.
- **Without a mask the ship stands still**, as before: every glow frame is
  your frame 0, also when its engines would be dark. A glow frame you
  paint yourself (`_2`, `_3`) wins for that frame.
- The mask follows the ship through the Painted detail setting, turned,
  mirrored and flipped facings and the cloak (a cloaked ship's glow fades
  with it).

### The other extracted pictures

Fleets, Leaders, Races, the Ship Designer, the diplomacy audience and the
Info screen's Tech Review draw the game's pictures the same way, from the
files their extractors write into `screens/<screen>/assets/gamedata/`. A
PNG at `files/screens/<screen>/assets/gamedata/<group>/<entry>_<frame>.png`
replaces the drawing stored as `<group>/<entry>.bin` (frame 0 for a still
picture; the Races screen and the Tech Review keep their drawings without
a group folder, `…/gamedata/portrait_3_0.png`,
`files/screens/info/assets/gamedata/app_<application>_0.png`), used as painted — no palette and no ship colours, so a ship you
paint shows in your colours for every owner. The Ship Designer draws the
Fleets screen's ships, so one PNG serves both.

Pictures from Master of Orion 2 itself are never copied into the
template — they are not ours to hand out — but their names are listed,
so you can draw your own.

### The colony screen's surface

The colony screen's landscape fills a panel much flatter than the game's
own 640 x 328 picture, which is therefore cut to cover it. A picture made
in the panel's format replaces it, one PNG per climate:

```
files/screens/colony/assets/surfaces/<climate>.png
files/screens/colony/assets/surfaces/<climate>_<ground>.png   (optional)
```

`<climate>` is one of `toxic radiated barren desert tundra ocean swamp
arid terran gaia`. The game has three grounds per climate (0, 1, 2, the
planet's own); a `<climate>_<ground>.png` wins over `<climate>.png` for
its ground, so one picture per climate or three both work. The size is
the panel less its inset — `NAMES.txt` gives it at 1920 x 1080 and at
3840 x 2160 (the same shape at every 16:9 window, and at wider ones; a
window taller than 16:9 shows the panel taller and cuts the picture's
sides). The picture is never stretched: at another shape it is cut to
cover the panel. A climate without a picture shows the game's.

### Texts

Every text of the **Info** screen is looked up by a stable key, and a text
file in your folder replaces it. The file name IS the key: the part before
the first dot is the folder, the rest the name —

```
info.tab.reference        ->  texts/info/tab.reference.txt
info.reference.213.body   ->  texts/info/reference.213.body.txt
```

The file is plain text, saved as UTF-8 (any editor's default); a blank line
starts a new paragraph. A long text wraps, and scrolls if it does not fit —
nothing is ever cut off. A file OrionLayer cannot read (not UTF-8, empty,
over 64 KB) costs one line in the log and the built-in text stays. Delete
the file and the built-in text is back.

The template writes OrionLayer's OWN texts into `originals/texts/` as
starting points. The game's texts (the reference articles, the page
titles, the trait names …) are the game owners' words: `NAMES.txt` lists
their keys only, and OrionLayer reads them from your own game files.

### Texts per language

OrionLayer speaks English or German (Game Settings, LANGUAGE; read at the
next start). For a key, a German file goes one folder deeper, under the
language's code:

```
info.tab.reference  ->  texts/de/info/tab.reference.txt   (German)
                    ->  texts/info/tab.reference.txt      (English, and any
                                                           language without
                                                           its own file)
```

OrionLayer's OWN words in German — every button, heading and notice it
writes itself — are one table, `assets/shared/lang/de.json` (`"words"`:
the English text, then the German). Put your own copy at
`files/assets/shared/lang/de.json` in your folder and it replaces the
built-in table; keep the English side exactly as OrionLayer shows it, and
keep the placeholders (`{n}`, `%d`) on the German side. The game's own
words are not in this table: they come from your German game files where
your installation has them, and stay English where it has none.

Everything below is the **developer's** route: mods inside the tree,
which can also replace data, layouts and whole screens.

## Mods inside the tree

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

### Population figures (per file, master or step)

```
mods/my_mod/assets/shared/figures/human_farmer.png       28 x 28
mods/my_mod/assets/shared/figures/human_farmer@3x.png    84 x 84
```

One PNG, one documented name, one documented folder, restart. Each
figure and each step resolves on its own, so a mod that supplies one
file changes one figure. A file of the wrong size is refused with a
line in the log and the original is drawn.

**The 54 names, the sizes and the resolution order are in
`doc/modding_figures.md`**, which is generated from the loader's own
table — copy the names from there rather than typing them, because a
file whose name nothing looks for fails silently.

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

Note on `boxes.json`: the in-game F3 editor always saves to the base
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

**Every shipped `help.json` carries a top-level `hd_extension`
string; keep it when you copy one.** The help panel grows to fit its
text and scrolls when it cannot, where the original draws a fixed box
and wraps into it at a fixed 339 px — a deliberate difference, and the
string records it where the file is read, naming the 339 px wrap. The
same key on a single region marks a difference belonging to that
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

Skins resolve as complete directories: the frame's `9slice.json`
(where the pre-game screens' two frame buttons sit) and `colors.json`
come from the selected skin. Copy `skins/default/` as
a starting point.

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
adding one.

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

---

## Writing a screen

Start from `screens/_template/`. Key class attributes:

| Attribute | Meaning |
|---|---|
| `SCREEN_NAME` | Must match the folder name |
| `GAME_SCREEN_ID` | orion2re screen ID for auto-switching; `None` for sub-screens |
| `IS_OVERLAY` / `OVERLAY_DIM` | Render above the active screen (popups) |
| `USE_FRAME` / `FRAME_TITLE` | The HUD title plate and the two frame buttons |
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
  is for radio buttons (type 1) and free map clicks.
- **Take sizes from `core/zoomtables.py`** rather than tuning them.

## Gotchas

- Changing skin or mods requires a restart (palettes resolve at
  import time).
- The F3 editor saves to the base project, never into a mod.
- JSON overrides are whole-file; there is no merging.
- Always use `style.render_text(text, size, colour)` rather than
  `style.get_font(size).render(...)`. It detects which glyphs a font
  maps onto one shared bitmap and falls back to the proportional font
  for exactly those, aligned on the baseline. The shipped font
  (Aldrich, OFL) substitutes nothing, so detection finds nothing and
  the call costs what a plain render costs — but a mod may ship a
  demo font that maps several characters onto one glyph (one such
  font hid the digit 4 inside every number), and this is what keeps
  it readable.
- **A font you ship in a mod needs its licence next to it.**
- After any change, start OrionLayer (`python main.py` runs without the
  game) and look at what you changed.
- Some assets are **not in the repository** — the ship steps, the colony
  output panel's six icons
  (`screens/colony_summary/assets/output/`, 31x31, the size in
  `layout.json` `output.icon_size`; a replacement of any other size is
  refused) and the black hole master are generated, and the help
  texts and nebula sprites come from your own MOO2 files. If a file
  you want to override is missing after a clone, run
  `python tools/setup.py` first. `.gitignore` lists which and why.
- A mod overriding a generated asset works normally: resolution goes
  through `core/resources.py` either way, and the mod's copy wins
  before the generated one is ever consulted.
