"""The battle's OPTIONS panel — open fix 68, "COPT" (work order 200).

    "COPT"  (`doc/ext_combat_options.patch`): written after CPOP while a
            battle is live. A version byte, then int16 the battle's serial
            and `MOX::_order_info_flag` (0 while the OPTIONS panel is up,
            combat1.cpp:618-624), then five bytes — the panel's lights in
            its own order (`Draw_Option_Panel_Lights_`,
            cmbtdrw1.cpp:1307-1322): the missile warning, fast animations,
            legal moves, shield arcs, the grid.

WHY: the five flags are MOX's, copied from the settings when a battle
starts (combinit.cpp:529-534) and written back only when it ends
(:1177-1178), so the settings record on the wire is stale for the whole
battle; whether the panel is up was nowhere on the wire.

Read WHOLE or left None (`core/colonyblocks.py`'s rule).
"""
import struct as _st

HEAD = "<BhhBBBBB"
HEAD_SIZE = _st.calcsize(HEAD)
#: the lights, top to bottom, as the panel and its hidden fields order them
FLAGS = ("missile_warning", "fast", "legal_moves", "shield_arcs", "grid")


def parse(gs, data, pos):
    """Read COPT at `pos` into `gs.combat_options` (None when absent or
    short). Returns the new position."""
    gs.combat_options = None
    if data[pos:pos + 4] != b"COPT" or pos + 4 + HEAD_SIZE > len(data):
        return pos
    version, serial, order_info, *flags = _st.unpack_from(HEAD, data, pos + 4)
    if version != 1:
        return pos
    gs.combat_options = {"serial": serial, "panel_up": order_info == 0,
                         **{k: v == 1 for k, v in zip(FLAGS, flags)}}
    return pos + 4 + HEAD_SIZE


def build(serial=1, panel_up=False, **flags):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"COPT" + _st.pack(HEAD, 1, serial, 0 if panel_up else 1,
                              *(1 if flags.get(k) else 0 for k in FLAGS))
