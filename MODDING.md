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
<subject>/...  <screen>/...  shared/...   every other picture, see the rule below
files/<path in the tree>   the advanced name of any picture (still works)
texts/<screen>/<key>.txt   a text, by its key
```

**The rule for every other picture (stated once, used on every page
below).** A picture that several screens draw lives under its SUBJECT:
`buildings/`, `ships/`, `planets/`, `landscapes/`, `stars/`, `leaders/`,
`races/`, `research/`, `popups/`, `fleets/`. A picture of one screen lives
under that screen's name: `new_game/difficulty/...`,
`galaxy_map/nebula/...`. `shared/<path>` is a picture every screen shares.
`files/<path in the tree>` still works for every picture, so a mod made
with the older `files/` names keeps working; where both names fill one picture the
new name wins (one line in the log says so). You never need to know
OrionLayer's own folder tree: `NAMES.txt` gives every name.

OrionLayer's own pictures are not in this repository either: they come
as the **base pack** (`basepack.json` names every file), which
`tools/setup.py` downloads and installs into its own folder
(`~/.local/share/orionlayer/base` on Linux; `python tools/basepack.py
install <zip>` installs a zip you have).
A picture under its new name replaces the base-pack picture it stands for
(`files/<path in the tree>` does the same by the tree's path). Never edit
the base pack itself; your mod folder is the place.

**See a change without starting by hand.** Open the layout editor (F3) and
press **Reload** twice: OrionLayer restarts itself in place and reads the
folder again; the game keeps running. Save a layout first, unsaved changes
are lost. Nothing is reloaded inside the running window, because a picture
is kept in many places until the program ends - a fresh start is the only
reload that never shows a stale one.

**The older `files/` names end after the beta.** They keep working during it;
the log says how many files still use them, and `python tools/mod_migrate.py`
moves them to the new names (it shows what it would do first, never
overwrites, and writes an undo list).

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

### Buildings in HD

Each of the 48 buildings can have one painted picture, in your mod folder
only (OrionLayer ships none):

```
buildings/<nn>_<anything>.png
```

`<nn>` is the building's number (01 to 48, the game's order; `NAMES.txt`
lists every name, for example `buildings/01_alien_control_center.png`); the
number decides, the rest of the name is yours. A PNG with transparency, the
whole building cut tight to its drawing. It is fitted by its aspect into
the place the original's drawing had and never stretched, in the colony's
ground and sky, its build box and the build popup's picture box. Paint it at
about 4 times the widest drawing of the original: roughly 290 to 700 px wide
for a window of 3840 x 2160, the satellites 308 px. A building without a
picture is drawn as the original's; a file that cannot be read costs one
line in the log. The picture stands where the original's drawing stood, so
the buildings need the game's extracted pictures (`tools/colony_art_extract.py`).
A painted satellite is small in the sky, as the original's, and larger in the
build box and popup. No shadow is drawn for a painted building.

Your folder is read once, at the start: a picture you change or add while the
game runs shows after the next start.

### Leader portraits in HD

Painted, cut-out portraits (PNG with transparency) for the leaders are an
optional download of their own, [`orionlayer-leader-portraits.zip`](https://github.com/Data-crea/orionlayerv3/releases/tag/leader-portraits-8218a046e53e) — not
part of the base pack: they are redrawings of the game's portraits, and
the base pack's licence cannot cover them. Unpack it into your mod folder;
the pictures land in `leaders/`
(`colony/`, `officers/`, named `<nn>_<name>.png` by the
leader's number in the game). A leader without one, and every leader
while the mod folder is off, shows the game's own portrait. To replace a
portrait, or to give a leader one, put a PNG with transparency in your mod
folder under
`leaders/<colony|officers>/`
named `<nn>_<anything>.png` — the number decides, the name after it is
yours. The largest place a portrait is drawn at 3840 x 2160 is 438 x 528
(the turn's leader offer); every place scales down from it.

The leaders' skill icons are the game's own 16 x 16 pictures. A redrawn
icon goes under `leaders/skill_icons/` as
`skill_<k>_0.png` (`<k>` = the skill's number / 2; one icon serves a
skill and its starred variant); it is drawn as painted, fitted into the
icon's square — at 3840 x 2160 64 x 64 in the hire offer, 61 x 61 on a
slot (49 x 49 with five skills); a square picture of 64 x 64 serves all.

### Race leaders in HD

Painted race leaders: an optional download like the leader portraits, unpacked into
`races/leaders/<nn>_<name>.png` (`<nn>` = the race, 00-12).
Each fills the Races screen's portrait cell (476 x 409 at 3840 x 2160), cut
centred, from the top.

The mark over a race that has been wiped out is the game's own picture;
a painted one goes to `races/eliminated.png`
(a PNG with transparency, only the banner). It is drawn over the portrait
where the game draws its mark, as wide as the game's banner — 451 px at
3840 x 2160, 225 px at 1920 x 1080 — at its own proportion, centred on the
cell; it shows even without the game's extracted pictures.

### The research panel's pictures

Each of the eight research categories can have a picture in its box, on
the research screen and on the research choice over the map alike:
`research/<category>.png`, `<category>` one of
`biology power physics construction force_fields chemistry computers
sociology`. The picture fills the box at its own proportion, centred, the
overflow cut (never stretched); the box is about 2.7 : 1 on the choice
over the map (1004 x 374 at 3840 x 2160) and about 3.8 : 1 on the
research screen (1319 x 345), so a picture of 1320 x 500 or more serves
both. Its left side is darkened and the ground under the words is held
dark enough to read them; a category without a picture keeps the plain
box.

### The Leaders screen's pictures

The Leaders screen has eight picture places, filled only from your mod
folder (OrionLayer ships none of them), each under
`leaders/screen/`:

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

### The Fleets screen's map picture

The Fleets screen's small galaxy map takes a painted background from your
mod folder only (OrionLayer ships none):
`fleets/minimap_background.png`. It fills
the map's whole panel — 1992 x 1158 at 3840 x 2160, 996 x 579 at
1920 x 1080 — under the stars, the fleets and the relocation lines. Paint
it without a frame: OrionLayer draws the panel's edge over it and clips
the picture to the panel's outline. Any size of roughly that shape works;
it is scaled to fill, never stretched, the overflow cut evenly. Unlike the
Leaders screen's galaxy box it is drawn as painted, not darkened, so keep
it dark enough for the small stars to stand out. Missing, unreadable, or
the Mod folder Off: the map is black, as before.

The ship panel under it shows the scanned ship a second time, large, at
its right: your painted ship (the battle's `cmbtshp` picture, see "The
battle's pictures") when the folder holds one, otherwise the game's own
ship picture. It needs no file of its own.

### The battle's pictures

The battle draws the game's own pictures from the files
`tools/combat_art_extract.py` extracts. One PNG replaces one stored
drawing, used as painted (no palette), at
`combat/gamedata/<file>/<entry>_<frame>.png` (the ships, `<file>` =
`cmbtshp`, are `ships/battle/<entry>_<frame>.png`); the
facings the game draws as flips stay flips, so a ship needs its five
stored facings, not sixteen. `NAMES.txt` gives the numbering.

Paint at the stored drawing's size or at a whole multiple of it: a Doom Star is 59 x 60, so 118 x 120, 236 x 240 and so on.
OrionLayer draws the picture at the drawing's size and place and keeps
its detail as the camera zooms in; any other size is refused (the log
says so) and the game's drawing is used. A ship's frames are
`<entry>_0.png` to `<entry>_19.png` (in `ships/battle/`): the five stored facings (0 points
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
`ships/battle/all_<picture>_<frame>.png`
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
ships/battle/all_<picture>_<frame>.png                    the ship
ships/battle/all_<picture>_<frame>_<pattern>_mask.png     first zone
ships/battle/all_<picture>_<frame>_<pattern>_mask2.png    second zone
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
ships/battle/all_<picture>_<frame>_engine.png    the engine mask
ships/battle/<colour * 45 + picture>_<frame>_engine.png   for a colour's own file
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
PNG at `<screen>/gamedata/<group>/<entry>_<frame>.png` (`ship_design/...`,
`audience/...`, `info/...`; for the three screens that are also subjects,
Fleets, Leaders and Races, the advanced name
`files/screens/<screen>/assets/gamedata/<group>/<entry>_<frame>.png` is the
only one) replaces the drawing stored as `<group>/<entry>.bin` (frame 0 for a still
picture; the Races screen and the Tech Review keep their drawings without
a group folder,
`files/screens/races/assets/gamedata/portrait_3_0.png`,
`info/gamedata/app_<application>_0.png`), used as painted — no palette and no ship colours, so a ship you
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
landscapes/colony/<climate>.png
landscapes/colony/<climate>_<ground>.png   (optional)
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
Paint at 3728 x 1270 (about 2.94 : 1): that is the panel at 3840 x 2160,
so the picture is sharp there and only scaled down at every smaller
window (1864 x 635 at 1920 x 1080, 2484 x 846 at 2560 x 1440).

### The colony screen's production symbols

The BC, food, industry and research rows count with the game's own
symbols, as the game does (one per unit, a second kind per ten), and end
with the row's value as a number. The symbols come from your game files
(`python tools/colony_art_extract.py`); without them each row shows one
icon and the number. A PNG replaces a symbol, drawn at the game's size
(16 x 23) and enlarged like the screen's other sprites:

```
colony/gamedata/prod_<type>_<tens>_0.png
colony/gamedata/import_<type>_<tens>_0.png
```

`<type>` is 0 food, 1 industry, 2 research, 3 BC; `<tens>` is 0 for the
ones and 1 for the tens. `import_…` are the imported goods (and, for
industry, the pollution); a shortage is the import symbol with the
game's red outline round it.

### Turning planets

Every planet OrionLayer draws is a sphere that turns slowly, built from a
flat map of its type — the colony list, the Planets list, the star system
windows, the colony screen's system display, the invasion popup and the
battle. The light, the darkening to the edge and the glow are drawn over
the turning map, so they stay where they are.

Replace a type's map, or add clouds over it (any size, 2:1; a map wraps
left to right):

```
planets/maps/<type>_surface.png     the surface, no alpha needed
planets/maps/<type>_clouds.png      optional, with transparency,
                                    turns a little faster
