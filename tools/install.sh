#!/bin/sh
# OrionLayer on Linux in one go: README "Getting started", steps 1 to 3.
#
#     tools/install.sh "$HOME/Master of Orion 2"
#
# Run it from the orionlayerv3 folder you cloned. It
#   1. clones the engine (the fork Data-crea/orion2re, branch orionlayer)
#      BESIDE this folder, as ../orion2re — where setup looks for it —,
#      or uses the clone already there, and builds it into the game folder;
#   2. makes the Python environment .venv and installs what OrionLayer needs;
#   3. runs setup with the engine and the game folder.
# It installs no system packages: when a tool is missing it prints the
# README's package line and stops.
set -e

# The README's package line, word for word (a smoke check holds the two
# equal): the build tools, git, Python's venv, xdotool, and what SDL3 — part
# of the engine — needs to build (its own docs/README-linux.md).
PACKAGES="build-essential cmake ninja-build pkg-config git python3-venv xdotool libasound2-dev libpulse-dev libaudio-dev libfribidi-dev libjack-dev libsndio-dev libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libxtst-dev libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev libthai-dev libusb-1.0-0-dev libpipewire-0.3-dev libwayland-dev libdecor-0-dev liburing-dev"
FORK="https://github.com/Data-crea/orion2re.git"

GAME="$1"
if [ -z "$GAME" ]; then
    echo "usage: tools/install.sh \"/path/to/Master of Orion 2\"" >&2
    exit 2
fi
if [ ! -d "$GAME" ]; then
    echo "not a folder: $GAME — give the folder of your Master of Orion 2" >&2
    exit 2
fi
GAME=$(cd "$GAME" && pwd)
HERE=$(cd "$(dirname "$0")/.." && pwd)
ENGINE_SRC="$(dirname "$HERE")/orion2re"

missing=""
for tool in git cmake ninja pkg-config cc c++ python3; do
    command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
if ! python3 -c "import ensurepip, venv" >/dev/null 2>&1; then
    missing="$missing python3-venv"
fi
if [ -n "$missing" ]; then
    echo "missing:$missing" >&2
    echo "On Debian or Ubuntu install everything with:" >&2
    echo "  sudo apt install $PACKAGES" >&2
    exit 1
fi

echo "== 1. the engine: $ENGINE_SRC"
if [ -d "$ENGINE_SRC/.git" ]; then
    echo "   using the clone already there (not updated)"
else
    git clone --recurse-submodules --branch orionlayer "$FORK" "$ENGINE_SRC"
fi
cd "$ENGINE_SRC"
cmake --preset linux-release -DORION2RE_EXT=ON -DORION2RE_GAME_DIR="$GAME"
cmake --build --preset linux-release

echo "== 2. OrionLayer's Python environment: $HERE/.venv"
cd "$HERE"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

echo "== 3. setup"
.venv/bin/python tools/setup.py --engine "$GAME/orion2re" --game "$GAME" --extract
echo "Done. Start the game with: .venv/bin/python play.py"
