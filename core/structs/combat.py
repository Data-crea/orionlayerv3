"""The records the battle's blocks and FMOV carry raw — decision 97, work order 243.

Moved here from `core/combatblocks.py` and `core/moveblocks.py`, which kept
their own offset tables, so that every byte position of an engine record is
in `core/structs/` and follows the engine's LAYOUT (`layout.py`):

  "CMBT" (open fix 53)  each unit is `s_combat_data` WITHOUT its picture
                        pointer: the bytes before `ship_image_seg` and from
                        `drive_max_hits` on, joined (the old engine: 309 of
                        317 bytes, orion2.h:595-658; after the pointer every
                        offset is the struct's minus 8). `UNIT_SPEC` cuts
                        the engine's layout the same way.
  "CMSL" (open fix 55)  each live `s_missile`, whole (26 bytes).
  "FMOV" (open fix 48)  `s_ship_move_info` per star, whole (14 bytes).

The offsets below are the old engine's (`orionlayer-local`), where the
blocks were cut and checked; the field names are the engine's.
"""
from core.structs import Spec
from core.structs import layout as _layout


class SplicedSpec(Spec):
    """A record sent without the bytes from member `cut[0]` up to member
    `cut[1]` (a pointer the client has no use for)."""

    def __init__(self, name, size, fields, cut, **kw):
        super().__init__(name, size, fields, **kw)
        self.cut = cut

    def _gap(self):
        start = _layout.member(self.name, self.cut[0])
        end = _layout.member(self.name, self.cut[1])
        return (start.offset, end.offset - start.offset) if start and end \
            else (None, 0)

    def resolved(self):
        size, fields = super().resolved()
        if self._resolved[0] is None:
            return size, fields
        at, gap = self._gap()
        return size - gap, fields

    def _engine_field(self, name, kind):
        offset, kind = super()._engine_field(name, kind)
        at, gap = self._gap()
        if offset is not None and at is not None and offset >= at:
            offset -= gap
        return offset, kind

    def offset_of(self, name, default):
        """A member's offset in the record AS SENT."""
        if not _layout.has(self.name):
            return default
        m = _layout.member(self.name, name)
        if m is None:
            return default
        at, gap = self._gap()
        return m.offset - gap if at is not None and m.offset >= at \
            else m.offset


#: CMBT's unit record, field for field (the old engine's wire offsets).
UNIT_SPEC = SplicedSpec("s_combat_data", 309, [
    ("name", 0, "str30"),
    ("ship_idx", 30, "i16"), ("owner", 32, "i8"), ("x", 33, "i8"),
    ("y", 34, "i8"), ("facing_dir", 35, "i8"), ("unit_status", 36, "i8"),
    ("size_class", 37, "i8"), ("shield_type", 38, "i8"),
    ("shield_arc_max", 39, "i16"), ("shield_arc_current", 41, "i16[4]"),
    ("ftl_type", 49, "i8"), ("computer_type", 50, "i8"),
    ("armor_type", 51, "i8"), ("tac_val_attack", 52, "i16"),
    ("tac_val_defense", 54, "i16"), ("tac_val_evade", 56, "i16"),
    ("combat_speed_base", 58, "i8"), ("current_speed", 59, "i16"),
    ("movement_left", 61, "i16"), ("special_status_flag", 64, "i8"),
    ("special_status_timer", 65, "u8"),
    # work order 210 C2: the tractor's target, 0xFF none (orion2.h:619,
    # set by `Tractor_Beam_`, cmbtspec.cpp:681)
    ("special_cooldown", 66, "u8"),
    # work order 199 C3: orion2.h's order between the verified neighbours
    # (64 special_status_flag ... 72, 74, 75 ... 82 the weapon slots)
    ("plasma_web_damage", 67, "i16"), ("reflected_damage_pool", 69, "i16"),
    ("special_device_flags", 76, "u8[5]"),
    ("special_device_damage_flags", 178, "u8[5]"),
    ("combat_status_flags", 72, "u8"),
    ("stasis_source_idx", 74, "u8"), ("is_retreating", 75, "i8"),
    ("structure_max", 170, "i16"), ("crew_quality", 172, "i8"),
    ("officer_idx", 173, "i16"), ("marine_count", 175, "u8"),
    ("is_captured", 176, "i8"), ("weapon_ready_flags", 184, "u8[8]"),
    ("structure_damage", 192, "i16"), ("armor_remaining", 194, "i16"),
    ("picture_num", 196, "i16"),
    ("drive_max_hits", 198, "i16"), ("computer_max_hits", 200, "i16"),
    # work order 256: the internal systems' hits, for the status picture's
    # internals bar (`Max_Total_Internal_Space_`, cmbtfir2.cpp:517-534)
    ("weapon_total_hits", 202, "i16[8]"), ("special_device_hits", 234, "i16[8]"),
    ("shield_max_hits", 250, "i16"), ("drive_current_hits", 252, "i16"),
    ("computer_current_hits", 254, "i16"),
    ("weapon_hits", 256, "i16[8]"), ("special_hits", 288, "i16[8]"),
    ("shield_current_hits", 304, "i16"),
    ("black_hole_flag", 306, "i8"), ("black_hole_source_idx", 307, "u8"),
    ("previous_owner", 308, "u8"),
], cut=("ship_image_seg", "drive_max_hits"), verified=True)

