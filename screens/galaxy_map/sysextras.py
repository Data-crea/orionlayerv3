"""The star system window's gate icons and its space-monster branch — work
order 322 D, the two pieces the window had left out (they were OMISSION
`box_fields`, `boxdraw`).

THE GATE ICONS are not star gates: the window shows the ARTEMIS NET and the
DIMENSIONAL PORTAL, the two bitmasks over players a star carries
(`s_star_data.has_artemis_net` / `has_dimensional_portal`, orion2.h:2999-
3000; on the wire with the whole star, `core.structs.star`). A star gate and
a jump gate have no icon and no field (`Print_Gate_Info_`'s cases 1 and 2
are unreachable, sys.cpp:1695-1703).

  TRANSCRIPTION  `gate_icons`: drawn only in a viewable window, after the
                 fleet bar (sys.cpp:891-892), from the window's native
                 (0xE9, 0xF3) (`Get_Gate_Icon_XY_`, sys.cpp:941-950): the
                 Artemis Net 12 native px left of it, the portal 12 further
                 left (`Draw_Gate_Icons_`, :952-976). Only the portal's
                 PICTURE drops 1 px (:968-969); its field stays at the
                 icons' y (:1935-1943). Each field is `Add_Hidden_Field_(x,
                 y, x + 15, y + 15)` (:1919-1946), and a field's bounds are
                 inclusive (`Scan_Input_`, fields.cpp:694), so 16 x 16; the
                 first field in the list wins where two overlap (:690-696) —
                 the Artemis Net's, added first. The window's place and size
                 are boxes.json's (DEVIATION `box_layout`), so HD places the
                 icons from CLOSE, which the original puts at the window's
                 (0x107, 0xEC) (:1818-1824): they keep their place beside it
  TRANSCRIPTION  `gate_info`: the gate under the pointer, scanned LAST
                 (mainscr.cpp:2384-2402), prints H 0x17B "Artemis Net (" or
                 H 0x17C "Dimensional Portal (", then every player whose bit
                 is set, by race name, "name, " each, the last two
                 characters cut and ")" added — the original's own string
                 work, kept (sys.cpp:1681, :1708) — wrapped at the width of
                 the label, in a darkened box at the view's corner, in the
                 local player's colour (`Font_Colors2_(1, colour, colour +
                 6)`, :1660; :1717-1731)
  DEVIATION      `gate_icon_drawn`: the pictures (BUFFER0.LBX 33 and 21)
                 are the player's files and not extracted; HD draws the two
                 in code — a net of crossing lines, a ring round a dark eye
                 — each inside its 12 native px step, so they do not
                 overlap (16 px is the FIELD, not a measured sprite), unless
                 a mod ships `screens/galaxy_map/assets/gate_artemis.png` /
                 `gate_portal.png`. With seven or more owners at the star
                 the fleet bar's cells run under the icons; the gates are
                 drawn over the ships, as the original draws them after
                 the bar
  UNVERIFIED     `gate_icons_live` (Data's decision of 20 October 2026: no
                 live runs): a save with an Artemis Net or a Dimensional
                 Portal at a visited star, the icons and the line beside
                 the original's

THE MONSTER BRANCH: a window that may not be viewed shows, where the player
has visited a star whose special is the space monster (`Player_Sighted_
Monster_`, harold.cpp:430-439), not the star's description but the
special's popup, titled "Star System %s" (sys.cpp:736-776).

  TRANSCRIPTION  `monster_branch`: the special's name (`planet_special_
                 string[9]`, ESTRINGS 0x2C2, estrings.cpp:184) over its
                 description (MAINTEXT record 9, `System_Special_Desc_`,
                 mainpups.cpp:1257-1269; `Draw_System_Special_Popup_`,
                 sys.cpp:626-632)
  DEVIATION      `monster_in_view`: the original hides the view
                 (`Hide_System_Display_(…, 1)`, sys.cpp:756: a
                 `Diagonal_Line_Fill_` hatch, :704-711), draws the border in
                 mode 1 (:758) and the popup in its own frame with the
                 monster's picture (MAINPUPS.LBX 0 and `Star_To_Monster_ +
                 15`, mainpups.cpp:1271-1311) at the window's corner; HD
                 keeps its own view and frame (DATA'S DECISION
                 `system_window_look`, HD EXTENSION `system_view_picture`)
                 and prints the name and the description centred in the
                 view, no picture (not extracted)
  Reached only by an unviewable star the player has visited — a black hole
  (`Ok_To_View_System_`, sys.cpp:75-87) — carrying special 9, which no game
  holds: the generator gives a black hole no special (mapgen.cpp:1625-1627)
  and the game's start turns every special-9 star into a monster ship and
  puts the star's own special back (`Make_System_Monsters_Into_Ships_`,
  initgame.cpp:241, :541-562). Kept for a save edited by hand or a mod.
"""
import pygame

