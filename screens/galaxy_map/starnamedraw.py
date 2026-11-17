"""The star names on the galaxy map: which name, in which colour, drawn how.

One job: `star_label` and `render_star_names` (with the owner-coloured,
haloed, outlined drawing and the surrender underline). Split out of
renderer.py (decision 6) at the seam between the map's sprite layers and
its text layer; the colours (`OWNER_COLORS`, `NEUTRAL_COLOR`,
`OUTLINE_COLOR`) stay in renderer.py, which does not import this module.
"""
import pygame

from screens.galaxy_map import renderer, starnames

STAR_NAME_GAP = 0.40      # of icon height, below the star centre


def star_label(s, player_num, players, omniscient, facts=None):
    """Name to draw for a star, or "" when it stays hidden.

    Mirrors MAINSCR::Get_Star_Name_ through `starnames.spec`:
      - black holes are never labelled
      - without lore: an unvisited system with no contacted colony owner
        shows nothing; an outposts-only system is written lower-case
      - with lore: an unvisited foreign system shows "(Name)"
    `facts` (starnames.facts_of) carries the colonies; without it the
    star's own owner field stands in, as before work order 402.
    """
    sp = starnames.spec(s, player_num, players, omniscient, facts)
    return sp.text if sp is not None else ""


def _owner_rgb(players, owner):
    pcol = getattr(players[owner], "color", None) if (
        owner is not None and 0 <= owner < len(players)) else None
    return (renderer.OWNER_COLORS.get(pcol, renderer.NEUTRAL_COLOR) if pcol is not None
            else renderer.NEUTRAL_COLOR)[:3]


def render_star_names(surface, ctx, stars, heights, render_label,
                      player_num, players, omniscient, facts=None,
                      pulses=None, clamp=None):
    """Star names with a one-pixel outline, centred under the icon.

    Names are not drawn on an extended map at maximum zoom-out
    (MAINSCR::Print_Star_Names_ returns first), a highlighted one apart.

    `render_label(text, colour)` returns a surface. It is a callable
    rather than a pygame Font because a lore-only name reads "(Name)",
    and the DEMO Bank Gothic draws parentheses as a watermark — the
    caller hands in Style.render_text, which splits the string across
    two fonts, so the renderer knows nothing about skins.

    Work order 402: the name is `starnames.spec` (outposts lower-case and
    darker, a shared system split into its owners' colours), `pulses`
    {star index: colour offset} brightens a highlighted name, `clamp` is
    the rect a name is pushed inside at the widest zoom (TRANSCRIPTION
    `name_clamp`, mainscr.cpp:1274-1283), and a surrender underlines it
    (TRANSCRIPTION `name_surrender`, mainscr.cpp:1285-1313). A split name has neither: the original returns
    after the bitmap name (:1262-1270). TRANSCRIPTION
    `name_highlight_when_hidden`: `Highlight_Star_` has no
    `Is_Extended_Max_Map_View_` test (mainscr.cpp:1833-1872, unlike :668),
    so a star in `pulses` is named under `names_hidden` too.
    """
    view = ctx.view
    pulses = pulses or {}
    widest = ctx.map_scale == ctx.max_map_scale
    for s in stars:
        if ctx.names_hidden and int(s.index) not in pulses:
            continue
        sp = starnames.spec(s, player_num, players, omniscient, facts)
        if sp is None:
            continue
        level = pulses.get(int(s.index), 0)
        base = _owner_rgb(players, sp.owner)
        if sp.steps:
            base = starnames.darker(base, sp.steps)
        base = starnames.shade(base, level)
        text = render_label(sp.text, base)
        shadow = render_label(sp.text, renderer.OUTLINE_COLOR[:3])
        sx, sy = view.to_screen(s.x, s.y)
        ih = heights.get(s.index, 0)
        # HD EXTENSION `star_name_halo`: a soft dark glow round the
        # outline, so a name reads over a nebula or a bright star
        halo = _name_halo(text, shadow)
        pad = (halo.get_width() - text.get_width()) // 2
        w = text.get_width()
        x = int(sx - w / 2)
        y = int(sy + ih * STAR_NAME_GAP)
        if clamp is not None and widest and not sp.split:
            if x < clamp.left:
                x = clamp.left
            elif x + w > clamp.right:
                x = clamp.right - w
        surface.blit(halo, (x - pad, y - pad))
        # HD EXTENSION `star_name_halo`: a two pixel outline and the name
        # drawn twice, one pixel apart, so the thin face reads heavier
        for dx, dy in _NAME_OUTLINE:
            surface.blit(shadow, (x + dx, y + dy))
        if sp.split:
            parts = [(x0, x1, starnames.shade(_owner_rgb(players, o), level))
                     for o, x0, x1 in starnames.spans(sp.split, w)]
        else:
            parts = [(0, w, None)]
        for n, (x0, x1, rgb) in enumerate(parts):
            img = text if rgb is None else render_label(sp.text, rgb)
            if not sp.split:
                surface.blit(img, (x, y))
                surface.blit(img, (x + 1, y))
                continue
            # a part keeps to its span (the last may run one pixel on), so
            # the double draw does not bleed into the next owner's colour
            keep = surface.get_clip()
            right = x1 + (1 if n == len(parts) - 1 else 0)
            surface.set_clip(keep.clip(pygame.Rect(
                x + x0, y - 4, right - x0, img.get_height() + 8)))
            surface.blit(img, (x, y))
            surface.blit(img, (x + 1, y))
            surface.set_clip(keep)
        if not sp.split:
            _surrender_line(surface, ctx, s, player_num, players, sx,
                            y + text.get_height(), w)


