"""What each Info page says, as data — info.cpp's builders transcribed.

Every text goes through `core/modtexts` by its key (`infotexts`), so a
mod can replace it; every number is the snapshot's.
"""
from core import modtexts
from core.structs import player as player_struct

T = modtexts.text

# ── The lists (bill.cpp:312-338, :565-596) ─────────────────


def players_of(game_state):
    raws = getattr(game_state, "player_raw", None) or []
    return [player_struct.parse(r) for r in raws
            if len(r) >= player_struct.SIZE]


def race_list(players, me, n_players, previously=False):
    """`_active_player[0] = me`, then `Get_Players_Dead_Or_Alive_Or_
    Omniscient_(1, previously)`: contacted living players, (with
    `previously`) those met before, then the eliminated — or all, for an
    omniscient player. History asks without, Race Statistics with
    (info.cpp:1146-1148, :1661-1662)."""
    if not 0 <= me < len(players):
        return []
    mine = players[me]
    met = player_struct.contacts(mine)
    seen = list(mine.n_times_established_contact)
    n = min(n_players, len(players))
    out = [me]
    out += [i for i in range(n) if i != me and not players[i].eliminated
            and met[i]]
    if previously:
        out += [i for i in range(n) if i != me and not players[i].eliminated
                and not met[i] and seen[i]]
    omni = player_struct.has_omniscience(mine)
    out += [i for i in range(n) if i not in out
            and (omni or players[i].eliminated)]
    return out


# ── The left panel (info.cpp:462-498, :686-776) ─────────────

