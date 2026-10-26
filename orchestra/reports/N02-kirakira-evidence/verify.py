#!/usr/bin/env python3
"""Reproduce N02 measurements serially, with logs and reports in ticket scratch."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = ROOT / 'orchestra/state/N02-olmkirakira-nightly-20261025'
parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=('campaigns', 'replays', 'nested', 'reference-witnesses', 'perf', 'baseline'))
args = parser.parse_args()
os.chdir(ROOT)
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(SCRATCH), TMP=str(SCRATCH), TEMP=str(SCRATCH),
                  OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
commands = []

def execute(label, cmd):
    with (SCRATCH / (label + '.log')).open('w') as log:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    commands.append(dict(label=label, command=cmd, returncode=result.returncode))
    (SCRATCH / (args.phase + '-commands.json')).write_text(json.dumps(commands, indent=2) + '\n')
    print(label, result.returncode, flush=True)

def run(label, flags, driver='tools/fuzz/run.py'):
    execute(label, [sys.executable, driver, '--plugin', 'olmkirakira', '--jobs', '1',
        '--scratch', str(SCRATCH / label), '--report', str(SCRATCH / (label + '.json')),
        '--corpus', str(SCRATCH / 'generated'), *flags])

if args.phase == 'campaigns':
    for sampler, flags in (
        ('realistic', ['--geometry', 'realistic']),
        ('realistic-v2', ['--geometry', 'realistic-v2']),
        ('odd-even-v1', ['--geometry', 'realistic', '--size-sampler', 'odd-even-v1',
                         '--max-size', '1080', '--size-max-height', '1080']),
        ('default', [])):
        for seed in ([1] if sampler == 'default' else [2601, 2602, 2603]):
            run(f'{sampler}-{seed}', ['--seed', str(seed), '--n', '300' if sampler == 'default' else '200',
                '--shrink-attempts', '0', '--shrink-seconds', '0', *flags])
elif args.phase in ('replays', 'reference-witnesses'):
    for corpus in sorted((ROOT / 'tests/fuzz_corpus').glob('olmkirakira*')):
        if args.phase == 'reference-witnesses' and corpus.name != 'olmkirakira_N02_nightly':
            continue
        if corpus.name == 'olmkirakira_N02_nightly':
            for witness in sorted(corpus.glob('*.json')):
                data = json.loads(witness.read_text())
                flags = ['--geometry', 'realistic-v2' if data['geometry_sampler'] == 'realistic-v2' else 'realistic',
                         '--max-size', str(data['max_size'])]
                if data.get('size_sampler') == 'odd-even-v1':
                    flags += ['--size-sampler', 'odd-even-v1', '--size-max-height', str(data['size_max_height'])]
                run(('reference-N02-' if args.phase == 'reference-witnesses' else 'replay-N02-') + witness.stem,
                    ['--replay', str(witness), *flags, *(['--reference-build'] if args.phase == 'reference-witnesses' else [])])
        else:
            run('replay-' + corpus.name, ['--replay', str(corpus), *(['--geometry', 'realistic'] if 'P02c' in corpus.name else [])])
elif args.phase == 'nested':
    run('replay-T15b', ['--replay', 'tests/fuzz_corpus/olmkirakira/T15b-odd-even-realistic',
        '--geometry', 'realistic', '--size-sampler', 'odd-even-v1', '--max-size', '1080', '--size-max-height', '1080'])
    run('replay-other-reductions', ['--replay', 'tests/fuzz_corpus/olmkirakira_gate_off_T06/other_reductions'])
elif args.phase == 'perf':
    execute('perf', [sys.executable, 'tools/perf/ref_vs_fast.py', '--plugin', 'olmkirakira',
                    '--jobs', '1', '--scratch', str(SCRATCH / 'perf')])
elif args.phase == 'baseline':
    # Preserve the initial revision as an explicit input to the comparison.
    baseline = SCRATCH / 'before.cpp'
    if not baseline.exists():
        raise SystemExit('Restore the report\'s base revision to scratch/before.cpp first.')
    run('baseline-default-1', ['--campaign-source', str(baseline), '--seed', '1', '--n', '300',
        '--shrink-attempts', '0', '--shrink-seconds', '0'], 'tools/emulation/verify_kirakira_admission_F10.py')

raise SystemExit(int(any(row["returncode"] != 0 for row in commands)))
