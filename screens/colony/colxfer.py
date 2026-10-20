"""Colonists to any colony of the player — `Send_Cluster_`'s walk, mirrored
(work order 316; open fix 103, the long form of `MSG_SETTLE_POPS`).

THE ORIGINAL: colonists in hand dropped on another colony — a planet of the
colony screen's system display (colony.cpp:1798), a row of the transport
popup (`COLXPORT::Xport_Popup_`, colony_main.cpp:1069-1072), a colony's
name or job column on the Colonies list (colsum.cpp:869, :909) — go to
`COLMOVE::Send_Cluster_(colony, job)` (colmove.cpp:145-531). For each pop
in hand, the first unassigned one each time (:175, :475), it asks
`SETTLER::Pop_Tries_To_Settle_` (settler.cpp:230-311):

    another player's colony        dest_owner_mismatch   E 0x211
    the source star blockaded      source_blockaded      E 0x207
    a space anomaly at the source  source_space_anomaly  (no line: E 0xE4)
    the plague at the source       source_plague         (no line: E 0xE4)
    an outpost                     dest_is_outpost       E 0x1FD
    the source's last pop          only_one_pop_left     E 0x241
    a conquered colonist           selected_pop_flag_0x400  E 0x20E
    another star: fewer freighters than settlers_freighted * 5 + 5
                                   insufficient_freighters  E 0x184
                  25 settlers already in transit
                                   max_settlers_in_transit  E 0x24D
    then, for a pop that may go: no room for one more of its race, the
    settlers already heading there counted (`Room_For_Another_`, :65-123),
    the destination blockaded (a warning only), the ETA (`Settler_ETA_`,
    :211-228: parsecs over the ship speed, at least 2, at most 15 turns).

A pop that may go but needs an ETA or finds no room makes it ASK, once per
kind (`warning_state`, colmove.cpp:204-266): E 0x209 "unavailable for N
turns, are you sure?"; at the limit E 0x205 (0x203 after sending some), or
with an ETA E 0x206 (0x204). YES settles it (beyond the limit the settlers
die on arrival — the strings say so); NO, or a refusal, ends the walk with
"Settlers Failed." (E 0x1D6) naming why (:330-470), the rest still in hand.
With a job (a drop on a job column of the Colonies list) each pop first
takes it as `Give_Colonist_New_Job_` gives it for a transfer (:279-289,
:535-575) — a native refused research and industry, an android any other
job, a job holding 42 — whose refusal box ends it at once (`return`, no
notice). After the walk, if any went: "Settlers Depart" (E 0x1D5 / 0x1D1,
:482-522).

HD (TRANSCRIPTION `transfer_walk`): `walk` is that loop over the records on
the wire — what HD can read of every rule; what it cannot (an anomaly, the
plague of a colony not on screen, room for a race other than the owner's)
the engine still decides and reports in STLR (`core.settlewire`), so `walk`
is a FILTER and a forecast, never a guarantee (P627). Its forecast is what
the questions are asked from, BEFORE the command, because a command cannot
ask (fundament 52): `next_question` names the first question the answers so
far do not carry, the player answers it in HD's box, and the command goes
out with the answers (`colxferflow`).
"""
from core import settlewire
from core.structs import colony as colony_struct
from core.structs import planet as planet_struct
from core.structs import player as player_struct

#: The game's own sentences (ESTRINGS), `Send_Cluster_`'s (colmove.cpp).
E_ETA_SURE = 0x209
E_LIMIT, E_LIMIT_AFTER = 0x205, 0x203
E_LIMIT_ETA, E_LIMIT_ETA_AFTER = 0x206, 0x204
E_DECLINED_ETA, E_DECLINED_LIMIT_ETA, E_DECLINED_LIMIT = 0xFE, 0xFC, 0xFD
E_FAILED_TITLE, E_DEPART_TITLE = 0x1D6, 0x1D5
E_DEPART, E_ENROUTE, E_UNSPECIFIED = 0x1D1, 0x80, 0xE4
E_DEST_BLOCKADED, E_NO_FARMING_NOTE, E_SHUFFLED = 0x84, 0x85, 0x83
E_NOT_A_COLONY = 0x210
#: `Give_Colonist_New_Job_`'s refusals (colmove.cpp:544, :551, :558; ESTR
#: 522, 524, 391 in orion2_str.h).
E_JOB_NATIVE, E_JOB_ANDROID, E_JOB_FULL = 522, 524, 391
#: The reasons' lines in the box's own order (colmove.cpp:319-358,
#: :407-445).
REASON_LINES = (
    ("dest_is_outpost", 0x1FD), ("only_one_pop_left", 0x241),
    ("max_settlers_in_transit", 0x24D), ("source_blockaded", 0x207),
    ("insufficient_freighters", 0x184), ("dest_owner_mismatch", 0x211),
    ("field10_0xa", 0x20F), ("selected_pop_flag_0x400", 0x20E))
