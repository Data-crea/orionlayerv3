"""The figure set for the colony list's optional figure mode: loading
it, refusing a bad one, and scaling it onto one common height.

Split from `colonylist.py` because this is the sprite set's contract
— what a valid set is, and what it must be scaled to — while the
drawing stays with the mode that draws it. Nothing here draws.

**The sprites are never in the repository.** They are cut from the
player's own copy of the game, so decision 40 applies exactly as it
does to the help texts and the nebulae: absent is a state to explain,
not an error, and figure mode falls back to squares on any
installation that has no set. That is also why the mode is off by
default — it cannot come on by itself.
"""
import logging

import pygame

log = logging.getLogger("colony_summary")

#: A set whose source crops disagree in height by more than this is
#: refused outright. See `check_crop_heights`.
MAX_CROP_HEIGHT_SPREAD = 2


def check_crop_heights(sprites, names, spread=MAX_CROP_HEIGHT_SPREAD):
    """Raise unless the set's source crops share a baseline.

    **Loud on purpose.** A set whose crops differ in height is not a
    set: every sizing rule below normalises the whole group onto one
    height, so one crop that carries an extra strip of background —
    or is missing a hat — silently rescales every figure beside it.
    The symptom is that the farmer looks slightly wrong next to the
    worker, which reads as an ART problem and sends the next session
    to redraw a sprite, when the fault is a MEASUREMENT: a crop
    rectangle taken two pixels low.

    Absent sprites are handled quietly by `load_figures`; a set that
    is present and inconsistent is not, because there is nothing to
    fall back to that would not be a lie about the artwork.
    """
    heights = [s.get_height() for s in sprites]
    if max(heights) - min(heights) > spread:
        pairs = ", ".join(f"{n} {s.get_width()}x{s.get_height()}"
                          for n, s in zip(names, sprites))
        raise ValueError(
            f"colony figure crops do not share a baseline: {pairs} — "
            f"heights span {max(heights) - min(heights)} px against a "
            f"{spread} px tolerance. Re-cut the crops to one baseline; "
            f"do not adjust the artwork.")


def figure_sizes(max_width, sprites, height_limit=None):
    """Scale a set onto ONE common height. Normalise on HEIGHT.

        common_height = min over the set of (max_width * h_i / w_i)

    Read it as: what height would each sprite reach if it were
    exactly `max_width` wide? Take the smallest. The sprite that
    yields it — the WIDEST in the set, the one with the smallest
    h/w — lands at `max_width` and sets the height; every other
    sprite follows from its own aspect ratio and comes out narrower.

    **Never normalise on width.** Giving every sprite the same width
    inverts the whole set: the narrowest figure becomes the tallest,
    because a narrow sprite stretched to a common width grows in both
    axes. It also makes the set unstable — adding one new sprite in a
    different tool pose, wider than anything already there, resizes
    every figure that was already correct. Normalising on height
    changes nothing about a sprite that was not the widest.

    `max_width` is the STEP MINUS THE GAP, which is one `unit`: a
    figure that ate its gap would touch its neighbour.

    Integer arithmetic throughout, and `//` rather than `int(a / b)`
    — every value here is positive, so the two agree, and the exact
    form cannot land a width on 14 because 15.0 came back as
    14.999999. Verified against the measured set: at a step of 23
    with a gap of 2, `max_width` is 21 and crops of 15x26 (farmer),
    20x25 (worker) and 18x26 (scientist) give a common height of 26
    and widths of 15, 20 and 18.

    `height_limit` is a SECOND bound, not the rule: the width budget
    decides the height, and this only stops a very short row from
    letting the figures overrun their own band.
    """
    dims = [(s.get_width(), s.get_height()) for s in sprites]
    common = min(max_width * h // w for w, h in dims)
    if height_limit is not None:
        common = min(common, height_limit)
    common = max(1, common)
    return common, [max(1, common * w // h) for w, h in dims]


class FigureSet:
    """One sprite per profession, in ECON order, scaled on demand.

    Scaled surfaces are cached per (max_width, height_limit): a full
    screen is seven rows of up to 42 slots, so scaling per slot would
    be some three hundred smoothscales a frame for a picture that
    does not change between them.
    """

    def __init__(self, sprites, names):
        self.sprites = tuple(sprites)
        self.names = tuple(names)
        self._cache = {}

    def sized(self, max_width, height_limit=None):
        """(common_height, one scaled Surface per zone)."""
        key = (max_width, height_limit)
        hit = self._cache.get(key)
        if hit is None:
            common, widths = figure_sizes(max_width, self.sprites,
                                          height_limit)
            hit = (common, tuple(
                pygame.transform.smoothscale(s, (w, common))
                for s, w in zip(self.sprites, widths)))
            self._cache[key] = hit
        return hit


def load_figures(res, cfg, screen="colony_summary"):
    """The set named in `cfg["figures"]`, or None if off or absent.

    None is the ordinary answer, not a failure: the mode is off by
    default, and even switched on it needs sprites that no clone of
    the repository has. `colonylist.render` draws squares when it is
    handed None, so the fallback needs no branch of its own anywhere
    else.

    A set that is PRESENT but inconsistent raises out of
    `check_crop_heights` rather than falling back — see there.
    """
    fig_cfg = (cfg or {}).get("figures") or {}
    if not fig_cfg.get("enabled"):
        return None
    names = fig_cfg.get("sprites") or []
    if len(names) != len(("food", "industry", "research")):
        log.warning("colony figures: need one sprite per ECON zone, "
                    "layout.json names %d", len(names))
        return None

    sprites = []
    for name in names:
        path = res.screen_file(screen, "assets", name)
        if not path:
            log.info("colony figures: %s not installed — the sprites are "
                     "cut from the player's own game and are not shipped "
                     "(decision 40); drawing squares", name)
            return None
        sprites.append(pygame.image.load(path).convert_alpha())

    check_crop_heights(sprites, names)
    return FigureSet(sprites, names)
