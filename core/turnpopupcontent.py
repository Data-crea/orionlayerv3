"""What each turn-time popup shows — open fix 49 (work order 188).

The content half of `core/turnpopup.py` (split for decision 6): from a
popup (TPOP) and the snapshot, a title, lines, options and buttons, each
bound to the popup's OWN field — see `core/turnpopup.py` for the rules.
"""
DEFAULT_WORDS = {"close": "CLOSE", "cancel": "CANCEL", "ok": "OK",
                 "prev": "PREV", "next": "NEXT", "continue": "CONTINUE",
                 "hire": "HIRE", "reject": "REJECT",
                 "turn_summary": "TURN SUMMARY"}


def _star_name(state, index):
    stars = getattr(state, "stars", None) or []
    return stars[index].name if 0 <= index < len(stars) else "?"


def _planet_name(state, planet_index):
    from core.structs import planet as planet_struct
    from screens.colony_summary.colonyrows import star_planet_name
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
    level = ls.shown_level(rec, index, lambda _p: False)
    title_word = words.estring(ls.level_name_estring(rec, level)) or ""
    the_word = ldrrows.the_word(words, index)
    name = ls.leader_name(rec, title_word, the_word)
    skills = []
    for sid in ls.displayed_skills(rec):
        value = ls.c_format(ls.SKILLS[sid][6], ls.skill_bonus(level, sid))
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
            "question": question}


def _ship_owner(state, ship_index):
    from core.structs import ship as ship_struct
    raw = getattr(state, "ships_raw", None) or []
    if not 0 <= ship_index < len(raw):
        return None
    return ship_struct.parse(raw[ship_index]).owner


def _race_name(state, player):
    from core.structs import player as player_struct
    raw = getattr(state, "player_raw", None) or []
    if player is None or not 0 <= player < len(raw):
        return "?"
    return player_struct.parse(raw[player]).race_name


def _tech_name(tech):
    try:
        from core import technames
        return technames.TechNames().application_name(tech & 0x1FF)
    except Exception:
        return None


def _field(state, index):
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == index and index > 0), None)


def content(popup, state, words, app=None):
    """`{"title", "lines", "options", "buttons"}` for one popup; options
    and buttons are `(label, action)`, an action `("activate" | "click",
    field)` or None when that field is not in the live list."""
    kind, a = popup["kind"], popup["args"]
    title = popup.get("title")
    lines, options, buttons = [], [], []
    picture = None

    def act(index, how="activate"):
        f = _field(state, index)
        return (how, f) if f is not None else None
    anywhere = next((f for f in (getattr(state, "fields", None) or [])
                     if getattr(f, "index", 0) > 0 and (f.x, f.y, f.x_end,
                                                        f.y_end) ==
                     (0, 0, 639, 479)), None)

    if kind == "science":
        n = max(0, a[0])
        names = []
        i = 3
        while i < 16 and len(names) < n:
            tech = a[i]
            i += 1
            if tech < 0:
                continue
            if tech & 0x4000:            # a weapon-mod entry and its mask
                i += 1
                continue
            names.append(_tech_name(tech) or f"#{tech & 0x1FF}")
        lines = [f"• {nm}" for nm in names]
        if popup.get("text"):
            lines = [""] + lines
            lines = [popup["text"]] + lines
        buttons = [(words["continue"], ("activate", anywhere)
                    if anywhere else None)]
    elif kind == "turn_summary":
        page = a[0]
        for m in popup.get("messages", []):
            if m["page"] != page:
                continue
            target = None
            if m["jumps"] and m["first_field"] > 0:
                target = act(m["first_field"], "click")
            options.append((m["text"], target))
        if a[1] > 1:
            buttons.append((words["prev"], act(a[2], "click")
                            if page > 1 else None))
            buttons.append((words["next"], act(a[3], "click")
                            if page < a[1] else None))
        buttons.append((words["close"], act(a[4], "click")))
        title = words["turn_summary"]
    elif kind == "leader_hire":
        card = leader_card(state, a[0], app)
        title = card["title"]
        lines = list(card["skills"])
        question = card["question"](a[1], a[8])
        if question:
            lines += ["", question]
        picture = card["portrait"]
        # REJECT left, HIRE right, as the popup's own buttons stand
        # (Update_Random_New_Officer_Fields_, mainpups.cpp:1721-1773)
        buttons = [(words["reject"], act(a[5], "click")),
                   (words["hire"], act(a[4], "click"))]
        if a[3] > 0:                    # the tutor's result states
            buttons = [(words["continue"], act(a[6]) or act(a[5], "click"))]
    elif kind in ("planet_choice", "discovery", "combat_target"):
        sysd = popup.get("system") or {}
        title = title or _star_name(state, sysd.get("star", -1))
        if popup.get("text"):
            lines.append(popup["text"])
        for slot in sysd.get("planets", []):
            if slot["planet"] < 0:
                continue
            target = (act(slot["field"], "click")
                      if kind != "discovery" and slot["field"] > 0 else None)
            options.append((_planet_name(state, slot["planet"]), target))
        if kind == "combat_target":
            # A player target is chosen by clicking one of its ships
            # (Check_System_Display_Fields_Defense_Selection_,
            # mainpups.cpp:2847-2951): one option per such ship button,
            # named by the owner's race (s_player.race_name).
            wanted = set((popup.get("targets") or {}).get("players", []))
            for slot in sysd.get("ships", []):
                owner = _ship_owner(state, slot["ship"])
                if slot["field"] > 0 and owner in wanted:
                    options.append((_race_name(state, owner),
                                    act(slot["field"], "click")))
        # the original's button reads CLOSE on both (BUFFER0.LBX, the
        # native frame of work order 188's planet choice)
        cancel = {"planet_choice": 4, "combat_target": 2}.get(kind)
        if cancel is not None:
            buttons.append((words["close"], act(a[cancel], "click")))
        else:
            buttons.append((words["close"], act(a[2])))
    elif kind == "leader_level":
        lines = [_leader_name(state, a[0])]
        buttons = [(words["close"], act(a[3]) or (
            ("activate", anywhere) if anywhere else None))]
    elif kind == "gnn":
        title = title or "GNN"
        if popup.get("text"):
            lines = [popup["text"]]
        buttons = [(words["continue"], ("activate", anywhere)
                    if anywhere else None)]
    elif kind == "landing":
        title = title or _planet_name(state, a[0])
        buttons = [(words["continue"], act(a[3]) or (
            ("activate", anywhere) if anywhere else None))]
    return {"title": title, "lines": lines, "options": options,
            "buttons": buttons,
            "picture": picture if kind == "leader_hire" else None}


