#!/usr/bin/env python3
"""Re-run one numbered fixed-fixture command with the runner's asset environment."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
from olm_assets import resolve_asset, main_assets
spec=importlib.util.spec_from_file_location('fixed_runner',ROOT/'scripts/run_olm_mac_fixed_fixture_regression_20260805.py')
runner=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=runner
spec.loader.exec_module(runner)
p=argparse.ArgumentParser()
p.add_argument('index',type=int)
a=p.parse_args()
commands=[(lane.name,cmd) for lane in runner.LANES for cmd in lane.commands]
lane,command=commands[a.index]
scratch=ROOT/'orchestra/state/F36-fixture-runner-worktree-and-triage/followup'
scratch.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',OLM_TEST_JOBS='1',OLM_MAIN_ASSETS=str(main_assets()),TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),OLM_REGRESSION_SCRATCH=str(scratch))
env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(ROOT/'tools/emulation')])
env['CPATH']=os.pathsep.join(str(resolve_asset(ROOT/name)) for name in ('Headers','Headers/SP','Util','Resources'))
resolved=(str(resolve_asset(ROOT/'tools/emulation/.venv/bin/python3')),*command[1:])
log=scratch/f'{a.index:03d}-{lane}.log'
rc=0
try:runner.run(resolved,env=env,log=log)
except subprocess.CalledProcessError as exc:rc=exc.returncode
(scratch/f'{a.index:03d}.json').write_text(json.dumps(dict(lane=lane,command=list(resolved),returncode=rc,log=str(log)),indent=2)+'\n')
print(f'{a.index} {lane} rc={rc}')
raise SystemExit(rc)