```

`<type>` is one of toxic, radiated, barren, desert, tundra, ocean, swamp,
arid, terran, gaia (and volcanic, which the game has no climate for).
Gas giants and asteroid belts are not spheres and stay as they are.

The numbers are in `planets.json` in your mod folder; write only the keys
you change:

```json
{
  "seconds_per_turn": 480,
  "speed_spread": 0.15,
  "ambient": 0.10,
  "types": { "ocean": { "glow": [60, 140, 230], "speed": 0.5 } }
}
```

| key | meaning (default) |
|---|---|
| `seconds_per_turn` | one full turn of a planet whose speed is 1; 0 stops the rotation (60) |
| `speed_spread` | each planet's own speed lies within 1 ± this; its start angle is its own (0.15) |
| `cloud_speed` | the clouds' speed compared with the surface (1.25) |
| `ambient` | how bright the night side stays, 0 to 1 (0.10) |
| `limb` | how much the edge darkens, 0 to 1 (0.55) |
| `glow_width` | the glow ring, a fraction of the picture's half size; the sphere fills the rest, 0.068 draws it as large as the old pictures (0.068) |
| `rim` | the atmosphere's brightness over the lit rim (0.45) |
| `types.<type>.glow` | the glow colour `[r, g, b]` |
| `types.<type>.glow_strength` | its strength (0.8) |
| `types.<type>.speed` | this type's turn compared with the others (1.0) |
| `types.<type>.light` | where the light comes from `[x, y, z]`: x right, y down, z toward you; upper left is `[-0.58, -0.52, 0.63]` |
| `types.<type>.emissive` | 0 to 1: how much bright warm spots (lava) keep their own light on the night side; volcanic 1, radiated 0.5 |

All planets turn the same way. A planet's start angle and exact speed come
from the planet itself, so it is the same on every screen and every run.

**An old-style picture still works.** A type for which you supply a full
planet picture (below) and no map of its own is shown as that static
picture: no rotation, no error. Supply a map for the type too and the map
wins.

### Planet pictures and the Space Dragon

One picture per climate replaces the planet wherever OrionLayer draws one
— the colony list, the Planets list, the star system windows (galaxy map
and Leaders), the colony screen's system display and the invasion popup —
at every planet size; the battle keeps its own pictures:

```
planets/pictures/<climate>.png
```

`<climate>` as above. A disc on transparency, 200 px or more (a smaller
one is ignored): it is cut to its ink and smoothly scaled to each place's
size. It wins over painted battle planets in the battle's slot
(`combat/gamedata/cmbtplnt/`), which then show in the
battle only.

The Space Dragon's bribe shows your picture above its message, in the
offer and when you cannot pay (not while you choose its new star on the
map):

```
popups/dragon_bribe.png
```

Any size; it is fitted whole, never stretched, into the panel's width and
at most about half the window's height. Without it the popup is text only.

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

**Which of the two?** Your mod folder (above) is for pictures and texts:
it is one folder, always the same, outside the program. A mod inside the
tree (`mods/<name>/`, switched on in `settings.json`) is for what is not a
picture or a text: layouts (`boxes.json`), data (`races.json`, `traits.json`),
help texts, skins, fonts and new screens, and it mirrors OrionLayer's own
folder tree, so you do need to know that tree. The layout editor writes
its changes there. A picture can be put in either; use the mod folder.
`mods/example_mod` is the smallest working example of the second kind.

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

Note on `boxes.json`: the in-game F3 editor never touches the base
project. Press F3 on any screen: a panel lists the screen's boxes by
name, says what each one is for and lets you move it (drag it, or type
X, Y, Width and Height) and resize it. Save (Ctrl+S) writes
`mods/<mod>/screens/<screen>/boxes.json` for the first mod in
`active_mods`; with none active it makes a mod named `my_layout` and tells you
to add `"my_layout"` to `active_mods` in `settings.json` and restart.
Boxes cannot be created or deleted (a box is a name the screen's code
looks up) and stay inside the 1920x1080 reference area. Revert drops
what you have not saved.

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

A mod's screen folder is loaded as a package, one per folder: its files may
import each other relatively (`from .helper import X`), as the base screens
do. A screen that fails to import is logged with its traceback and left
out, and the base screen of that name stays.

---

## The galaxy map's pictures

The galaxy map's star sprites, the black hole, the ship and monster icons,
wormhole links, nebulas, the sidebar readouts and the HUD boxes have their own
guide: [doc/modding_galaxy_map.md](doc/modding_galaxy_map.md).

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
- The F3 editor saves into a mod, never into the base project.
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