from core.structs import player as player_struct

H_ARTEMIS, H_PORTAL = 0x17B, 0x17C
#: The original's own gate numbers (`gate_icon_field[]`, sys.cpp:1928,
#: :1939), in the order the icons are laid out right to left.
GATES = (("artemis", 3, H_ARTEMIS, "has_artemis_net"),
         ("portal", 0, H_PORTAL, "has_dimensional_portal"))
#: Native px: the icons' anchor and CLOSE in the window; one icon's step,
#: its field's side (x .. x + 15, inclusive), the portal picture's drop.
ANCHOR = (0xE9, 0xF3)
CLOSE = (0x107, 0xEC)
STEP, SIDE, PORTAL_DROP = 12, 16, 1
SPECIAL_MONSTER = 9
E_MONSTER = 0x2C2
PICTURES = {"artemis": "screens/galaxy_map/assets/gate_artemis.png",
            "portal": "screens/galaxy_map/assets/gate_portal.png"}
#: The drawn icons' colours (DEVIATION `gate_icon_drawn`): the window's
#: blue lettering for the net, a violet for the portal's ring.
NET_COLOUR = (104, 140, 176)
PORTAL_COLOUR = (150, 110, 200)


def gates(star):
    """[(kind, gate number, H id, mask)] the star carries, in layout order."""
    out = []
    for kind, number, hid, member in GATES:
        mask = int(getattr(star, member, 0) or 0)
        if mask:
            out.append((kind, number, hid, mask))
    return out


def places(close, s, star):
    """[(field, kind, gate number, H id, mask, picture)]: each icon's field
    (16 native px, at the icons' y) and the square its picture is drawn in
    (one 12 px step, the portal's 1 px lower), placed from CLOSE's rect by
    the original's native offsets at scale `s`."""
    out = []
    x = close.x + (ANCHOR[0] - CLOSE[0]) * s
    y = close.y + (ANCHOR[1] - CLOSE[1]) * s
    side = max(4, int(round(SIDE * s)))
    step = max(3, int(round((STEP - 1) * s)))
    for kind, number, hid, mask in gates(star):
        x -= STEP * s
        drop = PORTAL_DROP * s if kind == "portal" else 0
        fx, fy = int(round(x)), int(round(y))
        out.append((pygame.Rect(fx, fy, side, side), kind, number, hid, mask,
                    pygame.Rect(fx, int(round(y + drop)), step, step)))
    return out


def gate_text(label, mask, race_names):
    """`Print_Gate_Info_`'s string (sys.cpp:1680-1715), its quirks kept:
    the label, "name, " per player whose bit is set, two characters cut,
    ")" added."""
    text = label or ""
    for i, name in enumerate(race_names):
        if (mask >> (i & 0x1F)) & 1:
            text += f"{name}, "
    return text[:-2] + ")"


def race_names(state):
    """The race names of the game's players, in player order."""
    players = getattr(state, "player_raw", None) or []
    count = int(getattr(state, "num_players", 0) or 0) or len(players)
    return [player_struct.parse(raw).race_name
            for raw in players[:count]]


def _picture(screen, kind, side):
    """A mod's picture of the icon, through the resource roots (decision
    16), as `sysstars`' picture; None without one."""
    from core import resources
    res = getattr(resources, "res", None)
    path = res.resolve(PICTURES[kind]) if res is not None else None
    if not path:
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None
    return pygame.transform.smoothscale(img, (side, side))


