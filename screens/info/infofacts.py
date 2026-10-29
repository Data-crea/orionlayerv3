"""What the Tech Review says about an application beyond its text: the
research field it belongs to, the field's cost, the category's ladder and
the field's other applications — all read from tables the research screens
already hold (`core/researchlist.py`, `core/research.py`); nothing here is a
second copy. The marking is in `infoview.py` (`tech_review_facts`).

THE LADDER. Each of the eight categories is a chain of fields walked by
`next_field_id` from `FIRST_FIELD_IN_GROUP`; a category's player field moves
to the next only when the current one is done (`Advance_Player_Field`,
colcalc.cpp:1749-1778). The hyper-advanced field (75-82) is the last rung.
So the rung before a field is what must be finished first.
"""
from core import research, researchlist as rl


def _ladders():
    out = {}
    for group in range(1, 9):
        field, rungs = rl.FIRST_FIELD_IN_GROUP[group], []
        while field and field not in rungs and len(rungs) < 40:
            rungs.append(field)
            field = rl.NEXT_FIELD[field]
        for level, f in enumerate(rungs, 1):
            out[f] = (group, level, len(rungs),
                      rungs[level - 2] if level > 1 else 0)
    return out


LADDER = _ladders()


def field_of(app):
    """The research field of an application, or 0 for one that has none
    (the three sentinel fields)."""
    if app is None or not 0 <= int(app) < len(rl.APP_FIELD):
        return 0
    field = rl.APP_FIELD[int(app)]
    return field if field in LADDER else 0


def facts(app):
    """`(field, cost, group, level, rungs, previous field)` or None."""
    field = field_of(app)
    if not field:
        return None
    group, level, rungs, previous = LADDER[field]
    return field, research.cost(field), group, level, rungs, previous


def same_field(app, researched):
    """The other applications of the application's field that `researched`
    (a collection of application ids) holds, in table order."""
    field = field_of(app)
    return [a for a in rl.field_applications().get(field, ())
            if a != app and a in researched]
