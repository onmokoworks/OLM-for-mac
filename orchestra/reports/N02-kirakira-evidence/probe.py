#!/usr/bin/env python3
"""N02 scalar nonfinite matrix and normalized-geometry paired-stage probes."""
import base64
import itertools
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools/emulation'))
import probe_kirakira_smart_C07 as probe

witness = None
if '--witness' in sys.argv:
    at = sys.argv.index('--witness')
    witness = Path(sys.argv[at + 1])
    del sys.argv[at:at + 2]

def cases(adapter, family):
    if witness:
        saved = json.loads(witness.read_text())
        case = saved['case']
        case['pixels'] = zlib.decompress(base64.b64decode(saved['pixels_zlib_base64']))
        num, den = case.get('downsample', [[1, 1]])[0]
        # Trace helper starts after the owner: materialize its X scale here.
        for p in case['parameters']:
            if p['slot'] in (10, 16, 22, 28, 34):
                p['value'] = int(p['value'] * num / den)
            if p['slot'] == 4 and num / den <= .5:
                p['value'] = 0
        for key in ('geometry_sampler', 'full_geometry', 'downsample', 'extent_hint',
                    'request_rect', 'pixel_aspect', 'rowbytes_padding'):
            case.pop(key, None)
        case['index'] = 0
        yield case
        return
    words = (0x7f800000, 0xff800000, 0x7fc12345, 0xff812346)
    combinations = itertools.product((2, 4), (1, 2), (1, 2), ((1, 1), (3, 5), (7, 11)), words, range(4))
    for index, (channel, mode, merge, shape, word, lane) in enumerate(combinations):
        case = probe.matrix_case(adapter, index, shape, 32, merge, mode, channel)
        params = {5: 1., 6: (1, 100, 537)[index % 3], 7: (0., .1)[index % 2],
                  8: 100, 9: 100, 10: (1, 3, 50)[index % 3], 16: 2, 22: 3,
                  28: 0, 34: (0, 3)[index % 2], 40: 0.}
        for p in case['parameters']:
            if p['slot'] in params:
                p['value'] = params[p['slot']]
        data = bytearray(case['pixels'])
        struct.pack_into('<I', data, lane * 4, word)
        case.update(pixels=bytes(data), profile='N02-nonfinite-scalar-box')
        yield case

probe.cases = cases
probe.main()
