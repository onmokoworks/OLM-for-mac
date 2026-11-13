"""Bitwise logf comparison with this machine's UCRT; no AE or child processes."""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import random
import struct


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    candidate = a.candidate.resolve()
    provider = Path(os.environ['SystemRoot']) / 'System32/ucrtbase.dll'
    native = c.CDLL(str(provider))
    rust = c.CDLL(str(candidate))
    native.logf.argtypes = [c.c_float]
    native.logf.restype = c.c_float
    native._set_FMA3_enable.argtypes = [c.c_int]
    native._set_FMA3_enable.restype = c.c_int
    rust.uv_logf.argtypes = [c.c_float, c.c_int]
    rust.uv_logf.restype = c.c_float
    rng = random.Random(20261113)
    # Finite positive values across all exponents, plus meaningful boundaries.
    bits = [rng.randrange(1, 0x7f800000) for _ in range(50000)]
    bits += [0, 0x80000000, 1, 0x7fffff, 0x800000, 0x3f800000,
             0x7f800000, 0xbf800000, 0x7fc12345]
    results = []
    for mode in [0, 1]:
        if native._set_FMA3_enable(mode) != mode:
            raise RuntimeError(f'UCRT cannot enable requested FMA mode {mode}')
        failures = []
        for word in bits:
            x = struct.unpack('<f', struct.pack('<I', word))[0]
            ref = struct.pack('<f', native.logf(x))
            got = struct.pack('<f', rust.uv_logf(x, mode))
            if ref != got:
                failures.append(dict(input=f'{word:08x}', reference=ref.hex(), rust=got.hex()))
        results.append(dict(mode=mode, count=len(bits), mismatches=len(failures), first=failures[:8]))
    def identity(path):
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    report = dict(candidate=identity(candidate), provider=identity(provider), seed=20261113,
                  results=results, scope='return bits only; errno and FP exception flags excluded')
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(results))
    return int(any(r['mismatches'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
