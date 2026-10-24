#!/usr/bin/env python3
"""Trace original PARAMS_SETUP and compare popup registrations with port source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/fuzz'))
from adapters.public import messages


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--main', type=Path, default=Path('/Users/onmk/Documents/Projects/Personal/OLM as'))
    p.add_argument('--worker', type=Path, default=Path.home() / '.cache/olm-emu/worker-F46-pow/aex-guest-worker')
    a = p.parse_args()
    scratch = a.scratch.resolve()
    if not scratch.is_relative_to(ROOT / 'orchestra/state/A01c-real-ae-render-aerender'):
        p.error('use this ticket scratch directory')
    scratch.mkdir(parents=True, exist_ok=True)
    source = json.loads((ROOT / 'orchestra/reports/A01b-evidence/source-popups.json').read_text())
    historical = json.loads((ROOT / 'orchestra/reports/A01-evidence/probe-2026.json').read_text())
    rows = []
    for plugin, original in [('OLMDirectionalBlur', 'OLMDirectionalBlur'),
                             ('OLMDistanceGradation', 'DistanceGradation'),
                             ('OLMKiraKira', 'OLMKiraKira')]:
        binary = a.main / 'plugins_2025' / (original + '.aex')
        inp = scratch / 'input.argb'
        inp.write_bytes(bytes(4))
        command = [str(a.worker), 'session', str(binary), str(inp), str(scratch / 'output'),
                   '1', '1', '24', '--pixel-format', 'argb8']
        with (scratch / f'{plugin}.stdout').open('wb') as out, (scratch / f'{plugin}.stderr').open('wb') as err:
            subprocess.run(command, input=b'', stdout=out, stderr=err, check=True, timeout=30,
                           env=dict(os.environ, TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch)))
        setup = next(m['setup'] for m in messages((scratch / f'{plugin}.stdout').read_bytes())
                     if m['type'] == 'session_ready')
        assert not setup['global_setup_error'] and not setup['params_setup_error']
        port = next(r for r in source if r['plugin'] == plugin)
        for param in setup['parameters']:
            if param['param_type'] != 7:
                continue
            src = next((r for r in port['popups'] if r['name'].lower() == param['name'].lower()), None)
            equal = src is not None and (src['count'] == param['valid_max'] and
                    src['default'] == param['default_value'] and
                    [x.strip() for x in src['labels']] == [x.strip() for x in param['choices'].split('|')])
            ae_row = next(r for r in historical['rows'] if r['plugin'] == plugin)
            ae_prop = next((r for r in ae_row['params']['children']
                            if r['name'].lower() == param['name'].lower()), None)
            rows.append(dict(plugin=plugin, command=command, slot=param['slot'], name=param['name'],
                             aex_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                             original=param, source=src, registration_faithful=equal,
                             ae_current_readback=None,
                             ae_historical_source='orchestra/reports/A01-evidence/probe-2026.json',
                             ae_historical_readback=ae_prop))
    result = dict(worker_sha256=hashlib.sha256(a.worker.read_bytes()).hexdigest(), rows=rows)
    (scratch / 'popup-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(rows)} popups; {sum(r["registration_faithful"] for r in rows)} faithful registrations')


if __name__ == '__main__':
    main()
