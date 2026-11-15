"""A monster's death — work order 393 ([combat.art_not_drawn]).

TRANSCRIPTION `monster_death`: `Destroy_Ship_FX_` (cmbtspec.cpp:1206-1433) takes
a different road for a unit whose `previous_owner` is 10 or more — a
monster, not a ship of a player, the Antarans (8) or the Guardian (9): no
explosion (:1224 `previous_owner < 10` is the ship's road), the monster's own death picture, one frame a tick for 16 ticks
(`for (i = 0; i < 16; i += step)`, :1349; `Release_Time_(1)`, :1425; two
ticks a frame under FAST ANIMATIONS, :1335-1339: `step` = 2 skips every
second frame, 8 frames in all) where its standing picture
was (`Get_Draw_Ship_Offsets_`, :1324-1326, the same offsets `Draw_Ship_`
uses). The unit is destroyed before the first frame (:1330), so it is not
drawn under the picture. The picture is CMBTSFX entry 69-78 (the file is
`E_Strings(0xE0)`, :1358 — the string table's 224 is CMBTSFX.LBX,
orion2_str.h:216), by the monster's player and, for a monster of size class
2 (the "large" pictures), the second of the pair:

    player 10 (Amoeba)   71 huge     72 large     (:1361-1364)
    player 11 (Crystal)  73 huge     74 large     (:1365-1368)
    player 12 (Dragon)   69 titan    70 large     (:1369-1372)
    player 13 (Eel)      75 huge     76 large     (:1373-1376)
    player 14 (Hydra)    77 titan    78 large     (:1377-1380)

Each entry holds 80 frames: the five stored facings of `Draw_Ship_` times 16
ticks, frame `stored * 16 + i`, the other eleven facings mirrored and flipped
as the standing monster's (:1393-1414; `cbart.stored_facing`).

Two sources hold the table (P602): the C++ above, and the pictures — frame 0
of each entry is the standing monster's frame 0 of the picture named in the
right-hand column (`tools/smoke_suite/090zzkz`'s fixture-free half reads the
engine's side; the pixel comparison was made once on the extracted files:
entry 69 against MONSTER 10, 70 against 22, 71 against 8, 72 against 20, 73
against 9, 74 against 21, 75 against 11, 76 against 23, 78 against 24; 77
against MONSTER 12 is the weakest match, the pose differs).

UNVERIFIED: live in a battle (offline only, work order 393).
UNVERIFIED `monster_death_colours`: the death is drawn in the standing
monster's own 32 colours (`CombatArt.monster_ramp`); the original recolours
the picture into the defender's band when the monster defends
(`Replace_Color_Range_`, :1416-1418), which the standing drawing's own remap
mirrors in HD's one ramp.
OMISSION `monster_death_sound`: the cry (SOUND 62-66, :1361-1380, played at :1390) comes from
the engine as a `sound` event (work order 212 C), not from here.
DEVIATION `monster_death_state`: the original's monster road ignores the
death state (:1224 tests only `previous_owner`); HD takes the same
road for every state of a monster.
"""
from . import cbart, cbdraw

#: monster player -> (entry, entry of size class 2) (cmbtspec.cpp:1361-1380).
ENTRY = {10: (71, 72), 11: (73, 74), 12: (69, 70), 13: (75, 76),
         14: (77, 78)}
LARGE = 2                   # SHIP_SIZE_LARGE, the "large" pictures' class
FRAMES = 16                 # `i < 16`, :1349
STORED = 5                  # stored facings, 16 ticks each: 80 frames


def entry_of(u):
    """CMBTSFX entry of unit `u`'s death, or None for a unit the monster
    road does not take (`previous_owner` below 10) or one it has no picture
    for (the original's `default: entry_id = 0`, :1381-1382, draws entry 0 — the
    small tractor, a bug, not transcribed: HD plays the ship's death)."""
    pair = ENTRY.get(int(u.get("previous_owner", 0)))
    if pair is None:
        return None
    return pair[1] if int(u["size_class"]) == LARGE else pair[0]


def plan(u, art):
    """`{"entry", "frames", "delay"}` for `cbpace.sfx_times`, or None —
    not a monster, or the player's art lacks the entry (the ship's death
    plays then)."""
    entry = entry_of(u)
    if entry is None or art is None or \
            art.frame_count("cmbtsfx", entry) < STORED * FRAMES:
        return None
    return {"entry": entry, "frames": FRAMES, "delay": 0.0}


def picture(art, colours, u, entry, i):
    """Frame `i` (0-15) of the death for unit `u`'s facing."""
    stored, mirror, flip = cbart.stored_facing(u["facing_dir"])
    return art.surface("cmbtsfx", entry, stored * FRAMES + i,
                       art.monster_ramp(cbdraw.unit_colour(colours, u)),
                       mirror, flip)


def draw(surface, cam, art, colours, u, p, frame, cache):
    """The death's frame `frame` where the standing picture was; the unit
    itself is gone from the first (:1330)."""
    if u is None or frame is None:
        return
    u["unit_status"] = 5
    pic = picture(art, colours, u, p["entry"], frame)
    if pic is None:
        return
    ox, oy = cbdraw.sprite_origin(u)
    surface.blit(cbdraw.scaled(pic, cam.scale, cache), cam.to_window(ox, oy))
