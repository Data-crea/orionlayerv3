"""Which pictures of the tree the mod template lists — work order 199 D.

The player's folder replaces any picture through `files/<tree path>`
(`core.usermod`, decision 72); the template's `NAMES.txt` lists the ones a
screen asks for, by name only, because they are MOO2's (195 §11.1). Until
199 that list was hand-kept and unchecked, so a picture added to the tree
was replaceable but missing from it. Now every picture under `assets/` and
`screens/*/assets/` is held by the smoke suite to exactly one rule here:
listed (`GAME_ART`) or not, with the reason (`NOT_LISTED`).
"""
import fnmatch
import os

#: The groups of pictures `files/` replaces that the screens are KNOWN
#: to ask for through `Resources.resolve` or `Resources.roots` (a trace of
#: every screen's render, work order 173; the colony screens' groups and
#: the cursor and help backdrop added by work order 199 D). Globs relative
#: to the tree. Their pictures are MOO2's or derived from them — or of an
#: origin not on record, which is treated the same: the template lists the
#: names only.
GAME_ART = ("assets/shared/background_cockpit.png",
            "assets/shared/cursor.png",
            "assets/shared/figures/*.png",
            "screens/colony_summary/assets/output/*.png",
            "screens/colony_summary/assets/planets/*.png",
            "screens/colony_summary/assets/surfaces/*.png",
            "screens/custom_race/assets/*.png",
            "screens/empire_identity/assets/*.png",
            "screens/galaxy_map/assets/black_hole.png",
            "screens/galaxy_map/assets/icons/*.png",
            "screens/galaxy_map/assets/nebula/*.png",
            "screens/galaxy_map/assets/ships/*/*.png",
            "screens/galaxy_map/assets/stars/*/*.png",
            "screens/main_menu/assets/logo.png",
            "screens/new_game/assets/*/*.png",
            "screens/select_race/assets/portraits/*.*")

#: EVERY OTHER PICTURE IN THE TREE, and why `files/` does not list it
#: (work order 199 D, 195 §11.1: the list was hand-kept and unchecked, so a
#: picture added to the tree was replaceable but missing from it). A check
#: holds every picture under `assets/` and `screens/*/assets/` to exactly
#: one glob here or in `GAME_ART`; the extracted artwork's `gamedata/` is
#: the painted-PNG slot (`SLOTS`) and listed by the template on its own.
NOT_LISTED = {
    "assets/shared/backgrounds/*.png":
        "named by background.png and backgrounds/<screen>.png",
    "assets/shared/hud/cut/*.png": "named by hud/<piece>.png",
    "assets/shared/banner/*.png":
        "a whole directory, replaced through mods/ only (decision 17)",
    "assets/shared/hud/galaxy_hud.png":
        "the sheet the HUD pieces are cut from (tools/hud_cut.py)",
    "screens/galaxy_map/assets/_black_hole_src.png":
        "the source of black_hole.png (tools/make_black_hole_master.py)",
    # Work order 205 moved the pictures nothing loaded — the galaxy map's
    # old floor, Select Race's banners and planet, four larger portraits
    # — into the developer store (Data: kept for the Select Race
    # redesign); a player's tree no longer carries them, so they need no
    # rule here.
    "screens/new_game/assets/background.png":
        "the cut-outs' geometry, never drawn (work order 199 D3)",
    "*/_src/*": "the sources an extractor or a tool works from",
    "*_ref/*": "an extraction's reference sheets, loaded by nothing",
}
#: Checked before the rest: a source is never a picture the game draws.
SOURCES = ("*/_src/*", "*_ref/*")


def art_class(rel):
    """For a picture's tree path: "game" (listed by name under `files/`),
    the reason it is not listed, or None when no rule names it — which the
    smoke suite refuses. Exactly one rule must match."""
    rel = rel.replace(os.sep, "/")
    for glob in SOURCES:
        if fnmatch.fnmatchcase(rel, glob):
            return NOT_LISTED[glob]
    hits = [g for g in GAME_ART if fnmatch.fnmatchcase(rel, g)] + \
        [g for g in NOT_LISTED if g not in SOURCES and
         fnmatch.fnmatchcase(rel, g)]
    if len(hits) != 1:
        return None
    return "game" if hits[0] in GAME_ART else NOT_LISTED[hits[0]]
