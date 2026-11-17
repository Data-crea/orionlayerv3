"""The galaxy map's event banners, the auto-turn banner and the multiplayer
lights on the wire — open fixes 114, 118 and 119 (work order 403).

    "EVTB"  (`doc/ext_event_banners.patch`, fix 114): written on EVERY
            screen, before FILM. A version byte (1), uint8 the warp beast's
            event is active (`EVENTS::Event_Check_Warp_Beast`), uint8 the
            hyperspace flux's is (`Event_Check_Hyperspace_Flux`).
    "AUTO"  (`doc/ext_auto_turn_banner.patch`, fix 118): written only while
            the chain of turns that run by themselves is armed
            (`MAINSCR::check_next_turn_exit_field`) and the banner was drawn
            by `Do_Begin_Of_Turn`. A version byte (1), uint8
            `in_auto_next_turn_mode`, int16 `MOX::global_exit_field` (the
            whole-screen field that ends the chain; 0xFC18 = -1000 when
            none), int16 the box's x, y, w, h (native pixels), uint8 n and
            the n bytes of the text ("<race> stardate X.Y", H 0xE9).
    "PLRL"  (`doc/ext_multiplayer_lights.patch`, fix 119): written only in a
            hotseat or network game (`MOX::game_type` 1-3), on every
            screen. A version byte (1), uint8 game_type, uint8 the lights
            are bright (every human but the player is done), uint8 the
            diplomacy request mask (0 outside a network game), uint8 n, then
            per player uint8 done and uint8 the player's colour.

They follow CSUM and precede SCOR (`core/scoreblock.py`) and FILM, in the
engine's write order. WHY: the original draws the banners and the lights on
the main screen from engine values no earlier block carried
(`mainscr_main.cpp:28-59`, `mainscr2.cpp:533-596`, `mainscr.cpp:2958-3100`).

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fixes writes none, and the map draws none of it (OMISSION, as before).
"""
import struct as _st

from core.blockreader import Reader

#: The exit field's "none": `MOX::global_exit_field` is a uint16 set to
#: -1000 by the TURN button (mainscr_main.cpp:672).
NO_FIELD = -1000


def _read(gs, attr, data, pos, tag, body):
    """Read `tag` at `pos` into `gs.<attr>` through `body(reader)`; None when
    absent, short or of another version. Returns the new position."""
    setattr(gs, attr, None)
    r = Reader(data, pos)
    if not r.at_tag(tag):
        return pos
    r.pos += len(tag)
    try:
        version = r.one("B")
        if version != 1:
            r.refuse(tag.decode(), f"version {version}")
            return pos
        setattr(gs, attr, body(r))
    except ValueError:
        r.refuse(tag.decode(), "short")
        return pos
    return r.pos


def _event_banners(r):
    beast, flux = r.take("BB")
    return {"warp_beast": bool(beast), "hyperspace_flux": bool(flux)}


def _auto_turn(r):
    in_auto, field, x, y, w, h = r.take("Bhhhhh")
    return {"in_auto": bool(in_auto), "exit_field": field,
            "box": (x, y, w, h), "text": r.text8()}


def _player_lights(r):
    game_type, bright, mask, n = r.take("BBBB")
    players = [(bool(done), colour) for done, colour in
               (r.take("BB") for _ in range(n))]
    return {"game_type": game_type, "bright": bool(bright),
            "request_mask": mask, "players": players}


def parse(gs, data, pos):
    """EVTB, AUTO, PLRL in the engine's order; returns the new position."""
    pos = _read(gs, "map_banners", data, pos, b"EVTB", _event_banners)
    pos = _read(gs, "auto_turn", data, pos, b"AUTO", _auto_turn)
    return _read(gs, "player_lights", data, pos, b"PLRL", _player_lights)


def build_evtb(beast=False, flux=False):
    """The block as the engine writes it — for the checks' stand-ins."""
    return b"EVTB" + _st.pack("<BBB", 1, bool(beast), bool(flux))


def build_auto(text, box=(0, 0, 0, 0), in_auto=True, field=NO_FIELD):
    raw = text.encode("latin-1")
    return (b"AUTO" + _st.pack("<BBhhhhh", 1, bool(in_auto), field, *box)
            + bytes([len(raw)]) + raw)


def build_plrl(game_type, players, bright=False, mask=0):
    out = b"PLRL" + _st.pack("<BBBBB", 1, game_type, bool(bright), mask,
                             len(players))
    for done, colour in players:
        out += _st.pack("<BB", bool(done), colour)
    return out
