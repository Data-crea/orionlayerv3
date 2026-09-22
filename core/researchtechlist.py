"""The research screen's category list popup — `TECH::_Tech_List_`.

tech.cpp:847-1029, opened by one of the eight category buttons on the
research panel and **display-only**: a row click returns an id no branch
compares, the highlight is pointer hover, and nothing in the popup
changes the research (`doc/tech_change_reading.md` §2, the input table).
So HD draws it and SENDS NOTHING — the game stays in `_Tech_Select_`'s
own loop with the panel's field list, which is also what keeps
`researchlist.validate_against_fields` passing while the popup is up.

ONE IMPLEMENTATION, TWO MODES, like everything else on this screen: the
only difference is the panel origin, and the window follows it —
`_list_window_x_offsets[i] + _g_scrn_x` (tech.cpp:33, :421, :909).

WHAT IS TRANSCRIBED

    the content     `Get_Group_List_` (tech.cpp:1105-1168): walk the
                    category's `next_field_id` chain, skip a researched
                    field and a hyper field past level 20, promote a
                    field with a researched application to status 1,
                    and keep it only if at least one application is at
                    status >= 1
    the statuses    the colour index IS the status, for the field name
                    (`group_color_index`) and per application
                    (`tech_app_status`) — `Display_List_Text_`,
                    list.cpp:37-74
    the layout      `Init_List_Data_` (list.cpp:143-186) and the
                    `s_list_state` literal at tech.cpp:76-100: x, y, the
                    223 px item width, the 424 px page bottom, the 8 px
                    item spacing, `_app_name_y` for the labels and
                    `_tech_field_y1/_y2` for the row rectangles
    the paging      an item that would cross 424 starts the next page,
                    and the first item always starts one
    the title       the category's own name (billtext 64 + group) plus
                    billtext 63, centred at `win_x + 134`, y 47
                    (tech.cpp:951-955)

WHAT IS NOT. All three are one DEVIATION, `category_list_popup` in
both screens' `MARKED`, and a smoke check holds it there:

    the window art  TECHSEL.LBX 0x17-0x1A (change) / 0x09-0x0C (select)
                    is not extracted; HD draws its own panel
    the page buttons' SIZE. Their ORIGINS are the source's —
                    `win_x + 0xF7, 0x4D` and `win_x + 0xF8, 0x18E`
                    (tech.cpp:937-938) — and `Add_Button_Field_` takes
                    the rectangle from the art (fields.cpp:366-367), so
                    the size is not in the source at all. DEVIATION.
    the hover       INVENTION: the original cycles a palette index and
                    an RGB surface has none, so the hovered row is
                    filled, exactly as `core/researchpanel.py` does it

**THE ONE COLOUR THAT IS AN ARRAY OVERRUN, and it is transcribed as
what it lands on.** `group_colors` has four entries and the status of
the field being researched is 4 (tech.cpp:1117), so
`state->group_colors[4]` reads one past the array — onto the next
member of `s_list_state`, `disabled_color`, which is `&_tech_color[2]`
(tech.cpp:76-100). `_tech_color[2]` is the second colour, the one the
panel marks the current research with, so the overrun lands on exactly
the colour a reader would have chosen. Written down because it is the
kind of thing that gets "corrected" by the next person to read it.
"""
import pygame

from core import palette
from core import researchlist
from core import researchnative as geom_mod
from core.researchpanel import _blit_text, col

#: `TECH::_list_window_x_offsets` (tech.cpp:33), indexed by PANEL ENTRY.
#: A left-column entry opens its window on the right and the other way
#: round, which is why the table is 205/6 and not one value.
WINDOW_X_OFFSETS = (205, 6, 205, 6, 205, 6, 205, 6)

#: The window `_Tech_List_` clears and draws into: `Fill_(win_x, 0x1F,
#: win_x + 0x10B, 0x1C1, 0)` (tech.cpp:946-947).
WINDOW_Y1, WINDOW_Y2, WINDOW_DX2 = 31, 449, 267

#: `Print_Centered_(win_x + 0x86, 0x2F, title)` (tech.cpp:954-955).
TITLE_DX, TITLE_Y = 134, 47

