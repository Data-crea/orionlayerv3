"""The build list's word colours — HD EXTENSION `build_colours` (Data,
1 November 2026, from his mockup of the screen).

Measured off the mockup's words (the median of their bright pixels), not
guessed: the product's name and the chosen list row in orange, the
summary's lines in gold, the table's labels in a deeper orange over white
values, a design's weapons and specials in light grey, the other list rows
grey. Fixed colours, as the mockup has them: they do not follow the frame
colour. A skin's `colors.json` may set each under `build_queue`.
"""
from core import palette

TITLE = palette.col("build_queue", "title", (247, 164, 2))
SELECTED = palette.col("build_queue", "selected", (247, 164, 2))
INFO = palette.col("build_queue", "info", (229, 193, 86))
LABEL = palette.col("build_queue", "label", (234, 153, 4))
VALUE = palette.col("build_queue", "value", (240, 240, 240))
ITEM = palette.col("build_queue", "item", (225, 225, 225))
ROW = palette.col("build_queue", "row", (236, 236, 236))
QUEUE = palette.col("build_queue", "queue", (233, 233, 233))
#: The thin rule under the product's name.
RULE = palette.col("build_queue", "rule", (122, 112, 92))
