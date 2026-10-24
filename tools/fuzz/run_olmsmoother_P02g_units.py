#!/usr/bin/env python3
"""Run Smoother v1 unit modules serially with ticket-local temporary storage."""
import importlib.util
import inspect
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[2]
S = ROOT/'orchestra/state/P02g-smoother-geometry/units'

def main():
    S.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(S), TMP=str(S), TEMP=str(S), OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
    tempfile.tempdir = str(S)
    sys.path.insert(0,str(ROOT))
    baseline = None
    if '--baseline-source' in sys.argv:
        baseline = S/'before.cpp'
        revision = sys.argv[sys.argv.index('--baseline-source')+1]
        baseline.write_bytes(subprocess.check_output([
            'git','show',revision+':mac/OLMSmoother/Mac/OLMSmoother_port.cpp'],cwd=ROOT))
    suite = unittest.TestSuite()
    for path in sorted((ROOT/'tests').glob('test_olmsmoother*.py')):
        if path.name.startswith('test_olmsmoother2'): continue
        spec = importlib.util.spec_from_file_location(path.stem,path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        if hasattr(module,'SCRATCH'): module.SCRATCH = S
        if baseline and hasattr(module,'SOURCE'): module.SOURCE = baseline
        if '--functions-only' not in sys.argv:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith('test_'): continue
            params = inspect.signature(fn).parameters
            if not params:
                suite.addTest(unittest.FunctionTestCase(fn))
            elif list(params) == ['tmp_path']:
                suite.addTest(unittest.FunctionTestCase(lambda fn=fn: fn(S)))
            else:
                raise RuntimeError(f'Unhandled fixture for {path.name}:{name}')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
