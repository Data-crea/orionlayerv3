"""s_settings — VERIFIED spec (553 bytes), partial: what the GAME popup reads.

**TWO INDEPENDENT SOURCES (decision 23), 14 September 2026.**

1. THE HEADER. orion2re's own `src/game/orion2.h` (struct s_settings,
   :2423) compiled with the build's own precompiled header and
   `#pragma pack(1)`, carrying one `static_assert(offsetof(...) == N)`
   per field below plus `sizeof(s_settings) == 0x229` — the assert in
   `sizes.h:20`. Every assert held. The same file with ONE offset
   deliberately wrong (`game_difficulty` at 0xD5) failed to compile,
   so the check can fail and did not.

2. THE LIVE GAME. A STATE_SNAPSHOT's settings block read
   `1 1 1 0 0 1 1 0 1 1 0 1 0 0 | 0 0 0 1 50 1 49 7` for bytes 0..21.
   The native Settings dialog of the same moment
   (`orionlayer-fixtures/evidence/game_menu/02_options.png`) shows its
   thirteen boxes as on, on, off, off, on, on, off, on, on, off, on,
   off, off — which is bytes 0, 1, 3..13 with byte 2 SKIPPED, exactly
   the mapping `Set_Current_Game_Option_Flags_` makes
   (loadsave.cpp:1145-1163; `random_events` is not a row). A layout
   one byte off would put byte 2's `1` on the third row, which the
   picture shows off. `active_save_slot` 7 is the row the native Load
   dialog draws highlighted (slot 8, `03_load.png`). `MOX.SET` on disk
   held the same 22 bytes, but it is written by the same struct and is
   NOT counted as a third source.

The volume bytes are in the spec because they are on the wire, and
nothing in HD draws them — the sliders are an OMISSION
(`screens/game_menu/screen.py`).
"""
from core.structs import Spec

SIZE = 0x229

SPEC = Spec("s_settings", SIZE, [
    ("end_of_turn_summary", 0, "u8"),
    ("end_of_turn_wait", 1, "u8"),
    ("random_events", 2, "u8"),
    ("enemy_moves", 3, "u8"),
    ("expanding_help", 4, "u8"),
    ("auto_select_ships", 5, "u8"),
    ("animations_on", 6, "u8"),
    ("auto_select_colony", 7, "u8"),
    ("show_relocation_lines", 8, "u8"),
    ("show_gnn_report", 9, "u8"),
    ("auto_delete_tg_housing", 10, "u8"),
    ("auto_saves", 11, "u8"),
    ("only_show_serious_turn_summary_reports", 12, "u8"),
    ("ship_initiative", 13, "u8"),
    ("sound_fx_on", 17, "u8"),
    ("sound_fx_level", 18, "i8"),
    ("music_on", 19, "u8"),
    ("music_level", 20, "i8"),
    ("active_save_slot", 21, "i8"),
], verified=True)

#: The Settings dialog's thirteen rows, in ROW order — not the struct's.
#: `Set_Current_Game_Option_Flags_`, loadsave.cpp:1145-1163.
OPTION_FIELDS = (
    "end_of_turn_summary", "end_of_turn_wait", "enemy_moves",
    "expanding_help", "auto_select_ships", "animations_on",
    "auto_select_colony", "show_relocation_lines", "show_gnn_report",
    "auto_delete_tg_housing", "auto_saves",
    "only_show_serious_turn_summary_reports", "ship_initiative",
)


def parse(raw):
    return SPEC.parse(raw)


def option_flags(raw, game_type):
    """The thirteen checkbox states the popup starts from.

    Transcribes `Set_Current_Game_Option_Flags_`, including its one
    rule: row 1, End Of Turn Wait, reads 0 in any game that is not
    single player (`_game_type != 0`, loadsave.cpp:1147-1151). It runs
    ONCE per popup (`_Game_Popup_`, :1552), not per visit to the
    dialog, so a toggle survives ACCEPT and a second visit.
    """
    view = parse(raw)
    flags = [1 if getattr(view, name) else 0 for name in OPTION_FIELDS]
    if game_type != 0:
        flags[1] = 0
    return flags
