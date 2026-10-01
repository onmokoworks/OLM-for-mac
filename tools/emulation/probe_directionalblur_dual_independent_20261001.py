#!/usr/bin/env python3
"""Exported Smart comparisons for independent typed sources and Layer fields."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile

import probe_directionalblur_layer_general_20261001 as layer
import test_dblur_generic_backonly_effectmain_20260821 as sdk

ROOT = layer.owner.ROOT
SOURCE = layer.owner.SOURCE
HARNESS = ROOT / 'tools/emulation/directionalblur_layer_geometry_effectmain_harness_20261001.cpp'
AEX_SHA = 'd3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e'
WORKER_SHA = '0eb2f7705598f7b5f53563b9d920274ba094c835ff3dbaaf5f6fb214ec0cfd61'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def fixture(w, h, depth, profile, seed):
    state = seed
    out = bytearray()
    words = (0, 1, 32767, 32768, 32769, 65535)
    float_bits = (0, 0x80000000, 1, 0x80000001, 0x3f7fffff, 0x3f800000,
                  0x3f800001, 0xbf800000, 0x40000000, 0x40800000)
    for y in range(h):
        for x in range(w):
            rgb = []
            for component in range(3):
                state = (1664525 * state + 1013904223) & 0xffffffff
                if profile == 'sparse':
                    value = ((state >> 16) & 255) / 255
                    if depth == 16:
                        value = int(value * 32768 + .5)
                elif profile == 'raw_range':
                    value = state >> 16 if depth == 16 else (((state >> 8) % 2049) - 512) / 256
                elif profile == 'boundary':
                    at = (x + 3*y + component) % (len(words) if depth == 16 else len(float_bits))
                    value = words[at] if depth == 16 else struct.unpack('<f', struct.pack('<I', float_bits[at]))[0]
                else:
                    raise ValueError(profile)
                rgb.append(value)
            if profile == 'sparse':
                alpha = (1 if (x == y or x == w-1 or y == h-1) else 0)
                if depth == 16:
                    alpha *= 32768
            else:
                alpha = (0, 16384, 32768, 65535)[(x + 2*y) % 4] if depth == 16 else (0, -.5, .5, 1, 2)[(x + 2*y) % 5]
            out.extend(struct.pack('<4H' if depth == 16 else '<4f', alpha, *rgb))
    return bytes(out)


def specifications():
    for geometry in ((17, 11), (61, 47)):
        for depth in (16, 32):
            for profile in ('sparse', 'raw_range', 'boundary'):
                for field in ('sparse', 'raw_range'):
                    for mode, controls in (
                        ('front', {5:31, 10:0, 1:89.99998474121094}),
                        ('back', {5:0, 10:47, 1:-90.00001525878906}),
                        ('dual', {5:31, 10:47, 1:179.99998474121094}),
                    ):
                        for name, more in (
                            ('layer', {}),
                            ('components', {3:37.75, 7:31.75, 12:63.75}),
                            ('fade_gain', {3:80.25, 7:99.75, 12:45.25, 6:17, 11:43, 2:2.25, 15:.25}),
                        ):
                            values = {1:17.25, 2:1, 3:0, 5:4, 6:0, 7:0, 10:3,
                                      11:0, 12:0, 15:73.75, 16:3, 18:1, 19:0, 20:3}
                            values.update(controls); values.update(more)
                            yield {'geometry':list(geometry), 'depth':depth, 'input_profile':profile,
                                   'layer_profile':field, 'mode':mode, 'feature':name,
                                   'input_seed':0x41c64e6d, 'layer_seed':0x1234abcd,
                                   'parameters':values}


def inputs(case):
    w, h = case['geometry']; depth = case['depth']
    return (fixture(w, h, depth, case['input_profile'], case['input_seed']),
            fixture(w, h, depth, case['layer_profile'], case['layer_seed']))


def build(temp, source, sanitize=False):
    temp.mkdir()
    # Relocate quoted includes only; preserve the numerical source body.
    relocated = re.sub(r'^#include "([^"]+)"',
                       lambda m: '#include "' + str((SOURCE.parent / m.group(1)).resolve()) + '"',
                       source, flags=re.MULTILINE)
    production = temp / 'production_under_test.cpp'; production.write_text(relocated)
    saved = sdk.CPP
    try:
        sdk.CPP = HARNESS.read_text().replace('../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp', str(production))
        return sdk.build(temp, sanitize)
    finally:
        sdk.CPP = saved


def mac_render(binary, case, mode, env=None):
    data, field = inputs(case); w, h = case['geometry']
    controls = ','.join(f'{slot}={value}' for slot, value in case['parameters'].items())
    run = subprocess.run([str(binary), str(w), str(h), str(case['depth']), controls,
                          mode, str(w), str(h)], input=data+field, check=True, capture_output=True, env=env)
    lines = dict(line.split(' ', 1) for line in run.stdout.decode().splitlines())
    return int(lines['ERROR']), bytes.fromhex(lines['RAW']), [int(v) for v in lines['COUNTS'].split()]


def native_render(worker, temp, case, origin_probe=False):
    data, field = inputs(case); w, h = case['geometry']
    # Worker world dumps are created exclusively, so each session owns a dir.
    temp = Path(tempfile.mkdtemp(prefix='native_', dir=temp))
    ip, lp, op, manifest = [temp / n for n in ('input.raw', 'layer.raw', 'output.raw', 'layers.json')]
    ip.write_bytes(data); lp.write_bytes(field)
    entry = {'slot':17, 'width':w, 'height':h, 'path':str(lp)}
    if origin_probe:
        entry['origin_x'] = 2; entry['origin_y'] = 1
    manifest.write_text(json.dumps({'v':1, 'layers':[entry]}))
    payload = 'v4|' + ';'.join(f'param_{slot}@{slot}:{"angle" if slot in (1,19) else "f64"}={value}'
                             for slot, value in case['parameters'].items())
    request = json.dumps({'v':4, 'type':'render_frame', 'frame_index':0,
                          'current_time':{'value':0, 'scale':24, 'step':1, 'total':1}, 'parameters':payload}).encode()
    run = subprocess.run([str(worker), 'session', str(layer.owner.AEX), str(ip), str(op), str(w), str(h), '24',
                          '--pixel-format', 'argb16' if case['depth'] == 16 else 'argb32f',
                          '--fixture-layers-v1', str(manifest), '--fixture-render-path', 'smart'],
                         input=struct.pack('<I',len(request))+request, capture_output=True)
    if origin_probe:
        assert run.returncode != 0 and b'unknown field' in run.stderr and b'origin_x' in run.stderr, run.stderr
        return {'exit_code':run.returncode, 'unknown_origin_field_rejected':True,
                'stderr_sha256':sha(run.stderr), 'aex_origin_render_proved':False}
    if run.returncode:
        raise RuntimeError(run.stderr.decode()[-2000:])
    messages = []; pos = 0
    while pos < len(run.stdout):
        n = struct.unpack_from('<I',run.stdout,pos)[0]; pos += 4
        messages.append(json.loads(run.stdout[pos:pos+n])); pos += n
    ready = next(m for m in messages if m['type'] == 'session_ready')
    frame = next(m for m in messages if m['type'] == 'frame_done')
    close = next(m for m in messages if m['type'] == 'session_closed')['close']
    raw = op.read_bytes()
    assert ready['setup']['global_setup_error'] == ready['setup']['params_setup_error'] == 0
    assert frame['render_error'] == 0 and frame['status'] == 'ok'
    assert frame['output']['guards_intact'] and frame['output']['render_path'] == 'smartfx'
    assert len(raw) == len(data) and frame['output']['checksum'] == sha(raw)
    assert close['session_clean'] and close['unsupported_suite_calls'] == [] and close['dropped_unsupported_suite_calls'] == 0
    assert ip.read_bytes() == data and lp.read_bytes() == field
    return raw, frame, payload, close


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert sha(args.worker.read_bytes()) == WORKER_SHA and sha(layer.owner.AEX.read_bytes()) == AEX_SHA
    cases = []; source = SOURCE.read_text()
    with tempfile.TemporaryDirectory(prefix='dblur_dual_independent_') as directory:
        temp = Path(directory); binary = build(temp/'o2', source)
        origin = native_render(args.worker, temp, next(specifications()), True)
        for case in specifications():
            native, frame, payload, close = native_render(args.worker, temp, case)
            data, field = inputs(case); results = {}
            for mode in ('classic','smart'):
                error, raw, counts = mac_render(binary, case, mode)
                assert counts[:3] == ([0,0,0] if mode == 'classic' else [21,21,2])
                assert counts[3] == counts[4]
                results[mode] = {'error':error, 'raw_sha256':sha(raw) if not error else None,
                                 'raw_exact':not error and raw == native, 'callback_counts':counts,
                                 'different_bytes':sum(a != b for a,b in zip(native,raw)) if not error else None,
                                 'first_differences':[{'offset':i,'aex':a,'mac':b} for i,(a,b) in enumerate(zip(native,raw)) if a != b][:12] if not error else []}
            case.update(input_sha256=sha(data), layer_sha256=sha(field), native_raw_sha256=sha(native),
                        frame_done=frame, parameter_payload=payload, session_clean=close['session_clean'],
                        unsupported_suite_calls=close['unsupported_suite_calls'], results=results)
            cases.append(case)
            if len(cases) % 18 == 0:
                print('DBLUR_DUAL_INDEPENDENT',len(cases),sum(all(r['raw_exact'] for r in c['results'].values()) for c in cases),flush=True)
    deps = [Path(__file__), HARNESS, Path(sdk.__file__), SOURCE, ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp']
    deps += list((ROOT/'core').glob('dblur*'))
    deps += [ROOT/'core/olm_sha256_rows.h', SOURCE.parent/'OLMDirectionalBlur.h',
             SOURCE.parent/'OLMDirectionalBlur_Strings.h']
    report = {'schema':'directionalblur.dual-independent-public/1', 'source_sha256':sha(source.encode()),
              'aex_sha256':AEX_SHA, 'worker_sha256':WORKER_SHA, 'case_count':len(cases),
              'summary':{'both_cmd_exact_count':sum(all(r['raw_exact'] for r in c['results'].values()) for c in cases)},
              'origin_capability_probe':origin, 'cases':cases,
              'dependencies_sha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in deps},
              'claims_not_made':['AEX exported CPU Smart uses emulated host imports, not native Windows UCRT/AE',
                  'Mac public Classic/Smart use real SDK in a fake host, not installed/native AE',
                  'Type 3 Layer state exceeds native declared popup choices2; no normal UI/save reachability proof',
                  'No native Layer parameter readback or padded native world proof',
                  'Resident Layer manifest rejects origin fields; no exported nonzero-origin numerical proof',
                  'No arbitrary input/settings/geometry/ROI/downsample or all-ten compatibility completion']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('RESULT',report['summary'],flush=True)


if __name__ == '__main__':
    main()