#: The settlers a player may have in transit: `settlers[]`'s 25
#: (settler.cpp:236, :290; v2's `max_pop_freighted`).
MAX_IN_TRANSIT = 25
#: `Room_For_Another_`'s ceiling (settler.cpp:98).
MAX_POPS = 42
#: The pop strings `Colony_Pop_String_` builds the notice's noun from
#: (colmove.cpp:577-602; colony.cpp:878-961): E 0x4C over the conquered
#: word, the race, the state word and the job.
E_POP_FORMAT, E_CONQUERED, E_EXPERT = 0x4C, 598, 286
E_JOBS = (291, 557, 455)              # farmer, worker, scientist
E_ANDROID, E_NATIVE = 0xB3, 0x255


class Question:
    """One of the original's confirmations: which answer it is (a
    `settlewire.YES_*` bit), the sentence id and its numbers."""

    __slots__ = ("needs", "estring", "values")

    def __init__(self, needs, estring, values):
        self.needs, self.estring, self.values = needs, estring, tuple(values)

    def __repr__(self):
        return f"Question(E {self.estring:#x}, {self.values})"


class Walk:
    """The forecast of one `Send_Cluster_` to another colony."""

    __slots__ = ("settled", "stop", "result", "question", "job_refusal",
                 "extra", "sent", "rest", "colonies", "pops", "transit")

    def __init__(self):
        self.settled = 0
        self.stop = settlewire.STOP_NONE
        self.result = {}            # the last pop asked about
        self.question = None        # the question that stopped it, if any
        self.job_refusal = 0
        self.extra = False          # `extra_success_notice`
        self.sent = []              # the pick's pop indices that went
        self.rest = []              # still in hand: indices AFTER the walk
        self.colonies = {}          # {index: (n_pops, jobs)} afterwards
        self.pops = {}              # {index: (n_pops, words)} afterwards
        self.transit = 0            # settlers put on freighters


class World:
    """What the walk reads, from one snapshot."""

    def __init__(self, state):
        self.state = state
        self.raws = getattr(state, "colonies_raw", None) or []
        self.planets = getattr(state, "planets_raw", None) or []
        self.stars = getattr(state, "stars", None) or []
        self.players = getattr(state, "player_raw", None) or []

    def colony(self, index):
        if not 0 <= index < len(self.raws):
            return None
        return colony_struct.parse(self.raws[index])

    def star_of(self, colony):
        if not 0 <= colony.planet < len(self.planets):
            return None
        return planet_struct.parse(self.planets[colony.planet]).star_index

    def star(self, index):
        return self.stars[index] if index is not None and \
            0 <= index < len(self.stars) else None

    def player_raw(self, index):
        return self.players[index] if 0 <= index < len(self.players) \
            else None


def blockaded(star, player):
    return star is not None and \
        bool((int(star.blockaded) >> (int(player) & 0x1F)) & 1)


