#!/usr/bin/env python3
"""Bit-exact comparator for already normalized tightly packed ARGB planes.

This does NOT decode TIFF/EXR or infer alpha/scaling/color transforms. Supply
planes only after independently checking the no-effect I/O round trip. Float
comparisons are byte-exact, including signed zero and NaN payloads.
"""
import argparse
import hashlib
import json
from pathlib import Path


def compare(left, right, width, height, depth):
    size = {8: 1, 16: 2, 32: 4}[depth]
    expected = width * height * 4 * size
    for path in (left, right):
        if path.stat().st_size != expected:
            raise ValueError(f'{path}: expected {expected} bytes, got {path.stat().st_size}')
    hashes = [hashlib.sha256(), hashlib.sha256()]
    differing = 0
    first = None
    with left.open('rb') as a, right.open('rb') as b:
        for y in range(height):
            la, rb = a.read(width * 4 * size), b.read(width * 4 * size)
            hashes[0].update(la); hashes[1].update(rb)
            for word in range(width * 4):
                av, bv = la[word*size:(word+1)*size], rb[word*size:(word+1)*size]
                if av != bv:
                    differing += 1
                    if first is None:
                        first = dict(x=word//4,y=y,channel='ARGB'[word%4],
                                     ae_bytes=av.hex(),host_bytes=bv.hex())
    return dict(exact=differing == 0, differing_samples=differing,
                first_mismatch=first, ae_sha256=hashes[0].hexdigest(),
                host_sha256=hashes[1].hexdigest(), classification=None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ae',type=Path); p.add_argument('host',type=Path)
    p.add_argument('--width',type=int,required=True)
    p.add_argument('--height',type=int,required=True)
    p.add_argument('--depth',type=int,choices=(8,16,32),required=True)
    a=p.parse_args()
    if a.width <= 0 or a.height <= 0: p.error('dimensions must be positive')
    result=compare(a.ae,a.host,a.width,a.height,a.depth)
    print(json.dumps(result,indent=2))
    return 0 if result['exact'] else 1

if __name__=='__main__':
    raise SystemExit(main())
