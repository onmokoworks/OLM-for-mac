#!/usr/bin/env python3
"""Run existing RadialBlur smoke and archived public tests without rebinding hashes.

No pytest dependency is needed for the selected zero-argument smoke tests. A
baseline source can be selected for the smoke tests without editing production.
Archived public tests deliberately retain their original source/worker binding.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'mac/OLMRadialBlur/OLMRadialBlur.cpp'
SMOKE = ['generic_baseline_20260820', 'generic_baseline_sanitizers_20260820',
         'generic_budget_20260821', 'generic_type3_sanitizers_20260820',
         'global_polar_smart_contract_20260820', 'size_noise_effectmain_20260821',
         'typed_inner_geometry_guard_20260807', 'parameter_ui_parity_20260806']


class Results(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append(dict(test=str(test), status='pass'))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.rows.append(dict(test=str(test), status='failure', detail=self.failures[-1][1]))

    def addError(self, test, err):
        super().addError(test, err)
        self.rows.append(dict(test=str(test), status='error', detail=self.errors[-1][1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-revision')
    parser.add_argument('--archived', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    suite = unittest.TestSuite()
    source = (subprocess.check_output(['git', 'show', args.baseline_revision+
              ':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=ROOT).decode()
              if args.baseline_revision else SOURCE.read_text())
    with tempfile.TemporaryDirectory(prefix='radial_tests_') as name:
        path = Path(name)/'OLMRadialBlur.cpp'
        path.write_text(re.sub(r'^#include "([^"]+)"', lambda m:
            '#include "'+str((SOURCE.parent/m.group(1)).resolve())+'"', source, flags=re.M))
        files = ([*sorted((ROOT/'tests').glob('test_radialblur*_20261002.py'))] if args.archived else
                 [ROOT/'tests'/('test_olmradialblur_'+stem+'.py') for stem in SMOKE])
        for file in files:
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[file.stem] = module
            spec.loader.exec_module(module)
            if args.baseline_revision and hasattr(module, 'SOURCE'):
                module.SOURCE = path if isinstance(module.SOURCE, Path) else source
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
            for key, function in vars(module).items():
                if key.startswith('test_') and callable(function):
                    suite.addTest(unittest.FunctionTestCase(function, description=file.name+':'+key))
        result = unittest.TextTestRunner(verbosity=2, resultclass=Results).run(suite)
        args.report.write_text(json.dumps(dict(baseline_revision=args.baseline_revision,
            archived=args.archived, tests=result.testsRun, failures=len(result.failures),
            errors=len(result.errors), rows=result.rows), indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
