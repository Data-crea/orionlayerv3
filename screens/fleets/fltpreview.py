"""The Fleets screen's move preview — open fix 121 (work order 406).

The engine's FMOV block now comes on this screen too (`core/moveblocks.py`,
`fleet_screen_verdicts`): the `s_ship_move_info` that
`SHIPMOVE::Ships_Try_To_Move_To_` gives the SELECTED big icons' ships at
every star. The original makes that verdict on hover
(`Print_Fltscrn_Scanned_Star_Name_`, flt2.cpp:349-354) and reads it twice:
the strip's text and the preview line's colour. HD never recomputes range,
fuel, speed or gates; it reads the verdict of the star under HD's own
pointer (`screen._scan_star`).

TRANSCRIPTION `status_states` (flt2.cpp:394-466, :492-499): the verdict
picks one of nine states in this order — a black hole in the way (3, H
0x21), an immobile fleet (4, H 0x6E), out of range (5, H 0x6F / 0x70 with
the star's name when the player has visited it, else 6, H 0xEB), the
hyperspace flux (9, H 0x73), a legal move (the black hole as the target is
3 again; a move of no turns is 0, H 0x67 with the name; else 1, H 0x69 /
0x6A with the turns and the name when visited, or 2, H 0x6B / 0x6C with the
turns alone). The singular form is the value 1. States 7 and 8 — no ships
selected — are `fltrows.scanned_star_line`.

TRANSCRIPTION `preview_line` (flt1.cpp:121-170): the line from the selected
stack's icon (the node `ship_stack_start[small_ship_stack_ptr]`, FLTS's
`head_node`) to the star under the pointer, drawn only while the relocate
mode is not 1, a stack is shown, a ship is selected and a star is scanned;
red when `moving == 0` or the star is a black hole, else green. Unlike the
galaxy map's own preview (`maplines.preview_colour`) there is no HD
EXTENSION here: a move of no turns is green, as the original draws it.

DEVIATION `strip_tone`: the original prints states 0-2 in `normal_colors`
(flt2.cpp:4) and 3-6, 9 in `neutral_colors` (:5); HD draws the strip in one
colour and carries the tone in the result so a check holds it, the palette
indices (111/116 and 4/16) being the game's own fonts.

UNVERIFIED live: the strip and the line in a running game (work order 406
built them offline); the byte layout is the engine's FMOV, read both ways by
check 090zzzzzzzzzzzzg.
"""
from core import hestrings
from core import moveblocks
from core.structs import star as star_struct

#: flt2.cpp:394-466 — the messages by state.
H_ORBIT, H_TURN, H_TURNS, H_ETA_TURN, H_ETA_TURNS = 0x67, 0x69, 0x6A, 0x6B, 0x6C
H_BLACK_HOLE, H_IMMOBILE, H_FLUX = 0x21, 0x6E, 0x73
H_RANGE_TURN, H_RANGE_TURNS, H_RANGE_UNKNOWN = 0x6F, 0x70, 0xEB

#: `normal_colors` / `neutral_colors` (flt2.cpp:4-5), by state.
NORMAL, NEUTRAL = "normal", "neutral"

#: The star class of a black hole (`STAR_CLASS_BLACK_HOLE`, flt2.cpp:441).
BLACK_HOLE_CLASS = star_struct.CLASS_BLACK_HOLE


def state_of(verdict, star, visited):
    """`(status, tone)` for one star's verdict — flt2.cpp:394-466. Status
    is the original's number (0-6, 9) or -1 when no branch is taken (the
    original then prints its uninitialised buffer: HD prints nothing)."""
    if verdict["blackhole_blocks"]:
        return 3, NEUTRAL
    if verdict["immobile"]:
        return 4, NEUTRAL
    if verdict["out_of_range"]:
        return (5 if visited else 6), NEUTRAL
    if verdict["hyperspace_flux"]:
        return 9, NEUTRAL
    if verdict["moving"]:
        if int(star.spectral_class) == BLACK_HOLE_CLASS:
            return 3, NEUTRAL
        if int(verdict["turns_left"]) == 0:
            return 0, NORMAL
        return (1 if visited else 2), NORMAL
    return -1, NORMAL


def status_text(verdict, star, visited, strings):
    """`(text, tone)` — the strip's line for the selection's verdict at the
    star (flt2.cpp:394-466 with the switch :410-499)."""
    status, tone = state_of(verdict, star, visited)
    turns, parsecs = int(verdict["turns_left"]), int(verdict["parsecs"])
    name = getattr(star, "name", "") or ""

    def msg(index, *values):
        template = strings.message(index) if strings is not None else None
        return hestrings.printf(template, *values) if template else ""
    if status == 0:
        return msg(H_ORBIT, name), tone
    if status == 1:
        return msg(H_TURN if turns == 1 else H_TURNS, turns, name), tone
    if status == 2:
        return msg(H_ETA_TURN if turns == 1 else H_ETA_TURNS, turns), tone
    if status == 3:
        return msg(H_BLACK_HOLE), tone
    if status == 4:
        return msg(H_IMMOBILE), tone
    if status == 5:
        return msg(H_RANGE_TURN if parsecs == 1 else H_RANGE_TURNS,
                   parsecs, name), tone
    if status == 6:
        return msg(H_RANGE_UNKNOWN, parsecs), tone
    if status == 9:
        return msg(H_FLUX), tone
    return "", tone


def strip(game_state, star_idx, strings):
    """`(text, tone)` for the move preview at the hovered star, or None
    when the engine sends no verdict (an engine without fix 121, or nothing
    selected / RELOCATE mode: states 7 and 8, `fltrows`)."""
    verdicts = moveblocks.fleet_screen_verdicts(game_state)
    stars = getattr(game_state, "stars", None) or []
    if not verdicts or not 0 <= star_idx < min(len(verdicts), len(stars)):
        return None
    me = int(getattr(game_state, "player_num", 0) or 0)
    visited = bool(star_struct.visited_by(stars[star_idx], me))
    return status_text(verdicts[star_idx], stars[star_idx], visited, strings)


def preview_line(game_state, block, star_idx):
    """`{"icon", "star", "colour"}` for the preview line, or None —
    flt1.cpp:130-170. `block` is FLTS's dict."""
    verdicts = moveblocks.fleet_screen_verdicts(game_state)
    stars = getattr(game_state, "stars", None) or []
    block = block or {}
    if not verdicts or int(block.get("relocate_mode", 0)) == 1 or \
            int(block.get("stack", -1)) <= -1 or \
            int(block.get("selected_count", 0) or 0) <= 0:
        return None
    if not 0 <= star_idx < min(len(verdicts), len(stars)):
        return None
    head = int(block.get("head_node", -1))
    icons = getattr(game_state, "ship_icons", None) or []
    icon = next((i for i, ic in enumerate(icons) if int(ic.node_idx) == head),
                None) if head >= 0 else None
    if icon is None:                      # F_Ship_Icon_From_Node_Ptr_ -1
        return None
    red = not verdicts[star_idx]["moving"] or \
        int(stars[star_idx].spectral_class) == BLACK_HOLE_CLASS
    return {"icon": icon, "star": star_idx, "colour": "red" if red else "green"}
