"""The two popups the research panel shares — one home, both modes.

`_Tech_List_` (the category list) and `Draw_Application_Description_`
(the description box) are tech.cpp:786-1029, and both are DISPLAY-ONLY
in the original: nothing in either changes the research
(`doc/tech_change_reading.md` §2, the input table). So HD draws them
itself and sends nothing to the game for either — the game stays in
`_Tech_Select_`'s own loop with the panel's field list, which is also
what keeps `researchlist.validate_against_fields` passing while a popup
is up.

A MIXIN rather than more of `core/researchscreen.py`, for the reason
decision 6 exists: that file passed the 300-line guideline the moment
the list popup's input landed in it, and none of what is here is about
being the panel. `ResearchPanelScreen` mixes it in, so both modes get
both popups from one implementation — which is what work order 165
part C asks for, and what the redundancy audit asks for generally.

The list popup's geometry and drawing are `core/researchtechlist.py`;
the description box borrows the shared help panel, which already draws
a help record's title and body (`core/helppopup.py`).
"""
from core import billtext, research, researchlist, researchtechlist


class ResearchPopupsMixin:
    """The category list and the description box, for both modes.

    Reads the panel's own state — `_techlist`, `_entries`, `_state`,
    `_tech`, `_current`, `geom`, `native_point` — and owns none of it.
    """

    def open_description_at(self, screen_x, screen_y):
        """The description box for the row under a point. True if one opened.

        `app_id != 0` is the original's own guard (tech.cpp:337): the
        placeholder row IS a row and can be committed, and it has no
        application to describe.
        """
        hit = self.row_at(screen_x, screen_y)
        if hit is None:
            return False
        entry = self._entries[hit[0]]
        app = entry.apps[hit[1]]
        if not app:
            return False
        text = self.description(entry, app)
        if text is None:
            return False
        self.help.open(app, *text)
        return True

    # ── The category list popup (`_Tech_List_`) ───────────

    def radio_field(self, index):
        """Entry `index`'s category button in the live list, or None.

        The ORIGIN is the source's — `_tech_button_pos + _g_scrn_x`,
        tech.cpp:38-43 — and the size comes from the art
        (`Add_Radio_Button_Field_` -> fields.cpp:409), so the match is
        on the origin and on being a type-1 field. That is the shape
        `exit_field` uses, for the same reason, and it means the button
        is found in the list read NOW and never by a remembered index
        (decision 20).
        """
        if not self.app.connected:
            return None
        x, y = researchlist.RADIO_POS[index]
        want = (x + self.geom.origin, y)
        for f in (getattr(self.app.client.state, "fields", None) or []):
            if (getattr(f, "field_type", None) == researchlist.TYPE_RADIO
                    and (f.x, f.y) == want):
                return f
        return None

    def open_list_at(self, screen_x, screen_y):
        """A click on a category button opens that category's list.

        **Q11, THE RADIO INDEX SKEW, IS NOT REPRODUCED — DEVIATION.**
        The original indexes `entries[input - first_btn_field]`
        (tech.cpp:378-379) while radios exist only for NON-EMPTY
        entries (:236, :497-513), so with an empty category ahead of it
        a button opens the WRONG category's list and may draw a
        `button_image` that entry never got. HD opens the category the
        button belongs to: the original is reading data that was never
        set, and transcribing that would make the list wrong in exactly
        the case a player can see it.

        **NOTHING IS SENT.** The popup is display-only in the original
        — a row click returns an id no branch compares, and nothing in
        it changes the research (`doc/tech_change_reading.md` §2) — so
        HD opens its own and the game stays in the panel's loop.
        """
        if self._state != self.READY_STATE:
            return False
        point = self.native_point(screen_x, screen_y)
        if point is None:
            return False
        nx, ny = point
        for entry in self._entries:
            if not entry.offered:
                continue
            field = self.radio_field(entry.index)
            if field is None:
                continue
            if not (field.x <= nx <= field.x_end
                    and field.y <= ny <= field.y_end):
                continue
            self._techlist.open(entry, self.group_items(entry))
            return True
        return False

    def group_items(self, entry):
        """`Get_Group_List_` for one category, off the arrays on the wire.

        `current_research_field` is the REAL one here, not the zero the
        entries were built with: change mode restores it immediately
        after `Init_Entry_Data_` (tech.cpp:208-210), so the list sees
        it and marks that field with status 4.
        """
        tech_fields, tech_applications = self._tech
        return researchtechlist.group_list(
            tech_fields, tech_applications, self._current[0], entry.group)

    def list_click(self, screen_x, screen_y):
        """A left click while the list is up (tech.cpp:979-1029).

        The page buttons page; a row returns an id NOTHING branches on,
        so it does nothing and the list stays; everything else is the
        whole-screen field and closes.
        """
        point = self.native_point(screen_x, screen_y)
        hit = (self._techlist.at(self.geom.origin, *point)
               if point else None)
        if hit and hit[0] in ("up", "down"):
            self._techlist.page_by(-1 if hit[0] == "up" else 1)
            return
        if hit and hit[0] == "row":
            return
        self._techlist.close()

    def list_describe(self, screen_x, screen_y):
        """A right click while the list is up. True if it was consumed.

        A row opens that application's description (tech.cpp:1003-1011,
        and `app_id != 0` guards it there too); anything else only
        redraws, which for HD means "nothing happens and the list stays
        open" — so the click is still consumed.
        """
        point = self.native_point(screen_x, screen_y)
        hit = (self._techlist.at(self.geom.origin, *point)
               if point else None)
        if not (hit and hit[0] == "row"):
            return True
        item = self._techlist.items()[hit[1]]
        app = item.apps[hit[2]]
        if not app:
            return True
        text = self.description_for(item.field, app)
        if text is not None:
            self.help.open(app, *text)
        return True

    def description(self, entry, app):
        """(title, body) for one application, as the original builds it.

        `Draw_Application_Description_` (tech.cpp:786-845) loads ONE
        help record — `Far_Reload_Data_(help_lbx, 0, buf, app_idx, 1,
        ...)`, no chain walk — and appends a line of its own:
        billtext 61, the cost, and the language's unit.

        **THE COST IS THE FULL ONE, in both modes.** The entry shows
        what is left in change mode (`research_accumulated` subtracted,
        tech.cpp:203); this shows `New_Get_Tech_Cost_(app, 1, player)`
        (:802), which subtracts nothing. The original's design and not
        a bug — `doc/tech_change_reading.md` §3 — so it is transcribed
        and `cost_offset()` is deliberately not used here.

        **AND THE FIELD IS THE ENTRY'S.** `New_Get_Tech_Cost_` looks the
        application's field up in `_technology_applications[app]
        .tech_field_id`; the entry's rows came out of
        `_technology_fields[entry.field].tech[]` in the first place
        (tech.cpp:537-586), so the two are the same field and a second
        app->field table here would be a copy that can disagree.

        **Q9 IS SETTLED** (work order 165 part C): no help record in
        0..211 chains — every one of the 212 in `help_en.json` reports
        `pages == 1` — so the extractor's chain walk has nothing to
        join in this range and the file already holds exactly the one
        record tech.cpp reads. No second extraction is needed.
        """
        return self.description_for(entry.field, app)

    def description_for(self, field, app):
        """The same box, for a field the caller names.

        The panel hands its entry's field; the list popup hands the row's
        own. One assembly, because the original has one
        `Draw_Application_Description_` and both call sites reach it.
        """
        record = self.helptext.entry(app)
        if record is None:
            record = self.helptext.missing_entry(app)
        if record is None:
            return None
        title, body = record
        # The original writes body, `\r`, then the cost line
        # (tech.cpp:833-839). `\r` is FMTPARA's line break and
        # `core/helpformat.py` honours it. The `\aY+3.` and the
        # justify/centre codes around it are layout that renderer drops
        # — it acts on X and T only, and says so — so they are not
        # written here rather than written and dropped.
        cost = research.cost(field)
        label = (self._wording.message(billtext.MSG_RESEARCH_COST)
                 if self._wording else "") or ""
        line = f"{label}{cost}{self._cost_suffix}"
        return (title, f"{body}\r{line}" if body else line)
