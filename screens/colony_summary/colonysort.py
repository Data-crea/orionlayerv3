"""The seven sort keys, one box each, and RETURN beside them.

**EACH KEY IS ITS OWN HOLE AGAIN — DEVIATION, 12 September 2026.**
This reverses "THE BAR IS ONE HOLE NOW" (Stage A3, 7 September
2026), which cut one `sort_bar` on the reading that the original has
a single recessed blue strip with seven labels laid along it (the
framebuffer at native y 445-470) and therefore that the division
belongs in code. That reading of the ORIGINAL is unchanged and is
still what the source says. What changed is the artwork: Data's
frame has seven slot cut-outs and he places one key in each, so the
division goes back into the geometry. `layout_reference.json` types
seven rects, `layout` reads them, and nothing here distributes
anything along a bar any more.

**AND THE GAPS STOP BEING OURS, WHICH IS THE POINT.** The even
spacing this module used to compute was marked here as a READING and
not a transcription, because the source carries no table of
positions. A hand-placed box carries no reading at all — it is where
the artwork puts it — so the marking that went with the arithmetic
goes with the arithmetic.

**THE ACTIVE KEY IS HIGHLIGHTED AT ITS OWN LABEL WIDTH, AND THAT IS
STILL TRANSCRIBED — IT IS NOT THE BOX.** The original fills a
rectangle the width of the word plus a small pad: with `name` active
the lit box is native x 92..138 around ink at 94..136, while the
field it sits in runs 89..139 (colsum.cpp:267-268). So the lit box
is the WORD plus two native px per side and is inset from its own
field, and "Name" lights a short box where "Producing" lights a long
one. Filling the whole slot instead would be the easy thing now that
each key has a slot, and it would be our invention wearing the
original's colours — the tell being a highlight the same width for
every key. `HIGHLIGHT_PAD` below carries the measurement.

**ONE FUNCTION, TWO ANSWERS** (decision 5). `layout` returns, per
key, both the HIT rect and the HIGHLIGHT rect. The renderer draws the
second and the click test walks the first; there is no second
arithmetic to drift. **THE HIT RECT IS THE BOX** — the whole slot,
so a click anywhere in a cut-out sorts by the key drawn in it, which
is what a hole in a frame promises — and the highlight is the word
inside it. The original's own fields are wider than their text too
(89..139 for a word that measures 92..138).

**NOTHING HERE KNOWS WHERE A BOX IS.** The seven rects come from
`layout_reference.json` through `boxes.json`, which is the chain
decision 3 already holds to the artwork: a slot Data moves in GIMP
arrives here without this module being touched, and a slot he swaps
with its neighbour arrives named correctly because `frame_holes`
matches a hole to a rect by OVERLAP and not by order.

**THE `native_click` POINTS ARE UNCHANGED AND STILL AUTHORITATIVE.**
They are one point inside each of the original's own buttons
(colsum.cpp:267-273, kept in `layout.json` as the injection point and
as the checkable half of decision 39), they are what gets INJECTED,
and a smoke check still asserts every one of them falls inside the
button it belongs to. What they no longer do is justify an arithmetic
here — the even gaps they were the evidence for are gone with it.
"""
import pygame

#: Breathing room around a highlighted word, reference px.
#:
#: MEASURED, and the "about" is gone — 9 September 2026, off the
#: original's own framebuffer at 1080p with `name` active. The lit box
#: is native x 92..138, y 450..466 and the word's ink inside it is
#: x 94..136, y 452..463: **2 native px left and right**, 2 top and 3
#: bottom. Two native px is 6 reference, which is what this was.
#:
#: WHAT THE ORIGINAL ACTUALLY DRAWS, because it is not this
#: construction at all. `Add_Multi_Button_Field_` takes the field's
#: extent from `animate::Get_Width_/Get_Height_(pic)` (fields.cpp) and
#: `Draw_Field_`'s FIELD_TYPE_MULTI_BUTTON arm blits that anim and
#: then prints the word with `fonts::Print_Centered_` at the field's
#: midpoint (fields.cpp:1896-1925). So the box is ARTWORK, one sprite
#: per button in the player's COLSUM.LBX, and the word is centred in
#: it — the box does not follow the word, the word follows the box.
#: The seven field origins are 89 / 140 / 219 / 262 / 326 / 393 / 480
#: (colsum.cpp:267-273) and their spacing is not uniform, which is
#: what says each sprite is cut to its own word.
#:
#: HD cannot ship those sprites (decision 42), so it fills a rect
#: instead and sizes it from the word plus this pad. That is a
#: DEVIATION in construction and it lands in the same place: the
#: measured 2 px per side is exactly what the artwork leaves.
HIGHLIGHT_PAD = 6


