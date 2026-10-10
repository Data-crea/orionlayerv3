"""Keys to the game — ONE mechanism for every HD screen (work order 230 E).

A key an HD screen does not answer itself comes here (`ScreenBase.
handle_key`, the default every screen falls back to). What the original
does with a key is `fields::Interpret_Keyboard_Input_` and `Interpret_
Mouse_Input_` (fields.cpp:976-1244, :2545-2642; `dev:doc/briefs/
230-keys.md` per screen). HD passes a key on only where the original's
answer is a field of the list that stands NOW, so the engine acts on the
key exactly as on the player's own:

  TRANSCRIPTION  a printable key: passed (INJECT_KEY, its character) when
                 the live list has a field with that hotkey — the engine's
                 own first-match rule picks the field (:2602-2635); none
                 has it: nothing, as in the original
  TRANSCRIPTION  while a text field is edited (open fix 88's TXTF says
                 which): printable keys but '_', Backspace, Enter (stores
                 the name, :1057-1068) and ESC (restores it, :1180-1190) go
                 to it; hotkeys are off then, in the original too
  F904           Enter with no text field edited presses the field under the
                 ENGINE's pointer (:1057-1152), which HD does not know: never
                 passed
  F908           ESC can cascade across sub-screens: passed only when the
                 live list has an ESC field (hotkey 0x1B), once per press;
                 the engine presses that field, as the player's ESC does
  TRANSCRIPTION  Alt+letter: passed (open fix 89's raw code, scan << 8)
                 when the live list has a multi-hotkey field — the engine's
                 own rule, multi-hotkeys answer only Alt+letters (:2593-
                 2600): Alt+Q, Alt+V, the cheats, the hall of fame's Alt+C
  TRANSCRIPTION  F1-F10 and Alt+F1-F10: passed (open fix 89) only where
                 `ENGINE_FKEYS` names them for the screen; the rest are
                 HD's own (F5, F8, F9, F11, F12 — main.py, before any screen)
                 or parked (`PARKED_FKEYS`, with both meanings)

`ENGINE_FKEYS` and `PARKED_FKEYS` are the one table; smoke check 090zzze
holds it to `dev:doc/briefs/230-keys.md` and to the code.
"""
import logging

import pygame

log = logging.getLogger("orionlayer")

TYPE_MULTI_HOTKEY = 8
ESC, ENTER, BACKSPACE = 27, 13, 8
#: platform.cpp:420-450, :455-492: F1-F10 and Alt+F1-F10 as the engine's
#: platform layer translates them.
F_CODE, ALT_F_CODE = 0x3B00, 0x6800
#: platform.cpp:470-495: Alt+letter -> the letter's PC scan code << 8.
ALT_SCAN = {"Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13, "T": 0x14,
            "Y": 0x15, "U": 0x16, "I": 0x17, "O": 0x18, "P": 0x19,
            "A": 0x1E, "S": 0x1F, "D": 0x20, "F": 0x21, "G": 0x22,
            "H": 0x23, "J": 0x24, "K": 0x25, "L": 0x26, "Z": 0x2C,
            "X": 0x2D, "C": 0x2E, "V": 0x2F, "B": 0x30, "N": 0x31,
            "M": 0x32}

#: The F keys HD passes on, per screen: (key name, why it is safe).
ENGINE_FKEYS = {
    "galaxy_map": {
        "F4": "merge-relocations on or off, or the engine's box when there "
              "is one relocation (mainscr.cpp:3112-3129) — HD's message box",
        "F10": "saves into SAVE10.GAM (slot index 9) and says so in a box "
               "(:3065-3074) — HD's message box; the player's own save",
        "Alt+F1": "a game option on or off; the engine says so in its "
                  "box (:3247-3251, :3237-3302) — HD's message box",
        "Alt+F2": "a game option on or off; the engine says so in its "
                  "box (:3253-3257, :3237-3302) — HD's message box",
        "Alt+F3": "a game option on or off; the engine says so in its "
                  "box (:3259-3263, :3237-3302) — HD's message box",
        "Alt+F5": "a game option on or off; the engine says so in its "
                  "box (:3265-3269, :3237-3302) — HD's message box",
        "Alt+F6": "a game option on or off; the engine says so in its "
                  "box (:3271-3275, :3237-3302) — HD's message box",
        "Alt+F7": "a game option on or off; the engine says so in its "
                  "box (:3277-3284, :3237-3302) — HD's message box",
        "Alt+F8": "a game option on or off; the engine says so in its "
                  "box (:3286-3290, :3237-3302) — HD's message box",
        "Alt+F9": "the autosave (mainscr_main.cpp:617-626) — a box",
        "Alt+F10": "loads the last saved game (:628-630) — the player's own",
    },
    "fleets": {
        "F1": "the previous fleet (flt1.cpp:761-770) — the screen follows "
              "the engine's fleet",
        "F2": "the next fleet (:749-759)",
        "Alt+F5": "clears every star's relocation, with a box (:597-601)",
    },
}
#: The F keys parked for Data: (key name, the original's meaning, HD's).
PARKED_FKEYS = {
    "galaxy_map": {
        "F1": ("the previous ship stack, its fleet box opened "
               "(mainscr.cpp:3141-3149)",
               "nothing: a fleet box the engine opens has no HD click to "
               "name it, and HD would draw no box"),
        "F2": ("the next ship stack, its fleet box opened (:3131-3139)",
               "nothing, as F1"),
        "F5": ("the previous own star: its colony or its system window "
               "(:3097-3110)", "HD's layout editor (main.py)"),
        "F6": ("the next own star (:3082-3095)",
               "nothing: a system window the engine opens has no HD click "
               "to name it"),
        "F9": ("the distance between stars (:3076-3080, screen 28, no HD "
               "view)", "HD's window size (main.py)"),
    },
    "fleets": {
        "F5": ("merge-relocations on or off (flt1.cpp:602-610)",
               "HD's layout editor (main.py)"),
    },
}


