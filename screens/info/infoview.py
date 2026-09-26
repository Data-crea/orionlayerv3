"""The Info screen's five pages, drawn — each a function of the screen,
the surface and the local player's record (`screen.py` routes by page).
Every text by its key through `core/modtexts`; see `screen.py` for what
each page may send (nothing but RETURN) and `infotexts` for the keys.
"""
from core import modtexts

from . import infodraw, infogeom as geom, infopages as pages

T = modtexts.text


def history(screen, surface, me):
    """`History_Subscreen_`: the legend in the players' colours
    (`Display_Graphed_Players_Names_`, info.cpp:1350-1386), the axes, the
    y maximum and the eight stardate labels (`Draw_The_History_Graph_`,
    :1565-1643) and one curve per player (`Draw_Histories_`, :1222-1347)
    — from open fix 32's divisors; an engine without it gets the notice."""
    state = screen._state
    n = int(getattr(state, "num_players", 0) or 0) or 8
    order = pages.race_list(screen._players, state.player_num, n)
    infodraw.nd.draw_box(surface, screen, geom.HISTORY_LEGEND)
    x, y, gap = 351, 64, 0
    if len(order) > 3:
        x, gap = 295, 150
    if len(order) > 6:
        x, gap = 233, 122
    for k, p in enumerate(order):
        colour = infodraw.player_colour(screen._players[p])
        infodraw.infobox.line(surface, screen, screen._players[p].race_name,
                              infodraw.R(screen, (x, y, x + max(gap, 120) - 8,
                                                  y + 14)),
                              infodraw.px(screen, "skill"), colour)
        y += 19
        if k in (2, 5):
            x, y = x + gap, 64
    block = getattr(state, "info_screen", None)
    for k, key in enumerate(("population", "production", "fleet", "tech")):
        infodraw.button(surface, screen, geom.history_button_rect(k),
                        T(f"info.history.metric.{key}", key),
                        bool(screen.hist_bits >> k & 1))
    if block is None:
        infodraw.text(surface, screen, "history.graph", geom.HISTORY_GRAPH,
                      T("info.history.no_block", ""))
        return
    infodraw.nd.draw_box(surface, screen, geom.HISTORY_GRAPH)
    graph = pages.history(screen._players, order, screen.hist_bits,
                          state.stardate, block["bill"])
    infodraw.draw_graph(surface, screen, graph, order, state.stardate)


def tech(screen, surface, me):
    groups = pages.tech_review(me, screen.tech_tab)
    items = []
    for gid, apps in groups:
        items.append((T(f"info.tech.group.{gid}", "") or "", None, True))
        items += [(T(f"info.tech.app.{a}.name", "") or f"#{a}", a, False)
                  for a in apps]
    if not items:
        items = [(T("info.tech.none", ""), None, True)]
    if screen.tech_app is None:
        screen.tech_app = next((p for _t, p, h in items if p is not None),
                             None)
    infodraw.rows(surface, screen, "tech.list", geom.TECH_LIST, items,
                  screen.tech_app)
    title, body = pages.record(screen.tech_app) if screen.tech_app is not None \
        else ("", "")
    name = T(f"info.tech.app.{screen.tech_app}.name", "") \
        if screen.tech_app is not None else ""
    infodraw.text(surface, screen, "tech.name", geom.TECH_NAME, name or title,
                  "name", infodraw.HIGH, "center")
    infodraw.nd.draw_box(surface, screen, geom.TECH_PICTURE)
    infodraw.text(surface, screen, f"tech.body.{screen.tech_app}",
                  geom.TECH_BODY, body)
    for k, key in enumerate(pages.TECH_TABS):
        infodraw.button(surface, screen, geom.tech_tab_rect(k),
                        T(f"info.tech.tab.{key}", key), k == screen.tech_tab)

def races(screen, surface, me):
    n = int(getattr(screen._state, "num_players", 0) or 0) or 8
    order = pages.race_list(screen._players, screen._state.player_num, n,
                            previously=True)
    first = 4 * screen.race_page
    for k in range(4):
        box = geom.RACE_PANELS[k]
        j = first + k
        if j < len(order):
            p = screen._players[order[j]]
            head = p.race_name.upper()
            lines = pages.trait_lines(p)
            if p.eliminated:
                lines = [T("info.races.eliminated", "") or ""] + lines
            body = "\n".join([head, ""] + lines)
        else:
            body = T("info.races.none", "") or ""
        infodraw.text(surface, screen, f"races.{k}", box,
                      body.replace("^", ""))
    if len(order) > 4:
        infodraw.button(surface, screen, geom.RACE_PAGE_BUTTON,
                        f"{screen.race_page + 1}/2")

def turns(screen, surface, me):
    """`Turn_Summary_Subscreen_`: the header "… as of SD: ê" with the
    stardate, then every message as `sprintf_msg_` rendered it (open fix
    32), each a "^" paragraph (info.cpp:1953-1995), or NO MESSAGES; an
    engine without the fix gets the notice."""
    block = getattr(screen._state, "info_screen", None)
    if block is None:
        infodraw.text(surface, screen, "turns", geom.TURNS_BOX,
                      T("info.turns.no_block", ""))
        return
    msgs = pages.messages(block)
    head = pages.year(T("info.turns.header", "") or "",
                      screen._state.stardate)
    body = "\n\n".join(m.replace("^", "").strip() for m in msgs) if msgs \
        else (T("info.turns.empty", "") or "")
    infodraw.text(surface, screen, "turns",
                  geom.TURNS_BOX, f"{head}\n\n{body}".strip())


def reference(screen, surface, me):
    if screen.ref_mode == "index":
        for k, head in enumerate(("info.reference.categories",
                                  "info.reference.howto")):
            infodraw.text(surface, screen, f"ref.head.{k}",
                          geom.REFERENCE_HEADS[k], T(head, "") or "",
                          "name", infodraw.HIGH)
        infodraw.rows(surface, screen, "ref.categories",
                      geom.REFERENCE_LISTS[0],
                      [(label, ("cat", i), False)
                       for i, label in pages.categories()])
        infodraw.rows(surface, screen, "ref.howto", geom.REFERENCE_LISTS[1],
                      [(t, ("howto", i), False) for t, i in
                       pages.topics(screen._info, 15, sort=False)])
        return
    back = geom.BACK_BUTTON
    if screen.ref_mode == "category":
        label = T(f"info.reference.category.{screen.ref_ix}", "") or ""
        infodraw.text(surface, screen, "ref.cat.head", geom.CATEGORY_HEAD,
                      (T("info.reference.category_prefix", "") or "")
                      + label, "name", infodraw.HIGH, "center")
        items = pages.topics(screen._info, screen.ref_ix)
        if screen.topic is None and items:
            screen.topic = items[0][1]
        infodraw.rows(surface, screen, "ref.cat.list", geom.CATEGORY_LIST,
                      [(t, i, False) for t, i in items], screen.topic)
        title, body = pages.record(screen.topic) if screen.topic is not None \
            else ("", "")
        infodraw.text(surface, screen, f"ref.cat.text.{screen.topic}",
                      geom.CATEGORY_TEXT, f"{title}\n\n{body}".strip())
    else:
        title, body = pages.record(screen.ref_ix)
        infodraw.text(surface, screen, "ref.howto.head", geom.HOWTO_HEAD,
                      (T("info.reference.howto_prefix", "") or "") + title,
                      "name", infodraw.HIGH, "center")
        infodraw.text(surface, screen, f"ref.howto.text.{screen.ref_ix}",
                      geom.HOWTO_TEXT, body)
    infodraw.button(surface, screen, back, T("info.reference.back", "BACK"))
