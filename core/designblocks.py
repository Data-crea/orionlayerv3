"""The Ship Designer's two blocks in the snapshot — open fixes 44 and 45
(work order 185; applied by work order 186, orion2re `70d31b10`, `4af9fefa`).

    "DSGN"  open fix 44 (`doc/ext_ship_designer_state.patch`): while the
            game's `_current_screen` is SCREEN_DESIGN — the design being
            edited (`MOX::_design`), the slot and the refit flag, the two
            numbers the bottom line prints, the values the main page
            computes at draw time, and per weapon row the damage and
            modification strings the engine formats.
    "DSBX"  open fix 45 (`doc/ext_ship_designer_boxes.patch`): while one of
            the three sub-dialogs reports its synthetic id (54 shield or
            computer, 55 weapon, 56 special system) — which box, its list
            and per row the numbers it prints, the chosen and hovered row,
            the weapon's arcs, rack and modifications (and which it
            offers), the filters, the scroll.

Read in the order `SerializeState` writes them (block 12, then 13), after
the colony blocks, each WHOLE or left None — `core/colonyblocks.py`'s rule
and FLTS's reason: a half-read block would draw a design from half its
data without saying so. An engine without the fixes writes neither, and
both keys stay None: the Ship Designer then keeps the game's own picture
(the safety net), as it did before there was an HD screen for it.

The layout is the patch's, field for field; the smoke test holds this
reader to a block built by the same field list, and the live recording of
work order 185 part 6 to the scratch engine's own bytes.
"""
import struct as _st

from core import lang

#: `WEAPON_MOD_COUNT` (orion2_consts.h:1057, and its static_assert at
#: :1391): the modification statuses DSBX carries.
WEAPON_MOD_COUNT = 15

#: The synthetic ids open fix 45 reports for the three sub-dialogs.
BOX_IDS = {54: "generic", 55: "weapon", 56: "special"}

MAIN_FIELDS = ("size", "picture", "shield", "ftl", "computer", "armor",
               "fuel")
STAT_FIELDS = ("warp_speed", "combat_speed", "structure", "armor_points",
               "shield_strength", "shield_blocked", "beam_attack",
               "beam_defense", "missile_evasion")


def parse(gs, data, pos):
    """Read DSGN and DSBX at `pos` into `gs.ship_design` / `gs.design_box`
    (None each when absent or short). Returns the new position."""

    def take(fmt):
        nonlocal pos
        size = _st.calcsize("<" + fmt)
        if pos + size > len(data):
            raise ValueError("short")
        vals = _st.unpack_from("<" + fmt, data, pos)
        pos += size
        return vals

    def text():
        (n,) = take("B")
        (raw,) = take(f"{n}s")
        return lang.wire_text(raw)

    def block(tag, reader):
        nonlocal pos
        if data[pos:pos + 4] != tag:
            return None
        start = pos
        pos += 4
        try:
            return reader()
        except ValueError:
            pos = start
            return None

    def dsgn():
        version, slot, refit, cost, space_avail = take("BhBii")
        if version != 1:
            raise ValueError("version")
        (name,) = take("16s")
        out = {"slot": slot, "refit": bool(refit), "printed_cost": cost,
               "printed_space_available": space_avail,
               "name": lang.wire_text(name.split(b"\0", 1)[0])}
        out.update(zip(MAIN_FIELDS, take("7h")))
        out.update(zip(("hull_space", "space_used", "total_cost"),
                       take("3i")))
        out.update(zip(STAT_FIELDS, take("9h")))
        weapons = []
        for _ in range(8):
            wtype, count, arc, specials, wcost, wspace, ammo = \
                take("hhbHiib")
            weapons.append({"type": wtype, "count": count, "arc": arc,
                            "mods": specials, "cost": wcost, "space": wspace,
                            "ammo": ammo, "damage": text(),
                            "mods_text": text()})
        out["weapons"] = weapons
        out["specials"] = list(take("8h"))
        return out

    def dsbx():
        version, kind = take("BB")
        if version != 1 or kind not in (1, 2, 3):
            raise ValueError("version")
        out = {"kind": {1: "generic", 2: "weapon", 3: "special"}[kind]}
        out.update(zip(("replacement_type", "slot", "item", "first_row",
                        "visible_rows", "chosen", "scanned", "mods", "arcs",
                        "rack"), take("10h")))
        out["filters"] = list(take("4B"))
        out["mod_status"] = list(take(f"{WEAPON_MOD_COUNT}h"))
        (offered,) = take("H")
        out["mods_offered"] = [i for i in range(1, WEAPON_MOD_COUNT)
                               if offered >> i & 1]
        (n,) = take("h")
        if not 0 <= n <= 40:
            raise ValueError("count")
        rows = []
        for _ in range(n):
            item, selected, unlocked, cost, space, extra = take("hBBiih")
            rows.append({"item": item, "selected": bool(selected),
                         "unlocked": bool(unlocked), "cost": cost,
                         "space": space, "extra": extra, "text": text()})
        out["rows"] = rows
        return out

    gs.ship_design = block(b"DSGN", dsgn)
    gs.design_box = block(b"DSBX", dsbx)
    return pos
