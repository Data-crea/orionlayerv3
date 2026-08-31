"""MOO2's paragraph formatting codes, decoded for the HD help popup.

The strings in HELP.LBX are not plain text. They carry the control
codes `FMTPARA` interprets while laying a paragraph out, and the
Command Points entry is the clearest case: its table is not made of
spaces, it is made of absolute column positions. Raw, that entry
reads

    \\aX3.Frigate\\aX97.-1 \\aX150.Star Base\\aX270.+1

and printing it verbatim produces exactly what a first attempt
produced — the codes on screen and the columns gone.

Transcribed from `src/game/fmtpara.cpp`:

  \\a (BEL)  starts a function sequence (`Process_Command_`:308 ->
            `Process_Function_`:384). One or more letters from
            `_legal_functions` = "FRTXYSHVPIMOC^=", each followed by
            a numeric argument, further arguments separated by ",",
            the whole sequence terminated by "." or the next "\\a".
            Argument characters are `_legal_fn_arg_chars` =
            "1234567890+- "; a leading + or - means "relative to the
            current position" rather than to the paragraph edge.
  \\t        tab -> `Paragraph_HT_`:239, moves to the next stop set
            by the T function
  \\r        line break        \\v  vertical move (same advance)
  \\n \\f     paragraph break (blank line between)
  \\b        soft break candidate — drop, it is a hyphenation hint

Of the fifteen functions, only X and T carry layout this renderer can
honour, and only those two are acted on:

  X  `FN_Set_X_Pos_`:  new_x = val + paragraph left edge — a column
                       position in the paragraph's own pixel space
  T  `FN_Set_Tabs_`:   appends a tab stop, same arithmetic

The rest (font changes, margins, indents, superscript, the variable
and item machinery at 0x17..0x1F) are dropped. `dropped_functions()`
reports which ones a body actually used, so "we ignore the others"
stays a checkable claim rather than an assumption — nothing in the
help text used anything but X, T and the line breaks when this was
written.

Column positions come out in the ORIGINAL's paragraph pixel space,
whose width is `HELP_PARA_W`; the caller scales them to whatever
width the HD panel has. That is what makes the table line up at every
resolution instead of at one.
"""
import re

#: fmtpara.cpp:4 — the letters that may follow \a
LEGAL_FUNCTIONS = "FRTXYSHVPIMOC^="
#: fmtpara.cpp:5 — what may appear inside an argument
LEGAL_ARG_CHARS = "1234567890+- "

#: textbox.cpp:345 — Draw_Help_Entry_ lays help text out at 0x153 px.
#: Every X position in a help body is relative to this width.
HELP_PARA_W = 0x153      # 339

#: Functions this parser acts on. Everything else is layout the HD
#: popup does not reproduce.
HANDLED = "XT"

_NUMBER = re.compile(r"[+-]?\d*")


class Run:
    """A piece of text on one line, optionally at a fixed column.

    `x` is None for text that simply flows after whatever came
    before, and a native column (0..HELP_PARA_W) when the source put
    it there with an X function or a tab.
    """

    __slots__ = ("text", "x")

    def __init__(self, text, x=None):
        self.text = text
        self.x = x

    def __repr__(self):
        return f"Run({self.text!r}, x={self.x})"

    def __eq__(self, other):
        return (isinstance(other, Run) and other.text == self.text
                and other.x == self.x)


class Line:
    """One laid-out line: its runs, and whether a blank follows."""

    __slots__ = ("runs", "paragraph_break")

    def __init__(self, runs=None, paragraph_break=False):
        self.runs = runs or []
        self.paragraph_break = paragraph_break

    @property
    def columns(self):
        """True if any run sits at a fixed column."""
        return any(r.x is not None for r in self.runs)

    def plain(self):
        """The line as flat text, for measuring or for a fallback."""
        return " ".join(r.text for r in self.runs if r.text)


