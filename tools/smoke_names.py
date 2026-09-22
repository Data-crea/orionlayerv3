"""Which names a block of the smoke suite reads, binds and mutates.

A library, not a tool — `tools/smoke_inventory.py` is its only caller
and carries the `__main__`. It is separate because the two jobs are
separate: this file answers "what does this code touch", the inventory
answers "what is this code about", and decision 6's guideline is easier
to keep with the two apart.

**Why it is scope-correct rather than a grep.** Work order 158 moved
seven blocks out of the commit gate and had to answer the same question
by hand; a first pass got it wrong twice, once by counting names bound
inside a nested `def` as the enclosing scope's, once by stopping at the
first mutation. Both mistakes are invisible in a green run and fatal in
a cut: a section moved away from the state it fills is a check that
still passes and no longer measures anything.

**A FREE read is the only kind that makes a dependency.** `_fh =
open(_fh)` reads a name it then binds; `_fh = open(path)` does not. A
set-based "reads minus binds" cannot tell the two apart, so everything
here walks in EXECUTION order — value before target, header before
body.

**Mutation is tracked separately and is the half a read/write analysis
cannot see.** `_surf.blit(...)` binds nothing and changes everything a
later reader of `_surf` sees.
"""
import ast

#: Methods that change their receiver in place. Not exhaustive on
#: purpose — it is a net for the common containers and surfaces, and a
#: name that reaches it is examined rather than trusted.
MUTATORS = frozenset((
    "append", "add", "extend", "insert", "update", "setdefault", "pop",
    "popitem", "remove", "discard", "clear", "sort", "reverse", "write",
    "writelines", "fill", "blit", "set_at", "set_alpha", "set_clip"))

SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def root_name(node):
    """The Name a Subscript/Attribute chain hangs off, or None."""
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _locals_of(node):
    """Every name a nested scope binds for itself."""
    out = set()
    args = getattr(node, "args", None)
    if args is not None:
        for group in (args.posonlyargs, args.args, args.kwonlyargs):
            out.update(a.arg for a in group)
        for extra in (args.vararg, args.kwarg):
            if extra:
                out.add(extra.arg)
    body = node.body if isinstance(node.body, list) else [node.body]
    stack = list(body)
    while stack:
        cur = stack.pop()
        if isinstance(cur, SCOPES):
            if not isinstance(cur, ast.Lambda):
                out.add(cur.name)
            continue
        if isinstance(cur, ast.Name) and isinstance(cur.ctx, ast.Store):
            out.add(cur.id)
        elif isinstance(cur, ast.alias):
            out.add((cur.asname or cur.name).split(".")[0])
        elif isinstance(cur, ast.ExceptHandler) and cur.name:
            out.add(cur.name)
        elif isinstance(cur, (ast.Global, ast.Nonlocal)):
            out.update(cur.names)
        stack.extend(ast.iter_child_nodes(cur))
    return out


def touches(nodes):
    """(reads, binds, mutates) at the OUTER scope, for a statement list.

    Order-blind: `reads` is every name read anywhere, whether or not
    this block binds it first. `free_of` is the ordered answer.
    """
    reads, binds, mutates = set(), set(), set()

    def walk(node, free):
        # `free` is None at the outer scope, where every store binds;
        # inside a nested scope it holds that scope's own locals, and a
        # name not in it is a read of the scope we came from.
        if isinstance(node, SCOPES + COMPS):
            if isinstance(node, SCOPES) and not isinstance(node, ast.Lambda):
                if free is None:
                    binds.add(node.name)
            inner = (_locals_of(node) if not isinstance(node, COMPS) else
                     {t.id for gen in node.generators
                      for t in ast.walk(gen.target) if isinstance(t, ast.Name)})
            below = inner if free is None else (free | inner)
            for child in ast.iter_child_nodes(node):
                walk(child, below)
            return
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                if free is None or node.id not in free:
                    reads.add(node.id)
            elif free is None:
                binds.add(node.id)
            return
        if isinstance(node, ast.alias) and free is None:
            binds.add((node.asname or node.name).split(".")[0])
            return
        if isinstance(node, ast.ExceptHandler) and node.name and free is None:
            binds.add(node.name)
        if (isinstance(node, (ast.Attribute, ast.Subscript))
                and not isinstance(node.ctx, ast.Load)):
            name = root_name(node)
            if name:
                mutates.add(name)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS):
            name = root_name(node.func.value)
            if name:
                mutates.add(name)
        for child in ast.iter_child_nodes(node):
            walk(child, free)

    for stmt in nodes:
        walk(stmt, None)
    return reads, binds, mutates


