"""The Save dialog's name entry: a local TextInput, delivered one key per tick.

**THE ORIGINAL'S PATH, WITHOUT A MOUSE.** A click on the strip under a
slot's name starts editing it (`Do_Save_Game_Popup_`, loadsave.cpp:
506-521: `_input_field_active = 1`, the description copied into
`fields::_continuous_string`, `_active_input_field_first = 1`); the
first backspace then clears the whole string (fields.cpp:1177-1193),
printable keys append (:1202-1219, `_` refused), and Enter returns the
name field, which on the slot being edited saves (loadsave.cpp:
496-501, :538-563). All of that is reachable by ACTIVATE_FIELD on the
strip plus keys, so that is what goes out: nothing here clicks.

**HD HOLDS THE NAME LOCALLY UNTIL IT IS COMMITTED** (decision 47's
shape): TextInput edits it and the game hears nothing until SAVE,
Enter or a second click on the same row. Then one paced chain step
sends the strip activation and the keys through `core.injection` — the
Empire Identity mechanism, not a second injector — ONE PER TICK,
because the game's key ring holds ten (`injection.type_name`).

**ESC WHILE EDITING LANDS IN THE MENU**, as in the original: the key
returns `-field` (fields.cpp:1165-1174), which `Do_Save_Game_Popup_`
reads as a slot-field cancel and leaves for the menu (loadsave.cpp:
568-574). HD has sent nothing yet, so the same landing is CANCEL
(:565-567).
"""
import logging

from core.injection import InjectionChain, name_keys, paced_keys
from core.widgets.text_input import TextInput
from screens.game_menu import gmdraw, nodes

log = logging.getLogger("game_menu")

#: The name field's `max_length` is 0x1e (loadsave.cpp:274) and the
#: typing loop stops one short of it (fields.cpp:1212-1216). The game
#: may cut further on pixel width (:1215), which is its own rule and
#: not mirrored — a longer name is silently shortened there, the one
#: comparison decision 33 would need is a font metric.
NAME_MAX = 29

#: How long the chain holds the watchdog while the keys go out and the
#: game writes the file: saving has no input loop.
SAVE_STEP_TIMEOUT_S = 30.0


def game_accepts(ch):
    """The characters the continuous input takes (fields.cpp:1206)."""
    return len(ch) == 1 and 0x20 <= ord(ch) <= 0x7E and ch != "_"


def is_save(fields):
    return nodes.classify(fields) == nodes.SAVE


class SaveEditor:
    def __init__(self, screen):
        self.screen = screen
        self.slot = None
        self.input = None
        self.chain = None

    def reset(self):
        self.reset_edit()
        self.chain = None

    def reset_edit(self):
        if self.chain is None:
            self.slot = None
            self.input = None

    @property
    def busy(self):
        return self.chain is not None

    def start(self, index):
        slots = gmdraw.slots_for(self.screen, nodes.SAVE)
        initial = ""
        if slots and slots[index]["status"] == 0:
            initial = "".join(c for c in slots[index]["description"]
                              if game_accepts(c))[:NAME_MAX]
        self.slot = index
        self.input = TextInput(value=initial, max_len=NAME_MAX,
                               allowed=game_accepts,
                               on_submit=self.commit, on_cancel=self.cancel)

    def commit(self, value=None):
        if self.slot is None or self.busy:
            return
        value = self.input.value if value is None else value
        strips = nodes.save_strips(self.screen.fields())
        if len(strips) != nodes.SLOTS or not self.screen.app.connected:
            return
        strip = strips[self.slot]
        keys = name_keys(value, clear=1)
        log.info("save: slot %d, %d keys after the strip activation",
                 self.slot + 1, len(keys))
        self.chain = InjectionChain(self.screen.app.client, [(
            "save name", is_save,
            lambda c, f: paced_keys(
                lambda client: client.activate_field(strip.index), keys),
            SAVE_STEP_TIMEOUT_S)])
        self.input.focused = False

    def cancel(self):
        self.reset_edit()
        self.screen.press("C")

    def update(self, game_state):
        if self.chain is None:
            return
        self.chain.update(game_state)
        if self.chain.failed:
            log.error("save: chain failed at '%s'", self.chain.failed_step)
        if self.chain.done or self.chain.failed:
            self.chain = None

    def handle_click(self, x, y):
        """True if the click belonged to the name entry."""
        if self.screen.node != nodes.SAVE:
            return False
        if self.busy:
            return True
        if self.slot is not None and gmdraw.hit(self.screen, "save_save",
                                                 x, y):
            self.commit()
            return True
        if gmdraw.hit(self.screen, "save_cancel", x, y):
            self.input = None
            self.slot = None
            return False
        index = gmdraw.row_at(self.screen, "slot_list", nodes.SLOTS, x, y)
        if index is None:
            return False
        if index == self.slot:
            self.commit()          # a second click on the row saves
        else:
            self.start(index)
        return True

    def handle_key_event(self, event):
        if self.screen.node != nodes.SAVE:
            return False
        if self.busy:
            return True
        if self.input is not None and self.input.focused:
            return self.input.handle_key_event(event)
        return False
