# Example Mod

Minimal demonstration of the OrionLayer mod system.

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
