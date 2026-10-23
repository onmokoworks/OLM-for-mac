#!/usr/bin/env python3
"""Build all Release bundles, audit effective flags, and run bounded public fuzz."""
import argparse
import json
import os
from pathlib import Path
import shutil
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'orchestra/state/R01-xcode-release-config'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('build', 'fuzz'), required=True)
    args = parser.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH),
               OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
    records = []

    def run(cmd, log):
        with log.open('w') as out:
            result = subprocess.run(list(map(str, cmd)), cwd=ROOT, env=env,
                                    stdout=out, stderr=subprocess.STDOUT)
        return result.returncode

    for project in sorted((ROOT / 'mac').glob('*/Mac/*.xcodeproj')):
        name = project.stem
        row = {'plugin': name}
        if args.phase == 'build':
            build = SCRATCH / 'build' / name
            cmd = ['xcodebuild', '-project', project, '-jobs', '1',
                   f'OBJROOT={build}/obj', f'SYMROOT={build}/products',
                   f'SHARED_PRECOMPS_DIR={build}/pch', 'CODE_SIGNING_ALLOWED=NO']
            settings = {}
            for config in ('Debug', 'Release'):
                log = SCRATCH / f'{name}-{config}-settings.log'
                rc = run(cmd + ['-configuration', config, '-showBuildSettings'], log)
                assert rc == 0, log
                settings[config] = dict(line.lstrip().split(' = ', 1)
                                        for line in log.read_text().splitlines() if ' = ' in line)
            keys = sorted(k for k in settings['Release'] if k.startswith('GCC_') or k.startswith('OTHER_C'))
            row['deployment_target'] = settings['Release']['MACOSX_DEPLOYMENT_TARGET']
            row['effective_flags'] = {c: {k: s.get(k) for k in keys} for c, s in settings.items()}
            row['flag_differences'] = {k: [settings['Debug'].get(k), settings['Release'].get(k)]
                                       for k in keys if settings['Debug'].get(k) != settings['Release'].get(k)}
            assert set(row['flag_differences']) <= {'GCC_OPTIMIZATION_LEVEL', 'GCC_SYMBOLS_PRIVATE_EXTERN'}, row
            release = settings['Release']
            assert release['GCC_OPTIMIZATION_LEVEL'] == '2'
            assert set(release['ARCHS'].split()) == {'arm64', 'x86_64'}
            assert release['ONLY_ACTIVE_ARCH'] == 'NO'
            assert release['MACOSX_DEPLOYMENT_TARGET'] == settings['Debug']['MACOSX_DEPLOYMENT_TARGET']
            for flag in ('-ffp-contract=off', '-fno-fast-math'):
                assert flag in release['OTHER_CFLAGS']
                assert flag in release['OTHER_CPLUSPLUSFLAGS']
            row['command'] = list(map(str, cmd + ['-configuration', 'Release', 'build']))
            row['exit_code'] = run(row['command'], SCRATCH / f'{name}-build.log')
            if row['exit_code'] == 0:
                binary = build / f'products/Release/{name}.plugin/Contents/MacOS/{name}'
                row['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
                row['lipo'] = subprocess.check_output(['lipo', '-info', str(binary)], text=True).strip()
                assert 'x86_64' in row['lipo'] and 'arm64' in row['lipo']
            shutil.rmtree(build, ignore_errors=True)
        else:
            plugin = 'radialblur' if name == 'OLMRadialBlur' else name.lower()
            main_root = ROOT.parent.parent if ROOT.parent.name == 'worktrees' else ROOT
            python = main_root / 'tools/emulation/.venv/bin/python'
            work = SCRATCH / 'fuzz' / plugin
            report = SCRATCH / f'{plugin}-fuzz.json'
            cmd = [python, ROOT / 'tools/fuzz/run.py', '--plugin', plugin, '--seed', '1',
                   '--n', '100', '--jobs', '1', '--scratch', work, '--report', report,
                   '--corpus', SCRATCH / 'corpus' / plugin, '--shrink-attempts', '0']
            row['command'] = list(map(str, cmd))
            row['exit_code'] = run(cmd, SCRATCH / f'{plugin}-fuzz.log')
            if report.exists():
                data = json.loads(report.read_text())
                row['provenance'] = data.get('provenance')
                row['first_mismatches'] = {}
                for case in data.get('cases', []):
                    for route, result in case.get('result', {}).get('routes', {}).items():
                        if result['status'] == 'mismatch' and route not in row['first_mismatches']:
                            row['first_mismatches'][route] = {
                                'index': case['index'], 'input_sha256': case['input_sha256'],
                                'depth': case['depth'], 'geometry': case['geometry'],
                                'result': result,
                                'oracle': case['result'].get('oracles', {}).get(route)}
                row.update(status=data.get('status'), summary=data.get('summary'), cases=len(data.get('cases', [])))
            shutil.rmtree(work, ignore_errors=True)
        records.append(row)
        (SCRATCH / f'{args.phase}-summary.json').write_text(json.dumps(records, indent=2) + '\n')
        print(name, row.get('exit_code'), row.get('lipo', row.get('summary')), flush=True)
    if any(r['exit_code'] != 0 for r in records):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
