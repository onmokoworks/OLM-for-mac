#!/usr/bin/env python3
"""Run both real gates sequentially; retain generated evidence without repinning it."""
import argparse, hashlib, json, os, shutil, signal, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
S = ROOT / 'orchestra/state/R05-regenerate-stale-bindings'
MAIN = ROOT.parent.parent
S.mkdir(parents=True, exist_ok=True)
PY = str(MAIN / 'tools/emulation/.venv/bin/python3')
env = dict(os.environ, OLM_TEST_JOBS='2', PYTHONDONTWRITEBYTECODE='1',
           TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_MAIN_ASSETS=str(MAIN), PYTHONPATH=str(ROOT))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', choices=('release','generic'))
options = parser.parse_args()
paths = subprocess.check_output(['git', 'ls-files', 'refs/conformance'], cwd=ROOT, text=True).splitlines()
backup = S/'gate-input-backup'
backup.mkdir(exist_ok=False)
for rel in paths:
    target = backup/rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/rel, target)
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
rows = json.loads((S/'commands.json').read_text()) if options.only and (S/'commands.json').exists() else []
if options.only: rows = [r for r in rows if r['name'] != options.only]
def restore_generated(stage):
    for rel in paths:
        path = ROOT/rel
        if digest(path) != digest(backup/rel):
            target = S/'generated'/stage/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            shutil.copyfile(backup/rel, path)
try:
    for name, argv in (
        ('release', ['scripts/run_olm_release_gate_20260806.py', '--report', str(S/'release.json'), '--results-dir', str(S/'fixtures')]),
        ('generic', ['scripts/run_olm_generic_beta_gate.py', '--report', str(S/'generic.json')]),
    ):
        if options.only and name != options.only:
            continue
        command = [PY, '-B', *argv]
        start = time.monotonic()
        with (S/f'{name}.log').open('w') as log:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = proc.wait(timeout=14400)
            except BaseException:
                os.killpg(proc.pid, signal.SIGTERM)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise
        restore_generated(name)
        rows.append(dict(name=name, command=command, exit=code, seconds=round(time.monotonic()-start, 2)))
        (S/'commands.json').write_text(json.dumps(rows, indent=2)+'\n')
        print(f'{name}: exit {code}', flush=True)
finally:
    restore_generated('interrupted')
    shutil.rmtree(backup)
