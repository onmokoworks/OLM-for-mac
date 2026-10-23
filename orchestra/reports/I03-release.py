#!/usr/bin/env python3
"""Pass the fixture runner its supported log/scratch location; leave gate logic intact."""
import runpy, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I03-integration-check'
original=subprocess.run
def run(argv,*args,**kwargs):
    if isinstance(argv,(list,tuple)) and any(str(a).endswith('run_olm_mac_fixed_fixture_regression_20260805.py') for a in argv):
        argv=[*argv,'--results-dir',str(S/'fixtures')]
    return original(argv,*args,**kwargs)
subprocess.run=run
sys.argv=[str(ROOT/'scripts/run_olm_release_gate_20260806.py'),'--report',str(S/'release.json')]
runpy.run_path(sys.argv[0],run_name='__main__')