def _drawn(surface, rect, kind):
    """DEVIATION `gate_icon_drawn`: the icon in code."""
    c = rect.center
    r = max(2, rect.w // 2 - 1)
    t = max(1, rect.w // 10)
    if kind == "artemis":
        # LOOK EXCEPTION picture: the Artemis Net's icon, drawn for BUFFER0.LBX 33 (not extracted)
        pygame.draw.circle(surface, NET_COLOUR, c, r, t)
        for k in (-1, 0, 1):
            off = k * r // 2
            # LOOK EXCEPTION picture: the net's threads, drawn for BUFFER0.LBX 33
            surface.fill(NET_COLOUR, (c[0] - r + t, c[1] + off, 2 * (r - t), t))
            # LOOK EXCEPTION picture: the net's threads, drawn for BUFFER0.LBX 33
            surface.fill(NET_COLOUR, (c[0] + off, c[1] - r + t, t, 2 * (r - t)))
    else:
        # LOOK EXCEPTION picture: the portal's icon, drawn for BUFFER0.LBX 21 (not extracted)
        pygame.draw.circle(surface, PORTAL_COLOUR, c, r, max(t, r // 3))
        # LOOK EXCEPTION picture: the portal's dark eye
        pygame.draw.circle(surface, (10, 4, 20), c, max(1, r // 2))


def draw_gates(screen, surface, close, s, star):
    """The icons beside CLOSE; returns their fields (see `places`)."""
    hits = places(close, s, star) if star is not None else []
    for _field, kind, _n, _h, _m, pic in hits:
        img = _picture(screen, kind, pic.w)
        if img is not None:
            surface.blit(img, pic.topleft)
        else:
            _drawn(surface, pic, kind)
    return hits


def gate_hover(screen, surface, view, state, hits, pointer, text):
    """TRANSCRIPTION `gate_info`: the gate under the pointer, its line in
    the darkened box at the view's corner. True if one was."""
    from core import textfit
    from screens.galaxy_map import sysfleets, syswindow
    over = next((h for h in hits if h[0].collidepoint(pointer)), None)
    if over is None or state is None:
        return False
    label = (text.message(over[3]) if text is not None else None) or ""
    words = gate_text(label, over[4], race_names(state))
    size = syswindow.font(screen, "system_text", 16)
    width = screen.style.render_text(label, size, (255, 255, 255)).get_width()
    lines = textfit.wrap_text(screen.style, words, size, width + 2)
    me = getattr(state, "player_num", 0)
    colour = syswindow.owner_colour(sysfleets.player_colour_index(state, me))
    syswindow.info_box(screen, surface, view,
                       [(line, False) for line in lines], colour)
    return True


def sighted_monster(star, me):
    """`Player_Sighted_Monster_` (harold.cpp:430-439)."""
    from core.structs import star as star_struct
    return (int(getattr(star, "system_special", 0)) == SPECIAL_MONSTER
            and star_struct.visited_by(star, me))


def language(screen):
    return (getattr(getattr(screen, "app", None), "settings", None)
            or {}).get("language", "en")


def monster_words(screen):
    """(name, description) of the monster special in the player's
    language, read once per language (as `sysfleets.part_names`); None for
    a word the install lacks."""
    from core.estrings import EStrings
    from core.maintext import MainText
    lang = language(screen)
    cached = getattr(screen, "_monster_words", None)
    if not isinstance(cached, dict):
        cached = screen._monster_words = {}
    if lang not in cached:
        cached[lang] = (EStrings(lang).string(E_MONSTER),
                        MainText(lang).description(SPECIAL_MONSTER))
    return cached[lang]


def draw_monster(screen, surface, view, colour, name_colour):
    """TRANSCRIPTION `monster_branch` with DEVIATION `monster_in_view`: the
    special's name over its description, centred in the view."""
    from core import textfit
    from screens.galaxy_map import syswindow
    name, desc = monster_words(screen)
    size = syswindow.font(screen, "system_view", 16)
    surfs = []
    if name:
        surfs.append(screen.style.render_text(name, size, name_colour))
    for line in (textfit.wrap_text(screen.style, desc, size,
                                   int(view.w * 0.9)) if desc else []):
        surfs.append(screen.style.render_text(line, size, colour))
    y = view.y + (view.h - sum(sf.get_height() for sf in surfs)) // 2
    for sf in surfs:
        surface.blit(sf, (view.x + (view.w - sf.get_width()) // 2, y))
        y += sf.get_height()
    return bool(surfs)
