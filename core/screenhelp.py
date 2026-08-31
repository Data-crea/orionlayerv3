"""Right-click context help, mixed into every screen.

MOO2 answers a right button by walking the active screen's help list
(`fields::Check_Help_List_`, fields.cpp:2916); a hit draws the entry
(`TEXTBOX::Draw_Help_Entry_`, textbox.cpp:307) and the click is
swallowed instead of acting as Cancel. This module is that behaviour
for the HD screens: region lookup, the modal input guards, and the
render call.

It is a mixin rather than more of `ScreenBase` for the reason
decision 6 exists — the base class was at 572 lines with this in it,
nearly double the guideline, and none of it is about being a screen.
`ScreenBase` inherits it, so every screen has the behaviour and a
screen without a `help.json` simply has no regions and answers a
right click with nothing, exactly as the original does outside a
help box.

Where the pieces live:
  regions   screens/<name>/help.json — NEVER in boxes.json, because
            `Box.to_dict` serializes a fixed key set and a help_id
            stored on a box would be dropped the first time the F5
            editor saved that screen
  geometry  the `help_popup` box, so the panel is F5-movable
  text      assets/shared/help/help_<lang>.json, generated from the
            user's own HELP.LBX by tools/help_extract.py
  wording   assets/shared/help/labels.json (CLOSE, the "not
            extracted yet" message)
"""
import os

import pygame

from core.helppopup import (Backdrop as HelpBackdrop, HelpPopup,
                            FALLBACK_BOX as HELP_FALLBACK_BOX)
from core.helptext import HelpText


