"""The tables of the original's beams — work order 199 C2, split out of
`cbbeam` (the line guideline): `angle.cpp`'s arc-tangent, `bolt.cpp`'s
wide-bolt strands, `Set_Beam_Colors_`' ramps (beams.cpp:27-54, 2481-2564)
and `Build_Steve_Stuff_Struct_For_Weapon_` (beams.cpp:1848-2062). Every
value is the source's; `cbbeam` draws with them (TRANSCRIPTION `beam_bolt`
there).
"""
#: angle.cpp:5-14
ATAN = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8, 9, 9,
        10, 10, 11, 11, 11, 12, 12, 13, 13, 14, 14, 14, 15, 15, 16, 16, 16,
        17, 17, 18, 18, 18, 19, 19, 20, 20, 20, 21, 21, 22, 22, 22, 23, 23,
        24, 24, 24, 25, 25, 25, 26, 26, 26, 27, 27, 27, 28, 28, 29, 29, 29,
        30, 30, 30, 31, 31, 31, 32, 32, 32, 32, 33, 33, 33, 34, 34, 34, 35,
        35, 35, 36, 36, 36, 36, 37, 37, 37, 38, 38, 38, 38, 39, 39, 39, 39,
        40, 40, 40, 40, 41, 41, 41, 41, 42, 42, 42, 42, 43, 43, 43, 43, 44,
        44, 44, 44, 45)
#: bolt.cpp:4-40, twelve per direction
HEAD_WIDE = (
    0, -1, 0, 1, -1, -1, -1, 1, -1, -2, -1, 2, -1, -1, 0, 1, -1, 0, -1, 1,
    -2, -1, -1, 2, -1, 0, 1, 0, -1, 0, 0, 1, 1, 1, -1, -1, -1, 0, 1, 1, -1,
    1, 0, 1, -2, 1, 1, 2, -1, 0, 0, 1, -1, 1, 1, 1, -2, 1, 2, 1, 1, 0, -1, 1,
    1, 1, 0, 1, 2, 1, -1, 2, 1, 0, -1, 0, 1, 0, 0, 1, -1, 1, 1, -1, 1, -1, 0,
    1, 1, 0, 1, 1, 2, -1, 1, 2, 0, -1, 0, 1, 1, -1, 1, 1, 1, -2, 1, 2, 1, 1,
    0, -1, 1, 0, 1, -1, 2, 1, 1, -2, 1, 0, -1, 0, 1, 0, 0, -1, -1, -1, 1, 1,
    1, 0, -1, -1, 1, -1, 0, -1, 2, -1, -1, -2, 1, 0, -1, -1, -1, -1, 1, -1,
    2, -1, -1, -2, -1, 0, 1, -1, -1, -1, 0, -1, -2, -1, 1, -2, -1, 0, 1, 0,
    -1, 0, 0, -1, 1, -1, -1, 1, -1, 1, 0, -1, -1, 0, -1, -1, -2, 1, -1, -2)
TAIL_WIDE = (
    0, 1, 0, -1, 1, -1, 1, 1, 1, 2, 1, -2, 0, -1, 1, 1, 1, 0, 1, -1, 1, -2,
    2, 1, -1, 0, 1, 0, 1, 0, 0, -1, 1, 1, -1, -1, -1, -1, 1, 0, 1, -1, 0, -1,
    -1, -2, 2, -1, -1, -1, 1, 0, -1, -1, 1, -1, -1, -2, 2, -1, 1, -1, -1, 0,
    -1, -1, 0, -1, 1, -2, -2, -1, 1, 0, -1, 0, -1, 0, 0, -1, -1, 1, 1, -1, 0,
    -1, -1, 1, -1, 0, -1, -1, -1, -2, -2, 1, 0, 1, 0, -1, -1, -1, -1, 1, -1,
    2, -1, -2, 0, 1, -1, -1, -1, 0, -1, 1, -1, 2, -2, -1, 1, 0, -1, 0, -1, 0,
    0, 1, -1, -1, 1, 1, 1, 1, -1, 0, -1, 1, 0, 1, 1, 2, -2, 1, 0, 1, -1, 0,
    -1, 1, 1, 1, 2, 1, -2, 1, -1, 1, 1, 0, 1, 1, 0, 1, -1, 2, 2, 1, -1, 0, 1,
    0, 1, 0, 0, 1, 1, -1, -1, 1, 0, 1, 1, -1, 1, 0, 1, 1, 1, 2, 2, -1)
#: beams.cpp:27-54
LOW_RAMP = (7, 25, 35, 45, 55, 70, 89)
CROSS = {0: (80, 60, 40, 20), 1: (90, 80, 60, 40), 2: (95, 85, 70, 50)}
SATURATED = {0: (110, 125, 155), 1: (115, 140, 200), 2: (150, 200, 300)}
#: beams.cpp:19, 23
SHIELD_DIAMETERS = (25, 46, 63, 76)
LONG_LINE = 1024                    # Plasma_Line_'s index mask, 0x3FF + 1

