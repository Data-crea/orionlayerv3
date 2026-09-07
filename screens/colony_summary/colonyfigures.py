"""The population figures: the game's own sprites, at the sprite step.

**DECISION 50.** The colony screens draw the player's own RACEICON
sprites, extracted by `tools/raceicon_extract.py`, stepped up by an
integer nearest-neighbour factor and never scaled (decision 28). HD
figure artwork is not a project deliverable. A mod replaces figures
per file — one PNG, one documented name, one documented folder,
restart — and the base set is the fallback per file.

WHICH SPRITE A POP GETS, transcribed from `COLONY::Colony_Pop_Anim_`
(colony.cpp:1268-1283) in the source's own order, which is
load-bearing:

    race  = _player[Get_Effective_Pop_Player_(...)].race
            (colony.cpp:1272-1275) — the pop's OWN player, which is
            the low nibble of the pop word unless that nibble is 8 or
            9, where it is the colony's owner (colony.cpp:1226-1234)
    if pop_word & 0x400          -> Colony_Pop_Icon_(race)
                                    = race * 13 + 12, the portrait
    else People_Anim_(job, state, race)   (colony_main.cpp:444-450)
        state 2  -> race * 13 + job * 2 + 1
        state 3  -> 0xAA, native      \\  race-independent, one
        state 4  -> 0xA9, android      /  sprite for every race

THE CONQUERED TEST COMES FIRST. A conquered native draws a portrait,
not the native sprite, because `Colony_Pop_Anim_` checks 0x400 before
it ever reaches `People_Anim_`. Reordering these two reads as a
one-line simplification and changes the picture.

**54 FIGURES, EVERY ONE 28 x 28.** 13 races x three jobs, 13 race
portraits, native and android. Measured across all 171 entries of the
extraction: the six job entries of every race block and the two
shared entries are 28x28 without exception; only `military_4`
(35x28) and `military_5` (24x35) differ, and neither is drawn on this
screen. The master size is therefore a fact about the game's data and
not a convention this project chose, which is why a wrong-sized file
is refused rather than fitted.

**THE STEP IS MADE HERE, NOT IN THE EXTRACTOR**, and the reason is
the mod path. A mod supplies a 28x28 master and it has to arrive at
the same size as the base figure it replaces; if the extractor
pre-stepped, mods would need a second path to the same pixel, which
is what decision 5 exists to stop. The cost is 54 nearest-neighbour
blits of at most 112x112 at load.

**PER-STEP MOD FILES, AND THE ORDER IS PER ROOT.** Beside
`<name>.png` a mod may ship `<name>@2x.png`, `@3x` and `@4x` at
exactly 56, 84 and 112 — each replaceable alone (decision 50). For
one figure at one step the order is

    explicit step file  ->  stepped master  ->  the next root

resolved INSIDE each root before moving to the next, so a mod that
ships only a master beats the base project's step files. Two
`resources.resolve` calls would give the opposite — a base step file
outranking a mod's master — which is why `Resources.roots()` exists.
"""
import logging
import os

from core import zoomtables

# **NO MODULE-LEVEL pygame, AND THAT IS A CONSTRAINT AND NOT A
# STYLE.** `colonyrows` states in its own docstring that it imports
# no pygame and knows nothing about pixels — the seam that let it and
# `colonylist` both stay under the guideline — and it now imports
# THIS module for `figure_for`. A pygame import here would reach it
# transitively and quietly end that property. The naming half of this
# module is pure arithmetic over a pop word; only the loading half
# needs a surface, and it imports pygame where it uses it. A smoke
# check walks the import graph, because the property had been prose
# for as long as it had been true.

log = logging.getLogger("figures")

#: Where the extractor writes and a mod overrides. SHARED, because
#: both colony screens draw the same figures and a per-screen folder
#: would need the mod author to copy every file twice.
FIGURE_DIR = os.path.join("assets", "shared", "figures")

#: The game's own sprite size, measured across the extraction — not a
#: convention. See the module docstring.
MASTER_SIZE = 28