#: The `s_list_state` literal, tech.cpp:76-100, with `x` set to
#: `win_x + 0x10` at :909.
LIST_DX, LIST_Y = 16, 73
ITEM_WIDTH, Y_MAX, ITEM_SPACING, APP_X_OFFSET = 223, 424, 8, 10

#: `TECH::_app_name_y` (tech.cpp:34) — where each application's label
#: sits under its field's name, and, at index `app_count`, how far the
#: next item starts below this one (`Init_List_Data_`, list.cpp:166).
APP_NAME_Y = (19, 34, 49, 64, 79, 0, 0, 0)

#: `BILL::Squeeze_Print_(item->app_base_x, …, 0xD5)` — tech.cpp:11.
APP_LABEL_WIDTH = 213

#: `Add_Button_Field_(win_x + 0xF7, 0x4D, …)` and `(win_x + 0xF8,
#: 0x18E, …)` (tech.cpp:937-938). The SIZE is not in the source.
UP_DX, UP_Y = 247, 77
DOWN_DX, DOWN_Y = 248, 398
#: CHOSEN, and marked: `Add_Button_Field_` reads the rectangle off
#: TECHSEL 0x19/0x1A and no extraction of that art exists. 16 px fits
#: between the list's right edge (`win_x + 239`) and the window's
#: (`win_x + 267`).
BUTTON_SIZE = 16

#: The application name is printed with a leading caret, which is the
#: original's own bullet: `buffer[0] = '^'` (tech.cpp:10).
APP_BULLET = "^"

#: `Get_Group_List_`'s own statuses. 3 is researched and is skipped; 4
#: is "this is the field being researched" and is not a
#: TECH_RESEARCH_STATUS at all, it is assigned at tech.cpp:1117.
STATUS_RESEARCHED = 3
STATUS_CURRENT = 4

#: A hyper-advanced field past this level counts as researched
#: (tech.cpp:1119-1121).
HYPER_DONE_ABOVE = 20

#: status -> the palette key its text is drawn in. The mapping IS
#: `s_list_state.group_colors` plus the overrun the module docstring
#: explains: 1 -> `_tech_color[3]`, 2 -> `_tech_color[0]` (the panel's
#: own row colour), 4 -> `_tech_color[2]` (the panel's current-research
#: colour).
STATUS_COLOUR = {0: ("list_none", (120, 132, 156)),
                 1: ("list_done", (150, 176, 210)),
                 2: ("row", (198, 212, 238)),
                 STATUS_CURRENT: ("row_current", (250, 226, 150))}


class Item:
    """One FIELD in the popup: its name, its applications, its status."""

    __slots__ = ("field", "apps", "statuses", "status", "y")

    def __init__(self, field, apps, statuses, status):
        self.field = field
        self.apps = tuple(apps)
        self.statuses = tuple(statuses)
        self.status = status
        #: Filled by `paginate`, which is where the original sets it
        #: too (`Init_List_Data_`).
        self.y = LIST_Y

    def row_rect(self, row, list_x):
        """Row `row`'s 640x480 rectangle (`Add_Fields_To_List_Page_`,
        list.cpp:94-116): `(x, y1[i] + y) .. (x + 213, y2[i] + y)`."""
        return (list_x,
                researchlist.ROW_Y1[row] + self.y,
                list_x + ITEM_WIDTH - APP_X_OFFSET,
                researchlist.ROW_Y2[row] + self.y)


def field_slots(field, apps_by_field=None):
    """`_technology_fields[field].tech[4]`, PADDED, as the engine holds it.

    The padding is load-bearing and not tidiness: `Get_Group_List_`
    walks all four slots and reads `tech_applications[tech[i]]` for the
    empty ones too, which is `tech_applications[0]`. Dropping the
    padding would silently decide that question instead of letting the
    player's own data answer it.
    """
    slots = list((apps_by_field
                  or researchlist.field_applications()).get(field, ()))
    return tuple(slots + [0] * (researchlist.MAX_ROWS - len(slots)))


