"""Structure reducible CFGs using nested SCC loops and lexical forward exits.

Every basic block is emitted once. Single-entry SCCs become loops; an edge to
the header becomes continue, an edge outside becomes the enclosing forward
exit. Removing header backedges must recursively reduce every SCC. Fail closed
on irreducible/multiple-entry loops. Operations inside blocks are untouched.
"""
from pathlib import Path
import re
import sys

sys.setrecursionlimit(10000)
path = Path(__file__).resolve().parents[1] / 'src/kernels.rs'
source = path.read_text()


def structure(f):
    # Alpha blend has a nested translated closure with its own dispatcher;
    # leave both scopes intact rather than parse Rust closures as CFG blocks.
    if f.count('loop {match pc {') != 1:
        return f
    match = re.search(r'let mut pc: u32=(\d+);\nloop \{match pc \{\n', f)
    if not match:
        return f
    entry = int(match[1])
    blocks = {int(n): b for n, b in re.findall(r'^(\d+) => \{ (.*?) \},$', f[match.end():], re.M | re.S)}
    kinds, edges = {}, {}
    for n, b in blocks.items():
        pos = b.rfind('if ')
        m = re.fullmatch(r'if (.*?) \{pc=(\d+);\} else \{pc=(\d+);\} continue;', b[pos:], re.S) if pos >= 0 else None
        if m:
            kinds[n] = ('if', b[:pos], m[1], int(m[2]), int(m[3]))
            edges[n] = [int(m[2]), int(m[3])]
        else:
            m = re.search(r'pc=(\d+);\s*continue;$', b)
            if m:
                kinds[n] = ('goto', b[:m.start()], int(m[1]))
                edges[n] = [int(m[1])]
            else:
                assert 'pc=' not in b
                kinds[n], edges[n] = ('end', b), []
    reachable = set()
    def visit(n):
        if n in reachable:
            return
        reachable.add(n)
        for q in edges[n]:
            visit(q)
    visit(entry)
    emitted = set()

    def emit(nodes, start, headers):
        # Tarjan with active enclosing-loop backedges removed.
        indices, low, stack, active, components = {}, {}, [], set(), []
        def strong(n):
            indices[n] = low[n] = len(indices)
            stack.append(n); active.add(n)
            for q in edges[n]:
                if q not in nodes or q in headers:
                    continue
                if q not in indices:
                    strong(q); low[n] = min(low[n], low[q])
                elif q in active:
                    low[n] = min(low[n], indices[q])
            if low[n] == indices[n]:
                c = set()
                while True:
                    q = stack.pop(); active.remove(q); c.add(q)
                    if q == n:
                        break
                components.append(c)
        for n in sorted(nodes):
            if n not in indices:
                strong(n)
        owner = {n: i for i,c in enumerate(components) for n in c}
        heads = {}
        for i,c in enumerate(components):
            incoming = ({start} if start in c else set()) | {q for p in nodes-c for q in edges[p] if q in c and q not in headers}
            assert len(incoming) == 1, ('irreducible', c, incoming)
            heads[i] = incoming.pop()
        order, seen = [], set()
        def topo(i):
            if i in seen:
                return
            seen.add(i)
            for n in sorted(components[i]):
                for q in edges[n]:
                    if q in nodes and q not in headers and owner[q] != i:
                        topo(owner[q])
            order.append(i)
        topo(owner[start]); order.reverse()
        assert len(order) == len(components)
        positions = {i:j for j,i in enumerate(order)}
        assert all(positions[i] < positions[owner[q]] for i,c in enumerate(components) for n in c for q in edges[n] if q in nodes and q not in headers and owner[q] != i)
        out = ["'b%d: {" % heads[i] for i in reversed(order[1:])]
        def jump(q):
            return "continue 'l%d;" % q if q in headers else "break 'b%d;" % q
        for index,i in enumerate(order):
            if index:
                out.append('}')
            c,h = components[i],heads[i]
            cyclic = len(c)>1 or (h in edges[h] and h not in headers)
            if cyclic:
                out += ["'l%d: loop {" % h, emit(c,h,headers|{h}), '}']
            else:
                assert h not in emitted
                emitted.add(h)
                k = kinds[h]
                out.append(k[1])
                if k[0] == 'goto':
                    out.append(jump(k[2]))
                elif k[0] == 'if':
                    out.append('if %s { %s } else { %s }' % (k[2],jump(k[3]),jump(k[4])))
        return '\n'.join(out)
    result = emit(reachable,entry,set())
    assert emitted == reachable
    return f[:match.start()] + result + '\n}\n'


parts = re.split(r'(?=pub\(super\) unsafe fn )',source)
results = []
for f in parts[1:]:
    name = re.search(r'fn (\w+)',f)[1]
    try:
        result = structure(f)
        results.append(result)
        print(name, 'structured' if result != f else 'retains nested closure dispatch')
    except AssertionError as error:
        if not error.args or not isinstance(error.args[0],tuple) or error.args[0][0] != 'irreducible':
            raise
        print(name,'retains irreducible dispatch:',error)
        results.append(f)
path.write_text(parts[0] + ''.join(results))
