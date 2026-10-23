#!/usr/bin/env python3
"""Run existing DG beta tests against an explicit revision, without changing HEAD."""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--ref', required=True)
p.add_argument('--scratch', type=Path, required=True)
a = p.parse_args()
a.scratch = a.scratch.resolve()
assert a.scratch.is_relative_to(ROOT/'orchestra/state')
a.scratch.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(a.scratch), TMP=str(a.scratch), TEMP=str(a.scratch))
tempfile.tempdir = str(a.scratch)
source = subprocess.check_output(['git','show',a.ref+':mac/OLMDistanceGradation/OLMDistanceGradation.cpp'],cwd=ROOT).decode()
source = source.replace('#include "OLMDistanceGradation.h"', '#include "'+str(ROOT/'mac/OLMDistanceGradation/OLMDistanceGradation.h')+'"').replace('"../../core/', '"'+str(ROOT/'core')+'/').replace('"../../ucrtmath/', '"'+str(ROOT/'ucrtmath')+'/')
cpp = a.scratch/'base.cpp';cpp.write_text(source)
suite = unittest.TestSuite()
for file in sorted((ROOT/'tests').glob('test_olmdistancegradation_*beta_20260820.py')):
    spec = importlib.util.spec_from_file_location(file.stem,file)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if hasattr(module,'SOURCE'):module.SOURCE=cpp
    if hasattr(module,'HARNESS'):
        module.HARNESS = module.HARNESS.replace('"mac/OLMDistanceGradation/OLMDistanceGradation.cpp"','"'+str(cpp)+'"')
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
