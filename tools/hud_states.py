"""Stand-in states for `hud_evidence.stage`, for the screens work order 188
added (the Hall of Fame on open fix 50's HOFM, the multiplayer setup read off
its own list) — split out so `hud_evidence.py` stays under the 300-line
guideline. Stand-in words only: no game text.
"""


def hof_state():
    """The Hall of Fame with STAND-IN rows (no game text): open fix 50's
    HOFM as the engine writes it, the entry 3 flashing."""
    from core import hofblocks
    from core.game_state import GameState
    gs = GameState()
    gs.current_screen = 14
    rows = [{"record": 9 - i, "score": 1600 - 110 * i, "difficulty": i % 5,
             "name": f"Name {i + 1}", "race": "Race",
             "difficulty_word": "Level"} for i in range(10)]
    hofblocks.parse(gs, hofblocks.build(rows, flash=6), 0)
    return gs


def mp_state():
    """The multiplayer setup (15) as its own list names it (Network)."""
    import types
    from core.game_state import GameState
    gs = GameState()
    gs.current_screen = 15
    gs.fields = [types.SimpleNamespace(index=i + 1, hotkey=hk, field_type=7,
                                       x=10 * i, y=10 * i, x_end=10 * i + 9,
                                       y_end=10 * i + 9)
                 for i, hk in enumerate((ord("N"), ord("M"), ord("H"), 0x1B,
                                         ord("S"), ord("L"), ord("J")))]
    return gs