# ── the weapons: Build_Steve_Stuff_Struct_For_Weapon_ (:1848-2062) ────
# (c1, c2, intensity, style, length, step, wide bonus); weapon ids are
# orion2_consts' WEAPON_* (the same numbers `core/shipparts` names)
_C = {1: (0x59, 0x6b, 0xc3, 0xda, 0xfc, 0xff),
      2: (0x59, 0x67, 0x6c, 0xb2, 0xc8, 0xc8),
      3: (0xc8, 0x14, 0x20, 0xff, 0x50, 0x0a),
      4: (0x5e, 0x70, 0xcd, 0xba, 0xdd, 0xff),
      5: (0xd2, 0x46, 0x00, 0xff, 0xa2, 0x00),
      6: (0x94, 0x9b, 0x49, 0xfe, 0xfe, 0x94),
      7: (0x44, 0x98, 0x8f, 0x93, 0xff, 0xff),
      8: (0x92, 0x53, 0xba, 0xff, 0xb8, 0xff),
      9: (0xa9, 0x2b, 0x00, 0xff, 0xa6, 0x60),
      10: (0x6b, 0xa2, 0x16, 0xf2, 0xff, 0x35),
      11: (0xc9, 0x53, 0xc4, 0xff, 0xb8, 0xff),
      12: (0xd2, 0x53, 0x00, 0xff, 0xff, 0x52)}
_C[41], _C[42] = _C[9], _C[11]       # phasor eye, crystal ray
CONTINUOUS, ENVELOPING = 0x10, 0x100


def fx(weapon, specials=0):
    """The weapon's visual record, or None for a weapon the table does not
    carry (beams.cpp:1848-2062; :1938 and :1947 for fusion's two flags)."""
    w, cont, env = int(weapon), bool(specials & CONTINUOUS), \
        bool(specials & ENVELOPING)
    if w not in _C:
        return None
    if w in (1, 2):
        row = (1, 1, 4 if w == 1 else 6, 20, 0)
    elif w in (3, 9, 41):
        row = (1, 2 if cont else 0, 200, 50, 0)
    elif w == 4:
        row = (0, 2 if cont else 0, 200, 50, 0)
    elif w == 5:
        row = (1, 3, 100, 25, 1) if cont and env else \
            (1, 2, 120, 30, 0) if cont else \
            (1, 1, 100, 25, 1) if env else (1, 1, 120, 30, 0)
    elif w == 6:
        row = (2, 2 if cont else 1, 200, 50, 0)
    elif w == 7:
        row = (2, 3, 200, 50, 0)
    elif w == 8:
        row = (1, 2 if cont else 1, 200, 50, 0)
    elif w == 10:
        row = (1, 1, 40, 30, 0)
    elif w in (11, 42):
        row = (1, 3, 200, 50, 0)
    else:                               # 12, plasma cannon
        row = (2, 3 if cont else 1, 100, 30, 1)
    intensity, style, length, step, bonus = row
    c = _C[w]
    return {"c1": c[:3], "c2": c[3:], "intensity": intensity,
            "style": style, "length": length, "step": step, "bonus": bonus}


def colours(f):
    """`Set_Beam_Colors_`: the sixteen colours, as the VGA shows them (6-bit
    values times four, as every palette here)."""
    (r1, g1, b1), (r2, g2, b2), k = f["c1"], f["c2"], f["intensity"]
    out = [(r1 * v // 100, g1 * v // 100, b1 * v // 100) for v in LOW_RAMP]
    out.append((r1, g1, b1))
    cross = 115
    for wgt in CROSS[k]:
        s, inv = wgt * cross, 100 - wgt
        out.append(tuple(min(255, (a * s // 100 + b * inv) // 100)
                         for a, b in ((r1, r2), (g1, g2), (b1, b2))))
        cross += 15
    out.append((r2, g2, b2))
    for wgt in SATURATED[k]:
        out.append(tuple(min(255, c * wgt // 100) for c in (r2, g2, b2)))
    return [tuple((c // 4) * 4 for c in rgb) for rgb in out]


def get_angle(dx, dy):
    if dx == 0:
        return 270 if dy < 0 else 90 if dy > 0 else 0
    if dy == 0:
        return 180 if dx < 0 else 0
    if dx < 0:
        nx, ny, q = (-dx, -dy, 180) if dy < 0 else (dy, -dx, 90)
    else:
        nx, ny, q = (dx, dy, 0) if dy > 0 else (-dy, dx, 270)
    if ny == nx:
        a = 45
    elif ny > nx:
        a = 90 - ATAN[(nx << 7) // ny]
    else:
        a = ATAN[(ny << 7) // nx]
    a += q
    return 0 if a == 360 else a
