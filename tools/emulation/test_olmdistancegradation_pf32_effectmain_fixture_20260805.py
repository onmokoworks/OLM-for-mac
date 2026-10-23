#!/usr/bin/env python3
"""Replay original-AEX public Smart expectations against current Mac production."""
import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'tools/fuzz'))
from adapters.olmdistancegradation import Adapter

FIXTURES = [R / ('refs/fixtures/olmdistancegradation_pf32_owner_17x11' + suffix
                 + '_public_smart_20261023') for suffix in ('', '_controlled_source')]


def main():
    # F18-route-target-per-plugin.md: AE selects Smart for DG. Classic is
    # outside this retained public regression; zero buffers are not its oracle.
    scratch = R / 'orchestra/state/F35-dg-fixture-rebind'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as t:
        directory = Path(t)
        deadline = time.monotonic() + 120
        # Building/replaying the Mac candidate needs no AEX or reference worker.
        adapter = Adapter(argparse.Namespace(max_size=256, case_timeout=30,
                                            main=R, worker=R))
        adapter.env.update(TMPDIR=t, TMP=t, TEMP=t)
        adapter.binary, _ = adapter.build(directory, deadline)
        parameters = adapter.defaults(17, 11)
        values = {1: 1, 2: 1, 3: 4, 4: 4, 5: 1, 6: 1, 7: [255, 28, 0, 238],
                  8: [255, 255, 0, 0], 9: 2, 10: 1, 11: 1, 12: 0}
        for param in parameters:
            param['value'] = values[param['slot']]
        for fixture in FIXTURES:
            source = (fixture / 'source_argb_f32.bin').read_bytes()
            expected = (fixture / 'output_argb_f32.bin').read_bytes()
            provenance = json.loads((fixture / 'provenance.json').read_text())
            assert parameters == provenance['controls']
            assert len(source) == len(expected) == 2992
            for data, key in ((source, 'source_sha256'), (expected, 'output_sha256')):
                assert hashlib.sha256(data).hexdigest() == provenance[key]
            case = dict(geometry=[17, 11], depth=32, parameters=parameters,
                        pixels=source, input_padding=0, output_padding=0)
            status, actual, _ = adapter.candidate(case, directory, 'smart', deadline)
            assert status['status'] == 'ok', status
            assert len(actual) == len(expected)
            mismatches = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
            assert not mismatches, f'byte mismatches={len(mismatches)} first={mismatches[0]}'
            print(f'PASS {fixture.name} Smart PF32 bytes=2992 mismatches=0')
    print('PASS_OLMDISTANCEGRADATION_PF32_EFFECTMAIN_TYPED_BYTES_EXACT')


if __name__ == '__main__':
    main()
