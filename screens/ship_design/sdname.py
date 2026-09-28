"""The Ship Designer's name entry in HD — work order 187, part 2.

**THE SAVE DIALOG'S PATH** (`screens/game_menu/gmsave.py`, the Empire
Identity mechanism): HD holds the name in a local `TextInput` — the field,
the cursor and the typed text are HD's — and the engine hears nothing until
Enter. Then ONE paced `core.injection` step sends the field's opening input,
the clearing Backspaces and the keys, one per tick (the game's key ring holds ten,
`injection.type_name`).

**THE OPENING INPUT IS A CLICK, NOT AN ACTIVATION** — measured in work order
186 part 3 (part 09, "A continuous string field (type 11) is opened only by
a click"): the designer's name is a continuous string field
(`Add_Continuous_String_Input_Field_`, design_main.cpp:688-691), and only
the mouse path opens it (fields.cpp:1436-1444: `_input_field_active = 1`,
the name copied into `_continuous_string`). THE NAME IS CLEARED WITH
`CLEAR_KEYS` BACKSPACES, not one: the click sets `_active_input_field_first`
(whose first Backspace clears everything, fields.cpp:1196-1199) only when it
OPENS the field (:1437), and the designer's field was already active —
measured live (work order 187 part 2): one Backspace took one letter,
"Rafale" + "Hawke" became "RafalHawke". The code that always clears,
0x0E7F (:1181-1183), no injected key produces (platform.cpp:420-455:
Delete is 0x10000). A Backspace on an empty field does nothing (:1193), so
15 clear the name in either state. Printable keys but `_` append up to `max_length - 1`
(fields.cpp:1204-1219: 14 of the field's 15) and while the text fits the
field's width; Enter commits (fields.cpp:1047-1058) and the designer then
trims it, an empty name falling back to the slot's (design_main.cpp).
The injected click also puts the engine's pointer on the field, so the
Enter cannot land on another field (186's Cruiser).

**ESC cancels HERE**: nothing has been sent, the engine's name is untouched
— the original's own field would take ESC the same way (it leaves the name
as it was). Nothing of the original's picture is shown at any point.
"""
import logging

from core.injection import InjectionChain, name_keys, paced_keys
from core.widgets.text_input import TextInput

from . import sdgeom as geom, sdwire

log = logging.getLogger("ship_design")

#: `max_length` 15 (design_main.cpp:690) and the typing loop stops one short
#: of it (fields.cpp:1212-1216). The field's pixel width may cut further —
#: the game's own rule, a font metric HD does not mirror.
NAME_MAX = 14

#: Snapshots after the chain ends that HD waits for the committed name
#: (the effect needs one pre-effect pair, `wire_protocol.EFFECT_PAIRS`).
SETTLE_SNAPSHOTS = 6

#: Backspaces sent before the text: the field's `max_length`, enough for any
#: name it can hold (see the module's docstring for why not one).
CLEAR_KEYS = 15

#: The chain waits this long for the page's list before it gives up.
STEP_TIMEOUT_S = 10.0


def game_accepts(ch):
    """The characters the continuous input takes (fields.cpp:1206)."""
    return len(ch) == 1 and 0x20 <= ord(ch) <= 0x7E and ch != "_"


def is_page(fields):
    """The designer's own list: its Cancel button and its name field."""
    return sdwire.live_field(fields, geom.CANCEL) is not None and \
        sdwire.live_field(fields, geom.NAME) is not None


class NameEditor:
    def __init__(self, screen):
        self.screen = screen
        self.input = None
        self.chain = None
        self.sent = None          # the value the chain delivers
        self._after = None        # snapshot count when the chain ended

    @property
    def editing(self):
        return self.input is not None and self.input.focused

    @property
    def busy(self):
        return self.chain is not None

    def start(self, current):
        if self.busy:
            return
        initial = "".join(c for c in (current or "") if game_accepts(c))
        self.input = TextInput(value=initial[:NAME_MAX], max_len=NAME_MAX,
                               allowed=game_accepts, on_submit=self.commit,
                               on_cancel=self.cancel)
        log.info("ship design: name entry started (%r)", initial)

    def commit(self, value=None):
        if self.input is None or self.busy:
            return
        value = self.input.value if value is None else value
        app = self.screen.app
        if not app.connected:
            return
        keys = name_keys(value, clear=CLEAR_KEYS)

        def run(client, fields):
            f = sdwire.live_field(fields, geom.NAME)
            x, y = (f.x + f.x_end) // 2, (f.y + f.y_end) // 2
            log.info("ship design: name %r — INJECT_CLICK (%d, %d), then %d "
                     "keys", value, x, y, len(keys))
            return paced_keys(lambda c: c.inject_click(x, y), keys)

        self.chain = InjectionChain(app.client, [(
            "design name", is_page, run, STEP_TIMEOUT_S)])
        self.sent = value
        self.input.focused = False

    def cancel(self):
        log.info("ship design: name entry cancelled — nothing sent")
        self.input = None
        self.sent = None

    def update(self, game_state):
        if self.chain is None:
            return
        self.chain.update(game_state)
        if self.chain.failed:
            log.error("ship design: the name chain failed at '%s'",
                      self.chain.failed_step)
        if self.chain.done or self.chain.failed:
            self.chain = None

    def settled(self, design_name, snapshots):
        """Close the HD field once the engine has the name. Until then HD
        keeps showing the typed text, not the old name: after the chain
        ends, until DSGN's name is what was sent, or `SETTLE_SNAPSHOTS`
        later (the game trims a name and may cut it at the field's width —
        its own rule, and then its name is the one to show)."""
        if self.input is None or self.input.focused or self.chain is not None:
            self._after = None
            return
        if self._after is None:
            self._after = snapshots
        if design_name == self.sent or \
                snapshots - self._after >= SETTLE_SNAPSHOTS:
            if design_name != self.sent:
                log.info("ship design: the game holds the name as %r (sent "
                         "%r)", design_name, self.sent)
            self.input = None
            self.sent = None
            self._after = None

    def handle_key_event(self, event):
        if self.busy:
            return True               # nothing else goes out meanwhile
        if self.editing:
            return self.input.handle_key_event(event)
        return False
