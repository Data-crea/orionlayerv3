"""Select mode's drawing — one binding of the shared panel renderer.

The drawing is `core.researchpanel`, which both research modes use;
this module exists so the screen folder keeps its own entry point and
so the marking below has a home beside the screen that carries it.

THE ORIGINAL SQUEEZES, HD SHRINKS. `BILL::Squeeze_Print_`
(tech.cpp:700, :735) compresses the glyphs of a name to fit its width
rather than clipping it. An HD font cannot be squeezed, so the size
comes down until the string fits — the same intent, and the nearest
thing available. DEVIATION, in `screen.py`'s marked list.

THE SECOND COLOUR IS UNREACHABLE HERE, and that is not an omission.
`TECH::_tech_color[2]` marks the field the player is already
researching (tech.cpp:686-696), and `Tech_Select_` zeroes
`current_research_field` before this list is built (tech.cpp:104-105) —
so select mode passes `current=(0, 0)` and every row is drawn in the
first colour. Change mode is where that colour has something to mark.
"""
from core.researchpanel import MIN_FONT, col, draw   # noqa: F401