def chart(player):
    """(income, [six maintenance], [seven percents], net)."""
    income = int(player.bc_produced)
    maint = [int(v) for v in player.maintenance]
    sources = [income] + maint
    top = max(max(sources), 0)
    pct = [((v * 1000) // top + 5) // 10 if top > 0 else 0 for v in sources]
    return income, maint, pct, income - int(player.total_maintenance)


def stat(text, value):
    """`Decode_Text_Stat_`: the 0x82 byte (é in cp437) is the number."""
    return (text or "").replace("é", str(value))


# ── Tech Review (info.cpp:35-72, :1498-1538) ─────────────────

#: `_review_achievements`, `_review_colony`, `_review_weapons`,
#: `_review_equipment` (info.cpp:35-70): (id, flags) — 4 a group header
#: (id = the BILLTEX2 message), 2 an application, 8 the end.
REVIEW = (
    ((1, 4), (55, 2), (16, 2), (186, 2), (189, 2), (109, 2), (69, 2),
     (41, 2), (40, 2), (2, 4), (43, 2), (173, 2), (147, 2), (182, 2),
     (114, 2), (166, 2), (3, 4), (170, 2), (99, 2), (195, 2), (29, 2),
     (8, 2), (7, 2), (6, 2), (3, 2), (113, 2), (108, 2), (193, 2),
     (107, 2), (5, 4), (89, 2), (46, 2), (59, 2), (4, 2), (179, 2),
     (4, 4), (24, 2), (144, 2), (124, 2), (9, 2), (138, 2), (128, 2),
     (73, 2), (101, 2), (145, 2), (0, 4), (91, 2), (176, 2), (180, 2),
     (92, 2), (77, 2), (65, 2), (42, 2), (200, 2), (84, 2), (62, 2),
     (32, 2), (0, 8)),
    ((6, 4), (198, 2), (68, 2), (162, 2), (87, 2), (74, 2), (178, 2),
     (183, 2), (7, 4), (50, 2), (19, 2), (142, 2), (9, 4), (49, 2),
     (154, 2), (152, 2), (156, 2), (22, 2), (11, 4), (76, 2), (136, 2),
     (21, 2), (155, 2), (12, 4), (75, 2), (135, 2), (164, 2), (10, 4),
     (15, 2), (129, 2), (130, 2), (134, 2), (169, 2), (27, 2), (168, 2),
     (133, 2), (132, 2), (67, 2), (14, 2), (103, 2), (8, 4), (141, 2),
     (86, 2), (0, 4), (61, 2), (197, 2), (52, 2), (5, 2), (131, 2),
     (39, 2), (163, 2), (18, 2), (0, 8)),
    ((13, 4), (174, 2), (47, 2), (123, 2), (105, 2), (54, 2), (137, 2),
     (79, 2), (127, 2), (97, 2), (115, 2), (78, 2), (70, 2), (104, 2),
     (100, 2), (14, 4), (139, 2), (146, 2), (12, 2), (202, 2), (149, 2),
     (106, 2), (121, 2), (15, 4), (28, 2), (48, 2), (118, 2), (10, 2),
     (71, 2), (119, 2), (16, 4), (83, 2), (31, 2), (66, 2), (17, 2),
     (17, 4), (165, 2), (30, 2), (171, 2), (148, 2), (140, 2), (80, 2),
     (13, 2), (0, 8)),
    ((18, 4), (81, 2), (112, 2), (161, 2), (37, 2), (36, 2), (35, 2),
     (34, 2), (33, 2), (19, 4), (56, 2), (82, 2), (201, 2), (2, 2),
     (117, 2), (203, 2), (191, 2), (187, 2), (20, 4), (20, 2), (95, 2),
     (88, 2), (11, 2), (96, 2), (72, 2), (120, 2), (22, 4), (63, 2),
     (184, 2), (194, 2), (98, 2), (51, 2), (167, 2), (21, 4), (110, 2),
     (44, 2), (143, 2), (122, 2), (58, 2), (24, 4), (160, 2), (116, 2),
     (181, 2), (157, 2), (23, 4), (45, 2), (153, 2), (60, 2), (53, 2),
     (102, 2), (126, 2), (38, 2), (93, 2), (94, 2), (199, 2), (111, 2),
     (57, 2), (25, 4), (1, 2), (175, 2), (85, 2), (151, 2), (26, 2),
     (0, 4), (150, 2), (125, 2), (185, 2), (90, 2), (177, 2), (190, 2),
     (188, 2), (23, 2), (172, 2), (159, 2), (64, 2), (196, 2), (158, 2),
     (25, 2), (192, 2), (0, 8)),
)
RESEARCHED = 3
TECH_TABS = ("achievements", "colony", "weapons", "equipment")


def tech_review(player, tab):
    """`[(group id, [application ids])]` — `Init_Tech_Review_List_`: only
    researched applications, a group without any left out (:1510-1536)."""
    apps = list(player.tech_applications)
    out = []
    for ident, flags in REVIEW[tab]:
        if flags & 8:
            break
        if flags & 4:
            if out and not out[-1][1]:
                out.pop()
            out.append((ident, []))
        elif out and apps[ident] == RESEARCHED:
            out[-1][1].append(ident)
    if out and not out[-1][1]:
        out.pop()
    return out


# ── Race Statistics (info.cpp:338-404) ─────────────────────

TRAIT_GOVERNMENT, TRAIT_FOOD, TRAIT_TAX = 0, 2, 5
TRAIT_LOW_G, TRAIT_RICH_HOME, TRAIT_COUNT = 10, 15, 31
POOR_HOME_NAME = 31


def trait_lines(player):
    """`Print_Player_Specials_To_Bitmap_`: "^ name" and its value, one
    line per trait that is set, the government always."""
    traits = player_struct.traits(player)
    lines = []
    for k in range(TRAIT_COUNT):
        v = traits[k]
        if v == 0 and k != TRAIT_GOVERNMENT:
            continue
        if k == TRAIT_GOVERNMENT:
            name = T(f"info.races.gov.{max(0, min(7, v))}", "")
        elif k == TRAIT_RICH_HOME:
            name = T(f"info.races.trait.{POOR_HOME_NAME if v < 0 else 15}", "")
        else:
            name = T(f"info.races.trait.{k}", "")
        text = name or ""
        if TRAIT_GOVERNMENT < k < TRAIT_LOW_G:
            if k == TRAIT_FOOD:
                text += "-0.5" if v < 0 else "+1" if v == 2 else "+2"
            elif k == TRAIT_TAX:
                text += ("-" if v < 0 else "+") + ("1 BC" if v == 2
                                                   else "0.5 BC")
            else:
                text += f"{v:+d}"
        lines.append(text)
    return lines


# ── Reference (info.cpp:997-1116, :1779-1906) ──────────────

def categories():
    """`[(index, label)]`: `_help_category_labels[1..16]` without the
    labels that start with a digit (:1814-1823)."""
    out = []
    for i in range(1, 17):
        label = T(f"info.reference.category.{i}", "") or ""
        if label and label[0] > "9":
            out.append((i, label))
    return out


def topics(info, entry, sort=True):
    """`[(text, id)]` of HELP.LBX `entry`, the text through the resolver;
    a category's sorted as `Compare_Unsigned_Strings_` sorts (:1033-1046)."""
    rows = [(T(f"info.topic.{tid}", text) or text, tid)
            for text, tid in (info.topic_list(entry) if info else [])]
    if sort:
        rows.sort(key=lambda r: r[0].encode("cp437", errors="replace"))
    return rows


def record(ident):
    """(title, body) of a HELP.LBX record through the resolver."""
    return (T(f"info.reference.{ident}.title", "") or "",
            T(f"info.reference.{ident}.body", "") or "")
