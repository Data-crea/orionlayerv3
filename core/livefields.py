"""Reading the LIVE field list: one field, by its shape, right now.

A field NUMBER means something else in every other list (decision 20,
decision 59), so nothing in OrionLayer may remember an index and send
it later. A send resolves the field in the list it was handed in the
same step, by type and native rectangle, or it does not go at all.

That rule was paid for twice — the scrapped colony base in work order
122 and the SIGSEGV in the research prompt in 128 — and it is what
`tools/livesend.py` enforces for the live tools (work order 129 A).

These two functions started in `screens/galaxy_map/mapboxes.py`, where
the map cancel and then the map's parking guard both needed them (work
order 128 C). The research screen is the third caller, and a screen
importing another screen's module to get at a shared rule is how the
rule ends up copied instead. `mapboxes` imports them from here and
keeps its own names, so its callers are unchanged.
"""


def rect(f):
    """The field's native 640x480 rectangle, inclusive."""
    return (f.x, f.y, f.x_end, f.y_end)


def live_field(fields, spec):
    """The field `spec` names — its type and native rect — in the LIVE list.

    None when the list holds no such field. A send goes to the index
    this returns at the moment, or does not go at all.

    `spec` is a mapping with `field_type` and `rect`.
    """
    if not spec:
        return None
    want = tuple(spec.get("rect") or ())
    return next((f for f in (fields or [])
                 if f.field_type == spec.get("field_type")
                 and rect(f) == want), None)