def _surrender_line(surface, ctx, s, player_num, players, sx, y, w):
    """TRANSCRIPTION `name_surrender` (mainscr.cpp:1285-1313): under the
    name, for the empire the star's owner surrendered to
    (`star.surrender_to[PLAYER_NUM]`, 0..7), a second line below map scale
    30; it starts at the star's x, not the clamped name's.

    DEVIATION `surrender_colour`: the original's colour is a palette index,
    `surrender_colors` by the empire's colour, +1 for line two, -3 for
    colours 3 and 5 (:1292-1301); HD has only the skin's RGB, so line one is
    the empire's colour, line two x 1.25 (x 0.8 for 3 and 5), the width the
    drawn name's. UNVERIFIED live."""
    slots = getattr(s, "surrender_to", None)
    if not slots or not 0 <= player_num < len(slots):
        return
    to = slots[player_num]
    if not 0 <= to < len(players):
        return
    rgb = _owner_rgb(players, to)
    t = max(1, int(round(ctx.px)))
    x0 = int(sx - w / 2)
    # LOOK EXCEPTION transcription: the empire's own colour
    pygame.draw.rect(surface, rgb, (x0, y, w, t))
    if ctx.map_scale < 30:
        k = 0.8 if getattr(players[to], "color", None) in (3, 5) else 1.25
        rgb2 = tuple(min(255, int(c * k)) for c in rgb)
        # LOOK EXCEPTION transcription: the underline's second line
        pygame.draw.rect(surface, rgb2, (x0, y + t, w, t))


_NAME_OUTLINE = ((-1, 0), (2, 0), (0, -1), (0, 1), (-1, -1), (2, -1),
                 (-1, 1), (2, 1), (-2, 0), (3, 0), (0, -2), (0, 2))

#: Halos made so far, keyed by the label picture they came from (the
#: picture itself is held so its id cannot be reused); bounded.
_HALOS = {}
HALO_KEEP = 512


def _name_halo(text, shadow):
    """The soft dark glow behind a label: its outline picture grown by
    `r` pixels in eight directions, at a fraction of full strength."""
    hit = _HALOS.get(id(text))
    if hit is not None and hit[0] is text:
        return hit[1]
    r = max(2, text.get_height() // 7)
    w, h = text.get_size()
    out = pygame.Surface((w + 2 * r, h + 2 * r), pygame.SRCALPHA, 32)
    glow = shadow.copy()
    glow.set_alpha(70)
    for d in range(1, r + 1):
        for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d),
                       (-d, -d), (d, -d), (-d, d), (d, d)):
            out.blit(glow, (r + dx, r + dy))
    if len(_HALOS) >= HALO_KEEP:
        _HALOS.clear()
    _HALOS[id(text)] = (text, out)
    return out
