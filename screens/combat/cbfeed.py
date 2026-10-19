"""The next battle's snapshots while the last one's tail still plays — work
order 305 (the audit's item 20).

A battle's last events arrive with the first snapshot after it and are
played on the battle as it stood (`screen.update`, work order 202 D). If
the next battle starts meanwhile, its snapshots pass under that tail; HD
took none of them, so the events they brought were never played and the
next battle opened on a state that already held their results — against
Data's condition (every event before the state after it, `cbplay`).

`NextBattle` keeps them: the first snapshot of the next battle (its own
events come before it and are not played, as at any battle's start) and
every event of that battle after it, once each, until the screen takes the
battle; then the Player starts on that first state and queues the kept
events before the new snapshot's own.
"""


class NextBattle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.first = None        # (combat, ordnance): its first snapshot
        self.events = []         # its events after that snapshot
        self._seen = None        # the last event number looked at

    def keep(self, serial, combat, events, ordnance):
        """One snapshot during the tail of battle `serial`."""
        new = [e for e in events if e.get("serial") != serial and
               (self._seen is None or e["seq"] > self._seen)]
        if events:
            self._seen = max(self._seen or 0, events[-1]["seq"])
        if self.first is None:
            if combat is not None and combat["serial"] != serial:
                self.first = (combat, ordnance)
            return
        self.events.extend(e for e in new
                           if e.get("serial") == self.first[0]["serial"])

    def start(self, player, combat, current=()):
        """The battle of snapshot `combat` is taken: the Player starts on
        its first kept state; returns the events kept after it — nothing
        when none was kept, or `combat` is that first snapshot itself (its
        events come before it). `current` is the events `combat` itself
        brings, which the caller queues: a snapshot already kept during
        the tail (no new state since) would otherwise play them twice."""
        first, events = self.first, self.events
        self.reset()
        if first is None or first[0]["serial"] != combat["serial"] or \
                first[0] is combat:
            return []
        player.feed(first[0], [], first[1])
        here = {e["seq"] for e in current}
        return [e for e in events if e["seq"] not in here]
