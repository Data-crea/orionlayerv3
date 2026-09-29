"""The per-App LRU the colony screens keep their sprite sets in — audit D3.

`colonyplanets`, `colonyoutputicons` and `colonyfigures` each build sets of
scaled sprites that are expensive to make and cheap to keep, keyed by what
makes one set differ from another (a pixel size; for the output icons the
master and the size). Each keeps them on the App, most recently used last,
and evicts the oldest beyond its own limit — 4, 2 and 4, each with its
reason beside its `SET_CACHE`. Until work order 191 the block stood in all
three, copied; this is its one home, and what differed — the App attribute,
the key, the factory, the limit — is what the callers pass. Their guards
(a size that is no set) stay theirs. Smoke check 053b holds the behaviour.
"""
import collections


def lru(app, attr, key, build, limit):
    """The set under `key` in `app.<attr>`, built by `build()` on a miss.

    A hit moves the key to the end; a miss adds it there and evicts from
    the front until at most `limit` remain.
    """
    cache = getattr(app, attr, None)
    if cache is None:
        cache = collections.OrderedDict()
        setattr(app, attr, cache)
    if key in cache:
        cache.move_to_end(key)
    else:
        cache[key] = build()
        while len(cache) > limit:
            cache.popitem(last=False)
    return cache[key]
