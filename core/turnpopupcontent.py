"""What each turn-time popup shows — open fix 49 (work order 188).

The content half of `core/turnpopup.py` (split for decision 6): from a
popup (TPOP) and the snapshot, a title, lines, options and buttons, each
bound to the popup's OWN field — see `core/turnpopup.py` for the rules.
"""
DEFAULT_WORDS = {"close": "CLOSE",
                 "prev": "PREV", "next": "NEXT", "continue": "CONTINUE",
                 "hire": "HIRE", "reject": "REJECT",
                 "turn_summary": "TURN SUMMARY",
                 # the colony combat popup's buttons (work order 232 C:
                 # MAINPUPS.LBX 0x52, 0x36, 0x37, 0x35, 0x50, 0x4F, 0x3C)
                 "inv_close": "CANCEL", "inv_invade": "INVADE",
                 "inv_bomb": "BOMBARD", "inv_destroy": "DESTROY",
                 "inv_mind_control": "MIND CONTROL",
                 "inv_drop_all": "DROP ALL", "inv_cease_fire": "HALT",
                 "inv_bomb_hits": "BOMBARD",
                 # the slider popup's buttons (work order 316 E: MAINPUPS.LBX
                 # 0x4A down, 0x4B up, 0x4C cancel, 0x4D accept, art; the
                 # fourth reads ACCEPT in the live framebuffer of the
                 # freighter scrap, work order 316)
                 "slider_down": "-", "slider_up": "+",
                 "slider_cancel": "CANCEL", "slider_ok": "ACCEPT",
                 # the Space Dragon's bribe (work order 319: MAINPUPS.LBX
                 # 0x46 refuse / close, 0x47 yes, art)
                 "dragon_no": "NO", "dragon_yes": "YES"}


def _star_name(state, index):
    stars = getattr(state, "stars", None) or []
    return stars[index].name if 0 <= index < len(stars) else "?"


def _planet_name(state, planet_index):
    from core.structs import planet as planet_struct
    from core.colonyfacts import star_planet_name
    planets = getattr(state, "planets_raw", None) or []
    stars = getattr(state, "stars", None) or []
    if not 0 <= planet_index < len(planets):
        return "?"
    planet = planet_struct.parse(planets[planet_index])
    if not 0 <= planet.star_index < len(stars):
        return "?"
    return star_planet_name(stars[planet.star_index], planet_index)


def _leader_name(state, index):
    from core.structs import leader as leader_struct
    raw = getattr(state, "leaders_raw", None) or []
    if not 0 <= index < len(raw):
        return "?"
    return leader_struct.parse(raw[index]).name


def _leader_words(app):
    """ESTRINGS and HESTRNGS as the Leaders screen reads them — HESTRNGS
    the App's one instance (`hestrings.for_app`, D17), cached on the App."""
    words = getattr(app, "_turnpopup_words", None) if app is not None \
        else None
    if words is None:
        from core import estrings, hestrings
        from screens.leaders import ldrrows
        lang = (getattr(app, "settings", {}) or {}).get("language", "en")
        words = ldrrows.Words(estrings.EStrings(lang),
                              hestrings.for_app(app) if app is not None
                              else None, lang)
        if app is not None:
            app._turnpopup_words = words
    return words


#: `planet_special_string[special]` is ESTRINGS 0x2B9 + the special
#: (estrings.cpp:175-187), the special popup's title (sys.cpp:626-632).
E_SPECIAL_NAME = 0x2B9
SPECIALS = 12


def _special_name(app, special):
    """The system special's name in the player's language, or None."""
    try:
        special = int(special)
    except (TypeError, ValueError):
        return None
    if not 0 < special < SPECIALS:
        return None
    lang = (getattr(app, "settings", {}) or {}).get("language", "en")
    held = getattr(app, "_turnpopup_estrings", None) if app is not None \
        else None
    # one table per language, read once (as `sysfleets.part_names`)
    if not held or held[0] != lang:
        from core import estrings
        held = (lang, estrings.EStrings(lang))
        if app is not None:
            app._turnpopup_estrings = held
    return held[1].string(E_SPECIAL_NAME + special) or None


