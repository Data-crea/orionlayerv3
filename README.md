# OrionLayer

An HD interface for **Master of Orion 2**. OrionLayer replaces the game's
640x480 screens with high-resolution ones, up to 4K, and leaves the game
itself alone: the rules, the AI and your saves stay the game's.

![The galaxy map in OrionLayer](https://github.com/Data-crea/orionlayerv3/releases/download/base-pack-0956de83bb3d/screenshot-galaxy-map.jpg)

It runs on [orion2re](https://github.com/orion2re/orion2re), the C++
reimplementation of the original engine by Joes and the orion2re team.
orion2re runs the game; OrionLayer draws it and passes your clicks and
keys back. A screen that has no HD version yet keeps its last picture
with the notice "F12 to answer", and F12 shows the original's own screen,
so the game stays playable.

![The main menu](https://github.com/Data-crea/orionlayerv3/releases/download/base-pack-0956de83bb3d/screenshot-main-menu.jpg)

## Status

> **Not ready to use yet.** OrionLayer is under heavy development. It is
> not ready to play or to rely on yet, and none of its screens has been
> accepted.

You can start it, load or begin a game and play through the HD screens,
but expect missing pieces, screens that still fall back to the original,
and bugs.

## What you need

- **Master of Orion 2**, your own copy (GOG or Steam). OrionLayer is a
  modification, not a game: it includes none of the game's files and reads
  the texts and pictures it needs from your installation.
- **Python 3.10 or newer**, with git.
- **The engine**: the orion2re fork
  [Data-crea/orion2re](https://github.com/Data-crea/orion2re), branch
  `orionlayer`, based on orion2re v2.0.0. That branch carries every engine
  change OrionLayer needs, and setup checks that they are all there; how
  the two talk is described in the fork's
  [docs/extension-api.md](https://github.com/Data-crea/orion2re/blob/orionlayer/docs/extension-api.md).
  You build it yourself in step 1 below, which needs CMake, Ninja and a C++
  compiler.
- **xdotool** (optional), so the start can skip the game's intro.

On Debian or Ubuntu everything but the game comes with:

```sh
sudo apt install build-essential cmake ninja-build git python3-venv xdotool
```

## Getting started

These are the steps on Linux, from an empty folder to the HD main menu.
Below, the game is in `~/Master of Orion 2`; use your own folder. On
Windows the steps are the same in principle; the engine's build command
is in the fork's README, and OrionLayer itself has not been tried there
yet.

**1. Build the engine.** This puts the engine and its own data into your
game folder:

```sh
git clone --recurse-submodules --branch orionlayer https://github.com/Data-crea/orion2re.git
cd orion2re
cmake --preset linux-release -DORION2RE_EXT=ON -DORION2RE_GAME_DIR="$HOME/Master of Orion 2"
cmake --build --preset linux-release
cd ..
```

**2. Get OrionLayer and what it needs:**

```sh
git clone https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**3. Set it up.** This tells OrionLayer where the engine and the game are,
downloads OrionLayer's own pictures (the base pack, checked file by file)
and reads the texts and pictures it needs from your game:

```sh
.venv/bin/python tools/setup.py --engine "$HOME/Master of Orion 2/orion2re" --game "$HOME/Master of Orion 2" --extract
```

At its end setup reports the engine it found and whether every change
OrionLayer needs is in it.

**4. Play:**

```sh
.venv/bin/python play.py
```

The game starts with its own window hidden, the intro is skipped (with
xdotool), and OrionLayer opens on the HD main menu. Choose LOAD GAME or
NEW GAME as in the original. Closing OrionLayer stops the game.

### Where your game and engine are

Step 3 saves both paths in your OrionLayer settings. To change them later:

```sh
.venv/bin/python play.py --engine /path/to/orion2re --game "/path/to/Master of Orion 2"
```

When one is missing or wrong, `play.py` says which and starts nothing.
`.venv/bin/python main.py` starts OrionLayer without the game, to look at
the screens without game data.

### Keys

- **Right click**: the game's help, where the original has it.
- **F12**: the original's screen and back.
- **F11** fullscreen, **F7** the next window size, **F8** a screenshot
  (into `~/.config/orionlayer/screenshots/`).
- Every other F key is the game's own: F1 / F2 the previous and next
  fleet, F5 / F6 the previous and next own star, F9 the distance between
  stars, F10 a quick save.
- On the galaxy map the mouse wheel zooms and a right drag pans.

### German

Game Settings → LANGUAGE → Deutsch, then restart. OrionLayer's own words
are German at once; the game's words need the files of a German Master of
Orion 2. If your installation is English, name a German one once (it is
only read):

```sh
.venv/bin/python tools/language_files.py "/path/to/a German Master of Orion 2"
```

## Saves

Your saves are the game's own (`SAVE1.GAM` … in the game folder). This
engine writes them in its own format: **older engines — orion2re before
2.0 and the original game — cannot read them.** It reads the older saves.

## Modding

Pictures, colours, texts and whole screens can be replaced without
touching the code: put your files in your mod folder
(`~/.config/orionlayer/mod` on Linux), and
`.venv/bin/python tools/mod_template.py`
writes a starting point with every name it can hold. Mods inside the
project folder can also change data, layouts and screens. Everything is
in [MODDING.md](MODDING.md).

## Licences and credits

- **OrionLayer's code** is under the MIT licence: [LICENSE](LICENSE), which
  also says what it does not cover.
- **orion2re** is by Joes and the orion2re team, under GPL-3.0-or-later.
  OrionLayer includes no part of it; the two talk over a local connection.
- **The base pack**, OrionLayer's own pictures, is by Data (Daniel
  Sattler) under Creative Commons Attribution 4.0 (CC BY 4.0); its
  `LICENSE.txt` comes with it.
- **The font** is Aldrich by Matthew Desmond (MADType), under the SIL Open
  Font License.
- **Master of Orion II** is by Simtex / MicroProse. Its makers and the
  MOO2 1.50 patch team are credited in [doc/CREDITS.md](doc/CREDITS.md).
