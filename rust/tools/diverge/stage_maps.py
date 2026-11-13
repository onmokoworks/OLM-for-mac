"""Grounded pilot maps. All original modules are used in place, never copied."""
import argparse
import copy
from pathlib import Path
import random
import struct
import olm_diverge as d

PINS = {
    'distance': ('DistanceGradation.aex', 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'),
    'directional': ('OLMDirectionalBlur.aex', 'd3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e'),
}


def scalar(kind, value):
    return {'type': kind, 'value': value}


def ptr(name):
    return {'type': 'ptr', 'buffer': name}


def cvmat(data, w, h):
    # Windows x64 CvMat: type, step, refcount*, hdr_refcount, padding,
    # data*, rows, cols. Capture script is the ABI authority.
    raw = struct.pack('<iiQi4xQii', 0x42424005, w * 4, 0, 0, 0, h, w)
    return {'size': 40, 'hex': raw.hex(), 'pointers': [{'offset': 24, 'buffer': data}]}


def stage(name, shape, ref_call, ref_buffer, cand_call, cand_buffer, grounding):
    return {'id': name, 'dtype': 'f32', 'shape': shape,
            'reference': {'call': ref_call, 'buffer': ref_buffer},
            'candidate': {'call': cand_call, 'buffer': cand_buffer}, 'grounding': grounding}


def build(plugin, original, candidate, *, w=17, h=11, kx=11, ky=11, angle=0.37,
          inject=-1, historical=False, source=None, seed=20261112):
    if plugin not in PINS or not 1 <= w <= 4096 or not 1 <= h <= 4096 or w*h > 1048576:
        raise ValueError('unsupported plugin/geometry')
    channels = 1 if plugin == 'distance' else 4
    size = w*h*channels*4
    if source is None:
        rng = random.Random(seed)
        source = struct.pack('<' + 'f'*(w*h*channels), *[rng.randrange(1001)/1000 for _ in range(w*h*channels)])
    if len(source) != size:
        raise ValueError('input must be tightly packed little-endian float32 of the declared shape')
    if inject < -1 or inject >= w*h*channels:
        raise ValueError('injection index outside image')
    original, candidate = Path(original).resolve(), Path(candidate).resolve()
    if d.witness.sha256(original) != PINS[plugin][1]:
        raise ValueError('original hash is not the reviewed stage-map version; supply your own grounded JSON map')
    buffers = {'input': {'size': size, 'hex': source.hex()}, 'middle': {'size': size}, 'output': {'size': size}}
    ref = {'schema_version': 1, 'module': str(original), 'fma': 'fma', 'buffers': copy.deepcopy(buffers), 'calls': []}
    rust = {'schema_version': 1, 'module': str(candidate), 'fma': 'fma', 'buffers': copy.deepcopy(buffers), 'calls': []}
    case = {'schema_version': 1, 'stateless_calls': True,
            'reference': {'sha256': PINS[plugin][1], 'expected_fma': 1, 'witness': ref},
            'candidate': {'sha256': d.witness.sha256(candidate), 'expected_fma': 1, 'witness': rust,
                          'return_bits': {'0': '00000000', '1': '00000000'}},
            'parameters': {'plugin': plugin, 'width': w, 'height': h, 'kx': kx, 'ky': ky,
                           'angle': angle, 'injection_index': inject, 'historical_sse': historical, 'seed': seed},
            'stages': []}
    if plugin == 'distance':
        if any(n < 1 or n > 8193 or n % 2 == 0 for n in (kx, ky)):
            raise ValueError('apertures must be odd in 1..8193')
        if w == 1 or h == 1 or (kx == 3 and ky == 3):
            raise ValueError('separable replay excludes singleton axes and the special 3x3 dispatch')
        case['scope'] = 'DistanceGradation Gaussian filter subpipeline; field input supplied, earlier mask/distance and later compose unmapped'
        grounding = ('rust/plugins/olm-distance-gradation/VALIDATION.md: Native Gaussian SIMD finding; '
                     'tests/capture_native_gaussian.py: CvMat ABI, cvSmooth RVA 0x12864d0; '
                     'src/filters.rs: gaussian_mode row then column. Full cvSmooth control checked each run.')
        for name in ('input', 'middle', 'output'):
            ref['buffers'][name+'_mat'] = cvmat(name, w, h)
        for i, (src, dst, x, y) in enumerate([('input', 'middle', kx, 1), ('middle', 'output', 1, ky)]):
            ref['calls'].append({'label': 'gaussian.row' if i == 0 else 'gaussian.column', 'rva': '0x12864d0',
                'args': [ptr(src+'_mat'), ptr(dst+'_mat'), scalar('i32', 2), scalar('i32', x), scalar('i32', y),
                         scalar('f64', 0), scalar('f64', 0)], 'return': 'void'})
            rust['calls'].append({'label': ref['calls'][-1]['label'], 'export': 'olm_stage_gaussian_v1',
                'args': [ptr(src), ptr(dst), scalar('u32', w), scalar('u32', h), scalar('u32', x), scalar('u32', y),
                         scalar('u32', 0 if historical else 1), scalar('i64', inject if i == 0 else -1)], 'return': 'i32'})
        ref['buffers']['full'] = {'size': size}
        ref['buffers']['full_mat'] = cvmat('full', w, h)
        full = copy.deepcopy(ref['calls'][0])
        full['label'] = 'full-filter control'
        full['args'][1] = ptr('full_mat')
        full['args'][4] = scalar('i32', ky)
        ref['calls'].append(full)
        case['controls'] = [{'side': 'reference', 'call': 2, 'left': 'output', 'right': 'full'}]
        shape = [h, w]
        names = ['gaussian.row', 'gaussian.column']
    else:
        if historical:
            raise ValueError('historical SSE option applies only to DistanceGradation')
        case['scope'] = 'DirectionalBlur rotation subpipeline; supplied padded RGBA input, forward/inverse rotations; intervening blur/normalization unmapped'
        grounding = ('notes/IR_OLMDirectionalBlur.md: Input Rotate and pipeline steps 3/10; '
                     'tools/emulation/test_dblur_rotate_exact.py: 0x1ec0(src,dst,width,height,float angle); '
                     'src/rotate.rs: rgba. This isolated pair does not claim full blur-render coverage.')
        for i, (src, dst, a) in enumerate([('input', 'middle', angle), ('middle', 'output', -angle)]):
            args = [ptr(src), ptr(dst), scalar('u32', w), scalar('u32', h), scalar('f32', a)]
            ref['calls'].append({'label': 'rotate.forward' if i == 0 else 'rotate.inverse', 'rva': '0x1ec0',
                                 'args': copy.deepcopy(args), 'return': 'void'})
            rust['calls'].append({'label': ref['calls'][-1]['label'], 'export': 'olm_stage_rotate_v1',
                                 'args': args + [scalar('i64', inject if i == 0 else -1)], 'return': 'i32'})
        shape = [h, w, 4]
        names = ['rotate.forward', 'rotate.inverse']
    case['stages'] = [stage('input', shape, 0, 'input', 0, 'input', 'identical supplied raw bytes; unchanged input observed after first call'),
                      stage(names[0], shape, 0, 'middle', 0, 'middle', grounding),
                      stage(names[1], shape, 1, 'output', 1, 'output', grounding)]
    return case


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plugin', choices=PINS)
    p.add_argument('--original', required=True, type=Path)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--input', type=Path, help='raw little-endian f32 field or RGBA stage input')
    p.add_argument('--width', type=int, default=17)
    p.add_argument('--height', type=int, default=11)
    p.add_argument('--kx', type=int, default=11)
    p.add_argument('--ky', type=int, default=11)
    p.add_argument('--angle', type=float, default=.37, help='radians at internal rotate ABI, not UI degrees')
    p.add_argument('--inject', type=int, default=-1, help='increment selected middle-stage element by one ULP')
    p.add_argument('--historical-sse', action='store_true')
    a = p.parse_args()
    if a.out.exists():
        p.error('output already exists')
    c = build(a.plugin, a.original, a.candidate, w=a.width, h=a.height, kx=a.kx, ky=a.ky, angle=a.angle,
              inject=a.inject, historical=a.historical_sse, source=a.input.read_bytes() if a.input else None)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    d.write_json(a.out, c)
    print(a.out)


if __name__ == '__main__':
    main()
