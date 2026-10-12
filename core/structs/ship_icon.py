"""s_ship_icon — VERIFIED spec (12 bytes, six int16).

Confirmed by live testing: stack_slot drives galaxy-map icon
placement (slot 0 right of star, 1-4 left, 5 in transit),
x/y match ship positions for slot 5.
"""
from core.structs import Spec

SIZE = 12

SPEC = Spec("s_ship_icon", SIZE, [
    ("stack_id",   0, "i16"),
    ("node_idx",   2, "i16"),
    ("star_idx",   4, "i16"),
    ("stack_slot", 6, "i16"),
    ("x",          8, "i16"),
    ("y",         10, "i16"),
], verified=True)


def parse(raw):
    return SPEC.parse(raw)


def parse_all(raw_list):
    return SPEC.parse_all(raw_list)
