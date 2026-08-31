"""Reusable UI widgets for OrionLayer screens.

ListView   — scrollable table (Colony/Planet Summary, Reports,
             Officers, Load/Save)
TextInput  — single-line text entry (Ruler Name, Home Star Name,
             savegame names)

Both rasterize fonts at target pixel size and take their colors
from the skin's colors.json "widgets" section (with code
defaults) — see MODDING.md.
"""
from core.widgets.list_view import ListView
from core.widgets.text_input import TextInput

__all__ = ["ListView", "TextInput"]
