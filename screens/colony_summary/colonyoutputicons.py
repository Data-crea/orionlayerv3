"""The output panel's row icons: four resources and two morale masks.

**A DEVIATION, AND DECISION 56 SAYS WHICH KIND** (decision 56 in
`doc/v3_fundament.md`, under Sizing and artwork). The original's scan
box draws its production rows and morale as COUNTING sprites
(`Draw_Colony_Wee_Prod_` and `Draw_Info_Wee_Morale_`, colsum.cpp:1172
and :1176) and never puts a glyph beside a word; this panel prints a
label and a number instead (`output._deviation_note` (1) and (2)), and
these icons are row LABELS on that label. The shapes are Data's
redrawings of the original's own unit sprites and masks, which is why
they read as MOO2 — and it is also exactly why this is marked: a
borrowed shape in a place the original never puts it.

**DERIVED, NOT COMMITTED.** `tools/make_output_icons.py` cuts them out
of Data's AI-generated sheets under `assets/_src/output/` and
`tools/setup.py` runs it after a clone (decision 40). Without them the
panel draws what it drew before — no icon, and the labels at the
padding — which is a state of the feature and not an error.

**THE MASTER SIZE IS `output.icon_size`, ONE NUMBER WITH TWO READERS.**
The tool writes it and this loader refuses anything else, the way
`colonyplanets.MASTER_SIZE` is used — except that this number is ours
and lives in `layout.json` with its source beside it, because it was
chosen from the panel's own row height and not from the art.

**SCALED LIKE A FIGURE, NEVER SMOOTHED.** The one Lanczos resample is
the tool's, from the source to the master. From the master every
window size is nearest neighbour and the stored layout scale, never a
font size (the help popup's double scale, fundament "Scaling twice").
"""
import collections
import logging
import os

log = logging.getLogger("output_icons")

#: Where the tool writes and a mod overrides, per screen.
ICON_DIR = os.path.join("assets", "output")

#: The file names, which are also what `colonyoutput.visible_rows`
#: hands the renderer. The resource names are the panel's own row
#: ids; the two morale names are what `colonyrows.morale_icon` answers.
RESOURCE_NAMES = ("food", "industry", "research", "bc")
MORALE_NAMES = ("morale_normal", "morale_low")
NAMES = RESOURCE_NAMES + MORALE_NAMES

#: One size is live per window; a resize makes a second.
SET_CACHE = 2


def master_size(cfg):
    """`output.icon_size`, or 0 when the key is absent — no icons."""
    size = cfg.get("icon_size", 0)
    return size if isinstance(size, int) and size > 0 else 0


def icon_px(cfg, scale):
    """The drawn side in device px: the master times the stored scale.

    Rounded DOWN so it can never exceed the row it sits in — the row
    height is built from `int()` terms of the same scale, and a smoke
    check asserts the icon fits it at every resolution the panel is
    declared for.
    """
    size = master_size(cfg)
    return max(1, int(size * scale)) if size else 0


class IconSet:
    """The six icons at one pixel size, or a stated absence.

    `state` is "ok", "partial" or "missing" — the figure loader's
    three words, and a partial set draws the icons it has.
    """

    def __init__(self, resources, master, size, root=None):
        self.master = int(master)
        self.size = int(size)
        self.state = "missing"
        self.icons = {}
        self.refused = []
        if self.master > 0 and self.size > 0:
            self._load(resources, root)

    def _load(self, resources, root):
        import pygame
        for name in NAMES:
            for base in ([root] if root else resources.roots()):
                path = os.path.join(base, "screens", "colony_summary",
                                    ICON_DIR, f"{name}.png")
                if not os.path.exists(path):
                    continue
                try:
                    image = pygame.image.load(path)
                except pygame.error as err:
                    log.warning("output icons: %s will not load (%s)",
                                path, err)
                    self.refused.append(path)
                    break
                if image.get_size() != (self.master, self.master):
                    log.warning(
                        "output icons: %s is %dx%d and output.icon_size "
                        "says %d — refused, the row keeps its label only",
                        path, image.get_size()[0], image.get_size()[1],
                        self.master)
                    self.refused.append(path)
                    break
                image = image.convert_alpha() if pygame.display.get_init() \
                    else image
                self.icons[name] = image if self.size == self.master \
                    else pygame.transform.scale(image, (self.size, self.size))
                break
        if not self.icons:
            log.info("output icons: none of %d found under %s — run "
                     "`python tools/make_output_icons.py`",
                     len(NAMES), ICON_DIR)
            return
        self.state = "ok" if len(self.icons) == len(NAMES) else "partial"

    def get(self, name):
        return self.icons.get(name) if name else None


def set_for(screen, cfg):
    """The icon set for this window's scale, cached per App."""
    master = master_size(cfg)
    size = icon_px(cfg, screen.layout.scale)
    if not size:
        return None
    cache = getattr(screen.app, "output_icon_sets", None)
    if cache is None:
        cache = collections.OrderedDict()
        screen.app.output_icon_sets = cache
    key = (master, size)
    if key in cache:
        cache.move_to_end(key)
    else:
        cache[key] = IconSet(screen.app.res, master, size)
        while len(cache) > SET_CACHE:
            cache.popitem(last=False)
    return cache[key]
