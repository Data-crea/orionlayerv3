"""A screen's extracted MOO2 artwork, read through the resolver — work
order 199 D (195 §7 and §11.1).

The extractors write raw LBX blobs, a palette and a manifest into
`screens/<screen>/assets/gamedata/` (decisions 38, 40, 42); the screens
decode them at load. Until 199 the Fleets, Leaders, Races, Ship Designer and
Audience loaders read that folder by a path of their own, so neither a mod
nor the player's folder could reach their pictures (195 §2, sites 27-31).

`Source` is the one way they read it now, the way `screens/info/infoart.py`
and the battle's `cbart` already did:

  * every file is `Resources.resolve`d at its tree path — the player's
    folder (`files/<tree path>`), a developer mod, the project — unless a
    FOLDER is given, which is then read alone (the checks' way);
  * before a stored drawing is decoded, a PNG painted for it is looked for
    beside it: `<group>/<entry>_<frame>.png` for `<group>/<entry>.bin`,
    resolved the same way (a slot, `core.usermod.SLOTS`). It is used AS
    PAINTED — no palette, no ship ramp: a modder paints the colours they
    want. HD EXTENSION `painted_png` — the original has no such route.
"""
import os

import pygame

from core.config import BASE_DIR


class Source:
    def __init__(self, rel, folder=None):
        self.rel = rel.replace(os.sep, "/")
        self.folder = folder

    @property
    def where(self):
        """For a log line: the folder read, or the tree path resolved."""
        return self.folder or self.rel

    def path(self, *parts):
        """The file to read for `parts` under the artwork folder. Absent
        everywhere, the project's own path — so the caller's open fails
        and says which file."""
        if self.folder is not None:
            return os.path.join(self.folder, *parts)
        from core import resources
        found = resources.res.resolve("/".join((self.rel,) + parts))
        return found or os.path.join(BASE_DIR, *self.rel.split("/"), *parts)

    def read(self, *parts):
        with open(self.path(*parts), "rb") as fh:
            return fh.read()

    def painted(self, *parts, frame=0):
        """The PNG a mod painted for the drawing `parts` (`….bin`) at
        `frame`, or None."""
        stem = os.path.splitext(parts[-1])[0]
        path = self.path(*parts[:-1], f"{stem}_{int(frame)}.png")
        if not os.path.isfile(path):
            return None
        try:
            img = pygame.image.load(path)
        except (pygame.error, OSError):
            return None
        return img.convert_alpha() if pygame.display.get_surface() else img