def group_list(tech_fields, tech_applications, current_field, group,
               hyper_levels=None, apps_by_field=None):
    """The items `Get_Group_List_` would build for one category.

    `hyper_levels` is `s_player.hyper_advanced_tech`, which has one
    verified source and not two (`core/structs/unverified.py`). None
    means "not vouched for", and then the hyper skip does not fire —
    the field stays in the list rather than being dropped on a number
    nobody may trust yet. Stated here because a list that is silently
    one row short is the failure this screen already paid for once.
    """
    apps_by_field = apps_by_field or researchlist.field_applications()
    items, field = [], researchlist.FIRST_FIELD_IN_GROUP[group]
    while field != 0:
        status = tech_fields[field]
        if current_field == field:
            status = STATUS_CURRENT
        elif (field >= researchlist.FIELD_HYPER_FIRST
                and hyper_levels is not None
                and hyper_levels[field - researchlist.FIELD_HYPER_FIRST]
                > HYPER_DONE_ABOVE):
            status = STATUS_RESEARCHED
        if status != STATUS_RESEARCHED:
            slots = field_slots(field, apps_by_field)
            if status == 0 and any(
                    tech_applications[a] == STATUS_RESEARCHED
                    for a in slots):
                status = 1
            if status >= 1:
                apps, statuses = [], []
                for app in slots:
                    app_status = tech_applications[app]
                    if app_status < 1:
                        continue
                    if status == STATUS_CURRENT:
                        app_status = STATUS_CURRENT
                    elif app_status == 1 and status == 2:
                        app_status = 2
                    apps.append(app)
                    statuses.append(app_status)
                if apps:
                    items.append(Item(field, apps, statuses, status))
        field = researchlist.NEXT_FIELD[field]
    return items


def paginate(items):
    """`[[Item, …], …]`, and every item's `y` set (list.cpp:143-186).

    An item whose bottom would pass `Y_MAX` starts the NEXT page at the
    top instead — `Init_List_Data_` writes `stop_flag` and rewinds `y`,
    and `Display_List_Page_` then draws from one stop flag to the next.
    The step is `_app_name_y[app_count] + 8`, which is the table read
    ONE PAST the last label: four applications step 87, one steps 42.
    """
    pages, y = [[]], LIST_Y
    for item in items:
        item.y = y
        step = APP_NAME_Y[len(item.apps)] + ITEM_SPACING
        y += step
        if y > Y_MAX:
            item.y = LIST_Y
            y = LIST_Y + step
            pages.append([item])
        else:
            pages[-1].append(item)
    return [p for p in pages if p] or [[]]


class TechListPopup:
    """The popup's state: which category, which page, what is hovered.

    Owns no text and no geometry of its own — the screen hands it the
    entry it was opened from, and `window_x` follows that entry's own
    column, which is what the original does with
    `_list_window_x_offsets`.
    """

    def __init__(self):
        self.entry = None
        self.pages = []
        self.page = 0
        self.hover = None          # (item index on the page, row)

    @property
    def visible(self):
        return self.entry is not None

    def open(self, entry, items):
        self.entry = entry
        self.pages = paginate(items)
        self.page = 0
        self.hover = None

    def close(self):
        self.entry = None
        self.pages = []
        self.page = 0
        self.hover = None

    # ── Geometry ──────────────────────────────────────────

    def window_x(self, origin):
        """`_list_window_x_offsets[entry] + _g_scrn_x` (tech.cpp:421)."""
        return WINDOW_X_OFFSETS[self.entry.index] + origin

    def window_rect(self, origin):
        x = self.window_x(origin)
        return (x, WINDOW_Y1, x + WINDOW_DX2, WINDOW_Y2)

    def list_x(self, origin):
        return self.window_x(origin) + LIST_DX

    def button_rects(self, origin):
        """(up, down) in native pixels, or None where the page has none.

        `Set_List_Up_Down_Field_Drawing_` (list.cpp:120-134) enables
        DOWN only below the last page and UP only above the first, and
        a disabled button's field type becomes -1001 — so the original
        does not merely grey it, it takes it out of the input walk.
        """
        x = self.window_x(origin)
        up = ((x + UP_DX, UP_Y, x + UP_DX + BUTTON_SIZE,
               UP_Y + BUTTON_SIZE) if self.page > 0 else None)
        down = ((x + DOWN_DX, DOWN_Y, x + DOWN_DX + BUTTON_SIZE,
                 DOWN_Y + BUTTON_SIZE)
                if self.page < len(self.pages) - 1 else None)
        return up, down

    def items(self):
        return self.pages[self.page] if self.pages else []

    # ── Input, native pixels ──────────────────────────────

    def at(self, origin, nx, ny):
        """What a native point is: ("up",), ("down",), ("row", i, k),
        ("window",) or None for outside the window entirely."""
        up, down = self.button_rects(origin)
        for name, r in (("up", up), ("down", down)):
            if r and r[0] <= nx <= r[2] and r[1] <= ny <= r[3]:
                return (name,)
        lx = self.list_x(origin)
        for i, item in enumerate(self.items()):
            for row in range(len(item.apps)):
                x1, y1, x2, y2 = item.row_rect(row, lx)
                if x1 <= nx <= x2 and y1 <= ny <= y2:
                    return ("row", i, row)
        wx1, wy1, wx2, wy2 = self.window_rect(origin)
        if wx1 <= nx <= wx2 and wy1 <= ny <= wy2:
            return ("window",)
        return None

    def page_by(self, step):
        self.page = max(0, min(len(self.pages) - 1, self.page + step))
        self.hover = None


