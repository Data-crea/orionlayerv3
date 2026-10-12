"""Reusable UI widgets for OrionLayer screens.

TextInput  — single-line text entry (Ruler Name, Home Star Name,
             savegame names)

It rasterizes fonts at target pixel size and takes its colors from the
skin's colors.json "widgets" section (with code defaults) — see
MODDING.md. (`ListView`, a scrollable table no screen used, went in
work order 228.)
"""
from core.widgets.text_input import TextInput

__all__ = ["TextInput"]