def _warlord_of(state, player):
    """`_player[player].traits[TRAIT_WARLORD]` (officer.cpp:93) — the hire
    popup's leaders are nobody's, but the level popup's is the player's own
    and `Owned_Officer_Level` (officer.cpp:152-172) counts the trait."""
    from core.structs import player as player_struct
    raws = getattr(state, "player_raw", None) or []
    if not 0 <= int(player) < len(raws):
        return False
    traits = player_struct.traits(player_struct.parse(raws[player]))
    return bool(traits[30]) if len(traits) > 30 else False


def leader_card(state, index, app=None):
    """The hire popup's card (officer.cpp:449-461, :3747-3837): the title
    `Leader_Name_` prints, the skill rows as `Print_Officer_Data_` does,
    the portrait, and the question — HESTRNGS 0x124 / 0x125 formatted with
    the name and the ENGINE'S cost and upkeep (TPOP args 1 and 8)."""
    from core import leaderskills as ls
    from core.structs import leader as leader_struct
    from screens.leaders import ldrrows
    raw = getattr(state, "leaders_raw", None) or []
    if not 0 <= index < len(raw):
        return {"title": "?", "skills": [], "portrait": None,
                "question": lambda c, u: None}
    rec = leader_struct.parse(raw[index])
    words = _leader_words(app)
    level = ls.shown_level(rec, index, lambda p: _warlord_of(state, p))
    title_word = words.estring(ls.level_name_estring(rec, level)) or ""
    the_word = ldrrows.the_word(words, index)
    name = ls.leader_name(rec, title_word, the_word)
    skills = []
    for sid in ls.displayed_skills(rec):
        value = ldrrows.skill_value(sid, level, words.unit)
        skills.append(((words.estring(ls.SKILL_NAME_ESTRINGS[sid]) or ""),
                       value))

    def question(cost, upkeep):
        template = words.hstring(0x124 if upkeep == 1 else 0x125)
        if not template or cost < 0:
            return None
        from core.hestrings import printf
        return printf(template, name, cost, upkeep)
    portrait = None
    try:
        from screens.leaders import ldrart
        art = ldrart.load()
        if art is not None and art.available:
            portrait = art.portrait(rec.pict_num)
    except Exception:       # absent extraction: no picture, stated
        portrait = None
    return {"title": name, "skills": skills, "portrait": portrait,
            "leader": rec, "question": question,
            # `Leader_Name_(idx, 0)`: the level title and name, no title
            "short_name": ls.leader_name(rec, title_word)}


#: TRANSCRIPTION `leader_level_line` (work order 315 C2) — the sentence
#: `Draw_Officer_Gains_Level_Popup_` prints under the card by its state
#: (TPOP arg 1, mainpups.cpp:1191): 0 gains a level, ESTRINGS 1 (:2229);
#: 1 a marooned hero joins, 0x248 (:2233, `Marooned_Officer_Joins_Popup_`
#: :2098-2102); 2 a hero with no room, 0x249 (:2237, :2092-2096).
LEVEL_LINE_ESTRINGS = {0: 0x1, 1: 0x248, 2: 0x249}


def leader_level_line(card, how, app=None):
    """The level popup's sentence, `printf`ed with the name as
    `Leader_Name_(idx, 0)` gives it; without the string (no extraction,
    an unknown state, where the original leaves its buffer as it was)
    the name alone, as before work order 315."""
    name = card.get("short_name") or card["title"]
    sid = LEVEL_LINE_ESTRINGS.get(how)
    template = _leader_words(app).estring(sid) if sid is not None else None
    if not template:
        return name
    from core.hestrings import printf
    return printf(template, name)


def _tech_name(tech):
    try:
        from core import lang, technames
        # in the language shown (the German walk found this one English)
        return technames.TechNames(lang.current()).application_name(
            tech & 0x1FF)
    except Exception:
        return None