def parse(body):
    """Raw HELP.LBX body -> [Line]. Never raises on odd input.

    A body with no control codes at all comes back as one Line per
    source line, which is what an already-cleaned string does, so the
    caller does not need to know which kind it has.
    """
    lines = []
    runs = []
    pending_x = None
    tabs = []
    text = []
    i = 0
    n = len(body)

    def flush_text():
        nonlocal pending_x, text
        if text:
            runs.append(Run("".join(text), pending_x))
            text = []
            pending_x = None

    def end_line(paragraph=False):
        nonlocal runs
        flush_text()
        lines.append(Line(runs, paragraph))
        runs = []

    while i < n:
        ch = body[i]

        if ch == "\a":
            flush_text()
            i, x, new_tabs = _read_functions(body, i + 1)
            if x is not None:
                pending_x = x
            tabs.extend(new_tabs)
            continue

        if ch in "\r\n\v\f":
            paragraph = ch in "\n\f"
            end_line(paragraph)
            # \r\n is one break, not two.
            if ch == "\r" and i + 1 < n and body[i + 1] == "\n":
                i += 1
            i += 1
            continue

        if ch == "\t":
            flush_text()
            # Paragraph_HT_ moves to the first stop past the current
            # position. Without stops the tab has no effect at all,
            # which is what the original does too.
            width = sum(len(r.text) for r in runs)
            pending_x = _next_tab(tabs, width)
            i += 1
            continue

        if ch == "\b":
            i += 1                      # hyphenation hint, no output
            continue

        if ch < " " or ch == "\x7f":
            i += 1                      # variable/item machinery
            continue

        text.append(ch)
        i += 1

    if text or runs:
        end_line()
    return lines


def dropped_functions(body):
    """Which function letters a body uses that parse() ignores."""
    used = set()
    i = 0
    while i < len(body):
        if body[i] == "\a":
            i, _, _ = _read_functions(body, i + 1, seen=used)
        else:
            i += 1
    return "".join(sorted(used - set(HANDLED)))


def to_json(lines):
    """[Line] -> plain data, for a cached or exported form."""
    return [{"runs": [{"t": r.text, "x": r.x} for r in ln.runs],
             "br": ln.paragraph_break} for ln in lines]


def from_json(data):
    """Inverse of `to_json`."""
    return [Line([Run(r["t"], r.get("x")) for r in ln.get("runs", [])],
                 ln.get("br", False)) for ln in data]


# ── Internals ────────────────────────────────────────────

def _read_functions(body, i, seen=None):
    """Consume one \\a sequence. Returns (next_index, x, tab_stops).

    Mirrors `Process_Function_` (fmtpara.cpp:384): letters with
    comma-separated arguments, then everything up to the "." or the
    next "\\a" is skipped, and the terminator itself is consumed.
    """
    n = len(body)
    x = None
    tabs = []

    while i < n and body[i].upper() in LEGAL_FUNCTIONS:
        cmd = body[i].upper()
        if seen is not None:
            seen.add(cmd)
        if cmd == "T":
            tabs.clear()          # T resets the stop list (_tabs[0] = 0)
        while True:
            i += 1
            i, val, relative = _read_argument(body, i)
            if cmd == "X" and val is not None and not relative:
                x = val
            elif cmd == "T" and val is not None and not relative:
                tabs.append(val)
            if i < n and body[i] == ",":
                continue
            break

    # Skip to the terminator and swallow it.
    while i < n and body[i] not in ".\a":
        i += 1
    if i < n and body[i] == ".":
        i += 1
    return i, x, tabs


def _read_argument(body, i):
    """Returns (next_index, value|None, relative)."""
    while i < len(body) and body[i] == " ":
        i += 1
    relative = i < len(body) and body[i] in "+-"
    match = _NUMBER.match(body, i)
    raw = match.group(0) if match else ""
    try:
        value = int(raw)
    except ValueError:
        value = None
    i = match.end() if match else i
    while i < len(body) and body[i] in LEGAL_ARG_CHARS:
        i += 1
    return i, value, relative


def _next_tab(tabs, current_chars):
    """First tab stop past the current position, or None.

    The original compares against a pixel x. This parser has no font,
    so it compares against the characters written so far — good
    enough to pick the right stop, since the stops in help text are
    far apart, and honest about being an approximation.
    """
    for stop in sorted(tabs):
        if stop > current_chars:
            return stop
    return None
