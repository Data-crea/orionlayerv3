"""The film that plays, on the wire — open fix 112, "FILM" (work order 320).

    86      synthetic screen id (`core.screen_names`): reported while
            `SMACK::Play_Cinematic_` (smack.cpp:42) plays a film, by
            `ext::FilmGuard` for the whole of the function.
    "FILM"  (`doc/ext_films.patch`): written LAST, only while a film plays.
            A version byte (1), uint8 n and n bytes of the film's file name
            as its caller named it ("PLNTDFIN.LBX", or an E_Strings name
            such as "loserfin.lbx"), int16 the frames drawn so far (the
            last drawn, 0-based, plus one: the draw decodes the next frame,
            smckplay.cpp:236-241), int16 the film's total frames.

WHY: the film's frame loop (smack.cpp:105-124 in 1.60, :102-121 in v2)
calls no Get_Input, so nothing ticked while a film played: HD held its last
frame, and a click could not skip a film the hidden engine window played.
The fix ticks from the loop at most every 50 ms; the picture is VISUAL's,
as for every screen, and the block says that it is a film and how far it
has come.

Read WHOLE or left None (`core/colonyblocks.py`'s rule): an engine without
the fix writes none and reports the caller's id, and HD keeps holding its
last frame (UNVERIFIED `film_live`: no live run has seen the block).
"""
import struct as _st

from core import lang

#: The synthetic id a playing film reports (open fix 112): the next free one
#: after 85 in both trees.
SCREEN_ID = 86
#: The films the game plays and where (eric.cpp:183-304 in v2; work order
#: 320's list in 1.60's lines). Display only; the engine names the file.
FILMS = {
    "loserfin.lbx": "the defeat",
    "genwinfn.lbx": "the victory",
    "anwinfin.lbx": "the victory over the Antarans",
    "wininfin.lbx": "the diplomatic victory",
    "plntdfin.lbx": "a planet destroyed",
    "amebafin.lbx": "the Amoeba",
    "orionfin.lbx": "Orion taken",
    "dimtvfin.lbx": "the dimensional portal",
    "anatkfin.lbx": "the Antarans attack",
}
TAIL = "<hh"


def parse(gs, data, pos):
    """Read FILM at `pos` into `gs.film` (None when absent, short or of
    another version). Returns the new position."""
    gs.film = None
    if data[pos:pos + 4] != b"FILM" or pos + 6 > len(data):
        return pos
    version, n = data[pos + 4], data[pos + 5]
    at = pos + 6
    end = at + n + _st.calcsize(TAIL)
    if version != 1 or end > len(data):
        return pos
    # every string off the wire through one door, a file name too (ASCII:
    # the German font's slots leave it as it is)
    name = lang.wire_text(data[at:at + n])
    frame, total = _st.unpack_from(TAIL, data, at + n)
    gs.film = {"name": name, "frame": frame, "total": total}
    return end


def for_state(state):
    """The film that plays, or None: the block, under the film's own id."""
    film = getattr(state, "film", None)
    if film is None or getattr(state, "current_screen", -1) != SCREEN_ID:
        return None
    return film


def title(film):
    """What the film shows, for the log and the frame trace."""
    return FILMS.get(str(film.get("name", "")).lower(), film.get("name"))