def _field(state, index):
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == index and index > 0), None)


#: TRANSCRIPTION `popup_right` (work order 200 B) — what a right click on a
#: popup does in the original. The whole-screen help entries:
#: Turn_Summary_Popup_Help_ 247 (billhelp.cpp:26, turnsum.cpp:151),
#: the planet choice's 563 (erichelp.cpp:110, mainpups.cpp:1676), the
#: officer popups' 564 (erichelp.cpp:114, mainpups.cpp:305-309). Per item
#: (`content`'s "right", a right click on the item's own field, its answer a
#: box on the wire — `core/rightinfo`): a planet of the discovery or the
#: defence choice, `Potential_Colony_Info_Popup_` (mainpups.cpp:2013,
#: :2937-2944 -> mainscr.cpp:2105); a leader offer's HIRE / REJECT, its
#: `Text_Box_` (mainpups.cpp:954-982), and its skill lines, the skill's
#: help (`line_right`); the landing, which any input ends
#: (colland.cpp:227-232). The science room and GNN deactivate help and read
#: only positive fields (science.cpp:178, events.cpp:2573, :2604): nothing.
#: The troop popup's id, open fix 98 (`core.turnpopupwire.IDS`).
TROOPS_ID = 71

RIGHT_HELP = {"turn_summary": 247, "planet_choice": 563,
              "leader_level": 564,
              # the Space Dragon's bribe: 561 over the whole screen
              # (erichelp.cpp:45-47, set at mainpups.cpp:521)
              "dragon_bribe": 561}


def _act(state, index, how="activate"):
    f = _field(state, index)
    return (how, f) if f is not None else None


def _anywhere(state):
    """The full-screen field a popup that ends on any click answers on."""
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", 0) > 0 and (f.x, f.y, f.x_end,
                                                    f.y_end) ==
                 (0, 0, 639, 479)), None)


def _science(popup, state, words, app, anywhere):
    a = popup["args"]
    n = max(0, a[0])
    names = []
    i = 3
    while i < 16 and len(names) < n:
        tech = a[i]
        i += 1
        if tech < 0:
            continue
        names.append(_tech_name(tech) or f"#{tech & 0x1FF}")
        # TRANSCRIPTION `science_weapon_mod` (work order 315 C2): a
        # weapon-modification entry is listed by its weapon's name, as
        # the room shows its help entry `& 0x1FF` (science.cpp:301-307,
        # :320); its next slot is the mask, not an entry (:323-325).
        # OMISSION `science_mod_names`: the mask's modification names
        # (`weapon_modifications[].name`, :327-336) are not listed
        if tech & 0x4000:
            i += 1
    lines = [f"• {nm}" for nm in names]
    if popup.get("text"):
        lines = [""] + lines
        lines = [popup["text"]] + lines
    return {"lines": lines,
            "buttons": [(words["continue"], ("activate", anywhere)
                         if anywhere else None)]}


def _turn_summary(popup, state, words, app, anywhere):
    a = popup["args"]
    options, buttons = [], []
    page = a[0]
    for m in popup.get("messages", []):
        if m["page"] != page:
            continue
        target = None
        if m["jumps"] and m["first_field"] > 0:
            target = _act(state, m["first_field"], "click")
        options.append((m["text"], target))
    if a[1] > 1:
        buttons.append((words["prev"], _act(state, a[2], "click")
                        if page > 1 else None))
        buttons.append((words["next"], _act(state, a[3], "click")
                        if page < a[1] else None))
    buttons.append((words["close"], _act(state, a[4], "click")))
    return {"options": options, "buttons": buttons,
            "title": words["turn_summary"]}


