"""Right clicks the original answers with an information window — work
order 200 B (`dev:doc/briefs/200-rightclick-inventory.md`).

Once the galaxy map has run, a right click never cancels any more
(`fields::Disable_Cancel_` is never undone, fields.cpp:112-114): over a
help rectangle it shows help, on field n `Get_Input_` returns -n
(fields.cpp:1369-1373, :1523-1526), and some screens answer -n with a box
of their own — the colony info of a planet, a weapon's description, where
a leader is. Those boxes are `TEXTBOX::Text_Box_` or `GENDRAW`'s message
boxes, which open fix 29 puts on the wire (MSGB), so HD's message box shows
them with the game's own words.

TRANSCRIPTION `right_info`: HD sends the right click to the original's
own field, the field found in the live list by the screen; the game opens
what it opens. The game resolves a click by the POINTER — the first field
in list order whose rectangle holds it wins (fields.cpp:1276-1290) — so the
click goes to a point of the field no earlier field covers (`point_for`; an
injected right click there, open fix 61), not blindly to its centre: the
discovery popup's planet buttons overlap, and a right click at one's centre
answered with another planet's colony info (work order 200 B, live).
Help rectangles stay HD's own (`core/screenhelp`): the game's help box,
`Draw_Help_Entry_` (textbox.cpp:316), is not on the wire. And because the
engine's right click lands at the field's centre, where its own help list is
walked FIRST (fields.cpp:1250-1256), `send` asks that list (open fix 69,
`core/helplist`) before it sends: a help entry there is what the original
would show, so HD opens that entry and sends nothing.
"""
import logging

log = logging.getLogger("rightinfo")


def send(app, field, why, open_help=None):
    """Right click on `field`'s centre. True when it went out — or when the
    help list covers that centre and `open_help(id)` was called instead."""
    if field is None or not getattr(app, "connected", False):
        return False
    from core import helplist
    state = getattr(app.client, "state", None)
    x, y = point_for(field, getattr(state, "fields", None) or [])
    hid = helplist.help_at(getattr(state, "help_list", None), x, y)
    if hid is not None and open_help is not None:
        log.info("right click on field %d (%s): help %d covers it",
                 field.index, why, hid)
        open_help(hid)
        return True
    log.info("right click on field %d (%s) at %d,%d", field.index, why, x, y)
    app.client.inject_right_click(x, y)
    return True


def point_for(field, fields):
    """A native point of `field` that no field before it in the list holds
    — the one `Get_Input_` would answer with this field — its centre when
    the centre is free, else the first free point of a 7 x 7 grid inside it;
    the centre when none is free."""
    before = [f for f in fields if 0 < f.index < field.index]
    cx, cy = (field.x + field.x_end) // 2, (field.y + field.y_end) // 2
    w, h = field.x_end - field.x, field.y_end - field.y
    points = [(cx, cy)] + [(field.x + w * i // 8, field.y + h * j // 8)
                           for j in range(1, 8) for i in range(1, 8)]
    for x, y in points:
        if not any(f.x <= x <= f.x_end and f.y <= y <= f.y_end
                   for f in before):
            return x, y
    return cx, cy


def opener(screen):
    """`send`'s `open_help` for a screen with a help popup."""
    def open_help(hid):
        entry = screen.helptext.entry(hid) or \
            screen.helptext.missing_entry(hid)
        screen.help.open(hid, *entry)
    return open_help


def field_at_index(app, index):
    """The live field with `index`, or None."""
    state = getattr(app.client, "state", None)
    return next((f for f in (getattr(state, "fields", None) or [])
                 if f.index == index), None)
