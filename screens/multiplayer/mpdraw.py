"""The multiplayer steps after the setup, drawn from open fix 51's "MPLY".

Each step becomes one panel — a title, lines, options (rows the player
picks) and buttons — drawn by the turn popups' panel (`core.turnpopup.draw`,
the HUD style), every option and button bound to its OWN field from the
block (never an index remembered). What each step shows and where its fields
lead is `dev:doc/multiplayer_reading.md` and the patch's header. The words are
`layout.json`'s (the original's are MULTIGM.LBX artwork, decision 15).
"""
from core import turnpopup

NONE = -1000


def _field(state, index):
    if index is None or index <= 0:
        return None
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == index), None)


def _player_name(state, player):
    from core.structs import player as player_struct
    raw = getattr(state, "player_raw", None) or []
    if not 0 <= player < len(raw):
        return f"#{player}"
    rec = player_struct.parse(raw[player])
    return f"{rec.name} ({rec.race_name})"


def content(screen, state):
    """`(content for turnpopup.draw, {"chat": field} or {})`."""
    mp = getattr(state, "multiplayer", None) or {}
    w = screen.words
    phase = mp.get("phase")
    title, lines, options, buttons, extra = "", [], [], [], {}

    def act(index):
        f = _field(state, index)
        return ("activate", f) if f is not None else None

    if phase == "load_list":
        title = w("load_title")
        for slot in mp["slots"]:
            if not slot["description"] and not slot["valid"]:
                continue
            label = " ".join(x for x in (slot["description"],
                                         slot["stardate"], slot["date"]) if x)
            options.append((label, act(slot["field"])
                            if slot["valid"] else None))
        buttons = [(w("cancel"), act(mp["cancel"]))]
    elif phase == "game_name":
        title = mp.get("prompt") or w("load_title")
        lines = [mp["input"]["text"]]
        buttons = [(w("cancel"), act(mp["cancel"])),
                   (w("accept"), act(mp["input"]["field"]))]
    elif phase == "hotseat":
        title = w("hotseat_title")
        lines = [f'{w("players")}: {len(mp["humans"])} / {mp["players"]}']
        lines += [f'{i + 1}. {h["name"]} ({h["race_name"]})'
                  for i, h in enumerate(mp["humans"])]
        buttons = [(w("join_player"), act(mp["join"])),
                   (w("accept"), act(mp["accept"])),
                   (w("cancel"), act(mp["cancel"]))]
    elif phase == "hotseat_switch":
        title = w("switch_title")
        for i, p in enumerate(mp["players"]):
            if p["status"] == 0:
                continue
            name = _player_name(state, i)
            if p["status"] == 2:
                options.append((name, act(p["row"])))
            else:
                options.append((f'{name} — {w("played")}', None))
    elif phase in ("host_init", "join_init"):
        title = w("host_title") if phase == "host_init" else w("join_title")
        lines = [w("initializing")]
        if mp.get("net_mode") == 1 and mp.get("endpoint"):
            lines.append(f'{w("endpoint")}: {mp["endpoint"]}')
    elif phase in ("host_wait", "host_load_wait"):
        title = w("host_title")
        lines = [mp["game_name"],
                 f'{w("players")}: {mp["users"]} / {mp["players"]}']
        if phase == "host_load_wait":
            lines.append(f'{w("needed")}: {mp["needed"]}')
        buttons = [(w("begin"), act(mp["begin"]))]
    elif phase == "host_race_info":
        title = w("host_title")
        lines = [w("race_info"), f'{mp["with_race"]} / {mp["connected"]}']
    elif phase in ("host_send", "join_get"):
        title = w("host_title") if phase == "host_send" else w("join_title")
        lines = [mp["status"] or (w("sending") if phase == "host_send"
                                  else w("getting"))]
    elif phase in ("host_pick", "join_pick"):
        title = w("pick_title")
        for i, p in enumerate(mp["players"]):
            if not p["shown"]:
                continue
            name = _player_name(state, i)
            options.append((name + (f' — {w("taken")}' if p["taken"] else ""),
                            None if p["taken"] else act(p["row"])))
        if mp["begin"] not in (None, NONE):
            buttons = [(w("begin"), act(mp["begin"]))]
    elif phase == "join_list":
        title = w("join_title")
        for g in mp["games"]:
            options.append((f'{g["name"]}  {g["players"]} / {g["max"]}',
                            act(g["field"]) if g["open"] else None))
        if not mp["games"]:
            lines = [w("no_games")]
        buttons = [(w("cancel"), act(mp["cancel"]))]
    elif phase == "join_wait":
        title = w("join_title")
        lines = [w("joined_waiting"), mp.get("game_name") or ""]
    elif phase == "join_map":
        title = w("join_title")
        lines = [w("generating")]
    elif phase == "net_turn":
        title = w("net_turn_title")
        for h in mp["humans"]:
            if not h["done"]:
                lines.append(_player_name(state, h["player"]))
        lines += [""] + [ln["text"] for ln in mp["lines"][-8:]]
        chat = mp["chat"]
        typing = getattr(screen, "_endpoint", None)
        shown = typing.value + "_" if typing is not None else \
            (chat["typed"] if chat["editing"] else "")
        options.append((f'{w("chat")}: {shown or ""}',
                        act(chat["field"])))
        extra["chat"] = _field(state, chat["field"])
    return ({"title": title, "lines": lines, "options": options,
             "buttons": buttons, "picture": None}, extra)


def draw_step(surface, screen, state):
    """Draw the step; `{key: (rect, field)}` of what can be clicked."""
    c, extra = content(screen, state)
    if not c["title"]:
        return {}
    rects, _buttons = turnpopup.draw(surface, screen.style, c)
    out = {}
    chat = extra.get("chat")
    for i, (rect, action) in enumerate(rects):
        if action is None:
            continue
        field = action[1]
        key = "chat" if chat is not None and field is chat else f"a{i}"
        out[key] = (rect, field)
    return out
