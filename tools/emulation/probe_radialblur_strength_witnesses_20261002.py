#!/usr/bin/env python3
"""Strength setup and a retained same-input native-UCRT hash witness.

Full frames/contexts stay private. The historical hash only proves its one
captured input/settings cell, not a general native math implementation.
"""
import json
from pathlib import Path
import struct

import probe_radialblur_strength_20261002 as strength

public = strength.public
quality = strength.gain.quality
HISTORICAL = public.ROOT/'refs/conformance/olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.json'
HISTORICAL_INPUT_SHA256 = '187a7caf98537700d3644aed245150467f284b87ef73df56e46dd331ba40cf1f'
HISTORICAL_OUTPUT_SHA256 = '5c70fe269db5c2923c1ce1a63645f83075975ab6b13eb34e09c240b999351f28'


def field_cases():
    cases = []
    for family in [1, 2]:
        for quality_value in [1, 3.4, 5, 10]:
            for outer in [64, 65, 66, 67, 290, 1499, 1500, 1501, 1999, 2000]:
                params = public.initial.settings(family, 1, 1)
                changes = {4: outer, 10: 2001-outer, 20: quality_value, 7: 37, 13: 31}
                for param in params:
                    if param['slot'] in changes: param['value'] = changes[param['slot']]
                cases.append(dict(family=family, geometry=[1, 1], depth=8, pattern='opaque',
                    state='strength_fields', parameters=params))
    assert len(cases) == 80
    return cases


def native_fields(worker, directory):
    previous = quality.field_cases
    try:
        quality.field_cases = field_cases
        return quality.native_fields(worker, directory)
    finally: quality.field_cases = previous


def historical_fixture():
    width, height = 32, 18
    raw = bytearray(width*height*16)
    points = ({(x, y) for y in range(2, 5) for x in range(2, 5)} |
              {(x, y) for y in range(9, 11) for x in range(13, 15)} | {(27, 14)})
    for y in range(height):
        for x in range(width):
            if (x, y) in points:
                struct.pack_into('<4f', raw, (y*width+x)*16, 1.0,
                    ((x*4093+y*257)%32769)/32768.0,
                    ((x*1237+y*3559)%32769)/32768.0,
                    ((x*7919+y*911)%32769)/32768.0)
    assert public.sha(raw) == HISTORICAL_INPUT_SHA256
    return bytes(raw)


def historical_case():
    params = public.initial.settings(2, 32, 18)
    for param in params:
        if param['slot'] in [4, 22, 24]: param['value'] = {4: 290, 22: 25, 24: 100}[param['slot']]
    return dict(family=2, geometry=[32, 18], depth=32, pattern='historical290',
        state='retained_native_ucrt_strength290', parameters=params)


def historical_replay(directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    historical = json.loads(HISTORICAL.read_text())
    assert historical['comparison']['native_exported_sha256'] == HISTORICAL_OUTPUT_SHA256
    assert historical['fixture']['source_sha256'] == HISTORICAL_INPUT_SHA256
    assert historical['comparison']['different_float_words'] == 80
    previous = public.initial.fixture
    results = {}
    try:
        public.initial.fixture = lambda case: historical_fixture()
        for name in ['o2', 'san', 'default']:
            binary = (strength.profiles.default_contract_build(directory/name, source) if name == 'default'
                else public.build(directory/name, source, name == 'san'))
            for route in ['classic', 'smart']:
                error, raw, metadata = public.mac_render(binary, directory, historical_case(), route, strength.ENV)
                assert not error and public.sha(raw) == HISTORICAL_OUTPUT_SHA256, (name, route, error)
                (directory/f'{name}_{route}.raw').write_bytes(raw)
                results[name+'_'+route] = dict(error=error, raw_sha256=public.sha(raw), metadata=metadata, native_raw_exact=True)
    finally: public.initial.fixture = previous
    return dict(case=historical_case(), fixture_sha256=HISTORICAL_INPUT_SHA256,
        native_raw_sha256=HISTORICAL_OUTPUT_SHA256, historical_report_sha256=public.sha(HISTORICAL.read_bytes()),
        historical_native_unique_math_keys=577, historical_native_math_calls=725,
        previous_different_float_words=80, results=results,
        new_windows_execution_claimed=False, general_native_ucrt_claimed=False)


if __name__ == '__main__':
    import sys
    output = Path(sys.argv[1]); output.mkdir(parents=True, exist_ok=False)
    worker = Path('/tmp/radial_windows_reference_v2_20261001/target/release/aex-guest-worker')
    before = json.loads(strength.BEFORE.read_text())
    assert public.sha(worker.read_bytes()) == before['window_worker_sha256']
    fields = native_fields(worker, output/'fields')
    result = dict(native_setup_case_count=len(fields), native_setup_fields=fields,
        historical_native_ucrt_replay=historical_replay(output/'historical', strength.candidate_source(strength.before_source())))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2)+'\n')
    print('STRENGTH_FIELDS_DONE', len(fields), 'HISTORICAL_UCRT 6 EXACT', flush=True)
