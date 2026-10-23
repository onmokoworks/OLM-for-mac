#!/usr/bin/env python3
"""PF32 NaN erosion/subtraction boundaries through the real public Smart host."""
import copy
import json
import os
from pathlib import Path
import struct
import tempfile
import time
from types import SimpleNamespace

from adapters.olmcolorkey import Adapter
from core import raw_diff, sha

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/C42-colorkey-pf32-nan-mismatch'


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH))
    rows = []
    with tempfile.TemporaryDirectory(dir=SCRATCH, prefix='boundaries-') as tmp:
        directory = Path(tmp)
        adapter = Adapter(SimpleNamespace(max_size=256, case_timeout=10,
            main=ROOT.parent.parent,
            worker=Path('/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker')))
        deadline = time.monotonic() + 600
        provenance = adapter.prepare(directory, deadline)
        original = adapter.generate(46, 237)
        # Retain the original RGB/classifier and independently vary every NaN alpha,
        # its sign/quiet bit/payload, erosion distance, and final subtraction owner.
        for word in (0x7fc12345, 0xffc12346, 0x7f812345, 0xff812346):
            for thin in (-1, -2929):
                for keep in (0, 1):
                    case = copy.deepcopy(original)
                    pixels = bytearray(case['pixels'])
                    for at in range(0, len(pixels), 16):
                        old = struct.unpack_from('<I', pixels, at)[0]
                        if (old & 0x7fffffff) > 0x7f800000:
                            struct.pack_into('<I', pixels, at, word)
                    case['pixels'] = bytes(pixels)
                    for p in case['parameters']:
                        if p['slot'] == 1: p['value'] = keep
                        if p['slot'] == 14: p['value'] = thin
                    oracle, ref = adapter.oracle(case, directory, deadline, 'smart')
                    candidate, raw, *_ = adapter.candidate(case, directory, 'smart', deadline)
                    rows.append(dict(alpha_word=f'{word:08x}', thin=thin, keep=keep,
                        input_sha256=sha(pixels), oracle=oracle, candidate=candidate,
                        reference_sha256=sha(ref), candidate_sha256=sha(raw),
                        diff=raw_diff(ref, raw, 32)))
    result = dict(provenance=provenance, cases=rows)
    (SCRATCH/'boundaries.json').write_text(json.dumps(result, indent=2)+'\n')
    failures = [r for r in rows if r['oracle']['status'] != 'ok' or
        r['candidate']['status'] != 'ok' or r['diff']['different_words']]
    print(f'{len(rows)-len(failures)}/{len(rows)} Smart boundaries exact')
    for r in failures: print(r['alpha_word'], r['thin'], r['keep'], r['diff'])
    assert not failures


if __name__ == '__main__':
    main()
