#!/usr/bin/env python3
"""Serial real-render qualification, replay of every call, and negative control."""
import argparse
import contextlib
import json
from pathlib import Path
from types import SimpleNamespace
import record
from contract import sha, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--originals', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--harness', type=Path, default=record.oracle.DEFAULT_HARNESS)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    summary = {'schema_version': 1, 'plugins': {}, 'source_sha256': {}}
    for folder, files in [(record.HERE, ['contract.py', 'record.py', 'win_debug.py', 'demo.py', 'adapter/src/main.rs']),
                          (record.HERE.parents[1] / 'plugins/olm-directional-blur/src', ['algorithm.rs', 'rotate.rs', 'noise.rs', 'rowdriver.rs']),
                          (record.HERE.parents[1] / 'plugins/olm-kirakira/src', ['trig.rs', 'trig_tables.rs'])]:
        for f in files:
            path = folder / f
            summary['source_sha256'][str(path)] = sha(path)
    for key, basename in [('directional', 'OLMDirectionalBlur.aex'), ('kirakira', 'OLMKiraKira.aex')]:
        captured = out / key
        settings = SimpleNamespace(module=args.originals / basename, profile=record.HERE / f'profiles/{key}.json',
            harness=args.harness, out=captured, request=record.HERE / f'profiles/{key}-request.json',
            route='smart8', width=11, height=7, seed=20261112, max_calls=128, max_bytes=16*1024*1024, timeout=120)
        if record.capture(settings):
            raise RuntimeError(f'{key} capture failed')
        manifest = json.loads((captured / 'manifest.json').read_text())
        if not manifest['render_evidence']['smart_render_selector_dispatched'] or manifest['render_evidence']['smart_render_error']:
            raise RuntimeError('real SmartFX render not established')
        # Same original, same input, same request, without the debugger.
        control = out / f'{key}-control'
        control.mkdir()
        command = manifest['command'].copy()
        command[-2] = str(control / 'output.png')
        proc = record.oracle.run_process(command, 120, record.oracle.frame_deadline_environment(120))
        write_json(control / 'process.json', proc)
        if proc['returncode'] or proc['timeout'] or proc['cancelled']:
            raise RuntimeError('uninstrumented control failed')
        diff = record.oracle.compare_samples(record.oracle.load_output(captured / 'output.png', 8),
            record.oracle.load_output(control / 'output.png', 8), 8)
        write_json(control / 'comparison.json', diff)
        rows = []
        for rec_path in sorted((captured / 'calls').glob('*/record.json')):
            target = out / f'{key}-replay' / rec_path.parent.name
            target.parent.mkdir(exist_ok=True)
            with (target.parent / f'{rec_path.parent.name}.log').open('w') as log, contextlib.redirect_stdout(log):
                code = record.replay(SimpleNamespace(record=rec_path, out=target, timeout=30, adapter=None,
                    adapter_exe=record.HERE / 'adapter/target/release/record-adapter.exe'))
            result = json.loads((target / 'comparison.json').read_text())
            rows.append({'sequence': int(rec_path.parent.name), 'exact': code == 0,
                         'comparison_sha256': sha(target / 'comparison.json'), 'comparisons': result['comparisons']})
        summary['plugins'][key] = {'calls': len(rows), 'exact': sum(x['exact'] for x in rows),
            'counts': manifest['counts'], 'control_exact': diff['exact'], 'module_sha256': manifest['module_sha256'],
            'capture_manifest_sha256': sha(captured / 'manifest.json'), 'records': rows,
            'snapshot_bytes': manifest['snapshot_bytes_reserved'], 'cleanup_verified': manifest['cleanup_verified'],
            'render_evidence': manifest['render_evidence']}
        print(f"{key}: {sum(x['exact'] for x in rows)}/{len(rows)} exact replays; control exact={diff['exact']}", flush=True)
        write_json(out / 'summary.json', summary)
    wrong = out / 'wrong-gaussian'
    with (out / 'wrong-gaussian.log').open('w') as log, contextlib.redirect_stdout(log):
        code = record.replay(SimpleNamespace(record=out / 'directional/calls/000000/record.json', out=wrong,
            timeout=30, adapter='wrong.gaussian', adapter_exe=record.HERE / 'adapter/target/release/record-adapter.exe'))
    summary['negative_control'] = json.loads((wrong / 'comparison.json').read_text())
    summary['negative_control']['exit_code'] = code
    summary['pass'] = code == 1 and all(x['exact'] == x['calls'] and x['control_exact'] and x['cleanup_verified']
                                      for x in summary['plugins'].values())
    write_json(out / 'summary.json', summary)
    print(f"wrong variant caught={code == 1}; PASS={summary['pass']}")
    return 0 if summary['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
