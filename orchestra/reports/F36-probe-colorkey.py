#!/usr/bin/env python3
"""Expose captured failure diagnostics without changing the original test."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
from olm_assets import resolve_asset
scratch=ROOT/'orchestra/state/F36-fixture-runner-worktree-and-triage/colorkey'
scratch.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
os.environ['CPATH']=os.pathsep.join(str(resolve_asset(ROOT/p)) for p in ('Headers','Headers/SP','Util','Resources'))
tempfile.tempdir=str(scratch)
original=subprocess.run

def observed(*args,**kwargs):
    try:
        return original(*args,**kwargs)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            (scratch/'failed-probe-stdout.bin').write_bytes(exc.stdout)
        print(f'CAPTURED rc={exc.returncode} stdout_bytes={len(exc.stdout or b"")}',flush=True)
        print((exc.stderr or b'').decode(errors='replace'),flush=True)
        raise

subprocess.run=observed
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_olmcolorkey_source_bound_atomic_20260813')
result=unittest.TextTestRunner().run(suite)
raise SystemExit(not result.wasSuccessful())
