#!/usr/bin/env python3
"""Verify only the F47b native lifecycle boundary; never claim pixel agreement."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'orchestra/state/F47b-native-plugin-host-render'
MAIN = Path('/Users/onmk/Documents/Projects/Personal/OLM as')


def main():
    env = dict(os.environ, TMPDIR=str(STATE), TMP=str(STATE), TEMP=str(STATE))
    worker = STATE / 'aex-guest-worker'
    bundle = STATE / 'bundles/xcode/OLMBlur/products/OLMBlur.plugin'
    command = [str(worker), 'native-plugin', str(bundle)]
    records = []
    for _ in range(2):
        run = subprocess.run(command + ['--setup'], env=env, capture_output=True, text=True, check=True, timeout=30)
        record = json.loads(run.stdout)
        assert record['capability'] == 'olmblur-lifecycle-only'
        assert record['setup_ok'] is True, record
        assert record['render_supported'] is False
        assert record['session_supported'] is False
        assert record['advertised_num_params'] == 6
        assert len(record['parameters']) == 5
        assert [p['param_type'] for p in record['parameters']] == [10, 2, 1, 7, 4]
        assert record['selectors_executed'] == [dict(selector=name, error=0) for name in
            ('GLOBAL_SETUP', 'PARAMS_SETUP', 'SEQUENCE_SETUP', 'SEQUENCE_SETDOWN', 'GLOBAL_SETDOWN')]
        records.append(record)
    assert records[0] == records[1], 'repeat lifecycle result changed'
    inspect = subprocess.run(command + ['--inspect'], env=env, capture_output=True, text=True, check=True, timeout=30)
    assert json.loads(inspect.stdout)['selectors_executed'] == []
    for suffix in ([], ['--render'], ['--session']):
        rejected = subprocess.run(command + suffix, env=env, capture_output=True, timeout=30)
        assert rejected.returncode == 2, rejected
    aex = MAIN / 'plugins_2025/OLMBlur.aex'
    old_worker = Path.home() / '.cache/olm-emu/worker-F47-nativeplugin/aex-guest-worker'
    originals = []
    for binary in (old_worker, worker):
        result = subprocess.run([str(binary), 'setup', str(aex)], env=env, capture_output=True, check=True, timeout=60)
        originals.append(result.stdout)
    assert originals[0] == originals[1], 'existing AEX setup changed'
    oracle = json.loads(originals[0])
    (STATE / 'aex-setup.json').write_bytes(originals[0])
    native = records[0]
    differences = {}
    for field in ('advertised_num_params', 'out_flags', 'out_flags2'):
        if native[field] != oracle[field]:
            differences[field] = {'aex': oracle[field], 'plugin': native[field]}
    aex_params = [{k: p[k] for k in ('slot', 'index', 'param_type', 'name', 'flags')} for p in oracle['parameters']]
    native_params = [{k: p[k] for k in ('slot', 'index', 'param_type', 'name', 'flags')} for p in native['parameters']]
    if aex_params != native_params:
        differences['parameters'] = {'aex': aex_params, 'plugin': native_params}
    summary = dict(native=native, setup_differences=differences, repeated_native_setup=2,
                   aex_setup_bytes=len(originals[0]), aex_setup_sha256=hashlib.sha256(originals[0]).hexdigest(),
                   aex_setup_unchanged=True, render_cases=0,
                   note='Sequence selectors return success; OLMBlur has no sequence-specific switch cases.')
    (STATE / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('native', 'setup_differences')}))
    print('setup differences:', json.dumps(differences))
    print('AcquireSuite calls:', json.dumps(native['acquire_suite_calls']))


if __name__ == '__main__':
    main()
