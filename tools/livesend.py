"""A LIVE TOOL IS A CLIENT, and sends only into a list it just read.

Every send here identifies the dialog from the FIELD LIST of the state it
is handed at that moment — never from an earlier snapshot, never from the
screen number alone — and refuses, loudly, when the shape is not the one
the caller named. The product has that rule since work order 128 C (the
galaxy map's parking guard); the tools pay for it twice:

- work order 122: a loop clicked CLOSE at a fixed native point until the
  map came back, a click turned a colony-base choice into "Really trash
  your colony base for 100BC?", and the scratch game's colony base was
  scrapped before anybody looked;
- work order 128 C: a driver read screen 0 with a message box's field
  list, decided from that stale reading, and sent ACTIVATE_FIELD 1 into
  the turn-start research prompt — orion2re died with SIGSEGV in
  `TECH::_Tech_Select_` (open fix 23).

A refusal RAISES. A tool that cannot say what is on screen has nothing to
send, and carrying on is what both incidents did.

The shape tests are the ones that already exist — `mapboxes.live_field`
for a field named by type and native rect, `game_menu.nodes.classify` for
the GAME popup's dialogs. Nothing here is a second copy of them.
"""
import os
import json
import logging

log = logging.getLogger("livesend")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WrongDialog(RuntimeError):
    """The live list is not the one the caller measured against."""


def _fields(state):
    return list(getattr(state, "fields", None) or [])


def _spec(screen_name, key):
    with open(os.path.join(ROOT, "screens", screen_name, "layout.json"),
              encoding="utf-8") as fh:
        return json.load(fh)[key]


def field_at(state, x, y):
    """The field a native click at (x, y) would reach, or None.

    The LOWEST index wins, which is what `fields::Check_Fields_XY_` does
    (fields.cpp:1264-1283) — so this is the field the game will act on,
    not merely a field that contains the point.
    """
    for f in sorted(_fields(state), key=lambda f: f.index):
        if f.index == 0:
            continue
        if f.x <= x <= f.x_end and f.y <= y <= f.y_end:
            return f
    return None


def on_galaxy_map(state):
    """True while the list is the galaxy map's own (its grid field)."""
    from screens.galaxy_map import mapboxes
    return mapboxes.live_field(_fields(state),
                               _spec("galaxy_map", "map_cancel")) is not None


def on_colony_summary(state):
    """True while the list is the colony summary's own.

    Its seven sort buttons are one row of `Add_Multi_Button_Field_` at
    native y 446 (colsum.cpp:267-273), and the live list reports them as
    fields 16-22 at y 446..469 (layout.json `sort._note`, measured
    3 September 2026). Seven fields of that band is the shape.
    """
    return len([f for f in _fields(state)
                if (f.y, f.y_end) == (446, 469)]) >= 7


def in_game_menu(node):
    """A predicate: the GAME popup showing `node` (nodes.classify)."""
    from screens.game_menu import nodes

    def check(state):
        return nodes.classify(_fields(state)) == node
    return check


def _guard(state, screen, shape, label):
    if screen is not None and getattr(state, "current_screen", None) != screen:
        raise WrongDialog(
            f"{label}: the game reports screen "
            f"{getattr(state, 'current_screen', None)}, not {screen} — "
            f"nothing sent")
    if shape is not None and not shape(state):
        raise WrongDialog(
            f"{label}: the field list is not the shape this step was "
            f"measured against ({len(_fields(state))} fields on screen "
            f"{getattr(state, 'current_screen', None)}) — nothing sent")


def activate(client, index, *, screen=None, shape=None, field_type=None,
             rect=None, label="activate"):
    """ACTIVATE_FIELD, if the live list still holds that field.

    `index` is checked against the list read now: the field must exist and,
    where the caller names them, carry the type and native rect it was
    measured with. A field NUMBER means something else in every other list
    (decision 20), which is exactly how 128 C's crash happened.
    """
    state = client.state
    _guard(state, screen, shape, label)
    field = next((f for f in _fields(state) if f.index == index), None)
    if field is None:
        raise WrongDialog(f"{label}: no field {index} in the live list — "
                          f"nothing sent")
    if field_type is not None and field.field_type != field_type:
        raise WrongDialog(f"{label}: field {index} is type "
                          f"{field.field_type}, expected {field_type} — "
                          f"nothing sent")
    if rect is not None and (field.x, field.y, field.x_end,
                             field.y_end) != tuple(rect):
        raise WrongDialog(f"{label}: field {index} is at "
                          f"{(field.x, field.y, field.x_end, field.y_end)}, "
                          f"expected {tuple(rect)} — nothing sent")
    log.info("%s: ACTIVATE_FIELD %d", label, index)
    return client.activate_field(index)


def click(client, x, y, *, screen=None, shape=None, field_type=None,
          label="click"):
    """INJECT_CLICK, if the live list has a field under that point.

    The field the click will reach is resolved first (`field_at`), and its
    type checked where the caller names one. A point over nothing is a
    refusal: a click the game cannot attribute is the shape of work order
    122's loop.
    """
    state = client.state
    _guard(state, screen, shape, label)
    field = field_at(state, x, y)
    if field is None:
        raise WrongDialog(f"{label}: no field under native ({x}, {y}) in "
                          f"the live list — nothing sent")
    if field_type is not None and field.field_type != field_type:
        raise WrongDialog(f"{label}: the field under ({x}, {y}) is type "
                          f"{field.field_type}, expected {field_type} — "
                          f"nothing sent")
    log.info("%s: INJECT_CLICK (%d, %d) -> field %d", label, x, y,
             field.index)
    return client.inject_click(x, y)


def key(client, keysym, *, screen=None, shape=None, label="key"):
    """INJECT_KEY, once the caller's shape test holds.

    A key has no field to resolve, so the shape is all there is — and it is
    required: `inject_key(ESC)` cascades across sub-screens (fundament,
    section 3), so the screen it lands in has to be known.
    """
    state = client.state
    if shape is None and screen is None:
        raise WrongDialog(f"{label}: a key needs a screen or a shape to "
                          f"send into — nothing sent")
    _guard(state, screen, shape, label)
    log.info("%s: INJECT_KEY %s", label, keysym)
    return client.inject_key(keysym)
