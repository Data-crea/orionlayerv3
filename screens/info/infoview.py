"""The Info screen's five pages, drawn — each a function of the screen,
the surface and the local player's record (`screen.py` routes by page).
Every text by its key through `core/modtexts`; see `screen.py` for what
each page may send (nothing but RETURN) and `infotexts` for the keys.
"""
from core import modtexts

from . import infodraw, infogeom as geom, infopages as pages

T = modtexts.text


def history(screen, surface, me):
    n = int(getattr(screen._state, "num_players", 0) or 0) or 8
    order = pages.race_list(screen._players, screen._state.player_num, n)
    names = [(screen._players[i].race_name, i, True) for i in order]
    infodraw.rows(surface, screen, "history.legend", geom.HISTORY_LEGEND,
                  [(t, None, h) for t, _i, h in names])
    infodraw.text(surface, screen, "history.graph", geom.HISTORY_GRAPH,
                  T("info.history.needs_fix", ""))
    for k, key in enumerate(("population", "production", "fleet", "tech")):
        infodraw.button(surface, screen, geom.history_button_rect(k),
                        T(f"info.history.metric.{key}", key),
                        bool((int(me.history_btns) >> k) & 1))

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
    infodraw.text(surface, screen, "turns", geom.TURNS_BOX,
                  T("info.turns.needs_fix", ""))

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
