"""Replay every KiraKira corpus using its saved worker and maximum size."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
scratch = root / 'orchestra/state/U02-kirakira-ramp-editor'
scratch.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, TMPDIR=str(scratch), OLM_TEST_JOBS='1')
groups = {}
for source in sorted((root / 'tests/fuzz_corpus').rglob('*.json')):
    record = json.loads(source.read_text())
    if record.get('plugin') != 'olmkirakira':
        continue
    groups.setdefault(record['max_size'], []).append(source)
results = []
for size, paths in sorted(groups.items()):
    inputs = scratch / f'corpora-{size}'
    inputs.mkdir(exist_ok=True)
    for stale in inputs.glob('*.json'):
        if stale.is_symlink():
            stale.unlink()
    for i, source in enumerate(paths):
        link = inputs / f'{i:04d}_{source.name}'
        if not link.exists():
            link.symlink_to(source)
    command = [sys.executable, str(root / 'tools/fuzz/run.py'), '--plugin', 'olmkirakira',
               '--replay', str(inputs), '--max-size', str(size), '--jobs', '1',
               '--scratch', str(scratch / f'replay-{size}'), '--budget-minutes', '60',
               '--report', str(scratch / f'replay-{size}.json')]
    if size>256:
        command += ['--size-sampler','odd-even-v1']
    with (scratch / f'replay-{size}.log').open('w') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = json.loads((scratch / f'replay-{size}.json').read_text())
    results.append({'max_size':size, 'requested':len(paths), 'exit_code':result.returncode,
                    'status':record.get('status'), 'completed':record.get('completed'),
                    'matches_saved':record.get('replay_matches_saved')})
    print(json.dumps(results[-1]), flush=True)
(scratch / 'replay-summary.json').write_text(json.dumps(results, indent=2)+'\n')
sys.exit(any(r['exit_code'] for r in results))