def _leader_hire(popup, state, words, app, anywhere):
    a = popup["args"]
    card = leader_card(state, a[0], app)
    lines = list(card["skills"])
    question = card["question"](a[1], a[8])
    if question:
        lines += ["", question]
    # REJECT left, HIRE right, as the popup's own buttons stand
    # (Update_Random_New_Officer_Fields_, mainpups.cpp:1721-1773)
    buttons = [(words["reject"], _act(state, a[5], "click")),
               (words["hire"], _act(state, a[4], "click"))]
    right_buttons = [_field(state, a[5]), _field(state, a[4])]
    # a skill line: its help field (`Add_Skill_Description_Help_
    # Fields_`, officer.cpp:3893-3968 — 0xBE wide, one per skill in the
    # order the card lists them), answered by `Print_Officer_Skill_
    # Help_`'s box (mainpups.cpp:914, officer.cpp:3977-4003)
    line_right = sorted(
        (f for f in (getattr(state, "fields", None) or [])
         if f.field_type == 7 and f.x_end - f.x == 0xBE),
        key=lambda f: f.y)
    if a[3] > 0:                    # the tutor's result states
        buttons = [(words["continue"],
                    _act(state, a[6]) or _act(state, a[5], "click"))]
        right_buttons = []
    return {"title": card["title"], "lines": lines,
            "picture": card["portrait"],
            # the HD picture replaces it in the same box (work order 234):
            # `turnpopup.draw` asks `core.leaderportraits` with this record
            "leader_rec": card.get("leader"),
            "buttons": buttons, "right_buttons": right_buttons,
            "line_right": line_right}


def _system_choice(popup, state, words, app, anywhere):
    """The planet choice and the discovery: the star's planets as options."""
    kind, a = popup["kind"], popup["args"]
    title = popup.get("title")
    lines, options, buttons, right_opts = [], [], [], []
    sysd = popup.get("system") or {}
    title = title or _star_name(state, sysd.get("star", -1))
    if popup.get("text"):
        # TRANSCRIPTION `special_name` (work order 322 D): the special
        # popup's title over its description (`Draw_System_Special_
        # Popup_`, sys.cpp:626-632; mainpups.cpp:1781-1787, :1920-1926)
        # — the special is arg 3 of the planet choice, 1 of a new system
        # (open fix 49's TPOP, mainpups.cpp:890, :1155)
        name = _special_name(app, a[3] if kind == "planet_choice"
                             else a[1])
        if name:
            lines.append(name)
        lines.append(popup["text"])
    for slot in sysd.get("planets", []):
        if slot["planet"] < 0:
            continue
        target = (_act(state, slot["field"], "click")
                  if kind != "discovery" and slot["field"] > 0 else None)
        options.append((_planet_name(state, slot["planet"]), target))
        right_opts.append(_field(state, slot["field"])
                          if kind != "planet_choice" else None)
    # the original's button reads CLOSE (BUFFER0.LBX, the native frame
    # of work order 188's planet choice)
    cancel = {"planet_choice": 4}.get(kind)
    if cancel is not None:
        buttons.append((words["close"], _act(state, a[cancel], "click")))
    else:
        buttons.append((words["close"], _act(state, a[2])))
    return {"title": title, "lines": lines, "options": options,
            "buttons": buttons, "right_opts": right_opts}


def _leader_level(popup, state, words, app, anywhere):
    a = popup["args"]
    out = {}
    # the hire popup's card, as the original draws it here too: the
    # full name as title (mainpups.cpp:2245), the portrait and the
    # skills (`Wrapper_For_Colony_Officer_Popup_Data_`, :2224), then
    # the sentence of the state (`leader_level_line`)
    card = leader_card(state, a[0], app)
    if card.get("leader") is None:      # no such leader on the wire
        out["lines"] = [_leader_name(state, a[0])]
    else:
        out["title"] = card["title"]
        out["lines"] = list(card["skills"]) + [
            "", leader_level_line(card, a[1], app)]
        out["picture"] = card["portrait"]
        out["leader_rec"] = card["leader"]
    out["buttons"] = [(words["close"], _act(state, a[3]) or (
        ("activate", anywhere) if anywhere else None))]
    return out


