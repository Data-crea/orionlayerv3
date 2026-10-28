# Example Mod

Minimal demonstration of a mod **inside the tree** (`mods/<name>/`): the
kind for data, texts, layouts, skins and new screens, which mirrors
OrionLayer's own folder tree.

**Changing a picture or a text? Use your mod folder instead** (one folder
outside the program, named by subject: `buildings/`, `ships/`, ...; see
"The easy way" in `MODDING.md`). Pictures can go in either, the mod folder
is the simpler one.

This mod overrides a single file: the main menu credits text.
The folder structure mirrors the project — that's the whole trick:

    mods/example_mod/
    ├── mod.json                              metadata
    └── screens/main_menu/assets/credits.txt  overrides the base file

## Activate

In `settings.json`:

    "active_mods": ["example_mod"]

Start OrionLayer — the main menu credit scroll now shows the
modded text. Remove the entry to deactivate.

See MODDING.md in the project root for the full guide.