#: `enum STOCK_RACE` (orion2_consts.h:444-457) in ITS OWN ORDER, with
#: `STOCK_RACE_COUNT == 13` held by a static_assert at :1379. These
#: are the SOURCE's identifiers, not `MOX::_race_names[]`
#: (estrings.cpp:108-127), which holds the localised display strings
#: — a file name that changed with the game's language would make a
#: mod stop working on a translated install.
RACE_KEYS = ("alkari", "bulrathi", "darlok", "elerian", "gnolam",
             "human", "klackon", "meklar", "mrrshan", "psilon",
             "sakkra", "silicoid", "trilarian")

#: `ECON_FOOD/INDUSTRY/RESEARCH` are 0/1/2 (orion2_consts.h:119-121),
#: which is the `job * 2` of `People_Anim_`.
ROLE_KEYS = ("farmer", "worker", "scientist")

#: The two race-independent sprites, `People_Anim_` states 3 and 4.
NATIVE = "native"
ANDROID = "android"

#: The steps a mod may supply explicitly, and the size each must be.
#: Derived from MASTER_SIZE rather than written out, so the three
#: numbers in `doc/modding_figures.md` cannot drift from the check.
STEPS = tuple(sorted(set(zoomtables.FIGURE_STEP.values())))


def step_size(step):
    """The exact pixel size a figure must be at this step."""
    return MASTER_SIZE * int(step)


def master_name(race=None, role=None, portrait=False, shared=None):
    """The documented file name for one figure, without directory."""
    if shared:
        return f"{shared}.png"
    if portrait:
        return f"{RACE_KEYS[race]}_portrait.png"
    return f"{RACE_KEYS[race]}_{ROLE_KEYS[role]}.png"


def step_name(name, step):
    """`<name>@2x.png` from `<name>.png`. One place, two readers."""
    return f"{name[:-4]}@{int(step)}x.png"


def all_names():
    """Every figure this screen can draw, in a stable order.

    The ONE table. `doc/modding_figures.md` is generated from it and
    a smoke check regenerates the document and compares byte for
    byte, so a name added here reaches the documentation or the check
    goes red — a hand-written list of 54 names is wrong within a
    month (decision 40's licence, applied to a document).
    """
    names = []
    for race in range(len(RACE_KEYS)):
        for role in range(len(ROLE_KEYS)):
            names.append(master_name(race=race, role=role))
        names.append(master_name(race=race, portrait=True))
    names.append(master_name(shared=NATIVE))
    names.append(master_name(shared=ANDROID))
    return tuple(names)


def figure_for(pop_word, owner_race, races):
    """The figure name for one pop word, or None.

    `Colony_Pop_Anim_` transcribed (colony.cpp:1268-1283). `races`
    maps a player index to a race index; `owner_race` is the
    colony owner's, used where the pop word names no player of its
    own. None when the race is not known — an absent player record,
    which the caller draws as a plain cell rather than guessing a
    race and drawing the wrong species.
    """
    nibble = int(pop_word) & 0x0F
    if nibble in (8, 9):
        race = owner_race
    else:
        race = races.get(nibble)
    if race is None or not 0 <= race < len(RACE_KEYS):
        return None
    # THE CONQUERED TEST IS FIRST. See the module docstring.
    if int(pop_word) & 0x400:
        return master_name(race=race, portrait=True)
    if nibble == 9:
        return master_name(shared=NATIVE)
    if nibble == 8:
        return master_name(shared=ANDROID)
    job = (int(pop_word) >> 7) & 0x3
    if not 0 <= job < len(ROLE_KEYS):
        return None
    return master_name(race=race, role=job)


