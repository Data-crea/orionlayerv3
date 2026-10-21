"""The diplomacy system picker's TPOP tail — open fix 109 (work order 322 E).

The wire half of the picker HD draws over the audience
(`screens/audience/aupicker.py`): kind 25 of open fix 49's "TPOP" block,
reported as id 85 while `DIP_SCRN::Diplomacy_System_Display` runs
(dip_scrn.cpp:701-805, "choose a system to offer / demand"; opened from
the audience's Offer Gift > System, dip_scrn_main.cpp:390, Demand >
Surrender System, dip_scrn.cpp:1555, the better offer asked of any human
target, :1195, and a network game's chat Demand and Offer Gift,
`Get_Net_Diplomacy_Choices`, :1966, :1971). The engine's lines here are the branch `orionlayer`'s just before
open fix 109 (`90656654^` = `d1efc870`). The layout is
`doc/ext_system_picker.patch`'s header, byte by byte:

    args  [0] the giver (whose systems are offered), [1] the receiver,
          [2] display_mode (0 offer, 1 demand), [3] the CANCEL field
          (`Add_Hidden_Field_(15, 139, 157, 162)`, :740), [4]
          current_ambassador (the room's race), [5] ambassador_option
    title "Choose A System:" (JIMTEXT2 0x02, choose_a_system_buffer)
    text  the statement the room prints (diplomacy_message: JIMTEXT2
          0x37 / 0x3F, decoded at :728-729)
    tail  five strings (int16 length + raw bytes): CANCEL's words, the
          star line's and the population line's templates (JIMTEXT2
          0x3A "\\x81 Star System", 0x38 "\\x82 Million Colonists",
          undecoded), " (HOMEWORLD)", "(Unsurrenderable)"; int16 n, n x
          int16 star i's hidden field (diplomacy_system_fields[i + 1],
          :734-738); int16 m, m x {int16 star, int16 may_surrender,
          int16 capitol planet (-1 none), int16 population, int16 k,
          k x (int16 planet, string "size, climate")} — the stars
          `Diplomacy_System_Scan_` answers with the giver
          (dip_scrn_main.cpp:829-859)
"""
import struct as _st

from core import lang

OFFER, DEMAND = 0, 1
#: The most stars a v2 galaxy can have (`core.dragonwire.MAX_STARS`'s
#: reason): one field per star.
MAX_STARS = 1024
#: A star's field: `Add_Hidden_Field_(x, y, x + 5, y + 5)` (type 7,
#: FIELD_TYPE_HIDDEN) at `Get_Galaxy_Map_Star_XY_(i, 10, 0xAB, 0xB4, 0x6E,
#: 0, 0, 1)` (:734-738) — the box at (10, 171), 180 x 110, the star's place
#: less 3 (movebox.cpp:343-375, marker mode 1).
MAP = (10, 171, 180, 110)
STAR_FIELD_TYPE, STAR_FIELD_SIZE, STAR_CENTRE_OFFSET = 7, 5, 3
#: CANCEL's hidden field (:740).
CANCEL_RECT = (0x0F, 0x8B, 0x9D, 0xA2)
#: Decode_Text_Message's two codes the templates carry (jim.cpp:277-283):
#: 0x81 the star's name, 0x82 the number ("%i").
CODE_STAR, CODE_NUMBER = 0x81, 0x82
#: The whole range `Decode_Text_Message_` treats as codes (jim.cpp:270).
CODE_FIRST, CODE_LAST = 0x80, 0x8A
#: `Draw_Diplomacy_System_Text_`'s `text_buffer[80]` (:2330): the star line
#: and "(Unsurrenderable)" are joined in it by strlcat, so at most 79 bytes.
LINE_MAX = 79


def _raw(take):
    (n,) = take("h")
    if n < 0:
        raise ValueError("length")
    (raw,) = take(f"{n}s")
    return raw


def read_tail(take):
    """The tail as a dict (raw templates kept as bytes; see `decode`)."""
    cancel, star_t, pop_t, home, unsurr = (_raw(take) for _ in range(5))
    (n,) = take("h")
    if not 0 <= n <= MAX_STARS:
        raise ValueError("star count")
    fields = [take("h")[0] for _ in range(n)]
    (m,) = take("h")
    if not 0 <= m <= MAX_STARS:
        raise ValueError("system count")
    systems = []
    for _ in range(m):
        star, may, capitol, pop, k = take("hhhhh")
        if not 0 <= k <= 5:
            raise ValueError("planet count")
        planets = []
        for _ in range(k):
            (planet,) = take("h")
            planets.append({"planet": planet,
                            "line": lang.wire_text(_raw(take))})
        systems.append({"star": star, "may_surrender": bool(may),
                        "capitol": capitol, "population": pop,
                        "planets": planets})
    return {"cancel": lang.wire_text(cancel), "star_template": star_t,
            "population_template": pop_t, "homeworld": lang.wire_text(home),
            "unsurrenderable": lang.wire_text(unsurr), "fields": fields,
            "systems": systems}