def _gnn(popup, state, words, app, anywhere):
    out = {"title": popup.get("title") or "GNN"}
    if popup.get("text"):
        out["lines"] = [popup["text"]]
    out["buttons"] = [(words["continue"], ("activate", anywhere)
                       if anywhere else None)]
    return out


def _troops(popup, state, words, app, anywhere):
    a = popup["args"]
    # the colony screen's troop popup (open fix 98, work order 274):
    # one full-screen field ends it (`NEWPUP::Reset_Fields_`,
    # newpup.cpp:193-197); the planet's name stands as its title. ONLY
    # WHILE THE GAME REPORTS ITS ID: the colony screen's own full-screen
    # field has the same shape and demolishes the building under the
    # real pointer (`core.colony_guard`)
    from core import troopwire
    title = popup.get("title") or (
        _planet_name(state, a[0]) if a[0] >= 0 else None)
    lines = troopwire.rows(popup.get("troops") or {})
    ours = getattr(state, "current_screen", None) == TROOPS_ID
    return {"title": title, "lines": lines,
            "buttons": [(words["close"], ("activate", anywhere)
                         if anywhere and ours else None)]}


def _slider(popup, state, words, app, anywhere):
    a = popup["args"]
    lines = []
    # TRANSCRIPTION `slider_popup` (work order 316 E, open fix 104):
    # `MAINPUPS::Slider_Popup_` (mainpups.cpp:747-794) — the message,
    # then min, the value and max as `Draw_Slider_Popup_` prints them
    # (:2386-2430); down / up step the value by one, unclamped as the
    # original (`Evaluate_Slider_Input_`, :1953-1973); CANCEL answers
    # -1, ACCEPT the value. OMISSION `slider_bar`: the bar's drag (the
    # scroll field mp_fields[11], 207 px) is not drawn; the arrows do
    # its work
    if popup.get("text"):
        lines = [popup["text"]]
    lines.append(f"{a[0]}   [ {a[2]} ]   {a[1]}")
    return {"lines": lines,
            "buttons": [(words["slider_down"], _act(state, a[4])),
                        (words["slider_up"], _act(state, a[5])),
                        (words["slider_cancel"], _act(state, a[6])),
                        (words["slider_ok"], _act(state, a[7]))]}


def _antaran_room(popup, state, words, app, anywhere):
    a = popup["args"]
    lines = []
    # TRANSCRIPTION `antaran_room` (work order 316 E, open fix 105):
    # `ANTAROOM::Main_Antaran_Room_Screen_` (antaroom.cpp:26-80) prints
    # one ANTARMSG.LBX message (:107-114) and ends on a click on its
    # full-screen field or any key (:60-70); the room's picture and
    # animation (ANTAROOM.LBX 0, 1) are not drawn (the HUD look of
    # every turn popup, `hud_turn_popup` in core/turnpopup.py).
    # UNVERIFIED `antaran_room_live`: drawn from the stand-in's bytes
    # only; no test save brings an Antaran attack (work order 316)
    if popup.get("text"):
        lines = [popup["text"]]
    return {"lines": lines,
            "buttons": [(words["continue"], _act(state, a[1]) or (
                ("activate", anywhere) if anywhere else None))]}