def parsecs(a, b):
    """`GEO::Parsecs_Between_Points_` (geo.cpp:88-102): the ceiling of the
    root of (dx² + dy²) / 900, in integers."""
    import math
    d2 = (a.x - b.x) ** 2 + (a.y - b.y) ** 2
    p = math.isqrt(d2 // 900)
    while p * p * 900 < d2:
        p += 1
    return p


def settler_eta(speed, a, b):
    """`SETTLER::Settler_ETA_` (settler.cpp:211-228)."""
    if a is None or b is None:
        return 0
    distance = parsecs(a, b)
    if distance == 0:
        return 0
    speed = max(2, int(speed or 0))
    return min(15, (distance + speed - 1) // speed)


def room_limit(state, dest, dest_index):
    """The destination's limit for its owner's race (the number the
    system display prints after the slash), or None — the colony
    screen's own reading (`colsettle._room`)."""
    from . import colsettle
    return colsettle._room(state, dest, dest_index)


def walk(state, source_index, held, dest_index, answers=0, job=-1,
         plague=None):
    """`Send_Cluster_(dest_index, job)` with the pops `held` of colony
    `source_index` in hand, the questions answered by `answers`
    (`settlewire.YES_*` bits): a `Walk`. `plague` is the source's plague
    where the screen knows it (the colony screen's CEVT), else None."""
    w = World(state)
    out = Walk()
    source, dest = w.colony(source_index), w.colony(dest_index)
    if source is None or dest is None:
        out.stop = settlewire.STOP_REFUSED
        out.result = {"can_settle": 0}
        return out
    s_star_i, d_star_i = w.star_of(source), w.star_of(dest)
    s_star, d_star = w.star(s_star_i), w.star(d_star_i)
    owner_raw = w.player_raw(source.owner)
    owner = player_struct.parse(owner_raw) if owner_raw else None
    in_transit = int(getattr(owner, "settlers_freighted", 0) or 0) \
        if owner is not None else 0
    freighters = int(getattr(owner, "n_freighters", 0) or 0) \
        if owner is not None else 0
    speed = getattr(owner, "ship_speed", 0) if owner is not None else 0
    heading = sum(1 for s in player_struct.settlers(owner_raw)
                  if s["dest_planet"] == dest.planet) if owner_raw else 0
    limit = room_limit(state, dest, dest_index)
    limit = MAX_POPS if limit is None else min(limit, MAX_POPS)
    other_star = s_star_i != d_star_i
    eta = settler_eta(speed, s_star, d_star) if other_star else 0

    src = list(source.pop)[:source.n_pops]
    dst = list(dest.pop)[:dest.n_pops]
    ids = list(range(len(src)))
    for i in held:
        if 0 <= i < len(src):
            src[i] &= ~colony_struct.POP_MASK_ASSIGNED
    n_held = len(held)

    def unassigned():
        return next((k for k, p in enumerate(src)
                     if not colony_struct.pop_is_assigned(p)), None)

    asked = 0                    # the kinds asked so far (warning_state)
    i = unassigned()
    while i is not None:
        word = src[i]
        r = dict.fromkeys(settlewire.RESULT_FIELDS, 0)
        out.result = r
        if dest.owner != source.owner:
            r["dest_owner_mismatch"] = 1
        elif blockaded(s_star, source.owner):
            r["source_blockaded"] = 1
        elif plague:
            r["source_plague"] = 1
        elif dest.outpost_flag != 0:
            r["dest_is_outpost"] = 1
        elif len(src) == 1:
            r["only_one_pop_left"] = 1
        elif colony_struct.pop_is_conquered(word):
            r["selected_pop_flag_0x400"] = 1
        elif other_star and freighters < in_transit * 5 + 5:
            r["insufficient_freighters"] = 1
        elif other_star and in_transit >= MAX_IN_TRANSIT:
            r["max_settlers_in_transit"] = 1
        else:
            if len(dst) + heading >= limit:
                r["no_room_at_destination"] = 1
            r["dest_blockaded"] = int(blockaded(d_star, dest.owner))
            r["eta_turns"] = eta
            r["can_settle"] = 1
        if not r["can_settle"]:
            out.stop = settlewire.STOP_REFUSED
            break
        if r["eta_turns"] or r["no_room_at_destination"]:
            q = question(r, out.settled, n_held - out.settled)
            if not answers & q.needs:
                out.stop = settlewire.STOP_DECLINED
                out.question = q if not asked & q.needs else None
                break
            asked |= q.needs
        prof = colony_struct.pop_prof(word)
        if job != -1 and prof != job:
            refusal = job_refusal(src, word, job)
            if refusal:
                out.stop, out.job_refusal = settlewire.STOP_JOB, refusal
                break
            word = (word & ~colony_struct.POP_MASK_PROF) | (job << 7)
            prof = job
            out.extra = True
        if other_star:
            # on a freighter now, and counted as heading there by the next
            # pop's `Room_For_Another_` (settler.cpp:73-88)
            in_transit += 1
            heading += 1
            out.transit += 1
        else:
            _add_settler(dst, word, prof, dest.max_farms, limit)
        out.sent.append(ids[i])
        out.settled += 1
        src[i], ids[i] = src[-1], ids[-1]
        src.pop()
        ids.pop()
        i = unassigned()
    out.rest = [k for k, p in enumerate(src)
                if not colony_struct.pop_is_assigned(p)]
    # the rest go back to their jobs on the engine's side (HD keeps them)
    src = [p | colony_struct.POP_MASK_ASSIGNED for p in src]
    out.colonies = {source_index: (len(src), jobs_of(src)),
                    dest_index: (len(dst), jobs_of(dst))}
    out.pops = {source_index: (len(src), src), dest_index: (len(dst), dst)}
    return out


def question(result, moved, unemployed):
    """The confirmation `Send_Cluster_` asks for this pop (colmove.cpp:
    204-262)."""
    eta = result["eta_turns"]
    if result["no_room_at_destination"]:
        if eta:
            return (Question(settlewire.YES_PAST_LIMIT, E_LIMIT_ETA, (eta,))
                    if moved == 0 else
                    Question(settlewire.YES_PAST_LIMIT, E_LIMIT_ETA_AFTER,
                             (moved, unemployed, eta)))
        return (Question(settlewire.YES_PAST_LIMIT, E_LIMIT, ())
                if moved == 0 else
                Question(settlewire.YES_PAST_LIMIT, E_LIMIT_AFTER,
                         (moved, unemployed)))
    return Question(settlewire.YES_ETA, E_ETA_SURE, (eta,))


def next_question(state, source_index, held, dest_index, answers, job=-1,
                  plague=None):
    """The first question the answers so far do not carry, or None."""
    return walk(state, source_index, held, dest_index, answers, job,
                plague).question


def job_refusal(src, word, job):
    """`Give_Colonist_New_Job_`'s refusal for a transfer (colmove.cpp:
    535-575), or 0: 1 a native to research or industry (:542-545), 2 an
    android (:548-553), 3 the job already holds 42 assigned colonists
    (:555-559). No farm limit: a transfer skips it (:565)."""
    nibble = int(word) & 0x0F
    if nibble == colony_struct.POP_NATIVE and job in (1, 2):
        return settlewire.JOB_NATIVE
    if nibble == colony_struct.POP_ANDROID:
        return settlewire.JOB_ANDROID
    assigned = sum(1 for p in src if colony_struct.pop_is_assigned(p) and
                   colony_struct.pop_prof(p) == job)
    if assigned >= MAX_POPS:
        return settlewire.JOB_FULL
    return 0


def _add_settler(dst, word, prof, max_farms, limit):
    """`SETTLER::Add_Settler_To_Colony_` (settler.cpp:16-63): appended with
    its job, assigned — a farmer where the farms are full turns scientist
    (an android turns the colony's first non-android farmer instead); none
    is added where the colony is full (it dies: the questions said so)."""
    if len(dst) >= limit:
        return
    race = int(word) & 0x0F
    farmers = [k for k, p in enumerate(dst) if colony_struct.pop_prof(p) == 0]
    if prof == 0 and len(farmers) >= max_farms:
        if race < 8:
            prof = 2
        else:
            first = next((k for k in farmers if (dst[k] & 0x0F) < 8), None)
            if first is not None:
                dst[first] = (dst[first] & ~colony_struct.POP_MASK_PROF) | \
                    (2 << 7)
    dst.append(race | ((race & 7) << 4) | (prof << 7) |
               colony_struct.POP_MASK_ASSIGNED)


def jobs_of(words):
    out = [0, 0, 0]
    for p in words:
        prof = colony_struct.pop_prof(p)
        if 0 <= prof < 3:
            out[prof] += 1
    return tuple(out)


# ── The boxes' texts, as `Send_Cluster_` builds them ─────────────────

def cfmt(fmt, *values):
    """printf's %d / %s, in order, by replacement (decision 37: a brace in
    a translated string must not raise in a render path)."""
    out, k, i = [], 0, 0
    fmt = fmt or ""
    while i < len(fmt):
        c = fmt[i]
        if c == "%" and i + 1 < len(fmt):
            n = fmt[i + 1]
            if n == "%":
                out.append("%")
                i += 2
                continue
            if n in "ds":
                out.append(str(values[k]) if k < len(values) else "")
                k += 1
                i += 2
                continue
        out.append(c)
        i += 1
    return "".join(out)


def _build(lines):
    """`ERIC::String_Builder2_`: line 0 starts it, every other is joined
    with E 71's "%s%c%s" and 13 (eric.cpp:425-455) — a FMTPARA line."""
    return "\r".join(lines)


def question_text(strings, q):
    return cfmt(strings.string(q.estring), *q.values)


def failed_text(strings, w):
    """The "Settlers Failed." box's text for a walk that stopped on a
    refusal or a NO, or None when it has no line — then the original
    says E 0xE4 in a help box (colmove.cpp:302-379, :390-468)."""
    r = w.result or {}
    lines = []
    if r.get("eta_turns"):
        lines.append(cfmt(strings.string(
            E_DECLINED_LIMIT_ETA if r.get("no_room_at_destination")
            else E_DECLINED_ETA), r["eta_turns"]))
    elif r.get("no_room_at_destination"):
        lines.append(cfmt(strings.string(E_DECLINED_LIMIT)))
    for key, sid in REASON_LINES:
        if r.get(key):
            lines.append(cfmt(strings.string(sid)))
    if not lines:
        return None
    if w.settled:
        lines.append(cfmt(strings.string(E_ENROUTE), w.settled))
    return _build(lines)


def pop_noun(strings, words_or_word, players_raw, owner):
    """`Colony_Pop_String_` (colmove.cpp:577-602): E 0x4C over the
    conquered word, the race, the state word and the job."""
    word = int(words_or_word)
    nibble = word & 0x0F
    if nibble == colony_struct.POP_ANDROID:
        race = strings.string(E_ANDROID) or ""
    elif nibble == colony_struct.POP_NATIVE:
        race = strings.string(E_NATIVE) or ""
    else:
        raw = players_raw[nibble] if 0 <= nibble < len(players_raw) else None
        race = player_struct.parse(raw).race_name if raw else ""
    conquered = strings.string(E_CONQUERED) if word & 0x400 else \
        strings.string(12)
    job = strings.string(E_JOBS[colony_struct.pop_prof(word) % 3])
    return cfmt(strings.string(E_POP_FORMAT), conquered or "", race or "",
                strings.string(12) or "", job or "")


def depart_text(strings, w, noun, source_name, dest_name):
    """The "Settlers Depart" box's text (colmove.cpp:482-522)."""
    r = w.result or {}
    lines = [cfmt(strings.string(E_DEPART), w.settled, noun, source_name,
                  dest_name, r.get("eta_turns", 0))]
    if r.get("dest_blockaded"):
        lines.append(cfmt(strings.string(E_DEST_BLOCKADED)))
    if r.get("field10_0xa"):
        lines.append(cfmt(strings.string(E_NO_FARMING_NOTE)))
    if w.extra:
        lines.append(cfmt(strings.string(E_SHUFFLED)))
    return _build(lines)


def job_refusal_text(strings, refusal):
    return cfmt(strings.string({settlewire.JOB_NATIVE: E_JOB_NATIVE,
                                settlewire.JOB_ANDROID: E_JOB_ANDROID,
                                settlewire.JOB_FULL: E_JOB_FULL}
                               .get(refusal, E_UNSPECIFIED)))


def from_outcome(outcome, forecast):
    """The engine's STLR as a `Walk` for the boxes: its count, its stop and
    its result; the forecast's arrays where they agree, else none."""
    w = Walk()
    w.settled = int(outcome.get("settled", 0))
    w.stop = int(outcome.get("stop", settlewire.STOP_NONE))
    w.result = dict(outcome.get("result") or {})
    w.job_refusal = int(outcome.get("job_refusal", 0))
    w.extra = bool(outcome.get("extra_notice")) or \
        bool(forecast is not None and forecast.extra and w.settled)
    if forecast is not None and forecast.settled == w.settled:
        w.sent, w.rest = forecast.sent, forecast.rest
        w.colonies, w.pops = forecast.colonies, forecast.pops
    return w
