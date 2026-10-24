"""Run historical ColorKeep unittest classes and standalone test functions serially."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
import unittest
ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/P02a-colorkeep-geometry'
os.environ.update(TMPDIR=str(S), OLM_TEST_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
rows = []
for path in sorted((ROOT/'tests').glob('test_colorkeep*.py')):
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        for name in sorted(vars(module)):
            if name.startswith('test_') and callable(getattr(module, name)):
                suite.addTest(unittest.FunctionTestCase(getattr(module, name)))
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        rows.append(dict(file=path.name, run=result.testsRun,
                         failures=[str(t) for t,e in result.failures],
                         errors=[str(t) for t,e in result.errors], skipped=len(result.skipped)))
    except Exception:
        traceback.print_exc()
        rows.append(dict(file=path.name, import_error=traceback.format_exc()))
(S/('unit-'+sys.argv[1]+'.json')).write_text(json.dumps(rows, indent=2)+'\n')