def _dragon_bribe(popup, state, words, app, anywhere):
    a = popup["args"]
    lines = []
    # TRANSCRIPTION `dragon_bribe` (work order 319, open fix 108):
    # `MAINPUPS::Dragon_New_Star_Popup_` (mainpups.cpp:493-543) — the
    # message as the engine formatted it (E 555 the offer, E 464 choose
    # a star, E 583 too poor, :2594-2599); mp_fields[2] refuses (-1, the
    # battle goes on) or closes, mp_fields[25] YES pays when the BC
    # reach the bribe (:2611-2633). NO left, YES right, as the fields
    # stand (186 and 381, :2135-2151). DEVIATION `dragon_button_words`:
    # mp_fields[2] is one picture (MAINPUPS 0x46) in every mode; HD
    # words it NO beside YES and CLOSE alone.
    # UNVERIFIED `dragon_yes_after`: the YES field stays in the list
    # after it is pressed (the fields are added once, :522); whether
    # the original still draws it is not seen — HD does not offer it.
    # Mode 1's star click is `screens/galaxy_map/dragonpopup.py`'s
    # HD EXTENSION `dragon_picture` (work order 326 F): Data's dragon
    # where the original's popup picture shows one (MAINPUPS.LBX 0x48,
    # drawn in every mode, :2617), from the mod folder only (`ART`)
    from core import dragonwire
    art = ART["dragon_bribe"]
    if popup.get("text"):
        lines = [popup["text"]]
    if dragonwire.mode(popup) == dragonwire.OFFER:
        buttons = [(words["dragon_no"], _act(state, a[4])),
                   (words["dragon_yes"], _act(state, a[5]))]
    else:
        buttons = [(words["close"], _act(state, a[4]))]
    return {"lines": lines, "buttons": buttons, "art": art}


def _landing(popup, state, words, app, anywhere):
    a = popup["args"]
    return {"title": popup.get("title") or _planet_name(state, a[0]),
            "buttons": [(words["continue"], _act(state, a[3]) or (
                ("activate", anywhere) if anywhere else None))],
            "right_buttons": [_field(state, a[3]) or anywhere]}


#: One builder per popup kind: each returns only what it sets of
#: `{"title", "lines", "options", "buttons", "picture", "leader_rec",
#: "art", "right_opts", "right_buttons", "line_right"}`; `content` fills
#: the rest with the empty defaults. An unknown kind sets nothing.
_BUILDERS = {"science": _science, "turn_summary": _turn_summary,
             "leader_hire": _leader_hire, "planet_choice": _system_choice,
             "discovery": _system_choice, "leader_level": _leader_level,
             "gnn": _gnn, "troops": _troops, "slider": _slider,
             "antaran_room": _antaran_room, "dragon_bribe": _dragon_bribe,
             "landing": _landing}


def content(popup, state, words, app=None):
    """`{"title", "lines", "options", "buttons"}` for one popup; options
    and buttons are `(label, action)`, an action `("activate" | "click",
    field)` or None when that field is not in the live list."""
    kind = popup["kind"]
    popup["args"]       # no args is a malformed popup: fail as before, early
    anywhere = _anywhere(state)
    # the right click (`RIGHT`): per option, per button, per table line,
    # else the popup's
    out = {"title": popup.get("title"), "lines": [], "options": [],
           "buttons": [], "picture": None, "leader_rec": None, "art": None,
           "right_opts": [], "right_buttons": [], "line_right": []}
    build = _BUILDERS.get(kind)
    if build is not None:
        out.update(build(popup, state, words, app, anywhere))
    options, buttons = out["options"], out["buttons"]
    right_opts, right_buttons = out["right_opts"], out["right_buttons"]
    right = [("field", f) if f is not None else None for f in
             right_opts + [None] * (len(options) - len(right_opts)) +
             right_buttons + [None] * (len(buttons) - len(right_buttons))]
    return {"title": out["title"], "lines": out["lines"],
            "options": options, "buttons": buttons, "right": right,
            "line_right": out["line_right"],
            "right_help": RIGHT_HELP.get(kind),
            "picture": out["picture"] if kind in LEADER_CARDS else None,
            "leader": out["leader_rec"] if kind in LEADER_CARDS else None,
            "art": out["art"]}


#: A popup's HD picture by kind: a tree path no file of OrionLayer's fills
#: — a slot of `core.usermod.SLOTS`, so only the player's mod folder does;
#: without it the popup is drawn as before (work order 326 F).
ART = {"dragon_bribe": "assets/shared/turnpopup/dragon_bribe.png"}


#: The kinds that draw a leader's card with its portrait.
LEADER_CARDS = ("leader_hire", "leader_level")