def display(label):
    """The string as it is DRAWN.

    **DEVIATION — THE HD FRONTEND'S TYPOGRAPHY.** The word is drawn
    in CAPITALS where the original prints it in mixed case, and on
    the sidebar the original's colon is dropped as well. Decided by
    Data on 9 September 2026 and kept: it is the HD frontend's own
    type voice, applied to every label on this screen, and the
    original's own column headings are capitals too.

    What it deviates FROM is on record either way, which is what
    makes this a deviation rather than a drift. `layout.json` stores
    the labels as the original prints them — "Name", "Population",
    "Producing" — and `empire._estrings_note` carries the sidebar's
    strings as `orion2_str.h` comments them, colon included:
    `ESTR_SRESERVE_SD '%sReserve: %d'`. Both are transcriptions; only
    the rendering is ours.

    Marked here, in `colonyempire.value_row` for the sidebar half, in
    `layout.json` under `sort._typography_deviation`, in
    `v3_projektstatus.md`, and in a smoke check that holds the stored
    labels to the original's spelling so the deviation stays a
    RENDERING choice and cannot become an edit to the data.

    **ONE HOME, BECAUSE MEASURING ONE STRING AND DRAWING ANOTHER IS
    HOW THE HIGHLIGHT STOPPED FITTING** — 9 September 2026. `layout`
    measured `label` and `render` drew `label.upper()`, and Aldrich's
    capitals are wider: at 1080p "Name" measures 52 px and "NAME"
    draws 56, "Industry" 76 against 96, "Producing" 92 against 113.
    So the lit box was 4 to 21 px short of the word it was supposed
    to contain, worst on the longest words, and the active key read
    as a smudge behind its own text rather than as a selection.

    Nothing about it looked wrong in the code: both lines call
    `Style.render_text`, both pass the same label, and the `.upper()`
    sits at the end of one of them. This is decision 5 for a STRING
    rather than for a rect — one function produces the thing, and
    whoever measures and whoever draws both call it.
    """
    return label.upper()


class SortButton:
    """One key's two rectangles and the label that produced them."""

    __slots__ = ("key", "label", "hit", "highlight")

    def __init__(self, key, label, hit, highlight):
        self.key = key
        self.label = label
        self.hit = hit
        self.highlight = highlight


def layout(boxes, keys, style, font_size):
    """[SortButton], one per key, each sitting in ITS OWN BOX.

    `boxes` maps a sort key to that key's slot rect in WINDOW pixels;
    `keys` is [(key, label)] and fixes the ORDER of the result, which
    is the order `layout.json` stores and not a left-to-right reading
    of the rects. A key with no box is skipped rather than placed
    somewhere — there is no bar left to fall back on, and a button
    drawn at a guessed position is worse than one that is absent.

    **THE HIT RECT IS THE WHOLE BOX. THE HIGHLIGHT IS THE WORD PLUS
    `HIGHLIGHT_PAD`, CENTRED IN IT — never the box's own width.**
    That is the transcription and it is the one thing this rewrite
    had to carry across: the original lights a rectangle around the
    word (native 92..138 for ink at 94..136) inside a field that is
    wider (89..139), so the lit box grows with the word and "Name"
    lights a short one where "Producing" lights a long one. Now that
    every key owns a slot, filling the slot would be one line
    shorter and would make all seven highlights the same width,
    which the original's never are.

    It is CLAMPED to the box and not allowed out of it: a word wider
    than the slot Data drew lights the whole slot and no more, and
    the smoke test is what says whether that ever happens.

    Widths are measured by RENDERING, never by one font's `.size()` —
    `Style.render_text` may mix two fonts inside a string, so a
    single font's metrics are not the width that will be drawn
    (decision 30's consequence).
    """
    out = []
    for key, label in keys:
        rect = boxes.get(key)
        if rect is None:
            continue
        box = pygame.Rect(rect)
        word = style.render_text(display(label), font_size,
                                 (255, 255, 255)).get_width()
        lit = min(box.width, word + 2 * HIGHLIGHT_PAD)
        out.append(SortButton(
            key, label, box,
            pygame.Rect(box.x + (box.width - lit) // 2, box.y,
                        lit, box.height)))
    return out


#: A sort key's box name. The seven boxes are `sort_<key>`, which is
#: how `layout_reference.json` types them and how `frame_holes` names
#: the holes it finds — one spelling rule in one place, so the screen
#: and the plate cannot disagree about what a box is called.
def box_name(key):
    return f"sort_{key}"


def for_screen(screen):
    """The seven buttons of `screen`, or [].

    Takes the screen the way `colonyheader.render_for` does, so the
    boxes, the font size and the label list are read in ONE place and
    the renderer and the click test cannot pick up different ones
    (decision 5). Rebuilt per call rather than cached: the boxes move
    with the window and the labels come from `layout.json`, so there
    is nothing here worth remembering.

    A MISSING BOX IS NOT AN ERROR HERE. The plate is generated and a
    clone that has not run `tools/setup.py` has none of it; the
    screen still has to draw. `layout` skips a key with no box and
    the smoke test is where the seven are required to exist.
    """
    keys = [(b["key"], b["label"])
            for b in screen._data.get("sort", {}).get("buttons", [])]
    boxes = {}
    for key, _label in keys:
        box = screen.box_rect(box_name(key))
        if box:
            boxes[key] = screen.layout.rect(box)
    return layout(boxes, keys, screen.style, font_size(screen))