class HelpMixin:
    """Right-click help for a screen. Mixed into ScreenBase."""

    #: Region table for this screen. Absent file = no help.
    HELP_FILE = "help.json"
    #: Box that bounds the popup. Missing box = the constant in
    #: helppopup.FALLBACK_BOX, so a bad edit cannot make help
    #: unreachable.
    HELP_BOX = "help_popup"

    def _init_help(self):
        """Called from ScreenBase.__init__."""
        self.help = HelpPopup()
        self._help_regions = []

    @property
    def helptext(self):
        """The shared HelpText, created once per App.

        Built lazily rather than in App.__init__ so there is exactly
        one construction site: any harness holding an app-like object
        (the smoke test's FakeApp, a mod's) gets the same instance
        without a second copy of the same two lines.
        """
        existing = getattr(self.app, "helptext", None)
        if existing is None:
            settings = getattr(self.app, "settings", {}) or {}
            existing = HelpText(self.app.res,
                                settings.get("language", "en"))
            self.app.helptext = existing
        return existing

    def _load_help_regions(self):
        """Read help.json for this screen. Absent file = no help."""
        data = self.app.res.load_json(
            os.path.join("screens", self.SCREEN_NAME,
                         self.HELP_FILE).replace(os.sep, "/"))
        regions = data.get("regions", []) if isinstance(data, dict) else []
        self._help_regions = [r for r in regions
                              if isinstance(r, dict) and "help_id" in r]

    def help_region_rect(self, spec):
        """Screen rect for one help.json region, or None.

        Handles the region kinds every screen can have. A screen with
        its own geometry (New Game's cover-scaled slots, the galaxy
        map's frame cutouts) adds kinds in `help_extra_rect`.
        """
        name = spec.get("box")
        if name:
            # A list unions its boxes. The original's help rectangles
            # are drawn around whole controls; HD often splits one
            # control into an icon box and a text box so both stay
            # F5-movable, and the help region has to cover both.
            wanted = [name] if isinstance(name, str) else list(name)
            rects = [b.screen_rect for b in self.boxes
                     if b.name in wanted and b.screen_rect]
            if not rects:
                return None
            return rects[0].unionall(rects[1:])

        side = spec.get("frame_button")
        if side in ("left", "right"):
            frame = self._get_active_frame()
            if not frame or not frame.available:
                return None
            r = (frame.button_rect_left(self.app.win_w, self.app.win_h)
                 if side == "left"
                 else frame.button_rect_right(self.app.win_w,
                                              self.app.win_h))
            return pygame.Rect(*r) if r else None

        if spec.get("screen"):
            return pygame.Rect(0, 0, self.app.win_w, self.app.win_h)

        return self.help_extra_rect(spec)

    def help_extra_rect(self, spec):
        """Screen-specific region kinds. Base knows none."""
        return None

    def open_help_at(self, screen_x, screen_y):
        """Open the help entry covering a point. True if one did.

        First hit wins and the walk stops, like `Check_Help_List_`,
        which is why a screen-wide fallback region must be last in
        help.json — exactly where the original keeps it
        (`{545, 0, 0, 639, 479}` closes New Game's list,
        erichelp.cpp:38).
        """
        for spec in self._help_regions:
            rect = self.help_region_rect(spec)
            if rect and rect.collidepoint(screen_x, screen_y):
                entry = self.helptext.entry(spec["help_id"])
                if entry is None:
                    entry = self.helptext.missing_entry(spec["help_id"])
                self.help.open(spec["help_id"], *entry)
                return True
        return False

    def handle_right_button(self, down, screen_x, screen_y):
        """Right button: open help, or close an open popup.

        Duck-typed hook routed from the main loop. Screens that use
        the right button for something of their own (the galaxy map
        pans with it) override this and call back into it first.
        """
        if not down:
            return False
        if self.help.visible:
            self.help.close()
            return True
        return self.open_help_at(screen_x, screen_y)

    def help_consumes_click(self, screen_x, screen_y):
        """True if an open popup swallowed a left click (and closed)."""
        if not self.help.visible:
            return False
        self.help.close()
        return True

    def help_consumes_key(self, key):
        """True if an open popup swallowed a key (and closed).

        Every key closes it, ESC included — so ESC dismisses the
        message rather than leaving the screen underneath.
        """
        if not self.help.visible:
            return False
        self.help.close()
        return True

    def help_consumes_wheel(self, direction):
        """True if an open popup took the wheel (scrolling a long entry)."""
        if not self.help.visible:
            return False
        return self.help.handle_wheel(direction)

    def _help_font_scale(self):
        """The box's stored `font_scale`, WITHOUT the auto-factor.

        `ScreenBase.box_font_scale` multiplies the stored value by
        `win_h / 1080`, and `Layout.font_size` then multiplies by the
        window scale as well. For a box whose value was hand-tuned
        per resolution — the sidebar readouts, the Custom Race panels
        — the two together are what makes the tuning land. For this
        one they are a double scale: the help popup has to be right
        at 4K and ultrawide, which nobody tuned and which resolve by
        pixel area to somebody else's stored list. At 3840x2160 the
        auto-factor made the text twice the size it should be
        relative to the panel, which is visible the moment two
        resolutions are rendered side by side and invisible in
        either one alone.
        """
        for box in self.boxes:
            if box.name == self.HELP_BOX:
                return box.style.get("font_scale", 1.0)
        return 1.0

    def help_backdrop(self):
        """Surface the popup cuts its fill out of, window-aligned.

        The shared cockpit texture rather than the screen's own
        background — see `helppopup.Backdrop` for why the Custom Race
        trick cannot be reused verbatim here. Built once per App and
        shared by every screen, like `helptext`.
        """
        holder = getattr(self.app, "help_backdrop_cache", None)
        if holder is None:
            holder = HelpBackdrop()
            self.app.help_backdrop_cache = holder
        return holder.surface(self.app.res, self.app.win_w,
                              self.app.win_h)

    def render_help(self, surface):
        """Draw the popup, if open. Call LAST in a screen's render.

        While the F5 editor is open the popup is drawn even when
        closed, with the first region's real text — the same reason
        the Custom Race message box previews itself: an empty panel
        gives no clue whether a font scale fits, and this one sizes
        itself from its content.
        """
        was_open = self.help.visible
        if not was_open:
            editor = getattr(self.app, "editor", None)
            if not (editor is not None
                    and getattr(editor, "active", False)
                    and self._help_regions):
                return
            first = self._help_regions[0]["help_id"]
            entry = (self.helptext.entry(first)
                     or self.helptext.missing_entry(first))
            self.help.open(first, *entry)

        box = self.box_rect(self.HELP_BOX) or HELP_FALLBACK_BOX
        self.help.render(surface, self.layout, self.style, box,
                         self._help_font_scale(),
                         backdrop=self.help_backdrop(),
                         close_label=self.helptext.label("close"),
                         scroll_label=self.helptext.label("scroll_hint"))
        if not was_open:
            self.help.close()
