"""Where the game engine and the game are — work order 229 D.

Until 229 both were this project's machine: `tools/engine_start.py` started
`~/orion2re/out/build/Linux/linux-debug/orion2re`, and every extractor read
`~/Master of Orion 2`. A player whose files are elsewhere failed with a
traceback, or found nothing and was not told why. Now each comes from, in
this order:

  1. the environment: `ORIONLAYER_ENGINE`, `ORIONLAYER_GAME_DIR`
  2. the player's own settings (`user_settings.json` in the player's folder,
     `core.usermod.user_dir`): `engine_path`, `game_dir` — `python play.py
     --engine PATH --game DIR` writes them
  3. the old defaults, which are where this project's own machine keeps
     them — so `cd ~/orionlayerv3 && python play.py` keeps working there
     with nothing set.

`problems()` names what is missing and how to set it; `play.py` prints it
and stops instead of failing deep inside the start.
"""
import os

ENGINE_ENV = "ORIONLAYER_ENGINE"
GAME_ENV = "ORIONLAYER_GAME_DIR"
ENGINE_KEY = "engine_path"
GAME_KEY = "game_dir"
DEFAULT_ENGINE = "~/orion2re/out/build/Linux/linux-debug/orion2re"
DEFAULT_GAME = "~/Master of Orion 2"
#: A file every Master of Orion 2 install has (the extractors read it).
GAME_MARKER = "HESTRNGS.LBX"


def _settings(settings):
    if settings is not None:
        return settings
    from core import usersettings
    return usersettings.load().data


def _pick(env, key, default, environ, settings):
    environ = os.environ if environ is None else environ
    value = environ.get(env) or (_settings(settings) or {}).get(key) \
        or default
    return os.path.abspath(os.path.expanduser(value))


def engine(environ=None, settings=None):
    """The orion2re binary to start."""
    return _pick(ENGINE_ENV, ENGINE_KEY, DEFAULT_ENGINE, environ, settings)


def game_dir(environ=None, settings=None):
    """The Master of Orion 2 folder: the engine's working directory, where
    the saves live, and what the extractors read."""
    return _pick(GAME_ENV, GAME_KEY, DEFAULT_GAME, environ, settings)


def game_dirs(environ=None, settings=None):
    """The folders an extractor looks in for a game file: the game folder
    and its DATA subfolder."""
    base = game_dir(environ, settings)
    return [base, os.path.join(base, "DATA")]


def _has_marker(folder):
    try:
        names = {n.upper() for n in os.listdir(folder)}
    except OSError:
        return False
    return GAME_MARKER in names or (
        "DATA" in names and _has_marker(os.path.join(folder, "DATA")))


def problems(environ=None, settings=None):
    """Plain sentences, one per path that is missing or wrong; [] when both
    are usable."""
    out = []
    eng, game = engine(environ, settings), game_dir(environ, settings)
    how = ("set it once with  python play.py --engine /path/to/orion2re  "
           f"(or the environment variable {ENGINE_ENV})")
    if not os.path.isfile(eng):
        out.append(f"The game engine (orion2re) is not at {eng} — {how}.")
    elif not os.access(eng, os.X_OK):
        out.append(f"The game engine at {eng} is not executable — "
                   f"chmod +x it, or {how}.")
    how = ("set it once with  python play.py --game /path/to/'Master of "
           f"Orion 2'  (or the environment variable {GAME_ENV})")
    if not os.path.isdir(game):
        out.append(f"The Master of Orion 2 folder is not at {game} — {how}.")
    elif not _has_marker(game):
        out.append(f"{game} does not look like Master of Orion 2 (no "
                   f"{GAME_MARKER} in it or its DATA folder) — {how}.")
    return out


def remember(engine_path=None, game=None):
    """Write the player's choice into their own settings file."""
    from core import usersettings
    s = usersettings.load()
    if engine_path:
        s.set(ENGINE_KEY, os.path.abspath(os.path.expanduser(engine_path)))
    if game:
        s.set(GAME_KEY, os.path.abspath(os.path.expanduser(game)))
    usersettings.save(s)
    return s.path