class FigureSet:
    """The loaded figures at one step, or a stated absence.

    `state` is "ok", "missing" or "partial" — the same shape the name
    loaders use, with "partial" where some files are present and
    others are not, because a set that draws 40 of 54 figures and
    silently leaves 14 cells coloured is a worse picture than either
    whole answer and the screen has to be able to say so.

    **AN ABSENT SET IS NOT AN ERROR.** The screen falls back to the
    coloured cells it has always drawn and names the command. That
    fallback is a STATE OF THIS FEATURE and not dead code: it is
    what a player without the extraction sees, which is why the cell
    renderer is excluded from Stage 5's deletion list.
    """

    def __init__(self, resources, step, root=None):
        self.step = int(step)
        self.state = "missing"
        self.figures = {}
        self.refused = []
        self._load(resources, root)

    def _load(self, resources, root):
        names = all_names()
        for name in names:
            surface = self._one(resources, name, root)
            if surface is not None:
                self.figures[name] = surface
        if not self.figures:
            log.info("figures: none of %d found under %s — run "
                     "`python tools/raceicon_extract.py`",
                     len(names), FIGURE_DIR)
            return
        self.state = "ok" if len(self.figures) == len(names) else "partial"
        if self.state == "partial":
            log.warning("figures: %d of %d present at step %dx — the "
                        "rest draw as coloured cells",
                        len(self.figures), len(names), self.step)

    def _one(self, resources, name, root):
        """One figure at this step: step file, then stepped master.

        Per root and in that order — see the module docstring. A file
        of the wrong size is REFUSED with one log line naming the
        size it is and the size it must be, and the search continues
        to the next root; it is never scaled to fit, because a figure
        a step out of line with its neighbours reads as a rendering
        fault rather than as a bad file.
        """
        want = step_size(self.step)
        for base in ([root] if root else resources.roots()):
            direct = os.path.join(base, FIGURE_DIR,
                                  step_name(name, self.step))
            surface = self._read(direct, want, want)
            if surface is not None:
                return surface
            master = os.path.join(base, FIGURE_DIR, name)
            surface = self._read(master, MASTER_SIZE, want)
            if surface is not None:
                return surface
        return None

    def _read(self, path, need, want):
        """Load `path`, refuse it unless it is `need` square, step it.

        Returns None both for "not there" and for "refused", and the
        two are distinguished in the LOG rather than in the return,
        because the caller does the same thing with either: try the
        next root. `refused` keeps the list so a check can assert a
        wrong-sized file was rejected and not merely absent.
        """
        import pygame
        if not os.path.exists(path):
            return None
        try:
            image = pygame.image.load(path)
        except pygame.error as err:
            log.warning("figures: %s will not load (%s)", path, err)
            self.refused.append(path)
            return None
        size = image.get_size()
        if size != (need, need):
            log.warning("figures: %s is %dx%d and must be %dx%d — "
                        "refused, the base figure is used instead",
                        path, size[0], size[1], need, need)
            self.refused.append(path)
            return None
        image = image.convert_alpha() if pygame.display.get_init() \
            else image
        if need == want:
            return image
        # INTEGER NEAREST NEIGHBOUR, decision 28. `scale` and not
        # `smoothscale`: a smoothed sprite at 2x is a different
        # object from the game's, and the whole point of stepping is
        # that it is the same pixels, larger.
        return pygame.transform.scale(image, (want, want))

    def get(self, name):
        """One stepped figure, or None when this set does not hold it."""
        return self.figures.get(name)


def figure_step(scale):
    """THE sprite step for a layout scale. One home, two readers.

    `colonytrack._column_boxes` lays the cell pitch at this factor and
    this module loads the sprites at it, and they are the SAME
    number by construction — a track laid at 3x holding sprites
    loaded at 2x is a picture where every figure is off its cell by a
    growing amount, and nothing in either module would report it.
    The pick is `box.closest_resolution` over the table's own keys
    (decision 1's fallback chain, decision 26's table).

    Made the one home 7 September 2026, when this module was about to
    become the second place that answered it.
    """
    from core import box as box_mod
    return zoomtables.FIGURE_STEP[box_mod.closest_resolution(
        zoomtables.FIGURE_STEP, round(1920 * scale), round(1080 * scale))]


def set_for(screen, scale):
    """The figure set for a screen's current scale, cached per App.

    Keyed by STEP and not by window size: two windows that pick the
    same `FIGURE_STEP` share one set, which is the point of the step
    being a small integer table (decision 26).
    """
    step = figure_step(scale)
    cache = getattr(screen.app, "figure_sets", None)
    if cache is None:
        cache = {}
        screen.app.figure_sets = cache
    if step not in cache:
        cache[step] = FigureSet(screen.app.res, step)
    return cache[step]
