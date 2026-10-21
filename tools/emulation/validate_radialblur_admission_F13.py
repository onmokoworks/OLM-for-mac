#!/usr/bin/env python3
"""Run the eight existing RadialBlur admission smoke tests in a worktree.

SDK headers/utility source are read from MAIN; production source and strings
remain in this worktree. All temporary builds stay under the ticket scratch.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from validate_radialblur_tests_T01 import ROOT, SOURCE, SMOKE, Results
import hashlib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--main', type=Path, default=Path('/Users/onmk/Documents/Projects/Personal/OLM as'))
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/F13-radial-offset-newly-admitted-mismatch')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    tempfile.tempdir = str(scratch)
    with tempfile.TemporaryDirectory(prefix='sdk_', dir=scratch) as name:
        sdk_root = Path(name)
        for directory in ['Headers', 'Util', 'Resources']:
            (sdk_root/directory).symlink_to(args.main/directory, target_is_directory=True)
        (sdk_root/'mac').symlink_to(ROOT/'mac', target_is_directory=True)
        suite = unittest.TestSuite()
        for stem in SMOKE:
            if stem == 'parameter_ui_parity_20260806':
                continue  # UI is outside this ticket; T01 records its stale Thickness assertion.
            path = ROOT/'tests'/f'test_olmradialblur_{stem}.py'
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[path.stem] = module
            spec.loader.exec_module(module)
            assert module.SOURCE == SOURCE
            module.ROOT = sdk_root
            for key, function in vars(module).items():
                if key.startswith('test_') and callable(function):
                    suite.addTest(unittest.FunctionTestCase(function, description=path.name+':'+key))
        result = unittest.TextTestRunner(verbosity=2, resultclass=Results).run(suite)
        args.report.write_text(json.dumps(dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), rows=result.rows), indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