#: `s_combat_weapon_slot` x 8 at `weapons` (82), 11 bytes each (sizes.h).
WEAPONS_OFFSET, WEAPON_SLOTS = 82, 8
WEAPON_SPEC = Spec("s_combat_weapon_slot", 11, [
    ("weapon_id", 0, "i16"), ("count", 2, "i8"), ("arc", 3, "i8"),
    ("specials", 4, "u16"), ("ammo", 6, "i16"), ("active", 8, "i8"),
    ("shots_left", 9, "i8"), ("status", 10, "u8"),
], verified=True)


def weapon_slots(raw):
    """The eight weapon slots of one CMBT unit record, as dicts."""
    base = UNIT_SPEC.offset_of("weapons", WEAPONS_OFFSET)
    size = _layout.size("s_combat_weapon_slot", WEAPON_SPEC.size)
    return [dict(WEAPON_SPEC.parse(raw[base + k * size:
                                       base + (k + 1) * size])._values)
            for k in range(WEAPON_SLOTS)]


#: `s_missile` (orion2.h:1249-1266), 0x1A bytes — sizes.h asserts it.
#: `is_anti_missile_rocket` is v2's `target_is_missile` (`layout.ALIASES`).
MISSILE_SPEC = Spec("s_missile", 26, [
    ("type", 0, "i16"), ("owner", 2, "i16"), ("source_unit_idx", 4, "i16"),
    ("target_unit_idx", 6, "i16"), ("is_anti_missile_rocket", 8, "i8"),
    ("x", 9, "i16"), ("y", 11, "i16"), ("hits_taken", 13, "i16"),
    ("quantity", 15, "i16"), ("specials", 17, "u16"),
    ("travel_dist", 19, "i16"), ("facing_dir", 21, "i8"), ("speed", 22, "u8"),
    ("fighter_count", 23, "i8"), ("pad", 24, "i8"), ("is_active", 25, "i8"),
], verified=True)

#: s_ship_move_info, field for field (orion2.h:2921-2936), 14 bytes.
MOVE_INFO_SPEC = Spec("s_ship_move_info", 14, [
    ("blackhole_blocks", 0, "i8"), ("insufficient_fuel", 1, "i8"),
    ("immobile", 2, "i8"), ("pad", 3, "i8"), ("turns_left", 4, "u8"),
    ("moving", 5, "i8"), ("out_of_range", 6, "i8"), ("has_navigator", 7, "i8"),
    ("traveling_speed", 8, "i8"), ("parsecs", 9, "u8"),
    ("uses_wormhole", 10, "i8"), ("has_jumpgate_route", 11, "i8"),
    ("has_stargate_route", 12, "i8"), ("hyperspace_flux", 13, "i8"),
], verified=True)


def record(spec, raw):
    """One record as a plain dict of its fields (the blocks' form)."""
    return dict(spec.parse(raw)._values)
