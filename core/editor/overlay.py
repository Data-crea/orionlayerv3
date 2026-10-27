"""Editor overlay rendering — the box outlines, the selection and the info bar.

Pure drawing functions; all state lives on the Editor instance
passed in as `ed`. Split from editor.py to keep both files under
the 300-line limit.
"""
import time
import pygame

from core.box import get_stored_resolutions
from core.editor import boxclass, labels
from core.editor.constants import (
    H_REF, C_SEL, C_OUT, C_IBG, C_ITX, C_ASN, C_DORMANT,
)


def render(ed, surface):
    """Full editor overlay. Called from the main render loop."""
    if not ed.active:
        return
    L = ed.app.layout
    scr = ed.app.dispatcher.top
    if not scr:
        return
    nf = ed.app.style.get_font(L.font_size(12))
    names = labels.load(getattr(scr, "_screen_dir", ""))
    # ONE BOX CHOSEN, THE OTHERS GO: with a selection only that box is
    # outlined and named, so what is being moved is not lost among its
    # neighbours; deselecting (Esc, or a click on nothing) shows all again.
    for box in scr.boxes:
        if not box.screen_rect:
            continue
        if ed.selected is not None and box is not ed.selected:
            continue
        dormant = scr.editor_dormant(box)
        # A popup's box with no popup open is dim and says so, so it is
        # not taken for a box of the picture that lost its content.
        colour = C_DORMANT if dormant else C_OUT
        pygame.draw.rect(surface, colour, box.screen_rect, 1)
        # EVERY BOX WEARS ITS TITLE, clipped to itself, so the picture
        # says what each rectangle is without a technical name.
        text = labels.title(names, box.name) + (" (popup)" if dormant else "")
        clip = surface.get_clip()
        surface.set_clip(box.screen_rect.clip(clip))
        surface.blit(nf.render(text, True, colour),
                     (box.screen_rect.x + 3, box.screen_rect.y + 2))
        surface.set_clip(clip)
    if ed.selected and ed.selected.screen_rect:
        draw_sel(ed, surface, L)
    ed.panel.draw(surface)
    draw_info(ed, surface, L)
    f = ed.app.style.get_font(L.font_size(14))
    res = f"{ed.app.win_w}x{ed.app.win_h}"
    surface.blit(f.render(f"EDITOR [{res}]", True, C_SEL), (10, 10))
    if ed._save_flash and time.monotonic() - ed._save_flash < 2:
        sf = ed.app.style.get_font(L.font_size(18))
        surface.blit(sf.render((getattr(ed, "_save_note", "") or f"SAVED [{res}]"), True, C_ASN),
                     (10, 38))


#: Handle key -> where it sits on the box, as `Editor._hit_resize`
#: names them. ONE table, so the drawing and the hit test cannot offer
#: different handles (decision 5).
HANDLE_AT = {
    "tl": (0.0, 0.0), "tr": (1.0, 0.0), "bl": (0.0, 1.0),
    "br": (1.0, 1.0), "t": (0.5, 0.0), "b": (0.5, 1.0),
    "l": (0.0, 0.5), "r": (1.0, 0.5),
}


def draw_sel(ed, surface, L):
    """The selection outline, and only the handles its class offers.

    **A HANDLE THAT IS DRAWN AND REFUSED IS WORSE THAN NO HANDLE.**
    Until 9 September 2026 all eight were drawn on every box, and on
    the colony screen every one of the fourteen boxes refuses at least
    some of them — a cutout refuses all eight. Drawing what cannot be
    used is how an editor teaches somebody the wrong model of its own
    rules; `core.editor.boxclass` decides, and the same function the
    click path asks.
    """
    box = ed.selected
    r = box.screen_rect
    pygame.draw.rect(surface, C_SEL, r, 2)
    hs = max(4, int(H_REF * L.scale))
    kind = boxclass.classify(ed._screen_name(), box.name)
    for key in boxclass.HANDLES[kind]:
        fx, fy = HANDLE_AT[key]
        hx = r.x + int(r.w * fx)
        hy = r.y + int(r.h * fy)
        pygame.draw.rect(surface, C_SEL,
                         (hx-hs//2, hy-hs//2, hs, hs))


def draw_info(ed, surface, L):
    ih = max(24, int(28 * L.scale))
    bg = pygame.Surface((ed.app.win_w, ih), pygame.SRCALPHA)
    bg.fill(C_IBG)
    iy = ed.app.win_h - ih
    surface.blit(bg, (0, iy))
    # A REFUSAL WINS THE LINE. It answers what was just tried, so it
    # has to be readable at the moment of trying rather than in a log
    # the person dragging is not watching.
    if ed.refusal:
        f = ed.app.style.get_font(L.font_size(16))
        surface.blit(f.render(ed.refusal[:200], True, C_ASN), (10, iy + 4))
        return
    if ed.selected:
        b = ed.selected
        x, y, w, h = b.ref_rect
        skin = b.style.get("skin", "none")
        fid = b.field_id if b.field_id is not None else "none"
        extra = ""
        # THE SCREEN SAYS WHAT ITS BOX MEANS. This was a
        # `hasattr(scr, "_race_by_id")` naming ONE screen from
        # inside generic editor code; `ScreenBase.editor_note` is
        # the same information asked for on the side that has it,
        # and the colony list needs it for values that have no
        # rect at all — the row band, the derived sprite step, the
        # lower bound the editor REPORTS and must never clamp.
        _note = None
        if ed.app.dispatcher.top is not None:
            _note = ed.app.dispatcher.top.editor_note(b)
        if _note:
            extra = " " + str(_note)
        # THE CLASS IS ON THE LINE, because it decides what the
        # handles do and nothing on screen shows it: a cutout and
        # a hand-placed box are the same rectangle.
        _kind = boxclass.classify(ed._screen_name(), b.name)
        t = (f"'{b.name}' [{_kind}] ({x},{y}) {w}x{h} "
             f"skin={skin} field={fid} "
             f"fs={b.style.get('font_scale', 1.0):.1f}{extra}")
    else:
        scr = ed.app.dispatcher.top
        stored = []
        if scr and scr._screen_dir:
            stored = get_stored_resolutions(
                getattr(scr, "_boxes_dir", None) or scr._screen_dir)
        res_key = f"{ed.app.win_w}x{ed.app.win_h}"
        if stored:
            src = "own" if res_key in stored else "fallback"
            res_info = f"  [{src} | saved: {', '.join(stored)}]"
        else:
            res_info = "  [no saved data]"
        t = ("Click a box to select it | P panel | "
             "Ctrl+S save" + res_info)
    f = ed.app.style.get_font(L.font_size(13))
    surface.blit(f.render(t, True, C_ITX), (10, iy + 4))

