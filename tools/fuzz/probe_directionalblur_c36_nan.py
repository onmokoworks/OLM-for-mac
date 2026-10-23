#!/usr/bin/env python3
"""Scratch-only test of generated-NaN correction at DirectionalBlur rotation.

Uses C30's two F32-bound nonfinite witnesses and O2/ASan/UBSan comparison.
The production finite-input gate and numerical sources remain unchanged.
This tests sufficiency of rotation correction, not general admission.
"""
from pathlib import Path
import json
import sys

import probe_directionalblur_c30_nonfinite as probe
from adapters.public import replace_once


class RotationNaN(probe.Nonfinite):
    def compile(self, argv, deadline):
        argv = list(argv)
        if argv[0] == 'clang++':
            host = Path(next(str(x) for x in argv if str(x).endswith('/host.cpp')))
            original = probe.ROOT / 'core/dblur_rotate.cpp'
            target = host.with_name('rotate_nan.cpp')
            body = original.read_text()
            body = '#include "x86_float.h"\n' + body
            for operator in ('*', '+', '-', '/'):
                body = replace_once(body, f'volatile float result = a {operator} b;',
                    f'volatile float result = olm::x86_float::generated_nan(a {operator} b, a, b);')
            target.write_text(body)
            assert original in argv, 'rotation translation unit missing'
            argv = [target if x == original else x for x in argv]
            argv += ['-I', probe.ROOT / 'core']
        return super().compile(argv, deadline)


if __name__ == '__main__':
    probe.Nonfinite = RotationNaN
    probe.main()
    report_path = Path(sys.argv[sys.argv.index('--report') + 1])
    report = json.loads(report_path.read_text())
    report['experiment'] = 'scratch rotation generated-NaN correction plus finite-gate bypass'
    report['driver_sha256'] = probe.sha(Path(__file__).read_bytes())
    report['rotation_source_sha256'] = probe.sha((probe.ROOT / 'core/dblur_rotate.cpp').read_bytes())
    report['nan_helper_sha256'] = probe.sha((probe.ROOT / 'core/x86_float.h').read_bytes())
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
