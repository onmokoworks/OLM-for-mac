#!/usr/bin/env python3
"""Check retained full-frame Rotation planes across the numerical boundary."""
import contextlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=ROOT/'orchestra/state/F36-fixture-runner-worktree-and-triage/full-planes'
SCRATCH.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),PYTHONDONTWRITEBYTECODE='1')
tempfile.tempdir=str(SCRATCH)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
module=importlib.import_module('test_olmradialblur_case0010_rotation_mac_production_planes_20260805')
results=[]
for ref in ('f5a74754^1','f5a74754','24e8b60d'):
    revision=subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()
    with tempfile.TemporaryDirectory(dir=SCRATCH) as raw:
        directory=Path(raw)
        archive=directory/'source.tar'
        with archive.open('wb') as stream:subprocess.run(['git','archive',revision,'mac/OLMRadialBlur','core'],cwd=ROOT,stdout=stream,check=True)
        with tarfile.open(archive) as stream:stream.extractall(directory,filter='data')
        module.SOURCE=directory/'mac/OLMRadialBlur/OLMRadialBlur.cpp'
        module.REPORT=SCRATCH/(revision+'.json')
        with (SCRATCH/(revision+'.log')).open('w') as stream,contextlib.redirect_stdout(stream):
            rc=module.main()
        report=json.loads(module.REPORT.read_text())
        row=dict(revision=revision,returncode=rc,conformance_status=report['conformance_status'],matches=report['matches'],differences=report['differences'],output_sha256=report['output_argb8_sha256'])
        results.append(row)
        print(json.dumps(row),flush=True)
        (SCRATCH/'results.json').write_text(json.dumps(results,indent=2)+'\n')