def _pack_raw(raw):
    if isinstance(raw, str):
        raw = raw.encode("latin-1")
    return _st.pack("<h", len(raw)) + raw


def build_tail(picker=None):
    """The tail as the engine writes it — for the checks' stand-ins."""
    p = picker or {}
    out = b"".join(_pack_raw(p.get(k, b"")) for k in (
        "cancel", "star_template", "population_template", "homeworld",
        "unsurrenderable"))
    fields = p.get("fields") or []
    out += _st.pack("<h", len(fields))
    out += b"".join(_st.pack("<h", f) for f in fields)
    systems = p.get("systems") or []
    out += _st.pack("<h", len(systems))
    for s in systems:
        planets = s.get("planets") or []
        out += _st.pack("<hhhhh", s["star"], int(s["may_surrender"]),
                        s["capitol"], s["population"], len(planets))
        for pl in planets:
            out += _st.pack("<h", pl["planet"]) + _pack_raw(pl["line"])
    return out


def decode(template, star_name="", number=-1):
    """A template with its codes substituted as `JIM::Decode_Text_Message_`
    does (jim.cpp:258-327) for the two the picker's templates carry: 0x81
    the star's name, 0x82 `"%i"` of the number. TRANSCRIPTION, narrower
    than the original: the other codes of 0x80-0x8A (player and race
    names, techs, the stardate, a planet's name) are dropped, where the
    original would substitute them — its picker passes -1 for every one of
    them, so a template carrying one would read past an array there.
    The number defaults to -1, what `Decode_Text_System_` passes: a star
    template with 0x82 prints "-1", as the engine does. Where HD differs:
    0x81 in the population template (the engine reads `star[-1]`) is
    empty, and the original's length caps — 0x23 for the star line, 0x1E
    for the population line, beyond which `Decode_Text_Message_` ends the
    game (jim.cpp:328-331) — are not applied."""
    out = bytearray()
    for b in template:
        if b == CODE_STAR:
            out += (star_name or "").encode("latin-1", "replace")
        elif b == CODE_NUMBER:
            out += str(int(number)).encode("ascii")
        elif CODE_FIRST <= b <= CODE_LAST:
            continue
        else:
            out.append(b)
    return lang.wire_text(bytes(out))


def selectable(system):
    """The original's click rule (dip_scrn.cpp:775-790): the giver's
    system, `May_Surrender_Star_` allows it, and it holds no capitol."""
    return bool(system["may_surrender"]) and system["capitol"] == -1


def system_of(popup, star):
    """The giver's system at `star` (the tail's record), or None — the
    hover shows nothing over any other star (`Diplomacy_System_Scan_`
    answers someone else, :746-769)."""
    tail = popup.get("picker") or {}
    return next((s for s in tail.get("systems") or ()
                 if s["star"] == star), None)


def lines(popup, system, star_name):
    """[(text, special)] as `Draw_Diplomacy_System_Text_` prints them
    (dip_scrn.cpp:2329-2374): the star line, "(Unsurrenderable)" appended
    without a space where `May_Surrender_Star_` refuses; the population;
    each planet's "size, climate", " (HOMEWORLD)" on the capitol. A line
    is `special` where the original switches to its special colours: all
    of them when the system holds a capitol or cannot be surrendered."""
    t = popup["picker"]
    special = system["capitol"] != -1 or not system["may_surrender"]
    first = decode(t["star_template"], star_name)
    if not system["may_surrender"]:
        first += t["unsurrenderable"]
    first = first[:LINE_MAX]
    out = [(first, special),
           (decode(t["population_template"], number=system["population"]),
            special)]
    for p in system["planets"]:
        words = p["line"]
        if p["planet"] == system["capitol"]:
            words += t["homeworld"]
        out.append((words, special))
    return out


def _is_star_field(f):
    x, y, w, h = MAP
    lo = -STAR_CENTRE_OFFSET
    return (getattr(f, "field_type", None) == STAR_FIELD_TYPE and
            f.x_end - f.x == STAR_FIELD_SIZE and
            f.y_end - f.y == STAR_FIELD_SIZE and
            x + lo <= f.x <= x + w and y + lo <= f.y <= y + h)


def star_field(popup, state, star):
    """The live field of `star`, or None (P816: the tail names it, the
    list just read must have it by its index, its type and its
    rectangle)."""
    fields = (popup.get("picker") or {}).get("fields") or []
    if not 0 <= star < len(fields) or fields[star] <= 0:
        return None
    fid = fields[star]
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == fid and _is_star_field(f)),
                None)


def cancel_field(popup, state):
    """CANCEL's live field (args[3]), by index, type and rectangle."""
    fid = popup["args"][3]
    if fid is None or fid <= 0:
        return None
    return next((f for f in (getattr(state, "fields", None) or [])
                 if getattr(f, "index", None) == fid and
                 getattr(f, "field_type", None) == STAR_FIELD_TYPE and
                 (f.x, f.y, f.x_end, f.y_end) == CANCEL_RECT), None)
