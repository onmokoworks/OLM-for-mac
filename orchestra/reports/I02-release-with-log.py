#!/usr/bin/env python3
"""Observe the unmodified gate's captured fixture output without changing its result."""
import runpy, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'orchestra/state/I02-integration-finish'
original_run=subprocess.run

def observed_run(*args,**kwargs):
    result=original_run(*args,**kwargs)
    command=args[0] if args else kwargs.get('args',[])
    if any(str(x).endswith('run_olm_mac_fixed_fixture_regression_20260805.py') for x in command):
        (S/'fixtures-stdout.log').write_text(result.stdout or '')
        (S/'fixtures-stderr.log').write_text(result.stderr or '')
        (S/'fixtures-exit.txt').write_text(str(result.returncode)+'\n')
    return result

subprocess.run=observed_run
sys.argv=[str(ROOT/'scripts/run_olm_release_gate_20260806.py'),'--report',str(S/'release-sdk.json')]
runpy.run_path(sys.argv[0],run_name='__main__')