def _use(node, bound, free, mut, glob):
    """Read one expression — or one assignment target — at this point."""
    reads, binds, mutates = touches([ast.Expr(node)])
    free.update(n for n in reads if n not in bound and n not in glob)
    bound.update(binds)
    mut.update(mutates)


def _stmt(node, bound, free, mut, glob):
    """One statement, in execution order."""
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        if node.value is not None:
            _use(node.value, bound, free, mut, glob)
        if isinstance(node, ast.AugAssign) and root_name(node.target):
            _use(ast.Name(id=root_name(node.target), ctx=ast.Load()),
                 bound, free, mut, glob)
        for target in (node.targets if isinstance(node, ast.Assign)
                       else [node.target]):
            _use(target, bound, free, mut, glob)
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        _use(node.iter, bound, free, mut, glob)
        _use(node.target, bound, free, mut, glob)
        _walk(node.body, bound, free, mut, glob)
        _walk(node.orelse, bound, free, mut, glob)
    elif isinstance(node, ast.While):
        _use(node.test, bound, free, mut, glob)
        _walk(node.body, bound, free, mut, glob)
        _walk(node.orelse, bound, free, mut, glob)
    elif isinstance(node, ast.If):
        _use(node.test, bound, free, mut, glob)
        # BOTH ARMS, each from the state before the test. A name bound
        # in one arm only counts as bound afterwards: the question is
        # which SECTION supplies a name, and a conditional binding
        # inside this one is this one's business.
        for arm in (node.body, node.orelse):
            _walk(arm, bound, free, mut, glob)
    elif isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            _use(item.context_expr, bound, free, mut, glob)
            if item.optional_vars is not None:
                _use(item.optional_vars, bound, free, mut, glob)
        _walk(node.body, bound, free, mut, glob)
    elif isinstance(node, ast.Try):
        for part in (node.body, node.orelse, node.finalbody):
            _walk(part, bound, free, mut, glob)
        for handler in node.handlers:
            if handler.type is not None:
                _use(handler.type, bound, free, mut, glob)
            if handler.name:
                bound.add(handler.name)
            _walk(handler.body, bound, free, mut, glob)
    else:
        # A def, a class, an import, an assert, an expression — through
        # the scoped walk in one piece. A nested def's body is read AT
        # ITS DEFINITION, which is the conservative direction: it can
        # only make a dependency look earlier than it is, never later.
        reads, binds, mutates = touches([node])
        free.update(n for n in reads if n not in bound and n not in glob)
        bound.update(binds)
        mut.update(mutates)


def _walk(stmts, bound, free, mut, glob):
    for stmt in stmts:
        _stmt(stmt, bound, free, mut, glob)


def free_of(stmts, glob=()):
    """(free reads, bindings, mutations) for one block, in order.

    `glob` is every name the block can take for granted — the suite
    module's own globals and the builtins.
    """
    bound, free, mut = set(), set(), set()
    _walk(stmts, bound, free, mut, set(glob))
    return sorted(free), sorted(bound), sorted(mut)


def module_names(tree):
    """Everything a module binds at its top level, plus the builtins."""
    import builtins
    out = set(dir(builtins))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            out.update((a.asname or a.name).split(".")[0] for a in node.names)
        else:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                    out.add(sub.id)
    return out
