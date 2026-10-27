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
>
> **The beta runs on Linux only.** Windows (and macOS) are not part of it:
> OrionLayer does not start on Windows yet.

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
  compiler — and, on Linux, the development packages of SDL3, the library
  the engine draws and plays sound with.
- **xdotool** (optional, Linux), so the start can skip the game's intro.

On Debian or Ubuntu everything but the game comes with this one line (the
build tools, git, Python's venv, xdotool, and what SDL3 needs to build):

```sh
sudo apt install build-essential cmake ninja-build pkg-config git \
    python3-venv xdotool libasound2-dev libpulse-dev libaudio-dev \
    libfribidi-dev libjack-dev libsndio-dev libx11-dev libxext-dev \
    libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev \
    libxtst-dev libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev \
    libgles2-mesa-dev libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev \
    libudev-dev libthai-dev libusb-1.0-0-dev libpipewire-0.3-dev \
    libwayland-dev libdecor-0-dev liburing-dev
```

Windows is not part of the beta (see [On Windows](#on-windows)).

## Getting started

These are the steps on Linux, from an empty folder to the HD main menu.
Below, the game is in `~/Master of Orion 2`; use your own folder. Do
steps 1 and 2 in the same folder: setup looks for the engine's source
beside OrionLayer's (`orion2re` next to `orionlayerv3`) and checks there
that it carries every change OrionLayer needs. Windows: see
[On Windows](#on-windows).

**Clone the `beta` branch**, as the commands below do. `main` is the
maintainer's working branch: its pictures can be ahead of the base pack that
setup downloads, so a fresh install of `main` may stop at the download.
`beta` only moves to a version whose base pack is published and installs
from empty.

**The short way.** Clone OrionLayer and let one script do steps 1 to 3
(it clones the engine beside it, builds it into your game folder, makes
the Python environment and runs setup):

```sh
git clone --branch beta https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
tools/install.sh "$HOME/Master of Orion 2"
```

Then play (step 4). The same, step by step:

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
git clone --branch beta https://github.com/Data-crea/orionlayerv3.git
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

*Optional:* painted leader portraits come as their own download,
[`orionlayer-leader-portraits.zip`](https://github.com/Data-crea/orionlayerv3/releases/tag/leader-portraits-8218a046e53e); unpack it into OrionLayer's mod folder
(its place is shown in the game: GAME, SETTINGS, ORIONLAYER, SYSTEM).
Without it the leaders show the game's own portraits.

**4. Play:**

```sh
.venv/bin/python play.py
```

The game starts with its own window hidden, the intro is skipped (with
xdotool), and OrionLayer opens on the HD main menu. Choose LOAD GAME or
NEW GAME as in the original. Closing OrionLayer stops the game.

### On Windows

**Windows is not part of the beta, and OrionLayer does not start there
today** (the client calls a Linux-only function while starting, and `play.py`
uses Linux-only process calls to run the engine). The steps below are the
Linux steps with Windows' commands, kept for later and not supported. You
would need Python 3.10 or newer, git and Visual Studio 2022 with "Desktop
development with C++". In an "x64 Native Tools Command Prompt for VS
2022", in one folder, with the game in `C:\GOG Games\Master of Orion 2`:

```bat
git clone --recurse-submodules --branch orionlayer https://github.com/Data-crea/orion2re.git
cd orion2re
cmake --preset win64-release -DORION2RE_EXT=ON -DORION2RE_GAME_DIR="C:\GOG Games\Master of Orion 2"
cmake --build --preset win64-release
cd ..
git clone --branch beta https://github.com/Data-crea/orionlayerv3.git
cd orionlayerv3
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python tools\setup.py --engine "C:\GOG Games\Master of Orion 2\orion2re.exe" --game "C:\GOG Games\Master of Orion 2" --extract
.venv\Scripts\python play.py
```

The game's intro cannot be skipped there (xdotool is Linux's).

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
in [MODDING.md](MODDING.md); the galaxy map's pictures have their own
part, [doc/modding_galaxy_map.md](doc/modding_galaxy_map.md).

## Licences and credits

- **OrionLayer's code** is under the MIT licence: [LICENSE](LICENSE), which
  also says what it does not cover.
- **orion2re** is by Joes and the orion2re team, under GPL-3.0-or-later.
  OrionLayer includes no part of it; the two talk over a local connection.
- **The base pack**, OrionLayer's own pictures, is by Data (Daniel
  Sattler) under Creative Commons Attribution 4.0 (CC BY 4.0); its
  `LICENSE.txt` comes with it.
- **The leader portraits** (the optional download) are redrawings of the
  game's portraits; the copyright in the original artwork stays with its
  rightsholder, and they are not under the base pack's licence.
- **The font** is Aldrich by Matthew Desmond (MADType), under the SIL Open
  Font License.
- **Master of Orion II** is by Simtex / MicroProse. Its makers and the
  MOO2 1.50 patch team are credited in [doc/CREDITS.md](doc/CREDITS.md).
