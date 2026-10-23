#!/usr/bin/env python3
"""Observe otherwise-hidden failed child output without changing test assertions."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

out = Path(os.environ['R03_DIAGNOSTICS'])
out.mkdir(parents=True, exist_ok=True)
original = subprocess.run
count = 0

def observe(argv, *args, **kwargs):
    global count
    try:
        result = original(argv, *args, **kwargs)
    except subprocess.CalledProcessError as exc:
        record(argv, exc.returncode, exc.stdout, exc.stderr)
        raise
    if result.returncode:
        record(argv, result.returncode, result.stdout, result.stderr)
    return result

def record(argv, code, stdout, stderr):
    global count
    prefix = out / str(count)
    count += 1
    prefix.with_suffix('.json').write_text(json.dumps(dict(command=list(map(str, argv)), exit=code), indent=2))
    for suffix, data in (('.stdout.bin', stdout), ('.stderr.bin', stderr)):
        if data is not None:
            prefix.with_suffix(suffix).write_bytes(data.encode() if isinstance(data, str) else data)

def trace(frame, event, arg):
    if frame.f_code.co_filename != target:
        return None
    if (event == 'exception' and issubclass(arg[0], AssertionError)) or (event == 'return' and frame.f_code.co_name == 'main'):
        values = frame.f_locals
        comparisons = []
        expected = values.get('actual', values.get('cases'))
        candidate = values.get('production')
        def planes(a, b, prefix=''):
            if isinstance(a, dict) and isinstance(b, dict):
                for key in a.keys() & b.keys():
                    yield from planes(a[key], b[key], prefix + '/' + str(key))
            elif isinstance(a, bytes) and isinstance(b, bytes):
                yield prefix, a, b
        for name, a, b in planes(expected, candidate):
            first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
            if first is None and len(a) != len(b): first = min(len(a), len(b))
            row = dict(plane=name, expected_bytes=len(a), actual_bytes=len(b), first_byte=first,
                       expected_sha256=hashlib.sha256(a).hexdigest(), actual_sha256=hashlib.sha256(b).hexdigest(),
                       differing_bytes=sum(x != y for x, y in zip(a, b)) + abs(len(a)-len(b)))
            if first is not None:
                start = first // 4 * 4
                row.update(expected_word=a[start:start+4].hex(), actual_word=b[start:start+4].hex())
            comparisons.append(row)
        result = dict(file=target, line=frame.f_lineno, exception=str(arg[1]) if event == 'exception' else 'return=' + str(arg), comparisons=comparisons, locals={k:type(v).__name__ for k,v in values.items()})
        (out / (event + '-' + str(frame.f_lineno) + '.json')).write_text(json.dumps(result, indent=2))
    return trace

subprocess.run = observe
sys.argv = sys.argv[1:]
if sys.argv[0] == '-m':
    name = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_module(name, run_name='__main__', alter_sys=True)
else:
    target = str(Path(sys.argv[0]).resolve())
    sys.settrace(trace)
    runpy.run_path(target, run_name='__main__')
