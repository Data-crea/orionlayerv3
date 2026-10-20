"""The evolutionary mutation's TPOP tail — open fix 107 (work order 318).

The wire half of the Custom Race screen's mutation mode
(`screens/custom_race/mutation.py`): kind 23 of open fix 49's "TPOP" block,
reported as id 83 while `raceopt::Evolutionary_Mutation_Screen` runs
(raceopt.cpp:213-420, the human player's branch of
`Setup_Evolutionary_Upgrade`, :188-211, from report.cpp:537 when
Evolutionary Mutation is researched). raceopt.cpp's lines here are
v2.0.0's; open fix 107 itself moves them. The layout is
`doc/ext_evolutionary_mutation.patch`'s header, byte by byte:

    args  [0] orig_picks, [1]..[10] the baseline flags 0-9 — fixed for the
          screen's life (raceopt.cpp:223-232): flag 0 (args[1]) is the
          government's trait value, `traits[0] & 0x0E` (:200), not a pick
          index; group g's flag is baseline[g + 1], i.e. args[g + 2] — its
          level 1-3 where the race's trait matches one, else the raw trait
          byte (:226-232)
    tail  int16 picks, int16 negative_picks, 10 x int16 button_variable,
          22 x int16 option_toggle, 36 x int16 group_button, 22 x int16
          option_button, int16 accept — raceopt's globals, written on every
          snapshot because each input changes them and the loop adds the
          fields again (:402)

`group_button[g * 4 + l]` is group g's level l (1-3); `[g * 4]` is the
group's head, always -1000 (`Add_Race_Options_Fields_EM`, :1199-1202). A
field of -1000 was not added: the screen does not offer that option
(:1219-1234 the groups, :1262-1306 the special abilities).
"""
import struct as _st

#: The nine primary groups (`e_primary_pick`, raceopt.h), the 22 special
#: abilities (`e_special_pick`), the group_button entries per group (the
#: head and three levels) — the sizes the engine's static_asserts hold.
GROUPS, SPECIALS, PER_GROUP = 9, 22, 4
#: A field the engine did not add (`Add_Race_Options_Fields_EM`).
NOT_ADDED = -1000
TAIL = "<hh10h22h36h22hh"
TAIL_SIZE = _st.calcsize(TAIL)          # 186


def read_tail(take):
    """The tail after TPOP's title and text; `take(fmt)` is the block
    reader's."""
    vals = take(TAIL[1:])
    picks, negative = vals[0], vals[1]
    at = 2
    buttons = list(vals[at:at + 10])
    at += 10
    toggles = list(vals[at:at + SPECIALS])
    at += SPECIALS
    groups = list(vals[at:at + GROUPS * PER_GROUP])
    at += GROUPS * PER_GROUP
    options = list(vals[at:at + SPECIALS])
    at += SPECIALS
    return {"picks": picks, "negative_picks": negative,
            "button_variable": buttons, "option_toggle": toggles,
            "group_button": groups, "option_button": options,
            "accept": vals[at]}


def build_tail(m):
    """The tail as the engine writes it — for the checks' stand-ins."""
    return _st.pack(TAIL, m["picks"], m["negative_picks"],
                    *m["button_variable"], *m["option_toggle"],
                    *m["group_button"], *m["option_button"], m["accept"])


def orig_picks(popup):
    """args[0]: the picks the screen opened with (`Calculate_EM_Picks`
    before the first input), the bound every offer is held to."""
    return popup["args"][0]


def baseline(popup):
    """args[1..10]: the baseline flags 0-9 as raceopt.cpp:223-232 left
    them — [0] the government's trait value (`traits[0] & 0x0E`, :200),
    [g + 1] group g's level 1-3, or its raw trait byte where it matches no
    level (:226-232)."""
    return list(popup["args"][1:11])


def group_field(m, group, level):
    """The field of group `group`'s level `level` (1-3), or None when the
    screen does not offer it."""
    f = m["group_button"][group * PER_GROUP + level]
    return f if f > 0 else None


def option_field(m, index):
    """Special ability `index`'s field (`e_special_pick` order), or None."""
    f = m["option_button"][index]
    return f if f > 0 else None