def _fields(screen):
    st = getattr(screen.app.client, "state", None) if \
        getattr(screen.app, "client", None) is not None else None
    return list(getattr(st, "fields", None) or []), st


def editing(state):
    """The text field being edited (open fix 88), or None."""
    for entry in (getattr(state, "text_fields", None) or {}).values():
        if entry["editing"]:
            return entry
    return None


def fkey_name(event):
    if pygame.K_F1 <= event.key <= pygame.K_F10:
        n = event.key - pygame.K_F1 + 1
        alt = bool(getattr(event, "mod", 0) & pygame.KMOD_ALT)
        return ("Alt+" if alt else "") + f"F{n}"
    return None


def decide(screen_name, fields, state, event):
    """(how, value, why) for one key: how is "key" (INJECT_KEY value),
    "raw" (open fix 89's code) or None (nothing sent)."""
    name = fkey_name(event)
    if name is not None:
        if name in ENGINE_FKEYS.get(screen_name, {}):
            n = int(name.split("F")[-1]) - 1
            code = (ALT_F_CODE if name.startswith("Alt+") else F_CODE) \
                + (n << 8)
            return "raw", code, ENGINE_FKEYS[screen_name][name]
        return None, None, "not passed on this screen"
    ch = getattr(event, "unicode", "") or ""
    alt = bool(getattr(event, "mod", 0) & pygame.KMOD_ALT)
    entry = editing(state)
    if entry is not None:
        if event.key == pygame.K_BACKSPACE:
            return "key", BACKSPACE, "into the text field"
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "key", ENTER, "stores the text field"
        if event.key == pygame.K_ESCAPE:
            return "key", ESC, "restores the text field"
        if len(ch) == 1 and 32 <= ord(ch) < 127 and ch != "_" and not alt:
            return "key", ord(ch), "into the text field"
        return None, None, "a text field is edited"
    if alt:
        letter = pygame.key.name(event.key).upper() if \
            pygame.K_a <= event.key <= pygame.K_z else ""
        if letter in ALT_SCAN and any(
                getattr(f, "field_type", None) == TYPE_MULTI_HOTKEY
                for f in fields):
            return "raw", ALT_SCAN[letter] << 8, "a multi-hotkey field stands"
        return None, None, "no multi-hotkey field"
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return None, None, "F904: Enter presses the field under the engine's pointer"
    if event.key == pygame.K_ESCAPE:
        if any(getattr(f, "hotkey", 0) == ESC and getattr(f, "index", 0)
               for f in fields):
            return "key", ESC, "the list's ESC field"
        return None, None, "F908: no ESC field in the list"
    if len(ch) == 1 and 32 <= ord(ch) < 127:
        want = ord(ch.upper())
        if any(getattr(f, "hotkey", 0) == want and getattr(f, "index", 0)
               for f in fields):
            return "key", ord(ch), "a field with this hotkey"
        return None, None, "no field with this hotkey"
    return None, None, "not a key the original answers"


def forward(screen, event):
    """Pass `event` on as `decide` says; True if something was sent."""
    if event is None or not getattr(screen.app, "connected", False):
        return False
    fields, state = _fields(screen)
    how, value, why = decide(getattr(screen, "SCREEN_NAME", ""), fields,
                             state, event)
    if how is None:
        return False
    log.info("key %s on %s -> %s %s (%s)", pygame.key.name(event.key),
             getattr(screen, "SCREEN_NAME", "?"), how, value, why)
    if how == "raw":
        screen.app.client.inject_raw_key(value)
    else:
        screen.app.client.inject_key(value)
    return True