def draw(surface, layout, style, popup, origin, names, wording):
    """Draw the popup. The caller has already drawn the panel under it."""
    if not popup.visible:
        return
    rect = pygame.Rect(*geom_mod.window_rect(popup.window_rect(origin),
                                             layout))
    pygame.draw.rect(surface, col("list_fill", (14, 18, 28)), rect)
    pygame.draw.rect(surface, col("list_border", (70, 104, 168)), rect, 2)

    title = wording.list_title(popup.entry.group) if wording else None
    if title:
        size = layout.font_size(15)
        surf = style.render_text(title, size, col("category",
                                                  (128, 148, 186)))
        tx, ty = geom_mod.window_point(
            (popup.window_x(origin) + TITLE_DX, TITLE_Y), layout)
        surface.blit(surf, (tx - surf.get_width() // 2, ty))

    lx = popup.list_x(origin)
    for i, item in enumerate(popup.items()):
        _blit_text(surface, style,
                   names.field_name(item.field) if names else None,
                   geom_mod.window_point((lx, item.y), layout),
                   geom_mod.window_width(lx, item.y, ITEM_WIDTH, layout),
                   layout.font_size(15),
                   palette.col("research_select",
                               *STATUS_COLOUR[item.status]))
        for row, app in enumerate(item.apps):
            if popup.hover == (i, row):
                fill = pygame.Rect(*geom_mod.window_rect(
                    item.row_rect(row, lx), layout))
                shade = pygame.Surface(fill.size, pygame.SRCALPHA)
                shade.fill(col("hover", (70, 104, 168, 90)))
                surface.blit(shade, fill.topleft)
            label_y = item.y + APP_NAME_Y[row]
            _blit_text(surface, style,
                       APP_BULLET + (names.application_name(app)
                                     if names else str(app)),
                       geom_mod.window_point((lx + APP_X_OFFSET, label_y),
                                             layout),
                       geom_mod.window_width(lx + APP_X_OFFSET, label_y,
                                             APP_LABEL_WIDTH, layout),
                       layout.font_size(13),
                       palette.col("research_select",
                                   *STATUS_COLOUR[item.statuses[row]]))

    for which, native in zip(("up", "down"), popup.button_rects(origin)):
        if native is None:
            continue
        box = pygame.Rect(*geom_mod.window_rect(native, layout))
        pygame.draw.rect(surface, col("list_border", (70, 104, 168)),
                         box, 1)
        # INVENTION: the original's arrows are TECHSEL sprites and no
        # extraction of that art exists, so the shape is ours.
        mid, colr = box.centerx, col("category", (128, 148, 186))
        if which == "up":
            pts = [(mid, box.top + 3), (box.left + 3, box.bottom - 3),
                   (box.right - 3, box.bottom - 3)]
        else:
            pts = [(mid, box.bottom - 3), (box.left + 3, box.top + 3),
                   (box.right - 3, box.top + 3)]
        pygame.draw.polygon(surface, colr, pts)
