"""Bounded randomized update qualification using the unchanged shared oracle.

The range restriction is a declared corpus design, not a clamp/retry of failures.
Full exposed extrema are retained separately in smoke-v1.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

CRATE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CRATE.parents[1] / 'tools/oracle'))
import olm_oracle as oracle

p = argparse.ArgumentParser()
p.add_argument('--candidate', required=True)
p.add_argument('--out', required=True)
p.add_argument('--seed', type=int, default=20261112)
p.add_argument('--cases', type=int, default=113)
p.add_argument('--year', default='2025')
p.add_argument('--plan')
p.add_argument('--resident', action='store_true')
p.add_argument('--opaque', action='store_true')
a = p.parse_args()
if a.opaque:
    pixels = oracle.input_pixels
    def opaque(w, h, seed):
        result = pixels(w, h, seed)
        result[..., 3] = 255
        return result
    oracle.input_pixels = opaque
generate = oracle.generate_cases
def bounded(parameters, count, seed, sizes, downsample):
    if a.plan:
        return json.loads(Path(a.plan).read_text())
    sampled = copy.deepcopy(parameters)
    for param in sampled:
        if param['slot'] in (3, 4):
            param['maximum'] = 128
        elif param['slot'] == 12:
            param['maximum'] = 12
    cases = generate(sampled, count, seed, sizes, downsample)
    for case in cases:
        case['sampling_domain'] = {'thresholds': [0, 128], 'blur_size': [0, 12],
                                   'other_controls': 'full declared range'}
    return cases
oracle.generate_cases = bounded
original = CRATE.parents[3] / 'upstream_20261112/extracted/OLMDistanceGradation/OLMDistanceGradation/Plugins/64' / a.year / 'DistanceGradation.aex'
args = ['render', '--reference', str(original), '--candidate', a.candidate,
        '--out', a.out, '--seed', str(a.seed), '--cases', str(a.cases),
        '--jobs', '2', '--routes', 'smart8,smart16,smart32',
        '--sizes', '1x1,3x7,11x7,17x11,31x19', '--downsample', '1,1/2,1/4', '--timeout', '60']
if a.resident:
    args += ['--resident']
raise SystemExit(oracle.main(args))