def font_size(screen):
    """One size for all seven, from the FIRST slot that has a style.

    Per-box would let two keys be drawn at two sizes on one row,
    which no frame can mean; a constant here would be a second copy
    of a number `boxes.json` already holds. So the row's size is the
    first box's and the rest follow it — and `18` is the fallback
    only when no slot carries a style at all.
    """
    for spec in screen._data.get("sort", {}).get("buttons", []):
        style = screen.box_style(box_name(spec["key"]))
        if "font_size" in style:
            return screen.layout.font_size(style["font_size"])
    return screen.layout.font_size(18)


def button_at(buttons, x, y):
    """The key under a window point, or None."""
    for button in buttons:
        if button.hit.collidepoint(x, y):
            return button.key
    return None


def render(surface, buttons, active_key, unavailable, mouse,
           style, font_size, active_bg, hover_bg, text, text_dim):
    """Draw the seven words. The renderer's half of `layout`.

    The highlight is filled only for the active key and the hovered
    one; every other word sits on its slot's own panel fill, which is
    what the original does — six plain words and one lit box.

    **THE WORD IS CENTRED IN ITS BOX, NOT IN ITS HIGHLIGHT.** The two
    are the same point while the highlight is centred in the box, and
    they stop being the same the moment a word is wider than its slot
    and the highlight clamps. The box is the thing the artwork drew,
    so the box is what the word is centred in — and the original does
    the same: `Draw_Field_`'s FIELD_TYPE_MULTI_BUTTON arm prints with
    `fonts::Print_Centered_` at the FIELD's midpoint
    (fields.cpp:1896-1925), not at its sprite's.
    """
    for button in buttons:
        active = button.key == active_key
        if active or button.hit.collidepoint(mouse):
            surface.fill((active_bg if active else hover_bg)[:3],
                         button.highlight)
        # **DEVIATION — HD DIMS A CONTROL THE ORIGINAL DOES NOT.**
        # All seven of the original's buttons are the same field,
        # `Add_Multi_Button_Field_(x, 446, …, &_g_sort_index, 0..6, …)`
        # (colsum.cpp:267-273), and it draws them alike: measured on
        # its own framebuffer, every inactive label is palette white
        # (196, 196, 196) and PRODUCING is one of them; only the
        # active one differs, at (196, 208, 252).
        #
        # HD dims the keys in `colonyrows.SORT_UNAVAILABLE` — today
        # only `producing`, because `TECHDATA::_buildings[].cost` is
        # not extracted, so the key orders buildings among themselves
        # by name where `cmp_Prod_` (colsum.cpp:1091) orders them by
        # cost. A control that is right on one save and wrong on the
        # next is worse than one that says it cannot do the job, and
        # that is the whole argument — but the ORIGINAL says nothing,
        # so saying it is ours.
        #
        # **IT ENDS WITH THE EXTRACTION**, not by taste: once the cost
        # table is transcribed with its checker (decision 36's
        # pattern), the key is correct and the dimming goes with its
        # markings. Until then it is marked here, in `layout.json`
        # under `sort._unavailable_deviation`, in `v3_projektstatus.md`
        # and in a smoke check.
        colour = text_dim if button.key in unavailable else text
        word = style.render_text(display(button.label), font_size,
                                 colour[:3])
        surface.blit(word, (
            button.hit.x + (button.hit.width - word.get_width()) // 2,
            button.hit.y + (button.hit.height - word.get_height()) // 2))


def render_return(surface, screen, mouse, bg, hover_bg, text_color):
    """RETURN, which is a button on this row and not a sort key.

    It keeps its own box because the plate cuts it as its own hole —
    the original draws it as a separate raised plate to the right of
    the bar (see the framebuffer at native x 523+), and it is the one
    control here that takes the CLICK path, because its field reports
    no letter (decision 39's fallback).
    """
    box = screen.box_rect("return")
    if not box:
        return
    rect = pygame.Rect(*screen.layout.rect(box))
    # THE ONE FILL THAT IS NOT IN `panels`: RETURN draws its own,
    # because it is the one control here that takes the CLICK path and
    # its hover has to reach the whole plate.
    surface.fill((hover_bg if rect.collidepoint(mouse) else bg)[:3], rect)
    label = screen._data.get("return", {}).get("label", "Return")
    word = screen.style.render_text(
        label.upper(),
        screen.layout.font_size(
            screen.box_style("return").get("font_size", 24)),
        text_color[:3])
    surface.blit(word, (rect.x + (rect.w - word.get_width()) // 2,
                        rect.y + (rect.h - word.get_height()) // 2))
