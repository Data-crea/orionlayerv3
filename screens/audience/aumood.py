"""Which clip the ambassador plays — work order 359.

**INVENTION `ambassador_mood`.** The original has one ambassador picture
per race and no mood (`audience_reading.md` §1.1: "there is no
mood-specific picture"). The mood is HD's own reading of what the wire
carries (`relations` and `treaty` of the ambassador's record towards the
player, `core/structs/player.py`; the audience's mode), in this order:

    first_contact  the first audience with this race since the client
                   started, and no treaty (`treaty == 0`)
    threatening    at war (`treaty >= 4`, the Races screen's war labels)
                   or `relations <= THREAT`
    pleading       an AI asked for the audience (mode "ai") and is not
                   threatening
    friendly       `relations >= FRIEND` or a pact or alliance
                   (`treaty` 1 or 2)
    neutral        everything else

The thresholds are guesses, not measurements; they are named here so a
playtest can move them.
"""
MOODS = ("first_contact", "friendly", "neutral", "pleading", "threatening")
#: A clip named `default` plays for every mood that has no clip of its own
#: (`auvideo.clip_dir`): one film for every situation.
CLIPS = MOODS + ("default",)
THREAT, FRIEND, WAR = -30, 25, 4

_seen = set()
_first = {}      # ambassador -> the statement its first audience opened with


def leave():
    """The audience closed: the races met in it are met."""
    _seen.update(_first)
    _first.clear()


def mood(state, audience):
    """The mood for the audience block `audience` of snapshot `state`.
    first_contact lasts for the opening statement only: the next reply
    is read from the relations as any other."""
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    me = int(getattr(state, "player_num", 0) or 0)
    amb = audience["ambassador"]
    relations = treaty = 0
    if 0 <= amb < len(raws) and raws[amb] is not None and \
            len(raws[amb]) >= player_struct.SIZE:
        p = player_struct.parse(raws[amb])
        if 0 <= me < 8:
            relations, treaty = int(p.relations[me]), int(p.treaty[me])
    words = audience["text"]
    if amb not in _seen and amb not in _first and treaty == 0:
        _first[amb] = words
    if amb in _first:
        if not words or words == _first[amb]:
            return "first_contact"
        _seen.add(amb)
        del _first[amb]
    if treaty >= WAR or relations <= THREAT:
        return "threatening"
    if audience["mode"] == "ai":
        return "pleading"
    if relations >= FRIEND or treaty in (1, 2):
        return "friendly"
    return "neutral"
